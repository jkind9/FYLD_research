#!/usr/bin/env bash
# Run official Marigold V2 inference on the exported TUM colour frames inside WSL,
# recording wall time, process peak memory and whole-GPU memory for each sequence.
#
# Usage (from WSL, repository root on /mnt/c):
#   bash experiments/02_stereo_depth/marigold_wsl_run.sh <input_root> <output_root>
# <input_root> holds one folder of PNGs per sequence (marigold.py export-rgb).
# <output_root> must not exist yet; results are never overwritten.
set -euo pipefail

INPUT_ROOT="$(realpath "$1")"
OUTPUT_ROOT="$2"
MARIGOLD_REPO="${MARIGOLD_REPO:-$HOME/marigold-v2}"
MARIGOLD_PYTHON="${MARIGOLD_PYTHON:-$HOME/.venvs/task54-marigold/bin/python}"
# Every recording folder under the input root (chunked reruns may hold only one).
mapfile -t SEQUENCES < <(find "$INPUT_ROOT" -mindepth 1 -maxdepth 1 -type d -printf '%f
' | sort)
SEED=0  # Task54 frozen setting; native resolution and the default Log-stage2 checkpoint.

if [ -e "$OUTPUT_ROOT" ]; then
  echo "Refusing to reuse existing output root: $OUTPUT_ROOT" >&2
  exit 2
fi
mkdir -p "$OUTPUT_ROOT"
OUTPUT_ROOT="$(realpath "$OUTPUT_ROOT")"

git -C "$MARIGOLD_REPO" rev-parse HEAD > "$OUTPUT_ROOT/marigold_commit.txt"
# The environment may have no pip, so list installed distributions directly.
"$MARIGOLD_PYTHON" -c 'import importlib.metadata as m; print("\n".join(sorted(d.metadata["Name"] + "==" + d.version for d in m.distributions())))' \
  > "$OUTPUT_ROOT/packages.txt"
nvidia-smi --query-gpu=name,driver_version,memory.used,memory.total --format=csv \
  > "$OUTPUT_ROOT/gpu_before.csv"

for sequence in "${SEQUENCES[@]}"; do
  out_dir="$OUTPUT_ROOT/$sequence"
  mkdir -p "$out_dir"
  # Whole-GPU memory once per second; the idle reading is the first row.
  nvidia-smi --query-gpu=timestamp,memory.used --format=csv,noheader,nounits -l 1 \
    > "$out_dir/gpu_memory.csv" &
  monitor_pid=$!
  sleep 2
  started=$(date +%s.%N)
  set +e
  ( cd "$MARIGOLD_REPO" && /usr/bin/time -v -o "$out_dir/time.txt" \
      "$MARIGOLD_PYTHON" scripts/infer.py --modality depth --seed "$SEED" \
      --image_dir "$INPUT_ROOT/$sequence" --output_dir "$out_dir" ) \
    > "$out_dir/infer.log" 2>&1
  status=$?
  set -e
  finished=$(date +%s.%N)
  kill "$monitor_pid" 2>/dev/null || true
  wait "$monitor_pid" 2>/dev/null || true
  printf '{"sequence": "%s", "exit_status": %d, "started_unix_s": %s, "finished_unix_s": %s}\n' \
    "$sequence" "$status" "$started" "$finished" > "$out_dir/run_status.json"
  if [ "$status" -ne 0 ]; then
    echo "Marigold failed on $sequence with status $status; see $out_dir/infer.log" >&2
    exit "$status"
  fi
done
echo "Marigold outputs written under $OUTPUT_ROOT"
