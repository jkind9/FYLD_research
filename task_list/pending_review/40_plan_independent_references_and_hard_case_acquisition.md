---
id: "40"
title: Plan independent references and hard-case acquisition
status: pending_review
priority: HIGH
type: decision
approval_status: proposed; no execution authorised by Task30
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: 2026-10-05 PASS
files:
  - task_list/pending_review/40_plan_independent_references_and_hard_case_acquisition.md
  - experiments/06_object_recognition/datasets/README.md
  - task_list/README.md
docs:
  - experiments/06_object_recognition/datasets/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/06_object_recognition/datasets/README.md:5
  field: evidence and comparison gap
  baseline_value: "6 provisional frames; 0 independent desk physical-centre references"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-05
superseded_by: null
---

# Task40: Plan independent references and hard-case acquisition

## In plain English

Plan the independent measurements and additional captures needed to judge the next experiments. Check what existing data can supply before requesting new recordings or hardware. Keep uncertain reference answers explicit.

## What

Question: Which independent identity/mask/anchor/extent/surface references and hard cases are necessary and practical for the proposed comparisons?

Proposed research/decision task. No implementation, execution or acquisition is bundled into it.

## Why

Existing evidence: Task17 has six provisional agent-reviewed frames, complete selected cup coverage and monitor positive subset. Task29 has no independent physical-centre reference; TUM has no acquired dense reference surface. Task17's 13-case registry records missing rotation/lighting/movement/origin-reset/phone scenarios.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Frozen provisional labels, calibration and scenario gaps already exist | `desk_smoke_v1.json`, prepared by the dataset publisher | all new evaluators | experiments/06_object_recognition/datasets/desk_smoke_v1.json:2; experiments/06_object_recognition/datasets/prepare.py:23,201-203 |
| Source RGB/depth payload is copied and checked against frozen hashes | Acquired TUM Freiburg1 desk files | dataset publisher | experiments/06_object_recognition/datasets/prepare.py:103-116; experiments/06_object_recognition/datasets/README.md:25 |
| Current desk spread is not absolute error | Task29 JSON | anchor/reference design | experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:16 |
| Independent ICL surface already acquired | stage04 | first surface control | experiments/04_surface_reconstruction/README.md:151 |
| Redmi exposes no advertised concurrent set; this is capability evidence, not an image or physical reference | Task08 device intake | Conditional RGB acquisition proposal | experiments/01_camera_capture_delivery/runs/redmi/session-1791186245035_f881c553/report.json:2966 |

Proposed comparison: First inventory existing references, independence and metadata. Design human-checked pixel masks and physical identity review with disagreements; survey explicitly defined anchors, visible surfaces and complete dimensions with recorded instrument uncertainty/frame transforms. Plan a minimal static capture bank with similar co-visible neighbours, duplicate boxes, identical objects only in separate views, look-away/return, occlusion, changed lighting/rotation, moved objects, missing depth and camera reset. Plan independent translated viewpoints/new sessions and source-disjoint enrollment/validation/test; do not invent frame counts, tolerances or thresholds.

Necessary data/reference: Owner access to objects/room, capture permission, calibrated sensors or verified existing recording, timestamps/depth lineage, independent instrument/surface reference, human annotation/review labour. Apple LiDAR or outdoor driving acquisition is optional separate Task37/38 decision. Preserve Task13 hold-out and frozen settings.

### Owner inputs before the first reference-backed comparison

The current six-frame TUM desk set already supplies a white-cup look-away/return case and two similar-looking monitor enclosures that are distinct in the inspected views. It is one previously inspected session. Its identity labels are provisional, its polygon masks are coarse, and it has no surveyed object centre or physical-size reference. Reuse those cases only for descriptive checks until a human reviews the labels; do not score mask accuracy or physical-position error from them.

For a new controlled scene, the owner needs to provide:

