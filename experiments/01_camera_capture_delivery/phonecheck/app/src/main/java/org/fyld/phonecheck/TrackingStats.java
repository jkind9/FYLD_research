package org.fyld.phonecheck;

import android.media.Image;

import com.google.ar.core.Camera;
import com.google.ar.core.CameraIntrinsics;
import com.google.ar.core.Frame;
import com.google.ar.core.PointCloud;
import com.google.ar.core.Pose;
import com.google.ar.core.TrackingState;
import com.google.ar.core.exceptions.NotYetAvailableException;

import org.json.JSONArray;
import org.json.JSONObject;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.ShortBuffer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Per-frame ARCore statistics for the tracking run, summarised into the report. Runs on the GL thread. */
final class TrackingStats {
    private final List<Double> updateMs = new ArrayList<>();
    private final Map<String, Integer> states = new HashMap<>();
    private final Map<String, Integer> failures = new HashMap<>();
    private final List<Integer> pointCounts = new ArrayList<>();
    private final List<Double> depthValid = new ArrayList<>();
    private final List<Double> depthConfidence = new ArrayList<>();
    private int depthWidth, depthHeight, frames;
    private double pathMetres;
    private float[] last;
    private JSONObject intrinsics;

    void add(Frame frame, double updateMillis, boolean depthEnabled) {
        frames++;
        updateMs.add(updateMillis);
        Camera camera = frame.getCamera();
        TrackingState state = camera.getTrackingState();
        states.merge(state.name(), 1, Integer::sum);
        if (state != TrackingState.TRACKING) {
            failures.merge(camera.getTrackingFailureReason().name(), 1, Integer::sum);
            return;
        }
        Pose pose = camera.getPose();
        float[] now = {pose.tx(), pose.ty(), pose.tz()};
        if (last != null) {
            pathMetres += Math.sqrt(Math.pow(now[0] - last[0], 2) + Math.pow(now[1] - last[1], 2) + Math.pow(now[2] - last[2], 2));
        }
        last = now;
        if (intrinsics == null) {
            CameraIntrinsics k = camera.getImageIntrinsics();
            intrinsics = new JSONObject();
            Report.put(intrinsics, "focal_px", floats(k.getFocalLength()));
            Report.put(intrinsics, "principal_px", floats(k.getPrincipalPoint()));
            int[] size = k.getImageDimensions();
            Report.put(intrinsics, "image_size", new JSONArray(java.util.Arrays.asList(size[0], size[1])));
        }
        try (PointCloud cloud = frame.acquirePointCloud()) {
            pointCounts.add(cloud.getPoints().remaining() / 4);
        }
        if (depthEnabled) addDepth(frame);
    }

    private void addDepth(Frame frame) {
        try (Image depth = frame.acquireRawDepthImage16Bits(); Image confidence = frame.acquireRawDepthConfidenceImage()) {
            depthWidth = depth.getWidth();
            depthHeight = depth.getHeight();
            ShortBuffer millimetres = depth.getPlanes()[0].getBuffer().order(ByteOrder.LITTLE_ENDIAN).asShortBuffer();
            ByteBuffer score = confidence.getPlanes()[0].getBuffer();
            int valid = 0, total = millimetres.remaining();
            long confidenceSum = 0;
            for (int i = 0; i < total; i++) {
                if (millimetres.get(i) != 0) {
                    valid++;
                    confidenceSum += score.get(i) & 0xff;
                }
            }
            depthValid.add(total == 0 ? 0.0 : (double) valid / total);
            depthConfidence.add(valid == 0 ? 0.0 : confidenceSum / (255.0 * valid));
        } catch (NotYetAvailableException e) {
            // depth arrives later than the first frames; counted by its absence
        }
    }

    int frames() { return frames; }

    int lastPoints() { return pointCounts.isEmpty() ? 0 : pointCounts.get(pointCounts.size() - 1); }

    double lastDepthValid() { return depthValid.isEmpty() ? Double.NaN : depthValid.get(depthValid.size() - 1); }

    double pathMetres() { return pathMetres; }

    double trackingFraction() { return frames == 0 ? 0 : states.getOrDefault("TRACKING", 0) / (double) frames; }

    int depthFrames() { return depthValid.size(); }

    int maxPoints() { return pointCounts.isEmpty() ? 0 : Collections.max(pointCounts); }

    JSONObject summary(double seconds) {
        JSONObject out = new JSONObject();
        Report.put(out, "seconds", seconds);
        Report.put(out, "frames", frames);
        Report.put(out, "frames_per_second", frames / seconds);
        Report.put(out, "tracking_fraction", trackingFraction());
        Report.put(out, "states", new JSONObject(states));
        Report.put(out, "failure_reasons", new JSONObject(failures));
        Report.put(out, "path_length_m", pathMetres);
        Report.put(out, "update_ms_median", percentile(updateMs, 50));
        Report.put(out, "update_ms_p95", percentile(updateMs, 95));
        Report.put(out, "points_per_frame_median", percentile(toDoubles(pointCounts), 50));
        Report.put(out, "depth_frames", depthValid.size());
        Report.put(out, "depth_size", new JSONArray(java.util.Arrays.asList(depthWidth, depthHeight)));
        Report.put(out, "depth_valid_fraction_median", percentile(depthValid, 50));
        Report.put(out, "depth_confidence_median", percentile(depthConfidence, 50));
        Report.put(out, "image_intrinsics", intrinsics == null ? JSONObject.NULL : intrinsics);
        return out;
    }

    static double percentile(List<Double> values, double p) {
        if (values.isEmpty()) return Double.NaN;
        List<Double> sorted = new ArrayList<>(values);
        Collections.sort(sorted);
        return sorted.get((int) Math.min(sorted.size() - 1, Math.round(p / 100.0 * (sorted.size() - 1))));
    }

    private static List<Double> toDoubles(List<Integer> values) {
        List<Double> out = new ArrayList<>();
        for (int v : values) out.add((double) v);
        return out;
    }

    private static JSONArray floats(float[] values) {
        JSONArray out = new JSONArray();
        for (float v : values) out.put(Double.valueOf(v));  // put(Object) has no checked exception
        return out;
    }
}
