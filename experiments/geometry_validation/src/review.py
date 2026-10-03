"""Explain control stages and distinguish file/coordinate checks from accuracy."""

import html
import json
from pathlib import Path

from experiments.shared.runs import write_json
from experiments.shared.visualization import artifact

from .scene import export_scene

STAGES = {
    "rgb.png": (
        "1. Supplied colour image",
        "Copied dataset image. No depth or camera motion is predicted from it.",
    ),
    "depth.png": (
        "2. Supplied depth",
        "Dataset PNG values divided by 5000 give camera-axis distance in metres. This is not a predicted depth map.",
    ),
    "mask.png": (
        "2. Valid depth pixels",
        "White pixels have positive finite supplied depth; black pixels remain unknown.",
    ),
    "camera_cloud.png": (
        "3. Camera-coordinate points",
        "Supplied depth and calibration place each valid pixel in XYZ relative to this camera. Download camera.npy or camera.ply.",
    ),
    "world_cloud.png": (
        "4. World-coordinate points",
        "The dataset's supplied camera rotation and translation place the same points in the common world. No tracking was performed.",
    ),
    "model_cloud.png": (
        "5. Reference-coordinate points",
        "A fixed publisher conversion expresses those points in the reference coordinate convention. This is not a learned model or reconstructed surface.",
    ),
    "projection_error.png": (
        "6. Projection consistency",
        "Projecting camera points back to the image gives pixel differences. These check arithmetic, not depth or tracking accuracy.",
    ),
}


def _figure(key: str, name: str, legends: dict) -> str:
    title, description = STAGES.get(
        name,
        (
            "Coordinate-channel diagnostic",
            "A coordinate value at each original valid pixel; this is not another prediction.",
        ),
    )
    role = (
        "Observed input"
        if name == "rgb.png"
        else "Ground truth" if name == "depth.png" else "Evaluated output"
    )
    title = role + ": " + title
    scale = legends.get(name, {})
    if scale.get("minimum") is not None:
        description += f" Display range: {scale['minimum']:.6g} to {scale['maximum']:.6g} {scale['units']}. Each image has its own scale."
    return (
        f'<figure><img src="debug/{html.escape(key)}/{html.escape(name)}" alt="{html.escape(title)}">'
        f"<figcaption><strong>{html.escape(title)}</strong><p>{html.escape(description)}</p>"
        f"<small>{html.escape(name)}</small></figcaption></figure>"
    )


def _frame_section(path: Path, frame: dict) -> str:
    key = frame["frame_id"]
    legends = json.loads((path / f"debug/{key}/legends.json").read_text())
    visuals = frame["artifacts"]["visualizations"]
    primary = [name for name in STAGES if name in visuals]
    channels = [name for name in visuals if name not in STAGES]
    links = " ".join(
        f'<a href="output/{html.escape(key)}/{html.escape(name)}">{html.escape(name)}</a>'
        for name in frame["artifacts"]["arrays"] + frame["artifacts"]["clouds"]
    )
    header = (
        f'<section><h2>Input frame {html.escape(key)}</h2><p>{frame["valid_pixels"]:,} valid pixels. '
        f'Maximum projection arithmetic residual: {frame["max_projection_error_pixels"]} pixels.</p>'
        f'<p><a href="input/{html.escape(key)}/observation.json">Supplied pose and calibration</a> · '
        f'<a href="output/{html.escape(key)}/stages.json">Stage records</a> · '
        f'<a href="debug/{html.escape(key)}/legends.json">Image scales</a></p>'
    )
    main = (
        '<div class="grid">'
        + "".join(_figure(key, name, legends) for name in primary)
        + "</div>"
    )
    extra = '<details><summary>Additional XYZ coordinate-channel diagnostics</summary><div class="grid">'
    extra += (
        "".join(_figure(key, name, legends) for name in channels) + "</div></details>"
    )
    return (
        header
        + main
        + "<p>Numerical outputs and point clouds: "
        + links
        + "</p>"
        + extra
        + "</section>"
    )