1. **Scene access and identity decisions.** Choose stationary objects the owner can inspect, including one object to revisit and a similar-looking but distinct neighbour. Record which objects are physically identical, distinct or genuinely ambiguous. Keep object identity separate from the object's measured location if it is moved.
2. **A physical coordinate reference and frame link.** Mark a stable origin and axes using visible room or table edges. For each stationary object, measure a defined physical anchor such as the centre of its support footprint relative to that origin. Record the measurement instrument, units, displayed resolution, calibration/check information, repeated readings and a justified uncertainty that includes known instrument and setup limits. Record the reference frame ID, axis direction and transform into the method's world frame, including the transform source and uncertainty. Determine this transform from independently measured control data that is not used as a scored object anchor. If no independent frame link is available, mark absolute position error unavailable and report only the relative or repeatability measures that remain valid; do not use the phone's own map as physical truth.
3. **Observed dimensions and 3D boundaries.** Measure the dimensions that are fully visible and name the endpoints used. Record surveyed 3D endpoint or corner coordinates in the survey frame, the object's orientation or measurement axes, length, width and height, and uncertainty for coordinates, orientation and measurements. Mark any unavailable boundary or dimension explicitly; do not call a partial view the object's full size.
4. **Human image references.** Review instance identities in the source RGB images without looking at model predictions. Draw a per-instance foreground mask for frames used in mask scoring. Record visibility, occlusion and ambiguity; preserve reviewer disagreements instead of forcing a label. Keep these evaluator annotations separate from method inputs.
5. **Independent capture sessions.** After the Redmi's capabilities are known, repeat the static scene from translated viewpoints in separately started sessions. Keep each session intact. If any setting or calibration is selected from data, reserve separate sessions for enrollment, validation and held-out evaluation; never use the held-out session to choose settings. The already inspected TUM session can remain a development/reference control, but it cannot count as a blind held-out session. Include a look-away/return, co-visible similar neighbours, an occlusion and changed object orientation where available. Confirm the number of sessions and captures before acquisition without splitting adjacent frames across partitions.

The minimum owner-supplied physical measurements are an independently measured anchor and observable dimensions for each chosen object, with instrument details and uncertainty. A 3D boundary comparison also needs surveyed endpoint or corner coordinates, object orientation/axes, and their uncertainty in the survey frame. Any absolute position or boundary comparison needs an independently justified survey-to-method frame transform. The capture protocol does not set a frame count, accuracy threshold or acceptance tolerance; those remain owner decisions before numerical comparison.

### Practical reference plan

Use the existing files only for the questions their references can answer:

| Source | Suitable use | Not a substitute for |
|---|---|---|
| Task17's six TUM desk frames | Provisional identity/revisit smoke control; original RGB and registered depth with the existing calibration and poses | Human-reviewed identities or masks, a surveyed object anchor, full dimensions, or a blind session |
| Task45's 571 posed TUM desk frames | Camera-path input and box-wobble/measurement-consistency context; keep its 573-pair source and two refused timestamps explicit | Independent object-position truth: its depth and detections are the tested inputs, and its boxes are not physical anchors |
| COCO val2017 outlines | Image-space box placement and visible-outline checks on the recorded validation set; retain Task45's checkpoint-selection caveat because the detector makers used this set to choose the checkpoint | Persistent identity, metric 3D position, complete dimensions, or a held-out detector result |
| ICL-NUIM surface reference | Existing independent surface-reconstruction control on its own scenes | Object identity or surveyed anchors in the desk/phone scene |
| ScanNet++ | Candidate source for per-view labels and registered scene surfaces if the owner obtains and approves access terms | Owner-scene identity and phone sessions unless those exact cases and permissions are covered |

Before acquisition, make a reference ledger with one row per object-view and these fields: dataset/scene/session and source frame IDs; stable physical object ID; reviewed identity relation (`same`, `different`, `ambiguous`, or `unavailable`); visibility/occlusion; mask reviewer and version; object anchor definition and 3D coordinates; observed extent; surveyed endpoint/corner coordinates and orientation for each measured boundary; coordinate, orientation and instrument uncertainty; reference frame; transform ID; instrument/reference source; uncertainty record; and whether the row is calibration, enrollment, validation, or held-out evaluation. Keep this ledger and all masks/measurements evaluator-only. Method inputs must not contain reference IDs, masks, anchors, transforms fitted from scored targets, or held-out labels.

