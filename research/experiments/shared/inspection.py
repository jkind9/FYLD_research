"""Saved-run adapters; geometry is display only and never enters estimation."""

import importlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from .geometry import associate_times
from .runs import write_json
from .visualization import artifact, depth_preview, frustum, sample_points, write_viewer


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def computation_metadata(root: Path) -> Path:
    """Resolve the original computation through immutable visual editions."""
    metadata = root / "metadata"
    while True:
        configuration = read_json(metadata / "configuration.json")
        if configuration.get("publication_only"):
            metadata = metadata / "computation"
        elif configuration.get("republication_source"):
            metadata = metadata / "previous_publication/metadata"
        else:
            return metadata


def aligned_tracking(records: list[dict], references: list, tolerance: float) -> list:
    matches = dict(
        associate_times(
            [r["timestamp_s"] for r in records], [r[0] for r in references], tolerance
        )
    )
    alignments = {}
    result: list[tuple[np.ndarray | None, np.ndarray | None, str | int | None]] = []
    for i, record in enumerate(records):
        pose = record["pose"]
        if pose is None:
            result.append((None, None, None))
            continue
        segment = pose["segment_id"]
        matrix = np.array(pose["T_world_camera"])
        if segment not in alignments:
            first = next(
                (
                    j
                    for j, r in enumerate(records)
                    if r["pose"] is not None
                    and r["pose"]["segment_id"] == segment
                    and j in matches
                ),
                None,
            )
            alignments[segment] = (
                None
                if first is None
                else references[matches[first]][1]
                @ np.linalg.inv(records[first]["pose"]["T_world_camera"])
            )
        alignment = alignments[segment]
        # Unmatched segments retain their own origin and have no reference overlay.
        transformed = matrix if alignment is None else alignment @ matrix
        reference = references[matches[i]][1] if i in matches else None
        result.append((transformed, reference, segment))
    return result


def tracking_view(root: Path) -> dict:
    evaluation = importlib.import_module(
        "experiments.03_camera_pose_estimation.src.evaluation"
    )
    records = read_json(root / "output/poses.json")["records"]
    rows = read_json(root / "output/associations.json")["rows"]
    configuration = read_json(computation_metadata(root) / "configuration.json")
    parameters = configuration["hyperparameters"]
    tolerance = parameters["association_tolerance_s"]["value"]
    calibration = dict(
        zip(
            ("width", "height", "fx", "fy", "cx", "cy"),
            parameters["intrinsics"]["value"],
            strict=True,
        )
    )
    references = evaluation.read_references(root / "input/evaluation/groundtruth.txt")
    matrices = aligned_tracking(records, references, tolerance)
    roles = [
        artifact(
            "output/poses.json",
            "predicted_output",
            "CPU RGB-D odometry",
            ["input/observations"],
            "metres; camera-to-world",
        ),
        artifact(
            "input/evaluation/groundtruth.txt",
            "ground_truth",
            "TUM motion capture",
            ["publisher groundtruth.txt"],
            "metres; camera-to-world",
        ),
        artifact(
            "output/metrics.json",
            "evaluated_output",
            "fixed-scale pose comparison",
            ["output/poses.json", "input/evaluation/groundtruth.txt"],
            "metres; radians",
        ),
    ]
    frames = []
    for order, (record, row, matrices_row) in enumerate(
        zip(records, rows, matrices, strict=True)
    ):
        matrix, reference, segment = matrices_row
        key = record["frame_id"]
        raw_rgb = "input/observations/" + row["rgb"]
        raw_depth = "input/observations/" + row["depth"]
        preview = f"debug/{key}_depth_metres.png"
        depth = np.array(Image.open(root / raw_depth), dtype=float) / 5000
        legend = depth_preview(depth, root / preview, "observed_input", raw_depth)
        roles.extend(
            [
                artifact(
                    raw_rgb, "observed_input", "TUM Kinect colour sensor", [], "RGB"
                ),
                artifact(
                    raw_depth,
                    "observed_input",
                    "TUM Kinect depth sensor",
                    [],
                    "raw units; 5000/m",
                ),
                {**legend, "path": preview},
            ]
        )
        frames.append(
            {
                "id": key,
                "order": order,
                "segment": segment,
                "status": record["status"],
                "timestamp_s": record["timestamp_s"],
                "camera": None if matrix is None else frustum(calibration, matrix),
                "reference_camera": (
                    None if reference is None else frustum(calibration, reference)
                ),
                "caption": "Predicted output: red camera/path. Ground truth: green motion-capture camera/path. "
                + f"Observed input depth: {legend['missing_fraction']:.2%} missing pixels; black remains unknown.",
                "images": [
                    {
                        "path": f"debug/{key}_rgb.png",
                        "raw": raw_rgb,
                        "caption": "Observed input: measured RGB",
                    },
                    {
                        "path": preview,
                        "raw": raw_depth,
                        "caption": "Observed input: measured depth, 0–4 m; blue near, yellow far, black missing",
                    },
                ],
            }
        )
    scene = {
        "title": "Camera motion in 3D",
        "frames": frames,
        "note": "CPU Canvas2D display. Full rigid alignment uses the first matched reference in each segment, scale one. "
        "Segments stay separate; failed observations have no pose. Depth is measured sensor input, not ground truth or model prediction.",
        "frustum_length_m": 0.15,
        "units": "metres",
        "roles": roles,
    }
    write_json(root / "metadata/artifact_roles.json", {"artifacts": roles})
    write_viewer(root, scene)
    return scene


