cmake_minimum_required(VERSION 3.16)
project(run_stella CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Release)

# stella_vslam, g2o and FBoW are installed into ~/live_slam/install by setup_wsl.sh.
list(APPEND CMAKE_PREFIX_PATH "$ENV{HOME}/live_slam/install")
find_package(stella_vslam REQUIRED)
find_package(OpenCV 4 REQUIRED)

add_executable(run_stella ../run_stella.cc)
target_link_libraries(run_stella PRIVATE stella_vslam::stella_vslam ${OpenCV_LIBS})
