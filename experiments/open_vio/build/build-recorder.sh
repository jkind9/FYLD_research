#!/usr/bin/env bash
# Build the raw recorder (debug APK) in WSL with the Android SDK and Gradle that the check app uses.
# Run from the repository root: wsl -d Ubuntu -- bash experiments/open_vio/build/build-recorder.sh
set -euo pipefail

SDK="${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}"
GRADLE="$(ls -d "$HOME"/.gradle/wrapper/dists/gradle-8.14.3-all/*/gradle-8.14.3/bin/gradle | head -1)"
SOURCE="$(cd "$(dirname "$0")/../recorder" && pwd)"
WORK="${RECORDER_WORK:-$HOME/rawrecorder-build}"  # Linux file system: Gradle on /mnt/c is slow

rm -rf "$WORK" && mkdir -p "$WORK" && cp -r "$SOURCE"/. "$WORK"/
echo "sdk.dir=$SDK" > "$WORK/local.properties"
(cd "$WORK" && "$GRADLE" --no-daemon -q --max-workers=2 assembleDebug)

OUT="$SOURCE/../runs/apk"
mkdir -p "$OUT" && cp "$WORK/app/build/outputs/apk/debug/app-debug.apk" "$OUT/rawrecorder-debug.apk"
sha256sum "$OUT/rawrecorder-debug.apk"
echo "BUILD DONE $OUT/rawrecorder-debug.apk"
