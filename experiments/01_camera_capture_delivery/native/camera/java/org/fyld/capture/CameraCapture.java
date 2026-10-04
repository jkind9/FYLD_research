package org.fyld.capture;

import android.content.Context;
import android.graphics.ImageFormat;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureFailure;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.CaptureResult;
import android.hardware.camera2.TotalCaptureResult;
import android.media.Image;
import android.media.ImageReader;
import android.os.Handler;
import android.util.Size;
import android.view.Surface;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

final class CameraCapture {
    interface Callback {
        void onComplete(JSONArray frames);
        void onFailure(String reason, JSONArray partialFiles);
    }

    private static final long TIMEOUT_MS = 20000;
    private final CameraManager manager;
    private final Handler handler;
    private final File sessionDirectory;
    private final String captureName;
    private final List<String> cameraIds;
    private final int displayRotationDegrees;
    private final Callback callback;
    private final Map<String, CameraDevice> devices = new HashMap<>();
    private final Map<String, CameraCaptureSession> sessions = new HashMap<>();
    private final Map<String, ImageReader> readers = new HashMap<>();
    private final Map<String, JSONObject> captureResults = new HashMap<>();
    private final Map<String, JSONObject> capturedImages = new HashMap<>();
    private boolean finished;

    CameraCapture(Context context, Handler handler, File sessionDirectory,
                  String captureName, List<String> cameraIds, int displayRotationDegrees,
                  Callback callback) {
        this.manager = (CameraManager) context.getSystemService(Context.CAMERA_SERVICE);
        this.handler = handler;
        this.sessionDirectory = sessionDirectory;
        this.captureName = safeName(captureName);
        this.cameraIds = new ArrayList<>(cameraIds);
        this.displayRotationDegrees = displayRotationDegrees;
        this.callback = callback;
    }

    void cancel(String reason) {
        handler.post(() -> fail(reason));
    }

    void start() {
        if (cameraIds.isEmpty() || new java.util.HashSet<>(cameraIds).size() != cameraIds.size()) {
            fail("Camera selection is empty or contains duplicate IDs");
            return;
        }
        handler.postDelayed(() -> fail("Camera capture timed out"), TIMEOUT_MS);
        try {
            for (String id : cameraIds) {
                CameraCharacteristics characteristics = manager.getCameraCharacteristics(id);
                Size size = smallestJpeg(characteristics);
                ImageReader reader = ImageReader.newInstance(size.getWidth(), size.getHeight(),
                        ImageFormat.JPEG, 2);
                readers.put(id, reader);
                reader.setOnImageAvailableListener(source -> receiveImage(id, source), handler);
                manager.openCamera(id, new CameraDevice.StateCallback() {
                    @Override
                    public void onOpened(CameraDevice camera) {
                        if (finished) {
                            camera.close();
                            return;
                        }
                        devices.put(id, camera);
                        if (devices.size() == cameraIds.size()) {
                            configureAll();
                        }
                    }

                    @Override
                    public void onDisconnected(CameraDevice camera) {
                        camera.close();
                        fail("Camera disconnected: " + id);
                    }

                    @Override
                    public void onError(CameraDevice camera, int error) {
                        camera.close();
                        fail("Camera open failed for " + id + " with code " + error);
                    }
                }, handler);
            }
        } catch (CameraAccessException | IOException | SecurityException error) {
            fail("Could not open camera session: " + error.getClass().getSimpleName() + ": " + error.getMessage());
        }
    }

    private void configureAll() {
        if (finished) return;
        for (String id : cameraIds) {
            try {
                devices.get(id).createCaptureSession(
                        Collections.singletonList(readers.get(id).getSurface()),
                        new CameraCaptureSession.StateCallback() {
                            @Override
                            public void onConfigured(CameraCaptureSession session) {
                                if (finished) {
                                    session.close();
                                    return;
                                }
                                sessions.put(id, session);
                                if (sessions.size() == cameraIds.size()) {
                                    captureAll();
                                }
                            }

                            @Override
                            public void onConfigureFailed(CameraCaptureSession session) {
                                session.close();
                                fail("Camera stream configuration failed for " + id);
                            }
                        }, handler);
            } catch (CameraAccessException | IllegalStateException error) {
                fail("Could not configure camera " + id + ": " + error.getMessage());
                return;
            }
        }
    }

