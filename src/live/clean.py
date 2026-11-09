"""Clean-up trials for fused learned depth: per-frame masks, near-first fusion passes and a visibility vote.

Sources and reasons are in research/surface_denoising/README.md. The thresholds are first trial settings proposed
by Claude, not tuned on data and not owner-ruled.
"""

from __future__ import annotations

import cv2
import numpy as np
import open3d as o3d
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

EDGE_JUMP = 0.05  # depth range within a 3 x 3 neighbourhood, as a share of the pixel's depth
MAX_VIEW_ANGLE_DEG = 75.0  # between the camera ray and the surface normal
NORMAL_STEP = 2  # pixels either side used for normals; one-pixel steps make learned-depth normals noisy
# (from m, to m, repeats): repeats round (4 m / z)^2, so a reading at 1 m counts about 16 times one at 4 m (Voxblox)
NEAR_FIRST_BANDS = ((0.0, 1.0, 16), (1.0, 2.0, 4), (2.0, 3.0, 2), (3.0, np.inf, 1))
VOTE_MARGIN_M = 0.08  # four 2 cm voxels: the fusion truncation
VOTE_MARGIN_SHARE = 0.05  # about the learned depth's median relative error against ARCore (Tasks109, 113)
SOR_NEIGHBOURS, SOR_STD_RATIO = 20, 2.0  # Open3D's outlier-removal tutorial values
RADIUS_M, RADIUS_MIN_POINTS = 0.05, 16  # Open3D tutorial values; a 5 cm disc of 2 cm surface holds about 20 points
CLUSTER_EPS_M = 0.05  # 2.5 voxels: neighbouring surface points join; a gap over 5 cm starts a new cluster
CLUSTER_MIN_POINTS = 1000  # about 0.4 m^2 of surface at 2 cm spacing; smaller clusters count as floating
MEASURED_M = 2.5  # ARCore depth rarely reaches past 2.5 m (Task117); nearer learned depth is sized from it
WIDE_ANGLE_DEG = 3.0  # COLMAP's filter_min_triangulation_angle: views closer in angle are not independent evidence
PIECE_EPS_M = 0.03  # the 3 cm join that removed the most floating points in Task122
PIECE_NORMAL_DEG = 30.0  # PCL's conditional-clustering tutorial joins neighbours whose normals differ by under 30°
VOTE_FAR_M = 8.0  # see-through evidence for the vote: well past the 4 m fusion limit, inside a 10 m room
# Owner, 8 November 2026, by eye in the clean-up tuner: a continuous walk joins the room into a few large pieces,
# so keep the 50 largest that hold at least 5,000 points each.
ROOM_PIECES, ROOM_PIECE_MIN_POINTS = 50, 5000


def edge_mask(depth: np.ndarray, jump: float = EDGE_JUMP) -> np.ndarray:
    """Pixels whose 3 x 3 neighbourhood spans more than `jump` of their depth: flying-pixel candidates."""
    d = depth.astype(np.float32)
    kernel = np.ones((3, 3), np.uint8)
    return (depth > 0) & (cv2.dilate(d, kernel) - cv2.erode(d, kernel) > jump * depth)


def view_angle_mask(depth: np.ndarray, intrinsics, max_angle_deg: float = MAX_VIEW_ANGLE_DEG,
                    step: int = NORMAL_STEP) -> np.ndarray:
    """Pixels whose surface, from neighbours `step` pixels away, is seen more than max_angle_deg off its normal."""
    fx, fy, cx, cy = intrinsics
    h, w = depth.shape
    u, v = np.meshgrid(np.arange(w), np.arange(h))
    points = np.dstack(((u - cx) / fx * depth, (v - cy) / fy * depth, depth))
    across = np.roll(points, -step, axis=1) - np.roll(points, step, axis=1)
    down = np.roll(points, -step, axis=0) - np.roll(points, step, axis=0)
    normal = np.cross(across, down)
    cosine = np.abs((normal * points).sum(-1)) / (np.linalg.norm(normal, axis=-1) * np.linalg.norm(points, axis=-1)
                                                   + 1e-12)
    mask = (depth > 0) & (cosine < np.cos(np.radians(max_angle_deg)))
    mask[:step], mask[-step:], mask[:, :step], mask[:, -step:] = False, False, False, False  # np.roll wraps there
    return mask


