#!/usr/bin/env bash
# Build all four images one after another (bash build_all.sh): parallel builds of GTSAM and catkin at full core
# count filled the 32 GB WSL machine on 14 October 2026. Prints each image's START/END/FAILED lines when done.
HERE="$(cd "$(dirname "$0")" && pwd)"
for system in basalt okvis2 kimera openvins; do bash "$HERE/build_images.sh" "$system"; done
grep -h -E '^(START|END|FAILED)' "$HOME"/open_vio/build_*.log