| Question | Required reference and measurement | Report separately |
|---|---|---|
| Identity | Owner-confirmed physical object registry plus reviewed same/different/ambiguous relations, including false-alarm candidates and unlabelled/unavailable cases | False merges, false splits, duplicate claims, unresolved pairs, missed objects, return recovery, and coverage; do not count ambiguous truth as a forced error |
| Image placement and visible extent | Human-reviewed per-instance RGB masks for selected frames; retain image size, pixel convention, visibility and reviewer disagreements | Box centre/edge displacement in pixels and relative to object diagonal; mask overlap, object outline coverage, excess background, truncation and clutter. Task45's COCO outputs remain a separate source and method |
| Absolute object position | A predeclared physical anchor per object (for example, centre of its support footprint), measured in metres in a surveyed room/table frame; repeated readings and instrument uncertainty | 3D Euclidean and axis-wise anchor residuals; distinguish reference uncertainty from method error and report missing/unobservable anchors as unavailable |
| Visible 3D surface | Independent calibrated surface samples/scan with scene and view lineage, linked to the RGB view; a sensor's own depth may be an evaluated input but cannot also be its independent surface truth | Surface distance and coverage by view/range, with reference density and uncertainty; no surface score if no independent scan or suitable benchmark exists |
| Full object size and 3D boundary | Independently measured named endpoints or corners with 3D survey-frame coordinates, orientation/measurement axes, uncertainty and visibility status | Score fully observed dimensions and 3D boundary separately after the independent frame link is fixed. Do not infer full size or boundary from a partial image or visible-surface spread |

### Frames, transforms and uncertainty

Use metres and right-handed 3D frames. Name the axes and origin for the room/survey frame, each camera optical frame (x right, y down, z forward), each benchmark/motion-capture frame, and each method world/segment. Store transforms with an explicit direction such as `T_world_from_survey`; document whether points are column vectors and compose transforms in that order. Keep image coordinates in source pixels with pixel-centre convention and depth in metres with its axial/radial meaning stated. A camera-to-world transform must name its timestamp, pose source, interpolation rule and revision.

Link the physical survey frame to each method/benchmark world frame using independently measured control targets or surveyed landmarks. Record the fitted rigid transform, control-point IDs, residuals, estimation method and transform covariance. Do not fit this transform from the object anchors that will be scored. If the independent link is missing or fails its predeclared quality check, absolute position is unavailable; relative repeatability can still be reported with its frame clearly named. For a new phone map with an arbitrary origin, estimate and freeze this link from the control set before evaluation. Never use the method's own map or detector/association output as the physical reference.

Each uncertainty record must name the source and whether it is random or systematic: instrument make/model and identifier; calibration/check date and result; display resolution; repeated readings; stated or estimated bias/repeatability; chosen interval and its basis; survey-control residuals and transform covariance; camera calibration/depth scale and timestamp/pose uncertainty; and mask-reviewer disagreement or visibility uncertainty. Preserve raw readings and the method used to combine them. Propagate available transform/reference covariance to the scored anchor, or use a documented resampling method that preserves shared calibration errors. Keep reference uncertainty separate from observed method residuals. If an uncertainty cannot be supported, mark it unknown instead of assigning a convenient value.

### Hard-case capture matrix and splits

Capture the cases below as deliberately labelled events, not as incidental frame counts. Record the truth before inspecting predictions. Keep each continuous capture session, all derived images, and every annotation version in one partition.

| Case | What it exposes | Independent truth needed |
|---|---|---|
| Same object disappears behind an obstruction or leaves the view, then returns | Identity continuity versus a new ID; separate out-of-view from physical removal | Owner-confirmed object ID and explicit visible/absent/occluded state per event |
| Two visually similar, physically distinct objects are visible together | False merge and one-to-one assignment errors | Owner-reviewed distinct IDs; individual masks and anchors |
| Visually identical objects appear only in separate views | Whether appearance alone invents continuity | Owner's physical registry/handling log; otherwise truth is explicitly ambiguous |
| Same object is deliberately moved between views | Identity must persist while position changes | Stable object ID plus separately remeasured anchor after movement |
| Duplicate/overlapping boxes cover one object; nearby boxes cover neighbours | Duplicate counting and wrong-neighbour association | Exhaustive instance list, masks and identities for the full view |
| Foreground object overlaps background in depth, including a thin or planar object | Wrong-surface position and support ambiguity | Independent surface/anchor reference; mark layers that cannot be measured separately |
| Object is partly hidden or cut off by image edge | Visible support versus complete extent; missing depth | Visibility mask, explicit occlusion/truncation, only measured visible dimensions |
| Camera changes viewpoint/range, returns, or starts with a reset/new map origin | Coordinate-transform and revisit errors | Survey controls visible/measurable across sessions and frozen transform lineage |
| Lighting/exposure and object orientation change | Identity/mask fragility versus geometric location | Same reviewed identity; per-view masks and orientation/event notes |
| Depth holes, depth boundary, timestamp gap or pose unavailable | Correct unavailable/error path instead of false certainty | Raw depth/timestamps and independent pose/surface reference where available |

