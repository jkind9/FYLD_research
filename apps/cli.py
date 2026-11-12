"""One command for the three ways to run sitescan.

    python -m apps.cli room   --session <recording> --label <what is different>
    python -m apps.cli replay --session <recording> --label <what is different> [--speed 1.0] [--no-objects]
    python -m apps.cli live   --port 8766 --label <what is different> [--no-objects]

room builds the cleaned room offline from every frame with fresh ARCore depth. replay feeds a saved
recording to the live processor at its recorded speed, as the phone would send it. Both can take poses
from an open tracker instead of ARCore (--trajectory, --calibration) and scale learned depth by depth
triangulated along that path (--scale-sources sparse, or dense sparse). live runs the capture
receiver, saving recordings under <run>/sessions, and processes frames as they arrive until the capture app
ends the session. Frames that arrive during an update are not queued: each update takes the newest frame.
--session takes a recording's short name from recordings.toml, or a folder. Each run writes
outputs/<recording>/<verb>/<yyyymmdd-hhmm>_<label>/ with run.json (sitescan.runs); a run folder is never
overwritten. CPU only.
"""

import argparse
import json
import sys
from functools import partial
from pathlib import Path

from sitescan import runs, session
from sitescan.depth import load_model
from sitescan.pipelines import (
    DEPTH_MODEL,
    DETECTOR_MODEL,
    LiveProcessor,
    LiveSettings,
    RoomSettings,
    build_room,
    run_live,
    save_room,
)
from sitescan.pipelines.live import LIVE_SOURCES
from sitescan.pipelines.targets import FITS, SOURCES

THREADS = 16
HEADLINE = ("frames", "surface_points", "map", "scale_min_median_max", "updates", "updates_per_second")  # into run.json


