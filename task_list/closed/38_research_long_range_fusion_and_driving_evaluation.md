---
id: "38"
title: Research longer-range fusion and driving evaluation
status: closed
priority: MED
type: decision
approval_status: proposed; no execution authorised by Task30
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - research/README.md
  - task_list/README.md
docs:
  - research/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/03_camera_pose_estimation/src/dataset.py:124
  field: evidence and comparison gap
  baseline_value: "0 acquired driving evaluation datasets; adapter maximum retained depth below 4 m"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-07
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
| Current official source checks are already recorded in the research agenda | Task30 research section | this decision | research/README.md:171 |

Proposed comparison: Research probabilistic 3D boxes/extents, camera/stereo/LiDAR fusion, occupancy with unknown space, uncertainty-aware association and ego-motion/timestamp compensation. Assess KITTI raw/tracking versus nuScenes annotations/poses/visibility and coordinate conventions without downloading. Design stationary-object modality ablations first, separate calibration/timing/ego-pose perturbations then combined tests; add moving-object velocity/identity only after ego-motion control.

Necessary data/reference: Approved subset/terms/storage, calibrated timestamped sensors, explicit ego poses and uncertain independent 3D box/anchor references, range/view/visibility/separation strata. Task40 reference definitions apply; box annotations are not perfect surveyed centres. No dataset download or adapter range change in this task.

Measurements: Planned absolute location error and repeatability separately; full 3D versus ground-plane error; extent/occupancy error, uncertainty coverage/proper scores, merges/splits/unresolved cases, identity switches, runtime/memory and acquisition costs. Stratify by range/viewpoint/visibility/separation without invented pass thresholds.

Dependencies: None for research/design; acquisition/execution still require authorisation. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Large dataset storage, registration/licences, sensor/capture availability, time alignment, GPU/model terms and reference annotation labour.

Decision informed: Select a candidate dataset/subset and sensor comparison for authorised evaluation, or identify why required range/references are unavailable.

Official sources checked on 5 October 2026: KITTI raw-data and 3D object benchmark pages, the nuScenes schema, and official detection/tracking evaluation pages. The research agenda records what they provide, range/metric limitations, and how the two candidates inform later Task41 trial selection. No dataset, model, threshold, sample size or acquisition choice was approved.

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
| Closing commit | `14957e6` (research record) |
| Files changed | `research/README.md`; `task_list/README.md`; this task record |
| Test status | Documentation/source check only; no implementation or experiment run |
| Before measurement | 0 acquired driving evaluation datasets; adapter maximum retained depth below 4 m |
| After measurement | 2 dataset candidates checked against official documentation; 0 downloads or local runs |
| Delta | nuScenes selected as the stronger multi-sensor moving-track control candidate; KITTI retained as a stereo/LiDAR/vehicle-pose control; neither validates static worksite inventory or full surface-position accuracy |
| Decision-gate outcome | Research decision recorded. Owner review is pending to accept or revise the Task41 trial-selection recommendation. Any subset, access terms, storage, capture, local settings and execution remain separate owner decisions. |

Independent source review and decision recording are complete. To close: the owner should accept or revise the recommendation for Task41; only then can a separately scoped task request data access, select a subset, and propose an experiment.

## Closure, 2026-10-07

Closed under Task60 with owner approval. Earlier `still open because` lines above are superseded by this note. The fixed-snapshot external validation is waived: the board README says those review sessions are not relaunched automatically, and a source claim is rechecked by whichever task uses it. Street-range driving evaluation is outside the current phone walkthrough scope; no follow-up is scheduled.
