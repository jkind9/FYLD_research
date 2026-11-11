"""Phone recordings decoded once at the package boundary."""

import json
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from sitescan.types import ArcoreDepth, Camera, Frame

from . import wire_v1, wire_v2


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


def read_wire_session(folder: Path | str) -> Iterator[wire_v1.Frame]:
    """Checked wire records for callers awaiting the pipeline migration."""
    folder = Path(folder)
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


def frames(folder: Path | str) -> Iterator[Frame]:
    """Frames in file order, with RGB arrays and world_from_camera matrices."""
    for record in read_wire_session(folder):
        with Image.open(BytesIO(record.image_jpeg)) as image:
            rgb = np.asarray(image.convert("RGB"))
        camera = None
        if record.intrinsics is not None:
            camera = Camera(*record.intrinsics, *record.image_size)
        depth = None
        if record.depth is not None:
            d = record.depth
            height, width = d.depth_m.shape
            depth = ArcoreDepth(
                d.t_ns, d.depth_m, d.confidence, Camera(*d.intrinsics, width, height)
            )
        pose = None if record.pose is None else wire_v1.world_from_camera_cv(record.pose)
        created = record.anchor_created
        if created is not None:
            created = (created[0], wire_v1.world_from_camera_cv(created[1]))
        updates = {i: wire_v1.world_from_camera_cv(p) for i, p in record.anchor_updates.items()}
        yield Frame(
            record.seq,
            record.t_ns,
            rgb,
            camera,
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
        )
