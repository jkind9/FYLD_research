#!/usr/bin/env bash
# Run the JVM tests (encoders against the shared v2 fixture, the phone queue, the sender with resume), then build the
# capture app (debug APK) in WSL with the SDK and Gradle already used by build-apk.sh, and stage it for installing.
# Gradle downloads the ARCore library from Google's Maven repository on the first build.
# Run from the repository root: wsl -d Ubuntu -- bash experiments/01_camera_capture_delivery/build/build-capture.sh
set -euo pipefail

SDK="${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}"
GRADLE="$(ls -d "$HOME"/.gradle/wrapper/dists/gradle-8.14.3-all/*/gradle-8.14.3/bin/gradle | head -1)"
SOURCE="$(cd "$(dirname "$0")/../capture" && pwd)"
# Build on the Linux file system: Gradle on /mnt/c is slow and trips over Windows file locks.
WORK="${CAPTURE_WORK:-$HOME/capture-build}"

rm -rf "$WORK" && mkdir -p "$WORK" && cp -r "$SOURCE"/. "$WORK"/
echo "sdk.dir=$SDK" > "$WORK/local.properties"
(cd "$WORK" && "$GRADLE" --no-daemon -q --max-workers=2 testDebugUnitTest assembleDebug)

APK="$WORK/app/build/outputs/apk/debug/app-debug.apk"
DEPLOY="$(python3 "$SOURCE/../build/deployment.py" "$APK" --aapt "$SDK/build-tools/35.0.0/aapt")"
sha256sum "$DEPLOY"/*.apk
echo "BUILD DONE $DEPLOY"
