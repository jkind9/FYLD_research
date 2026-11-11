"""Counted objects that persist between frames and follow ARCore's anchor corrections."""

from collections import Counter
from dataclasses import asdict

import numpy as np

from sitescan.types import Camera

from .detect import Detection
from .match import AMBIGUITY_MARGIN_M, MAX_DISTANCE_M, associate_frame
from .place import box_position


def nearest_same_class(row: dict, tracks: dict[str, dict]) -> float | None:
    """Distance from a placed detection to the closest object of its class; None if either is missing."""
    if row["world_position_m"] is None:
        return None
    distances = [
        np.linalg.norm(np.subtract(row["world_position_m"], track["last_position_m"]))
        for track in tracks.values()
        if track["class_id"] == row["class_id"]
    ]
    return round(float(min(distances)), 3) if distances else None


class Objects:
    """The objects counted so far.

    Each object is stored relative to the anchor of the keyframe it was last seen from, so when ARCore
    corrects that anchor the object moves with the surface fused from the same keyframe.
    """

    def __init__(self, *, max_distance_m: float = MAX_DISTANCE_M, ambiguity_margin_m: float = AMBIGUITY_MARGIN_M):
        self.max_distance_m = max_distance_m
        self.ambiguity_margin_m = ambiguity_margin_m
        self.tracks: dict[str, dict] = {}
        self.anchored: dict[str, tuple[int, np.ndarray]] = {}
        self.next_number = 1

    def update(
        self,
        detections: list[Detection],
        depth: np.ndarray,
        valid: np.ndarray,
        camera: Camera,
        world_from_camera: np.ndarray,
        keyframe: int,
        anchors: dict[int, np.ndarray],
        frame_index: int,
    ) -> list[dict]:
        """Place, match and count one frame's detections; returns one log row per detection."""
        rows = []
        for detection in detections:
            position = box_position(depth, valid, camera, detection.xyxy, world_from_camera)
            rows.append({**asdict(detection), "frame_index": frame_index,
                         "world_position_m": None if position is None else position.tolist()})
        for object_id, (anchor_id, relative) in self.anchored.items():
            anchor = anchors[anchor_id]
            self.tracks[object_id]["last_position_m"] = (anchor[:3, :3] @ relative + anchor[:3, 3]).tolist()
        nearest = [nearest_same_class(row, self.tracks) for row in rows]
        decided, self.tracks, self.next_number = associate_frame(
            rows, self.tracks, self.next_number, self.max_distance_m, self.ambiguity_margin_m
        )
        inverse = np.linalg.inv(anchors[keyframe])
        for row in decided:
            if row["object_id"] is not None:
                position = np.asarray(row["world_position_m"])
                self.anchored[row["object_id"]] = (keyframe, inverse[:3, :3] @ position + inverse[:3, 3])
        return [
            {"label": row["label"], "confidence": round(row["confidence"], 3), "outcome": row["association"],
             "object_id": row["object_id"], "nearest_same_class_m": distance}
            for row, distance in zip(decided, nearest, strict=True)
        ]

    def counts(self) -> dict[str, int]:
        """Objects counted so far, by class label."""
        return dict(Counter(track["label"] for track in self.tracks.values()))
