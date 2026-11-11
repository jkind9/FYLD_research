# Phone session v2: what the capture app records and how it reaches the PC

This is the one written definition of what the capture app (`capture/`, package `org.fyld.capture`) records and sends, and what the PC receiver (`host/capture_receiver.py`) accepts and saves. Version 1 ([phone_session_v1.md](phone_session_v1.md)) was a live stream that skipped frames when Wi-Fi slowed; version 2 keeps every camera frame.

- Java encoder: `capture/app/src/main/java/org/fyld/capture/SessionFrame.java`, `ArcoreRecord.java` and `SessionMessages.java`. The sender is `Uploader.java`; the queue on the phone is `DiskQueue.java`.
- Python reader: `host/session_v2.py`. Receiver: `host/capture_receiver.py`.
- Shared fixture: `capture/app/src/test/resources/session_v2/`. The JVM tests (`SessionV2Test.java`, run by `build/build-capture.sh`) must produce it, and `tests/test_session_v2.py` must read it to the values written there. A change to this file needs a change to both sides and to the fixture, or a new version number.

## How a recording travels

1. Every message the app records (frames, motion-sensor batches, telemetry, the end message) gets a **message number** `n`, counting from 0 per session with no gaps. The app writes each message to the phone's own storage at once, as the exact bytes it will send (the *queue*: one file per message).
2. A sender thread reads the queue in message-number order and sends it over TCP. Capture never waits for the network: a slow link only makes the queue longer.
3. The PC stores each message, then acknowledges it. An acknowledgement is *cumulative*: it names the highest message number the PC holds with no gap below it. The phone deletes a message's file only once an acknowledgement covers it.
4. The phone keeps up to **64 messages** sent but not yet acknowledged (the *window*), so it does not wait one round trip per frame. The older stop-and-wait measurement was 0.70 MB/s. Capture 1.2's completed Redmi session received 10.22 MB/s; the separate link-speed check measured 33.4 MB/s.
5. After Stop, the app queues the end message and keeps sending until the queue is empty. The screen shows frames and MB left and an estimated time; the screen stays on.
6. After a dropped connection, or one with no write, acknowledgement or idle moment for 20 s, the phone reconnects and sends `hello` again. The PC answers with the highest message number it holds with no gap, and the phone resends everything after it. A session left on the phone when the app closed is sent the next time the app runs with a computer address.

The link has no authentication or encryption. Use it on a local network only; sending over the internet needs a tunnel with authentication, which is out of scope.

## Connection and framing

The phone opens a TCP connection to the PC, **port 8766** (8765 stays free for the old v1 live stream). Every message, in both directions, uses `host/protocol.py` framing: a 4-byte big-endian header length, the UTF-8 JSON header, a 4-byte big-endian payload length, the payload.

| Direction | `type` | When | Payload |
|---|---|---|---|
| phone to PC | `hello` | first message on each session connection | empty |
| phone to PC | `frame` | one per Camera2 frame | grey image, colour JPEG, then depth and confidence when the header has `arcore.depth` |
| phone to PC | `imu` | a batch of motion-sensor samples, about every 100 ms | 36 bytes per sample (below) |
| phone to PC | `telemetry` | once a second while recording | empty |
| phone to PC | `end` | once, after Stop; the last message of the session | empty |
| PC to phone | `ack` | answer to `hello`, then after each stored message | empty |
| PC to phone | `error` | the PC refused a message and closes the connection | empty |
| phone to PC | `speed` | link-speed check, on its own connection | test bytes |
| phone to PC | `report` | check report, alone on its own connection | the report JSON (schema 1, `host/report.py`) |

Every queued message (`frame`, `imu`, `telemetry`, `end`) has `"version": 2`, `"session"` (the session id) and `"n"` (its message number).

### `hello`

`{"type": "hello", "version": 2, "session": "<id>", "wall_ms": <phone wall clock now>, "info": {...}}`

The session id is the app's folder name, for example `20261014_201500_walk`: letters, digits, `_` and `-` only. `info` is the same on every connection of a session and becomes the PC's `session.json`:

