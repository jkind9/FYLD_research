"""A scale that may change with distance, fitted robustly to weighted targets."""

import numpy as np
from scipy.stats import theilslopes

from .fit import MIN_POINTS, pixel_rows_cols

LEARNED_LOG_SIGMA = 0.05
MAD_K = 3.0
MAD_TO_SIGMA = 1.4826
MAX_THEIL_SEN = 300
MIN_LOG_SPAN = np.log(1.5)
MAX_SLOPE = 0.5


def target_weights(
    metres: np.ndarray, sigma_m: np.ndarray, learned_log_sigma: float = LEARNED_LOG_SIGMA
):
    """1 / (learned variance + measured variance), both in log depth.

    A triangulated point's relative error is sigma / depth, so far points from short baselines
    count for less. The learned depth's own 5% error keeps one very precise point from dominating.
    """
    return 1.0 / (learned_log_sigma**2 + (sigma_m / metres) ** 2)


def robust_inliers(x: np.ndarray, y: np.ndarray, k: float = MAD_K) -> np.ndarray:
    """Points within k robust standard deviations of a Theil-Sen line through (x, y).

    The line is the median of pairwise slopes, so a third of the points can be wrong without
    moving it; at most 300 evenly spaced points are paired, to bound the cost.
    """
    stride = max(1, int(np.ceil(len(x) / MAX_THEIL_SEN)))
    if np.ptp(x[::stride]) < 1e-9:
        line = np.full(len(x), np.median(y))
    else:
        with np.errstate(invalid="ignore"):  # its unused confidence interval can be undefined
            slope, intercept, _, _ = theilslopes(y[::stride], x[::stride])
        line = intercept + slope * x
    residual = y - line
    spread = np.abs(residual - np.median(residual))
    return spread <= k * MAD_TO_SIGMA * np.median(spread) + 1e-12


def fit_power(
    model: np.ndarray,
    valid: np.ndarray,
    uv: np.ndarray,
    target: np.ndarray,
    weight: np.ndarray | None = None,
    *,
    minimum: int = MIN_POINTS,
) -> np.ndarray | None:
    """Per-pixel scale exp(a) * learned ** b, so the scale can grow or shrink with distance.

    In log space the scale's logarithm is a line in log learned depth. Targets far off a robust
    line are dropped; a weighted least-squares line through the rest gives a and b. The slope b is
    kept within +-0.5, and is 0 (one scale) when the targets span less than a factor of 1.5 in
    learned depth. Pixels nearer or farther than every target take the scale at that end, so the
    fit never extrapolates. None with fewer than `minimum` usable targets.
    """
    height, width = model.shape
    rows, cols = pixel_rows_cols(uv, width, height)
    keep = valid[rows, cols] & (model[rows, cols] > 0) & (target > 0)
    if np.count_nonzero(keep) < minimum:
        return None
    x = np.log(model[rows[keep], cols[keep]])
    y = np.log(target[keep]) - x
    w = np.ones(len(x)) if weight is None else weight[keep]
    inliers = robust_inliers(x, y)
    x, y, w = x[inliers], y[inliers], w[inliers]
    centre = np.average(x, weights=w)
    slope = 0.0
    if np.ptp(x) >= MIN_LOG_SPAN:
        slope = np.average((x - centre) * y, weights=w) / np.average((x - centre) ** 2, weights=w)
        slope = float(np.clip(slope, -MAX_SLOPE, MAX_SLOPE))
    level = np.average(y, weights=w) - slope * centre
    with np.errstate(invalid="ignore", divide="ignore"):
        log_model = np.clip(np.log(model), x.min(), x.max())
    return np.exp(level + slope * np.where(np.isfinite(log_model), log_model, centre))
