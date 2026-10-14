package org.fyld.phonecheck;

import android.media.Image;

import com.google.ar.core.Anchor;
import com.google.ar.core.Camera;
import com.google.ar.core.CameraIntrinsics;
import com.google.ar.core.Frame;
import com.google.ar.core.PointCloud;
import com.google.ar.core.Pose;
import com.google.ar.core.Session;
import com.google.ar.core.TrackingState;
import com.google.ar.core.exceptions.NotYetAvailableException;

import java.nio.ByteBuffer;
import java.nio.FloatBuffer;
import java.nio.IntBuffer;
import java.util.ArrayList;
import java.util.List;

/**
 * Reads what phone session v1 sends from each ARCore frame: pose, tracking state, points, new raw depth,
 * keyframe anchors and their later corrections. One per stream connection; runs on the GL thread.
 */
final class FrameCapture {
    static final long ANCHOR_INTERVAL_NS = 1_000_000_000L;

    private final Session session;
    private final boolean depthEnabled;
    private final List<Anchor> anchors = new ArrayList<>();  // index = anchor id
    private final List<float[]> lastSentPoses = new ArrayList<>();
    private long seq, lastCameraNs = -1, lastDepthNs = -1, lastAnchorNs = Long.MIN_VALUE;
    private int depthFrames;

    FrameCapture(Session session, boolean depthEnabled) {
        this.session = session;
        this.depthEnabled = depthEnabled;
    }

    /** False when this frame shows the same camera image as the last captured one (the screen redraws faster). */
    boolean isNew(Frame frame) {
        return frame.getTimestamp() != lastCameraNs;
    }

    /** Everything except the JPEG, which HostStream adds after compressing on its own thread. */
    SessionFrame capture(Frame frame) {
        Camera camera = frame.getCamera();
        SessionFrame f = new SessionFrame();
        f.seq = seq++;
        f.tNs = lastCameraNs = frame.getTimestamp();
        f.sentMs = System.currentTimeMillis();
        f.tracking = camera.getTrackingState().name();
        f.failure = camera.getTrackingFailureReason().name();
        CameraIntrinsics k = camera.getImageIntrinsics();
        f.intrinsics = intrinsics(k, 1f, 1f);
        if (camera.getTrackingState() != TrackingState.TRACKING) return f;
        f.pose = pose(camera.getPose());
        try (PointCloud cloud = frame.acquirePointCloud()) {
            FloatBuffer points = cloud.getPoints();
            IntBuffer ids = cloud.getIds();
            f.pointXyzc = new float[points.remaining()];
            points.get(f.pointXyzc);
            f.pointIds = new int[ids.remaining()];
            ids.get(f.pointIds);
        }
        if (depthEnabled) addDepth(frame, camera, f);
        addCorrections(frame, f);
        if (f.tNs - lastAnchorNs >= ANCHOR_INTERVAL_NS) {
            Anchor anchor = session.createAnchor(camera.getPose());
            f.anchorId = anchors.size();
            f.anchorPose = pose(anchor.getPose());
            anchors.add(anchor);
            lastSentPoses.add(f.anchorPose);
            lastAnchorNs = f.tNs;
        }
        return f;
    }

    int depthFrames() { return depthFrames; }

    int anchorCount() { return anchors.size(); }

    void close() {
        for (Anchor anchor : anchors) anchor.detach();
    }

    private void addDepth(Frame frame, Camera camera, SessionFrame f) {
        try (Image depth = frame.acquireRawDepthImage16Bits(); Image confidence = frame.acquireRawDepthConfidenceImage()) {
            if (depth.getTimestamp() == lastDepthNs) return;
            lastDepthNs = depth.getTimestamp();
            int w = depth.getWidth(), h = depth.getHeight();
            CameraIntrinsics texture = camera.getTextureIntrinsics();
            int[] size = texture.getImageDimensions();
            f.depthTNs = depth.getTimestamp();
            f.depthWidth = w;
            f.depthHeight = h;
            f.depthIntrinsics = intrinsics(texture, w / (float) size[0], h / (float) size[1]);
            f.depthLe = rows(depth.getPlanes()[0], w * 2, h);
            f.confidence = rows(confidence.getPlanes()[0], w, h);
            depthFrames++;
        } catch (NotYetAvailableException e) {
            // ARCore needs some motion before its first depth image
        }
    }

    private void addCorrections(Frame frame, SessionFrame f) {
        List<Integer> ids = new ArrayList<>();
        List<float[]> poses = new ArrayList<>();
        for (Anchor anchor : frame.getUpdatedAnchors()) {
            int id = anchors.indexOf(anchor);
            if (id < 0 || anchor.getTrackingState() != TrackingState.TRACKING) continue;
            float[] now = pose(anchor.getPose());
            if (!SessionFrame.moved(lastSentPoses.get(id), now)) continue;
            lastSentPoses.set(id, now);
            ids.add(id);
            poses.add(now);
        }
        f.correctionIds = new int[ids.size()];
        for (int i = 0; i < ids.size(); i++) f.correctionIds[i] = ids.get(i);
        f.correctionPoses = poses.toArray(new float[0][]);
    }

    /** A plane's pixels without row padding; the depth plane is already little-endian. */
    private static byte[] rows(Image.Plane plane, int rowBytes, int height) {
        ByteBuffer buffer = plane.getBuffer();
        byte[] out = new byte[rowBytes * height];
        for (int r = 0; r < height; r++) {
            buffer.position(r * plane.getRowStride());
            buffer.get(out, r * rowBytes, rowBytes);
        }
        return out;
    }

    private static float[] intrinsics(CameraIntrinsics k, float scaleX, float scaleY) {
        float[] focal = k.getFocalLength(), centre = k.getPrincipalPoint();
        return new float[]{focal[0] * scaleX, focal[1] * scaleY, centre[0] * scaleX, centre[1] * scaleY};
    }

    private static float[] pose(Pose p) {
        return new float[]{p.tx(), p.ty(), p.tz(), p.qx(), p.qy(), p.qz(), p.qw()};
    }
}