def add_room_options(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """The options every room build shares; trial scripts add their own."""
    parser.add_argument("--session", required=True, help="recording name from recordings.toml, or a folder")
    add_run_options(parser)
    parser.add_argument("--far", type=float, default=RoomSettings.far_m, help="furthest fused depth in metres")
    parser.add_argument("--voxel", type=float, default=RoomSettings.voxel_m, help="fusion voxel in metres")
    parser.add_argument("--threads", type=int, default=THREADS)
    return parser


def add_run_options(parser: argparse.ArgumentParser) -> None:
    """Where the run goes: outputs/<recording>/<tool>/<yyyymmdd-hhmm>_<label>/."""
    parser.add_argument("--label", required=True, help="one to four lowercase words joined by hyphens, e.g. sweep-jump125")
    parser.add_argument("--root", type=Path, default=runs.OUTPUTS, help=argparse.SUPPRESS)


def room_parser(description: str) -> argparse.ArgumentParser:
    """A parser with the room options, for trial scripts that build rooms their own way."""
    return add_room_options(argparse.ArgumentParser(description=description))


def parse_room_args(parser: argparse.ArgumentParser, argv: list[str] | None, tool: str | None = None
                    ) -> argparse.Namespace:
    """Parsed options with `out`, the new run folder, made and recorded; `tool` defaults to the verb."""
    args = parser.parse_args(argv)
    session_given = getattr(args, "session", None)
    if session_given is not None:
        args.session = runs.session_path(session_given)
    recording = runs.recording_name(args.session) if session_given is not None else "live"
    values = {k: v for k, v in vars(args).items() if k not in ("label", "root")}
    typed = runs.typed_options(sys.argv[1:] if argv is None else argv, values)
    try:
        args.out = runs.new_run(recording, tool or args.command, args.label, values, typed, root=args.root)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    return args


def add_pose_options(parser: argparse.ArgumentParser) -> None:
    """Options that pose a saved recording by an open tracker instead of ARCore."""
    parser.add_argument("--trajectory", type=Path, help="tracker poses, `time x y z qx qy qz qw` (TUM format)")
    parser.add_argument("--tracker", default="basalt", help="the tracker's name, recorded as the pose source")
    parser.add_argument("--trajectory-of", choices=("imu", "camera"), default="imu",
                        help="whose pose the file holds: Basalt writes the motion sensors' (imu)")
    parser.add_argument("--trajectory-up", type=float, nargs=3, default=(0.0, 0.0, 1.0), metavar=("X", "Y", "Z"),
                        help="the tracker world's up axis (Basalt: 0 0 1)")
    parser.add_argument("--calibration", type=Path, help="the phone's calibration JSON (camera and imu_from_camera)")


def tracker_poses(parser: argparse.ArgumentParser, args: argparse.Namespace):
    """(trajectory, calibration) from the command line; either may be None."""
    calibration = None if args.calibration is None else session.read_calibration(args.calibration)
    if args.trajectory is None:
        return None, calibration
    if args.trajectory_of == "imu" and calibration is None:
        parser.error("--trajectory-of imu needs --calibration for the camera's place on the phone")
    imu_from_camera = calibration.imu_from_camera if args.trajectory_of == "imu" else None
    trajectory = session.read_tum(args.trajectory, source=args.tracker, up=args.trajectory_up,
                                  imu_from_camera=imu_from_camera)
    return trajectory, calibration


def add_live_options(parser: argparse.ArgumentParser) -> None:
    """The options the replay and live verbs share."""
    add_run_options(parser)
    parser.add_argument("--threads", type=int, default=THREADS)
    parser.add_argument("--voxel", type=float, default=LiveSettings.voxel_m, help="fusion voxel in metres")
    parser.add_argument("--no-objects", action="store_true", help="skip detection and counting")
    parser.add_argument("--depth-model", type=Path, default=DEPTH_MODEL)
    parser.add_argument("--detector-model", type=Path, default=DETECTOR_MODEL)
    parser.add_argument("--scale-sources", nargs="+", choices=SOURCES, default=LIVE_SOURCES,
                        help="scale sources in order of preference")


def room(args: argparse.Namespace, trajectory, calibration) -> dict:
    """Build, save and summarise the room for the room verb."""
    model = load_model(DEPTH_MODEL, threads=args.threads)
    settings = RoomSettings(args.far, args.voxel, args.piece_cell, args.supported_only,
                            tuple(args.scale_sources), args.scale_fit, args.max_scale_jump)
    built = build_room(args.session, model, settings, trajectory, calibration)
    save_room(built, args.out)
    return built.summary


def live(args: argparse.Namespace, trajectory=None, calibration=None) -> dict:
    """Run the live processor on a replayed or received recording; returns the run summary."""
    import torch

    from sitescan.objects import load_detector

    torch.set_num_threads(args.threads)
    detector = None if args.no_objects else load_detector(args.detector_model)
    settings = LiveSettings(voxel_m=args.voxel, scale_sources=tuple(args.scale_sources))
    processor = LiveProcessor(load_model(args.depth_model, threads=None), detector, settings)
    if args.command == "replay":
        reader = partial(session.read_wire_session, trajectory=trajectory, calibration=calibration)
        feed = partial(session.replay, args.session, processor.add, speed=args.speed, reader=reader)
        source = str(args.session)
    else:
        feed = partial(listen, args.out / "sessions", args.port, processor.add)
        source = f"listen:{args.port}"
    about = {"input": source, "speed": getattr(args, "speed", 1.0), "threads": args.threads, "voxel_m": args.voxel,
             "objects": not args.no_objects, "scale_sources": list(args.scale_sources),
             "pose_source": "arcore" if trajectory is None else trajectory.source}
    return run_live(processor, feed, args.out, about)


def listen(folder: Path, port: int, on_frame) -> None:
    """Receive one capture session, passing each saved frame on, until the app ends it."""
    from apps.receiver import capture_receiver

    server = capture_receiver.Receiver(folder, port=port, on_frame=on_frame).start()
    print(f"Listening on port {server.port}: {', '.join(capture_receiver.addresses())}", flush=True)
    server.wait()
    server.close()


def main(argv: list[str] | None = None) -> int:
    """The command line: room, replay or live."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    room_command = add_room_options(commands.add_parser("room", help="offline room from a saved recording"))
    room_command.add_argument("--piece-cell", type=float, help="grid cell in metres for joining surface into pieces "
                              "(default: the fusion voxel)")
    room_command.add_argument("--supported-only", action="store_true",
                              help="fuse only pixels whose grid cell has its own ARCore scale (trial)")
    room_command.add_argument("--scale-sources", nargs="+", choices=SOURCES, default=RoomSettings.scale_sources,
                              help="scale sources in order of preference")
    room_command.add_argument("--scale-fit", choices=FITS, default=RoomSettings.scale_fit)
    room_command.add_argument("--max-scale-jump", type=float, help="skip a frame whose scale is more than this "
                              "factor off the recent frames' median, e.g. 1.25 (trial)")
    add_pose_options(room_command)
    replay_command = commands.add_parser("replay", help="live processing of a saved recording")
    replay_command.add_argument("--session", required=True, help="recording name from recordings.toml, or a folder")
    replay_command.add_argument("--speed", type=float, default=1.0, help="replay speed; 1.0 is the recorded rate")
    add_live_options(replay_command)
    add_pose_options(replay_command)
    live_command = commands.add_parser("live", help="live processing of frames from the capture app")
    live_command.add_argument("--port", type=int, default=8766)
    add_live_options(live_command)
    args = parse_room_args(parser, argv)
    trajectory, calibration = tracker_poses(parser, args) if args.command != "live" else (None, None)
    try:
        summary = room(args, trajectory, calibration) if args.command == "room" else live(args, trajectory, calibration)
    except BaseException:
        runs.finish_run(args.out, status="failed")
        raise
    runs.finish_run(args.out, {k: summary[k] for k in HEADLINE if k in summary})
    print(json.dumps({k: v for k, v in summary.items() if k != "final"}, indent=1))
    print(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
