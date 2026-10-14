package org.fyld.rawrecorder;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.media.Image;
import android.opengl.GLES11Ext;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.text.InputType;
import android.util.TypedValue;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.google.ar.core.ArCoreApk;
import com.google.ar.core.Camera;
import com.google.ar.core.CameraIntrinsics;
import com.google.ar.core.Config;
import com.google.ar.core.Frame;
import com.google.ar.core.Pose;
import com.google.ar.core.Session;
import com.google.ar.core.TrackingState;

import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.EnumSet;
import java.util.Locale;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/**
 * Records a walk (camera frames, gyroscope, accelerometer and ARCore poses on the phone's elapsedRealtime clock)
 * or the motion sensors alone, then sends the recording to the computer. Folder layout: experiments/open_vio/README.md.
 */
public class RecorderActivity extends Activity implements GLSurfaceView.Renderer, SharedCameraRig.Listener {
    static final String CAM0_HEADER = "t_ns,exposure_ns,frame_duration_ns,rolling_shutter_skew_ns,focus_distance_dpt,iso,ois_mode";
    static final String ARCORE_HEADER = "t_ns,camera_t_ns,tracking,tx,ty,tz,qx,qy,qz,qw,dev_tx,dev_ty,dev_tz,dev_qx,dev_qy,dev_qz,dev_qw,failure";

    /** Everything one recording writes to; callbacks on other threads write only while it is the current one. */
    private static final class Recording {
        final File dir;
        final boolean walk;
        final JSONObject meta;
        final long startMs = SystemClock.elapsedRealtime();
        FrameWriter frames;
        CsvLog cam0, arcore;

        Recording(File dir, boolean walk, JSONObject meta) {
            this.dir = dir;
            this.walk = walk;
            this.meta = meta;
        }
    }

    private final Handler main = new Handler(Looper.getMainLooper());
    private final byte[] previewLuma = new byte[SharedCameraRig.WIDTH * SharedCameraRig.HEIGHT];
    private final int[] previewPixels = new int[SharedCameraRig.WIDTH * SharedCameraRig.HEIGHT];
    private GLSurfaceView gl;
    private ImageView preview;
    private TextView status, live;
    private EditText hostField;
    private Button walkButton, imuButton, sendButton;
    private Session session;
    private SharedCameraRig rig;
    private ImuLogger imu;
    private boolean installRequested, busy, resumed;
    private volatile Recording current;
    private volatile String trackingText = "ARCore starting";
    private volatile CameraIntrinsics intrinsics;
    private int texture = -1;
    private boolean textureSet;
    private long lastFrameT, lastPreviewMs;

