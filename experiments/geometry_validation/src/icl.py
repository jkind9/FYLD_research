"""Clean ICL trajectory-2 adapter; exact image IDs, never positional pose shifts."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from experiments.shared.contracts import Calibration, Observation, Pose
from experiments.shared.geometry import pose_matrix, validate_transform


@dataclass(frozen=True)
class Frame:
    observation: Observation
    rgb: NDArray
    raw_depth: NDArray
    rgb_path: Path
    depth_path: Path
    model_from_first: NDArray
    world_from_first: NDArray


def select_ids(ids: list[int]) -> list[int]:
    if (
        not ids
        or any(type(i) is not int or i < 1 for i in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValueError(
            "Select distinct positive exact posed frame IDs; image 0 has no pose"
        )
    return list(ids)


def read_poses(path: Path) -> dict[int, NDArray]:
    poses = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        row = line.split()
        if len(row) != 8:
            raise ValueError("Pose row must have ID, translation and xyzw quaternion")
        frame_id = int(row[0])
        if frame_id in poses:
            raise ValueError("duplicate pose ID")
        poses[frame_id] = pose_matrix(
            [float(x) for x in row[1:4]], [float(x) for x in row[4:]]
        )
    if 1 not in poses:
        raise ValueError("Trajectory must include first posed frame ID 1")
    return poses


def load_frame(root: Path, frame_id: int) -> Frame:
    select_ids([frame_id])
    conventions = json.loads((root / "conventions.json").read_text(encoding="utf-8"))
    fields = {
        key: conventions["calibration"][key]
        for key in ("width", "height", "fx", "fy", "cx", "cy")
    }
    k = Calibration(**fields, axes="x-right_y-up_z-forward")
    poses = read_poses(root / "trajectory2/livingRoom2.gt.freiburg")
    if frame_id not in poses:
        raise ValueError(f"No exact pose for frame ID {frame_id}")
    rgb_path, depth_path = (
        root / f"trajectory2/{kind}/{frame_id}.png" for kind in ("rgb", "depth")
    )
    with Image.open(rgb_path) as image:
        rgb = np.array(image.convert("RGB"))
    with Image.open(depth_path) as image:
        raw_depth = np.array(image)
    if rgb.shape != (k.height, k.width, 3) or raw_depth.shape != (k.height, k.width):
        raise ValueError("Stored image resolution disagrees with calibration")
    if raw_depth.dtype != np.uint16:
        raise ValueError("Clean ICL depth must be uint16 PNG")
    model_from_first = np.array(
        conventions["alignment"]["S_model_first_camera"], dtype=float
    )
    validate_transform(model_from_first, basis=True)
    observation = Observation(
        str(frame_id),
        "icl_camera",
        None,
        "frame_index_only",
        k,
        Pose(poses[frame_id], "icl_compatible_world", "trajectory2", "supplied"),
    )
    for array in (rgb, raw_depth, model_from_first):
        array.setflags(write=False)
    return Frame(
        observation, rgb, raw_depth, rgb_path, depth_path, model_from_first, poses[1]
    )
