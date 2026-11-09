---
id: "110"
title: Find motions that hide scale in the recorded walks
status: open
priority: MEDIUM
type: experiment
blocked_by: []
blocks: []
verification_test: "experiments/open_vio/tests/test_motion_check.py"
plan_reviewed: null
files:
  - experiments/open_vio/host/**
  - experiments/open_vio/tests/**
  - outputs/**
docs:
  - experiments/open_vio/README.md
  - experiments/01_camera_capture_delivery/field_accuracy.md
baseline_metric:
  source: "SLAM Handbook Table 11.1 (research/camera_tracking_and_slam/slam_handbook.md)"
  field: "share of walk time in motions that hide scale or distance"
  baseline_value: "never measured"
  target: "Share of each walk in turning on the spot and in near-constant velocity, with times, compared with tracking gaps and missing ARCore records"
created: 2026-11-07
last_updated: 2026-11-07
superseded_by: null
---

# Task 110: Find motions that hide scale in the recorded walks

## In plain English

A camera with motion sensors cannot measure distance well during some motions: turning on the spot, or moving at a steady speed. Find how much of each recorded walk was spent in those motions, and whether they line up with the moments tracking struggled. The answer feeds the advice given to people filming a site.

## Verified inputs, 7 November 2026

- Both walks have uncalibrated gyroscope and accelerometer at about 423.5 Hz on the camera's clock (`imu.csv`), and ARCore camera poses on most frames (`frames.jsonl`).
- 14 October walk: 17 frames without ARCore records (sequences 360-363, 600-603, 840-845, 960, 1192-1193). 15 October walk: 43 frames without ARCore records.
- SLAM Handbook Table 11.1 (printed p. 326): constant acceleration hides the overall scale; pure rotation and moving straight towards a point hide the distance to that point.

## Plan

1. Test first on synthetic signals: a pure turn, a straight walk at constant speed and an accelerating walk must each get the right label.
2. Over 1 s windows, label each window:
   - **turning on the spot:** gyroscope rate above the threshold while ARCore's camera speed is below its threshold;
   - **near-constant velocity:** accelerometer magnitude, after removing gravity, below its threshold while the camera is moving;
   - **other.**
3. Report each label's share of walk time, with times, for both walks. Mark the frames without ARCore records and any tracking-state changes on the same timeline (one PNG per walk).
4. If either label is common, propose wording for the capture guide (`field_accuracy.md`): vary the motion, avoid turning on the spot.

## Settings

| name | value | source |
|---|---|---|
| window | 1 s | proposed by Claude 7 November 2026; needs owner confirmation |
| turning threshold | gyroscope rate above 30 degrees/s and camera speed below 0.1 m/s | proposed by Claude; needs owner confirmation |
| constant-velocity threshold | gravity-removed acceleration below 0.2 m/s^2 while camera speed is above 0.2 m/s | proposed by Claude; needs owner confirmation |
| gravity removal | ARCore orientation applied to the accelerometer | proposed by Claude; the IMU is uncalibrated, so the gyroscope bias is ignored at these thresholds |

## Finish when

Both walks are labelled, the shares and timelines are reported, and the capture-guide change is proposed or ruled unnecessary.
