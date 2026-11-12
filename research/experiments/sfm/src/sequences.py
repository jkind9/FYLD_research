"""Recorded image sequences with their camera model and ground-truth reader."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# Flips a camera's y axis; F @ T @ F turns ICL's y-up camera and mirrored world into a
# right-handed pose with y down, the convention COLMAP and the rest of the project use.
FLIP_Y = np.diag([1.0, -1.0, 1.0, 1.0])

# Published TUM fr1 RGB calibration (cvg.cit.tum.de file formats page, checked 2026-10-13).
TUM_FR1_FULL_OPENCV = (517.3, 516.5, 318.6, 255.3, 0.2624, -0.9531, -0.0054, 0.0026, 1.1633, 0.0, 0.0, 0.0)
# The TUM page's recommended default set, used by experiment 03 (dataset.py:13).
TUM_DEFAULT_PINHOLE = (525.0, 525.0, 319.5, 239.5)
# data/icl_nuim/conventions.json; fy is published as -480 (y-up camera), see FLIP_Y.
ICL_PINHOLE = (481.2, 480.0, 319.5, 239.5)


@dataclass(frozen=True)
class Sequence:
    name: str
    image_root: Path
    image_names: tuple[str, ...]
    frame_ids: tuple[str, ...]
    timestamps_s: tuple[float, ...]
    camera_model: str
    camera_params: tuple[float, ...]
    groundtruth: Path
    flip_reference: bool = False
    depth_names: tuple[str | None, ...] = field(default=())

    def __post_init__(self) -> None:
        count = len(self.image_names)
        if count == 0 or not (count == len(self.frame_ids) == len(self.timestamps_s)):
            raise ValueError("Sequence needs matching non-empty image, frame and time lists")
        if self.depth_names and len(self.depth_names) != count:
            raise ValueError("Depth list must match the image list")
        if len(set(self.frame_ids)) != count or any(b <= a for a, b in zip(self.timestamps_s, self.timestamps_s[1:])):
            raise ValueError("Frame IDs must be unique and times increasing")

    def references(self) -> list[tuple[float, np.ndarray]]:
        """Ground-truth camera-to-world poses as (time, 4x4); ICL is converted to y-down."""
        rows = []
        for line in self.groundtruth.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            values = np.array([float(v) for v in line.split()])
            if values.shape != (8,):
                raise ValueError("Ground-truth rows need eight values")
            rows.append(values)
        from experiments.shared.geometry import pose_matrix

        out = []
        for values in rows:
            quaternion = values[4:] / np.linalg.norm(values[4:])
            matrix = pose_matrix(values[1:4], quaternion)
            out.append((float(values[0]), FLIP_Y @ matrix @ FLIP_Y if self.flip_reference else matrix))
        return out

    def manifest(self) -> dict:
        """Image list with hashes, so a run records exactly what it read."""
        return {
            "name": self.name,
            "image_root": str(self.image_root),
            "camera_model": self.camera_model,
            "camera_params": list(self.camera_params),
            "groundtruth": str(self.groundtruth),
            "flip_reference": self.flip_reference,
            "frames": [
                {"frame_id": f, "timestamp_s": t, "image": n,
                 "sha256": hashlib.sha256((self.image_root / n).read_bytes()).hexdigest()}
                for f, t, n in zip(self.frame_ids, self.timestamps_s, self.image_names)
            ],
        }


def _rows(path: Path) -> list[list[str]]:
    return [line.split() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def _depth_for(root: Path, times: list[float], tolerance_s: float = 0.02) -> list[str | None]:
    depth_file = root / "depth.txt"
    if not depth_file.is_file():
        return [None] * len(times)
    rows = [(float(r[0]), r[1]) for r in _rows(depth_file)]
    depth_times = np.array([t for t, _ in rows])
    out = []
    for t in times:
        i = int(np.argmin(np.abs(depth_times - t)))
        out.append(rows[i][1] if abs(depth_times[i] - t) <= tolerance_s else None)
    return out


def tum(root: Path, *, every: int = 1, calibration: str = "default") -> Sequence:
    """A TUM recording or Task65 clip folder with rgb.txt and groundtruth.txt."""
    root = Path(root)
    rows = _rows(root / "rgb.txt")[::every]
    times = [float(r[0]) for r in rows]
    names = [r[1] for r in rows]
    if calibration == "fr1":
        model, params = "FULL_OPENCV", TUM_FR1_FULL_OPENCV
    elif calibration == "default":
        model, params = "PINHOLE", TUM_DEFAULT_PINHOLE
    else:
        raise ValueError("TUM calibration must be 'fr1' or 'default'")
    return Sequence(root.name + (f"_every{every}" if every > 1 else ""), root, tuple(names), tuple(names),
                    tuple(times), model, params, root / "groundtruth.txt", False, tuple(_depth_for(root, times)))


def icl(root: Path, *, every: int = 1) -> Sequence:
    """ICL-NUIM trajectory folder; frame number is the time, image 0 has no pose and is skipped."""
    root = Path(root)
    rows = [r for r in _rows(root / "associations.txt") if int(r[0]) >= 1][::every]
    groundtruth = next(root.glob("*.gt.freiburg"))
    # associations.txt columns: frame, depth image, frame, colour image.
    return Sequence(root.name + (f"_every{every}" if every > 1 else ""), root, tuple(r[3] for r in rows),
                    tuple(r[0] for r in rows), tuple(float(r[0]) for r in rows), "PINHOLE", ICL_PINHOLE,
                    groundtruth, True, tuple(r[1] for r in rows))


def load(spec: str, *, every: int = 1, calibration: str = "default") -> Sequence:
    """`tum:<folder>` or `icl:<folder>`."""
    kind, _, folder = spec.partition(":")
    if kind == "tum":
        return tum(Path(folder), every=every, calibration=calibration)
    if kind == "icl":
        return icl(Path(folder), every=every)
    raise ValueError("Recording must be tum:<folder> or icl:<folder>")
