"""Run reference depth, poses and surface on an optional real TUM image slice."""

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from src.walkthrough import pipeline
from src.walkthrough.config import PipelineSpec
from src.walkthrough.steps.capture import TumSequence, pose_dataset
from src.walkthrough.steps.contracts import nearest_references
from src.walkthrough.steps.depth import RecordedSensorDepth
from src.walkthrough.steps.tracking import ReferencePoses

REPO = Path(__file__).resolve().parents[3]
DATASET = REPO / "data/tum/rgbd_dataset_freiburg1_xyz"
pytestmark = pytest.mark.skipif(
    not (DATASET / "rgb/1305031102.175304.png").is_file(),
    reason="Optional real TUM image download is not installed",
)


def test_real_xyz_depth_matches_all_colour_timestamps():
    colour = pose_dataset.read_table(DATASET / "rgb.txt")
    depth = pose_dataset.read_table(DATASET / "depth.txt")
    matches = list(
        nearest_references(
            (SimpleNamespace(frame_id=path, timestamp_s=time) for time, path in colour),
            [time for time, _ in depth],
            0.02,
        )
    )
    assert len(matches) == 798
    assert all(index is not None for _, index in matches)


def test_real_xyz_twenty_frame_reference_pipeline(tmp_path):
    sample = tmp_path / "sample"
    sample.mkdir()
    rows = pose_dataset.read_table(DATASET / "rgb.txt")[:20]
    for _, relative in rows:
        destination = sample / relative
        destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(DATASET / relative, destination)
    (sample / "rgb.txt").write_text(
        "".join(f"{timestamp:.6f} {relative}\n" for timestamp, relative in rows),
        encoding="utf-8",
    )
    result = pipeline.run(
        PipelineSpec(
            tmp_path / "runs",
            REPO,
            TumSequence(sample),
            depth=RecordedSensorDepth(DATASET),
            tracking=ReferencePoses(DATASET / "groundtruth.txt"),
            requested=("capture", "depth", "tracking", "surface"),
        )
    )
    assert [step.status for step in result.steps] == ["complete"] * 4 + ["skipped"] * 2
    assert result.controls == {"depth": "reference", "tracking": "reference"}
    assert not result.is_measurement
    output = result.path / "output/predictions"
    depth = json.loads((output / "depth.json").read_text())
    tracking = json.loads((output / "tracking.json").read_text())
    surface = json.loads((output / "surface.json").read_text())
    assert len(depth["frames"]) == len(tracking["records"]) == len(surface["shards"]) == 20
    assert [frame["frame_id"] for frame in depth["frames"]] == [path for _, path in rows]
    assert all(record["status"] == "supplied" for record in tracking["records"])
    for frame in depth["frames"]:
        with np.load(result.path / frame["arrays"], allow_pickle=False) as arrays:
            assert arrays["depth"].shape == (480, 640)
            assert arrays["valid"].any()
