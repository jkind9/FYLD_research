"""Original source evidence and evaluation answers remain separate."""

import copy
import hashlib
import importlib
from dataclasses import asdict

import numpy as np
import pytest
from PIL import Image

from experiments.shared.contracts import Calibration

contracts = importlib.import_module("experiments.06_object_recognition.shared.manifest")


def source(repo, name, array):
    path = repo / name
    Image.fromarray(array).save(path)
    return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


@pytest.fixture
def manifest(tmp_path):
    rgb = source(tmp_path, "rgb.png", np.zeros((6, 8, 3), dtype=np.uint8))
    depth = source(tmp_path, "depth.png", np.ones((6, 8), dtype=np.uint16))
    return {
        "schema_version": 1,
        "name": "fixture",
        "calibration": asdict(
            Calibration(8, 6, 5, 5, 3.5, 2.5, "x-right_y-down_z-forward")
        ),
        "depth_policy": {
            "units_per_metre": 5000,
            "raw_missing": 0,
            "processed_max_m": 4,
            "registration": "same_pixel_grid",
        },
        "source_records": [],
        "provenance": {"annotation_author": "agent", "review_status": "provisional"},
        "split_policy": {"claim": "within_session_smoke", "tuning": False},
        "frames": [
            {
                "session_id": "desk",
                "frame_id": "f0",
                "timestamp_s": 1.0,
                "visit_id": "before",
                "partition": "enrollment",
                "rgb": rgb,
                "depth": {**depth, "timestamp_s": 1.0},
                "label_coverage": {"cup": "complete"},
                "labels": [
                    {
                        "instance_id": "cup1",
                        "category": "cup",
                        "polygon": [[1, 1], [4, 1], [4, 4], [1, 4]],
                        "bbox_xyxy": [1, 1, 4, 4],
                        "mask_status": "provisional",
                        "support": "visible_cup",
                    }
                ],
            }
        ],
        "scenarios": [{"name": "return", "status": "absent", "evidence": "fixture"}],
        "revisits": [],
    }


def test_valid_manifest_and_method_input_allowlist(manifest, tmp_path):
    contracts.validate_manifest(manifest, tmp_path)
    manifest["frames"][0]["surprise_answer"] = "cup1"
    result = contracts.method_inputs(manifest)
    assert set(result) == {
        "schema_version",
        "name",
        "calibration",
        "depth_policy",
        "frames",
    }
    assert set(result["frames"][0]) == {
        "session_id",
        "frame_id",
        "timestamp_s",
        "partition",
        "rgb",
        "depth",
    }
    assert "labels" not in result["frames"][0]
    assert "visit_id" not in result["frames"][0]
    result["frames"][0]["rgb"]["path"] = "changed"
    assert manifest["frames"][0]["rgb"]["path"] == "rgb.png"


def test_method_inputs_withhold_semantic_visit_answers(manifest):
    for visit_id in ("look_away", "return", "before"):
        manifest["frames"][0]["visit_id"] = visit_id
        projected = contracts.method_inputs(manifest)
        assert "visit_id" not in projected["frames"][0]
        assert visit_id not in repr(projected)


