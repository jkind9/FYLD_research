"""Learned camera-plane depth from RGB arrays."""

from collections.abc import Callable
from functools import partial
from pathlib import Path

import numpy as np
from PIL import Image

from .orientation import quarter_turns, recorded, upright

MAX_DEPTH_M = 20.0
THREADS = 16


def metres(encoded, units_per_metre: float) -> tuple[np.ndarray, np.ndarray]:
    """Float64 camera-plane metres and a mask of finite, positive pixels."""
    depth = np.asarray(encoded, dtype=np.float64) / units_per_metre
    valid = np.isfinite(depth) & (depth > 0)
    return np.where(valid, depth, np.nan), valid


def infer(
    image: np.ndarray, *, processor, model, torch, device: str, max_depth_m: float = MAX_DEPTH_M
) -> tuple[np.ndarray, np.ndarray]:
    """Depth and validity on the RGB image's pixel grid from loaded model components."""
    inputs = processor(images=Image.fromarray(image, mode="RGB"), return_tensors="pt")
    inputs = {name: tensor.to(device) for name, tensor in inputs.items()}
    with torch.inference_mode():
        prediction = model(**inputs).predicted_depth
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=image.shape[:2],
            mode="bicubic",
            align_corners=False,
        )[0, 0]
    depth, valid = metres(prediction.detach().cpu().numpy(), units_per_metre=1)
    valid &= depth <= max_depth_m
    return np.where(valid, depth, np.nan), valid


def load_model(
    checkpoint: Path | str,
    *,
    threads: int | None = THREADS,
    device: str = "cpu",
    max_depth_m: float = MAX_DEPTH_M,
) -> Callable:
    """An RGB-to-depth callable, loading local processor and weights once."""
    checkpoint = Path(checkpoint)
    if not checkpoint.is_dir():
        raise FileNotFoundError(f"Local model checkpoint directory not found: {checkpoint}")
    import torch
    from transformers import AutoImageProcessor, AutoModelForDepthEstimation

    if threads is not None:
        torch.set_num_threads(threads)
    processor = AutoImageProcessor.from_pretrained(checkpoint, local_files_only=True)
    model = AutoModelForDepthEstimation.from_pretrained(checkpoint, local_files_only=True)
    model = model.to(device).eval()
    return partial(
        infer, processor=processor, model=model, torch=torch, device=device, max_depth_m=max_depth_m
    )


def predict(
    model: Callable, image: np.ndarray, pose: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Depth and validity on the recorded grid, using upright input when pose is given."""
    turns = 0 if pose is None else quarter_turns(pose)
    depth, valid = model(np.ascontiguousarray(upright(image, turns)))
    return recorded(depth, turns), recorded(valid, turns)
