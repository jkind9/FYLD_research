"""ICL input snapshots and strict binary point-reference loading."""

import shutil
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from experiments.datasets.acquisition import sha256
from experiments.geometry_validation.src.icl import Frame, load_frame

PLY_TYPES = {"float": "<f4", "double": "<f8", "uchar": "u1"}


def copy_checked(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    before = sha256(source)
    shutil.copyfile(source, target)
    if before != sha256(target) or before != sha256(source):
        raise ValueError(f"Input changed during copy: {source.name}")


def snapshot_metadata(dataset: Path, target: Path) -> None:
    for name in ("conventions.json", "trajectory2/livingRoom2.gt.freiburg"):
        copy_checked(dataset / name, target / name)


def snapshot_frame(dataset: Path, snapshot: Path, frame_id: int) -> Frame:
    for kind in ("rgb", "depth"):
        name = f"trajectory2/{kind}/{frame_id}.png"
        copy_checked(dataset / name, snapshot / name)
    return load_frame(snapshot, frame_id)


def read_reference(path: Path) -> NDArray:
    """Read XYZ in file order; reject unsupported elements, lists and payload size."""
    with path.open("rb") as stream:
        lines = []
        for _ in range(100):
            line = stream.readline(1024)
            if not line or len(line) == 1024:
                raise ValueError("Invalid PLY header")
            lines.append(line.decode("ascii").strip())
            if lines[-1] == "end_header":
                break
        else:
            raise ValueError("PLY header too long")
        offset = stream.tell()
    if lines[:2] != ["ply", "format binary_little_endian 1.0"]:
        raise ValueError("Reference must be binary little-endian PLY")
    count: int | None = None
    fields: list[tuple[str, str]] = []
    for declaration in lines[2:-1]:
        row = declaration.split()
        if row[0] == "comment":
            continue
        if row[:2] == ["element", "vertex"] and len(row) == 3 and count is None:
            count = int(row[2])
        elif row[0] == "property" and len(row) == 3 and count is not None:
            if row[1] not in PLY_TYPES or row[2] in {name for name, _ in fields}:
                raise ValueError("Unsupported or duplicate PLY property")
            fields.append((row[2], PLY_TYPES[row[1]]))
        else:
            raise ValueError("Unsupported PLY header declaration")
    if count is None or count < 1 or not {"x", "y", "z"}.issubset(dict(fields)):
        raise ValueError("Reference requires nonempty XYZ vertices")
    dtype = np.dtype(fields)
    payload_end = offset + count * dtype.itemsize
    size = path.stat().st_size
    # The acquired publisher PLY ends its exact binary vertex payload with one LF.
    trailer = b""
    if size == payload_end + 1:
        with path.open("rb") as stream:
            stream.seek(payload_end)
            trailer = stream.read(1)
    if size != payload_end and not (size == payload_end + 1 and trailer == b"\n"):
        raise ValueError("PLY payload size does not match header")
    raw = np.memmap(path, mode="r", offset=offset, dtype=dtype, shape=(count,))
    points = np.column_stack([raw[name] for name in ("x", "y", "z")]).astype(np.float64)
    if not np.isfinite(points).all():
        raise ValueError("Reference contains nonfinite XYZ")
    points.setflags(write=False)
    return points
