"""Overview page: the five layers, results so far and links to every demo page."""

from __future__ import annotations

import html

import numpy as np
from PIL import Image, ImageDraw

from tools.demos.geometry import render_points
from tools.demos.pack import colormap, image_data_url
from tools.demos.page import build_page, layout
from tools.demos.sources import TUM, read_depth_m, read_rgb

THUMB = (360, 270)

LAYERS = [
    ("l1", "1 · Camera capture", "Phone records video, motion sensors and, where available, the phone's own position and depth.",
     ["Phone walkthrough · planned", "Benchmark recordings · stand-in", "Delivery to edge or cloud · planned"]),
    ("l2", "2 · Depth estimation", "How far away each pixel is, in metres. Two-lens stereo if the phone allows it, otherwise single-camera video.",
     ["Stereo from two lenses · planned", "Phone depth API · planned", "Recorded sensor depth · stand-in"]),
    ("l3", "3 · Camera position", "Where the camera was, and which way it pointed, for every frame.",
     ["Visual tracking · 6.9 mm error", "Reference camera path · control", "Drift correction · planned"]),
    ("l4", "4 · Environment", "One 3D model of the visible site in metres, and views of it: points, meshes, splats and a top-down map.",
     ["Point surfaces · 7.8 mm error", "Gaussian splats · demo here", "Meshes · planned", "Bird's-eye map · demo here"]),
    ("l5", "5 · Object isolation", "Which objects are there, where they are in 3D, and how many distinct ones, even when they leave and return.",
     ["Detection · early trial", "Segmentation · early trial", "Similarity · early trial", "Tracking and counting · early trial"]),
]


def thumbnails(replay: dict, scene: dict, birds_eye_rgb: np.ndarray, surface_top: np.ndarray, depth_index: int) -> dict[str, str]:
    """Small still images for the overview cards, made from the same saved data as the pages."""
    frame = replay["frames"][depth_index]
    rgb = read_rgb(frame.rgb_path)
    depth = colormap(read_depth_m(frame.depth_path), 0.5, 3.5)
    view = replay["frames"][1]
    rendered = render_points(scene["positions"], scene["colours"], view.pose, TUM, radius_px=1, background=(21, 24, 28))
    boxed = Image.fromarray(rgb)
    draw = ImageDraw.Draw(boxed)
    for d in frame.detections:
        colour = (216, 27, 96) if d.get("object_id") else (150, 150, 150)
        draw.rectangle(d["xyxy"], outline=colour, width=4)
    return {
        "depth": image_data_url(depth, size=THUMB), "tracking": image_data_url(read_rgb(replay["frames"][0].rgb_path), size=THUMB),
        "surface": image_data_url(surface_top, size=THUMB), "splats": image_data_url(rendered, size=THUMB),
        "birds": image_data_url(birds_eye_rgb, size=THUMB), "objects": image_data_url(np.asarray(boxed), size=THUMB),
    }


def _layer_stack() -> str:
    blocks = []
    for cls, title, text, boxes in LAYERS:
        items = "".join(f'<li class="{"planned" if "planned" in b else ""}">{html.escape(b)}</li>' for b in boxes)
        blocks.append(f'<div class="layer {cls}"><div><h3>{html.escape(title)}</h3><p>{html.escape(text)}</p></div><ul>{items}</ul></div>')
    blocks.append('<div class="layer answers"><h3>What it answers</h3><ul><li>How big is the site?</li><li>How many of each object?</li></ul></div>')
    return '<div class="stack">' + '<div class="arrow" aria-hidden="true">↓</div>'.join(blocks) + "</div>"


