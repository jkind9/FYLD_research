package org.fyld.phonecheck;

import android.graphics.ImageFormat;
import android.graphics.Rect;
import android.graphics.YuvImage;
import android.media.Image;

import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.TimeUnit;

/**
 * Sends a phone session v1 stream (phone_session_v1.md) to the host receiver and waits for each acknowledgement.
 * Wire format matches host/protocol.py: 4-byte length + JSON header, 4-byte length + payload; ack = 4-byte frame number.
 */
final class HostStream {
    static final int JPEG_QUALITY = 80;

    private static final class Item {
        final SessionFrame frame;
        final byte[] nv21;

        Item(SessionFrame frame, byte[] nv21) {
            this.frame = frame;
            this.nv21 = nv21;
        }
    }

    private final ArrayBlockingQueue<Item> queue = new ArrayBlockingQueue<>(2);
    private final List<Double> roundTripMs = new ArrayList<>();
    private volatile boolean running;
    private volatile String error;
    private Thread worker;
    private int offered, dropped, acked;
    private long bytesSent, startNanos, endNanos;

    void start(String host, int port) {
        running = true;
        startNanos = System.nanoTime();
        worker = new Thread(() -> run(host, port), "host-stream");
        worker.start();
    }

    /** False when the sender is behind; the GL thread then skips this camera image (counted as dropped). */
    boolean hasRoom() {
        if (queue.remainingCapacity() > 0) return true;
        dropped++;
        return false;
    }

    /** Called on the GL thread after hasRoom(); copies the image, so the caller closes it. */
    void offer(SessionFrame frame, Image image) {
        offered++;
        frame.imageWidth = image.getWidth();
        frame.imageHeight = image.getHeight();
        queue.add(new Item(frame, nv21(image)));
    }

    JSONObject stop() throws InterruptedException {
        running = false;
        worker.join(5000);
        endNanos = System.nanoTime();
        double seconds = (endNanos - startNanos) / 1e9;
        JSONObject out = new JSONObject();
        Report.put(out, "seconds", seconds);
        Report.put(out, "frames_offered", offered);
        Report.put(out, "frames_dropped_sender_busy", dropped);
        Report.put(out, "frames_acknowledged", acked);
        Report.put(out, "acknowledged_per_second", acked / seconds);
        Report.put(out, "megabytes_per_second", bytesSent / 1e6 / seconds);
        Report.put(out, "round_trip_ms_median", TrackingStats.percentile(roundTripMs, 50));
        Report.put(out, "round_trip_ms_p95", TrackingStats.percentile(roundTripMs, 95));
        Report.put(out, "jpeg_quality", JPEG_QUALITY);
        Report.put(out, "error", error == null ? JSONObject.NULL : error);
        return out;
    }

    int acked() { return acked; }

    int offered() { return offered; }

    String error() { return error; }

    private void run(String host, int port) {
        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(host, port), 3000);
            socket.setTcpNoDelay(true);
            DataOutputStream out = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream()));
            DataInputStream in = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
            JSONObject start = new JSONObject();
            Report.put(start, "type", "session");
            Report.put(start, "version", SessionFrame.VERSION);
            Report.put(start, "device", Report.device());
            Report.put(start, "started_ms", System.currentTimeMillis());
            send(out, start, new byte[0]);
            while (running || !queue.isEmpty()) {
                Item item = queue.poll(100, TimeUnit.MILLISECONDS);
                if (item == null) continue;
                ByteArrayOutputStream jpeg = new ByteArrayOutputStream();
                SessionFrame f = item.frame;
                new YuvImage(item.nv21, ImageFormat.NV21, f.imageWidth, f.imageHeight, null)
                        .compressToJpeg(new Rect(0, 0, f.imageWidth, f.imageHeight), JPEG_QUALITY, jpeg);
                f.jpeg = jpeg.toByteArray();
                long sent = System.nanoTime();
                bytesSent += send(out, f.header(), f.payload());
                int seq = in.readInt();
                if (seq != f.seq) throw new IOException("acknowledged frame " + seq + ", expected " + f.seq);
                roundTripMs.add((System.nanoTime() - sent) / 1e6);
                acked++;
            }
        } catch (Exception e) {
            error = e.getClass().getSimpleName() + ": " + e.getMessage();
        }
    }

    /** Sends one message (used for frames and, on a fresh connection, for the report); returns bytes written. */
    static int send(DataOutputStream out, JSONObject header, byte[] payload) throws IOException {
        byte[] encoded = header.toString().getBytes(StandardCharsets.UTF_8);
        out.writeInt(encoded.length);
        out.write(encoded);
        out.writeInt(payload.length);
        out.write(payload);
        out.flush();
        return 8 + encoded.length + payload.length;
    }

    /** YUV_420_888 camera image to NV21 bytes (Y plane, then interleaved V and U). */
    static byte[] nv21(Image image) {
        int width = image.getWidth(), height = image.getHeight();
        byte[] out = new byte[width * height * 3 / 2];
        Image.Plane[] planes = image.getPlanes();
        ByteBuffer y = planes[0].getBuffer(), u = planes[1].getBuffer(), v = planes[2].getBuffer();
        int yRow = planes[0].getRowStride(), yStep = planes[0].getPixelStride();
        int uvRow = planes[1].getRowStride(), uvStep = planes[1].getPixelStride();
        int at = 0;
        for (int r = 0; r < height; r++) {
            for (int c = 0; c < width; c++) out[at++] = y.get(r * yRow + c * yStep);
        }
        for (int r = 0; r < height / 2; r++) {
            for (int c = 0; c < width / 2; c++) {
                int i = r * uvRow + c * uvStep;
                out[at++] = v.get(i);
                out[at++] = u.get(i);
            }
        }
        return out;
    }
}
