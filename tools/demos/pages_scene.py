"""Scene pages: one frame from depth to 3D, Gaussian splats of the desk, and a bird's-eye map."""

from __future__ import annotations

import numpy as np

from tools.demos.geometry import backproject, to_world, top_down_grid
from tools.demos.pack import (
    colormap,
    encode_array,
    encode_normals,
    encode_positions,
    image_data_url,
)
from tools.demos.page import build_page, layout, read_web, viewer_html
from tools.demos.sources import REPLAY_RUN, TUM, read_depth_m, read_rgb

DEPTH_FRAME_INDEX = 9  # desk frame 104: the cup is in view
SPLAT_WIDTH = 1.0  # tangent sigma as a multiple of the cell size; neighbours overlap smoothly
SPLAT_THICKNESS = 0.1  # normal sigma as a multiple of the cell size
BIRDS_EYE_MIN_POINTS = 3  # a map cell needs at least this many merged surface points to count as seen


def footer(run: str, settings: str) -> str:
    return (f"Built by <code>tools/demos/build.py</code> from the saved run <code>{run.split('/')[-1]}</code>. "
            f"No experiment was rerun. {settings} Self-contained: this file needs no network access.")


def depth_to_3d(replay: dict) -> tuple[str, dict]:
    """Page 01: one desk frame as colour, depth, missing-depth mask and 3D points."""
    frame = replay["frames"][DEPTH_FRAME_INDEX]
    rgb = read_rgb(frame.rgb_path)
    depth = read_depth_m(frame.depth_path)
    valid = np.isfinite(depth)
    lo, hi = (round(float(v), 1) for v in np.nanpercentile(depth, [1, 99]))
    depth_rgb = colormap(depth, lo, hi)
    missing = np.where(valid[..., None], (rgb * 0.35).astype(np.uint8), np.array([255, 64, 160], np.uint8))
    pts_cam, pix = backproject(depth, TUM, stride=2)
    world = to_world(pts_cam, frame.pose)
    data = {
        "up": [0, 0, 1],
        "pose": frame.pose.tolist(),
        "intrinsics": {"fx": TUM.fx, "fy": TUM.fy, "width": TUM.width, "height": TUM.height},
        "points": encode_positions(world),
        "rgb": encode_array(rgb[pix[:, 0], pix[:, 1]], "u8"),
        "depthColours": encode_array(depth_rgb[pix[:, 0], pix[:, 1]], "u8"),
        "images": {"rgb": image_data_url(rgb), "depth": image_data_url(depth_rgb, quality=88), "missing": image_data_url(missing)},
        "legend": {"lo": lo, "hi": hi, "gradient": legend_gradient("turbo")},
    }
    stats = {
        "valid_pct": 100.0 * valid.mean(), "points": len(world), "min": float(np.nanmin(depth)),
        "median": float(np.nanmedian(depth)), "max": float(np.nanmax(depth)),
    }
    main = f"""
<div class="stats">
  <div class="stat"><b>{stats['valid_pct']:.1f}%</b><span>pixels with a depth value</span></div>
  <div class="stat"><b>{stats['median']:.2f} m</b><span>median distance (range {stats['min']:.2f}–{stats['max']:.2f} m)</span></div>
  <div class="stat"><b>{stats['points']:,}</b><span>3D points shown (every second pixel)</span></div>
  <div class="stat"><b>525 px</b><span>focal length used to turn pixels into directions</span></div>
</div>
<h2>Step 1: what the camera recorded</h2>
<p>Each pixel has a colour and, from the depth sensor, a distance along the camera's forward axis. Pink marks pixels with no depth: shiny, dark or very close surfaces, and edges where the sensor could not decide.</p>
<div class="figure-row">
  <figure><img id="img-rgb" alt="Colour image of the desk"><figcaption>Colour image, desk frame {frame.frame_id}</figcaption></figure>
  <figure><img id="img-depth" alt="Depth image coloured by distance"><figcaption>Depth: blue is near, red is far
    <div class="legend-bar" id="legend"></div><div class="legend-scale"><span>{lo} m</span><span>{hi} m</span></div></figcaption></figure>
  <figure><img id="img-missing" alt="Pixels without depth in pink"><figcaption>Missing depth in pink ({100 - stats['valid_pct']:.1f}% of pixels)</figcaption></figure>
</div>
<h2>Step 2: every pixel becomes a point in space</h2>
<p>With focal length <i>f</i> and image centre (<i>c<sub>x</sub></i>, <i>c<sub>y</sub></i>), a pixel at column <i>u</i>, row <i>v</i> with depth <i>Z</i> sits at
<code>X = (u − c<sub>x</sub>)·Z / f</code>, <code>Y = (v − c<sub>y</sub>)·Z / f</code>. The camera pose then moves the point from the camera's frame into the room's frame, in metres. The white pyramid is the camera.</p>
<div class="controls">
  <div class="seg" role="group" aria-label="Point colours"><button data-colour="rgb" aria-pressed="true">Real colours</button><button data-colour="depth" aria-pressed="false">Depth colours</button></div>
  <button class="btn" id="from-camera">View from the camera</button><button class="btn" id="orbit">Step back</button>
</div>
{viewer_html()}
<p class="note">From the camera's own position the points line up with the photo exactly. Step back and the scene is only a shell: the camera saw just the front of each object, so the far sides are empty. Filling those in is why many views are combined (see the Gaussian splats page).</p>
"""
    body = layout("01_depth_to_3d.html", '<span class="layer-tag l2">Layer 2 · Depth</span>', "From one photo to points in 3D",
                  "Depth is what turns a flat image into something that can be measured. This page follows one real frame from the desk recording through that step.",
                  main, footer(REPLAY_RUN, "Depth from the TUM RGB-D Kinect sensor, raw values ÷ 5000, valid below 4 m."))
    doc = build_page("Depth to 3D", "One desk frame shown as colour, depth and 3D points.", body, data, ["viewer.js"], read_web("page_depth.js"))
    return doc, stats


