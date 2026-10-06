---
id: "13"
title: Validate frozen tracking settings on full development and held-out data
status: closed
priority: HIGH
type: experiment
blocked_by: []
blocks: []
verification_test: experiments/03_camera_pose_estimation/tests/test_supervisor.py
plan_reviewed: 2026-10-06 PASS
shrinks:
  - experiments/03_camera_pose_estimation/src/supervisor.py
  - experiments/03_camera_pose_estimation/tests/test_tracking.py
files:
  - experiments/03_camera_pose_estimation/**
  - experiments/shared/runs.py
  - experiments/datasets/**
  - data/tum/rgbd_dataset_freiburg1_desk/**
  - data/archives/rgbd_dataset_freiburg1_desk.tgz*
  - README.md
  - task_list/README.md
  - experiments/README.md
docs:
  - experiments/03_camera_pose_estimation/README.md
  - experiments/datasets/README.md
  - data/README.md
  - README.md
  - task_list/README.md
  - experiments/README.md
baseline_metric:
  source: experiments/03_camera_pose_estimation/README.md
  field: complete full-sequence and held-out evaluations
  baseline_value: "0 complete full-sequence or held-out tracking evaluations"
  target: "2 complete frozen-setting evaluations: development xyz and held-out desk"
created: 2026-10-02
last_updated: 2026-10-06
superseded_by: null
---

# Task 13: Validate tracking beyond the short CPU trial

## In plain English

Check whether the camera tracker stays accurate beyond the short trial already completed. Run the full development recording and a separately selected recording without changing the tracking settings to fit its answers. Preserve failures and report speed and memory alongside camera-path errors.

## Planning update, 3 October 2026

Historical direction on 3 October put recorded-video recognition first. The 6 October board restored this full camera baseline near the start of the queue; it no longer waits for Task35. At the time of this planning note the task was open, with approved selections/resource caps and unfinished authorized code. The full runs and guard fix recorded below have since completed.

Before inference, fix the independently reproduced acceptance defect: a final Job Object memory-limit event can be recorded without a rejection reason when the worker exits zero, allowing a complete artifact to be accepted. Add the combined memory-event/exit-zero/complete-run regression. Split supervisor.py and test_tracking.py below 800 lines, keep imports/behaviour equivalent and verify both shrink relative to the launch baseline. The shrinks declarations make this obligation measurable. Task25 owns later feature-seeded and verified-revisit comparisons; it must not alter this frozen baseline.

## Planning update, 6 October 2026

A fresh plan review found that the root README and task board also need result updates. Both are now declared in `files:` and `docs:`. The review confirmed that the planned data path still keeps reference poses outside tracking and preserves frozen CPU settings. It also confirmed the final memory-limit event defect remains reproducible. Re-review the amended plan before code changes.

A second fresh plan review found that `experiments/README.md` also describes the Task13 full evaluation as unfinished. This status will be updated with the measured outcome and is now in scope. Historical dated notes will remain identified as historical.

## Planning update, 6 October 2026, process-limit verification

The focused Windows checks showed that querying the current process Job Object without a handle can return an enclosing job in this environment. The worker therefore cannot use that query to confirm the exact child limit. The supervisor will verify the configured limit through its exact Job Object handle after assigning the worker, then release only after writing a PID-bound confirmation. The worker checks that confirmation and its Job Object membership before inference. The hard process limit still uses the approved 2 GiB Windows Job Object setting. Re-review this amended handoff before continuing.

## What

This task takes ownership of full development and preselected Freiburg1 desk evaluation deferred from Task05 when the user prioritized phone feasibility on 2 October 2026. Keep Task05's short CPU baseline and source snapshots unchanged. Acquire and verify desk, extend the runner beyond its current 30-frame xyz CLI restriction, and publish independent complete run receipts. No phone feasibility result is required to run these benchmark controls.

## Why

The verified baseline covers only 30 observations and 1.136 seconds. It does not establish long-trajectory drift, failure behavior on different observations or mobile performance. A separate task makes that missing evidence visible without preventing workstation and phone preparation.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| CPU settings and stage timing already exist | run.HYPERPARAMETERS and execute | benchmark runs | experiments/03_camera_pose_estimation/src/run.py:21 |
| CLI accepts positive counts only for the configured xyz and desk paths; it checks official source URLs and matches archive size and SHA-256 against both local receipts | main and archive-provenance check | full-sequence runs | experiments/03_camera_pose_estimation/src/run.py:233 |
| Run configuration records the selected sequence and actual association-row count | execute | run readers and scoring receipts | experiments/03_camera_pose_estimation/src/run.py:165 |
| Dataset association and pose-free decoding exist | associations and load_frame | tracker | experiments/03_camera_pose_estimation/src/dataset.py:78 |
| Independent fixed-scale scoring exists | evaluate | run output | experiments/03_camera_pose_estimation/src/evaluation.py:46 |
| Shared publication rejects incomplete or changed artifacts | verify_run | evaluation receipts | experiments/shared/runs.py:60 |
| Bounded safe extraction exists; downloader remains ICL-specific | `publish_archive` in the existing acquisition module | TUM-specific download and receipt handling in that module; its tests | experiments/datasets/acquisition.py:111 |

1. Run the hyperparameter audit and record the confirmed full-sequence selections and caps before execution. On 3 October 2026, the user approved all 792 xyz pairs, all 573 desk pairs, a 30-minute per-sequence wall-clock limit and a 2 GiB per-process memory limit. Preserve all numerical backend settings from Task05. The acquired xyz data has 798 RGB rows and 798 depth rows, with 792 one-to-one pairs at the inherited 0.02-second tolerance. The acquired desk data has 613 RGB rows and 595 depth rows, with 573 one-to-one pairs at that tolerance.
2. Extend the existing CLI and tests rather than introducing a second estimator. The CLI accepts either configured local Freiburg1 data path and a positive frame count. It checks official source URLs, archive size and SHA-256, then compares association tables and selected image files with archive-derived member hashes. It validates the reference file against its archive hash only after all estimates are saved. Preflight the selected association rows before backend loading; require the input snapshot to reproduce them. Hash the selected input copies in the run manifest. Record the actual sequence, row count and resource limits in run configuration and hyperparameters. A separate supervisor enforces the wall-clock deadline and a Windows per-process memory limit. The supervisor queries that exact Job Object after assigning the worker, confirms its limit, then writes a release record with the worker PID and confirmed limit. Before inference, the worker checks that the record names its own PID, that the recorded limit matches the approved value, that it belongs to a Windows Job Object, and that source receipts match. The supervisor writes failed status before detail receipts after termination; it preserves completed artifacts and writes a separate rejection receipt if a completion is observed beyond the wall-clock cap. It never accepts an incomplete or over-time run. Preserve frozen backend settings and bounded image-pair processing.
3. Desk acquisition is complete. The archive was obtained from the official HTTPS publisher; its GET byte count matched the HTTPS HEAD length, its local SHA-256 is recorded because no publisher checksum is listed, and bounded extraction produced a verified fresh destination. Keep the archive and extraction receipts with the held-out data. Never overwrite development observations.
4. Freeze settings on xyz before desk. Score desk only after estimation, without retuning against its reference poses. A desk-driven settings change needs a new independent held-out sequence.
5. Publish both complete runs with statuses, segment-aware scores, stage timing/FPS, memory and inspectable reports. Keep no-loop-closure and no-map-recovery limitations explicit. Do not infer phone performance from desktop benchmarks.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Immutable TUM inputs | dataset adapter | timestamps in seconds; raw/5000 axial metres; xyzw reference rotations kept outside tracker | hashed snapshots | experiments/03_camera_pose_estimation/src/dataset.py:110 |
| Estimated poses | evaluator and future reconstruction | camera-to-world metres; unique run and segment origins | output records | experiments/03_camera_pose_estimation/src/tracking.py:39 |
| Run | report reader | incomplete until required artifacts and hash manifest validate | status and manifests | experiments/shared/runs.py:229 |

Source of truth is original data, frozen configuration and immutable run snapshots. The supervisor owns the deadline and process-memory limit; the worker owns estimation and scoring. The parent assigns a unique run path before launch, and it writes a durable failed status and timing receipt if the worker is terminated. It checks for a complete, verified run before recording failure so it cannot overwrite a successful publication at the deadline. The worker saves all estimates before opening independent reference poses. Interrupted downloads remain partial; interrupted estimation or reporting starts a fresh run and never appends to an old origin. Fresh deployment follows the existing tracking README's pinned environment and validated input route. The prior 30-frame trial remains readable and unchanged.

## Hyperparameters

All backend values below are inherited unchanged from the Task05 completed run configuration and current CPU runner. The full-data selections and resource caps were approved on 3 October 2026. The experiment's hyperparameter audit was run before inference.

| name | value | source |
|---|---|---|
| development sequence | TUM Freiburg1 xyz | inherited experiments/03_camera_pose_estimation/src/run.py:23 |
| held-out sequence | TUM Freiburg1 desk; selected before baseline tuning | inherited data/icl_nuim/held_out_tracking.json:6 |
| development observation selection | all 792 one-to-one RGB/depth pairs from 798 rows per stream at 0.02 s tolerance; no stride | confirmed 2026-10-03 |
| held-out observation selection | all 573 one-to-one RGB/depth pairs from 613 RGB and 595 depth rows at 0.02 s tolerance; no stride | confirmed 2026-10-03 |
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
| per-sequence wall-clock cap | 1800 seconds; starts before worker launch and covers source capture, backend, estimation, scoring and reports; parent-side archive provenance preflight excluded | confirmed 2026-10-03 |
| per-process memory cap | 2 GiB (2,147,483,648 bytes), Windows Job Object process-memory limit; fail before inference if limit setup fails | confirmed 2026-10-03 |
| supervisor poll interval | 0.1 seconds for elapsed-time and RSS evidence; memory enforcement is the OS Job Object limit | n/a supervisor scheduling cadence, not an estimator setting |

`hyperparam-audit.js .` was run. It reports historical differences across copied run/source snapshots; within the tracking declarations, the successful 30-frame run configuration matches the current CPU settings. The earlier failed attempt lacks the reference-quaternion normalization now recorded by the successful run. This task inherits the successful run configuration. The audit also compares generic `source` and `value` keys from nested source snapshots, which are provenance fields rather than experiment settings.

After recording approval, the audit reports the wall-clock cap, process-memory cap and supervisor poll cadence as single-source settings; no earlier tracking run used these limits. Backend values remain inherited from the successful Task05 baseline.

## Verification

Contract tests cover experiments/03_camera_pose_estimation/tests/test_tracking.py and test_supervisor.py: selected frames and recorded hyperparameters match actual inputs; changed selected bytes or reference bytes fail archive-hash checks; the 30-minute limit leaves a failed receipt; late complete artifacts are rejected; incomplete runs are not scored; failed/reset edges do not join origins; and changed required artifacts cannot publish complete. The Windows memory-cap test starts a child waiting on stdin, verifies the configured 64 MiB test cap, then releases allocation. It requires a nonzero allocation below its 256 MiB ceiling, peak commit below 64 MiB, and a Job Object limit event. The test passes. The two full runs must publish valid manifests and reports using all 792 xyz and 573 desk observations without changing Task05 backend settings.

Before: 0 complete full-sequence or held-out evaluations. Target: 2 complete reports using frozen backend settings, with every selected observation accounted for and all report/manifest links validated. Numeric product acceptance limits and phone performance remain separate questions.

## Receipts

| Field | Value |
|---|---|
| Closing commit | None; preserve the existing uncommitted work. Fresh post-fix diff review found no reproducible defect. `task.js verify 13` passed after Task51 was moved to open while its owner decisions remain pending. |
| Files changed | Earlier Task13 work remains listed. This session changed `experiments/03_camera_pose_estimation/tests/test_supervisor.py`, the camera tracking README, project README, `experiments/README.md`, `data/README.md`, and this task record. It produced verified xyz run `20261006T092306.264759Z_859f644f1fd94231bf45feeddfaf4965` and desk run `20261006T093210.950449Z_cb1755babecc4d62afe543d46445eac2`. The older probe and pytest scratch folders under `task_list/` were removed. |
| Test status | The revised Windows memory-cap integration test passed (1 passed), and Ruff passed in the earlier verification. This turn re-ran `verify_run` on both manifests; both returned `status: complete` (5,736 xyz files; 4,203 desk files). The fresh independent diff review found no reproducible defect and did not rerun tests. The full repository check collected 572 tests but emitted errors and ended with `PermissionError` while pytest enumerated its system-temp base; the Task13 directory check also could not finish cleanly for that temp-base error. No full-suite pass is claimed. |
| Before measurement | 0 full-sequence or held-out evaluations |
| After measurement | Two complete, manifest-verified runs. xyz: 792 observations, 53.56 mm position RMSE, 48.50 mm median, 88.20 mm p95, 5.37 mm relative translation RMSE, 480.06 s end-to-end, 1.88 GiB peak committed memory, 440 MiB peak working set. Desk: 573 observations, 280.36 mm position RMSE, 207.31 mm median, 474.10 mm p95, 10.57 mm relative translation RMSE, 341.58 s end-to-end, 1.87 GiB peak committed memory, 435 MiB peak working set. Both had zero failed observations and no supervisor memory-limit event. |
| Delta | 0 to 2 full frozen-setting evaluations; manifests and reports verified; memory cap enforced on both runs |
| Outcome | The two frozen tracking runs are complete and their manifests still verify. The worker now checks the operating system's actual per-process memory cap before inference. Product accuracy and wait limits remain pending, so these scores are not a product acceptance pass. Desk is a held-out sequence from the same indoor sensor/site as xyz. Fresh independent post-fix diff review found no reproducible defect. |

The first focused Windows stress check used a temporary-file gate. It reported that a worker touched and retained 256 MiB under a queried 64 MiB Job Object limit, exited successfully and produced no limit event. That result remains here as historical evidence. Replacing the file handoff with an stdin pipe removed the access failure. A direct pipe-gated worker stopped after 48 MiB, reached a 56.5 MiB peak commit, received the limit event and exited successfully after catching `MemoryError`. The revised repository test uses the pipe gate, bounds the allocation loop, requires a nonzero allocation below that bound, checks peak commit stays under 64 MiB, and checks the limit event; it passes on this host. Microsoft documents this setting as a limit on process committed memory and says an allocation beyond it fails ([Windows Job Object process-memory limit](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information)). Both approved full runs are now complete; see their receipts in the table above.

docs n/a: the root README and `data/README.md` do not describe Task13 supervisor execution, and this session added no claims to those files. Generated test and probe files were removed from `task_list/`; its README now directs future scratch output to system temp.

The bounded frozen-setting tracking baseline is complete. Product accuracy and wait limits remain unjudged until Task51 records the required limits.
