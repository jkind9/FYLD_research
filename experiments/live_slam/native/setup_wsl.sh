#!/usr/bin/env bash
# Build stella_vslam (BSD-2) and ORB-SLAM3 (GPLv3, reference only) in WSL Ubuntu 24.04, outside the repository.
# Needs the system libraries from experiments/live_slam/README.md ("Setup"). Run: bash setup_wsl.sh [stella|orbslam3|all]
set -euo pipefail

ROOT="${LIVE_SLAM_ROOT:-$HOME/live_slam}"
JOBS="${JOBS:-$(nproc)}"
WHAT="${1:-all}"
mkdir -p "$ROOT/src" "$ROOT/install"
cd "$ROOT/src"

record() {  # name, folder: write the built commit to BUILD.txt
  echo "$1 $(git -C "$2" rev-parse HEAD) $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$ROOT/BUILD.txt"
}

clone() {  # url, folder, [tag]
  [ -d "$2/.git" ] || git clone --recursive "$1" "$2"
  if [ -n "${3:-}" ]; then git -C "$2" checkout -q "$3"; fi
}

cmake_build() {  # source folder, extra cmake args...
  local src="$1"; shift
  cmake -S "$src" -B "$src/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$ROOT/install" "$@"
  cmake --build "$src/build" -j "$JOBS"
}

build_stella() {
  # g2o tag used by stella_vslam's installation guide
  clone https://github.com/RainerKuemmerle/g2o.git g2o 20230223_git
  cmake_build g2o -DBUILD_SHARED_LIBS=ON -DBUILD_UNITTESTS=OFF -DG2O_USE_CHOLMOD=OFF -DG2O_USE_CSPARSE=ON \
    -DG2O_USE_OPENGL=OFF -DG2O_USE_OPENMP=OFF -DG2O_BUILD_APPS=OFF -DG2O_BUILD_EXAMPLES=OFF -DG2O_BUILD_LINKED_APPS=OFF
  cmake --install g2o/build && record g2o g2o

  clone https://github.com/stella-cv/FBoW.git FBoW
  cmake_build FBoW -DBUILD_TESTS=OFF -DBUILD_UTILS=OFF && cmake --install FBoW/build && record FBoW FBoW

  clone https://github.com/stella-cv/stella_vslam.git stella_vslam
  cmake_build stella_vslam -DCMAKE_PREFIX_PATH="$ROOT/install" && cmake --install stella_vslam/build && record stella_vslam stella_vslam

  mkdir -p "$ROOT/vocab"
  [ -f "$ROOT/vocab/orb_vocab.fbow" ] || curl -sL -o "$ROOT/vocab/orb_vocab.fbow" \
    https://github.com/stella-cv/FBoW_orb_vocab/raw/main/orb_vocab.fbow
}

build_orbslam3() {
  # Pangolin v0.6 uses GLEW (no libepoxy needed); ORB-SLAM3 links it even without a viewer.
  clone https://github.com/stevenlovegrove/Pangolin.git Pangolin v0.6
  # v0.6 predates GCC 13, which no longer pulls in <cstdint> and <limits> indirectly. No window is ever
  # opened, so the X11 backend (which also fails under GCC 13) and the video inputs are left out.
  cmake_build Pangolin -DBUILD_EXAMPLES=OFF -DBUILD_TESTS=OFF -DBUILD_PANGOLIN_PYTHON=OFF -DCMAKE_CXX_STANDARD=14 \
    -DDISPLAY_X11=OFF -DBUILD_PANGOLIN_FFMPEG=OFF -DBUILD_PANGOLIN_V4L=OFF -DBUILD_PANGOLIN_LIBDC1394=OFF \
    -DCMAKE_CXX_FLAGS="-include cstdint -include limits"
  cmake --install Pangolin/build && record Pangolin Pangolin

  clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git ORB_SLAM3
  cd ORB_SLAM3
  # GCC 13 and OpenCV 4.6 need C++14; the upstream files ask for C++11.
  sed -i 's/-std=c++11/-std=c++14/g; s/CXX_STANDARD 11/CXX_STANDARD 14/g' CMakeLists.txt Thirdparty/*/CMakeLists.txt
  sed -i 's/CHECK_CXX_COMPILER_FLAG("-std=c++11" COMPILER_SUPPORTS_CXX11)/set(COMPILER_SUPPORTS_CXX11 TRUE)/' CMakeLists.txt
  for lib in DBoW2 g2o Sophus; do cmake_build "Thirdparty/$lib" -DBUILD_TESTS=OFF; done
  [ -f Vocabulary/ORBvoc.txt ] || tar -xf Vocabulary/ORBvoc.txt.tar.gz -C Vocabulary
  cmake_build . -DCMAKE_PREFIX_PATH="$ROOT/install"
  cd "$ROOT/src" && record ORB_SLAM3 ORB_SLAM3
}

case "$WHAT" in
  stella) build_stella ;;
  orbslam3) build_orbslam3 ;;
  all) build_stella; build_orbslam3 ;;
  *) echo "usage: setup_wsl.sh [stella|orbslam3|all]" >&2; exit 2 ;;
esac
echo "BUILD DONE $WHAT"
