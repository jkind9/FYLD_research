package org.fyld.capture;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Base64;

/** Persists Java failures before Android terminates the app; sends them on the next launch, not while crashing. */
final class CrashReport implements Thread.UncaughtExceptionHandler {
    private final File file;
    private final JSONObject metadata;
    private final Thread.UncaughtExceptionHandler previous;

    CrashReport(File file, JSONObject metadata, Thread.UncaughtExceptionHandler previous) {
        this.file = file;
        this.metadata = metadata;
        this.previous = previous;
    }

    static void install(File file, JSONObject metadata) {
        Thread.UncaughtExceptionHandler previous = Thread.getDefaultUncaughtExceptionHandler();
        if (!(previous instanceof CrashReport)) Thread.setDefaultUncaughtExceptionHandler(new CrashReport(file, metadata, previous));
    }

    @Override
    public synchronized void uncaughtException(Thread thread, Throwable error) {
        try {
            StringWriter stack = new StringWriter();
            error.printStackTrace(new PrintWriter(stack));
            Report.put(metadata, "created_ms", System.currentTimeMillis());
            Report.put(metadata, "thread", thread.getName());
            Report.put(metadata, "exception", error.toString());
            Report.put(metadata, "stack_trace", stack.toString());
            Files.write(file.toPath(), metadata.toString().getBytes(StandardCharsets.UTF_8));
        } catch (IOException failure) {
            error.addSuppressed(failure);
        } finally {
            if (previous != null) previous.uncaughtException(thread, error);
        }
    }

    static boolean send(File file, JSONObject metadata, JSONArray exits, String host, int port) throws IOException {
        if (!file.exists() && exits.length() == 0) return false;
        Object saved = JSONObject.NULL;
        if (file.exists()) {
            String text = new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8);
            try {
                saved = new JSONObject(text);
            } catch (JSONException e) {
                Report.put(metadata, "java_crash_error", "Cannot read saved crash: " + e.getMessage());
                Report.put(metadata, "java_crash_text", text);
            }
        }
        Report.put(metadata, "type", "crash_diagnostics");
        Report.put(metadata, "created_ms", System.currentTimeMillis());
        Report.put(metadata, "java_crash", saved);
        Report.put(metadata, "process_exits", exits);
        Uploader.sendReport(host, port, metadata.toString());
        return true;
    }

    /** Native tombstones are protobuf bytes; base64 preserves them without assuming UTF-8 text. */
    static String trace(InputStream stream) throws IOException {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int count;
        while ((count = stream.read(buffer)) != -1) out.write(buffer, 0, count);
        return Base64.getEncoder().encodeToString(out.toByteArray());
    }
}
