"""Desktop inspection artifacts; plots do not change estimated trajectories."""

import html
from pathlib import Path

import numpy as np
from PIL import Image

from experiments.shared.inspection import tracking_view

from .dataset import RGBDFrame


def thumbnail(frame: RGBDFrame, root: Path) -> None:
    path = root / "debug" / f"{frame.frame_id}_rgb.png"
    Image.fromarray(frame.colour).resize((320, 240)).save(path)
    values = np.where(frame.valid, np.minimum(frame.depth / 4, 1), 0)
    Image.fromarray((values * 255).astype(np.uint8)).resize((320, 240)).save(
        root / "debug" / f"{frame.frame_id}_depth.png"
    )


def report(root: Path, records: list, metrics: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    errors = metrics["errors"]
    for segment in metrics["segments"]:
        rows = [e for e in errors if e["segment_id"] == segment["segment_id"]]
        if rows:
            estimated = np.array([r["estimated_position"] for r in rows])
            reference = np.array([r["reference_position"] for r in rows])
            axes[0].plot(
                estimated[:, 0],
                estimated[:, 2],
                label=f"estimated segment {segment['segment_id']}",
            )
            axes[0].plot(reference[:, 0], reference[:, 2], "--", label="reference")
            axes[1].plot(
                [int(r["frame_id"]) for r in rows],
                [r["position_error_m"] * 1000 for r in rows],
            )
    axes[0].set(
        xlabel="X (metres)", ylabel="Z (metres)", title="Fixed-scale trajectory"
    )
    axes[1].set(
        xlabel="Observation",
        ylabel="Position error (mm)",
        title="Independent reference error",
    )
    if errors:
        axes[0].legend()
    figure.tight_layout()
    figure.savefig(root / "debug/trajectory.png")
    plt.close(figure)
    rows = []
    for record in records:
        identifier = html.escape(record.frame_id)
        rows.append(
            f"<tr><td>{identifier}</td><td>{html.escape(record.status)}</td>"
            f'<td>{html.escape(record.reason)}</td><td><img src="debug/{identifier}_rgb.png"></td>'
            f'<td><img src="debug/{identifier}_depth.png"></td></tr>'
        )
    payload = '<!doctype html><html><meta charset="utf-8"><title>CPU tracking inspection</title>'
    payload += "<style>body{font:16px Arial;margin:24px}img{max-width:320px}td{padding:8px}table{border-collapse:collapse}</style>"
    payload += "<h1>CPU camera tracking</h1><p>Supplied depth; estimated poses. This pairwise baseline has no loop closure or map recovery.</p>"
    payload += f'<p>Tracked edges: {metrics["tracked_edges"]}/{metrics["possible_transitions"]}. Position error: {metrics["position_rmse_m"]} metres.</p>'
    payload += "<p>Each segment uses its first matched reference pose for rigid alignment, with scale fixed at one. Anchor-only accuracy is unavailable.</p>"
    payload += '<p><a href="metadata/timing.json">Timing and FPS metadata</a> | <a href="output/metrics.json">Scores</a> | <a href="output/poses.json">Poses and failures</a></p>'
    payload += "<p>Depth thumbnails show 0 to 4 metres; black means invalid depth. Desktop timing includes backend loading and reporting, and is not phone performance.</p>"
    payload += '<p><a href="viewer.html">Labelled interactive 3D camera motion</a> | <a href="metadata/artifact_roles.json">Artifact roles and provenance</a></p>'
    payload += "<p>Predicted output: estimated path. Ground truth: independent motion-capture path. Evaluated output: position error. Observed input: measured RGB and sensor depth.</p>"
    payload += '<img src="debug/trajectory.png"><table><tr><th>Observation</th><th>Status</th><th>Reason</th><th>Observed input RGB</th><th>Observed input depth</th></tr>'
    (root / "review.html").write_text(
        payload + "".join(rows) + "</table></html>", encoding="utf-8"
    )
    tracking_view(root)
