package org.fyld.capture;

import org.json.JSONObject;

/**
 * One phone session v2 frame (experiments/01_camera_capture_delivery/phone_session_v2.md) as plain values,
 * encoded to the JSON header and payload the PC reads. No Android or ARCore types, so it is tested on the JVM.
 */
final class SessionFrame {
    long seq, cameraTNs, wallMs;
    JSONObject camera;  // capture-result settings, or null when none matched this image
    int width, height;
    byte[] grey;  // luminance plane, raw or deflated
    String greyEncoding = "raw";
    byte[] jpeg;
    int jpegQuality;
    ArcoreRecord arcore;  // null when ARCore did not process this image

    /** The header without its message number, which DiskQueue adds. */
    JSONObject header(String session) {
        JSONObject h = SessionMessages.message("frame", session);
        Report.put(h, "seq", seq);
        Report.put(h, "camera_t_ns", cameraTNs);
        Report.put(h, "wall_ms", wallMs);
        Report.put(h, "camera", camera == null ? JSONObject.NULL : camera);
        JSONObject g = new JSONObject();
        Report.put(g, "width", width);
        Report.put(g, "height", height);
        Report.put(g, "encoding", greyEncoding);
        Report.put(g, "bytes", grey.length);
        Report.put(h, "grey", g);
        JSONObject c = new JSONObject();
        Report.put(c, "format", "jpeg");
        Report.put(c, "width", width);
        Report.put(c, "height", height);
        Report.put(c, "quality", jpegQuality);
        Report.put(c, "bytes", jpeg.length);
        Report.put(h, "colour", c);
        Report.put(h, "arcore", arcore == null ? JSONObject.NULL : arcore.json());
        return h;
    }

    /** Grey, then the colour JPEG, then depth and confidence when ARCore has new depth. */
    byte[] payload() {
        int depthBytes = arcore == null ? 0 : arcore.depthBytes();
        byte[] out = new byte[grey.length + jpeg.length + depthBytes];
        System.arraycopy(grey, 0, out, 0, grey.length);
        System.arraycopy(jpeg, 0, out, grey.length, jpeg.length);
        if (arcore != null) arcore.writeDepth(out, grey.length + jpeg.length);
        return out;
    }

    /** The capture result's settings; a value the phone did not report is null. */
    static JSONObject cameraSettings(Long exposureNs, Long frameDurationNs, Long rollingShutterSkewNs, Float focusDistanceDpt,
                                     Integer iso, Integer oisMode) {
        JSONObject s = new JSONObject();
        Report.put(s, "exposure_ns", orNull(exposureNs));
        Report.put(s, "frame_duration_ns", orNull(frameDurationNs));
        Report.put(s, "rolling_shutter_skew_ns", orNull(rollingShutterSkewNs));
        Report.put(s, "focus_distance_dpt", focusDistanceDpt == null ? JSONObject.NULL : Double.valueOf(focusDistanceDpt));
        Report.put(s, "iso", orNull(iso));
        Report.put(s, "ois_mode", orNull(oisMode));
        return s;
    }

    private static Object orNull(Object value) {
        return value == null ? JSONObject.NULL : value;
    }
}
