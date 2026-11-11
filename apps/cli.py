"""One command for the three ways to run sitescan.

    python -m apps.cli room   --session <recording> --out <new folder>
    python -m apps.cli replay --session <recording> --out <new folder> [--speed 1.0] [--no-objects]
    python -m apps.cli live   --port 8766 --out <new folder> [--no-objects]

room builds the cleaned room offline from every frame with fresh ARCore depth. replay feeds a saved
recording to the live processor at its recorded speed, as the phone would send it. live runs the capture
receiver, saving recordings under <out>/sessions, and processes frames as they arrive until the capture app
ends the session. Frames that arrive during an update are not queued: each update takes the newest frame.
A run folder is never overwritten. CPU only.
"""

import argparse
import json
import sys
from functools import partial
from pathlib import Path

from sitescan import session
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

THREADS = 16


def add_room_options(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """The options every room build shares; trial scripts add their own."""
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--far", type=float, default=RoomSettings.far_m, help="furthest fused depth in metres")
    parser.add_argument("--voxel", type=float, default=RoomSettings.voxel_m, help="fusion voxel in metres")
    parser.add_argument("--threads", type=int, default=THREADS)
    return parser


def room_parser(description: str) -> argparse.ArgumentParser:
    """A parser with the room options, for trial scripts that build rooms their own way."""
    return add_room_options(argparse.ArgumentParser(description=description))


def parse_room_args(parser: argparse.ArgumentParser, argv: list[str] | None) -> argparse.Namespace:
    """Parsed options, refusing an output folder that already exists."""
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"{args.out} already exists; runs are never overwritten")
    return args


def add_live_options(parser: argparse.ArgumentParser) -> None:
    """The options the replay and live verbs share."""
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=THREADS)
    parser.add_argument("--voxel", type=float, default=LiveSettings.voxel_m, help="fusion voxel in metres")
    parser.add_argument("--no-objects", action="store_true", help="skip detection and counting")
    parser.add_argument("--depth-model", type=Path, default=DEPTH_MODEL)
    parser.add_argument("--detector-model", type=Path, default=DETECTOR_MODEL)


def room(args: argparse.Namespace) -> dict:
    """Build, save and summarise the room for the room verb."""
    model = load_model(DEPTH_MODEL, threads=args.threads)
    built = build_room(args.session, model, RoomSettings(args.far, args.voxel, args.piece_cell, args.supported_only))
    save_room(built, args.out)
    return built.summary


def live(args: argparse.Namespace) -> dict:
    """Run the live processor on a replayed or received recording; returns the run summary."""
    import torch

    from sitescan.objects import load_detector

    torch.set_num_threads(args.threads)
    detector = None if args.no_objects else load_detector(args.detector_model)
    processor = LiveProcessor(load_model(args.depth_model, threads=None), detector, LiveSettings(voxel_m=args.voxel))
    args.out.mkdir(parents=True)
    if args.command == "replay":
        feed = partial(session.replay, args.session, processor.add, speed=args.speed, reader=session.read_wire_session)
        source = str(args.session)
    else:
        feed = partial(listen, args.out / "sessions", args.port, processor.add)
        source = f"listen:{args.port}"
    about = {"input": source, "speed": getattr(args, "speed", 1.0), "threads": args.threads, "voxel_m": args.voxel,
             "objects": not args.no_objects}
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
    replay_command = commands.add_parser("replay", help="live processing of a saved recording")
    replay_command.add_argument("--session", type=Path, required=True)
    replay_command.add_argument("--speed", type=float, default=1.0, help="replay speed; 1.0 is the recorded rate")
    add_live_options(replay_command)
    live_command = commands.add_parser("live", help="live processing of frames from the capture app")
    live_command.add_argument("--port", type=int, default=8766)
    add_live_options(live_command)
    args = parse_room_args(parser, argv)
    summary = room(args) if args.command == "room" else live(args)
    print(json.dumps({k: v for k, v in summary.items() if k != "final"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
