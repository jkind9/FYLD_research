"""CPU display geometry, explicit provenance roles and offline inspection."""

import html
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

from .runs import write_json

ROLES = {
    "observed_input": "Observed input",
    "ground_truth": "Ground truth",
    "predicted_output": "Predicted output",
    "evaluated_output": "Evaluated output",
}


def artifact(
    path: str,
    role: str,
    producer: str,
    sources: list[str],
    units: str,
    conversion: str = "unchanged",
) -> dict:
    if role not in ROLES or not producer or not path:
        raise ValueError("Artifact requires a known role, path and producer")
    return {
        "path": path,
        "role": role,
        "label": ROLES[role],
        "producer": producer,
        "sources": sources,
        "units": units,
        "display_conversion": conversion,
    }


def sample_points(points: np.ndarray, colours: np.ndarray, cap: int) -> dict:
    points, colours = np.asarray(points), np.asarray(colours)
    if (
        points.ndim != 2
        or points.shape[1] != 3
        or colours.shape != points.shape
        or not np.isfinite(points).all()
        or not np.isfinite(colours).all()
        or isinstance(cap, bool)
        or not isinstance(cap, int)
        or cap < 1
    ):
        raise ValueError("Display needs finite paired XYZ/RGB and positive cap")
    indices = np.linspace(0, len(points) - 1, min(cap, len(points)), dtype=int)
    return {
        "points": points[indices].tolist(),
        "colours": colours[indices].tolist(),
        "full_count": len(points),
        "display_count": len(indices),
    }


def frustum(calibration: dict, matrix: np.ndarray, size: float = 0.15) -> list:
    matrix = np.asarray(matrix, dtype=float)
    if not all(
        np.isfinite(calibration[k]) for k in ("width", "height", "fx", "fy", "cx", "cy")
    ):
        raise ValueError("Display calibration must be finite")
    if any(
        calibration[k] < 1 or calibration[k] != int(calibration[k])
        for k in ("width", "height")
    ):
        raise ValueError("Display dimensions must be positive integers")
    if (
        matrix.shape != (4, 4)
        or not np.isfinite(matrix).all()
        or not np.allclose(matrix[3], [0, 0, 0, 1])
        or not np.isfinite(size)
        or size <= 0
        or calibration["fx"] <= 0
        or calibration["fy"] == 0
    ):
        raise ValueError("Invalid display camera basis or calibration")
    corners = [
        (0, 0),
        (calibration["width"] - 1, 0),
        (calibration["width"] - 1, calibration["height"] - 1),
        (0, calibration["height"] - 1),
    ]
    rays = [[0.0, 0.0, 0.0]] + [
        [
            (u - calibration["cx"]) * size / calibration["fx"],
            (v - calibration["cy"]) * size / calibration["fy"],
            size,
        ]
        for u, v in corners
    ]
    vertices = np.column_stack([rays, np.ones(5)]) @ matrix.T
    return vertices[:, :3].tolist()


def depth_preview(
    depth: np.ndarray, destination: Path, role: str, source: str, maximum: float = 4.0
) -> dict:
    depth = np.asarray(depth, dtype=float)
    if depth.ndim != 2 or not np.isfinite(maximum) or maximum <= 0:
        raise ValueError("Depth preview requires 2D depth and positive scale")
    valid = np.isfinite(depth) & (depth > 0)
    normalized = np.clip(np.where(valid, depth, 0) / maximum, 0, 1)
    # Blue near, yellow far; black exclusively denotes missing measurement.
    colour = np.stack([normalized, np.sqrt(normalized), 1 - normalized], axis=-1)
    colour = np.where(valid[..., None], colour, 0)
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.rint(colour * 255).astype(np.uint8)).save(destination)
    mask = destination.with_name(destination.stem + "_valid.png")
    Image.fromarray(valid.astype(np.uint8) * 255).save(mask)
    result = {
        **artifact(
            destination.name,
            role,
            "CPU depth preview",
            [source],
            "metres",
            "supplied metre array to colours; blue near to yellow far; no smoothing",
        ),
        "minimum": 0,
        "maximum": maximum,
        "missing_pixels": int((~valid).sum()),
        "total_pixels": int(valid.size),
        "missing_fraction": float((~valid).mean()),
        "valid_mask": mask.name,
        "black": "missing measurement",
    }
    write_json(destination.with_suffix(".json"), result)
    return result


def render_viewer(scene: dict) -> str:
    """Render inline scene and drawing assets without writing run artifacts."""
    payload = (
        json.dumps(scene, allow_nan=False)
        .replace("<", "\\u003c")
        .replace("&", "\\u0026")
    )
    template = Path(__file__).with_name("viewer.html").read_text(encoding="utf-8")
    replacements = {
        "__TITLE__": html.escape(scene["title"]),
        "__SCENE__": payload,
        "__SCRIPT__": Path(__file__).with_name("viewer.js").read_text(encoding="utf-8"),
    }
    return re.sub(
        r"__(?:TITLE|SCENE|SCRIPT)__", lambda match: replacements[match[0]], template
    )


def write_viewer(root: Path, scene: dict) -> None:
    page = render_viewer(scene)
    write_json(root / "debug/scene.json", scene)
    (root / "viewer.html").write_text(page, encoding="utf-8")
    import shutil

    from experiments.datasets.acquisition import sha256

    sources = {}
    for name in ("viewer.html", "viewer.js"):
        source = Path(__file__).with_name(name)
        target = root / "metadata/viewer_source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        sources[name] = sha256(target)
    write_json(root / "metadata/viewer_source.json", {"files": sources})
