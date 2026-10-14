# Kimera-VIO (BSD-2): its own dependency image (Dockerfile_20_04: GTSAM 4.2, OpenGV, DBoW2, Kimera-RPGO), then Kimera itself.
FROM kimera-deps
ARG JOBS=8
COPY kimera-vio /root/Kimera-VIO
RUN cmake -S /root/Kimera-VIO -B /root/Kimera-VIO/build -DCMAKE_BUILD_TYPE=Release -DKIMERA_BUILD_TESTS=OFF \
    && cmake --build /root/Kimera-VIO/build -j"${JOBS:-8}"