@pytest.mark.parametrize(
    "mutation",
    [
        "hash",
        "escape",
        "absolute",
        "grid",
        "raw8",
        "units",
        "registration",
        "timestamp",
        "duplicate_frame",
        "duplicate_instance",
        "category",
        "bbox",
        "polygon",
        "coverage",
        "partition",
        "split",
        "provenance",
        "scenario",
        "missing_source",
        "metadata",
    ],
)
def test_manifest_rejects_invalid_evidence(manifest, tmp_path, mutation):
    frame = manifest["frames"][0]
    label = frame["labels"][0]
    if mutation == "hash":
        frame["rgb"]["sha256"] = "a" * 64
    elif mutation == "escape":
        frame["rgb"]["path"] = "../rgb.png"
    elif mutation == "absolute":
        frame["rgb"]["path"] = "C:/rgb.png"
    elif mutation == "grid":
        frame["depth"] = {
            **source(tmp_path, "bad.png", np.ones((3, 8), dtype=np.uint16)),
            "timestamp_s": 1.0,
        }
    elif mutation == "raw8":
        frame["depth"] = {
            **source(tmp_path, "bad.png", np.ones((6, 8), dtype=np.uint8)),
            "timestamp_s": 1.0,
        }
    elif mutation == "units":
        manifest["depth_policy"]["units_per_metre"] = 1000
    elif mutation == "registration":
        manifest["depth_policy"]["registration"] = "other_grid"
    elif mutation == "timestamp":
        frame["timestamp_s"] = float("nan")
    elif mutation == "duplicate_frame":
        manifest["frames"].append(copy.deepcopy(frame))
    elif mutation == "duplicate_instance":
        frame["labels"].append(copy.deepcopy(label))
    elif mutation == "category":
        frame["labels"][0]["category"] = "tv"
    elif mutation == "bbox":
        label["bbox_xyxy"] = [1, 1, 9, 4]
    elif mutation == "polygon":
        label["polygon"] = [[1, 1], [2, 2], [3, 3]]
    elif mutation == "coverage":
        frame["label_coverage"] = {}
    elif mutation == "partition":
        frame["partition"] = "unknown"
    elif mutation == "split":
        manifest["split_policy"]["tuning"] = True
    elif mutation == "provenance":
        manifest["provenance"] = {}
    elif mutation == "scenario":
        manifest["scenarios"][0]["status"] = "maybe"
    elif mutation == "missing_source":
        frame["rgb"]["path"] = "missing.png"
    elif mutation == "metadata":
        manifest["source_records"] = [{"path": "rgb.png", "sha256": "b" * 64}]
    with pytest.raises(ValueError):
        contracts.validate_manifest(manifest, tmp_path)


@pytest.mark.parametrize(
    "kind",
    [
        "path",
        "hash",
        "augmentation_of",
        "source_frame_id",
        "missing_parent",
        "category",
    ],
)
def test_split_and_identity_leakage(manifest, tmp_path, kind):
    second = copy.deepcopy(manifest["frames"][0])
    second.update(frame_id="f1", partition="evaluation", timestamp_s=2)
    second["depth"]["timestamp_s"] = 2
    if kind not in {"path", "hash"}:
        second["rgb"] = source(
            tmp_path, "second.png", np.ones((6, 8, 3), dtype=np.uint8)
        )
        second["depth"] = {
            **source(tmp_path, "second_depth.png", np.ones((6, 8), dtype=np.uint16)),
            "timestamp_s": 2,
        }
    if kind == "hash":
        second["rgb"] = source(
            tmp_path, "second.png", np.zeros((6, 8, 3), dtype=np.uint8)
        )
    if kind in {"augmentation_of", "source_frame_id"}:
        second[kind] = "f0"
    if kind == "missing_parent":
        second["augmentation_of"] = "absent"
    if kind == "category":
        second["labels"][0].update(category="tv", support="visible_display_enclosure")
        second["label_coverage"] = {"tv": "subset"}
    manifest["frames"].append(second)
    with pytest.raises(ValueError):
        contracts.validate_manifest(manifest, tmp_path)


def test_depth_path_alias_cannot_cross_partitions(manifest, tmp_path):
    second = copy.deepcopy(manifest["frames"][0])
    second.update(frame_id="f1", partition="evaluation", timestamp_s=2)
    second["rgb"] = source(tmp_path, "other.png", np.ones((6, 8, 3), dtype=np.uint8))
    second["depth"].update(path="./depth.png", timestamp_s=2)
    manifest["frames"].append(second)
    with pytest.raises(ValueError, match="leaks between partitions"):
        contracts.validate_manifest(manifest, tmp_path)


def test_structure_validation_can_skip_source_io(manifest, tmp_path):
    (tmp_path / "rgb.png").unlink()
    contracts.validate_manifest(manifest, tmp_path, verify_sources=False)
    manifest["frames"][0]["rgb"]["path"] = "../unsafe.png"
    with pytest.raises(ValueError):
        contracts.validate_manifest(manifest, tmp_path, verify_sources=False)


