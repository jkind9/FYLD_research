"""Build a single-file Gaussian-splat viewer from a captured walk's saved surface.

python -B -m tools.demos.capture_scene --surface <surface.ply> --session <v2 folder> --out <viewer.html>
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

import numpy as np
import open3d as o3d
from PIL import Image

from src.live.stream import session_v1

from .pack import (
    colormap,
    encode_array,
    encode_normals,
    encode_positions,
    image_data_url,
)
from .page import build_page, read_web, viewer_html, write_page


def load_scene(surface: Path, session: Path, voxel_m: float) -> dict:
    if not np.isfinite(voxel_m) or voxel_m <= 0:
        raise ValueError("voxel spacing must be finite and positive")
    cloud = o3d.io.read_point_cloud(str(surface))
    points = np.asarray(cloud.points)
    if not len(points) or not np.isfinite(points).all():
        raise ValueError("surface must contain finite points")
    original_count = len(points)
    cloud = cloud.voxel_down_sample(voxel_m)
    cloud.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=3 * voxel_m, max_nn=30))
    cloud.normalize_normals()
    points = np.asarray(cloud.points)
    low, high = float(points[:, 1].min()), float(points[:, 1].max())
    colours = colormap(points[:, 1], low, max(high, low + 1e-6), name="viridis")

    meta = json.loads((session / "session.json").read_text(encoding="utf-8"))
    if meta.get("version") != 2:
        raise ValueError("the capture viewer requires a v2 session")
    rows = [json.loads(line) for line in (session / "frames.jsonl").read_text(encoding="utf-8").splitlines()]
    if not np.isfinite([row["camera_t_ns"] for row in rows]).all():
        raise ValueError("camera timestamps must be finite")
    posed = [row for row in rows if row.get("arcore") and row["arcore"].get("pose") is not None]
    if not posed:
        raise ValueError("session has no posed images for camera bookmarks")
    compare = []
    for index in np.linspace(0, len(posed) - 1, min(8, len(posed)), dtype=int):
        row = posed[index]
        if not np.isfinite(row["arcore"]["pose"]).all() or not np.isfinite(row["arcore"]["intrinsics"]).all():
            raise ValueError("bookmark pose and intrinsics must be finite")
        seq = int(row["seq"])
        with Image.open(session / "frames" / f"{seq:06d}.jpg") as image:
            width, height = image.size
            photo = image_data_url(np.asarray(image.convert("RGB")), size=(480, 360))
        elapsed = (row["camera_t_ns"] - rows[0]["camera_t_ns"]) / 1e9
        compare.append({"frame": seq, "label": f"{elapsed:.1f} s", "photo": photo,
                        "pose": session_v1.world_from_camera_cv(row["arcore"]["pose"]).tolist(),
                        "fy": row["arcore"]["intrinsics"][1], "height": height, "width": width})
    with surface.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "up": [0, 1, 0], "voxel": voxel_m, "frameScene": True,
        "sceneName": session.name, "downloadName": f"{session.name}_gaussian_splats.ply",
        "source": {"surface": surface.name, "surface_sha256": digest, "session": session.name,
                   "points": original_count, "frames": len(rows), "height_range_m": [low, high],
                   "duration_s": (rows[-1]["camera_t_ns"] - rows[0]["camera_t_ns"]) / 1e9,
                   "method": "surface-derived Gaussians; height colours; no photographic training"},
        "splat": {"positions": encode_positions(points), "normals": encode_normals(np.asarray(cloud.normals)),
                  "colours": encode_array(colours, "u8"), "alpha": encode_array(np.full(len(points), 230, np.uint8), "u8"),
                  "tangentSigma": voxel_m, "normalSigma": voxel_m * 0.1},
        "compare": compare,
    }


def scene_page(data: dict) -> str:
    source, splat = data["source"], data["splat"]
    name = html.escape(source["session"])
    low, high = source["height_range_m"]
    body = f"""
<main class="page">
  <div class="eyebrow">FYLD · Captured scene</div>
  <h1>Your walk in 3D</h1>
  <p class="lede">Explore the reconstructed surfaces from {name}.</p>
  <div class="stats">
    <div class="stat"><b>{source['points']:,}</b><span>reconstructed surface points</span></div>
    <div class="stat"><b>{splat['positions']['count']:,}</b><span>displayed Gaussian splats</span></div>
    <div class="stat"><b>{source['frames']:,}</b><span>recorded camera frames</span></div>
    <div class="stat"><b>{source['duration_s']:.1f} s</b><span>recorded span</span></div>
  </div>
  <div class="controls">
    <div class="seg" role="group" aria-label="Scene representation">
      <button data-mode="splats" aria-pressed="true">Gaussian splats</button>
      <button data-mode="points" aria-pressed="false">Points</button>
    </div>
    <button class="btn" id="fit-scene">Fit scene</button>
    <button class="btn" id="top-view">Top view</button>
    <label class="inline">Splat size <input type="range" id="splat-scale" min="0.5" max="2" step="0.05" value="1" style="width:120px"></label>
    <button class="btn" id="download-ply">Download splats (.ply)</button>
  </div>
  <div class="stage">
    {viewer_html(style="height:70vh;min-height:450px")}
    <aside class="panel">
      <h3>Height colours</h3>
      <div class="legend-bar" style="background:linear-gradient(90deg,#440154,#31688e,#35b779,#fde725)"></div>
      <div class="legend-scale"><span>{low:.1f} m</span><span>{high:.1f} m</span></div>
      <p>Height uses ARCore's world origin. Dimensions have not been checked against a tape measure.</p>
      <h3>Recorded camera views</h3>
      <p>Choose a time to look from that camera position. Drag to explore from there.</p>
      <div class="controls" id="compare-buttons"></div>
      <figure><img id="compare-photo" src="{data['compare'][0]['photo']}" alt="Reference photo from the recorded walk">
        <figcaption id="compare-caption">Reference photo from frame {data['compare'][0]['frame']}.</figcaption></figure>
    </aside>
  </div>
  <p class="note">These are surface-derived Gaussian splats with height colours. Photographic Gaussian training has not been run.
    Display points are grouped into {data['voxel'] * 100:.0f} cm cells; the original surface is preserved.</p>
  <p>Drag to orbit · Shift-drag or right-drag to pan · scroll or pinch to zoom.
    With the view focused, use arrow keys to orbit and + / − to zoom.</p>
  <footer class="footer">Works offline. The scene and reference photos are embedded in this file.
    Camera bookmarks use recorded poses; later anchor corrections can shift the final surface relative to a photo.</footer>
</main>
"""
    return build_page("FYLD · Your walk in 3D", "Interactive Gaussian splats of the Redmi reconstruction.",
                      body, data, ["viewer.js"], read_web("page_splats.js"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--surface", type=Path, required=True)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--voxel", type=float, default=0.06,
                        help="display cell size in metres (proposed by Claude, not owner-ruled)")
    args = parser.parse_args()
    data = load_scene(args.surface, args.session, args.voxel)
    size = write_page(args.out.parent, args.out.name, scene_page(data), max_bytes=20_000_000)
    print(f"{args.out.resolve()}: {data['splat']['positions']['count']:,} splats, {size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
