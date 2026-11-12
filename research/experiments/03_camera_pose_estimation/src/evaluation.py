"""References are loaded only after estimation; fixed-scale segment alignment."""

from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from experiments.shared.geometry import associate_times, pose_matrix, validate_transform

from .tracking import Record


def read_references(path: Path) -> list[tuple[float, np.ndarray]]:
    references: list[tuple[float, np.ndarray]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        values = np.array([float(v) for v in line.split()])
        if values.shape != (8,) or not np.isfinite(values).all():
            raise ValueError("Reference rows require eight finite values")
        if references and values[0] <= references[-1][0]:
            raise ValueError("Reference timestamps must increase")
        quaternion = values[4:]
        norm = np.linalg.norm(quaternion)
        if not np.isfinite(norm) or norm == 0:
            raise ValueError("Reference quaternion must have finite nonzero length")
        # Publisher decimal rounding does not preserve an exactly unit quaternion.
        references.append(
            (float(values[0]), pose_matrix(values[1:4], quaternion / norm))
        )
    if not references:
        raise ValueError("No reference poses")
    return references


MIN_SPREAD_M = 1e-9
RPE_WINDOW_S = 1.0
RPE_ACCEPT_S = (0.9, 1.1)


def _rmse(values: list[float]) -> float | None:
    return float(np.sqrt(np.mean(np.square(values)))) if values else None


def _best_fit(estimated: np.ndarray, reference: np.ndarray, with_size: bool) -> tuple[np.ndarray, float] | None:
    """Umeyama least-squares alignment of estimated to reference positions; errors and size."""
    if len(estimated) < 3:
        return None
    mean_e, mean_r = estimated.mean(axis=0), reference.mean(axis=0)
    centred_e, centred_r = estimated - mean_e, reference - mean_r
    # A path along one line leaves the rotation about that line undetermined.
    if np.linalg.svd(centred_r, compute_uv=False)[1] <= MIN_SPREAD_M:
        return None
    variance_e = float(np.mean(np.sum(centred_e**2, axis=1)))
    if variance_e <= 0:
        return None
    u, d, vt = np.linalg.svd(centred_r.T @ centred_e / len(estimated))
    sign = np.diag([1.0, 1.0, np.sign(np.linalg.det(u) * np.linalg.det(vt))])
    rotation = u @ sign @ vt
    size = float(np.trace(np.diag(d) @ sign) / variance_e) if with_size else 1.0
    aligned = size * estimated @ rotation.T + (mean_r - size * rotation @ mean_e)
    return np.linalg.norm(aligned - reference, axis=1), size


def _relative_one_second(times: np.ndarray, estimated: list[np.ndarray], reference: list[np.ndarray]) -> tuple[list[float], list[float]]:
    """Motion error over the frame nearest 1 s later (TUM evaluate_rpe.py, delta 1 s)."""
    translations, rotations = [], []
    for i, start in enumerate(times):
        j = int(np.argmin(np.abs(times - (start + RPE_WINDOW_S))))
        if not RPE_ACCEPT_S[0] <= times[j] - start <= RPE_ACCEPT_S[1]:
            continue
        delta_est = np.linalg.inv(estimated[i]) @ estimated[j]
        delta_ref = np.linalg.inv(reference[i]) @ reference[j]
        residual = np.linalg.inv(delta_ref) @ delta_est
        translations.append(float(np.linalg.norm(residual[:3, 3])))
        rotations.append(float(Rotation.from_matrix(residual[:3, :3]).magnitude()))
    return translations, rotations


def _matrix(record: Record) -> np.ndarray:
    if record.pose is None:
        raise ValueError("Scored observation requires an estimated pose")
    return record.pose.matrix


def evaluate(
    records: list[Record],
    references: list[tuple[float, np.ndarray]],
    tolerance: float = 0.02,
) -> dict:
    for _, matrix in references:
        validate_transform(matrix)
    matches = associate_times(
        [r.timestamp_s for r in records], [r[0] for r in references], tolerance
    )
    lookup = {a: references[b][1] for a, b in matches}
    segments: dict[str, list[int]] = {}
    for i, record in enumerate(records):
        if record.pose is not None:
            segments.setdefault(record.pose.segment_id, []).append(i)
    positions, translations, rotations, details, all_errors = [], [], [], [], []
    rigid_all, scaled_all, sizes, rpe_t_all, rpe_r_all = [], [], [], [], []
    for segment, indices in segments.items():
        matched = [i for i in indices if i in lookup]
        successful = [i for i in matched if records[i].status == "tracked"]
        errors, edge_t, edge_r = [], [], []
        # A lone reference pose is consumed by alignment, leaving no motion check.
        if successful and len(matched) >= 2:
            first = matched[0]
            alignment = lookup[first] @ np.linalg.inv(_matrix(records[first]))
            for i in matched:
                aligned = alignment @ _matrix(records[i])
                error = float(np.linalg.norm(aligned[:3, 3] - lookup[i][:3, 3]))
                errors.append(error)
                all_errors.append(
                    {
                        "frame_id": records[i].frame_id,
                        "position_error_m": error,
                        "estimated_position": aligned[:3, 3].tolist(),
                        "reference_position": lookup[i][:3, 3].tolist(),
                        "segment_id": segment,
                    }
                )
            for i in successful:
                previous = i - 1
                if previous not in lookup or previous not in indices:
                    continue
                delta_est = np.linalg.inv(_matrix(records[previous])) @ _matrix(
                    records[i]
                )
                delta_ref = np.linalg.inv(lookup[previous]) @ lookup[i]
                residual = np.linalg.inv(delta_ref) @ delta_est
                edge_t.append(float(np.linalg.norm(residual[:3, 3])))
                edge_r.append(float(Rotation.from_matrix(residual[:3, :3]).magnitude()))
        rigid = scaled = None
        rpe_t, rpe_r = [], []
        if successful and len(matched) >= 2:
            est = np.array([_matrix(records[i])[:3, 3] for i in matched])
            ref = np.array([lookup[i][:3, 3] for i in matched])
            rigid, scaled = _best_fit(est, ref, False), _best_fit(est, ref, True)
            rpe_t, rpe_r = _relative_one_second(
                np.array([records[i].timestamp_s for i in matched]),
                [_matrix(records[i]) for i in matched],
                [lookup[i] for i in matched],
            )
        if rigid is not None:
            rigid_all.extend(rigid[0].tolist())
        if scaled is not None:
            scaled_all.extend(scaled[0].tolist())
            sizes.append(scaled[1])
        rpe_t_all.extend(rpe_t)
        rpe_r_all.extend(rpe_r)
        positions.extend(errors)
        translations.extend(edge_t)
        rotations.extend(edge_r)
        details.append(
            {
                "segment_id": segment,
                "observations": len(indices),
                "matched": len(matched),
                "position_rmse_m": _rmse(errors),
                "position_samples": len(errors),
                "relative_pairs": len(edge_t),
                "relative_translation_rmse_m": _rmse(edge_t),
                "relative_rotation_rmse_rad": _rmse(edge_r),
                "ate_rigid_rmse_m": None if rigid is None else _rmse(rigid[0].tolist()),
                "ate_scaled_rmse_m": None if scaled is None else _rmse(scaled[0].tolist()),
                "ate_scaled_size": None if scaled is None else scaled[1],
                "rpe_1s_translation_rmse_m": _rmse(rpe_t),
                "rpe_1s_rotation_rmse_rad": _rmse(rpe_r),
            }
        )
    attempted = sum(r.status in {"tracked", "failed"} for r in records[1:])
    tracked = sum(r.status == "tracked" for r in records)
    return {
        "alignment": "first matched reference per segment; rigid; scale exactly one",
        "position_rmse_m": _rmse(positions),
        "position_samples": len(positions),
        "relative_translation_rmse_m": _rmse(translations),
        "relative_rotation_rmse_rad": _rmse(rotations),
        "relative_pairs": len(translations),
        "ate_rigid_rmse_m": _rmse(rigid_all),
        "ate_scaled_rmse_m": _rmse(scaled_all),
        # One size per segment; an overall size only exists when one segment was fitted.
        "ate_scaled_size": sizes[0] if len(sizes) == 1 else None,
        "rpe_1s_translation_rmse_m": _rmse(rpe_t_all),
        "rpe_1s_rotation_rmse_rad": _rmse(rpe_r_all),
        "alignment_note": "position_rmse_m: first matched pose, size 1; ate_rigid: best-fit rotation and shift per segment (TUM ATE); ate_scaled: best fit with one size per segment; rpe_1s: alignment-free motion error over 1 s",
        "segments": details,
        "errors": all_errors,
        "unmatched_estimates": len(records) - len(matches),
        "unmatched_references": len(references) - len(matches),
        "tracked_edges": tracked,
        "failed_observations": sum(r.status == "failed" for r in records),
        "possible_transitions": max(0, len(records) - 1),
        "attempted_or_failed_transitions": attempted,
        "tracked_fraction": tracked / (len(records) - 1) if len(records) > 1 else None,
        "pooling": "sample-weighted squared errors; segments remain individually reported",
        "loop_closure": False,
        "map_recovery": False,
    }
