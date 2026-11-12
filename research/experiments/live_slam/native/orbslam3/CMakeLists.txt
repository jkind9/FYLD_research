cmake_minimum_required(VERSION 3.16)
project(run_orbslam3 CXX)
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_BUILD_TYPE Release)

# ORB_SLAM3 is the built source tree (setup_wsl.sh); it has no install step.
set(ORB_SLAM3 "$ENV{HOME}/live_slam/src/ORB_SLAM3" CACHE PATH "ORB-SLAM3 source tree")
find_package(OpenCV 4 REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(Pangolin REQUIRED)

add_executable(run_orbslam3 ../run_orbslam3.cc)
target_include_directories(run_orbslam3 PRIVATE ${ORB_SLAM3} ${ORB_SLAM3}/include ${ORB_SLAM3}/include/CameraModels
    ${ORB_SLAM3}/Thirdparty/Sophus ${EIGEN3_INCLUDE_DIR} ${Pangolin_INCLUDE_DIRS})
target_link_libraries(run_orbslam3 PRIVATE ${ORB_SLAM3}/lib/libORB_SLAM3.so ${OpenCV_LIBS} ${Pangolin_LIBRARIES}
    ${ORB_SLAM3}/Thirdparty/DBoW2/lib/libDBoW2.so ${ORB_SLAM3}/Thirdparty/g2o/lib/libg2o.so -lboost_serialization -lcrypto)
