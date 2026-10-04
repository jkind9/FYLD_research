---
id: "18"
title: Evaluate object detection on frozen labelled observations
status: closed
approval_status: approved
priority: MED
type: experiment
blocked_by: []
blocks: ["22"]
verification_test: experiments/06_object_recognition/experiments/01_detection/tests/test_detection.py
plan_reviewed: 2026-10-03 PASS
files:
  - experiments/06_object_recognition/experiments/01_detection/**
  - experiments/06_object_recognition/README.md
  - pytest.ini
  - tools/check.py
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/experiments/01_detection/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Evaluate object detection on frozen labelled observations
  baseline_value: "0 scored detector comparisons"
  target: "1 complete frozen-input comparison with every selected frame accounted for"
created: 2026-10-03
last_updated: 2026-10-04
superseded_by: null
---

# Task 18: Evaluate object detection on frozen labelled observations

## In plain English

Measure whether objects can be found and labelled in the selected recording. Keep the same images and scoring rules for each detector. Preserve missed and duplicate detections rather than showing only successful frames.

## What

Implement pinned cached-YOLO26x extraction, pure one-to-one evaluation and offline overlays in stage06 experiments/01_detection. Compare the accepted detector with an explicitly named empty-prediction accounting control. Other Task16 shortlist models are waived for this bounded initial comparison because local weights are unavailable and downloads are not authorised. Mask refinement and identity scoring remain separate.

## Why

YOLO26x detection is already implemented in the pilot; reference poses and a persistence database cannot find objects in pixels.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Run publication already hashes completed outputs | Run | new detector runner | experiments/shared/runs.py:137 |
| Stage-specific observations/labels are owned by Task17 | proposed agreement | detector/scorer | experiments/06_object_recognition/README.md:35 |

Use the existing verified GPU YOLO26x predictions for Task17's exact six original frames; do not repeat inference. Task28 complete-run manifest SHA256 is e07af81930e80fe7400c0a0b12b26138c3fea6f7533b1b8137b5186a587267a3. Verify the completion manifest and all artifacts before extracting original-pixel class/score/xyxy proposals from output/detections.json by source_selection_index, crosschecked against output/selection.json RGB/sourceframe/hash. Validate checkpoint hash, package/settings/device/precision metadata from verified run; preserve cached inference timings as predecessor costs and report new evaluation costs separately. Cache extraction reads no GT poses, instance IDs or association outputs. All inference was completed before Task17 labels; no model input consumes labels. Include all proposals in output; score only complete cup coverage. Non-exhaustive tv labels support matched positive subset diagnostics only, with zero precision/recall or false-positive claim for tv. Compare YOLO26x to explicitly named empty-prediction software control; other shortlist models are deferred without weights/downloads.

Pure scoring: validate finite bounded original-pixel xyxy, category/class and confidence, duplicate source/frames. Build maximum-cardinality one-to-one IoU match followed by maximum summed IoU (not greedy order). Record every matched/unmatched prediction/reference and duplicate candidate. Cup denominators computed for all6frames including negativegap; zero denominators yield null. Threshold sensitivity0.3/0.5/0.7 is predeclared, not chosen from scores. Coarse box labels and already inspected within-session frames make these smoke diagnostics, not a formal held-out accuracy claim. Monitors have separate reference IDs but non-exhaustive labels; show matched/missed annotated subset and unscored proposals without false-positive claims. Add duplicate/nearby-neighbour/cross-order synthetic evaluator controls.

Publish through existing Run, copying only6sourceRGB/annotation/cachedproposal/receipt artifacts plus source snapshots; use actual repository as repo for production and tiny clean fixture repo for tests so snapshot walks never scan temporary fixtures. Require no inference rerun. Save overlays, perframe diagnostics, method/evaluator separation, own walltimes/memory, predecessor costs and complete settings. Preserve Task13. Record immutable receipt hashes and all failure outcomes. Fresh deployment needs Task17 offline sources and explicitly transferred accepted Task28 run; preflight fails if unavailable, no implicit downloads. Restart uses a fresh run; incomplete runs rejected. Existing run/artifact hashes unchanged. Update discovery and docs this session.

### Additional reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| YOLO class/score/original pixel proposals already exist | YoloDetector | cached GPU run | experiments/06_object_recognition/pilot/detector.py:49 |
| Completion rejects missing/changed artifacts | verify_run | cache preflight | experiments/shared/runs.py:59 |
| Task17 capture-only projection excludes labels | method_inputs | detector input ledger | experiments/06_object_recognition/shared/manifest.py:261 |
| SHA256 streamed source validation exists | sha256 | provenance checks | experiments/datasets/acquisition.py:48 |

Plan lane: experiment publication with existing inference; one plan reviewer, one fresh implementation worker, one Python/code reviewer and one finished diff reviewer (4agents). Avoid broad tests or copied giant repositories. Efficiency and preserve-dirty directions override night-shift's clean-tree/full-suite/commit defaults. The owner explicitly delegated choices and overnightGPU work; every selected value is recorded below.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Original observations | method adapter | immutable calibrated images and declared source/frame identity | source hashes | experiments/06_object_recognition/shared/manifest.py:50 |
| Run and independent labels | scorer/review | unique outputs, evaluator-only labels and SHA256 manifest | complete runs only | experiments/shared/runs.py:59 |

Original inputs, frozen configuration and independent labels are the source of truth. Only declared adapter records cross the method/scorer boundary. References never enter inference except explicitly declared oracle prompts. Process death before publication leaves an incomplete run; restart uses a new directory, never a partially overwritten origin. Fresh deployment verifies pinned packages/model provenance and inputs before execution; prior completed runs stay readable. No automatic database identity mutation occurs in these method comparisons.

## Hyperparameters

Audit inherited Task17 review: historical run snapshots contain divergent experiment settings; no new inference settings here. Reuse accepted run only.

| Name | Value | Source |
|---|---|---|
| model/checkpoint | YOLO26x;9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92 | inherited Task28 verifiedreceipt |
| inference | cuda:0FP32, Ultralytics8.4.172;640/conf0.25/NMS0.7/max_det300/batch1/augmentFalse/rectTrue/halfFalse | inherited experiments/06_object_recognition/pilot/detector.py:16 and accepted Task28 metadata |
| source frames | Task17 sixframes selectedindexes0,9,27,37,42,59 | inherited experiments/06_object_recognition/datasets/desk_smoke_v1.json |
| target | cup complete; tv positive subset unscored precision/recall | inherited Task17 labelcoverage |
| IoU thresholds | 0.3,0.5,0.7, report all; primary0.5 | confirmed 2026-10-03 under delegated overnightcompletion; fixeddiagnostic sensitivity, no thresholdtuning |
| assignment | max cardinality, then max summedIoU; samecategory only; one-to-one | confirmed 2026-10-03 under delegatedcompletion |
| repeats/new inference | 1 evaluation;0 new model runs | confirmed 2026-10-03 efficiency request; reuse verifiedcached outputs |
| control | empty predictions | confirmed 2026-10-03 diagnostic miss/accounting control |
| output | all proposals;6frames; default finite source bounds; no sampling | inherited Task17/Predictsettings; confirmed 2026-10-03 |

## Verification

Contract test: experiments/06_object_recognition/experiments/01_detection/tests/test_detection.py (proposed where not yet present). A fixture with 1 expected instance and 2 duplicate predictions records 1 true match and 1 false detection; an empty prediction records 1 miss. Empty-reference/empty-prediction cases have declared unavailable metrics, not invented perfect scores. Malformed output cannot publish complete. Independent scoring review and red-first controls must pass.

Before: 0 scored detector comparisons. Target: 1 complete frozen-input comparison with every selected frame accounted for. Targets count completed evidence/control artifacts; they are not operational accuracy thresholds. No performance improvement is assumed. At implementation, write meaningful controls first and observe failure, or obtain independent test review. Cover expected values, empty/one/many boundaries, invalid input, failure/recovery and reference separation. Changed implementation coverage must be at least 80%; lint/type and required integration/browser checks must pass. Record actual measurements and all unresolved follow-ups before closure.

## Receipts

| Field | Value |
|---|---|
| Closing commit | None; no commit requested; existing dirty changes preserved |
| Files changed | New experiments/06_object_recognition/experiments/01_detection/{cache.py,scoring.py,report.py,run.py,__init__.py,requirements.txt,README.md,tests/test_detection.py,tests/test_cache.py,tests/test_publication.py}; stage06 README; pytest.ini; tools/check.py; this task receipt |
| Test status | 60 focused controls passed; focused statement coverage89%; combined tests plus final verified CLI coverage97% (cache93%, scoring99%, report100%, runner98%). Ruff, programmatic Black check and mypy package check passed. Final accepted offline Edge report:6images/6sections,0page errors,0external requests. Python and independent cache/publication test review PASS; finished diff review PASS after portability and nested-output fixes |
| Before measurement | 0 scored detector comparisons |
| After measurement | 1 accepted six-frame detector/control comparison; all IoU0.3/0.5/0.7: cup4matches/5references,1miss,0false detections,P1.00/R0.80; monitor6matches/6annotated positives,13proposals,P/R/FPnull. Empty control misses5cups and6monitor positives at each threshold. No new inference |
| Delta | 0 to1 scored detector/control comparison;6of6frames accounted for;0new model runs |
| Decision-gate outcome | Bounded within-session coarse-reference smoke diagnostics only. Additional detectors waived: unavailable local shortlisted weights and no downloads. Formal blind accuracy, new-session/object generalisation, mask-boundary accuracy and mobile performance claims waived: already inspected coarse references and no phone measurements |

Engineering completion, reviews, final publication and declared docs are complete. No implementation follow-up remains. Coordinator owns the final repository verification and board transition; no commit was requested.

### Immutable run and verification receipts

Accepted final-source run: experiments/06_object_recognition/experiments/01_detection/runs/20261004T071442.158193Z_4be5db5d6dca43e4be715c0665e44fcd. Completion manifest SHA256 `7ee60f385871eeb6288c007bc03a548a233a2fee3e6dcf7cca9a5f583a15e39c`;103artifacts verified. Offline review.html and output/scores.json expose all frames, predictions and per-threshold accounting. External execution companion SHA256 `901356e451cb2465f58b0792a8a7b1aaffea781b1ffc434514c9a3643650e344` pins this run manifest. Final Python/diff reviews PASS and actual offline Edge verification PASS.

Dedicated CLI process creation through verification:6.163537seconds (Windows OS creation timestamp/wallclock, includes imports). Evaluation entry through verification:5.299256seconds (monotonic). Preflight0.198676seconds; input-copy0.160921seconds; scoring0.133819seconds; report0.242575seconds. Measured under coverage instrumentation. Peak Windows process working set124,420,096bytes; peak traced Python allocations16,652,149bytes, separately scoped. No new accelerator allocations or inference. Preserved60-frame predecessor cost6.681731seconds, model-load1.321259seconds/detection2.382105seconds, not misattributed to new six-frame scoring.

Original Task28 run still verifies195artifacts with pinned manifest `e07af81930e80fe7400c0a0b12b26138c3fea6f7533b1b8137b5186a587267a3`. First Task18 publication remains verified102artifacts with manifest `fe14b262b1bd1b1f9092435e13b6fb45ba748ce7c61e1a5ecafed10138494f26`; replaced by a fresh publication after validation/tracing/cost fixes. One broad formatter traversal touched7source-snapshot copies in the first Task18 run. Each was restored from source only after verifying its exact original manifest SHA256; the original manifest/artifacts verify again. Formatter now excludes runs. No original model/source/Task13 artifact was altered.

Initial scoring controls observed RED (missing scoring module), then passed expected-answer controls. Independent cache/publication test review PASS covers accounting, input/reference separation, failed-copy recovery, exact production pin and tamper/missing/unavailable controls. Python review fixed unknown-class/missing-label validation and preflight tracer ownership, each with regression controls. Fresh diff review fixed the default-check dependency on an ignored local generated cache: optional recorded-data check skips only when that cache is absent; synthetic unavailable-cache controls still assert fail-closed behaviour.

Verification failures preserved in this receipt: initial RED collection failure; first fixture attempt failed with Windows sandbox temporary-directory ACL, then accessible escalated temporary fixtures passed; original-path and recorded half=None metadata mismatches corrected before accepted publication; numeric-package mypy path invocation rejected, corrected to package invocation `-p`; no model/inference retry. Tests use tiny clean git fixture repositories outside experiments; no copied project trees. Docs updated this session. No unrelated broad suite or commit was run.

4October final-diff findingDR-1: output beneath a prior completed run could add artifacts and invalidate that run's inventory. Added a shared resolved-output guard before both public preflight and internal publication. It checks destination plus every ancestor for an existing Run status marker and rejects before mutation. Four expected-answer controls observed RED, then GREEN: output equal to the prior run, its runs child, a deeper debug child and a real Windows junction alias. Both entry paths reject and original manifests continue verifying. Final focused suite60passed,89%newimplementation coverage; Ruff/mypy passed. Follow-up of the existing reviewer initially returned agent-thread-limit; coordinator resumed the same reviewer after a slot freed. Final six-surface re-review PASS, no remaining findings or unverified surfaces. Root independently reran the final60focused tests:all passed in8.53seconds. No code or source artifacts outside Task18 were changed by the fix.

## Authorised exploratory predecessor, 3 October 2026

The owner selected YOLO as the easy starting point, then authorised GPU and delegated a good pretrained model and one suitable frame. Task27 owns the single-frame YOLO26x cup trial and detection review followed by RGB-D localisation. Its unscored output is preparation for this task, not the frozen multi-detector benchmark. Use this evidence when choosing the formal comparison; Task17 labels, split decisions and accuracy scoring remain required.
