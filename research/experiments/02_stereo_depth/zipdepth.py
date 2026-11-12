"""Local-checkpoint ZipDepth adapter for RGB frame streams."""

import importlib
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from experiments.shared.runs import Run

Build = Literal["gpu", "npu"]
ZipDepthConvention = Literal["relative_inverse_depth"]


@dataclass(frozen=True)
class ZipDepthPrediction:
    """Native ZipDepth inverse-depth output, kept before reference alignment."""

    frame_id: str
    depth: NDArray[np.float32]
    valid: NDArray[np.bool_]
    convention: ZipDepthConvention = "relative_inverse_depth"


@dataclass(frozen=True)
class ZipDepth:
    """Use the official predictor with a local GPU or mobile/NPU checkpoint."""

    checkpoint: Path
    build: Build = "gpu"
    device: str = "cuda"
    input_size: int = 384
    name: str = field(init=False)
    output_convention: ZipDepthConvention = field(
        default="relative_inverse_depth", init=False
    )

    def __post_init__(self) -> None:
        if self.build not in ("gpu", "npu"):
            raise ValueError("ZipDepth build must be gpu or npu")
        if self.device not in ("cpu", "cuda"):
            raise ValueError("ZipDepth device must be cpu or cuda")
        if type(self.input_size) is not int or self.input_size < 32:
            raise ValueError("ZipDepth input_size must be an integer of at least 32")
        object.__setattr__(self, "checkpoint", Path(self.checkpoint))
        object.__setattr__(self, "name", f"zipdepth_base_{self.build}")

    def load(self) -> Any:
        """Load only an existing local checkpoint through the official API."""
        if not self.checkpoint.is_file():
            raise FileNotFoundError(
                f"Local ZipDepth checkpoint file not found: {self.checkpoint}"
            )

        predictor_module = importlib.import_module("zipdepth.inference.predictor")
        predictor = predictor_module.DepthInference(
            checkpoint_path=str(self.checkpoint),
            variant="base",
            device=self.device,
            input_size=self.input_size,
            upsample_unfold=self.build == "gpu",
            use_compile=False,
        )
        return partial(_predict_zipdepth, predictor=predictor)


def _predict_zipdepth(
    frames: Iterator[Any],
    *,
    predictor: Any,
    run: Run,
) -> Iterator[ZipDepthPrediction]:
    """Predict relative inverse depth without access to reference depth."""
    del run  # The owning runner measures per-frame elapsed time.
    for frame in frames:
        colour = np.asarray(frame.colour)
        if colour.ndim != 3 or colour.shape[2] != 3 or colour.dtype != np.uint8:
            raise ValueError(f"{frame.frame_id}: expected an RGB uint8 image")

        # The official infer_image() contract accepts OpenCV-order BGR arrays.
        image_bgr = np.ascontiguousarray(colour[..., ::-1])
        raw_depth = np.asarray(predictor.infer_image(image_bgr), dtype=np.float32)
        if raw_depth.ndim != 2 or raw_depth.shape != colour.shape[:2]:
            raise ValueError(
                f"{frame.frame_id}: ZipDepth output grid must match the input image"
            )
        valid = np.isfinite(raw_depth)
        depth = np.where(valid, raw_depth, np.nan).astype(np.float32, copy=False)
        yield ZipDepthPrediction(frame.frame_id, depth, valid)
