# OKVIS2 (BSD-3), plain CMake build without the neural-network sky mask, RealSense or ROS 2.
# Its EuRoC app opens OpenCV windows, so runs go through xvfb-run (a virtual display).
FROM ubuntu:22.04
ARG JOBS=8
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake git ca-certificates \
    libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev libsuitesparse-dev libboost-dev \
    libboost-filesystem-dev libopencv-dev libopenblas-openmp-dev xvfb xauth && rm -rf /var/lib/apt/lists/*
COPY okvis2 /src/okvis2
RUN cmake -S /src/okvis2 -B /src/okvis2/build -DCMAKE_BUILD_TYPE=Release -DUSE_NN=OFF -DBUILD_ROS2=OFF \
    -DHAVE_LIBREALSENSE=OFF && cmake --build /src/okvis2/build -j"${JOBS:-8}"
ENV PATH=/src/okvis2/build:$PATH
