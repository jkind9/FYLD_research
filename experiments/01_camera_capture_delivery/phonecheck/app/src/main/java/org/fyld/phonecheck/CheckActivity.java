package org.fyld.phonecheck;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.media.Image;
import android.opengl.GLES11Ext;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import com.google.ar.core.ArCoreApk;
import com.google.ar.core.Camera;
import com.google.ar.core.CameraConfig;
import com.google.ar.core.CameraConfigFilter;
import com.google.ar.core.CameraIntrinsics;
import com.google.ar.core.Config;
import com.google.ar.core.Frame;
import com.google.ar.core.Pose;
import com.google.ar.core.Session;
import com.google.ar.core.TrackingState;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/**
 * Runs the Redmi checks: (1) ARCore availability, session, depth support and camera configurations;
 * (2) a 15 s tracking run; (3) a 20 s stream of camera frames to the host receiver; (4) save and send the report.
 */
public class CheckActivity extends Activity implements GLSurfaceView.Renderer {
    private enum Mode { IDLE, TRACKING, STREAM }

    static final long TRACKING_MS = 15000, STREAM_MS = 20000;
    static final int PORT = 8765;

    private final Handler main = new Handler(Looper.getMainLooper());
    private final Report report = new Report();
    private GLSurfaceView surface;
    private TextView log;
    private EditText hostField;
    private Session session;
    private boolean installRequested, depthEnabled;
    private volatile boolean textureSet;
    private int texture = -1, viewWidth, viewHeight, seq;
    private volatile Mode mode = Mode.IDLE;
    private long modeStart;
    private TrackingStats stats;
    private HostStream stream;

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout controls = new LinearLayout(this);
        controls.setOrientation(LinearLayout.VERTICAL);
        hostField = new EditText(this);
        hostField.setHint("host IP, e.g. 192.168.1.20");
        controls.addView(hostField);
        controls.addView(button("1. ARCore check", this::runArCoreCheck));
        controls.addView(button("2. Tracking run (15 s, move the phone)", () -> startMode(Mode.TRACKING)));
        controls.addView(button("3. Stream to host (20 s)", () -> startMode(Mode.STREAM)));
        controls.addView(button("4. Save and send report", this::saveReport));
        log = new TextView(this);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(log);
        controls.addView(scroll);
        surface = new GLSurfaceView(this);
        surface.setPreserveEGLContextOnPause(true);
        surface.setEGLContextClientVersion(2);
        surface.setRenderer(this);
        surface.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
        LinearLayout root = new LinearLayout(this);
        root.addView(controls, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1));
        root.addView(surface, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1));
        setContentView(root);
        say(report.json().split("\"checks\"")[0]);
    }

    private Button button(String label, Runnable action) {
        Button b = new Button(this);
        b.setText(label);
        b.setOnClickListener(v -> action.run());
        return b;
    }

    private void say(String text) {
        runOnUiThread(() -> log.append(text + "\n"));
    }

    // ---- 1. ARCore check -------------------------------------------------------------------------

    private void runArCoreCheck() {
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, 1);
            return;
        }
        if (session != null) {
            say("ARCore session already open; run 2 or 3.");
            return;
        }
        ArCoreApk.Availability availability = ArCoreApk.getInstance().checkAvailability(this);
        if (availability.isTransient()) {
            main.postDelayed(this::runArCoreCheck, 300);
            return;
        }
        JSONObject detail = Report.put(new JSONObject(), "availability", availability.name());
        if (availability == ArCoreApk.Availability.UNSUPPORTED_DEVICE_NOT_CAPABLE) {
            report.check("arcore_available", "FAIL", "Google lists this device as not ARCore capable", detail);
            say("ARCore: device not capable.");
            return;
        }
        if (availability != ArCoreApk.Availability.SUPPORTED_INSTALLED) {
            try {
                if (ArCoreApk.getInstance().requestInstall(this, !installRequested) == ArCoreApk.InstallStatus.INSTALL_REQUESTED) {
                    installRequested = true;
                    say("Install Google Play Services for AR when asked, then press 1 again.");
                    return;
                }
            } catch (Exception e) {
                report.check("arcore_available", "FAIL", "install failed: " + e, detail);
                say("ARCore install failed: " + e);
                return;
            }
        }
        report.check("arcore_available", "PASS", "", detail);
        try {
            session = new Session(this);
        } catch (Exception e) {
            report.check("arcore_session", "FAIL", e.getClass().getSimpleName() + ": " + e.getMessage(), null);
            say("ARCore session failed: " + e);
            return;
        }
        report.check("arcore_session", "PASS", "", null);
        boolean raw = session.isDepthModeSupported(Config.DepthMode.RAW_DEPTH_ONLY);
        boolean automatic = session.isDepthModeSupported(Config.DepthMode.AUTOMATIC);
        depthEnabled = raw || automatic;
        JSONObject depth = Report.put(Report.put(new JSONObject(), "raw_depth_only", raw), "automatic", automatic);
        report.check("depth_supported", depthEnabled ? "PASS" : "SKIPPED", depthEnabled ? "" : "ARCore reports no depth mode on this device", depth);
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
        report.check("camera_configs", configs.isEmpty() ? "FAIL" : "PASS", configs.isEmpty() ? "no camera configuration offered" : "",
                Report.put(new JSONObject(), "configs", listed));
        Config config = new Config(session);
        config.setUpdateMode(Config.UpdateMode.LATEST_CAMERA_IMAGE);
        config.setDepthMode(raw ? Config.DepthMode.RAW_DEPTH_ONLY : automatic ? Config.DepthMode.AUTOMATIC : Config.DepthMode.DISABLED);
        session.configure(config);
        try {
            session.resume();
        } catch (Exception e) {
            report.check("arcore_resume", "FAIL", e.toString(), null);
            say("ARCore resume failed: " + e);
            return;
        }
        textureSet = false;
        say("ARCore ready: " + configs.size() + " camera configs, raw depth " + raw + ", automatic depth " + automatic + ".");
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] permissions, int[] results) {
        if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
            runArCoreCheck();
        } else {
            report.check("camera_permission", "FAIL", "camera permission refused", null);
            say("Camera permission refused.");
        }
    }

    // ---- 2 and 3. Tracking run and host stream ---------------------------------------------------

    private void startMode(Mode next) {
        if (session == null) {
            say("Run 1 first.");
            return;
        }
        if (mode != Mode.IDLE) {
            say("Busy; wait for the current run to end.");
            return;
        }
        if (next == Mode.STREAM) {
            String host = hostField.getText().toString().trim();
            if (host.isEmpty()) {
                report.check("host_stream", "SKIPPED", "no host address entered", null);
                say("Enter the host IP printed by receiver.py.");
                return;
            }
            stream = new HostStream();
            stream.start(host, PORT);
        } else {
            stats = new TrackingStats();
        }
        seq = 0;
        modeStart = SystemClock.elapsedRealtime();
        mode = next;
        say(next == Mode.TRACKING ? "Tracking for 15 s: walk slowly and point at textured surfaces." : "Streaming for 20 s.");
    }

    @Override
    public void onSurfaceCreated(GL10 unused, EGLConfig config) {
        int[] ids = new int[1];
        GLES20.glGenTextures(1, ids, 0);
        texture = ids[0];
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, texture);
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
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
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);
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
        long elapsed = SystemClock.elapsedRealtime() - modeStart;
        if (mode == Mode.TRACKING) {
            stats.add(frame, updateMs, depthEnabled);
            if (elapsed >= TRACKING_MS) finishTracking(elapsed / 1000.0);
        } else if (mode == Mode.STREAM) {
            try (Image image = frame.acquireCameraImage()) {
                stream.offer(header(frame), image);
            } catch (Exception e) {
                // the CPU image is not ready on every frame
            }
            if (elapsed >= STREAM_MS) finishStream();
        }
    }

    private JSONObject header(Frame frame) {
        Camera camera = frame.getCamera();
        JSONObject h = new JSONObject();
        Report.put(h, "type", "frame");
        Report.put(h, "seq", seq++);
        Report.put(h, "t_ns", frame.getTimestamp());
        Report.put(h, "sent_ms", System.currentTimeMillis());
        Report.put(h, "tracking", camera.getTrackingState().name());
        if (camera.getTrackingState() == TrackingState.TRACKING) {
            Pose p = camera.getPose();
            Report.put(h, "pose", new JSONArray(Arrays.asList((double) p.tx(), (double) p.ty(), (double) p.tz(),
                    (double) p.qx(), (double) p.qy(), (double) p.qz(), (double) p.qw())));
        }
        CameraIntrinsics k = camera.getImageIntrinsics();
        float[] f = k.getFocalLength(), c = k.getPrincipalPoint();
        Report.put(h, "intrinsics", new JSONArray(Arrays.asList((double) f[0], (double) f[1], (double) c[0], (double) c[1])));
        return h;
    }

    private void finishTracking(double seconds) {
        mode = Mode.IDLE;
        JSONObject summary = stats.summary(seconds);
        double fraction = stats.trackingFraction();
        report.check("arcore_tracking", fraction >= 0.5 ? "PASS" : "FAIL",
                fraction >= 0.5 ? "" : String.format("tracking on %.0f%% of frames", 100 * fraction), summary);
        report.check("tracked_points", stats.maxPoints() > 0 ? "PASS" : "FAIL", stats.maxPoints() > 0 ? "" : "no tracked points", null);
        if (!depthEnabled) {
            report.check("raw_depth_frames", "SKIPPED", "depth not supported", null);
        } else {
            report.check("raw_depth_frames", stats.depthFrames() > 0 ? "PASS" : "FAIL", stats.depthFrames() > 0 ? "" : "no depth image in the run", null);
        }
        say("Tracking run: " + summary);
    }

    private void finishStream() {
        mode = Mode.IDLE;
        HostStream finished = stream;
        new Thread(() -> {
            try {
                JSONObject summary = finished.stop();
                boolean ok = finished.acked() > 0;
                report.check("host_stream", ok ? "PASS" : "FAIL", ok ? "" : (finished.error() != null ? finished.error() : "no frame acknowledged"), summary);
                say("Stream: " + summary);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }).start();
    }

    // ---- 4. Save and send the report -------------------------------------------------------------

    private void saveReport() {
        String json = report.json();
        File file = new File(getExternalFilesDir(null), "phonecheck_" + System.currentTimeMillis() + ".json");
        try (FileOutputStream out = new FileOutputStream(file)) {
            out.write(json.getBytes(StandardCharsets.UTF_8));
            say("Saved " + file.getAbsolutePath());
        } catch (Exception e) {
            say("Could not save the report: " + e);
        }
        String host = hostField.getText().toString().trim();
        if (host.isEmpty()) return;
        new Thread(() -> {
            try (Socket socket = new Socket()) {
                socket.connect(new InetSocketAddress(host, PORT), 3000);
                DataOutputStream out = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream()));
                HostStream.send(out, Report.put(Report.put(new JSONObject(), "type", "report"), "schema", 1), json.getBytes(StandardCharsets.UTF_8));
                say("Report sent to " + host);
            } catch (Exception e) {
                say("Could not send the report: " + e);
            }
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
                say("ARCore resume failed: " + e);
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
