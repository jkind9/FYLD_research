---
id: "29"
title: Export replay and review reconstruction and identity evidence
status: closed
priority: MED
type: decision
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/06_object_recognition/experiments/05_replay/runs/shareable/**
  - experiments/06_object_recognition/experiments/05_replay/README.md
  - task_list/README.md
docs:
  - experiments/06_object_recognition/experiments/05_replay/README.md
  - experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/README.md
  - task_list/README.md
baseline_metric:
  source: Task22 completed replay
  field: Portable named replay package with coordinate exports
  baseline_value: "0 named packages"
  target: "1 hash-checked package, 0 numerical reruns"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task29: portable replay and evidence review

## In plain English

Package the recorded replay so it can be copied to another computer and opened in a browser. Export the saved cup measurements and explain what the experiments actually establish. Research smoother and more realistic scene displays without implementing reconstruction changes.

## What

Copy the existing self-contained Task22 HTML outside its completed run, package it with provenance and every saved desk cup observation, and verify source and export hashes. Compute descriptive repeatability from existing observations. Record research and dataset limits in the replay README. No source-code changes, model runs, threshold changes, or reconstruction implementation.

## Why

The owner needs a transferable viewer and a clear distinction between position repeatability, absolute accuracy, identity recovery, and realistic scene rendering. Task27's original cup belongs to the xyz sequence; the repeat-detection trial belongs to desk. Those objects and scenes must not be combined as one physical identity.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Task22 already embeds images, scene data and Plotly | payload.write | offline browser | experiments/06_object_recognition/experiments/05_replay/payload.py:42; experiments/06_object_recognition/experiments/05_replay/payload.py:93 |
| Completed runs can be checked without inference | verify_run | export command | experiments/shared/runs.py:59 |
| Camera/world surface medians and centre samples are already saved | localise_detection | baseline observation ledger | experiments/06_object_recognition/pilot/localisation.py:49 |
| Existing generic exporter expects a different scene contract | export_share | generic geometry viewer | experiments/shared/share.py:163 |

Use byte-identical HTML copying, not the generic exporter that would change the viewer contract. Check manifest membership and completion before and after exporting. Parse embedded payload and resource tags, verify ZIP CRC and every exported hash, and copy-read the HTML from the package. Export all saved desk cup detections, including unresolved ones; summarize both all located measurements and accepted object-0005 observations so gate selection is visible. Preserve centre-pixel and box-median definitions separately. Statistics use existing metre coordinates: coordinate median, radial RMS/max/95th percentile around that median and maximum pairwise distance. They are descriptive spread, with no calibrated truth or acceptance threshold. Research official Open3D, COLMAP, Gaussian-splatting and street-benchmark sources. Update declared README and receipts.

## Invariants and recovery

Source of truth: pinned Task22 manifest fd7a7cce28fad27a0eb8af5b81a96f7aa613e825b2fbe8dfacf4191d5939254f. Original completed runs remain byte-identical. New export directory is outside the source; refuse an existing target to avoid replacing a publication. Single-process copy/export; incomplete export is not recorded as verified. Recipient extracts the ZIP and opens the standalone HTML without a server. No existing producer or consumer contract changes.

## Hyperparameters

hyperparameters n/a: no new experiment, inference, resampling or reconstruction. All original display points/images/conditions are inherited unchanged. Descriptive statistics retain all available observations without fitted parameters; NumPy linear percentile convention is stated in the receipt.

## Verification

Artifact checks: source manifest still verifies; HTML hashes match exactly; embedded payload has 60 frames, 457 proposals and 20,000 points; no external HTML resource attributes; ZIP CRC and per-file SHA256 match; CSV rows equal all saved cup proposals and summary counts. Baseline 0 named packages; target 1 package. Browser interaction was checked on an earlier Task22 build; do not claim new browser checks unless actually run. tests n/a: artifact-only export and research, no implementation changed.

## Receipts

| Field | Value |
|---|---|
| Closing commit | None requested |
| Files changed | Six export files and one ZIP under 05_replay/runs/shareable; replay README research/measurement section; task board |
| Test status | Source run verifies before/after; source/export HTML SHA256 identical; embedded counts 60/457/20000; zero external HTML resource attributes; 19 CSV rows; ZIP CRC and every archived hash match. New plot visually inspected. tests n/a: no implementation changed. Browser interaction not rerun. |
| Before measurement | 0 named replay packages |
| After measurement | 1 standalone 12,809,832-byte HTML; 1 six-file ZIP, 6,448,978 bytes; all 19 cup proposals exported. Sixteen assigned desk-cup positions have box-median RMS 72.8 mm and centre-sample RMS 82.3 mm; maximum pairwise separations 291.7/317.0 mm. Absolute centre accuracy remains unmeasured. |
| Delta | One portable package and full per-detection coordinate export; zero inference, new downloads or reconstruction changes |
| Decision-gate outcome | Requested export and research complete. Geometry-only success in Task21 prevents a claim that both position and appearance have been proved necessary. Task27 xyz cup has one view; identity trials use desk only. Task16/21/22 remain pending_review and Task13 preserved. |

ZIP SHA256: 3072847e057805cc732bdcb6c8fec10854f8941e38593ad55bb6a016e7bb04cc. HTML SHA256: 9f0cee9d38af73665dcca4c8580815f93c0b8ea419d469136e9a38b5c7e93522. Original Task22 manifest remains fd7a7cce28fad27a0eb8af5b81a96f7aa613e825b2fbe8dfacf4191d5939254f. Package receipt has all file hashes. Research sources are linked in the replay README; Open3D depth fusion/mesh, COLMAP textured reconstruction, Gaussian splatting, Deep SORT, KITTI and nuScenes were read, with no acquisition or implementation.

The largest assigned desk deviation is frame523, with the cup clipped at the image top and the nearest valid centre-depth pixel 19.7 pixels from the box centre. This is a quality concern requiring investigation; no causal claim or new measurement filter is fitted. All-frame identities lack independent labels and repeated views are correlated. Unresolved proposals remain exported rather than silently filtered from the receipt.

Scope: research and artifact export only. A future application, street-scale evaluation, reconstruction comparisons and calibrated association/noise rules are suggestions recorded in the README, not implemented work or approved protocol changes. No new task in those streams was started and no commit was made.
