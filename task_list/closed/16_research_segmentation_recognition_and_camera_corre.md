---
id: "16"
title: Research segmentation recognition and camera correction comparisons
status: closed
approval_status: pending_review
priority: MED
type: decision
blocked_by: []
blocks: []
verification_test: research/README.md
plan_reviewed: null
files:
  - research/README.md
  - experiments/06_object_recognition/README.md
  - experiments/03_camera_pose_estimation/README.md
  - task_list/closed/16_research_segmentation_recognition_and_camera_corre.md
  - task_list/open/17_prepare_labelled_revisit_inputs_and_object_observa.md
  - task_list/open/18_evaluate_object_detection_on_frozen_labelled_obser.md
  - task_list/open/19_evaluate_classical_and_edge_device_object_segmenta.md
  - task_list/open/20_compare_object_appearance_matching_across_viewpoin.md
  - task_list/closed/21_associate_object_identities_with_geometry_and_appe.md
  - task_list/closed/22_build_recorded_video_camera_surface_and_inventory_.md
  - task_list/stale/23_embed_interactive_surface_review_and_explain_depth.md
  - task_list/closed/24_recover_and_reproduce_android_apk_build_inside_cap.md
  - task_list/open/25_compare_feature_seeded_odometry_and_verified_camer.md
docs:
  - research/README.md
  - experiments/06_object_recognition/README.md
  - experiments/03_camera_pose_estimation/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Research segmentation recognition and camera correction comparisons
  baseline_value: "0 approved stage 06 comparison protocols"
  target: "1 approved protocol and availability-checked shortlist spanning the 5 stage 06 experiments"
created: 2026-10-03
last_updated: 2026-10-07
superseded_by: null
---

# Task 16: Research segmentation recognition and camera correction comparisons

## In plain English

Check which recognition and segmentation methods can answer the next experiments. Separate methods that draw boundaries from models designed for small devices. Produce a shortlist and a measurable test protocol before choosing settings.

## What

Research classical segmentation, compact prompted masks, detectors, appearance matching and camera correction; publish evidence and an executable-comparison protocol, not another unranked literature list.

## Why

Methods and claims have different inputs, hardware and outputs. The public SqueezeSAM repository was checked on 3 October 2026 and contains no implementation, checkpoint or licence; classical boundaries do not identify inventory objects.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Existing research separates paper and local evidence | research index | experiment plans | research/README.md:3 |
| Current camera adapter is existing Open3D odometry | CPUOdometry | Task 25 | experiments/03_camera_pose_estimation/src/backend.py:41 |

The research shortlist and five-experiment protocol are documented in the existing research, stage06 and stage03 READMEs. Task17 must inventory actual footage and return missing-scenario gaps before labels or frame selections are frozen. This task does not run models, download weights, execute GPU work or alter Task13 settings.

The owner later directed: close Tasks16 and 17 autonomously, continue overnight, and GPU tests are authorised. This supersedes the earlier pending-review instruction. Accept the documented research design; retain YOLO26x and defer unavailable learned candidates without downloading weights. Numerical execution choices belong in the task that runs them, with dated delegated-choice provenance.

## Invariants and recovery

invariants n/a: research-only decision; no model execution, downloads or input mutation.

## Hyperparameters

hyperparameters n/a: research and protocol documentation only; no inference, new settings or experiment entry point. Before any later run, audit and record every selected model, prompt, split, seed, resolution, threshold, association rule, resource cap and scoring tolerance with owner-confirmed or inherited provenance.

## Verification

Documentation contract: research/README.md, experiments/06_object_recognition/README.md and experiments/03_camera_pose_estimation/README.md were checked against the primary source links and traced local code. The shortlist records candidate version or unverified status, code/weight availability, licence, inputs, prompts and hardware-qualified claims. Each of the 5 stage 06 experiments defines inputs, evaluator-only references, controls, failure cases and costs. No paper timing is described as a project phone result.

Before: 0 approved stage 06 comparison protocols. Target: 1 approved protocol and availability-checked shortlist spanning the 5 stage 06 experiments. Targets count completed evidence/control artifacts; they are not operational accuracy thresholds. No performance improvement is assumed. At implementation, write meaningful controls first and observe failure, or obtain independent test review. Cover expected values, empty/one/many boundaries, invalid input, failure/recovery and reference separation. Changed implementation coverage must be at least 80%; lint/type and required integration/browser checks must pass. Record actual measurements and all unresolved follow-ups before closure.

## Receipts

| Field | Value |
|---|---|
| Closing commit | `de324e5` (research record; no code) |
| Files changed | research/README.md; experiments/03_camera_pose_estimation/README.md; experiments/06_object_recognition/README.md; Tasks 16 to 25 records |
| Test status | No tests run; read-only source-to-documentation trace completed |
| Before measurement | 0 approved stage 06 comparison protocols |
| After measurement | 1 accepted research shortlist and five-experiment protocol; 0 runs by Task16; Task17 inventory separately records available and missing scenarios |
| Delta | +1 accepted research design; no performance improvement claimed |
| Decision-gate outcome | Research shortlist and draft protocol are recorded. Per the owner's later direction on 4 October 2026, Task16 remains pending review; exploratory Task27/28/20/21 work does not approve its broader protocol. No new weights were used. |

tests n/a: documentation-only source review; no implementation changed.

## Owner direction, 3 October 2026

Earlier narrow YOLO approval did not approve this protocol. The subsequent instruction ?close 16 and 17 yourself? superseded pending review and delegated protocol completion. Overnight GPU tests were authorised. Task17 proceeded next; unavailable recorded scenarios were reported as gaps, not fabricated. Task13's frozen settings and unfinished work remain intact.

## Later owner direction, 4 October 2026

Exploratory replay and association work do not approve this broader protocol. Keep Task16 in pending review until the owner accepts it. Task17 and the bounded exploratory trials remain separate evidence; they do not close this approval question.

## Closure, 2026-10-07

Closed under Task60 with owner approval. Earlier `still open because` lines above are superseded by this note. The fixed-snapshot external validation is waived: the board README says those review sessions are not relaunched automatically, and a source claim is rechecked by whichever task uses it. The broad protocol is not adopted as a gate on other work; Task56's measured failures choose any later comparison.
