---
id: "28"
title: Replay cup revisits with persistent object IDs
status: closed
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: experiments/06_object_recognition/pilot/tests/test_replay.py
plan_reviewed: null
files:
  - experiments/06_object_recognition/pilot/replay.py
  - experiments/06_object_recognition/pilot/replay_viewer.py
  - experiments/06_object_recognition/pilot/tests/test_replay.py
  - experiments/06_object_recognition/pilot/tests/test_replay_viewer.py
docs:
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/pilot/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/06_object_recognition/pilot/README.md
  field: Multi-frame supplied-pose identity replays
  baseline_value: "0 published bounded return replays"
  target: "1 replay with every selected frame accounted for and the returning cup on its original ID"
created: 2026-10-03
last_updated: 2026-10-03
superseded_by: null
---

# Task 28 — Replay cup revisits with persistent object IDs

## In plain English

Replay a short colour-and-depth recording while showing camera movement and the growing 3D point cloud. Track detections with scene positions so the same cup keeps one label when it leaves view and returns. Save every detection and any failed match so the result can be checked later.

## What

Add a bounded GPU replay to the existing YOLO26x pilot. It reuses Task27's detector, depth projection, and supplied camera poses. It shows the return cup and any other detected objects with separate clip-local IDs. This exploratory replay does not create labels or evaluate Task16's wider protocol.

## Why

Task27 connects detections to 3D positions on one frame, so it cannot show whether a returning cup keeps its identity. Task17 found a short visible, out-of-view, return section in TUM Freiburg1 desk. This bounded replay checks that case and records coordinate changes without changing Task13's tracker settings or running its full sequence.

## How

**Reuse evidence** — every "this already exists / lives here / is owned by X" claim gets a
row, with a real `file:line` in the Evidence column. A claim without evidence is a guess:
the plan-shaped failure this table exists to stop is keyword-level grepping passed off as
tracing (a plan once named the wrong file as the owner of a behaviour and no gate noticed).
If nothing comparable exists, write one row saying so and what you searched.

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| YOLO26x local-checkpoint inference and saved detector settings already exist | `YoloDetector` | replay runner | `experiments/06_object_recognition/pilot/detector.py:27` |
| Detection boxes already map to measured RGB-D scene positions | `localise_detection` | replay association | `experiments/06_object_recognition/pilot/localisation.py:49` |
| TUM rows already pair colour/depth timestamps and decode valid metric depth | `load_frame` | replay geometry | `experiments/03_camera_pose_estimation/src/dataset.py:110` |
| Supplied camera poses already decode to camera-to-world matrices | `read_references` | scene-coordinate replay | `experiments/03_camera_pose_estimation/src/evaluation.py:13` |
| Calibrated point projection and timestamp matching already exist | `backproject`, `associate_times` | cloud accumulation and pose matching | `experiments/shared/geometry.py:20`, `experiments/shared/geometry.py:108` |
| Run publication hashes artifacts and rejects incomplete output | `Run` | replay receipts | `experiments/shared/runs.py:137` |

Implement bounded sampling, sequential YOLO inference, scene localisation and global one-to-one per-class spatial assignment in `replay.py`. Keep each object's last valid scene position through missed detections. Mark globally ambiguous or outside-gate matches unresolved; save every proposal and failed association. Build an offline interactive view in `replay_viewer.py` with the RGB recording, frame controls, camera path, accumulated coloured cloud and labelled markers. Add synthetic controls and an offline browser sync check under `pilot/tests/`. Update both object-recognition READMEs and the task board. Reuse the immutable TUM inputs and Task27 checkpoint; do not change Task13 settings or Task16 status.

The replay entry point constructs the verified YOLO26x detector directly. It does not accept an injected adapter that could claim the checkpoint hash without loading those weights.

## Hyperparameters

_Required when this task runs or writes an experiment (type: experiment, or `files:`
touching an experiment directory); otherwise replace this section's body with one line:
`hyperparameters n/a: <reason>`. A tunable value that never gets written down here is a
scientific choice nobody flagged as a choice — how frames are sampled, caps, seeds, model
settings, decode/resolution all shape results silently. Enumerate EVERY one. Only new or
deviating values need a fresh human ruling; inheriting a prior receipt's value unchanged
is a valid source. Run `node ~/.claude/scripts/hyperparam-audit.js <repo root>` first —
any key that diverges from prior use must carry a `deviates ... confirmed <date>` row,
and the ruling comes from the user, not from the model's judgment._

