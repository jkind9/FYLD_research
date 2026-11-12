"""Tiny clean fixture runs are synthetic integrity controls, never GPU evidence."""

import importlib
import subprocess
from copy import deepcopy

import pytest
from PIL import Image

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import Run, write_json

cache = importlib.import_module(
    "experiments.06_object_recognition.experiments.01_detection.cache"
)


@pytest.fixture
def synthetic_cache(tmp_path):
    repo = tmp_path / "tiny_repo"
    repo.mkdir()
    for args in [
        ("init",),
        (
            "-c",
            "user.name=Synthetic",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--allow-empty",
            "-m",
            "synthetic fixture",
        ),
    ]:
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    meta = {
        "actual_device": "cuda:0",
        "actual_fp16": False,
        "image_shape_hw": [480, 640],
        "effective_arguments": cache.detector.PREDICT_SETTINGS,
        "class_names": {"41": "cup", "62": "tv"},
    }
    with Run(
        tmp_path / "controls",
        repo,
        {
            "checkpoint_sha256": cache.detector.CHECKPOINT_SHA256,
            "synthetic_control": True,
        },
    ) as run:
        image = run.path / "input/rgb/synthetic.png"
        image.parent.mkdir()
        Image.new("RGB", (640, 480)).save(image)
        frames = [
            {
                "source_selection_index": 0,
                "frame_id": "synthetic",
                "timestamp_s": 1.0,
                "rgb": {"path": "data/rgb/synthetic.png", "sha256": sha256(image)},
            }
        ]
        write_json(
            run.path / "output/selection.json",
            {
                "selected_frames": [
                    {
                        "frame_id": "synthetic",
                        "rgb": "rgb/synthetic.png",
                        "timestamp_s": 1.0,
                    }
                ]
            },
        )
        write_json(
            run.path / "output/detections.json",
            {
                "frames": [
                    {
                        "frame_index": 0,
                        "timestamp_s": 1.0,
                        "proposals": [
                            {
                                "xyxy": [1, 1, 10, 10],
                                "label": "cup",
                                "class_id": 41,
                                "confidence": 0.8,
                            }
                        ],
                    }
                ],
                "metadata": [meta],
            },
        )
        # This metadata is a synthetic validator input, not production provenance.
        write_json(
            run.path / "metadata/environment.json",
            {
                "packages": [{"name": "ultralytics", "version": "8.4.172"}],
                "synthetic_control": True,
            },
        )
    return run.path, frames, sha256(run.path / "metadata/manifest.json")


def test_synthetic_cache_extraction_has_no_reference_inputs(synthetic_cache):
    path, frames, digest = synthetic_cache
    before = deepcopy(frames)
    result = cache.check_cache(path, frames, digest)
    assert result["frames"][0]["proposals"][0]["class_id"] == 41
    assert frames == before
    assert result["environment"]["synthetic_control"] is True


def test_production_rejects_synthetic_completed_cache(synthetic_cache):
    path, frames, digest = synthetic_cache
    assert digest != cache.ACCEPTED_MANIFEST_SHA256
    with pytest.raises(ValueError, match="exact six"):
        cache.load_accepted_cache(path, frames)
    six = [{**frames[0], "source_selection_index": i} for i in cache.SELECTION_INDEXES]
    with pytest.raises(ValueError, match="pinned"):
        cache.load_accepted_cache(path, six)


@pytest.mark.parametrize(
    "change", ["tamper", "extra", "missing", "incomplete", "join", "duplicate", "index"]
)
def test_cache_corruption_and_bad_joins(synthetic_cache, change):
    path, frames, digest = synthetic_cache
    if change == "tamper":
        (path / "output/detections.json").write_text("{}")
    elif change == "extra":
        (path / "unexpected").write_text("extra")
    elif change == "missing":
        (path / "input/rgb/synthetic.png").unlink()
    elif change == "incomplete":
        write_json(path / "metadata/status.json", {"status": "running"})
    elif change == "join":
        frames = [{**frames[0], "timestamp_s": 2.0}]
    elif change == "duplicate":
        frames = frames * 2
    else:
        frames = [{**frames[0], "source_selection_index": True}]
    with pytest.raises(ValueError):
        cache.check_cache(path, frames, digest)


def test_unavailable_cache(tmp_path):
    with pytest.raises(ValueError, match="unavailable"):
        cache.check_cache(tmp_path / "absent", [], "0" * 64)


@pytest.mark.parametrize(
    "field,value",
    [
        ("actual_device", "cpu"),
        ("actual_fp16", True),
        ("image_shape_hw", [640, 480]),
        ("effective_arguments", {}),
        ("class_names", {}),
    ],
)
def test_invalid_predecessor_metadata(field, value):
    metadata = {
        "actual_device": "cuda:0",
        "actual_fp16": False,
        "image_shape_hw": [480, 640],
        "effective_arguments": cache.detector.PREDICT_SETTINGS,
        "class_names": {"41": "cup", "62": "tv"},
    }
    with pytest.raises(ValueError):
        cache._metadata({**metadata, field: value})
