package org.fyld.rawrecorder;

import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Handler;
import android.os.HandlerThread;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;

/**
 * Logs the gyroscope (rad/s) and accelerometer (m/s^2) at the fastest rate the phone allows, on their own thread.
 * Prefers the uncalibrated sensors: Android's own bias correction can jump during a recording, which a
 * visual-inertial system would read as motion; their bias estimates are kept in columns bx, by, bz.
 */
final class ImuLogger implements SensorEventListener {
    static final String HEADER = "t_ns,x,y,z,bx,by,bz";

    private final SensorManager manager;
    final Sensor gyro, accel;
    private HandlerThread thread;
    private CsvLog gyroLog, accelLog;

    ImuLogger(Context context) {
        manager = context.getSystemService(SensorManager.class);
        gyro = pick(Sensor.TYPE_GYROSCOPE_UNCALIBRATED, Sensor.TYPE_GYROSCOPE);
        accel = pick(Sensor.TYPE_ACCELEROMETER_UNCALIBRATED, Sensor.TYPE_ACCELEROMETER);
    }

    private Sensor pick(int preferred, int fallback) {
        Sensor sensor = manager.getDefaultSensor(preferred);
        return sensor != null ? sensor : manager.getDefaultSensor(fallback);
    }

    void start(File dir) throws IOException {
        gyroLog = new CsvLog(new File(dir, "gyro.csv"), HEADER);
        accelLog = new CsvLog(new File(dir, "accel.csv"), HEADER);
        thread = new HandlerThread("imu");
        thread.start();
        Handler handler = new Handler(thread.getLooper());
        manager.registerListener(this, gyro, SensorManager.SENSOR_DELAY_FASTEST, handler);
        manager.registerListener(this, accel, SensorManager.SENSOR_DELAY_FASTEST, handler);
    }

    void stop() throws InterruptedException {
        manager.unregisterListener(this);
        thread.quitSafely();
        thread.join();
        gyroLog.close();
        accelLog.close();
    }

    long gyroSamples() {
        return gyroLog == null ? 0 : gyroLog.lines();
    }

    long accelSamples() {
        return accelLog == null ? 0 : accelLog.lines();
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        float[] v = event.values;
        String bias = v.length >= 6 ? v[3] + "," + v[4] + "," + v[5] : "0,0,0";
        (event.sensor == gyro ? gyroLog : accelLog).line(event.timestamp + "," + v[0] + "," + v[1] + "," + v[2] + "," + bias);
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
    }

    static JSONObject describe(Sensor sensor) throws JSONException {
        return new JSONObject()
                .put("type", sensor.getStringType())
                .put("name", sensor.getName())
                .put("vendor", sensor.getVendor())
                .put("version", sensor.getVersion())
                .put("resolution", sensor.getResolution())
                .put("maximum_range", sensor.getMaximumRange())
                .put("min_delay_us", sensor.getMinDelay())
                .put("fifo_reserved_events", sensor.getFifoReservedEventCount());
    }
}
