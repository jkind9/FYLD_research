---
id: "44"
title: Build a per-stage accuracy log for end-to-end runs
status: open
priority: HIGH
type: infra
approval_status: proposed 2026-10-05 by owner request; owner delegated settings on 2026-10-05
blocked_by: []
blocks: []
verification_test: experiments/evaluation/tests/test_stage_report.py
plan_reviewed: 2026-10-05 PASS
files:
  - experiments/evaluation/**
  - pytest.ini
  - tools/check.py
docs:
  - experiments/evaluation/README.md
  - experiments/README.md
  - task_list/README.md
baseline_metric:
  source: "task_list/README.md (board) and owning task receipts 05, 18, 04, 21"
  field: "pipeline stages reported in one per-run log scored against reference data"
  baseline_value: "0 of 8 stages in a common log; 4 stages scored only inside separate experiment folders"
  target: "8 of 8 stages present in one composite report from pinned runs; each either scored or marked unavailable with a reason"
created: 2026-10-05
last_updated: 2026-10-05
superseded_by: null
---

# Task 44: Build a per-stage accuracy log for end-to-end runs

## In plain English

When the whole system runs on a test recording, we want one report that says how accurate each step was compared with the known correct answers. The steps are: where the camera was, which objects were found, their outlines, their depth, their 3D position, the map surface, whether repeat sightings were matched to the same object, and the final count. The report should also say how much of each step's error came from the steps before it. Two reports can then be compared side by side, so a change can be shown to have helped or hurt each step.

## What

Add `experiments/evaluation/`, a small shared package that:

1. **Defines one stage report format** (version 1, JSON plus a readable table, published under `experiments/evaluation/runs/`). One section per stage: camera path, detection, segmentation, depth support, 3D object position, surface, identity, count. Each section records:
   - the evaluated run's ID and completion-manifest SHA-256, plus the dataset and sequence it ran on;
   - the reference used: ID, version, file hash and kind (`independent`, `provisional`, `analytic` or `none`);
   - each measure as method key, name, value, unit, sample count and **coverage** (`complete` or `subset`, per measure, because one detection section can hold a complete cup measure and a subset monitor measure), or `null` with a stated reason;
   - a path to the per-item rows so any summary number can be traced back;
   - **input mode**: `isolated` (inputs came from the reference, so the error is the stage's own) or `chained` (inputs came from earlier stages' predictions, so the error includes inherited error).
2. **Wraps the existing scorers** without changing their maths. Digit-prefixed experiment modules are loaded lazily with `importlib.import_module` and their dotted paths, as experiments/06_object_recognition/experiments/04_geometry_identity/tests/test_run.py:10-12 already does. No owner file is edited.
   - **Camera path:** rebuild records from `output/poses.json`, score with layer 3 `evaluate` against `input/evaluation/groundtruth.txt`. Measures: position RMSE (m) and per-frame position error.
   - **Detection:** layer 6 detection `evaluate` on `input/annotations.json` and `output/cached_proposals.json`. Method keys reported: `cached_yolo26x_accepted_task28` and `empty_prediction_software_control`, each with matched, missed, false detections, precision and recall per category and IoU threshold.
   - **Surface:** replay `DistanceTotals.add` over each `output/<frame>/reference_distance.npy` in `metadata/configuration.json` `frame_ids` order (the published path through `SurfaceScorer.summary`), and `distance_summary` over `output/reference_distance.npy` for the reference side. Measures: accuracy mean, RMSE and max (m), within-0.05 m fraction of reconstructed points, reference coverage fraction.
   - **Identity:** `_score` on each condition's `output/conditions/<c>/decisions.json`, `input/evaluator_truth.json` and `input/method_observations.json`. All five conditions are reported as separate method keys (matched, unresolved, false merges, false splits).
   Segmentation, depth support, 3D position and count start as registered stages with `null` measures and the reason "no reference or scorer yet". Tasks 34, 32, 35 and 45 add their measures here instead of each inventing a format.
3. **Compares two reports** (`compare(baseline, candidate)`). Per measure: both values, the change, and whether lower or higher is better. It refuses a measure when the two reports differ in reference hash, coverage, input mode, method key or dataset, and says which. It sets no pass/fail limits.
4. **Splits own error from inherited error.** For a measure present in both `isolated` and `chained` mode on the same frames, the report gives both and their difference. In this slice no accepted run has a stage in both modes (Task04 and Task21 used supplied poses), so the split is proved only by a synthetic fixture; real pairs arrive with Tasks 45, 34 and 35.

**The first report is a composite, not one pipeline run.** It assembles four accepted runs on three datasets, and each section names its dataset so nobody reads it as an end-to-end result:

| Stage | Run (pinned) | Manifest SHA-256 | Dataset | Reference kind |
|---|---|---|---|---|
| Camera path | Task05 `03_camera_pose_estimation/runs/20261002T164601.734717Z_befb0ccd27ab44daba6d9ac41f9b9ae0` | 3d5e3f6f…dbd6 | TUM freiburg1 xyz, 30 frames | independent (motion capture) |
| Detection | Task18 `01_detection/runs/20261004T071442.158193Z_4be5db5d6dca43e4be715c0665e44fcd` | 7ee60f38…e39c | TUM freiburg1 desk, 6 frames | provisional (Task17 coarse polygons, not human reviewed) |
| Surface | Task04 `04_surface_reconstruction/runs/20261002T145103.184769Z_000165ef2e044376baf54b675172a64e` | ef35312a…e7f | ICL-NUIM, 9 views | independent (published surface) |
| Identity | Task21 `04_geometry_identity/runs/20261004T143434.634726Z_33f59456f7d34e50a64020ed6e0613bb` (Task21 still pending review) | 75a1b943…d6f7 | TUM freiburg1 desk, 11 observations | provisional |

No new model inference.

## Why

The owner wants to know whether each change makes the system better or worse, step by step, and eventually to get a detailed per-step accuracy log from an end-to-end test. Today four steps are scored, each in its own experiment folder with its own output format. Nothing records which reference each score used, so two scores can't safely be compared. Nothing separates a step's own error from error passed down from earlier steps. Example: the 72.8 mm spread of the desk cup position (Task29) mixes box placement, background depth leaking into the box, and camera error, and no current output can say which one dominates. Tasks 32, 34 and 35 each plan their own measurements; without a shared format their results won't line up.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Camera position error against motion-capture paths exists | layer 3 `evaluate`, `read_references` | Task05/13 runs | experiments/03_camera_pose_estimation/src/evaluation.py:13, :46 |
| Detection one-to-one matching with hit/miss/false counts exists | `score_category`, `evaluate` | Task18 run | experiments/06_object_recognition/experiments/01_detection/scoring.py:86, :160 |
| Detection publishes two method keys | detection runner | Task18 scores.json | experiments/06_object_recognition/experiments/01_detection/run.py:133-138 |
| Published surface numbers come from `SurfaceScorer.summary` via `DistanceTotals` | layer 4 evaluation | Task04 metrics.json | experiments/04_surface_reconstruction/src/evaluation.py:54, :125 |
| Reference-side surface distances use `distance_summary` | layer 4 evaluation | `SurfaceScorer.summary` | experiments/04_surface_reconstruction/src/evaluation.py:37, :133 |
| Identity scoring against reference instances exists, one per condition | `_score` | Task21 run | experiments/06_object_recognition/experiments/04_geometry_identity/run.py:164, :350-362 |
| Digit-prefixed modules load through importlib | identity tests | none | experiments/06_object_recognition/experiments/04_geometry_identity/tests/test_run.py:10-12 |
| Accepted-run tests read paths from environment variables and skip when absent | identity tests | none | experiments/06_object_recognition/experiments/04_geometry_identity/tests/test_run.py:24-26 |
| Runs publish only after all artifact hashes verify | `Run`, `verify_run` | all runners | experiments/shared/runs.py:59, :137 |
| Run folders are not in git | .gitignore | none | .gitignore:20 |
| Default test collection lists folders explicitly | pytest.ini, tools/check.py | developers | pytest.ini:2; tools/check.py:23-35 |
| No shared per-stage report or comparison exists | searched `per-stage`, `error budget`, `stage report`, `compare(` across experiments/ and task_list/ | none | no matches outside task prose |

Steps:
1. Write the schema and validator (`experiments/evaluation/schema.py`), tests first.
2. Write one wrapper per scorer under `experiments/evaluation/stages/` (camera, detection, surface, identity). Each first calls `verify_run` on its run, then reads the files listed above.
3. Write `experiments/evaluation/compare.py` and a table renderer.
4. Write `experiments/evaluation/run.py` (entry script with a module-level `HYPERPARAMETERS` dict mirroring the table below), which verifies the given runs, assembles the report and publishes it through the shared `Run`.
5. Add `experiments/evaluation/tests` to `pytest.ini` testpaths and to the default list in `tools/check.py`.
6. Produce the first composite report and write up which stages are scored, which are provisional, and which are unavailable.

Out of scope: new measures for detection placement (Task45), segmentation (Task34), position uncertainty (Task32), fusion (Task35); new references (Task40); new datasets (Task41); any pass/fail limit; edits to owner scorer files.

## Hyperparameters

| name | value | source |
|---|---|---|
| detection IoU thresholds | 0.3, 0.5, 0.7; primary 0.5 | inherited task_list/closed/18_evaluate_object_detection_on_frozen_labelled_obser.md:89 |
| detection assignment | max cardinality then max summed IoU, same class, one-to-one | inherited task_list/closed/18_evaluate_object_detection_on_frozen_labelled_obser.md:90 |
| detection method keys reported | `cached_yolo26x_accepted_task28` and `empty_prediction_software_control` | confirmed 2026-10-05 under owner delegation |
| identity conditions reported | all five Task21 conditions, each its own method key | confirmed 2026-10-05 under owner delegation |
| surface measures | accuracy mean/RMSE/max, within-threshold fraction, reference coverage fraction | confirmed 2026-10-05 under owner delegation |
| camera timestamp association tolerance | 0.02 s | inherited experiments/03_camera_pose_estimation/src/evaluation.py:49 |
| surface reporting distance | 0.05 m | inherited experiments/04_surface_reconstruction/README.md:100 |
| pinned runs | the four runs and manifest hashes in the What table | confirmed 2026-10-05 under owner delegation |
| summary table number format | 4 significant figures for display; JSON keeps full floats | confirmed 2026-10-05 under owner delegation |
| comparison pass/fail limits | none | n/a owner has not set limits; report shows change and direction only |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Evaluated run outputs | each experiment's completed run, checked by experiments/shared/runs.py:59 | stage wrappers | the run's own published files; never modified | Yes; read-only |
| Reference data | benchmark and dataset files copied into each run's input folder (experiments/06_object_recognition/datasets/prepare.py:201) | stage wrappers only | evaluator-only files with ID, version, hash | Yes; read-only |
| Stage report | `experiments/evaluation/run.py` via experiments/shared/runs.py:137 | readers, `compare.py` | JSON v1; unit stated per measure; `null` plus reason for unavailable | Yes, once verified; incomplete reports stay `running`/`failed` |
| Comparison | `compare.py` | owner review | per-measure baseline, candidate, change, direction, comparable flag and reason | Rebuilt from two reports |

- **Source of truth:** the evaluated runs and reference files. A report is derived and can be rebuilt.
- **Process boundary:** none new; the evaluator reads files written by earlier runs.
- **Failure after each step:** a crash before verification leaves an unpublished report folder; restart writes a new one. Evaluated runs are never touched.
- **Fresh-deployment path:** run folders are gitignored (.gitignore:20). To reproduce the first report elsewhere, transfer the four pinned run folders; the command calls `verify_run` on each and checks its manifest SHA-256 against the pinned value before reading anything. Without them, the committed fixtures still exercise every wrapper.
- **Backward compatibility:** existing runs and their own scores stay as they are. The report must reproduce each owner's stored numbers exactly.
- **Reference leakage:** wrappers read references only from completed runs; nothing in this package writes into method inputs.

## Verification

- **Contract test:** `experiments/evaluation/tests/test_stage_report.py`, collected by default through `pytest.ini` and `tools/check.py`. Committed small fixtures: a 3-record `poses.json` plus `groundtruth.txt`; a 1-frame `annotations.json` plus `cached_proposals.json`; a 2-condition `decisions.json` plus truth; two tiny distance `.npy` files. The detection fixture must meet the scorer's fixed checks: boxes inside 640×480, class 41 = cup and 62 = tv, and every frame carrying `frame_id`, `source_selection_index`, `labels` and `label_coverage` with both cup and tv keys (experiments/06_object_recognition/experiments/01_detection/scoring.py:70-77, :168-180). Assertions:
  - Each wrapper reads its fixture and gives the hand-computed values.
  - Unavailable stays unavailable: a stage with no reference gives `null` plus a reason, never 0 and never omitted.
  - Comparison refuses mismatches: different reference hash, coverage, input mode, method key or dataset each give `comparable: false` with that reason.
  - Direction: a detection fixture with one correct prediction removed gives recall lower by 1/N and `compare` labels it worse.
  - Camera: a fixture with frames after the first set to status `tracked` and offset by 5 cm gives per-frame `position_error_m` of 0.05 for every frame after the first, 0.0 for the alignment frame, and position RMSE 0.05·sqrt((n−1)/n).
  - Own vs inherited: the camera section built against the reference path (`isolated`, RMSE 0) and against the same path with every frame after the first offset by 5 cm and status `tracked` (`chained`, RMSE 0.05·sqrt((n−1)/n)) gives a nonzero inherited difference equal to 0.05·sqrt((n−1)/n), within floating-point tolerance. A constant offset of the whole path would be absorbed by the scorer's first-frame alignment, so it is not used. This proves the report arithmetic only; real stage pairs come later.
  - Provisional references are labelled: a section built on Task17's provisional labels shows reference kind `provisional` in the summary table.
- **Accepted-run reproduction test:** `experiments/evaluation/tests/test_accepted_runs.py`. Run paths come from environment variables (`EVAL_TASK05_RUN`, `EVAL_TASK18_RUN`, `EVAL_TASK04_RUN`, `EVAL_TASK21_RUN`); each test skips with a stated reason when its variable is unset. Exact equality with the stored values: camera RMSE 0.006925680114771647 m (Task05 `output/metrics.json`); detection cup matched 4, missed 1, false 0, precision 1.0, recall 0.8 at every threshold; surface accuracy mean equal to Task04 `output/metrics.json` bit for bit; identity per condition equal to Task21 `summary.json`.
- Written red-first; at least one test should fail against a deliberately wrong wrapper (for example one that swaps reference and prediction).
- **Before/after:** before, 0 of 8 stages in a common log. After the first slice, 8 of 8 stages present in one composite report: camera, detection, surface and identity scored from the pinned runs, the other four marked unavailable with reasons.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

- Tasks 32, 34, 35, 45 add their measures to this format. Task09 (inventory umbrella) should use this report as its end-to-end evidence.
- Plan review 2026-10-05 FAIL (wrong surface owner function; tests depended on gitignored runs and were not collected by default). Both fixed above, together with the seven advisory findings: exact stored float for Task05, alignment frame in the camera RMSE, named method keys and conditions, per-measure coverage, composite labelling, pinned runs, importlib loading.
