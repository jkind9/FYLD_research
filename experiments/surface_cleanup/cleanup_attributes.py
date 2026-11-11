"""The raw fused room and, per point, the evidence each clean-up stage tests, for the clean-up tuner page.

    python -B -m experiments.surface_cleanup.cleanup_attributes --session <v2 session> --out <folder>

Writes raw.ply (room pipeline rules, no clean-up) and attributes.npz. The page applies the thresholds itself, so
moving a slider needs no depth maps. Chain linking and radius outliers depend on which points remain, so the page
computes those from the points alone.
"""

from __future__ import annotations

import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree

from apps.cli import parse_room_args, room_parser
from experiments.surface_cleanup.filters import SOR_NEIGHBOURS
from experiments.surface_cleanup.support import spot_evidence, views_measuring
from sitescan.cleanup import vote_tallies
from sitescan.depth import load_model
from sitescan.pipelines import DEPTH_MODEL

from .denoise_trial import VARIANTS, collect, fuse


def point_attributes(points: np.ndarray, views) -> dict[str, np.ndarray]:
    """Per point: frames measuring it, see-through share of the weighted vote, nearest measured depth, second-widest
    angle between measuring views, and mean distance to its SOR_NEIGHBOURS nearest neighbours.

    views: (camera_from_world, intrinsics, fused depth, see-through evidence) per frame, as denoise_trial.fuse gives.
    """
    fused = [(camera, k, depth) for camera, k, depth, _ in views]
    support, against = vote_tallies(points, [(camera, k, evidence) for camera, k, _, evidence in views])
    total = support + against
    nearest, second = spot_evidence(points, fused)
    distances, _ = cKDTree(points).query(points, k=SOR_NEIGHBOURS + 1)  # the first neighbour is the point
    return {"seen": views_measuring(points, fused),
            "see_through": np.divide(against, total, out=np.zeros(len(points)), where=total > 0),
            "nearest_m": nearest, "second_angle_deg": second, "knn_mean_m": distances[:, 1:].mean(1)}


def main(argv: list[str] | None = None) -> int:
    args = parse_room_args(room_parser(__doc__.splitlines()[0]), argv)
    events, outcome = collect(args.session, load_model(DEPTH_MODEL, threads=args.threads))
    surface, colours, _, _, views = fuse(events, VARIANTS["baseline"], args.voxel, args.far)
    args.out.mkdir(parents=True)
    cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(surface))
    cloud.colors = o3d.utility.Vector3dVector(np.clip(colours, 0.0, 1.0))
    o3d.io.write_point_cloud(str(args.out / "raw.ply"), cloud)
    np.savez_compressed(args.out / "attributes.npz", **point_attributes(surface, views))
    print(f"{len(surface):,} points from {outcome['frames']} frames -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
