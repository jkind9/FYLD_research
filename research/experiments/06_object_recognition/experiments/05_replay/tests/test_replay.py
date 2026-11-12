"""Contract checks for Task22's frozen joins and class-instance inventory."""

import importlib
from pathlib import Path

checked_inputs = importlib.import_module(
    "experiments.06_object_recognition.experiments.05_replay.checked_inputs"
)
generation = importlib.import_module(
    "experiments.06_object_recognition.experiments.05_replay.generation"
)


def test_output_preflight_uses_the_requested_repository():
    repo = Path("C:/task22-output-preflight-fixture")
    generation._preflight_output(repo)
    assert (repo / generation.RUN_ROOT_RELATIVE).is_relative_to(repo)


def test_verified_inputs_keep_sixty_frames_and_exact_automatic_proposals():
    data = checked_inputs.load(Path(__file__).resolve().parents[5])
    assert len(data["baseline_rows"]) == 60
    assert [frame["frame_id"] for frame in data["proposal_frames"]] == [
        "23",
        "104",
        "268",
        "359",
        "405",
        "560",
    ]
    proposals = [
        row
        for frame in data["proposal_frames"]
        for row in frame["proposals"]
        if row["class_id"] in checked_inputs.CLASSES
    ]
    assert len(proposals) == 17
    assert sum(row["class_id"] == 41 for row in proposals) == 4
    assert sum(row["class_id"] == 62 for row in proposals) == 13


def test_same_class_instances_in_one_frame_keep_distinct_observation_keys():
    data = checked_inputs.load(Path(__file__).resolve().parents[5])
    frame = data["proposal_frames"][0]
    same_class = [row for row in frame["proposals"] if row["class_id"] == 62]
    assert len(same_class) == 5
    assert len({tuple(row["xyxy"]) for row in same_class}) == 5


def test_accepted_actual_box_embeddings_reuse_cuda_receipt_without_inference():
    repo = Path(__file__).resolve().parents[5]
    sources = checked_inputs.load(repo)
    automatic, provenance = generation._read_accepted_feature_cache(repo, sources)
    assert provenance["manifest_sha256"] == generation.FEATURE_CACHE_MANIFEST_SHA256
    assert automatic["feature_receipt"]["actual_device"] == "cuda:0"
    assert automatic["feature_receipt"]["actual_fp16"] is False
    assert automatic["feature_receipt"]["requested_embedding_count"] == 17
    for frames in automatic["conditions"].values():
        by_index = {frame["frame_index"]: frame for frame in frames}
        cup_before = next(
            row for row in by_index[9]["observations"] if row["category"] == "cup"
        )
        cup_after = next(
            row for row in by_index[37]["observations"] if row["category"] == "cup"
        )
        assert cup_before["object_id"] == cup_after["object_id"]
        retained = next(
            row
            for row in by_index[27]["tracks"]
            if row["object_id"] == cup_before["object_id"]
        )
        assert retained["last_frame_id"] == "104"
