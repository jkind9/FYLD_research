"""Task45 COCO loader: verified extraction, class mapping and outlines."""

import importlib
import json
import zipfile

import pytest

coco = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.coco"
)
from experiments.datasets.acquisition import sha256


def _archives(tmp_path, images=2):
    folder = tmp_path / "archives"
    folder.mkdir()
    with zipfile.ZipFile(folder / "val2017.zip", "w") as archive:
        archive.writestr("val2017/", "")
        for i in range(images):
            archive.writestr(f"val2017/{i:012d}.jpg", b"jpg")
    with zipfile.ZipFile(folder / "annotations_trainval2017.zip", "w") as archive:
        archive.writestr(coco.ANNOTATIONS, json.dumps({"images": []}))
        archive.writestr("annotations/instances_train2017.json", "{}")
    return folder


def _pin(monkeypatch, folder, images=2):
    pinned = {
        name: {"bytes": (folder / name).stat().st_size, "sha256": sha256(folder / name)}
        for name in coco.ARCHIVES
    }
    monkeypatch.setattr(coco, "ARCHIVES", pinned)
    monkeypatch.setattr(coco, "IMAGE_COUNT", images)


def test_extraction_writes_receipt_and_only_needed_members(tmp_path, monkeypatch):
    folder = _archives(tmp_path)
    _pin(monkeypatch, folder)
    destination = tmp_path / "coco2017"
    receipt = coco.extract(folder, destination)
    assert receipt["members"] == 3
    assert not (destination / "annotations/instances_train2017.json").exists()
    assert coco.check_extraction(destination)["members"] == 3
    with pytest.raises(FileExistsError):
        coco.extract(folder, destination)


def test_extraction_refuses_changed_archive(tmp_path, monkeypatch):
    folder = _archives(tmp_path)
    _pin(monkeypatch, folder)
    with zipfile.ZipFile(folder / "val2017.zip", "a") as archive:
        archive.writestr("val2017/extra.jpg", b"x")
    with pytest.raises(ValueError, match="differs"):
        coco.extract(folder, tmp_path / "coco2017")
    assert not (tmp_path / "coco2017").exists()


def test_check_refuses_missing_image(tmp_path, monkeypatch):
    folder = _archives(tmp_path)
    _pin(monkeypatch, folder)
    destination = tmp_path / "coco2017"
    coco.extract(folder, destination)
    next((destination / "val2017").glob("*.jpg")).unlink()
    with pytest.raises(ValueError, match="images"):
        coco.check_extraction(destination)


def test_class_map_matches_by_name_and_refuses_mismatch():
    categories = [{"id": 1, "name": "person"}, {"id": 47, "name": "cup"}]
    assert coco.class_map(categories, {0: "person", 41: "cup"}) == {
        1: (0, "person"),
        47: (41, "cup"),
    }
    with pytest.raises(ValueError, match="no class"):
        coco.class_map([{"id": 1, "name": "human"}], {0: "person"})


def test_image_records_convert_boxes_and_split_crowds():
    data = {
        "images": [{"id": 7, "file_name": "a.jpg", "width": 500, "height": 375}],
        "annotations": [
            {
                "id": 11,
                "image_id": 7,
                "category_id": 47,
                "bbox": [10, 20, 30, 40],
                "area": 900.0,
                "iscrowd": 0,
                "segmentation": [[10, 20, 40, 20, 40, 60]],
            },
            {
                "id": 12,
                "image_id": 7,
                "category_id": 1,
                "bbox": [0, 0, 5, 5],
                "area": 25.0,
                "iscrowd": 1,
                "segmentation": {"size": [375, 500], "counts": [375 * 500]},
            },
        ],
    }
    (record,) = coco.image_records(data, {47: (41, "cup"), 1: (0, "person")})
    assert record["references"][0]["bbox_xyxy"] == [10.0, 20.0, 40.0, 60.0]
    assert record["references"][0]["instance_id"] == "11"
    assert record["crowds"][0]["category"] == "person"
    mask = coco.outline(record["crowds"][0], width=500, height=375)
    assert mask.shape == (375, 500) and mask.sum() == 0
    with pytest.raises(ValueError, match="size"):
        coco.outline(record["crowds"][0], width=375, height=500)
