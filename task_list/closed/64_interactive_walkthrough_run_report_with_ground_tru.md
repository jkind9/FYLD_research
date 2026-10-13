---
id: "64"
title: Interactive walkthrough run report with ground-truth error graphs
status: closed
priority: MED
type: infra
approval_status: owner asked on 2026-10-08 for run outputs like demo_outputs, with error graphs against ground truth
blocked_by: []
blocks: []
verification_test: "tools/demos/tests/test_run_report.py"
plan_reviewed: null
files:
  - src/walkthrough/**
  - tools/demos/**
docs:
  - src/walkthrough/README.md
  - task_list/README.md
baseline_metric:
  source: "outputs/task51_real_runs/cli_xyz60_every2_depth-anything/.../output/visualizations/index.html (owner: 'show nothing useful')"
  field: "interactive report pages per walkthrough run; error graphs against ground truth"
  baseline_value: "0 interactive pages; 0 error graphs; depth scorer unavailable"
  target: "6 offline pages per run (overview, depth, camera path, surface, map, objects); per-frame error graphs for camera position and depth when a reference exists"
created: 2026-10-08
last_updated: 2026-10-08
superseded_by: null
---

# Task 64 — Interactive walkthrough run report with ground-truth error graphs

## In plain English

Each walkthrough run currently ends with a plain list of pictures that is hard to learn anything from. This task gives every run a small set of interactive pages, like the project's existing demo pages: a summary, a frame-by-frame depth view, the camera path in 3D, the 3D points, the top-down map and the detected objects. Where the recording has true answers (the depth sensor and the measured camera path), the pages also graph the error for every frame.

## What

1. `src/walkthrough/validation.py`: a depth scorer. After predictions are sealed it pairs each predicted depth frame with the recording's own sensor depth (through the existing recorded-depth reader, matched by timestamp) and records AbsRel, RMSE, δ1, coverage and distance bands per frame and pooled, using experiment 02's tested scoring.
2. `src/walkthrough/cli.py`: request that depth score whenever the dataset has `depth.txt`; `--report` builds the report after the run.
3. `tools/demos/run_report.py` and `tools/demos/web/page_run.js`: six offline single-file pages per run in `<run>-report/`, built only from the run's saved files and `scores.json`, reusing the demo page frame, styles, data packing and 3D viewer.

## Why

The owner judged the current visual index not useful and asked for output like `demo_outputs`, plus graphs of error against ground truth for camera position, depth and other layers where a reference exists.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Single-file offline page assembly, nav and layout | `tools/demos/page.py` | demo builder | tools/demos/page.py:28-90 |
| Array and image packing for pages | `tools/demos/pack.py` | demo pages | tools/demos/pack.py:14-68 |
| WebGL point and line viewer | `DemoViewer` in `tools/demos/web/viewer.js` | demo pages | tools/demos/web/viewer.js:135-260 |
| Scorer runs after prediction hashes are saved, per component | `validation.score` | `pipeline.run` | src/walkthrough/validation.py:72-114; src/walkthrough/pipeline.py:86-95 |
| Per-frame metric depth scoring with bands, and pooling | `scoring.score_depth`, `evaluate.aggregate_scores` | experiment 02 | experiments/02_stereo_depth/scoring.py:16; experiments/02_stereo_depth/evaluate.py:95 |
| Recorded depth matched to frames by timestamp | `RecordedSensorDepth` | depth layer | src/walkthrough/steps/depth.py:39-79 |
| Tracking score already lists per-frame aligned estimated and reference positions | experiment 03 validation via `_tracking` | scores.json | src/walkthrough/validation.py:44-53 |

### Pages

| Page | Content | Ground-truth graph |
|---|---|---|
| Overview | Layer status, method, frames per second and reason for each layer; controls; end-to-end and processing fps against the 1 fps floor | — |
| Depth | Frame slider: colour, predicted depth, reference depth, absolute error map | AbsRel and RMSE per frame; error by distance band |
| Camera path | 3D view of estimated and reference positions per segment | position error per frame with RMSE line |
| Surface | 3D points in their camera colours, sampled for display, with camera positions | none (no surface reference for TUM) |
| Map | Top-down map images and the measurements table | none (no surveyed reference yet) |
| Objects | Frame slider with box overlays; provisional identities per origin | none (no independent inventory yet) |

Frames are evenly sampled to at most 60 per page; point clouds to at most 150,000 points. Both caps are display-only and labelled on the page.

## Invariants and recovery

invariants n/a: the report reads a finished run and writes a separate folder; the only pipeline change is one more scorer that runs after prediction hashes are saved, so methods still never see references.

## Hyperparameters

hyperparameters n/a: no experiment; display caps (60 frames, 150,000 points, colour ranges 0–4 m depth and 0–0.5 m error) are presentation settings stated on each page.

## Verification

- `tools/demos/tests/test_run_report.py`: builds all six pages from a small synthetic run; each page is offline (no external resource), names its run, and the depth and camera pages carry per-frame error series whose values equal the saved scores.
- `src/walkthrough/tests/`: the depth scorer pairs frames by timestamp, gives AbsRel 0 for identical depth, refuses a frame with no reference within tolerance, and leaves `scores.json` unavailable with a reason when depth did not complete.
- Real check: build the report for the 30-frame Depth Anything and Kinect runs and look at every page.

## Receipts

| field | value |
|---|---|
| closing commit | Uncommitted workspace changes; no commit was requested |
| files changed | New: `tools/demos/run_report.py`, `tools/demos/run_pages.py`, `tools/demos/web/page_run.js`, `tools/demos/tests/test_run_report.py`, `src/walkthrough/tests/test_depth_score.py`. Changed: `src/walkthrough/validation.py` (depth scorer), `src/walkthrough/cli.py` (`score_requests`, depth score when `depth.txt` exists, `--report-pages`); walkthrough README; board |
| test | 4 depth-scorer tests and 2 report tests written first and seen failing; 268 walkthrough, experiment 02/05 and demo tests pass, then 18 report/CLI/scorer tests after the last fixes; Ruff clean; all six pages of a real report open offline in headless Chromium with no errors (`tools.demos.screenshot`) |
| before / after | 0 interactive pages and 0 error graphs per run, depth unscored → 6 pages per run; per-frame camera-position and depth error graphs. Real 30-frame xyz runs (`outputs/task64_report_runs/`): Depth Anything depth AbsRel 0.389, camera RMSE 0.218 m, 0.92 fps processing; Kinect reference AbsRel 0.000, camera RMSE 0.021 m |
| result | Done. Surface, map and object pages show results without error graphs until independent references exist (Task53) |

Notes / caveats / follow-ups:

- `--report` was already the phone capture-report flag, so the new flag is `--report-pages`.
- The offline test uses the demo builder's external-resource check; the only `http://` text on the pages is the SVG namespace name.
