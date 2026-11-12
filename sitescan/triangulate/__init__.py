"""Depth triangulated between frames with known poses: sparse features and dense sweeps."""

from .geometry import (
    depth_sigma,
    epipolar_distance,
    parallax,
    project,
    rays,
    triangulate,
)
from .sparse import Features, SparseDepth, detect, match, merge, triangulate_pair
from .sweep import (
    aggregate,
    best_depth,
    candidate_depths,
    census,
    matching_costs,
    plane_count,
    sweep_depth,
)
from .window import Keyframe, Triangulator, references, view_angle_deg

__all__ = [
    "Features",
    "Keyframe",
    "SparseDepth",
    "Triangulator",
    "aggregate",
    "best_depth",
    "candidate_depths",
    "census",
    "depth_sigma",
    "detect",
    "epipolar_distance",
    "match",
    "matching_costs",
    "merge",
    "parallax",
    "plane_count",
    "project",
    "rays",
    "references",
    "sweep_depth",
    "triangulate",
    "triangulate_pair",
    "view_angle_deg",
]
