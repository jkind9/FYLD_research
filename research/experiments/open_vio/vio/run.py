"""Run one open visual-inertial system on a EuRoC/ASL recording in Docker (WSL) and score its trajectory.

    python experiments/open_vio/vio/run.py --system okvis2 --dataset <folder containing mav0> \
        --camchain <Kalibr camchain> --imu <Kalibr imu.yaml> --reference <file> --reference-format euroc|tum \
        --reference-frame imu|camera --profile tumvi|phone --run <run folder>

Images: experiments/open_vio/vio/build_all.sh. One camera (cam0) plus IMU. The configs are written into
<run>/config from each system's own template (cloned under ~/open_vio/src) with this calibration swapped in.
Writes <run>/log.txt (START/END lines and the system's output), the system's trajectory, and scores.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

import configs
import score
import trajectories

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "calibration"))
import kalibr_files  # noqa: E402

TEMPLATES = Path("//wsl.localhost/Ubuntu/home/jkind/open_vio/src")
SYSTEMS = ("basalt", "okvis2", "kimera", "openvins")
MEMORY_LIMIT = "12g"
TIME_LIMIT_S = 1800
HYPERPARAMETERS = {
    "camera_mode": {"value": "monocular (cam0) + IMU", "source": "owner brief 2026-10-14 (phone deployment)"},
    "templates": {"value": "basalt tumvi_512_config / euroc_config; okvis2 tumvi_slam_512 / euroc; openvins tum_vi / euroc_mav; kimera EurocMono",
                  "source": "each project's shipped configs"},
    "loop_closure": {"value": "each system's default", "source": "project defaults"},
    "pacing": {"value": "as fast as processed", "source": "inherited live_slam hyperparameter"},
    "limits": {"value": "12 GB memory and 1800 s per run", "source": "proposed by Claude 2026-10-14 after a run filled WSL memory"},
    "time_match_tolerance_s": {"value": 0.01, "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "time_per_frame": {"value": "wall time of the whole container run divided by camera frames (includes loading)",
                       "source": "proposed by Claude 2026-10-14, not owner-ruled"},
}
PROFILE_TEMPLATES = {
    "tumvi": {"basalt": "tumvi_512_config.json", "okvis2": "okvis2/config/tumvi_slam_512.yaml", "openvins": "tum_vi"},
    "phone": {"basalt": "euroc_config.json", "okvis2": "okvis2/config/euroc.yaml", "openvins": "euroc_mav"},
}


def to_wsl(path: Path) -> str:
    drive, _, rest = Path(path).resolve().as_posix().partition(":")
    return f"/mnt/{drive.lower()}{rest}"


def write_configs(system: str, profile: str, cam: dict, imu: dict, out: Path, *, template_noise: bool, dataset: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    if system == "basalt":
        (out / "basalt_calib.json").write_text(json.dumps(configs.basalt_calib(cam, imu), indent=1), encoding="utf-8")
    elif system == "okvis2":
        template = (TEMPLATES / PROFILE_TEMPLATES[profile]["okvis2"]).read_text(encoding="utf-8")
        (out / "okvis2.yaml").write_bytes(configs.okvis2_yaml(template, cam, imu, template_noise=template_noise).encode("utf-8"))
    elif system == "openvins":
        folder = TEMPLATES / "open_vins/config" / PROFILE_TEMPLATES[profile]["openvins"]
        files = configs.openvins_files((folder / "estimator_config.yaml").read_text(encoding="utf-8"),
                                       (folder / "kalibr_imu_chain.yaml").read_text(encoding="utf-8"), cam, imu)
        for name, text in files.items():
            (out / name).write_bytes(text.encode("utf-8"))
    else:
        # Kimera's EuRoC reader stops without a ground-truth folder; it gets an empty one (no poses), and
        # autoInitialize 1 below makes it start from the IMU instead of the ground-truth pose.
        stub = out / "empty_groundtruth"
        stub.mkdir(exist_ok=True)
        (stub / "sensor.yaml").write_bytes(b"%YAML:1.0\nsensor_type: visual-inertial\ncomment: empty\nT_BS:\n  cols: 4\n  rows: 4\n"
                                           b"  data: [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]\n")
        # The reader also refuses fewer than two rows, so two placeholder rows (identity pose, at rest) are given at
        # the first IMU times; with autoInitialize 1 Kimera reads no state from them.
        imu_times = [line.split(",")[0] for line in (dataset / "mav0/imu0/data.csv").read_text(encoding="utf-8").splitlines()[1:3]]
        rows = "".join(f"{t},0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0\n" for t in imu_times)
        (stub / "data.csv").write_bytes(("#timestamp,p_x,p_y,p_z,q_w,q_x,q_y,q_z,v_x,v_y,v_z,bw_x,bw_y,bw_z,ba_x,ba_y,ba_z\n" + rows).encode())
        folder = TEMPLATES / "kimera-vio/params/EurocMono"
        files = configs.kimera_files((folder / "LeftCameraParams.yaml").read_text(encoding="utf-8"),
                                     (folder / "ImuParams.yaml").read_text(encoding="utf-8"), cam, imu,
                                     camera_rate_hz=cam["rate_hz"], template_noise=template_noise)
        for name, text in files.items():
            (out / name).write_bytes(text.encode("utf-8"))


def command(system: str, profile: str, dataset: str, run: str) -> str:
    """The shell command run inside WSL; outputs land in the run folder."""
    mounts = f"-v {dataset}:/data:ro -v {run}:/run"
    if system == "basalt":
        inner = (f"cd /run && basalt_vio --dataset-path /data --dataset-type euroc --cam-calib /run/config/basalt_calib.json "
                 f"--config-path /root/.local/etc/basalt/{PROFILE_TEMPLATES[profile]['basalt']} --show-gui 0 "
                 f"--save-trajectory tum --use-imu 1")
    elif system == "okvis2":
        # OKVIS2 writes its trajectories next to the images, so it reads a linked copy of the read-only folder;
        # it finds its vocabulary beside the program, so the program is called by its full path.
        inner = ("mkdir -p /work/mav0 && ln -s /data/mav0/* /work/mav0/ && "
                 "xvfb-run -a /src/okvis2/build/okvis_app_synchronous /run/config/okvis2.yaml /work/mav0/ && cp /work/mav0/okvis2-* /run/")
    elif system == "kimera":
        flags = " ".join(f"--flagfile=/params/flags/{f}.flags" for f in
                         ("stereoVIOEuroc", "Mesher", "VioBackend", "RegularVioBackend", "Visualizer3D"))
        inner = ("mkdir -p /work/mav0 && ln -s /data/mav0/cam0 /data/mav0/cam1 /data/mav0/imu0 /work/mav0/ && "
                 "cp -r /run/config/empty_groundtruth /work/mav0/state_groundtruth_estimate0 && "
                 "cp -r /root/Kimera-VIO/params/EurocMono /params && cp /run/config/*.yaml /params/ && "
                 "sed -i 's/^autoInitialize: 0/autoInitialize: 1/' /params/BackendParams.yaml && "
                 f"/root/Kimera-VIO/build/stereoVIOEuroc {flags} --dataset_path=/work --params_folder_path=/params "
                 "--initial_k=0 --final_k=1000000 --use_lcd=false --log_output=true --log_euroc_gt_data=false "
                 "--output_path=/run --visualize=false --logtostderr=1 --v=0")
    else:
        # serial.launch resolves $(find ov_data) even when path_gt is given, so an empty package stands in for it.
        stand_in = ("<package format='2'><name>ov_data</name><version>0.0.0</version><description>none</description>"
                    "<maintainer email='none@none'>none</maintainer><license>none</license></package>")
        inner = (f"mkdir -p /tmp/ov_data && echo \\\"{stand_in}\\\" > /tmp/ov_data/package.xml && "
                 "source /catkin_ws/devel/setup.bash && export ROS_PACKAGE_PATH=/catkin_ws/src:/opt/ros/noetic/share:/tmp/ov_data && "
                 "roslaunch ov_msckf serial.launch "
                 "config_path:=/run/config/estimator_config.yaml bag:=/run/data.bag max_cameras:=1 use_stereo:=false "
                 "dosave:=true path_est:=/run/openvins_traj.txt dotime:=true path_time:=/run/openvins_timing.txt "
                 "path_gt:=/run/no_groundtruth.txt")  # set, or the launch file looks for the ov_data package
    # Capped so one system cannot fill the 32 GB WSL machine (it did on 14 October 2026); a stalled run ends at the limit.
    return f"timeout {TIME_LIMIT_S} docker run --rm --memory {MEMORY_LIMIT} --entrypoint /bin/bash {mounts} vio-{system} -c \"{inner}\""


def bag_command(run: str) -> str:
    """OpenVINS reads a ROS bag: Kalibr's bag creator on a cam0 + imu0.csv folder made by kalibr_files."""
    return (f"docker run --rm --entrypoint /bin/bash -v {run}:/run kalibr:ros1 -c \"source /catkin_ws/devel/setup.bash && "
            f"rosrun kalibr kalibr_bagcreater --folder /run/bag_input/. --output-bag /run/data.bag\"")


