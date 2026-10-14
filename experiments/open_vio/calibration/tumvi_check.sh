#!/usr/bin/env bash
# Verify the calibration pipeline on TUM-VI's calibration recordings (camera, then camera-IMU), from the repository root in WSL.
# Inputs come from prepare.py --mav0 (see README); TUM-VI's own IMU noise file is used, as published.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
RUNS="${RUNS:-$ROOT/experiments/open_vio/runs/kalibr_tumvi}"
DATA="${DATA:-$ROOT/data/tumvi}"
KALIBR="$(dirname "$0")/run_kalibr.sh"
# the robust estimator: without it the incremental camera solve diverged on this recording (14 October 2026)
KALIBR_OPTIONS="--use-blakezisserman" bash "$KALIBR" cameras "$RUNS/cam1/kalibr" "$RUNS/cam1/target.yaml" pinhole-equi "$RUNS/cam1/out"
bash "$KALIBR" imu "$RUNS/imu1/kalibr" "$RUNS/imu1/target.yaml" "$RUNS/cam1/out/data-camchain.yaml" \
    "$DATA/dataset-calib-imu1_512_16/dataset-calib-imu1_512_16/dso/imu_config.yaml" "$RUNS/imu1/out"
