"""Rejected point outlier filters and normal-based component tests."""

import numpy as np
import open3d as o3d
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

SOR_NEIGHBOURS = 20
SOR_STD_RATIO = 2.0
RADIUS_M = 0.05
RADIUS_MIN_POINTS = 16
CLUSTER_EPS_M = 0.05
CLUSTER_MIN_POINTS = 1000
PIECE_EPS_M = 0.03
PIECE_NORMAL_DEG = 30.0


def keep_after(points: np.ndarray, kind: str, eps: float = CLUSTER_EPS_M) -> np.ndarray:
    """A mask from a rejected statistical, radius or density-cluster filter."""
    surface = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    mask = np.zeros(len(points), bool)
    if kind == "clusters":
        labels = np.asarray(surface.cluster_dbscan(eps, min_points=10))
        counts = np.bincount(labels[labels >= 0], minlength=1)
        return (labels >= 0) & (counts[np.maximum(labels, 0)] >= CLUSTER_MIN_POINTS)
    if kind == "sor":
        _, indices = surface.remove_statistical_outlier(SOR_NEIGHBOURS, SOR_STD_RATIO)
    elif kind == "radius":
        _, indices = surface.remove_radius_outlier(RADIUS_MIN_POINTS, RADIUS_M)
    else:
        raise ValueError(f"unknown filter {kind}")
    mask[indices] = True
    return mask


def piece_majority(
    points: np.ndarray,
    normals: np.ndarray,
    suspect: np.ndarray,
    eps: float = PIECE_EPS_M,
    max_angle_deg: float = PIECE_NORMAL_DEG,
) -> np.ndarray:
    """A mask rejecting suspect points and pieces whose majority is suspect."""
    neighbours = cKDTree(points).query_pairs(eps, output_type="ndarray")
    aligned = np.abs((normals[neighbours[:, 0]] * normals[neighbours[:, 1]]).sum(1)) >= np.cos(
        np.radians(max_angle_deg)
    )
    links = coo_matrix(
        (np.ones(aligned.sum()), (neighbours[aligned, 0], neighbours[aligned, 1])),
        shape=(len(points), len(points)),
    )
    _, labels = connected_components(links, directed=False)
    share = np.bincount(labels, weights=suspect) / np.bincount(labels)
    return ~suspect & (share[labels] <= 0.5)
