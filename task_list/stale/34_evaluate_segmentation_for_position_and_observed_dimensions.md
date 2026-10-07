---
id: "34"
title: Evaluate segmentation for position and observed dimensions
status: stale
priority: HIGH
type: experiment
approval_status: authorised by owner instruction 2026-10-05; existing data and classical methods only
blocked_by: [31, 56]
validation_gates: [21, 22, 32, 48]
blocks: []
verification_test: experiments/06_object_recognition/experiments/02_segmentation/tests/test_task34_metrics.py
plan_reviewed: 2026-10-05 PASS
files:
  - task_list/stale/34_evaluate_segmentation_for_position_and_observed_dimensions.md
  - task_list/README.md
  - experiments/06_object_recognition/experiments/02_segmentation/scoring.py
  - experiments/06_object_recognition/experiments/02_segmentation/support.py
  - experiments/06_object_recognition/experiments/02_segmentation/coco_evaluation.py
  - experiments/06_object_recognition/experiments/02_segmentation/run_task34.py
  - experiments/06_object_recognition/experiments/02_segmentation/tests/test_task34_metrics.py
  - experiments/06_object_recognition/experiments/02_segmentation/mask_pipeline.py
  - experiments/06_object_recognition/experiments/02_segmentation/tests/test_mask_pipeline.py
  - experiments/06_object_recognition/experiments/02_segmentation/runs/**
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/experiments/02_segmentation/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/02_segmentation/README.md:5
  field: evidence and comparison gap
  baseline_value: "45 historical masks; 0 scored against public instance polygons"
  target: "All non-crowd outlines in the inherited 5,000-image COCO val2017 selection plus all 457 Task22 proposals; no accuracy target for 3D position"
created: 2026-10-04
last_updated: 2026-10-07
superseded_by: null
---

# Task34: Evaluate segmentation for position and observed dimensions

## In plain English

Measure whether better foreground masks improve position and visible dimensions. Use the same depth and camera views so the comparison isolates the mask. Full object size needs a separate measured reference and enough visible surfaces.

## Current state and priority, 6 October 2026

This task is open and unrun. Existing Task19 helpers do not establish a completed Task34 comparison. Preserve earlier reviews and authorized settings. Run this refinement after Task56 reveals a pixel-selection weakness, Task31 and existing validation gates clear, and the current plan is reviewed. Task53 supplies independent physical references; COCO masks alone cannot prove full size or count.

## What

Compare the existing rectangle, GrabCut and Canny masks on the full inherited COCO val2017 annotation set. Use each COCO annotation's reference box as an explicitly labelled oracle prompt, then score the generated mask against its paired reference polygon. The box and polygon come from the same COCO annotation record, so this is not an independent held-out reference test. Apply the same three pixel-selection methods to all 457 proposals in the verified 60-frame Task22 RGB-D replay. Keep each detection's Task46 identity, depth, calibration and supplied pose fixed; do not rerun association.

This is two linked but separate comparisons. COCO establishes image-space mask agreement under oracle boxes. TUM measures how mask selection changes observed depth support, surface positions, repeated-surface spread and visible extent. COCO has no depth and TUM has no human-checked object masks or independently surveyed object positions. Neither dataset can establish 3D position accuracy, complete object size or a physical inventory count.

## Why

Task19 compared 45 masks on inspected RGB-D frames and measured coordinate changes and cost. It had no score against dataset instance polygons. Task45 already acquired COCO val2017, its polygon annotations and all 5,000 images. The box and polygon are paired fields from the same annotation, and COCO val2017 was used in detector model selection. The result is an oracle-box-conditioned mask comparison, not an independent held-out reference, detector or end-to-end score.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Rectangle, GrabCut and Canny mask generation already exists | `masks.segment` and `mask_pipeline.run_methods` | this comparison | experiments/06_object_recognition/experiments/02_segmentation/masks.py:31; experiments/06_object_recognition/experiments/02_segmentation/mask_pipeline.py:41 |
| COCO polygons use a pixel-centre rasterizer and Task45 fixed the full val2017 selection | `placement.polygon_mask` and `coco` | oracle-prompt mask scores against the paired COCO polygon; Task34 records the exact image bytes consumed | experiments/06_object_recognition/experiments/01_detection/placement.py:55; experiments/06_object_recognition/experiments/01_detection/coco.py:95-109,159; task_list/closed/45_measure_detection_position_error_in_cluttered_scen.md:39 |
| Depth summaries return selected area, valid depth count and camera-frame surface medians | `support.summarise` | Task34 extends these to world-frame surface summaries and visible spans | experiments/06_object_recognition/experiments/02_segmentation/support.py:11-33 |
| Shared run manager owns fresh-directory lifecycle, environment capture and completion-manifest verification | `Run` and `verify_run` | Task34 uses the shared publication contract for its new results | experiments/shared/runs.py:117-145,180-209,229-244 |
| Task22 fixes the 60-frame RGB-D replay; Task46 fixes identities and birth policy | verified source runs and cached replay | all three mask conditions share the same proposal and identity rows | experiments/06_object_recognition/experiments/06_identity_policy/cached_replay.py:23; experiments/06_object_recognition/experiments/05_replay/README.md:19 |
| No independent TUM object position or complete-size reference exists | Task40 reference plan | limits every 3D claim in this task | experiments/06_object_recognition/experiments/05_replay/README.md:40; task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:68-69 |

1. On COCO, process all 5,000 images and every one of the 36,335 non-crowd polygon annotations. Exclude the 446 crowd regions because they use a separate, non-instance reference representation. Use each annotation's reference box for all three methods, score IoU and one-pixel boundary F1 against that annotation's paired polygon, and retain every empty, unusable or failed output with its reason. Do not call the paired box/polygon an independent reference or the result a held-out test.
2. On Task22, run all three methods on the same 457 boxes in 60 source frames. Use Task46 object IDs as fixed grouping only. Do not feed mask-derived positions back into association. For each proposal/method, report selected and valid-depth pixel counts, camera-frame median, world-frame median, the world-frame median's displacement from rectangle, and world-axis spans of the selected valid-depth point cloud (maximum minus minimum in x/y/z). Across views of each fixed ID, report coordinate-wise IQR and maximum pair separation of per-view world medians. Label these as observed-surface repeatability/spread and visible spans, not position accuracy, calibrated uncertainty or complete object size. Keep unavailable views with a reason.
3. Persist the per-proposal COCO and TUM rows and per-stage durations in a new Task34 run. Measure source verification/loading, mask generation, polygon rasterisation/scoring, depth selection/projection, world-coordinate summaries, report writing and final manifest verification. For each selected COCO image, hash the exact file bytes that are decoded and scored, save the filename/hash/byte count manifest, and recheck it before marking the run complete. This proves which local bytes the run consumed and detects changes during a run; it does not independently prove each extracted image matches the original archive because the archive is not retained. Keep COCO and TUM outputs separate because their references answer different questions. Do not reuse Task45 box-centre wobble as a mask-position measure.

Execution prerequisite: Task31 must finish provisional/confirmed identity and duplicate policy. Validation gates are independent reviews of Tasks21/22 input receipts and PASS reviews of Tasks32/48; these outcomes do not replace Task31's implementation dependency or owner acceptance. Any findings must be fixed and rechecked before this comparison starts. The reviews must confirm which geometry and birth policy the fixed Task46 IDs represent. Before starting, manually inspect the current Task31 status and the returned independent review records for Tasks21, 22, 32 and 48. `task.js start` does not enforce `validation_gates`; its ability to start this task is not evidence that these prerequisites cleared. Task40 is not required for descriptive existing-data measurements, but remains required for independent physical-position, surveyed-surface and complete-size scoring.

No learned model, new capture, annotation, GPU run or new operating threshold is authorized or required. Do not use Task17's provisional polygons as human ground truth. Do not call lower surface spread more accurate, visible extent complete size, or fixed IDs confirmed physical objects.

Clarification, 4 October 2026 (owner): an earlier research question listed SAM 2/SAM 3 and MobileSAM/EdgeSAM as learned-mask candidates and requested a separate SAM 3 video-identity comparison. The 5 October owner instruction authorizes only the already-built classical-mask comparison in this task. Learned checkpoints, SAM 3 video identity, new acquisition and phone-cost tests are excluded; they require a separate reviewed and authorized task.

Necessary data/reference: COCO val2017 human outlines and boxes are already acquired and hash-listed under Task45. Task22 supplies measured RGB-D, calibration and supplied camera poses. Task40's independent physical anchors, surveyed surfaces and complete dimensions remain unavailable, so absolute position error and physical size accuracy remain unavailable.

Measurements: COCO IoU/boundary F1, mask failure/empty counts, TUM valid-depth coverage, coordinate changes against rectangle, repeat-view surface spread, observed extent, per-method cost and total measurement time. Background-contamination truth, absolute 3D position error, full object-size error and inventory accuracy remain unavailable.

Dependencies: Task31 must complete its identity and duplicate-policy work. Tasks21/22 input receipts must receive independent review; the Task32 box-depth baseline and Task48 paired comparison must receive independent PASS reviews, with findings fixed and rechecked, before Task34 starts. Task40 is not needed for descriptive existing-data measures but is required for independent physical-position/surface/complete-size scoring. The 5 October owner instruction authorizes only the existing classical methods with already acquired inputs. Learned models, new data permissions and phone trials remain separate.

Cost questions: Annotation labour, learned checkpoint/licence/hardware access, prompts, full encoder/decoder cost, thin-surface capture and storage. Unavailable branches remain explicit.

Decision informed: Decide whether masking improves measurement enough to justify cost and which dimensions can be reported as observed rather than inferred whole size.

Primary sources are linked in research/README.md under the corresponding A-I workstream. The full experimental question and requirements are stated here.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| Task45 COCO acquisition (`task_list/closed/45_measure_detection_position_error_in_cluttered_scen.md:39`) | COCO loader/scorer | original RGB grid; paired annotation box and polygon; annotation IDs; 5,000-image selection; verified archive and JSON hashes at extraction; Task34 per-image hashes identify exact consumed local bytes | yes; the run stores filename, hash and byte count per scored image, but local image hashes have no independent pre-existing expected values |
| Task22 source run (`experiments/06_object_recognition/experiments/05_replay/README.md:19`) | Task34 TUM runner | uint16 depth at 5,000 units/metre; camera calibration; supplied pose per source frame; proposal/frame IDs | yes, read-only source manifest and copied-input hashes verified |
| Task46 cached replay (`experiments/06_object_recognition/experiments/06_identity_policy/cached_replay.py:23`) | Task34 grouping | fixed proposal-to-object IDs and birth-policy output | yes, replay ledger/manifest hashes verified; association is not rerun |
| `mask_pipeline.run_methods` (`experiments/06_object_recognition/experiments/02_segmentation/mask_pipeline.py:41`) | Task34 measurement caller | immutable uint8 masks on the original RGB pixel grid with frame/prompt/world/pose lineage | in memory only; completed rows are written to the run |
| Task34 evaluator using shared `Run`/`verify_run` | report readers | COCO image-space scores and TUM per-proposal camera/world measurements in separate files; timings and settings are Task34 artifacts; shared manager captures environment and verifies completion manifest | yes, complete runs are immutable; incomplete runs are retained and never reused as complete |

Source of truth is the verified Task22 and Task45 input publication plus Task46 replay for fixed IDs. For each TUM measurement, the runner pairs RGB, depth, calibration and supplied camera pose by source frame, selects depth only through that method's mask, back-projects to camera coordinates, transforms with the same supplied pose, and records world-frame units in metres. It records world-axis spans of observed valid-depth points; the visible surface is not the whole object. The COCO prompt box and reference polygon remain paired fields of one annotation and are labelled as such.

Fresh-checkout setup: the runner accepts explicit `--coco-root`, `--task22-run`, `--task46-run` and new `--output` paths. Before running, the operator must restore the existing local-only inputs listed here; the runner performs no download or substitute-data fallback. COCO is `data/coco2017`, with the extraction receipt listing the verified `val2017.zip` SHA-256 `4f7e2ccb2866ec5041993c9cf2a952bbed69647b115d0f74da7ce8f4bef82f05`, 5,000 extracted images and annotation JSON SHA-256 `e8c7f7908f1d7278341fae127d0da654f102f11bd7b21d8aeefa635b8c810b6f`. The original archive is not retained, so Task34 records hashes of the image files it actually consumes and does not claim an independent per-image match to the archive. Task22 is `experiments/06_object_recognition/experiments/05_replay/runs/20261004T152704.023370Z_84abb8b3b9594dcea8a1e5b2c8aced66` with manifest SHA-256 `fd7a7cce28fad27a0eb8af5b81a96f7aa613e825b2fbe8dfacf4191d5939254f`. Task46 is `experiments/06_object_recognition/experiments/06_identity_policy/runs/20261005T102726.235703Z_bace0cc9ceb44abfa9172c16f0f3d53b` with manifest SHA-256 `a580860117a0b04dab6b400c494b7b70da59696f889628ddbb13cbdb3c0845d2`. A missing input or hash mismatch in the pinned source manifests fails before publishing. The segmentation README will include this invocation and restore requirements; replace the output path with a verified-new directory before execution:

```powershell
.venv-yolo/Scripts/python.exe -B -m experiments.06_object_recognition.experiments.02_segmentation.run_task34 --coco-root data/coco2017 --task22-run experiments/06_object_recognition/experiments/05_replay/runs/20261004T152704.023370Z_84abb8b3b9594dcea8a1e5b2c8aced66 --task46-run experiments/06_object_recognition/experiments/06_identity_policy/runs/20261005T102726.235703Z_bace0cc9ceb44abfa9172c16f0f3d53b --output experiments/06_object_recognition/experiments/02_segmentation/runs/<new-run-id>
```

A fresh checkout requires an authorized offline copy of these ignored run folders and COCO data.

The only execution boundary is the experiment process. It reads verified source artifacts and publishes to a new Task34 run directory. A failure leaves that directory incomplete; restart uses a fresh destination and rechecks original manifests. It never overwrites Task22, Task45, Task46 or an existing Task34 run. A completed publication is accepted only after every listed artifact hash and the final run manifest verify. Fresh deployment requires the existing pinned Python environment, NumPy, SciPy and OpenCV; no model artifact or network access is required. No persistent service or shared process state is introduced.

Task34 persists camera/world measurements, per-stage durations, source/settings/environment records and a verified completion manifest. COCO and TUM outputs remain separate. Failed runs are retained as incomplete; complete prior runs and source inputs are never overwritten.

Source RGB/depth/calibration and prompts → masks → visible-depth supports → camera/world measurements → evaluator. Units/grid/world/revision and visible/full semantics are explicit. References withheld except named oracle input. Failure leaves unpublished new run; old masks/measurements never overwritten. Fresh run verifies original manifests; learned branch absent without explicit acquisition.

## Per-stage measures

Task34 persists its own stage durations for input verification/loading, mask generation, COCO rasterisation/scoring, TUM depth projection/world transformation, report writing and completion-manifest verification. Task44 remains a separate cross-stage report and can consume this publication only through its declared run format. Task45's box-centre wobble is not reused as a mask-selected position measure. The paired COCO box/polygon supports oracle-prompt mask scoring only; surveyed world-position and complete-size claims still need Task40 references.

## Hyperparameters

| Name | Value | Source |
|---|---|---|
| Built-in methods | `rectangle`, `grabcut`, `canny` | inherited experiments/06_object_recognition/experiments/02_segmentation/masks.py:10 |
| OpenCV thread count | `1` | inherited masks.py:48; deterministic component cost |
| OpenCV random seed | `0` | inherited masks.py:49; deterministic GrabCut component |
| GrabCut initialisation | `GC_INIT_WITH_RECT` | inherited masks.py:56-64 |
| GrabCut iterations | `5` | inherited masks.py:56-64 |
| Canny thresholds | `50`, `150` | inherited masks.py:76-77 |
| Canny aperture and gradient | aperture `3`; `L2gradient=True` | inherited masks.py:76-77 |
| Canny contour selection | `RETR_EXTERNAL`, `CHAIN_APPROX_SIMPLE`, largest-area contour | inherited masks.py:78-84 |
| Prompt box conversion | floor left/top, ceil right/bottom, clamp to image bounds; unusable below 2x2 pixels or for a full-image box | inherited experiments/06_object_recognition/experiments/02_segmentation/masks.py:12-46 and run.py:57-58 |
| COCO RGB decoding | Pillow `Image.open(...).convert("RGB")`; uint8 RGB on the source image grid; runtime Pillow `12.3.0` | inherited experiments/06_object_recognition/experiments/02_segmentation/run.py:13,176-178 and installed `.venv-yolo` runtime checked 2026-10-05; record exact runtime in each run |
| COCO image selection | all 5,000 val2017 images and all valid non-crowd annotations | inherited Task45 plan; 36,335 non-crowd annotations in the pinned local annotations file |
| COCO crowd annotations | 446 excluded from instance scores | inherited Task45 reference policy; crowd regions do not represent one object instance |
| COCO box prompts | paired reference box from the same annotation as the scored polygon; explicitly oracle | inherited Task45 full selection (`task_list/closed/45_measure_detection_position_error_in_cluttered_scen.md:39`); same prompt sent to all methods; not independent of the polygon |
| TUM depth decode and valid range | raw uint16 divided by 5,000 units/metre; retain only `0 < depth < 4 m` | inherited experiments/06_object_recognition/experiments/02_segmentation/support.py:15-17; use unchanged |
| Boundary scoring tolerance | `1` pixel | inherited scoring.py:33-36; no sweep |
| Surface quantiles | NumPy `method="linear"`; coordinate-wise Q75 minus Q25; null for no points | inherited experiments/06_object_recognition/experiments/02_segmentation/support.py:22-30; installed NumPy `2.4.2`, checked 2026-10-05; record exact runtime in each run |
| Boundary extraction | one erosion with SciPy `binary_erosion` default 2D connectivity-one footprint (4-connected cross), `border_value=0`, `origin=0` | inherited scoring.py:29; SciPy 1.17.1 pinned in experiments/shared/requirements.txt:3 |
| Boundary distance | Euclidean distance on unit-spaced image pixels; score a boundary pixel as matched at distance `<= 1` pixel | inherited scoring.py:33-34; `distance_transform_edt` sampling default, SciPy 1.17.1 pinned in experiments/shared/requirements.txt:3 |
| COCO score aggregation | Equal weight per non-crowd annotation; report arithmetic mean and median per method, plus paired mean score difference against rectangle on annotations scored by both methods. Empty masks are scored; failed/unusable outputs remain unavailable with reasons and are counted separately, never imputed. | confirmed 2026-10-05 (owner reply) |
| TUM RGB-D selection | Task22's 60 frames / 457 proposals | inherited verified Task22 source run; no added frames |
| TUM object IDs | Task46 replay IDs, fixed for all mask methods | inherited verified Task46 run; association is not rerun |
| Learned model/checkpoint | none | n/a acquisition and validation remain separate |

## Verification

Contract tests: `tests/test_task34_metrics.py` asserts paired human-annotated COCO references receive IoU/boundary scores, provisional references remain unavailable, empty masks stay in the scored denominator, mismatched image grids fail, world transforms preserve units and pose, spans use only selected valid-depth points, missing depth stays unavailable with a reason, each scored COCO image has a saved digest of the exact decoded bytes, and a changed image cannot pass final run verification. The existing `test_mask_pipeline.py` continues to assert original-grid binary masks and explicit empty/failed states. The measured run must account for all 36,335 non-crowd records, match the 457 Task22 proposal IDs exactly, preserve Task46 IDs across methods, and verify the completed run manifest.

Before: 45 historical masks compared; 0 independent mask scores; no independent 3D position or complete-size measurements. After: run all 36,335 non-crowd COCO instances and all 457 Task22 proposals through the fixed three-mask comparison. No accuracy target or operating threshold is selected.

Task30 checks plan completeness and board consistency only. HIGH/stateful implementation requires plan lint and fresh-context review before start, then finished-diff review before closure. Record negative/inconclusive outcomes without substituting software test totals for experimental evidence.

Plan review history, 5 October 2026: first fresh review returned FAIL. It found (1) persisted TUM measurements were required but the invariants said the component stopped at in-memory masks; (2) Task31/32 baseline prerequisites were missing from the dependency plan; and (3) Task45 box-centre wobble could not measure mask-selected position. The plan now owns persisted camera/world support summaries and visible spans, blocks on Task31 and reviewed Task32/48 outputs, and removes the box-centre wobble reuse claim. It also states that each COCO oracle box and polygon are paired fields of one annotation, not independent references. Re-review is required before start.

The second fresh review returned FAIL for an undeclared inherited TUM depth conversion/range, an incomplete fresh-checkout input path, and an old SAM 3 request that conflicted with the 5 October classical-only authorization. The plan now records the 5,000-units-per-metre conversion and strict `(0, 4 m)` support range, exact COCO/Task22/Task46 input hashes and restore arguments, and excludes learned checkpoints and SAM 3 video identity from this task.

The third fresh review returned FAIL because the COCO extraction check only validates the annotation hash and image count; it does not verify the 5,000 image bytes. It also found that the review gates for Tasks21/22/32/48 were stated only in prose. The plan now records each image's exact consumed-byte hash in the run and fails completion if those bytes change during the run. It explicitly does not claim an independent match to the original archive, which is not retained. A `validation_gates` field names the required independent reviews separately from Task31's dependency.

The fourth fresh review returned FAIL because the COCO mean/median and paired-score aggregation were not declared, boundary extraction and pixel-distance defaults were missing from the settings table, and the segmentation README still linked Task34 under `open/` and described learned masks as authorized. The plan now uses equal-weight per-annotation mean, median and paired differences against rectangle, with empty masks scored and failures unavailable with reasons. It records SciPy 1.17.1, its default 4-connected erosion element, zero border, one iteration and unit-spaced Euclidean pixel distance. The README now states the current classical-only scope and correct task path. The owner confirmed the aggregation rule on 2026-10-05; another fresh plan review is required before start.

The fifth fresh review returned FAIL because the plan omitted inherited prompt-box rounding/clamping, minimum usable bounds, RGB decode/runtime and linear quantile settings. It also found that `task.js start` does not enforce `validation_gates`. The plan now records those inherited settings and requires a manual prerequisite check against Task31 and the independent Tasks21/22/32/48 review records. The segmentation README now gives the planned runner invocation with pinned source paths. A sixth fresh plan review is required before start.

The sixth fresh plan review returned PASS. It found no blocking issue and advised reusing the shared `Run`/`verify_run` publisher for run lifecycle, environment capture and completion checks. That ownership is now explicit in the reuse and invariants tables. The PASS records plan consistency only; Task31 and independent Tasks21/22/32/48 validation gates still block execution.

## Receipts

| Field | Value |
|---|---|
| Closing commit | None; no commit created |
| Files changed | Task plan, task board README and segmentation README; declared code, tests and a new verified run remain |
| Test status | No tests or Task34 experiment run; plan lint passed and the sixth fresh plan review returned PASS. Independent Claude validation is pending because of the session limit through 02:30 London on 6 October. |
| Before measurement | 45 historical masks compared; 0 independent mask scores; no independent 3D position or complete-size measurements |
| After measurement | Plan corrected and passed fresh review; no Task34 experiment run exists |
| Delta | Planned comparison remains three fixed mask methods with paired COCO oracle-mask scores and fixed-identity TUM observed-surface diagnostics; no measurements have been produced |
| Decision-gate outcome | Owner authorized this bounded existing-data comparison and confirmed the COCO aggregation rule on 2026-10-05. Plan review passed. Start remains blocked by Task31 and independent review of the Task21/22 inputs and Task32/48 baseline. Physical accuracy remains unavailable without Task40 references. |

still open because Task31, the independent Tasks21/22/32/48 gates and Claude technical validation are incomplete. No Task34 run has been produced. The planned comparison cannot establish absolute 3D position, full object size or physical count.

## Board decision, 2026-10-07

Parked under Task60 with owner approval. This is an optional object-identity or review refinement that does not lead directly to the accuracy, latency or phone-deployment goals. It returns to `open/` only if Task56's complete walkthrough benchmark shows a measured failure it would fix; refresh its blockers and plan review then. Earlier receipts and authorisations remain as written. The planned methods (rectangle, GrabCut, Canny on COCO with answer-key boxes) cannot show site accuracy and are not phone candidates.
