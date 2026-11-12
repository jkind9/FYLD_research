"""Build a single-file Gaussian-splat viewer from a captured walk's saved surface.

python -B -m tools.demos.capture_scene --run <room run folder> [--every 6]
python -B -m tools.demos.capture_scene --surface <surface.ply> --session <v2 folder> --out <viewer.html>

With --run, the page shows the run's surface after the vote (voted_surface.ply, else surface.ply) with its
frame-by-frame view, and is written to <run>/pages/viewer.html. --every N keeps every Nth fused frame in the
frame-by-frame view, to keep long walks under the 20 MB page budget.
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

from sitescan.cleanup.pieces import (
    CELL_M,
    ROOM_PIECE_MIN_POINTS,
    ROOM_PIECES,
    piece_ranks,
)
from sitescan.depth.orientation import quarter_turns, turned_camera, upright
from sitescan.runs import session_path
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


SOURCE_WORDS = {"arcore_depth": "ARCore's depth", "tracked_points": "ARCore's tracked points",
                "sparse": "triangulated feature points", "dense": "plane-sweep depth"}


def run_description(frames: Path) -> dict:
    """Pose source and the scale sources used, from the room run's summary.json beside frames.npz, if any."""
    summary = frames.parent / "summary.json"
    if not summary.exists():
        return {}
    record = json.loads(summary.read_text(encoding="utf-8"))
    used = record.get("scale", {}).get("frames_per_source", {})
    return {"poseSource": record.get("pose_source", "arcore"),
            "sizedBy": [SOURCE_WORDS.get(name, name) for name in used]}


def survivors(points: np.ndarray, raw: np.ndarray, surface: np.ndarray) -> np.ndarray:
    """Which points have, as their nearest raw room point, one the shown surface kept after clean-up."""
    shown = np.isfinite(cKDTree(surface).query(raw, distance_upper_bound=1e-6)[0])
    return shown[cKDTree(raw).query(points)[1]]


def every_nth(saved, every: int) -> dict:
    """Every `every`th frame of a room timeline, each with its own points; offsets renumbered."""
    chosen = np.arange(0, len(saved["seq"]), every)
    out = {name: saved[name][chosen] for name in ("seq", "poses", "intrinsics")}
    for name, offsets_name in (("points", "point_offsets"), ("colours", "point_offsets"), ("arcore", "arcore_offsets")):
        bounds = saved[offsets_name]
        parts = [saved[name][bounds[i]:bounds[i + 1]] for i in chosen]
        out[name], out[offsets_name] = np.concatenate(parts), np.r_[0, np.cumsum([len(part) for part in parts])]
    return out


def load_timeline(frames: Path, session: Path, seconds: dict[int, float], surface: np.ndarray, every: int = 1) -> dict:
    """Room-build frames (frames.npz from the room pipeline) as steps: camera, upright photo and the points each added.

    Frames are saved before clean-up. With the run's raw_surface.ply beside frames.npz, points the clean-up removed
    from `surface` are left out. `every` keeps every Nth frame.
    """
    saved = every_nth(np.load(frames), every)
    points, colours, offsets = saved["points"], saved["colours"], saved["point_offsets"]
    raw = frames.parent / "raw_surface.ply"
    if raw.exists():
        keep = survivors(points, np.asarray(o3d.io.read_point_cloud(str(raw)).points), surface)
        points, colours, offsets = points[keep], colours[keep], np.r_[0, np.cumsum(keep)][offsets]
    views = [upright_view(session, int(seq), pose, k, longest=320)
             for seq, pose, k in zip(saved["seq"], saved["poses"], saved["intrinsics"])]
    return {"seq": saved["seq"].tolist(), "labels": [f"{seconds[int(seq)]:.1f} s" for seq in saved["seq"]],
            "poses": [v["pose"] for v in views], "fx": [v["fx"] for v in views], "fy": [v["fy"] for v in views],
            "width": [v["width"] for v in views], "height": [v["height"] for v in views],
            "photos": [v["photo"] for v in views], "cleaned": raw.exists(), "every": every,
            "points": encode_positions(points), "colours": encode_array(colours, "u8"),
            "pointOffsets": offsets.tolist(),
            "arcore": encode_positions(saved["arcore"]), "arcoreOffsets": saved["arcore_offsets"].tolist()
            } | run_description(frames)


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


