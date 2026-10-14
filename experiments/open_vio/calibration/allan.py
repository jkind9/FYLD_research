"""Motion-sensor noise from a recording at rest, by Allan deviation (IEEE Std 952-1997 method).

    python experiments/open_vio/calibration/allan.py <recording folder>

Writes allan.json in the recording folder. White noise (Kalibr's "noise density") falls on a line of slope -1/2
on a log-log Allan deviation plot and is read at tau = 1 s; bias random walk lies on a line of slope +1/2 and is
read at tau = 3 s (Kalibr wiki, "IMU Noise Model"). A recording too short to show the +1/2 line gives no
random walk: the Kalibr wiki and TUM-VI used hours at rest.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
import recording  # noqa: E402

HYPERPARAMETERS = {
    "cluster_times": {"value": "60 log-spaced cluster sizes from one sample to a tenth of the recording", "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "estimator": {"value": "overlapping Allan deviation", "source": "IEEE Std 952-1997"},
    "slope_tolerance": {"value": 0.15, "source": "proposed by Claude 2026-10-14, not owner-ruled"},
    "read_points": {"value": "noise density at tau = 1 s on the slope -1/2 line; random walk at tau = 3 s on the slope +1/2 line", "source": "Kalibr wiki IMU Noise Model"},
    "axes": {"value": "mean of the three axes", "source": "proposed by Claude 2026-10-14, not owner-ruled; Kalibr takes one value per sensor"},
}
SLOPE_TOLERANCE = 0.15


def allan_deviation(rate: np.ndarray, dt: float, points: int = 60) -> tuple[np.ndarray, np.ndarray]:
    """Overlapping Allan deviation of a rate signal sampled every dt seconds, at log-spaced cluster times."""
    angle = np.concatenate([[0.0], np.cumsum(rate) * dt])
    n = len(rate)
    sizes = np.unique(np.logspace(0, np.log10(max(n // 10, 1)), points).astype(int))
    deviation = []
    for m in sizes:
        d = angle[2 * m:] - 2 * angle[m:-m] + angle[:-2 * m]
        deviation.append(np.sqrt(np.sum(d ** 2) / (2 * (m * dt) ** 2 * len(d))))
    return sizes * dt, np.array(deviation)


def _read_line(taus: np.ndarray, deviation: np.ndarray, slope: float, tau_read: float) -> float | None:
    """Value at tau_read of the line of the given slope through the points whose local slope matches it."""
    local = np.gradient(np.log(deviation), np.log(taus))
    keep = np.abs(local - slope) < SLOPE_TOLERANCE
    if keep.sum() < 3:
        return None
    intercept = np.mean(np.log(deviation[keep]) - slope * np.log(taus[keep]))
    return float(np.exp(intercept + slope * np.log(tau_read)))


def fit_noise(taus: np.ndarray, deviation: np.ndarray) -> tuple[float | None, float | None]:
    """(noise density, random walk) in continuous-time units; None where the plot has no such line."""
    return _read_line(taus, deviation, -0.5, 1.0), _read_line(taus, deviation, 0.5, 3.0)


def imu_noise(rec: recording.Recording) -> dict:
    out = {}
    for name, times, values in (("gyro", rec.gyro_times, rec.gyro), ("accel", rec.accel_times, rec.accel)):
        dt = float(np.median(np.diff(times))) * 1e-9
        axes = [fit_noise(*allan_deviation(values[:, k] - values[:, k].mean(), dt)) for k in range(3)]
        densities = [a for a, _ in axes if a is not None]
        walks = [b for _, b in axes if b is not None]
        out[name] = {"rate_hz": 1 / dt, "seconds": float((times[-1] - times[0]) * 1e-9),
                     "noise_density": float(np.mean(densities)) if densities else None,
                     "random_walk": float(np.mean(walks)) if len(walks) == 3 else None,
                     "per_axis": [{"noise_density": a, "random_walk": b} for a, b in axes]}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("recording", type=Path)
    args = parser.parse_args()
    result = imu_noise(recording.load(args.recording)) | {"hyperparameters": HYPERPARAMETERS}
    (args.recording / "allan.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "hyperparameters"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
