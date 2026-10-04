"""Offline plots of one measured cloud and explicit detection-depth markers."""

import base64
import html
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from experiments.shared.visualization import sample_points


def annotate(image: Path, detections: list[dict], output: Path) -> None:
    with Image.open(image) as original:
        preview = original.convert("RGB")
    draw = ImageDraw.Draw(preview)
    for i, detection in enumerate(detections):
        colour = "red" if detection["class_id"] == 41 else "lime"
        draw.rectangle(detection["xyxy"], outline=colour, width=3)
        text = f"{i}: {detection['label']} {detection['confidence']:.2f}"
        draw.text(
            (detection["xyxy"][0], max(0, detection["xyxy"][1] - 15)),
            text,
            fill=colour,
            stroke_width=1,
            stroke_fill="black",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    preview.save(output)


def _markers(locations: list[dict], key: str) -> list[dict]:
    return [
        {
            "point": item["centre_sample"][key],
            "label": f"cup detection {item['detection_index']}",
        }
        for item in locations
        if item["centre_sample"] and item["centre_sample"][key] is not None
    ]


def write_cloud_review(
    output: Path,
    image: Path,
    camera: np.ndarray,
    world: np.ndarray,
    colours: np.ndarray,
    locations: list[dict],
    pose: dict,
    cap: int = 20000,
) -> None:
    import plotly.graph_objects as go

    sampled = sample_points(world, colours, cap)
    world_sample = np.asarray(sampled["points"]).reshape(-1, 3)
    camera_sample = np.asarray(sample_points(camera, colours, cap)["points"]).reshape(
        -1, 3
    )
    rgb = [f"rgb({r},{g},{b})" for r, g, b in sampled["colours"]]
    world_marks = _markers(locations, "world_m")
    camera_marks = _markers(locations, "camera_m")
    figure = go.Figure()
    figure.add_trace(
        go.Scatter3d(
            x=world_sample[:, 0],
            y=world_sample[:, 1],
            z=world_sample[:, 2],
            mode="markers",
            marker={"size": 2, "color": rgb},
            name="Measured RGB-D scene",
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter3d(
            x=[m["point"][0] for m in world_marks],
            y=[m["point"][1] for m in world_marks],
            z=[m["point"][2] for m in world_marks],
            text=[m["label"] for m in world_marks],
            mode="markers+text",
            marker={"size": 9, "color": "red", "symbol": "cross"},
            textposition="top center",
            name="Cup: measured centre pixel",
            hovertemplate="%{text}<br>X %{x:.3f} m<br>Y %{y:.3f} m<br>Z %{z:.3f} m<extra></extra>",
        )
    )
    figure.update_layout(
        title="Cup detection inside the measured point cloud",
        height=740,
        scene={
            "aspectmode": "data",
            "xaxis_title": "World X (m)",
            "yaxis_title": "World Y (m)",
            "zaxis_title": "World Z (m)",
        },
        margin={"l": 0, "r": 0, "b": 0, "t": 60},
        updatemenus=[
            {
                "buttons": [
                    {
                        "label": label,
                        "method": "update",
                        "args": [
                            {
                                axis: [
                                    cloud[:, n].tolist(),
                                    [m["point"][n] for m in marks],
                                ]
                                for n, axis in enumerate(("x", "y", "z"))
                            },
                            {
                                "scene.xaxis.title": f"{label} X (m)",
                                "scene.yaxis.title": f"{label} Y (m)",
                                "scene.zaxis.title": f"{label} Z (m)",
                            },
                        ],
                    }
                    for label, cloud, marks in [
                        ("World", world_sample, world_marks),
                        ("Camera", camera_sample, camera_marks),
                    ]
                ],
                "x": 0,
                "y": 1.1,
            }
        ],
    )
    with Image.open(image) as original:
        buffer = io.BytesIO()
        original.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    rows = "".join(
        f"<tr><td>{item['detection_index']}</td><td>{html.escape(item['status'])}</td>"
        f"<td><pre>{html.escape(json.dumps(item['centre_sample'], indent=2))}</pre></td>"
        f"<td><pre>{html.escape(json.dumps(item['box_median'], indent=2))}</pre></td></tr>"
        for item in locations
    )
    page = (
        "<!doctype html><html lang='en'><meta charset='utf-8'><title>Cup in RGB-D point cloud</title>"
        "<style>body{font:16px system-ui;margin:24px;color:#16202a}img{max-width:100%}"
        "table{border-collapse:collapse}td,th{border:1px solid #ddd;padding:12px;text-align:left}"
        "pre{white-space:pre-wrap}h1{font-size:26px}</style>"
        "<h1>Cup detection in a measured 3D scene</h1>"
        "<p>Drag to rotate; scroll to zoom. Red crosses mark measured depth pixels nearest the cup box centres. "
        "Switch World/Camera above the cloud. World coordinates use supplied TUM camera poses. "
        "Each cross marks a visible surface sample, not the physical object's centre. "
        "Box depth can include the desk; neither method is a foreground mask.</p>"
        f"<p>{len(world):,} valid measured points; {len(world_sample):,} displayed. Missing depth stays missing. "
        "Original pixels and full coordinates are retained in output/cloud.npz. "
        "Camera axes are X right, Y down, Z forward. No independent object-location accuracy is claimed.</p>"
        + figure.to_html(
            full_html=False, include_plotlyjs=True, config={"responsive": True}
        )
        + f"<h2>Original-frame detections</h2><img alt='Detected cup box and other objects' src='data:image/png;base64,{encoded}'>"
        + "<h2>Position support, in metres</h2><table><tr><th>Detection</th><th>Status</th>"
        "<th>Nearest measured centre pixel</th><th>All box pixels: camera median</th></tr>"
        + rows
        + "</table><h2>Camera pose provenance</h2><pre>"
        + html.escape(json.dumps(pose, indent=2))
        + "</pre></html>"
    )
    output.write_text(page, encoding="utf-8")
    _static_cloud(
        output.with_suffix(".png"),
        world_sample,
        np.asarray(sampled["colours"]).reshape(-1, 3),
        world_marks,
    )


def _static_cloud(
    output: Path, points: np.ndarray, colours: np.ndarray, markers: list[dict]
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(10, 8))
    axes = figure.add_subplot(projection="3d", computed_zorder=False)
    axes.scatter(*points.T, c=colours / 255, s=1, alpha=0.55)
    for marker in markers:
        axes.scatter(
            *marker["point"],
            c="red",
            marker="x",
            s=180,
            linewidths=3,
            depthshade=False,
            zorder=10,
        )
        axes.text(
            *marker["point"],
            marker["label"],
            color="red",
            zorder=11,
            bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "none"},
        )
    axes.set(
        xlabel="World X (m)",
        ylabel="World Y (m)",
        zlabel="World Z (m)",
        title="YOLO cup detection in recorded RGB-D cloud",
    )
    if len(points):
        axes.set_box_aspect(np.maximum(np.ptp(points, axis=0), 0.01))
    else:
        axes.text2D(
            0.2,
            0.5,
            "No valid depth measurements; no object marker",
            transform=axes.transAxes,
        )
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)
