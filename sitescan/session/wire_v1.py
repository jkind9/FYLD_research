"""Version 1 wire records and boundary checks for phone messages."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

VERSION = 1
STATES = ("TRACKING", "PAUSED", "STOPPED")
PIXEL_TOLERANCE_PX = 0.5
PIXEL_TOLERANCE = PIXEL_TOLERANCE_PX
QUATERNION_TOLERANCE = 1e-3
_ARCORE_TO_OPENCV = np.diag([1.0, -1.0, -1.0, 1.0])


@dataclass(frozen=True)
class Depth:
    """A checked raw-depth message with its recorded intrinsics."""

    t_ns: int
    depth_m: np.ndarray
    confidence: np.ndarray
    intrinsics: tuple[float, float, float, float]


@dataclass(frozen=True)
class Frame:
    """A checked wire frame retaining JPEG bytes and ARCore quaternion poses."""

    seq: int
    t_ns: int
    sent_ms: int
    tracking: str
    failure: str
    pose: tuple[float, ...] | None
    intrinsics: tuple[float, float, float, float]
    image_jpeg: bytes
    image_size: tuple[int, int]
    point_ids: np.ndarray
    points_world: np.ndarray
    points_pixel: np.ndarray
    points_confidence: np.ndarray
    depth: Depth | None
    anchor_created: tuple[int, tuple[float, ...]] | None
    anchor_updates: dict[int, tuple[float, ...]]


def _require(condition: bool, message: str) -> None:
    """Raise ValueError for a wire field that violates the recording contract."""
    if not condition:
        raise ValueError(message)


def _pose(values, name: str) -> tuple[float, ...]:
    """A checked pose tuple in ARCore camera axes."""
    _require(isinstance(values, list) and len(values) == 7, f"{name} needs 7 numbers")
    _require(
        abs(np.linalg.norm(values[3:]) - 1.0) <= QUATERNION_TOLERANCE,
        f"{name} quaternion is not unit length",
    )
    return tuple(float(v) for v in values)


def _intrinsics(values, name: str) -> tuple[float, float, float, float]:
    _require(
        isinstance(values, list) and len(values) == 4 and values[0] > 0 and values[1] > 0,
        f"{name} needs fx, fy > 0, cx, cy",
    )
    return tuple(float(v) for v in values)


def world_from_camera(pose) -> np.ndarray:
    """Camera-to-world matrix with ARCore axes: x right, y up, looking along -z."""
    tx, ty, tz, x, y, z, w = pose
    matrix = np.eye(4)
    matrix[:3, :3] = [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]
    matrix[:3, 3] = tx, ty, tz
    return matrix


def world_from_camera_cv(pose) -> np.ndarray:
    """World_from_camera in metres, with OpenCV camera axes in the ARCore world."""
    return world_from_camera(pose) @ _ARCORE_TO_OPENCV


def corrected_world_from_camera(frame_pose, anchor_created, anchor_now) -> np.ndarray:
    """The frame's ARCore pose moved by its anchor's correction."""
    return (
        world_from_camera(anchor_now)
        @ np.linalg.inv(world_from_camera(anchor_created))
        @ world_from_camera(frame_pose)
    )


def project(pose, intrinsics, points_world: np.ndarray) -> np.ndarray:
    """Pixels of world points seen from the recorded ARCore pose and intrinsics."""
    camera_from_world = np.linalg.inv(world_from_camera(pose))
    camera = points_world @ camera_from_world[:3, :3].T + camera_from_world[:3, 3]
    fx, fy, cx, cy = intrinsics
    return np.c_[cx + fx * camera[:, 0] / -camera[:, 2], cy - fy * camera[:, 1] / -camera[:, 2]]


def check_session(header: dict) -> dict:
    _require(
        header.get("type") == "session" and header.get("version") == VERSION,
        f"session start must be type session, version {VERSION}",
    )
    _require(isinstance(header.get("device"), dict), "session start needs a device object")
    return header


def parse_depth(header: dict | None, payload: bytes) -> Depth | None:
    """Checked depth and confidence arrays from the binary message tail."""
    sizes = (header["bytes"], header["confidence_bytes"]) if header else (0, 0)
    _require(len(payload) == sum(sizes), "payload length does not match the header")
    if not header:
        return None
    width = header["width"]
    height = header["height"]
    count = width * height
    _require(sizes == (count * 2, count), "depth sizes do not match width x height")
    millimetres = np.frombuffer(payload, dtype="<u2", count=count).reshape(height, width)
    confidence = np.frombuffer(payload, dtype=np.uint8, count=count, offset=count * 2)
    return Depth(
        int(header["t_ns"]),
        millimetres.astype(np.float32) / 1000.0,
        confidence.reshape(height, width),
        _intrinsics(header["intrinsics"], "depth intrinsics"),
    )


def parse_points(points: list, pose, intrinsics) -> np.ndarray:
    """Checked tracked-point rows, including their agreement with the camera projection."""
    _require(all(len(p) == 7 for p in points), "each point needs [id, x, y, z, u, v, confidence]")
    _require(pose is not None or not points, "points need a pose")
    table = np.array(points, dtype=np.float64).reshape(-1, 7)
    if len(table):
        error = np.abs(project(pose, intrinsics, table[:, 1:4]) - table[:, 4:6]).max()
        _require(
            error <= PIXEL_TOLERANCE_PX, f"a point's pixel is {error:.2f} px from its projection"
        )
    return table


def parse_arcore(record: dict, depth_payload: bytes) -> dict:
    """Checked camera, tracked points, depth and anchor fields from an ARCore record."""
    tracking = record["tracking"]
    _require(tracking in STATES, f"tracking must be one of {STATES}")
    _require(
        (record["pose"] is not None) == (tracking == "TRACKING"),
        "pose must be given exactly when tracking",
    )
    pose = _pose(record["pose"], "pose") if record["pose"] is not None else None
    intrinsics = _intrinsics(record["intrinsics"], "intrinsics")
    table = parse_points(record["points"], pose, intrinsics)
    anchor = record.get("anchor")
    return {
        "tracking": tracking,
        "failure": record["failure"],
        "pose": pose,
        "intrinsics": intrinsics,
        "point_ids": table[:, 0].astype(np.int64),
        "points_world": table[:, 1:4],
        "points_pixel": table[:, 4:6],
        "points_confidence": table[:, 6],
        "depth": parse_depth(record.get("depth"), depth_payload),
        "anchor_created": (int(anchor["id"]), _pose(anchor["pose"], "anchor pose"))
        if anchor
        else None,
        "anchor_updates": {
            int(a[0]): _pose(list(a[1:]), "anchor correction") for a in record["anchors"]
        },
    }


def parse_frame(header: dict, payload: bytes) -> Frame:
    _require(
        header.get("type") == "frame" and header.get("version") == VERSION,
        f"frame must be type frame, version {VERSION}",
    )
    image = header["image"]
    _require(image["format"] == "jpeg" and payload[:2] == b"\xff\xd8", "image must be JPEG")
    return Frame(
        seq=int(header["seq"]),
        t_ns=int(header["t_ns"]),
        sent_ms=int(header["sent_ms"]),
        image_jpeg=payload[: image["bytes"]],
        image_size=(int(image["width"]), int(image["height"])),
        **parse_arcore(header, payload[image["bytes"] :]),
    )
