---
id: "75"
title: Measure ARCore camera path accuracy on the Redmi
status: open
priority: MEDIUM
type: experiment
approval_status: filed 2026-10-13 from the owner's request to research the tracking problem and file tasks for the best path; needs handset access; not yet planned or approved to start
blocked_by: ["52"]
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/01_camera_capture_delivery/**
docs:
  - experiments/01_camera_capture_delivery/README.md
  - task_list/README.md
baseline_metric:
  source: "none on this handset"
  field: "end-point drift on a closed loop (mm and % of distance walked); error of tape-measured distances between printed markers; tracking-lost events; same walk scored with Task67's COLMAP path"
  baseline_value: "0 ARCore recordings; the current APK contains no ARCore SDK (Task52)"
  target: "at least 3 recorded walks with drift and distance error reported"
created: 2026-10-13
last_updated: 2026-10-13
superseded_by: null
---

# Task 75 — ARCore camera path accuracy on the Redmi

## In plain English

On the phone, the camera path should come from ARCore, Google's tracking system. It combines the camera with the phone's motion sensors and gives real-world size. Published tests show anything from about 1 cm to over 10 cm of error, depending on the phone and the walk. This task measures it on our handset. There is no motion-capture room, so the check uses walks that end where they started, and printed markers whose distances are measured with a tape.

## What

1. Confirm the Redmi is on Google's ARCore supported-device list.
2. Record ARCore's camera pose with every frame. Either add ARCore to the project's recorder (Task52) or, for a first look, use an existing logger app; Pyojin Kim's ARCore data logger, used in the Sensors 2022 four-system benchmark, is a candidate to verify.
3. Walk at least three closed loops through a room with printed markers at tape-measured positions. Score end-point drift, distances between markers computed from ARCore poses against the tape, and tracking-lost events.
4. Run Task67's COLMAP on the same frames and score it the same way, so the phone tracker and the offline image-only path are compared on one recording.

## Why

The phone design the research points to takes the camera path from ARCore and uses learned depth only to fill in surfaces. That design is only as good as ARCore on this handset, which nobody has measured.

## How

To be planned before `task.js start`. ARCore's Recording and Playback API can save a session to MP4 and replay it. Google warns that replayed poses may differ from the live ones and between replays, so poses should be logged live.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

- Sources: [ARCore recording and playback](https://developers.google.com/ar/develop/java/recording-and-playback/developer-guide), [Kim et al. 2022, four visual-inertial systems compared](https://doaj.org/article/4845749bf71543bb9d8bd51082e46690), [RealityCheck, ARCore drift measurement](https://www.cs.ucr.edu/~jiasi/pub/RealityCheck_ism21.pdf).
