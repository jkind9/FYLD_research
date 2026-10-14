package org.fyld.rawrecorder;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.ImageFormat;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.TotalCaptureResult;
import android.media.Image;
import android.media.ImageReader;
import android.os.Handler;
import android.os.HandlerThread;
import android.view.Surface;

import com.google.ar.core.Session;
import com.google.ar.core.SharedCamera;
import com.google.ar.core.exceptions.CameraNotAvailableException;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Opens the camera through ARCore's shared-camera mode, following Google's documented order
 * (developers.google.com/ar/develop/java/camera-sharing): the app's own ImageReader is registered with
 * setAppSurfaces, the camera is opened with ARCore's wrapped callbacks, and ARCore resumes once the capture
 * session is active. While ARCore runs it issues the capture requests and the app's surface receives every image.
 */
final class SharedCameraRig {
    static final int WIDTH = 640, HEIGHT = 480;

    interface Listener {
        void onImage(Image image);

        void onCapture(TotalCaptureResult result);

        void onCameraError(String message);
    }

    private final HandlerThread thread = new HandlerThread("camera");
    private final Handler handler;
    private final CameraManager manager;
    private final Session session;
    private final SharedCamera shared;
    private final Listener listener;
    final String cameraId;
    private ImageReader reader;
    private CameraDevice device;
    private CameraCaptureSession capture;
    private CaptureRequest.Builder request;
    private volatile boolean arActive;

    SharedCameraRig(Context context, Session session, Listener listener) {
        thread.start();
        handler = new Handler(thread.getLooper());
        manager = context.getSystemService(CameraManager.class);
        this.session = session;
        this.listener = listener;
        shared = session.getSharedCamera();
        cameraId = session.getCameraConfig().getCameraId();
    }

    boolean arActive() {
        return arActive;
    }

    @SuppressLint("MissingPermission")  // the activity holds the camera permission before opening
    void open() {
        reader = ImageReader.newInstance(WIDTH, HEIGHT, ImageFormat.YUV_420_888, 4);
        reader.setOnImageAvailableListener(r -> {
            Image image = r.acquireNextImage();
            if (image == null) return;
            try {
                listener.onImage(image);
            } finally {
                image.close();
            }
        }, handler);
        shared.setAppSurfaces(cameraId, Collections.singletonList(reader.getSurface()));
        try {
            manager.openCamera(cameraId, shared.createARDeviceStateCallback(deviceCallback, handler), handler);
        } catch (CameraAccessException e) {
            listener.onCameraError("camera would not open: " + e.getMessage());
        }
    }

    void close() {
        if (arActive) {
            session.pause();
            arActive = false;
        }
        if (capture != null) capture.close();
        if (device != null) device.close();
        if (reader != null) reader.close();
        capture = null;
        device = null;
        reader = null;
    }

    void quit() {
        thread.quitSafely();
    }

    private final CameraDevice.StateCallback deviceCallback = new CameraDevice.StateCallback() {
        @Override
        public void onOpened(CameraDevice opened) {
            device = opened;
            try {
                request = opened.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
                List<Surface> surfaces = new ArrayList<>(shared.getArCoreSurfaces());
                surfaces.add(reader.getSurface());
                for (Surface surface : surfaces) request.addTarget(surface);
                opened.createCaptureSession(surfaces, shared.createARSessionStateCallback(sessionCallback, handler), handler);
            } catch (CameraAccessException e) {
                listener.onCameraError("camera session failed: " + e.getMessage());
            }
        }

        @Override
        public void onDisconnected(CameraDevice lost) {
            lost.close();
            device = null;
        }

        @Override
        public void onError(CameraDevice failed, int error) {
            failed.close();
            device = null;
            listener.onCameraError("camera error " + error);
        }
    };

    private final CameraCaptureSession.StateCallback sessionCallback = new CameraCaptureSession.StateCallback() {
        @Override
        public void onConfigured(CameraCaptureSession configured) {
            capture = configured;
            try {
                configured.setRepeatingRequest(request.build(), captureCallback, handler);
            } catch (CameraAccessException e) {
                listener.onCameraError("camera request failed: " + e.getMessage());
            }
        }

        @Override
        public void onConfigureFailed(CameraCaptureSession failed) {
            listener.onCameraError("the camera refused this set of streams");
        }

        @Override
        public void onActive(CameraCaptureSession active) {
            if (arActive) return;
            try {
                session.resume();
                arActive = true;
                shared.setCaptureCallback(captureCallback, handler);
            } catch (CameraNotAvailableException e) {
                listener.onCameraError("ARCore could not take the camera: " + e.getMessage());
            }
        }
    };

    private final CameraCaptureSession.CaptureCallback captureCallback = new CameraCaptureSession.CaptureCallback() {
        @Override
        public void onCaptureCompleted(CameraCaptureSession s, CaptureRequest r, TotalCaptureResult result) {
            listener.onCapture(result);
        }
    };
}
