"""Display supplied poses and full per-frame geometry; no inference or fusion."""

import json
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from experiments.shared.contracts import Pose, require_same_origin
from experiments.shared.runs import write_json


def _saved_geometry(
    path: Path, frames: list[dict]
) -> tuple[list[Pose], list[np.ndarray]]:
    if not frames:
        raise ValueError("Cannot visualize an empty frame selection")
    poses: list[Pose] = []
    points: list[np.ndarray] = []
    for frame in frames:
        key = frame["frame_id"]
        record = json.loads((path / f"input/{key}/observation.json").read_text())[
            "pose"
        ]
        if record["source"] != "supplied":
            raise ValueError("This control view requires supplied poses")
        if (
            record.get("units") != "metres"
            or record.get("direction") != "camera_to_world"
        ):
            raise ValueError(
                "Supplied pose must use metres and camera_to_world direction"
            )
        pose = Pose(
            np.asarray(record["T_world_camera"]),
            record["world_id"],
            record["segment_id"],
            record["source"],
        )
        if poses:
            require_same_origin(poses[0], pose)
        cloud = np.load(path / f"output/{key}/world.npy", allow_pickle=False)
        if cloud.shape != (frame["valid_pixels"], 3) or not np.isfinite(cloud).all():
            raise ValueError(
                "World points must preserve finite valid-pixel correspondence"
            )
        poses.append(pose)
        points.append(cloud)
    return poses, points


def _scene_plot(
    path: Path, frames: list[dict], clouds: list[np.ndarray], centres: np.ndarray
) -> None:
    figure = Figure(figsize=(10, 8))
    FigureCanvasAgg(figure)
    axes = figure.add_subplot(111, projection="3d")
    for frame, points in zip(frames, clouds, strict=True):
        axes.scatter(
            *points.T,
            s=0.15,
            alpha=0.35,
            label=f"Frame {frame['frame_id']} supplied-depth points",
        )
    axes.scatter(
        *centres.T, c="black", marker="^", s=65, label="Supplied camera centres"
    )
    for frame, position in zip(frames, centres, strict=True):
        axes.text(*position, f" Camera {frame['frame_id']}")
    extent = np.ptp(np.concatenate([centres, *clouds]), axis=0)
    axes.set_box_aspect(np.maximum(extent, 1e-9))
    axes.set(
        xlabel="World X (metres)",
        ylabel="World Y (metres)",
        zlabel="World Z (metres)",
        title="All supplied observations in one world; no fusion or tracking",
    )
    axes.legend(loc="upper left")
    figure.savefig(path, dpi=120)
    figure.clear()


def _camera_plot(path: Path, frames: list[dict], relative: np.ndarray) -> None:
    figure = Figure(figsize=(9, 7))
    FigureCanvasAgg(figure)
    axes = figure.add_subplot(111, projection="3d")
    axes.plot(*relative.T, color="#234b73", marker="o")
    for frame, position in zip(frames, relative, strict=True):
        axes.text(*position, f" {frame['frame_id']}")
    axes.set_box_aspect(np.maximum(np.ptp(relative, axis=0), 1))
    axes.set(
        xlabel="World X offset (millimetres)",
        ylabel="World Y offset (millimetres)",
        zlabel="World Z offset (millimetres)",
        title="Supplied camera centres relative to first selected view",
    )
    figure.text(
        0.08,
        0.02,
        "Line connects selected supplied positions; movement was not estimated.",
    )
    figure.savefig(path, dpi=120)
    figure.clear()


def export_scene(path: Path, frames: list[dict]) -> dict:
    poses, clouds = _saved_geometry(path, frames)
    centres = np.stack([pose.matrix[:3, 3] for pose in poses])
    relative = (centres - centres[0]) * 1000
    debug = path / "debug"
    debug.mkdir(exist_ok=True)
    _scene_plot(debug / "scene_world.png", frames, clouds, centres)
    _camera_plot(debug / "camera_positions.png", frames, relative)
    summary = {
        "frame_ids": [frame["frame_id"] for frame in frames],
        "world_id": poses[0].world_id,
        "segment_id": poses[0].segment_id,
        "pose_source": "supplied",
        "centres_world_m": centres.tolist(),
        "relative_centres_mm": relative.tolist(),
        "points_per_frame": [len(cloud) for cloud in clouds],
        "interpretation": "Full separate supplied-depth point clouds; no inferred poses, fusion or surface score",
    }
    write_json(debug / "scene.json", summary)
    return summary
