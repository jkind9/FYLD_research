"""Camera poses from an open tracker, joined to a recording's frames by time.

A tracker writes its path in its own world. The reader turns that world so that +y is up, as
ARCore's is, because the depth stage finds image "down" from the world's -y axis. Every later stage
then works unchanged on tracker poses.
"""

import dataclasses
import json
from collections.abc import Iterable, Iterator
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from sitescan.types import Calibration, Camera, Trajectory

from . import wire_v2
from .wire_v1 import _require

Y_UP = np.array([0.0, 1.0, 0.0])
BASALT_UP = (0.0, 0.0, 1.0)
MAX_POSE_GAP_S = 0.1
SAME_TIME_NS = 1000
KEYFRAME_EVERY_S = 1.0
RIGID_TOLERANCE = 1e-6
_ARCORE_TO_OPENCV = np.diag([1.0, -1.0, -1.0, 1.0])


def up_to_y(up) -> np.ndarray:
    """4 x 4 rotation taking a world's up axis to +y, about the axis perpendicular to both."""
    up = np.asarray(up, dtype=float) / np.linalg.norm(up)
    axis = np.cross(up, Y_UP)
    matrix = np.eye(4)
    if np.linalg.norm(axis) < 1e-12:
        matrix[:3, :3] = np.eye(3) if up @ Y_UP > 0 else np.diag([1.0, -1.0, -1.0])
        return matrix
    angle = np.arctan2(np.linalg.norm(axis), up @ Y_UP)
    matrix[:3, :3] = Rotation.from_rotvec(axis / np.linalg.norm(axis) * angle).as_matrix()
    return matrix


def nanoseconds(seconds: str) -> int:
    """Exact nanoseconds from a decimal or scientific seconds string, as trackers write times."""
    return int(Decimal(seconds).scaleb(9).to_integral_value())


def read_tum(path: Path | str, *, source: str, up=BASALT_UP, imu_from_camera=None) -> Trajectory:
    """Tracker poses from a `time x y z qx qy qz qw` file, as camera poses in a +y-up world.

    Times are seconds on the camera clock. Basalt writes the motion sensors' pose, so pass the
    calibration's imu_from_camera to get the camera's; without it the file must hold OpenCV camera
    poses. `up` is the tracker world's up axis: +z for Basalt.
    """
    rows = [line.split() for line in Path(path).read_text(encoding="utf-8").splitlines()]
    rows = [row for row in rows if row and not row[0].startswith("#")]
    _require(
        rows and all(len(row) >= 8 for row in rows),
        f"{path}: each line needs time x y z qx qy qz qw",
    )
    try:
        t_ns = np.array([nanoseconds(row[0]) for row in rows], dtype=np.int64)
    except InvalidOperation as error:
        raise ValueError(f"{path}: a time is not a number") from error
    _require(bool(np.all(np.diff(t_ns) > 0)), f"{path}: times must increase")
    values = np.array([row[1:8] for row in rows], dtype=float)
    norms = np.linalg.norm(values[:, 3:], axis=1)
    _require(bool(np.all(np.abs(norms - 1) < 1e-3)), f"{path}: quaternions must be unit length")
    poses = np.tile(np.eye(4), (len(rows), 1, 1))
    poses[:, :3, :3] = Rotation.from_quat(values[:, 3:]).as_matrix()
    poses[:, :3, 3] = values[:, :3]
    if imu_from_camera is not None:
        poses = poses @ imu_from_camera
    return Trajectory(source, t_ns, up_to_y(up) @ poses)


def read_calibration(path: Path | str) -> Calibration:
    """A phone calibration from its JSON file: colour camera, distortion and imu_from_camera."""
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    camera = Camera(**record["camera"])
    _require(
        camera.fx > 0 and camera.fy > 0 and camera.width > 0 and camera.height > 0,
        f"{path}: the camera needs positive focal lengths and size",
    )
    matrix = np.asarray(record["imu_from_camera"], dtype=float)
    _require(
        matrix.shape == (4, 4)
        and np.allclose(matrix[3], [0, 0, 0, 1])
        and np.allclose(matrix[:3, :3] @ matrix[:3, :3].T, np.eye(3), atol=RIGID_TOLERANCE),
        f"{path}: imu_from_camera must be a 4 x 4 rigid transform",
    )
    return Calibration(camera, tuple(float(v) for v in record.get("distortion", ())), matrix)


