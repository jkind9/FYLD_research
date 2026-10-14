"""Reference surfaces in the same right-handed world as the sequence's true poses."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import numpy as np

from .sequences import FLIP_Y

surface_dataset = importlib.import_module("experiments.04_surface_reconstruction.src.dataset")


def icl_model_to_world(conventions: Path) -> np.ndarray:
    """4x4 taking ICL model-frame points into the y-flipped pose world used by `sequences.icl`.

    The publisher gives model-from-compatible-world (determinant -1, a mirror); the pose
    world is then mirrored once more by FLIP_Y, so the product is a proper transform.
    """
    record = json.loads(Path(conventions).read_text(encoding="utf-8"))
    model_from_world = np.array(record["alignment"]["derived_model_from_compatible_world"], dtype=np.float64)
    return FLIP_Y @ np.linalg.inv(model_from_world)


def icl_reference(icl_root: Path) -> np.ndarray:
    """ICL living-room model points (N x 3, metres) in the flipped pose world."""
    root = Path(icl_root)
    points = surface_dataset.read_reference(root / "reference_surface/living-room.ply")
    transform = icl_model_to_world(root / "conventions.json")
    return points @ transform[:3, :3].T + transform[:3, 3]
