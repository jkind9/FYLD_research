---
id: "27"
title: Localise YOLO cup detections in recorded RGB-D
status: closed
priority: HIGH
type: infra
blocked_by: []
blocks: []
verification_test: experiments/06_object_recognition/pilot/tests/test_localisation.py
plan_reviewed: 2026-10-03 PASS
files:
  - experiments/06_object_recognition/pilot/**
  - experiments/06_object_recognition/README.md
  - task_list/README.md
  - task_list/closed/27_localise_yolo_cup_detections_in_recorded_rgbd.md
  - task_list/pending_review/27_localise_yolo_cup_detections_in_recorded_rgbd.md
  - task_list/closed/27_localise_yolo_cup_detections_in_recorded_rgbd.md
  - task_list/pending_review/16_research_segmentation_recognition_and_camera_corre.md
  - task_list/open/17_prepare_labelled_revisit_inputs_and_object_observa.md
  - task_list/open/18_evaluate_object_detection_on_frozen_labelled_obser.md
  - task_list/open/21_associate_object_identities_with_geometry_and_appe.md
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/pilot/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md:13
  field: Automatic detections connected to scene coordinates
  baseline_value: "0 published detection-to-world-coordinate trials"
  target: "1 inspectable GPU pilot with every selected frame accounted for"
created: 2026-10-03
last_updated: 2026-10-03
superseded_by: null
---

# Task 27: Localise YOLO cup detections in recorded RGB-D

## In plain English

Start with an existing cup detector and connect its image boxes to depth and camera position. Compare two ways of choosing depth inside each box. Show the supporting pixels and resulting scene coordinates so we can see when a desk or missing depth produces a misleading position.

## What

Implement a small single-frame GPU detector-to-3D trial and offline marked point-cloud viewer under experiments/06_object_recognition/pilot. This exploratory task is independent of Task17's frozen benchmark and does not claim detector accuracy, physical object centres, persistent identity recovery or reconstructed surfaces.

## Why

On 3 October 2026 the owner directed us to experiment with pretrained YOLO first and prioritise connecting detections to 3D coordinates. Task16's detailed five-experiment protocol remains pending_review. In reply to the checkpoint-download approval question, the owner authorised GPU execution, delegated a good model and a suitable single frame, required detection review before mapping, and requested a marked point cloud. This narrow trial is authorised; the broader Task16 protocol remains pending.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| TUM inputs are paired and decoded without camera references | associations/load_frame | new pilot runner | experiments/03_camera_pose_estimation/src/dataset.py:78 |
| Invalid depth and the inherited 4 m limit are preserved | load_frame | localisation support | experiments/03_camera_pose_estimation/src/dataset.py:112 |
| Calibrated backprojection and rigid transformation exist | backproject/transform_points | detection localisation | experiments/shared/geometry.py:21 |
| Camera-to-world origins and transform validity already have a contract | Pose | localisation | experiments/shared/contracts.py:39 |
| Supplied reference trajectory reader exists | read_references | named integration control after detections saved | experiments/03_camera_pose_estimation/src/evaluation.py:13 |
| Unique hashed run publication exists | Run/verify_run | runner and review | experiments/shared/runs.py:59 |

- [x] Write analytic controls first: known depth, rotated/translated camera, missing depth, invalid boxes, background contamination, incompatible calibration and invalid transforms.
- [x] Add validated box-localisation records. Compare all valid box pixels with the valid pixel nearest the geometric box centre. Report the camera median transformed into world coordinates and depth range, not an inferred full-object centre or statistical uncertainty.
- [x] Preserve per-view localisation; do not assign persistent IDs or mutate IdentityStore.
- [x] Acquire the checkpoint explicitly and hash it. Add a local-checkpoint-only detector adapter; refuse absent weights and require an explicit device. No implicit checkpoint download in the runner.
- [x] Add a runner using original xyz RGB/depth, saved raw detector outputs, then supplied poses in a clearly marked reference-pose integration control. Reuse existing one-to-one 0.02 s association for RGB/depth and pose matching. Missing depth yields unavailable records; missing matching pose fails publication of the world report.
- [x] Save original input and checkpoint hashes, exact configuration, source snapshot, per-stage timing, proposals, localisation support and an inspectable annotated image/HTML report. Publish with Run; interrupted runs stay incomplete/failed.
- [x] Run one GPU detection frame and visually review its published image first. Publish mapping as a separate run from the verified detection output, with the coloured cloud and marked cup position. Record no-detection frames and do not treat the pilot as an accuracy benchmark.
- [x] Update Tasks16/17/18/21 and the board to distinguish this exploratory trial from their remaining approvals and evaluations.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Original RGB-D reader | detector/localiser | original 640x480 RGB, registered Z depth in metres, invalid mask, timestamps | immutable originals and hashes | experiments/03_camera_pose_estimation/src/dataset.py:112 |
| Detector | localiser | xyxy float box in ORIGINAL image pixels; cup class and score | saved predictions before poses loaded | experiments/06_object_recognition/README.md:99 |
| Pose reader | localiser | proper camera-to-world 4x4, TUM world, same segment, metres | saved sidecars in run | experiments/shared/contracts.py:39 |
| Run | reviewer | complete artifact inventory and completion receipt | yes | experiments/shared/runs.py:59 |

Source of truth: immutable originals, pinned local checkpoint and saved proposals. The detector never receives depth or reference poses. Reference poses are opened only after proposals are persisted, solely for the named integration control. Coordinates use registered original pixel grid; no resized model coordinates reach backprojection. This task creates no corrected poses or identity generations. A process death leaves a failed/incomplete unique run; rerun into a fresh directory. Fresh deployment installs pinned dependencies, supplies explicitly acquired checkpoint and existing xyz data, then runs unit controls and the requested pilot. Prior runs, Task13 settings/work and shared pose schema remain untouched. GPU is authorised for the single-frame detector trial.

## Hyperparameters

| Name | Value | Source |
|---|---|---|
| Model and package | YOLO26x COCO; ultralytics 8.4.172 | confirmed 2026-10-03: owner delegated a good pretrained model; strongest published YOLO26 detection scale chosen |
| Device/precision/batch | cuda:0; FP32; 1 | confirmed 2026-10-03: owner requested GPU and one frame; FP32 published default |
| Recording/frame | xyz RGB 1305031128.547399.png | confirmed 2026-10-03: owner delegated one suitable frame; cup visibly present |
| Input/confidence/IoU/max detections | 640; 0.25; 0.7; 300 | confirmed 2026-10-03: delegated initial settings use published prediction defaults, no tuning |
| Classes/augmentation | all 80 COCO classes; disabled | confirmed 2026-10-03: inspect detections first; map cup class 41 |
| Pairing tolerance | 0.02 seconds | inherited experiments/03_camera_pose_estimation/src/dataset.py:78 |
| Calibration | 640x480; 525,525,319.5,239.5 | inherited experiments/03_camera_pose_estimation/src/dataset.py:14 |
| Depth scale/validity | raw/5000 m; positive and below 4 m | inherited experiments/03_camera_pose_estimation/src/dataset.py:126 |
| Support methods | all valid box pixels; one nearest valid pixel to box centre | n/a analytic baseline definitions with no tuned foreground threshold |
| Display cap | 20000 points; full arrays saved | n/a deterministic display sampling only |
| Repeats | 1 invocation; model warmup recorded in timing caveat | confirmed 2026-10-03: one-frame trial, no throughput claim |
| External execution timeout | 180 s per detector invocation | n/a execution safeguard, not product acceptance threshold |

The 3 October 2026 audit includes historical source snapshots; current Task13 settings are unchanged. The owner superseded the proposed 10-frame CPU pilot with a single-frame GPU trial. Save resolved model settings and checkpoint hash. Preserve original image grid for all coordinates.

## Verification

Contract tests in experiments/06_object_recognition/pilot/tests/test_localisation.py must assert exact known coordinates, zero invented locations for missing depth, rejection of invalid boxes/calibration/poses and isolation of box support. An analytic foreground/background fixture must expose how box-wide depth can point at background. Runner controls use a fake detector and supplied poses, verifying every selected frame and original RGB/depth hashes, no implicit download, explicit device selection and fail-closed publication. No full Task13 tracking sequence runs.

Before: 0 published detection-to-world-coordinate trials. Target: 1 inspectable authorised GPU pilot, with all selected frames and failures recorded. Analytic coordinate errors must be within 1e-10 m of specified expectations; changed implementation coverage at least 80%. These tolerances are fixture precision, not product acceptance gates. Detector and position accuracy require Task17 independent labels and are not claimed by this pilot.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No commit requested |
| Files changed | New pilot detector, localisation, report, runner, requirements, README and four test modules; stage06 README; Tasks16/17/18/21/27 and task board |
| Test status | 41 passed; analytic controls observed RED before implementation; implementation coverage 91%; Ruff formatting/lint and mypy passed; offline Edge rotation/switching/network check passed; actual report rendered offline without errors |
| Before measurement | 0 published detection-to-world-coordinate trials |
| After measurement | 1 GPU detection frame: cup confidence 0.827695; 230405 measured cloud points; 3439 valid cup-box pixels; marked world sample (0.603606,0.685479,0.859663) m; median/sample separation 0.050927 m |
| Delta | 0 to 1 inspectable detection-to-world-coordinate trial; no detector accuracy or persistent-identity gain claimed |
| Decision-gate outcome | Narrow GPU trial authorised 3 October 2026 and implemented; plan/code/Python reviews PASS; finished-diff review PASS after DR-1 fixed; broader Task16 protocol remains pending |

Detection: experiments/06_object_recognition/pilot/runs/20261003T173943.511670Z_54a40c632f704b8685e9ed4568355c28. Final corrected mapping: experiments/06_object_recognition/pilot/runs/20261003T175727.913404Z_352c685ab5d24f16b31b50aa2cf50fb4. The earlier mapping edition is retained unchanged. Both final run manifests verify. Only one real detector invocation ran on cuda:0, FP32, RTX5070Ti. Model inference timing is 10.2105 ms; first-call setup/warmup prevents a throughput claim. Checkpoint SHA-256: 9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92.

Code/Python review findings were fixed with regression controls: nearest-pixel half-offset mismatch, empty-cloud plotting, and copied-parent artifact hash verification. Protected Task13, tracking and shared-viewer source hashes match the session baseline. No full tracking sequence ran. Task17 still owns independent revisit labels and gap decisions; Tasks18/21 own accuracy and identity evaluation. Task16 cannot close until its owner approves the detailed protocol and remaining numerical choices.

Finished-diff DR-1: arbitrary checkpoint bytes and loader-normalised paths could substitute a model or trigger implicit acquisition. Resolved by pinning the approved SHA-256, canonical basename and unchanged pathname before model import; validate cup class meaning and save class map. Regression controls cover alternate bytes, legacy filenames, apostrophes and legacy names in parent directories. The final reviewer confirmed PASS. These adapter corrections do not change the saved cup result; the real model was not rerun.
