"""Static review with explicit measurement populations and raw artifact links."""

import html
from pathlib import Path

import numpy as np

from experiments.shared.exporting import _cloud_preview
from experiments.shared.inspection import surface_view


def build_review(path: Path, metrics: dict, frames: list[dict]) -> None:
    scene = surface_view(path)
    if not (path / "debug/surface.png").is_file():
        points = np.array([p for frame in scene["frames"] for p in frame["points"]])
        colours = np.array([c for frame in scene["frames"] for c in frame["colours"]])
        _cloud_preview(path / "debug/surface.png", points, colours)
    depth_legends = {
        record["path"]: record
        for record in scene["roles"]
        if record.get("path", "").endswith("/depth_metres.png")
    }
    rows = []
    for frame in frames:
        key = html.escape(frame["frame_id"])
        depth_path = f"debug/{key}/depth_metres.png"
        depth_legend = depth_legends[depth_path]
        valid_pixels = depth_legend["total_pixels"] - depth_legend["missing_pixels"]
        rows.append(
            f'<article><h2>Frame {key}: {frame["points"]:,} observed points</h2>'
            f"<p>Observed input: colour. Ground truth: synthetic depth. Evaluated output: distance.</p>"
            f"<p>Depth validity mask: white means valid depth; black means missing depth. "
            f"This is not an object mask. {valid_pixels:,} valid, "
            f"{depth_legend['missing_pixels']:,} missing of "
            f"{depth_legend['total_pixels']:,} pixels.</p>"
            f'<img src="input/{key}/rgb.png" alt="Observed input RGB frame {key}">'
            f'<img src="debug/{key}/depth_metres.png" alt="Ground truth synthetic depth in metres">'
            f'<img src="debug/{key}/{html.escape(depth_legend["valid_mask"])}" '
            f'alt="Depth validity mask for frame {key}: white valid, black missing">'
            f'<img src="debug/{key}/distance.png" alt="Distance to reference in metres">'
            f'<p><a href="debug/{key}/depth_metres.json">Depth colour scale</a> · '
            f'<a href="debug/{key}/legends.json">Distance scale</a> · '
            f'<a href="output/{key}/surface.ply">Observed point surface</a> · '
            f'<a href="output/{key}/stages.json">Stages and scores</a> · '
            f'<a href="input/{key}/observation.json">Supplied camera pose</a></p></article>'
        )
    accuracy = metrics["accuracy"]
    controls = metrics["negative_controls"]
    fault_rows = (
        f"<tr><td>Mean distance with doubled depth</td><td>{controls['double_depth']['mean_m']:.6f} m</td></tr>"
        f"<tr><td>Mean distance with inverse poses</td><td>{controls['inverse_pose']['mean_m']:.6f} m</td></tr>"
        if controls
        else "<tr><td>Dataset fault checks</td><td>Not measured in this completed run</td></tr>"
    )
    control_note = ""
    if (
        "negative_control_frame_ids" in metrics
        and metrics["negative_control_clean_accuracy"] is not None
    ):
        control_note = (
            "<p>Fault checks cover frames "
            + ", ".join(str(i) for i in metrics["negative_control_frame_ids"])
            + f". Their matched clean mean is {metrics['negative_control_clean_accuracy']['mean_m']:.6f} m. "
            "These checked measurements were recovered from a verified complete run. Other frames have no fault-check measurement.</p>"
            '<h2>Accumulated observed surface</h2><img style="width:80%" src="debug/surface.png" '
            'alt="All selected supplied-depth points in the reference coordinate frame">'
        )
    elif "negative_control_frame_ids" in metrics:
        control_note = (
            "<p>Fault summaries from the interrupted run lack a completed hash inventory. They are retained "
            "as diagnostic records and excluded from measurements here. Analytic tests separately verify fault sensitivity.</p>"
            '<h2>Accumulated observed surface</h2><img style="width:80%" src="debug/surface.png" '
            'alt="All selected supplied-depth points in the reference coordinate frame">'
        )
    content = f"""<!doctype html><html lang="en"><meta charset="utf-8">
<title>Supplied-depth surface baseline</title><style>
body{{font:17px system-ui;max-width:1200px;margin:32px auto;padding:0 20px;color:#17242c}}
img{{width:31%;height:auto}} article{{border-top:1px solid #aaa;margin-top:28px}}
table{{border-collapse:collapse}} td,th{{padding:10px;border:1px solid #bbb;text-align:left}}
</style><h1>Surface built from supplied depth and camera poses</h1>
<p>This CPU baseline accumulates observations as coloured points. It does not estimate camera
motion, predict depth, merge duplicates or fill holes. Each file retains its source frame and pixel.</p>
<h2>Interactive accumulated point surface</h2>
<iframe title="Interactive 3D point surface" src="viewer.html" loading="lazy"
style="width:100%;height:720px;border:1px solid #99a8b8"></iframe>
{control_note}
<p><a href="viewer.html">Open labelled interactive 3D point surface</a> · <a href="metadata/artifact_roles.json">Artifact roles</a></p>
<h2>Evaluated output: accumulated point surface</h2><img style="width:80%" src="debug/surface.png" alt="Evaluated output: point surface in reference coordinates">
<table><tr><th>Measurement</th><th>Result</th></tr>
<tr><td>Observed points</td><td>{metrics['reconstruction_points']:,}</td></tr>
<tr><td>Mean observed-point distance to reference</td><td>{accuracy['mean_m']:.6f} m</td></tr>
<tr><td>Root mean squared distance</td><td>{accuracy['rmse_m']:.6f} m</td></tr>
<tr><td>Maximum distance</td><td>{accuracy['max_m']:.6f} m</td></tr>
<tr><td>Whole reference within {metrics['threshold_m']:g} m</td>
<td>{metrics['reference_coverage_fraction']:.2%} of {metrics['reference_points']:,} vertices</td></tr>
{fault_rows}</table>
<p>Coverage includes unseen room regions and is weighted by reference vertex count, not surface
area. It is not visible-region completeness. Duplicate views weight the observed-point error
multiple times. The fixed publisher conversion is used without fitted alignment or scale.
The reporting distance is not a product accuracy requirement.</p>
<p><a href="output/metrics.json">All measurements and timings</a> ·
<a href="output/surface.json">Accumulated surface file index</a> ·
<a href="metadata/configuration.json">Configuration</a> ·
<a href="metadata/status.json">Completion receipt</a></p>
<p>Images show original colour, supplied depth, then reference distance. Each diagnostic has its
own scale in the linked legend. Black means invalid depth. Raw values are stored in matching arrays.</p>
{''.join(rows)}</html>"""
    (path / "review.html").write_text(content, encoding="utf-8")