def one_two_five(top: int) -> list[int]:
    """Slider stops 1, 2, 5, 10, 20, 50, ... up to the first stop of at least `top`."""
    stops = [m * 10**e for e in range(len(str(top)) + 1) for m in (1, 2, 5)]
    return stops[:next(i for i, stop in enumerate(stops) if stop >= top) + 1]


NEIGHBOUR_STOPS = (0, 5, 7, 9, 11, 13)  # filled neighbours a cell needs to extend a chain; 0 is the room build's rule


def surface_pieces(original: np.ndarray, display: np.ndarray) -> dict:
    """Per neighbour rule: each display splat's piece rank (largest first) and the piece sizes; and slider stops."""
    nearest = cKDTree(original).query(display)[1]
    pieces = []
    for neighbours in NEIGHBOUR_STOPS:
        rank, sizes = piece_ranks(original, CELL_M, neighbours)
        pieces.append({"neighbours": neighbours, "rank": encode_array(rank[nearest].astype(np.uint32), "u32"),
                       "sizes": sizes.tolist()})
    most = max(len(rule["sizes"]) for rule in pieces)
    keep, smallest = one_two_five(max(most, ROOM_PIECES)), one_two_five(max(pieces[0]["sizes"][0], ROOM_PIECE_MIN_POINTS))
    return {"pieces": pieces, "keepStops": keep, "keepAt": keep.index(ROOM_PIECES),
            "smallestStops": smallest, "smallestAt": smallest.index(ROOM_PIECE_MIN_POINTS)}


def load_scene(surface: Path, session: Path, voxel_m: float, frames: Path | None = None,
               kept: Path | None = None, every: int = 1) -> dict:
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
    timeline = {} if frames is None else {"timeline": load_timeline(frames, session, seconds, original, every)}
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
                 | ({"heightColours": encode_array(heights, "u8")} if photo else {}) | cleaned
                 | surface_pieces(original, points),
        "compare": compare,
    }


# 24 px stroke icons, drawn inline so the page fetches nothing.
ICONS = {
    "first": '<path d="M6 5v14"/><path d="M18 6l-8 6 8 6z"/>',
    "prev": '<path d="M15 6l-6 6 6 6"/>',
    "next": '<path d="M9 6l6 6-6 6"/>',
    "play": '<path d="M8 5v14l11-7z"/>',
    "pause": '<rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/>',
    "fit": '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
    "top": '<path d="M12 3v11M7 9l5 5 5-5M4 20h16"/>',
    "measure": '<path d="M3 17L17 3l4 4L7 21zM7 13l2 2M10 10l2 2M13 7l2 2"/>',
    "photo": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-8 8"/>',
    "settings": '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/>'
                '<circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.6M12 17.5v.01"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
    "report": '<path d="M6 3h9l4 4v14H6zM9 12h7M9 16h7M9 8h3"/>',
}


