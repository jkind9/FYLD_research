# Phone session v1: the per-frame stream from the Redmi app to the computer

This is the one written definition of what the phone app (`phonecheck/`) sends and what the computer (`host/`) accepts. The Java encoder is `phonecheck/app/src/main/java/org/fyld/phonecheck/SessionFrame.java`; the Python reader is `host/session_v1.py`. Both are tested against the same example frame, the fixture in `phonecheck/app/src/test/resources/session_v1/` (`frame_header.json` and `frame_payload.bin`). A change to this file needs a change to both sides and to the fixture, or a new version number.

## Connection and framing

The phone opens a TCP connection to the computer (port 8765). Every message is: a 4-byte big-endian header length, the UTF-8 JSON header, a 4-byte big-endian payload length, the payload. The computer answers each frame message with that frame's `seq` as a 4-byte big-endian number (the acknowledgement); the phone waits for it before sending the next frame.

Messages:

| `type` | When | Payload |
|---|---|---|
| `session` | First message on a stream connection | empty |
| `frame` | One per camera image sent | image, then depth and confidence when the header has `depth` |
| `report` | Alone on its own connection, after a check run | the check report JSON (schema 1, see `host/report.py`) |

The `session` header: `{"type": "session", "version": 1, "device": {...}, "started_ms": <phone wall clock>}`. `device` has `manufacturer`, `model`, `android_release`, `api`.

## Frame header

| Field | Type | Meaning |
|---|---|---|
| `type` | `"frame"` | |
| `version` | `1` | |
| `seq` | integer | 0, 1, 2 ... per connection, in sending order |
| `t_ns` | integer | ARCore camera timestamp (`Frame.getTimestamp()`), nanoseconds; the clock's zero is undefined, differences are exact |
| `sent_ms` | integer | phone wall clock when the frame was queued, milliseconds since 1970 |
| `tracking` | `"TRACKING"`, `"PAUSED"` or `"STOPPED"` | ARCore tracking state |
| `failure` | string | ARCore's `TrackingFailureReason` name; `"NONE"` while tracking |
| `pose` | 7 numbers or `null` | camera pose as ARCore reported it for this frame: `[tx, ty, tz, qx, qy, qz, qw]`, metres; `null` unless `tracking` is `"TRACKING"` |
| `intrinsics` | 4 numbers | `[fx, fy, cx, cy]` in pixels of the sent image (`Camera.getImageIntrinsics()`) |
| `image` | object | `{"format": "jpeg", "width": W, "height": H, "bytes": N}`; the first N payload bytes |
| `points` | list | ARCore's tracked points seen by this frame, each `[id, x, y, z, u, v, confidence]`; empty unless tracking |
| `depth` | object, optional | present only when ARCore produced a new raw depth image since the last sent one (see below) |
| `anchor` | object, optional | `{"id": k, "pose": [7 numbers]}` when this frame started a new keyframe anchor |
| `anchors` | list | pose corrections: `[id, tx, ty, tz, qx, qy, qz, qw]` for each earlier anchor that ARCore has moved (see below) |

### Coordinates

- **World:** ARCore's world frame, metres, +Y up (against gravity). Its origin and heading are wherever tracking started.
- **Camera (ARCore, OpenGL axes):** +X right in the image, +Y up in the image, the camera looks along -Z. `pose` maps camera to world: `p_world = R(q) p_camera + t`. The pose is for the sensor's own orientation (the sent image is landscape, 640 x 480 on the Redmi), not the screen's.
- **Project axes (OpenCV):** the rest of this repository uses +X right, +Y down, looking along +Z. `host/session_v1.py` gives `world_from_camera_cv(pose) = world_from_camera(pose) @ diag(1, -1, -1, 1)`.
- **Pixel:** `u` across, `v` down, from the top-left of the sent image. A camera-frame point `(X, Y, Z)` with `Z < 0` appears at `u = cx + fx * X / -Z`, `v = cy - fy * Y / -Z`.