    private void captureAll() {
        if (finished) return;
        for (String id : cameraIds) {
            try {
                CaptureRequest.Builder request = devices.get(id).createCaptureRequest(
                        CameraDevice.TEMPLATE_STILL_CAPTURE);
                request.addTarget(readers.get(id).getSurface());
                request.setTag(id);
                CameraCharacteristics characteristics = manager.getCameraCharacteristics(id);
                int jpegOrientation = jpegOrientation(characteristics);
                request.set(CaptureRequest.JPEG_ORIENTATION, jpegOrientation);
                sessions.get(id).capture(request.build(), new CameraCaptureSession.CaptureCallback() {
                    @Override
                    public void onCaptureCompleted(CameraCaptureSession session,
                                                   CaptureRequest request,
                                                   TotalCaptureResult result) {
                        captureResult(id, result, request.get(CaptureRequest.JPEG_ORIENTATION));
                    }

                    @Override
                    public void onCaptureFailed(CameraCaptureSession session,
                                                CaptureRequest request,
                                                CaptureFailure failure) {
                        fail("Camera request failed for " + id + " with reason " + failure.getReason());
                    }
                }, handler);
            } catch (CameraAccessException | IllegalStateException error) {
                fail("Could not request frame from " + id + ": " + error.getMessage());
                return;
            }
        }
    }

    private void captureResult(String id, TotalCaptureResult result, Integer requestedRotation) {
        try {
            JSONObject value = new JSONObject();
            Long timestamp = result.get(CaptureResult.SENSOR_TIMESTAMP);
            value.put("sensor_timestamp_ns", timestamp == null ? JSONObject.NULL : timestamp);
            value.put("frame_number", result.getFrameNumber());
            JSONArray crop = rect(result.get(CaptureResult.SCALER_CROP_REGION));
            value.put("crop_region", crop == null ? JSONObject.NULL : crop);
            CameraCharacteristics characteristics = manager.getCameraCharacteristics(id);
            value.put("timestamp_source", CameraReport.timestampSource(
                    characteristics.get(CameraCharacteristics.SENSOR_INFO_TIMESTAMP_SOURCE)));
            Integer resultRotation = result.get(CaptureResult.JPEG_ORIENTATION);
            Integer orientation = resultRotation == null ? requestedRotation : resultRotation;
            value.put("rotation_degrees", orientation == null ? JSONObject.NULL : orientation);
            value.put("rotation_source", resultRotation == null ? "capture_request" : "capture_result");
            value.put("display_rotation_degrees", displayRotationDegrees);
            captureResults.put(id, value);
            completeIfReady();
        } catch (CameraAccessException | JSONException error) {
            fail("Could not record capture result for " + id + ": " + error.getMessage());
        }
    }

    private void receiveImage(String id, ImageReader source) {
        Image image = source.acquireNextImage();
        if (image == null) return;
        try (Image current = image) {
            ByteBuffer buffer = current.getPlanes()[0].getBuffer();
            byte[] bytes = new byte[buffer.remaining()];
            buffer.get(bytes);
            String fileName = captureName + "_camera_" + safeName(id) + ".jpg";
            File output = new File(sessionDirectory, fileName);
            try (FileOutputStream stream = new FileOutputStream(output, false)) {
                stream.write(bytes);
                stream.getFD().sync();
            }
            long arrival = System.currentTimeMillis();
            capturedImages.put(id, CameraReport.frame(id, fileName, bytes,
                    current.getWidth(), current.getHeight(),
                    "unavailable", JSONObject.NULL, JSONObject.NULL,
                    current.getTimestamp(), JSONObject.NULL, JSONObject.NULL, arrival));
            completeIfReady();
        } catch (IOException | JSONException error) {
            fail("Could not save captured image for " + id + ": " + error.getMessage());
        }
    }

    private void completeIfReady() {
        if (finished || captureResults.size() != cameraIds.size()
                || capturedImages.size() != cameraIds.size()) return;
        JSONArray frames = new JSONArray();
        try {
            for (String id : cameraIds) {
                JSONObject image = capturedImages.get(id);
                JSONObject result = captureResults.get(id);
                JSONObject frame = new JSONObject(image.toString());
                frame.put("sensor_timestamp_ns", result.get("sensor_timestamp_ns"));
                frame.put("frame_number", result.get("frame_number"));
                frame.put("crop_region", result.get("crop_region"));
                frame.put("timestamp_source", result.get("timestamp_source"));
                frame.put("rotation_degrees", result.get("rotation_degrees"));
                frame.put("rotation_source", result.get("rotation_source"));
                frame.put("display_rotation_degrees", result.get("display_rotation_degrees"));
                frames.put(frame);
            }
            for (int index = 0; index < frames.length(); index++) {
                JSONObject frame = frames.getJSONObject(index);
                if (!hasCaptureMetadata(frame)) {
                    capturedImages.clear();
                    for (int frameIndex = 0; frameIndex < frames.length(); frameIndex++) {
                        capturedImages.put(frames.getJSONObject(frameIndex).getString("camera_id"),
                                frames.getJSONObject(frameIndex));
                    }
                    fail("Camera returned an image without complete timestamp or crop metadata");
                    return;
                }
            }
            finish();
            callback.onComplete(frames);
        } catch (JSONException error) {
            fail("Could not join image and sensor result: " + error.getMessage());
        }
    }

