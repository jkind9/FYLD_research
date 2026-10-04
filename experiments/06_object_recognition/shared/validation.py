"""Small validators shared by object records and annotation manifests."""

import math
import re
from collections.abc import Iterable
from typing import Any

from experiments.shared.contracts import Calibration


def identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def finite(value: Any, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"{name} must be finite")
    return float(value)


def sha256_value(value: Any) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("Expected lowercase SHA256 with 64 hex characters")
    return value


def pairs(
    values: Iterable[tuple[str, str]], name: str, *, hashes: bool = False
) -> tuple[tuple[str, str], ...]:
    result = tuple(tuple(pair) for pair in values)
    if not result or any(len(pair) != 2 for pair in result):
        raise ValueError(f"{name} requires nonempty key/value pairs")
    keys = [identifier(pair[0], name) for pair in result]
    if len(set(keys)) != len(keys):
        raise ValueError(f"Duplicate {name} keys")
    for _, value in result:
        sha256_value(value) if hashes else identifier(value, name)
    return result  # type: ignore[return-value]


def pixel_support(
    polygon: Any, bbox: Any, calibration: Calibration
) -> tuple[tuple[tuple[float, float], ...], tuple[float, ...]]:
    if not isinstance(calibration, Calibration):
        raise ValueError(  # noqa: TRY004 - schema errors use ValueError
            "Expected Calibration"
        )
    if isinstance(calibration.width, bool) or isinstance(calibration.height, bool):
        raise ValueError("Image dimensions must be positive integers")  # noqa: TRY004
    if not isinstance(polygon, (tuple, list)) or not isinstance(bbox, (tuple, list)):
        raise ValueError("Pixel support must be polygon/bbox sequences")  # noqa: TRY004
    if any(not isinstance(point, (tuple, list)) for point in polygon):
        raise ValueError("Polygon must contain pixel pairs")
    vertices = tuple(tuple(finite(v, "polygon") for v in point) for point in polygon)
    box = tuple(finite(v, "bbox") for v in bbox)
    if len(box) != 4 or len(vertices) < 3 or any(len(point) != 2 for point in vertices):
        raise ValueError("Expected polygon with >=3 pixel pairs and xyxy bbox")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= calibration.width and 0 <= y0 < y1 <= calibration.height):
        raise ValueError("Bounding box must have positive area inside image")
    if any(not (x0 <= x <= x1 and y0 <= y <= y1) for x, y in vertices):
        raise ValueError("Polygon must lie inside bounding box")
    area2 = sum(
        x * vertices[(i + 1) % len(vertices)][1]
        - y * vertices[(i + 1) % len(vertices)][0]
        for i, (x, y) in enumerate(vertices)
    )
    if area2 == 0:
        raise ValueError("Polygon must have nonzero area")
    return vertices, box  # type: ignore[return-value]


def position(
    value: Any, name: str, *, camera: bool = False
) -> tuple[float, ...] | None:
    if value is None:
        return None
    result = tuple(finite(component, name) for component in value)
    if len(result) != 3 or (camera and result[2] <= 0):
        raise ValueError(
            f"{name} requires three finite metre coordinates and positive camera Z"
        )
    return result
