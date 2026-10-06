---
id: "37"
title: Research ARCore, ARKit and RoomPlan mapping
status: pending_review
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
  source: experiments/01_camera_capture_delivery/README.md:7
  field: evidence and comparison gap
  baseline_value: "0 verified project phone AR-depth/room scans"
  target: "Measured answer after review; operating thresholds require owner agreement"
created: 2026-10-04
last_updated: 2026-10-05
superseded_by: null
---

# Task37: Research ARCore, ARKit and RoomPlan mapping

## In plain English

Check what room-mapping platforms provide and which ideas could transfer to this project. Separate available phone capabilities from algorithms described in papers. Apple laser-depth features require different hardware from the current Android phones.

## What

Question: Which accessible APIs and capture/correction/revisit techniques can supply the project's measurement records, and which require new hardware or algorithms?

Proposed research/decision task. No implementation, execution or acquisition is bundled into it.

## Why

Existing evidence: Primary ARCore/ARKit/RoomPlan sources reviewed in Task30. No current phone depth/confidence/pose recording exists. RoomPlan uses supported Apple camera+LiDAR; its research describes local/global detections and box fusion beyond exposed API detail.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Phone capability owner already exists | Task08 | hardware acquisition plan | task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:36 |
| Capture/build owner already exists | stage01/Task24 | future API capture | experiments/01_camera_capture_delivery/README.md:7; task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:36 |

Proposed comparison: Research visual-inertial tracking, raw/full depth and confidence, timestamps/reprojected observations, planes, meshes, room/object parameters, anchors/relocalisation, scan guidance, corrections and repeated observations. Map each required field to actual APIs and mark internal research algorithms separately. Design Android raw-depth export control first; propose Apple LiDAR/RoomPlan control only with hardware approval. Keep existing Task08/24 ownership for any app/device implementation.

Necessary data/reference: Exact phone model/OS/ARCore support, raw depth/confidence/measurement times, camera/anchor poses and revisions; independent room surfaces/dimensions and repeated/restart captures planned via Task40. No hardware capability is inferred from S23/Redmi availability.

Measurements: Research capability matrix with primary citations; planned later completeness of exported metadata, independent plane/mesh/object error, relocalisation/repeat-scan agreement, capture gaps and cost. No vendor timing becomes a local result.

Dependencies: None for research/design; acquisition/execution still require authorisation. Completed controls remain historical evidence, not reopened work. Task16 broad-protocol approval and new settings/model/data permissions remain separate prerequisites where relevant.

Cost questions: Supported Android/API access, Apple LiDAR device access, scan labour, USD/USDZ and raw data export fidelity, memory/runtime/energy, independent room survey.

Decision informed: Choose platform techniques worth adopting and identify inaccessible/internal methods or hardware-dependent capabilities before capture implementation.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

invariants n/a: dedicated research/requirements task. Any future device acquisition, API implementation or scan uses separately reviewed Task08/24 scope and owner authorisation.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run. Before numerical execution, audit inherited parameters and record every source/selection/split/model/prompt/depth/pose/threshold/resource/scoring setting with dated owner confirmation where required. Exploratory gates are not validated rules.

## Verification

Planned contract: Each technical claim maps to a primary API/paper; LiDAR-required capabilities are labelled; repeated depth timestamps are not counted as independent measurements; unavailable device fields stay unknown.

Before: 0 verified project phone AR-depth/room scans. After: no new measurement yet. Provide primary-source traceability, explicit acquisition gaps and a reviewable decision; no runtime result is implied.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started; plan created during Task30 |
| Files changed | Task file only; future scope proposed |
| Test status | Rechecked six current first-party platform/API sources and the current ARCore device list on 2026-10-05; the updated capability and limitation matrix is in `research/README.md`. No implementation test, phone capture, timing run or accuracy experiment was authorised or executed. Claude's source validation is pending. |
| Before measurement | 0 verified project phone AR-depth/room scans |
| After measurement | API capability and capture-lineage requirements recorded for ARCore, ARKit and RoomPlan; Google lists the Galaxy S23, Redmi Note 11 Pro and Redmi Note 11 Pro 5G product families for Depth API; the exact Redmi code `2201116TG` is not listed and runtime support remains untested; 0 project phone AR-depth/room scans |
| Delta | Research-only; no project measurement |
| Decision-gate outcome | Platform comparison is documented from current primary sources. Samsung access, Redmi runtime support, a phone capture route, independent survey link and any implementation/acquisition approval remain outstanding. A research matrix does not establish accuracy or phone performance. |

Source correction, 5 October 2026: Google's live supported-device list includes the Redmi Note 11 Pro and Redmi Note 11 Pro 5G names, both with Depth API support. It does not identify the exact `2201116TG` handset code. The inventory now records the listed product family separately from the project's untested handset and runtime support. This correction changes the pending Claude review snapshot; validate the corrected README from a new fixed snapshot.

still open because Claude's independent source validation and owner decisions on any later device capture remain outstanding.
