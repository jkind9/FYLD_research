package org.fyld.capture;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public final class CameraActivity extends Activity {
    private static final int CAMERA_PERMISSION_REQUEST = 42;
    private static final int EXPORT_REQUEST = 43;
    private HandlerThread cameraThread;
    private Handler cameraHandler;
    private Handler uiHandler;
    private TextView status;
    private File latestSession;
    private Runnable permissionAction;
    private static final String STATE_SESSION_PATH = "capture_session_path";
    private static final String PROCESS_ID = java.util.UUID.randomUUID().toString();

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        uiHandler = new Handler(getMainLooper());
        cameraThread = new HandlerThread("camera-capture");
        cameraThread.start();
        cameraHandler = new Handler(cameraThread.getLooper());
        if (state != null) {
            String sessionPath = state.getString(STATE_SESSION_PATH);
            if (sessionPath != null) latestSession = new File(sessionPath);
        }
        recoverInterruptedSessions();
        buildScreen();
    }

    @Override
    protected void onSaveInstanceState(Bundle state) {
        if (latestSession != null) state.putString(STATE_SESSION_PATH, latestSession.getAbsolutePath());
        super.onSaveInstanceState(state);
    }

    @Override
    protected void onDestroy() {
        if (cameraThread != null) cameraThread.quitSafely();
        super.onDestroy();
    }

    private void buildScreen() {
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(28, 24, 28, 24);
        TextView title = new TextView(this);
        title.setText("FYLD Camera Check");
        title.setTextSize(24);
        content.addView(title);
        status = new TextView(this);
        status.setText("Camera data stays on this phone until you export a report.");
        content.addView(status);
        addButton(content, "Inspect Camera2 capabilities", view -> withCameraPermission(this::inspect));
        addButton(content, "Capture one rear-camera control", view -> withCameraPermission(this::captureSingle));
        addButton(content, "Attempt advertised concurrent camera sets", view -> withCameraPermission(this::capturePairs));
        addButton(content, "Export latest session", view -> exportLatest());
        ScrollView scroll = new ScrollView(this);
        scroll.addView(content);
        setContentView(scroll);
    }

    private void addButton(LinearLayout parent, String label, View.OnClickListener action) {
        Button button = new Button(this);
        button.setText(label);
        button.setOnClickListener(action);
        parent.addView(button);
    }

    private void withCameraPermission(Runnable action) {
        if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            action.run();
            return;
        }
        permissionAction = action;
        requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode != CAMERA_PERMISSION_REQUEST) return;
        Runnable next = permissionAction;
        permissionAction = null;
        if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED && next != null) {
            next.run();
        } else {
            recordPermissionDenied();
        }
    }

    private void inspect() {
        try {
            JSONObject report = newSessionReport();
            JSONArray cameras = report.getJSONArray("cameras");
            JSONArray details = new JSONArray();
            for (int index = 0; index < cameras.length(); index++) {
                details.put(cameras.getJSONObject(index).getString("id"));
            }
            CameraReport.addCheck(report, "camera2_enumeration", cameras.length() == 0 ? "FAIL" : "PASS",
                    cameras.length() == 0 ? "Camera2 returned no camera IDs" : null, details);
            saveReport(report, "Camera2 capability report saved. Use Export latest session to transfer it.");
        } catch (CameraAccessException | IOException | JSONException error) {
            showError("Camera inspection failed: " + error.getMessage());
        }
    }

    private void captureSingle() {
        try {
            JSONObject report = newSessionReport();
            JSONArray cameras = report.getJSONArray("cameras");
            String rear = null;
            for (int index = 0; index < cameras.length(); index++) {
                JSONObject camera = cameras.getJSONObject(index);
                if ("back".equals(camera.optString("lens_facing"))) {
                    rear = camera.getString("id");
                    break;
                }
            }
            if (rear == null) {
                CameraReport.addCheck(report, "single_camera_control", "SKIPPED",
                        "No rear-facing Camera2 ID is available", null);
                saveReport(report, "No rear camera was available.");
                return;
            }
            status.setText("Opening rear camera " + rear + " and capturing one diagnostic JPEG…");
            runCapture(report, Collections.singletonList(rear), "single",
                    "Single rear-camera control", (updated, frames, error) -> {
                        try {
                            CameraReport.addCheck(updated, "single_camera_control",
                                    error == null ? "PASS" : "FAIL", error, frames);
                            saveReport(updated, "Single-camera control finished. Export the session to transfer it.");
                        } catch (JSONException failure) {
                            showError("Could not record the single-camera result: " + failure.getMessage());
                        }
                    });
        } catch (CameraAccessException | IOException | JSONException error) {
            showError("Could not start single-camera control: " + error.getMessage());
        }
    }

    private void capturePairs() {
        try {
            JSONObject report = newSessionReport();
            CameraManager manager = (CameraManager) getSystemService(CAMERA_SERVICE);
            if (android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.R) {
                CameraReport.addCheck(report, "advertised_camera_pairs", "SKIPPED",
                        "Concurrent camera sets require Android 11 or newer", null);
                saveReport(report, "Concurrent camera sets are unavailable on this Android version.");
                return;
            }
            List<List<String>> groups = sortedGroups(manager.getConcurrentCameraIds());
            if (groups.isEmpty()) {
                CameraReport.addCheck(report, "advertised_camera_pairs", "SKIPPED",
                        "The Camera2 service advertises no concurrent camera ID sets", null);
                saveReport(report, "This phone advertises no Camera2 concurrent camera sets.");
                return;
            }
            status.setText("Attempting " + groups.size() + " advertised concurrent set(s)…");
            capturePairAt(report, groups, 0);
        } catch (CameraAccessException | IOException | JSONException error) {
            showError("Could not enumerate concurrent camera sets: " + error.getMessage());
        }
    }

    private void capturePairAt(JSONObject report, List<List<String>> groups, int index) {
        if (index >= groups.size()) {
            saveCaptureResult(report, "All advertised camera sets have been attempted.");
            return;
        }
        List<String> ids = groups.get(index);
        runCapture(report, ids, "pair_" + (index + 1),
                "Camera set " + ids, (updated, frames, error) -> {
                    try {
                        if (error == null && frames.length() == ids.size()) {
                            CameraReport.addCheck(updated, "concurrent_set_" + (index + 1), "PASS", null, frames);
                        } else {
                            CameraReport.addCheck(updated, "concurrent_set_" + (index + 1), "FAIL",
                                    error == null ? "Not every camera produced an image and sensor result" : error,
                                    frames);
                        }
                        capturePairAt(updated, groups, index + 1);
                    } catch (JSONException failure) {
                        showError("Could not record pair result: " + failure.getMessage());
                    }
                });
    }

    private interface CaptureDone {
        void done(JSONObject report, JSONArray frames, String error);
    }

    private void runCapture(JSONObject report, List<String> ids, String captureName,
                            String statusText, CaptureDone done) {
        CameraCapture capture = new CameraCapture(this, cameraHandler, latestSession,
                captureName, ids, new CameraCapture.Callback() {
            @Override
            public void onComplete(JSONArray frames) {
                uiHandler.post(() -> done.done(report, frames, null));
            }

            @Override
            public void onFailure(String reason, JSONArray partialFiles) {
                uiHandler.post(() -> done.done(report, partialFiles, reason));
            }
        });
        status.setText(statusText);
        capture.start();
    }

    private void saveCaptureResult(JSONObject report, String message) {
        saveCaptureResult(report, message, new JSONArray(), null);
    }

    private void saveCaptureResult(JSONObject report, String message, JSONArray frames, String error) {
        try {
            if (report.getJSONArray("checks").length() == 0) {
                CameraReport.addCheck(report, "single_camera_control", error == null ? "PASS" : "FAIL",
                        error, frames);
            }
            saveReport(report, message);
        } catch (JSONException failure) {
            showError("Could not save capture result: " + failure.getMessage());
        }
    }

    private JSONObject newSessionReport() throws CameraAccessException, IOException, JSONException {
        latestSession = CameraReport.newSessionDirectory(this);
        JSONObject report = CameraReport.create(this);
        report.put("session_id", latestSession.getName());
        report.put("session_process_id", PROCESS_ID);
        report.put("status", "incomplete");
        report.put("session_directory", latestSession.getName());
        CameraReport.addCheck(report, "arcore_depth_and_pose", "SKIPPED",
                "This APK does not include the ARCore SDK; no runtime depth or pose result was collected", null);
        CameraReport.writeReport(latestSession, report);
        return report;
    }

    private void saveReport(JSONObject report, String message) {
        try {
            report.put("status", "complete");
            CameraReport.writeReport(latestSession, report);
            status.setText(message + "\nSession: " + latestSession.getName());
        } catch (IOException | JSONException error) {
            showError("Could not write camera report: " + error.getMessage());
        }
    }

    private void recordPermissionDenied() {
        try {
            latestSession = CameraReport.newSessionDirectory(this);
            JSONObject report = new JSONObject();
            report.put("schema_version", CameraReport.SCHEMA_VERSION);
            report.put("session_id", latestSession.getName());
            report.put("created_at_utc_ms", System.currentTimeMillis());
            report.put("device", CameraReport.deviceFields());
            report.put("permission", "denied");
            report.put("cameras", new JSONArray());
            report.put("concurrent_camera_sets", new JSONArray());
            report.put("checks", new JSONArray());
            report.put("status", "complete");
            report.put("captures", new JSONArray());
            report.put("files", new JSONObject());
            report.put("session_directory", latestSession.getName());
            CameraReport.addCheck(report, "camera_permission", "FAIL",
                    "Camera permission was denied by the user", null);
            CameraReport.addCheck(report, "arcore_depth_and_pose", "SKIPPED",
                    "This APK does not include the ARCore SDK; no runtime depth or pose result was collected", null);
            CameraReport.writeReport(latestSession, report);
            status.setText("Camera permission was denied. The result is saved in this session.");
        } catch (IOException | JSONException error) {
            showError("Could not record permission result: " + error.getMessage());
        }
    }

    private void exportLatest() {
        latestSession = latestSession == null ? findLatestSession() : latestSession;
        if (latestSession == null || !new File(latestSession, "report.json").isFile()) {
            showError("Run a capability check or capture before exporting.");
            return;
        }
        try {
            JSONObject report = readReport(latestSession);
            if (!"complete".equals(report.optString("status"))) {
                showError("Incomplete sessions cannot be exported as complete.");
                return;
            }
        } catch (IOException | JSONException error) {
            showError("The latest report cannot be read: " + error.getMessage());
            return;
        }
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/zip");
        intent.putExtra(Intent.EXTRA_TITLE, latestSession.getName() + ".zip");
        startActivityForResult(intent, EXPORT_REQUEST);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != EXPORT_REQUEST || resultCode != RESULT_OK || data == null || data.getData() == null) return;
        try (OutputStream output = getContentResolver().openOutputStream(data.getData(), "w")) {
            if (output == null) throw new IOException("The selected destination could not be opened");
            zipSession(latestSession, output, System.currentTimeMillis());
            status.setText("Export complete. Transfer the ZIP to the workstation and verify its hashes.");
        } catch (IOException error) {
            showError("Export failed: " + error.getMessage());
        }
    }

    private static void zipSession(File directory, OutputStream output, long exportTimestampMs) throws IOException {
        File[] files = directory.listFiles(file -> file.isFile() && !file.isHidden());
        if (files == null) throw new IOException("Cannot list completed session files");
        Arrays.sort(files, (left, right) -> left.getName().compareTo(right.getName()));
        try (ZipOutputStream zip = new ZipOutputStream(output)) {
            byte[] buffer = new byte[16384];
            for (File file : files) {
                ZipEntry entry = new ZipEntry(file.getName());
                zip.putNextEntry(entry);
                if ("report.json".equals(file.getName())) {
                    try {
                        JSONObject report = new JSONObject(new String(readAll(file),
                                java.nio.charset.StandardCharsets.UTF_8));
                        report.put("exported_at_utc_ms", exportTimestampMs);
                        zip.write((report.toString(2) + "\n").getBytes(
                                java.nio.charset.StandardCharsets.UTF_8));
                    } catch (JSONException error) {
                        throw new IOException("Could not add export time to the report", error);
                    }
                } else try (FileInputStream input = new FileInputStream(file)) {
                    int count;
                    while ((count = input.read(buffer)) != -1) zip.write(buffer, 0, count);
                }
                zip.closeEntry();
            }
            zip.finish();
        }
    }

    private JSONObject readReport(File session) throws IOException, JSONException {
        File file = new File(session, "report.json");
        return new JSONObject(new String(readAll(file), java.nio.charset.StandardCharsets.UTF_8));
    }

    private static byte[] readAll(File file) throws IOException {
        long length = file.length();
        if (length <= 0 || length > 4L * 1024 * 1024) {
            throw new IOException("Camera report has an invalid size");
        }
        byte[] bytes = new byte[(int) length];
        try (FileInputStream input = new FileInputStream(file)) {
            int offset = 0;
            while (offset < bytes.length) {
                int count = input.read(bytes, offset, bytes.length - offset);
                if (count < 0) throw new IOException("Camera report ended unexpectedly");
                offset += count;
            }
        }
        return bytes;
    }

    private File findLatestSession() {
        File root = new File(getFilesDir(), "capture-sessions");
        File[] sessions = root.listFiles(File::isDirectory);
        if (sessions == null || sessions.length == 0) return null;
        Arrays.sort(sessions, (left, right) -> left.getName().compareTo(right.getName()));
        return sessions[sessions.length - 1];
    }

    private void recoverInterruptedSessions() {
        File root = new File(getFilesDir(), "capture-sessions");
        File[] sessions = root.listFiles(File::isDirectory);
        if (sessions == null) return;
        for (File session : sessions) {
            File receipt = new File(session, "report.json");
            if (!receipt.isFile()) continue;
            try {
                JSONObject report = readReport(session);
                if (!"incomplete".equals(report.optString("status"))) continue;
                if (PROCESS_ID.equals(report.optString("session_process_id"))) continue;
                boolean recorded = false;
                JSONArray checks = report.optJSONArray("checks");
                if (checks != null) {
                    for (int index = 0; index < checks.length(); index++) {
                        JSONObject check = checks.optJSONObject(index);
                        if (check != null && "session_recovery".equals(check.optString("id"))) {
                            recorded = true;
                            break;
                        }
                    }
                }
                if (!recorded) {
                    CameraReport.addCheck(report, "session_recovery", "FAIL",
                            "The app stopped before this session finished; partial files were preserved", null);
                }
                CameraReport.writeReport(session, report);
            } catch (IOException | JSONException error) {
                android.util.Log.e("CameraActivity", "Could not mark interrupted session " + session.getName(), error);
            }
        }
    }

    private List<List<String>> sortedGroups(Set<Set<String>> groups) {
        List<List<String>> sorted = new ArrayList<>();
        for (Set<String> group : groups) {
            List<String> ids = new ArrayList<>(group);
            Collections.sort(ids);
            sorted.add(ids);
        }
        sorted.sort((left, right) -> String.join(",", left).compareTo(String.join(",", right)));
        return sorted;
    }

    private void showError(String message) {
        status.setText(message);
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }
}