def test_revisit_rejects_missing_frames(manifest, tmp_path):
    manifest["revisits"] = [
        {
            "instance_id": "cup1",
            "before_frame_id": "f0",
            "gap_frame_id": "missing",
            "return_frame_id": "f0",
        }
    ]
    with pytest.raises(ValueError):
        contracts.validate_manifest(manifest, tmp_path)


def revisit_fixture(manifest, repo):
    for index in (1, 2):
        frame = copy.deepcopy(manifest["frames"][0])
        frame.update(
            frame_id=f"f{index}", timestamp_s=1 + index, partition="evaluation"
        )
        frame["rgb"] = source(
            repo, f"rgb{index}.png", np.full((6, 8, 3), index, dtype=np.uint8)
        )
        frame["depth"] = {
            **source(repo, f"depth{index}.png", np.ones((6, 8), dtype=np.uint16)),
            "timestamp_s": 1 + index,
        }
        if index == 1:
            frame["labels"] = []
        manifest["frames"].append(frame)
    manifest["revisits"] = [
        {
            "instance_id": "cup1",
            "before_frame_id": "f0",
            "gap_frame_id": "f1",
            "return_frame_id": "f2",
        }
    ]
    return manifest


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "gap_labelled",
        "return_unlabelled",
        "subset",
        "unordered",
        "session",
        "duplicate",
    ],
)
def test_revisit_evidence(manifest, tmp_path, mutation):
    revisit_fixture(manifest, tmp_path)
    if mutation == "gap_labelled":
        manifest["frames"][1]["labels"] = copy.deepcopy(manifest["frames"][0]["labels"])
    elif mutation == "return_unlabelled":
        manifest["frames"][2]["labels"] = []
    elif mutation == "subset":
        manifest["frames"][1]["label_coverage"]["cup"] = "subset"
    elif mutation == "unordered":
        manifest["revisits"][0].update(before_frame_id="f2", return_frame_id="f0")
    elif mutation == "session":
        manifest["frames"][2]["session_id"] = "other"
    elif mutation == "duplicate":
        manifest["revisits"].append(copy.deepcopy(manifest["revisits"][0]))
    if mutation is None:
        contracts.validate_manifest(manifest, tmp_path)
    else:
        with pytest.raises(ValueError):
            contracts.validate_manifest(manifest, tmp_path)


def test_derived_frames_keep_parent_partition(manifest, tmp_path):
    derived = copy.deepcopy(manifest["frames"][0])
    derived.update(frame_id="crop", source_frame_id="f0", augmentation_of="f0")
    manifest["frames"].append(derived)
    contracts.validate_manifest(manifest, tmp_path)
    derived["source_frame_id"] = "crop"
    with pytest.raises(ValueError):
        contracts.validate_manifest(manifest, tmp_path)


@pytest.mark.parametrize(
    "mutation",
    [
        "root",
        "rows",
        "version",
        "calibration",
        "empty_frames",
        "duplicate_metadata",
        "duplicate_scenario",
        "coverage",
        "status",
    ],
)
def test_manifest_schema_errors(manifest, tmp_path, mutation):
    if mutation == "root":
        manifest = []
    elif mutation == "rows":
        manifest["frames"] = {}
    elif mutation == "version":
        manifest["schema_version"] = True
    elif mutation == "calibration":
        manifest["calibration"].pop("axes")
    elif mutation == "empty_frames":
        manifest["frames"] = []
    elif mutation == "duplicate_metadata":
        row = copy.deepcopy(manifest["frames"][0]["rgb"])
        manifest["source_records"] = [row, row]
    elif mutation == "duplicate_scenario":
        manifest["scenarios"].append(copy.deepcopy(manifest["scenarios"][0]))
    elif mutation == "coverage":
        manifest["frames"][0]["label_coverage"]["cup"] = "guess"
    elif mutation == "status":
        manifest["frames"][0]["labels"][0]["mask_status"] = "verified"
    with pytest.raises(ValueError):
        contracts.validate_manifest(manifest, tmp_path)