| Field | Meaning |
|---|---|
| `kind` | `"walk"` (camera, ARCore and motion sensors) or `"imu_only"` (motion sensors alone, camera closed, for the calibration rest recording) |
| `app` | `"org.fyld.capture <version>"` |
| `device` | `manufacturer`, `model`, `device`, `android`, `sdk`, `fingerprint`, `arcore_apk_version` |
| `camera` | walk only: Camera2 `id`, `size` `[640, 480]`, `timestamp_source` (`REALTIME` means the camera stamps on `elapsedRealtimeNanos`, like the motion sensors), sensor orientation, reported calibration, distortion, lens pose, active and pixel array sizes, focus calibration, optical stabilisation modes; `null` for `imu_only` |
| `arcore` | walk only: camera configuration (`cpu_image`, `texture` sizes, `fps` range), depth mode, focus mode, pose convention; `null` for `imu_only` |
| `imu` | `gyro` and `accel`: Android sensor type, name, vendor, version, resolution, maximum range, minimum delay (µs), FIFO size |
| `clock` | `{"start": {"elapsed_realtime_ns", "nano_time_ns", "wall_ms"}}`: both Android clocks and the wall clock read together at Start |
| `settings` | `jpeg_quality`, `grey_encoding`, `window`, `anchor_interval_s`, `arcore_wait_ms`, `imu_batch_ms`, `min_free_bytes` (the values in force) |

### `ack` and `error`

`{"type": "ack", "session": "<id>", "through": k}`: the PC holds messages 0..k with no gap; `k = -1` when it holds none. The first `ack` on a connection answers `hello`; the phone resends from `k + 1`.

`{"type": "error", "message": "<why>"}`: the PC refused a message. The PC closes the connection; the phone stops sending that session, keeps its files and shows the message.

## Clocks

| Clock | Where it appears | Notes |
|---|---|---|
| Android `elapsedRealtimeNanos` | `camera_t_ns`, IMU `t_ns`, `clock.*.elapsed_realtime_ns`, telemetry `elapsed_realtime_ns` | Camera2 `SENSOR_TIMESTAMP` is on this clock when `camera.timestamp_source` is `REALTIME`, as on the Redmi; the motion sensors always are. One clock for the camera and the motion sensors is what visual-inertial trackers need. |
| ARCore timestamp | `arcore.t_ns`, `arcore.depth.t_ns` | `Frame.getTimestamp()`; its zero is undefined, differences are exact. The frame is matched to its Camera2 image by `Frame.getAndroidCameraTimestamp()`, which equals `camera_t_ns` exactly. |
| Phone wall clock | `wall_ms` | `System.currentTimeMillis()`, milliseconds since 1970; only for matching to the PC's clock. |
| PC wall clock | `host_received_ms` (added by the PC) | milliseconds since 1970. |

## `frame`

One per Camera2 image delivered to the app. `seq` counts frames from 0 per session with no gaps; a frame the phone could not keep (counted in `dropped`) gets no `seq`.

| Field | Type, unit | Meaning |
|---|---|---|
| `seq` | integer | frame number |
| `camera_t_ns` | integer, ns, elapsedRealtime | Camera2 sensor timestamp: start of exposure of the first row |
| `wall_ms` | integer, ms | phone wall clock when the image reached the app |
| `camera` | object or `null` | the capture result with the same sensor timestamp; `null` if none arrived within 500 ms |
| `camera.exposure_ns` | integer, ns | `SENSOR_EXPOSURE_TIME` |
| `camera.frame_duration_ns` | integer, ns | `SENSOR_FRAME_DURATION` |
| `camera.rolling_shutter_skew_ns` | integer, ns | `SENSOR_ROLLING_SHUTTER_SKEW`: time from the first row's to the last row's start of exposure (readout) |
| `camera.focus_distance_dpt` | number, dioptres (1/m) | `LENS_FOCUS_DISTANCE` |
| `camera.iso` | integer | `SENSOR_SENSITIVITY` |
| `camera.ois_mode` | integer | `LENS_OPTICAL_STABILIZATION_MODE`: 0 off, 1 on |
| `grey` | object | `{"width": W, "height": H, "encoding": "raw" or "deflate", "bytes": N}`: the image's luminance plane, 8 bits per pixel, row by row, no padding; `raw` is `W*H` bytes, `deflate` is a zlib stream (Java `Deflater` level 1) that inflates to `W*H` bytes |
| `colour` | object | `{"format": "jpeg", "width": W, "height": H, "quality": 90, "bytes": N}`: the same Camera2 image in colour |
| `arcore` | object or `null` | ARCore's output for this image; `null` when ARCore did not process it within 500 ms (it can skip images when the screen redraw falls behind) |

