from __future__ import annotations

import hashlib
import importlib

import numpy as np
import pytest

locations = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.locations"
)
revision = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.revision"
)
add, estimate = locations.add, locations.estimate
recompute_generation = revision.recompute_generation
start_explicit_location_generation = revision.start_explicit_location_generation


def test_nearby_views_share_one_vote_and_independent_views_use_coordinate_median(
    observation_factory,
):
    location = None
    for i, (x, camera_x) in enumerate(((0.0, 0.0), (0.02, 0.01), (0.10, 0.20))):
        location, _ = add(
            location,
            observation_factory(f"o{i}", f"f{i}", float(i), x, camera_x=camera_x),
        )
    assert len(location.accepted) == 3
    assert len(location.views) == 2
    assert estimate(location, "viewmedian")[0] == pytest.approx(0.05)
    assert estimate(location, "last")[0] == pytest.approx(0.10)


def test_one_hundred_same_pose_views_add_only_one_position_vote(observation_factory):
    location = None
    for i in range(100):
        location, _ = add(
            location, observation_factory(f"o{i:03d}", f"f{i:03d}", float(i), 0.0)
        )
    assert len(location.accepted) == 100
    assert len(location.views) == 1
    assert estimate(location, "viewmedian") == (0.0, 0.0, 1.0)


def test_duplicate_frame_cannot_add_second_measurement(observation_factory):
    location, _ = add(None, observation_factory("a", "f1", 1.0, 0.0))
    with pytest.raises(ValueError, match="at most one"):
        add(location, observation_factory("b", "f1", 1.0, 0.01))


def test_similarity_is_not_a_position_weight(observation_factory):
    first = observation_factory("a", "f1", 1.0, 0.0, vector=(1, 0))
    second = observation_factory("b", "f2", 2.0, 0.02, vector=(0, 1), camera_x=0.2)
    a, _ = add(None, first)
    b, _ = add(None, {**first, "appearance": second["appearance"]})
    a, _ = add(a, second)
    b, _ = add(b, second)
    assert estimate(a, "viewmedian") == estimate(b, "viewmedian")


def test_synthetic_pose_revision_rebuilds_all_coordinates_but_keeps_ids(
    observation_factory,
):
    obs = [observation_factory("a", "f1", 1.0, 1.0)]
    decisions = [{"observation_id": "a", "decision": "new", "object_id": "stable-id"}]
    transform = np.eye(4)
    transform[0, 3] = 1.0
    updated = recompute_generation(
        obs,
        decisions,
        {
            "f1": {
                "camera_to_world": transform.tolist(),
                "world_id": "w",
                "segment_id": "s",
                "source_sha256": hashlib.sha256(b"revision").hexdigest(),
            }
        },
        "synthetic-v2",
    )
    assert updated["observations"][0]["position_camera_m"] == [1.0, 0.0, 1.0]
    assert updated["observations"][0]["position_world_m"] == [2.0, 0.0, 1.0]
    assert updated["decisions"] == decisions
    assert updated["positions"]["stable-id"]["position_world_m"] == [2.0, 0.0, 1.0]


def test_explicit_relocation_starts_fresh_location_but_retains_previous_history(
    observation_factory,
):
    moved = observation_factory("b", "f2", 2.0, 5.0)
    previous = [{"generation_index": 1, "estimate_m": [0.0, 0.0, 1.0]}]
    result = start_explicit_location_generation(
        "stable-id", "cup", "w", "s", moved, previous
    )
    assert result["location"]["anchor_m"] == [5.0, 0.0, 1.0]
    assert result["previous_generations"] == previous
    assert "explicit external" in result["decision_source"]
