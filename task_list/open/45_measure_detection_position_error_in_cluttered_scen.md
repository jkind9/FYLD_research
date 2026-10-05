---
id: "45"
title: Measure detection position error in cluttered scenes
status: in_progress
priority: HIGH
type: experiment
approval_status: owner delegated settings and GPU use on 2026-10-05 ("happy to defer to your judgement"; GPU allowed when no parallel session is using it)
blocked_by: []
blocks: []
verification_test: experiments/06_object_recognition/experiments/01_detection/tests/test_placement.py
plan_reviewed: 2026-10-05 PASS
files:
  - experiments/06_object_recognition/experiments/01_detection/**
docs:
  - experiments/06_object_recognition/experiments/01_detection/README.md
  - data/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/01_detection/README.md:9
  field: "detection box placement error against reference outlines, and frame-to-frame jitter on stationary objects"
  baseline_value: "0 placement or jitter measures recorded; only hit/miss counts (cup 4 of 5 matched at IoU 0.3/0.5/0.7 on 6 coarse frames)"
  target: "placement error for every matched box in COCO val2017 (5000 images) against clutter; jitter for every desk track over the 571 posed TUM desk frames (573 associated colour/depth pairs, 2 refused for motion-capture gaps), next to a like-for-like feature noise floor; no pass/fail limit"
created: 2026-10-05
last_updated: 2026-10-05
superseded_by: null
---

# Task 45: Measure detection position error in cluttered scenes

## In plain English

In a cluttered scene, the boxes the object detector draws move around from frame to frame even when nothing in the scene moves. That movement later turns into errors in an object's 3D position. This task measures how far each box lands from the object's true outline and how much background it takes in, using 5,000 public photos where every object is outlined. It also measures how much boxes jump around over time in a recorded desk scene where the camera's exact position is known, and compares that with how much well-defined image corners appear to jump under the same conditions. The detector and its settings stay unchanged.

## What

Two parts. Part A measures **accuracy** of box placement against hand-drawn outlines. Part B measures **consistency** over time; it cannot see a steady offset, only jitter, and is labelled that way.

### Part A: placement against clutter (COCO val2017)

COCO's 2017 validation split: 5,000 everyday photos, many cluttered, with every instance of 80 object classes outlined by hand. COCO category ids (1-90 with gaps) are mapped to detector classes by name, and the run refuses if any of the 80 names differs. Ultralytics uses val2017 to validate and select its checkpoints, so results are in-distribution and may be optimistic; they are not a held-out score.

Reference conversion: COCO `[x, y, w, h]` becomes `bbox_xyxy`; `instance_id = str(annotation id)`; `category` = the detector's class name. Only categories present in an image's predictions or references are scored for that image.

Matching reuses Task18's `score_category` (one-to-one, max count then max summed IoU), extended with the image's real width and height (see How). Per matched pair, at IoU 0.5 (primary) and 0.3 (so poorly placed boxes are still measured; the cutoff is stated with every result):
- **Overlap** (IoU), as a distribution (median and worst 10%).
- **Centre offset** in pixels (x, y, length) and as a fraction of the reference box diagonal.
- **Edge error** per side in pixels, and width and height ratio.
- **Excess background**: share of the predicted box (its in-image area) outside the reference outline, minus the same share for the reference box.
- **Outline coverage**: share of the reference outline inside the predicted box. Together with excess background this separates a too-big box (excess > 0) from a too-small one (coverage < 1), which a single number would hide.
- A pixel belongs to an outline or a box when its centre (i + 0.5, j + 0.5) lies inside, using an even-odd test on the unrounded COCO vertices (numpy, no rounding). Boxes use the same rule, so an outline identical to its box covers exactly the box's pixels.
- Boxes or outlines under 1 px in area give `null` with a reason. References within 2 px of the image edge are flagged as truncated and reported separately.

Per reference: **clutter** (number of other labelled objects, including crowd regions, whose boxes intersect it; and the share of its box covered by other objects' outlines, crowd outlines included) and **size band** by COCO annotation `area` (mask pixels: small < 32², medium < 96², large), as COCO's own evaluation does.

**Crowd regions** (446 regions in 411 images, uncompressed run-length outlines): excluded from the references, with coverage kept `complete`. After matching, an unmatched prediction is moved to `ignored_crowd` only if its intersection with a same-class crowd box divided by its own area is at least the matching threshold, as COCO's evaluator does. A crowd region may absorb any number of detections. False detections and `ignored_crowd` are both reported.

### Part B: jitter over time (TUM freiburg1 desk, already acquired)

The desk recording is a cluttered office desk at about 30 frames per second, with motion-capture camera positions and measured depth. It has 573 associated colour/depth pairs. Two colour timestamps fall in motion-capture gaps of up to 0.05 s and are refused, leaving 571 posed frames. The detector runs on those 571 colour frames only; the 2 refused frames are listed with their gap and treated as track breaks, not detector misses. It is development data already inspected in Tasks 17, 18 and 21, not unseen data, and no result here feeds back into tracking settings (Task13 reserves this sequence for tracking only).

Camera poses: motion capture is **interpolated** at each needed timestamp (linear position, quaternion slerp), refusing when the two bracketing rows are more than 0.02 s apart. TUM poses are camera-to-world (`T_wc`, `experiments/shared/geometry.py:90`).

0. **Depth moved to colour time.** The depth image is taken up to 19.7 ms away from the colour image (median 11.6 ms). Before any sampling, every valid depth pixel is back-projected with the depth-time pose, moved into the colour-time camera and projected; each colour pixel keeps the nearest depth that lands on it (projected position rounded to a pixel; pixels nothing lands on stay invalid). All depth sampling below uses this colour-time depth map.
1. **Linking.** For each detection at frame t, take its centre pixel and the median valid depth (colour-time map) in the central half of the box. Back-project the colour pixel with the **colour-time** pose of t to a world point X. Predict its pixel at frame t+1 by projecting X with the colour-time pose of t+1: `x' = project(inv(T_wc(t+1)) · X)`. Link to the same-class detection at t+1 nearest that prediction, if within 0.5 × the **frame-t** box diagonal, one-to-one by smallest distance. For each unlinked detection, record the distance to the nearest same-class candidate. A nearby candidate already claimed by another track is reported as `claimed`; a depthless candidate within the gate is `no_depth`; jump candidates between 0.5 and 2 diagonals are assigned one-to-one, so one current box cannot count as several jumps.
2. **Windowed anchored jitter.** For each linked track of 5 or more frames, map every back-projected centre to world coordinates. For each frame, the anchor is the median world point over the track's linked frames within ±5 frames; project that local anchor into the frame. Residual = detected centre − projected local anchor. Report the standard deviation per image axis (sx, sy, ddof = 1) and the radial RMS separately, in pixels and as a fraction of box diagonal. The box centre is not a fixed 3D point (the outline changes with viewpoint, and the anchor's depth can be off), so over a whole track it drifts smoothly; a local anchor follows that drift instead of counting it as jitter. Each track also reports its camera baseline (metres) and range of viewing angles. A steady offset cancels by construction, so no "bias" is reported; Part A measures placement accuracy.
3. **Pairwise jitter (cross-check, like-for-like with the floor).** Frame-to-frame residual (detected at t+1 minus predicted from t), per axis, reported as standard deviation / √2 together with its lag-1 autocorrelation. Independent per-frame jitter σ gives about σ after the √2 correction and autocorrelation near −0.5. Both estimates are reported with the autocorrelation, and neither is named the winner by default. An autocorrelation near −0.5 means independent frame-to-frame jitter, where the two should agree. A higher value means errors that persist over several frames (for example a box that takes in a neighbouring object for 5-10 frames) or slow drift; there the pairwise number understates wander and the windowed number is the better guide. Each estimate's uncertainty is a track-level bootstrap: 1000 resamples of whole tracks, numpy seed 20261005, 2.5th to 97.5th percentile.
4. **Box quality flags**, recorded for every box and used to split results into clean and flagged groups (flagged boxes are reported, not dropped): valid-depth pixels in the central-half window (flag if fewer than 20 or under 25% of the window), depth spread (flag if IQR / median > 0.2), and touching the image edge (within 2 px). Flagged boxes are where depth-choice error or edge truncation can look like detector jitter.
5. **Size jitter**: box width and height in each frame against the track's median size scaled by the anchor depth ratio.

**Noise floor control.** The same pairwise construction (step 3) is applied to ORB corner matches between frames t and t+1, with settings inherited from the project's appearance experiment. Features are kept only at pyramid level 0; their depth uses the same median rule in a 7×7 window, and features whose window spans a depth range above 10% of its median depth are dropped (depth edges). Residual outliers beyond 5 × the median absolute deviation are counted and reported separately. The floor is reported globally and **per track**: residuals of features inside that track's boxes, pooled over all its frame pairs. One box gets only about 2 usable features per pair at these settings, which were chosen for 128×128 crops. A track with fewer than 30 pooled feature residuals gets a `null` local floor with that reason. Every result is stratified by |colour − depth time gap| × camera angular speed, the main known source of misalignment. Box jitter is read against the local floor, not a single global number.

Results are written in Task44's stage report format (detection section, input mode `isolated`) once Task44 is merged; until then the same fields go into this experiment's own JSON. Part B uses reference kind `independent` (motion capture and depth) and labelled as a consistency measure.

## Why

The owner's main concern is that detection positions vary a lot in cluttered scenes, and segmentation might fix it. Task18 only counts a box as matched once it overlaps the reference by more than a cutoff, so a box that drifts 40 px between frames still counts as correct. No output measures placement, jitter or background content. Without those, Task34 cannot show whether a mask improves on a box, and Task35 cannot separate detection error from depth and camera error. The 72.8 mm spread of the desk cup position (Task29) mixes all three.

ScanNet++ (the first plan) needs a signed access agreement and approval that only the owner can request. COCO and the local desk data need no sign-up and cover both questions.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| One-to-one matching to reuse, currently fixed to 640×480 | `score_category`, `_validate_scoring_rows` | Task18 `evaluate` | experiments/06_object_recognition/experiments/01_detection/scoring.py:63-83, :86, :173 |
| Box and prediction validation take width/height already | `box`, `validate_predictions` | scoring helpers | experiments/06_object_recognition/experiments/01_detection/scoring.py:10, :25 |
| Pinned YOLO26x detector and fixed predict settings | `YoloDetector`, `PREDICT_SETTINGS` | Task18/27/28 runs | experiments/06_object_recognition/pilot/detector.py:11, :13, :49 |
| Desk colour/depth association, frame loading, calibration | `associations`, `load_frame`, `CALIBRATION` | layer 3 runs | experiments/03_camera_pose_estimation/src/dataset.py:13, :78, :110 |
| Desk association composed with motion capture already | Task21 inputs | Task21 run | experiments/06_object_recognition/experiments/04_geometry_identity/inputs.py:150-166 |
| Motion-capture reader | `read_references` | layer 3 evaluation | experiments/03_camera_pose_estimation/src/evaluation.py:13 |
| Back-projection, projection, transforms, pose matrices | shared geometry | layers 3-6 | experiments/shared/geometry.py:20, :42, :78, :90 |
| Project ORB settings and ratio-plus-mutual matching | appearance experiment | Task20 | experiments/06_object_recognition/experiments/03_appearance/adapter.py:59-71; experiments/06_object_recognition/experiments/03_appearance/compare.py:43-55 |
| Safe archive member names and staged publish-then-rename | dataset acquisition | TUM/ICL acquisition | experiments/datasets/acquisition.py:57, :122 |
| Verified run publication | `Run`, `verify_run` | all runners | experiments/shared/runs.py:59, :137 |
| Stage report format | Task44 package | this task | experiments/evaluation/schema.py (Task44 branch) |
| No placement, jitter, excess-background or warp-consistency measure exists | searched `centre offset`, `jitter`, `wobble`, `background fraction`, `edge error`, `expected centre` in experiments/ | none | no matches |

Changes, all under `experiments/06_object_recognition/experiments/01_detection/`:
- `scoring.py`: add keyword-only `width=640, height=480` to `_validate_scoring_rows` and `score_category`, passed through to `box` and `validate_predictions`. Task18's `evaluate` keeps calling with no size, so its results stay byte-identical.
- `placement.py`: pure placement, excess-background, outline-coverage, clutter, crowd-ignore, anchored-jitter and pairwise-jitter functions.
- `coco.py`: extraction of the two COCO zips into `data/coco2017/` using `safe_name` and the stage-then-rename pattern, with a receipt holding the archive SHA-256 values; pixel-centre even-odd rasterising on unrounded vertices (numpy), the same rule used for boxes; an uncompressed run-length decoder for crowd outlines; name-checked class mapping.
- `placement_run.py`: Part A runner. At start it checks the extraction receipt and archive hashes and writes them into the run configuration.
- `jitter_run.py`: Part B runner (detection on the 571 posed desk frames, interpolation, linking, anchoring, flags, ORB floor).
- `requirements.txt`: add `opencv-python==5.0.0.93`, the build the detector environment imports (`cv2.__version__` 5.0.0; `opencv-contrib-python` 4.13.0.92 is also installed there but is not the one loaded). Runners refuse any other `cv2.__version__` and record it in run metadata.
- tests under `tests/`.

Steps: tests first for the `scoring.py` extension and `placement.py`; then `coco.py`; Part A run; Part B run; README write-up with every image, frame and box accounted for; `data/README.md` entry with the official COCO URLs, archive hashes and licence (annotations CC BY 4.0; images under Flickr terms).

Out of scope: changing the detector, its settings or classes; segmentation (Task34); 3D position (Task32/35); new captures (Task40).

## Hyperparameters

| name | value | source |
|---|---|---|
| detector checkpoint | YOLO26x, SHA-256 9fdd44a3…3e92 | inherited experiments/06_object_recognition/pilot/detector.py:11 |
| image size | 640 | inherited experiments/06_object_recognition/pilot/detector.py:14 |
| confidence floor | 0.25 | inherited experiments/06_object_recognition/pilot/detector.py:15 |
| detector NMS IoU | 0.7 | inherited experiments/06_object_recognition/pilot/detector.py:16 |
| max detections | 300 | inherited experiments/06_object_recognition/pilot/detector.py:17 |
| matching IoU thresholds | 0.3, 0.5, 0.7 for hit/miss; placement reported at 0.5 and 0.3 | inherited task_list/closed/18_evaluate_object_detection_on_frozen_labelled_obser.md:89; placement at 0.3 confirmed 2026-10-05 under owner delegation |
| assignment rule | max cardinality then max summed IoU, same class, one-to-one | inherited task_list/closed/18_evaluate_object_detection_on_frozen_labelled_obser.md:90 |
| Part A data | COCO val2017, all 5000 images; instances_val2017.json | confirmed 2026-10-05 under owner delegation |
| Part A archive hashes | val2017.zip SHA-256 4f7e2ccb…2f05 (815,585,330 bytes); annotations_trainval2017.zip SHA-256 113a836d…0268 (252,907,541 bytes, MD5 matches server ETag) | confirmed 2026-10-05 under owner delegation; recorded at download |
| class mapping | COCO category name to detector class name; refuse on any mismatch | confirmed 2026-10-05 under owner delegation |
| crowd handling | excluded as references; unmatched prediction ignored if intersection / prediction area ≥ matching threshold against a same-class crowd box; no limit on absorbed detections | confirmed 2026-10-05 under owner delegation; follows COCO's evaluator |
| crowd regions as clutter | yes, in overlap count and outline coverage | confirmed 2026-10-05 under owner delegation |
| mask rasterising | pixel-centre even-odd test on unrounded vertices, same rule for boxes; crowd run-length decoded column-major as COCO stores it | confirmed 2026-10-05 under owner delegation (replaces cv2.fillPoly, which fills boundaries inclusively: 121 px for a 10×10 square) |
| size bands | 32² and 96² px on annotation `area` | inherited COCO evaluation definition (cocodataset.org/#detection-eval) |
| minimum area | 1 px for box and outline, else null | confirmed 2026-10-05 under owner delegation |
| edge margin | 2 px (truncated reference / edge-touching box) | confirmed 2026-10-05 under owner delegation |
| clutter bands | none; per-box rows and Spearman rank correlation only | n/a no band edges chosen |
| Part B data | TUM freiburg1 desk, 573 associated pairs (571 posed), root data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk | confirmed 2026-10-05 under owner delegation |
| colour/depth association tolerance | 0.02 s | inherited experiments/03_camera_pose_estimation/src/dataset.py:79 |
| calibration | fx=fy=525, cx=319.5, cy=239.5, no undistortion | inherited experiments/03_camera_pose_estimation/src/dataset.py:13 |
| depth range | valid and < 4 m | inherited experiments/03_camera_pose_estimation/src/dataset.py:124 |
| pose timing | motion capture interpolated (linear + slerp); colour pixels back-projected and projected with colour-time poses; depth-time pose used only to move the depth map to colour time; refuse if bracketing rows > 0.02 s apart (2 desk frames) | confirmed 2026-10-05 under owner delegation |
| depth re-projection | every valid depth pixel moved to the colour-time camera, projected position rounded to a pixel, nearest depth kept per pixel, unfilled pixels invalid | confirmed 2026-10-05 under owner delegation |
| depth window for box centre | central half of the box, median of valid depth | confirmed 2026-10-05 under owner delegation |
| depth-window flags | fewer than 20 valid pixels or under 25% valid; IQR / median > 0.2 | confirmed 2026-10-05 under owner delegation |
| link gate | ≤ 0.5 × frame-t box diagonal, same class, one-to-one by smallest distance; claimed-neighbour outcome within the gate; one-to-one jump assignment for 0.5-2 diagonals | confirmed 2026-10-05 under owner delegation |
| minimum track length | 5 linked frames | confirmed 2026-10-05 under owner delegation |
| anchor window | median world point over linked frames within ±5 frames | confirmed 2026-10-05 under owner delegation |
| local floor minimum | 30 pooled feature residuals per track, else null | confirmed 2026-10-05 under owner delegation |
| jitter uncertainty | track-level bootstrap, 1000 resamples, seed 20261005, 2.5-97.5 percentile | confirmed 2026-10-05 under owner delegation |
| synthetic test seed and size | numpy seed 20261005; 5000 frames for statistical tests | confirmed 2026-10-05 under owner delegation |
| OpenCV | opencv-python 5.0.0.93 (`cv2.__version__` 5.0.0) | confirmed 2026-10-05 under owner delegation; the build the detector environment imports |
| standard deviation convention | ddof = 1 | confirmed 2026-10-05 under owner delegation |
| ORB settings | nfeatures 500, scaleFactor 1.2, nlevels 8, edgeThreshold 31, firstLevel 0, WTA_K 2, HARRIS score, patchSize 31, fastThreshold 20 | inherited experiments/06_object_recognition/experiments/03_appearance/adapter.py:59-71 |
| ORB matching | knn k=2, ratio 0.75, mutual check, crossCheck False | inherited experiments/06_object_recognition/experiments/03_appearance/compare.py:43-55 |
| floor feature filters | pyramid level 0 only; 7×7 depth window median; drop if window depth range > 10% of median | confirmed 2026-10-05 under owner delegation |
| floor outlier rule | residuals beyond 5 × MAD counted and reported separately | confirmed 2026-10-05 under owner delegation |
| GPU | CUDA device 0, only when no other process is using it | confirmed 2026-10-05 by owner |

## Invariants and recovery

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| COCO archives | download receipt (hashes above) | `coco.py` extraction | original zips in data/archives/coco2017 | Yes; read-only |
| COCO extraction | `coco.py`, staged then renamed like experiments/datasets/acquisition.py:122 | runners | data/coco2017 with a receipt naming archive hashes | A partial staging folder is never renamed; runners refuse without a matching receipt |
| COCO outlines | instances_val2017.json via `coco.py` | placement scorer only | masks in original pixels | Rebuilt from the archive |
| TUM frames, depth, motion capture | data/tum/…/rgbd_dataset_freiburg1_desk | detector (colour only); linking and anchoring (depth, poses) | PNG colour, uint16 depth / 5000 = metres, TUM camera-to-world rows | Yes; read-only |
| Detector proposals | experiments/06_object_recognition/pilot/detector.py:54 | scorers | class, score, original-pixel xyxy | Yes, inside a completed run |
| Results | `placement_run.py`, `jitter_run.py` | Task44 report, README | pixels, fractions, metres per field; `null` plus reason | Yes, once the run verifies (experiments/shared/runs.py:59) |

- **Reference leakage:** the detector receives only colour images. Outlines, depth and motion capture are read after detection.
- **Failure:** an interrupted run stays unpublished; restart uses a new run folder. Task18's run and numbers are untouched.
- **Fresh machine:** data/ is gitignored. data/README.md gives the official COCO URLs, sizes and SHA-256 values; the runner refuses archives that don't match.
- **Backward compatibility:** `score_category` defaults stay 640×480, so Task18's calls are unchanged; a regression test pins Task18's fixture results.

## Verification

- **Contract test:** `experiments/06_object_recognition/experiments/01_detection/tests/test_placement.py`. Assertions:
  - `score_category` with a 480×640 portrait image accepts a box with y2 = 600, and with a 500×375 image rejects a box with x2 = 520. Default calls give results identical to before (existing `test_detection.py` unchanged and passing).
  - Rasterising: a rectangle outline from (2, 2) to (12, 12) covers exactly 100 pixels, and the box with the same corners covers the same 100.
  - A prediction equal to its reference gives centre offset 0, all edge errors 0, IoU 1.0, excess background 0, outline coverage 1.
  - A prediction shifted by (+10, -4) px gives centre offset (10, -4), length √116, left and right edge error +10, top and bottom -4.
  - A prediction 20% wider on each side gives centre offset 0 and width ratio 1.4.
  - A reference outline filling its box, with a predicted box twice as wide, gives excess 0.5 and coverage 1; a predicted box half as wide gives excess 0 and coverage 0.5.
  - Crowd: an unmatched prediction 60% inside a same-class crowd box at threshold 0.5 is ignored; one 40% inside counts as false; two such predictions are both absorbed.
  - Clutter: a reference box half covered by another object's outline gives coverage 0.5 and overlap count 1.
  - Jitter, all with numpy seed 20261005: a constant 10 px offset with a sideways-translating camera gives jitter 0 on each axis. Independent per-axis jitter σ = 3 px over 5000 synthetic frames gives windowed sx and sy within 10% of 3, pairwise per-axis std / √2 within 10% of 3, and lag-1 autocorrelation within 0.1 of −0.5 (about 8 standard errors each). A residual ramping from 0 to 20 px over 200 frames with no noise gives a whole-track-anchor standard deviation of about 5.8 px, but windowed jitter and pairwise std / √2 both below 0.5 px.
  - Warp: camera translates +0.1 m in x, point at (0, 0, 1 m) in the first camera; the predicted pixel in the second frame has u = 319.5 − 52.5 = 267.0 to within 1e-9. A transform applied in the wrong direction fails.
  - Interpolation refuses a timestamp whose bracketing motion-capture rows are 0.05 s apart.
  - Depth timing: a plane at 1 m that is fronto-parallel in the colour-time camera, a camera rotating 1° between depth time and colour time, a box away from the border strip the depth move leaves empty, 0.1 m sideways translation between t and t+1, and zero detector error give a predicted pixel within 1e-6 px of the truth once the depth map is moved to colour time. Using the depth-time pose for the colour pixel instead misses by about 9 px, and the test must catch that.
  - Empty cases give `null` with a reason, never 0; a track shorter than 5 has jitter `null`; areas under 1 px give `null`.
  - Written red-first.
- **Before/after:** before, 0 placement or jitter measures. After: placement for every matched COCO val2017 box with clutter, size and truncation flags, every image accounted for; anchored jitter for every desk track of 5 or more frames, split into clean and flagged boxes, next to the local ORB floor. No pass/fail limit.

## Receipts

| field | value |
|---|---|
| closing commit | None yet; uncommitted in branch `experiment/45-measure_detection_position_error_in_cluttered_scen` (worktree `.worktrees/task-45`, based on main 78ce46b); commit and merge await owner instruction |
| files changed | 01_detection: `scoring.py` (keyword width/height, default 640×480), new `placement.py`, `coco.py`, `coco_scoring.py`, `placement_run.py`, `jitter.py`, `jitter_tracks.py`, `jitter_run.py`, `floor.py`, tests `test_placement.py`, `test_coco.py`, `test_jitter.py`; `01_detection/README.md`; `data/README.md`; `task_list/README.md` |
| test | 01_detection suite 97 passed, 1 skipped (Task18's existing tests unchanged and passing). New modules covered 93-100% (placement 99%, jitter 98%, jitter_tracks 100%, coco 93%, coco_scoring 96%, floor 94%); the two GPU runners are exercised by the real runs, not unit tests. Red-first: placement, COCO and jitter tests failed on import before implementation; windowed masks match a full-image brute-force check on 50 random shapes; the synthetic ORB test failed with a blocky texture (no level-0 corners) and was corrected to a smoothed texture |
| before / after | Before: 0 placement or jitter measures. After Part A (run `20261005T085845.472152Z_035bf495…`, manifest 817021f3…5aa3, 5000 images, 0 rejected proposals): 20,036 unclipped matched boxes at IoU 0.5, median IoU 0.91 (worst 10% < 0.72), centre offset 1.6 px / 1.6% of diagonal (worst 10% > 7.3 px / 7.3%), excess background 0.6%, outline coverage 99.7%; Spearman(offset fraction, covered by others) 0.10; recall 0.70 / precision 0.76 at IoU 0.5, 1,332 crowd-absorbed. After Part B (run `20261005T093056.105890Z_0bc39ecb…`, 571 posed frames, 2 refused for a 0.05 s motion-capture gap): 147 tracks of ≥5 frames; windowed radial jitter mean 1.8 px (95% 1.5-2.2) on 33 clean tracks vs 5.8 px (5.0-6.6) on 114 flagged; pairwise 1.5 vs 3.5 px; floor 0.83/1.10 px per axis; lag-1 median clean −0.42/−0.26 (x/y), flagged 0.03/−0.16; lost tracks are reported as 449 gone, 60 claimed, 53 no depth and 26 one-to-one jumps (median 229 px); 57% of boxes flagged (49% edge, 9% no depth, 13% sparse with depth, 8% spread) |
| result | Implementation and rerun are complete. Claimed-neighbour losses are separate from missed detections, jump targets are one-to-one, and the small-track estimator bias is reported accurately. Focused tests pass; branch review and merge remain |

Notes / caveats / follow-ups:

- still open because the blind diff review is running and committing/merging the branch needs the owner's go-ahead.
- `requirements.txt` was not edited: the documentation-policy hook blocks every `.txt` write. The OpenCV version is still enforced at run time (both runners refuse unless `cv2.__version__` is 5.0.0) and recorded in each run's configuration. Add `opencv-python==5.0.0.93` by hand or allow the file in the hook.
- The stratification bands for the noise floor (tertiles of camera rotation during the colour-depth gap) were chosen under owner delegation at run time; the plan asked for stratification without fixing bands.
- Follow-up: recall by clutter level is not yet reported (counts are per image and class, not per reference); placement by clutter is.

- Plan re-review 2026-10-05 FAIL with 3 new blocking findings: the depth-time pose applied to a colour-time pixel (about 3-10 px error on every box); cv2.fillPoly rasterising one pixel row too large; a whole-track anchor counting smooth drift as jitter. Fixed above with the 4 advisory findings (per-track pooled floor, 571 frames, test seed and size, Task44 fallback and OpenCV pin).
- Plan review 2026-10-05 FAIL with 6 blocking findings: the 640×480 fixed size in `score_category`; the crowd rule hiding false detections; a frame-to-frame "bias" that could not see a steady offset and overstated jitter by √2; an inflated ORB floor (depth/colour timing, depth edges, keypoint level, outliers); depth-choice and edge effects counted as detector jitter; ORB settings diverging from the project's. All revised above, along with the nine advisory findings.
- Task34 should reuse the placement, excess-background and outline-coverage measures to compare boxes with masks on the same COCO images and desk frames.
- ScanNet++ phone-video outlines remain a later option; it needs the owner to request access.