    // ---- Screen ----------------------------------------------------------------------------------

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        imu = new ImuLogger(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.BLACK);
        root.setPadding(dp(12), dp(12), dp(12), dp(12));
        root.addView(label("FYLD raw recorder", 22));
        preview = new ImageView(this);
        preview.setRotation(90);  // the rear sensor is mounted landscape; the screen is portrait
        root.addView(preview, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1));
        gl = new GLSurfaceView(this);  // ARCore needs a GL context; the view itself shows nothing
        gl.setPreserveEGLContextOnPause(true);
        gl.setEGLContextClientVersion(2);
        gl.setRenderer(this);
        root.addView(gl, new LinearLayout.LayoutParams(dp(2), dp(2)));
        status = label("Starting the camera...", 17);
        live = label("", 15);
        root.addView(status);
        root.addView(live);
        hostField = new EditText(this);
        hostField.setHint("Computer address, e.g. 192.168.68.123");
        hostField.setHintTextColor(Color.GRAY);
        hostField.setTextColor(Color.WHITE);
        hostField.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        hostField.setText(getPreferences(MODE_PRIVATE).getString("host", ""));
        root.addView(hostField);
        walkButton = button("Record walk", v -> toggle(true));
        imuButton = button("Record motion sensors only (phone at rest)", v -> toggle(false));
        sendButton = button("Send last recording to computer", v -> sendLast());
        root.addView(walkButton);
        root.addView(imuButton);
        root.addView(sendButton);
        setContentView(root);
        main.post(this::tick);
    }

    private TextView label(String text, int sp) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        t.setTextColor(Color.WHITE);
        return t;
    }

    private Button button(String text, android.view.View.OnClickListener action) {
        Button b = new Button(this);
        b.setText(text);
        b.setAllCaps(false);
        b.setOnClickListener(action);
        return b;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void setStatus(String text) {
        runOnUiThread(() -> status.setText(text));
    }

    /** Four times a second: tracking state and what the current recording has written. */
    private void tick() {
        Recording r = current;
        String text = trackingText;
        if (r != null) {
            double seconds = (SystemClock.elapsedRealtime() - r.startMs) / 1000.0;
            text += String.format(Locale.US, "\nRecording %s: %.0f s, gyroscope %.0f Hz, accelerometer %.0f Hz",
                    r.walk ? "walk" : "motion sensors", seconds, imu.gyroSamples() / seconds, imu.accelSamples() / seconds);
            if (r.walk) text += String.format(Locale.US, "\n%d frames saved, %d dropped, %d ARCore poses",
                    r.frames.written(), r.frames.dropped(), r.arcore.lines());
        }
        live.setText(text);
        main.postDelayed(this::tick, 250);
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
            setStatus("ARCore is not available: " + e.getMessage());
            return false;
        }
        Config config = new Config(session);
        config.setFocusMode(Config.FocusMode.FIXED);
        config.setUpdateMode(Config.UpdateMode.LATEST_CAMERA_IMAGE);
        config.setDepthMode(Config.DepthMode.DISABLED);
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

    @Override
    public void onImage(Image image) {
        Recording r = current;
        if (r != null && r.walk) r.frames.offer(image);
        long now = SystemClock.elapsedRealtime();
        if (now - lastPreviewMs < 200) return;
        lastPreviewMs = now;
        FrameWriter.copyLuma(image, previewLuma, SharedCameraRig.WIDTH, SharedCameraRig.HEIGHT);
        for (int i = 0; i < previewLuma.length; i++) {
            int y = previewLuma[i] & 0xFF;
            previewPixels[i] = 0xFF000000 | (y << 16) | (y << 8) | y;
        }
        Bitmap bitmap = Bitmap.createBitmap(previewPixels, SharedCameraRig.WIDTH, SharedCameraRig.HEIGHT, Bitmap.Config.ARGB_8888);
        runOnUiThread(() -> preview.setImageBitmap(bitmap));
    }

    @Override
    public void onCapture(TotalCaptureResult result) {
        Recording r = current;
        if (r == null || !r.walk) return;
        r.cam0.line(value(result.get(CaptureResult.SENSOR_TIMESTAMP)) + "," + value(result.get(CaptureResult.SENSOR_EXPOSURE_TIME))
                + "," + value(result.get(CaptureResult.SENSOR_FRAME_DURATION)) + "," + value(result.get(CaptureResult.SENSOR_ROLLING_SHUTTER_SKEW))
                + "," + value(result.get(CaptureResult.LENS_FOCUS_DISTANCE)) + "," + value(result.get(CaptureResult.SENSOR_SENSITIVITY))
                + "," + value(result.get(CaptureResult.LENS_OPTICAL_STABILIZATION_MODE)));
    }

    /** A capture value the phone did not report is written as -1. */
    private static String value(Object v) {
        return v == null ? "-1" : v.toString();
    }

    @Override
    public void onCameraError(String message) {
        setStatus(message);
    }

    @Override
    public void onSurfaceCreated(GL10 unused, EGLConfig config) {
        int[] names = new int[1];
        GLES20.glGenTextures(1, names, 0);
        texture = names[0];
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, texture);
        textureSet = false;
    }

    @Override
    public void onSurfaceChanged(GL10 unused, int width, int height) {
        textureSet = false;
    }

    /** GL thread: one ARCore update per drawn frame; a new camera image adds one row to arcore.csv. */
    @Override
    public void onDrawFrame(GL10 unused) {
        SharedCameraRig r0 = rig;
        if (r0 == null || !r0.arActive() || texture < 0) return;
        if (!textureSet) {
            session.setCameraTextureName(texture);
            textureSet = true;
        }
        Frame frame;
        try {
            frame = session.update();
        } catch (Exception e) {
            return;
        }
        Camera camera = frame.getCamera();
        boolean tracking = camera.getTrackingState() == TrackingState.TRACKING;
        trackingText = tracking ? "ARCore: tracking" : "ARCore: not tracking (" + camera.getTrackingFailureReason().name().toLowerCase(Locale.US) + ")";
        if (tracking && intrinsics == null) intrinsics = camera.getImageIntrinsics();
        Recording r = current;
        if (r == null || !r.walk || frame.getTimestamp() == lastFrameT) return;
        lastFrameT = frame.getTimestamp();
        r.arcore.line(frame.getTimestamp() + "," + frame.getAndroidCameraTimestamp() + "," + camera.getTrackingState().name()
                + "," + pose(camera.getPose()) + "," + pose(frame.getAndroidSensorPose()) + "," + camera.getTrackingFailureReason().name());
    }

    private static String pose(Pose p) {
        return p.tx() + "," + p.ty() + "," + p.tz() + "," + p.qx() + "," + p.qy() + "," + p.qz() + "," + p.qw();
    }

    // ---- Recording -------------------------------------------------------------------------------

    private void toggle(boolean walk) {
        if (busy) return;
        if (current != null) {
            stop();
            return;
        }
        if (walk && (rig == null || !rig.arActive())) {
            setStatus("Wait for the camera and ARCore to start.");
            return;
        }
        try {
            String name = "rec_" + new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date()) + (walk ? "_walk" : "_imu");
            File dir = new File(getExternalFilesDir(null), "recordings/" + name);
            if (!dir.mkdirs()) throw new IllegalStateException("could not create " + dir);
            if (!walk && rig != null) rig.close();  // hours at rest: no camera, no ARCore, less heat
            JSONObject meta = new JSONObject().put("schema", 1).put("kind", walk ? "walk" : "imu_only")
                    .put("app", "org.fyld.rawrecorder 0.1").put("device", RecordingMeta.device(this))
                    .put("imu", new JSONObject().put("gyro", ImuLogger.describe(imu.gyro)).put("accel", ImuLogger.describe(imu.accel)));
            if (walk) {
                meta.put("camera", RecordingMeta.camera(this, rig.cameraId))
                        .put("arcore", RecordingMeta.arcore(session.getCameraConfig(), intrinsics));
            }
            Recording r = new Recording(dir, walk, meta);
            if (walk) {
                File cam0 = new File(dir, "cam0");
                if (!cam0.mkdirs()) throw new IllegalStateException("could not create " + cam0);
                r.frames = new FrameWriter(cam0, SharedCameraRig.WIDTH, SharedCameraRig.HEIGHT);
                r.cam0 = new CsvLog(new File(dir, "cam0.csv"), CAM0_HEADER);
                r.arcore = new CsvLog(new File(dir, "arcore.csv"), ARCORE_HEADER);
            }
            meta.put("clock", new JSONObject().put("start", RecordingMeta.clock()));
            imu.start(dir);
            current = r;
            (walk ? walkButton : imuButton).setText("Stop recording");
            (walk ? imuButton : walkButton).setEnabled(false);
            setStatus(walk ? "Recording: walk slowly, point at textured things, return to the start."
                    : "Recording motion sensors: leave the phone still on a table.");
        } catch (Exception e) {
            setStatus("Could not start: " + e.getMessage());
        }
    }

    private void stop() {
        Recording r = current;
        current = null;
        busy = true;
        setStatus("Finishing the recording...");
        new Thread(() -> {
            String result;
            try {
                imu.stop();
                JSONObject counts = new JSONObject().put("gyro_samples", imu.gyroSamples()).put("accel_samples", imu.accelSamples());
                if (r.walk) {
                    r.frames.finish();
                    r.cam0.close();
                    r.arcore.close();
                    counts.put("frames_offered", r.frames.offered()).put("frames_saved", r.frames.written())
                            .put("frames_dropped", r.frames.dropped()).put("captures", r.cam0.lines()).put("arcore_rows", r.arcore.lines());
                    if (r.frames.error() != null) counts.put("frame_write_error", r.frames.error());
                }
                r.meta.getJSONObject("clock").put("end", RecordingMeta.clock());
                r.meta.put("counts", counts);
                try (FileOutputStream out = new FileOutputStream(new File(r.dir, "meta.json"))) {
                    out.write(r.meta.toString(2).getBytes(StandardCharsets.UTF_8));
                }
                getPreferences(MODE_PRIVATE).edit().putString("last", r.dir.getAbsolutePath()).apply();
                result = "Saved " + r.dir.getName() + ". Press Send to copy it to the computer.";
            } catch (Exception e) {
                result = "Recording not finished cleanly: " + e.getMessage();
            }
            String message = result;
            runOnUiThread(() -> {
                busy = false;
                walkButton.setText("Record walk");
                imuButton.setText("Record motion sensors only (phone at rest)");
                walkButton.setEnabled(true);
                imuButton.setEnabled(true);
                if (!r.walk && rig != null && resumed) rig.open();
                status.setText(message);
            });
        }).start();
    }

    private void sendLast() {
        String last = getPreferences(MODE_PRIVATE).getString("last", "");
        String host = hostField.getText().toString().trim();
        if (last.isEmpty() || host.isEmpty() || busy || current != null) {
            setStatus(last.isEmpty() ? "Nothing recorded yet." : host.isEmpty() ? "Type the computer address first." : "Stop recording first.");
            return;
        }
        getPreferences(MODE_PRIVATE).edit().putString("host", host).apply();
        busy = true;
        sendButton.setEnabled(false);
        new Thread(() -> {
            String result = Uploader.send(new File(last), host, this::setStatus);
            runOnUiThread(() -> {
                busy = false;
                sendButton.setEnabled(true);
                status.setText(result);
            });
        }).start();
    }

    // ---- Lifecycle -------------------------------------------------------------------------------

    @Override
    protected void onResume() {
        super.onResume();
        resumed = true;
        if (ensureSession() && current == null) rig.open();
        gl.onResume();
    }

    @Override
    protected void onPause() {
        super.onPause();
        resumed = false;
        if (current != null) stop();
        gl.onPause();
        if (rig != null) rig.close();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (rig != null) rig.quit();
        if (session != null) session.close();
    }
}
