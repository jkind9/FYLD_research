"""Read and check phone session v2 messages and folders (experiments/01_camera_capture_delivery/phone_session_v2.md).

parse_frame, parse_imu, check_telemetry, check_end and check_hello check one received message each; read_session
reads a folder saved by capture_receiver.py. ARCore's per-frame record is checked by session_v1.parse_arcore, so v1
and v2 accept exactly the same ARCore values.
"""

from __future__ import annotations

import json
import re
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

import session_v1
from session_v1 import _intrinsics, _pose, _require

VERSION = 2
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{1,80}")
IMU_ROW = struct.Struct("<qi6f")
SENSORS = ("gyro", "accel")
CAMERA_FIELDS = ("exposure_ns", "frame_duration_ns", "rolling_shutter_skew_ns", "focus_distance_dpt", "iso", "ois_mode")
TELEMETRY_FIELDS = ("elapsed_realtime_ns", "wall_ms", "battery_pct", "thermal_status", "free_bytes", "queue_frames", "queue_bytes",
                    "frames_captured", "frames_queued", "frames_sent", "frames_acknowledged", "frames_dropped", "arcore_update_ms")
INFO_FIELDS = ("kind", "app", "device", "camera", "arcore", "imu", "clock", "settings")
KINDS = ("walk", "imu_only")


@dataclass(frozen=True)
class Frame(session_v1.Frame):
    """A v1 frame (so src/live reads either) plus what v2 adds; t_ns is the Camera2 timestamp in v2."""
    n: int
    camera_t_ns: int
    camera: dict | None
    grey: np.ndarray  # (h, w) uint8
    arcore_t_ns: int | None
    device_pose: tuple[float, ...] | None
    texture_intrinsics: tuple[float, float, float, float] | None

    @property
    def wall_ms(self) -> int:
        return self.sent_ms


@dataclass(frozen=True)
class ImuBatch:
    n: int
    t_ns: np.ndarray  # (k,) int64, elapsedRealtime
    sensor: np.ndarray  # (k,) 0 gyroscope, 1 accelerometer
    values: np.ndarray  # (k, 3) rad/s or m/s^2, uncalibrated
    bias: np.ndarray  # (k, 3) Android's bias estimate, not subtracted


def check_session_id(session) -> str:
    _require(isinstance(session, str) and SESSION_ID.fullmatch(session) is not None, f"bad session id {session!r}")
    return session


def check_queued(header: dict, kind: str) -> dict:
    """The envelope every queued message shares: type, version, session id and message number."""
    _require(header.get("type") == kind and header.get("version") == VERSION, f"{kind} must be type {kind}, version {VERSION}")
    check_session_id(header.get("session"))
    _require(isinstance(header.get("n"), int) and header["n"] >= 0, "n must be a whole number from 0")
    return header


def check_hello(header: dict) -> dict:
    _require(header.get("type") == "hello" and header.get("version") == VERSION, f"hello must be type hello, version {VERSION}")
    check_session_id(header.get("session"))
    info = header.get("info")
    _require(isinstance(info, dict) and all(k in info for k in INFO_FIELDS), f"hello info needs {INFO_FIELDS}")
    _require(info["kind"] in KINDS, f"kind must be one of {KINDS}")
    _require(isinstance(info["clock"].get("start", {}).get("elapsed_realtime_ns"), int), "hello needs clock.start.elapsed_realtime_ns")
    return header


def parse_frame(header: dict, payload: bytes) -> Frame:
    check_queued(header, "frame")
    _require(isinstance(header.get("seq"), int) and header["seq"] >= 0, "seq must be a whole number from 0")
    camera = header["camera"]
    _require(camera is None or set(camera) == set(CAMERA_FIELDS), f"camera needs exactly {CAMERA_FIELDS}")
    grey_header, colour = header["grey"], header["colour"]
    w, h, grey_bytes = grey_header["width"], grey_header["height"], grey_header["bytes"]
    _require(colour["format"] == "jpeg" and (colour["width"], colour["height"]) == (w, h), "colour must be a JPEG of the grey's size")
    packed = payload[:grey_bytes]
    if grey_header["encoding"] == "raw":
        _require(grey_bytes == w * h, "raw grey must be width x height bytes")
        pixels = packed
    else:
        _require(grey_header["encoding"] == "deflate", "grey encoding must be raw or deflate")
        try:
            pixels = zlib.decompress(packed)
        except zlib.error as e:
            raise ValueError(f"grey does not inflate: {e}") from e
        _require(len(pixels) == w * h, "deflated grey must inflate to width x height bytes")
    jpeg = payload[grey_bytes:grey_bytes + colour["bytes"]]
    _require(len(jpeg) == colour["bytes"] and jpeg[:2] == b"\xff\xd8", "colour image must be JPEG")
    rest = payload[grey_bytes + colour["bytes"]:]
    record = header["arcore"]
    if record is None:
        _require(not rest, "payload length does not match the header")
        fields = dict(tracking="NO_ARCORE", failure="NO_ARCORE", pose=None, intrinsics=None, point_ids=np.zeros(0, np.int64),
                      points_world=np.zeros((0, 3)), points_pixel=np.zeros((0, 2)), points_confidence=np.zeros(0), depth=None,
                      anchor_created=None, anchor_updates={})
        extra = dict(arcore_t_ns=None, device_pose=None, texture_intrinsics=None)
    else:
        fields = session_v1.parse_arcore(record, rest)
        device = record["device_pose"]
        _require((device is not None) == (fields["pose"] is not None), "device_pose must be given exactly when tracking")
        extra = dict(arcore_t_ns=int(record["t_ns"]), device_pose=_pose(device, "device_pose") if device is not None else None,
                     texture_intrinsics=_intrinsics(record["texture_intrinsics"], "texture_intrinsics"))
    return Frame(seq=header["seq"], t_ns=int(header["camera_t_ns"]), sent_ms=int(header["wall_ms"]), image_jpeg=jpeg,
                 image_size=(w, h), n=header["n"], camera_t_ns=int(header["camera_t_ns"]), camera=camera,
                 grey=np.frombuffer(pixels, np.uint8).reshape(h, w), **fields, **extra)


