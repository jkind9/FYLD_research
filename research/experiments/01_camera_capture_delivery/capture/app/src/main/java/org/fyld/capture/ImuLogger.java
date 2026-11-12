package org.fyld.capture;

import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Handler;
import android.os.HandlerThread;

import org.json.JSONObject;

import java.io.IOException;

/**
 * Reads the gyroscope (rad/s) and accelerometer (m/s^2) at the fastest rate the phone allows, on their own thread,
 * and queues them as phone session v2 imu batches every BATCH_MS. Prefers the uncalibrated sensors: Android's own
 * bias correction can jump during a recording, which a visual-inertial system would read as motion; Android's bias
 * estimates travel alongside in bx, by, bz.
 */
final class ImuLogger implements SensorEventListener {
    static final int BATCH_MS = 100, MAX_BATCH = 1024;

    private final SensorManager manager;
    final Sensor gyro, accel;
    private final long[] t = new long[MAX_BATCH];
    private final int[] sensor = new int[MAX_BATCH];
    private final float[] values = new float[6 * MAX_BATCH];
    private HandlerThread thread;
    private Handler handler;
    private DiskQueue queue;
    private int count;
    private volatile long gyroSamples, accelSamples, batches;
    private volatile String error;
    private final Runnable tick = new Runnable() {
        @Override
        public void run() {
            flush();
            handler.postDelayed(this, BATCH_MS);
        }
    };

    ImuLogger(Context context) {
        manager = context.getSystemService(SensorManager.class);
        gyro = pick(Sensor.TYPE_GYROSCOPE_UNCALIBRATED, Sensor.TYPE_GYROSCOPE);
        accel = pick(Sensor.TYPE_ACCELEROMETER_UNCALIBRATED, Sensor.TYPE_ACCELEROMETER);
    }

    private Sensor pick(int preferred, int fallback) {
        Sensor s = manager.getDefaultSensor(preferred);
        return s != null ? s : manager.getDefaultSensor(fallback);
    }

    void start(DiskQueue into) {
        queue = into;
        count = 0;
        gyroSamples = accelSamples = batches = 0;
        error = null;
        thread = new HandlerThread("imu");
        thread.start();
        handler = new Handler(thread.getLooper());
        manager.registerListener(this, gyro, SensorManager.SENSOR_DELAY_FASTEST, handler);
        manager.registerListener(this, accel, SensorManager.SENSOR_DELAY_FASTEST, handler);
        handler.postDelayed(tick, BATCH_MS);
    }

    /** Stops the sensors and queues the last batch. */
    void stop() throws InterruptedException {
        manager.unregisterListener(this);
        handler.post(() -> {
            handler.removeCallbacks(tick);
            flush();
        });
        thread.quitSafely();
        thread.join();
    }

    long gyroSamples() { return gyroSamples; }

    long accelSamples() { return accelSamples; }

    long batches() { return batches; }

    String error() { return error; }

    @Override
    public void onSensorChanged(SensorEvent event) {
        float[] v = event.values;
        boolean isGyro = event.sensor == gyro;
        t[count] = event.timestamp;
        sensor[count] = isGyro ? 0 : 1;
        for (int k = 0; k < 6; k++) values[6 * count + k] = k < 3 || v.length >= 6 ? v[k] : 0f;
        count++;
        if (isGyro) gyroSamples++;
        else accelSamples++;
        if (count == MAX_BATCH) flush();
    }

    @Override
    public void onAccuracyChanged(Sensor s, int accuracy) {
    }

    private void flush() {
        if (count == 0) return;
        try {
            queue.add(SessionMessages.imu(queue.id(), count), SessionMessages.imuPayload(t, sensor, values, count));
            batches++;
        } catch (IOException e) {
            error = "could not write motion-sensor batch: " + e.getMessage();
        }
        count = 0;
    }

    static JSONObject describe(Sensor s) {
        JSONObject out = new JSONObject();
        Report.put(out, "type", s.getStringType());
        Report.put(out, "name", s.getName());
        Report.put(out, "vendor", s.getVendor());
        Report.put(out, "version", s.getVersion());
        Report.put(out, "resolution", (double) s.getResolution());
        Report.put(out, "maximum_range", (double) s.getMaximumRange());
        Report.put(out, "min_delay_us", s.getMinDelay());
        Report.put(out, "fifo_reserved_events", s.getFifoReservedEventCount());
        return out;
    }
}
