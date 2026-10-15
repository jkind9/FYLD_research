---
id: "56"
title: Benchmark complete walkthrough accuracy time and memory
status: open
priority: HIGH
type: infra
blocked_by: [52, 53, 61]
blocks: []
verification_test: "experiments/evaluation/tests/test_complete_walkthrough.py"
plan_reviewed: null
files:
  - experiments/evaluation/**
docs:
  - experiments/evaluation/README.md
  - experiments/README.md
  - README.md
  - task_list/README.md
baseline_metric:
  source: "15 October board review; evidence below"
  field: "Benchmark complete walkthrough accuracy time and memory"
  baseline_value: "Redmi replay 1.58 updates/s; no independently scored complete phone test"
  target: "One held-out same-session accuracy, complete timing and peak-memory report"
created: 2026-10-06
last_updated: 2026-10-15
superseded_by: null
---

# Task 56: Benchmark complete walkthrough accuracy time and memory

## In plain English

Run the whole process on one held-out recording and compare measurements and object counts with independent answers. Measure the full wait and memory cost on the computer. A successful replay or plausible picture alone cannot pass this test.

## Current evidence

Task99 replayed the real Redmi walk on CPU: 63 updates, 1.58 updates/s, longest gap 0.856 s, 845,428 surface points. The owner judged the geometry poor. There are no independent dimensions or object counts. Task93 logged overcounting on TUM; a wider matching radius is only a proposed fix. Task55 implements area; Tasks58/59 own six-step orchestration and layer contracts; Task64 owns reports; `src/live` owns live/replay scheduling. No second orchestrator, detector, session parser or fusion engine is needed.

## Plan

1. Freeze the method/configuration selected from Tasks102, 74 and 104, including orientation, scale, frame selection, live/offline status and CPU hardware. Preserve frozen TUM/ICL controls. Use Task53's held-out bank; keep references evaluator-only.
2. Reuse `src/walkthrough` stage contracts, `src/live` outputs and `experiments/evaluation` report/scoring owners. Trace and test the adapter between saved live results and complete evaluation before adding code; do not assume the two runners already share all input adapters.
3. Test truth leakage, changed source/reference hashes, missing stages, wrong units/grid, world/segment resets and incompatible report versions. Deliberately wrong geometry or duplicated identities must score worse or be explicitly unavailable.
4. Report dimension/area errors, coverage, missed/extra/duplicate objects, false identity joins/splits and stage errors where independent references exist. Keep absent truth explicit. Begin with the existing counting method, not optional Tasks31-35 improvements.
5. Measure cold loading, decode through usable output, steady processing, complete elapsed time and peak memory. Separate upload/drain, reference scoring and rendering costs. Report frame/update rates and longest gaps; do not sum unrelated historical component timings.
6. Compare with the owner decisions from Task61. A method can fail a target in a valid completed baseline; missing required independent answers cannot be scored as zero error.

## Completion boundary

One reproducible held-out same-session report with independent counts/measurements and declared timing boundaries. The current development walk, software fixtures and the Gaussian viewer do not satisfy it. Algorithm corrections stay with their owning tasks. CPU only; deployment of inference on the phone is later Task57.
