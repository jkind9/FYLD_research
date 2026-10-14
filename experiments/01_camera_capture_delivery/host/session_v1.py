"""Read and check phone session v1 frames (experiments/01_camera_capture_delivery/phone_session_v1.md).

parse_frame turns one received header and payload into arrays; read_session reads a folder saved by receiver.py.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

VERSION = 1
STATES = ("TRACKING", "PAUSED", "STOPPED")
PIXEL_TOLERANCE = 0.5
_ARCORE_TO_OPENCV = np.diag([1.0, -1.0, -1.0, 1.0])


@dataclass(frozen=True)
class Depth:
    t_ns: int
    depth_m: np.ndarray  # (h, w) float32 metres to the camera plane, 0 where ARCore has none
    confidence: np.ndarray  # (h, w) uint8, 0-255
    intrinsics: tuple[float, float, float, float]


@dataclass(frozen=True)
class Frame:
    seq: int
    t_ns: int
    sent_ms: int
    tracking: str
    failure: str
    pose: tuple[float, ...] | None  # [tx, ty, tz, qx, qy, qz, qw], ARCore camera axes
    intrinsics: tuple[float, float, float, float]
    image_jpeg: bytes
    image_size: tuple[int, int]
    point_ids: np.ndarray  # (n,) int64
    points_world: np.ndarray  # (n, 3) metres
    points_pixel: np.ndarray  # (n, 2)
    points_confidence: np.ndarray  # (n,)
    depth: Depth | None
    anchor_created: tuple[int, tuple[float, ...]] | None
    anchor_updates: dict[int, tuple[float, ...]]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _pose(values, name: str) -> tuple[float, ...]:
    _require(isinstance(values, list) and len(values) == 7, f"{name} needs 7 numbers")
    _require(abs(np.linalg.norm(values[3:]) - 1.0) <= 1e-3, f"{name} quaternion is not unit length")
    return tuple(float(v) for v in values)


def _intrinsics(values, name: str) -> tuple[float, float, float, float]:
    _require(isinstance(values, list) and len(values) == 4 and values[0] > 0 and values[1] > 0, f"{name} needs fx, fy > 0, cx, cy")
    return tuple(float(v) for v in values)


def world_from_camera(pose) -> np.ndarray:
    """4 x 4 camera-to-world transform with ARCore's camera axes (x right, y up, looking along -z)."""
    tx, ty, tz, x, y, z, w = pose
    matrix = np.eye(4)
    matrix[:3, :3] = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    matrix[:3, 3] = tx, ty, tz
    return matrix


def world_from_camera_cv(pose) -> np.ndarray:
    """The same transform for the project's OpenCV camera axes (x right, y down, looking along +z)."""
    return world_from_camera(pose) @ _ARCORE_TO_OPENCV


def corrected_world_from_camera(frame_pose, anchor_created, anchor_now) -> np.ndarray:
    """A frame's pose moved with its keyframe anchor: A_now A_created^-1 world_from_camera (ARCore axes)."""
    return world_from_camera(anchor_now) @ np.linalg.inv(world_from_camera(anchor_created)) @ world_from_camera(frame_pose)


def project(pose, intrinsics, points_world: np.ndarray) -> np.ndarray:
    """Pixel (u, v) of world points seen from an ARCore pose, by the formula in phone_session_v1.md."""
    camera_from_world = np.linalg.inv(world_from_camera(pose))
    camera = points_world @ camera_from_world[:3, :3].T + camera_from_world[:3, 3]
    fx, fy, cx, cy = intrinsics
    return np.c_[cx + fx * camera[:, 0] / -camera[:, 2], cy - fy * camera[:, 1] / -camera[:, 2]]


def check_session(header: dict) -> dict:
    _require(header.get("type") == "session" and header.get("version") == VERSION, f"session start must be type session, version {VERSION}")
    _require(isinstance(header.get("device"), dict), "session start needs a device object")
    return header


def parse_arcore(record: dict, depth_payload: bytes) -> dict:
    """Checks ARCore's per-frame fields (shared by v1 frames and v2 arcore records); returns them as Frame fields.

    depth_payload is what follows the images: raw depth, then confidence, when the record has new depth.
    """
    tracking = record["tracking"]
    _require(tracking in STATES, f"tracking must be one of {STATES}")
    _require((record["pose"] is not None) == (tracking == "TRACKING"), "pose must be given exactly when tracking")
    pose = _pose(record["pose"], "pose") if record["pose"] is not None else None
    intrinsics = _intrinsics(record["intrinsics"], "intrinsics")
    depth_header = record.get("depth")
    depth_bytes = (depth_header["bytes"], depth_header["confidence_bytes"]) if depth_header else (0, 0)
    _require(len(depth_payload) == sum(depth_bytes), "payload length does not match the header")

    points = record["points"]
    _require(all(len(p) == 7 for p in points), "each point needs [id, x, y, z, u, v, confidence]")
    _require(pose is not None or not points, "points need a pose")
    table = np.array(points, dtype=np.float64).reshape(-1, 7)
    if len(table):
        error = np.abs(project(pose, intrinsics, table[:, 1:4]) - table[:, 4:6]).max()
        _require(error <= PIXEL_TOLERANCE, f"a point's pixel is {error:.2f} px from its projection")

    depth = None
    if depth_header:
        w, h = depth_header["width"], depth_header["height"]
        _require(depth_bytes == (w * h * 2, w * h), "depth sizes do not match width x height")
        millimetres = np.frombuffer(depth_payload, dtype="<u2", count=w * h).reshape(h, w)
        depth = Depth(int(depth_header["t_ns"]), millimetres.astype(np.float32) / 1000.0,
                      np.frombuffer(depth_payload, dtype=np.uint8, count=w * h, offset=w * h * 2).reshape(h, w),
                      _intrinsics(depth_header["intrinsics"], "depth intrinsics"))

    anchor = record.get("anchor")
    return dict(
        tracking=tracking, failure=record["failure"], pose=pose, intrinsics=intrinsics, point_ids=table[:, 0].astype(np.int64),
        points_world=table[:, 1:4], points_pixel=table[:, 4:6], points_confidence=table[:, 6], depth=depth,
        anchor_created=(int(anchor["id"]), _pose(anchor["pose"], "anchor pose")) if anchor else None,
        anchor_updates={int(a[0]): _pose(list(a[1:]), "anchor correction") for a in record["anchors"]})


def parse_frame(header: dict, payload: bytes) -> Frame:
    _require(header.get("type") == "frame" and header.get("version") == VERSION, f"frame must be type frame, version {VERSION}")
    image = header["image"]
    _require(image["format"] == "jpeg" and payload[:2] == b"\xff\xd8", "image must be JPEG")
    return Frame(seq=int(header["seq"]), t_ns=int(header["t_ns"]), sent_ms=int(header["sent_ms"]),
                 image_jpeg=payload[:image["bytes"]], image_size=(int(image["width"]), int(image["height"])),
                 **parse_arcore(header, payload[image["bytes"]:]))


def read_session(folder: Path) -> Iterator[Frame]:
    """Frames saved by receiver.py, in order: frames.jsonl headers, frames/<seq>.jpg, depth/<seq>.bin."""
    folder = Path(folder)
    with open(folder / "frames.jsonl", encoding="utf-8") as lines:
        for line in lines:
            header = json.loads(line)
            name = f"{int(header['seq']):06d}"
            payload = (folder / "frames" / f"{name}.jpg").read_bytes()
            if header.get("depth"):
                payload += (folder / "depth" / f"{name}.bin").read_bytes()
            yield parse_frame(header, payload)
