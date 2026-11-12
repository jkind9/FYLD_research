package org.fyld.capture;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

import org.json.JSONException;
import org.json.JSONObject;
import org.junit.Test;

import java.io.IOException;

public class FrameJsonTest {
    private static final float[] POSE = {0, 0, 0, 0, 0, 0, 1};
    private static final float[] K = {400, 400, 320, 240};

    @Test
    public void unprojectablePointsDoNotEnterFrameJson() throws Exception {
        ArcoreRecord a = new ArcoreRecord();
        a.tracking = "TRACKING";
        a.failure = "NONE";
        a.pose = POSE;
        a.devicePose = POSE;
        a.intrinsics = K;
        a.textureIntrinsics = K;
        a.pointIds = new int[]{1, 2, 3, 4, 5};
        a.pointXyzc = new float[]{
                0, 0, -1, 1,
                Float.NaN, 0, -1, 1,
                0, Float.POSITIVE_INFINITY, -1, 1,
                1, 0, -Float.MIN_VALUE, 1,
                0, 0, -1, Float.NaN};
        JSONObject record = a.json();
        assertEquals(1, record.getJSONArray("points").length());
        assertEquals(1, record.getJSONArray("points").getJSONArray(0).getInt(0));
        assertNotNull(record.toString());
    }

    @Test
    public void projectionRejectsNonFiniteCoordinatesAndOverflow() {
        assertNull(ArcoreRecord.project(POSE, K, Float.NaN, 0, -1));
        assertNull(ArcoreRecord.project(POSE, K, 0, 0, Float.NEGATIVE_INFINITY));
        assertNull(ArcoreRecord.project(POSE, K, 1, 0, -Float.MIN_VALUE));
    }

    @Test
    public void androidSerializationFailureBecomesAQueueWriteError() {
        JSONObject invalid = new JSONObject() {
            @Override public String toString() { return null; }
            @Override public String toString(int spaces) throws JSONException {
                throw new JSONException("Forbidden numeric value: NaN");
            }
        };
        IOException error = assertThrows(IOException.class, () -> SessionMessages.encode(invalid, new byte[0]));
        assertTrue(error.getMessage().contains("NaN"));
    }
}