def legend_gradient(name: str) -> str:
    """CSS linear-gradient for a colormap legend bar."""
    stops = colormap(np.linspace(0, 1, 9), 0, 1, name)
    return "linear-gradient(90deg," + ",".join(f"rgb({r},{g},{b})" for r, g, b in stops) + ")"


def gaussian_splats(replay: dict, scene: dict, voxel_m: float, compare_indices: list[int]) -> tuple[str, dict]:
    """Page 04: the fused desk shown as the current sparse cloud, fused points and Gaussian splats."""
    n = len(scene["positions"])
    alpha = np.where(scene["counts"] >= 4, 235, 160).astype(np.uint8)
    compare = []
    for i in compare_indices:
        f = replay["frames"][i]
        compare.append({"frame": f.frame_id, "pose": f.pose.tolist(),
                        "photo": image_data_url(read_rgb(f.rgb_path), quality=78, size=(480, 360))})
    data = {
        "up": [0, 0, 1], "voxel": voxel_m, "fy": TUM.fy, "height": TUM.height,
        "splat": {"positions": encode_positions(scene["positions"]), "normals": encode_normals(scene["normals"]),
                  "colours": encode_array(scene["colours"], "u8"), "alpha": encode_array(alpha, "u8"),
                  "tangentSigma": voxel_m * SPLAT_WIDTH, "normalSigma": voxel_m * SPLAT_THICKNESS},
        "display": {"positions": encode_positions(replay["display_points"]), "colours": encode_array(replay["display_rgb"], "u8")},
        "compare": compare,
    }
    stats = {"splats": n, "raw": int(scene["raw_point_count"]), "display": len(replay["display_points"]), "frames": len(replay["frames"])}
    main = f"""
<div class="stats">
  <div class="stat"><b>{stats['frames']}</b><span>colour and depth frames, each with its camera pose</span></div>
  <div class="stat"><b>{stats['raw'] / 1e6:.1f} M</b><span>depth points before merging</span></div>
  <div class="stat"><b>{stats['splats']:,}</b><span>Gaussians after merging repeats into {voxel_m * 100:.1f} cm cells</span></div>
  <div class="stat"><b>{stats['display']:,}</b><span>points in the project's existing replay viewer</span></div>
</div>
<div class="controls">
  <div class="seg" role="group" aria-label="Scene representation">
    <button data-mode="display" aria-pressed="false">Existing viewer · {stats['display']:,} points</button>
    <button data-mode="points" aria-pressed="false">Merged points</button>
    <button data-mode="splats" aria-pressed="true">Gaussian splats</button>
  </div>
  <label class="inline">Splat size <input type="range" id="splat-scale" min="0.5" max="2" step="0.05" value="1" style="width:120px"></label>
  <button class="btn" id="download-ply">Download splats (.ply)</button>
</div>
<div class="stage">
  {viewer_html(style="height:auto;min-height:0;aspect-ratio:4/3;max-height:78vh")}
  <div class="panel">
    <h3>Compare with the real photo</h3>
    <p>Jump to a recorded camera position. The 3D view then uses that camera's exact field of view, so it can be checked against the photo it came from.</p>
    <div class="controls" id="compare-buttons"></div>
    <figure><img id="compare-photo" alt="Photo from the selected camera"><figcaption id="compare-caption">Pick a frame above.</figcaption></figure>
  </div>
</div>
<h2>What a Gaussian splat is</h2>
<p>A point is a dot with no size, so a cloud of points always shows gaps and looks like dust. A Gaussian splat is a small soft-edged coloured blob with a position, a size, a direction and a transparency. Thousands of overlapping blobs blend into continuous surfaces, which is why splat scenes look close to photographs.</p>
<h3>How these splats were made</h3>
<ol>
<li>Every desk frame's depth was turned into 3D points using its recorded camera pose (as on the depth page). Pixels on depth edges, where the sensor mixes foreground and background, were dropped.</li>
<li>Points from all {stats['frames']} frames that fall in the same {voxel_m * 100:.1f} cm cell were averaged, which cancels some sensor noise. Cells seen fewer than 3 times were dropped as likely noise.</li>
<li>Each cell became one flat Gaussian disc lying along the local surface, with a soft radius of about {voxel_m * SPLAT_WIDTH * 100:.1f} cm and {voxel_m * SPLAT_THICKNESS * 1000:.1f} mm thick, coloured by the averaged pixels.</li>
</ol>
<p class="note">These splats are built directly from measured depth. They are not trained. Full Gaussian splatting (<a href="https://arxiv.org/abs/2308.04079">Kerbl et al., 2023</a>) starts from points like these and then adjusts every blob's position, size, colour and transparency on a GPU until rendered views match the photos, often reaching photo-real quality. That training step needs a GPU run, which was not done here. The splat geometry still comes only from measured depth, so it carries the same depth noise and the same unseen gaps.</p>
<p>The download button saves the splats in the standard 3D Gaussian splatting <code>.ply</code> format. Viewers such as <a href="https://superspl.at/editor">SuperSplat</a> can open it.</p>
"""
    body = layout("04_gaussian_splats.html", '<span class="layer-tag l4">Layer 4 · Environment</span>', "The desk as Gaussian splats",
                  "The same recorded desk shown three ways: the sparse cloud in the project's existing viewer, all merged depth points, and soft Gaussian splats built from them.",
                  main, footer(REPLAY_RUN, f"Cell {voxel_m * 100:.1f} cm, minimum 3 observations per cell, depth-edge threshold 3%, every second pixel used."))
    doc = build_page("Gaussian splats", "The recorded desk as points and as Gaussian splats.", body, data, ["viewer.js"], read_web("page_splats.js"))
    return doc, stats


