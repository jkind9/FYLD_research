---
id: "13"
title: Validate frozen tracking settings on full development and held-out data
status: in_progress
priority: MED
type: experiment
blocked_by: []
blocks: []
verification_test: experiments/03_camera_pose_estimation/tests/test_tracking.py
plan_reviewed: 2026-10-02 PASS
files:
  - experiments/03_camera_pose_estimation/**
  - experiments/datasets/**
  - data/tum/rgbd_dataset_freiburg1_desk/**
  - data/archives/rgbd_dataset_freiburg1_desk.tgz*
docs:
  - experiments/03_camera_pose_estimation/README.md
  - experiments/datasets/README.md
  - data/README.md
baseline_metric:
  source: experiments/03_camera_pose_estimation/README.md
  field: complete full-sequence and held-out evaluations
  baseline_value: "0 complete full-sequence or held-out tracking evaluations"
  target: "2 complete frozen-setting evaluations: development xyz and held-out desk"
created: 2026-10-02
last_updated: 2026-10-02
superseded_by: null
---

# Task 13: Validate tracking beyond the short CPU trial

## In plain English

Check whether the camera tracker stays accurate beyond the short trial already completed. Run the full development recording and a separately selected recording without changing the tracking settings to fit its answers. Preserve failures and report speed and memory alongside camera-path errors.

## What

This task takes ownership of full development and preselected Freiburg1 desk evaluation deferred from Task05 when the user prioritized phone feasibility on 2 October 2026. Keep Task05's short CPU baseline and source snapshots unchanged. Acquire and verify desk, extend the runner beyond its current 30-frame xyz CLI restriction, and publish independent complete run receipts. No phone feasibility result is required to run these benchmark controls.

## Why

The verified baseline covers only 30 observations and 1.136 seconds. It does not establish long-trajectory drift, failure behavior on different observations or mobile performance. A separate task makes that missing evidence visible without preventing workstation and phone preparation.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| CPU settings and stage timing already exist | run.HYPERPARAMETERS and execute | benchmark runs | experiments/03_camera_pose_estimation/src/run.py:21 |
| CLI currently restricts inference to the approved 30-frame xyz trial | main | extended runner | experiments/03_camera_pose_estimation/src/run.py:204 |
| Dataset association and pose-free decoding exist | associations and load_frame | tracker | experiments/03_camera_pose_estimation/src/dataset.py:78 |
| Independent fixed-scale scoring exists | evaluate | run output | experiments/03_camera_pose_estimation/src/evaluation.py:46 |
| Shared publication rejects incomplete or changed artifacts | verify_run | evaluation receipts | experiments/shared/runs.py:60 |
| Bounded safe extraction exists; downloader remains ICL-specific | `publish_archive` in the existing acquisition module | TUM-specific download and receipt handling in that module; its tests | experiments/datasets/acquisition.py:111 |

1. Run the hyperparameter audit and record exact full-sequence selections and any runtime caps before execution. Preserve all numerical backend settings from Task05; new selections need explicit dated approval. Full xyz has 798 listed RGB and depth rows, of which 792 pairs associate one-to-one at the inherited 0.02-second tolerance; use all 792 if the user approves this selection. Desk frame count is unknown until its archive is verified. Do not run either sequence while desk count or resource caps remain unstamped.
2. Extend the existing CLI and tests rather than introducing a second estimator. Ensure recorded frame selections equal the actual selected count and enforce dataset/source provenance.
3. Extend the existing acquisition module and tests with TUM-specific download and receipt handling. Acquire desk from its official HTTPS publisher, compare the exact GET byte count with the publisher's HTTPS HEAD length, record a local SHA-256 because no publisher checksum is listed, extract safely to a fresh destination and retain provenance. Never overwrite development observations.
4. Freeze settings on xyz before desk. Score desk only after estimation, without retuning against its reference poses. A desk-driven settings change needs a new independent held-out sequence.
5. Publish both complete runs with statuses, segment-aware scores, stage timing/FPS, memory and inspectable reports. Keep no-loop-closure and no-map-recovery limitations explicit. Do not infer phone performance from desktop benchmarks.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Immutable TUM inputs | dataset adapter | timestamps in seconds; raw/5000 axial metres; xyzw reference rotations kept outside tracker | hashed snapshots | experiments/03_camera_pose_estimation/src/dataset.py:110 |
| Estimated poses | evaluator and future reconstruction | camera-to-world metres; unique run and segment origins | output records | experiments/03_camera_pose_estimation/src/tracking.py:39 |
| Run | report reader | incomplete until required artifacts and hash manifest validate | status and manifests | experiments/shared/runs.py:229 |

Source of truth is original data, frozen configuration and immutable run snapshots. No transport or new process boundary is required. Interrupted downloads remain partial; interrupted estimation or reporting starts a fresh run and never appends to an old origin. Fresh deployment follows the existing tracking README's pinned environment and validated input route. The prior 30-frame trial remains readable and unchanged. Review this stateful plan before code or inference.

## Hyperparameters

All backend values below are inherited unchanged from the Task05 completed run configuration and current CPU runner. The expanded selections and resource caps are not yet approved; do not run inference until they are confirmed.

| name | value | source |
|---|---|---|
| development sequence | TUM Freiburg1 xyz | inherited experiments/03_camera_pose_estimation/src/run.py:23 |
| held-out sequence | TUM Freiburg1 desk; selected before baseline tuning | inherited data/icl_nuim/held_out_tracking.json:6 |
| development observation selection | proposed: all 792 one-to-one RGB/depth pairs from 798 rows per stream at 0.02 s tolerance; no stride; awaits dated confirmation | observed data/tum/rgbd_dataset_freiburg1_xyz/rgb.txt and depth.txt; inherited experiments/03_camera_pose_estimation/src/dataset.py:78 |
| held-out observation selection | proposed: all 573 one-to-one RGB/depth pairs from 613 RGB and 595 depth rows at 0.02 s tolerance; awaits dated confirmation | inherited data/icl_nuim/held_out_tracking.json:6; observed data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk/rgb.txt and depth.txt |
| camera calibration | 640x480; fx=525, fy=525, cx=319.5, cy=239.5 pixels | inherited experiments/03_camera_pose_estimation/src/run.py:31; TUM ROS defaults |
| RGB/depth timestamp association | one-to-one, within 0.02 s | inherited experiments/03_camera_pose_estimation/src/run.py:36 |
| TUM depth decoding | raw uint16 / 5000 = metres; valid range 0 < z < 4 m | inherited experiments/03_camera_pose_estimation/src/run.py:35,39; data/README.md:31 |
| backend | Open3D 0.19.0 CPU hybrid odometry | inherited experiments/03_camera_pose_estimation/src/run.py:37 |
| RGBD input representation | float32 metric depth; scale 1; truncation 4 m; intensity enabled | inherited experiments/03_camera_pose_estimation/src/run.py:59 |
| depth correspondence difference | maximum 0.03 m | inherited experiments/03_camera_pose_estimation/src/run.py:40 |
| optimizer iterations | [20, 10, 5] | inherited experiments/03_camera_pose_estimation/src/run.py:38 |
| pair initialization | identity transform | inherited experiments/03_camera_pose_estimation/src/run.py:41 |
| segment reset after gap | timestamp gap > 0.1 s | inherited experiments/03_camera_pose_estimation/src/run.py:42 |
| segment reset after tracking failure | next usable observation anchors a new segment | inherited experiments/03_camera_pose_estimation/src/run.py:43 |
| pose alignment | first matched reference pose per segment; scale fixed at 1 | inherited experiments/03_camera_pose_estimation/src/run.py:47 |
| relative-motion scoring | adjacent successful matched edges within a segment | inherited experiments/03_camera_pose_estimation/src/run.py:51 |
| reference quaternion handling | normalize finite nonzero publisher xyzw values for scoring; preserve original bytes | inherited experiments/03_camera_pose_estimation/src/run.py:55 |
| report selection | every selected observation status; 320x240 thumbnails; desktop trajectory plot | inherited experiments/03_camera_pose_estimation/src/run.py:67 |
| CPU threads | existing desktop runtime defaults; no override | inherited experiments/03_camera_pose_estimation/src/run.py:63 |
| execution device | CPU only; no GPU | inherited Task05 run configuration; user instruction for this project |
| runtime and memory caps | pending dated user confirmation; no inference until confirmed | n/a not yet approved |

`hyperparam-audit.js .` was run. It reports historical differences across copied run/source snapshots; within the tracking declarations, the successful 30-frame run configuration matches the current CPU settings. The earlier failed attempt lacks the reference-quaternion normalization now recorded by the successful run. This task inherits the successful run configuration. The audit also compares generic `source` and `value` keys from nested source snapshots, which are provenance fields rather than experiment settings.

## Verification

Contract tests extend experiments/03_camera_pose_estimation/tests/test_tracking.py: selected_frames and recorded hyperparameters match actual inputs; long streaming input retains only the image pair; failed/reset edges never join origins; held-out references are opened only after estimates persist; missing or changed required artifacts cannot publish complete. Existing scaled/reversed trajectory controls must remain worse than the exact fixture under scale1 alignment.

Before: 0 complete full-sequence or held-out evaluations. Target: 2 complete reports using frozen backend settings, with every selected observation accounted for and all report/manifest links validated. Numeric product acceptance limits and phone performance remain separate questions.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | `experiments/datasets/acquisition.py`, `experiments/datasets/tests/test_acquisition.py`, `data/README.md`, `experiments/datasets/README.md`, `experiments/03_camera_pose_estimation/README.md`, `experiments/README.md`, `README.md`, `task_list/README.md`; ignored TUM desk archive and extracted input tree |
| Test status | Full repository suite: 162 passed; acquisition tests include 28 controls; tracking evaluation not run |
| Before measurement | 0 full-sequence or held-out evaluations |
| After measurement | Still 0 full-sequence or held-out evaluations; desk archive verified, 573 paired images decode at 640x480, and 25.44% missing depth measurements remain invalid |
| Delta | 0 evaluations; held-out inputs acquired, structurally checked and decoded without filling missing measurements |
| Outcome | Continue only after frozen selection and user-confirmed runtime and memory limits; no inference has run |