### Tracked points

From `Frame.acquirePointCloud()`: `id` is ARCore's point id (stable while ARCore follows the point), `x, y, z` the world position in metres, `confidence` ARCore's 0-1 value. `u, v` are computed on the phone from the world position with this frame's `pose` and `intrinsics` using the formula above. Points behind the camera are left out; points outside the image are kept (their `u, v` fall outside 0..W, 0..H). The computer refuses a frame whose `u, v` differ from its own projection by more than 0.5 pixels. Google describes the point cloud as for visualisation and debugging and says its format may change; the stream depends only on positions and ids.

### Raw depth

From `Frame.acquireRawDepthImage16Bits()` and `Frame.acquireRawDepthConfidenceImage()`. ARCore makes about 10 new depth images per second and reprojects the last one in between; a depth image is new when its timestamp differs from the previous one. The phone sends depth only when it is new.

`depth` = `{"t_ns": <depth image timestamp>, "width": w, "height": h, "intrinsics": [fx, fy, cx, cy], "bytes": w*h*2, "confidence_bytes": w*h}`.

- Payload after the image: `bytes` of depth, row by row, unsigned 16-bit little-endian millimetres to the camera plane (0 means no depth), then `confidence_bytes` of confidence, unsigned 8-bit, 0-255 (0 where depth is 0; Google suggests 128 as a usable cut-off).
- `intrinsics` are for the depth image: ARCore's GPU-texture intrinsics (`Camera.getTextureIntrinsics()`) with x values scaled by `w / texture width` and y values by `h / texture height`, as in Google's raw depth sample. The depth image covers the texture's field of view (16:9 on the Redmi), which is wider than the 4:3 CPU image.
- The depth image belongs to this frame's `pose`: a depth pixel `(x, y)` with depth `d` metres is the camera point `(d (x - cx) / fx, d (cy - y) / fy, -d)`.

### Pose corrections (anchors)

ARCore can move its estimate of where the camera has been, for example when it recognises a place it has seen before. It never re-reports old camera poses, but it does move *anchors*: fixed points in the world that it keeps consistent with its map (`Session.createAnchor`, `Frame.getUpdatedAnchors()`).

- While tracking, the phone starts a new anchor at the camera's pose once every 1.0 s; that frame's header carries `anchor` with the anchor's id and its pose at creation (the frame is a *keyframe*). Ids count from 0 per connection.
- When ARCore later moves an anchor by more than 1 mm or 0.1 degrees from the pose last sent for it, the next sent frame lists its new pose in `anchors`.
- The computer corrects anything built from a frame by attaching it to the newest keyframe at or before that frame. If that keyframe's anchor moved from `A_created` to `A_now`, then `world_from_camera_corrected = A_now A_created⁻¹ world_from_camera`.

## Checks the computer makes

`host/session_v1.py` refuses a frame (and the receiver closes the connection) when: the version is not 1; `pose` is missing while tracking or present while not; the quaternion's length is not within 0.001 of 1; the image is not JPEG (does not start `FF D8`); the payload length is not `image.bytes + depth.bytes + depth.confidence_bytes`; `depth.bytes` is not `w*h*2` or `confidence_bytes` not `w*h`; a point has the wrong number of values or its pixel is more than 0.5 px from the projection.

## Settings (version 1)

| Setting | Value | Source |
|---|---|---|
| Sent image | ARCore CPU image, 640 x 480, JPEG quality 80 | Task85 |
| Keyframe anchor interval | 1.0 s while tracking | proposed by Claude 2026-10-14, not owner-ruled |
| Correction threshold | 1 mm or 0.1 degrees | proposed by Claude 2026-10-14, not owner-ruled |
| Repeated camera images | skipped (the screen redraws at 60 Hz, the camera runs at 30 Hz) | |
| Port | 8765 | Task85 |
