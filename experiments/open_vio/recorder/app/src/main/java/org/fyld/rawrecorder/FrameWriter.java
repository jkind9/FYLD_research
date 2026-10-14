package org.fyld.rawrecorder;

import android.media.Image;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.TimeUnit;

/**
 * Saves the luminance plane of each camera image as cam0/<timestamp_ns>.pgm on its own thread.
 * Buffers come from a fixed pool, so a slow disk drops frames (counted) instead of filling memory.
 */
final class FrameWriter {
    static final int QUEUE = 60;

    private static final class Item {
        long t;
        final byte[] luma;

        Item(int size) {
            luma = new byte[size];
        }
    }

    private final File dir;
    private final int width, height;
    private final ArrayBlockingQueue<Item> free = new ArrayBlockingQueue<>(QUEUE), full = new ArrayBlockingQueue<>(QUEUE);
    private final Thread worker;
    private volatile boolean running = true;
    private volatile String error;
    private long offered, dropped, written;

    FrameWriter(File dir, int width, int height) {
        this.dir = dir;
        this.width = width;
        this.height = height;
        for (int i = 0; i < QUEUE; i++) free.add(new Item(width * height));
        worker = new Thread(this::run, "frame-writer");
        worker.start();
    }

    /** Copies the luminance rows of a YUV_420_888 image, which may be padded, into a tight width x height array. */
    static void copyLuma(Image image, byte[] into, int width, int height) {
        Image.Plane plane = image.getPlanes()[0];
        ByteBuffer buffer = plane.getBuffer().duplicate();
        int stride = plane.getRowStride();
        for (int row = 0; row < height; row++) {
            buffer.position(row * stride);
            buffer.get(into, row * width, width);
        }
    }

    /** Camera thread. */
    void offer(Image image) {
        offered++;
        Item item = free.poll();
        if (item == null) {
            dropped++;
            return;
        }
        copyLuma(image, item.luma, width, height);
        item.t = image.getTimestamp();
        full.add(item);
    }

    private void run() {
        byte[] header = ("P5\n" + width + " " + height + "\n255\n").getBytes(StandardCharsets.US_ASCII);
        while (running || !full.isEmpty()) {
            Item item;
            try {
                item = full.poll(100, TimeUnit.MILLISECONDS);
            } catch (InterruptedException e) {
                return;
            }
            if (item == null) continue;
            try (FileOutputStream out = new FileOutputStream(new File(dir, item.t + ".pgm"))) {
                out.write(header);
                out.write(item.luma);
                written++;
            } catch (IOException e) {
                error = e.getMessage();
            }
            free.add(item);
        }
    }

    /** Waits until every queued frame is on disk. */
    void finish() throws InterruptedException {
        running = false;
        worker.join();
    }

    long offered() {
        return offered;
    }

    long dropped() {
        return dropped;
    }

    long written() {
        return written;
    }

    String error() {
        return error;
    }
}
