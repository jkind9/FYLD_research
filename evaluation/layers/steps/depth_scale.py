"""Depth whose scale is corrected per frame, so frames agree with each other in size.

Single-image depth models get a frame's shape right but its size wrong, by a different
factor in each frame (Depth Anything V2 reads TUM indoor frames 1.21-1.63x too far). Combined
in the world, the same surface then appears several times along the view. `ScaleCorrected`
runs a base depth method over the whole sequence and multiplies each frame by one factor
from a scale source:

- `OverlapChainScale`: colour frames and the base depth only (a deployable method).
- `PoseTriangulatedScale`: triangulates tracked corners with metric camera motion. Here the
  motion comes from the recording's motion-capture poses plus noise, standing in for a
  phone's ARCore or IMU poses, so it is a labelled reference control.
- `ReferenceFrameScale`, `ReferenceGlobalScale`: fitted to the recorded sensor depth; reference
  controls that test whether per-frame scale is the problem. Upper bounds, never results.
"""

import importlib
import warnings
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, Protocol

import cv2
import numpy as np
from numpy.typing import NDArray

from experiments.shared.runs import Run

from .contracts import (
    RGBD_MAX_DEPTH_M,
    ColourFrame,
    DepthEstimator,
    DepthPrediction,
    MethodChoice,
    check_reference_tolerance,
    nearest_references,
)
from .depth import DepthMethod, RecordedSensorDepth

depth_geometry = importlib.import_module("experiments.02_stereo_depth.geometry")
pose_evaluation = importlib.import_module("experiments.03_camera_pose_estimation.src.evaluation")
read_reference_poses = pose_evaluation.read_references


@dataclass(frozen=True)
class FrameScale:
    """The factor applied to one frame's base depth, and evidence for how it was found."""

    scale: float
    diagnostics: dict[str, Any]


# All base frames and predictions in, one FrameScale per frame out, same order.
FrameScaler = Callable[[list[ColourFrame], list[DepthPrediction]], list[FrameScale]]


class ScaleSource(MethodChoice, Protocol):
    def load(self) -> FrameScaler: ...


@dataclass(frozen=True)
class ScaleCorrected:
    """A depth method: a base method's depth, each frame multiplied by its scale source's factor.

    It buffers the whole sequence (about 2 MB per 640x480 frame) because scale sources may
    look at every frame before deciding any one factor. The control label is the scale
    source's when it has one, else the base method's.
    """

    base: DepthMethod
    scale: ScaleSource
    max_depth_m: float = 20.0  # inherited from DepthAnythingV2Metric's cap, depth.py:93
    name: str = field(init=False)
    control: str | None = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", f"{self.base.name}+{self.scale.name}")
        object.__setattr__(self, "control", self.scale.control or self.base.control)

    def load(self) -> DepthEstimator:
        return partial(
            _predict_scaled,
            predict_base=self.base.load(),
            find_scales=self.scale.load(),
            max_depth_m=self.max_depth_m,
        )


def _predict_scaled(
    frames: Iterator[ColourFrame],
    *,
    run: Run,
    predict_base: DepthEstimator,
    find_scales: FrameScaler,
    max_depth_m: float,
) -> Iterator[DepthPrediction]:
    colour_frames = list(frames)
    base = [
        DepthPrediction(p.frame_id, np.where(p.valid, p.depth, np.nan).astype(np.float32), p.valid.copy())
        for p in predict_base(iter(colour_frames), run=run)
    ]
    scales = find_scales(colour_frames, base)
    if len(scales) != len(base):
        raise ValueError(f"Scale source returned {len(scales)} factors for {len(base)} frames")
    for prediction, found in zip(base, scales, strict=True):
        if not np.isfinite(found.scale) or found.scale <= 0:
            raise ValueError(f"{prediction.frame_id}: scale {found.scale:g} is not a positive number")
        depth = prediction.depth.astype(np.float64) * found.scale
        valid = prediction.valid & np.isfinite(depth) & (depth > 0) & (depth <= max_depth_m)
        diagnostics = {"scale": float(found.scale), **found.diagnostics}
        yield DepthPrediction(prediction.frame_id, np.where(valid, depth, np.nan), valid, diagnostics)


