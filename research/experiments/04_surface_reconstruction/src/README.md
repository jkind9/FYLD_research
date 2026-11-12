# Surface baseline and its independent scorer

This folder builds a point surface from supplied depth and supplied camera poses, then scores it against a separate reference model. It belongs to [experiment 04, surface reconstruction](../README.md).

The surface is direct point accumulation: every valid depth pixel is placed in the common world and kept, with no fusion, filtering or voxel grid. The scorer is exact: it measures the distance from each surface point to the nearest reference point, and from each reference point to the nearest surface point, with no alignment or scale fitting. The reference never reaches the reconstruction code.

| File | What it does |
|---|---|
| `run.py` | Entry point. `execute(dataset, ids, threshold_m, runs, repo)` reconstructs each frame, scores it, and publishes a run folder with per-frame outputs and metrics. |
| `inspection.py` | Entry point. Rebuilds the same run for a batch of frames, reusing earlier fault-scoring records when `recovery.py` accepts them, and republishes with a review page. |
| `recovery.py` | `validate_prior` and `recover_frame` refuse to reuse a saved score when the inputs, settings or scoring code differ. `combine_summaries` merges records. |
| `backend.py` | `reconstruct(frame, origin)` checks the pose is in the common origin and returns the frame's points. It calls `geometry_validation/src/control.py`. |
| `metric_surface.py` | `reconstruct_metric(depth, valid, calibration, pose)` places valid depth pixels in the world from an estimated camera pose. It is used with a tracker's poses, not the supplied ones. |
| `dataset.py` | Hash-checked copies of ICL-NUIM inputs and `read_reference(path)`, a strict binary reference loader. |
| `evaluation.py` | `SurfaceScorer(reference, threshold_m)`, `DistanceTotals` and `distance_summary` give mean, root-mean-square and maximum distance, share within the threshold, and reference coverage. |
| `export.py` | `export_shard` saves per-frame arrays (depth, mask, pixels, camera, world and model points, colours) and per-pixel diagnostics. |
| `review.py` | `build_review` writes the HTML review of inputs, scores and their limits. |
| `validation/controls.py` | `fault_points(frame, fault)` makes deliberately wrong surfaces (`double_depth`, `inverse_pose`) to check the scorer notices them. |
| `validation/__init__.py` | Public entry to the scorer; re-exports `SurfaceScorer`, `DistanceTotals`, `distance_summary`, `nearest` and `validate_points`. |

`research/evaluation/stage_report/stages/surface.py` re-scores saved runs with `DistanceTotals` and `distance_summary`.

## How to run it

Run from the repository root, CPU only:

```text
.venv/Scripts/python.exe -B -m research.experiments.04_surface_reconstruction.src.run --dataset data/icl_nuim --frame-ids 1 101 201 --threshold-m 0.05
.venv/Scripts/python.exe -B -m research.experiments.04_surface_reconstruction.src.inspection --dataset data/icl_nuim --frame-ids 1 101 201 --threshold-m 0.05 --recover-run <earlier run folder>
```

`--frame-ids` and `--threshold-m` are required; nothing is chosen for you. `--runs` changes where run folders are written. Tests:

```text
.venv/Scripts/python.exe -B tools/check.py -q research/experiments/04_surface_reconstruction/tests
```

## Where results are recorded

Distances, coverage, timings and the nine-view run are in the [experiment 04 README](../README.md). Run folders are in [`../runs/`](../runs).
