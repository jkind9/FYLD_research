package org.fyld.capture;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.DataInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

/**
 * One session's messages on the phone's storage, one file per message as the exact bytes to send, numbered from 0
 * with no gaps (phone_session_v2.md). Capture threads add; the sender reads in order and deletes what the PC has
 * acknowledged. One instance per folder, shared by both sides; a folder left by a closed app reopens where it was.
 */
final class DiskQueue {
    static final long MIN_FREE_BYTES = 1_000_000_000L;
    private static final Map<String, DiskQueue> OPEN = new HashMap<>();

    private final File dir;
    private final JSONObject info;
    private final TreeMap<Long, long[]> pending = new TreeMap<>();  // n -> {bytes, 1 for a frame}
    private long next, endN = -1, ackedFrames, ackedBytes, pendingBytes, framesSent;
    private int pendingFrames;
    private boolean refused;

    private DiskQueue(File dir) throws IOException {
        this.dir = dir;
        try {
            info = new JSONObject(text("info.json", "{}"));
        } catch (JSONException e) {
            throw new IOException("unreadable info.json in " + dir);
        }
        next = Long.parseLong(text("through", "-1")) + 1;
        File[] files = dir.listFiles((d, name) -> name.endsWith(".msg"));
        for (File f : files == null ? new File[0] : files) {
            long n = Long.parseLong(f.getName().substring(0, 10));
            boolean frame = f.getName().contains("-f");
            track(n, f.length(), frame);
            next = Math.max(next, n + 1);
        }
        endN = Long.parseLong(text("end", "-1"));
        // The process can stop after writing the end message but before writing its marker.
        if (endN < 0 && !pending.isEmpty()) {
            long last = pending.lastKey();
            try (DataInputStream in = new DataInputStream(Files.newInputStream(file(last).toPath()))) {
                if ("end".equals(SessionMessages.read(in).optString("type"))) {
                    writeAtomically(new File(dir, "end"), Long.toString(last).getBytes(StandardCharsets.UTF_8));
                    endN = last;
                }
            }
        }
        refused = new File(dir, "refused.txt").exists();
    }

    static synchronized DiskQueue create(File root, String id, JSONObject info) throws IOException {
        File dir = new File(root, id);
        if (!dir.mkdirs()) throw new IOException("could not create " + dir);
        writeAtomically(new File(dir, "info.json"), info.toString().getBytes(StandardCharsets.UTF_8));
        return open(dir);
    }

    static synchronized DiskQueue open(File dir) throws IOException {
        DiskQueue q = OPEN.get(dir.getAbsolutePath());
        if (q == null) {
            q = new DiskQueue(dir);
            OPEN.put(dir.getAbsolutePath(), q);
        }
        return q;
    }

    /** Drops the shared instance, as an app restart does. */
    static synchronized void forget(File dir) {
        OPEN.remove(dir.getAbsolutePath());
    }

    /** Session folders under root still to send, oldest first. */
    static List<File> sessions(File root) {
        File[] dirs = root.listFiles(d -> new File(d, "info.json").exists() && !new File(d, "refused.txt").exists());
        List<File> out = new ArrayList<>(Arrays.asList(dirs == null ? new File[0] : dirs));
        out.sort((a, b) -> a.getName().compareTo(b.getName()));
        return out;
    }

    File dir() { return dir; }

    String id() { return dir.getName(); }

    JSONObject info() { return info; }

    /** Gives the message its number, writes it in full, then makes it visible to the sender; returns n. */
    synchronized long add(JSONObject header, byte[] payload) throws IOException {
        long n = next;
        Report.put(header, "n", n);
        boolean frame = "frame".equals(header.optString("type"));
        byte[] bytes = SessionMessages.encode(header, payload);
        writeAtomically(new File(dir, name(n, frame)), bytes);
        track(n, bytes.length, frame);
        next++;
        return n;
    }

    synchronized long end(JSONObject header) throws IOException {
        long n = add(header, new byte[0]);
        writeAtomically(new File(dir, "end"), Long.toString(n).getBytes(StandardCharsets.UTF_8));
        endN = n;
        return n;
    }

    synchronized File file(long n) {
        long[] p = pending.get(n);
        return p == null ? null : new File(dir, name(n, p[1] == 1));
    }

    synchronized boolean isFrame(long n) {
        long[] p = pending.get(n);
        return p != null && p[1] == 1;
    }

    /** The PC holds 0..k: delete those files. */
    synchronized void ackThrough(long k) throws IOException {
        // Persist numbering before deleting the last evidence of it, including if the app dies during deletion.
        if (next > 0) writeAtomically(new File(dir, "through"), Long.toString(next - 1).getBytes(StandardCharsets.UTF_8));
        while (!pending.isEmpty() && pending.firstKey() <= k) {
            Map.Entry<Long, long[]> e = pending.pollFirstEntry();
            if (!new File(dir, name(e.getKey(), e.getValue()[1] == 1)).delete()) throw new IOException("could not delete message " + e.getKey());
            pendingBytes -= e.getValue()[0];
            ackedBytes += e.getValue()[0];
            if (e.getValue()[1] == 1) {
                pendingFrames--;
                ackedFrames++;
            }
        }
    }

    /** The whole session is delivered: delete its folder. */
    synchronized void finish() {
        File[] files = dir.listFiles();
        for (File f : files == null ? new File[0] : files) f.delete();
        dir.delete();
        forget(dir);
    }

    synchronized void refuse(String why) throws IOException {
        writeAtomically(new File(dir, "refused.txt"), why.getBytes(StandardCharsets.UTF_8));
        refused = true;
    }

    synchronized long nextN() { return next; }

    synchronized boolean ended() { return endN >= 0; }

    synchronized long endN() { return endN; }

    synchronized boolean refused() { return refused; }

    synchronized int pendingFrames() { return pendingFrames; }

    synchronized long pendingBytes() { return pendingBytes; }

    synchronized long ackedFrames() { return ackedFrames; }

    /** Counts a frame message handed to the network, resends included. */
    synchronized void sentFrame() { framesSent++; }

    synchronized long framesSent() { return framesSent; }

    synchronized long ackedBytes() { return ackedBytes; }

    private void track(long n, long bytes, boolean frame) {
        pending.put(n, new long[]{bytes, frame ? 1 : 0});
        pendingBytes += bytes;
        if (frame) pendingFrames++;
    }

    private String text(String name, String missing) throws IOException {
        File f = new File(dir, name);
        return f.exists() ? new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8).trim() : missing;
    }

    private static String name(long n, boolean frame) {
        return String.format(Locale.US, "%010d-%s.msg", n, frame ? "f" : "m");
    }

    /** Written to a temporary name first, so a file under its real name is always complete. */
    private static void writeAtomically(File target, byte[] bytes) throws IOException {
        File tmp = new File(target.getPath() + ".tmp");
        try (FileOutputStream out = new FileOutputStream(tmp)) {
            out.write(bytes);
        }
        if (!tmp.renameTo(target)) throw new IOException("could not rename " + tmp);
    }
}
