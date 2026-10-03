"""Explicit CPU Open3D adapter; transforms map source camera into target."""

import ast
import importlib.util
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from experiments.shared.geometry import validate_transform

from .dataset import RGBDFrame


@dataclass(frozen=True)
class PairResult:
    success: bool
    transform: NDArray | None
    reason: str


def cpu_build() -> dict:
    spec = importlib.util.find_spec("open3d")
    if spec is None or spec.origin is None:
        raise ImportError("Install the pinned Open3D CPU wheel")
    tree = ast.parse(Path(spec.origin).with_name("_build_config.py").read_text())
    assignments = [n for n in tree.body if isinstance(n, ast.Assign)]
    config = next(
        ast.literal_eval(n.value)
        for n in assignments
        if any(isinstance(t, ast.Name) and t.id == "_build_config" for t in n.targets)
    )
    if config.get("BUILD_CUDA_MODULE", True) or config.get("BUILD_SYCL_MODULE", True):
        raise RuntimeError(
            "Refusing GPU-capable Open3D initialization without permission"
        )
    return config


class CPUOdometry:
    def __init__(self) -> None:
        self.build = cpu_build()
        import open3d as o3d

        if o3d.__version__ != "0.19.0" or not o3d.geometry.Image.__module__.startswith(
            "open3d.cpu."
        ):
            raise RuntimeError("Expected Open3D 0.19.0 CPU backend")
        self.o3d = o3d

    def _image(self, frame: RGBDFrame):
        o3d = self.o3d
        depth = np.where(frame.valid, frame.depth, 0).astype(np.float32)
        return o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d.geometry.Image(np.array(frame.colour, copy=True)),
            o3d.geometry.Image(depth),
            depth_scale=1.0,
            depth_trunc=4.0,
            convert_rgb_to_intensity=True,
        )

    def estimate(self, source: RGBDFrame, target: RGBDFrame) -> PairResult:
        if source.calibration != target.calibration:
            raise ValueError("Pair calibration differs")
        if not source.valid.any() or not target.valid.any():
            return PairResult(False, None, "no valid depth")
        c, o3d = source.calibration, self.o3d
        intrinsic = o3d.camera.PinholeCameraIntrinsic(
            c.width, c.height, c.fx, c.fy, c.cx, c.cy
        )
        option = o3d.pipelines.odometry.OdometryOption()
        option.iteration_number_per_pyramid_level = o3d.utility.IntVector([20, 10, 5])
        option.depth_diff_max, option.depth_min, option.depth_max = 0.03, 0.0, 4.0
        source_image, target_image = self._image(source), self._image(target)
        if not np.any(np.asarray(source_image.depth) > 0) or not np.any(
            np.asarray(target_image.depth) > 0
        ):
            return PairResult(False, None, "no usable converted depth")
        success, transform, information = o3d.pipelines.odometry.compute_rgbd_odometry(
            source_image,
            target_image,
            intrinsic,
            np.eye(4),
            o3d.pipelines.odometry.RGBDOdometryJacobianFromHybridTerm(),
            option,
        )
        if not success or not np.isfinite(information).all():
            return PairResult(False, None, "backend failure or nonfinite information")
        try:
            validate_transform(transform)
        except ValueError:
            return PairResult(False, None, "invalid backend transform")
        return PairResult(True, np.array(transform, copy=True), "success")
