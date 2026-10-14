package org.fyld.phonecheck;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.media.Image;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.text.InputType;
import android.text.Html;
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
import com.google.ar.core.exceptions.NotYetAvailableException;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/**
 * One button runs every check in order: ARCore set-up, a 15 s tracking run, a 20 s stream to the host,
 * then the report is saved on the phone and sent to the host. A second button streams phone session v1
 * to the host until pressed again. The camera image fills the screen behind.
 */
public class CheckActivity extends Activity implements GLSurfaceView.Renderer {
    private enum Mode { IDLE, TRACKING, STREAM }

    static final long TRACKING_MS = 15000, STREAM_MS = 20000;
    static final int PORT = 8765;
    private static final int GREEN = 0xFF2E9E4F, RED = 0xFFD64545, GREY = 0xFF8A8A8A;

    private final Handler main = new Handler(Looper.getMainLooper());
    private final CameraPreview preview = new CameraPreview();
    private final List<Object[]> setupChecks = new ArrayList<>();  // {name, status, reason, detail, text}, kept between runs
    private Report report = new Report();
    private GLSurfaceView surface;
    private TextView status, live;
    private LinearLayout results;
    private EditText hostField;
    private Button runButton, streamButton;
    private Session session;
    private boolean installRequested, depthEnabled, running, streamOnly;
    private volatile boolean textureSet, stopRequested;
    private int texture = -1, viewWidth, viewHeight;
    private volatile Mode mode = Mode.IDLE;
    private long modeStart, lastLive;
    private TrackingStats stats;
    private HostStream stream;
    private FrameCapture capture;

