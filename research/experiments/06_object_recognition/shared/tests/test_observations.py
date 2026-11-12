"""Stage contracts reject invented geometry and preserve immutable evidence."""

import importlib
from dataclasses import FrozenInstanceError, replace

import numpy as np
import pytest

from experiments.shared.contracts import Calibration, Pose

observations = importlib.import_module(
    "experiments.06_object_recognition.shared.observations"
)
revisions = importlib.import_module(
    "experiments.06_object_recognition.shared.pose_revisions"
)
ObjectObservation = observations.ObjectObservation
PoseRevision = revisions.PoseRevision
HASH = "a" * 64
CALIBRATION = Calibration(8, 6, 5, 5, 3.5, 2.5, "x-right_y-down_z-forward")


def observation(**changes):
    values = {
        "source_id": "camera",
        "session_id": "desk",
        "frame_id": "frame",
        "observation_id": "o1",
        "timestamp_s": 1.0,
        "calibration": CALIBRATION,
        "polygon": ((1, 1), (4, 1), (4, 4), (1, 4)),
        "bbox_xyxy": (1, 1, 4, 4),
        "source_hashes": (("rgb", HASH),),
        "depth_available": False,
        "method_provenance": (("method", "fixture"),),
    }
    return ObjectObservation(**{**values, **changes})


def revision(**changes):
    values = {
        "run_id": "run",
        "frame_id": "frame",
        "revision_id": "r0",
        "pose": Pose(np.eye(4), "world", "segment", "supplied"),
        "source_sha256": HASH,
        "parent_revision_id": None,
        "provenance": (("method", "fixture"),),
    }
    return PoseRevision(**{**values, **changes})


def test_observation_copies_nested_inputs_and_rejects_assignment():
    polygon = [[1, 1], [4, 1], [4, 4], [1, 4]]
    item = observation(polygon=polygon)
    polygon[0][0] = 7
    assert item.polygon[0] == (1, 1)
    with pytest.raises(FrozenInstanceError):
        item.frame_id = "changed"
    assert item.to_dict()["position_camera_m"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"timestamp_s": float("nan")},
        {"source_id": ""},
        {"bbox_xyxy": (1, 1, 1, 4)},
        {"bbox_xyxy": (-1, 1, 4, 4)},
        {"polygon": ((1, 1), (2, 2), (3, 3))},
        {"polygon": ((1, 1), (float("inf"), 1), (4, 4))},
        {"polygon": ((1, 1), (9, 1), (4, 4))},
        {"polygon": ((1, 1), (5, 1), (4, 4))},
        {"source_hashes": (("rgb", "bad"),)},
        {"source_hashes": (("rgb", HASH), ("rgb", HASH))},
        {"method_provenance": (("method", "a"), ("method", "b"))},
        {"position_camera_m": (0, 0, 1)},
        {"depth_available": True, "position_camera_m": (0, 0, float("nan"))},
        {"depth_available": True, "position_camera_m": (0, 0, -1)},
        {"depth_available": True, "position_world_m": (1, 2, 3)},
        {"world_id": "world"},
        {"depth_available": "yes"},
    ],
)
def test_observation_invalid_inputs(changes):
    with pytest.raises(ValueError):
        observation(**changes)


def test_metric_observation_and_duplicate_identity_validation():
    item = observation(
        depth_available=True,
        position_camera_m=(0, 0, 1),
        position_world_m=(1, 2, 3),
        world_id="world",
        segment_id="segment",
        pose_revision_id="r0",
    )
    assert item.to_dict()["position_world_m"] == [1, 2, 3]
    observations.validate_observations([item, replace(item, observation_id="o2")])
    with pytest.raises(ValueError, match="Duplicate"):
        observations.validate_observations([item, item])


@pytest.mark.parametrize(
    "changes",
    [
        {"calibration": Calibration(True, 6, 5, 5, 0, 0, "x-right_y-down_z-forward")},
        {"calibration": "not calibration"},
        {"polygon": None},
        {"polygon": [1, 2, 3]},
        {"polygon": [[1, 1], [4, 1]]},
        {"position_camera_m": [0, 1], "depth_available": True},
        {"source_hashes": ()},
        {"method_provenance": (("method", ""),)},
    ],
)
def test_observation_rejects_malformed_support_and_metadata(changes):
    with pytest.raises(ValueError):
        observation(**changes)


def test_pose_revision_preserves_pose_and_parent_chain():
    first = revision()
    second = revision(revision_id="r1", parent_revision_id="r0")
    revisions.validate_pose_revisions([second, first])
    assert first.key == ("run", "world", "segment", "frame", "r0")
    assert first.to_dict()["direction"] == "camera_to_world"
    assert first.to_dict()["units"] == "metres"
    with pytest.raises(ValueError):
        first.pose.matrix[0, 0] = 2


@pytest.mark.parametrize(
    "changes",
    [
        {"run_id": ""},
        {"source_sha256": "bad"},
        {"units": "centimetres"},
        {"direction": "world_to_camera"},
        {"parent_revision_id": "r0"},
        {"provenance": ()},
        {"provenance": (("m", "a"), ("m", "b"))},
    ],
)
def test_pose_revision_invalid_fields(changes):
    with pytest.raises(ValueError):
        revision(**changes)


def test_pose_rejects_improper_matrix():
    matrix = np.eye(4)
    matrix[0, 0] = -1
    with pytest.raises(ValueError):
        revision(pose=Pose(matrix, "world", "segment", "supplied"))


@pytest.mark.parametrize(
    "kind", ["missing", "other_frame", "other_origin", "cycle", "roots", "duplicate"]
)
def test_revision_collection_rejects_invalid_parentage(kind):
    first = revision()
    second = revision(revision_id="r1", parent_revision_id="r0")
    records = [first, second]
    if kind == "missing":
        records = [second]
    elif kind == "other_frame":
        records = [first, replace(second, frame_id="different")]
    elif kind == "other_origin":
        records = [
            first,
            replace(second, pose=Pose(np.eye(4), "other", "segment", "supplied")),
        ]
    elif kind == "cycle":
        records = [replace(first, parent_revision_id="r1"), second]
    elif kind == "roots":
        records = [first, replace(second, parent_revision_id=None)]
    elif kind == "duplicate":
        records = [first, first]
    with pytest.raises(ValueError):
        revisions.validate_pose_revisions(records)


def test_revision_cycle_with_an_independent_root_is_rejected():
    with pytest.raises(ValueError, match="cycle"):
        revisions.validate_pose_revisions(
            [
                revision(),
                revision(revision_id="r1", parent_revision_id="r2"),
                revision(revision_id="r2", parent_revision_id="r1"),
            ]
        )


def test_revision_parent_cannot_cross_run_and_pose_type_is_checked():
    with pytest.raises(ValueError):
        revisions.validate_pose_revisions(
            [
                revision(),
                revision(run_id="other", revision_id="r1", parent_revision_id="r0"),
            ]
        )
    with pytest.raises(ValueError):
        revision(pose=np.eye(4))