def icon(name: str) -> str:
    return f'<svg class="i-{name}" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def scene_page(data: dict, report: str = "") -> str:
    """The viewer: one screen with the photo beside the 3D view and a frame player below.

    Settings, help and `report` (trusted HTML, for example a trial's results) open from the top bar.
    """
    source, splat, timeline = data["source"], data["splat"], data.get("timeline")
    name = html.escape(source["session"])
    low, high = source["height_range_m"]
    photo = "heightColours" in splat
    steps_count = len(timeline["seq"]) if timeline else len(data["compare"])
    # A room run's summary says where poses and scale came from; older timelines assume ARCore.
    run = timeline if timeline and "sizedBy" in timeline else {}
    pose_source = html.escape(run.get("poseSource", "arcore"))
    sized_by = html.escape(" or ".join(run.get("sizedBy", [])) or "nothing")
    origin = "ARCore's world origin" if pose_source == "arcore" else f"the world origin of the poses ({pose_source})"
    run_line, measured, cyan = "", "ARCore's own depth for this frame", "ARCore depth"
    if run:
        run_line = f" Poses: {pose_source}. Learned depth sized by {sized_by}."
        if "ARCore" not in sized_by:
            run_line += " ARCore's depth was not used."
        measured, cyan = "the measured depth that sized it", "Measured depth"

    build_help = views = build_keys = ""
    if timeline:
        steps = f"Each step adds one frame that carried ARCore depth ({steps_count} frames)"
        if run:
            which = "one fused frame" if timeline["every"] == 1 else f"one in every {timeline['every']} fused frames"
            steps = f"Each step adds {which} ({steps_count} steps), its learned depth sized by {sized_by}"
        if timeline["cleaned"]:
            steps += ". Points the clean-up removed are left out"
        build_help = f"""
      <h3>Frame by frame</h3>
      <p>{steps}. The bars under the player show how many points each step added.
        Points sit where that frame's pose put them, before later anchor corrections.</p>
      <ul class="swatches">
        <li><i style="background:#ff8c00"></i>Orange: this frame's learned depth.</li>
        <li><i style="background:#00dcff"></i>Cyan: {measured}.</li>
        <li><i style="background:#e62828"></i>Red: the camera and its path.</li>
      </ul>"""
        views = """
    <div class="seg views" role="group" aria-label="What the 3D view shows">
      <button data-view="final" aria-pressed="true" title="The finished surface (B)">Final surface</button>
      <button data-view="build" aria-pressed="false" title="Watch the cloud grow, one frame at a time (B)">Frame by frame</button>
    </div>"""
        build_keys = "<dt><kbd>B</kbd></dt><dd>Switch between the final surface and frame by frame</dd>"

    legend = "" if not timeline else f"""
        <span class="key build-only"><i class="photo-dot"></i>Built so far</span>
        <button class="key build-only" data-layer="frame" aria-pressed="true" title="This frame's learned depth">
          <i style="background:#ff8c00"></i>This frame</button>
        <button class="key build-only" data-layer="measured" aria-pressed="true" title="Cyan: {measured}">
          <i style="background:#00dcff"></i>{cyan}</button>"""
    legend += f"""
        <button class="key" data-layer="camera" aria-pressed="true" title="Where the phone was for this photo">
          <i style="background:#e62828"></i>Camera{" and path" if timeline else ""}</button>"""

    colours = "" if not photo else """
          <div class="seg" role="group" aria-label="Splat colours">
            <button data-colour="photo" aria-pressed="true">Photo</button>
            <button data-colour="height" aria-pressed="false">Height</button>
          </div>"""
    cleanup = "" if "removed" not in splat else f"""
      <section class="final-only">
        <h4>Clean-up</h4>
        <label class="check"><input type="checkbox" id="show-removed"> Show what the clean-up removes, in red</label>
        <label class="check"><input type="checkbox" id="hide-removed"> Hide what the clean-up removes</label>
        <p class="small">{source['removed_points']:,} of {source['points']:,} surface points removed</p>
      </section>"""
    close = '<form method="dialog"><button class="tb">Close</button></form>'
    report_button = "" if not report else (
        f'<button class="tb" data-open="report-sheet" title="The trial\'s results">{icon("report")}<span>Report</span></button>')
    report_sheet = "" if not report else (
        f'<dialog class="sheet wide" id="report-sheet"><header><b>Report</b>{close}</header>'
        f'<div class="sheet-body">{report}</div></dialog>')

    body = f"""
<div class="app" id="app" data-view="final">
  <header class="bar">
    <div class="brand"><b>Your walk in 3D</b>
      <span>{name} · {source['duration_s']:.1f} s · {source['frames']:,} frames · {source['points']:,} points</span></div>
    {views}
    <div class="actions">
      <button class="tb" id="fit-scene" title="Fit the whole scene (F)">{icon("fit")}<span>Fit</span></button>
      <button class="tb" id="top-view" title="Look straight down">{icon("top")}<span>Top</span></button>
      <button class="tb final-only" id="measure" aria-pressed="false" title="Click two points to measure between them (M)">
        {icon("measure")}<span>Measure</span></button>
      <button class="tb" id="toggle-photo" aria-pressed="true" title="Show the photo beside the 3D view (P)">
        {icon("photo")}<span>Photo</span></button>
      <button class="tb" id="toggle-tools" aria-pressed="false" title="Display, cut-away and clean-up settings">
        {icon("settings")}<span>Settings</span></button>
      {report_button}
      <button class="tb" data-open="help" title="What this page shows, and the keys (?)">{icon("help")}<span>Help</span></button>
    </div>
  </header>
  <main class="work">
    <figure class="photo-pane"><img id="frame-photo" alt="The photo the phone took at this frame">
      <figcaption id="photo-caption"></figcaption></figure>
    <div class="scene-pane">
      {viewer_html()}
      <div class="legend">{legend}
      </div>
      <output class="readout" id="measure-value"></output>
      <aside class="tools" id="tools" hidden aria-label="Settings">
        <section class="final-only">
          <h4>Look</h4>
          <div class="pair">
            <div class="seg" role="group" aria-label="Scene representation">
              <button data-mode="splats" aria-pressed="true">Splats</button>
              <button data-mode="points" aria-pressed="false">Points</button>
            </div>{colours}
          </div>
          <label class="row">Splat size <input type="range" id="splat-scale" min="0.5" max="2" step="0.05" value="1"><span></span></label>
          <div class="legend-bar" style="background:linear-gradient(90deg,#440154,#31688e,#35b779,#fde725)"></div>
          <div class="legend-scale"><span>{low:.1f} m</span><span>height colours</span><span>{high:.1f} m</span></div>
        </section>
        <section>
          <h4>Cut away</h4>
          <label class="check final-only"><input type="checkbox" id="one-way" checked> Hide surfaces seen from behind</label>
          <label class="row">Ceiling <input type="range" id="ceiling" min="{low:.2f}" max="{high:.2f}" step="0.05"
            value="{high:.2f}"><output id="ceiling-value">{high:.2f} m</output></label>
          <label class="row">Floor <input type="range" id="floor" min="{low:.2f}" max="{high:.2f}" step="0.05"
            value="{low:.2f}"><output id="floor-value">{low:.2f} m</output></label>
        </section>
        <section class="final-only">
          <h4>Surface pieces</h4>
          <label class="row">Pieces kept <input type="range" id="piece-keep" min="0" max="{len(splat['keepStops']) - 1}"
            step="1" value="{splat['keepAt']}"><output id="piece-keep-value"></output></label>
          <label class="row">Min points <input type="range" id="piece-min" min="0" max="{len(splat['smallestStops']) - 1}"
            step="1" value="{splat['smallestAt']}"><output id="piece-min-value"></output></label>
          <label class="row">Neighbours <input type="range" id="piece-links" min="0" max="{len(splat['pieces']) - 1}"
            step="1" value="0"><output id="piece-links-value"></output></label>
          <p class="small"><output id="piece-shown"></output></p>
        </section>{cleanup}
        <button class="btn wide final-only" id="download-ply">Download splats (.ply)</button>
      </aside>
    </div>
  </main>
  <footer class="dock">
    <div class="transport">
      <button class="ib" id="tl-first" title="First frame (Home)" aria-label="First frame">{icon("first")}</button>
      <button class="ib" id="tl-prev" title="Previous frame (←)" aria-label="Previous frame">{icon("prev")}</button>
      <button class="ib play" id="tl-play" title="Play or pause (Space)" aria-label="Play" aria-pressed="false">
        {icon("play")}{icon("pause")}</button>
      <button class="ib" id="tl-next" title="Next frame (→)" aria-label="Next frame">{icon("next")}</button>
      <button class="speed" id="tl-speed" title="Playback speed">1×</button>
      <span class="now" id="tl-caption"></span>
      <label class="toggle" title="Look through the camera that took this photo, so the 3D view lines up with it (C)">
        <input type="checkbox" id="tl-follow">{icon("camera")}View from camera</label>
    </div>
    <div class="track" title="{"Bar height: points each step added" if timeline else "One mark per camera view"}">
      <div class="bars" id="tl-bars"></div><div class="playhead"></div>
      <input type="range" id="tl-slider" min="0" max="{steps_count - 1}" value="0" aria-label="Frame">
    </div>
    <div class="strip" id="tl-strip" aria-label="Photos, one per frame"></div>
  </footer>
  <dialog class="sheet" id="help"><header><b>About this view</b>{close}</header>
    <div class="sheet-body">
      <h3>This scene</h3>
      <p>{name}: {source['frames']:,} recorded camera frames over a {source['duration_s']:.1f} s recorded span.
        {source['points']:,} reconstructed surface points, shown as {splat['positions']['count']:,} Gaussian splats in
        {data['voxel'] * 100:.0f} cm cells.{run_line}</p>
      <p>Height uses {origin}. Dimensions have not been checked against a tape measure.</p>
      <p>The splats are built from the surface, with {"photo colours from the fused frames" if photo else "height colours"};
        photographic Gaussian training has not been run. Camera views use recorded poses; later anchor corrections can
        shift the final surface relative to a photo. The scene and photos are embedded in this file, so it works offline.</p>{build_help}
      <h3>Seeing inside</h3>
      <p>Each splat's front is the side its nearest recorded camera faced. "Hide surfaces seen from behind" removes walls
        between you and the room, and the ceiling seen from above. Ceiling and Floor hide everything above or below a height.</p>
      <h3>Measuring</h3>
      <p>Press Measure, then click two points on the surface. The distance is shown with its level and height parts.
        A click picks the front-most splat within 8 screen pixels that the current view shows.</p>
      <h3>Surface pieces</h3>
      <p>A piece is surface whose {CELL_M * 100:.0f} cm cells touch, counted in surface points. The sliders keep the
        largest pieces of at least a size. They start at the room build's rule: the {ROOM_PIECES} largest of at least
        {ROOM_PIECE_MIN_POINTS:,} points. They hide only what is shown, so on the surface after the vote they can bring
        back pieces the rule removed. "Neighbours" sets how many of a cell's 26 neighbours must be filled before it
        joins cells further on. At 0 any touching cells join, so a streak touching a wall is part of the room. Higher
        values split thin streaks off; past about 9 they start splitting real surface too.</p>
      <h3>Controls</h3>
      <dl class="keys">
        <dt>Drag</dt><dd>Rotate</dd>
        <dt>Right-drag or Shift-drag</dt><dd>Pan</dd>
        <dt>Scroll or pinch</dt><dd>Zoom</dd>
        <dt><kbd>Space</kbd></dt><dd>Play or pause</dd>
        <dt><kbd>←</kbd> <kbd>→</kbd></dt><dd>Previous or next frame; with Shift, 10 frames</dd>
        <dt><kbd>Home</kbd> <kbd>End</kbd></dt><dd>First or last frame</dd>
        <dt><kbd>C</kbd></dt><dd>View from this frame's camera</dd>{build_keys}
        <dt><kbd>P</kbd></dt><dd>Show or hide the photo</dd>
        <dt><kbd>F</kbd> <kbd>M</kbd></dt><dd>Fit the scene; measure</dd>
        <dt><kbd>Tab</kbd> to the 3D view</dt><dd>Arrow keys orbit; + and − zoom</dd>
      </dl>
    </div>
  </dialog>{report_sheet}
</div>
"""
    return build_page("FYLD · Your walk in 3D", "Interactive Gaussian splats of the Redmi reconstruction.",
                      body, data, ["viewer.js"], read_web("page_splats.js") + "\n" + read_web("page_capture.js"),
                      css=read_web("capture.css"))