    // ---- Screen ----------------------------------------------------------------------------------

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        surface = new GLSurfaceView(this);
        surface.setPreserveEGLContextOnPause(true);
        surface.setEGLContextClientVersion(2);
        surface.setRenderer(this);
        surface.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);

        LinearLayout top = panel();
        top.addView(text("FYLD phone check", 22, Color.WHITE, true));
        Button notice = new Button(this);
        notice.setText("ARCore and privacy notice");
        notice.setOnClickListener(v -> showArCoreNotice());
        top.addView(notice);
        status = text("Press Run all checks. Keep the phone upright.", 18, Color.WHITE, false);
        live = text("", 15, 0xFFCFCFCF, false);
        top.addView(status);
        top.addView(live);

        LinearLayout bottom = panel();
        results = new LinearLayout(this);
        results.setOrientation(LinearLayout.VERTICAL);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(results);
        bottom.addView(scroll, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(220)));
        hostField = new EditText(this);
        hostField.setHint("Computer address, e.g. 192.168.68.123");
        hostField.setHintTextColor(GREY);
        hostField.setTextColor(Color.WHITE);
        hostField.setTextSize(TypedValue.COMPLEX_UNIT_SP, 17);
        hostField.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        hostField.setText(prefs().getString("host", ""));
        bottom.addView(hostField);
        runButton = new Button(this);
        runButton.setText("Run all checks");
        runButton.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
        runButton.setOnClickListener(v -> runAll());
        bottom.addView(runButton, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(64)));
        streamButton = new Button(this);
        streamButton.setText("Stream to computer");
        streamButton.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
        streamButton.setOnClickListener(v -> toggleStream());
        bottom.addView(streamButton, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(64)));

        LinearLayout overlay = new LinearLayout(this);
        overlay.setOrientation(LinearLayout.VERTICAL);
        overlay.addView(top);
        overlay.addView(new FrameLayout(this), new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        overlay.addView(bottom);
        FrameLayout root = new FrameLayout(this);
        root.addView(surface);
        root.addView(overlay);
        setContentView(root);
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

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private SharedPreferences prefs() {
        return getSharedPreferences("phonecheck", MODE_PRIVATE);
    }

    private void setStatus(String value) {
        runOnUiThread(() -> status.setText(value));
    }

    /** Records a check in the report and shows it as a coloured row. */
    private void record(String name, String result, String reason, JSONObject detail, String summary) {
        report.check(name, result, reason, detail);
        String mark = result.equals("PASS") ? "PASS" : result.equals("FAIL") ? "FAIL" : "SKIP";
        int colour = result.equals("PASS") ? GREEN : result.equals("FAIL") ? RED : GREY;
        String line = summary + (reason.isEmpty() ? "" : " (" + reason + ")");
        runOnUiThread(() -> {
            LinearLayout row = new LinearLayout(this);
            row.setGravity(Gravity.CENTER_VERTICAL);
            TextView badge = text(mark, 14, Color.WHITE, true);
            badge.setBackgroundColor(colour);
            badge.setPadding(dp(8), dp(2), dp(8), dp(2));
            row.addView(badge);
            TextView label = text("  " + line, 15, Color.WHITE, false);
            row.addView(label);
            row.setPadding(0, dp(4), 0, dp(4));
            results.addView(row);
        });
    }

    // ---- Run all ---------------------------------------------------------------------------------

    private void runAll() {
        if (running) return;
        running = true;
        streamOnly = false;
        runButton.setEnabled(false);
        streamButton.setEnabled(false);
        prefs().edit().putString("host", hostField.getText().toString().trim()).apply();
        report = new Report();
        results.removeAllViews();
        for (Object[] c : setupChecks) record((String) c[0], (String) c[1], (String) c[2], (JSONObject) c[3], (String) c[4]);
        if (session != null) {
            startMode(Mode.TRACKING);
        } else {
            setUpArCore();
        }
    }

    /** Starts an open-ended stream (setting up ARCore first if needed), or asks a running one to stop. */
    private void toggleStream() {
        if (running) {
            if (streamOnly) stopRequested = true;
            return;
        }
        String host = hostField.getText().toString().trim();
        if (host.isEmpty()) {
            setStatus("Type the computer address first (the receiver prints it).");
            return;
        }
        prefs().edit().putString("host", host).apply();
        running = true;
        streamOnly = true;
        runButton.setEnabled(false);
        streamButton.setText("Stop streaming");
        if (session != null) {
            startMode(Mode.STREAM);
        } else {
            setUpArCore();
        }
    }

    private void finishRun(String message) {
        running = false;
        mode = Mode.IDLE;
        runOnUiThread(() -> {
            runButton.setEnabled(true);
            runButton.setText("Run all checks again");
            streamButton.setEnabled(true);
            streamButton.setText("Stream to computer");
            live.setText("");
        });
        setStatus(message);
    }

    private void setup(String name, String result, String reason, JSONObject detail, String summary) {
        setupChecks.add(new Object[]{name, result, reason, detail == null ? new JSONObject() : detail, summary});
        record(name, result, reason, detail, summary);
    }

    // ---- Step 1: ARCore set-up -------------------------------------------------------------------

    private void setUpArCore() {
        setStatus("Checking ARCore...");
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, 1);
            return;
        }
        ArCoreApk.Availability availability = ArCoreApk.getInstance().checkAvailability(this);
        if (availability.isTransient()) {
            main.postDelayed(this::setUpArCore, 300);
            return;
        }
        JSONObject detail = Report.put(new JSONObject(), "availability", availability.name());
        if (availability == ArCoreApk.Availability.UNSUPPORTED_DEVICE_NOT_CAPABLE) {
            setup("arcore_available", "FAIL", "Google lists this phone as not ARCore capable", detail, "ARCore available");
            finishRun("ARCore cannot run on this phone.");
            return;
        }
        if (availability != ArCoreApk.Availability.SUPPORTED_INSTALLED) {
            try {
                if (ArCoreApk.getInstance().requestInstall(this, !installRequested) == ArCoreApk.InstallStatus.INSTALL_REQUESTED) {
                    installRequested = true;
                    running = false;
                    runOnUiThread(() -> runButton.setEnabled(true));
                    setStatus("Install Google Play Services for AR, then press Run all checks again.");
                    return;
                }
            } catch (Exception e) {
                setup("arcore_available", "FAIL", "install failed: " + e.getMessage(), detail, "ARCore available");
                finishRun("ARCore could not be installed.");
                return;
            }
        }
        setup("arcore_available", "PASS", "", detail, "ARCore installed");
        try {
            session = new Session(this);
        } catch (Exception e) {
            setup("arcore_session", "FAIL", e.getClass().getSimpleName() + ": " + e.getMessage(), null, "ARCore session");
            finishRun("ARCore would not start.");
            return;
        }
        setup("arcore_session", "PASS", "", null, "ARCore session started");
        boolean raw = session.isDepthModeSupported(Config.DepthMode.RAW_DEPTH_ONLY);
        boolean automatic = session.isDepthModeSupported(Config.DepthMode.AUTOMATIC);
        depthEnabled = raw || automatic;
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
            Report.put(entry, "depth_sensor", c.getDepthSensorUsage().name());
            listed.put(entry);
        }
        setup("camera_configs", configs.isEmpty() ? "FAIL" : "PASS", configs.isEmpty() ? "none offered" : "",
                Report.put(new JSONObject(), "configs", listed), configs.size() + " camera settings offered");
        Config config = new Config(session);
        config.setUpdateMode(Config.UpdateMode.LATEST_CAMERA_IMAGE);
        config.setDepthMode(raw ? Config.DepthMode.RAW_DEPTH_ONLY : automatic ? Config.DepthMode.AUTOMATIC : Config.DepthMode.DISABLED);
        session.configure(config);
        try {
            session.resume();
        } catch (Exception e) {
            setup("arcore_resume", "FAIL", e.toString(), null, "Camera start");
            finishRun("The camera would not start.");
            return;
        }
        textureSet = false;
        startMode(streamOnly ? Mode.STREAM : Mode.TRACKING);
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] permissions, int[] grants) {
        if (grants.length > 0 && grants[0] == PackageManager.PERMISSION_GRANTED) {
            setUpArCore();
        } else {
            record("camera_permission", "FAIL", "camera permission refused", null, "Camera permission");
            finishRun("The camera permission is needed.");
        }
    }

    // ---- Steps 2 and 3: tracking run and stream ----------------------------------------------------

    private void startMode(Mode next) {
        if (next == Mode.STREAM) {
            stream = new HostStream();
            stream.start(hostField.getText().toString().trim(), PORT);
            capture = new FrameCapture(session, depthEnabled);
            stopRequested = false;
        } else {
            stats = new TrackingStats();
        }
        modeStart = SystemClock.elapsedRealtime();
        mode = next;
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

    @Override
    public void onDrawFrame(GL10 unused) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT | GLES20.GL_DEPTH_BUFFER_BIT);
        Session s = session;
        if (s == null || texture < 0) return;
        if (!textureSet) {
            s.setCameraTextureName(texture);
            s.setDisplayGeometry(getWindowManager().getDefaultDisplay().getRotation(), viewWidth, viewHeight);
            textureSet = true;
        }
        Frame frame;
        long start = System.nanoTime();
        try {
            frame = s.update();
        } catch (Exception e) {
            return;
        }
        double updateMs = (System.nanoTime() - start) / 1e6;
        preview.draw(frame);
        long elapsed = SystemClock.elapsedRealtime() - modeStart;
        Mode m = mode;
        if (m == Mode.TRACKING) {
            stats.add(frame, updateMs, depthEnabled);
            showLive(frame, "Tracking: walk slowly, point at textured things", TRACKING_MS - elapsed,
                    String.format("%d points, depth %.0f%% valid, %.1f m walked, %.1f ms per update",
                            stats.lastPoints(), 100 * stats.lastDepthValid(), stats.pathMetres(), updateMs));
            if (elapsed >= TRACKING_MS) finishTracking(elapsed / 1000.0);
        } else if (m == Mode.STREAM) {
            if (capture.isNew(frame) && stream.hasRoom()) {
                try (Image image = frame.acquireCameraImage()) {
                    stream.offer(capture.capture(frame), image);
                } catch (NotYetAvailableException e) {
                    // the CPU image is not ready on every frame
                }
            }
            String numbers = String.format("%d frames sent, %d received, %d with depth, %d keyframes%s", stream.offered(),
                    stream.acked(), capture.depthFrames(), capture.anchorCount(), stream.error() == null ? "" : "\n" + stream.error());
            if (streamOnly) {
                showLive(frame, "Streaming until you press Stop", 0, numbers);
                if (stopRequested || stream.error() != null) finishStream();
            } else {
                showLive(frame, "Streaming to the computer: keep moving", STREAM_MS - elapsed, numbers);
                if (elapsed >= STREAM_MS) finishStream();
            }
        }
    }

    private void showLive(Frame frame, String step, long remainingMs, String numbers) {
        long now = SystemClock.elapsedRealtime();
        if (now - lastLive < 200) return;
        lastLive = now;
        Camera camera = frame.getCamera();
        String state = camera.getTrackingState() == TrackingState.TRACKING ? "Tracking OK"
                : "Not tracking: " + camera.getTrackingFailureReason().name().toLowerCase().replace('_', ' ');
        String head = String.format("%s - %d s left", step, Math.max(0, (remainingMs + 999) / 1000));
        runOnUiThread(() -> {
            status.setText(head);
            live.setText(state + "\n" + numbers);
        });
    }

    private void finishTracking(double seconds) {
        mode = Mode.IDLE;
        JSONObject summary = stats.summary(seconds);
        double fraction = stats.trackingFraction();
        record("arcore_tracking", fraction >= 0.5 ? "PASS" : "FAIL", fraction >= 0.5 ? "" : "tracking under half the time", summary,
                String.format("Tracked %.0f%% of %d frames, %.1f m walked", 100 * fraction, stats.frames(), stats.pathMetres()));
        record("tracked_points", stats.maxPoints() > 0 ? "PASS" : "FAIL", stats.maxPoints() > 0 ? "" : "no points", null,
                "Up to " + stats.maxPoints() + " tracked points per frame");
        if (!depthEnabled) {
            record("raw_depth_frames", "SKIPPED", "depth not supported", null, "Depth images");
        } else {
            record("raw_depth_frames", stats.depthFrames() > 0 ? "PASS" : "FAIL", stats.depthFrames() > 0 ? "" : "none received", null,
                    stats.depthFrames() + " depth images");
        }
        if (hostField.getText().toString().trim().isEmpty()) {
            record("host_stream", "SKIPPED", "no computer address entered", null, "Stream to computer");
            saveAndSend();
        } else {
            startMode(Mode.STREAM);
        }
    }

    /** Runs on the GL thread, so ARCore's anchors are released there. */
    private void finishStream() {
        mode = Mode.IDLE;
        capture.close();
        setStatus("Finishing the stream...");
        HostStream finished = stream;
        if (streamOnly) {
            int depthFrames = capture.depthFrames();
            new Thread(() -> {
                try {
                    JSONObject summary = finished.stop();
                    finishRun(String.format("Stream ended: %d frames received, %.1f per second, %d with depth.%s", finished.acked(),
                            summary.optDouble("acknowledged_per_second"), depthFrames,
                            finished.error() == null ? "" : " Error: " + finished.error()));
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }).start();
            return;
        }
        new Thread(() -> {
            try {
                JSONObject summary = finished.stop();
                boolean ok = finished.acked() > 0;
                record("host_stream", ok ? "PASS" : "FAIL", ok ? "" : (finished.error() != null ? finished.error() : "nothing received"), summary,
                        String.format("Stream: %.1f frames/s received, round trip %.0f ms",
                                summary.optDouble("acknowledged_per_second"), summary.optDouble("round_trip_ms_median")));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            saveAndSend();  // only after the stream check is in the report
        }).start();
    }

    // ---- Step 4: save and send the report --------------------------------------------------------

    private void saveAndSend() {
        String json = report.json();
        File file = new File(getExternalFilesDir(null), "phonecheck_" + System.currentTimeMillis() + ".json");
        String saved;
        try (FileOutputStream out = new FileOutputStream(file)) {
            out.write(json.getBytes(StandardCharsets.UTF_8));
            saved = "Report saved on the phone.";
        } catch (Exception e) {
            saved = "Report not saved: " + e.getMessage();
        }
        String host = hostField.getText().toString().trim();
        String savedMessage = saved;
        if (host.isEmpty()) {
            finishRun("Done. " + savedMessage);
            return;
        }
        new Thread(() -> {
            String sent;
            try (Socket socket = new Socket()) {
                socket.connect(new InetSocketAddress(host, PORT), 3000);
                DataOutputStream out = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream()));
                HostStream.send(out, Report.put(Report.put(new JSONObject(), "type", "report"), "schema", 1), json.getBytes(StandardCharsets.UTF_8));
                sent = "Sent to the computer.";
            } catch (Exception e) {
                sent = "Not sent: " + e.getMessage();
            }
            finishRun("Done. " + savedMessage + " " + sent);
        }).start();
    }

    // ---- Lifecycle -------------------------------------------------------------------------------

    @Override
    protected void onResume() {
        super.onResume();
        if (session != null) {
            try {
                session.resume();
            } catch (Exception e) {
                setStatus("Camera restart failed: " + e.getMessage());
            }
        }
        surface.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        surface.onPause();
        if (session != null) session.pause();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (session != null) session.close();
    }
}
