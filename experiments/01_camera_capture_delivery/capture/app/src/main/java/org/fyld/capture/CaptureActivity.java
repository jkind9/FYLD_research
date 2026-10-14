package org.fyld.capture;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.media.Image;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.text.Html;
import android.text.InputType;
import android.text.method.LinkMovementMethod;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.google.ar.core.ArCoreApk;
import com.google.ar.core.Camera;
import com.google.ar.core.CameraConfig;
import com.google.ar.core.CameraConfigFilter;
import com.google.ar.core.Config;
import com.google.ar.core.Frame;
import com.google.ar.core.Session;
import com.google.ar.core.TrackingState;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.EnumSet;
import java.util.List;
import java.util.Locale;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/**
 * The FYLD capture app (phone_session_v2.md). Record walk: ARCore tracks through the shared camera while every
 * Camera2 image, its capture settings, ARCore's record and the motion sensors go into a queue on the phone's
 * storage, which a sender drains to the PC during and after the walk. Record motion sensors only: the calibration
 * rest recording, camera closed. Run all checks: ARCore set-up, a 15 s tracking run, the link speed and whether
 * deflating the grey frames pays; the report is saved and sent to the PC. The camera image fills the screen.
 */
public class CaptureActivity extends Activity implements GLSurfaceView.Renderer, SharedCameraRig.Listener {
    static final String VERSION = "1.0";
    static final long TRACKING_MS = 15000;
    static final int SAMPLE_EVERY = 15, SAMPLES = 20;
    private static final int GREEN = 0xFF2E9E4F, RED = 0xFFD64545, GREY = 0xFF8A8A8A;
    private static final String WALK = "Record walk", IMU_ONLY = "Record motion sensors only (phone at rest)";

    /** Everything one recording writes to; callbacks on other threads add only while it is the current one. */
    private static final class Recording {
        final DiskQueue queue;
        final boolean walk;
        final FrameCapture capture;
        final FrameAssembler assembler;
        final FrameWriter writer;
        final long startMs = SystemClock.elapsedRealtime();
        long lastTelemetryMs, telemetry;

        Recording(DiskQueue queue, FrameCapture capture, boolean deflate) {
            this.queue = queue;
            this.capture = capture;
            walk = capture != null;
            assembler = walk ? new FrameAssembler(true) : null;
            writer = walk ? new FrameWriter(assembler, queue, deflate) : null;
        }
    }

    private final Handler main = new Handler(Looper.getMainLooper());
    private final CameraPreview preview = new CameraPreview();
    private final List<Object[]> setupChecks = new ArrayList<>();  // {name, status, reason, detail, text}, kept between runs
    private final List<Double> updateMs = new ArrayList<>();  // ARCore update times since the last telemetry
    private final List<byte[]> samples = Collections.synchronizedList(new ArrayList<>());  // camera images for the compression check
    private Report report = new Report();
    private File root;
    private GLSurfaceView surface;
    private TextView status, live;
    private LinearLayout results;
    private EditText hostField;
    private Button walkButton, imuButton, checkButton;
    private Session session;
    private SharedCameraRig rig;
    private ImuLogger imu;
    private Uploader uploader;
    private Thread uploaderThread;
    private Config.DepthMode depthMode = Config.DepthMode.DISABLED;
    private boolean installRequested, depthEnabled, busy, resumed;
    private volatile boolean textureSet, checking;
    private volatile Recording current;
    private volatile TrackingStats stats;
    private volatile String trackingText = "Starting the camera...", sendText = "";
    private volatile int sampleWidth, sampleHeight;
    private int texture = -1, viewWidth, viewHeight, imageCount;
    private long checkStart;

    // ---- Screen ----------------------------------------------------------------------------------

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        root = new File(getExternalFilesDir(null), "sessions");
        root.mkdirs();
        imu = new ImuLogger(this);
        surface = new GLSurfaceView(this);
        surface.setPreserveEGLContextOnPause(true);
        surface.setEGLContextClientVersion(2);
        surface.setRenderer(this);
        surface.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        LinearLayout top = panel();
        top.addView(text("FYLD capture", 22, Color.WHITE, true));
        Button notice = new Button(this);
        notice.setText("ARCore and privacy notice");
        notice.setOnClickListener(v -> showArCoreNotice());
        top.addView(notice);
        status = text("Type the computer address, then record.", 17, Color.WHITE, false);
        live = text("", 14, 0xFFCFCFCF, false);
        top.addView(status);
        top.addView(live);

