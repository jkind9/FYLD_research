package org.fyld.capture;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;

import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.File;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.Base64;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

public class CrashReportTest {
    @Rule
    public TemporaryFolder tmp = new TemporaryFolder();

    private JSONObject metadata() throws Exception {
        return new JSONObject().put("schema", 1).put("app_version", "capture 1.1")
                .put("device", new JSONObject().put("model", "2201116TG"));
    }

    @Test
    public void savesThreadAndFullCauseBeforeCallingAndroidsHandler() throws Exception {
        File file = new File(tmp.getRoot(), "last-crash.json");
        Thread thread = new Thread("frame-writer");
        Throwable error = new IllegalStateException("frame failed", new NullPointerException("missing image"));
        AtomicBoolean delegated = new AtomicBoolean();
        CrashReport handler = new CrashReport(file, metadata(), (t, e) -> {
            assertTrue(file.isFile());
            assertTrue(t == thread && e == error);
            delegated.set(true);
        });
        handler.uncaughtException(thread, error);
        JSONObject saved = new JSONObject(new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8));
        assertTrue(delegated.get());
        assertEquals("frame-writer", saved.getString("thread"));
        assertEquals("capture 1.1", saved.getString("app_version"));
        assertEquals("2201116TG", saved.getJSONObject("device").getString("model"));
        assertTrue(saved.getString("stack_trace").contains("Caused by: java.lang.NullPointerException: missing image"));
        assertTrue(saved.getLong("created_ms") > 0);
    }

    @Test
    public void failedCrashWriteStillCallsAndroidsHandler() throws Exception {
        File directory = tmp.newFolder("cannot-write-a-file-here");
        AtomicBoolean delegated = new AtomicBoolean();
        Throwable error = new IllegalStateException("capture failed");
        new CrashReport(directory, metadata(), (t, e) -> delegated.set(e == error))
                .uncaughtException(Thread.currentThread(), error);
        assertTrue(delegated.get());
        assertEquals(1, error.getSuppressed().length);
    }

    @Test
    public void sendsSavedExceptionOrSystemExitOnTheExistingReportConnection() throws Exception {
        File file = new File(tmp.getRoot(), "last-crash.json");
        JSONArray exits = new JSONArray().put(new JSONObject().put("reason", 5).put("trace_base64", "AQID"));
        for (boolean hasJavaCrash : new boolean[]{false, true}) {
            if (hasJavaCrash) new CrashReport(file, metadata(), null)
                    .uncaughtException(new Thread("camera"), new IllegalArgumentException("bad capture"));
            JSONObject report = receive(file, exits);
            assertEquals("crash_diagnostics", report.getString("type"));
            assertEquals("2201116TG", report.getJSONObject("device").getString("model"));
            assertEquals(5, report.getJSONArray("process_exits").getJSONObject(0).getInt("reason"));
            assertEquals(!hasJavaCrash, report.isNull("java_crash"));
            if (hasJavaCrash) {
                assertEquals("camera", report.getJSONObject("java_crash").getString("thread"));
                assertTrue(file.isFile());
            }
        }
    }

    @Test
    public void noPreviousCrashDoesNotOpenAConnection() throws Exception {
        assertFalse(CrashReport.send(new File(tmp.getRoot(), "absent.json"), metadata(), new JSONArray(), "127.0.0.1", 1));
    }

    @Test
    public void activityRecreationDoesNotChainAnotherCrashHandler() throws Exception {
        Thread.UncaughtExceptionHandler original = Thread.getDefaultUncaughtExceptionHandler();
        try {
            Thread.setDefaultUncaughtExceptionHandler((t, e) -> {});
            File file = new File(tmp.getRoot(), "last-crash.json");
            CrashReport.install(file, metadata());
            Thread.UncaughtExceptionHandler first = Thread.getDefaultUncaughtExceptionHandler();
            CrashReport.install(file, metadata());
            assertTrue(first instanceof CrashReport);
            assertTrue(first == Thread.getDefaultUncaughtExceptionHandler());
        } finally {
            Thread.setDefaultUncaughtExceptionHandler(original);
        }
    }

    @Test
    public void invalidSavedJavaTraceDoesNotBlockSystemExitDiagnostics() throws Exception {
        File file = tmp.newFile("last-crash.json");
        Files.write(file.toPath(), "{broken".getBytes(StandardCharsets.UTF_8));
        JSONObject report = receive(file, new JSONArray().put(new JSONObject().put("reason", 5)));
        assertTrue(report.isNull("java_crash"));
        assertTrue(report.getString("java_crash_error").contains("saved crash"));
        assertEquals("{broken", report.getString("java_crash_text"));
        assertEquals(5, report.getJSONArray("process_exits").getJSONObject(0).getInt("reason"));
    }

    @Test
    public void nativeTraceRetainsBinaryBytesAcrossReadBuffers() throws Exception {
        byte[] bytes = new byte[20003];
        Arrays.fill(bytes, (byte) 0x85);
        assertArrayEquals(bytes, Base64.getDecoder().decode(CrashReport.trace(new ByteArrayInputStream(bytes))));
        assertEquals("", CrashReport.trace(new ByteArrayInputStream(new byte[0])));
    }

    private JSONObject receive(File file, JSONArray exits) throws Exception {
        try (ServerSocket server = new ServerSocket(0)) {
            CompletableFuture<JSONObject> received = CompletableFuture.supplyAsync(() -> readReport(server));
            assertTrue(CrashReport.send(file, metadata(), exits, "127.0.0.1", server.getLocalPort()));
            return received.get(5, TimeUnit.SECONDS);
        }
    }

    private JSONObject readReport(ServerSocket server) {
        try (Socket socket = server.accept(); DataInputStream in = new DataInputStream(socket.getInputStream())) {
            socket.setSoTimeout(5000);
            JSONObject header = new JSONObject(new String(in.readNBytes(in.readInt()), StandardCharsets.UTF_8));
            assertEquals("report", header.getString("type"));
            return new JSONObject(new String(in.readNBytes(in.readInt()), StandardCharsets.UTF_8));
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
}
