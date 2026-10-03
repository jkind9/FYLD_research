---
id: "14"
title: Add labelled 3D stage inspection and camera-motion views
status: closed
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: experiments/shared/tests/test_visualization.py
plan_reviewed: 2026-10-02 PASS
files:
  - experiments/shared/**
  - experiments/03_camera_pose_estimation/**
  - experiments/04_surface_reconstruction/**
  - experiments/geometry_validation/**
  - tools/check.py
  - pytest.ini
docs:
  - experiments/shared/README.md
  - experiments/03_camera_pose_estimation/README.md
  - experiments/04_surface_reconstruction/README.md
  - experiments/geometry_validation/README.md
  - experiments/README.md
  - README.md
  - task_list/README.md
baseline_metric:
  source: current saved stage reviews
  field: interactive 3D stage views
  baseline_value: 0 views
  target: 2 views
created: 2026-10-02
last_updated: 2026-10-02
superseded_by: null
---

# Task 14: Labelled stage inspection

## In plain English

Make the saved camera motion and reconstructed surface visible in three dimensions. Show which images were measured, which values are reference answers, and which results our code produced. Keep the original runs intact and publish new inspection copies using the processor only.

## What

Add offline Canvas2D 3D point and camera viewers, explicit artifact roles, readable depth previews, and new inspection publications for completed stage 03 and 04 runs. Include selected source images, frame stepping, camera orientation and labelled output comparisons. A point surface must not be described as a mesh.

## Why

Current reviews have zero interactive 3D views. A raw 16-bit TUM depth image is displayed mostly white and has 25.1708984375 percent zero pixels. It is measured Kinect input, not model output or independent ground-truth depth. The supplied TUM ground-truth camera trajectory is independent of estimation. ICL clean synthetic depth, poses and reference surface are ground truth. Distance maps and reconstructed surfaces are generated outputs.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Static CPU cloud preview | shared exporting | geometry and surface exports | experiments/shared/exporting.py:49 |
| Pose and origin validation | shared contracts | tracking/control | experiments/shared/contracts.py:39 |
| Tracking rigid alignment | evaluation | scores/reporting | experiments/03_camera_pose_estimation/src/evaluation.py:69 |
| Existing 2D tracking report | reporting | stage run | experiments/03_camera_pose_estimation/src/reporting.py:27 |
| Lossless surface shards | export | review/inspection | experiments/04_surface_reconstruction/src/export.py:19 |
| Verified publication copying | inspection | completed review | experiments/04_surface_reconstruction/src/inspection.py:234 |
| Geometry stage captions | review | geometry run | experiments/geometry_validation/src/review.py:9 |

- Shared artifact descriptions validate four explicit roles: observed_input, ground_truth, predicted_output, evaluated_output. Record producer, source paths, units and display conversion. Never infer ground truth from input position.
- Shared visualization validates finite scene geometry, deterministic paired point sampling and full/display counts. Offline HTML embeds escaped JSON and uses Canvas2D only. Orbit, zoom, frame stepping and source links stay accessible. No network libraries, WebGL or GPU use.
- Stage 03 derives full aligned matrices using the saved scoring association tolerance and first matched reference for each segment. Failed observations have no camera geometry, and paths never join across segments. TUM RGB and depth are observed input; reference poses ground truth; estimated poses predicted output; residuals evaluated output.
- Stage 04 builds frustum rays with signed focal lengths and transforms vertices by saved model_from_world times supplied camera-to-world. The reflected publisher basis is not a Pose. Display coloured point shards and optional reference points, keeping all numerical arrays unchanged. Make the accumulated static preview unconditional.
- Geometry control retains existing figures with explicit role captions and metadata.
- A shared publication command verifies source inventory, copies original numerical artifacts byte-for-byte, archives computation metadata, adds visual outputs and roles, verifies source again, and completes a new Run. Copied hashes must match the initially verified manifest. Visualization timing is distinct from original numerical timing; publication does not report processing FPS.
- Add depth-in-metres colour preview with black missing pixels and explicit legend; raw 16-bit originals remain linked. No hole filling or smoothing is performed.
- Update declared READMEs and task board, including closed task 05 and deferred full/held-out evaluation task 13. Then return to authorized task 08 workstation preparation.

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Estimated poses | experiments/03_camera_pose_estimation/src/tracking.py:58 | experiments/03_camera_pose_estimation/src/evaluation.py:69 | full 4x4, metres, segment-tagged | saved JSON |
| Surface shards | experiments/04_surface_reconstruction/src/export.py:19 | new viewer adapter | model XYZ/RGB matching indices | saved arrays |
| Input authenticity | experiments/04_surface_reconstruction/src/inspection.py:234 | publication copier | verified manifest SHA256 | original complete run |
| Timing | experiments/shared/runs.py:60 | new publication review | original computation archived, new publication separately timed | separate JSON |

Source of truth: original verified numeric/input artifacts. No scoring, tracker settings or coordinates change. Browser receives display-only finite JSON and source links. If publication dies, its Run remains failed/incomplete; original remains complete. Fresh deployment uses existing Python requirements and a local browser with Canvas2D; no new native/GPU dependency. Old runs remain readable and receive new visual copies rather than edits.

## Hyperparameters

| name | value | source |
|---|---|---|
| numerical parameters | unchanged saved configuration | inherited experiments/03_camera_pose_estimation/src/run.py:21 |
| display point cap | 20,000 reconstructed points total plus at most 20,000 independent reference points | n/a visualization only; no scoring or numerical sampling changes |
| frustum size | 0.15 metres for tracking; 0.3 metres for surface cameras | n/a drawing only, not sensor body or scoring parameter |
| depth preview range | 0 to 4 metres for TUM | inherited experiments/03_camera_pose_estimation/src/reporting.py:16 |

No numerical experiment is rerun. Entry points declare hyperparams n/a: inspection publication only.

## Verification

Contract tests in experiments/shared/tests/test_visualization.py assert four valid roles, finite geometry, escaped hostile JSON, deterministic sample cap and paired RGB, signed fy frustum rays, and invalid-role rejection. Adapter tests assert full rigid alignment of rotation and translation, failed-frame absence and segment breaks, reflected-basis frustum centres, unconditional surface preview and dataset-specific depth roles. Publication tests assert original arrays/metrics byte identity and changed-source rejection. Add tests first and record failures before implementation. Browser end-to-end check opens both offline viewers with GPU disabled, steps frames, orbits geometry, checks links and errors. Full CPU suite passes and changed Python coverage target is at least 80 percent. Before: 0 interactive 3D views. Target: 2 verified complete inspection publications, both with explicit input/output roles.

## Receipts

| field | value |
|---|---|
| closing commit | No commit requested; working tree based on 80d4927600bb290040d75d99379d93bb46315451 |
| files changed | Shared visualization, inspection, publication and viewer assets; shared tests; 03 reporting; 04 review; geometry review; all declared READMEs |
| test | 147 CPU tests pass; 90 percent shared new-code statement coverage; Ruff, Black and mypy pass; offline browser checks pass with GPU/WebGL disabled |
| before / after | 0 to 2 verified labelled interactive 3D stage views; 66 tracking and 150 surface input/output hashes unchanged; 0 broken links or browser errors |
| result | Complete; independently reviewed findings fixed and reproduced cases verified; original sources remain complete, numeric metrics unchanged |

Complete. Final camera inspection: experiments/03_camera_pose_estimation/runs/20261002T195923.778722Z_8bcaf965d8dc496192563205df59d85c/viewer.html. Final surface inspection: experiments/04_surface_reconstruction/runs/20261002T195928.219822Z_55d2d0bfa455453eb2289a5e717490c1/viewer.html. Task 08 workstation installation remains separate open work.


### Review and verification evidence

The plan reviewer returned PASS before start. Tests initially failed on the missing visualization module. Python, JavaScript and general code reviewers found no remaining high-severity issue after corrections. Fixed reviewed failures: numeric segment selector mismatch; missing/empty geometry navigation; CSS canvas aspect ratio; nonfinite calibration; total point cap across many shards; wrong depth legend link; nested computation configuration and repeated publication timing links. The independent diff review reported DR-1 and DR-2. Both were fixed, with a real third tracking publication confirming the original timing lookup and exactly one correct visual timing link. A legacy surface publication is also traced through previous_publication metadata rather than treating its copy time as numerical computation.

Two final browser checks used Edge headless with --disable-gpu and --disable-webgl. Source images loaded, previous/next and orbit controls worked, reference toggling worked, and no JavaScript errors or broken links were found. Browser regression tests cover all-failed and empty observations and canvas proportions. Final 03 publication preserves all 66 original input/output artifact hashes; final 04 preserves all 150. Original complete sources still verify (172 and 273 artifacts), and final editions verify (425 and 356). Numerical metrics were not rerun or changed.

The implementation helper stopped at an account usage limit; the parent completed its remaining work. The attempted separate end-to-end agent hit the concurrent thread limit, so the parent performed the browser verification directly. No check was skipped for either reason. No GPU was used.
