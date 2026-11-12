"""Known supplied camera positions and honest stage explanations."""

import importlib
import json
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pytest

review = importlib.import_module("experiments.geometry_validation.src.review")


def saved_frames(root: Path, positions: list[list[float]]) -> list[dict]:
    frames = []
    for i, position in enumerate(positions):
        key = str(i + 1)
        directory = root / f"input/{key}"
        directory.mkdir(parents=True)
        pose = np.eye(4)
        pose[:3, 3] = position
        if i:
            pose[:3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
        (directory / "observation.json").write_text(
            json.dumps(
                {
                    "pose": {
                        "T_world_camera": pose.tolist(),
                        "world_id": "known",
                        "segment_id": "a",
                        "source": "supplied",
                        "units": "metres",
                        "direction": "camera_to_world",
                    }
                }
            )
        )
        output = root / f"output/{key}"
        output.mkdir(parents=True)
        np.save(output / "world.npy", np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0]]))
        frames.append(
            {
                "frame_id": key,
                "valid_pixels": 2,
                "max_projection_error_pixels": 0.0,
                "artifacts": {
                    "visualizations": [],
                    "arrays": ["world.npy"],
                    "clouds": [],
                },
            }
        )
    return frames


def test_supplied_centres_and_no_mutation(tmp_path):
    frames = saved_frames(tmp_path, [[1, 2, 3], [1.001, 2.002, 3.003]])
    before = (tmp_path / "output/1/world.npy").read_bytes()
    scene = review.export_scene(tmp_path, frames)
    np.testing.assert_allclose(
        scene["centres_world_m"], [[1, 2, 3], [1.001, 2.002, 3.003]]
    )
    np.testing.assert_allclose(
        scene["relative_centres_mm"], [[0, 0, 0], [1, 2, 3]], atol=1e-10
    )
    assert scene["points_per_frame"] == [2, 2]
    assert scene["pose_source"] == "supplied"
    assert (tmp_path / "output/1/world.npy").read_bytes() == before
    assert (tmp_path / "debug/scene_world.png").is_file()
    assert (tmp_path / "debug/camera_positions.png").is_file()
    assert (
        json.loads((tmp_path / "debug/scene.json").read_text())["world_id"] == "known"
    )


def test_one_empty_and_incompatible_origins(tmp_path):
    frames = saved_frames(tmp_path, [[1, 2, 3]])
    np.testing.assert_equal(
        review.export_scene(tmp_path, frames)["relative_centres_mm"], [[0, 0, 0]]
    )
    with pytest.raises(ValueError, match="empty"):
        review.export_scene(tmp_path, [])
    observation = tmp_path / "input/1/observation.json"
    data = json.loads(observation.read_text())
    data["pose"]["source"] = "estimated"
    observation.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="supplied"):
        review.export_scene(tmp_path, frames)


def test_rejects_mixed_origins(tmp_path):
    frames = saved_frames(tmp_path, [[0, 0, 0], [1, 0, 0]])
    observation = tmp_path / "input/2/observation.json"
    data = json.loads(observation.read_text())
    data["pose"]["segment_id"] = "reset"
    observation.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="origins"):
        review.export_scene(tmp_path, frames)


def test_explanations_and_links(tmp_path):
    frames = saved_frames(tmp_path, [[1, 0, 0]])
    for name in (
        "depth.png",
        "mask.png",
        "camera_cloud.png",
        "world_cloud.png",
        "model_cloud.png",
        "projection_error.png",
    ):
        frames[0]["artifacts"]["visualizations"].append(name)
        (tmp_path / "debug/1").mkdir(parents=True, exist_ok=True)
        (tmp_path / f"debug/1/{name}").write_bytes(b"link fixture")
    for name in ("legends.json",):
        (tmp_path / f"debug/1/{name}").write_text("{}")
    (tmp_path / "output/1/stages.json").write_text("{}")
    (tmp_path / "metadata").mkdir()
    (tmp_path / "metadata/status.json").write_text('{"status":"running"}')
    review.export_scene(tmp_path, frames)
    review.build_review(tmp_path, frames)
    content = (tmp_path / "review.html").read_text(encoding="utf-8")
    for phrase in (
        "Supplied depth",
        "Supplied camera poses",
        "No tracking",
        "Depth prediction accuracy",
        "Not measured",
        "Projection consistency",
        "reference coordinate",
        "5000",
        "millimetres",
    ):
        assert phrase in content

    class Links(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key in {"href", "src"}:
                    assert (tmp_path / value).is_file(), value

    Links().feed(content)
    assert "adjacent cameras" not in content
    assert "only a few millimetres" not in content


@pytest.mark.parametrize(
    "bad", [np.full((2, 3), np.nan), np.zeros((1, 3)), np.zeros((2, 4))]
)
def test_rejects_invalid_world_arrays(tmp_path, bad):
    frames = saved_frames(tmp_path, [[0, 0, 0]])
    np.save(tmp_path / "output/1/world.npy", bad)
    with pytest.raises(ValueError, match="correspondence"):
        review.export_scene(tmp_path, frames)


def test_empty_cloud_and_wrong_pose_units(tmp_path):
    frames = saved_frames(tmp_path, [[0, 0, 0]])
    frames[0]["valid_pixels"] = 0
    np.save(tmp_path / "output/1/world.npy", np.empty((0, 3)))
    assert review.export_scene(tmp_path, frames)["points_per_frame"] == [0]
    observation = tmp_path / "input/1/observation.json"
    data = json.loads(observation.read_text())
    data["pose"]["units"] = "millimetres"
    observation.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="metres"):
        review.export_scene(tmp_path, frames)
