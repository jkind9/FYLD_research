"""Version 2 wire records and boundary checks for phone messages."""

from __future__ import annotations

import re
import struct
import zlib
from dataclasses import dataclass

import numpy as np

from . import wire_v1 as session_v1
from .wire_v1 import _intrinsics, _pose, _require

VERSION = 2
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{1,80}")
IMU_ROW = struct.Struct("<qi6f")
SENSORS = ("gyro", "accel")
CAMERA_FIELDS = (
    "exposure_ns",
    "frame_duration_ns",
    "rolling_shutter_skew_ns",
    "focus_distance_dpt",
    "iso",
    "ois_mode",
)
TELEMETRY_FIELDS = (
    "elapsed_realtime_ns",
    "wall_ms",
    "battery_pct",
    "thermal_status",
    "free_bytes",
    "queue_frames",
    "queue_bytes",
    "frames_captured",
    "frames_queued",
    "frames_sent",
    "frames_acknowledged",
    "frames_dropped",
    "arcore_update_ms",
)
INFO_FIELDS = ("kind", "app", "device", "camera", "arcore", "imu", "clock", "settings")
KINDS = ("walk", "imu_only")


@dataclass(frozen=True)
class Frame(session_v1.Frame):
    """A decoded v2 wire message; camera timestamps use the Camera2 clock."""

    n: int
    camera_t_ns: int
    camera: dict | None
    grey: np.ndarray
    arcore_t_ns: int | None
    device_pose: tuple[float, ...] | None
    texture_intrinsics: tuple[float, float, float, float] | None

    @property
    def wall_ms(self) -> int:
        """The wall-clock send time from the wire envelope, in milliseconds."""
        return self.sent_ms


@dataclass(frozen=True)
class ImuBatch:
    """Recorded inertial samples and Android bias estimates on the device clock."""

    n: int
    t_ns: np.ndarray
    sensor: np.ndarray
    values: np.ndarray
    bias: np.ndarray


def check_session_id(session) -> str:
    """A session id of 1-80 letters, digits, underscores or hyphens."""
    _require(
        isinstance(session, str) and SESSION_ID.fullmatch(session) is not None,
        f"bad session id {session!r}",
    )
    return session


def check_queued(header: dict, kind: str) -> dict:
    """The envelope every queued message shares: type, version, session id and message number."""
    _require(
        header.get("type") == kind and header.get("version") == VERSION,
        f"{kind} must be type {kind}, version {VERSION}",
    )
    check_session_id(header.get("session"))
    _require(
        isinstance(header.get("n"), int) and header["n"] >= 0, "n must be a whole number from 0"
    )
    return header


def check_hello(header: dict) -> dict:
    """A checked hello message: the session id and the phone, camera, clock and settings info."""
    _require(
        header.get("type") == "hello" and header.get("version") == VERSION,
        f"hello must be type hello, version {VERSION}",
    )
    check_session_id(header.get("session"))
    info = header.get("info")
    _require(
        isinstance(info, dict) and all(k in info for k in INFO_FIELDS),
        f"hello info needs {INFO_FIELDS}",
    )
    _require(info["kind"] in KINDS, f"kind must be one of {KINDS}")
    _require(
        isinstance(info["clock"].get("start", {}).get("elapsed_realtime_ns"), int),
        "hello needs clock.start.elapsed_realtime_ns",
    )
    return header


def parse_images(header: dict, payload: bytes) -> tuple[np.ndarray, bytes, bytes]:
    """Lossless grey, JPEG bytes and the remaining depth bytes from a frame message."""
    grey = header["grey"]
    colour = header["colour"]
    width = grey["width"]
    height = grey["height"]
    count = grey["bytes"]
    _require(
        colour["format"] == "jpeg" and (colour["width"], colour["height"]) == (width, height),
        "colour must be a JPEG of the grey's size",
    )
    packed = payload[:count]
    if grey["encoding"] == "raw":
        _require(count == width * height, "raw grey must be width x height bytes")
        pixels = packed
    else:
        _require(grey["encoding"] == "deflate", "grey encoding must be raw or deflate")
        try:
            pixels = zlib.decompress(packed)
        except zlib.error as error:
            raise ValueError(f"grey does not inflate: {error}") from error
        _require(
            len(pixels) == width * height, "deflated grey must inflate to width x height bytes"
        )
    jpeg = payload[count : count + colour["bytes"]]
    _require(len(jpeg) == colour["bytes"] and jpeg[:2] == b"\xff\xd8", "colour image must be JPEG")
    return (
        np.frombuffer(pixels, np.uint8).reshape(height, width),
        jpeg,
        payload[count + colour["bytes"] :],
    )