For any setting selected from data, use whole-session enrollment/development, validation and held-out evaluation partitions. Keep calibration/control-target observations separate from scored anchors, and keep object/session groups intact across all stages. Any session, source frame or derivative already read, labelled, scored or used for tuning by an earlier task is development evidence for later claims based on that material. This includes every task that used Freiburg1 desk, not only a fixed list of task IDs. Check source provenance before assigning a partition. If there are too few genuinely independent sessions or object instances for a split, report that limitation and do not describe the result as held out. Owner must approve the session and object counts before collection; this design selects no sample size, tolerance or pass threshold.

Before collecting anything, owners must decide: scene/object access and permissions; which objects are physically same, distinct or ambiguous; the anchor definition for each shape; the survey frame and axis/origin convention; access to a calibrated measuring instrument and independent surface scanner or an approved reference dataset; mask-review staffing and adjudication; phone/device access and whether a separate rear-camera control passed; and session/object counts, acceptable reference uncertainty, comparison tolerances and decision thresholds. Record costs and unavailable items. A missing owner decision pauses that part of the plan rather than being filled with guessed labels or measurements.

### Redmi constraint from Task08, 5 October 2026

Task08's received `session-1791186245035_f881c553` passes export validation and confirms model 2201116TG/Android 13. Only rear ID `0` and front ID `1` are exposed, with no physical IDs or advertised concurrent sets. Its pair attempt is SKIPPED. No DEPTH16 stream is advertised; ARCore is absent from the APK, so runtime depth/pose is untested. The session contains no images. The capture README's "Redmi device result, 5 October 2026" section owns the full result and intake hashes; the raw source is listed in the reuse evidence table above.

The smallest useful next device check is a separately exported single-rear-camera control. If that passes, propose stationary-object RGB views first: revisit one object, show its similar neighbour in the same view, and include identical-looking objects seen only in separate views with owner-supplied identity evidence. Acquire separately started sessions as described above after settings/splits are agreed. A longer recorder still needs implementation or a separately verified recording tool; this one-shot APK is not a walkthrough recorder. Do not require stereo in that proposal or assume depth/poses exist. RGB can support reviewed identity/mask evidence; metric position needs a separately verified depth/pose route and independent survey frame link. The required anchors, dimensions, uncertainty and human reviews above remain absent.

Measurements: Reference coverage matrix, identity certainty/disagreement, masks usable for formal scoring, instrument uncertainty, survey-to-method frame transform and its uncertainty, registration versus scored-anchor separation, coordinate/time consistency, independent session/view coverage, acquisition costs and exact unavailable cases. No experiment accuracy result is claimed by the plan.

Public labelled data first, 5 October 2026: for detection and mask references in clutter, check what public labelled data already supplies (Task45 uses COCO val2017 outlines; ScanNet++ per-frame labels need an owner access request) before asking for human-drawn masks of new captures. They cannot replace surveyed physical anchors, the owner's own scenes, or held-out phone sessions. Record every reference in Task44's report with its kind (`independent`, `provisional`, `analytic`) so provisional and independent scores are never compared as if equal.

Dependencies: None for research/design; acquisition/execution still require authorisation. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Survey instrument/hardware access, human annotation and repeated independent review, capture labour/storage/permissions and missing depth/visibility. Prefer minimum acquisition that isolates a cause.

