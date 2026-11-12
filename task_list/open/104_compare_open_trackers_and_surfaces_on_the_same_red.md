---
id: "104"
title: Compare open trackers and surfaces on the same Redmi v2 walk
status: open
priority: HIGH
type: experiment
blocked_by: [52, 103]
blocks: []
verification_test: "research/experiments/open_vio/tests/test_vio.py"
plan_reviewed: null
files:
  - research/experiments/open_vio/**
  - research/experiments/live_slam/**
  - src/live/**
docs:
  - research/experiments/open_vio/README.md
  - research/experiments/live_slam/README.md
  - learning/12_rebuilding_arcore.md
  - task_list/README.md
baseline_metric:
  source: "15 October board review; evidence below"
  field: "Compare open trackers and surfaces on the same Redmi v2 walk"
  baseline_value: "Four VIO systems tested on TUM-VI, visual SLAM tested on TUM/ICL; zero calibrated Redmi comparisons"
  target: "Same-walk CPU tracking and surface comparison with loss, timing, calibration identity and honest reference limits"
created: 2026-10-15
last_updated: 2026-11-12
superseded_by: null
---

# Task 104: Compare open trackers and surfaces on the same Redmi v2 walk

## Amendment, 12 November 2026

Now the decisive test of the product's tracker (owner decision 10, [plan](../../PROJECT_PLAN.md#owner-decisions-in-force)). Blocked by Tasks52 and 103 only; Task102's ARCore diagnosis no longer gates it. Run Basalt first on the recorded v2 walks, whose motion sensors are already recorded, scored against ARCore's path as a comparison, with tracking loss, start-up time and CPU cost. Then rebuild the 15 October room on Basalt's poses through `sitescan`, once DESIGN section 7.15 change 1 lets the session reader take an outside trajectory ([next steps](../../PROJECT_PLAN.md#next-steps)). The two Android projects that track without ARCore report tracking, not depth, as their failure point ([review](../../research/visual_inertial_odometry/depth_without_arcore_2026-11-12.md#whole-chain-templates)).


## In plain English

Run the open camera-and-motion trackers on the same house recording used by the phone's tracker. Compare their paths and the surfaces produced from those paths. Keep the depth method fixed when comparing camera tracking so the two effects are not confused.

## Current evidence

Task91 built Basalt, OKVIS2, Kimera-VIO and OpenVINS runners and tested mono-camera plus IMU on TUM-VI, not the Redmi. Task84 built live image-only stella_vslam and ORB-SLAM3 controls. Task99 provides real phone inputs, but final-frame metadata and handset calibration remain incomplete. Task103 supplies measured Redmi calibration; Task102 supplies checked orientation and the baseline surface controls.

## Plan

1. Reuse `host/recording.py --euroc`, `vio/run.py`, `vio/vio_report.py` and the pinned CPU Docker/WSL runners. Add a synthetic v2-to-runner contract test before any necessary adapter changes. Keep every method's input frame IDs, sensor calibration and timestamps auditable.
2. Run Basalt and OKVIS2 first using the measured Redmi calibration. Retain Kimera's public-dataset failure as a recorded result; a Redmi attempt must use valid initialization and expose divergence. OpenVINS and ORB-SLAM3 remain GPL reference-only, not product selections. No new tracker implementation.
3. Include the existing image-only stella/ORB controls if they help separate IMU calibration from camera tracking. Export tracked points only if a declared surface-scale row needs them; Task84's missing point-export follow-up is conditional here.
4. Compare placed/lost frames, segments, resets, scale, path disagreement and loop/distance checks where independently available. Convert IMU and camera trajectories using the measured transform; do not compare unlike frames. ARCore is another estimate, not independent ground truth.
5. Fuse the same Task102 depth maps/frame subset on each path, then vary depth separately. Keep surface eligibility and coverage explicit. Replay causal live outputs separately from final corrected/offline trajectories; never use future frames in a claimed live row.
6. Measure cold and steady CPU time, end-to-end wait, update gaps, peak memory and failures. Use one background START/END queue and completion notification. Record a method-selection recommendation; Task57's later phone port cannot start on the strength of TUM-VI alone.

## Settings and completion

Inherit Task91 source pins and Task103 measured calibration, with configuration/noise overrides recorded individually. New selections are proposed by Claude, not owner-ruled. CPU only. Independent physical accuracy waits for Tasks75/53, but a same-walk disagreement/performance report may finish without it. Preserve failed runs and the original walk. This task carries Task91's unperformed Redmi comparison; it does not reopen or relabel the completed TUM-VI trial.