# ---- Reference controls: fitted to the recorded sensor depth ----


@dataclass(frozen=True)
class ReferenceFrameScale:
    """Each frame's factor from all its recorded sensor pixels (least squares through zero).

    Changes size only, not shape, so it shows how much of the error per-frame scale explains.
    """

    root: Path
    name: str = field(default="reference_frame_scale", init=False)
    control: str = field(default="reference", init=False)

    def load(self) -> FrameScaler:
        return partial(_reference_scales, read=RecordedSensorDepth(self.root).load(), one_factor=False)


@dataclass(frozen=True)
class ReferenceGlobalScale:
    """One factor for the whole sequence: the median over frames of median(reference / base)."""

    root: Path
    name: str = field(default="reference_global_scale", init=False)
    control: str = field(default="reference", init=False)

    def load(self) -> FrameScaler:
        return partial(_reference_scales, read=RecordedSensorDepth(self.root).load(), one_factor=True)


def _reference_scales(
    frames: list[ColourFrame], base: list[DepthPrediction], *, read: DepthEstimator, one_factor: bool
) -> list[FrameScale]:
    fitted, ratios = [], []
    for frame, prediction in zip(frames, base, strict=True):
        (reference,) = list(read(iter([frame]), run=None))
        shared = depth_geometry.alignment_fit_pixels(
            prediction.depth, "metric_depth", reference.depth, np.asarray(reference.valid, dtype=bool)
        )
        if np.count_nonzero(shared) < 2:
            raise ValueError(f"{frame.frame_id}: fewer than 2 pixels have both base and recorded depth")
        scale, _ = depth_geometry.fit_native_alignment(
            prediction.depth, "metric_depth", reference.depth, shared, scale_only=True
        )
        fitted.append(scale)
        ratios.append(float(np.median(reference.depth[shared] / prediction.depth[shared])))
    if one_factor:
        overall = float(np.median(ratios)) if ratios else 1.0
        return [FrameScale(overall, {}) for _ in frames]
    return [FrameScale(scale, {}) for scale in fitted]


# ---- Shared corner tracking ----


@dataclass(frozen=True)
class CornerTracking:
    """Corner detection and Lucas-Kanade settings shared by the image-based scale sources."""

    max_corners: int = 500
    corner_quality: float = 0.01
    corner_distance_px: float = 7.0
    flow_window_px: int = 21
    flow_levels: int = 3
    flow_iterations: int = 30
    flow_epsilon_px: float = 0.01
    flow_check_px: float = 1.0  # forward-backward disagreement allowed

    def track(self, first: NDArray, second: NDArray, mask: NDArray) -> tuple[NDArray, NDArray]:
        """Corners found in `first` (where mask is set) and where they moved to in `second`."""
        corners = cv2.goodFeaturesToTrack(
            first, self.max_corners, self.corner_quality, self.corner_distance_px, mask=mask.astype(np.uint8)
        )
        if corners is None:
            return np.empty((0, 2)), np.empty((0, 2))
        settings = {
            "winSize": (self.flow_window_px, self.flow_window_px),
            "maxLevel": self.flow_levels,
            "criteria": (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, self.flow_iterations, self.flow_epsilon_px),
        }
        moved, ahead, _ = cv2.calcOpticalFlowPyrLK(first, second, corners, None, **settings)
        back, behind, _ = cv2.calcOpticalFlowPyrLK(second, first, moved, None, **settings)
        height, width = first.shape
        start, end = corners.reshape(-1, 2), moved.reshape(-1, 2)
        keep = (
            (ahead.ravel() == 1)
            & (behind.ravel() == 1)
            & (np.linalg.norm(back.reshape(-1, 2) - start, axis=1) <= self.flow_check_px)
            & (end[:, 0] >= 0) & (end[:, 0] <= width - 1) & (end[:, 1] >= 0) & (end[:, 1] <= height - 1)
        )
        return start[keep].astype(np.float64), end[keep].astype(np.float64)


def _grey(frame: ColourFrame) -> NDArray:
    return cv2.cvtColor(np.ascontiguousarray(frame.colour), cv2.COLOR_RGB2GRAY)


