---
id: "22"
title: Build recorded video camera surface and inventory replay
status: pending_review
approval_status: approved
priority: MED
type: experiment
blocked_by: []
blocks: []
verification_test: experiments/06_object_recognition/experiments/05_replay/tests/test_replay.py
plan_reviewed: null
files:
  - experiments/06_object_recognition/experiments/05_replay/**
  - experiments/06_object_recognition/README.md
  - README.md
  - task_list/README.md
  - pytest.ini
  - tools/check.py
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/experiments/05_replay/README.md
  - README.md
  - task_list/README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Build recorded video camera surface and inventory replay
  baseline_value: "0 matched-input camera surface inventory replays"
  target: "1 verified integrated replay with 0 broken artifact links and complete selected-frame accounting"
created: 2026-10-03
last_updated: 2026-10-04
superseded_by: null
---

# Task 22: Build recorded video camera surface and inventory replay

## In plain English

Show the recording, camera movement, growing surface and recognised objects together. Make every result traceable to its source frame. Show failures and unknown identities while the recording progresses.

## What

Publish one offline interactive replay containing two explicitly separate conditions: the unchanged Task28 60-frame geometry baseline and a new six-frame automatic cup/monitor association condition. Reuse cached YOLO detections, measured depth and supplied TUM poses. Extract learned appearance descriptors only from the new condition's actual detector boxes, then apply Task21's pure combined association and location policies. Show every observation and unresolved proposal. Estimated camera-path execution is excluded until Task13 supplies completed evidence.

## Why

The existing pilot already shows RGB, camera position, growing coloured points and retained labels. It lacks explicit camera orientation and comparison between individual measurements and a robust position estimate. Appearance descriptors computed from independent reference masks would silently change an automatic detector experiment. The new condition therefore gets its own actual-box descriptor cache and ledger, while the existing baseline remains immutable and visible.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Pilot already saves synchronized camera poses, cloud boundaries and original measurements | replay | checked baseline reader | experiments/06_object_recognition/pilot/replay.py:573; experiments/06_object_recognition/pilot/replay.py:606 |
| Offline synchronized playback and boxes already exist | write_replay_review | reuse behavior and payload conventions in new focused renderer | experiments/06_object_recognition/pilot/replay_viewer.py:94; experiments/06_object_recognition/pilot/replay_viewer.py:145 |
| Accepted detector-cache production pin and exact six-frame join already exist | load_accepted_cache | automatic proposal adapter | experiments/06_object_recognition/experiments/01_detection/cache.py:150 |
| Accepted pin is distinct from fixture helper | check_cache / load_accepted_cache | production cannot substitute expected hash | experiments/06_object_recognition/experiments/01_detection/cache.py:60 |
| Box median camera/world coordinates already exist | localise_detection | automatic surface-location adapter | experiments/06_object_recognition/pilot/localisation.py:54 |
| Camera-to-world projection exists | backproject / transform_points | independent fixture and revision cloud builder | experiments/shared/geometry.py:20; experiments/shared/geometry.py:78 |
| Calibrated camera frustum already exists | frustum | orientation trace | experiments/shared/visualization.py:67 |
| Verified immutable run and completion boundary exist | Run / verify_run | new integrated generation publication | experiments/shared/runs.py:59; experiments/shared/runs.py:137; experiments/shared/runs.py:229 |
| Existing acquired checkpoint constructor pins hash | YoloDetector | actual detector-box appearance extraction | experiments/06_object_recognition/pilot/detector.py:27 |
| Capture-only projection excludes identity/revisit answers | method_inputs | method/scorer separation | experiments/06_object_recognition/shared/manifest.py:261 |
| Revision sidecar enforces origin and parent ownership | validate_pose_revisions | synthetic coherent-generation control | experiments/06_object_recognition/shared/pose_revisions.py:67 |
| Accepted appearance cache exposes checked vectors | read_verified | actual-box adapter may reuse only matching source/config/code pins | experiments/06_object_recognition/experiments/03_appearance/cache.py:34 |
| Task21 owns fixed association and location rules | associate_frame / estimate | new actual-box observations in each automatic condition | experiments/06_object_recognition/experiments/04_geometry_identity/association.py:272; experiments/06_object_recognition/experiments/04_geometry_identity/locations.py:73 |
| Task21 owns strict persisted-generation reads | read_generation | new viewer input adapter verifies completed condition artifacts | experiments/06_object_recognition/experiments/04_geometry_identity/persistence.py:147 |

### Pins and preflight before effects

Hyperparameter audit run on 4 October reported 220 declaration sources including historical run snapshots and unrelated stages. Preserve old receipts and Task13 choices; the new six-frame association condition deliberately differs from the pilot's last-position geometry policy. Mirror the table below in HYPERPARAMETERS and receipts.

Production inputs are the accepted Task28 run experiments/06_object_recognition/pilot/runs/20261003T200418.845966Z_f20e5b1de3744f47a850ffa3b3ba396b, completion manifest SHA256 e07af81930e80fe7400c0a0b12b26138c3fea6f7533b1b8137b5186a587267a3 (195 verified artifacts), and Task17 desk_smoke_v1 publication. Pin its receipt eb30954d32b56778d55ac4a1858dd933ddec7550d2aa4da5bfb9e9ae1b5d57e3, published annotations 27fe047dac254161ea823d6c55aeb28e16bd88cd993f1e4bf8fbdee40d4741d3 and original annotation source a786adc5f814ad9773712397f46ba79d8d40dc5c174fe17045336440cdffd920. Verify all original RGB/depth/table hashes against the existing archive-member ledger. Task18 accepted completion manifest is 7ee60f385871eeb6288c007bc03a548a233a2fee3e6dcf7cca9a5f583a15e39c; read its six-frame proposal extraction using original source keys, never scoring matches as identity hints. Task19 masks are comparison evidence only and do not replace box supports.

The accepted Task20 run is `experiments/06_object_recognition/experiments/03_appearance/runs/20261004T135203.039973Z_fd481f16c8374ca2a0f04d6f0703a16d`, with 140 artifacts and completion manifest SHA256 `f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4`. The accepted cache reader validates the full manifest, feature code and input signature. Its descriptor receipt has 11 vectors, layer22 (`C3k2`), 768 float32 values, CUDA0, and the existing checkpoint hash. The accepted Task21 run is `experiments/06_object_recognition/experiments/04_geometry_identity/runs/20261004T143434.634726Z_33f59456f7d34e50a64020ed6e0613bb`, 172 files, complete manifest SHA256 `75a1b943ab087d846a87d71289b4e118063fad8bac2010694e1521499046d6f7`. Task21 schema version1 owns `association.associate_frame` at `association.py:272`, `locations.estimate` at `locations.py:73`, and hash-checked `persistence.read_generation` at `persistence.py:147`. Read every required Task21 condition through that reader before reuse. Its cross-session guard compares session/world/segment; new records must preserve the session boundary. Both accepted runs and their source code snapshots remain immutable. No generic replacement expected hash or injectable production inference callback. Pure fixture helpers identify synthetic provenance and cannot publish accepted GPU evidence.

Before mkdir, Run snapshot, copy, database or model construction, resolve output, source publication/cache/checkpoint/source roots and previous completed-run ancestors. Reject output equal to or inside protected inputs, prior completed runs or accepted capture roots. Do not use a broad source-root ancestor as a publication destination. The own runs directory may contain previous completed siblings: allocating a fresh unique child there is allowed, while nesting beneath any prior run is rejected; reject symlink/junction/reparse aliases and traversal. Output stays inside workspace. Existing completed-run status markers in any output ancestor cause rejection. Default is own runs directory plus unique Run child. Check ancestry before snapshot recursion, not after writing metadata. Reuse an existing scoped guard if its actual completed implementation covers these checks; otherwise own a small adapter within this task. Basetemp under outputs or OS temp, never an experiment/snapshot input.

### Two conditions and strict input accounting

Read all 60 baseline frames, 457 cached detector proposals, recorded camera-to-world matrices and cloud_display.npz from Task28. Copy immutable original artifacts into new Run input by exact bytes and record each source/destination SHA256; do not rewrite the baseline ledgers or import their assigned IDs into the new method. Preserve all classes and unknown/unresolved proposals. Baseline IDs are algorithm outputs, not physical truth: five TV track IDs do not imply five distinct physical monitors.

Automatic condition is exactly selected indexes [0,9,27,37,42,59], original source frame IDs [23,104,268,359,405,560]. Its cup/tv proposal set is exactly 4 cup and 13 tv detections, 17 total. Preflight asserts this against checked cache; changes fail, rather than silently resize the trial. All other 440 proposals remain inspectable in baseline. The six frames share their original RGB/timestamps/calibration/depth/pose with baseline. Source frame268 at1305031463.059810 is independently verified physical cup absence, followed by return359 at1305031466.095840. The earlier 27 sampled YOLO misses are detector misses and are not continuous visual absence. Every automatic frame appears even if there are zero cup detections; no fabricated observation fills the gap.

The new method receives capture-only source records and detector class/box/confidence, opaque keys and camera geometry. Reference identity IDs, oracle masks, return answers and detection-to-reference matches go only to the evaluator. Cup reference is complete on these six frames; monitors are a provisional positive subset. Evaluation may compare proposal boxes to references with Task18's fixed same-class one-to-one matching at IoU0.5, but that mapping never enters association or gallery. Report unresolved/unmatched/missed references and association errors separately; no formal blind generalisation, physical-centre error or exhaustive monitor inventory claim.

### Actual detector support and bounded GPU work

Reuse Task20's actual completed crop/pooled-feature adapter with all-one support inside each floor/ceil-clamped detector rectangle, never an oracle polygon or descriptor copied from an oracle crop. Use original RGB pixels, crop128x128 RGB bilinear/mask nearest and explicit contiguous BGR ndarray at Ultralytics boundary, predictor imgsz640. Invalid crop/support remains unavailable. Extract one descriptor per distinct actual proposal key, at most17 requested crop embeddings, batch1, using existing hash-verified YOLO26x cuda0 FP32. Record the installed first-call full-model warmup separately or label first-call inclusive of warmup; 17 requests is not a claim of17 total GPU forwards. No detector rerun, training, downloads, package installs or alternative model. Hash checkpoint before/after and validate actual runtime/layer/vector size. Cache descriptors once for all policies and viewer accesses.

Localise actual rectangles through existing localise_detection on checked depth and supplied poses; store original camera/world observed-surface medians and support validity. Task21 robust location policies use these box-conditioned coordinates, not reference-mask geometry from its oracle experiment. No depth yields null; no pose yields no metric identity birth/update. Use Task21 combined-last and combined-viewmedian policies side by side, including fixed anchor, appearance gate, duplicates, global ambiguity, conservative births and independent-view groups. This is the same policy implementation with different explicit support condition, not reused oracle decisions. Preserve original observation coordinates and all rejected/candidate/alternative records. Appearance similarity never weights spatial precision. Frame gap retains estimate. Real cup return success is measured, not promised: if missing initial/return proposals, failed descriptor or conservative gate prevents it, report that result.

### Viewer and persistence ownership

Own small modules under 05_replay/src/: checked_inputs.py, automatic.py, generation.py, payload.py and report.py; experiment run.py, scoped requirements and focused tests. Adapt the pilot's already working synchronization/payload logic; reuse shared frustum and existing point sampling. Render a new condition-aware offline page with focused HTML/JS assets in this experiment. Do not modify pilot or shared renderer monoliths, and preserve Task23's inherited shared viewer changes. Every new code file stays below800 lines. No stage04 reconstruction run or Task13 estimated-pose run is needed: supplied-pose baseline geometry is already cached.

One page has a clearly labelled condition selector, RGB playback/seek/previous/next/speed, camera origin/path AND frustum orientation, growing colour cloud, persistent labelled estimate markers and toggleable individual observation markers. Condition labels include full60-frame cached geometry baseline versus six-frame automatic actual-box appearance/geometry trial. For automatic mode, camera/cloud timeline still uses original60 frame slider but boxes/automatic updates occur only on the six selected source frames. Intermediate frames say 'automatic condition not sampled'; they retain last accepted markers without claiming fresh observations. Counter distinguishes geometry frame count from automatic sampled-frame index. Histories include every observation up to current playback time; no future estimate/gallery leaks into earlier frames. Selecting an ID shows all accepted and unresolved candidate measurements, raw camera/world coordinates, before/after estimate, delta norm/components, representative votes/spread, similarity/cost/abstention and last-seen timestamp. Candidate relationships remain separate from confirmed membership. Distinct IDs of the same class can be shown together; filtering does not delete original records. A proposal browser exposes all457 baseline proposals, including unknown/unresolved and unavailable coordinates.

Display growing cloud via cached prefix boundaries and retain exact original arrays. Label display subsampling (<=500/frame, <=20000total) rather than implying a dense reference surface. No independent dense TUM ground truth exists. Frustum uses calibration/matrix and fixed0.15m display rays. JSON is escaped against script injection; dynamic labels use textContent, never interpolated unsafe HTML. Plotly comes from pinned installed offline package, embedded once; no CDN/network. Reuse JPEG90 preview convention while linking/hash-recording original PNGs. No MP4 required; any optional video export uses H.264 with checked writer success.

New combined-generation sidecar owns condition/input/configuration/pose-revision IDs and membership; Task21 strict reader/persistence validates automatic decisions. Close each private per-condition SQLite database and validate exact ledger membership before completion. No global IdentityStore or active pointer, no schema migration or overwrite. A generation is readable only after verify_run and agreement among camera/cloud/object origins/revisions and hashes. Consumer explicitly names the completed run. Single writer. Original baseline records remain untouched input; new automatic deterministic IDs are in their own condition namespace and must not imply equivalence to pilot IDs.

### Coherent revision control, costs and recovery

Base uses supplied tum_freiburg1_desk_mocap / continuous_capture pose generation. Separate synthetic fixture applies one +1m scene-X rigid revision to EVERY selected camera pose, cloud point and derived object coordinate, preserving RGB/pixel coordinates, colours, source membership and stable IDs. Derived object view groups are recomputed consistently via Task21 revision policy. Publish a distinct generation; reject mixed old/new revisions before readable completion. This checks coordinate bookkeeping only, not improved real camera tracking. Do not display synthetic revision as a recorded corrected trajectory or rerun identity assignment to invent changed IDs. Original camera coordinates remain unchanged.

Measure checked-cache/decode/copy, model load, warmup-inclusive first embed, remaining descriptor extraction/CPU transfer, localisation, each policy, generation validation and rendering separately. Record requested embeddings, warmup accounting, new detector forwards0, peak process memory and CUDA allocated/reserved measurements with scopes, payload bytes/frame/observation counts. Existing predecessor cost is labelled inherited, not charged as new inference. No parameter sweep/retry tuning: one declared trial; changes create new runs and receipts explaining why.

Failure before effects creates0outputs. Failure during copy/descriptor/database/report leaves rejected running/failed new run; earlier completed run remains byte-identical and verifies. Crash after complete preserves immutable generation. Restart uses fresh Run and recomputes only own unfinished derived outputs, never mutates a predecessor or silently accepts partial descriptor cache. Source hashes rechecked immediately before completion. Fresh source handoff requires offline copies of pinned Task17/18/20/21/28 runs, original source members and existing checkpoint; scoped requirements inherit Task20/pilot/shared pinned dependencies including installed Plotly. Missing inputs/runtime fail clearly before inference. No implicit downloads. Run a focused actual offline Edge check once after accepted numeric publication; browser timings are not accuracy measurements.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Accepted Task28 cache | baseline viewer/new proposal extraction | original RGB keys, proposals, camera-to-world metres, world/segment and cloud prefixes | exact copied hashes | experiments/06_object_recognition/pilot/replay.py:573; experiments/06_object_recognition/pilot/replay.py:606 |
| Capture-only checked Task17 source | actual detector support adapter | original640x480 RGB/depth, raw units/5000; evaluator answers absent | immutable checked inputs | experiments/06_object_recognition/shared/manifest.py:261 |
| Actual-box descriptors | Task21 pure policy | opaque key, finite pooled vector or unavailable, own support/config hash | completed new Run only | task_list/open/20_compare_object_appearance_matching_across_viewpoin.md:55 |
| Camera pose/revision plus immutable camera measurements | cloud and object generation | same world/segment/revision, metre scene coordinates | jointly verified generation | experiments/06_object_recognition/shared/pose_revisions.py:67 |
| Complete generation plus closed private stores | offline viewer/reader | strict membership, config/input hashes, explicit condition namespaces | completed Run only | experiments/shared/runs.py:59; experiments/shared/runs.py:229 |

Source of truth is original captured pixels/depth, supplied poses and pinned caches; provisional labels are evaluator-only. One process writes new staging Run and private databases. No method reads open DB or mutable latest pointer. At every transition (copy, descriptor cache, per-observation DB commit, generation write, HTML publication), death leaves0new readable completed generations. Restart fresh, prior accepted files unchanged. No API/database migration; prior readers and Task23 viewer remain unchanged. The accepted Task20/21 pins and actual completed code owners are recorded above; verify their full run receipts before constructing outputs. Constitution draft is not owner-ratified; do not invent new MUST principles.

## Hyperparameters

New display/support/control choices use owner's overnight settings/GPU/tests delegation. They are fixed exploratory settings, not tuned operating thresholds. Inherited Task21 policy values below must match its reviewed completed HYPERPARAMETERS; otherwise revise/re-review rather than silently diverge.

| Name | Value | Source |
|---|---|---|
| source conditions | full60-frame baseline/all457proposals; six selected frames indexes0,9,27,37,42,59;17automatic cup/tv proposals4/13 | inherited experiments/06_object_recognition/experiments/01_detection/cache.py:25; Task18 final receipt |
| sequence/sampling | original1305031454.127701 to1305031472.795640,60cached integer-linspace paired rows; no new sampling | inherited experiments/06_object_recognition/pilot/replay.py:40; experiments/06_object_recognition/pilot/replay.py:73 |
| source pins | Task17/18/28 hashes above; Task20 `f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4`; Task21 `75a1b943ab087d846a87d71289b4e118063fad8bac2010694e1521499046d6f7` | inherited accepted run receipts and manifest verification |
| model/runtime | existingYOLO26x checkpoint9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92; Ultralytics8.4.172/Torch2.11.0+cu128/cuda0FP32/batch1 | inherited experiments/06_object_recognition/pilot/detector.py:12; Task20 fixed plan |
| detection | cached only; imgsz640/conf0.25/NMS0.7/maxdet300/batch1/augmentFalse/rectTrue/halfFalse | inherited experiments/06_object_recognition/pilot/detector.py:14 |
| descriptors | <=17requested actual-box embeddings once each plus installed first-call warmup; second-last pooled layer actual index/type/size recorded; no detector forwards | inherited Task20 adapter plan; confirmed 2026-10-04 owner delegated automatic-support trial |
| crop | detector rectangle floor/ceil/clamp, all-one support;128x128 RGBbilinear/masknearest blackoutside; explicit BGR predictor input, letterbox640 | inherited Task20 crop/preprocessing; confirmed 2026-10-04 actual-box support condition |
| geometry |640x480;fx/fy525,cx319.5,cy239.5;depth/5000,rawzero missing,processed0<z<4m; supplied poses/time tolerance0.02s | inherited experiments/06_object_recognition/pilot/replay.py:85; experiments/06_object_recognition/pilot/replay.py:38 |
| support location | original box valid-point coordinate-wise camera median then supplied camera-to-world transform; unavailable null | inherited experiments/06_object_recognition/pilot/localisation.py:54 |
| policies | combined-last and combined-viewmedian; gallery max cosine over independent representatives; missing appearance unresolved; schema version1 | inherited Task21 reviewed settings and `experiments/06_object_recognition/experiments/04_geometry_identity/association.py:272`; confirmed two bounded automatic comparisons |
| association gates/cost | distance<=0.35m to anchor and estimate,cosine>=0.80; geometry d/0.35 and appearance(1-cos)/2 weighted0.5/0.5 | inherited Task21 fixed plan |
| assignment/ambiguity | maxcardinality then minsumcost; alternate fullcardinality mean gap<=0.05 abstains changed rows; comparison tolerance1e-12 | inherited Task21 fixed plan |
| duplicate/birth | IoU>=0.90 AND worlddistance<=0.02m same-class pairs bothunresolved/0votes; initial-class seeds, later same-class unmatched pending | inherited Task21 fixed plan |
| view/location | fixed earliest group pose;translation<=0.05m AND rotation<=10deg; earliest sole representative; sourceframe<=1vote; median acrossrepresentatives vs last; no appearance/confidence precision weights | inherited Task21 fixed plan |
| spread/retention | min/max/IQR NumPylinear and radial/shift diagnostics; allhistories/allclip frames, noexpiry; pendingmovement no automaticrelocation | inherited Task21 accepted policy, `experiments/06_object_recognition/experiments/04_geometry_identity/locations.py:39` |
| evaluation | sameclass maximumcardinality/maxsumIoU0.5 evaluator-only; no thresholdtuning; provisional cupcomplete/monitorpositivesubset | inherited experiments/06_object_recognition/experiments/01_detection/scoring.py:143; Task18 receipt |
| display | cached<=500points/frame,<=20000total,originalprefixes; frustum0.15m; JPEG90 previews; initialspeed1x with0.5/1/2 controls | inherited experiments/06_object_recognition/pilot/replay.py:35; experiments/shared/visualization.py:67; experiments/06_object_recognition/pilot/replay_viewer.py:13 |
| synthetic revision | +1m scene-X coherent rigid transform, fixture-only separate generation; exact numeric tolerance1e-9 | confirmed 2026-10-04 owner delegated edge controls; no recorded correction claim |
| execution | one serial trial,onewriter,freshRun,0models/downloads/installs/training/detectorreruns; descriptors cached for two policies | confirmed 2026-10-04 owner efficiency/overnight direction |
| runtime dependencies | inherit Task20/pilot/shared scoped pins; Plotly6.6.0, installed version checked before planning; scoped requirements pin plotly==6.6.0 | inherited experiments/06_object_recognition/pilot/replay_viewer.py:111; confirmed 2026-10-04 installed Plotly6.6.0 |

## Verification

Contract files under 05_replay/tests/: test_replay.py, test_inputs.py, test_generation.py and test_viewer_browser.py. Focused changed-module coverage>=80%, Ruff/mypy/programmatic Black and scoped JS syntax checks. Tests use tiny clean repositories outside experiments, no project-tree snapshot fixtures. Meaningful expected-answer controls first or independent test review; Python/code and fresh finished diff reviews before closure.

Exact numeric assertions: copied baseline inputs have identical SHA256,195accepted artifacts still verify;60camera/RGB/cloud-prefix records and457proposals preserved. Exactly6automatic frame records and17actual-box descriptor requests,0new detector forwards; each descriptor's support hash differs from a deliberately substituted oracle support and replacement fails. Changing evaluator identity labels changes0method inputs/descriptors/decisions. Cached camera pose at frame268 is paired with its exact RGB/depth keys. Missing descriptor/depth/pose yields explicit unresolved/null and0locationupdate. Synthetic returned-cup fixture keeps1ID and unchanged gap estimate; two identical-appearance neighbours remain2IDs with geometry or abstain, never silently merge. Use Task21 duplicate/ambiguity/repeated-view controls at adapter boundary; original measurements never overwritten. Three distinct-view x=[0,0.02,0.10]m yield median0.02/last0.10;100same-view repeats add0extra representatives. No real return success asserted until measured.

Synthetic coherent revision shifts all camera origins, cloud XYZ and derived object positions exactly+1m X (atol1e-9), changes0RGB/colour/original-camera coordinates/IDs and preserves cloud prefixes. Mixed revision or source memberships reject before completion. Killed/incomplete Run is unreadable; simulated crash after private-store commit leaves old accepted run byte-identical and0new completed generations. Bad output equal/child/ancestor/Windowsjunction of protected input or previous run causes0mkdir/copy/model/database effects. Unsafe paths/NaN/frame duplicate/origin mismatch/manifesttamper failclosed.

Focused offline actual browser checks: both conditions switch; seek/previous/next/play stop atlast; RGB/camera origin/frustum/cloud cutoff agree with selected source key; orientation changes according to camera matrix; orbit/pan/zoom work. At source268 automatic cup marker is retained if earlier assignment exists, frame359 exposes measured return decision and delta, with no assumed outcome. Intermediate unsampledframes show no new automatic observations. Object selection shows every past accepted/unresolved-candidate observation without future evidence; distinctsameclassIDs toggle independently. Proposal browser accounting is457; brokenartifactlinks0,externalrequests0,pageerrors0. Payload/label hostile text renders as text, never executes. Numeric verification remains independent of displayed rounded values.

Before:0integrated automatic appearance/geometry comparisons, existing60-frame pilot available. Target:1verified integrated viewer with separate60-framebaseline and6-frame/two-policy actual-box automatic trial, completeproposal/frame accounting,0brokenlinks/originmerges/mixedgenerationpublications, explicit outcome for returningcup and everyfailedassociation. No accuracy improvement or truecentre error target. Record costs and missing recording cases honestly. No full Task13,Task25camera correction or newmodels.

## Receipts

| Field | Value |
|---|---|
| Closing commit | None; changes remain uncommitted |
| Files changed | Task22 replay modules/tests/README, object-recognition README, task board and root README; unrelated existing dirty files preserved |
| Test status | Focused Task22 suite 4 passed; Ruff passed. Current publication verifies all 258 artifacts. Prior publication passed offline Edge smoke checks. Final browser relaunch was blocked by Windows `WinError 5` creating the Playwright subprocess. Black reformatted `report.py` and `test_replay.py`, then stalled; no Black check result claimed. |
| Before measurement | Existing 60-frame geometry replay; 0 integrated appearance-and-geometry association trials |
| After measurement | One 60-frame baseline with 457 proposals and 20,000 display points; one six-frame/two-rule automatic trial with 17 proposals. Cup kept one ID over frame104 → absent frame268 → return frame359 in both rules; visible-surface difference 30.8 mm. Four/three monitor matches stayed unresolved. |
| Delta | First integrated recorded replay delivered; no new detector/feature forwards for final viewer publication; no new weights/downloads |
| Decision-gate outcome | Exploratory POC result recorded. Task22 awaits owner review; Task16 remains pending review and unapproved. |

still open because the owner needs to review the replay outcome and the final viewer could not be reopened in a browser after its unsampled-frame overlay fix. Code review found and confirmed that fix; Python review found and confirmed the custom-repository output-path fix. Task21 awaits owner review, which does not approve Task16.