Missing capture-result values (a phone that does not report one) are `null`. Width and height are the sensor's landscape orientation, 640 x 480 on the Redmi.

### `arcore`

| Field | Type, unit | Meaning |
|---|---|---|
| `t_ns` | integer, ns | ARCore timestamp |
| `tracking` | `"TRACKING"`, `"PAUSED"` or `"STOPPED"` | ARCore tracking state |
| `failure` | string | `TrackingFailureReason` name; `"NONE"` while tracking |
| `pose` | 7 numbers or `null` | camera pose `[tx, ty, tz, qx, qy, qz, qw]`, metres, camera to world, ARCore's camera axes; `null` unless tracking |
| `device_pose` | 7 numbers or `null` | `Frame.getAndroidSensorPose()`: the pose of the Android sensor coordinate frame (the frame the motion sensors report in), same convention; `null` unless tracking |
| `intrinsics` | 4 numbers, pixels | `[fx, fy, cx, cy]` of the 640 x 480 image (`Camera.getImageIntrinsics()`; the app's Camera2 image has the same size and field of view as ARCore's CPU image) |
| `texture_intrinsics` | 4 numbers, pixels | `Camera.getTextureIntrinsics()`, in pixels of the GPU texture (`info.arcore.texture`) |
| `points` | list | tracked points, `[id, x, y, z, u, v, confidence]`, exactly as in v1 |
| `depth` | object, optional | new raw depth only, exactly as in v1: `{"t_ns", "width", "height", "intrinsics", "bytes", "confidence_bytes"}` |
| `anchor` | object, optional | `{"id": k, "pose": [7]}` when this frame started a keyframe anchor, as in v1 |
| `anchors` | list | anchor corrections `[id, tx, ty, tz, qx, qy, qz, qw]`, as in v1 |

Coordinates, the projection of points to `u, v`, raw depth, keyframe anchors and corrections follow [phone_session_v1.md](phone_session_v1.md) word for word: world +Y up, ARCore camera +X right, +Y up, looking along -Z; a new anchor once every 1.0 s while tracking; a correction when an anchor moves more than 1 mm or 0.1 degrees. Anchor ids count from 0 per session.

Capture 1.2 omits points whose projection or confidence is non-finite, as well as points behind the camera; it retains the image. JSON does not represent NaN or infinity. If another header value cannot serialize, recording stops through the existing `write_error` path. No fields or wire version changed. A saved session can miss an anchor-creation record when the associated ARCore image has no delivered Camera2 image; readers must not assume anchor 0 is present. The completed Redmi session's first recorded anchor is 1, so live fusion binds each fragment to a received anchor and keeps that binding for later corrections.

### Payload

`grey.bytes` of grey, then `colour.bytes` of JPEG, then (when `arcore.depth` is present) `depth.bytes` of depth (unsigned 16-bit little-endian millimetres, 0 for none) and `depth.confidence_bytes` of confidence (unsigned 8-bit).

## `imu`

`{"type": "imu", "version": 2, "session", "n", "samples": k}`, with `36 * k` payload bytes: per sample, little-endian, `int64 t_ns`, `int32 sensor` (0 gyroscope, 1 accelerometer), then six `float32`: `x, y, z, bx, by, bz`.

- Gyroscope in rad/s, accelerometer in m/s², Android sensor axes, `t_ns` on elapsedRealtime.
- The app reads the *uncalibrated* sensors at the fastest rate (`SENSOR_DELAY_FASTEST`). `bx, by, bz` are Android's own bias estimate, which it has not subtracted. A phone without an uncalibrated sensor falls back to the calibrated one with zero bias columns, and `info.imu` names the type used.
- Samples are in arrival order. Each sensor's `t_ns` increases within a batch and across batches.

