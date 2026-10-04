---
id: "38"
title: Research longer-range fusion and driving evaluation
status: open
priority: MED
type: decision
approval_status: proposed; no execution authorised by Task30
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - research/README.md
docs:
  - research/README.md
baseline_metric:
  source: experiments/03_camera_pose_estimation/src/dataset.py:124
  field: evidence and comparison gap
  baseline_value: "0 acquired driving evaluation datasets; adapter maximum retained depth below 4 m"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task38: Research longer-range fusion and driving evaluation

## In plain English

Plan a fair longer-range evaluation using driving datasets and sensor comparisons. Keep stationary object inventory separate from tracking moving objects. Indoor depth results cannot establish street-scale accuracy.

## What

Question: Which sensor/data/uncertainty representation can test the intended range, and what can KITTI/nuScenes references actually establish?

Proposed research/decision task. No implementation, execution or acquisition is bundled into it.

## Why

Existing evidence: Current depth adapter excludes >=4 m and no driving dataset is acquired. Task30 primary review covers probabilistic detection, LaserNet, BEVFusion, occupancy and KITTI/nuScenes schemas/metrics. Detection box centres and visible-surface anchors differ.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Existing range limit is explicit | TUM adapter | range suitability | experiments/03_camera_pose_estimation/src/dataset.py:124 |
| Dataset selection already has an owner | dataset README | acquisition planning | experiments/datasets/README.md:5 |

Proposed comparison: Research probabilistic 3D boxes/extents, camera/stereo/LiDAR fusion, occupancy with unknown space, uncertainty-aware association and ego-motion/timestamp compensation. Assess KITTI raw/tracking versus nuScenes annotations/poses/visibility and coordinate conventions without downloading. Design stationary-object modality ablations first, separate calibration/timing/ego-pose perturbations then combined tests; add moving-object velocity/identity only after ego-motion control.

Necessary data/reference: Approved subset/terms/storage, calibrated timestamped sensors, explicit ego poses and uncertain independent 3D box/anchor references, range/view/visibility/separation strata. Task40 reference definitions apply; box annotations are not perfect surveyed centres. No dataset download or adapter range change in this task.

Measurements: Planned absolute location error and repeatability separately; full 3D versus ground-plane error; extent/occupancy error, uncertainty coverage/proper scores, merges/splits/unresolved cases, identity switches, runtime/memory and acquisition costs. Stratify by range/viewpoint/visibility/separation without invented pass thresholds.

Dependencies: None for research/design; acquisition/execution still require authorisation. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Large dataset storage, registration/licences, sensor/capture availability, time alignment, GPU/model terms and reference annotation labour.

Decision informed: Select a candidate dataset/subset and sensor comparison for authorised evaluation, or identify why required range/references are unavailable.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

invariants n/a: dedicated research and evaluation-design task; runtime changes, downloads and moving-object tracking implementations require separately reviewed tasks.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Dataset modality/split/reference/metric claims have primary citations; stationary inventory and moving tracks have separate scoring; format range is never reported as sensor accuracy; no unapproved acquisition occurs.

Before: 0 acquired driving evaluation datasets; adapter maximum retained depth below 4 m. After: no new measurement yet. Provide primary-source traceability, explicit acquisition gaps and a reviewable decision; no runtime result is implied.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | No implementation tests or experiment executed |
| Before measurement | 0 acquired driving evaluation datasets; adapter maximum retained depth below 4 m |
| After measurement | No new experimental result |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Proposed; review/settings/references/acquisition authorisation outstanding |

still open because the investigation and its reference/decision requirements are not complete.