def parse_arcore(record: dict | None, payload: bytes) -> dict:
    """ARCore fields including device pose, or absent fields for camera-only recordings."""
    if record is None:
        _require(not payload, "payload length does not match the header")
        return {
            "tracking": "NO_ARCORE",
            "failure": "NO_ARCORE",
            "pose": None,
            "intrinsics": None,
            "point_ids": np.zeros(0, np.int64),
            "points_world": np.zeros((0, 3)),
            "points_pixel": np.zeros((0, 2)),
            "points_confidence": np.zeros(0),
            "depth": None,
            "anchor_created": None,
            "anchor_updates": {},
            "arcore_t_ns": None,
            "device_pose": None,
            "texture_intrinsics": None,
        }
    fields = session_v1.parse_arcore(record, payload)
    device = record["device_pose"]
    _require(
        (device is not None) == (fields["pose"] is not None),
        "device_pose must be given exactly when tracking",
    )
    return fields | {
        "arcore_t_ns": int(record["t_ns"]),
        "device_pose": _pose(device, "device_pose") if device is not None else None,
        "texture_intrinsics": _intrinsics(record["texture_intrinsics"], "texture_intrinsics"),
    }


def parse_frame(header: dict, payload: bytes) -> Frame:
    """Checked frame message retaining the wire fields for existing callers."""
    check_queued(header, "frame")
    _require(
        isinstance(header.get("seq"), int) and header["seq"] >= 0,
        "seq must be a whole number from 0",
    )
    camera = header["camera"]
    _require(
        camera is None or set(camera) == set(CAMERA_FIELDS), f"camera needs exactly {CAMERA_FIELDS}"
    )
    grey, jpeg, rest = parse_images(header, payload)
    return Frame(
        seq=header["seq"],
        t_ns=int(header["camera_t_ns"]),
        sent_ms=int(header["wall_ms"]),
        image_jpeg=jpeg,
        image_size=(header["grey"]["width"], header["grey"]["height"]),
        n=header["n"],
        camera_t_ns=int(header["camera_t_ns"]),
        camera=camera,
        grey=grey,
        **parse_arcore(header["arcore"], rest),
    )


def parse_imu(header: dict, payload: bytes) -> ImuBatch:
    """A checked batch of gyroscope or accelerometer samples, 36 bytes each."""
    check_queued(header, "imu")
    count = header.get("samples")
    _require(
        isinstance(count, int) and count > 0 and len(payload) == IMU_ROW.size * count,
        "imu payload must be 36 bytes per sample",
    )
    rows = np.array(list(IMU_ROW.iter_unpack(payload)), dtype=object)
    t = rows[:, 0].astype(np.int64)
    sensor = rows[:, 1].astype(np.int64)
    _require(np.isin(sensor, (0, 1)).all(), "imu sensor must be 0 (gyroscope) or 1 (accelerometer)")
    for code in (0, 1):
        _require(
            np.all(np.diff(t[sensor == code]) >= 0), f"{SENSORS[code]} timestamps go backwards"
        )
    values = rows[:, 2:].astype(np.float64)
    return ImuBatch(header["n"], t, sensor, values[:, :3], values[:, 3:])


def check_telemetry(header: dict) -> dict:
    """A checked telemetry envelope with all phone counters present."""
    check_queued(header, "telemetry")
    _require(all(k in header for k in TELEMETRY_FIELDS), f"telemetry needs {TELEMETRY_FIELDS}")
    return header


def check_end(header: dict) -> dict:
    """A checked end envelope with counts and the final phone clock reading."""
    check_queued(header, "end")
    _require(
        isinstance(header.get("reason"), str) and isinstance(header.get("counts"), dict),
        "end needs reason and counts",
    )
    _require(isinstance(header.get("clock", {}).get("end"), dict), "end needs clock.end")
    return header


def stream_stats(times) -> dict | None:
    """Sample count, rate and gap counts, or None for fewer than two timestamps."""
    intervals_ns = np.diff(np.asarray(times, dtype=np.int64))
    if not intervals_ns.size:
        return None
    median_ns = float(np.median(intervals_ns))
    return {
        "samples": int(intervals_ns.size + 1),
        "rate_hz": float(1e9 / np.mean(intervals_ns)),
        "median_interval_ms": median_ns / 1e6,
        "max_interval_ms": float(intervals_ns.max()) / 1e6,
        "gaps_over_1_5x": int(np.count_nonzero(intervals_ns > 1.5 * median_ns)),
    }
