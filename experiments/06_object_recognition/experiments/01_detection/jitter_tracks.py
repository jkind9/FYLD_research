"""Task45 Part B: build tracks from per-frame detections and summarise each one."""

import itertools
import math

import numpy as np

from experiments.shared.contracts import Calibration

from .floor import floor
from .jitter import MIN_TRACK, link, pairwise_jitter, project_world, windowed_jitter


def link_frames(
    frames: list[dict], camera: Calibration
) -> tuple[list[list[tuple[int, int]]], list[dict]]:
    """Chain detections across consecutive posed frames into tracks.

    Returns tracks as lists of (frame position, detection index) and every
    unlinked record with its nearest same-class distance and outcome.
    """
    track_of: dict[tuple[int, int], int] = {}
    tracks: list[list[tuple[int, int]]] = []
    unlinked_all = []
    for position, frame in enumerate(frames):
        for index, detection in enumerate(frame["detections"]):
            if detection["world"] is not None and (position, index) not in track_of:
                track_of[(position, index)] = len(tracks)
                tracks.append([(position, index)])
        if (
            position + 1 >= len(frames)
            or frames[position + 1]["sequence"] != frame["sequence"] + 1
        ):
            continue
        after = frames[position + 1]
        previous, keys = [], []
        for index, detection in enumerate(frame["detections"]):
            if detection["world"] is None:
                continue
            u, v = project_world(detection["world"], camera, after["pose"])
            previous.append(
                {
                    "label": detection["label"],
                    "predicted": (u, v),
                    "diagonal": detection["diagonal"],
                }
            )
            keys.append(index)
        current = [
            {**d, "linkable": d["world"] is not None} for d in after["detections"]
        ]
        result = link(previous, current)
        for i, j in result["links"]:
            track = track_of[(position, keys[i])]
            track_of[(position + 1, j)] = track
            tracks[track].append((position + 1, j))
        unlinked_all += [
            {**u, "frame": frame["frame_id"], "detection": keys[u["index"]]}
            for u in result["unlinked"]
        ]
    return tracks, unlinked_all


def _max_angle_deg(anchor: np.ndarray, centres: np.ndarray) -> float:
    rays = centres - anchor
    rays /= np.linalg.norm(rays, axis=1, keepdims=True)
    cosines = np.clip(rays @ rays.T, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosines.min())))


def _size_jitter(items: list[dict]) -> dict:
    metric = np.array(
        [[d["width"] * d["depth"], d["height"] * d["depth"]] for d in items]
    )
    relative = metric / np.median(metric, axis=0) - 1.0
    width, height = np.std(relative, axis=0, ddof=1)
    return {"width_relative_std": float(width), "height_relative_std": float(height)}


def by_position(features: list[dict]) -> dict[int, list[dict]]:
    """Index feature residuals by the frame they start from."""
    index: dict[int, list[dict]] = {}
    for row in features:
        index.setdefault(row["frame_position"], []).append(row)
    return index


def summarise_track(
    track: list[tuple[int, int]],
    frames: list[dict],
    features: dict[int, list[dict]],
    camera: Calibration,
) -> dict:
    items = [
        {
            **frames[p]["detections"][i],
            "index": frames[p]["sequence"],
            "pose": frames[p]["pose"],
        }
        for p, i in track
    ]
    entry = {
        "label": items[0]["label"],
        "length": len(items),
        "first_frame": frames[track[0][0]]["frame_id"],
        "flagged_boxes": sum(
            d["flag_sparse"] or d["flag_spread"] or d["edge"] for d in items
        ),
    }
    if len(items) < MIN_TRACK:
        return {**entry, "status": "too_short"}
    anchor = np.median([d["world"] for d in items], axis=0)
    centres = np.array([d["pose"][:3, 3] for d in items])
    inside = []
    for (position, index), item in zip(track, items, strict=True):
        x1, y1, x2, y2 = item["xyxy"]
        inside += [
            [r["dx"], r["dy"]]
            for r in features.get(position, [])
            if x1 < r["u"] < x2 and y1 < r["v"] < y2
        ]
    return {
        **entry,
        "status": "scored",
        "clean": entry["flagged_boxes"] == 0,
        "windowed": windowed_jitter(items, camera, half_window=5),
        "whole_track": windowed_jitter(items, camera, half_window=None),
        "pairwise": pairwise_jitter(items, camera),
        "size": _size_jitter(items),
        "camera_baseline_m": float(
            max(math.dist(a, b) for a, b in itertools.combinations(centres, 2))
        ),
        "viewing_angle_range_deg": _max_angle_deg(anchor, centres),
        "local_floor": floor(np.array(inside).reshape(-1, 2)),
    }