def parse_imu(header: dict, payload: bytes) -> ImuBatch:
    check_queued(header, "imu")
    count = header.get("samples")
    _require(isinstance(count, int) and count > 0 and len(payload) == IMU_ROW.size * count, "imu payload must be 36 bytes per sample")
    rows = np.array(list(IMU_ROW.iter_unpack(payload)), dtype=object)
    t, sensor = rows[:, 0].astype(np.int64), rows[:, 1].astype(np.int64)
    _require(np.isin(sensor, (0, 1)).all(), "imu sensor must be 0 (gyroscope) or 1 (accelerometer)")
    for code in (0, 1):
        _require(np.all(np.diff(t[sensor == code]) >= 0), f"{SENSORS[code]} timestamps go backwards")
    values = rows[:, 2:].astype(np.float64)
    return ImuBatch(header["n"], t, sensor, values[:, :3], values[:, 3:])


def check_telemetry(header: dict) -> dict:
    check_queued(header, "telemetry")
    _require(all(k in header for k in TELEMETRY_FIELDS), f"telemetry needs {TELEMETRY_FIELDS}")
    return header


def check_end(header: dict) -> dict:
    check_queued(header, "end")
    _require(isinstance(header.get("reason"), str) and isinstance(header.get("counts"), dict), "end needs reason and counts")
    _require(isinstance(header.get("clock", {}).get("end"), dict), "end needs clock.end")
    return header


def stream_stats(times) -> dict | None:
    """Samples, rate and gaps of one stream of nanosecond stamps; None with fewer than two."""
    intervals_ns = np.diff(np.asarray(times, dtype=np.int64))
    if not intervals_ns.size:
        return None
    median_ns = float(np.median(intervals_ns))
    return {"samples": int(intervals_ns.size + 1), "rate_hz": float(1e9 / np.mean(intervals_ns)),
            "median_interval_ms": median_ns / 1e6, "max_interval_ms": float(intervals_ns.max()) / 1e6,
            "gaps_over_1_5x": int(np.count_nonzero(intervals_ns > 1.5 * median_ns))}


def frame_payload(folder: Path, header: dict) -> bytes:
    """Rebuilds a saved frame's payload, with the grey as raw bytes, so parse_frame checks it again."""
    from PIL import Image

    name = f"{int(header['seq']):06d}"
    grey = np.asarray(Image.open(folder / "cam0" / f"{name}.png")).tobytes()
    payload = grey + (folder / "frames" / f"{name}.jpg").read_bytes()
    if header["arcore"] is not None and header["arcore"].get("depth"):
        payload += (folder / "depth" / f"{name}.bin").read_bytes()
    return payload


def raw_header(header: dict) -> dict:
    """A saved frame header with its grey described as stored on the PC (raw), not as sent."""
    grey = header["grey"]
    return {k: v for k, v in header.items() if k != "host_received_ms"} | {
        "grey": grey | {"encoding": "raw", "bytes": grey["width"] * grey["height"]}}


def read_session(folder: Path) -> Iterator[Frame]:
    """Frames saved by capture_receiver.py, in order: frames.jsonl, cam0/<seq>.png, frames/<seq>.jpg, depth/<seq>.bin."""
    folder = Path(folder)
    with open(folder / "frames.jsonl", encoding="utf-8") as lines:
        for line in lines:
            header = json.loads(line)
            yield parse_frame(raw_header(header), frame_payload(folder, header))
