"""Trajectory evaluation; metric RGB-D defaults to rigid SE(3), never hidden scale fitting."""

from itertools import pairwise

import numpy as np
from numpy.typing import NDArray

from .geometry import inverse_transform


def align_trajectory(
    estimated: NDArray, reference: NDArray, with_scale: bool = False
) -> tuple[NDArray, dict]:
    """Least-squares proper rotation/translation, optionally disclosed Sim(3) scale."""
    if (
        estimated.shape != reference.shape
        or estimated.ndim != 2
        or estimated.shape[1] != 3
        or len(estimated) < 3
        or not np.isfinite(estimated).all()
        or not np.isfinite(reference).all()
    ):
        raise ValueError("Need >=3 finite paired trajectory positions")
    a, b = estimated - estimated.mean(axis=0), reference - reference.mean(axis=0)
    u, singular, vt = np.linalg.svd(b.T @ a / len(a))
    signs = np.ones(3)
    signs[-1] = np.sign(np.linalg.det(u @ vt))
    rotation = u @ np.diag(signs) @ vt
    variance = np.mean(np.sum(a * a, axis=1))
    if with_scale and variance < 1e-12:
        raise ValueError("Scale unobservable on stationary trajectory")
    scale = float(np.sum(singular * signs) / variance) if with_scale else 1.0
    translation = reference.mean(axis=0) - scale * rotation @ estimated.mean(axis=0)
    aligned = scale * estimated @ rotation.T + translation
    return aligned, {
        "alignment": "Sim(3)" if with_scale else "SE(3)",
        "scale_factor": scale,
        "rotation": rotation.tolist(),
        "translation_m": translation.tolist(),
        "position_rank": int(np.linalg.matrix_rank(a)),
        "assistance": "ground truth for evaluation alignment only",
    }


def trajectory_metrics(
    estimated: list[NDArray], reference: list[NDArray | None]
) -> dict:
    """ATE after rigid alignment and adjacent accepted-frame translational RPE."""
    pairs = [
        (i, e, r) for i, (e, r) in enumerate(zip(estimated, reference)) if r is not None
    ]
    if len(pairs) < 3:
        return {
            "evaluation_status": "insufficient associated ground truth",
            "gt_pairs": len(pairs),
        }
    aligned, alignment = align_trajectory(
        np.array([e[:3, 3] for _, e, _ in pairs]),
        np.array([r[:3, 3] for _, _, r in pairs]),
    )
    errors = np.linalg.norm(aligned - np.array([r[:3, 3] for _, _, r in pairs]), axis=1)
    rpe = []
    for (i, a, ra), (j, b, rb) in pairwise(pairs):
        if j == i + 1:
            error = inverse_transform(inverse_transform(ra) @ rb) @ (
                inverse_transform(a) @ b
            )
            rpe.append(np.linalg.norm(error[:3, 3]))
    return {
        "evaluation_status": "evaluated",
        "gt_pairs": len(pairs),
        "ate_rmse_m": float(np.sqrt(np.mean(errors**2))),
        "ate_median_m": float(np.median(errors)),
        "ate_max_m": float(errors.max()),
        "rpe_adjacent_translation_rmse_m": (
            float(np.sqrt(np.mean(np.square(rpe)))) if rpe else None
        ),
        "rpe_pairs": len(rpe),
        "rpe_delta": "one accepted input step, not fixed elapsed seconds",
        **alignment,
    }
