"""Sparse depth at features matched between a frame and an earlier keyframe, both posed."""

from dataclasses import dataclass

import cv2
import numpy as np

from sitescan.types import Camera

from .geometry import depth_sigma, epipolar_distance, parallax, project, triangulate

FEATURES = 2000
RATIO = 0.8
MAX_EPIPOLAR_PX = 4.0
MAX_REPROJECTION_PX = 2.0
MIN_PARALLAX_DEG = 1.0
SIGMA_PX = 1.0
MAX_RELATIVE_SIGMA = 0.1


@dataclass(frozen=True)
class Features:
    """ORB corners: N x 2 pixel positions and N x 32 binary descriptors."""

    uv: np.ndarray
    descriptors: np.ndarray


@dataclass(frozen=True)
class SparseDepth:
    """Camera-plane depth at N feature pixels of a frame, with standard error and feature index."""

    uv: np.ndarray
    depth_m: np.ndarray
    sigma_m: np.ndarray
    index: np.ndarray


def detect(grey: np.ndarray, count: int = FEATURES) -> Features:
    """ORB corners and descriptors of a grey image, at most `count` of them."""
    keypoints, descriptors = cv2.ORB_create(count).detectAndCompute(grey, None)
    if descriptors is None:
        return Features(np.zeros((0, 2)), np.zeros((0, 32), np.uint8))
    return Features(np.array([k.pt for k in keypoints], dtype=np.float64), descriptors)


def match(a: Features, b: Features, ratio: float = RATIO) -> tuple[np.ndarray, np.ndarray]:
    """Indices of mutual best matches whose Hamming distance beats the second best by `ratio`."""
    if len(a.uv) < 2 or len(b.uv) < 2:
        return np.zeros(0, int), np.zeros(0, int)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    forward = matcher.knnMatch(a.descriptors, b.descriptors, k=2)
    backward = {m.queryIdx: m.trainIdx for m in matcher.match(b.descriptors, a.descriptors)}
    pairs = [
        (m.queryIdx, m.trainIdx)
        for m, n in forward
        if m.distance < ratio * n.distance and backward.get(m.trainIdx) == m.queryIdx
    ]
    if not pairs:
        return np.zeros(0, int), np.zeros(0, int)
    index_a, index_b = np.array(pairs).T
    return index_a, index_b


def triangulate_pair(
    frame: Features,
    camera: Camera,
    pose: np.ndarray,
    keyframe: Features,
    keyframe_camera: Camera,
    keyframe_pose: np.ndarray,
) -> SparseDepth:
    """Depth at the frame's features matched in the keyframe, for matches the poses support.

    A match must lie within 4 px of its epipolar line, triangulate in front of both cameras,
    reproject within 2 px in both images, cross at 1 degree or more, and have a depth error of
    at most 10%. The error assumes 1 px of feature noise.
    """
    i, j = match(frame, keyframe)
    uv, uv_k = frame.uv[i], keyframe.uv[j]
    near_line = (
        epipolar_distance(uv_k, uv, keyframe_camera, camera, keyframe_pose, pose) <= MAX_EPIPOLAR_PX
    )
    i, uv, uv_k = i[near_line], uv[near_line], uv_k[near_line]
    points = triangulate(uv, uv_k, camera, keyframe_camera, pose, keyframe_pose)
    seen, depth = project(points, camera, pose)
    seen_k, depth_k = project(points, keyframe_camera, keyframe_pose)
    angle = parallax(points, pose, keyframe_pose)
    sigma = depth_sigma(depth, angle, camera.fx, SIGMA_PX)
    with np.errstate(invalid="ignore"):
        keep = (
            (depth > 0)
            & (depth_k > 0)
            & (np.linalg.norm(seen - uv, axis=1) <= MAX_REPROJECTION_PX)
            & (np.linalg.norm(seen_k - uv_k, axis=1) <= MAX_REPROJECTION_PX)
            & (angle >= np.radians(MIN_PARALLAX_DEG))
            & (sigma <= MAX_RELATIVE_SIGMA * depth)
        )
    return SparseDepth(uv[keep], depth[keep], sigma[keep], i[keep])


def merge(depths: list[SparseDepth]) -> SparseDepth:
    """One depth per feature: the inverse-variance mean of its depths from every keyframe."""
    if not depths:
        return SparseDepth(np.zeros((0, 2)), np.zeros(0), np.zeros(0), np.zeros(0, int))
    index = np.concatenate([d.index for d in depths])
    uv = np.concatenate([d.uv for d in depths])
    weight = 1.0 / np.concatenate([d.sigma_m for d in depths]) ** 2
    weighted = np.concatenate([d.depth_m for d in depths]) * weight
    features, first, inverse = np.unique(index, return_index=True, return_inverse=True)
    total = np.bincount(inverse, weight)
    depth = np.bincount(inverse, weighted) / total
    return SparseDepth(uv[first], depth, 1.0 / np.sqrt(total), features)
