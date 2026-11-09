---
id: "119"
title: Apply the owner's indoor range to the denoising research
status: done
files:
  - research/surface_denoising/README.md
  - research/README.md
  - learning/05_dense_surfaces.md
  - PROJECT_PLAN.md
  - src/live/README.md
created: 2026-11-08
---
# Apply the owner's indoor range to the denoising research

## Goal

Replace the guessed 1-1.5 m reading of low depth scenes with the owner's indoor, under about 10 m, and state what that range means for fusion limits, ARCore reach and clean-up

## Plan

1. Rewrite the scene definition and the close-range section of research/surface_denoising. 2. Distance bands in the first trial. 3. Matching lines in learning chapter 5, research index, PROJECT_PLAN and src/live README. 4. Link check.

## Files

- PROJECT_PLAN.md (+257 -0, 257 lines)
- README.md (+1 -1, 421 lines)
- experiments/01_camera_capture_delivery/README.md (+16 -0, 422 lines)
- experiments/04_surface_reconstruction/README.md (+1 -0, 233 lines)
- learning/00_glossary.md (+2 -0, 51 lines)
- learning/02_depth.md (+2 -0, 70 lines)
- learning/03_camera_tracking_and_slam.md (+9 -0, 104 lines)
- learning/05_dense_surfaces.md (+42 -0, 156 lines)
- learning/10_findings_timeline.md (+7 -0, 57 lines)
- learning/methods_inputs_and_outputs.md (+10 -0, 198 lines)
- research/README.md (+3 -1, 241 lines)
- research/camera_tracking_and_slam/README.md (+3 -0, 45 lines)
- research/camera_tracking_and_slam/slam_handbook.md (+52 -0, 52 lines)
- research/camera_tracking_and_slam/slam_links_review_2026-11-07.md (+27 -0, 27 lines)
- research/dense_surface_fusion/README.md (+92 -0, 92 lines)
- research/dense_surface_fusion/other_systems.md (+27 -0, 27 lines)
- research/surface_denoising/README.md (+167 -0, 167 lines)
- src/live/README.md (+97 -0, 186 lines)
- src/live/depth_check.py (+79 -0, 79 lines)
- src/live/fragments.py (+9 -1, 79 lines)
- src/live/landmark_probe.py (+86 -0, 86 lines)
- src/live/orientation_control.py (+136 -0, 136 lines)
- src/live/room_build.py (+171 -0, 171 lines)
- src/live/tests/test_depth_check.py (+15 -0, 15 lines)
- src/live/tests/test_fragments.py (+9 -0, 63 lines)
- src/live/tests/test_landmark_probe.py (+23 -0, 23 lines)
- src/live/tests/test_orientation_control.py (+73 -0, 73 lines)
- src/live/tests/test_room_build.py (+55 -0, 55 lines)
- tools/demos/capture_scene.py (+95 -17, 226 lines)
- tools/demos/tests/test_capture_scene.py (+68 -0, 185 lines)
- tools/demos/web/page_splats.js (+69 -3, 158 lines)
- tools/demos/web/page_timeline.js (+72 -0, 72 lines)
- tools/demos/web/viewer.js (+21 -5, 463 lines)

## Checked

- `grep for close-range / 1-1.5 m wording in the 5 edited files -> only the owner's quoted phrase remains, now defined; links.py -> 0 missing relative links; floor angles from atan(distance/0.9 m) -> 65.8, 79.8, 84.9 degrees at 2, 5, 10 m`
- cost: 1 min from begin to finish; Claude tokens 3,369,519 (fresh input 29,893, cache read 3,319,318, output 20,308; 2 sessions)
- new duplicate blocks: 0
- complexity share (functions over 10): 0.22 (was 0.1)
- dead code on added lines: not checked (vulture not installed; knip not installed)
- prose patterns: 29 in 8400 words: same-opening "it", same-opening "the", same-opening "the", bold-labels "3 items", bold-labels "5 items"

## Left over

Nothing run on project data. First trial: floaters by depth jump, grazing angle and distance band (0-1, 1-2.5, 2.5-4 m) plus the share of pixels beyond 4 m. Sizing beyond ARCore's 2.5 m reach (Task117 left-over) matters more than clean-up for a 10 m room. No task filed for the trials. Not committed.
