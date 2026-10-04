"""Build the shareable demo pages in demo_outputs/ from saved experiment runs.

Usage, from the repository root:
    python -B -m tools.demos.build --source-root <checkout with local runs and data>

No experiment is rerun. The only computation is back-projecting saved depth with saved
poses, merging repeated points, building splats and drawing thumbnails.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np

from tools.demos.geometry import top_down_grid
from tools.demos.pack import colormap, image_data_url
from tools.demos.page import write_page
from tools.demos.pages_overview import overview, thumbnails
from tools.demos.pages_results import (
    ERROR_RANGE_M,
    camera_tracking,
    objects_in_3d,
    surface_accuracy,
)
from tools.demos.pages_scene import (
    DEPTH_FRAME_INDEX,
    birds_eye,
    depth_to_3d,
    gaussian_splats,
)
from tools.demos.sources import (
    TRACKING_RUN,
    fused_desk_scene,
    load_cup_spread,
    load_reference_sample,
    load_replay,
    load_surface,
    load_tracking,
    read_rgb,
)

# Display settings. They affect only how saved data is drawn, not any measured result.
SETTINGS = {
    "fusion_stride_px": 2,
    "depth_edge_relative_jump": 0.03,
    "splat_voxel_m": 0.008,
    "scene_voxel_m": 0.012,
    "splat_min_observations": 3,
    "splat_compare_frames": [0, 12, 24, 36, 48, 59],
    "birds_eye_cell_m": 0.02,
    "birds_eye_height_range_m": (-0.1, 1.9),
    "birds_eye_colour_range_m": (0.0, 1.2),
    "surface_points_per_view": 30000,
    "reference_points": 200000,
    "sample_seed": 7,
    "max_page_mb": 15,
}
STORY = {"before": "104", "gap": "268", "after": "359"}

log = logging.getLogger("demos")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-root", type=Path, required=True, help="checkout containing local experiment runs and data")
    parser.add_argument("--out", type=Path, default=Path("demo_outputs"), help="output folder")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    root, out, s = args.source_root.resolve(), args.out, SETTINGS
    budget = int(s["max_page_mb"] * 1e6)
    sizes: dict[str, int] = {}

    replay = load_replay(root)
    log.info("merging %d desk frames", len(replay["frames"]))
    scene = fused_desk_scene(replay["frames"], s["fusion_stride_px"], s["depth_edge_relative_jump"], s["scene_voxel_m"], s["splat_min_observations"])
    fine = fused_desk_scene(replay["frames"], s["fusion_stride_px"], s["depth_edge_relative_jump"], s["splat_voxel_m"], s["splat_min_observations"])

    doc, depth_stats = depth_to_3d(replay)
    sizes["01_depth_to_3d.html"] = write_page(out, "01_depth_to_3d.html", doc, budget)

    tracking = load_tracking(root)
    doc, track_stats = camera_tracking(root, tracking)
    sizes["02_camera_tracking.html"] = write_page(out, "02_camera_tracking.html", doc, budget)

    surface = load_surface(root, s["surface_points_per_view"], s["sample_seed"])
    reference = load_reference_sample(root, s["reference_points"], s["sample_seed"])
    doc, surf_stats = surface_accuracy(root, surface, reference)
    sizes["03_surface_accuracy.html"] = write_page(out, "03_surface_accuracy.html", doc, budget)

    doc, splat_stats = gaussian_splats(replay, fine, s["splat_voxel_m"], s["splat_compare_frames"])
    sizes["04_gaussian_splats.html"] = write_page(out, "04_gaussian_splats.html", doc, budget)

    doc, map_stats = birds_eye(scene, s["birds_eye_cell_m"], s["birds_eye_height_range_m"], s["birds_eye_colour_range_m"])
    sizes["05_birds_eye_map.html"] = write_page(out, "05_birds_eye_map.html", doc, budget)

    cup = load_cup_spread(root)
    doc, obj_stats = objects_in_3d(replay, scene, s["scene_voxel_m"], STORY, cup)
    sizes["06_objects_in_3d.html"] = write_page(out, "06_objects_in_3d.html", doc, budget)

    grid = top_down_grid(scene["positions"], scene["colours"], 2, s["birds_eye_cell_m"], s["birds_eye_height_range_m"])
    birds_rgb = np.flipud(np.where(grid["observed"][..., None], grid["colour"], 200)).astype(np.uint8)
    err = colormap(surface["distance_m"], *ERROR_RANGE_M)
    top = top_down_grid(surface["points"], err, 1, 0.03, (-1.0, 2.4))
    surface_top = np.where(top["observed"][..., None], top["colour"], 21).astype(np.uint8)
    thumbs = thumbnails(replay, scene, birds_rgb, surface_top, DEPTH_FRAME_INDEX)
    obs = root / TRACKING_RUN / "input/observations"
    first = next(line.split()[1] for line in (obs / "rgb.txt").read_text().splitlines() if line and not line.startswith("#"))
    thumbs["tracking"] = image_data_url(read_rgb(obs / first), size=(360, 270))
    results = [
        ("3 · Camera position", "30 frames of a desk recording", f"{track_stats['rmse_mm']:.1f} mm", "Full-length runs, phone video, drift on long walks"),
        ("4 · Environment", "9 views of a synthetic room", f"{surf_stats['mean_mm']:.1f} mm mean distance; {surf_stats['coverage_pct']:.1f}% of room covered", "Real phone depth, tracked camera paths, meshes"),
        ("5 · Objects", "60-frame desk replay", f"{obj_stats['detections']} detections → {obj_stats['objects']} identities", "Accuracy against an independently labelled inventory"),
        ("5 · Objects", "Cup position over repeat sightings", f"{cup['rms_mm']:.0f} mm spread ({cup['n']} sightings)", "Error against the cup's true centre, which was not surveyed"),
    ]
    sizes["00_overview.html"] = write_page(out, "00_overview.html", overview(thumbs, results), budget)

    log.info("desk scene: %d raw points merged into %d splats", splat_stats["raw"], splat_stats["splats"])
    log.info("depth page: %.1f%% pixels valid; map: %.1f m2 seen", depth_stats["valid_pct"], map_stats["seen_m2"])
    for name, size in sorted(sizes.items()):
        log.info("%-26s %6.2f MB", name, size / 1e6)


if __name__ == "__main__":
    main()
