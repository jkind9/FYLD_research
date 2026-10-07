---
id: "48"
title: Paired validation of median-point and Task32 support association
status: closed
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - task_list/closed/48_paired_validation_of_median_point_and_task32_suppo.md
  - task_list/README.md
  - C:/Users/jkind/AppData/Local/Temp/claude/c--Users-jkind-Documents-02-Work-01-fyld-mobile-depth-estimation-tracking/b26acd3f-d0ce-46e0-832e-1538bd5e9231/scratchpad/compare_association.py
  - C:/Users/jkind/AppData/Local/Temp/claude/c--Users-jkind-Documents-02-Work-01-fyld-mobile-depth-estimation-tracking/b26acd3f-d0ce-46e0-832e-1538bd5e9231/scratchpad/run_timing.sh
  - C:/Users/jkind/AppData/Local/Temp/claude/c--Users-jkind-Documents-02-Work-01-fyld-mobile-depth-estimation-tracking/b26acd3f-d0ce-46e0-832e-1538bd5e9231/scratchpad/run_regions.sh
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/**
docs:
  - task_list/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/06_identity_policy/README.md (Task46 published result)
  field: median-point identity outcomes on the 60-frame desk replay
  baseline_value: "55 IDs, 346 matched, 56 unresolved of 457 proposals"
  target: "Paired support-aware outcomes on the same inputs; no accuracy target"
created: 2026-10-05
last_updated: 2026-10-07
superseded_by: null
---

# Task 48 — Paired validation of median-point and Task32 support association

## In plain English

Two ways of deciding whether a newly detected object is one we have already seen are compared on exactly the same recorded frames. One uses a single middle point per detection box; the other compares the whole set of measured depth points inside the box. The comparison counts how often each method keeps, starts, or refuses to assign an identity, and how long each decision takes. It does not claim either method is more accurate, because the recording has no independently measured object positions.

## What

A read-only evaluator rebuilds per-box depth samples from the verified Task22 source run, runs `pilot.replay.associate_frame` (median point, Task46 birth policy) and `07_spatial_uncertainty.association.associate_frame` (support-aware) frame by frame on identical detections, depth, poses and transforms, and publishes the evaluator, result and lineage into a new verified run under the existing Task32 experiment. The six-frame Task17 label fixture is excluded from the 60-frame comparison because its frame IDs occur in that recording. The existing Claude-session scratch files remain unchanged. No model inference, source change, sample change or demo rebuild is part of this comparison.

## Why

Task32 handed the support-aware variant to a parallel evaluator without a repository-published run. This task reproduces the paired descriptive measurements, pins all input and provisional-reference hashes, records full processing timing, and states why accuracy remains unvalidated.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Median-point baseline and Task46 birth policy | `pilot/replay.py` `associate_frame` | cached replay, this script | experiments/06_object_recognition/pilot/replay.py:127-302 |
| In-memory replay of the saved ledger with stable observation IDs | `cached_replay.recompute` | Task46 publication, this script | experiments/06_object_recognition/experiments/06_identity_policy/cached_replay.py:241 |
| Pinned source run and ledger hashes | cached replay constants | this script | experiments/06_object_recognition/experiments/06_identity_policy/cached_replay.py:23-32 |
| Box-sample export with pose-revision lineage | `localise_box_samples` | this script | experiments/06_object_recognition/pilot/localisation.py:49 |
| Support-aware association | `07_spatial_uncertainty/association.py` `associate_frame` | this script | experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py:450 |
| Frame loading and depth policy | `dataset.load_frame` | replay, this script | experiments/03_camera_pose_estimation/src/dataset.py:110 |
| Read-only run verification | `verify_run` | this script | experiments/shared/runs.py:59 |

## Hyperparameters

| Name | Value | Source |
|---|---:|---|
| Median association distance gate | 0.35 m | inherited `experiments/06_object_recognition/pilot/replay.py:38` |
| Ambiguity margin | 0.05 m | inherited `experiments/06_object_recognition/pilot/replay.py:39` |
| Support depth-layer gap | 0.08 m | inherited Task32 setting in `experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py:244` |
| Duplicate-box IoU used for reporting | 0.90 | inherited `experiments/06_object_recognition/experiments/04_geometry_identity/run.py:103` |
| Paired outcome repeats | 7 per method | inherited from the existing scratch evaluator; timing only, no setting sweep |
| Detailed timing repeats | 7 median-point association, 3 instrumented support association, 1 plain support association; 3 input-stage repeats | inherited from the existing timing script; timing only |
| Region probe | 0.02 m voxels and 0.02 m depth tolerance | inherited exploratory values in the existing region script; not tuned or acceptance limits |

## Invariants and recovery

invariants n/a: read-only evaluation; output is a scratchpad JSON that can be regenerated.

## Verification

Contract checks: the new run verifies through `experiments.shared.runs.verify_run`; source and Task46 manifests verify; every frame file hash matches the selection and dataset member records; stored median positions and poses are reproduced from the original files; the in-memory Task46 replay matches the published run per detection; repeated runs give identical IDs. The run carries the evaluator copy, input/reference hashes, settings, environment, timing, result and source snapshot. The Task17 six-frame fixture is not read as a score reference in the 60-frame comparison. No unit-test change applies to this read-only evaluation.

The concise status and run location are recorded in `task_list/README.md`; the run folder contains the full result and provenance.

## Receipts

| field | value |
|---|---|
| closing commit | `14957e6` |
| files changed | This task record, `task_list/README.md`, and verified publication run `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68`; the existing Claude scratchpad remains unchanged |
| test / verification | Comparison reproduced deterministically across 7 repeats per method; Task46 replay matched all 457 detections; 120 selected RGB/depth files rehashed with 0 mismatches; source and Task46 runs verified; copied 124 Task22 input files checked; publication manifest verified (327 files). No unit test changed because this is a read-only experiment. |
| before / after | Earlier scratch report: median point 55 IDs, 346 matched, 56 unresolved; support-aware 30 IDs, 319 matched, 108 unresolved. Reproduced: same counts. The 60-frame replay has no independent object-position/count reference, so accuracy and physical count remain unavailable. |
| result | Support-aware assigned fewer proposals and abstained more often: 55 competing-support, 23 ambiguous, 20 already-assigned, and 10 no-support abstentions. Seven-repeat association medians: 8.50 ms total (0.0186 ms/proposal) for median point and 78.46 s (171.7 ms/proposal) for support-aware. Do not promote fewer IDs as better counting. |
| decision-gate outcome | Technical result awaits Claude's pinned independent reproduction/review. Owner approval and independent object references remain separate and outstanding. |

Notes / caveats / follow-ups:

- The old scratch result used Task17's six-frame provisional labels in an identity diagnostic. Their frame IDs overlap the 60-frame Task22 source, so that diagnostic is excluded from the published paired result. The labels are agent-reviewed proposals, not human ground truth. The Task48 comparison makes no identity-accuracy claim.
- Task32 per-decision `processing_time_ms` times only record assembly (median 0.51 ms) and omits candidate scoring and assignment, which dominate (243 ms per detection).
- A box with two or more depth layers can never start an identity in the support variant (171 of 457 boxes, including 30 of 32 chairs).
- The first computation container was marked failed after all three measurements completed because its final check counted directories as files. It remains unchanged. A separate publication run records that failure, rechecks every copied source file, carries the original execution timing, and passes run-manifest verification.
- The detailed timing run measured median-point processing at 1.35 s and support-aware processing at 96.64 s for frame decode, pose lookup, geometry/sample construction, and association. Support association alone took 80.05 s in the plain timing pass. Complete support cost per proposal had median 80.67 ms, p95 514 ms, and max 10.36 s. The module-reported timer median was 0.323 ms and covered 1.73% of complete measured cost. These are desktop CPU timings, not phone results.

### Reproduced timing record, 2026-10-05

Same inputs and lineage as above; IDs were identical across all repeats. Desktop CPU (32 logical CPUs, Python 3.12.10, NumPy 2.4.2, SciPy 1.17.1); another session may share the machine. These are not phone timings.

| Stage (60 frames, 457 boxes) | Median point | Support-aware |
|---|---:|---:|
| Detector inference, recorded upstream (GPU, not re-measured) | 2.38 s + 1.32 s model load | same |
| Frame decode | 0.414 s | 0.414 s |
| Pose lookup | 0.022 s | 0.022 s |
| Box geometry / support sample export | 0.91 s | 2.38 s |
| Sample records (`BoxObservation` tuples) | n/a | 13.77 s |
| Association | 8.50 ms | 78.46 s (plain), 80.05 s (instrumented median) |
| CPU total excluding inference | 1.354 s | 96.64 s |

Support association, median of 3 instrumented repeats: candidate construction 10.36 s; edge scoring 67.97 s, of which nearest-sample distance 65.57 s; assignment 4.43 ms; duplicate check 0.81 ms; other work 1.80 s. The plain uninstrumented support pass took 80.05 s. Complete cost per decision (including an equal share of frame-level work): median 80.67 ms, p95 514 ms, max 10.36 s (dining table). The module timer covered 1.73% of measured complete cost.

### 3D region probe, 2026-10-05 (exploratory, owner direction)

Each box was turned into a 3D region: the box's pyramid between its nearest and farthest measured depth, minus space the depth camera saw as empty. Overlap was then measured against each median-point track's region (all its earlier views intersected). Probe values: 2 cm voxels and 2 cm depth tolerance, chosen for this probe only and not tuned. The probe took 10.81 s total.

- Matched detections: the assigned track had the largest region overlap in 224 of 258 cases (13 had none).
- Later same-class births: 15 of 37 overlap an existing same-class region.
- Support abstentions on competing depth layers: 18 of 55 overlap exactly one track; 19 overlap none.
- The frame-32 extra cup box (`object-0011`) does not overlap the cup's region.
- Strict all-view intersection is too brittle for size: 13 of 55 tracks emptied, and the cup shrank from 429 to 5 voxels over 16 views. A size estimate needs tolerant fusion (vote or occupancy probability) and handling of the known colour/depth timing offset and box jitter.
- Evidence: `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/output/timing_result.json` and `regions_result.json`; source scripts and original failed execution metadata are copied into the run. The run manifest is verified.
- still open because Claude's independent technical validation and owner review are pending. The validated package contains no independent object-position or physical-count reference, so it cannot establish identity accuracy or better counting.

## Closure, 2026-10-07

Closed under Task60 with owner approval. Earlier `still open because` lines above are superseded by this note. Code is committed in `14957e6`. The recording has no independent object positions, so no accuracy claim is made. Independently scored accuracy and complete timing belong to Task56; no further work on this method is scheduled unless Task56 shows identity errors it could fix.
