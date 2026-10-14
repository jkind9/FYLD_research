#!/usr/bin/env bash
# Run Kalibr in Docker (image kalibr:ros1, built from ethz-asl/kalibr's Dockerfile_ros1_20_04) on a bag-creator folder.
#   run_kalibr.sh image                                                    build the image (once)
#   run_kalibr.sh cameras <folder> <target.yaml> <model> <out>             camera intrinsics -> data-camchain.yaml
#   run_kalibr.sh imu <folder> <target.yaml> <camchain.yaml> <imu.yaml> <out> [time offset search, s]
#                                                                          camera-IMU -> data-camchain-imucam.yaml
# Run inside WSL with WSL paths. Each stage appends START and END lines to <out>/kalibr.log, or FAILED when
# Kalibr writes no result (it can give up and still exit 0). KALIBR_OPTIONS adds options to the calibration stage.
set -euo pipefail

SOURCE="${KALIBR_SOURCE:-$HOME/open_vio/src/kalibr}"
stage="$1"
if [ "$stage" = image ]; then
    [ -d "$SOURCE" ] || git clone -q https://github.com/ethz-asl/kalibr.git "$SOURCE"
    git -C "$SOURCE" log -1 --format="kalibr commit %H %cs"
    docker build -q -t kalibr:ros1 -f "$SOURCE/Dockerfile_ros1_20_04" "$SOURCE"
    exit 0
fi

folder="$(realpath "$2")"
case "$stage" in
    cameras) out="$5" ;;
    imu) out="$6" ;;
    *) echo "unknown stage $stage" >&2; exit 2 ;;
esac
out="$(realpath -m "$out")"
mkdir -p "$out"
log="$out/kalibr.log"

run() {  # one shell command in the Kalibr container, input folder at /in (read-only), run folder at /out
    # the image's shell-form ENTRYPOINT ignores arguments, so bash is named as the entrypoint
    docker run --rm --entrypoint /bin/bash -e MPLBACKEND=Agg -v "$folder":/in:ro -v "$out":/out kalibr:ros1 \
        -c "source /catkin_ws/devel/setup.bash && cd /out && $1" >> "$log" 2>&1 \
        || { status=$?; echo "FAILED $(date -Is) exit=$status" >> "$log"; exit 1; }
}

if [ ! -f "$out/data.bag" ]; then
    echo "START $(date -Is) bag" >> "$log"
    run "rosrun kalibr kalibr_bagcreater --folder /in/. --output-bag /out/data.bag"
    echo "END $(date -Is) bag" >> "$log"
fi

cp "$3" "$out/target.yaml"
if [ "$stage" = cameras ]; then
    echo "START $(date -Is) cameras model=$4" >> "$log"
    run "rosrun kalibr kalibr_calibrate_cameras --bag data.bag --target target.yaml --models $4 --topics /cam0/image_raw --dont-show-report ${KALIBR_OPTIONS:-}"
    result="$out/data-camchain.yaml"
else
    cp "$4" "$out/camchain.yaml"
    cp "$5" "$out/imu.yaml"
    padding="${7:-0.03}"
    echo "START $(date -Is) imu time-offset-search=$padding" >> "$log"
    run "rosrun kalibr kalibr_calibrate_imu_camera --bag data.bag --target target.yaml --cam camchain.yaml --imu imu.yaml --timeoffset-padding $padding --dont-show-report ${KALIBR_OPTIONS:-}"
    result="$out/data-camchain-imucam.yaml"
fi
if [ -f "$result" ]; then
    echo "END $(date -Is) $stage $(basename "$result")" >> "$log"
else
    echo "FAILED $(date -Is) $stage: no $(basename "$result")" >> "$log"
    exit 1
fi
