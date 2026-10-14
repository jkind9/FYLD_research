package org.fyld.capture;

import org.json.JSONObject;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Joins the three things that arrive separately for one Camera2 image, keyed by its sensor timestamp: the image
 * (camera thread), its capture result (camera thread) and ARCore's record (GL thread). Frames leave in image
 * order once complete, or WAIT_NS after the image arrived with whatever has come. Plain Java, tested on the JVM.
 */
final class FrameAssembler {
    static final long WAIT_NS = 500_000_000L;
    static final int MAX_PENDING = 30;

    static final class Pending {
        long t, wallMs, arrivedNs;
        byte[] nv21;
        int width, height;
        JSONObject camera;
        ArcoreRecord arcore;
    }

    private final boolean expectArcore;
    private final ArrayDeque<Pending> pending = new ArrayDeque<>();
    private final Map<Long, JSONObject> earlyCamera = new HashMap<>();
    private final Map<Long, ArcoreRecord> earlyArcore = new HashMap<>();
    private final ArrayDeque<byte[]> free = new ArrayDeque<>();
    private long lastEmitted = Long.MIN_VALUE, captured, dropped, lateArcore;

    FrameAssembler(boolean expectArcore) {
        this.expectArcore = expectArcore;
    }

    /** A reused image buffer, so 30 images a second do not each allocate 460 KB. */
    synchronized byte[] buffer(int size) {
        byte[] b = free.poll();
        return b != null && b.length == size ? b : new byte[size];
    }

    synchronized void recycle(byte[] b) {
        if (free.size() < MAX_PENDING) free.add(b);
    }

    /** False when MAX_PENDING images are already waiting (the writer is behind): the image is dropped and counted. */
    synchronized boolean addImage(long t, byte[] nv21, int width, int height, long wallMs, long nowNs) {
        captured++;
        if (pending.size() >= MAX_PENDING) {
            dropped++;
            recycle(nv21);
            return false;
        }
        Pending p = new Pending();
        p.t = t;
        p.nv21 = nv21;
        p.width = width;
        p.height = height;
        p.wallMs = wallMs;
        p.arrivedNs = nowNs;
        p.camera = earlyCamera.remove(t);
        p.arcore = earlyArcore.remove(t);
        pending.add(p);
        return true;
    }

    synchronized void addCamera(long t, JSONObject settings) {
        Pending p = find(t);
        if (p != null) p.camera = settings;
        else if (t > lastEmitted) earlyCamera.put(t, settings);
    }

    synchronized void addArcore(long t, ArcoreRecord record) {
        Pending p = find(t);
        if (p != null) p.arcore = record;
        else if (t > lastEmitted) earlyArcore.put(t, record);
        else lateArcore++;
    }

    /** Frames ready to write, in image order; flush releases everything (at Stop). */
    synchronized List<Pending> ready(long nowNs, boolean flush) {
        List<Pending> out = new ArrayList<>();
        while (!pending.isEmpty()) {
            Pending p = pending.peek();
            boolean complete = p.camera != null && (p.arcore != null || !expectArcore);
            if (!complete && !flush && nowNs - p.arrivedNs < WAIT_NS) break;
            out.add(pending.poll());
            lastEmitted = p.t;
        }
        // parts whose image never arrived (the app's reader skipped it)
        earlyCamera.keySet().removeIf(t -> t <= lastEmitted);
        earlyArcore.keySet().removeIf(t -> t <= lastEmitted);
        return out;
    }

    synchronized long captured() { return captured; }

    synchronized long dropped() { return dropped; }

    synchronized long lateArcore() { return lateArcore; }

    private Pending find(long t) {
        for (Pending p : pending) if (p.t == t) return p;
        return null;
    }
}