def near_first_passes(depth: np.ndarray, bands=NEAR_FIRST_BANDS) -> list[tuple[np.ndarray, int]]:
    """(depth kept in one distance band, repeats). Fusing each pass `repeats` times weights near readings more."""
    passes = []
    for low, high, repeats in bands:
        mine = (depth > 0) & (depth >= low) & (depth < high)
        if mine.any():
            passes.append((np.where(mine, depth, 0.0), repeats))
    return passes


def keep_after(points: np.ndarray, kind: str, eps: float = CLUSTER_EPS_M) -> np.ndarray:
    """Points kept by one point-cloud filter: "sor" (statistical outliers), "radius" or "clusters" (floating pieces).

    For "clusters", points closer than `eps` join one piece; pieces under CLUSTER_MIN_POINTS are dropped.
    """
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    keep = np.zeros(len(points), bool)
    if kind == "clusters":
        labels = np.asarray(cloud.cluster_dbscan(eps, min_points=10))
        sizes = np.bincount(labels[labels >= 0], minlength=1)
        return (labels >= 0) & (sizes[np.maximum(labels, 0)] >= CLUSTER_MIN_POINTS)
    if kind == "sor":
        _, index = cloud.remove_statistical_outlier(SOR_NEIGHBOURS, SOR_STD_RATIO)
    elif kind == "radius":
        _, index = cloud.remove_radius_outlier(RADIUS_MIN_POINTS, RADIUS_M)
    else:
        raise ValueError(f"unknown filter {kind}")
    keep[index] = True
    return keep


def largest_pieces(points: np.ndarray, cell: float, keep: int = ROOM_PIECES,
                   min_points: int = ROOM_PIECE_MIN_POINTS) -> np.ndarray:
    """Points in the `keep` largest pieces that hold at least min_points each.

    A piece is a run of filled grid cells `cell` wide, each touching the next at a face, edge or corner: the 3D form
    of cv2.connectedComponents, and of splats `cell` wide that touch. Bigger cells bridge wider gaps.
    """
    index = np.floor((points - points.min(0)) / cell).astype(np.int64)
    filled = np.zeros(index.max(0) + 1, bool)
    filled[tuple(index.T)] = True
    piece = ndimage.label(filled, structure=np.ones((3, 3, 3)))[0][tuple(index.T)]
    sizes = np.bincount(piece)
    largest = np.argsort(sizes)[::-1][:keep]
    return np.isin(piece, largest[sizes[largest] >= min_points])


def visibility_vote(points: np.ndarray, views) -> np.ndarray:
    """Points to keep: weighted support at least weighted free-space violations (after Merrell et al. 2007)."""
    support, against = vote_tallies(points, views)
    return support >= against


def vote_tallies(points: np.ndarray, views) -> tuple[np.ndarray, np.ndarray]:
    """Per point: weighted views supporting it and weighted views seeing through it.

    views: (camera_from_world, intrinsics, depth image) per frame. A view supports a point it measures at the
    point's depth (within the margin) and violates one it sees through. Votes weigh 1 / depth^2, so near views
    outvote far ones.
    """
    support, against = np.zeros(len(points)), np.zeros(len(points))
    for z, measured in _measurements(points, views):
        seen = measured > 0
        margin = np.maximum(VOTE_MARGIN_M, VOTE_MARGIN_SHARE * measured)
        weight = 1.0 / np.maximum(measured, 0.5) ** 2
        support += np.where(seen & (np.abs(z - measured) <= margin), weight, 0.0)
        against += np.where(seen & (z < measured - margin), weight, 0.0)
    return support, against


def views_measuring(points: np.ndarray, views) -> np.ndarray:
    """How many views measure each point at its depth, within the vote margin: its observation count."""
    count = np.zeros(len(points), int)
    for z, measured in _measurements(points, views):
        count += _agrees(z, measured)
    return count


