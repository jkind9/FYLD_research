---
id: "00"
title: Finish and validate the Phase 1 scene mapping prototype
status: superseded
priority: HIGH
type: experiment
blocked_by: []
blocks: []
verification_test: archive/task00_prototype/tests/test_tracking.py
plan_reviewed: 2026-10-01 PASS
files:
  - src/fyld_scene_mapping/*.py
  - scripts/*.py
  - tests/*.py
  - test.py
  - benchmark.py
  - pyproject.toml
  - environments/*
  - research/*
  - docs/*
  - .github/workflows/cpu-tests.yml
  - .gitignore
docs:
  - README.md
  - research/README.md
  - archive/task00_prototype/README.md
baseline_metric:
  source: archive/task00_prototype/outputs/20261001T183706Z_estimated_pose_rgbd_50ad5e31/metrics.json
  field: accepted frames and trajectory error
  baseline_value: "120/120 frames; 0.02315 m ATE"
  target: "120/120 frames; retain disclosed SE(3) evaluation; >=80% test coverage"
created: 2026-10-01
last_updated: 2026-10-01
superseded_by: "01"
---

# Task 00: Phase 1 validation and handover

## In plain English

Build an inspectable desktop experiment that reconstructs observed surfaces from images with depth. Compare supplied camera motion with estimated camera motion. Save maps with missing regions visible and report measured results. Research later phone capture without building a service.

## What

The first A/B runs exist. Finish review fixes, reproducible setup, provenance, research, tests and requested future-phase documents. Preserve the original brief's explicit documentation filenames. No mobile app, deployment or production integration.

## Why

The original request requires a functioning prototype and real evidence. The review found a depth gate that ignored its configured interval and an unpackaged import. Both are fixed before this task record; remaining work is verification, recovery paths and handover. The workflow instructions arrived during implementation, so this record begins at the current 120-frame baseline rather than pretending it existed earlier.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| RGB/depth selection does not read ground truth | datasets.select_frames | experiments.run_experiment | src/fyld_scene_mapping/datasets.py:67 |
| Estimated reconstruction accepts no GT unless supplied argument is explicitly passed | reconstruction.reconstruct | experiments.run_experiment passes None in B | src/fyld_scene_mapping/reconstruction.py:162 |
| Measurement rasters preserve unknowns and bound allocation | mapping.project | experiments.run_experiment | src/fyld_scene_mapping/mapping.py:10 |
| Download cache and extraction have separate owners | acquisition.download/extract_tar | download_sample_data.main | src/fyld_scene_mapping/acquisition.py:21 |
| Output artifacts are exported together, but timing rewrites and summary ordering need repair | reporting.export_run and experiments.run_experiment | benchmark summary and run consumers | src/fyld_scene_mapping/reporting.py:64; src/fyld_scene_mapping/experiments.py:211 |

- Keep geometry, timestamp association and map modules. Do not create a second mapping pipeline.
- Split decode/depth conversion timing and record startup/export scope honestly.
- Make partial download/extraction recovery explicit. A failed acquisition must not be treated as complete.
- Move final timing writes into export_run. Atomically write each JSON via a temporary sibling file. Append summary only after all artifact and final JSON writes. Write a completion marker after summary append; interrupted directories without the marker remain incomplete. Document single-process summary writing.
- Add first-party revision/source hashes to manifests and installed-package smoke verification.
- Retain RGB-D frame selection: first 120 associated observations at stride 1.
- Run synthetic tests, real A/B and inspect all generated rasters. Run real end-to-end export test when dataset exists; CI does not download it.
- Complete research and licence records. ETH3D and MASt3R have unresolved permitted company use; no execution of restricted candidates.
- Optional image-only COLMAP is attempted only if verified Windows binary/wheel access and practical setup permit it. No new learned method is required.
- Complete requested documentation; later services remain proposals.

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Depth | reconstruction.read_observation, src/fyld_scene_mapping/reconstruction.py:36 | backprojection/odometry | optical metres, invalid NaN/0 at Open3D boundary | source PNGs and run hashes |
| Frames | datasets.select_frames, src/fyld_scene_mapping/datasets.py:67 | reconstruction.reconstruct | unique indices, Unix seconds | input tables and exact manifest |
| Map | mapping.project, src/fyld_scene_mapping/mapping.py:10 | reporting.export_run | right-handed declared Z-up; gravity unverified; unknown NaN | NPY/metadata |
| Archive | acquisition.download, src/fyld_scene_mapping/acquisition.py:70 | extraction | locally hashed tgz, CC BY 4.0 | verified cache; partial file removed/retry |
| Run completion | reporting.export_run, src/fyld_scene_mapping/reporting.py:64 | benchmark summary | manifest, metrics and output files | unique directories; partial runs explicitly incomplete |

Source of truth: input files, recorded hashes, pinned dependencies and completed run manifest. Ground truth is evaluation-only in B. No pose is supplied across a failed tracking interval.
Process boundary: Git and HTTP downloads only; argument lists for subprocess. One local reconstruction process; no service or workers.
Failure walk: download interruption retries partial download; archive metadata cache can be rebuilt from complete local file; incomplete extraction uses a staging directory and completion provenance; interrupted run remains a unique incomplete directory. Final metrics/manifest timing writes happen before summary append; a completion marker follows summary append. Consumers check the marker, including when a crash happens between summary append and marker. Summary is sequential local use; concurrent writes are unsupported.
Fresh setup: Python 3.11 preferred, 3.12 actually tested; isolated environment, editable install, explicit sample download, python test.py, python benchmark.py, pytest. No hidden network in demos or tests.
Compatibility: retain existing output fields and explicit unknown/scale conventions. Optional image-only output cannot be labelled metric without a scale source.

## Hyperparameters

All values below inherit the already executed baseline. These are engineering defaults, not product acceptance criteria. Module-level declarations will mirror values/provenance in run output.

| name | value | source |
|---|---|---|
| frame_limit / stride / tolerance | 120 / 1 / 0.02 s | inherited test.py:22 and outputs/20261001T183706Z_estimated_pose_rgbd_50ad5e31/run_manifest.json |
| RGB resolution / intrinsics | 640x480; 525,525,319.5,239.5 px | inherited src/fyld_scene_mapping/geometry.py:13; publisher recommended ROS defaults |
| depth scale / bounds | 5000 units/m; 0.2–4 m | inherited src/fyld_scene_mapping/reconstruction.py:23 |
| pixel step / voxel | 3 / 0.015 m | inherited src/fyld_scene_mapping/reconstruction.py:23 |
| translation / rotation step gates | 0.3 m / 30 deg | inherited src/fyld_scene_mapping/reconstruction.py:23 |
| depth overlap / gap / texture std | 0.2 / 0.15 s / 0.01 | inherited src/fyld_scene_mapping/reconstruction.py:23 |
| overlap sample stride / depth agreement | 8 px / 0.07 m | inherited src/fyld_scene_mapping/reconstruction.py:66 |
| odometry pyramid iterations / initializer | Open3D default [20,10,5] / identity | inherited installed Open3D 0.19.0 options and src/fyld_scene_mapping/reconstruction.py:95 |
| outlier filter | 20 neighbors / std ratio 3 | inherited src/fyld_scene_mapping/reconstruction.py:162 |
| grid / map limits / height statistic | 0.02 m / 20 m / 2,000,000 cells / maximum | inherited src/fyld_scene_mapping/mapping.py:10 |
| alignment / height slice | normal (0,-1,0), offset 0 m; no slice | inherited src/fyld_scene_mapping/experiments.py:21; declared axes, unverified gravity |
| CPU threads | default 8; preserve and record effective OMP_NUM_THREADS | inherited benchmark.py:8 |
| archive budget / expanded budget / entry cap | 2 GB / 2 GB / 100,000 entries | inherited scripts/download_sample_data.py:16 and src/fyld_scene_mapping/acquisition.py:21 |
| neural model / random seed | none / no stochastic first-party estimator | n/a deterministic CPU baseline; Open3D numerical nondeterminism disclosed |
| preview point cap / figure size / dpi | 15,000 / 13x8 inch / 140 | inherited src/fyld_scene_mapping/reporting.py:29 |
| positive reprojection Z gate / Open3D truncation | >0.01 m / 100 m after configured prefilter | inherited src/fyld_scene_mapping/reconstruction.py:78 and :60 |
| synthetic fixture | X[-2,2],Y[-1.5,1.5],.025 m steps; trench abs(X)<.4,abs(Y)<1,Z=-.6; box 1<X<1.5,abs(Y)<.3,Z=.4; missing X<-1,Y>.5 | inherited src/fyld_scene_mapping/experiments.py:224 |
| synthetic grid default / demo override | .05 m helper; .02 m demo | inherited src/fyld_scene_mapping/experiments.py:220 and test.py:27 |

## Verification

Contract tests: tests/test_tracking.py must produce overlap=1 for valid 5 m depth with max_depth=6 and reject an untextured plane without a pose. tests/test_mapping.py must retain trench height -0.6 m, box height 0.4 m and NaN unknowns; reject huge allocation. The deliberately scaled trajectory must fail rigid accuracy and pass disclosed similarity fitting. Archive traversal and metadata budgets must fail before writing. Review tests independently; existing baseline did not use TDD before the newer instruction arrived.

Before: 26 tests pass, estimated ATE 0.02315 m, 120/120 accepted; no complete research/docs. After: >=80% measured first-party package coverage, mathematical tests pass, actual A/B results documented, installed package imports outside checkout, exact setup commands verified. No geometry accuracy claimed without a surface reference.

## Receipts

| field | value |
|---|---|
| closing commit | Not applicable: workspace has no project Git repository; prototype retained locally |
| files changed | initial src, scripts and tests; research index, 21 source summaries, background guide and future-phase docs |
| test | 26 passed before review fixes; final checks pending |
| research verification | 21 individual source notes plus background and reading guide; zero broken local research links; fresh-context review found no material errors. ETH3D licence was checked during collection but its website was unavailable to the second reviewer. |
| before / after | 120/120 frames, ATE 0.02315 m before; final rerun pending |
| result | Superseded by Task 01 at the user's request. Research and preliminary prototype runs are retained; original integrated acceptance criteria were not completed. Final code review, package setup verification, >=80% coverage and post-fix A/B reruns remain unverified and must be performed if code is promoted into an experiment. |
