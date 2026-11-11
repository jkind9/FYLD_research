# Dockerfiles for the VIO systems

This folder holds one Dockerfile for each open visual-inertial system that [`../run.py`](../README.md) can run. It belongs to the [open visual-inertial tracking experiment](../../README.md).

| File | What it builds |
|---|---|
| `basalt.Dockerfile` | Basalt (BSD-3) from its published Ubuntu 22.04 binary release, installed into `/root/.local`. |
| `okvis2.Dockerfile` | OKVIS2 (BSD-style) with a plain CMake build: no neural-network sky mask, RealSense or ROS 2. Its EuRoC app opens OpenCV windows, so runs go through `xvfb-run` (a virtual display). |
| `kimera.Dockerfile` | Kimera-VIO (BSD-2) on top of the image `kimera-deps`, which `build_images.sh` first builds from Kimera's own dependency Dockerfile (GTSAM 4.2, OpenGV, DBoW2, Kimera-RPGO). |
| `openvins.Dockerfile` | OpenVINS (GPL-3.0, reference only) in a ROS 1 Noetic catkin workspace, with the `ov_msckf` and `ov_eval` packages. It reads ROS bags. |

The images are tagged `vio-basalt`, `vio-okvis2`, `vio-kimera` and `vio-openvins`. Compile jobs are capped at 8 by default (`JOBS`), because full-core builds of GTSAM and catkin filled the 32 GB WSL machine.

## How to run it

Do not call `docker build` directly: `okvis2`, `kimera` and `openvins` copy a source folder from the build context, which `build_images.sh` sets to `~/open_vio/src`. Build from WSL with Docker, from the repository root:

```text
wsl -- bash experiments/open_vio/vio/build_images.sh <basalt|okvis2|kimera|openvins>
wsl -- bash experiments/open_vio/vio/build_all.sh
```

## Where results are recorded

Build commits and the run results are in the [open_vio README](../../README.md).
