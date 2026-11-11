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
from scipy.spatial import cKDTree

from sitescan.depth.orientation import quarter_turns, turned_camera, upright
from sitescan.session import wire_v1

from .pack import (
    colormap,
    encode_array,
    encode_normals,
    encode_positions,
    image_data_url,
)
from .page import build_page, read_web, viewer_html, write_page


def upright_view(session: Path, seq: int, world_from_camera: np.ndarray, intrinsics, longest: int = 480) -> dict:
    """A recorded photo and its camera, both turned so the image's down axis is closest to world down."""
    turns = quarter_turns(world_from_camera)
    with Image.open(session / "frames" / f"{seq:06d}.jpg") as image:
        pose, k, (width, height) = turned_camera(world_from_camera, intrinsics, image.size, turns)
        rgb = upright(np.asarray(image.convert("RGB")), turns)
    scale = longest / max(width, height)
    return {"photo": image_data_url(rgb, size=(round(width * scale), round(height * scale))), "pose": pose.tolist(),
            "fx": float(k[0]), "fy": float(k[1]), "width": width, "height": height}


def face_cameras(points: np.ndarray, normals: np.ndarray, cameras: np.ndarray) -> np.ndarray:
    """Normals turned toward each point's nearest recorded camera, so a surface's front is the side the phone saw."""
    nearest = cameras[cKDTree(cameras).query(points)[1]]
    return np.where(((nearest - points) * normals).sum(1, keepdims=True) < 0, -normals, normals)


def load_timeline(frames: Path, session: Path, seconds: dict[int, float]) -> dict:
    """Room-build frames (frames.npz from the room pipeline) as steps: camera, upright photo and the points each added."""
    saved = np.load(frames)
    views = [upright_view(session, int(seq), pose, k, longest=320)
             for seq, pose, k in zip(saved["seq"], saved["poses"], saved["intrinsics"])]
    return {"seq": saved["seq"].tolist(), "labels": [f"{seconds[int(seq)]:.1f} s" for seq in saved["seq"]],
            "poses": [v["pose"] for v in views], "fx": [v["fx"] for v in views], "fy": [v["fy"] for v in views],
            "width": [v["width"] for v in views], "height": [v["height"] for v in views],
            "photos": [v["photo"] for v in views],
            "points": encode_positions(saved["points"]), "colours": encode_array(saved["colours"], "u8"),
            "pointOffsets": saved["point_offsets"].tolist(),
            "arcore": encode_positions(saved["arcore"]), "arcoreOffsets": saved["arcore_offsets"].tolist()}


def removed_cells(original: np.ndarray, kept: np.ndarray, display: np.ndarray, voxel_m: float) -> np.ndarray:
    """Display cells in which most original points are missing from `kept`, a cleaned subset of the surface.

    Cells follow Open3D's voxel_down_sample grid, which starts half a cell below the cloud's minimum.
    """
    gone = ~np.isfinite(cKDTree(kept).query(original, distance_upper_bound=1e-6)[0])
    origin = original.min(axis=0) - voxel_m / 2
    cells = np.floor((np.vstack([original, display]) - origin) / voxel_m).astype(np.int64)
    _, index = np.unique(cells, axis=0, return_inverse=True)
    index = index.ravel()
    mine, shown = index[:len(original)], index[len(original):]
    cells_seen = index.max() + 1
    total, missing = np.bincount(mine, minlength=cells_seen), np.bincount(mine, weights=gone, minlength=cells_seen)
    return missing[shown] > total[shown] / 2


