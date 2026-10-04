"""Public array-only crop/descriptor adapter; no identity or source-path inputs."""

import time
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class CropEvidence:
    rgb: np.ndarray
    mask: np.ndarray
    bounds: tuple[int, int, int, int]


def prepare_crop(
    rgb: np.ndarray, support: np.ndarray, bbox: list | tuple
) -> CropEvidence:
    """Clamp floor/ceil bounds, mask before and after the declared 128-grid resize."""
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("RGB must be uint8 HxWx3")
    if support.dtype != np.uint8 or support.shape != rgb.shape[:2]:
        raise ValueError("Support must be uint8 on the original RGB grid")
    if len(bbox) != 4 or not np.isfinite(bbox).all():
        raise ValueError("Four finite bounding coordinates required")
    x0, y0, x1, y1 = map(float, bbox)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("Bounding coordinates must be ordered")
    h, w = support.shape
    bounds = (
        max(0, min(w, int(np.floor(x0)))),
        max(0, min(h, int(np.floor(y0)))),
        max(0, min(w, int(np.ceil(x1)))),
        max(0, min(h, int(np.ceil(y1)))),
    )
    left, top, right, bottom = bounds
    if right <= left or bottom <= top:
        raise ValueError("Bounding box has no pixels")
    mask = np.where(support[top:bottom, left:right] != 0, 255, 0).astype(np.uint8)
    pixels = np.where(mask[..., None] != 0, rgb[top:bottom, left:right], 0)
    pixels = cv2.resize(pixels, (128, 128), interpolation=cv2.INTER_LINEAR).astype(
        np.uint8
    )
    mask = cv2.resize(mask, (128, 128), interpolation=cv2.INTER_NEAREST).astype(
        np.uint8
    )
    pixels = np.where(mask[..., None] != 0, pixels, 0).astype(np.uint8)
    pixels.setflags(write=False)
    mask.setflags(write=False)
    return CropEvidence(pixels, mask, bounds)


def describe_classical(crop: CropEvidence) -> dict[str, Any]:
    cv2.setNumThreads(1)
    gray = cv2.cvtColor(crop.rgb, cv2.COLOR_RGB2GRAY)
    factories = {
        "orb": cv2.ORB_create(  # type: ignore[attr-defined]
            nfeatures=500,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=31,
            firstLevel=0,
            WTA_K=2,
            scoreType=cv2.ORB_HARRIS_SCORE,
            patchSize=31,
            fastThreshold=20,
        ),
        "sift": cv2.SIFT_create(  # type: ignore[attr-defined]
            nfeatures=500,
            nOctaveLayers=3,
            contrastThreshold=0.04,
            edgeThreshold=10,
            sigma=1.6,
            descriptorType=cv2.CV_32F,
            enable_precise_upscale=False,
        ),
    }
    result = {}
    for name, extractor in factories.items():
        started = time.perf_counter()
        cv2.setRNGSeed(0)
        keypoints, descriptors = extractor.detectAndCompute(gray, crop.mask)
        keep = [
            i
            for i, point in enumerate(keypoints)
            if crop.mask[min(127, int(point.pt[1])), min(127, int(point.pt[0]))] != 0
        ]
        result[name] = {
            "extraction_seconds": time.perf_counter() - started,
            "points": [list(keypoints[i].pt) for i in keep],
            "descriptors": (
                descriptors[keep].tolist() if descriptors is not None else []
            ),
        }
    return result
