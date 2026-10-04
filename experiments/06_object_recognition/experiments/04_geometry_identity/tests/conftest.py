from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def observation_factory():
    def make(
        key: str,
        frame: str,
        timestamp: float,
        x: float,
        *,
        category: str = "tv",
        bbox=(0, 0, 10, 10),
        vector=(1.0, 0.0),
        world="w",
        segment="s",
        camera_x=0.0,
    ):
        pose = np.eye(4)
        pose[0, 3] = camera_x
        return {
            "observation_id": key,
            "frame_id": frame,
            "timestamp_s": timestamp,
            "session_id": "session",
            "category": category,
            "bbox_xyxy": list(bbox),
            "position_camera_m": [x, 0.0, 1.0],
            "position_world_m": [x, 0.0, 1.0] if world and segment else None,
            "world_id": world,
            "segment_id": segment,
            "pose_revision_id": "supplied-base-v1",
            "pose_camera_to_world": pose.tolist(),
            "appearance": list(vector),
            "geometry": {
                "camera_surface_median": [x, 0.0, 1.0],
                "world_surface_median": [x, 0.0, 1.0],
            },
        }

    return make