def surface_view(root: Path, cap: int = 20000) -> dict:
    if isinstance(cap, bool) or not isinstance(cap, int) or cap < 1:
        raise ValueError("Surface display cap must be a positive integer")
    shards = read_json(root / "output/surface.json")["shards"]
    frames, roles = [], []
    per_frame = cap // max(1, len(shards))
    for order, shard in enumerate(shards):
        key = str(shard["frame_id"])
        observation = read_json(root / f"input/{key}/observation.json")
        stages = read_json(root / f"output/{key}/stages.json")
        matrix = np.array(stages["model_from_world"]) @ np.array(
            observation["pose"]["T_world_camera"]
        )
        points = np.load(root / f"output/{key}/model.npy", mmap_mode="r")
        colours = np.load(root / f"output/{key}/rgb.npy", mmap_mode="r")
        budget = per_frame + int(order < cap % max(1, len(shards)))
        sampled = (
            sample_points(points, colours, budget)
            if budget
            else {
                "points": [],
                "colours": [],
                "full_count": len(points),
                "display_count": 0,
            }
        )
        depth = np.load(root / f"output/{key}/depth.npy")
        preview = f"debug/{key}/depth_metres.png"
        legend = depth_preview(
            depth,
            root / preview,
            "ground_truth",
            f"input/{key}/depth.png",
            max(4.0, float(np.max(depth[np.isfinite(depth)], initial=0))),
        )
        roles.extend(
            [
                artifact(
                    f"input/{key}/rgb.png",
                    "observed_input",
                    "ICL synthetic colour renderer",
                    [],
                    "RGB",
                ),
                artifact(
                    f"input/{key}/depth.png",
                    "ground_truth",
                    "ICL clean synthetic depth renderer",
                    [],
                    "raw units; 5000/m",
                ),
                artifact(
                    f"input/{key}/observation.json",
                    "ground_truth",
                    "ICL synthetic camera trajectory",
                    [],
                    "metres",
                ),
                artifact(
                    f"output/{key}/model.npy",
                    "evaluated_output",
                    "CPU depth backprojection and supplied pose transform",
                    [f"input/{key}"],
                    "metres",
                ),
                artifact(
                    f"debug/{key}/distance.png",
                    "evaluated_output",
                    "CPU nearest reference distance",
                    [f"output/{key}/model.npy", "input/evaluation/living-room.ply"],
                    "metres",
                ),
                {**legend, "path": preview},
            ]
        )
        frames.append(
            dict(
                **sampled,
                id=key,
                order=order,
                segment="publisher reference coordinates",
                status="supplied camera pose",
                camera=frustum(observation["calibration"], matrix, 0.3),
                reference_camera=None,
                caption="Evaluated output: coloured point surface from ground-truth depth and poses. Camera pyramid: ground-truth pose. No fusion, mesh or filled holes.",
                images=[
                    {
                        "path": f"input/{key}/rgb.png",
                        "raw": f"input/{key}/rgb.png",
                        "caption": "Observed input: rendered colour",
                    },
                    {
                        "path": preview,
                        "raw": f"input/{key}/depth.png",
                        "caption": f"Ground truth: clean synthetic depth; 0–{legend['maximum']:.2f} m",
                    },
                    {
                        "path": f"debug/{key}/distance.png",
                        "raw": f"output/{key}/reference_distance.npy",
                        "raw_label": "Full computed distances",
                        "caption": "Evaluated output: our distance to independent reference; see per-frame legend",
                    },
                ],
            )
        )
    roles.append(
        artifact(
            "input/evaluation/living-room.ply",
            "ground_truth",
            "ICL publisher reference surface",
            [],
            "metres",
        )
    )
    reader = importlib.import_module(
        "experiments.04_surface_reconstruction.src.dataset"
    )
    reference = reader.read_reference(root / "input/evaluation/living-room.ply")
    reference_sample = sample_points(
        reference, np.broadcast_to([125, 170, 190], reference.shape), cap
    )
    scene = {
        "title": "Reconstructed point surface in 3D",
        "reference_points": {**reference_sample, "role": "ground_truth"},
        "frames": frames,
        "note": "Evaluated output built from ground-truth synthetic depth and poses. Points accumulate through the selected frame. "
        "Deterministic display sampling only; full arrays and PLY files retain every point. This is a point surface, not a mesh. "
        "Coloured points are our evaluated output. Toggle ground truth to overlay the independent reference in muted blue.",
        "units": "metres",
        "frustum_length_m": 0.3,
        "display_cap": cap,
        "full_count": sum(f["full_count"] for f in frames),
        "display_count": sum(f["display_count"] for f in frames),
        "roles": roles,
    }
    write_json(root / "metadata/artifact_roles.json", {"artifacts": roles})
    write_viewer(root, scene)
    return scene
