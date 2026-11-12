package org.fyld.capture;

import android.content.Context;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.os.Build;
import android.os.SystemClock;

import com.google.ar.core.CameraConfig;
import com.google.ar.core.Config;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** The parts of a session's hello.info (phone_session_v2.md) that describe the phone, its camera and its clocks. */
final class RecordingMeta {
    private RecordingMeta() {
    }

    /** Both Android clocks at one moment: they differ by the time the phone has slept since boot. */
    static JSONObject clock() throws JSONException {
        return new JSONObject()
                .put("elapsed_realtime_ns", SystemClock.elapsedRealtimeNanos())
                .put("nano_time_ns", System.nanoTime())
                .put("wall_ms", System.currentTimeMillis());
    }

    static JSONObject device(Context context) throws JSONException {
        JSONObject out = new JSONObject()
                .put("manufacturer", Build.MANUFACTURER).put("model", Build.MODEL).put("device", Build.DEVICE)
                .put("android", Build.VERSION.RELEASE).put("sdk", Build.VERSION.SDK_INT).put("fingerprint", Build.FINGERPRINT);
        try {
            out.put("arcore_apk_version", context.getPackageManager().getPackageInfo("com.google.ar.core", 0).versionName);
        } catch (Exception e) {
            out.put("arcore_apk_version", JSONObject.NULL);
        }
        return out;
    }

    static JSONObject camera(Context context, String id) throws JSONException {
        JSONObject out = new JSONObject().put("id", id).put("size", new JSONArray().put(SharedCameraRig.WIDTH).put(SharedCameraRig.HEIGHT))
                .put("format", "YUV_420_888; grey = luminance plane, colour = JPEG of the same image");
        try {
            CameraCharacteristics c = context.getSystemService(CameraManager.class).getCameraCharacteristics(id);
            Integer source = c.get(CameraCharacteristics.SENSOR_INFO_TIMESTAMP_SOURCE);
            out.put("timestamp_source", source == null ? "MISSING"
                    : source == CameraCharacteristics.SENSOR_INFO_TIMESTAMP_SOURCE_REALTIME ? "REALTIME" : "UNKNOWN");
            put(out, "sensor_orientation_deg", c.get(CameraCharacteristics.SENSOR_ORIENTATION));
            put(out, "intrinsic_calibration", c.get(CameraCharacteristics.LENS_INTRINSIC_CALIBRATION));
            put(out, "distortion", c.get(CameraCharacteristics.LENS_DISTORTION));
            put(out, "pose_rotation", c.get(CameraCharacteristics.LENS_POSE_ROTATION));
            put(out, "pose_translation", c.get(CameraCharacteristics.LENS_POSE_TRANSLATION));
            put(out, "pose_reference", c.get(CameraCharacteristics.LENS_POSE_REFERENCE));
            put(out, "active_array", c.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE));
            put(out, "pixel_array", c.get(CameraCharacteristics.SENSOR_INFO_PIXEL_ARRAY_SIZE));
            put(out, "hyperfocal_distance_dpt", c.get(CameraCharacteristics.LENS_INFO_HYPERFOCAL_DISTANCE));
            put(out, "focus_distance_calibration", c.get(CameraCharacteristics.LENS_INFO_FOCUS_DISTANCE_CALIBRATION));
            put(out, "optical_stabilization_modes", c.get(CameraCharacteristics.LENS_INFO_AVAILABLE_OPTICAL_STABILIZATION));
        } catch (CameraAccessException e) {
            out.put("characteristics_error", e.getMessage());
        }
        return out;
    }

    static JSONObject arcore(CameraConfig config, Config.DepthMode depth, Config.FocusMode focus) throws JSONException {
        return new JSONObject()
                .put("cpu_image", new JSONArray().put(config.getImageSize().getWidth()).put(config.getImageSize().getHeight()))
                .put("texture", new JSONArray().put(config.getTextureSize().getWidth()).put(config.getTextureSize().getHeight()))
                .put("fps", config.getFpsRange().toString())
                .put("depth_mode", depth.name())
                .put("focus_mode", focus.name())
                .put("pose_convention", "camera-to-world; OpenGL camera axes: x right, y up, looking down -z; at the centre of exposure of the middle row");
    }

    private static void put(JSONObject out, String key, Object value) throws JSONException {
        if (value == null) out.put(key, JSONObject.NULL);
        else if (value.getClass().isArray()) out.put(key, new JSONArray(value));
        else if (value instanceof Number) out.put(key, value);
        else out.put(key, value.toString());
    }
}
