"""Honest run manifests, numerical arrays and headless previews."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
from scipy.spatial.transform import Rotation

from .acquisition import sha256
from .mapping import save_maps


def write_json(path: Path, data: dict) -> None:
    """Strict JSON: nonfinite measurements cannot silently become invalid JSON."""
    text = json.dumps(data, indent=2, allow_nan=False)
    temporary = path.with_name(path.name + f".{uuid4().hex}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def new_run(root: Path, method: str) -> Path:
    """Unique UTC run directory with collision-resistant suffix."""
    path = root / f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{method}_{uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def preview(
    cloud: o3d.geometry.PointCloud, products: dict, output: Path, title: str
) -> None:
    """Software-rendered diagnostic, not a photorealistic or invented overhead view."""
    xyz, rgb = np.asarray(cloud.points), np.asarray(cloud.colors)
    indices = np.linspace(0, len(xyz) - 1, min(15000, len(xyz)), dtype=int)
    fig = plt.figure(figsize=(13, 8))
    ax = fig.add_subplot(221, projection="3d")
    ax.scatter(*xyz[indices].T, c=rgb[indices], s=0.3, rasterized=True)
    ax.set(
        xlabel="X (m)", ylabel="Y (m)", zlabel="Z (m)", title="Observed fused geometry"
    )
    ax.set_box_aspect(np.maximum(np.ptp(xyz, axis=0), 0.01))
    bounds = products["metadata"]["bounds_xy_m"]
    extent = [bounds[0][0], bounds[1][0], bounds[0][1], bounds[1][1]]
    ax = fig.add_subplot(222)
    ax.imshow(products["colour"], origin="lower", extent=extent)
    ax.set(title="Highest observed surface RGB", xlabel="X (m)", ylabel="Y (m)")
    ax = fig.add_subplot(223)
    plot = ax.imshow(products["height"], origin="lower", extent=extent, cmap="viridis")
    fig.colorbar(plot, ax=ax, label="Height (m)")
    ax.set(title="Height; blank = unknown", xlabel="X (m)", ylabel="Y (m)")
    ax = fig.add_subplot(224)
    plot = ax.imshow(np.log1p(products["count"]), origin="lower", extent=extent)
    fig.colorbar(plot, ax=ax, label="log(1 + retained samples)")
    ax.set(title="Sampling coverage, not free space", xlabel="X (m)", ylabel="Y (m)")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(output / "preview.png", dpi=140)
    plt.close(fig)


def export_run(
    output: Path,
    cloud: o3d.geometry.PointCloud,
    products: dict,
    manifest: dict,
    metrics: dict,
    timestamps: list[float],
    poses: list[np.ndarray],
    run_started_perf: float | None = None,
) -> None:
    """Save outputs and append compact summary across sequential local runs."""
    export_tick = perf_counter()
    if not o3d.io.write_point_cloud(str(output / "point_cloud.ply"), cloud):
        raise OSError("Point cloud export failed")
    save_maps(products, output)
    write_json(output / "map_metadata.json", products["metadata"])
    with (output / "trajectory.tum").open("w", encoding="utf-8") as stream:
        stream.write(
            "# timestamp tx ty tz qx qy qz qw; T_map_camera; metres, seconds\n"
        )
        for t, pose in zip(timestamps, poses):
            values = [t, *pose[:3, 3], *Rotation.from_matrix(pose[:3, :3]).as_quat()]
            stream.write(" ".join(f"{x:.9f}" for x in values) + "\n")
    preview(
        cloud,
        products,
        output,
        manifest["method"]
        + (
            " | known synthetic coordinates"
            if manifest["method"].startswith("synthetic")
            else " | supplied reference axes, gravity unverified"
        ),
    )
    export_s = perf_counter() - export_tick
    final_timings = {**metrics.get("timings", {}), "export_s": export_s}
    final_metrics = {
        **metrics,
        "timings": final_timings,
        "end_to_end_runtime_s": (
            perf_counter() - run_started_perf
            if run_started_perf is not None
            else metrics["runtime_s"] + export_s
        ),
    }
    final_manifest = {
        **manifest,
        "timings": final_timings,
        "completion_contract": "COMPLETE.json required; single-process summary writing only",
    }
    write_json(output / "run_manifest.json", final_manifest)
    write_json(output / "metrics.json", final_metrics)
    lines = [
        f"# {manifest['method']}",
        "",
        f"Sequence: {manifest['input_sequence']}",
        f"Accepted: {metrics['accepted_frames']}/{metrics['selected_frames']}. Tracking failures: {len(manifest['tracking_failures'])}.",
        "",
        f"Scale source: {manifest['scale_source']}; units: metres.",
        "No loop closure. Supplied-pose control is not SLAM. Estimated poses use identity initialization without ground truth.",
        "",
        "Top-down rasters project observed geometry. Unknown cells remain NaN. Sample counts are not confidence/free-space evidence.",
        "Reference axes come from the declared transform; gravity alignment is unverified. These are not surveyed level site maps.",
        "Maximum height can hide lower surfaces; inspect height_min.npy and vertical_range.npy or rerun a height slice.",
        "",
        "## Measured metrics",
        "",
        "```json",
        json.dumps(final_metrics, indent=2),
        "```",
        "",
        "TUM pose ground truth is not a reference mesh; no surface accuracy/completeness is claimed.",
        "No mesh, learned depth or phone reconstruction was executed in this baseline.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = output.parent / "benchmark_summary.csv"
    row = {
        "run": output.name,
        "method": manifest["method"],
        "sequence": manifest["input_sequence"],
        "selected": metrics["selected_frames"],
        "accepted": metrics["accepted_frames"],
        "ate_rmse_m": metrics.get("ate_rmse_m"),
        "runtime_s": metrics["runtime_s"],
        "points": len(cloud.points),
        "observed_cells": metrics["observed_cells"],
    }
    exists = summary.exists()
    with summary.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    write_json(
        output / "COMPLETE.json",
        {
            "status": "complete",
            "method": manifest["method"],
            "manifest_sha256": sha256(output / "run_manifest.json"),
            "metrics_sha256": sha256(output / "metrics.json"),
        },
    )
