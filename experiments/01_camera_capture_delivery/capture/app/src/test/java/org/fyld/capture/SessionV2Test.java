package org.fyld.capture;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Iterator;
import java.util.zip.Inflater;

/** The encoders must produce exactly the shared fixture (phone_session_v2.md) that host/session_v2.py reads. */
public class SessionV2Test {
    static final String SESSION = "20261014_201500_walk";
    private static final float[] POSE = {0.5f, 1.25f, -2f, 0.5f, 0.5f, 0.5f, 0.5f};
    private static final float[] K = {400f, 400f, 320f, 240f};

    static byte[] resource(String name) throws Exception {
        try (InputStream in = SessionV2Test.class.getResourceAsStream("/session_v2/" + name)) {
            return in.readAllBytes();
        }
    }

    static JSONObject json(String name) throws Exception {
        return new JSONObject(new String(resource(name), StandardCharsets.UTF_8));
    }

    private static ArcoreRecord fixtureArcore(byte[] payload) {
        ArcoreRecord a = new ArcoreRecord();
        a.tNs = 123456789000L;
        a.tracking = "TRACKING";
        a.failure = "NONE";
        a.pose = POSE;
        a.devicePose = new float[]{0.5f, 1.25f, -2f, 0f, 0f, 0f, 1f};
        a.intrinsics = K;
        a.textureIntrinsics = new float[]{500f, 500f, 960f, 540f};
        // the third point is behind the camera and must be left out
        a.pointIds = new int[]{11, 12, 13};
        a.pointXyzc = new float[]{-1.5f, 1.5f, -2.125f, 0.5f, -0.5f, 0.75f, -1.75f, 0.25f, 1.5f, 1.25f, -2f, 0.9f};
        a.depthTNs = 123456700000L;
        a.depthWidth = 4;
        a.depthHeight = 3;
        a.depthIntrinsics = new float[]{2.5f, 2.5f, 2f, 1.5f};
        a.depthLe = Arrays.copyOfRange(payload, 16, 40);
        a.confidence = Arrays.copyOfRange(payload, 40, 52);
        a.anchorId = 3;
        a.anchorPose = POSE;
        a.correctionIds = new int[]{1};
        a.correctionPoses = new float[][]{{0f, 0f, 0.0625f, 0f, 0f, 0f, 1f}};
        return a;
    }

    @Test
    public void encodesTheFrameFixture() throws Exception {
        byte[] payload = resource("frame.bin");
        SessionFrame f = new SessionFrame();
        f.seq = 7;
        f.cameraTNs = 5000123456789L;
        f.wallMs = 1760450000000L;
        f.camera = SessionFrame.cameraSettings(8000000L, 33333333L, 20000000L, 0.5f, 400, 0);
        f.width = 4;
        f.height = 3;
        f.grey = Arrays.copyOfRange(payload, 0, 12);
        f.jpeg = Arrays.copyOfRange(payload, 12, 16);
        f.jpegQuality = 90;
        f.arcore = fixtureArcore(payload);
        JSONObject header = Report.put(f.header(SESSION), "n", 12);
        assertSame(json("frame.json"), header);
        assertArrayEquals(payload, f.payload());
    }

    @Test
    public void encodesTheImuTelemetryEndAndHelloFixtures() throws Exception {
        long[] t = {5000120000000L, 5000121250000L, 5000122500000L};
        int[] sensor = {0, 1, 0};
        float[] values = {0.5f, -0.25f, 0.125f, 0.0078125f, 0f, -0.0078125f, 0f, 9.75f, -0.5f, 0f, 0f, 0f,
                0.75f, -0.25f, 0f, 0.0078125f, 0f, -0.0078125f};
        assertArrayEquals(resource("imu.bin"), SessionMessages.imuPayload(t, sensor, values, 3));
        assertSame(json("imu.json"), Report.put(SessionMessages.imu(SESSION, 3), "n", 13));

        JSONObject telemetry = SessionMessages.telemetry(SESSION, 5000200000000L, 1760450000077L, 81, 1, 52000000000L,
                42, 16800000L, 215, 214, 180, 172, 1, 6.5);
        assertSame(json("telemetry.json"), Report.put(telemetry, "n", 14));

        JSONObject expectedEnd = json("end.json");
        JSONObject end = SessionMessages.end(SESSION, "stop", expectedEnd.getJSONObject("clock").getJSONObject("end"),
                expectedEnd.getJSONObject("counts"));
        assertSame(expectedEnd, Report.put(end, "n", 15));

        JSONObject expectedHello = json("hello.json");
        JSONObject info = expectedHello.getJSONObject("info");
        assertSame(info.getJSONObject("settings"), SessionMessages.settings(90, "raw"));
        assertSame(expectedHello, SessionMessages.hello(SESSION, 1760449990000L, info));
    }

