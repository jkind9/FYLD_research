package org.fyld.capture;

import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayDeque;
import java.util.List;

/**
 * Sends the phone's queued sessions to host/capture_receiver.py (phone_session_v2.md), oldest first: up to WINDOW
 * messages unacknowledged, cumulative acknowledgements, files deleted only once acknowledged, and after a dropped
 * connection a new hello, resuming after the last message the PC holds with no gap. Plain Java, tested on the JVM.
 */
final class Uploader {
    static final int PORT = 8766, WINDOW = 64, TIMEOUT_MS = 20000, RETRY_MS = 1000, RETRY_MAX_MS = 5000;
    static final int SPEED_CHUNKS = 50, SPEED_CHUNK_BYTES = 1 << 20;

    interface Listener {
        void status(String text);
    }

    /** The PC refused a message; resending it would be refused again. */
    static final class Refused extends IOException {
        Refused(String message) {
            super(message);
        }
    }

    private final File root;
    private final String host;
    private final int port;
    private final Listener listener;
    private final ArrayDeque<long[]> acks = new ArrayDeque<>();  // {time ms, acknowledged bytes} over the last 5 s
    private volatile boolean running = true;
    private volatile DiskQueue current;
    private volatile long progressMs;  // last write, acknowledgement or idle moment on the current connection
    int timeoutMs = TIMEOUT_MS;  // shorter in tests

    Uploader(File root, String host, int port, Listener listener) {
        this.root = root;
        this.host = host;
        this.port = port;
        this.listener = listener;
    }

    /** For a worker thread: keeps sending whatever sessions appear until stop(). */
    void run() {
        while (running) {
            drainAll();
            pause(500);
        }
    }

    void stop() {
        running = false;
    }

    String host() { return host; }

    DiskQueue current() { return current; }

    /** Bytes per second acknowledged over the last 5 s; 0 before any. */
    synchronized double rate() {
        if (acks.size() < 2) return 0;
        long[] first = acks.peekFirst(), last = acks.peekLast();
        return last[0] == first[0] ? 0 : (last[1] - first[1]) * 1000.0 / (last[0] - first[0]);
    }

    /** Sends every session in root until each is delivered or refused (or stop() is called). */
    void drainAll() {
        while (running) {
            List<File> sessions = DiskQueue.sessions(root);
            if (sessions.isEmpty()) return;
            try {
                current = DiskQueue.open(sessions.get(0));
            } catch (IOException e) {
                listener.status("Cannot read " + sessions.get(0).getName() + ": " + e.getMessage());
                return;
            }
            drain(current);
        }
    }

    private void drain(DiskQueue q) {
        int wait = RETRY_MS;
        while (running) {
            try (Socket socket = new Socket()) {
                socket.connect(new InetSocketAddress(host, port), 5000);
                socket.setSoTimeout(timeoutMs);
                progressMs = System.currentTimeMillis();
                watch(socket);
                DataOutputStream out = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream(), 1 << 16));
                DataInputStream in = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
                SessionMessages.write(out, SessionMessages.hello(q.id(), System.currentTimeMillis(), q.info()), new byte[0]);
                long through = acknowledged(in, q), next = through + 1;
                wait = RETRY_MS;
                while (running) {
                    while (in.available() > 0) through = acknowledged(in, q);
                    if (q.ended() && through >= q.endN()) {
                        q.finish();
                        listener.status("Session " + q.id() + " is on the computer.");
                        return;
                    }
                    boolean windowOpen = next - through <= WINDOW;
                    File file = windowOpen ? q.file(next) : null;
                    if (file != null) {
                        out.write(Files.readAllBytes(file.toPath()));
                        progressMs = System.currentTimeMillis();
                        if (q.isFrame(next)) q.sentFrame();
                        next++;
                    } else if (windowOpen && next < q.nextN()) {
                        // deleted after an earlier acknowledgement, so this PC folder is not the one that had it
                        throw new Refused("the computer lacks message " + next + ", which it had acknowledged");
                    } else {
                        out.flush();
                        if (next > through + 1) {
                            through = acknowledged(in, q);
                        } else {
                            progressMs = System.currentTimeMillis();  // nothing outstanding
                            pause(20);
                        }
                    }
                }
                return;
            } catch (Refused e) {
                try {
                    q.refuse(e.getMessage());
                } catch (IOException ignored) {
                    // the message below still reaches the screen
                }
                listener.status("The computer refused session " + q.id() + ": " + e.getMessage());
                return;
            } catch (IOException e) {
                listener.status("Not connected to " + host + " (" + e.getMessage() + "); retrying");
                pause(wait);
                wait = Math.min(RETRY_MAX_MS, wait * 2);
            }
        }
    }

    /** Reads one answer from the PC: an acknowledgement (deletes what it covers) or a refusal. */
    private long acknowledged(DataInputStream in, DiskQueue q) throws IOException {
        JSONObject m = SessionMessages.read(in);
        if ("error".equals(m.optString("type"))) throw new Refused(m.optString("message"));
        long through = m.optLong("through", -2);
        if (through < -1) throw new IOException("unexpected answer " + m);
        q.ackThrough(through);
        progressMs = System.currentTimeMillis();
        synchronized (this) {
            long now = System.currentTimeMillis();
            acks.addLast(new long[]{now, q.ackedBytes()});
            while (acks.size() > 2 && now - acks.peekFirst()[0] > 5000) acks.pollFirst();
        }
        return through;
    }

    /**
     * Closes a connection that has made no progress for timeoutMs. A read gives up by itself, but a write to a PC
     * that has gone silent (Wi-Fi fading on the stairs) can block for many minutes before TCP reports it.
     */
    private void watch(Socket socket) {
        Thread watchdog = new Thread(() -> {
            while (!socket.isClosed()) {
                if (System.currentTimeMillis() - progressMs > timeoutMs) {
                    try {
                        socket.close();
                    } catch (IOException ignored) {
                        // the blocked write fails either way
                    }
                    return;
                }
                pause(200);
            }
        }, "uploader-watchdog");
        watchdog.setDaemon(true);
        watchdog.start();
    }

    /** Link-speed check: sends SPEED_CHUNKS of SPEED_CHUNK_BYTES on its own connection; returns MB/s as the phone timed it. */
    static double speedTest(String host, int port) throws IOException {
        byte[] chunk = new byte[SPEED_CHUNK_BYTES];
        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(host, port), 5000);
            socket.setSoTimeout(TIMEOUT_MS);
            DataOutputStream out = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream(), 1 << 16));
            DataInputStream in = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
            long start = System.nanoTime();
            for (int i = 0; i < SPEED_CHUNKS; i++) {
                JSONObject h = Report.put(Report.put(Report.put(new JSONObject(), "type", "speed"), "chunk", i), "chunks", SPEED_CHUNKS);
                out.write(SessionMessages.encode(h, chunk));
            }
            out.flush();
            JSONObject answer = SessionMessages.read(in);
            double seconds = (System.nanoTime() - start) / 1e9;
            return answer.optLong("bytes") / 1e6 / seconds;
        }
    }

    /** Sends a check report on its own connection. */
    static void sendReport(String host, int port, String json) throws IOException {
        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(host, port), 5000);
            DataOutputStream out = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream()));
            JSONObject h = Report.put(Report.put(new JSONObject(), "type", "report"), "schema", 1);
            SessionMessages.write(out, h, json.getBytes(StandardCharsets.UTF_8));
        }
    }

    private static void pause(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
