---
id: "20"
title: Compare object appearance matching across viewpoint and revisits
status: closed
approval_status: approved
priority: MED
type: experiment
blocked_by: []
blocks: ["21", "22"]
verification_test: experiments/06_object_recognition/experiments/03_appearance/tests/test_appearance.py
plan_reviewed: 2026-10-04 PASS
files:
  - experiments/06_object_recognition/experiments/03_appearance/**
  - experiments/06_object_recognition/README.md
  - pytest.ini
  - tools/check.py
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/experiments/03_appearance/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Compare object appearance matching across viewpoint and revisits
  baseline_value: "0 scored object appearance comparisons"
  target: "1 bounded same-input ZNCC/ORB/SIFT/existing-YOLO-feature comparison, explicit unavailable/uncertain pairs"
created: 2026-10-03
last_updated: 2026-10-04
superseded_by: null
---

# Task 20: Compare object appearance matching across viewpoint and revisits

## In plain English

Check whether two observations look like the same object despite a changed view. Compare image correlation, local feature matches and learned appearance descriptions. Measure incorrect matches as well as missed returns.

## What

Implement ZNCC, ORB/SIFT and learned embedding comparisons in experiments/03_appearance using the same checked object support and enrollment/evaluation split.

## Why

Position alone can confuse nearby or moved objects; raw appearance can confuse identical objects or changing backgrounds. No scored appearance comparison exists.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Observation evidence descriptors already persist | canonical source payload | later identity decisions | experiments/06_object_recognition/src/identity_store.py:124 |
| Checked-mask protocol is proposed | Task17 | appearance methods | experiments/06_object_recognition/datasets/README.md:5 |

Initial available-data comparison on Task17's11provisional RGB-only supports and2enrollment/4evaluation frames, with one cup and two distinct monitor IDs. This is an explicitly named oracle-support appearance control, not automatic recognition or blind held-out accuracy. Coarse supports are already inspected; no thresholds are tuned. Similar-looking neighbours and identical synthetic patches expose appearance-only ambiguity. Missing scene-absence/lighting/rotation/movement scenarios remain recording gaps.

Compare masked zero-mean normalized cross-correlation (ZNCC), ORB/Hamming and SIFT/L2 matches, plus pooled features from the same acquired YOLO26x detector checkpoint. This reuses one existing model; do not download DINO/SAM or add a second model. Existing Ultralytics8.4.172 Model.embed extracts adaptive-average pooled second-to-last-layer features; explicitly record layerindex/type and vectorlength. These detection-trained features are not claimed re-identification embeddings. GPU inference is authorised for11distinct requested crop embeddings, once per crop, plus the installed Ultralytics first-call full-model warmup; reuse descriptors for every pair. Validate checkpointSHA9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92 before/after, runtime/deviceFP32/cuda0, no injection/fakeGPU receipt. Cache descriptor arrays with source/prompt hashes. Pin accepted original desk_smoke_v1.json SHA256 a786adc5f814ad9773712397f46ba79d8d40dc5c174fe17045336440cdffd920 before/after, in addition to Task17 publication verification. Source mask filenames contain instance IDs; methods receive arrays and opaque keys, never those filenames, identity-bearing source paths or truth records. Crop/descriptor methods see RGB+support and opaque observationkeys only, never instance answers; evaluator owns instance correspondence.

Preprocessing: floor/ceil-bbox crop from originalRGB, zero pixels outside provisional support, resize RGBbilinear and masknearest to128x128 (aspect maychange and is a declared limitation). No rotation search, alignment or augmentation. At the embedding boundary convert the RGB crop explicitly to contiguous BGR ndarray (Ultralytics ndarray preprocessing assumes BGR and flips to RGB). Its predictor then letterbox-resizes the128x128 crop to imgsz640 before embedding. Record both grids and avoid a second accidental RGB/BGR flip. The first embed call additionally triggers one full-model CUDA warmup forward; report that separately if measurable, otherwise label the first-call cost as inclusive of warmup. Do not describe11 requested embeddings as exactly11 total GPU forward passes. ZNCC uses jointly valid mask intersection, >=16supported pixels, demeaned grayscale values, nonzero variance; constant/empty cases return unavailable, not an invented match. ORB nfeatures500/scale1.2/8levels/edge31/patch31/fast20; SIFT nfeatures500/3octaves/contrast.04/edge10/sigma1.6/descriptorTypeCV_32F/enable_precise_upscaleFalse. Filter keypoints to support. Match KNN2 both directions, ratio0.75 and mutual consistency. If >=4matches, fit homography with cv2RANSAC3pixel threshold,2000iterations,.995confidence, seeded0; require >=4inliers and centered 2Dpointmatrix rank2 with NumPy rank tolerance1e-6 in bothcrops. Record descriptor matches/inliers/reprojection as appearance evidence only, never a metric camera transform. If no valid transform, scoreunavailable. Local-feature score is inliers/min(validkeypointcounts), plus inlier ratio and count. Learned score is cosine of finite nonzero pooledvectors; null for invalid/zero support. Report raw scores, cost and ranked samecategory galleries, not probability or a threshold selected from evaluation. Report top1/ties (scoretie tolerance1e-6) as descriptive diagnostics only; never break an indistinguishable neighbour tie into an identityclaim. Enrollment has4gallery observations across2frames; evaluation has7objectqueries across3positiveframes and1gapframe with0queries. A same-looking negative can have similarity1; label it as ambiguous rather than proof of identity.

Use the same oracle-support condition for allmethods; do not silently swap Task19predicted masks. Those can be a later substitution control requiring matchedmask provenance. Save all11crop outcomes including unavailablefeatures, all25samecategory distinct-observation pairs (16sameidentity/9differentidentity), including same-frame neighbours, with truth only in evaluator, separate source/config/evaluator artifacts, descriptor timings/memory including modelload/transfer, sourcehashverification and Runpublication. Production no appservice/dbmutation. Staticreview shows cropgallery, pairscorematrices, positive/negative labels in evaluatorview and unavailablecases. Fresh deployment uses scoped03_appearance/requirements.txt pinning opencv-python==5.0.0.93 (effectivecv2 5.0.0), numpy==2.4.2 and the existing pilot/shared requirements; reject runtime mismatch and do not install opencv-contrib alongside it. Use the already installed environment overnight with no downloads or installs. Freshsourcehandoff requires verifiedTask17publication and existingcheckpoint/pinnedruntime; no implicitdownload. UniqueRun, crashincomplete, restartfresh, priorartifacts unchanged. Synthetic exactvalue/boundary/identity-separation controls; focusedmodule>=80%coverage, Python/code and freshfinisheddiffreview beforeclose. Task13 untouched.

### Additional reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Existing checkpoint is hash-verified before construction | YoloDetector | pooled-feature adapter | experiments/06_object_recognition/pilot/detector.py:27 |
| Capture-only sources/labels are separate | method_inputs | sourceledger | experiments/06_object_recognition/shared/manifest.py:261 |
| Provisional maskreview is recorded | desk_smoke_v1 provenance | oracle-support condition | experiments/06_object_recognition/datasets/desk_smoke_v1.json:32 |
| Same acquired model supports embeddings | installed Ultralytics Model.embed | featureadapter | .venv-yolo/Lib/site-packages/ultralytics/engine/model.py:447 |
| Pooling and layer-return behavior exists | installed BaseModel._predict_once | featureadapter | .venv-yolo/Lib/site-packages/ultralytics/nn/tasks.py:194 |
| Immutable verified publication exists | Run/verify_run | experimentartifact | experiments/shared/runs.py:59 |

GPU11-cropfeature trial and new numericalchoices are covered by owner overnightdelegation. No new learnedmodels/weights, no training, no accuracythreshold tuning. Require planreview againstactualinstalled APIs/settings beforestart.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Original observations | method adapter | immutable calibrated images and declared source/frame identity | source hashes | experiments/06_object_recognition/shared/manifest.py:73 |
| Run and independent labels | scorer/review | unique outputs, evaluator-only labels and SHA256 manifest | complete runs only | experiments/shared/runs.py:59 |

Original inputs, frozen configuration and independent labels are the source of truth. Only declared adapter records cross the method/scorer boundary. References never enter inference except explicitly declared oracle prompts. Process death before publication leaves an incomplete run; restart uses a new directory, never a partially overwritten origin. Fresh deployment verifies pinned packages/model provenance and inputs before execution; prior completed runs stay readable. No automatic database identity mutation occurs in these method comparisons.

## Hyperparameters

| Name | Value | Source |
|---|---|---|
| source/support/partition | Task17sixframes/11supports,2enrollment/4evaluation/0validation; oracleprovisionalmask | inherited Task17publishedmanifest |
| model/checkpoint/runtime | YOLO26x,9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92; Ultralytics8.4.172/Torch2.11.0+cu128/cuda0FP32/batch1/augmentFalse/imgsz640/rectTrue/halfFalse | inherited Task28modelsettings; confirmed 2026-10-03 existing-modelfeaturetrial |
| embedding | adaptiveaveragepool, layerlen(model.model)-2; recordindex/type/vectorlength atpreflight | inherited installed Ultralyticsengine/model.py:484 and nn/tasks.py:205 |
| embedding preprocessing/warmup | contiguous BGR ndarray input from RGB crop; predictor letterbox128 to640; first-call full-model CUDA warmup plus11 requested embeddings | inherited installed predictor.py:183,230,379 and autobackend.py:375; confirmed 2026-10-04 explicit cost/input trace |
| crop |128x128; RGBbilinear/masknearest; aspectreshape, blackoutside; no rotations/augmentation | confirmed 2026-10-03 bounded commonappearancecontrol |
| ZNCC |intersection mask>=16pixels; variance>0; null otherwise | confirmed 2026-10-03 numericalsupportvalidation |
| ORB |nfeatures500,scale1.2,8levels,edge31,firstlevel0,WTA_K2,HARRISscore,patch31,FAST20,Hamming | confirmed 2026-10-03 explicitclassicalbaseline |
| SIFT |nfeatures500,nOctaveLayers3,contrast.04,edge10,sigma1.6,descriptorTypeCV_32F,enable_precise_upscaleFalse,L2 | confirmed 2026-10-03 explicitclassicalbaseline |
| matching |KNN2,ratio0.75,mutual; crossCheckFalse; >=4matches/inliers; pointmatrixrank2 at1e-6 | confirmed 2026-10-03 bounded 2Dverification |
| homography |RANSAC3px,2000iterations,.995confidence; RNG0,OpenCVthreads1 | confirmed 2026-10-03 deterministicboundedcontrol |
| scores |ZNCCraw[-1,1],featuresinliers/min(keypoints),learnedcosine[-1,1]; null whenunsupported | confirmed 2026-10-03 descriptivecomparison; no calibratedprobabilityclaim |
| ranking tie | absolute score difference<=1e-6; no forced identity from tie | confirmed 2026-10-03 numericaltiecontrol, not accuracythreshold |
| operatingthreshold |n/a none selected/tuned; rankings/ties descriptiveonly | n/a no validationpartition or blindaccuracyclaim |
| runtime |OpenCVpython5.0.0.93/effective5.0.0; NumPy2.4.2; own scopedrequirements plus pilot/sharedrequirements | inherited installedversions checked2026-10-03; Task19scopedpin |
| repeats/cache |1descriptor extraction per11source support; eachpair scoredonce; no learning | confirmed 2026-10-03 efficiencyrequest |

## Verification

Contract test: experiments/06_object_recognition/experiments/03_appearance/tests/test_appearance.py (proposed where not yet present). Identical nonconstant supported patches have ZNCC 1; constant/zero-support patches return declared unavailable evidence. Identical nonzero vectors have cosine similarity 1; zero vectors are unavailable. Independent labels expose same-looking different objects as negative pairs. No evaluation-frame descriptor enters enrollment/tuning. Compare at an approved operating point, not retrospectively selected held-out thresholds.

Before: 0 scored object appearance comparisons. Target: 1 frozen same-input comparison of correlation, local features and an available learned appearance branch. Targets count completed evidence/control artifacts; they are not operational accuracy thresholds. No performance improvement is assumed. At implementation, write meaningful controls first and observe failure, or obtain independent test review. Cover expected values, empty/one/many boundaries, invalid input, failure/recovery and reference separation. Changed implementation coverage must be at least 80%; lint/type and required integration/browser checks must pass. Record actual measurements and all unresolved follow-ups before closure.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Uncommitted working-tree delivery; no commit requested |
| Files changed | 03_appearance/{__init__,adapter,cache,compare,evaluator,features,report,run}.py, scoped requirements and README, three focused test files; stage06 README, pytest.ini, tools/check.py; this task |
| Test status | Red first: missing adapter module failed collection. Final 41 focused tests PASS; implementation coverage 334/368 statements = 90.76% (reported 91%). Ruff PASS, programmatic Black PASS, mypy -p PASS (12 modules). Final actual offline Edge: 11/11 crop images loaded, 25 pair rows, 0 page errors, 0 external requests. Verified accepted descriptor-cache read: 11 rows, 0 new inference. Python/code reviews and fresh diff review PASS after findings repaired; root retains independent review receipts. |
| Before measurement | 0 scored object appearance comparisons |
| After measurement | 1 verified same-input comparison: 11 observations, 25 same-category pairs (16 same identity, 9 different identity), 4 gallery observations, 7 queries. ZNCC 25 available pairs and 7 correct descriptive rankings; ORB/SIFT 0 available recorded pairs and 7 unavailable rankings each; existing YOLO pooled features 25 available pairs, 6 correct and 1 wrong ranking. |
| Delta | +1 bounded comparison, +25 scored pair records, explicit unavailable local-feature outcomes and one false learned appearance match |
| Decision-gate outcome | Complete bounded inspected-data comparison, not blind accuracy or approval of an operating threshold. No new models/downloads; existing YOLO26x used once for 11 crop requests plus installed first-call full-model warmup. Learned feature extraction runtime CUDA0 FP32, layer22 C3k2, vectorlength768. Missing controlled recording scenarios and broader new-model comparisons are explicitly deferred under owner scope. |

Accepted run: experiments/06_object_recognition/experiments/03_appearance/runs/20261004T135203.039973Z_fd481f16c8374ca2a0f04d6f0703a16d/review.html. Completion manifest SHA256 f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4; 140 artifacts verified. It is pinned in cache.py for exact descriptor reuse. Feature-code provenance pins adapter.py, features.py, pilot/detector.py and actual PREDICT_SETTINGS, plus inputs/config and original/published annotation hashes. Cache acceptance pin changed after publication; feature-producing code and original artifacts did not change.

Measured costs: model construction0.629552s; eleven requested GPU embeddings4.076556s, first call3.961634s including full-model warmup; transfer0.001344s. Descriptor stage9.676336s includes imports/preparation/classical extraction/model/inference/transfer. Run ledger11.052647s through timing publication, excluding final manifest hashing/completion publication. GPU process peaks404958208allocated/501219328reserved bytes. Per-method classical extraction and per-pair comparison costs are retained.

False appearance match: evaluation o008, black monitor frame405, ranked silver enrollment o002 cosine0.9540935668 above black o0010.9109874014. Cup rankings have no different-cup negative and cannot establish same-class cup separation. ORB/SIFT unavailable reasons: insufficient keypoints/mutual matches/no finite homography. Identical-neighbour synthetic controls abstain; synthetic textured self-matches succeed. These are appearance diagnostics, not persistent-ID assignments.

Review findings repaired: transitive detector producer/settings missing from cache signature (regression pins owner and changed imgsz); output under frozen publication/raw data/checkpoints could corrupt inputs (resolved guards and six no-effects controls). Output aliases are resolved before creation. Root fresh diff review PASS before final publication; only formatting, accepted manifest pin and receipts/docs changed afterward.

Ultralytics emitted an existing-settings schema migration warning (values preserved where possible) and deprecated half warnings. Actual precision was float32. Task13 files/settings and full sequence were not edited/run by this task; unrelated dirty files and accepted Task17/18/19/28 artifacts were preserved. No second GPU extraction was performed. Requirements are a deployment handoff, not an overnight install. Scope waivers: controlled lighting/rotation/moved/identical-neighbour recorded cases absent, exact segmentation boundaries unavailable, second-cup negatives absent, no calibrated similarity operating threshold or unseen-session accuracy claim.