    @Test
    public void frameWithoutArcoreOrCaptureResultSendsNulls() throws Exception {
        SessionFrame f = new SessionFrame();
        f.width = 2;
        f.height = 1;
        f.grey = new byte[]{1, 2};
        f.jpeg = new byte[]{(byte) 0xff, (byte) 0xd8};
        JSONObject header = f.header(SESSION);
        assertTrue(header.isNull("arcore") && header.isNull("camera"));
        assertEquals(4, f.payload().length);
        assertTrue(SessionFrame.cameraSettings(null, 1L, null, null, 100, null).isNull("exposure_ns"));
    }

    @Test
    public void unavailableMeasurementsAreJsonNullInsteadOfCrashingTheReport() {
        JSONObject detail = Report.put(new JSONObject(), "link_megabytes_per_second", Double.NaN);
        assertTrue(detail.isNull("link_megabytes_per_second"));
    }

    @Test
    public void lostTrackingSendsNoPosesAndNoPoints() throws Exception {
        ArcoreRecord a = new ArcoreRecord();
        a.tracking = "PAUSED";
        a.failure = "INSUFFICIENT_FEATURES";
        a.intrinsics = K;
        a.textureIntrinsics = K;
        a.pointIds = new int[]{1};
        a.pointXyzc = new float[]{0f, 0f, -1f, 1f};
        JSONObject json = a.json();
        assertTrue(json.isNull("pose") && json.isNull("device_pose"));
        assertEquals(0, json.getJSONArray("points").length());
        assertTrue(!json.has("depth") && !json.has("anchor"));
        assertEquals(0, a.depthBytes());
    }

    @Test
    public void projectsLikeTheHost() {
        assertArrayEquals(new float[]{370f, 265f}, ArcoreRecord.project(POSE, K, -1.5f, 1.5f, -2.125f), 1e-3f);
        assertNull(ArcoreRecord.project(POSE, K, 1.5f, 1.25f, -2f));
    }

    @Test
    public void anchorMovesAreThresholded() {
        float[] a = {0f, 0f, 0f, 0f, 0f, 0f, 1f};
        assertFalse(ArcoreRecord.moved(a, new float[]{0.0005f, 0f, 0f, 0f, 0f, 0f, 1f}));
        assertTrue(ArcoreRecord.moved(a, new float[]{0.002f, 0f, 0f, 0f, 0f, 0f, 1f}));
        float half = (float) Math.toRadians(0.2) / 2;  // 0.2 degrees about z
        assertTrue(ArcoreRecord.moved(a, new float[]{0f, 0f, 0f, 0f, 0f, (float) Math.sin(half), (float) Math.cos(half)}));
    }

    @Test
    public void deflatedGreyInflatesBackExactly() throws Exception {
        byte[] grey = new byte[640 * 4];
        for (int i = 0; i < grey.length; i++) grey[i] = (byte) (i / 7);
        byte[] packed = FrameWriter.deflate(grey);
        assertTrue(packed.length < grey.length);
        Inflater inflater = new Inflater();
        inflater.setInput(packed);
        byte[] back = new byte[grey.length];
        assertEquals(grey.length, inflater.inflate(back));
        assertTrue(inflater.finished());
        assertArrayEquals(grey, back);
    }

    @Test
    public void deflatePaysOnlyWhenItSavesBytesKeepsUpAndTheLinkIsTheLimit() {
        // 307 200 grey + 70 000 JPEG bytes a frame at 30 fps is 11.3 MB/s raw
        assertTrue(FrameWriter.deflatePays(0.7, 6, 8, 33.3, 4.0, 307200, 70000));
        assertFalse("saves under 10%", FrameWriter.deflatePays(0.95, 6, 8, 33.3, 4.0, 307200, 70000));
        assertFalse("writer falls behind", FrameWriter.deflatePays(0.7, 20, 8, 33.3, 4.0, 307200, 70000));
        assertFalse("link carries raw", FrameWriter.deflatePays(0.7, 6, 8, 33.3, 20.0, 307200, 70000));
    }

    /** JSON equality with numbers compared by value (7 and 7.0 are the same), using only Android's org.json methods. */
    static void assertSame(Object expected, Object actual) throws Exception {
        assertTrue("differs from the fixture:\n" + actual + "\n" + expected, same(expected, actual));
    }

    private static boolean same(Object a, Object b) throws Exception {
        if (a instanceof Number && b instanceof Number) return ((Number) a).doubleValue() == ((Number) b).doubleValue();
        if (a instanceof JSONObject && b instanceof JSONObject) {
            JSONObject x = (JSONObject) a, y = (JSONObject) b;
            if (x.length() != y.length()) return false;
            for (Iterator<String> keys = x.keys(); keys.hasNext(); ) {
                String key = keys.next();
                if (!y.has(key) || !same(x.get(key), y.get(key))) return false;
            }
            return true;
        }
        if (a instanceof JSONArray && b instanceof JSONArray) {
            JSONArray x = (JSONArray) a, y = (JSONArray) b;
            if (x.length() != y.length()) return false;
            for (int i = 0; i < x.length(); i++) if (!same(x.get(i), y.get(i))) return false;
            return true;
        }
        return a.equals(b);
    }
}
