# Per-stage accuracy report

This package scores each stage of the pipeline against reference data and puts the results in one report. Two reports can then be compared stage by stage, so a change can be shown to have helped or hurt each step.

## What a report contains

One section per pipeline stage, always in this order: camera path, detection, segmentation, depth support, 3D object position, surface, identity, count. A stage with no scorer or no reference data is still listed, marked unavailable, with the reason.

Each scored section records:

- the run it came from (folder name and the SHA-256 of its completion manifest), and the dataset;
- the reference data used: name, version, file hash, and kind. The kinds are `independent` (measured separately from the method, such as motion capture), `provisional` (checked by an agent or coarse, not reviewed by a person), `analytic` (synthetic, known exactly) and `none`;
- the input mode: `isolated` if the stage was fed correct inputs, so the error is its own, or `chained` if it was fed earlier stages' predictions, so the error includes error passed down;
- every measure with its method name, value, unit, sample count, whether lower or higher is better, and coverage (`complete`, or `subset` when the labels cover only some objects). A value that can't be computed is `null` with a reason. It is never shown as 0.

Per-item evidence (per frame, per box, per object) is written to `output/rows/<stage>.json`, so any summary number can be traced back.

## Comparing two reports

`compare.compare(baseline, candidate)` returns one row per stage, method and measure, with both values, the change and a verdict (`better`, `worse` or `same`). A measure is only compared when both reports used the same dataset, reference file, input mode, coverage and unit, and scored exactly the same items. Each section carries a fingerprint of the items it scored (frames, observations), so two runs over different parts of one recording are never compared. Otherwise the row says which of these differ. Counts with no better direction (for example how many sightings were given any ID, right or wrong) get the verdict `changed`, never `better` or `worse`. No pass or fail limits are applied.

`compare.inherited(isolated, chained)` takes the same stage scored both ways on the same items and splits the result into the stage's own part and the loss passed down from earlier stages. The loss is positive when earlier predictions made the stage worse, whichever direction is better for that measure.

## Stage wrappers

Each wrapper first checks that its run is complete and unchanged (`verify_run`), and optionally that its manifest hash matches a pinned value. It then re-scores the run's saved outputs with the owning experiment's own scorer, and refuses if the result differs from the score the run stored. No model is run again.

| Stage | Wrapper | Owner scorer | Reads |
|---|---|---|---|
| Camera path | `stages/camera.py` | `03_camera_pose_estimation/src/evaluation.py` `evaluate` | `output/poses.json`, `input/evaluation/groundtruth.txt` |
| Detection | `stages/detection.py` | `06_object_recognition/experiments/01_detection/scoring.py` `evaluate` | `input/annotations.json`, `output/cached_proposals.json`, `output/scores.json` |
| Surface | `stages/surface.py` | `04_surface_reconstruction/src/evaluation.py` `DistanceTotals`, `distance_summary` | `output/<frame>/reference_distance.npy` in `metadata/configuration.json` `frame_ids` order, `output/reference_distance.npy` |
| Identity | `stages/identity.py` | `06_object_recognition/experiments/04_geometry_identity/run.py` `_score` | `output/conditions/<condition>/decisions.json`, `input/evaluator_truth.json`, `input/method_observations.json` |

Segmentation, depth support, 3D position and count have no wrapper yet. Tasks 34, 32, 35 and 45 add them.

## Run it

```bash
python -B -m experiments.evaluation.run --runs-root <checkout holding the run folders>
```

Run folders are not in git, so `--runs-root` names the checkout that has them. The command checks each pinned run, builds the report and publishes it as a new verified run under `experiments/evaluation/runs/`, with `output/report.json`, a readable `output/report.md` and the per-item rows.

Tests: `python -B -m pytest experiments/evaluation/tests`. The small fixtures are built in the tests. To also check that the four pinned runs reproduce exactly, set `EVAL_RUNS_ROOT` to the checkout that holds them; without it those tests skip and say why.

## First report, 5 October 2026

The first report combines four earlier runs on three datasets. It is a composite, not one run of the whole pipeline, and its title says so.

| Stage | Source | Result | Reference |
|---|---|---|---|
| Camera path | Task05, TUM freiburg1 xyz, 30 frames | position error 6.93 mm (RMSE) | motion capture, independent |
| Detection | Task18, TUM desk, 6 frames | cups: 4 of 5 found, 0 false, at every overlap cutoff (0.3, 0.5, 0.7) | coarse agent-drawn outlines, provisional |
| Surface | Task04, ICL-NUIM, 9 views | mean distance to reference 7.85 mm; 22.3% of the reference surface covered within 5 cm | published surface, independent |
| Identity | Task21, TUM desk, 11 sightings | 4 of 5 rules match all 11 with no wrong merges or splits; the appearance-only rule leaves 4 unresolved | provisional |
| Segmentation, depth support, 3D position, count | none | unavailable | none yet |

Every number equals the value its own run stored, bit for bit. Report run: `experiments/evaluation/runs/20261005T084939.267589Z_eb6fdf05c67b4cf19da710104a771448` (manifest SHA-256 `0b9d468c…8e81`, report format version 2), generated in the Task 44 worktree. It replaces two earlier reports from the same day in older formats; `compare` refuses reports from another format version.

No stage has yet been scored both with correct inputs and with predicted inputs on the same frames, so the split between a stage's own error and inherited error is so far tested only on synthetic data.

## Complete walkthrough successor, 6 October 2026

[Task56](../../task_list/open/56_benchmark_complete_walkthrough_accuracy_time_and_m.md) owns one complete same-recording test, including phone-compatible inputs, independently scored counts/dimensions/area, full processing time and peak memory. It extends this existing report schema and its comparison/readers for missing stage measures and site area, with an explicit format version. It reuses existing method owners and keeps reference answers outside method inputs. The composite report above remains historical component evidence; no complete walkthrough run is claimed.

## Complete walkthrough ownership

The sole current six-step sequencing lives in [src/walkthrough](../../src/walkthrough/README.md). This package still joins/scorers existing compatible results; Task56 consumes the root runner and owns complete physical-survey adapters and measured time/memory reports. Identity reporting now imports the public experiment validation scorer, with identical historical interpretation. No software fixture here establishes worksite accuracy, total latency or sustained edge acceptance.
