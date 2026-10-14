---
id: "82"
title: Review state-of-the-art SLAM for accuracy and edge latency
status: done
files:
  - research/camera_tracking_and_slam/sota_slam_review_2026-10-14.md
  - research/camera_tracking_and_slam/README.md
created: 2026-10-14
---
# Review state-of-the-art SLAM for accuracy and edge latency

## Goal

Pick live SLAM candidates for recorded-data tests and the phone, from published accuracy (TUM, EuRoC) and measured edge latency

## Plan

1. Search 2025-2026 SLAM and VIO results with accuracy tables. 2. Search on-device and embedded timings. 3. Check licences and CPU/phone feasibility. 4. Write the review with a shortlist and save papers locally. 5. Add a README row.

## Files

- research/camera_tracking_and_slam/README.md (+6 -0, 40 lines)
- research/camera_tracking_and_slam/sota_slam_review_2026-10-14.md (+80 -0, 80 lines)

## Checked

- `no test exists: research note; sources opened and quoted with their caveats`
- cost: 3 min from begin to finish; Claude tokens 2,923,093 (fresh input 30,546, cache read 2,880,936, output 11,611; 1 session)
- new duplicate blocks: 0
- complexity share (functions over 10): n/a (no functions) (was n/a (no functions))
- dead code on added lines: 0
- prose patterns: 1 in 495 words: bold-labels "4 items"

## Left over

Next: live CPU SLAM on recorded data (ORB-SLAM3 reference, stella_vslam); ARCore recorder APK for the Redmi