| name | value | source |
|---|---|---|
| Sequence and frames | TUM Freiburg1 desk, RGB timestamp 1305031454.127701 to 1305031472.795640; 60 paired frames sampled by integer linspace from 322 paired rows | confirmed 2026-10-03: Task17 visual inventory found a stationary cup before and after a camera look-away |
| Model/checkpoint/runtime | YOLO26x COCO, existing checkpoint SHA-256 `9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92`, ultralytics 8.4.172 | inherited task_list/closed/27_localise_yolo_cup_detections_in_recorded_rgbd.md |
| Inference | cuda:0, FP32, image size 640, confidence 0.25, IoU 0.7, max 300 boxes, batch 1, augmentation off; retain all returned classes | inherited Task27 receipt and experiments/06_object_recognition/pilot/detector.py:18 |
| RGB/depth and pose time tolerances | 0.02 seconds each | inherited experiments/03_camera_pose_estimation/src/dataset.py:78 and Task27 receipt |
| Camera calibration and depth | 640x480; fx=fy=525, cx=319.5, cy=239.5; raw depth/5000 metres, valid `0 < Z < 4 m` | inherited experiments/03_camera_pose_estimation/src/dataset.py:14 and :126-127 |
| Pose source | Supplied TUM Freiburg1 desk camera-to-world poses; normalized finite quaternion | inherited Task27 receipt |
| Detection position | Existing all-valid-box-pixel median; also retain nearest valid pixel to box centre | inherited Task27 receipt |
| Association | Same-class global one-to-one assignment by maximum match count then minimum total world distance; maximum distance 0.35 m; unresolved if an alternative full-cardinality assignment costs within 0.05 m; later detections beyond the gate do not create new IDs for a previously seen class | confirmed 2026-10-03: owner requested persistent IDs and all same-class detections |
| Cloud/view limits | At most 500 deterministically sampled points per frame and 20,000 accumulated display points; keep every selected frame and its detections | confirmed 2026-10-03: bounded exploratory replay |
| Repeats/warmup | One accepted bounded desk run; one model load; warm-up included in end-to-end timing; no throughput claim | confirmed 2026-10-03: one exploratory result; rejected candidate runs do not count as repeats |

The script itself mirrors this table in a module-level `HYPERPARAMETERS` dict (value +
provenance per entry, written into the result JSON) — the write-time hook blocks an
experiment entry script without one.

## Invariants and recovery

Identity and coordinate state must remain traceable across frames and process restarts.

| Concern | Producer / owner | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Original colour/depth and timestamps | TUM files plus `load_frame`, `experiments/03_camera_pose_estimation/src/dataset.py:110` | replay runner | original RGB pixels; depth metres; frame timestamps | source stays unchanged; hashes saved in run |
| Detector proposals | `YoloDetector.predict`, `experiments/06_object_recognition/pilot/detector.py:54` | association stage | original-image xyxy pixels, class and confidence | proposals saved before depth/poses are read |
| Camera pose | `read_references`, `experiments/03_camera_pose_estimation/src/evaluation.py:13` | projection and association | camera-to-world 4x4, xyz TUM world, metres | exact matched pose and timestamp saved per frame |
| Assigned object state | replay association | viewer and receipts | clip-local ID, class, last observed world position in metres | run JSON preserves assignments; replay rebuilds from saved proposals |
| Accumulated scene | backprojection and supplied pose transform | interactive viewer | sampled RGB points in declared TUM world, metres | display-only sample; input hashes and per-frame detection/localisation records survive |

- **Source of truth:** immutable acquired RGB/depth/pose sources and their hashes; the saved detector proposals and per-frame records are the replay inputs.
- **Process/thread boundary:** JSON proposals, JSON per-frame records, compressed cloud arrays and the self-contained HTML viewer.
- **Failure after each state transition:** a kill during capture, inference, localisation or report leaves the unique run incomplete; `verify_run` rejects it. Rerun into a fresh directory; never patch a completed run.
- **Fresh-deployment path:** install pinned pilot requirements, provide the already acquired verified checkpoint and TUM Freiburg1 desk data, then run the documented bounded replay command. No weight download is performed.
- **Backward compatibility:** existing Task27 detector/mapping runs and Task13 settings remain untouched; Task28 reads 60 sampled desk frames and writes to its separate replay run directory.

