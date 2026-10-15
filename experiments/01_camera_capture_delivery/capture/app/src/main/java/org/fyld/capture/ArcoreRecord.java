package org.fyld.capture;

import org.json.JSONArray;
import org.json.JSONObject;

/**
 * ARCore's output for one camera image (the "arcore" object of a phone session v2 frame) as plain values.
 * No Android or ARCore types, so it is tested on the JVM; FrameCapture fills it on the GL thread.
 */
final class ArcoreRecord {
    static final float MOVE_METRES = 0.001f, TURN_DEGREES = 0.1f;

    long tNs;
    String tracking, failure;
    float[] pose, devicePose;  // tx, ty, tz, qx, qy, qz, qw, or null when not tracking
    float[] intrinsics, textureIntrinsics;  // fx, fy, cx, cy
    int[] pointIds = new int[0];
    float[] pointXyzc = new float[0];  // x, y, z, confidence per point, as ARCore's point cloud gives them
    long depthTNs;
    int depthWidth, depthHeight;
    float[] depthIntrinsics;
    byte[] depthLe, confidence;  // null when this image has no new depth
    int anchorId = -1;
    float[] anchorPose;
    int[] correctionIds = new int[0];
    float[][] correctionPoses = new float[0][];

    JSONObject json() {
        JSONObject a = new JSONObject();
        Report.put(a, "t_ns", tNs);
        Report.put(a, "tracking", tracking);
        Report.put(a, "failure", failure);
        Report.put(a, "pose", pose == null ? JSONObject.NULL : numbers(pose));
        Report.put(a, "device_pose", devicePose == null ? JSONObject.NULL : numbers(devicePose));
        Report.put(a, "intrinsics", numbers(intrinsics));
        Report.put(a, "texture_intrinsics", numbers(textureIntrinsics));
        JSONArray points = new JSONArray();
        for (int i = 0; pose != null && i < pointIds.length; i++) {
            float x = pointXyzc[4 * i], y = pointXyzc[4 * i + 1], z = pointXyzc[4 * i + 2];
            float[] pixel = project(pose, intrinsics, x, y, z);
            if (pixel == null || !Float.isFinite(pointXyzc[4 * i + 3])) continue;
            points.put(withId(pointIds[i], x, y, z, pixel[0], pixel[1], pointXyzc[4 * i + 3]));
        }
        Report.put(a, "points", points);
        if (depthLe != null) {
            JSONObject depth = new JSONObject();
            Report.put(depth, "t_ns", depthTNs);
            Report.put(depth, "width", depthWidth);
            Report.put(depth, "height", depthHeight);
            Report.put(depth, "intrinsics", numbers(depthIntrinsics));
            Report.put(depth, "bytes", depthLe.length);
            Report.put(depth, "confidence_bytes", confidence.length);
            Report.put(a, "depth", depth);
        }
        if (anchorId >= 0) {
            JSONObject anchor = new JSONObject();
            Report.put(anchor, "id", anchorId);
            Report.put(anchor, "pose", numbers(anchorPose));
            Report.put(a, "anchor", anchor);
        }
        JSONArray anchors = new JSONArray();
        for (int i = 0; i < correctionIds.length; i++) anchors.put(withId(correctionIds[i], correctionPoses[i]));
        Report.put(a, "anchors", anchors);
        return a;
    }

    int depthBytes() {
        return depthLe == null ? 0 : depthLe.length + confidence.length;
    }

    /** Depth (uint16 little-endian mm), then confidence (uint8), into out at the given offset. */
    void writeDepth(byte[] out, int at) {
        if (depthLe == null) return;
        System.arraycopy(depthLe, 0, out, at, depthLe.length);
        System.arraycopy(confidence, 0, out, at + depthLe.length, confidence.length);
    }

    /** Pixel (u, v) of a world point seen from an ARCore pose (camera looks along -z, y up); null when behind the camera. */
    static float[] project(float[] pose, float[] k, float x, float y, float z) {
        float[] c = rotate(-pose[3], -pose[4], -pose[5], pose[6], x - pose[0], y - pose[1], z - pose[2]);
        if (!(c[2] < 0) || !Float.isFinite(c[2])) return null;
        float u = k[2] + k[0] * c[0] / -c[2], v = k[3] - k[1] * c[1] / -c[2];
        // One non-finite point makes Android's JSON serialization fail for the entire frame.
        return Float.isFinite(u) && Float.isFinite(v) ? new float[]{u, v} : null;
    }

    /** True when an anchor pose has moved more than MOVE_METRES or turned more than TURN_DEGREES. */
    static boolean moved(float[] before, float[] after) {
        double dx = after[0] - before[0], dy = after[1] - before[1], dz = after[2] - before[2];
        double dot = Math.abs(before[3] * after[3] + before[4] * after[4] + before[5] * after[5] + before[6] * after[6]);
        double degrees = Math.toDegrees(2 * Math.acos(Math.min(1.0, dot)));
        return Math.sqrt(dx * dx + dy * dy + dz * dz) > MOVE_METRES || degrees > TURN_DEGREES;
    }

    /** Rotates (x, y, z) by the unit quaternion (qx, qy, qz, qw): v + 2w (u x v) + 2 u x (u x v). */
    private static float[] rotate(float qx, float qy, float qz, float qw, float x, float y, float z) {
        float tx = 2 * (qy * z - qz * y), ty = 2 * (qz * x - qx * z), tz = 2 * (qx * y - qy * x);
        return new float[]{x + qw * tx + (qy * tz - qz * ty), y + qw * ty + (qz * tx - qx * tz), z + qw * tz + (qx * ty - qy * tx)};
    }

    static JSONArray numbers(float... values) {
        JSONArray out = new JSONArray();
        for (float v : values) out.put(Double.valueOf(v));  // put(Object) has no checked exception
        return out;
    }

    /** [id, values...]; the id stays an integer (ARCore ids can exceed a float's exact range). */
    private static JSONArray withId(int id, float... values) {
        JSONArray out = new JSONArray().put(Integer.valueOf(id));
        for (float v : values) out.put(Double.valueOf(v));
        return out;
    }
}