    private void fail(String reason) {
        if (finished) return;
        JSONArray partial = new JSONArray();
        try {
            for (String id : cameraIds) {
                JSONObject image = capturedImages.get(id);
                if (image != null) {
                    JSONObject result = captureResults.get(id);
                    if (result != null) {
                        image.put("sensor_timestamp_ns", result.opt("sensor_timestamp_ns"));
                        image.put("frame_number", result.opt("frame_number"));
                        image.put("crop_region", result.opt("crop_region"));
                        image.put("timestamp_source", result.opt("timestamp_source"));
                        image.put("rotation_degrees", result.opt("rotation_degrees"));
                        image.put("rotation_source", result.opt("rotation_source"));
                        image.put("display_rotation_degrees", result.opt("display_rotation_degrees"));
                    }
                    partial.put(image);
                }
            }
        } catch (JSONException error) {
            android.util.Log.e("CameraCapture", "Could not record partial camera metadata", error);
        }
        finish();
        callback.onFailure(reason, partial);
    }

    private void finish() {
        finished = true;
        for (CameraCaptureSession session : sessions.values()) session.close();
        for (CameraDevice camera : devices.values()) camera.close();
        for (ImageReader reader : readers.values()) reader.close();
    }

    private static Size smallestJpeg(CameraCharacteristics characteristics) throws IOException {
        android.hardware.camera2.params.StreamConfigurationMap map = characteristics.get(
                CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
        Size[] sizes = map == null ? null : map.getOutputSizes(ImageFormat.JPEG);
        if (sizes == null || sizes.length == 0) throw new IOException("No JPEG output size is advertised");
        Size selected = sizes[0];
        for (Size size : sizes) {
            if ((long) size.getWidth() * size.getHeight()
                    < (long) selected.getWidth() * selected.getHeight()) selected = size;
        }
        return selected;
    }

    private int jpegOrientation(CameraCharacteristics characteristics) {
        Integer sensor = characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
        Integer facing = characteristics.get(CameraCharacteristics.LENS_FACING);
        int sensorDegrees = sensor == null ? 0 : sensor;
        int orientation = sensorDegrees;
        if (facing != null && facing == CameraCharacteristics.LENS_FACING_FRONT) {
            orientation += displayRotationDegrees;
        } else if (facing != null && facing == CameraCharacteristics.LENS_FACING_BACK) {
            orientation -= displayRotationDegrees;
        }
        return ((orientation % 360) + 360) % 360;
    }

    private static JSONArray rect(android.graphics.Rect value) {
        if (value == null) return null;
        return new JSONArray().put(value.left).put(value.top).put(value.right).put(value.bottom);
    }

    private static boolean hasCaptureMetadata(JSONObject frame) {
        Object timestamp = frame.opt("sensor_timestamp_ns");
        Object frameNumber = frame.opt("frame_number");
        Object crop = frame.opt("crop_region");
        Object rotation = frame.opt("rotation_degrees");
        JSONArray cropValues = crop instanceof JSONArray ? (JSONArray) crop : null;
        int rotationValue = rotation instanceof Number ? ((Number) rotation).intValue() : -1;
        return timestamp instanceof Number && ((Number) timestamp).longValue() >= 0
                && frameNumber instanceof Number && ((Number) frameNumber).longValue() >= 0
                && cropValues != null && cropValues.length() == 4
                && cropValues.optInt(2, 0) > cropValues.optInt(0, 0)
                && cropValues.optInt(3, 0) > cropValues.optInt(1, 0)
                && (rotationValue == 0 || rotationValue == 90
                    || rotationValue == 180 || rotationValue == 270);
    }

    private static String safeName(String value) {
        String safe = value.replaceAll("[^A-Za-z0-9_-]", "_");
        return safe.isEmpty() ? "camera" : safe;
    }
}
