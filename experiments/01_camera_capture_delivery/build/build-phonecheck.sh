#!/usr/bin/env bash
# Build the Redmi check app (debug APK) in WSL with the SDK and Gradle already used by build-apk.sh.
# Gradle downloads the ARCore library from Google's Maven repository on the first build.
# Run from the repository root: wsl -d Ubuntu -- bash experiments/01_camera_capture_delivery/build/build-phonecheck.sh
set -euo pipefail

SDK="${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}"
GRADLE="$(ls -d "$HOME"/.gradle/wrapper/dists/gradle-8.14.3-all/*/gradle-8.14.3/bin/gradle | head -1)"
SOURCE="$(cd "$(dirname "$0")/../phonecheck" && pwd)"
# Build on the Linux file system: Gradle on /mnt/c is slow and trips over Windows file locks.
WORK="${PHONECHECK_WORK:-$HOME/phonecheck-build}"

rm -rf "$WORK" && mkdir -p "$WORK" && cp -r "$SOURCE"/. "$WORK"/
echo "sdk.dir=$SDK" > "$WORK/local.properties"
(cd "$WORK" && "$GRADLE" --no-daemon -q --max-workers=2 assembleDebug)

APK="$WORK/app/build/outputs/apk/debug/app-debug.apk"
OUT="$SOURCE/../runs/phonecheck_apk"
mkdir -p "$OUT" && cp "$APK" "$OUT/phonecheck-debug.apk"
sha256sum "$OUT/phonecheck-debug.apk"
echo "BUILD DONE $OUT/phonecheck-debug.apk"
