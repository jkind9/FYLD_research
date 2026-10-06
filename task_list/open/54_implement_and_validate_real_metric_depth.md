---
id: "54"
title: Implement and validate real metric depth
status: open
priority: HIGH
type: infra
approval_status: planning authorised 2026-10-06; execution requires task-specific review and frozen settings
blocked_by: [51]
blocks: []
verification_test: "experiments/02_stereo_depth/tests/test_metric_depth.py"
plan_reviewed: null
files:
  - experiments/02_stereo_depth/**
docs:
  - experiments/02_stereo_depth/README.md
  - task_list/README.md
baseline_metric:
  source: task_list/README.md and reuse evidence below
  field: implement and validate real metric depth
  baseline_value: "0 depth methods run in experiment02; downstream trials use supplied sensor depth"
  target: "1 measured baseline producing depth in metres with validity, timing and independent scoring"
created: 2026-10-06
last_updated: 2026-10-06
superseded_by: null
---

# Task54: Implement and validate real metric depth

## In plain English

Test how the chosen capture can provide real distances from the camera to surfaces. Measure its errors, missing answers and processing time. Use those estimates in the complete test instead of borrowing correct depth from a benchmark.

## What

Own the selected real depth route, its adapter, scoring and cost records within experiment02. Decide with Task51 and runtime Task52 evidence whether to use ARCore output, a hosted single-camera method or calibrated stereo. Do not wait indefinitely for a second camera that the Redmi does not advertise. Preserve original sensor/API depth lineage. Record the producer's depth convention, metric scale source and invalid pixels. Normalize ray distance to axial Z depth using the matching calibration before existing shared consumers, which require camera-axis depth in metres. First controls can use existing independent public references; final phone measurements use Task52/53.

## Why

Depth is the missing bridge from phone images to physical measurements. Supplied benchmark depth bypasses this project's hardest input problem.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Depth method is absent but a plan/data exist | experiment02 | surface, tracking and objects | experiments/02_stereo_depth/README.md:7; experiments/02_stereo_depth/README.md:69 |
| Metric decoding and projection already exist | shared geometry | new depth adapter and consumers | experiments/shared/geometry.py:10; experiments/shared/geometry.py:20 |
| Metric decoding returns an explicit validity mask | depth_metres | downstream geometry | experiments/shared/geometry.py:10 |

1. Select one baseline route/checkpoint/license and required execution environment under Task51; tighten source/test files and freeze parameters before start.
2. Add red-first controls for depth-unit conversion, depth convention, invalid pixels, scaling, calibration-grid mismatch and missing/unsupported depth.
3. Produce a fresh run from actual method/API output. Independent truth enters scoring only. Report distance error and valid coverage by Task51 range/visibility groups, boundary errors, runtime and memory.
4. Use Task52 phone streams and Task53 independent measurements for the physical trial. An unavailable reference remains unavailable; API confidence is not an independent error measurement.
5. Hand metric depth, calibration, timestamps and provenance to Task56. Publish a failed/unsuitable depth route as a result with a next decision rather than quietly replacing it with reference depth.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Selected depth method/API | surface/object/camera adapters | producer convention plus normalized axial Z metres, validity mask, image grid and timestamps | sealed run survives | experiments/shared/geometry.py:10; experiments/shared/geometry.py:20 |
| Independent reference | depth scorer only | reference distances plus uncertainty/coverage | versioned evaluator bundle survives | experiments/02_stereo_depth/README.md:76 |

Original observations and frozen settings are source of truth. References never substitute for method output in the chained run. Interrupted estimation leaves an incomplete run; restart uses a fresh directory. First execution requires validated input, installed licensed runtime/model and a verified test fixture. Existing supplied-depth benchmark controls remain readable and labelled as controls.

## Hyperparameters

| name | value | source |
|---|---|---|
| depth route/checkpoint, resize, scale source, ranges, thresholds and sampled scenes/views | pending Task51 and reviewed execution plan | n/a no depth run in this board task; audit and stamp every value before execution |
| output units | original convention recorded; shared consumers receive axial Z metres | inherited experiments/shared/geometry.py:10; experiments/shared/geometry.py:20 |

## Verification

Known-distance controls reproduce independently specified metric values; invalid pixels remain invalid and bad calibration is rejected. Physical scoring uses Task53 truth and never the estimated depth itself. Before 0 real depth runs; target 1 complete baseline with error, coverage, runtime, memory and failure record, judged against Task51 limits. Failing an accuracy limit is a valid reported experiment outcome.

Before starting HIGH work, refine exact scope, audit settings, run task-plan lint and obtain a fresh plan review against current sources. No implementation or acquisition is performed while writing this plan.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | Plan only; implementation not started |
| Test status | Planned contract checks; no run claimed |
| Before measurement | 0 depth methods run in experiment02; downstream trials use supplied sensor depth |
| After measurement | Not measured |
| Delta | Not measured |
| Decision-gate outcome | Open; execution and verification pending |

still open because this plan has not been implemented or measured.
