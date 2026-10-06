---
id: "05"
title: Establish a CPU tracking baseline with supplied benchmark depth
status: closed
priority: MED
type: experiment
blocked_by: []
blocks: []
verification_test: experiments/03_camera_pose_estimation/tests/test_tracking.py
plan_reviewed: 2026-10-02 PASS
files:
  - experiments/03_camera_pose_estimation/**
  - tools/check.py
  - pytest.ini
  - experiments/shared/runs.py
  - experiments/shared/timing.py
  - experiments/shared/tests/test_timing.py
docs:
  - experiments/03_camera_pose_estimation/README.md
  - experiments/shared/README.md
  - README.md
  - experiments/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/03_camera_pose_estimation/README.md
  field: fresh independent controls
  baseline_value: "0 active independently evaluated tracking runs"
  target: "Reproducible CPU baseline with independent short-trial scores and shared timing; broader validation tracked in Task13"
created: 2026-10-01
last_updated: 2026-10-02
superseded_by: null
---

# Task 05: Evaluate tracking with supplied benchmark depth

## In plain English

Estimate how a camera moves while giving the tracker known depth. Compare its movement estimates with independently recorded camera positions. Keep failed tracking intervals visible so reconstruction cannot mistake them for reliable poses.

## What

Build a CPU RGB-D motion-estimation baseline using TUM supplied depth. Evaluate camera poses with a separate ground-truth reader. Use acquired Freiburg1 xyz for development and the already selected Freiburg1 desk for held-out evaluation. Desk is not yet acquired: acquire and verify it before held-out evaluation, without blocking initial baseline implementation. This task owns pipeline stage 03; estimating rotation and translation is camera tracking itself.

## Why

Supplied depth isolates tracking from stereo errors. Reference-pose reconstruction and estimated tracking can be developed independently after shared contracts are established.

On 2 October 2026 the user requested a shared timing wrapper, run metadata with frames per second, and execution when ready. This authorizes the proposed CPU trial configuration. Add a reusable timer with explicit stage, frame count and denominator; record estimator throughput separately from end-to-end run throughput so preprocessing, reporting and scoring costs remain visible.

## How

| Claim | Existing owner | Consumers | Evidence |
|---|---|---|---|
| Portable pose and origin records already exist | Pose and require_same_origin | estimator adapter and reconstruction | experiments/shared/contracts.py:39 |
| Timestamp association helper already exists | associate_times | TUM observation adapter | experiments/shared/geometry.py:108 |
| Run publication and artifact checks already exist | Run and verify_run | estimator entry point | experiments/shared/runs.py:137 |
| The existing observation schema requires a pose and must not be used for estimator inputs | Observation | supplied-pose geometry only; new tracking inputs reuse Calibration instead | experiments/shared/contracts.py:73 |
| Timestamp matching is greedy, one-to-one nearest matching, not interpolation | associate_times | colour/depth association and independent evaluation | experiments/shared/geometry.py:108 |
| Depth conversion and pose validation already exist | depth_metres and validate_transform | tracking frame adapter and estimated relative transforms | experiments/shared/geometry.py:10 |
| A checked snapshot copy already exists | copy_checked | tracking input snapshots via importlib because the directory starts with a digit | experiments/04_surface_reconstruction/src/dataset.py:16 |
| Shared publication checks integrity but does not require tracking-specific outputs | Run.finish | tracking run must assert its own required artifacts first | experiments/shared/runs.py:229 |
| Bounded archive extraction already exists; downloader is ICL-specific and cannot acquire TUM | publish_archive and download | fresh deployment can reuse extraction after a verified TUM download, not the ICL downloader | experiments/datasets/acquisition.py:111 |

1. Write known-motion, gap, texture/depth failure and segment-reset tests before the estimator.
2. Wrap existing Open3D RGB-D CPU odometry as the first diagnostic baseline without ground-truth access; evaluator loads references only after estimation. Keep dataset ingestion, backend adaptation, evaluation and exporting separate. Do not reimplement feature matching or optimisation to fit our folder layout. This baseline does not establish full SLAM, loop closure or recovery; an established SLAM package such as ORB-SLAM3 remains a later backend candidate, not an already selected or validated implementation.
3. Report absolute/relative trajectory error using disclosed rigid alignment with scale fixed, tracked fraction, failures and timings.
4. Evaluate held-out sequences chosen in Task02 without retuning against their references. Report whether loop closure/recovery exist.
5. Record poses with segment/world-frame identity, tracking status and observation IDs. For any backend that revises earlier poses, retain revisions and require reconstruction to update affected contributions or rebuild; never silently overwrite a trajectory already used downstream. A later same-observation supplied/estimated-pose reconstruction comparison follows when Tasks04 and05 both have controls.

### Implementation boundaries

All `src/` module names below are relative to `experiments/03_camera_pose_estimation/` and covered by its declared recursive scope.

- `src/dataset.py`: immutable pose-free RGBDFrame records with RGB timestamp, depth timestamp, calibration, colour, depth and validity. Validate timestamp ordering, safe relative paths, PNG types and resolution. Match timestamp tables with the shared one-to-one helper; reject crossed matches if selected depth times do not increase with RGB times. Preserve both capture times and unmatched counts. This module never opens `groundtruth.txt`.
- `src/backend.py`: Open3D CPU adapter consumes only two RGBDFrame records and explicit settings. Check the installed build disables CUDA and SYCL before import. The relative transform maps the source camera into the target camera. Compose `T_world_current = T_world_previous @ inverse(T_current_previous)`. Keep only a bounded image pair in estimator memory. Reject invalid transforms, non-finite information or backend failure; a failed observation has no successful estimated pose.
- `src/tracking.py`: immutable output records distinguish initialized anchors, successful tracking, failures and resets. On failure, do not bridge the failed edge; the next usable observation starts a fresh segment. A timestamp gap above the selected limit also creates a segment. Never count identity anchors as successful tracked edges. Publish estimated Pose records with distinct world/segment identities.
- `src/evaluation.py`: independently load and validate references after all estimation finishes. Associate references one-to-one within the selected tolerance. For each segment, use its first matched reference pose to place that segment into the reference frame, with scale exactly one. Segments without a matched successfully tracked edge have unavailable accuracy, not zero error. Report positional root-mean-square error and adjacent-edge translation/rotation errors, plus unmatched references and unscoreable intervals. Relative errors never cross segments or skip a failed/unmatched observation. Keep segment metrics separate; pooled totals are explicitly sample-weighted.
- `src/run.py` and `src/reporting.py`: snapshot only selected observation inputs for the estimator, then snapshot independent references for scoring. Use Run completion and hash checks. Save settings, poses/status, association rows, pair timings, process memory measurements, input thumbnails and trajectory/error plots in a unique run. Report that this pairwise baseline has no loop closure or map recovery. Add this test directory to both `pytest.ini` and `tools/check.py`.
- Before leaving the Run context, `src/run.py` explicitly checks every selected frame has exactly one status, every tracked status has a valid estimated pose, every required input/status/metrics/report artifact exists, and all report links resolve. Shared Run verifies hashes of existing files; it does not enforce these tracking-specific requirements. Test deletion of a required output before publication causes a failed run.
- Start with the proposed 30-frame development inspection only after the settings answer. Do not treat approval of this smoke trial as approval of any revised setting or product acceptance threshold. Freeze development settings before acquisition/evaluation of desk; document later full-sequence selection separately.

### Fresh deployment to first trial

### Shared timing extension

`experiments/shared/timing.py` owns a reusable monotonic context timer. Run owns its collector. `run.measure(stage, frames=...)` records successful stage samples in seconds, frames and frames/second; failed samples stay visible as failed and are excluded from successful stage throughput. Aggregate FPS is summed successful frames divided by summed successful elapsed time, never the mean of sample FPS. `run.set_processed_frames(count)` records the unique observation count for end-to-end FPS; it is independent of summed stage counts. Unknown counts and zero elapsed time produce null FPS, never infinity. Reject invalid counts, blank stage names and non-finite/negative elapsed time. A run with no timing scopes still publishes legacy elapsed/start/end fields plus zero samples and unavailable FPS. Extend the same `metadata/timing.json`, preserving Run's manifest and completion order. Save timing on failed runs too, with failed-run throughput unavailable. Tracking applies the wrapper to loading, odometry pairs, evaluation and report generation; pair throughput uses attempted pairs and explicitly identifies those units, while end-to-end uses selected image frames. Tests use a fake monotonic clock to assert exact denominators, weighted aggregation, exceptions, zero-time behavior and run-manifest integrity.

The sections below specify the fresh deployment to first trial.

Implement and document these commands in the declared experiment README; the commands below are planned interfaces, not claims that the entry points already exist.

1. Create a CPU environment with `python -m venv .venv-tracking`, then `.venv-tracking/Scripts/python -m pip install -r experiments/03_camera_pose_estimation/requirements.txt`. The new requirements file pins the actually verified NumPy, SciPy, Pillow, Open3D, Matplotlib, psutil and test versions. Record a fresh-install check or explicitly retain it as an outstanding prerequisite; successful import in the current desktop environment does not prove a clean install.
2. Obtain `rgbd_dataset_freiburg1_xyz.tgz` from the official TUM HTTPS link documented in the README. Check final HTTPS publisher host, HTTP success, stated content length versus downloaded bytes, SHA-256 and gzip/archive completeness. Preserve its provenance. Use `experiments.datasets.acquisition.publish_archive` for safe bounded extraction to a fresh destination; never use that module's ICL-only download/main path for TUM. A fresh clone can also supply an already acquired directory via the explicit `--dataset` argument after the same image/table validation. The present workspace's verified xyz directory satisfies this input prerequisite for the first smoke run. Acquisition files/receipts outside current scope must be declared before writing them.
3. Run `.venv-tracking/Scripts/python -B tools/check.py -q experiments/03_camera_pose_estimation/tests`. Contract tests include the actual CPU backend integration fixture. Refuse inference if build flags or imports violate the CPU-only requirement.
4. After configuration approval, run `.venv-tracking/Scripts/python -B -m experiments.03_camera_pose_estimation.src.run --dataset data/tum/rgbd_dataset_freiburg1_xyz --frames 30`. The planned CLI exposes the agreed settings explicitly and prints the unique review and metrics paths. Verify that published run with shared `verify_run` before inspecting results. Failed or interrupted runs never serve as successful deployment receipts.

## Invariants and recovery

Reference inputs remain unchanged and outside estimated-method inputs. Record units, frame identities and provenance at each boundary. A partial download or run is not ready data. Publish completed records only after required artifacts validate; interrupted work remains identifiable. Separate origins cannot be fused without a documented transform. No phone, cloud service or GPU is required for the initial control.

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| TUM PNGs and timestamp tables | pose-free RGBDFrame adapter | RGB uint8, depth uint16/5000 metres, camera x-right/y-down/z-forward; both timestamps in seconds | immutable input snapshots | data/README.md:29 |
| Calibration | CPU backend | 640 by 480 pixel intrinsics; no supplied pose field | configuration receipt | experiments/shared/contracts.py:11 |
| CPU source-to-target transform | tracking accumulator | proper rigid 4 by 4 matrix, translation metres; invert before camera-to-world composition | estimated records; live pair state does not resume | experiments/shared/geometry.py:60 |
| Estimated Pose | evaluator and future reconstruction | camera-to-world, source estimated, explicit world and segment IDs | output JSON | experiments/shared/contracts.py:39 |
| Independent reference file | evaluator only | world camera pose, metres, xyzw quaternion and seconds | separate evaluation snapshot | data/README.md:31 |
| Run | verifier/report reader | running or failed until manifest validates complete | status and hash manifest | experiments/shared/runs.py:180 |

Source of truth: original observations plus immutable snapshots, explicit configuration and estimated outputs. No process/thread transport is introduced. If the process dies during copying, estimation, evaluation or rendering, the run remains incomplete and must not be consumed as a completed trajectory. Recovery starts a fresh run rather than appending or merging origins. A fresh deployment installs pinned dependencies and runs contract tests before a CPU trial. Existing supplied-pose schema and Task04 baseline remain compatible; pose-free tracking inputs are a separate type. No pose revisions occur in this pairwise baseline.

## Hyperparameters

The user authorized the proposed 30-frame CPU trial on 2 October 2026 after requesting shared timing metadata. Its settings are recorded below and mirrored in the module-level HYPERPARAMETERS and run configuration. Full-sequence selection and any revised settings must be recorded before later runs. This trial does not establish a product acceptance threshold.

### Approved development smoke trial

The user authorized execution when the shared timing wrapper is applied on 2 October 2026. This approves the previously proposed 30-frame CPU configuration. Hyperparameter audit was run on 2 October 2026; its differences include the archived direct-geometry and surface backends. Those different experiments are not tracking defaults and their receipts must remain unchanged.

| Name | Proposed value | Source |
|---|---|---|
| sequence and selection | Freiburg1 xyz, first 30 consecutive associated frames; no stride | confirmed 2026-10-02 |
| image size and calibration | 640 by 480; fx=fy=525, cx=319.5, cy=239.5; no extra undistortion | confirmed 2026-10-02; TUM official recommended ROS defaults |
| depth conversion | raw/5000 metres; zero invalid; no second publisher depth correction | inherited data/README.md:31 |
| association | shared greedy one-to-one nearest match, tolerance 0.02 seconds for RGB/depth and RGB/reference | confirmed 2026-10-02 |
| backend | Open3D 0.19.0 CPU legacy hybrid RGB-D odometry | confirmed 2026-10-02 |
| pyramid/iterations | three levels, iteration vector [20,10,5] | confirmed 2026-10-02; Open3D 0.19 OdometryOption documented defaults |
| depth interval and correspondence gate | positive depth below 4 metres (Open3D truncation excludes the endpoint); depth_diff_max=0.03 metres | confirmed 2026-10-02; Open3D 0.19 OdometryOption documented defaults |
| RGBD construction | pass metric float depth with depth_scale=1, depth_trunc=4; convert_rgb_to_intensity=True for hybrid odometry | n/a implements the proposed depth interval and backend image representation; never use the constructor's 1000/3 defaults on metric depth |
| pair initialization | identity transform, independent of reference poses | confirmed 2026-10-02 |
| reset | failed edge never bridged; next usable observation starts separate origin; gap above 0.1 seconds resets | confirmed 2026-10-02 |
| evaluation | first matched reference pose per segment, rigid alignment with scale=1; relative errors only adjacent successful matched observations within segment | confirmed 2026-10-02 |
| numerical validation | shared rigid-transform tolerances; finite backend outputs; no invented motion or correspondence acceptance limit | inherited experiments/shared/geometry.py:60 |
| reference quaternion conversion | normalize finite nonzero publisher xyzw quaternions before shared unit-quaternion conversion; preserve original reference bytes | n/a input representation, not a tracker or scoring tune |
| estimator retention | current image pair; no map or revisits; outputs streamed to run records | n/a implementation ownership, not an accuracy setting |
| CPU threads | existing OpenMP environment and backend runtime defaults; no new thread-limit override; record environment, CPU count and observed process threads | n/a observe installed desktop runtime; this is not a single-core or phone timing claim |
| reporting | all 30 observation statuses, all pair timings, process memory including backend load and report generation | n/a exhaustive smoke-trial reporting |

References: [Open3D option defaults](https://www.open3d.org/docs/0.19.0/python_api/open3d.pipelines.odometry.OdometryOption.html), [TUM formats and calibration](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats).

## Verification

Estimator input cannot expose reference poses. Deliberately scaled/reversed trajectories score worse under fixed-scale evaluation; failed/reset segments remain separate. Record measured trajectory error, tracked fraction and failures on development and held-out data.

Contract assertions in `experiments/03_camera_pose_estimation/tests/test_tracking.py`: a known source-to-target translation of -0.1 metres on X produces a camera-to-world translation of +0.1 metres; the frame input has no pose or reference-path field; a forbidden reference read causes an estimator test failure; an invalid transform or zero-depth pair cannot publish tracked status; failure/gap splits origins and relative-error pairs never cross the split; an exact fixture trajectory scores zero while 2x translations and reversed movement score worse under fixed-scale evaluation. Test timestamp tolerance boundaries, duplicate/out-of-order rows, malformed image paths, missing references, all-failed sequences and incomplete publication. Add a small actual Open3D known-motion fixture so numerical integration is tested in addition to a fake backend.

Before: 0 active independently evaluated tracking runs. First target: one complete CPU 30-frame inspection with exactly 30 statuses, 29 possible transition outcomes, independent trajectory scores, timings, measured memory and hash-verified artifacts. Closure now covers the verified CPU baseline. Full development and preselected held-out evaluation are explicitly deferred from this task to Task13, following the user's request to close the baseline and prioritize Task08 on 2 October 2026. Numeric product acceptance limits are not selected and this diagnostic run cannot establish acceptance.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not committed; source and working diff retained in run metadata; baseline HEAD 80d4927600bb290040d75d99379d93bb46315451 |
| Files changed | Tracking src modules, tests, requirements and README; shared timing.py, runs.py, test_timing.py and README; tools/check.py, pytest.ini; root/experiment/task READMEs; this task |
| Test status | 130 CPU tests PASS; timing and tracking 423/465 statements covered (91%); Ruff, Black and mypy PASS |
| Before measurement | 0 active independently evaluated tracking runs |
| After measurement | 1 complete independent CPU trial: 30 observations, 29/29 tracked edges, 0 failures, 1 segment, 30 reference matches; 6.925680 mm position RMSE; 6.946881 mm relative translation RMSE; 0.462491 degree relative rotation RMSE |
| Delta | 0 to 1 completed development inspection; shared FPS unavailable before, now measured per stage and run |
| Timing | Tracking 29 pairs/13.581245 s = 2.135298 pairs/s; end-to-end 30 images/17.724440 s = 1.692578 frames/s; final manifest hashing excluded and scope explicit |
| Memory | Desktop peak working set 461418496 bytes (440.043 MiB), including backend and plotting; existing runtime defaults, 32 logical CPUs and 86 process threads; not phone or single-core performance |
| Decision-gate outcome | PASS for the CPU baseline milestone; full development and held-out work explicitly deferred to Task13 by user prioritization on 2026-10-02; no product acceptance gate claimed |
| Run | experiments/03_camera_pose_estimation/runs/20261002T164601.734717Z_befb0ccd27ab44daba6d9ac41f9b9ae0; complete, 172 artifacts hash-verified; all 60 selected input image hashes and reference hash match originals; 64 review links resolve |
| Reviews | Plan PASS before start including timing scope; code/Python reviews fixed failure-status, numeric FPS and exact-4m depth findings; final fresh-context diff review reports no remaining defects after source-snapshot, single-reference scoring and quaternion conversion fixes |

The first real-data attempt, 20261002T164134.080776Z_10a5e97bcb38479d935d3bb39d50cb3c, remains failed and unchanged. It estimated all 30 observations, then shared quaternion validation rejected publisher norms between 0.999917742 and 1.000083771. The evaluator now unit-normalizes finite nonzero reference quaternions without changing their original file. A dedicated regression failed before conversion and passes afterward. Shared geometry's strict unit-quaternion contract remains unchanged. Evaluation tests reject zero quaternions and do not manufacture zero accuracy from a lone reference match.

Review findings have RED/GREEN regressions: timing-write failure and unclosed scopes preserve failed status; infinite/overflow FPS becomes unavailable; output roots that contain source code still archive source; depth exactly 4 metres cannot create falsely tracked empty images; different runs use different origin namespaces; associations read copied tables; a single matched tracked pose is unscoreable. The actual CPU backend known-motion fixture and scaled/reversed trajectory controls pass.

Task05 baseline is complete. Its former full development and held-out closure conditions are waived for this milestone and transferred to Task13; those measurements are not claimed complete. Shared timing and the authorized 30-frame CPU trial are complete and verified. Read-only inspection confirms the installed Open3D build has BUILD_CUDA_MODULE=False and BUILD_SYCL_MODULE=False. A CPU-only import succeeded with NumPy2.4.2; Image resolves to open3d.cpu.pybind.geometry. Actual OdometryOption defaults match the proposal. RGBD construction defaults instead scale depth by 1000 and truncate at 3 metres, so the adapter must explicitly use metric depth_scale=1 and the proposed depth_trunc=4.

Task13 owns the full-sequence and held-out work deferred here: [frozen tracking validation](13_validate_frozen_tracking_settings_on_full_developm.md). Its verified benchmark results do not establish mobile readiness.