## `telemetry`

Once a second while recording:

| Field | Unit | Meaning |
|---|---|---|
| `elapsed_realtime_ns`, `wall_ms` | ns, ms | when it was taken |
| `battery_pct` | % | battery level |
| `thermal_status` | 0-6 | `PowerManager.getCurrentThermalStatus()` (0 none, 1 light ... 6 shutdown); -1 before Android 10 |
| `free_bytes` | bytes | free space on the app's storage |
| `queue_frames`, `queue_bytes` | frames, bytes | frames and bytes waiting on the phone (not yet acknowledged) |
| `frames_captured` | frames | Camera2 images delivered to the app |
| `frames_queued` | frames | frames written to the queue (= next `seq`) |
| `frames_sent`, `frames_acknowledged` | frames | frames the sender has sent and the PC has acknowledged, over all connections |
| `frames_dropped` | frames | images the phone could not keep because its writer fell behind |
| `arcore_update_ms` | ms | median `Session.update()` time over the last second; `null` with no ARCore |

## `end`

`{"type": "end", "version": 2, "session", "n", "reason", "clock": {"end": {...}}, "counts": {...}}`.

- `reason`: `stop` (the button), `low_storage` (under 1 GB free), `paused` (the app left the screen), `camera_error`, `write_error` (the phone could not write to its storage), or `interrupted` (the app was closed while recording; the next start of the app adds this end message, with empty `counts`, so the session can still be delivered).
- `clock.end` has the same three clocks as `clock.start`, read when Stop was pressed.
- `counts`: `frames` (frames queued), `frames_captured`, `frames_dropped`, `frames_without_arcore`, `frames_without_camera_settings`, `depth_frames`, `anchors`, `arcore_records_late` (ARCore records that came after their frame had been written), `gyro_samples`, `accel_samples`, `imu_batches`, `telemetry`.

## `speed` and `report`

Link-speed check (in *Run all checks*): on its own connection the phone sends 50 messages `{"type": "speed", "chunk": i, "chunks": 50}`, each with 1 MiB of payload, and waits for the PC's answer `{"type": "speed", "bytes": total, "seconds": s}` after the last. The phone reports `bytes / (its own seconds from first byte to answer)`.

`report`: as in v1; the PC saves it as `<out>/reports/<PC time>_<model>.json`.

## Checks the PC makes

`host/session_v2.py` refuses a message, and the receiver answers `error` and closes the connection, when: `version` is not 2; the session id is not the one in `hello` or has other characters; `n` is more than one past the last stored message (a gap); a frame's `seq` is not one past the previous frame's; grey `bytes` is not `W*H` for `raw`, or a `deflate` grey does not inflate to `W*H`; the colour image is not JPEG (`FF D8`) or not the grey's size; the payload length is not the sum of its parts; any v1 ARCore check fails (pose exactly when tracking, unit quaternions, depth sizes, points within 0.5 px of their projection); a device pose is present while not tracking; an `imu` payload is not `36 * samples` bytes, has a sensor code other than 0 or 1, or a sensor's `t_ns` goes backwards; a `telemetry` field is missing, or an `end` message lacks `reason`, `clock.end` or `counts`. A message with `n` at or below the last stored one is a resend: it is acknowledged and not stored again.

## Session folder on the PC

`<out>/<session id>/`:

