---
id: "43"
title: Build shareable demo visualisations from exported results
status: in_progress
priority: MED
type: infra
blocked_by: []
blocks: []
verification_test: tools/demos/tests/test_demos.py
plan_reviewed: null
files:
  - tools/demos/**
  - demo_outputs/**
  - pytest.ini
docs:
  - demo_outputs/README.md
baseline_metric:
  source: "README.md, 'What has been measured so far'"
  field: self-contained demo pages explaining stages, objects and results
  baseline_value: "0 demo pages; 3 earlier portable viewers of 8–13 MB each, one per experiment"
  target: "6 or more single-file pages that open offline, each under 15 MB, covering every layer with measured results so far"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task 43 — Build shareable demo visualisations from exported results

## In plain English

Make a small set of single-file web pages that explain the project to someone new: how a phone video becomes depth, a camera path, a 3D model and a list of objects, and what results we have so far. Each page works offline and can be emailed or dropped into a chat. The pages reuse data the experiments already saved. One page also shows the 3D scene drawn as Gaussian splats (soft coloured blobs) rather than dots, which looks much more like the real room.

## What

A generator in `tools/demos/` reads existing run outputs and writes self-contained HTML pages to `demo_outputs/`:

| Page | Shows | Source data |
|---|---|---|
| `00_overview.html` | The five layers, results table and links to the other pages | Root README numbers; thumbnails from runs |
| `01_depth_to_3d.html` | One desk frame: colour, depth, missing-depth mask, and the same pixels as 3D points | 05_replay run inputs |
| `02_camera_tracking.html` | Estimated versus motion-capture camera path, with per-frame error | 03 tracking run (30 frames) |
| `03_surface_accuracy.html` | 9-view room point surface coloured by distance to the reference model | 04 surface run (ICL) |
| `04_gaussian_splats.html` | Desk scene drawn as points versus Gaussian splats | 05_replay inputs: 60 colour/depth frames and supplied poses |
| `05_birds_eye_map.html` | Top-down height and colour map with seen/unseen mask and a measuring tool | Fused desk points (illustrative only) |
| `06_objects_in_3d.html` | 18 object identities in 3D, frame timeline with boxes, cup leave-and-return, book weakness | 05_replay observations |

No experiment is rerun. Back-projecting saved depth with saved poses, voxel averaging and splat construction are small CPU steps inside the generator.

## Why

The owner needs shareable material to explain the stages, the object handling and the tested results. Existing portable viewers are one per experiment, 8–13 MB each, and assume project knowledge.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Desk replay saved 60 RGB/depth frames, poses, 457 detections and 18 tracks | 05_replay run | this generator | experiments/06_object_recognition/experiments/05_replay/README.md:19 |
| Replay calibration 525/525/319.5/239.5, depth/5000, valid 0–4 m | replay configuration | back-projection here | experiments/06_object_recognition/experiments/05_replay/runs/20261004T152704.023370Z_84abb8b3b9594dcea8a1e5b2c8aced66/metadata/configuration.json (local run) |
| 30-frame tracking poses and per-frame errors saved | 03 tracking run | page 02 | experiments/03_camera_pose_estimation/README.md:182 |
| ICL per-frame world points, colours and reference distances saved | 04 surface run | page 03 | experiments/04_surface_reconstruction/README.md:119 |
| Existing portable viewer export | experiments/shared/share.py | earlier shareable viewers | experiments/shared/share.py:1 |

The existing shared viewer is a point viewer tied to run folders. Splat rendering, timelines and the overview page need a new small dependency-free WebGL module, kept in `tools/demos/web/`.

Gaussian splats here are built directly from measured depth (one flat Gaussian per fused surface sample, oriented by the local surface normal, sized by the pixel footprint). This is how splat training is usually initialised. No optimisation (training) is run: that needs a GPU, and GPU runs need owner approval. The page states this.

## Hyperparameters

hyperparameters n/a: presentation only; no experiment result is produced. Display settings (voxel size, point budgets, splat sizing, grid cell) are recorded in each page's footer and in `demo_outputs/README.md`.

## Invariants and recovery

invariants n/a: offline generator writing standalone files; no shared state. Re-running regenerates every page from the pinned run IDs.

## Verification

- **Contract test:** `tools/demos/tests/test_demos.py` asserts back-projection reproduces a known 3D point from a synthetic depth pixel, voxel fusion averages duplicates, splat axes are perpendicular to the supplied normal, and every generated page has no external URL in `src`/`href` for scripts, styles or data and stays under the size budget.
- **Before/after:** before, 0 demo pages. After, the page count, sizes and an offline-open check are recorded in Receipts.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

-
