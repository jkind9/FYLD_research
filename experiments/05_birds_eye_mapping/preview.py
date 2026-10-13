"""Draw one footprint as a top-down picture: height colours, unseen cells grey."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

UNSEEN_GREY = (150, 150, 150)
BELOW_PLANE = (90, 40, 120)  # purple: the cell's highest point is under the plane
# Same as the walkthrough's plane band: tops within 2 cm below still count as on the plane.
BELOW_TOLERANCE_M = 0.02
MAX_IMAGE_SIDE_PX = 900


def footprint_preview(
    observed: np.ndarray, max_height_m: np.ndarray, cell_size_m: float, destination: Path
) -> dict[str, float | int]:
    """Save a PNG of one saved footprint grid and return the scale it was drawn with.

    Colour runs from blue at the plane (0 m) to yellow at the origin's highest cell.
    Purple cells have their highest point more than BELOW_TOLERANCE_M under the plane
    (for example floor seen beside a desk-top plane). Grey cells were never seen.
    The first grid axis runs down the image.
    """
    heights = np.asarray(max_height_m, dtype=float)
    observed = np.asarray(observed, dtype=bool)
    top_m = max(float(np.nanmax(heights)) if observed.any() else 0.0, 1e-6)
    length_m, width_m = heights.shape[0] * cell_size_m, heights.shape[1] * cell_size_m
    fraction = np.clip(np.nan_to_num(heights, nan=0.0) / top_m, 0.0, 1.0)
    colour = np.stack([fraction, np.sqrt(fraction), 1.0 - fraction], axis=-1) * 255
    colour[observed & (np.nan_to_num(heights, nan=0.0) < -BELOW_TOLERANCE_M)] = BELOW_PLANE
    colour[~observed] = UNSEEN_GREY
    image = Image.fromarray(np.rint(colour).astype(np.uint8))

    pixels_per_cell = max(1, MAX_IMAGE_SIDE_PX // max(heights.shape))
    image = image.resize(
        (heights.shape[1] * pixels_per_cell, heights.shape[0] * pixels_per_cell),
        Image.Resampling.NEAREST,
    )
    caption_lines = (
        (
            f"Top-down map: {length_m:.2f} m down x {width_m:.2f} m across; "
            f"cell {cell_size_m * 100:g} cm ({pixels_per_cell} px)"
        ),
        f"Colour: blue 0 m to yellow {top_m:.2f} m above the plane; purple = below it; grey = never seen",
    )
    font = ImageFont.load_default()
    canvas = Image.new("RGB", (max(image.width, 460), image.height + 34), (24, 34, 45))
    canvas.paste(image, (0, 0))
    draw = ImageDraw.Draw(canvas)
    for line_index, line in enumerate(caption_lines):
        draw.text((6, image.height + 4 + 14 * line_index), line, fill=(245, 247, 250), font=font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination)
    return {
        "pixels_per_cell": pixels_per_cell,
        "colour_top_m": top_m,
        "cell_size_m": float(cell_size_m),
    }
