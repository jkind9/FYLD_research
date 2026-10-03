"""Lossless numeric artifacts with full-resolution review images."""

from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from PIL import Image

from experiments.shared.runs import write_json


def _raster(path: Path, values: np.ndarray, units: str) -> dict:
    valid = np.isfinite(values)
    low = float(values[valid].min()) if valid.any() else None
    high = float(values[valid].max()) if valid.any() else None
    gray = np.zeros(values.shape, dtype=np.uint8)
    if low is not None and high is not None:
        scaled = np.ones(values.shape) if high == low else (values - low) / (high - low)
        gray[valid] = (1 + np.clip(scaled[valid], 0, 1) * 254).astype(np.uint8)
    Image.fromarray(gray).save(path)
    return {
        "units": units,
        "minimum": low,
        "maximum": high,
        "encoding": "black invalid; grayscale 1 minimum to 255 maximum",
    }


def _ply(path: Path, points: np.ndarray, colors: np.ndarray) -> None:
    with path.open("x", encoding="ascii", newline="\n") as stream:
        stream.write("ply\nformat ascii 1.0\n" + f"element vertex {len(points)}\n")
        stream.write("property double x\nproperty double y\nproperty double z\n")
        stream.write(
            "property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n"
        )
        for point, color in zip(points, colors, strict=True):
            stream.write(
                " ".join(
                    [
                        *(format(float(v), ".17g") for v in point),
                        *(str(int(v)) for v in color),
                    ]
                )
                + "\n"
            )


def _cloud_preview(path: Path, points: np.ndarray, colors: np.ndarray) -> None:
    """Render every cloud point on CPU with labeled, equally scaled axes."""
    figure = Figure(figsize=(7, 6), dpi=120)
    FigureCanvasAgg(figure)
    axes = figure.add_subplot(projection="3d")
    axes.scatter(
        points[:, 0],
        points[:, 1],
        points[:, 2],
        c=colors.astype(float) / 255,
        s=1,
        depthshade=False,
    )
    axes.set(
        xlabel="X (metres)",
        ylabel="Y (metres)",
        zlabel="Z (metres)",
        title=path.stem.replace("_", " "),
    )
    if len(points):
        lower, upper = points.min(axis=0), points.max(axis=0)
        center = (lower + upper) / 2
        radius = max(float((upper - lower).max()) / 2, 1e-6)
        axes.set_xlim(center[0] - radius, center[0] + radius)
        axes.set_ylim(center[1] - radius, center[1] + radius)
        axes.set_zlim(center[2] - radius, center[2] + radius)
    else:
        axes.text2D(0.4, 0.5, "No valid points", transform=axes.transAxes)
    axes.set_box_aspect((1, 1, 1))
    figure.savefig(path)
    figure.clear()


def _validate(
    depth: np.ndarray,
    mask: np.ndarray,
    pixels: np.ndarray,
    camera: np.ndarray,
    world: np.ndarray,
    model: np.ndarray,
    rgb: np.ndarray,
    projection_error: np.ndarray,
) -> None:
    if depth.ndim != 2 or mask.shape != depth.shape or mask.dtype != bool:
        raise ValueError("Depth must be HxW and mask must be a matching boolean array")
    if pixels.shape != (int(mask.sum()), 2) or not np.issubdtype(
        pixels.dtype, np.integer
    ):
        raise ValueError("Pixels must be integer Nx2 in mask order")
    expected = np.column_stack(np.nonzero(mask))
    if not np.array_equal(pixels, expected):
        raise ValueError("Pixels must match mask in row-major (v, u) order")
    for points in (camera, world, model):
        if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
            raise ValueError("Clouds must be finite Nx3")
    if camera.shape != world.shape or len(camera) != len(pixels):
        raise ValueError("Camera/world clouds must preserve valid pixel correspondence")
    if len(model) != len(pixels):
        raise ValueError("Model coordinates must preserve valid pixel correspondence")
    if rgb.shape != (*depth.shape, 3) or rgb.dtype != np.uint8:
        raise ValueError("RGB must be HxWx3 uint8")
    if (
        projection_error.shape not in {(len(pixels),), (len(pixels), 2)}
        or not np.isfinite(projection_error).all()
    ):
        raise ValueError(
            "Projection errors must be finite N values or Nx2 pixel deltas"
        )
    if not np.isfinite(depth[mask]).all():
        raise ValueError("Valid depth pixels must be finite")


def export_frame(
    output: Path,
    debug: Path,
    depth: np.ndarray,
    mask: np.ndarray,
    pixels: np.ndarray,
    camera: np.ndarray,
    world: np.ndarray,
    model: np.ndarray,
    rgb: np.ndarray,
    projection_error: np.ndarray,
) -> dict:
    """Export a single frame; clouds are metres and pixels use (v, u)."""
    _validate(depth, mask, pixels, camera, world, model, rgb, projection_error)
    output.mkdir(parents=True, exist_ok=True)
    debug.mkdir(parents=True, exist_ok=True)
    arrays = {
        "depth": depth,
        "mask": mask,
        "pixels": pixels,
        "camera": camera,
        "world": world,
        "model": model,
        "rgb": rgb,
        "projection_error": projection_error,
    }
    for name, values in arrays.items():
        with (output / f"{name}.npy").open("xb") as stream:
            np.save(stream, values, allow_pickle=False)
    legends = {"depth.png": _raster(debug / "depth.png", depth, "metres")}
    Image.fromarray(mask.astype(np.uint8) * 255).save(debug / "mask.png")
    Image.fromarray(rgb).save(debug / "rgb.png")
    colors = rgb[pixels[:, 0], pixels[:, 1]]
    for name, points in (("camera", camera), ("world", world), ("model", model)):
        _ply(output / f"{name}.ply", points, colors)
        _cloud_preview(debug / f"{name}_cloud.png", points, colors)
        for axis, channel in enumerate("xyz"):
            raster = np.full(depth.shape, np.nan)
            raster[pixels[:, 0], pixels[:, 1]] = points[:, axis]
            filename = f"{name}_{channel}.png"
            legends[filename] = _raster(debug / filename, raster, "metres")
    error = np.full(depth.shape, np.nan)
    magnitudes = (
        np.linalg.norm(projection_error, axis=1)
        if projection_error.ndim == 2
        else projection_error
    )
    error[pixels[:, 0], pixels[:, 1]] = magnitudes
    legends["projection_error.png"] = _raster(
        debug / "projection_error.png", error, "pixels"
    )
    legends["mask.png"] = {"encoding": "black invalid; white valid"}
    write_json(debug / "legends.json", legends)
    return {
        "arrays": [f"{name}.npy" for name in arrays],
        "clouds": ["camera.ply", "world.ply", "model.ply"],
        "visualizations": [
            "rgb.png",
            "camera_cloud.png",
            "world_cloud.png",
            "model_cloud.png",
            *legends.keys(),
        ],
        "legend": "legends.json",
    }
