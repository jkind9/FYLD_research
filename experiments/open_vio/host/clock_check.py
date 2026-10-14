"""Check that a raw recording's camera, gyroscope and accelerometer share one clock, and measure the offset.

    python experiments/open_vio/host/clock_check.py <recording folder>

Writes clock_check.json in the recording folder. The offset is found the way gyroscope-based phone
synchronisation does it (Twist-n-Sync, Faizullin et al. 2021): the angular speed seen by one source is
cross-correlated with the angular speed seen by the other. Here the camera's side is ARCore's camera
rotation, frame to frame. Sign: a motion stamped t on the camera clock is stamped t + offset by the gyroscope.
ARCore states its camera pose at the centre of exposure of the middle image row, while Camera2 stamps the
start of exposure of the first row, so a perfectly aligned phone still shows half the exposure plus half the
readout time; `camera_imu_clock_offset_ms` is what is left after removing that.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

import recording

HYPERPARAMETERS = {
    "offset_search_ms": {"value": 200, "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "offset_grid_ms": {"value": 1, "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "signal": {"value": "angular speed magnitude; gyroscope averaged over one camera frame interval", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "peak_refinement": {"value": "parabola through the best lag and its two neighbours", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "same_clock_base_tolerance_s": {"value": 1, "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "gap": {"value": "an interval over 1.5 times the median interval", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "minimum_tracked_poses": {"value": 60, "source": "proposed by Claude 2026-10-14, not owner-ruled"},
}
MINIMUM_POSES = 60


def angular_speed_from_poses(times_s: np.ndarray, quats: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rotation angle between consecutive poses over their time step, placed at the step's midpoint."""
    rotations = Rotation.from_quat(quats)
    angles = (rotations[:-1].inv() * rotations[1:]).magnitude()
    return (times_s[:-1] + times_s[1:]) / 2, angles / np.diff(times_s)


def estimate_offset(t_ref: np.ndarray, s_ref: np.ndarray, t_imu: np.ndarray, s_imu: np.ndarray, *,
                    max_lag_s: float = 0.2, step_s: float = 0.001) -> tuple[float, float]:
    """Lag L that best matches s_ref(t) with s_imu(t + L), and the correlation there; NaNs when a signal is flat."""
    grid = np.arange(max(t_ref[0], t_imu[0] + max_lag_s), min(t_ref[-1], t_imu[-1] - max_lag_s), step_s)
    a = np.interp(grid, t_ref, s_ref)
    if len(grid) < 3 or a.std() == 0 or np.std(s_imu) == 0:
        return float("nan"), float("nan")
    a = (a - a.mean()) / a.std()
    lags = np.arange(-max_lag_s, max_lag_s + step_s / 2, step_s)
    scores = np.empty(len(lags))
    for i, lag in enumerate(lags):
        b = np.interp(grid + lag, t_imu, s_imu)
        scores[i] = np.mean(a * (b - b.mean()) / b.std()) if b.std() else -1.0
    k = int(np.argmax(scores))
    shift = 0.0
    if 0 < k < len(lags) - 1:
        curvature = scores[k - 1] - 2 * scores[k] + scores[k + 1]
        shift = 0.5 * (scores[k - 1] - scores[k + 1]) / curvature if curvature else 0.0
    return float(lags[k] + shift * step_s), float(scores[k])


def camera_to_gyro_offset(rec: recording.Recording) -> tuple[float, float]:
    """Offset in seconds between ARCore's camera rotation and the gyroscope, and the correlation at the peak."""
    pose_t, _, quats = recording.tracking_poses(rec)
    origin = int(pose_t[0])
    mid, pose_speed = angular_speed_from_poses((pose_t - origin) * 1e-9, quats)
    gyro_t = (rec.gyro_times - origin) * 1e-9
    window = max(1, int(round(np.median(np.diff(mid)) / np.median(np.diff(gyro_t)))))
    gyro_speed = np.convolve(np.linalg.norm(rec.gyro, axis=1), np.ones(window) / window, mode="same")
    return estimate_offset(mid, pose_speed, gyro_t, gyro_speed)


def _stream(times: np.ndarray) -> dict | None:
    if len(times) < 2:
        return None
    steps = np.diff(times) * 1e-6
    return {"samples": int(len(times)), "rate_hz": float((len(times) - 1) / ((times[-1] - times[0]) * 1e-9)),
            "median_interval_ms": float(np.median(steps)), "max_interval_ms": float(steps.max()),
            "gaps_over_1_5x": int(np.sum(steps > 1.5 * np.median(steps)))}


def report(rec: recording.Recording) -> dict:
    start = rec.meta["clock"]["start"]["elapsed_realtime_ns"]
    firsts = recording.first_stamps(rec)
    out = {"recording": str(rec.root), "kind": rec.meta.get("kind"), "camera": _stream(rec.image_times) if rec.is_walk else None,
           "gyro": _stream(rec.gyro_times), "accel": _stream(rec.accel_times),
           "first_stamp_after_start_ms": {k: (v - start) * 1e-6 for k, v in firsts.items()},
           "same_clock_base": all(abs(v - start) <= recording.CLOCK_BASE_TOLERANCE_NS for v in firsts.values()),
           "imu_types": {k: v.get("type") for k, v in rec.meta.get("imu", {}).items()},
           "arcore_frames_matching_an_image": None, "camera_to_gyro_offset_ms": None, "offset_peak_correlation": None,
           "expected_arcore_pose_lag_ms": None, "camera_imu_clock_offset_ms": None}
    if rec.is_walk and rec.camera_rows:
        rows = list(rec.camera_rows.values())
        exposure = float(np.median([r["exposure_ns"] for r in rows])) * 1e-6
        skew = float(np.median([r["rolling_shutter_skew_ns"] for r in rows])) * 1e-6
        focus = [r["focus_distance_dpt"] for r in rows]
        out |= {"exposure_ms_median": exposure, "rolling_shutter_skew_ms_median": skew,
                "focus_distance_dpt_range": [min(focus), max(focus)], "expected_arcore_pose_lag_ms": exposure / 2 + skew / 2,
                "frames_dropped_by_app": rec.meta.get("counts", {}).get("frames_dropped")}
    if rec.is_walk and rec.arcore:
        out["arcore_frames_matching_an_image"] = recording.arcore_match_fraction(rec)
        out["arcore_tracking_fraction"] = float(np.mean([r["tracking"] == "TRACKING" for r in rec.arcore]))
        if len(recording.tracking_poses(rec)[0]) >= MINIMUM_POSES:
            offset, peak = camera_to_gyro_offset(rec)
            out["camera_to_gyro_offset_ms"], out["offset_peak_correlation"] = offset * 1e3, peak
            if out["expected_arcore_pose_lag_ms"] is not None:
                out["camera_imu_clock_offset_ms"] = offset * 1e3 - out["expected_arcore_pose_lag_ms"]
    out["problems"] = recording.problems(rec)
    out["hyperparameters"] = HYPERPARAMETERS
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("recording", type=Path)
    args = parser.parse_args()
    result = report(recording.load(args.recording))
    (args.recording / "clock_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "hyperparameters"}, indent=2))
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
