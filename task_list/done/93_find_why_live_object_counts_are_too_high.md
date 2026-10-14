---
id: "93"
title: Find why live object counts are too high
status: done
files:
  - src/live/processor.py
  - src/live/tests/test_processor.py
  - src/live/count_report.py
  - src/live/tests/test_count_report.py
  - src/live/README.md
  - README.md
created: 2026-10-14
---
# Find why live object counts are too high

## Goal

Know which of position scatter, low-confidence detections or one-off sightings creates the extra live identities (15 chairs on TUM xyz), from logged per-detection decisions, and report a count that shows it; no reference inventory exists, so no accuracy claim

## Plan

1. Tests first: each update record lists its detections (class, confidence, outcome new/matched/unresolved, object id, distance to the nearest same-class object before matching); count_report.py reads updates.jsonl and splits new identities by nearest-same-class distance (none, 0.35-0.7 m, 0.7-1.5 m, over 1.5 m), by confidence (under 0.5, 0.5 and over) and by sightings per identity (1, 2, 3 or more). 2. Write the logging in processor.py and count_report.py. 3. One background queue: replay TUM xyz and desk stand-in sessions (recorded speed), then run count_report on both. 4. Write the cause and the split into src/live/README.md and the root README line; finish; commit only these files; push.

## Files

- README.md (+1 -1, 399 lines)
- src/live/README.md (+15 -0, 72 lines)
- src/live/count_report.py (+57 -0, 57 lines)
- src/live/processor.py (+16 -4, 183 lines)
- src/live/tests/test_count_report.py (+32 -0, 32 lines)
- src/live/tests/test_processor.py (+4 -0, 85 lines)

## Checked

- `python -m src.live.run --replay + python -m src.live.count_report (TUM xyz, desk) -> 51 and 45 new identities; 23 and 21 of them 0.35-0.7 m from a same-class object; seen-3-or-more still 9 chairs, 7 TVs on xyz`
- cost: 3 min from begin to finish; Claude tokens 10,594,446 (fresh input 22,211, cache read 10,558,124, output 14,111; 2 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.25 (was 0)
- dead code on added lines: not checked (vulture not installed)
- prose patterns: 0 in 479 words

## Left over

Fix: matching distance that grows with object size or camera distance, then check against a counted inventory of a real scene (none exists for TUM); owner phone walks per field_accuracy.md
