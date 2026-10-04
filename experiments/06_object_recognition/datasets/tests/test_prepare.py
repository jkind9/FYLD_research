"""Publication controls using tiny synthetic sources, never the recorded dataset."""

import importlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from PIL import Image

from experiments.datasets.acquisition import sha256

prepare = importlib.import_module("experiments.06_object_recognition.datasets.prepare")
ANNOTATIONS = Path(__file__).parents[1] / "desk_smoke_v1.json"


@pytest.fixture
def source(tmp_path):
    manifest = json.loads(ANNOTATIONS.read_text(encoding="utf-8"))
    manifest["provenance"]["review_status"] = "agent_reviewed_with_limits"
    for number, frame in enumerate(manifest["frames"]):
        for role in ("rgb", "depth"):
            item = frame[role]
            target = tmp_path / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            mode, value = (
                ("RGB", (100 + number, 80, 60)) if role == "rgb" else ("I;16", 5000)
            )
            Image.new(mode, (640, 480), value).save(target)
            item["sha256"] = sha256(target)
    for item in manifest["source_records"]:
        target = tmp_path / item["path"]
        target.write_text("synthetic source\n", encoding="utf-8")
        item["sha256"] = sha256(target)
    return manifest, tmp_path


def test_publish_separates_labels_and_preserves_sources(source):
    manifest, repo = source
    before = [sha256(repo / f["rgb"]["path"]) for f in manifest["frames"]]
    destination = repo / "published"
    receipt = prepare.publish(manifest, repo, destination)
    assert receipt["counts"] == {"frames": 6, "instances": 11, "identities": 3}
    inputs = json.loads((destination / "method_inputs.json").read_text())
    assert all("labels" not in frame for frame in inputs["frames"])
    assert "revisits" not in inputs and "provenance" not in inputs
    assert "source_records" not in inputs
    assert [sha256(repo / f["rgb"]["path"]) for f in manifest["frames"]] == before
    assert len(list((destination / "masks").rglob("*.png"))) == 11
    with Image.open(destination / "masks/23/reference-cup.png") as mask:
        assert mask.getpixel((89, 390)) == 255
        assert mask.getpixel((0, 0)) == 0
    assert "provisional" in (destination / "review.html").read_text()
    assert prepare.verify_publication(destination, repo)["status"] == "complete"
    with pytest.raises(FileExistsError):
        prepare.publish(manifest, repo, destination)


@pytest.mark.parametrize(
    "failure", ["tamper", "extra", "escape", "missing", "counts", "incomplete"]
)
def test_publication_rejects_corruption(source, failure):
    manifest, repo = source
    destination = repo / "published"
    prepare.publish(manifest, repo, destination)
    if failure == "tamper":
        (destination / "method_inputs.json").write_text("{}")
    elif failure == "extra":
        (destination / "unexpected.json").write_text("{}")
    elif failure == "missing":
        (destination / "review.html").unlink()
    elif failure == "escape":
        receipt = json.loads((destination / "publication.json").read_text())
        receipt["files"][0]["path"] = "../outside"
        (destination / "publication.json").write_text(json.dumps(receipt))
    else:
        receipt = json.loads((destination / "publication.json").read_text())
        if failure == "counts":
            receipt["counts"]["identities"] = 100
        else:
            receipt["status"] = "incomplete"
        (destination / "publication.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        prepare.verify_publication(destination, repo)


def test_unreviewed_invalid_or_changed_inputs_do_not_publish(source):
    manifest, repo = source
    pending = deepcopy(manifest)
    pending["provenance"]["review_status"] = "pending_agent_review"
    with pytest.raises(ValueError, match="review"):
        prepare.publish(pending, repo, repo / "pending")
    assert not (repo / "pending").exists()
    (repo / manifest["frames"][0]["rgb"]["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError):
        prepare.publish(manifest, repo, repo / "changed")
    assert not (repo / "changed").exists()


def test_destination_must_stay_inside_repo(source, tmp_path):
    manifest, repo = source
    with pytest.raises(ValueError, match="repository"):
        prepare.publish(manifest, repo, tmp_path.parent / "outside")


def test_frame_names_cannot_write_outside_staging(source):
    manifest, repo = source
    manifest["frames"][2]["frame_id"] = "../escape"
    manifest["revisits"][0]["gap_frame_id"] = "../escape"
    with pytest.raises(ValueError, match="filename"):
        prepare.publish(manifest, repo, repo / "unsafe")
    assert not (repo / "unsafe").exists()


def test_nested_receipt_is_an_unindexed_extra(source):
    manifest, repo = source
    destination = repo / "published"
    prepare.publish(manifest, repo, destination)
    (destination / "extra").mkdir()
    (destination / "extra/publication.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        prepare.verify_publication(destination, repo)


def test_mask_paths_do_not_collide_for_valid_ids(source):
    manifest, repo = source
    manifest["frames"] = manifest["frames"][:2]
    manifest["revisits"] = []
    for frame, key, identity in zip(manifest["frames"], ["a_b", "a"], ["c", "b_c"]):
        frame["frame_id"] = key
        frame["labels"] = frame["labels"][:1]
        frame["labels"][0]["instance_id"] = identity
    destination = repo / "published"
    prepare.publish(manifest, repo, destination)
    assert len(list((destination / "masks").rglob("*.png"))) == 2


def test_windows_case_collisions_are_rejected_before_staging(source):
    manifest, repo = source
    manifest["frames"][0]["frame_id"] = "a"
    manifest["frames"][1]["frame_id"] = "A"
    manifest["revisits"] = []
    with pytest.raises(ValueError, match="collision"):
        prepare.publish(manifest, repo, repo / "published")


def test_reindexed_wrong_image_is_not_a_source_copy(source):
    manifest, repo = source
    destination = repo / "published"
    prepare.publish(manifest, repo, destination)
    copy = destination / "rgb/23.png"
    Image.new("RGB", (640, 480), "black").save(copy)
    receipt = json.loads((destination / "publication.json").read_text())
    for item in receipt["files"]:
        if item["path"] == "rgb/23.png":
            item["sha256"] = sha256(copy)
    (destination / "publication.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="original source"):
        prepare.verify_publication(destination, repo)


@pytest.mark.parametrize("name", ["NUL", "con", "PRN", "AUX", "COM1", "LPT9"])
def test_windows_devices_rejected_before_staging(source, name):
    manifest, repo = source
    manifest["frames"][2]["frame_id"] = name
    manifest["revisits"][0]["gap_frame_id"] = name
    with pytest.raises(ValueError, match="reserved"):
        prepare.publish(manifest, repo, repo / "published")
    assert not list(repo.glob(".published.staging_*"))
