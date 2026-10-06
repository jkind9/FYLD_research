"""Associate frozen object supports using cached appearance and measured depth."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from experiments.shared.runs import Run, verify_run, write_json

from . import inputs
from .association import CONDITIONS, Track, associate_frame
from .locations import estimate
from .persistence import read_generation, write_condition
from .report import write_report
from .validation import score_identity as _score

ROOT = Path(__file__).resolve().parents[4]
RUN_ROOT = Path(__file__).parent / "runs"
HYPERPARAMETERS = {
    "reference": {
        "value": {
            "frames": 6,
            "observations": 11,
            "cup_ids": 1,
            "monitor_ids": 2,
            "enrollment": 4,
            "evaluation": 7,
            "validation": 0,
            "tuning": False,
        },
        "source": "inherited Task17 frozen publication; already inspected within-session sample",
    },
    "appearance": {
        "value": {
            "run": str(inputs.TASK20_RUN_RELATIVE),
            "manifest_sha256": inputs.TASK20_MANIFEST_SHA256,
            "vectors": 11,
            "device": "no inference; cached FP32 vectors",
        },
        "source": "inherited Task20 accepted completion manifest and cache contract",
    },
    "conditions": {
        "value": list(CONDITIONS),
        "source": "confirmed 2026-10-04 bounded comparison",
    },
    "geometry": {
        "value": {
            "units_per_metre": 5000,
            "raw_missing": 0,
            "valid_range_m": [0, 4],
            "calibration": [640, 480, 525, 525, 319.5, 239.5],
            "pixel_centres": True,
            "support": "provisional binary polygon",
            "camera_median_then_world_transform": True,
            "component_quantiles": "NumPy linear",
        },
        "source": "inherited Task17 manifest, experiments/shared/geometry.py, and confirmed support control",
    },
    "pose": {
        "value": {
            "world_id": inputs.WORLD_ID,
            "segment_id": inputs.SEGMENT_ID,
            "time_tolerance_s": inputs.TIME_TOLERANCE_S,
            "revision": "supplied-base-v1",
        },
        "source": "inherited Task17/TUM supplied poses",
    },
    "metric_gate": {
        "value": 0.35,
        "source": "confirmed 2026-10-04 exploratory gate to anchor and current estimate",
    },
    "appearance_gate": {
        "value": 0.80,
        "source": "confirmed 2026-10-04 exploratory gate, no tuning",
    },
    "combined_cost": {
        "value": {
            "geometry_weight": 0.5,
            "appearance_weight": 0.5,
            "alternative_gap": 0.05,
        },
        "source": "confirmed 2026-10-04 exploratory association policy",
    },
    "costs": {
        "value": {
            "geometry": "distance/current_gate",
            "appearance": "(1-cosine)/2",
            "comparison": "maximum cardinality, minimum total cost",
            "numeric_tolerance": 1e-12,
        },
        "source": "confirmed 2026-10-04 exploratory dimensionless costs",
    },
    "origin_policy": {
        "value": "session/world/segment must match; unknown origin stays outside metric identities",
        "source": "inherited IdentityStore and confirmed unresolved-origin mapping",
    },
    "duplicates": {
        "value": {
            "same_class_iou_min": 0.90,
            "world_distance_max_m": 0.02,
            "winner": None,
        },
        "source": "confirmed 2026-10-04 conservative duplicate control",
    },
    "view_groups": {
        "value": {"translation_max_m": 0.05, "rotation_max_deg": 10, "frame_votes": 1},
        "source": "confirmed 2026-10-04 correlated-view cap",
    },
    "birth": {
        "value": "first usable frame per class seeds all valid nonduplicates; later unmatched same-class stays pending",
        "source": "confirmed 2026-10-04 conservative birth policy",
    },
    "location": {
        "value": "fixed generation anchor; surface camera median transformed to world; representative median or last; no similarity/confidence weighting; no automatic relocation",
        "source": "confirmed 2026-10-04 coordinate clarification",
    },
    "spread": {
        "value": "coordinate min/max/IQR, radial spread and estimate shifts; no covariance or centre-error claim",
        "source": "confirmed 2026-10-04 descriptive report",
    },
    "revision": {
        "value": "full generation recomputation from camera coordinates; stable IDs and decisions; synthetic relocation only",
        "source": "confirmed 2026-10-04; real correction remains Task25/Task13",
    },
    "ordering_ids": {
        "value": "timestamp then opaque observation key; UUID5 schema/condition/session/origin/first key; exact evidence replay required",
        "source": "confirmed 2026-10-04 deterministic replay",
    },
    "execution": {
        "value": "one serial CPU writer; fresh run; no overwrite; immutable completed-run reader",
        "source": "inherited experiments/shared/runs.py and confirmed publication contract",
    },
    "runtime": {
        "value": {
            "numpy": "2.4.2",
            "pillow": "12.3.0",
            "scipy": "1.17.1",
            "opencv": None,
            "torch": None,
        },
        "source": "inherited shared runtime; no detector/model import execution or GPU forwards",
    },
    "resource": {
        "value": {
            "frames": 6,
            "observations": 11,
            "conditions": 5,
            "gpu_forwards": 0,
            "models_loaded": 0,
        },
        "source": "confirmed 2026-10-04 efficient bounded trial",
    },
}


def _origin(row: dict) -> tuple[str | None, str | None]:
    return row.get("world_id"), row.get("segment_id")


def _run_condition(
    observations: list[dict], condition: str, frames: list[dict]
) -> tuple[list[dict], list[dict], list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in observations:
        groups[row["frame_id"]].append(row)
    frame_by_id = {row["frame_id"]: row for row in frames}
    if not set(groups).issubset(frame_by_id):
        raise ValueError(
            "An observation references a frame outside the frozen source list"
        )
    tracks: tuple[Track, ...] = ()
    ledger: list[dict] = []
    history: list[dict] = []
    for frame in sorted(
        frames, key=lambda row: (float(row["timestamp_s"]), row["frame_id"])
    ):
        frame_id = frame["frame_id"]
        frame_rows = groups.get(frame_id, [])
        if frame_rows:
            tracks, decisions, state = associate_frame(frame_rows, tracks, condition)
        else:
            decisions = []
            state = [
                {
                    "object_id": track.object_id,
                    "category": track.category,
                    "session_id": track.session_id,
                    "world_id": track.world_id,
                    "segment_id": track.segment_id,
                    "location": {
                        "anchor_m": list(track.location.anchor_m),
                        "estimate_m": list(
                            estimate(
                                track.location,
                                "last" if condition.endswith("last") else "viewmedian",
                            )
                        ),
                        "last_m": list(track.location.last_m),
                        "view_median_m": list(estimate(track.location, "viewmedian")),
                        "accepted_count": len(track.location.accepted),
                        "representative_count": len(track.location.views),
                        "claim": "No observation in this frame; stored position and vote count carried unchanged.",
                    },
                    "gallery_observations": [key for key, _ in track.gallery],
                }
                for track in tracks
                if track.location is not None
            ]
        ledger.extend(decisions)
        history.append(
            {
                "frame_id": frame_id,
                "timestamp_s": float(frame["timestamp_s"]),
                "observations": decisions,
                "no_observation": not frame_rows,
                "tracks": state,
            }
        )
    return (
        ledger,
        [
            {
                "object_id": track.object_id,
                "category": track.category,
                "session_id": track.session_id,
                "world_id": track.world_id,
                "segment_id": track.segment_id,
                "anchor_m": list(track.location.anchor_m) if track.location else None,
                "last_m": list(track.location.last_m) if track.location else None,
                "representatives": (
                    [view.observation_id for view in track.location.views]
                    if track.location
                    else []
                ),
                "accepted": (
                    [view.observation_id for view in track.location.accepted]
                    if track.location
                    else []
                ),
                "gallery": [key for key, _ in track.gallery],
            }
            for track in tracks
        ],
        history,
    )


def run_evaluation(repo: Path = ROOT, output: Path | None = None) -> Path:
    destination = inputs.output_root(repo, output or RUN_ROOT)
    manifest, cache_path, publication_receipt = inputs.preflight(repo)
    for parent in (repo / "data", repo / "checkpoints"):
        if not parent.exists():
            raise ValueError(f"Required frozen input tree is missing: {parent}")
    configuration = {
        "hyperparameters": HYPERPARAMETERS,
        "source_annotation_sha256": inputs.ORIGINAL_SHA256,
        "published_annotation_sha256": inputs.PUBLISHED_SHA256,
        "task20_manifest_sha256": inputs.TASK20_MANIFEST_SHA256,
        "conditions": list(CONDITIONS),
        "revision_id": "supplied-base-v1",
        "synthetic_control": False,
    }
    with Run(destination, repo, configuration) as run:
        observations, truth, provenance = inputs.collect(
            run, repo, manifest, cache_path, publication_receipt
        )
        if (
            len(observations) != 11
            or len({row["observation_id"] for row in observations}) != 11
        ):
            raise ValueError(
                "Frozen method input must contain exactly eleven unique observations"
            )
        write_json(run.path / "input/method_observations.json", observations)
        write_json(run.path / "input/evaluator_truth.json", truth)
        write_json(run.path / "input/source_receipt.json", provenance)
        all_results = {}
        all_history = {}
        recorded_frames = provenance["frame_sources"]
        if len(recorded_frames) != len(manifest["frames"]):
            raise ValueError("Every selected source frame must have a checked receipt")
        for condition in CONDITIONS:
            ledger, tracks, history = _run_condition(
                observations, condition, recorded_frames
            )
            all_history[condition] = history
            settings = {"condition": condition, "hyperparameters": HYPERPARAMETERS}
            generation = write_condition(
                run.path, condition, observations, ledger, tracks, settings=settings
            )
            all_results[condition] = {
                "generation": generation,
                "score": _score(ledger, truth, observations),
            }
        write_json(run.path / "output/frame_history.json", all_history)
        write_json(
            run.path / "output/summary.json",
            {
                "schema_version": 1,
                "claim": "descriptive association on previously inspected provisional supports; no blind accuracy, calibrated gate or object-centre error",
                "source_observations": len(observations),
                "conditions": all_results,
                "gpu_forwards": 0,
                "appearance_vectors_reused": len(observations),
                "hyperparameters": HYPERPARAMETERS,
                "unavailable_geometry": sum(
                    row.get("position_world_m") is None for row in observations
                ),
                "origin_merge_count": sum(
                    len(row["score"]["wrong_merge_object_ids"])
                    for row in all_results.values()
                ),
            },
        )
        write_json(
            run.path / "output/pose_revisions.json",
            {
                "schema_version": 1,
                "revision_id": "supplied-base-v1",
                "records": provenance["frame_sources"],
                "revisions": "Original camera coordinates retained; revision rebuild helper is a synthetic software control.",
            },
        )
        write_report(run.path)
        # Recheck all original inputs and cached artifact before the completion manifest is made.
        fresh_manifest, fresh_cache, fresh_receipt = inputs.preflight(repo)
        if (
            fresh_manifest != manifest
            or fresh_cache != cache_path
            or fresh_receipt != publication_receipt
        ):
            raise ValueError("Frozen input references changed during the trial")
    verify_run(run.path)
    for condition in CONDITIONS:
        read_generation(run.path, condition)
    return run.path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(json.dumps({"run": str(run_evaluation(output=args.output))}))


if __name__ == "__main__":
    main()