Decision informed: Approve or revise the reference/capture plan and authorise only needed acquisition; enable Tasks31-35 with stated reference limitations.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| `desk_smoke_v1.json` | `prepare.py` | Frozen labels, calibration, partitions, source hashes and scenarios | Frozen annotation file persists | experiments/06_object_recognition/datasets/prepare.py:23 |
| Acquired TUM Freiburg1 desk payload | `prepare.py` | Original RGB/depth bytes checked against the annotation hashes | Original files persist outside derived publication | experiments/06_object_recognition/datasets/prepare.py:103-116 |
| `prepare.py` | Isolated comparison/evaluator | Versioned publication containing method inputs separately from evaluator annotations | Staging output is verified and renamed to its final destination; failed output remains unpublished | experiments/06_object_recognition/datasets/prepare.py:201-203,208 |
| Proposed reference owner | Future evaluator | Independently reviewed labels and measurements with units, frames and uncertainty | Versioned reference files persist; disagreement and unavailable values remain explicit | experiments/06_object_recognition/datasets/README.md:33 |

Reference owner → immutable versioned annotations/survey calibration → evaluator-only datasets. Visible/full geometry and physical anchor definitions have units/frame/source. Annotator disagreements remain explicit; frozen revisions never overwritten. No acquisition in Task30. A later failed capture/annotation publication remains incomplete and cannot score methods; restart publishes a new verified version. Existing Task17 references remain readable historical evidence.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Every proposed score has a compatible independent reference and declared uncertainty or is explicitly unavailable; absolute-position scoring has a recorded independent survey-to-method frame transform whose control targets are excluded from scored object anchors; validation and held-out sessions are separate whenever settings are selected from data; co-visible/disjoint identical cases are separately labelled; no derived method estimate is reused as its own truth; Task13 inputs/settings remain untouched.

Before: 6 provisional frames; 0 independent desk physical-centre references. After: no new measurement yet. Provide primary-source traceability, explicit acquisition gaps and a reviewable decision; no runtime result is implied.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No commit created; work remains local and unpublished |
| Files changed | Task40 plan and `experiments/06_object_recognition/datasets/README.md`; no data or code changed |
| Test status | Task-plan lint passed. Fresh plan-reviewer review of the corrected plan returned PASS on 2026-10-05 and was recorded with `task.js review 40 PASS`. `git diff --check` passed. The earlier Claude snapshot review passed protocol structure and identified the findings listed below; a new fixed-snapshot Claude review is pending. No acquisition or comparison executed. |
| Before measurement | 6 provisional frames; 0 independent desk physical-centre references |
| After measurement | Existing evidence classified by suitability; required identity, mask, anchor, extent, surface and uncertainty fields specified; hard-case matrix and session split defined; 0 new references or captures |
| Delta | No experimental measurement; documentation and planning only |
| Decision-gate outcome | Claude passed the protocol structure on the fixed Task40 snapshot and identified four documentation defects plus a missing surveyed 3D-boundary reference requirement; this follow-up corrects those findings. Task40 remains a plan only. Physical measurements, device control, sessions, tolerances and thresholds still require owner decisions. No acquisition, comparison, segmentation integration, phone optimization, demo regeneration or publication is authorised. |

still open because the investigation and its reference/decision requirements are not complete.

Independent review history: Claude's read-only review passed the protocol structure on snapshot `fyld_goal_review_snapshot_20261005_b` (manifest SHA-256 `86e41ac18c3f0432d1c1ada0cc5c9b245d47845e1ad2f5a24b7a2b33cf55e5f4`). It found the desk-session exclusion list was incomplete, a stale Task48-state sentence, a depth-hash citation that ended before the depth check, a fifth table cell that hid evidence, and the lack of surveyed 3D-boundary coordinates/orientation. Four evidence claims were UNPROVEN because ignored run artifacts or the review journal were absent from that snapshot. This correction changes Task40's review target; a new fixed snapshot and independent review are still required.

Fresh plan review: a plan-reviewer agent checked the corrected plan against the current code and the unratified constitution placeholder on 2026-10-05 and returned PASS with no findings. This is a plan review, not the required independent Claude validation. Claude's new fixed-snapshot review and the owner's reference, access and measurement decisions remain outstanding.