| File | Contents |
|---|---|
| `session.json` | `hello.info` plus `session`, `version`; at the end also `clock.end`, `counts` and `end_reason` |
| `frames.jsonl` | one line per frame: its header (every field above, including `n`) plus `host_received_ms` |
| `cam0/<seq>.png` | grey image, lossless PNG (`seq` as 6 digits) |
| `frames/<seq>.jpg` | colour JPEG as sent |
| `depth/<seq>.bin` | for frames with new raw depth: depth then confidence, as in the payload |
| `imu.csv` | `sensor,t_ns,x,y,z,bx,by,bz`, `sensor` is `gyro` or `accel` |
| `telemetry.jsonl` | one line per telemetry message plus `host_received_ms` |
| `messages.jsonl` | one commit line per stored message: integer `n`, string `type`, payload `bytes`, `host_received_ms`, frame `seq` when applicable; `sizes` maps each appended log name to its committed length in bytes; `imu_last_ns` is the last elapsedRealtime timestamp for gyro and accel (or null); `end` contains the full end header when applicable |
| `hellos.jsonl` | one line per connection: `host_received_ms` and the phone's `wall_ms` from its `hello` |
| `summary.json` | written when `end` arrives: frames, missing frame numbers, frames with ARCore and with depth, IMU rates and gaps, a clock-base check, MB/s achieved, connections, and how long sending ran after capture stopped |

The PC writes a message's files before its complete, newline-terminated commit line in `messages.jsonl`. On recovery it discards an incomplete final commit line and trims `frames.jsonl`, `imu.csv` and `telemetry.jsonl` to their last committed byte lengths. Resending then overwrites an uncommitted image and appends its record once. The same rollback runs after a storage error without restarting the receiver. The last IMU timestamps survive reconnects, so the receiver still refuses samples that go backwards across batches. A committed end header restores `session.json` and `summary.json` if their writes were interrupted. Completion is reported only after the acknowledgement is flushed, including when a reconnect finds the session already complete.

The phone persists the highest assigned message number before deleting acknowledged files. If it stops after queuing an end message but before writing the separate end marker, reopening the queue recovers that marker from its last message. It therefore continues numbering without reusing an acknowledged number or adding another end message.

Clock-base check: the first camera, gyroscope and accelerometer stamps must each lie within 1 s of `clock.start.elapsed_realtime_ns`. Sending after Stop: the PC time the `end` message arrived minus the phone's Stop time, moved to the PC's clock by the offset measured at the last `hello` (`host_received_ms - wall_ms`, which includes one network delay of a few ms).

## Settings (version 2)

| Setting | Value | Source |
|---|---|---|
| Camera2 image | 640 x 480 YUV_420_888, every frame ARCore's capture requests produce (30 fps on the Redmi) | Task88; ARCore's CPU image size |
| Colour | JPEG quality 90 | proposed by Claude 2026-10-14, not owner-ruled |
| Grey | raw, or Deflater level 1 when *Run all checks* found that it pays (below) | proposed by Claude 2026-10-14, not owner-ruled |
| Window | 64 messages unacknowledged | proposed by Claude 2026-10-14, not owner-ruled |
| Wait for ARCore and capture result | 500 ms after the image | proposed by Claude 2026-10-14, not owner-ruled |
| Frames held in memory before the writer | 30; a full buffer drops the newest image and counts it | proposed by Claude 2026-10-14, not owner-ruled |
| IMU batch | every 100 ms | proposed by Claude 2026-10-14, not owner-ruled |
| Storage guard | refuse to start, and stop recording, below 1 GB free (10^9 bytes) | owner brief, 14 Oct 2026 |
| Reconnect | 1 s after a failure, growing to 5 s | proposed by Claude 2026-10-14, not owner-ruled |
| Read timeout; no-progress limit on the phone | 20 s on both sides; the phone also closes a connection whose writes have not moved for 20 s | proposed by Claude 2026-10-14, not owner-ruled |
| Keyframe anchors, corrections, focus | as v1; ARCore FIXED focus | Task87, Task88 |
| Port | 8766 | Task88 |

**When compression pays.** Deflate is chosen only when all three hold: it saves at least 10% of the grey bytes; JPEG plus deflate of one frame take at most 75% of the frame interval on the phone (25 ms at 30 fps), so the writer keeps up; and the measured link is slower than the raw data rate (grey + colour per frame times the frame rate), so sending is the bottleneck. Otherwise the CPU time buys nothing and grey is sent raw. Proposed by Claude 2026-10-14, not owner-ruled.

Data rate: raw 640 x 480 grey at 30 fps is 9.2 MB/s, the colour JPEG about 2 MB/s more. On a link slower than that the queue grows during the walk and empties afterwards; the screen shows how long that will take.