def read_estimate(system: str, run: Path) -> list:
    if system == "basalt":
        return trajectories.read_tum(run / "trajectory.txt")
    if system == "openvins":
        return trajectories.read_tum(run / "openvins_traj.txt")
    if system == "kimera":
        return trajectories.read_csv(run / "traj_vio.csv", quaternion="wxyz")
    live = sorted(run.glob("okvis2-*_trajectory.csv"))[0]
    return trajectories.read_csv(live, quaternion="xyzw")


def wsl(command_text: str, log) -> int:
    return subprocess.run(["wsl", "-d", "Ubuntu", "--", "bash", "-c", command_text], stdout=log, stderr=subprocess.STDOUT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--system", choices=SYSTEMS, required=True)
    parser.add_argument("--dataset", type=Path, required=True, help="folder that contains mav0")
    parser.add_argument("--camchain", type=Path, required=True)
    parser.add_argument("--imu", type=Path, required=True)
    parser.add_argument("--camera-rate", type=float, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--reference-format", choices=("euroc", "tum"), required=True)
    parser.add_argument("--reference-frame", choices=("imu", "camera"), required=True)
    parser.add_argument("--profile", choices=tuple(PROFILE_TEMPLATES), required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--template-noise", action="store_true", help="OKVIS2 and Kimera: keep the template's IMU noise values")
    args = parser.parse_args()

    cam = kalibr_files.read_camchain(args.camchain) | {"rate_hz": args.camera_rate}
    imu = yaml.safe_load(args.imu.read_text(encoding="utf-8"))
    args.run.mkdir(parents=True, exist_ok=True)
    write_configs(args.system, args.profile, cam, imu, args.run / "config", template_noise=args.template_noise, dataset=args.dataset)
    frames = len((args.dataset / "mav0" / "cam0" / "data.csv").read_text(encoding="utf-8").splitlines()) - 1
    with open(args.run / "log.txt", "a", encoding="utf-8") as log:
        if args.system == "openvins" and not (args.run / "data.bag").exists():
            kalibr_files.to_kalibr_folder(args.dataset / "mav0", args.run / "bag_input")
            log.write(f"START {time.strftime('%Y-%m-%dT%H:%M:%S')} bag\n")
            log.flush()
            wsl(bag_command(to_wsl(args.run)), log)
        log.write(f"START {time.strftime('%Y-%m-%dT%H:%M:%S')} {args.system}\n")
        log.flush()
        started = time.perf_counter()
        code = wsl(command(args.system, args.profile, to_wsl(args.dataset), to_wsl(args.run)), log)
        seconds = time.perf_counter() - started
        log.write(f"END {time.strftime('%Y-%m-%dT%H:%M:%S')} {args.system} exit={code} seconds={seconds:.1f}\n")
    result = {"system": args.system, "profile": args.profile, "template_noise": args.template_noise, "exit_code": code, "seconds": seconds, "frames": frames,
              "ms_per_frame_whole_run": 1000 * seconds / frames, "hyperparameters": HYPERPARAMETERS}
    try:
        estimate = read_estimate(args.system, args.run)
    except (FileNotFoundError, IndexError) as error:
        result["error"] = f"no trajectory: {error}"
    else:
        if args.reference_frame == "camera":
            estimate = score.to_camera(estimate, cam["T_cam_imu"])
        reference = (trajectories.read_csv(args.reference, quaternion="wxyz") if args.reference_format == "euroc"
                     else trajectories.read_tum(args.reference))
        result |= score.score(estimate, reference, tolerance_s=HYPERPARAMETERS["time_match_tolerance_s"]["value"])
        result["tracked_fraction"] = result["estimates"] / frames
    (args.run / "scores.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "hyperparameters"}, indent=2))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
