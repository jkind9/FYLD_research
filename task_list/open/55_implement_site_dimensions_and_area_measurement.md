---
id: "55"
title: Implement site dimensions and area measurement
status: open
priority: HIGH
type: infra
approval_status: planning authorised 2026-10-06; execution requires task-specific review and frozen settings
blocked_by: []
blocks: []
verification_test: "experiments/05_birds_eye_mapping/tests/test_measurement.py"
plan_reviewed: null
files:
  - experiments/05_birds_eye_mapping/**
docs:
  - experiments/05_birds_eye_mapping/README.md
  - task_list/README.md
baseline_metric:
  source: task_list/README.md and reuse evidence below
  field: implement site dimensions and area measurement
  baseline_value: "0 implemented site-area calculations or independent known-shape tests"
  target: "1 tested measurement component with dimensions, defined area and unknown coverage"
created: 2026-10-06
last_updated: 2026-10-07
superseded_by: null
---

# Task55: Implement site dimensions and area measurement

## In plain English

Turn the visible site model into dimensions and an area in real units. Start with shapes whose answers are known, then test a measured scene. Show what was never seen so missing ground cannot be counted as empty ground.

## Board update, 7 October 2026

Task51 was rescoped on 6 October 2026 to the first prerecorded pipeline. Where this file refers to Task51 decisions for field work (site, objects, survey method, storage and retrieval, numeric limits, phone processing split), Task61 now owns them. The known-shape tests and existing-surface controls need no field decision, so this task is no longer blocked. The site region and boundary definition for field use comes from Task61 and is only needed before Task56's physical comparison.

## What

Own ground/reference-plane choice, projection, site-boundary/region definition and dimensions/area outputs in experiment05. Distinguish observed footprint, full site area, surface area and volume; only claim outputs supported by the selected references and visibility. The first baseline can use analytic shapes and existing surface controls before phone capture. Task56 owns the combined report extension and physical comparison on Task53/54 outputs.

## Why

A coloured point model is not a measured site-size answer. This stage currently has no code or test shapes.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Known-shape and unknown-space plan already exists | experiment05 | measurement implementation | experiments/05_birds_eye_mapping/README.md:5; experiments/05_birds_eye_mapping/README.md:50 |
| Coordinate transforms/projection already exist | shared geometry | measurement input | experiments/shared/geometry.py:42; experiments/shared/geometry.py:78 |
| Surface production exists | experiment04 | measurement component | experiments/04_surface_reconstruction/src/run.py:106 |

1. Agree the region/boundary definition and error/coverage requirements in Task51, then freeze grid/plane settings in a reviewed plan.
2. Write independent known-shape truth and red-first tests for a rectangle, hole, tilted plane, overhang, empty input, wrong units and unseen cells. Do not derive expected answers with the production projection.
3. Implement the simplest projection/measurement component using shared transforms. Export units, plane/world frame, observed/unknown coverage, dimensions/area and provenance.
4. Test analytic shapes and existing supplied-input surface controls. Their verified component result and measurement interface are this task's handoff to Task56. Task56 subsequently owns the integrated Task53 survey comparison using Task54 depth; that later comparison is not a prerequisite for closing Task55. Do not treat incomplete observations as full site area.
5. Hand versioned measurement output/scorer to Task56; improve surface representation only if measurement or visibility failures justify it.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Surface/depth adapter | measurement component | metric points, world/segment and declared ground plane | sealed run survives | experiments/shared/geometry.py:78 |
| Measurement component | complete benchmark/report | lengths in metres, defined area in square metres, observed/unknown mask and frame/plane lineage | versioned artifact survives | experiments/05_birds_eye_mapping/README.md:24 |

Source of truth is the original geometry, declared region/plane and settings. Missing space stays unknown. Changed camera poses require recomputation from observations, not moving an old measurement silently. Failed publication remains incomplete and restart uses a fresh run. First deployment validates units/frame/plane with independent shape fixtures. No existing area API needs backward migration; Task56 versions its new report consumer contract.

## Hyperparameters

| name | value | source |
|---|---|---|
| grid size, region/boundary rules, plane selection, outlier/visibility thresholds and test dimensions | pending Task51 and reviewed measurement plan | n/a planning only; no numerical choices invented here |
| output units | metres and square metres; missing coverage explicit | inherited experiments/05_birds_eye_mapping/README.md:5; experiments/05_birds_eye_mapping/README.md:24 |

## Verification

Known-shape tests assert independently calculated lengths and area within the declared grid error, holes/unseen cells excluded, and incompatible frames/units rejected. Before 0 measurements; target 1 complete independent analytic/control report and a versioned measurement interface ready for Task56. Those outputs close Task55 and unblock Task56. The later physical dimensions/area and coverage comparison against Task53 under Task51 limits belongs to Task56's closure, not this component handoff.

Before starting HIGH work, refine exact scope, audit settings, run task-plan lint and obtain a fresh plan review against current sources. No implementation or acquisition is performed while writing this plan.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | Plan only; implementation not started |
| Test status | Planned contract checks; no run claimed |
| Before measurement | 0 implemented site-area calculations or independent known-shape tests |
| After measurement | Not measured |
| Delta | Not measured |
| Decision-gate outcome | Open; execution and verification pending |

still open because this plan has not been implemented or measured.
