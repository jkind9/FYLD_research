"""Build one per-stage accuracy report from pinned, verified runs (Task 44).

Usage:
    python -B -m experiments.evaluation.run --runs-root <repo holding the run folders>

Run folders are gitignored, so `--runs-root` names the checkout that holds them.
Every run is verified and its manifest hash checked against the pin before any
output is read. The report is published as a new verified run.
"""

import argparse
from pathlib import Path
from typing import Any

from experiments.evaluation import render, schema
from experiments.evaluation.stages import camera, detection, identity, surface
from experiments.shared.runs import Run, write_json

HYPERPARAMETERS = {
    "detection_iou_thresholds": {
        "value": [0.3, 0.5, 0.7],
        "source": "inherited task_list/closed/18_evaluate_object_detection_on_frozen_labelled_obser.md:89",
    },
    "detection_methods": {
        "value": [
            "cached_yolo26x_accepted_task28",
            "empty_prediction_software_control",
        ],
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "identity_conditions": {
        "value": "all five Task21 conditions",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "surface_measures": {
        "value": [
            "accuracy_mean",
            "accuracy_rmse",
            "accuracy_max",
            "within_threshold_fraction",
            "reference_coverage_fraction",
        ],
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "camera_association_tolerance_s": {
        "value": 0.02,
        "source": "inherited experiments/03_camera_pose_estimation/src/evaluation.py:49",
    },
    "surface_reporting_distance_m": {
        "value": 0.05,
        "source": "inherited experiments/04_surface_reconstruction/README.md:100 (read from the run's metrics)",
    },
    "display_format": {
        "value": "4 significant figures; JSON keeps full floats",
        "source": "confirmed 2026-10-05 under owner delegation",
    },
    "pass_fail_limits": {"value": None, "source": "n/a owner has not set limits"},
}

PINNED: dict[str, dict[str, Any]] = {
    "camera_path": {
        "path": "experiments/03_camera_pose_estimation/runs/20261002T164601.734717Z_befb0ccd27ab44daba6d9ac41f9b9ae0",
        "sha256": "3d5e3f6fe69855725e26645e265e62d8a5f0d9f0274523d7721aa87c3174dbd6",
        "dataset": "TUM freiburg1 xyz, 30 frames (Task05)",
        "reference_kind": "independent",
        "wrapper": camera.camera_section,
    },
    "detection": {
        "path": "experiments/06_object_recognition/experiments/01_detection/runs/20261004T071442.158193Z_4be5db5d6dca43e4be715c0665e44fcd",
        "sha256": "7ee60f385871eeb6288c007bc03a548a233a2fee3e6dcf7cca9a5f583a15e39c",
        "dataset": "TUM freiburg1 desk, 6 frames (Task18)",
        "reference_kind": "provisional",
        "wrapper": detection.detection_section,
    },
    "surface": {
        "path": "experiments/04_surface_reconstruction/runs/20261002T145103.184769Z_000165ef2e044376baf54b675172a64e",
        "sha256": "ef35312a41243ed86b5ff5b144afea1012bd54bd7a1aec02f2dbee2871179e7f",
        "dataset": "ICL-NUIM living room, 9 views (Task04)",
        "reference_kind": "independent",
        "wrapper": surface.surface_section,
    },
    "identity": {
        "path": "experiments/06_object_recognition/experiments/04_geometry_identity/runs/20261004T143434.634726Z_33f59456f7d34e50a64020ed6e0613bb",
        "sha256": "75a1b943ab087d846a87d71289b4e118063fad8bac2010694e1521499046d6f7",
        "dataset": "TUM freiburg1 desk, 11 observations (Task21, pending review)",
        "reference_kind": "provisional",
        "wrapper": identity.identity_section,
    },
}
TITLE = (
    "Composite stage report: four pinned runs on three datasets, not one pipeline run"
)


def build(runs_root: Path) -> dict:
    sections = [
        pin["wrapper"](
            runs_root / pin["path"],
            dataset=pin["dataset"],
            pinned_sha256=pin["sha256"],
            reference_kind=pin["reference_kind"],
        )
        for pin in PINNED.values()
    ]
    return schema.build_report(sections, title=TITLE)


def publish(report: dict, repo: Path, output: Path) -> Path:
    configuration = {
        "experiment": "evaluation",
        "hyperparameters": HYPERPARAMETERS,
        "pinned_runs": {
            k: {"path": v["path"], "sha256": v["sha256"]} for k, v in PINNED.items()
        },
    }
    with Run(output, repo, configuration) as run:
        sections = []
        for entry in report["sections"]:
            rows = entry.get("rows", [])
            if rows:
                write_json(run.path / f"output/rows/{entry['stage']}.json", rows)
            sections.append(
                {
                    **entry,
                    "rows": f"output/rows/{entry['stage']}.json" if rows else None,
                }
            )
        write_json(run.path / "output/report.json", {**report, "sections": sections})
        (run.path / "output/report.md").write_text(
            render.table(report), encoding="utf-8"
        )
    return run.path


def main(argv: list[str] | None = None) -> None:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs-root", type=Path, default=repo)
    parser.add_argument(
        "--output", type=Path, default=repo / "experiments/evaluation/runs"
    )
    arguments = parser.parse_args(argv)
    path = publish(build(arguments.runs_root.resolve()), repo, arguments.output)
    print(path)


if __name__ == "__main__":
    main()
