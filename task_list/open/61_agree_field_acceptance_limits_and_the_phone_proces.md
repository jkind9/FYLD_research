---
id: "61"
title: Record remaining field acceptance and reference decisions
status: open
priority: MED
type: decision
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - task_list/open/61_agree_field_acceptance_limits_and_the_phone_proces.md
  - task_list/README.md
  - README.md
docs:
  - task_list/README.md
  - README.md
baseline_metric:
  source: "15 October board review; evidence below"
  field: "Record remaining field acceptance and reference decisions"
  baseline_value: "Capture-only phone and PC processing decided; measured error limits and independent reference protocol remain pending"
  target: "Each remaining decision has a dated owner answer or an explicit pending state and named consumer"
created: 2026-10-07
last_updated: 2026-10-15
superseded_by: null
---

# Task 61: Record remaining field acceptance and reference decisions

## In plain English

Record the choices needed to judge a useful result. The phone and computer roles are already decided. The remaining choices concern what to measure, independent answers, acceptable error and waiting time, and how long the system must run.

## Decisions already made

| Item | Owner decision and date | Evidence / boundary |
|---|---|---|
| Phone | Redmi Note 11 Pro, 2201116TG | Confirmed handset; capture 1.2 installed and one walk completed (Task99) |
| Current processing split | Phone captures; PC receives, stores and processes; phone processing later in this same app, 14 October | Task94 and README Capture first; no separate recorder or phone inference project now |
| First comparison input | House walk: upstairs, downstairs, back upstairs, 14 October | Completed 39.88 s walk available; coverage of that whole route has not been independently verified |
| Current focus | Compare 3D reconstruction methods on the same walk before measured dimensions, 14 October | Tasks102, 74 and 104 |
| Hardware | CPU only; GPU use is not authorised | Applies to every queued experiment |
| Speed floor | At least 1 fps per method and whole pipeline, 7 October; live or at least one update/s, 14 October | Actual rate and longest gaps must be reported; offline references stay labelled offline |
| Delivery | Email APK install, LAN capture to this PC | Current package is in `mobile_deployments`; no USB/SIM-dependent workflow |

## Decisions still pending

| Item | What remains to record | Consumer |
|---|---|---|
| Surveyed site/region | House is development data; choose scored field region and floor/area definition | Tasks53, 56 |
| Objects and revisits | Target classes, independent inventory, moved objects and ambiguous identities | Tasks53, 56 |
| Survey | Instruments, uncertainty, marker placement and independent human reviewer | Tasks53, 75 |
| Retention/recovery | Durable private phone/survey storage, backup and exact offline recovery procedure | Tasks53, 56; local receiver folder alone is not a backup policy |
| Accuracy/coverage | Numeric dimension, area, count and coverage limits with units | Task56 |
| Waiting time | Maximum full-result wait and live update/latency target beyond the speed floor | Task56 |
| Sustained use | Required duration and limits on phone queue, storage, memory, battery and heat | Task52; later Task57 |
| Session roles | Independent whole-session enrollment, validation and held-out evaluation choices | Task53 |

## Plan and validation

Resolve only the pending choices needed by the next executing task, using its measured evidence. Record owner answers with dates and units. Unanswered acceptance limits do not block Task102's diagnosis or publication of negative method comparisons. Survey/reference acquisition and product PASS claims do require the relevant decisions. Settings recommended by Claude remain proposals, not owner rulings.

Validation is a decision audit: every item above is decided or explicitly pending, with its consumer named. No numerical acceptance value is inferred from a benchmark result. This review does not request all answers at once or reopen settled choices.