def _at(image: NDArray, pixels: NDArray) -> NDArray:
    """Values of `image` at the nearest pixel to each (u, v)."""
    columns = np.clip(np.round(pixels[:, 0]).astype(int), 0, image.shape[1] - 1)
    rows = np.clip(np.round(pixels[:, 1]).astype(int), 0, image.shape[0] - 1)
    return image[rows, columns]


def _intrinsics(frame: ColourFrame) -> NDArray:
    c = frame.calibration
    return np.array([[c.fx, 0.0, c.cx], [0.0, c.fy, c.cy], [0.0, 0.0, 1.0]])


def _project(intrinsics: NDArray, points: NDArray) -> NDArray:
    projected = points @ intrinsics.T
    return projected[:, :2] / projected[:, 2:3]


# ---- Deployable: scale carried from earlier frames through their overlap ----


@dataclass(frozen=True)
class OverlapChainScale:
    """Each frame's factor from the frames before it, using colour frames and base depth only.

    For frame k and each partner k-lag: corners from the partner are tracked into frame k,
    placed in 3D with the partner's already-corrected depth, and a PnP solve gives frame k's
    pose relative to the partner. Those points' depth in frame k, divided by frame k's base
    depth, is the partner's estimate; the frame takes the median over partners. Factors are
    finally divided by their median, so the overall size stays the base model's own (no
    metric source is used). Offline: it needs the whole run before any factor is final.
    """

    partners: tuple[int, ...] = (1, 2, 4, 8)
    tracking: CornerTracking = field(default_factory=CornerTracking)
    pnp_threshold_px: float = 2.0
    pnp_iterations: int = 100
    pnp_confidence: float = 0.99
    min_inliers: int = 30
    max_point_depth_m: float = RGBD_MAX_DEPTH_M  # tracking's working range
    smoothing_frames: int = 1  # 1 = none; n = causal median over the last n factors
    name: str = field(default="overlap_chain_scale", init=False)
    control: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if not self.partners or any(type(lag) is not int or lag < 1 for lag in self.partners):
            raise ValueError("Chain partners must be positive whole numbers of frames back")
        if type(self.smoothing_frames) is not int or self.smoothing_frames < 1:
            raise ValueError("smoothing_frames must be a whole number of at least 1")

    def load(self) -> FrameScaler:
        return self._scales

    def _scales(self, frames: list[ColourFrame], base: list[DepthPrediction]) -> list[FrameScale]:
        greys = [_grey(frame) for frame in frames]
        chained: list[float] = []
        details: list[dict[str, Any]] = []
        for k, frame in enumerate(frames):
            estimates = [] if k else [1.0]
            for lag in self.partners:
                if k - lag >= 0:
                    partner_depth = base[k - lag].depth * chained[k - lag]
                    estimate = self._estimate(frame, greys[k - lag], partner_depth, greys[k], base[k].depth)
                    if estimate is not None:
                        estimates.append(estimate)
            fallback = not estimates
            if fallback:
                warnings.warn(f"{frame.frame_id}: no earlier frame gave a scale; keeping the previous one", stacklevel=2)
                estimates = [chained[-1]]
            chained.append(float(np.median(estimates)))
            details.append({"partners_used": 0 if fallback or k == 0 else len(estimates), "fallback": fallback})
        window = self.smoothing_frames
        smoothed = [float(np.median(chained[max(0, k - window + 1) : k + 1])) for k in range(len(chained))]
        typical = float(np.median(smoothed)) if smoothed else 1.0
        return [FrameScale(value / typical, info) for value, info in zip(smoothed, details, strict=True)]

    def _estimate(
        self, frame: ColourFrame, partner_grey: NDArray, partner_depth: NDArray, grey: NDArray, depth: NDArray
    ) -> float | None:
        """One partner's estimate of this frame's factor, or None when the overlap is too weak."""
        usable = np.isfinite(partner_depth) & (partner_depth > 0) & (partner_depth < self.max_point_depth_m)
        start, end = self.tracking.track(partner_grey, grey, usable)
        z = _at(partner_depth, start)
        keep = np.isfinite(z) & (z > 0) & (z < self.max_point_depth_m)
        if np.count_nonzero(keep) < self.min_inliers:
            return None
        c = frame.calibration
        start, end, z = start[keep], end[keep], z[keep]
        points = np.column_stack(((start[:, 0] - c.cx) * z / c.fx, (start[:, 1] - c.cy) * z / c.fy, z))
        solved, rotation_vector, translation, inliers = cv2.solvePnPRansac(
            points, end, _intrinsics(frame), None,
            iterationsCount=self.pnp_iterations, reprojectionError=self.pnp_threshold_px,
            confidence=self.pnp_confidence, flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not solved or inliers is None or len(inliers) < self.min_inliers:
            return None
        chosen = inliers.ravel()
        rotation, _ = cv2.Rodrigues(rotation_vector)
        moved_z = (points[chosen] @ rotation.T + translation.ravel())[:, 2]
        here = _at(depth, end[chosen])
        good = np.isfinite(here) & (here > 0) & (moved_z > 0)
        if np.count_nonzero(good) < self.min_inliers:
            return None
        return float(np.median(moved_z[good] / here[good]))


# ---- Reference control standing in for phone poses: triangulation with metric motion ----


@dataclass(frozen=True)
class PoseTriangulatedScale:
    """Each frame's factor from corners triangulated with metric camera motion.

    The motion comes from the recording's motion-capture poses plus Gaussian translation
    noise, standing in for ARCore or IMU poses on a phone; reading them makes this a
    reference control. Frames without a pose or a partner far enough away take the factor
    interpolated in time from their neighbours.
    """

    groundtruth: Path
    noise_m: float = 0.005
    seed: int = 0
    tolerance_s: float = 0.02  # inherited from experiment 03 dataset.py:79
    min_baseline_m: float = 0.05
    search_frames: int = 10
    tracking: CornerTracking = field(default_factory=CornerTracking)
    max_reprojection_px: float = 2.0
    min_parallax_deg: float = 1.0
    min_points: int = 20
    name: str = field(default="pose_triangulated_scale", init=False)
    control: str = field(default="reference", init=False)

    def __post_init__(self) -> None:
        check_reference_tolerance(self.tolerance_s)
        if not np.isfinite(self.noise_m) or self.noise_m < 0:
            raise ValueError("noise_m must be finite and not negative")

    def load(self) -> FrameScaler:
        return partial(self._scales, references=read_reference_poses(self.groundtruth))

    def _scales(
        self, frames: list[ColourFrame], base: list[DepthPrediction], *, references: list[tuple[float, NDArray]]
    ) -> list[FrameScale]:
        poses = self._noisy_poses(frames, references)
        greys = [_grey(frame) for frame in frames]
        found = [self._frame_scale(k, frames, greys, base, poses) for k in range(len(frames))]
        known = [k for k, value in enumerate(found) if value is not None]
        if frames and not known:
            raise ValueError("No frame could be triangulated with the supplied poses")
        times = np.array([f.timestamp_s if f.timestamp_s is not None else k for k, f in enumerate(frames)], dtype=float)
        filled = np.interp(times, times[known], [found[k][0] for k in known]) if known else []
        return [
            FrameScale(float(scale), {"points": found[k][1] if found[k] else 0, "interpolated": found[k] is None})
            for k, scale in enumerate(filled)
        ]

    def _noisy_poses(self, frames: list[ColourFrame], references: list[tuple[float, NDArray]]) -> list[NDArray | None]:
        rng = np.random.default_rng(self.seed)
        poses: list[NDArray | None] = []
        for _, matched in nearest_references(iter(frames), [t for t, _ in references], self.tolerance_s):
            noise = rng.normal(0.0, self.noise_m, 3)  # drawn for every frame, so runs repeat
            if matched is None:
                poses.append(None)
                continue
            pose = np.array(references[matched][1], dtype=float)
            pose[:3, 3] += noise
            poses.append(pose)
        return poses

    def _frame_scale(
        self, k: int, frames: list[ColourFrame], greys: list[NDArray], base: list[DepthPrediction], poses: list
    ) -> tuple[float, int] | None:
        """The nearest-in-time partner far enough away that gives a triangulation."""
        if poses[k] is None:
            return None
        for offset in range(1, self.search_frames + 1):
            for j in (k - offset, k + offset):
                if not (0 <= j < len(frames)) or poses[j] is None:
                    continue
                if np.linalg.norm(poses[j][:3, 3] - poses[k][:3, 3]) < self.min_baseline_m:
                    continue
                to_partner = np.linalg.inv(poses[j]) @ poses[k]
                result = self._triangulate(frames[k], greys[k], greys[j], base[k].depth, to_partner)
                if result is not None:
                    return result
        return None

    def _triangulate(
        self, frame: ColourFrame, grey: NDArray, partner_grey: NDArray, depth: NDArray, to_partner: NDArray
    ) -> tuple[float, int] | None:
        start, end = self.tracking.track(grey, partner_grey, np.isfinite(depth) & (depth > 0))
        if len(start) < self.min_points:
            return None
        intrinsics = _intrinsics(frame)
        here = intrinsics @ np.hstack([np.eye(3), np.zeros((3, 1))])
        there = intrinsics @ to_partner[:3]
        homogeneous = cv2.triangulatePoints(here, there, start.T, end.T)
        with np.errstate(divide="ignore", invalid="ignore"):
            points = (homogeneous[:3] / homogeneous[3]).T
            in_partner = points @ to_partner[:3, :3].T + to_partner[:3, 3]
            error_here = np.linalg.norm(_project(intrinsics, points) - start, axis=1)
            error_there = np.linalg.norm(_project(intrinsics, in_partner) - end, axis=1)
            partner_centre = np.linalg.inv(to_partner)[:3, 3]
            rays = points / np.linalg.norm(points, axis=1, keepdims=True)
            offset = points - partner_centre
            partner_rays = offset / np.linalg.norm(offset, axis=1, keepdims=True)
            parallax = np.degrees(np.arccos(np.clip(np.sum(rays * partner_rays, axis=1), -1.0, 1.0)))
        base_here = _at(depth, start)
        keep = (
            (points[:, 2] > 0) & (in_partner[:, 2] > 0)
            & (error_here <= self.max_reprojection_px) & (error_there <= self.max_reprojection_px)
            & (parallax >= self.min_parallax_deg) & np.isfinite(base_here) & (base_here > 0)
        )
        if np.count_nonzero(keep) < self.min_points:
            return None
        return float(np.median(points[keep, 2] / base_here[keep])), int(np.count_nonzero(keep))


# ---- Consistent scale from one source, overall size from another ----


@dataclass(frozen=True)
class AnchoredScale:
    """Frame-to-frame factors from `consistent`, times one run-wide factor from `metric`.

    `consistent` (for example the overlap chain) keeps frames in agreement with each other but
    has no metric size; `metric` (for example triangulation with phone poses) has metric size
    but wobbles from frame to frame. The anchor is the median over frames of metric/consistent,
    skipping frames whose metric factor was interpolated rather than measured.
    """

    consistent: ScaleSource
    metric: ScaleSource
    name: str = field(init=False)
    control: str | None = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", f"{self.consistent.name}+anchored_to+{self.metric.name}")
        object.__setattr__(self, "control", self.metric.control or self.consistent.control)

    def load(self) -> FrameScaler:
        return partial(_anchored_scales, find_consistent=self.consistent.load(), find_metric=self.metric.load())


def _anchored_scales(
    frames: list[ColourFrame], base: list[DepthPrediction], *, find_consistent: FrameScaler, find_metric: FrameScaler
) -> list[FrameScale]:
    consistent = find_consistent(frames, base)
    metric = find_metric(frames, base)
    measured = [m.scale / c.scale for c, m in zip(consistent, metric, strict=True) if not m.diagnostics.get("interpolated")]
    if frames and not measured:
        raise ValueError("No frame has a measured metric scale to anchor the consistent scale to")
    anchor = float(np.median(measured)) if measured else 1.0
    return [
        FrameScale(c.scale * anchor, {**c.diagnostics, "consistent_scale": c.scale, "anchor": anchor})
        for c in consistent
    ]