        LinearLayout bottom = panel();
        results = new LinearLayout(this);
        results.setOrientation(LinearLayout.VERTICAL);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(results);
        bottom.addView(scroll, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(150)));
        hostField = new EditText(this);
        hostField.setHint("Computer address, e.g. 192.168.68.123");
        hostField.setHintTextColor(GREY);
        hostField.setTextColor(Color.WHITE);
        hostField.setTextSize(TypedValue.COMPLEX_UNIT_SP, 17);
        hostField.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        hostField.setText(prefs().getString("host", ""));
        bottom.addView(hostField);
        walkButton = button(WALK, v -> toggle(true));
        imuButton = button(IMU_ONLY, v -> toggle(false));
        checkButton = button("Run all checks", v -> runAll());
        bottom.addView(walkButton);
        bottom.addView(imuButton);
        bottom.addView(checkButton);

        LinearLayout overlay = new LinearLayout(this);
        overlay.setOrientation(LinearLayout.VERTICAL);
        overlay.addView(top);
        overlay.addView(new FrameLayout(this), new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        overlay.addView(bottom);
        FrameLayout frame = new FrameLayout(this);
        frame.addView(surface);
        frame.addView(overlay);
        setContentView(frame);
        endInterruptedSessions();
        main.post(this::tick);
    }

    private void showArCoreNotice() {
        TextView content = new TextView(this);
        content.setText(Html.fromHtml(getString(R.string.arcore_notice), Html.FROM_HTML_MODE_LEGACY));
        content.setTextSize(TypedValue.COMPLEX_UNIT_SP, 17);
        content.setMovementMethod(LinkMovementMethod.getInstance());
        content.setPadding(dp(20), dp(16), dp(20), dp(16));
        ScrollView scroll = new ScrollView(this);
        scroll.addView(content);
        new AlertDialog.Builder(this).setTitle("ARCore and privacy notice")
                .setView(scroll).setPositiveButton("Close", null).show();
    }

    private LinearLayout panel() {
        LinearLayout p = new LinearLayout(this);
        p.setOrientation(LinearLayout.VERTICAL);
        p.setBackgroundColor(0xC0000000);
        p.setPadding(dp(16), dp(12), dp(16), dp(12));
        return p;
    }

    private TextView text(String value, int sp, int colour, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        t.setTextColor(colour);
        if (bold) t.setTypeface(Typeface.DEFAULT_BOLD);
        return t;
    }

    private Button button(String label, android.view.View.OnClickListener action) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 17);
        b.setOnClickListener(action);
        return b;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private SharedPreferences prefs() {
        return getSharedPreferences("capture", MODE_PRIVATE);
    }

    private String host() {
        return hostField.getText().toString().trim();
    }

    private void setStatus(String value) {
        runOnUiThread(() -> status.setText(value));
    }

    /** Records a check in the report and shows it as a coloured row. */
    private void record(String name, String result, String reason, JSONObject detail, String summary) {
        report.check(name, result, reason, detail);
        int colour = result.equals("PASS") ? GREEN : result.equals("FAIL") ? RED : GREY;
        String line = summary + (reason.isEmpty() ? "" : " (" + reason + ")");
        runOnUiThread(() -> {
            LinearLayout row = new LinearLayout(this);
            row.setGravity(Gravity.CENTER_VERTICAL);
            TextView badge = text(result.equals("SKIPPED") ? "SKIP" : result, 14, Color.WHITE, true);
            badge.setBackgroundColor(colour);
            badge.setPadding(dp(8), dp(2), dp(8), dp(2));
            row.addView(badge);
            row.addView(text("  " + line, 15, Color.WHITE, false));
            row.setPadding(0, dp(4), 0, dp(4));
            results.addView(row);
        });
    }

    private void setup(String name, String result, String reason, JSONObject detail, String summary) {
        setupChecks.add(new Object[]{name, result, reason, detail == null ? new JSONObject() : detail, summary});
        record(name, result, reason, detail, summary);
    }

    /** Four times a second: the live numbers; once a second while recording, a telemetry message. */
    private void tick() {
        Recording r = current;
        long now = SystemClock.elapsedRealtime();
        if (r != null && now - r.lastTelemetryMs >= 1000) {
            r.lastTelemetryMs = now;
            telemetry(r);
        }
        live.setText(liveText(current));
        main.postDelayed(this::tick, 250);
    }

    private String liveText(Recording r) {
        StringBuilder out = new StringBuilder(rig != null && rig.arActive() ? trackingText : "Camera closed");
        if (r != null) {
            double seconds = Math.max(1, SystemClock.elapsedRealtime() - r.startMs) / 1000.0;
            out.append(String.format(Locale.US, "\nRecording %s: %.0f s, gyroscope %.0f Hz, accelerometer %.0f Hz",
                    r.walk ? "walk" : "motion sensors", seconds, imu.gyroSamples() / seconds, imu.accelSamples() / seconds));
            if (r.walk) out.append(String.format(Locale.US, "\n%d frames (%.1f per s), %d dropped",
                    r.writer.frames(), r.writer.frames() / seconds, r.assembler.dropped()));
        }
        Uploader u = uploader;
        DiskQueue q = u == null ? null : u.current();
        if (q != null && q.dir().exists()) {
            double rate = u.rate();
            String eta = rate > 0 ? String.format(Locale.US, ", about %.0f s left at %.1f MB/s", q.pendingBytes() / rate, rate / 1e6) : "";
            out.append(String.format(Locale.US, "\nSending %s: %d frames, %.0f MB left%s", q.id(), q.pendingFrames(), q.pendingBytes() / 1e6, eta));
        }
        if (!sendText.isEmpty()) out.append("\n").append(sendText);
        out.append(String.format(Locale.US, "\nFree on the phone: %.1f GB", root.getUsableSpace() / 1e9));
        return out.toString();
    }

    // ---- ARCore and camera -----------------------------------------------------------------------

    private boolean ensureSession() {
        if (session != null) return true;
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, 1);
            return false;
        }
        try {
            if (ArCoreApk.getInstance().requestInstall(this, !installRequested) == ArCoreApk.InstallStatus.INSTALL_REQUESTED) {
                installRequested = true;
                return false;
            }
            session = new Session(this, EnumSet.of(Session.Feature.SHARED_CAMERA));
        } catch (Exception e) {
            setup("arcore_session", "FAIL", e.getClass().getSimpleName() + ": " + e.getMessage(), null, "ARCore session");
            setStatus("ARCore is not available: " + e.getMessage());
            return false;
        }
        setup("arcore_session", "PASS", "", null, "ARCore session started (shared camera)");
        boolean raw = session.isDepthModeSupported(Config.DepthMode.RAW_DEPTH_ONLY);
        boolean automatic = session.isDepthModeSupported(Config.DepthMode.AUTOMATIC);
        depthEnabled = raw || automatic;
        depthMode = raw ? Config.DepthMode.RAW_DEPTH_ONLY : automatic ? Config.DepthMode.AUTOMATIC : Config.DepthMode.DISABLED;
        setup("depth_supported", depthEnabled ? "PASS" : "SKIPPED", depthEnabled ? "" : "ARCore reports no depth mode",
                Report.put(Report.put(new JSONObject(), "raw_depth_only", raw), "automatic", automatic),
                "Depth: raw " + (raw ? "yes" : "no") + ", smoothed " + (automatic ? "yes" : "no"));
        List<CameraConfig> configs = session.getSupportedCameraConfigs(new CameraConfigFilter(session));
        JSONArray listed = new JSONArray();
        for (CameraConfig c : configs) {
            JSONObject entry = new JSONObject();
            Report.put(entry, "image", Arrays.asList(c.getImageSize().getWidth(), c.getImageSize().getHeight()).toString());
            Report.put(entry, "texture", Arrays.asList(c.getTextureSize().getWidth(), c.getTextureSize().getHeight()).toString());
            Report.put(entry, "fps", c.getFpsRange().toString());
            listed.put(entry);
        }
        setup("camera_configs", configs.isEmpty() ? "FAIL" : "PASS", configs.isEmpty() ? "none offered" : "",
                Report.put(new JSONObject(), "configs", listed), configs.size() + " camera settings offered");
        Config config = new Config(session);
        config.setFocusMode(Config.FocusMode.FIXED);
        config.setUpdateMode(Config.UpdateMode.LATEST_CAMERA_IMAGE);
        config.setDepthMode(depthMode);
        config.setPlaneFindingMode(Config.PlaneFindingMode.DISABLED);
        config.setLightEstimationMode(Config.LightEstimationMode.DISABLED);
        session.configure(config);
        rig = new SharedCameraRig(this, session, this);
        return true;
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] permissions, int[] grants) {
        // when granted, onResume follows and opens the camera
        if (grants.length == 0 || grants[0] != PackageManager.PERMISSION_GRANTED) setStatus("The camera permission is needed.");
    }

    /** Camera thread: every image of the app's 640 x 480 stream. */
    @Override
    public void onImage(Image image) {
        Recording r = current;
        int w = image.getWidth(), h = image.getHeight();
        if (r != null && r.walk) {
            byte[] buffer = r.assembler.buffer(w * h * 3 / 2);
            FrameWriter.nv21(image, buffer);
            r.assembler.addImage(image.getTimestamp(), buffer, w, h, System.currentTimeMillis(), System.nanoTime());
        } else if (checking && imageCount++ % SAMPLE_EVERY == 0 && samples.size() < SAMPLES) {
            byte[] copy = new byte[w * h * 3 / 2];
            FrameWriter.nv21(image, copy);
            sampleWidth = w;
            sampleHeight = h;
            samples.add(copy);
        }
    }

    /** Camera thread: the settings each image was taken with, matched to it by sensor timestamp. */
    @Override
    public void onCapture(TotalCaptureResult result) {
        Recording r = current;
        Long t = result.get(CaptureResult.SENSOR_TIMESTAMP);
        if (r == null || !r.walk || t == null) return;
        r.assembler.addCamera(t, SessionFrame.cameraSettings(result.get(CaptureResult.SENSOR_EXPOSURE_TIME),
                result.get(CaptureResult.SENSOR_FRAME_DURATION), result.get(CaptureResult.SENSOR_ROLLING_SHUTTER_SKEW),
                result.get(CaptureResult.LENS_FOCUS_DISTANCE), result.get(CaptureResult.SENSOR_SENSITIVITY),
                result.get(CaptureResult.LENS_OPTICAL_STABILIZATION_MODE)));
    }

    @Override
    public void onCameraError(String message) {
        setStatus(message);
        runOnUiThread(() -> {
            if (current != null && current.walk) stop("camera_error", "Camera error: " + message + ".");
        });
    }

    @Override
    public void onSurfaceCreated(GL10 unused, EGLConfig config) {
        GLES20.glClearColor(0f, 0f, 0f, 1f);
        texture = preview.create();
        textureSet = false;
    }

    @Override
    public void onSurfaceChanged(GL10 unused, int width, int height) {
        GLES20.glViewport(0, 0, width, height);
        viewWidth = width;
        viewHeight = height;
        textureSet = false;
    }

    /** GL thread: one ARCore update per screen redraw; a new camera image gives one ARCore record. */
    @Override
    public void onDrawFrame(GL10 unused) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT | GLES20.GL_DEPTH_BUFFER_BIT);
        SharedCameraRig r0 = rig;
        if (r0 == null || !r0.arActive() || texture < 0) return;
        if (!textureSet) {
            session.setCameraTextureName(texture);
            session.setDisplayGeometry(getWindowManager().getDefaultDisplay().getRotation(), viewWidth, viewHeight);
            textureSet = true;
        }
        Frame frame;
        long start = System.nanoTime();
        try {
            frame = session.update();
        } catch (Exception e) {
            return;
        }
        double ms = (System.nanoTime() - start) / 1e6;
        preview.draw(frame);
        Camera camera = frame.getCamera();
        trackingText = camera.getTrackingState() == TrackingState.TRACKING ? "ARCore: tracking"
                : "ARCore: not tracking (" + camera.getTrackingFailureReason().name().toLowerCase(Locale.US).replace('_', ' ') + ")";
        Recording r = current;
        if (r != null && r.walk) {
            synchronized (updateMs) {
                updateMs.add(ms);
            }
            if (r.capture.isNew(frame)) r.assembler.addArcore(frame.getAndroidCameraTimestamp(), r.capture.capture(frame));
        }
        TrackingStats s = stats;
        if (checking && s != null) {
            s.add(frame, ms, depthEnabled);
            long elapsed = SystemClock.elapsedRealtime() - checkStart;
            if (elapsed >= TRACKING_MS) {
                checking = false;
                main.post(() -> finishTracking(s, elapsed / 1000.0));
            }
        }
    }

    // ---- Recording -------------------------------------------------------------------------------

    private void toggle(boolean walk) {
        if (busy || checking) return;
        if (current != null) {
            stop("stop", null);
            return;
        }
        String host = host();
        if (host.isEmpty()) {
            setStatus("Type the computer address first (the receiver prints it).");
            return;
        }
        if (walk && (rig == null || !rig.arActive())) {
            setStatus("Wait for the camera and ARCore to start.");
            return;
        }
        if (root.getUsableSpace() < DiskQueue.MIN_FREE_BYTES) {
            setStatus("Under 1 GB free on the phone: free some space before recording.");
            return;
        }
        prefs().edit().putString("host", host).apply();
        startUploader();
        try {
            boolean deflate = prefs().getBoolean("deflate", false);
            String id = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date()) + (walk ? "_walk" : "_imu");
            if (!walk && rig != null) rig.close();  // hours at rest: no camera, no ARCore, less heat
            JSONObject info = new JSONObject().put("kind", walk ? "walk" : "imu_only").put("app", "org.fyld.capture " + VERSION)
                    .put("device", RecordingMeta.device(this))
                    .put("camera", walk ? RecordingMeta.camera(this, rig.cameraId) : JSONObject.NULL)
                    .put("arcore", walk ? RecordingMeta.arcore(session.getCameraConfig(), depthMode, Config.FocusMode.FIXED) : JSONObject.NULL)
                    .put("imu", new JSONObject().put("gyro", ImuLogger.describe(imu.gyro)).put("accel", ImuLogger.describe(imu.accel)))
                    .put("settings", SessionMessages.settings(FrameWriter.JPEG_QUALITY, deflate ? "deflate" : "raw"))
                    .put("clock", new JSONObject().put("start", RecordingMeta.clock()));
            DiskQueue queue = DiskQueue.create(root, id, info);
            Recording r = new Recording(queue, walk ? new FrameCapture(session, depthEnabled) : null, deflate);
            imu.start(queue);
            current = r;
            (walk ? walkButton : imuButton).setText("Stop recording");
            (walk ? imuButton : walkButton).setEnabled(false);
            checkButton.setEnabled(false);
            setStatus(walk ? "Recording: walk slowly, point at textured things, return to the start."
                    : "Recording motion sensors: leave the phone still on a table.");
        } catch (Exception e) {
            setStatus("Could not start: " + e.getMessage());
            if (!walk && resumed && rig != null) rig.open();
        }
    }

    /** Main thread, once a second: device state, queue and counts; stops the recording below 1 GB free or on a write error. */
    private void telemetry(Recording r) {
        long free = root.getUsableSpace();
        String error = r.walk && r.writer.error() != null ? r.writer.error() : imu.error();
        if (free < DiskQueue.MIN_FREE_BYTES) {
            stop("low_storage", "Stopped: under 1 GB free on the phone.");
            return;
        }
        if (error != null) {
            stop("write_error", "Stopped: " + error + ".");
            return;
        }
        Double arcoreMs = null;
        synchronized (updateMs) {
            if (!updateMs.isEmpty()) arcoreMs = TrackingStats.percentile(updateMs, 50);
            updateMs.clear();
        }
        int thermal = Build.VERSION.SDK_INT >= 29 ? getSystemService(PowerManager.class).getCurrentThermalStatus() : -1;
        int battery = getSystemService(BatteryManager.class).getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
        DiskQueue q = r.queue;
        try {
            q.add(SessionMessages.telemetry(q.id(), SystemClock.elapsedRealtimeNanos(), System.currentTimeMillis(), battery, thermal, free,
                    q.pendingFrames(), q.pendingBytes(), r.walk ? r.assembler.captured() : 0, r.walk ? r.writer.frames() : 0,
                    q.framesSent(), q.ackedFrames(), r.walk ? r.assembler.dropped() : 0, arcoreMs), new byte[0]);
            r.telemetry++;
        } catch (Exception e) {
            stop("write_error", "Stopped: could not write telemetry: " + e.getMessage() + ".");
        }
    }

    /** Ends the recording: no more frames are taken, everything held is queued, then the end message. Sending goes on. */
    private void stop(String reason, String message) {
        Recording r = current;
        if (r == null) return;
        current = null;
        busy = true;
        JSONObject clockEnd;
        try {
            clockEnd = RecordingMeta.clock();  // the moment of Stop, before the queue is flushed
        } catch (Exception e) {
            clockEnd = new JSONObject();
        }
        JSONObject stopped = clockEnd;
        setStatus("Finishing the recording...");
        new Thread(() -> {
            String result;
            try {
                imu.stop();
                JSONObject counts = new JSONObject();
                if (r.walk) {
                    r.writer.finish();
                    surface.queueEvent(r.capture::close);  // ARCore's anchors are released on the GL thread
                    counts.put("frames", r.writer.frames()).put("frames_captured", r.assembler.captured())
                            .put("frames_dropped", r.assembler.dropped()).put("frames_without_arcore", r.writer.withoutArcore())
                            .put("frames_without_camera_settings", r.writer.withoutCamera()).put("depth_frames", r.writer.depthFrames())
                            .put("anchors", r.capture.anchorCount()).put("arcore_records_late", r.assembler.lateArcore());
                }
                counts.put("gyro_samples", imu.gyroSamples()).put("accel_samples", imu.accelSamples())
                        .put("imu_batches", imu.batches()).put("telemetry", r.telemetry);
                r.queue.end(SessionMessages.end(r.queue.id(), reason, stopped, counts));
                result = (message == null ? "" : message + " ") + "Recording saved; sending goes on until the computer has all of it.";
            } catch (Exception e) {
                result = "Recording not finished cleanly: " + e.getMessage();
            }
            String text = result;
            runOnUiThread(() -> {
                busy = false;
                walkButton.setText(WALK);
                imuButton.setText(IMU_ONLY);
                walkButton.setEnabled(true);
                imuButton.setEnabled(true);
                checkButton.setEnabled(true);
                if (!r.walk && resumed && rig != null) rig.open();
                status.setText(text);
            });
        }).start();
    }

    /** A session the app did not finish (it was closed while recording) gets an end message, so it can be delivered. */
    private void endInterruptedSessions() {
        for (File dir : DiskQueue.sessions(root)) {
            try {
                DiskQueue q = DiskQueue.open(dir);
                if (!q.ended()) q.end(SessionMessages.end(q.id(), "interrupted", RecordingMeta.clock(), new JSONObject()));
            } catch (Exception e) {
                setStatus("Could not close " + dir.getName() + ": " + e.getMessage());
            }
        }
    }

    /** One sender for all sessions; a new address replaces the old sender once that one has let go. */
    private void startUploader() {
        String host = host();
        if (host.isEmpty() || (uploader != null && uploader.host().equals(host))) return;
        Uploader old = uploader;
        Thread previous = uploaderThread;
        if (old != null) old.stop();
        Uploader next = new Uploader(root, host, Uploader.PORT, text -> sendText = text);
        uploader = next;
        uploaderThread = new Thread(() -> {
            try {
                if (previous != null) previous.join();
            } catch (InterruptedException e) {
                return;
            }
            next.run();
        }, "uploader");
        uploaderThread.start();
    }

    // ---- Run all checks --------------------------------------------------------------------------

    private void runAll() {
        if (busy || checking || current != null) return;
        if (rig == null || !rig.arActive()) {
            setStatus("Wait for the camera and ARCore to start.");
            return;
        }
        prefs().edit().putString("host", host()).apply();
        report = new Report();
        results.removeAllViews();
        for (Object[] c : setupChecks) record((String) c[0], (String) c[1], (String) c[2], (JSONObject) c[3], (String) c[4]);
        samples.clear();
        imageCount = 0;
        stats = new TrackingStats();
        checkStart = SystemClock.elapsedRealtime();
        checking = true;
        busy = true;
        walkButton.setEnabled(false);
        imuButton.setEnabled(false);
        checkButton.setEnabled(false);
        setStatus("Tracking check, 15 s: walk slowly, point at textured things.");
    }

    private void finishTracking(TrackingStats s, double seconds) {
        JSONObject summary = s.summary(seconds);
        double fraction = s.trackingFraction();
        record("arcore_tracking", fraction >= 0.5 ? "PASS" : "FAIL", fraction >= 0.5 ? "" : "tracking under half the time", summary,
                String.format(Locale.US, "Tracked %.0f%% of %d frames, %.1f m walked", 100 * fraction, s.frames(), s.pathMetres()));
        record("tracked_points", s.maxPoints() > 0 ? "PASS" : "FAIL", s.maxPoints() > 0 ? "" : "no points", null,
                "Up to " + s.maxPoints() + " tracked points per frame");
        if (!depthEnabled) record("raw_depth_frames", "SKIPPED", "depth not supported", null, "Depth images");
        else record("raw_depth_frames", s.depthFrames() > 0 ? "PASS" : "FAIL", s.depthFrames() > 0 ? "" : "none received", null,
                s.depthFrames() + " depth images");
        int fps = session.getCameraConfig().getFpsRange().getUpper();
        setStatus("Measuring the link and compression...");
        new Thread(() -> {
            double link = linkSpeed();
            compression(link, fps);
            saveAndSend();
        }).start();
    }

    /** About 50 MB to the receiver; MB/s, or NaN when skipped or failed. */
    private double linkSpeed() {
        String host = host();
        if (host.isEmpty()) {
            record("link_speed", "SKIPPED", "no computer address entered", null, "Link speed");
            return Double.NaN;
        }
        try {
            double link = Uploader.speedTest(host, Uploader.PORT);
            JSONObject detail = Report.put(Report.put(new JSONObject(), "megabytes_per_second", link),
                    "megabytes_sent", Uploader.SPEED_CHUNKS * (double) Uploader.SPEED_CHUNK_BYTES / 1e6);
            record("link_speed", "PASS", "", detail, String.format(Locale.US, "Link to the computer: %.1f MB/s", link));
            return link;
        } catch (Exception e) {
            record("link_speed", "FAIL", e.getMessage() == null ? e.toString() : e.getMessage(), null, "Link speed");
            return Double.NaN;
        }
    }

    /** Times JPEG and deflate on the tracking run's images and remembers whether deflating grey frames pays. */
    private void compression(double link, int fps) {
        List<byte[]> copy;
        synchronized (samples) {
            copy = new ArrayList<>(samples);
        }
        if (copy.isEmpty()) {
            record("grey_compression", "SKIPPED", "no camera images during the tracking run", null, "Grey compression");
            return;
        }
        JSONObject c = FrameWriter.compressionCheck(copy, sampleWidth, sampleHeight);
        double ratio = c.optDouble("deflate_ratio"), deflateMs = c.optDouble("deflate_ms_median"), jpegMs = c.optDouble("jpeg_ms_median");
        boolean pays = !Double.isNaN(link) && FrameWriter.deflatePays(ratio, deflateMs, jpegMs, 1000.0 / fps, link,
                sampleWidth * sampleHeight, (int) c.optDouble("jpeg_bytes_median"));
        Report.put(Report.put(Report.put(c, "frame_rate", fps), "link_megabytes_per_second", link), "deflate_pays", pays);
        prefs().edit().putBoolean("deflate", pays).apply();
        record("grey_compression", "PASS", "", c, String.format(Locale.US, "Grey deflate: %.0f%% of raw in %.1f ms, JPEG %.1f ms: %s",
                100 * ratio, deflateMs, jpegMs, pays ? "used from now on" : "not worth it, grey goes raw"));
    }

    private void saveAndSend() {
        String json = report.json();
        File file = new File(getExternalFilesDir(null), "check_" + System.currentTimeMillis() + ".json");
        String saved;
        try (FileOutputStream out = new FileOutputStream(file)) {
            out.write(json.getBytes(StandardCharsets.UTF_8));
            saved = "Report saved on the phone.";
        } catch (Exception e) {
            saved = "Report not saved: " + e.getMessage();
        }
        String sent = "";
        if (!host().isEmpty()) {
            try {
                Uploader.sendReport(host(), Uploader.PORT, json);
                sent = " Sent to the computer.";
            } catch (Exception e) {
                sent = " Not sent: " + e.getMessage();
            }
        }
        String message = "Checks done. " + saved + sent;
        runOnUiThread(() -> {
            busy = false;
            walkButton.setEnabled(true);
            imuButton.setEnabled(true);
            checkButton.setEnabled(true);
            checkButton.setText("Run all checks again");
            status.setText(message);
        });
    }

    // ---- Lifecycle -------------------------------------------------------------------------------

    @Override
    protected void onResume() {
        super.onResume();
        resumed = true;
        if (ensureSession()) rig.open();
        surface.onResume();
        startUploader();  // delivers sessions left from an earlier run
    }

    @Override
    protected void onPause() {
        super.onPause();
        resumed = false;
        if (current != null) stop("paused", "Stopped because the app left the screen.");
        surface.onPause();
        if (rig != null) rig.close();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (uploader != null) uploader.stop();
        if (rig != null) rig.quit();
        if (session != null) session.close();
    }
}
