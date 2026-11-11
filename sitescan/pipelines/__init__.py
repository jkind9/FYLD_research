"""Orchestrators: which stage runs, on which frame, in what order."""

from pathlib import Path

from .live import LiveProcessor, LiveSettings, run_live
from .room import Room, RoomSettings, build_room, save_room

MODELS = Path(__file__).resolve().parents[2] / "models"
DEPTH_MODEL = MODELS / "depth_anything_v2_metric_indoor_small"
DETECTOR_MODEL = MODELS / "yolo26x.pt"

__all__ = [
    "DEPTH_MODEL",
    "DETECTOR_MODEL",
    "LiveProcessor",
    "LiveSettings",
    "Room",
    "RoomSettings",
    "build_room",
    "run_live",
    "save_room",
]
