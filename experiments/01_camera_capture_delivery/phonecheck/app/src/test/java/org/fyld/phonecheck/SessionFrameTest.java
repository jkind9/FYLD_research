package org.fyld.phonecheck;

import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Test;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Iterator;

/** The encoder must produce exactly the shared fixture (phone_session_v1.md) that host/session_v1.py reads. */
public class SessionFrameTest {
    private static final float[] POSE = {0.5f, 1.25f, -2f, 0.5f, 0.5f, 0.5f, 0.5f};

    private static byte[] resource(String name) throws Exception {
        try (InputStream in = SessionFrameTest.class.getResourceAsStream("/session_v1/" + name)) {
            return in.readAllBytes();
        }
    }

    private static SessionFrame fixtureFrame(byte[] payload) {
        SessionFrame f = new SessionFrame();
        f.seq = 7;
        f.tNs = 123456789000L;
        f.sentMs = 1760450000000L;
        f.tracking = "TRACKING";
        f.failure = "NONE";
        f.pose = POSE;
        f.intrinsics = new float[]{400f, 400f, 320f, 240f};
        f.imageWidth = 640;
        f.imageHeight = 480;
        f.jpeg = Arrays.copyOfRange(payload, 0, 4);
        // the third point is behind the camera and must be left out
        f.pointIds = new int[]{11, 12, 13};
        f.pointXyzc = new float[]{-1.5f, 1.5f, -2.125f, 0.5f, -0.5f, 0.75f, -1.75f, 0.25f, 1.5f, 1.25f, -2f, 0.9f};
        f.depthTNs = 123456700000L;
        f.depthWidth = 4;
        f.depthHeight = 3;
        f.depthIntrinsics = new float[]{2.5f, 2.5f, 2f, 1.5f};
        f.depthLe = Arrays.copyOfRange(payload, 4, 28);
        f.confidence = Arrays.copyOfRange(payload, 28, 40);
        f.anchorId = 3;
        f.anchorPose = POSE;
        f.correctionIds = new int[]{1};
        f.correctionPoses = new float[][]{{0f, 0f, 0.0625f, 0f, 0f, 0f, 1f}};
        return f;
    }

    @Test
    public void encodesTheSharedFixture() throws Exception {
        byte[] payload = resource("frame_payload.bin");
        JSONObject expected = new JSONObject(new String(resource("frame_header.json"), StandardCharsets.UTF_8));
        SessionFrame f = fixtureFrame(payload);
        JSONObject header = f.header();
        assertTrue("header differs from the fixture:\n" + header + "\n" + expected, same(expected, header));
        assertArrayEquals(payload, f.payload());
    }

    /** JSON equality with numbers compared by value (7 and 7.0 are the same), using only Android's org.json methods. */
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

    @Test
    public void projectsLikeTheHost() {
        assertArrayEquals(new float[]{370f, 265f}, SessionFrame.project(POSE, new float[]{400f, 400f, 320f, 240f}, -1.5f, 1.5f, -2.125f), 1e-3f);
        assertNull(SessionFrame.project(POSE, new float[]{400f, 400f, 320f, 240f}, 1.5f, 1.25f, -2f));
    }

    @Test
    public void lostTrackingSendsNoPoseAndNoPoints() throws Exception {
        SessionFrame f = new SessionFrame();
        f.tracking = "PAUSED";
        f.failure = "INSUFFICIENT_FEATURES";
        f.intrinsics = new float[]{400f, 400f, 320f, 240f};
        f.jpeg = new byte[]{(byte) 0xff, (byte) 0xd8};
        JSONObject header = f.header();
        assertTrue(header.isNull("pose"));
        assertEquals(0, header.getJSONArray("points").length());
        assertEquals(0, header.getJSONArray("anchors").length());
        assertTrue(!header.has("depth") && !header.has("anchor"));
        assertEquals(2, f.payload().length);
    }

    @Test
    public void anchorMovesAreThresholded() {
        float[] a = {0f, 0f, 0f, 0f, 0f, 0f, 1f};
        assertTrue(!SessionFrame.moved(a, new float[]{0.0005f, 0f, 0f, 0f, 0f, 0f, 1f}));
        assertTrue(SessionFrame.moved(a, new float[]{0.002f, 0f, 0f, 0f, 0f, 0f, 1f}));
        float half = (float) Math.toRadians(0.2) / 2;  // 0.2 degrees about z
        assertTrue(SessionFrame.moved(a, new float[]{0f, 0f, 0f, 0f, 0f, (float) Math.sin(half), (float) Math.cos(half)}));
    }
}
