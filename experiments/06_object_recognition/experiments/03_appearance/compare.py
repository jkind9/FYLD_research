"""Nullable similarity evidence; image transforms never become metric poses."""

import time

import cv2
import numpy as np


def _unavailable(reason: str, **extra: object) -> dict:
    return {"score": None, "reason": reason, **extra}


def zncc(
    left: np.ndarray, left_mask: np.ndarray, right: np.ndarray, right_mask: np.ndarray
) -> dict:
    if (
        left.shape != right.shape
        or left_mask.shape != left.shape[:2]
        or right_mask.shape != right.shape[:2]
    ):
        raise ValueError("Correlation grids differ")
    valid = (left_mask != 0) & (right_mask != 0)
    count = int(valid.sum())
    if count < 16:
        return _unavailable("insufficient_joint_support", pixels=count)
    a = cv2.cvtColor(left, cv2.COLOR_RGB2GRAY)[valid].astype(float)
    b = cv2.cvtColor(right, cv2.COLOR_RGB2GRAY)[valid].astype(float)
    return {**cosine(a - a.mean(), b - b.mean()), "pixels": count}


def cosine(left: list | np.ndarray, right: list | np.ndarray) -> dict:
    a, b = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if a.ndim != 1 or b.ndim != 1 or a.shape != b.shape:
        raise ValueError("Vector dimensions differ")
    if not a.size or not np.isfinite(a).all() or not np.isfinite(b).all():
        return _unavailable("nonfinite_or_empty_vector")
    norms = float(np.linalg.norm(a) * np.linalg.norm(b))
    if norms == 0 or not np.isfinite(norms):
        return _unavailable("zero_or_invalid_variance")
    return {"score": float(np.clip(np.dot(a, b) / norms, -1, 1)), "reason": None}


def _mutual(left: np.ndarray, right: np.ndarray, norm: int) -> list[tuple[int, int]]:
    matcher = cv2.BFMatcher(norm, crossCheck=False)

    def accepted(a: np.ndarray, b: np.ndarray) -> dict[int, int]:
        rows = matcher.knnMatch(a, b, k=2)
        return {
            r[0].queryIdx: r[0].trainIdx
            for r in rows
            if len(r) == 2 and r[0].distance < 0.75 * r[1].distance
        }

    forward, backward = accepted(left, right), accepted(right, left)
    return [(a, b) for a, b in sorted(forward.items()) if backward.get(b) == a]


def local_features(left: dict, right: dict, method: str) -> dict:
    if method not in {"orb", "sift"}:
        raise ValueError("Unknown local feature method")
    counts = [len(left["points"]), len(right["points"])]
    base = {
        "keypoints": counts,
        "matches": 0,
        "inliers": 0,
        "inlier_ratio": None,
        "reprojection_median_px": None,
    }
    if min(counts) < 4:
        return _unavailable("insufficient_keypoints", **base)
    dtype, width, norm = (
        (np.uint8, 32, cv2.NORM_HAMMING)
        if method == "orb"
        else (np.float32, 128, cv2.NORM_L2)
    )
    arrays = [np.asarray(r["descriptors"], dtype=dtype) for r in (left, right)]
    points = [np.asarray(r["points"], dtype=np.float32) for r in (left, right)]
    if any(a.shape != (n, width) for a, n in zip(arrays, counts, strict=True)) or any(
        p.shape != (n, 2) for p, n in zip(points, counts, strict=True)
    ):
        raise ValueError("Malformed local descriptors")
    if not all(np.isfinite(a).all() for a in arrays + points):
        raise ValueError("Nonfinite local descriptors")
    matches = _mutual(arrays[0], arrays[1], norm)
    base = {**base, "matches": len(matches)}
    if len(matches) < 4:
        return _unavailable("insufficient_mutual_matches", **base)
    a = points[0][[i for i, _ in matches]]
    b = points[1][[j for _, j in matches]]
    if any(np.linalg.matrix_rank(p - p.mean(axis=0), tol=1e-6) < 2 for p in (a, b)):
        return _unavailable("degenerate_points", **base)
    cv2.setRNGSeed(0)
    cv2.setNumThreads(1)
    homography, support = cv2.findHomography(
        a, b, cv2.RANSAC, 3.0, maxIters=2000, confidence=0.995
    )
    if homography is None or support is None or not np.isfinite(homography).all():
        return _unavailable("no_finite_homography", **base)
    accepted = support.ravel() != 0
    inliers = int(accepted.sum())
    base = {**base, "inliers": inliers, "inlier_ratio": inliers / len(matches)}
    if inliers < 4 or any(
        np.linalg.matrix_rank(p[accepted] - p[accepted].mean(axis=0), tol=1e-6) < 2
        for p in (a, b)
    ):
        return _unavailable("insufficient_nondegenerate_inliers", **base)
    warped = cv2.perspectiveTransform(a.reshape(-1, 1, 2), homography).reshape(-1, 2)
    error = np.linalg.norm(warped[accepted] - b[accepted], axis=1)
    if not np.isfinite(error).all():
        return _unavailable("nonfinite_projection", **base)
    return {
        "score": inliers / min(counts),
        "reason": None,
        **base,
        "reprojection_median_px": float(np.median(error)),
    }


def compare_descriptors(left: dict, right: dict) -> dict:
    calls = {
        "zncc": lambda: zncc(
            np.asarray(left["rgb"], np.uint8),
            np.asarray(left["mask"], np.uint8),
            np.asarray(right["rgb"], np.uint8),
            np.asarray(right["mask"], np.uint8),
        ),
        "orb": lambda: local_features(left["orb"], right["orb"], "orb"),
        "sift": lambda: local_features(left["sift"], right["sift"], "sift"),
        "yolo": lambda: cosine(left["yolo"], right["yolo"]),
    }
    results = {}
    for method, call in calls.items():
        started = time.perf_counter()
        results[method] = {
            **call(),
            "comparison_seconds": time.perf_counter() - started,
        }
    return results
