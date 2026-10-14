#!/usr/bin/env bash
# Build one Docker image per visual-inertial system from the sources cloned under ~/open_vio/src (see README).
#   bash build_images.sh basalt|okvis2|kimera|openvins
# Appends START and END (or FAILED) lines to ~/open_vio/build_<system>.log; the source commit is recorded there.
set -uo pipefail
SYSTEM="$1"
SRC="${OPEN_VIO_SRC:-$HOME/open_vio/src}"
DOCKER="$(cd "$(dirname "$0")/docker" && pwd)"
LOG="$HOME/open_vio/build_$SYSTEM.log"
echo "START $(date -Is) $SYSTEM" >> "$LOG"
case "$SYSTEM" in
    basalt) git -C "$SRC/basalt" log -1 --format="basalt source %H %cs (binary release installed)" >> "$LOG"; context="$DOCKER" ;;
    kimera) git -C "$SRC/kimera-vio" log -1 --format="kimera-vio %H %cs" >> "$LOG"
            # Kimera's own dependency Dockerfile compiles with every core; capped so GTSAM fits in memory.
            sed 's/-j$(nproc)/-j8/g' "$SRC/kimera-vio/Dockerfile_20_04" > "$SRC/kimera-vio/Dockerfile_20_04_j8"
            docker build -t kimera-deps -f "$SRC/kimera-vio/Dockerfile_20_04_j8" "$SRC/kimera-vio" >> "$LOG" 2>&1 || { echo "FAILED $(date -Is) kimera-deps" >> "$LOG"; exit 1; }
            context="$SRC" ;;
    okvis2) git -C "$SRC/okvis2" log -1 --format="okvis2 %H %cs" >> "$LOG"; context="$SRC" ;;
    openvins) git -C "$SRC/open_vins" log -1 --format="open_vins %H %cs" >> "$LOG"; context="$SRC" ;;
    *) echo "unknown system $SYSTEM" >&2; exit 2 ;;
esac
if docker build -t "vio-$SYSTEM" -f "$DOCKER/$SYSTEM.Dockerfile" "$context" >> "$LOG" 2>&1; then
    echo "END $(date -Is) $SYSTEM" >> "$LOG"
else
    echo "FAILED $(date -Is) $SYSTEM" >> "$LOG"
    exit 1
fi
