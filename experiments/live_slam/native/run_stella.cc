// Feed a frame list to stella_vslam (monocular) one frame at a time and log the pose it returns for each frame.
// Usage: run_stella <vocabulary.fbow> <config.yaml> <frames.txt> <output folder>
// Writes live.txt ("time segment x y z qx qy qz qw" camera-to-world, or "time lost"), frame_ms.txt and
// final_tum.txt (stella_vslam's refined trajectory after the run).
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include <Eigen/Geometry>
#include <opencv2/imgcodecs.hpp>

#include <stella_vslam/config.h>
#include <stella_vslam/publish/frame_publisher.h>
#include <stella_vslam/system.h>

int main(int argc, char** argv) {
    if (argc != 5) {
        std::cerr << "usage: run_stella <vocabulary.fbow> <config.yaml> <frames.txt> <output folder>\n";
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
    auto config = std::make_shared<stella_vslam::config>(argv[2]);
    stella_vslam::system slam(config, argv[1]);
    slam.startup();
    std::ofstream live(out + "/live.txt"), timing(out + "/frame_ms.txt");
    live << std::fixed << std::setprecision(9);
    int segment = -1;
    bool initializing = true;  // a new map starts when tracking reaches "Tracking" after "Initializing"
    for (size_t i = 0; i < paths.size(); ++i) {
        cv::Mat image = cv::imread(paths[i], cv::IMREAD_COLOR);
        if (image.empty()) {
            std::cerr << "cannot read " << paths[i] << "\n";
            return 1;
        }
        const auto start = std::chrono::steady_clock::now();
        const auto world_from_camera = slam.feed_monocular_frame(image, times[i]);
        const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start).count();
        const std::string state = slam.get_frame_publisher()->get_tracking_state();
        timing << std::setprecision(4) << ms << "\n";
        if (state == "Initializing") initializing = true;
        if (state != "Tracking" || !world_from_camera) {
            live << times[i] << " lost\n";
            continue;
        }
        if (initializing) {
            ++segment;
            initializing = false;
        }
        const Eigen::Matrix4d& m = *world_from_camera;
        const Eigen::Quaterniond q(m.block<3, 3>(0, 0));
        live << times[i] << " " << segment << " " << m(0, 3) << " " << m(1, 3) << " " << m(2, 3) << " "
             << q.x() << " " << q.y() << " " << q.z() << " " << q.w() << "\n";
    }
    while (slam.loop_BA_is_running()) std::this_thread::sleep_for(std::chrono::milliseconds(50));
    slam.shutdown();
    slam.save_frame_trajectory(out + "/final_tum.txt", "TUM");
    return 0;
}
