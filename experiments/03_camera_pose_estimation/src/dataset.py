"""Pose-free, bounded TUM RGB/depth input reader."""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from experiments.shared.contracts import Calibration
from experiments.shared.geometry import associate_times, depth_metres

CALIBRATION = Calibration(640, 480, 525, 525, 319.5, 239.5, "x-right_y-down_z-forward")


@dataclass(frozen=True)
class RGBDFrame:
    frame_id: str
    timestamp_s: float
    depth_timestamp_s: float
    calibration: Calibration
    colour: NDArray
    depth: NDArray
    valid: NDArray

    def __post_init__(self) -> None:
        shape = (self.calibration.height, self.calibration.width)
        if (
            not self.frame_id
            or not np.isfinite([self.timestamp_s, self.depth_timestamp_s]).all()
        ):
            raise ValueError("Frame identifiers and finite timestamps required")
        if self.colour.shape != (*shape, 3) or self.colour.dtype != np.uint8:
            raise ValueError("Expected calibrated uint8 RGB image")
        if (
            self.depth.shape != shape
            or self.valid.shape != shape
            or self.valid.dtype != np.bool_
        ):
            raise ValueError("Expected calibrated depth and boolean mask")
        if np.any(
            self.valid
            & (~np.isfinite(self.depth) | (self.depth <= 0) | (self.depth >= 4))
        ):
            raise ValueError("Valid mask admits out-of-range depth")
        for name in ("colour", "depth", "valid"):
            values = np.array(getattr(self, name), copy=True)
            values.setflags(write=False)
            object.__setattr__(self, name, values)


def read_table(path: Path) -> list[tuple[float, str]]:
    rows: list[tuple[float, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        columns = line.split()
        if len(columns) != 2:
            raise ValueError("Timestamp tables require exactly two columns")
        timestamp, relative = float(columns[0]), columns[1]
        posix, windows = PurePosixPath(relative), PureWindowsPath(relative)
        if (
            not np.isfinite(timestamp)
            or posix.is_absolute()
            or windows.drive
            or "\\" in relative
            or any(part in {".", ".."} for part in posix.parts)
        ):
            raise ValueError("Invalid timestamp or unsafe observation path")
        if rows and timestamp <= rows[-1][0]:
            raise ValueError("Timestamps must be strictly increasing")
        rows.append((timestamp, relative))
    if not rows:
        raise ValueError("Empty observation table")
    return rows


def associations(
    root: Path, count: int, tolerance: float = 0.02
) -> tuple[list[dict], dict]:
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("Frame count must be positive integer")
    colour, depth = read_table(root / "rgb.txt"), read_table(root / "depth.txt")
    pairs = associate_times([r[0] for r in colour], [r[0] for r in depth], tolerance)
    if len(pairs) < count:
        raise ValueError("Insufficient associated frames")
    if any(
        depth[pairs[i][1]][0] <= depth[pairs[i - 1][1]][0] for i in range(1, len(pairs))
    ):
        raise ValueError("Timestamp association crossed depth order")
    rows = [
        {
            "frame_id": str(i),
            "timestamp_s": colour[a][0],
            "depth_timestamp_s": depth[b][0],
            "rgb": colour[a][1],
            "depth": depth[b][1],
        }
        for i, (a, b) in enumerate(pairs[:count])
    ]
    return rows, {
        "rgb_rows": len(colour),
        "depth_rows": len(depth),
        "matched_rows": len(pairs),
        "unmatched_rgb": len(colour) - len(pairs),
        "unmatched_depth": len(depth) - len(pairs),
    }


def load_frame(root: Path, row: dict) -> RGBDFrame:
    for key in ("rgb", "depth"):
        path = root / row[key]
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Observation escapes dataset")
    with Image.open(root / row["rgb"]) as image:
        if image.format != "PNG" or image.mode != "RGB":
            raise ValueError("Expected RGB PNG")
        colour = np.asarray(image)
    with Image.open(root / row["depth"]) as image:
        encoded = np.asarray(image)
        if image.format != "PNG" or encoded.dtype != np.uint16:
            raise ValueError("Expected uint16 depth PNG")
    depth, valid = depth_metres(encoded, 5000)
    valid = valid & (depth < 4)
    return RGBDFrame(
        row["frame_id"],
        row["timestamp_s"],
        row["depth_timestamp_s"],
        CALIBRATION,
        colour,
        depth,
        valid,
    )
