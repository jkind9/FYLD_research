---
id: "100"
title: Build offline Gaussian splat HTML viewer for the Redmi reconstruction
status: done
files:
  - tools/demos/capture_scene.py
  - tools/demos/web/page_splats.js
  - tools/demos/tests/test_capture_scene.py
  - src/live/README.md
  - experiments/01_camera_capture_delivery/README.md
  - README.md
  - learning/05_surface_reconstruction.md
  - research/camera_tracking_and_slam/fragments_and_anchors.md
  - learning/05_dense_surfaces.md
  - research/3d_vision_fundamentals/surface_gaussian_viewing.md
created: 2026-10-15
---
# Build offline Gaussian splat HTML viewer for the Redmi reconstruction

## Goal

View the actual Redmi surface in a standalone interactive HTML with surface-derived Gaussian splats, height colours and source-photo bookmarks.

## Plan

1. Test surface preparation and offline page generation before implementation. 2. Reuse the existing renderer and add the Redmi adapter and controls. 3. Generate the real viewer, test interactions offline, update docs, finish and push.

## Files

- README.md (+2 -0, 419 lines)
- experiments/01_camera_capture_delivery/README.md (+5 -1, 404 lines)
- learning/05_dense_surfaces.md (+12 -0, 114 lines)
- research/3d_vision_fundamentals/surface_gaussian_viewing.md (+11 -0, 11 lines)
- src/live/README.md (+8 -0, 89 lines)
- tools/demos/capture_scene.py (+148 -0, 148 lines)
- tools/demos/web/page_splats.js (+28 -6, 92 lines)

## Checked

- `python -B tools/check.py tools/demos/tests -> 30 passed; Ruff new Python files -> passed; node --check page_splats.js -> passed; real viewer -> 78328 surface-derived Gaussians from 845428 points, 1.58 MB; offline software Chromium -> point/splat switch, fit/top, keyboard orbit/zoom, size and camera/photo bookmarks passed, zero errors or external requests; Gaussian PLY download -> 78328 finite records with unit quaternions, 5326719 bytes; screenshot visually inspected; scratch/cache audit clean; git diff --check clean; two independent read-only reviews -> findings reproduced and fixed`
- cost: 15 min from begin to finish; Claude tokens: none found (Codex sessions are not read)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.73 (was 0)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 0 in 487 words

## Left over

Viewer uses height colours and surface-derived Gaussian primitives. Photographic Gaussian training and independent geometry accuracy are not done. Camera bookmarks use original recorded poses, so later anchor corrections can shift the surface relative to a reference photo. Existing capture metadata gaps and rest/calibration recordings remain as in Task99.
