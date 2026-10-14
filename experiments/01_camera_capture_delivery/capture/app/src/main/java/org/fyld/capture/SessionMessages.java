package org.fyld.capture;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/**
 * Phone session v2 messages other than frames (phone_session_v2.md), and the wire framing of host/protocol.py:
 * 4-byte big-endian length + UTF-8 JSON header, 4-byte big-endian length + payload. Plain Java, tested on the JVM.
 */
final class SessionMessages {
    static final int VERSION = 2;
    static final int IMU_SAMPLE_BYTES = 36;

    private SessionMessages() {
    }

    /** The envelope of every queued message; DiskQueue adds the message number n. */
    static JSONObject message(String type, String session) {
        JSONObject h = new JSONObject();
        Report.put(h, "type", type);
        Report.put(h, "version", VERSION);
        Report.put(h, "session", session);
        return h;
    }

    static JSONObject hello(String session, long wallMs, JSONObject info) {
        JSONObject h = message("hello", session);
        Report.put(h, "wall_ms", wallMs);
        Report.put(h, "info", info);
        return h;
    }

    static JSONObject imu(String session, int samples) {
        return Report.put(message("imu", session), "samples", samples);
    }

    /** Per sample, little-endian: int64 t_ns, int32 sensor (0 gyroscope, 1 accelerometer), six float32 x, y, z, bx, by, bz. */
    static byte[] imuPayload(long[] tNs, int[] sensor, float[] values, int count) {
        ByteBuffer out = ByteBuffer.allocate(IMU_SAMPLE_BYTES * count).order(ByteOrder.LITTLE_ENDIAN);
        for (int i = 0; i < count; i++) {
            out.putLong(tNs[i]).putInt(sensor[i]);
            for (int k = 0; k < 6; k++) out.putFloat(values[6 * i + k]);
        }
        return out.array();
    }

    static JSONObject telemetry(String session, long elapsedRealtimeNs, long wallMs, int batteryPct, int thermalStatus, long freeBytes,
                                int queueFrames, long queueBytes, long framesCaptured, long framesQueued, long framesSent,
                                long framesAcknowledged, long framesDropped, Double arcoreUpdateMs) {
        JSONObject h = message("telemetry", session);
        Report.put(h, "elapsed_realtime_ns", elapsedRealtimeNs);
        Report.put(h, "wall_ms", wallMs);
        Report.put(h, "battery_pct", batteryPct);
        Report.put(h, "thermal_status", thermalStatus);
        Report.put(h, "free_bytes", freeBytes);
        Report.put(h, "queue_frames", queueFrames);
        Report.put(h, "queue_bytes", queueBytes);
        Report.put(h, "frames_captured", framesCaptured);
        Report.put(h, "frames_queued", framesQueued);
        Report.put(h, "frames_sent", framesSent);
        Report.put(h, "frames_acknowledged", framesAcknowledged);
        Report.put(h, "frames_dropped", framesDropped);
        Report.put(h, "arcore_update_ms", arcoreUpdateMs == null ? JSONObject.NULL : arcoreUpdateMs);
        return h;
    }

    static JSONObject end(String session, String reason, JSONObject clockEnd, JSONObject counts) {
        JSONObject h = message("end", session);
        Report.put(h, "reason", reason);
        Report.put(h, "clock", Report.put(new JSONObject(), "end", clockEnd));
        Report.put(h, "counts", counts);
        return h;
    }

    /** The settings in force, recorded in hello.info (proposed by Claude 2026-10-14, not owner-ruled). */
    static JSONObject settings(int jpegQuality, String greyEncoding) {
        JSONObject s = new JSONObject();
        Report.put(s, "jpeg_quality", jpegQuality);
        Report.put(s, "grey_encoding", greyEncoding);
        Report.put(s, "window", Uploader.WINDOW);
        Report.put(s, "anchor_interval_s", FrameCapture.ANCHOR_INTERVAL_NS / 1e9);
        Report.put(s, "arcore_wait_ms", FrameAssembler.WAIT_NS / 1_000_000);
        Report.put(s, "imu_batch_ms", ImuLogger.BATCH_MS);
        Report.put(s, "min_free_bytes", DiskQueue.MIN_FREE_BYTES);
        return s;
    }

    static byte[] encode(JSONObject header, byte[] payload) {
        byte[] encoded = header.toString().getBytes(StandardCharsets.UTF_8);
        ByteArrayOutputStream bytes = new ByteArrayOutputStream(8 + encoded.length + payload.length);
        DataOutputStream out = new DataOutputStream(bytes);
        try {
            out.writeInt(encoded.length);
            out.write(encoded);
            out.writeInt(payload.length);
            out.write(payload);
        } catch (IOException e) {
            throw new IllegalStateException(e);  // a ByteArrayOutputStream does not fail
        }
        return bytes.toByteArray();
    }

    /** Writes and flushes one message; returns the bytes written. */
    static int write(DataOutputStream out, JSONObject header, byte[] payload) throws IOException {
        byte[] bytes = encode(header, payload);
        out.write(bytes);
        out.flush();
        return bytes.length;
    }

    /** Reads one message and returns its header; the payload (empty in every message the PC sends) is skipped. */
    static JSONObject read(DataInputStream in) throws IOException {
        byte[] encoded = new byte[in.readInt()];
        in.readFully(encoded);
        in.readFully(new byte[in.readInt()]);  // skipBytes may skip less on a socket
        try {
            return new JSONObject(new String(encoded, StandardCharsets.UTF_8));
        } catch (JSONException e) {
            throw new IOException("unreadable header: " + e.getMessage());
        }
    }
}
