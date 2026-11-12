"""Phone recordings decoded once at the package boundary."""

import json
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from sitescan.types import Calibration, Camera, Frame, MeasuredDepth, Trajectory

from . import wire_v1, wire_v2
from .trajectory import with_trajectory


def raw_header(header: dict) -> dict:
    """The header describing the lossless grey image saved on the host."""
    grey = header["grey"]
    return {k: v for k, v in header.items() if k != "host_received_ms"} | {
        "grey": grey | {"encoding": "raw", "bytes": grey["width"] * grey["height"]}
    }


def frame_payload(folder: Path, header: dict) -> bytes:
    """The saved v2 image and depth bytes, in wire order."""
    name = f"{int(header['seq']):06d}"
    with Image.open(folder / "cam0" / f"{name}.png") as image:
        grey = np.asarray(image).tobytes()
    payload = grey + (folder / "frames" / f"{name}.jpg").read_bytes()
    if header["arcore"] is not None and header["arcore"].get("depth"):
        payload += (folder / "depth" / f"{name}.bin").read_bytes()
    return payload


def read_wire_session(
    folder: Path | str, trajectory: Trajectory | None = None, calibration: Calibration | None = None
) -> Iterator[wire_v1.Frame]:
    """Checked wire records, posed by ARCore or, given a trajectory, by an open tracker."""
    records = wire_records(Path(folder))
    return records if trajectory is None else with_trajectory(records, trajectory, calibration)


def wire_records(folder: Path) -> Iterator[wire_v1.Frame]:
    """Checked wire records in file order, as the phone recorded them."""
    version = json.loads((folder / "session.json").read_text(encoding="utf-8"))["version"]
    wire_v1._require(version in (1, 2), "recording version must be 1 or 2")
    with (folder / "frames.jsonl").open(encoding="utf-8") as lines:
        for line in lines:
            header = json.loads(line)
            if version == 2:
                yield wire_v2.parse_frame(raw_header(header), frame_payload(folder, header))
            else:
                name = f"{int(header['seq']):06d}"
                payload = (folder / "frames" / f"{name}.jpg").read_bytes()
                if header.get("depth"):
                    payload += (folder / "depth" / f"{name}.bin").read_bytes()
                yield wire_v1.parse_frame(header, payload)


def camera(record: wire_v1.Frame) -> Camera | None:
    """The colour image's camera of a wire record, if it has intrinsics."""
    if record.intrinsics is None:
        return None
    return Camera(*record.intrinsics, *record.image_size)


def arcore_depth(depth: wire_v1.Depth) -> MeasuredDepth:
    """ARCore's wire depth record as a measured depth map, with its own camera."""
    height, width = depth.depth_m.shape
    camera = Camera(*depth.intrinsics, width, height)
    return MeasuredDepth(depth.t_ns, depth.depth_m, depth.confidence, camera, "arcore")


def frames(
    folder: Path | str, trajectory: Trajectory | None = None, calibration: Calibration | None = None
) -> Iterator[Frame]:
    """Frames in file order, with RGB arrays and world_from_camera matrices."""
    for record in read_wire_session(folder, trajectory, calibration):
        with Image.open(BytesIO(record.image_jpeg)) as image:
            rgb = np.asarray(image.convert("RGB"))
        depth = None if record.depth is None else arcore_depth(record.depth)
        pose = None if record.pose is None else wire_v1.world_from_camera_cv(record.pose)
        created = record.anchor_created
        if created is not None:
            created = (created[0], wire_v1.world_from_camera_cv(created[1]))
        updates = {i: wire_v1.world_from_camera_cv(p) for i, p in record.anchor_updates.items()}
        yield Frame(
            record.seq,
            record.t_ns,
            rgb,
            camera(record),
            pose,
            depth,
            record.point_ids,
            record.points_world,
            record.points_pixel,
            record.points_confidence,
            created,
            updates,
            record.tracking,
            record.failure,
            getattr(record, "arcore_t_ns", record.t_ns),
            getattr(record, "pose_source", "arcore"),
        )
