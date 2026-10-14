package org.fyld.capture;

import android.app.ActivityManager;
import android.app.ApplicationExitInfo;
import android.content.Context;
import android.os.Build;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;

/** Android's own exit history complements the Java handler when a native crash bypasses it. */
final class CrashDiagnostics {
    private CrashDiagnostics() {
    }

    private static File file(Context context) {
        return new File(context.getFilesDir(), "last-crash.json");
    }

    private static JSONObject metadata() {
        JSONObject out = new JSONObject();
        Report.put(out, "schema", 1);
        Report.put(out, "app_version", "capture " + CaptureActivity.VERSION);
        return Report.put(out, "device", Report.device());
    }

    static void install(Context context) {
        CrashReport.install(file(context), metadata());
    }

    static void send(Context context, String host, Uploader.Listener listener) {
        new Thread(() -> {
            try {
                if (CrashReport.send(file(context), metadata(), exits(context), host, Uploader.PORT)) {
                    listener.status("Previous crash diagnostics sent to the computer.");
                }
            } catch (Exception e) {
                listener.status("Crash diagnostics not sent: " + e.getMessage());
            }
        }, "crash-report").start();
    }

    private static JSONArray exits(Context context) {
        JSONArray out = new JSONArray();
        if (Build.VERSION.SDK_INT < 30) return out;
        ActivityManager manager = context.getSystemService(ActivityManager.class);
        for (ApplicationExitInfo exit : manager.getHistoricalProcessExitReasons(context.getPackageName(), 0, 5)) {
            JSONObject row = new JSONObject();
            Report.put(row, "timestamp_ms", exit.getTimestamp());
            Report.put(row, "pid", exit.getPid());
            Report.put(row, "reason", exit.getReason());
            Report.put(row, "status", exit.getStatus());
            Report.put(row, "description", exit.getDescription() == null ? JSONObject.NULL : exit.getDescription());
            Report.put(row, "trace_base64", JSONObject.NULL);
            try (InputStream stream = exit.getTraceInputStream()) {
                if (stream != null) Report.put(row, "trace_base64", CrashReport.trace(stream));
            } catch (IOException e) {
                Report.put(row, "trace_error", e.toString());
            }
            out.put(row);
        }
        return out;
    }
}
