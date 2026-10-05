---
id: "41"
title: Investigate candidate test datasets and trial existing experiments on them
status: open
priority: HIGH
type: experiment
approval_status: proposed; investigation only; each download and run needs owner approval
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - experiments/datasets/**
  - data/README.md
  - research/README.md
docs:
  - research/README.md
  - experiments/datasets/README.md
baseline_metric:
  source: research/README.md:30
  field: candidate datasets tried with existing experiments
  baseline_value: "0 of 13 candidate datasets downloaded or trialled; 3 local datasets in use"
  target: "Each shortlisted dataset has a recorded capability check and, where approved, one trial run per applicable layer with inspected outputs"
created: 2026-10-04
last_updated: 2026-10-05
superseded_by: null
---

# Task 41 — Investigate candidate test datasets and trial existing experiments on them

## In plain English

The project's experiments have only been run on three indoor datasets. None of them is filmed on a phone, none is outdoors, and none shows a worksite. This task checks a list of public datasets that are closer to the real use: phone recordings, construction sites, longer walks outdoors and road work zones. It confirms what each one contains and what its licence allows, then runs the existing experiments on small samples, unchanged, and looks at what comes out. The goal is to learn where the current methods break, not to tune them or set pass marks.

## What

Investigation only. No thresholds, tuning or method changes.

1. **Desk check of every candidate** listed in [research/README.md](../../research/README.md) under "Candidate test datasets": contents, formats, calibration, timestamps, reference type (camera path, laser scan, instance labels, object boxes), download size, the smallest useful subset and the full licence text. Record the result as a capability matrix in `experiments/datasets/README.md`.
2. **Proposed shortlist for trials**, to be confirmed by the owner before any download:
   - ADVIO, one sequence: real phone sensors, ARCore and ARKit paths, independent reference path.
   - ScanNet++, one or two scenes: iPhone colour and depth video, laser-scan surface, labelled object instances.
   - Hilti 2022 or ConSLAM, one sequence: construction-site scale with a surveyed or laser reference.
   - ROADWork, a small sample: work-zone objects such as cones, barriers and signs.
   - TartanGround `ConstructionSite`, a small subset: synthetic site with exact depth and camera path.
3. **Adapters** in `experiments/datasets/` that convert each shortlisted sample into the existing observation records (`Calibration`, `Pose`, `Observation`), with reference data kept for scoring only.
4. **Trial runs with existing code and recorded settings, unchanged:**
   - Layer 3 tracker on ADVIO, Hilti or ConSLAM, and ScanNet++ iPhone sequences.
   - Layer 4 point surface on ScanNet++ iPhone depth, scored against the laser scan.
   - Layer 5 detection and replay on ScanNet++ and ROADWork samples. Score detection with Task18's hit/miss counts and Task45's box placement measures (centre offset, edge error, frame-to-frame wobble, share of the box that is background), not hit/miss alone.
   - Layer 2 has no method yet; record which datasets suit it.
5. **Inspect and write up** what each trial produced: numbers where a reference exists, review pages, and every failure (format, scale, depth beyond 4 m, outdoor lighting, rolling shutter, missing calibration, classes the detector does not know).

## Why

Every result so far is indoor and close range. The current object adapter drops depth at or beyond 4 m (experiments/06_object_recognition/README.md:99). The detector has only been asked about cups, monitors and books. The real use is outdoor street works filmed on phones. Running the existing pipeline on closer data shows which layers need work first, before effort goes into refining the indoor controls. Several candidates also supply the independent references the project lacks: laser-scanned surfaces and labelled object instances (ScanNet++, ARKitScenes) and surveyed paths on construction sites (Hilti, ConSLAM).

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Candidate list with contents and recorded licences now lives in research | research README | this task, task 40 | research/README.md:30 |
| Earlier research already named Hilti, ConSLAM, ADVIO, TUM VI, ARKitScenes, ScanNet++ | session recovery notes | research README table | research/session_recovery/README.md:123 |
| Archive download and safe extraction helpers exist | `experiments/datasets/acquisition.py` | TUM and ICL acquisition | experiments/datasets/acquisition.py:122 (`publish_archive`), :186 (`download`) |
| Shared observation records exist and must be the adapter target | `experiments/shared/contracts.py` | layers 3, 4, 5 | experiments/shared/contracts.py:11 (`Calibration`), :39 (`Pose`), :73 (`Observation`) |
| TUM timestamp association and frame loading exist for reuse | layer 3 dataset adapter | layer 3 run | experiments/03_camera_pose_estimation/src/dataset.py:78, :110 |
| Layer 3 command line accepts only the two local TUM paths | layer 3 runner | — | experiments/03_camera_pose_estimation/README.md:130 |
| Layer 4 dataset adapter is ICL-specific | layer 4 `src/dataset.py` | layer 4 run | experiments/04_surface_reconstruction/README.md:110 |
| TartanGround and KITTI already assessed in the dataset guide | dataset guide | — | experiments/datasets/README.md:67, :75 |

The layer 3 and layer 4 runners are tied to TUM and ICL paths. Running them on new data needs either a small dataset-selection change in those runners or a trial runner in `experiments/datasets/`. If a runner must change, add its file to `files:` first and keep the frozen settings for tracking (task 13) untouched.

Task45 measures detection position error in clutter on COCO val2017 and the local TUM desk recording, because ScanNet++ needs a signed access agreement that only the owner can request. ScanNet++ remains useful later for phone-video outlines and laser-scan surfaces. Write any scored trial output in Task44's per-stage report format where it exists.

Out of scope: KITTI and nuScenes subsets (task 38), phone captures (task 08), planning new reference measurements (task 40), any method tuning.

## Hyperparameters

hyperparameters n/a: planning only; no values selected or run yet. Trial runs reuse each experiment's recorded settings unchanged (layer 3: experiments/03_camera_pose_estimation/README.md "Run the CPU development inspection"; layer 4: the 0.05 m reporting distance recorded in its README). Before any run, list dataset, sequence, frame selection, resolution and any depth range per trial here, with owner confirmation for each new value.

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Downloaded archives and extraction receipts | experiments/datasets/acquisition.py:122 | dataset adapters | original archive bytes, size, SHA-256, publisher URL | Yes; receipts stored beside the data under `data/` |
| Converted observations | new adapters in `experiments/datasets/` | layer 3, 4, 5 runs | experiments/shared/contracts.py:73 records; metres, declared camera frame | Rebuilt from archives; never edited in place |
| Reference paths, scans and labels | dataset archives | evaluators only | publisher format, converted with recorded transform | Yes; kept apart from method inputs |
| Trial outputs | existing run exporters | review pages, write-up | `runs/<id>/{input,output,debug,metadata}` | Yes; incomplete runs stay marked failed or running |

- **Source of truth:** the publisher archive and its receipt. Converted data is derived and can be rebuilt.
- **Process boundary:** none new; adapters write files that existing runs read.
- **Failure after each step:** an interrupted download leaves no published archive; an interrupted run is rejected by the existing run verification.
- **Fresh-deployment path:** documented download with size and hash checks, adapter conversion, then the existing run command for each layer.
- **Backward compatibility:** existing TUM, ICL and Middlebury runs and receipts must keep working unchanged.

## Verification

- **Contract test(s):** for each adapter, a test that converts a tiny fixture and asserts units in metres, the declared transform direction, explicit invalid depth, and that no reference field reaches method inputs. Also a test that a wrong scale or a flipped pose makes the existing evaluator score worse.
- **Before/after:** before, 0 of 13 candidates checked or trialled. After, a capability matrix for all 13, and for each approved shortlisted sample one trial per applicable layer with its outputs inspected and its failures recorded. No numeric target is set; this is investigation only.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

-
