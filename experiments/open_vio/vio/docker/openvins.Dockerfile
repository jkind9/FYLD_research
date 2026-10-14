# OpenVINS (GPL-3.0, reference only) in a ROS 1 Noetic catkin workspace; reads ROS bags.
FROM osrf/ros:noetic-desktop-full
ARG JOBS=8
RUN apt-get update && apt-get install -y --no-install-recommends python3-catkin-tools libceres-dev \
    && rm -rf /var/lib/apt/lists/*
COPY open_vins /catkin_ws/src/open_vins
RUN . /opt/ros/noetic/setup.sh && cd /catkin_ws && catkin init && catkin config --cmake-args -DCMAKE_BUILD_TYPE=Release \
    && catkin build -j"${JOBS:-8}" ov_msckf
# ov_eval's pose_to_file node writes the trajectory (time, position, Hamilton quaternion) when serial.launch has dosave:=true
RUN . /opt/ros/noetic/setup.sh && cd /catkin_ws && catkin build -j"${JOBS:-8}" ov_eval