def pose_at(
    trajectory: Trajectory, t_ns: int, *, max_gap_s: float = MAX_POSE_GAP_S
) -> np.ndarray | None:
    """world_from_camera at a time, interpolated between the poses either side.

    A pose within a microsecond is the frame's own: trackers that write seconds as floating point
    move times by up to a few hundred nanoseconds. None before the first pose, after the last, or
    where the two poses are further apart in time than a tracker leaves only when it lost track.
    """
    times = trajectory.t_ns
    after = int(np.searchsorted(times, t_ns))
    for nearest in (after - 1, after):
        if 0 <= nearest < len(times) and abs(int(times[nearest]) - t_ns) <= SAME_TIME_NS:
            return trajectory.world_from_camera[nearest].copy()
    if after in (0, len(times)) or times[after] - times[after - 1] > max_gap_s * 1e9:
        return None
    start, end = trajectory.world_from_camera[after - 1 : after + 1]
    weight = (t_ns - times[after - 1]) / (times[after] - times[after - 1])
    pose = np.eye(4)
    pose[:3, :3] = Slerp([0.0, 1.0], Rotation.from_matrix([start[:3, :3], end[:3, :3]]))(
        weight
    ).as_matrix()
    pose[:3, 3] = (1 - weight) * start[:3, 3] + weight * end[:3, 3]
    return pose


def arcore_pose(world_from_camera_cv: np.ndarray) -> tuple[float, ...]:
    """The wire record's pose: position and quaternion (x, y, z, w) in ARCore camera axes."""
    matrix = world_from_camera_cv @ _ARCORE_TO_OPENCV
    return (*map(float, matrix[:3, 3]), *map(float, Rotation.from_matrix(matrix[:3, :3]).as_quat()))


def with_trajectory(
    records: Iterable,
    trajectory: Trajectory,
    calibration: Calibration | None = None,
    *,
    keyframe_every_s: float = KEYFRAME_EVERY_S,
) -> Iterator[wire_v2.Frame]:
    """Wire records posed by a tracker, with one new anchor every keyframe interval.

    ARCore's tracked points and anchors belong to ARCore's world, so they are dropped. ARCore
    depth is measured in the camera, so it stays as a comparison. The tracker never corrects a
    pose, so its anchors are never updated. Intrinsics come from the calibration, or else from
    the recording.
    """
    anchor = -1
    anchor_t_ns = None
    for record in records:
        _require(
            isinstance(record, wire_v2.Frame), "a tracker trajectory needs a version 2 recording"
        )
        intrinsics = record.intrinsics
        if calibration is not None:
            k = calibration.camera
            _require(
                record.image_size == (k.width, k.height),
                "the calibration is for another image size",
            )
            intrinsics = (k.fx, k.fy, k.cx, k.cy)
        world_from_camera = pose_at(trajectory, record.t_ns)
        pose = None if world_from_camera is None else arcore_pose(world_from_camera)
        _require(
            pose is None or intrinsics is not None,
            "frames recorded without ARCore need a calibration",
        )
        created = None
        if pose is not None and (
            anchor_t_ns is None or record.t_ns - anchor_t_ns >= keyframe_every_s * 1e9
        ):
            anchor += 1
            anchor_t_ns = record.t_ns
            created = (anchor, pose)
        yield dataclasses.replace(
            record,
            pose=pose,
            intrinsics=intrinsics,
            pose_source=trajectory.source,
            tracking="TRACKING" if pose else "LOST",
            failure="NONE" if pose else "OUTSIDE_TRAJECTORY",
            point_ids=np.zeros(0, np.int64),
            points_world=np.zeros((0, 3)),
            points_pixel=np.zeros((0, 2)),
            points_confidence=np.zeros(0),
            anchor_created=created,
            anchor_updates={},
        )
