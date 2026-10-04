"""Extract bounded detector-box features and apply Task21's two fixed policies."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from experiments.shared.contracts import Calibration, Pose

adapter = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.adapter"
)
feature_api = importlib.import_module(
    "experiments.06_object_recognition.experiments.03_appearance.features"
)
detector_api = importlib.import_module(
    "experiments.06_object_recognition.pilot.detector"
)
localisation = importlib.import_module(
    "experiments.06_object_recognition.pilot.localisation"
)
identity = importlib.import_module(
    "experiments.06_object_recognition.experiments.04_geometry_identity.association"
)

POLICIES = ("combined-last", "combined-viewmedian")
CALIBRATION = Calibration(640, 480, 525, 525, 319.5, 239.5, "x-right_y-down_z-forward")


def extract(repo: Path, frames: list[dict], proposal_frames: list[dict]) -> dict:
    """Return actual-box vectors, locations, decisions and GPU cost receipts."""
    checkpoint = repo / "checkpoints/yolo26x.pt"
    if detector_api.sha256(checkpoint) != detector_api.CHECKPOINT_SHA256:
        raise ValueError("Existing YOLO26x checkpoint hash differs")
    extractor = feature_api.FeatureExtractor(checkpoint)
    by_index = {frame["frame_index"]: frame for frame in frames}
    inputs = []
    for cache_frame in proposal_frames:
        index = cache_frame["source_selection_index"]
        frame = by_index[index]
        image = np.asarray(Image.open(frame["rgb_source"]).convert("RGB"))
        if image.shape != (480, 640, 3):
            raise ValueError("Original RGB dimensions differ from frozen calibration")
        depth_raw = np.asarray(Image.open(frame["depth_source"]))
        if depth_raw.dtype != np.uint16 or depth_raw.shape != (480, 640):
            raise ValueError("Original depth must be 640x480 uint16")
        depth = depth_raw.astype(np.float32) / 5000.0
        valid = (depth > 0) & (depth < 4.0)
        pose_record = frame["pose"]
        pose = Pose(
            np.asarray(pose_record["T_world_camera"], dtype=float),
            pose_record["world_id"],
            pose_record["segment_id"],
            "supplied",
        )
        rgb_support = np.full((480, 640), 255, dtype=np.uint8)
        geo_frame = SimpleNamespace(depth=depth, valid=valid, calibration=CALIBRATION)
        rows = []
        for proposal_index, proposal in enumerate(cache_frame["proposals"]):
            if proposal["class_id"] not in (41, 62):
                continue
            key = f"f{frame['frame_id']}-p{proposal_index:03d}"
            crop = adapter.prepare_crop(image, rgb_support, proposal["xyxy"])
            vector = extractor.extract(crop)
            detection = localisation.Detection(
                tuple(proposal["xyxy"]),
                proposal["label"],
                int(proposal["class_id"]),
                float(proposal["confidence"]),
            )
            location = localisation.localise_detection(geo_frame, detection, pose)
            median = location["box_median"]
            rows.append(
                {
                    "observation_id": key,
                    "frame_id": str(frame["frame_id"]),
                    "frame_index": index,
                    "timestamp_s": float(frame["timestamp_s"]),
                    "category": proposal["label"],
                    "class_id": int(proposal["class_id"]),
                    "bbox_xyxy": list(map(float, proposal["xyxy"])),
                    "confidence": float(proposal["confidence"]),
                    "session_id": "tum-freiburg1-desk-continuous-capture",
                    "world_id": pose.world_id,
                    "segment_id": pose.segment_id,
                    "position_world_m": median["world_m"] if median else None,
                    "position_camera_m": median["camera_m"] if median else None,
                    "pose_camera_to_world": pose.matrix.tolist(),
                    "appearance": vector,
                    "geometry": location,
                    "decision_by_condition": {},
                }
            )
        inputs.append(
            {"frame_index": index, "frame_id": frame["frame_id"], "observations": rows}
        )
    feature_receipt = extractor.receipt()
    if feature_receipt["requested_embedding_count"] != 17:
        raise ValueError("Expected exactly 17 unique actual-box embeddings")
    results = {policy: [] for policy in POLICIES}
    for policy in POLICIES:
        tracks = ()
        for frame in inputs:
            tracks, decisions, history = identity.associate_frame(
                frame["observations"], tracks, policy
            )
            decision_by_key = {row["observation_id"]: row for row in decisions}
            for row in frame["observations"]:
                row["decision_by_condition"][policy] = decision_by_key[
                    row["observation_id"]
                ]
            results[policy].append(
                {
                    "frame_index": frame["frame_index"],
                    "frame_id": frame["frame_id"],
                    "observations": decisions,
                    "tracks": [
                        {
                            "object_id": track.object_id,
                            "category": track.category,
                            "position_m": (
                                list(
                                    identity.estimate(
                                        track.location,
                                        (
                                            "last"
                                            if policy.endswith("last")
                                            else "viewmedian"
                                        ),
                                    )
                                )
                                if track.location
                                else None
                            ),
                            "last_frame_id": (
                                track.location.accepted[-1].frame_id
                                if track.location
                                else None
                            ),
                            "observation_ids": (
                                [v.observation_id for v in track.location.accepted]
                                if track.location
                                else []
                            ),
                        }
                        for track in tracks
                    ],
                    "history": history,
                }
            )
    return {
        "frames": inputs,
        "conditions": results,
        "feature_receipt": feature_receipt,
    }