STACK_CSS = """
.stack { display: grid; gap: 4px; margin: 18px 0 8px; }
.stack .arrow { text-align: center; color: var(--ink-3); line-height: 1; }
.layer { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr); gap: 14px; align-items: center; padding: 14px 16px; border-radius: var(--radius); border: 2px solid; }
.layer h3 { margin: 0 0 4px; font-size: 1.05rem; }
.layer p { margin: 0; font-size: .9rem; color: var(--ink-2); }
.layer ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 6px; }
.layer li { background: var(--surface); border: 1.5px solid var(--ink-2); border-radius: 6px; padding: 4px 9px; font-size: .82rem; }
.layer li.planned { border-style: dashed; color: var(--ink-3); border-color: var(--ink-3); }
.layer.l1 { background: var(--l1-bg); border-color: var(--l1); } .layer.l1 h3 { color: var(--l1); }
.layer.l2 { background: var(--l2-bg); border-color: var(--l2); } .layer.l2 h3 { color: var(--l2); }
.layer.l3 { background: var(--l3-bg); border-color: var(--l3); } .layer.l3 h3 { color: var(--l3); }
.layer.l4 { background: var(--l4-bg); border-color: var(--l4); } .layer.l4 h3 { color: var(--l4); }
.layer.l5 { background: var(--l5-bg); border-color: var(--l5); } .layer.l5 h3 { color: var(--l5); }
.layer.answers { background: #263238; border-color: #263238; color: #fff; grid-template-columns: auto 1fr; }
.layer.answers h3 { color: #fff; } .layer.answers li { background: transparent; color: #fff; border-color: rgba(255,255,255,.6); }
@media (max-width: 700px) { .layer { grid-template-columns: minmax(0, 1fr); } }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; margin: 16px 0; }
.card { display: block; text-decoration: none; color: inherit; background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); transition: transform .15s ease, box-shadow .15s ease; }
.card:hover, .card:focus-visible { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(0,0,0,.12); }
.card img { width: 100%; aspect-ratio: 4/3; object-fit: cover; display: block; background: #15181c; }
.card div { padding: 12px 14px 14px; }
.card h3 { margin: 6px 0 4px; font-size: 1.05rem; }
.card p { margin: 0; font-size: .88rem; color: var(--ink-2); }
"""

CARDS = [
    ("01_depth_to_3d.html", "depth", "l2", "Layer 2", "From one photo to points in 3D", "Follow one real frame from colour and depth to a 3D point cloud."),
    ("02_camera_tracking.html", "tracking", "l3", "Layer 3", "Where was the camera?", "Our tracker's camera path next to a motion-capture measurement."),
    ("03_surface_accuracy.html", "surface", "l4", "Layer 4", "How close is the 3D surface?", "A room's points coloured by distance to an independent reference model."),
    ("04_gaussian_splats.html", "splats", "l4", "Layer 4", "The desk as Gaussian splats", "Sparse points, merged points and soft splats, checked against real photos."),
    ("05_birds_eye_map.html", "birds", "l4", "Layer 4", "Bird's-eye map", "Top-down colour and height, unseen areas kept visible, with a measuring tool."),
    ("06_objects_in_3d.html", "objects", "l5", "Layer 5", "Counting objects that leave and return", "Scrub a 60-frame recording and watch the object count build up."),
]


def overview(thumbs: dict[str, str], results: list[tuple[str, str, str, str]]) -> str:
    """Page 00: layered approach, results table and cards linking to the other pages."""
    cards = "".join(
        f'<a class="card" href="{f}"><img src="{thumbs[k]}" alt=""><div><span class="layer-tag {cls}">{tag}</span>'
        f'<h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></div></a>' for f, k, cls, tag, t, d in CARDS)
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td><b>{c}</b></td><td>{d}</td></tr>" for a, b, c, d in results)
    main = f"""
<style>{STACK_CSS}</style>
<h2>The problem</h2>
<p>Field workers already film short walkthrough videos of their sites. This research asks whether the same kind of phone video can also give two things: <b>the size of the visible site in metres</b>, and <b>a count of distinct objects</b>, where an object that leaves the frame and comes back is counted once.</p>
<h2>The approach: five layers</h2>
<p>Each layer is built and tested on its own with known-good inputs, then connected. Solid boxes work today; dashed boxes are planned.</p>
{_layer_stack()}
<h2>Explore each stage</h2>
<div class="cards">{cards}</div>
<h2>Results so far</h2>
<p>All results are on public recorded data on a desktop computer. None is from a phone or a worksite yet.</p>
<div class="table-wrap"><table><thead><tr><th>Layer</th><th>Test</th><th>Result</th><th>What it does not show</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="note">Earlier object trials are summarised in the project README: detection (4 of 5 checked cups found), segmentation (45 masks compared), appearance matching (7 of 7 pairs ranked correctly) and identity rules (11 of 11 sightings assigned).</p>
"""
    body = layout("00_overview.html", "FYLD scene-mapping research", "Measuring sites and counting objects from a phone walkthrough",
                  "A short visual tour of the research: what each layer does, how it is tested, and what the tests show so far. Every page in this folder is a single file that works offline.",
                  main, "Built by <code>tools/demos/build.py</code> from saved experiment runs. No experiment was rerun.")
    return build_page("Research overview", "Visual overview of the five-layer site mapping and object counting research.", body, {}, [], "")
