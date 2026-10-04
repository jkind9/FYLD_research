---
id: "19"
title: Evaluate classical and edge device object segmentation
status: closed
approval_status: approved
priority: MED
type: experiment
blocked_by: []
blocks: ["22"]
verification_test: experiments/06_object_recognition/experiments/02_segmentation/tests/test_segmentation.py
plan_reviewed: 2026-10-03 PASS
files:
  - experiments/06_object_recognition/experiments/02_segmentation/**
  - experiments/06_object_recognition/README.md
  - pytest.ini
  - tools/check.py
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/experiments/02_segmentation/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Evaluate classical and edge device object segmentation
  baseline_value: "0 independently scored mask comparisons"
  target: "1 complete bounded classical mask/depth-support comparison; unavailable learned branches explicitly evidenced"
created: 2026-10-03
last_updated: 2026-10-04
superseded_by: null
---

# Task 19: Evaluate classical and edge device object segmentation

## In plain English

Compare ways to separate each object from its background. Test simple boundary methods and compact learned mask models with the same prompts. Measure whether mask mistakes also corrupt the object position.

## What

Implement classical and compact learned mask comparisons in experiments/02_segmentation. Use fixed checked regions/prompts first, with predicted proposals as a separate measured condition.

## Why

Background pixels affect appearance and depth localisation. Classical boundary detection, prompted masks and automatic object discovery have different capabilities.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Valid-depth support already exists | backprojection agreement | mask localisation | experiments/shared/geometry.py:21 |
| Prompt and mask benchmark contract is proposed | Task17 | segmentation scorer | experiments/06_object_recognition/README.md:110 |

Fresh deployment uses an isolated environment with `python -m pip install -r experiments/06_object_recognition/experiments/02_segmentation/requirements.txt`; the new scoped requirements file pins opencv-python==5.0.0.93 (effective cv2 5.0.0), numpy==2.4.2 and inherits existing shared requirements for Pillow/Run/scipy. Use the existing installed environment for this overnight run: no dependency or model downloads. Reject runtime cv2 version mismatch; do not install opencv-contrib-python alongside it.

Bounded initial comparison on the Task17 six source frames and11provisional cup/monitor supports. Implement rectangle-support control, OpenCV GrabCut fixed box prompts, and Canny/largest-external-contour filled control. These are crop/mask controls, not semantic detectors. No compact segmentation checkpoint is acquired; YOLO26x is detection-only, so all learned segmentation candidates are explicitly unavailable/deferred under no-new-models/weights direction. Do not download them or relabel a detector rectangle as a learned instance mask.

Use independently RGB-checked bbox prompts as an explicitly named oracle-box condition. Its coarse supports are excluded from formal segmentation accuracy. Save actual predicted masks, empty/unavailable states, source-frame and opaque promptkey, RGB/valid-depth overlays and costs. Synthetic masks alone test evaluator overlap/boundary and split/merge behavior: real coarse reference masks must never produce an accuracy headline, background-contamination truth or claimed metric-location error. On real frames report mask area, raw/processed valid-depth count and camera-coordinate median/spread shifts relative to rectangle support, with rawdepth and calibration hashes; these are coordinate differences, not accuracy. Compare predicted Task18 cup boxes separately if its verified cache/run is available, using deterministic oracle-free prompt extraction and evaluator-only matching; all failed/unmatched prompts remain recorded. Non-exhaustive monitor references cannot establish inventory counts.

GrabCut receives originalRGB converted explicitly to BGR, full-grid image and floor/ceil-clamped rectangle without reference masks. Reject a prompt leaving no certain background or smaller than2x2; return explicit unusable rather than silently use a rectangle. Seed OpenCV RNG0 for each prompt and threads1 for this serial control. Canny runs grayscale crop, fixed50/150 thresholds,3aperture,L2gradientTrue; fill the largest external contour (no contour means empty). For rectangle/localise_detection comparison, pass the explicitly floor/ceil-rounded bounds so pixel-centre selection matches the rasterized rectangle. Spread is component-wise interquartile range (q75 minus q25, NumPy method linear), with median and validpointcount; unavailable support reports null, never zero position. Optional Task18 predicted-box matching reuses its exact same-category maximum-cardinality/maxsumIoU assignment at0.5, without threshold tuning. Clamp box/polygon support and preserve grid; no resizing, morphology or hole filling. Masks are uint8binary0/255 on640x480. Depthvalidity follows raw0missing and processed0<depth_m<4, units/5000. Require no pose to measure camera-coordinate differences; don't load independentGT poses for this task.

Publish unique verified Run using existing Run/write_json/verify_run, capture source snapshots only from realrepo in production/tinyfake repos in tests, no experimenttreefixture copies. Verify Task17publication receipt hash and15originalarchive-derived memberhashes; references stay in evaluatorinput except named boxprompt oracle. Final html links all frame masks and source imagery. Explicitly list absent learnedweights and mask-accuracy-unavailable limits. Crash leaves incomplete run; restart fresh, existingoutputs unchanged. Focus newtests and meaningfulsynthetic controls; >=80%productioncoverage, Ruff/mypy/Blackdirectformatcheck, no broadtests or GPUneeded.

### Additional reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Binary raw/processed depth and calibration already decoded | load_frame | cameracoordinate support | experiments/03_camera_pose_estimation/src/dataset.py:110 |
| Metric projection already exists | backproject | support medians | experiments/shared/geometry.py:20 |
| Task17 provisional/reference separation exists | validate_manifest/method_inputs | prompt/evaluator | experiments/06_object_recognition/shared/manifest.py:261 |
| Immutable completed artifacts are verified | verify_run | publication/cache | experiments/shared/runs.py:59 |
| Existing localization median comparator exists | localise_detection | rectangle baseline semantics | experiments/06_object_recognition/pilot/localisation.py:49 |

Owner delegated overnightcompletion/settings and efficiency on3October2026. Formalhuman/boundarymaskaccuracy and learnedbranch comparison are explicitly excluded from this initial available-data control. Record availability evidence, no fabricated completed learnedtrial. Plan review before statefulpublication; code/Pythonreview and finishedfreshdiffreview atclosure. Onefresh implementationworker, serialtasks; reviews can overlap documentation.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Original observations | method adapter | immutable calibrated images and declared source/frame identity | source hashes | experiments/03_camera_pose_estimation/src/dataset.py:17 |
| Run and independent labels | scorer/review | unique outputs, evaluator-only labels and SHA256 manifest | complete runs only | experiments/shared/runs.py:59 |

Original inputs, frozen configuration and independent labels are the source of truth. Only declared adapter records cross the method/scorer boundary. References never enter inference except explicitly declared oracle prompts. Process death before publication leaves an incomplete run; restart uses a new directory, never a partially overwritten origin. Fresh deployment verifies pinned packages/model provenance and inputs before execution; prior completed runs stay readable. No automatic database identity mutation occurs in these method comparisons.

## Hyperparameters

| Name | Value | Source |
|---|---|---|
| runtime | OpenCVpython5.0.0.93 / effective cv2 5.0.0; NumPy2.4.2; scoped pinnedrequirements | inherited installed runtime checked2026-10-03; confirmed 2026-10-03 singleOpenCVpackage freshsetup |
| sources/grid | Task17sixframes,11supports;640x480,525/525/319.5/239.5 | inherited Task17publishedreceipt |
| depth | /5000metres; rawzero missing; processed0<depth_m<4 | inherited experiments/03_camera_pose_estimation/src/dataset.py:123 |
| reference condition | RGBchecked bbox-only oracle; coarse masks not accuracyGT | inherited Task17policy; confirmed 2026-10-03 delegatedcompletion |
| rectangle | floorleft/top,ceilright/bottom, clampgrid; min2x2 and certain-background required | confirmed 2026-10-03 delegatedboundedtrial |
| GrabCut |5iterations,GC_INIT_WITH_RECT,no learnedweights | confirmed 2026-10-03 delegatedboundedtrial |
| RNG/threads |0seed perprompt,1OpenCVthread,serial | confirmed 2026-10-03 reproducible boundedcost |
| Canny/contour |50/150,aperture3,L2gradientTrue,RETR_EXTERNAL,CHAIN_APPROX_SIMPLE,largestarea fill,no morphology | confirmed 2026-10-03 simpleboundarycontrol |
| location/spread | component-wise median and q75-q25 IQR, NumPy linear quantiles; null if empty | confirmed 2026-10-03 bounded descriptive statistics, not calibrated uncertainty |
| optional predicted-box match | samecategory maximumcardinality then maxsumIoU, threshold0.5 | inherited Task18predeclared primaryscoring rule |
| repeat |1trial; no resizing; no smoothing/holefilling | confirmed 2026-10-03 efficiency |
| output |binary uint8mask0/255; originalgrid, everypromptaccounted | confirmed 2026-10-03 explicitmaskagreement |
| learnedbranch |n/a no acquiredmaskweights; no newmodels/downloads | n/a ownerconstraint, availabilityevidence to be recorded |
| boundaryscoring control |1pixel tolerance on synthetic exact masks only | confirmed 2026-10-03 evaluatorsoftwarecontrol, no realaccuracyclaim |

## Verification

Contract test: experiments/06_object_recognition/experiments/02_segmentation/tests/test_segmentation.py (proposed where not yet present). Exact fixture mask scores overlap 1; a disjoint mask scores 0; synthetic-only boundary and split/merge controls; real-reference scores must be unavailable; joining 2 separately labelled instances is reported as a merge. Thin parts, touching objects, empty masks, missing depth and malformed dimensions have explicit assertions. Hold prompts constant; references are evaluator-only except labelled checked-prompt controls.

Before: 0 independently scored mask comparisons. Target: 1 complete mask comparison with classical and available learned branches, or an evidenced unavailable branch. Targets count completed evidence/control artifacts; they are not operational accuracy thresholds. No performance improvement is assumed. At implementation, write meaningful controls first and observe failure, or obtain independent test review. Cover expected values, empty/one/many boundaries, invalid input, failure/recovery and reference separation. Changed implementation coverage must be at least 80%; lint/type and required integration/browser checks must pass. Record actual measurements and all unresolved follow-ups before closure.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No commit requested; verified working-tree implementation |
| Files changed | 02_segmentation masks/scoring/support/run/report/init/requirements/tests/README; stage06 README; pytest.ini; tools/check.py; this task record |
| Test status | 28 focused controls PASS; 92% production coverage (240 statements,19 misses); Ruff/mypy PASS; direct Black check PASS; accepted actual offline Edge review PASS; independent Python/code and fresh finished diff reviews PASS |
| Before measurement | 0 independently scored mask comparisons |
| After measurement | 1 completed bounded six-frame classical comparison;11 oracle-box plus4 cached cup prompts,45 mask outputs; exact synthetic evaluators only |
| Delta | 0 to1 classical comparison;6of6frames and15of15prompts recorded;0new inference/model downloads |
| Decision-gate outcome | Real provisional polygons excluded from formal accuracy. Learned mask branches explicitly unavailable: no acquired mask weights, existing YOLO26x detection-only, no new models/downloads. Oracle boxes are named prompts. Camera coordinate differences are not location error or calibrated uncertainty. Formal mask accuracy and learned/mobile/generalisation branches waived for this bounded available-data control |

Engineering complete; parent repository verification and task lifecycle move remain. No named implementation follow-up remains.

### Run and verification evidence

Initial completed publication: experiments/06_object_recognition/experiments/02_segmentation/runs/20261004T072334.650457Z_962f6eb065884ae3bfc05efacf6464d1. Manifest SHA256 `8143deb91d5c6a666dd3bb9e385a7a9f6347942d9c9f212e1e2aec95499bc9b3`;206 artifacts verified. Internal processing time5.735571seconds excludes preflight/final completion hashing. Mask generation totals rectangle0.000272seconds,GrabCut3.844102seconds,Canny0.005516seconds over15prompts each. Run captures exact settings and timings; no new accelerator inference. Offline installed Edge:6sections,57images,all640pxloaded,0pageerrors,0networkrequests.

Rectangle/Canny each15nonempty masks;GrabCut12nonempty and3empty. Empty/no-valid-depth supports preserve null coordinates. All masks stay original640x480binary0/255; raw zero missing and0<depth_m<4 processed. Rectangle medians match existing localise_detection with floor/ceil-rounded bounds. Predicted condition has4cupboxes and retains1missing cup reference in evaluator accounting. Non-exhaustive monitor references do not establish inventory counts. Synthetic controls alone score exact IoU/boundaries/split/merge; real formal accuracy remains null.

Focused initial controls observed RED before masks/scoring modules existed, then meaningful expected-answer controls passed. Tests use tiny clean git repositories outside experiments. Actual Windows junction output-alias and nested-root regressions reject before mutation and reverify original completed manifests. The short ancestry guard mirrors Task18 semantics locally because importing its private timed runner would add psutil/detector runtime dependencies to the classical deployment. No shared Run mutation or prior publication overwrite occurred. Formatting explicitly excludes runs snapshots. Initial mypy scipy-stub warning fixed with an explicit untyped-library annotation, no package installs. No Task13 full sequence or unrelated broad suite ran.


### Accepted final publication and review

Accepted final run: experiments/06_object_recognition/experiments/02_segmentation/runs/20261004T073228.246785Z_2716be65637647e2a0a499e5c493df1f. Manifest SHA256 `f3c7dddf0c7e047959e79895c611dd09fd5e0f0f677133974472fe1177060ec7`;206 artifacts verified. Internal time5.762825seconds, masks/depth/artifact plus source capture/report; final completion hashing and preflight excluded. Actual mask-generation totals rectangle0.000258seconds,GrabCut3.879175seconds,Canny0.005046seconds over15prompts each. Final offline Edge check:6sections,57images/all640pxloaded,0pageerrors,0externalrequests. No new inference or model downloads.

Independent Python reviewer APPROVE; fresh six-surface diff reviewer PASS, no reproducible HIGH/MEDIUM defects or unverified findings. HIGH provenance race fixed: every source is copied and SHA-verified first, then decoded only from saved run input paths. Regression substitutes conflicting decoded original pixels and proves original source paths are never decoded. MEDIUM callable-boundary ambiguity fixed: publishing helper private, production helper revalidates frozen Task17 manifest and accepted cache before any Run side effect; arbitrary synthetic fixtures cannot emit the real accepted-source stamp without explicit synthetic mode. Explicit requested bad cache fails before outputs; missing default optional cache records condition unavailable. Meaningful regressions pin all fixes. Twenty-eight focused controls pass;240statements/19misses=92%coverage. Ruff/package mypy/programmatic Black PASS. Initial run preserved and remains206-artifact verified, final fresh run owns reviewed code snapshot. Docs updated this session; no commit requested.

Root independently reran final28 focused tests:all passed in5.58seconds; final206artifactmanifest reverified before closure.