def load_scene(surface: Path, session: Path, voxel_m: float, frames: Path | None = None,
               kept: Path | None = None) -> dict:
    if not np.isfinite(voxel_m) or voxel_m <= 0:
        raise ValueError("voxel spacing must be finite and positive")
    cloud = o3d.io.read_point_cloud(str(surface))
    points = np.asarray(cloud.points)
    if not len(points) or not np.isfinite(points).all():
        raise ValueError("surface must contain finite points")
    original_count, original = len(points), points.copy()
    cloud = cloud.voxel_down_sample(voxel_m)
    cloud.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=3 * voxel_m, max_nn=30))
    cloud.normalize_normals()
    points = np.asarray(cloud.points)
    low, high = float(points[:, 1].min()), float(points[:, 1].max())
    heights = colormap(points[:, 1], low, max(high, low + 1e-6), name="viridis")
    photo = cloud.has_colors()
    colours = (np.asarray(cloud.colors) * 255).round().astype(np.uint8) if photo else heights

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
        view = upright_view(session, seq, wire_v1.world_from_camera_cv(row["arcore"]["pose"]), row["arcore"]["intrinsics"])
        elapsed = (row["camera_t_ns"] - rows[0]["camera_t_ns"]) / 1e9
        compare.append({"frame": seq, "label": f"{elapsed:.1f} s", "photo": view["photo"], "pose": view["pose"],
                        "fy": view["fy"], "height": view["height"], "width": view["width"]})
    cameras = np.array([wire_v1.world_from_camera_cv(row["arcore"]["pose"])[:3, 3] for row in posed])
    normals = face_cameras(points, np.asarray(cloud.normals), cameras[np.isfinite(cameras).all(1)])
    with surface.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    seconds = {int(row["seq"]): (row["camera_t_ns"] - rows[0]["camera_t_ns"]) / 1e9 for row in rows}
    timeline = {} if frames is None else {"timeline": load_timeline(frames, session, seconds)}
    cleaned, removed_points = {}, {}
    if kept is not None:
        kept_points = np.asarray(o3d.io.read_point_cloud(str(kept)).points)
        removed = removed_cells(original, kept_points, points, voxel_m)
        cleaned = {"removed": encode_array(removed.astype(np.uint8), "u8")}
        removed_points = {"removed_points": original_count - len(kept_points), "kept_surface": kept.name}
    return timeline | {
        "up": [0, 1, 0], "voxel": voxel_m, "frameScene": True,
        "sceneName": session.name, "downloadName": f"{session.name}_gaussian_splats.ply",
        "source": {"surface": surface.name, "surface_sha256": digest, "session": session.name,
                   "points": original_count, "frames": len(rows), "height_range_m": [low, high],
                   "duration_s": (rows[-1]["camera_t_ns"] - rows[0]["camera_t_ns"]) / 1e9,
                   "method": f"surface-derived Gaussians; {'photo' if photo else 'height'} colours; "
                             "no photographic training"} | removed_points,
        "splat": {"positions": encode_positions(points), "normals": encode_normals(normals),
                  "colours": encode_array(colours, "u8"), "alpha": encode_array(np.full(len(points), 230, np.uint8), "u8"),
                  "tangentSigma": voxel_m, "normalSigma": voxel_m * 0.1}
                 | ({"heightColours": encode_array(heights, "u8")} if photo else {}) | cleaned,
        "compare": compare,
    }


