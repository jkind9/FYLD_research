"""COCO val2017 for Task45: verified extraction, references and outlines.

Only the 5000 val2017 images and instances_val2017.json are extracted. The
archives must match the sizes and SHA-256 values recorded at download. A staging
folder is renamed into place only after every member is written, so an
interrupted extraction never looks complete.
"""

import json
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray

from experiments.datasets.acquisition import safe_name, sha256

from .placement import decode_rle, polygon_mask

URLS = {
    "val2017.zip": "http://images.cocodataset.org/zips/val2017.zip",
    "annotations_trainval2017.zip": "http://images.cocodataset.org/annotations/annotations_trainval2017.zip",
}
ARCHIVES = {
    "val2017.zip": {
        "bytes": 815_585_330,
        "sha256": "4f7e2ccb2866ec5041993c9cf2a952bbed69647b115d0f74da7ce8f4bef82f05",
    },
    "annotations_trainval2017.zip": {
        "bytes": 252_907_541,
        "sha256": "113a836d90195ee1f884e704da6304dfaaecff1f023f49b6ca93c4aaae470268",
    },
}
ANNOTATIONS = "annotations/instances_val2017.json"
IMAGE_COUNT = 5000
RECEIPT = "EXTRACTION.json"


def _check_archives(archives: Path) -> dict:
    found = {}
    for name, expected in ARCHIVES.items():
        path = archives / name
        size, digest = path.stat().st_size, sha256(path)
        if size != expected["bytes"] or digest != expected["sha256"]:
            raise ValueError(f"{name} differs from the recorded download")
        found[name] = {"bytes": size, "sha256": digest, "url": URLS[name]}
    return found


def _wanted(name: str) -> bool:
    return name == ANNOTATIONS or (
        name.startswith("val2017/") and name.endswith(".jpg")
    )


def extract(archives: Path, destination: Path) -> dict:
    """Stage, write a receipt, then rename into place; never overwrite."""
    if destination.exists():
        raise FileExistsError(f"Refusing overwrite: {destination}")
    checked = _check_archives(archives)
    staging = destination.with_name(destination.name + ".staging-" + uuid4().hex)
    staging.mkdir(parents=True)
    members = 0
    for name in ARCHIVES:
        with zipfile.ZipFile(archives / name) as archive:
            for info in archive.infolist():
                if info.is_dir() or not _wanted(info.filename):
                    continue
                target = staging.joinpath(*safe_name(info.filename).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)
                if target.stat().st_size != info.file_size:
                    raise ValueError(f"Truncated member {info.filename}")
                members += 1
    if members != IMAGE_COUNT + 1:
        raise ValueError(
            f"Expected {IMAGE_COUNT} images and annotations, got {members}"
        )
    receipt = {
        "archives": checked,
        "members": members,
        "annotations_sha256": sha256(staging / ANNOTATIONS),
        "extracted_utc": datetime.now(UTC).isoformat(),
        "licence": "annotations CC BY 4.0; images under their Flickr terms",
    }
    (staging / RECEIPT).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    staging.rename(destination)
    return receipt


def check_extraction(destination: Path) -> dict:
    """Refuse a missing, partial or different extraction before any run."""
    receipt = json.loads((destination / RECEIPT).read_text(encoding="utf-8"))
    recorded = {
        k: {"bytes": v["bytes"], "sha256": v["sha256"]}
        for k, v in receipt["archives"].items()
    }
    if recorded != ARCHIVES:
        raise ValueError("Extraction came from different archives")
    if sha256(destination / ANNOTATIONS) != receipt["annotations_sha256"]:
        raise ValueError("Annotation file changed since extraction")
    images = sum(1 for _ in (destination / "val2017").glob("*.jpg"))
    if images != IMAGE_COUNT:
        raise ValueError(f"Expected {IMAGE_COUNT} images, found {images}")
    return receipt


def class_map(
    categories: list[dict], detector_names: dict[int, str]
) -> dict[int, tuple[int, str]]:
    """COCO category id -> detector class id and name, matched by name."""
    by_name = {name: class_id for class_id, name in detector_names.items()}
    mapping = {}
    for category in categories:
        if category["name"] not in by_name:
            raise ValueError(f"Detector has no class named {category['name']!r}")
        mapping[category["id"]] = (by_name[category["name"]], category["name"])
    if len(mapping) != len(detector_names):
        raise ValueError("COCO and detector class lists differ in size")
    return mapping


def _xyxy(bbox: list[float]) -> list[float]:
    x, y, w, h = map(float, bbox)
    return [x, y, x + w, y + h]


def image_records(data: dict, mapping: dict[int, tuple[int, str]]) -> list[dict]:
    """One record per image: references, crowd regions and raw outlines."""
    records = {
        image["id"]: {
            "image_id": image["id"],
            "file": f"val2017/{image['file_name']}",
            "width": image["width"],
            "height": image["height"],
            "references": [],
            "crowds": [],
        }
        for image in data["images"]
    }
    for annotation in data["annotations"]:
        record = records[annotation["image_id"]]
        entry = {
            "bbox_xyxy": _xyxy(annotation["bbox"]),
            "category": mapping[annotation["category_id"]][1],
            "instance_id": str(annotation["id"]),
            "area": float(annotation["area"]),
            "segmentation": annotation["segmentation"],
        }
        record["crowds" if annotation["iscrowd"] else "references"].append(entry)
    return [records[key] for key in sorted(records)]


def outline(entry: dict, *, width: int, height: int) -> NDArray:
    """Pixel-centre mask for a polygon outline or an uncompressed crowd outline."""
    segmentation = entry["segmentation"]
    if isinstance(segmentation, list):
        return polygon_mask(segmentation, width=width, height=height)
    if isinstance(segmentation.get("counts"), list):
        size = segmentation["size"]
        if list(size) != [height, width]:
            raise ValueError("Crowd outline size differs from image size")
        return decode_rle(segmentation["counts"], height=height, width=width)
    raise ValueError("Compressed run lengths are not expected in instances_val2017")


def empty_mask(*, width: int, height: int) -> NDArray:
    return np.zeros((height, width), dtype=bool)