def birds_eye(scene: dict, cell_m: float, height_range: tuple[float, float], colour_range: tuple[float, float]) -> tuple[str, dict]:
    """Page 05: top-down colour and height maps of the fused desk with a seen/unseen mask."""
    grid = top_down_grid(scene["positions"], scene["colours"], up_axis=2, cell_m=cell_m, height_range=height_range)
    observed = np.flipud(grid["observed"] & (grid["counts"] >= BIRDS_EYE_MIN_POINTS))
    height = np.where(observed, np.flipud(grid["height"]), np.nan)
    colour = np.flipud(grid["colour"])
    rgba_colour = np.dstack([colour, np.where(observed, 255, 0).astype(np.uint8)])
    hmap = colormap(height, *colour_range, name="viridis")
    rgba_height = np.dstack([hmap, np.where(observed, 255, 0).astype(np.uint8)])
    seen = np.zeros(observed.shape + (4,), np.uint8)
    seen[observed] = [70, 180, 120, 255]
    seen[~observed] = [210, 70, 70, 255]
    mm = np.where(observed, np.clip(np.rint((height - height_range[0]) * 1000), 0, 65534), 65535).astype(np.uint16)
    area_seen = float(observed.sum() * cell_m ** 2)
    data = {
        "cell": cell_m, "width": int(height.shape[1]), "height": int(height.shape[0]),
        "origin": [float(v) for v in grid["origin"]], "heightOffset": height_range[0],
        "heights": encode_array(mm, "u16"),
        "images": {"colour": image_data_url(rgba_colour, fmt="PNG"), "height": image_data_url(rgba_height, fmt="PNG"),
                   "seen": image_data_url(seen, fmt="PNG")},
        "legend": {"lo": colour_range[0], "hi": colour_range[1], "gradient": legend_gradient("viridis")},
    }
    stats = {"cells": int(observed.size), "seen_m2": area_seen, "box_m2": float(observed.size * cell_m ** 2),
             "size": (height.shape[1] * cell_m, height.shape[0] * cell_m)}
    main = f"""
<div class="stats">
  <div class="stat"><b>{stats['size'][0]:.1f} × {stats['size'][1]:.1f} m</b><span>area covered by the map</span></div>
  <div class="stat"><b>{stats['seen_m2']:.1f} m²</b><span>ground area actually seen from above</span></div>
  <div class="stat"><b>{100 * stats['seen_m2'] / stats['box_m2']:.0f}%</b><span>of the map box is seen; the rest is unknown</span></div>
  <div class="stat"><b>{cell_m * 100:.0f} cm</b><span>map cell size</span></div>
</div>
<div class="controls">
  <div class="seg" role="group" aria-label="Map layer">
    <button data-layer="colour" aria-pressed="true">Colour from above</button>
    <button data-layer="height" aria-pressed="false">Height</button>
    <button data-layer="seen" aria-pressed="false">Seen or unknown</button>
  </div>
  <button class="btn" id="clear-measure">Clear measurement</button>
</div>
<div class="stage">
  <div class="viewer" style="background:var(--surface-2)"><canvas id="map" aria-label="Top-down map; click two points to measure"></canvas>
    <div class="hint" style="color:var(--ink-3)">Click two points to measure · hover for height</div></div>
  <div class="panel">
    <h3>Reading the map</h3>
    <p id="readout">Hover over the map to see the height at a point.</p>
    <p id="measure">Click two points to measure the distance between them.</p>
    <div id="legend-wrap" hidden><div class="legend-bar" id="legend"></div><div class="legend-scale"><span>{colour_range[0]} m</span><span>{colour_range[1]} m above floor</span></div></div>
    <p>Each cell keeps the highest surface seen above it. A cell counts as seen when at least {BIRDS_EYE_MIN_POINTS} merged surface points fall in it, which removes isolated specks. Transparent or red cells were not seen. They are unknown, not empty floor.</p>
  </div>
</div>
<p class="note">This is an illustration of layer 4's planned top-down output, built from the same merged desk points as the splats page. It has no independent reference, so its distances and heights are not measured results. The floor is taken as height 0 in the motion-capture frame. Surfaces above {height_range[1]} m are ignored so they cannot hide the floor.</p>
"""
    body = layout("05_birds_eye_map.html", '<span class="layer-tag l4">Layer 4 · Environment</span>', "Bird's-eye map",
                  "Looking straight down on the merged desk scene turns 3D into a map that can be measured in metres, with unseen areas kept visible.",
                  main, footer(REPLAY_RUN, f"Cell {cell_m * 100:.0f} cm, highest surface per cell, heights {height_range[0]}–{height_range[1]} m."))
    doc = build_page("Bird's-eye map", "A top-down height and colour map of the recorded desk.", body, data, ["viewer.js"], read_web("page_birdseye.js"))
    return doc, stats
