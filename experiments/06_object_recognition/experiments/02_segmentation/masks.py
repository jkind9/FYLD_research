"""Original-grid rectangle, GrabCut and filled boundary controls, without labels."""

import math
from typing import Any

import cv2
import numpy as np

METHODS = ("rectangle", "grabcut", "canny")


def rectangle_bounds(value: Any, width: int, height: int) -> tuple[int, int, int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("Box needs four coordinates")
    if any(
        isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v)
        for v in value
    ):
        raise ValueError("Box coordinates must be finite numbers")
    x1, y1, x2, y2 = value
    if x2 <= x1 or y2 <= y1 or width < 1 or height < 1:
        raise ValueError("Box/grid must have positive extent")
    return (
        max(0, min(width, math.floor(x1))),
        max(0, min(height, math.floor(y1))),
        max(0, min(width, math.ceil(x2))),
        max(0, min(height, math.ceil(y2))),
    )


def segment(rgb: np.ndarray, box: list[float], method: str) -> dict:
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ValueError("Expected uint8 RGB image")
    if method not in METHODS:
        raise ValueError("Unknown mask method")
    height, width = rgb.shape[:2]
    bounds = rectangle_bounds(box, width, height)
    x1, y1, x2, y2 = bounds
    empty = np.zeros((height, width), np.uint8)
    if x2 - x1 < 2 or y2 - y1 < 2 or (x1 == y1 == 0 and x2 == width and y2 == height):
        return {
            "status": "unusable_prompt",
            "mask": empty,
            "bounds": bounds,
            "error": "Prompt needs 2x2 support and certain background",
        }
    if method == "rectangle":
        empty[y1:y2, x1:x2] = 255
        return {"status": "ok", "mask": empty, "bounds": bounds, "error": None}
    cv2.setNumThreads(1)
    cv2.setRNGSeed(0)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    if method == "grabcut":
        labels = np.zeros((height, width), np.uint8)
        try:
            cv2.grabCut(
                bgr,
                labels,
                (x1, y1, x2 - x1, y2 - y1),
                np.zeros((1, 65), np.float64),
                np.zeros((1, 65), np.float64),
                5,
                cv2.GC_INIT_WITH_RECT,
            )
        except cv2.error as error:
            return {
                "status": "failed",
                "mask": empty,
                "bounds": bounds,
                "error": str(error),
            }
        result = np.where(
            (labels == cv2.GC_FGD) | (labels == cv2.GC_PR_FGD), 255, 0
        ).astype(np.uint8)
    else:
        gray = cv2.cvtColor(bgr[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3, L2gradient=True)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if contours:
            crop = np.zeros(gray.shape, np.uint8)
            cv2.drawContours(
                crop, [max(contours, key=cv2.contourArea)], -1, 255, cv2.FILLED
            )
            empty[y1:y2, x1:x2] = crop
        result = empty
    return {
        "status": "ok" if result.any() else "empty",
        "mask": result,
        "bounds": bounds,
        "error": None,
    }
