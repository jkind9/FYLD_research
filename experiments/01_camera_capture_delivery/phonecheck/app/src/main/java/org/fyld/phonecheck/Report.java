package org.fyld.phonecheck;

import android.os.Build;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** The check report: schema 1, device identity and one entry per check (PASS, FAIL or SKIPPED with a reason). */
final class Report {
    private final JSONObject root = new JSONObject();
    private final JSONArray checks = new JSONArray();

    Report() {
        put(root, "schema", 1);
        put(root, "app_version", "0.2");
        put(root, "created_ms", System.currentTimeMillis());
        put(root, "device", device());
        put(root, "checks", checks);
    }

    static JSONObject device() {
        JSONObject device = new JSONObject();
        put(device, "manufacturer", Build.MANUFACTURER);
        put(device, "model", Build.MODEL);
        put(device, "device", Build.DEVICE);
        put(device, "android_release", Build.VERSION.RELEASE);
        put(device, "api", Build.VERSION.SDK_INT);
        put(device, "abis", new JSONArray(java.util.Arrays.asList(Build.SUPPORTED_ABIS)));
        return device;
    }

    synchronized void check(String name, String status, String reason, JSONObject detail) {
        JSONObject entry = new JSONObject();
        put(entry, "name", name);
        put(entry, "status", status);
        put(entry, "reason", reason == null ? "" : reason);
        put(entry, "detail", detail == null ? new JSONObject() : detail);
        checks.put(entry);
    }

    synchronized String json() {
        try {
            return root.toString(2);
        } catch (JSONException e) {
            throw new IllegalStateException(e);
        }
    }

    /** JSONObject.put without the checked exception; keys here are never null. */
    static JSONObject put(JSONObject object, String key, Object value) {
        try {
            return object.put(key, value);
        } catch (JSONException e) {
            throw new IllegalArgumentException(key, e);
        }
    }
}
