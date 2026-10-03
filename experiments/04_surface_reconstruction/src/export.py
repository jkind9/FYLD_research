"""Lossless point shards and per-pixel scoring diagnostics."""

from pathlib import Path

import numpy as np
from PIL import Image

from experiments.geometry_validation.src.control import Stages
from experiments.geometry_validation.src.icl import Frame
from experiments.shared.exporting import _raster
from experiments.shared.runs import write_json


def export_shard(
    output: Path, debug: Path, frame: Frame, stages: Stages, distances: np.ndarray
) -> dict:
    output.mkdir(parents=True)
    debug.mkdir(parents=True)
    for name in (
        "depth",
        "mask",
        "pixels",
        "camera",
        "world",
        "model",
        "projection_error",
    ):
        np.save(output / f"{name}.npy", getattr(stages, name), allow_pickle=False)
    colors = frame.rgb[stages.pixels[:, 0], stages.pixels[:, 1]]
    np.save(output / "rgb.npy", colors, allow_pickle=False)
    np.save(output / "reference_distance.npy", distances, allow_pickle=False)
    dtype = np.dtype(
        [
            ("x", "<f8"),
            ("y", "<f8"),
            ("z", "<f8"),
            ("red", "u1"),
            ("green", "u1"),
            ("blue", "u1"),
        ]
    )
    cloud = np.empty(len(stages.model), dtype=dtype)
    for i, key in enumerate(("x", "y", "z")):
        cloud[key] = stages.model[:, i]
    for i, key in enumerate(("red", "green", "blue")):
        cloud[key] = colors[:, i]
    with (output / "surface.ply").open("xb") as stream:
        header = (
            "ply\nformat binary_little_endian 1.0\n"
            f"element vertex {len(cloud)}\nproperty double x\nproperty double y\n"
            "property double z\nproperty uchar red\nproperty uchar green\n"
            "property uchar blue\nend_header\n"
        )
        stream.write(header.encode("ascii"))
        stream.write(cloud.tobytes())
    raster = np.full(stages.depth.shape, np.nan)
    raster[stages.mask] = distances
    legends = {
        "depth.png": _raster(debug / "depth.png", stages.depth, "metres"),
        "distance.png": _raster(debug / "distance.png", raster, "metres"),
    }
    Image.fromarray(stages.mask.astype(np.uint8) * 255).save(debug / "mask.png")
    write_json(debug / "legends.json", legends)
    return {
        "frame_id": frame.observation.frame_id,
        "points": len(stages.model),
        "coordinates": "publisher_reference_surface",
        "units": "metres",
        "point_file": f"{frame.observation.frame_id}/model.npy",
        "cloud_file": f"{frame.observation.frame_id}/surface.ply",
        "pixel_file": f"{frame.observation.frame_id}/pixels.npy",
        "colour_file": f"{frame.observation.frame_id}/rgb.npy",
        "observation": f"../input/{frame.observation.frame_id}/observation.json",
    }
