package org.fyld.capture;

import android.content.Context;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.os.Build;
import android.util.Size;
import android.util.SizeF;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

final class CameraReport {
    static final int SCHEMA_VERSION = 1;

    private CameraReport() { }

    static JSONObject create(Context context) throws JSONException {
        CameraManager manager = (CameraManager) context.getSystemService(Context.CAMERA_SERVICE);
        JSONObject report = new JSONObject();
        report.put("schema_version", SCHEMA_VERSION);
        report.put("created_at_utc_ms", System.currentTimeMillis());
        report.put("device", deviceFields());
        report.put("permission", "granted");
        JSONArray cameras = new JSONArray();
        JSONArray checks = new JSONArray();
        report.put("cameras", cameras);
        report.put("checks", checks);
        try {
            for (String id : manager.getCameraIdList()) {
                cameras.put(cameraFields(manager, id));
            }
            addCheck(report, "camera_inventory", "PASS", null, cameras);
        } catch (CameraAccessException error) {
            addCheck(report, "camera_inventory", "FAIL", error.toString(), cameras);
        }
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            report.put("concurrent_camera_sets", new JSONArray());
            addCheck(report, "concurrent_camera_inventory", "SKIPPED",
                    "Concurrent camera inventory requires Android 11 or newer", null);
        } else {
            try {
                report.put("concurrent_camera_sets", concurrentSets(manager));
                addCheck(report, "concurrent_camera_inventory", "PASS", null,
                        report.getJSONArray("concurrent_camera_sets"));
            } catch (CameraAccessException error) {
                report.put("concurrent_camera_sets", new JSONArray());
                addCheck(report, "concurrent_camera_inventory", "FAIL", error.toString(), null);
            }
        }
        report.put("captures", new JSONArray());
        report.put("files", new JSONObject());
        return report;
    }

    static JSONObject deviceFields() throws JSONException {
        JSONObject device = new JSONObject();
        device.put("manufacturer", Build.MANUFACTURER);
        device.put("brand", Build.BRAND);
        device.put("model", Build.MODEL);
        device.put("device", Build.DEVICE);
        device.put("product", Build.PRODUCT);
        device.put("android_release", Build.VERSION.RELEASE);
        device.put("sdk_int", Build.VERSION.SDK_INT);
        device.put("build_id", Build.ID);
        return device;
    }

    private static JSONObject cameraFields(CameraManager manager, String id)
            throws CameraAccessException, JSONException {
        CameraCharacteristics characteristics = manager.getCameraCharacteristics(id);
        JSONObject camera = new JSONObject();
        camera.put("id", id);
        camera.put("lens_facing", lensFacing(characteristics.get(CameraCharacteristics.LENS_FACING)));
        camera.put("hardware_level", hardwareLevel(
                characteristics.get(CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL)));
        camera.put("sensor_orientation_degrees", number(
                characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION)));
        camera.put("timestamp_source", timestampSource(
                characteristics.get(CameraCharacteristics.SENSOR_INFO_TIMESTAMP_SOURCE)));
        camera.put("sensor_physical_size_mm", metadata(
                characteristics.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE)));
        camera.put("pixel_array_size", size(
                characteristics.get(CameraCharacteristics.SENSOR_INFO_PIXEL_ARRAY_SIZE)));
        camera.put("intrinsic_calibration", metadata(
                characteristics.get(CameraCharacteristics.LENS_INTRINSIC_CALIBRATION)));
        camera.put("lens_distortion", metadata(
                characteristics.get(CameraCharacteristics.LENS_DISTORTION)));
        camera.put("pose_rotation", metadata(
                characteristics.get(CameraCharacteristics.LENS_POSE_ROTATION)));
        camera.put("pose_translation_m", metadata(
                characteristics.get(CameraCharacteristics.LENS_POSE_TRANSLATION)));
        camera.put("sync_type", Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
                ? syncType(characteristics.get(CameraCharacteristics.LOGICAL_MULTI_CAMERA_SENSOR_SYNC_TYPE))
                : "unavailable_before_api_28");
        camera.put("physical_camera_ids", Build.VERSION.SDK_INT >= Build.VERSION_CODES.P
                ? strings(characteristics.getPhysicalCameraIds()) : JSONObject.NULL);
        camera.put("stream_configurations", streams(characteristics.get(
                CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP)));
        return camera;
    }

    private static JSONArray streams(StreamConfigurationMap map) throws JSONException {
        JSONArray output = new JSONArray();
        if (map == null) {
            return output;
        }
        int[] formats = map.getOutputFormats();
        if (formats == null) return output;
        for (int format : formats) {
            Size[] sizes = map.getOutputSizes(format);
            if (sizes == null) continue;
            JSONArray entries = new JSONArray();
            for (Size size : sizes) {
                JSONObject stream = new JSONObject();
                stream.put("width", size.getWidth());
                stream.put("height", size.getHeight());
                stream.put("minimum_frame_duration_ns", map.getOutputMinFrameDuration(format, size));
                entries.put(stream);
            }
            JSONObject configuration = new JSONObject();
            configuration.put("format", format);
            configuration.put("format_name", formatName(format));
            configuration.put("sizes", entries);
            output.put(configuration);
        }
        return output;
    }

    private static JSONArray concurrentSets(CameraManager manager)
            throws CameraAccessException, JSONException {
        JSONArray sets = new JSONArray();
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            return sets;
        }
        Set<Set<String>> groups = manager.getConcurrentCameraIds();
        List<List<String>> sorted = new ArrayList<>();
        for (Set<String> group : groups) {
            List<String> ids = new ArrayList<>(group);
            Collections.sort(ids);
            sorted.add(ids);
        }
        sorted.sort((left, right) -> String.join(",", left).compareTo(String.join(",", right)));
        for (List<String> group : sorted) {
            sets.put(new JSONArray(group));
        }
        return sets;
    }

    static void addCheck(JSONObject report, String name, String result, String reason,
                         JSONArray details) throws JSONException {
        if (!"PASS".equals(result) && !"FAIL".equals(result) && !"SKIPPED".equals(result)) {
            throw new IllegalArgumentException("Unknown check result: " + result);
        }
        if ("SKIPPED".equals(result) && (reason == null || reason.trim().isEmpty())) {
            throw new IllegalArgumentException("Skipped checks need a reason");
        }
        JSONObject check = new JSONObject();
        check.put("id", name);
        check.put("status", result);
        check.put("reason", reason == null ? "" : reason);
        check.put("details", details == null ? new JSONArray() : details);
        if (details != null) {
            for (int index = 0; index < details.length(); index++) {
                JSONObject frame = details.optJSONObject(index);
                if (frame == null || !frame.has("file")) continue;
                JSONObject file = new JSONObject();
                file.put("sha256", frame.getString("sha256"));
                file.put("bytes", frame.getInt("bytes"));
                report.getJSONObject("files").put(frame.getString("file"), file);
                if (isCompleteCapture(frame)) report.getJSONArray("captures").put(frame);
            }
        }
        report.getJSONArray("checks").put(check);
    }

    static JSONObject frame(String cameraId, String imageName, byte[] bytes, int width, int height,
                            String timestampSource, Object rotationDegrees, Object cropRegion,
                            long imageTimestampNs, Object sensorTimestampNs,
                            Object frameNumber, long arrivalTimestampMs) throws JSONException {
        JSONObject value = new JSONObject();
        value.put("camera_id", cameraId);
        value.put("file", imageName);
        value.put("sha256", sha256(bytes));
        value.put("bytes", bytes.length);
        value.put("width", width);
        value.put("height", height);
        value.put("image_timestamp_ns", imageTimestampNs);
        value.put("sensor_timestamp_ns", sensorTimestampNs);
        value.put("frame_number", frameNumber);
        value.put("arrival_utc_ms", arrivalTimestampMs);
        value.put("timestamp_source", timestampSource);
        value.put("rotation_degrees", rotationDegrees);
        value.put("crop_region", cropRegion == null ? JSONObject.NULL : cropRegion);
        return value;
    }

    private static boolean isCompleteCapture(JSONObject frame) {
        Object timestamp = frame.opt("sensor_timestamp_ns");
        Object number = frame.opt("frame_number");
        Object crop = frame.opt("crop_region");
        Object rotation = frame.opt("rotation_degrees");
        Object source = frame.opt("timestamp_source");
        JSONArray cropValues = crop instanceof JSONArray ? (JSONArray) crop : null;
        int rotationValue = rotation instanceof Number ? ((Number) rotation).intValue() : -1;
        return timestamp instanceof Number && ((Number) timestamp).longValue() >= 0
                && number instanceof Number && ((Number) number).longValue() >= 0
                && cropValues != null && cropValues.length() == 4
                && cropValues.optInt(2, 0) > cropValues.optInt(0, 0)
                && cropValues.optInt(3, 0) > cropValues.optInt(1, 0)
                && (rotationValue == 0 || rotationValue == 90
                    || rotationValue == 180 || rotationValue == 270)
                && source instanceof String && !((String) source).trim().isEmpty()
                && frame.optInt("width") > 0 && frame.optInt("height") > 0;
    }

    static File newSessionDirectory(Context context) throws IOException {
        File sessions = new File(context.getFilesDir(), "capture-sessions");
        if (!sessions.isDirectory() && !sessions.mkdirs()) {
            throw new IOException("Cannot create private capture directory");
        }
        File session = new File(sessions, "session-" + System.currentTimeMillis() + "_"
                + java.util.UUID.randomUUID().toString().substring(0, 8));
        if (!session.mkdir()) {
            throw new IOException("Cannot create a unique capture session");
        }
        return session;
    }

    static void writeReport(File session, JSONObject report) throws IOException {
        try {
            JSONObject capabilities = new JSONObject();
            capabilities.put("schema_version", SCHEMA_VERSION);
            capabilities.put("device", report.get("device"));
            capabilities.put("cameras", report.optJSONArray("cameras"));
            capabilities.put("concurrent_camera_sets", report.optJSONArray("concurrent_camera_sets"));
            byte[] capabilityBytes = (capabilities.toString(2) + "\n")
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8);
            try (FileOutputStream capabilityOutput = new FileOutputStream(
                    new File(session, "capabilities.json"), false)) {
                capabilityOutput.write(capabilityBytes);
                capabilityOutput.getFD().sync();
            }
            JSONObject capabilityRecord = new JSONObject();
            capabilityRecord.put("sha256", sha256(capabilityBytes));
            capabilityRecord.put("bytes", capabilityBytes.length);
            report.getJSONObject("files").put("capabilities.json", capabilityRecord);
            File destination = new File(session, "report.json");
            try (FileOutputStream output = new FileOutputStream(destination, false)) {
                output.write((report.toString(2) + "\n").getBytes(java.nio.charset.StandardCharsets.UTF_8));
                output.getFD().sync();
            }
        } catch (JSONException error) {
            throw new IOException("Could not serialize camera report", error);
        }
    }

    private static Object number(Integer value) {
        return value == null ? JSONObject.NULL : value;
    }

    private static Object size(android.util.Size value) throws JSONException {
        if (value == null) return JSONObject.NULL;
        return new JSONArray().put(value.getWidth()).put(value.getHeight());
    }

    private static Object metadata(float[] values) throws JSONException {
        JSONObject metadata = new JSONObject();
        metadata.put("available", values != null);
        metadata.put("value", values == null ? JSONObject.NULL : floats(values));
        if (values == null) metadata.put("reason", "Camera2 did not report this field");
        return metadata;
    }

    private static Object metadata(SizeF value) throws JSONException {
        JSONObject metadata = new JSONObject();
        metadata.put("available", value != null);
        metadata.put("value", value == null ? JSONObject.NULL
                : new JSONArray().put(value.getWidth()).put(value.getHeight()));
        if (value == null) metadata.put("reason", "Camera2 did not report this field");
        return metadata;
    }

    private static String formatName(int format) {
        switch (format) {
            case android.graphics.ImageFormat.JPEG: return "JPEG";
            case android.graphics.ImageFormat.YUV_420_888: return "YUV_420_888";
            case android.graphics.ImageFormat.RAW_SENSOR: return "RAW_SENSOR";
            case android.graphics.ImageFormat.PRIVATE: return "PRIVATE";
            case android.graphics.ImageFormat.DEPTH16: return "DEPTH16";
            case android.graphics.ImageFormat.RAW10: return "RAW10";
            case android.graphics.ImageFormat.RAW12: return "RAW12";
            default: return "unknown:" + format;
        }
    }

    private static JSONArray floats(float[] values) throws JSONException {
        JSONArray array = new JSONArray();
        if (values != null) {
            for (float value : values) {
                array.put(value);
            }
        }
        return array;
    }

    private static JSONArray strings(Set<String> values) throws JSONException {
        JSONArray array = new JSONArray();
        if (values != null) {
            List<String> sorted = new ArrayList<>(values);
            Collections.sort(sorted);
            for (String value : sorted) {
                array.put(value);
            }
        }
        return array;
    }

    private static String lensFacing(Integer value) {
        if (value == null) return "unavailable";
        if (value == CameraCharacteristics.LENS_FACING_BACK) return "back";
        if (value == CameraCharacteristics.LENS_FACING_FRONT) return "front";
        if (value == CameraCharacteristics.LENS_FACING_EXTERNAL) return "external";
        return "unknown:" + value;
    }

    private static String hardwareLevel(Integer value) {
        if (value == null) return "unavailable";
        switch (value) {
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_LEGACY: return "legacy";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_EXTERNAL: return "external";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_LIMITED: return "limited";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_FULL: return "full";
            case CameraCharacteristics.INFO_SUPPORTED_HARDWARE_LEVEL_3: return "level_3";
            default: return "unknown:" + value;
        }
    }

    static String timestampSource(Integer value) {
        if (value == null) return "unavailable";
        if (value == CameraCharacteristics.SENSOR_INFO_TIMESTAMP_SOURCE_REALTIME) return "realtime";
        if (value == CameraCharacteristics.SENSOR_INFO_TIMESTAMP_SOURCE_UNKNOWN) return "unknown";
        return "unknown_value:" + value;
    }

    private static String syncType(Integer value) {
        if (value == null) return "unavailable";
        if (value == CameraCharacteristics.LOGICAL_MULTI_CAMERA_SENSOR_SYNC_TYPE_APPROXIMATE) return "approximate";
        if (value == CameraCharacteristics.LOGICAL_MULTI_CAMERA_SENSOR_SYNC_TYPE_CALIBRATED) return "calibrated";
        return "unknown_value:" + value;
    }

    private static String sha256(byte[] bytes) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes);
            StringBuilder value = new StringBuilder(digest.length * 2);
            for (byte item : digest) {
                value.append(String.format(java.util.Locale.ROOT, "%02x", item & 0xff));
            }
            return value.toString();
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("SHA-256 is unavailable", error);
        }
    }
}
