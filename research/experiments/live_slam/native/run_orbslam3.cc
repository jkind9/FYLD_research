// Feed a frame list to ORB-SLAM3 (monocular) one frame at a time and log the pose it returns for each frame.
// Usage: run_orbslam3 <vocabulary> <settings.yaml> <frames.txt> <output folder>
// Writes live.txt ("time segment x y z qx qy qz qw" camera-to-world, or "time lost"), frame_ms.txt and
// final_euroc.txt (ORB-SLAM3's refined trajectory after the run; time in nanoseconds).
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include <opencv2/imgcodecs.hpp>

#include "System.h"

int main(int argc, char** argv) {
    if (argc != 5) {
        std::cerr << "usage: run_orbslam3 <vocabulary> <settings.yaml> <frames.txt> <output folder>\n";
        return 2;
    }
    std::vector<double> times;
    std::vector<std::string> paths;
    std::ifstream list(argv[3]);
    for (std::string line; std::getline(list, line);) {
        std::istringstream fields(line);
        double t;
        std::string path;
        if (fields >> t >> path) {
            times.push_back(t);
            paths.push_back(path);
        }
    }
    const std::string out = argv[4];
    ORB_SLAM3::System slam(argv[1], argv[2], ORB_SLAM3::System::MONOCULAR, false);
    std::ofstream live(out + "/live.txt"), timing(out + "/frame_ms.txt");
    live << std::fixed << std::setprecision(9);
    int segment = -1;
    bool initializing = true;  // a new map starts when tracking reaches OK from NOT_INITIALIZED
    for (size_t i = 0; i < paths.size(); ++i) {
        cv::Mat image = cv::imread(paths[i], cv::IMREAD_UNCHANGED);
        if (image.empty()) {
            std::cerr << "cannot read " << paths[i] << "\n";
            return 1;
        }
        const auto start = std::chrono::steady_clock::now();
        const Sophus::SE3f camera_from_world = slam.TrackMonocular(image, times[i]);
        const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start).count();
        const int state = slam.GetTrackingState();
        timing << std::setprecision(4) << ms << "\n";
        if (state == ORB_SLAM3::Tracking::NOT_INITIALIZED) initializing = true;
        if (state != ORB_SLAM3::Tracking::OK) {
            live << times[i] << " lost\n";
            continue;
        }
        if (initializing) {
            ++segment;
            initializing = false;
        }
        const Sophus::SE3f world_from_camera = camera_from_world.inverse();
        const Eigen::Vector3f p = world_from_camera.translation();
        const Eigen::Quaternionf q = world_from_camera.unit_quaternion();
        live << times[i] << " " << segment << " " << p.x() << " " << p.y() << " " << p.z() << " "
             << q.x() << " " << q.y() << " " << q.z() << " " << q.w() << "\n";
    }
    slam.Shutdown();
    slam.SaveTrajectoryEuRoC(out + "/final_euroc.txt");
    return 0;
}
