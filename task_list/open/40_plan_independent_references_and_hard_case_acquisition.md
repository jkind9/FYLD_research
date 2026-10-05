---
id: "40"
title: Plan independent references and hard-case acquisition
status: open
priority: HIGH
type: decision
approval_status: proposed; no execution authorised by Task30
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: 2026-10-04 PASS
files:
  - experiments/06_object_recognition/datasets/README.md
docs:
  - experiments/06_object_recognition/datasets/README.md
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
| Source RGB/depth payload is copied and checked against frozen hashes | Acquired TUM Freiburg1 desk files | dataset publisher | experiments/06_object_recognition/datasets/prepare.py:101-111; experiments/06_object_recognition/datasets/README.md:25 |
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
3. **Observed dimensions.** Measure the dimensions that are fully visible and name the endpoints used. Record length, width and height separately. Mark a dimension unavailable when its endpoints or surfaces cannot be independently measured; do not call a partial view the object's full size.
4. **Human image references.** Review instance identities in the source RGB images without looking at model predictions. Draw a per-instance foreground mask for frames used in mask scoring. Record visibility, occlusion and ambiguity; preserve reviewer disagreements instead of forcing a label. Keep these evaluator annotations separate from method inputs.
5. **Independent capture sessions.** After the Redmi's capabilities are known, repeat the static scene from translated viewpoints in separately started sessions. Keep each session intact. If any setting or calibration is selected from data, reserve separate sessions for enrollment, validation and held-out evaluation; never use the held-out session to choose settings. The already inspected TUM session can remain a development/reference control, but it cannot count as a blind held-out session. Include a look-away/return, co-visible similar neighbours, an occlusion and changed object orientation where available. Confirm the number of sessions and captures before acquisition without splitting adjacent frames across partitions.

The minimum owner-supplied physical measurements are therefore an independently measured anchor and observable dimensions for each chosen object, with instrument details and uncertainty, plus an independently justified transform from the survey frame to the method frame if absolute position error is required. The capture protocol does not set a frame count, accuracy threshold or acceptance tolerance; those remain owner decisions before numerical comparison.

### Redmi constraint from Task08, 5 October 2026

Task08's received `session-1791186245035_f881c553` passes export validation and confirms model 2201116TG/Android 13. Only rear ID `0` and front ID `1` are exposed, with no physical IDs or advertised concurrent sets. Its pair attempt is SKIPPED. No DEPTH16 stream is advertised; ARCore is absent from the APK, so runtime depth/pose is untested. The session contains no images. The capture README's "Redmi device result, 5 October 2026" section owns the full result and intake hashes; the raw source is listed in the reuse evidence table above.

The smallest useful next device check is a separately exported single-rear-camera control. If that passes, propose stationary-object RGB views first: revisit one object, show its similar neighbour in the same view, and include identical-looking objects seen only in separate views with owner-supplied identity evidence. Acquire separately started sessions as described above after settings/splits are agreed. A longer recorder still needs implementation or a separately verified recording tool; this one-shot APK is not a walkthrough recorder. Do not require stereo in that proposal or assume depth/poses exist. RGB can support reviewed identity/mask evidence; metric position needs a separately verified depth/pose route and independent survey frame link. The required anchors, dimensions, uncertainty and human reviews above remain absent.

Measurements: Reference coverage matrix, identity certainty/disagreement, masks usable for formal scoring, instrument uncertainty, survey-to-method frame transform and its uncertainty, registration versus scored-anchor separation, coordinate/time consistency, independent session/view coverage, acquisition costs and exact unavailable cases. No experiment accuracy result is claimed by the plan.

Dependencies: None for research/design; acquisition/execution still require authorisation. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Survey instrument/hardware access, human annotation and repeated independent review, capture labour/storage/permissions and missing depth/visibility. Prefer minimum acquisition that isolates a cause.

Decision informed: Approve or revise the reference/capture plan and authorise only needed acquisition; enable Tasks31-35 with stated reference limitations.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| `desk_smoke_v1.json` | `prepare.py` | Frozen labels, calibration, partitions, source hashes and scenarios | Frozen annotation file persists | experiments/06_object_recognition/datasets/prepare.py:23 |
| Acquired TUM Freiburg1 desk payload | `prepare.py` | Original RGB/depth bytes checked against the annotation hashes | Original files persist outside derived publication | experiments/06_object_recognition/datasets/prepare.py:101-111 |
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
| Closing commit | Not started; plan created during Task30 |
| Files changed | Reviewed task plan and reference README; Task08 handset constraints added on 2026-10-05; no acquisition or comparison implemented |
| Test status | Plan lint passed; fresh-context plan review recorded PASS on 2026-10-04. No implementation tests or experiment executed. |
| Before measurement | 6 provisional frames; 0 independent desk physical-centre references |
| After measurement | 1 validated Redmi capability session informs acquisition constraints; 0 new independent identity/mask/survey references or phone image captures |
| Delta | 0 executed comparisons |
| Decision-gate outcome | Plan review passed. Redmi Camera2 report advertises no concurrent set, so plan single-rear RGB acquisition conditionally on a successful control. Owner decision, reference measurements, session acquisition, verified metric inputs and any numerical settings remain outstanding; no acquisition or comparison is authorised. |

still open because the investigation and its reference/decision requirements are not complete.