def scene_page(data: dict, report: str = "") -> str:
    """The viewer page; `report` is trusted HTML shown below the scene (for example a trial's results)."""
    source, splat = data["source"], data["splat"]
    cleanup = "" if "removed" not in splat else f"""
  <div class="controls">
    <label class="inline"><input type="checkbox" id="show-removed"> Show what the clean-up removes, in red</label>
    <label class="inline"><input type="checkbox" id="hide-removed"> Hide what the clean-up removes</label>
    <span>{source['removed_points']:,} of {source['points']:,} surface points removed</span>
  </div>"""
    name = html.escape(source["session"])
    low, high = source["height_range_m"]
    timeline = data.get("timeline")
    photo = "heightColours" in splat
    colour_buttons = "" if not photo else """
    <div class="seg" role="group" aria-label="Splat colours">
      <button data-colour="photo" aria-pressed="true">Photo colours</button>
      <button data-colour="height" aria-pressed="false">Height colours</button>
    </div>"""
    timeline_button = '<button data-mode="timeline" aria-pressed="false">Frame by frame</button>' if timeline else ""
    timeline_panel = "" if not timeline else f"""
      <h3>Frame by frame</h3>
      <p>Each step adds one frame that carried ARCore depth ({len(timeline['seq'])} frames). Photo colours: points built so far.
        Orange: this frame's learned depth. Cyan: ARCore's own depth for this frame. Red: the camera and its path.
        Points sit where that frame's pose put them, before later anchor corrections.</p>
      <div class="controls">
        <button class="btn" id="tl-play">Play</button>
        <input type="range" id="tl-slider" min="0" max="{len(timeline['seq']) - 1}" value="0" style="width:160px" aria-label="Frame">
        <label class="inline"><input type="checkbox" id="tl-follow"> View from camera</label>
      </div>
      <p id="tl-caption"></p>
      <figure><img id="tl-photo" src="{timeline['photos'][0]}" alt="Upright photo of the current frame"></figure>"""
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
      {timeline_button}
    </div>
    <button class="btn" id="fit-scene">Fit scene</button>
    <button class="btn" id="top-view">Top view</button>
    <label class="inline">Splat size <input type="range" id="splat-scale" min="0.5" max="2" step="0.05" value="1" style="width:120px"></label>
    <button class="btn" id="download-ply">Download splats (.ply)</button>
  </div>
  <div class="controls">{colour_buttons}
    <label class="inline"><input type="checkbox" id="one-way" checked> Hide surfaces seen from behind</label>
    <label class="inline">Ceiling <input type="range" id="ceiling" min="{low:.2f}" max="{high:.2f}" step="0.05"
      value="{high:.2f}" style="width:120px"> <output id="ceiling-value">{high:.2f} m</output></label>
    <label class="inline">Floor <input type="range" id="floor" min="{low:.2f}" max="{high:.2f}" step="0.05"
      value="{low:.2f}" style="width:120px"> <output id="floor-value">{low:.2f} m</output></label>
    <button class="btn" id="measure" aria-pressed="false">Measure</button>
    <output id="measure-value"></output>
  </div>{cleanup}
  <div class="stage">
    {viewer_html(style="height:70vh;min-height:450px")}
    <aside class="panel">
      <h3>Height colours{" (when chosen)" if photo else ""}</h3>
      <div class="legend-bar" style="background:linear-gradient(90deg,#440154,#31688e,#35b779,#fde725)"></div>
      <div class="legend-scale"><span>{low:.1f} m</span><span>{high:.1f} m</span></div>
      <p>Height uses ARCore's world origin. Dimensions have not been checked against a tape measure.</p>
      <h3>Seeing inside</h3>
      <p>Each splat's front is the side its nearest recorded camera faced. With "Hide surfaces seen from behind",
        walls between you and the room and the ceiling seen from above disappear. The sliders hide everything above
        the ceiling height or below the floor height.</p>
      <h3>Measuring</h3>
      <p>Press Measure, then click two points on the surface. The distance is shown with its level and height parts.
        A click picks the front-most splat within 8 screen pixels that the current view shows.</p>
      <h3>Recorded camera views</h3>
      <p>Choose a time to look from that camera position. Drag to explore from there.</p>
      <div class="controls" id="compare-buttons"></div>
      <figure><img id="compare-photo" src="{data['compare'][0]['photo']}" alt="Reference photo from the recorded walk">
        <figcaption id="compare-caption">Reference photo from frame {data['compare'][0]['frame']}.</figcaption></figure>{timeline_panel}
    </aside>
  </div>{report}
  <p class="note">These are surface-derived Gaussian splats with {"photo colours from the fused frames" if photo else "height colours"}.
    Photographic Gaussian training has not been run.
    Display points are grouped into {data['voxel'] * 100:.0f} cm cells; the original surface is preserved.</p>
  <p>Drag to orbit · Shift-drag or right-drag to pan · scroll or pinch to zoom.
    With the view focused, use arrow keys to orbit and + / − to zoom.</p>
  <footer class="footer">Works offline. The scene and reference photos are embedded in this file.
    Camera bookmarks use recorded poses; later anchor corrections can shift the final surface relative to a photo.</footer>
</main>
"""
    return build_page("FYLD · Your walk in 3D", "Interactive Gaussian splats of the Redmi reconstruction.",
                      body, data, ["viewer.js"],
                      read_web("page_splats.js") + ("\n" + read_web("page_timeline.js") if timeline else ""))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--surface", type=Path, required=True)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--voxel", type=float, default=0.06,
                        help="display cell size in metres (proposed by Claude, not owner-ruled)")
    parser.add_argument("--frames", type=Path, help="frames.npz from the room pipeline: adds the frame-by-frame view")
    args = parser.parse_args()
    data = load_scene(args.surface, args.session, args.voxel, args.frames)
    size = write_page(args.out.parent, args.out.name, scene_page(data), max_bytes=20_000_000)
    print(f"{args.out.resolve()}: {data['splat']['positions']['count']:,} splats, {size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
