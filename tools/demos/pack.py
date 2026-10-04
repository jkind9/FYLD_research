"""Compact base64 encodings for arrays embedded in demo pages, decoded by web/viewer.js."""

from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image

_DTYPES = {"f32": "<f4", "u8": "|u1", "i8": "|i1", "u16": "<u2", "i16": "<i2", "u32": "<u4"}


def encode_array(values: np.ndarray, dtype: str | None = None) -> dict:
    """Encode an array as little-endian bytes in base64 with its dtype tag and shape."""
    arr = np.asarray(values)
    if dtype is None:
        dtype = next((k for k, v in _DTYPES.items() if np.dtype(v) == arr.dtype.newbyteorder("<")), None)
        if dtype is None:
            raise ValueError(f"unsupported dtype {arr.dtype}; pass dtype explicitly")
    data = np.ascontiguousarray(arr.astype(_DTYPES[dtype]))
    return {"dtype": dtype, "shape": list(data.shape), "b64": base64.b64encode(data.tobytes()).decode("ascii")}


def encode_positions(points: np.ndarray) -> dict:
    """Quantise (N, 3) positions to 16 bits per axis inside their bounding box.

    Error is at most one quantisation step: extent / 65535 per axis (about 0.06 mm for a
    4 m room).
    """
    p = np.asarray(points, dtype=float)
    lo, hi = p.min(axis=0), p.max(axis=0)
    span = np.where(hi > lo, hi - lo, 1.0)
    q = np.rint((p - lo) / span * 65535).astype("<u2")
    return {"min": lo.tolist(), "max": (lo + span).tolist(), "count": len(p),
            "b64": base64.b64encode(q.tobytes()).decode("ascii")}


def encode_normals(normals: np.ndarray) -> dict:
    """Quantise unit normals to signed 8 bits per axis; the viewer renormalises them."""
    q = np.clip(np.rint(np.asarray(normals) * 127), -127, 127).astype("|i1")
    return encode_array(q, "i8")


def image_data_url(rgb: np.ndarray, fmt: str = "JPEG", quality: int = 82, size: tuple[int, int] | None = None) -> str:
    """Encode an (H, W, 3) or (H, W, 4) uint8 image as a data URL."""
    img = Image.fromarray(np.asarray(rgb, dtype=np.uint8))
    if size is not None:
        img = img.resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    if fmt == "JPEG":
        img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True)
        mime = "image/jpeg"
    else:
        img.save(buf, "PNG", optimize=True)
        mime = "image/png"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def colormap(values: np.ndarray, lo: float, hi: float, name: str = "turbo") -> np.ndarray:
    """Map scalars to uint8 RGB with a fixed matplotlib colormap; NaN becomes black."""
    from matplotlib import colormaps

    v = np.asarray(values, dtype=float)
    t = np.clip((v - lo) / (hi - lo), 0.0, 1.0)
    rgb = (colormaps[name](np.nan_to_num(t))[..., :3] * 255).astype(np.uint8)
    rgb[~np.isfinite(v)] = 0
    return rgb
