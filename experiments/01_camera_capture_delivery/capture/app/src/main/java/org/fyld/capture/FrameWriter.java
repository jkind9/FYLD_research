package org.fyld.capture;

import android.graphics.ImageFormat;
import android.graphics.Rect;
import android.graphics.YuvImage;
import android.media.Image;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.zip.Deflater;

/**
 * On its own thread, turns each frame the assembler releases into a phone session v2 frame message (grey plane,
 * colour JPEG, ARCore record) and writes it to the queue. seq counts written frames, so it has no gaps.
 */
final class FrameWriter {
    static final int JPEG_QUALITY = 90;

    private final FrameAssembler assembler;
    private final DiskQueue queue;
    private final boolean deflate;
    private final Thread worker;
    private volatile boolean stopping;
    private volatile String error;
    private volatile long seq;
    private long depthFrames, withoutArcore, withoutCamera;

    FrameWriter(FrameAssembler assembler, DiskQueue queue, boolean deflate) {
        this.assembler = assembler;
        this.queue = queue;
        this.deflate = deflate;
        worker = new Thread(this::run, "frame-writer");
        worker.start();
    }

    private void run() {
        while (true) {
            boolean last = stopping;
            List<FrameAssembler.Pending> ready = assembler.ready(System.nanoTime(), last);
            for (FrameAssembler.Pending p : ready) write(p);
            if (last) return;
            if (ready.isEmpty()) {
                try {
                    Thread.sleep(5);
                } catch (InterruptedException e) {
                    return;
                }
            }
        }
    }

    private void write(FrameAssembler.Pending p) {
        SessionFrame f = new SessionFrame();
        f.seq = seq;
        f.cameraTNs = p.t;
        f.wallMs = p.wallMs;
        f.camera = p.camera;
        f.width = p.width;
        f.height = p.height;
        byte[] grey = Arrays.copyOf(p.nv21, p.width * p.height);  // NV21 starts with the luminance plane
        f.grey = deflate ? deflate(grey) : grey;
        f.greyEncoding = deflate ? "deflate" : "raw";
        f.jpeg = jpeg(p.nv21, p.width, p.height);
        f.jpegQuality = JPEG_QUALITY;
        f.arcore = p.arcore;
        assembler.recycle(p.nv21);
        try {
            queue.add(f.header(queue.id()), f.payload());
        } catch (IOException e) {
            error = "could not write frame " + seq + ": " + e.getMessage();
            return;
        }
        seq++;
        if (p.arcore == null) withoutArcore++;
        else if (p.arcore.depthLe != null) depthFrames++;
        if (p.camera == null) withoutCamera++;
    }

    /** Writes every frame still held, then returns. */
    void finish() throws InterruptedException {
        stopping = true;
        worker.join();
    }

    long frames() { return seq; }

    long depthFrames() { return depthFrames; }

    long withoutArcore() { return withoutArcore; }

    long withoutCamera() { return withoutCamera; }

    String error() { return error; }

    static byte[] jpeg(byte[] nv21, int width, int height) {
        ByteArrayOutputStream out = new ByteArrayOutputStream(width * height / 4);
        new YuvImage(nv21, ImageFormat.NV21, width, height, null).compressToJpeg(new Rect(0, 0, width, height), JPEG_QUALITY, out);
        return out.toByteArray();
    }

    /** Lossless zlib stream at level 1, the fastest. */
    static byte[] deflate(byte[] data) {
        Deflater d = new Deflater(1);
        d.setInput(data);
        d.finish();
        ByteArrayOutputStream out = new ByteArrayOutputStream(data.length / 2);
        byte[] buffer = new byte[1 << 16];
        while (!d.finished()) out.write(buffer, 0, d.deflate(buffer));
        d.end();
        return out.toByteArray();
    }

    /**
     * Deflate is worth its CPU time only when it saves at least 10% of the grey bytes, JPEG plus deflate of one frame
     * fit in 75% of the frame interval (so the writer keeps up), and the link is slower than the raw data rate
     * (so sending is the bottleneck). Proposed by Claude 2026-10-14, not owner-ruled.
     */
    static boolean deflatePays(double ratio, double deflateMs, double jpegMs, double frameIntervalMs, double linkMBps,
                               int greyBytes, int jpegBytes) {
        double rawMBps = (greyBytes + jpegBytes) * (1000.0 / frameIntervalMs) / 1e6;
        return ratio <= 0.9 && deflateMs + jpegMs <= 0.75 * frameIntervalMs && linkMBps < rawMBps;
    }

    /** Times JPEG and deflate on sample camera images (NV21); medians in ms, and the deflate size ratio. */
    static JSONObject compressionCheck(List<byte[]> samples, int width, int height) {
        List<Double> jpegMs = new ArrayList<>(), deflateMs = new ArrayList<>(), jpegBytes = new ArrayList<>();
        long raw = 0, packed = 0;
        for (byte[] nv21 : samples) {
            long t0 = System.nanoTime();
            byte[] jpeg = jpeg(nv21, width, height);
            long t1 = System.nanoTime();
            byte[] grey = deflate(Arrays.copyOf(nv21, width * height));
            long t2 = System.nanoTime();
            jpegMs.add((t1 - t0) / 1e6);
            deflateMs.add((t2 - t1) / 1e6);
            jpegBytes.add((double) jpeg.length);
            raw += width * height;
            packed += grey.length;
        }
        JSONObject out = new JSONObject();
        Report.put(out, "frames", samples.size());
        Report.put(out, "jpeg_ms_median", TrackingStats.percentile(jpegMs, 50));
        Report.put(out, "deflate_ms_median", TrackingStats.percentile(deflateMs, 50));
        Report.put(out, "deflate_ratio", raw == 0 ? Double.NaN : packed / (double) raw);
        Report.put(out, "jpeg_bytes_median", TrackingStats.percentile(jpegBytes, 50));
        return out;
    }

    /** YUV_420_888 camera image to NV21 bytes (Y plane, then interleaved V and U) in a buffer of width * height * 3 / 2. */
    static void nv21(Image image, byte[] out) {
        int width = image.getWidth(), height = image.getHeight();
        Image.Plane[] planes = image.getPlanes();
        ByteBuffer y = planes[0].getBuffer(), u = planes[1].getBuffer(), v = planes[2].getBuffer();
        int yRow = planes[0].getRowStride(), uvRow = planes[1].getRowStride(), uvStep = planes[1].getPixelStride();
        for (int r = 0; r < height; r++) {
            y.position(r * yRow);
            y.get(out, r * width, width);  // the luminance plane's pixel stride is always 1
        }
        int at = width * height;
        for (int r = 0; r < height / 2; r++) {
            for (int c = 0; c < width / 2; c++) {
                int i = r * uvRow + c * uvStep;
                out[at++] = v.get(i);
                out[at++] = u.get(i);
            }
        }
    }
}
