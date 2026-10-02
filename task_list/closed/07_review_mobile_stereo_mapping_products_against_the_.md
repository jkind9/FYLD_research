---
id: "07"
title: Review mobile stereo mapping products against the field brief
status: closed
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: research/edge_products/README.md
plan_reviewed: null
files:
  - research/edge_products/README.md
  - research/README.md
  - task_list/README.md
docs:
  - research/edge_products/README.md
  - research/README.md
baseline_metric:
  source: research/README.md
  field: product routes with explicit reconstruction-rate evidence status
  baseline_value: "0 routes in a field-brief product review"
  target: "4 routes with map-output and throughput evidence boundaries"
created: 2026-10-02
last_updated: 2026-10-02
superseded_by: null
---

# Task 07: Mobile stereo products for the field brief

## In plain English

Find products that build a three-dimensional scene on a portable computer during a walkthrough. Check whether they update the scene at least once per second. Explain how the same scene could help measure the work area and count objects without counting them again on a return visit.

## What

Add a primary-source product review in research/edge_products/README.md and link it from the research index. Separate mobile stereo rigs from ordinary phone camera products and numerical map results from depth or display rates.

## Why

The user supplied the original field brief and asked whether one reconstruction system could support site-size estimation and distinct-object counting. The existing source review does not provide a comparison of current product routes for that combined workload.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
| --- | --- | --- | --- |
| Research has a source index | research/README.md | Research readers | research/README.md:5 |
| Research already separates observed geometry from unseen space | research/README.md | Measurement evaluation | research/README.md:26 |

- [x] Reuse two existing agents for OAK/Spectacular product evidence and object identity limits.
- [x] Verify ZED kit, continuous mapping and NVIDIA live mesh benchmark against vendor documents.
- [x] Explain shared geometry and persistent object records; distinguish moving objects and unknown boundaries.
- [x] Save four product routes, phone limitations, source links and proposed evaluation in a README.
- [x] Add links to research and task indexes; verify local paths and task lint.

## Invariants and recovery

invariants n/a: documentation-only review; no deployed system or persistent application state changed. Published throughput remains attributed to the specific vendor configuration.

## Hyperparameters

hyperparameters n/a: no experiment run or parameter selection implemented. Suggested hardware is an evaluation recommendation.

## Verification

Doc-claim check: all four product rows identify real accumulated output, computation location and whether sustained map throughput was established. Exactly one route has a quoted live mesh throughput result; that result is labelled release 3.2, Nova Carter, three Hawk cameras and vendor-measured. Check both local index links resolve. Before: zero field-brief product comparisons. After: four routes with explicit evidence limits.

tests n/a: documentation-only research; no code or hardware run.

## Receipts

| field | value |
| --- | --- |
| closing commit | n/a: workspace is not a Git repository; no commit requested |
| files changed | research/edge_products/README.md; research/README.md; task_list/README.md; this task record |
| test | Primary vendor pages and paper abstracts checked; two local index links resolve; task lint checked at closure |
| before / after | 0 / 4 product routes; 1 vendor live mesh benchmark explicitly above the requested 1 Hz |
| result | Review captured; ZED recommended for evaluation; end-to-end field accuracy, count quality and sustained throughput remain unmeasured |

No hardware purchase, vendor outreach or experiment was performed. Hardware evaluation is a proposed next action, not unfinished work required to close this research review.
