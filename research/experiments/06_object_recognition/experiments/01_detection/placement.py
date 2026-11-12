"""Task45 Part A: how far a matched box lands from its reference outline.

Pure functions over original-pixel boxes and boolean masks. A pixel (column i,
row j) belongs to an outline or a box when its centre (i + 0.5, j + 0.5) lies
inside; outlines use an even-odd test on unrounded vertices. Boxes and outlines
therefore share one rule, so an outline identical to its box covers the same
pixels. Values that cannot be computed are None with a reason, never 0.
"""

import math
from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

SMALL_AREA = 32 * 32
LARGE_AREA = 96 * 96
EDGE_MARGIN_PX = 2.0


def _span(low: float, high: float, size: int) -> tuple[int, int]:
    """Pixel indices i with centre i + 0.5 strictly between low and high."""
    first = max(0, math.floor(low - 0.5) + 1)
    stop = min(size, math.ceil(high - 0.5))
    return first, max(first, stop)


def box_slices(
    xyxy: Sequence[float], *, width: int, height: int
) -> tuple[slice, slice]:
    x1, y1, x2, y2 = map(float, xyxy)
    columns, rows = _span(x1, x2, width), _span(y1, y2, height)
    return slice(*rows), slice(*columns)


def box_mask(xyxy: Sequence[float], *, width: int, height: int) -> NDArray:
    mask = np.zeros((height, width), dtype=bool)
    mask[box_slices(xyxy, width=width, height=height)] = True
    return mask


def _even_odd(vertices: NDArray, x: NDArray, y: NDArray) -> NDArray:
    inside = np.zeros(x.shape, dtype=bool)
    previous = vertices[-1]
    for current in vertices:
        (x0, y0), (x1, y1) = previous, current
        if y0 != y1:
            crosses = (y0 > y) != (y1 > y)
            at = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            inside ^= crosses & (x < at)
        previous = current
    return inside


def polygon_mask(
    parts: Sequence[Sequence[float]], *, width: int, height: int
) -> NDArray:
    """Union of COCO polygon parts, each a flat [x0, y0, x1, y1, ...] list."""
    mask = np.zeros((height, width), dtype=bool)
    for flat in parts:
        vertices = np.asarray(flat, dtype=np.float64).reshape(-1, 2)
        if len(vertices) < 3:
            continue
        # Only pixels whose centres fall inside the part's bounding box can be inside.
        rows, columns = box_slices(
            [*vertices.min(axis=0), *vertices.max(axis=0)], width=width, height=height
        )
        x, y = np.meshgrid(
            np.arange(columns.start, columns.stop) + 0.5,
            np.arange(rows.start, rows.stop) + 0.5,
        )
        mask[rows, columns] |= _even_odd(vertices, x, y)
    return mask


def decode_rle(counts: Sequence[int], *, height: int, width: int) -> NDArray:
    """Uncompressed COCO run lengths: alternate background/foreground, column-major."""
    if sum(counts) != height * width or any(c < 0 for c in counts):
        raise ValueError("Run lengths must be nonnegative and cover the image")
    flat = np.zeros(height * width, dtype=bool)
    position = 0
    for index, count in enumerate(counts):
        if index % 2:
            flat[position : position + count] = True
        position += count
    return flat.reshape((width, height)).T


def _iou(first: Sequence[float], second: Sequence[float]) -> float:
    width = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
    height = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
    intersection = width * height
    area = (first[2] - first[0]) * (first[3] - first[1]) + (second[2] - second[0]) * (
        second[3] - second[1]
    )
    return intersection / (area - intersection)


def placement(predicted: Sequence[float], reference: Sequence[float]) -> dict:
    """Signed centre and edge errors in pixels (predicted minus reference)."""
    px1, py1, px2, py2 = map(float, predicted)
    rx1, ry1, rx2, ry2 = map(float, reference)
    dx = (px1 + px2) / 2 - (rx1 + rx2) / 2
    dy = (py1 + py2) / 2 - (ry1 + ry2) / 2
    diagonal = math.hypot(rx2 - rx1, ry2 - ry1)
    offset = math.hypot(dx, dy)
    return {
        "iou": _iou(predicted, reference),
        "centre_dx": dx,
        "centre_dy": dy,
        "centre_offset": offset,
        "centre_offset_fraction": offset / diagonal,
        "edge_left": px1 - rx1,
        "edge_top": py1 - ry1,
        "edge_right": px2 - rx2,
        "edge_bottom": py2 - ry2,
        "width_ratio": (px2 - px1) / (rx2 - rx1),
        "height_ratio": (py2 - py1) / (ry2 - ry1),
    }


def background_and_coverage(
    predicted: Sequence[float], reference: Sequence[float], outline: NDArray
) -> dict:
    """Excess background versus the reference box, and share of outline inside the box.

    Shares are over in-image pixels, so a box clipped at the border is judged on
    what the image shows.
    """
    height, width = outline.shape
    inside_predicted = outline[box_slices(predicted, width=width, height=height)]
    inside_reference = outline[box_slices(reference, width=width, height=height)]
    sizes = (inside_predicted.size, inside_reference.size, int(outline.sum()))
    if min(sizes) < 1:
        return {
            "excess_background": None,
            "outline_coverage": None,
            "reason": "box or outline under 1 px",
        }
    covered = int(inside_predicted.sum())
    outside_predicted = (sizes[0] - covered) / sizes[0]
    outside_reference = (sizes[1] - int(inside_reference.sum())) / sizes[1]
    return {
        "excess_background": float(outside_predicted - outside_reference),
        "outline_coverage": float(covered / sizes[2]),
        "reason": None,
    }


def size_band(area: float) -> str:
    """COCO evaluation bands on annotation `area` (outline pixels)."""
    if area < SMALL_AREA:
        return "small"
    return "medium" if area < LARGE_AREA else "large"


def touches_edge(
    xyxy: Sequence[float], *, width: int, height: int, margin: float = EDGE_MARGIN_PX
) -> bool:
    x1, y1, x2, y2 = map(float, xyxy)
    return x1 <= margin or y1 <= margin or x2 >= width - margin or y2 >= height - margin


def _intersection(first: Sequence[float], second: Sequence[float]) -> float:
    width = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
    height = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
    return width * height


def crowd_ignored(
    unmatched: Sequence[dict], crowds: Sequence[dict], *, threshold: float
) -> list[int]:
    """COCO's rule: ignore a detection mostly inside a same-class crowd region.

    The share is intersection over the detection's own area. A crowd region may
    absorb any number of detections.
    """
    ignored = []
    for index, row in enumerate(unmatched):
        x1, y1, x2, y2 = row["xyxy"]
        area = (x2 - x1) * (y2 - y1)
        if area > 0 and any(
            crowd["category"] == row["label"]
            and _intersection(row["xyxy"], crowd["bbox_xyxy"]) / area >= threshold
            for crowd in crowds
        ):
            ignored.append(index)
    return ignored


def clutter(
    target: Sequence[float],
    others: Sequence[dict],
    others_mask: NDArray,
    *,
    width: int,
    height: int,
) -> dict:
    """How crowded a reference box is: overlapping objects and share covered by them."""
    window = others_mask[box_slices(target, width=width, height=height)]
    return {
        "overlapping_objects": sum(
            _intersection(target, other["bbox_xyxy"]) > 0 for other in others
        ),
        "covered_by_others": float(window.mean()) if window.size else None,
    }