def from_run(run: Path) -> tuple[Path, Path, Path, Path]:
    """Surface, recording folder, frames and page path for a room run folder (sitescan.runs layout)."""
    record = json.loads((run / "run.json").read_text(encoding="utf-8"))
    voted = run / "voted_surface.ply"
    surface = voted if voted.exists() else run / "surface.ply"
    return surface, session_path(record["recording"]), run / "frames.npz", run / "pages" / "viewer.html"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, help="a room run folder: sets --surface, --session, --frames and --out")
    parser.add_argument("--surface", type=Path)
    parser.add_argument("--session", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--voxel", type=float, default=0.06,
                        help="display cell size in metres (proposed by Claude, not owner-ruled)")
    parser.add_argument("--frames", type=Path, help="frames.npz from the room pipeline: adds the frame-by-frame view")
    parser.add_argument("--every", type=int, default=1, help="keep every Nth frame in the frame-by-frame view")
    args = parser.parse_args(argv)
    if args.run:
        args.surface, args.session, args.frames, default_out = from_run(args.run)
        args.out = args.out or default_out
    if not (args.surface and args.session and args.out):
        parser.error("give --run, or --surface, --session and --out")
    data = load_scene(args.surface, args.session, args.voxel, args.frames, every=args.every)
    size = write_page(args.out.parent, args.out.name, scene_page(data), max_bytes=20_000_000)
    print(f"{args.out.resolve()}: {data['splat']['positions']['count']:,} splats, {size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