For HIGH tasks, the pre-start ritual (each step while the plan is still cheap to change):
1. `node ~/.claude/scripts/task-plan-lint.js <this file>` — deterministic checks (scope,
   invariants/reuse coverage, numeric baseline, vague criteria).
2. `/clarify-task <id>` if anything material is still vague — up to 5 recorded questions.
3. Spawn the `plan-reviewer` agent on this file — fresh context, reads the actual code
   (and the project `CONSTITUTION.md`, if present), hunts for a claim the code contradicts.
4. Record the verdict: `node ~/.claude/task-system/task.js review <id> PASS|FAIL` — the
   stamp lands in `plan_reviewed:` above; `null` means "never reviewed".

## Verification

How we'll know it worked — and it must be a *real* check, not one written to pass.

- **Contract test(s):** `pilot/tests/test_replay.py` asserts the return observation retains the first cup ID after a no-detection gap, its last position stays unchanged during that gap, same-class objects receive distinct IDs, global assignment resolves constrained matches, invalid geometry cannot create an ID, out-of-gate detections do not mint new IDs, and sampling obeys the frame cap. `pilot/tests/test_replay_viewer.py` checks in offline Edge that selected-frame changes update the RGB image, cloud, camera position and object markers together. Walk **Right-BICEP**
  for *what* to test (Right result, Boundary, Inverse, Cross-check, Error) and **CORRECT** for
  *which boundaries* (empty / one / many, ranges, does-it-mutate-its-input). You don't need every
  row — name the ones that apply and why. Full catalogue: the "Testing standard" section of the
  project task README.
- **Rigour — not green-by-construction:** confirm each new test FAILS without the change
  (red-first), or have the tests independently reviewed. A test that passes no matter what the code
  does is worse than none. Scale the depth to how load-bearing the logic is — don't pad a trivial
  change with a dozen tautological tests.
- **Before/after on the real symptom:** before 0 published bounded return replays; after 1 complete 60-frame replay where the cup is detected before and after a 27-frame gap and retains `object-0005`.

The completion gate expects a test to have been added/updated when code changed. If this change
genuinely warrants none (rename, comment, pure-doc), write a one-line `tests n/a: <reason>`
(mirrors `docs n/a:`).

## Receipts

| field | value |
|---|---|
| closing commit | No commit requested |
| files changed | `replay.py`; `replay_viewer.py`; `tests/test_replay.py`; `tests/test_replay_viewer.py`; object-recognition READMEs; Task17/28 records; task board |
| test | 52 pilot tests passed; the two added provenance controls failed before the fix and passed after; direct offline Edge check passed with no network requests or page errors; Ruff and mypy passed |
| before / after | Before: 0 bounded return replays. After: one complete 60-frame desk replay; the cup kept `object-0005` across 27 selected frames without a cup detection, then returned with a 0.0308 m change from its last pre-gap scene position |
| result | YOLO26x detected all 457 proposals across 60 frames on cuda:0 FP32. End-to-end time was 6.68 seconds. The completed run manifest lists 195 files and has SHA-256 `e07af81930e80fe7400c0a0b12b26138c3fea6f7533b1b8137b5186a587267a3`. All proposals, coordinates, identities and 226 unresolved cases are saved. The fresh diff review's checkpoint-provenance finding was fixed by removing the injectable detector parameter; final review is pending. |

Notes / caveats / follow-ups:

- Fresh finished-diff review passed on 3 October 2026. It found that an injected detector could misstate checkpoint provenance. The replay now constructs its detector directly from the hash-verified local checkpoint, and the regression test confirms that the replay entry point has no adapter argument.
- Three cup detections remain unresolved: one was beyond the 0.35 m position gate, and two had no valid depth. The return observation itself matched `object-0005`.

## Task17 independent RGB correction, 3 October 2026

The27sample gap is a YOLO detection miss interval, not a verified continuous visual-absence interval. Original1305031460.891774 still partly shows the cup. Fresh independent RGB-only review verifies no cup pixels at1305031463.059810 (sourceframe268), followed by the same cup at1305031466.095840. Persistent object-0005 and30.8mm return displacement remain unchanged; the exploratory physical look-away/return is present. No accepted run artifact was edited. Task17 supplies separate provisional reference IDs and explicit review limits.
