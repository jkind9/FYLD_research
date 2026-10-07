---
id: "41"
title: Inventory public datasets for the hosted processing baseline
status: closed
priority: HIGH
type: decision
approval_status: research-only inventory authorised; no download, adapter, or experiment run authorised
blocked_by: []
blocks: []
verification_test: experiments/datasets/README.md
plan_reviewed: 2026-10-05 PASS
files:
  - task_list/closed/41_investigate_candidate_test_datasets_and_trial_exis.md
  - task_list/README.md
  - research/README.md
  - experiments/datasets/README.md
docs:
  - task_list/README.md
  - research/README.md
  - experiments/datasets/README.md
baseline_metric:
  source: research/README.md:30
  field: additional public datasets with source-checked capability and reference records
  baseline_value: "0 of 14 candidates fully inventoried; 3 local datasets already in use"
  target: "14 of 14 candidates inventoried with capability, reference, size, licence, and permission status; no downloads or runs"
created: 2026-10-04
last_updated: 2026-10-07
superseded_by: null
---

# Task 41 — Inventory public datasets for the hosted processing baseline

## In plain English

The project has three local datasets, all with limits for phone walkthroughs and worksite scenes. This task checks 14 additional public datasets for sensor data, reference measurements, sample size, licence terms and usefulness to the hosted baseline. It records what a later authorised trial could answer and what still needs owner input. No data is downloaded, and no experiment is run.

## What

Research-only inventory. Check the 14 additional candidates listed separately in `research/README.md`: ADVIO, ScanNet++, ARKitScenes, LaMAria, TUM VI, Hilti SLAM Challenge 2022, ConSLAM, TartanGround, ETH3D, Middlebury 2021 Mobile, ROADWork, Mapillary Vistas, KITTI and nuScenes.

For each candidate, record the publisher source and version/date checked; available modalities and file formats; calibration and timestamps; reference type, frame and stated uncertainty; published whole-dataset and smallest useful subset size where the publisher provides them; full data licence and access terms; local status; and which hosted-processing stage the evidence can assess. Mark unavailable or unverified fields explicitly. Distinguish physical survey references from pose estimates, synthetic ground truth, labelled boxes, masks and provisional outputs. Identify any existing validation/test splits or signs that benchmark data were used for model selection.

Recommend a shortlist only for its expected information value, public accessibility and reference independence. State the smallest publisher-defined subset that could isolate one stage, but do not select frame counts, thresholds, acceptance limits or download budgets. A missing public term, unclear commercial-use right, token-gated agreement, or owner-only access request is a blocker to that source, not permission to proceed.

Out of scope: downloads, archive extraction, adapters, code or test changes, model inference, experiment runs, new captures and annotations. Any later trial or acquisition requires an owner-approved task with exact paths, licence/access status, input hashes, settings, resource limits, run commands and evaluation references.

## Why

Every result so far is indoor and close range. The current object adapter drops depth at or beyond 4 m (experiments/06_object_recognition/README.md:99). The detector has only been asked about cups, monitors and books. The real use is outdoor street works filmed on phones. This inventory identifies which existing stages later datasets might test before any separately authorised trial. Several candidates also supply references the project lacks: laser-scanned surfaces and labelled object instances (ScanNet++, ARKitScenes) and surveyed paths on construction sites (Hilti, ConSLAM).

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Candidate list and existing local dataset boundaries are documented | `research/README.md` and dataset guide | this inventory and Task40 | research/README.md:31-56; experiments/datasets/README.md:5-20 |
| Acquisition helper safely publishes archives, but its download routine is ICL-specific | `experiments/datasets/acquisition.py` | future approved acquisitions only | experiments/datasets/acquisition.py:122-183; :186-229 |
| Shared observations and current TUM/ICL adapters exist but are outside this desk-check scope | shared contracts and adapters | future separately approved trial | experiments/shared/contracts.py:11,39,73; experiments/03_camera_pose_estimation/src/dataset.py:78,110 |
| Existing TartanGround, KITTI and ETH3D entries do not form a complete capability/licence inventory | dataset guide | Task41 matrix | experiments/datasets/README.md:67-88 |

The three local datasets remain unchanged. Their existing receipts and dataset guide are checked as context only. The ICL download function is not treated as a generic acquisition route. No proposed trial relies on project code being reusable until a later scoped plan verifies its inputs and consumers.

## Hyperparameters

hyperparameters n/a: no code, data processing, download, model or experiment run is authorised in this inventory.

## Invariants and recovery

invariants n/a: read-only source research; no data or process state is created.

## Verification

- **Documentation contract:** `experiments/datasets/README.md` has a source-linked row for each of the 14 candidates and records modalities, formats, calibration/time fields, reference type and independence, available size/subset information, licence/access state, local status and relevant hosted stage. Missing publisher evidence stays marked unknown. `research/README.md` lists KITTI and nuScenes separately, and its candidate count agrees with the matrix.
- **Before/after:** before, 0 of 14 additional candidates fully checked; three existing local datasets. After, 14 of 14 candidate rows reviewed against publisher sources and a shortlist proposal that distinguishes usable public references from sources needing an access or licence decision. No download or run occurs.

No acceptance threshold, performance result, adapter contract or experiment result is claimed. If exact terms or subset size cannot be verified from a publisher source, the row states that limit and the smallest owner action needed to resolve it.

## Receipts

| field | value |
|---|---|
| closing commit | `14957e6` (research record) |
| files changed | Task41 plan/receipt; `task_list/README.md`; `research/README.md`; `experiments/datasets/README.md` |
| test | Documentation contract: 14 distinct candidate rows and six cells per row confirmed; no code/data test applies. `task-plan-lint.js` passed and `git diff --check` passed. `python -B tools/check.py -q` did not complete cleanly: tests emitted errors and the runner ended with `PermissionError [WinError 5]` while pytest cleaned its temp folder; exact suite outcomes are unavailable. |
| before / after | Before: 0 of 14 additional candidates fully inventoried; 3 local datasets. After: 14 source-linked candidates record modalities, references, size, permissions/access, hosted-stage relevance and unknowns; no downloads or runs. |
| result | Research-only shortlist: ETH3D small stereo set, LaMAria example/approved sequence, one ScanNet++ scene subject to access, ROADWork only after image-rights review; TartanGround as a synthetic control after exact subset sizing. No accuracy, latency or worksite suitability result is claimed. Claude source/claim validation remains pending. |

Notes / caveats / follow-ups:

- Sources checked against publisher pages/repositories on 2026-10-05. Release details or rights not present in publisher sources are marked unknown or require owner review. No licence acceptance, account request, download, extraction, adapter, inference or experiment was performed.
- Claude must independently verify material dataset/reference/licence claims from a fixed snapshot and mark each PASS, FAIL or UNPROVEN before this task closes.

still open because Claude's fixed-snapshot validation has not returned yet.

### Plan review history

- 2026-10-05 FAIL: scope included downloads/adapters/runs despite the authorised research-only inventory; the grouped KITTI/nuScenes row made the 13-candidate count incomplete; settings and code paths were not fully scoped; the cited downloader is ICL-specific. Plan narrowed to 14 source checks only. Fresh review required before start.

## Closure, 2026-10-07

Closed under Task60 with owner approval. Earlier `still open because` lines above are superseded by this note. The fixed-snapshot external validation is waived: the board README says those review sessions are not relaunched automatically, and a source claim is rechecked by whichever task uses it. Any dataset download or trial needs a separately scoped task.
