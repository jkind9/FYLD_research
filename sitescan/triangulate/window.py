"""A rolling window of keyframes with known poses, and the depth they give each new frame."""

from collections import deque
from dataclasses import dataclass

import numpy as np

from sitescan.types import Camera, MeasuredDepth

from .sparse import Features, SparseDepth, detect, merge, triangulate_pair
from .sweep import sweep_depth

KEYFRAMES = 8
KEYFRAME_STEP_M = 0.1
KEYFRAME_TURN_DEG = 15.0
MIN_BASELINE_M = 0.05
MAX_BASELINE_M = 1.0
MAX_VIEW_ANGLE_DEG = 30.0
SPARSE_REFERENCES = 3
DENSE_REFERENCES = 2
DENSE_BASELINE_PER_M = 0.1
MIN_TYPICAL_POINTS = 10


@dataclass(frozen=True)
class Keyframe:
    """A grey image with its camera, world_from_camera and features."""

    grey: np.ndarray
    camera: Camera
    pose: np.ndarray
    features: Features


def view_angle_deg(pose_a: np.ndarray, pose_b: np.ndarray) -> float:
    """Angle between two cameras' viewing directions, in degrees."""
    return float(np.degrees(np.arccos(np.clip(pose_a[:3, 2] @ pose_b[:3, 2], -1.0, 1.0))))


def references(
    window, pose: np.ndarray, count: int, baseline_m: float | None = None
) -> list[Keyframe]:
    """Up to `count` keyframes far enough away to triangulate and facing the same way.

    A baseline from 5 cm to 1 m and viewing directions within 30 degrees keep enough overlap for
    matching while giving the rays room to cross. The newest come first, because they share the
    most of the view; with `baseline_m`, those nearest that baseline come first instead.
    """
    usable = []
    for age, keyframe in enumerate(reversed(window)):
        baseline = float(np.linalg.norm(keyframe.pose[:3, 3] - pose[:3, 3]))
        facing = view_angle_deg(keyframe.pose, pose) <= MAX_VIEW_ANGLE_DEG
        if MIN_BASELINE_M <= baseline <= MAX_BASELINE_M and facing:
            usable.append((age if baseline_m is None else abs(baseline - baseline_m), keyframe))
    return [keyframe for _, keyframe in sorted(usable, key=lambda item: item[0])[:count]]


class Triangulator:
    """Keyframes kept between frames, so each new frame is triangulated against earlier views."""

    def __init__(self, *, keyframes: int = KEYFRAMES):
        self.window: deque[Keyframe] = deque(maxlen=keyframes)
        self.typical_depth_m: float | None = None

    def sparse(self, grey: np.ndarray, camera: Camera, pose: np.ndarray) -> SparseDepth:
        """Depth at the frame's features from the three newest usable keyframes.

        The median depth is remembered for choosing dense baselines. The frame then joins the window
        if it has moved 10 cm or turned 15 degrees since the last keyframe; the oldest keyframe
        leaves when the window is full.
        """
        features = detect(grey)
        found = merge(
            [
                triangulate_pair(features, camera, pose, k.features, k.camera, k.pose)
                for k in references(self.window, pose, SPARSE_REFERENCES)
            ]
        )
        if len(found.depth_m) >= MIN_TYPICAL_POINTS:
            self.typical_depth_m = float(np.median(found.depth_m))
        last = self.window[-1].pose if self.window else None
        if (
            last is None
            or np.linalg.norm(last[:3, 3] - pose[:3, 3]) >= KEYFRAME_STEP_M
            or view_angle_deg(last, pose) >= KEYFRAME_TURN_DEG
        ):
            self.window.append(Keyframe(grey, camera, pose, features))
        return found

    def dense(
        self,
        grey: np.ndarray,
        camera: Camera,
        pose: np.ndarray,
        t_ns: int,
        prior: np.ndarray | None = None,
    ) -> MeasuredDepth | None:
        """Plane-sweep depth from two keyframes about a tenth of the typical depth away.

        That baseline gives about 6 degrees between the rays. The typical depth is the prior's
        median, else the last sparse median. None before either exists, or when no keyframe is
        usable.
        """
        typical = self.typical_depth_m if prior is None else float(np.nanmedian(prior))
        if typical is None or not np.isfinite(typical):
            return None
        chosen = references(self.window, pose, DENSE_REFERENCES, DENSE_BASELINE_PER_M * typical)
        if not chosen:
            return None
        return sweep_depth(
            grey, camera, pose, [(k.grey, k.camera, k.pose) for k in chosen], t_ns=t_ns, prior=prior
        )