def build_review(path: Path, frames: list[dict]) -> None:
    scene = export_scene(path, frames)
    roles = []
    for frame in frames:
        key = frame["frame_id"]
        for name in frame["artifacts"]["visualizations"]:
            role = (
                "observed_input"
                if name == "rgb.png"
                else "ground_truth" if name == "depth.png" else "evaluated_output"
            )
            roles.append(
                artifact(
                    f"debug/{key}/{name}",
                    role,
                    "CPU supplied-input geometry control",
                    [f"input/{key}/observation.json"],
                    "see image legend",
                    "display scale in legends.json",
                )
            )
        for name in frame["artifacts"]["arrays"] + frame["artifacts"]["clouds"]:
            roles.append(
                artifact(
                    f"output/{key}/{name}",
                    "ground_truth" if name == "depth.npy" else "evaluated_output",
                    "CPU geometry conversion",
                    [f"input/{key}/observation.json"],
                    "see stages.json",
                )
            )
        roles.append(
            artifact(
                f"input/{key}/observation.json",
                "ground_truth",
                "ICL supplied pose and calibration",
                [],
                "metres; pixels",
            )
        )
    write_json(path / "metadata/artifact_roles.json", {"artifacts": roles})
    rows = "".join(
        f'<tr><td>{html.escape(key)}</td><td>{", ".join(f"{v:.6f}" for v in centre)}</td>'
        f'<td>{", ".join(f"{v:.6f}" for v in delta)}</td></tr>'
        for key, centre, delta in zip(
            scene["frame_ids"],
            scene["centres_world_m"],
            scene["relative_centres_mm"],
            strict=True,
        )
    )
    page = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Supplied-input geometry control</title><style>
body{font:16px system-ui;line-height:1.5;margin:2rem;background:#f5f5f5;color:#172330}section{margin:2rem 0;padding:1.5rem;background:white}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem}figure{margin:0}img{max-width:100%;height:auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #b5c0cc;padding:.6rem;text-align:left}small{color:#44546a}a{color:#174d87}summary{cursor:pointer}
</style><h1>Geometry control using supplied depth and poses</h1>
<p><strong>Supplied depth. Supplied camera poses. No tracking or depth prediction.</strong></p>
<p>This program decodes known depth into metres, turns pixels into 3D points, and applies known camera poses. Each frame keeps its own points. It does not fuse a surface or estimate camera movement.</p>
<section><h2>What was checked, and what was not</h2><table><tr><th>Check</th><th>Meaning and limit</th></tr>
<tr><td>Run integrity</td><td>Completion is published after all artifact hashes validate. Check the <a href="metadata/status.json">completion receipt</a>; a running or failed run is incomplete.</td></tr>
<tr><td>Independent geometry tests</td><td>Known coordinates test units, signed focal lengths, transform direction and separate origins. These test the implementation, not an estimator.</td></tr>
<tr><td>Projection consistency</td><td>Pixel → 3D → pixel residuals check arithmetic. A tiny residual does not show correct predicted depth or tracking.</td></tr>
<tr><td>Depth prediction accuracy</td><td>Not measured: depth was supplied.</td></tr>
<tr><td>Tracking accuracy</td><td>Not measured: camera poses were supplied. Task 05 implements estimation and reference comparisons.</td></tr>
<tr><td>Reconstruction accuracy and coverage</td><td>Not measured: no fused surface or reference-surface comparison. Task 04 handles these.</td></tr></table></section>
<section><h2>Observations in one coordinate space</h2><p>Every valid point is shown, coloured by frame. Camera triangles mark supplied camera centres. World axes are not claimed to align with gravity.</p>
<img src="debug/scene_world.png" alt="Separate per-frame point clouds and supplied camera centres in common world">
<h3>Camera movement from the supplied pose table</h3><p>This view shows offsets in millimetres relative to the first selected view, without fitting or predicting movement. The connecting line does not establish motion between selected observations.</p>
<img src="debug/camera_positions.png" alt="Supplied camera centres in millimetres relative to first selected view">
<table><tr><th>Frame ID</th><th>World camera centre X, Y, Z (metres)</th><th>Offset from first view X, Y, Z (millimetres)</th></tr>"""
    page += (
        rows
        + '</table><p><a href="debug/scene.json">Exact positions and view provenance</a></p></section>'
    )
    page += "".join(_frame_section(path, frame) for frame in frames) + "</html>"
    (path / "review.html").write_text(page, encoding="utf-8")
