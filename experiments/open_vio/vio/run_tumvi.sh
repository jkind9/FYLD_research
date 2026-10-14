#!/usr/bin/env bash
# Every system on TUM-VI room1, one at a time (Git Bash on Windows, from the repository root of a checkout).
# REPO points at the checkout that holds data/ and the .venv-sfm environment.
set -u
REPO="${REPO:-$(pwd)}"
DATA="$REPO/data/tumvi/dataset-room1_512_16/dataset-room1_512_16"
CALIB="$REPO/data/tumvi/dataset-calib-imu1_512_16/dataset-calib-imu1_512_16/dso"
for system in "$@"; do
    "$REPO/.venv-sfm/Scripts/python.exe" experiments/open_vio/vio/run.py --system "$system" --dataset "$DATA" \
        --camchain "$CALIB/camchain.yaml" --imu "$CALIB/imu_config.yaml" --camera-rate 20 \
        --reference "$DATA/mav0/mocap0/data.csv" --reference-format euroc --reference-frame imu --profile tumvi \
        --run "$REPO/experiments/open_vio/runs/vio_tumvi_room1/$system" | grep -E '"(system|exit_code|error|ate_rigid_rmse_m|ate_scaled_rmse_m|tracked_fraction|ms_per_frame_whole_run)"'
done