def wide_support(points: np.ndarray, views, measured_m: float = MEASURED_M, angle_deg: float = WIDE_ANGLE_DEG
                 ) -> np.ndarray:
    """Points to keep: measured nearer than measured_m by some view, or by two more views whose rays meet the point
    at least angle_deg away from the first measuring view's ray (after COLMAP's geometric-consistency filter, whose
    filter_min_num_consistent is 2).

    Frames from one standing spot share one guess at far depth's size, so only views from elsewhere confirm it.
    """
    nearest, second_widest = spot_evidence(points, views)
    return (nearest < measured_m) | (second_widest >= angle_deg)


def spot_evidence(points: np.ndarray, views) -> tuple[np.ndarray, np.ndarray]:
    """Per point: the nearest depth a view measured it at (inf if none), and the second-widest angle in degrees
    between a measuring view's ray and the first measuring view's ray (0 with fewer than two more views)."""
    first, widest = np.zeros((len(points), 3)), np.zeros((len(points), 2))
    nearest = np.full(len(points), np.inf)
    for (camera_from_world, _, _), (z, measured) in zip(views, _measurements(points, views)):
        agrees = _agrees(z, measured)
        nearest[agrees] = np.minimum(nearest[agrees], measured[agrees])
        mine = np.flatnonzero(agrees)
        ray = -camera_from_world[:3, :3].T @ camera_from_world[:3, 3] - points[mine]
        ray /= np.linalg.norm(ray, axis=1, keepdims=True)
        new = ~first[mine].any(1)
        first[mine[new]] = ray[new]
        angle = np.where(new, 0.0, np.degrees(np.arccos(np.clip((ray * first[mine]).sum(1), -1.0, 1.0))))
        top, second = widest[mine, 0], widest[mine, 1]
        widest[mine, 1] = np.maximum(second, np.minimum(top, angle))
        widest[mine, 0] = np.maximum(top, angle)
    return nearest, widest[:, 1]


def piece_majority(points: np.ndarray, normals: np.ndarray, suspect: np.ndarray, eps: float = PIECE_EPS_M,
                   max_angle_deg: float = PIECE_NORMAL_DEG) -> np.ndarray:
    """Points to keep: not suspect, and not in a piece whose points are mostly suspect.

    Neighbours within eps join one piece only if their normals differ by under max_angle_deg (PCL's conditional
    Euclidean clustering), so a side-on strip at a corner does not join an echo copy to the wall behind it.
    """
    pairs = cKDTree(points).query_pairs(eps, output_type="ndarray")
    alike = np.abs((normals[pairs[:, 0]] * normals[pairs[:, 1]]).sum(1)) >= np.cos(np.radians(max_angle_deg))
    graph = coo_matrix((np.ones(alike.sum()), (pairs[alike, 0], pairs[alike, 1])), shape=(len(points), len(points)))
    _, piece = connected_components(graph, directed=False)
    suspect_share = np.bincount(piece, weights=suspect) / np.bincount(piece)
    return ~suspect & (suspect_share[piece] <= 0.5)


def _agrees(z: np.ndarray, measured: np.ndarray) -> np.ndarray:
    """The view measured the point at its depth, within the vote margin."""
    return (measured > 0) & (np.abs(z - measured) <= np.maximum(VOTE_MARGIN_M, VOTE_MARGIN_SHARE * measured))


def _measurements(points: np.ndarray, views):
    """Per view: each point's depth in that camera and the depth the view measured at its pixel (0 if none)."""
    for camera_from_world, (fx, fy, cx, cy), depth in views:
        h, w = depth.shape
        camera = points @ camera_from_world[:3, :3].T + camera_from_world[:3, 3]
        z = camera[:, 2]
        ahead = z > 0.1
        safe_z = np.where(ahead, z, 1.0)
        u = np.round(camera[:, 0] / safe_z * fx + cx).astype(int)
        v = np.round(camera[:, 1] / safe_z * fy + cy).astype(int)
        inside = ahead & (u >= 0) & (u < w) & (v >= 0) & (v < h)
        measured = np.zeros(len(points))
        measured[inside] = depth[v[inside], u[inside]]
        yield z, measured
