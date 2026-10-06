---
id: "56"
title: Benchmark complete walkthrough accuracy time and memory
status: open
priority: HIGH
type: infra
approval_status: planning authorised 2026-10-06; execution requires task-specific review and frozen settings
blocked_by: [52, 53, 54, 55]
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
  source: task_list/README.md and reuse evidence below
  field: benchmark complete walkthrough accuracy time and memory
  baseline_value: "0 same-recording complete tests with independently scored site measurements and counts"
  target: "1 held-out complete-process baseline report with accuracy, total time, memory and device context"
created: 2026-10-06
last_updated: 2026-10-06
superseded_by: null
---

# Task56: Benchmark complete walkthrough accuracy time and memory

## In plain English

Run one recorded walkthrough through the whole process and compare its measurements and counts with independent answers. Measure the total wait and memory use on the chosen hardware. Show which stage failed instead of combining unrelated good results.

## What

Consume Task58's canonical six-step runner in src/walkthrough for the complete phone benchmark. Own independent count/position/area scorer wiring, a versioned complete report and measured accuracy/time/memory evidence. Task58 owns cross-layer sequencing, phone-record adaptation and the small component extractions; do not create another orchestrator here. Reuse stage implementations and dedicated experiment validation imports; no second detector, identity store, depth estimator or surface implementation. Preserve frozen TUM/ICL runners. Task09 retains inventory/persistence ownership. Task54/55 own depth and measurement methods/scorers; this task owns their report adapters and comparison consumers.

## Why

Task44 currently combines separate trials, not one walkthrough. Current camera/replay/surface runners bake in benchmark data assumptions. Area is absent from the fixed report schema, and depth/position/count wrappers are missing.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Stage report and comparison contracts exist | evaluation package | complete report extension | experiments/evaluation/schema.py:12; experiments/evaluation/compare.py:52; experiments/evaluation/run.py:95 |
| Camera runner is restricted to benchmark sources | tracking runner | new phone input adapter | experiments/03_camera_pose_estimation/src/run.py:308 |
| Replay requires benchmark grid and reference poses | pilot replay | reused projection/association primitives | experiments/06_object_recognition/pilot/replay.py:394; experiments/06_object_recognition/pilot/replay.py:492 |
| Surface runner assumes its independent ICL reference | surface runner | method-only orchestration | experiments/04_surface_reconstruction/src/run.py:132 |
| Shared timing and run integrity already exist | TimingLedger and Run | complete workload measurements | experiments/shared/timing.py:49; experiments/shared/runs.py:59; experiments/shared/runs.py:137 |
| Inventory store already has an owner | IdentityStore/Task09 | counting baseline | experiments/06_object_recognition/src/identity_store.py:34 |

1. Freeze the Task51 baseline methods, session selection and hardware; use simple existing Task46 counting first. Do not require Tasks31/33/34/35 improvements before measuring the baseline.
2. Run Task58's canonical pipeline on actual phone calibration, image grid, clocks, world/segments and method-produced depth/pose. Use its experiment adapters instead of adding sequencing or a second phone reader here. Reference poses/depth/physical IDs remain scorer-only in the complete run. Keep explicitly labelled supplied-input controls separate.
3. Add test-first contract/error controls for truth leakage, grid/units, missing stages, session resets, mismatched report versions and changed source hashes.
4. Extend the evaluation schema/version, comparison, renderers and tests for site measurements and missing depth/position/count stages. Retain historical report readers or an explicit refusal/migration path; never silently compare incompatible formats. Accept unavailable independent surface/pose truth while retaining required independently scored count/area evidence.
5. Publish same-item controls and predicted-input runs on Task53's held-out recording. Report dimensions/area, coverage, object misses, extra/duplicate counts, mistaken identity joins/splits and stage errors where references exist.
6. Measure original recording decode through usable outputs on the selected hardware: cold load, steady processing, full elapsed time, per-stage costs and peak memory. Keep survey scoring, diagnostic rendering and publication costs separate; also record delivery/upload wait for the chosen route. Do not add unrelated historical stage timings.
7. Record PASS/FAIL against each Task51 pillar requirement. Publish failed targets and causal evidence; create only the specific corrective tasks the measured failures justify. Task09's goal proof uses this report.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Shared phone reader/stage methods | complete orchestrator | metric calibration/depth/poses and observation/segment lineage | sealed source/stage runs survive | experiments/shared/contracts.py:11; experiments/shared/contracts.py:39; experiments/shared/contracts.py:73 |
| Independent survey/human labels | scorer only | matching items/units with evaluator provenance | sealed evaluator bank survives | experiments/evaluation/schema.py:88 |
| Versioned complete report | comparison/viewers | explicit stages, site measures, timing scope and unavailable fields | verified manifest survives | experiments/evaluation/schema.py:144; experiments/evaluation/compare.py:52 |

Original inputs/settings and stage outputs are source of truth; evaluation truth is not method input. Worker/thread boundaries carry only declared records with world/segment/revision lineage. Interrupted stages are not scored as complete; retry creates a new run. Fresh deployment loads validated inputs, installs declared method runtimes, verifies component fixtures and produces one known fixture report before a held-out run. Frozen benchmark runners and report version2 publications stay intact; incompatible report versions cannot be compared.

## Hyperparameters

| name | value | source |
|---|---|---|
| workload, session split, methods, model settings, grids, ranges, thresholds, repeats and timing boundaries | Task51 decisions plus owning Task52/54/55 frozen settings | n/a planning only; inherit exact reviewed settings before run |
| historical Task13 controls | unchanged approved selections/backend and resource caps | inherited task_list/closed/13_validate_frozen_tracking_settings_on_full_developm.md:62 |

## Verification

A fixture returns independently specified dimensions/counts, and deliberately wrong depth/poses or duplicate identities score worse or refuse with the declared reason. Report comparison rejects changed reference/items/units/formats. Before 0 complete held-out tests; target 1 verified same-recording report with required independent measurements/counts, one measured complete timing scope and peak memory. Missing required truth is a blocker; a method failing a product limit is a valid completed baseline result.

Before starting HIGH work, refine exact scope, audit settings, run task-plan lint and obtain a fresh plan review against current sources, including Task58's completed runner. No implementation or acquisition is performed while writing this plan.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | Plan only; implementation not started |
| Test status | Planned contract checks; no run claimed |
| Before measurement | 0 same-recording complete tests with independently scored site measurements and counts |
| After measurement | Not measured |
| Delta | Not measured |
| Decision-gate outcome | Open; execution and verification pending |

still open because this plan has not been implemented or measured.
