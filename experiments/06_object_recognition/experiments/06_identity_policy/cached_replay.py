"""Reassign saved object proposals on CPU and publish an audited identity overlay."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import math
import shutil
import time
from collections import Counter
from pathlib import Path

from experiments.datasets.acquisition import sha256
from experiments.shared.runs import Run, verify_run, write_json

replay = importlib.import_module("experiments.06_object_recognition.pilot.replay")
ROOT = Path(__file__).resolve().parents[4]
RUNS_RELATIVE = Path(
    "experiments/06_object_recognition/experiments/06_identity_policy/runs"
)
DEFAULT_SOURCE_RELATIVE = Path(
    "experiments/06_object_recognition/experiments/05_replay/runs/"
    "20261004T152704.023370Z_84abb8b3b9594dcea8a1e5b2c8aced66"
)
DEFAULT_LEDGER_SHA256 = (
    "fe4a35b0f9ebf0542bc4573afe995b0174a277c7f609d67298982314d6d66a8f"
)
DEFAULT_MANIFEST_SHA256 = (
    "fd7a7cce28fad27a0eb8af5b81a96f7aa613e825b2fbe8dfacf4191d5939254f"
)
HYPERPARAMETERS: dict[str, dict[str, object]] = {
    "association_max_distance_m": {
        "value": 0.35,
        "source": "inherited experiments/06_object_recognition/pilot/replay.py:38",
    },
    "ambiguity_margin_m": {
        "value": 0.05,
        "source": "inherited experiments/06_object_recognition/pilot/replay.py:39",
    },
    "assignment": {
        "value": "same class; maximum cardinality then minimum distance; retain all tracks",
        "source": "inherited experiments/06_object_recognition/pilot/replay.py:127",
    },
    "birth_policy": {
        "value": "valid position without a feasible candidate starts a provisional ID at any frame",
        "source": "confirmed 2026-10-05: owner requested late object births",
    },
    "inputs": {
        "value": "all source frames and proposals; reuse recorded world positions without inference",
        "source": "inherited Task22 accepted baseline_observations.json",
    },
}
ASSOCIATION_FIELDS = {
    "association",
    "object_id",
    "coordinate_delta_m",
    "association_distance_m",
    "identity_state",
    "observation_id",
}
DERIVED_LEDGER_FIELDS = {
    "frames",
    "tracks",
    "counts",
    "source",
    "hyperparameters",
    "policy_report",
}
DERIVED_FRAME_FIELDS = {"detections", "tracks", "failures"}


def _without(data: dict, excluded: set[str]) -> dict:
    return {key: value for key, value in data.items() if key not in excluded}


def validate_overlay(baseline: dict, corrected: dict) -> None:
    """Reject edits to recorded proposals, frame order, geometry or settings."""
    if not isinstance(baseline, dict) or not isinstance(corrected, dict):
        raise ValueError(  # noqa: TRY004 - schema validation
            "Overlay immutable content must be dictionaries"
        )
    if _without(baseline, DERIVED_LEDGER_FIELDS) != _without(
        corrected, DERIVED_LEDGER_FIELDS
    ):
        raise ValueError("Overlay changed immutable context or settings")
    original_frames, new_frames = baseline.get("frames"), corrected.get("frames")
    if (
        not isinstance(original_frames, list)
        or not isinstance(new_frames, list)
        or len(original_frames) != len(new_frames)
    ):
        raise ValueError("Overlay changed immutable frame order or count")
    for original, new in zip(original_frames, new_frames, strict=True):
        if (
            not isinstance(original, dict)
            or not isinstance(new, dict)
            or _without(original, DERIVED_FRAME_FIELDS)
            != _without(new, DERIVED_FRAME_FIELDS)
        ):
            raise ValueError("Overlay changed immutable frame content")
        proposals, updated = original.get("detections"), new.get("detections")
        if (
            not isinstance(proposals, list)
            or not isinstance(updated, list)
            or len(proposals) != len(updated)
        ):
            raise ValueError("Overlay changed immutable proposal count")
        for proposal, correction in zip(proposals, updated, strict=True):
            if (
                not isinstance(proposal, dict)
                or not isinstance(correction, dict)
                or _without(proposal, ASSOCIATION_FIELDS)
                != _without(correction, ASSOCIATION_FIELDS)
            ):
                raise ValueError("Overlay changed immutable proposal content or order")
    _validate_counts(corrected)


def _validate_counts(corrected: dict) -> None:
    """Require numeric totals that agree with the rendered records and tracks."""
    counts = corrected.get("counts")
    expected = _summary(corrected)["counts"]
    if (
        not isinstance(counts, dict)
        or set(counts) != set(expected)
        or any(type(value) is not int or value < 0 for value in counts.values())
        or counts != expected
    ):
        raise ValueError("Overlay counts must be nonnegative integers matching records")
    tracks = corrected.get("tracks")
    if not isinstance(tracks, dict) or counts["object_ids"] != len(tracks):
        raise ValueError("Overlay object counts differ from track snapshot")


def _validate_ledger(ledger: dict, source_hash: str) -> None:
    if (
        not isinstance(source_hash, str)
        or len(source_hash) != 64
        or any(character not in "0123456789abcdef" for character in source_hash)
    ):
        raise ValueError("Source hash must be a lowercase SHA-256 digest")
    required = {
        "world_id",
        "segment_id",
        "position_method",
        "frames",
        "association_max_distance_m",
        "ambiguity_margin_m",
    }
    if (
        not isinstance(ledger, dict)
        or not required.issubset(ledger)
        or not isinstance(ledger["frames"], list)
    ):
        raise ValueError(
            "Source ledger must contain context, settings and a frame list"
        )
    for setting in ("association_max_distance_m", "ambiguity_margin_m"):
        value = ledger[setting]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value != HYPERPARAMETERS[setting]["value"]
        ):
            raise ValueError(f"Source setting {setting} differs from inherited policy")
    for index, frame in enumerate(ledger["frames"]):
        _validate_frame(frame, index)


def _validate_frame(frame: dict, index: int) -> None:
    if (
        not isinstance(frame, dict)
        or type(frame.get("frame_index")) is not int
        or frame["frame_index"] != index
        or not isinstance(frame.get("detections"), list)
    ):
        raise ValueError(
            "Source frames must have ordered integer indexes and proposal lists"
        )
    required = {"class_id", "label", "world_position_m", "association"}
    for proposal_index, proposal in enumerate(frame["detections"]):
        if not isinstance(proposal, dict) or not required.issubset(proposal):
            raise ValueError(
                "Source proposals must contain class, position and original decision fields"
            )
        if (
            type(proposal.get("detection_index")) is not int
            or proposal["detection_index"] != proposal_index
            or type(proposal.get("frame_index")) is not int
            or proposal["frame_index"] != index
            or type(proposal["class_id"]) is not int
            or proposal["class_id"] < 0
            or not isinstance(proposal["label"], str)
            or not proposal["label"]
            or not isinstance(proposal["association"], str)
            or not proposal["association"]
            or (
                proposal.get("object_id") is not None
                and not isinstance(proposal["object_id"], str)
            )
        ):
            raise ValueError(
                "Source proposals must have ordered integer indexes, class, label and decision fields"
            )


def _summary(ledger: dict) -> dict:
    records = [item for frame in ledger["frames"] for item in frame["detections"]]
    books = [item for item in records if item["class_id"] == 73]

    def counts(items: list[dict]) -> dict:
        return {
            "detections": len(items),
            "object_ids": len(
                {item["object_id"] for item in items if item.get("object_id")}
            ),
            "unresolved": sum(
                str(item.get("association", "")).startswith("unresolved")
                for item in items
            ),
        }

    return {
        "counts": {"frames": len(ledger["frames"]), **counts(records)},
        "reasons": dict(
            sorted(Counter(item["association"] for item in records).items())
        ),
        "books": {
            **counts(books),
            "reasons": dict(
                sorted(Counter(item["association"] for item in books).items())
            ),
        },
    }


def recompute(ledger: dict, source_hash: str) -> dict:
    """Replay associations without altering or re-estimating recorded geometry."""
    _validate_ledger(ledger, source_hash)
    corrected = copy.deepcopy(ledger)
    tracks: dict[str, dict] = {}
    next_number = 1
    frames = []
    elapsed = 0.0
    for frame in ledger["frames"]:
        proposals = [
            copy.deepcopy(_without(item, ASSOCIATION_FIELDS))
            for item in frame["detections"]
        ]
        started = time.perf_counter()
        assigned, tracks, next_number = replay.associate_frame(
            proposals,
            tracks,
            next_number,
            ledger["association_max_distance_m"],
            ledger["ambiguity_margin_m"],
        )
        elapsed += time.perf_counter() - started
        records = []
        for index, item in enumerate(assigned):
            key = f"{source_hash}:{frame['frame_index']}:{index}".encode("ascii")
            records.append(
                {
                    **item,
                    "observation_id": "observation-" + hashlib.sha256(key).hexdigest(),
                    "identity_state": "provisional" if item["object_id"] else None,
                }
            )
        frames.append(
            {
                **copy.deepcopy(frame),
                "detections": records,
                "tracks": copy.deepcopy(tracks),
                "failures": [
                    {
                        "detection_index": item["detection_index"],
                        "label": item["label"],
                        "association": item["association"],
                    }
                    for item in records
                    if item["association"].startswith("unresolved")
                ],
            }
        )
    corrected = {
        **corrected,
        "frames": frames,
        "tracks": copy.deepcopy(tracks),
        "hyperparameters": copy.deepcopy(HYPERPARAMETERS),
    }
    after = _summary(corrected)
    corrected = {
        **corrected,
        "counts": after["counts"],
        "policy_report": {
            "before": _summary(ledger),
            "after": after,
            "association_elapsed_seconds": elapsed,
            "interpretation": "Policy outcomes and provisional ID counts; no measurement of physical accuracy. Timing covers association only, without inference or geometry.",
        },
    }
    validate_overlay(ledger, corrected)
    return corrected


def _source_receipt(repo: Path, source_run: Path, ledger_path: Path) -> dict:
    verify_run(source_run)
    receipt = {
        "run": source_run.relative_to(repo).as_posix(),
        "manifest_sha256": sha256(source_run / "metadata/manifest.json"),
        "ledger_sha256": sha256(ledger_path),
    }
    if source_run == (repo / DEFAULT_SOURCE_RELATIVE).resolve() and (
        receipt["manifest_sha256"] != DEFAULT_MANIFEST_SHA256
        or receipt["ledger_sha256"] != DEFAULT_LEDGER_SHA256
    ):
        raise ValueError("Default source differs from pinned Task22 receipt")
    return receipt


def execute(repo: Path, source_run: Path) -> Path:
    """Snapshot a verified source and publish to a fresh immutable run directory."""
    repo, source_run = Path(repo).resolve(), Path(source_run).resolve()
    if not source_run.is_relative_to(repo):
        raise ValueError("Source run must be inside the repository")
    baseline_path = source_run / "input/baseline_observations.json"
    ledger_path = (
        baseline_path
        if baseline_path.is_file()
        else source_run / "output/observations.json"
    )
    receipt = _source_receipt(repo, source_run, ledger_path)
    configuration = {
        "operation": "cached association-only replay",
        "source": receipt,
        "hyperparameters": HYPERPARAMETERS,
    }
    with Run(repo / RUNS_RELATIVE, repo, configuration) as run:
        snapshot = run.path / "input/baseline_observations.json"
        shutil.copyfile(ledger_path, snapshot)
        if sha256(snapshot) != receipt["ledger_sha256"]:
            raise ValueError("Source ledger changed during snapshot")
        baseline = json.loads(snapshot.read_text(encoding="utf-8"))
        with run.measure("cached_identity_replay", frames=len(baseline["frames"])):
            corrected = recompute(baseline, receipt["ledger_sha256"])
        corrected = {**corrected, "source": receipt}
        validate_overlay(baseline, corrected)
        write_json(run.path / "output/observations.json", corrected)
        write_json(run.path / "output/policy_report.json", corrected["policy_report"])
        run.set_processed_frames(len(corrected["frames"]))
        if _source_receipt(repo, source_run, ledger_path) != receipt:
            raise ValueError("Source lineage changed during cached replay")
    verify_run(run.path)
    return run.path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-run", type=Path, default=ROOT / DEFAULT_SOURCE_RELATIVE
    )
    arguments = parser.parse_args()
    print(execute(ROOT, arguments.source_run))


if __name__ == "__main__":
    main()
