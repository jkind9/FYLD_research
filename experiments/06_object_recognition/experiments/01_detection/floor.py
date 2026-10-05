"""Task45 Part B noise floor: how far well-defined corners appear to move.

ORB corners matched between consecutive frames go through the same pairwise
construction as box centres (back-project at t, project at t+1, compare). Their
residuals show how much apparent motion comes from timing, depth and
calibration rather than the detector. Settings are inherited from the
appearance experiment; only pyramid level 0 is kept and depth edges are dropped.
"""

import importlib
import math

import cv2
import numpy as np
from numpy.typing import NDArray

from experiments.shared.contracts import Calibration

from .jitter import backproject_pixel, project_world

ORB_SETTINGS = {
    "nfeatures": 500,
    "scaleFactor": 1.2,
    "nlevels": 8,
    "edgeThreshold": 31,
    "firstLevel": 0,
    "WTA_K": 2,
    "scoreType": cv2.ORB_HARRIS_SCORE,
    "patchSize": 31,
    "fastThreshold": 20,
}
DEPTH_WINDOW = 7
MAX_EDGE_RANGE = 0.10
OUTLIER_MADS = 5.0
MIN_LOCAL = 30


def features(gray: NDArray) -> tuple[list, NDArray | None]:
    """Level-0 ORB keypoints and descriptors (inherited settings)."""
    cv2.setNumThreads(1)
    detector = cv2.ORB_create(**ORB_SETTINGS)  # type: ignore[attr-defined]
    keypoints, descriptors = detector.detectAndCompute(gray, None)
    if descriptors is None:
        return [], None
    keep = [i for i, point in enumerate(keypoints) if point.octave == 0]
    return [keypoints[i] for i in keep], descriptors[keep]


def matches(left: NDArray | None, right: NDArray | None) -> list[tuple[int, int]]:
    """Ratio 0.75 plus mutual check, reused from the appearance experiment."""
    if left is None or right is None or not len(left) or not len(right):
        return []
    compare = importlib.import_module(
        "experiments.06_object_recognition.experiments.03_appearance.compare"
    )
    return compare._mutual(left, right, cv2.NORM_HAMMING)


def feature_depth(depth: NDArray, valid: NDArray, u: float, v: float) -> float | None:
    """Median of a 7x7 window; None at depth edges or with no valid samples."""
    half = DEPTH_WINDOW // 2
    row, column = math.floor(v), math.floor(u)
    window = (
        slice(max(0, row - half), row + half + 1),
        slice(max(0, column - half), column + half + 1),
    )
    values = depth[window][valid[window]]
    if not len(values):
        return None
    median = float(np.median(values))
    if (values.max() - values.min()) > MAX_EDGE_RANGE * median:
        return None
    return median


def pair_residuals(before: dict, after: dict, camera: Calibration) -> list[dict]:
    """Residual of each matched level-0 corner, observed at t+1 minus predicted from t."""
    rows = []
    for i, j in matches(before["descriptors"], after["descriptors"]):
        u, v = before["keypoints"][i].pt
        z = feature_depth(before["depth"], before["valid"], u, v)
        if z is None:
            continue
        world = backproject_pixel(u, v, z, camera, before["pose"])
        expected = project_world(world, camera, after["pose"])
        observed = after["keypoints"][j].pt
        rows.append(
            {
                "u": u,
                "v": v,
                "dx": observed[0] - expected[0],
                "dy": observed[1] - expected[1],
            }
        )
    return rows


def split_outliers(residuals: NDArray) -> tuple[NDArray, NDArray]:
    """Mark rows beyond 5 median absolute deviations from the median on either axis."""
    if not len(residuals):
        return residuals, residuals
    median = np.median(residuals, axis=0)
    mad = np.median(np.abs(residuals - median), axis=0)
    limit = OUTLIER_MADS * np.where(mad > 0, mad, np.inf)
    outlier = np.any(np.abs(residuals - median) > limit, axis=1)
    return residuals[~outlier], residuals[outlier]


def floor(residuals: NDArray, minimum: int = MIN_LOCAL) -> dict:
    """Per-axis std / sqrt(2) of inlier residuals, like the pairwise box jitter."""
    inliers, outliers = split_outliers(
        np.asarray(residuals, dtype=float).reshape(-1, 2)
    )
    if len(inliers) < minimum:
        return {
            "sx": None,
            "sy": None,
            "n": len(inliers),
            "outliers": len(outliers),
            "reason": f"fewer than {minimum} feature residuals",
        }
    sx, sy = np.std(inliers, axis=0, ddof=1) / math.sqrt(2)
    return {
        "sx": float(sx),
        "sy": float(sy),
        "n": len(inliers),
        "outliers": len(outliers),
        "reason": None,
    }
