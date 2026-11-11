"""Metric Video Depth Anything Small: depth for a whole clip at once, trained to stay consistent.

Single-image depth models guess each frame's size separately, so the size jumps from frame to
frame. Video Depth Anything (Chen et al., CVPR 2025, arXiv 2501.12375) looks at 32 frames at a
time with a temporal attention head, so neighbouring frames should agree. The Small metric
model (28.4M parameters, Apache-2.0 code and weights) outputs metres; it was trained on
synthetic driving (Virtual KITTI) and indoor (IRS) scenes, so its indoor scale is untested here.

Its code is not a package: clone https://github.com/DepthAnything/Video-Depth-Anything and put
that folder on PYTHONPATH. The adapter never downloads anything.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np

from experiments.shared.runs import Run

from ..records import Unavailable
from .contracts import ColourFrame, DepthEstimator, DepthPrediction

# Upstream run.py:45-46 settings for the Small ('vits') encoder.
SMALL_SETTINGS = {"encoder": "vits", "features": 64, "out_channels": [48, 96, 192, 384]}


@dataclass(frozen=True)
class MetricVideoDepthAnything:
    """Run the whole clip through the model once, then return one metric depth map per frame.

    `input_size` 518 is upstream's default (run.py:26). Upstream runs half precision by
    default; on the CPU this adapter runs full precision (`fp32`).
    """

    checkpoint: Path
    device: str = "cpu"
    input_size: int = 518
    fp32: bool = True
    max_depth_m: float = 20.0  # same cap as DepthAnythingV2Metric
    name: str = field(default="metric_video_depth_anything_small", init=False)
    control: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.device not in {"cpu", "cuda"}:
            raise ValueError("Video Depth Anything device must be cpu or cuda")

    def load(self) -> DepthEstimator:
        if not self.checkpoint.is_file():
            raise FileNotFoundError(f"Video Depth Anything checkpoint not found: {self.checkpoint}")
        try:
            from video_depth_anything.video_depth import VideoDepthAnything
        except ImportError as error:
            raise Unavailable(
                "Video Depth Anything code is not importable; add data/models/Video-Depth-Anything to PYTHONPATH"
            ) from error
        model = VideoDepthAnything(**SMALL_SETTINGS, metric=True)
        model.load_state_dict(_load_weights(self.checkpoint), strict=True)
        model = model.to(self.device).eval()
        return partial(_predict_video_depth, model=model, settings=self)


def _load_weights(path: Path) -> Any:
    import torch

    return torch.load(path, map_location="cpu", weights_only=True)


def _predict_video_depth(
    frames: Iterator[ColourFrame], *, run: Run, model: Any, settings: MetricVideoDepthAnything
) -> Iterator[DepthPrediction]:
    """All frames are read first, because the model works on 32-frame windows."""
    del run  # timing is measured by the depth layer
    colour_frames = list(frames)
    if not colour_frames:
        return
    stacked = np.stack([frame.colour for frame in colour_frames])
    depths, _ = model.infer_video_depth(
        stacked, target_fps=None, input_size=settings.input_size, device=settings.device, fp32=settings.fp32
    )
    for frame, depth in zip(colour_frames, depths, strict=True):
        depth = np.asarray(depth, dtype=np.float64)
        valid = np.isfinite(depth) & (depth > 0) & (depth <= settings.max_depth_m)
        yield DepthPrediction(frame.frame_id, np.where(valid, depth, np.nan), valid)
