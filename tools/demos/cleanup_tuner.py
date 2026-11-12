"""Offline page for tuning the clean-up by hand: the raw fused room, with every clean-up stage on sliders.

python -B -m tools.demos.cleanup_tuner --attributes <research.experiments.surface_cleanup.cleanup_attributes folder> --session <v2 session> \
    --out <page.html> --views 65 420

The page runs each stage in the browser, in the order listed, on the points the earlier stages kept. It embeds the
walk's photos, so it stays local.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

import numpy as np
import open3d as o3d

from .cleanup_scene import focus_cameras
from .pack import encode_array, encode_normals, encode_positions
from .page import build_page, read_web, viewer_html, write_page

STAGES = [
    {"id": "vote", "label": "Visibility vote",
     "description": "Removes surface that frames saw straight through to something farther away."},
    {"id": "seen", "label": "Seen by enough frames",
     "description": "Removes surface that only a few frames measured at its depth."},
    {"id": "spots", "label": "Spots rule",
     "description": "Removes far surface that only one standing spot measured; frames from one spot share one guess "
                    "at the size of far depth."},
    {"id": "sor", "label": "Statistical outliers",
     "description": "Removes points far from their neighbours compared with the rest of the room."},
    {"id": "radius", "label": "Radius outliers",
     "description": "Removes points with too few kept neighbours close by."},
    {"id": "chain", "label": "Chain linking",
     "description": "Links kept points into chains (pieces) through neighbours closer than the link distance, then "
                    "removes small pieces and points that touch no chain."},
    {"id": "display", "label": "Display only",
     "description": "These change what is drawn, not what is removed."},
]

# "value" is the setting the trials used, so ticking a stage reproduces them; "log" sliders move in powers of ten.
PARAMS = [
    {"id": "voteMax", "stage": "vote", "label": "Maximum see-through share", "min": 0.0, "max": 1.0, "step": 0.05,
     "value": 0.5, "unit": "",
     "description": "Frames that measured a point at its depth support it; frames that saw through it to something "
                    "farther count against it. Each frame's vote weighs 1/depth², so a frame 1 m away counts 16 "
                    "times one 4 m away. Points whose share of see-through votes is above this are removed. 0.5 is "
                    "the trials' vote (support must at least equal see-through); lower removes more. See-through "
                    "evidence reaches 8 m."},
    {"id": "seenMin", "stage": "seen", "label": "Minimum frames that measured the point", "min": 1, "max": 20,
     "step": 1, "value": 3, "unit": "frames",
     "description": "Removes points fewer than this many frames measured at their depth (within the larger of 8 cm "
                    "and 5%). Real surface seen only briefly, such as the room's edges, goes too. Open3D's default "
                    "extraction threshold is 3."},
    {"id": "spotAngle", "stage": "spots", "label": "Minimum angle between views", "min": 0.5, "max": 20.0,
     "step": 0.5, "value": 3.0, "unit": "°",
     "description": "Surface that no frame measured nearer than the trusted distance needs two more frames that "
                    "measured it at the same depth from rays at least this many degrees from the first frame's ray. "
                    "Frames from one standing spot see a point at almost the same angle, so they do not count. "
                    "COLMAP uses 3°."},
    {"id": "spotNear", "stage": "spots", "label": "Trusted measuring distance", "min": 0.5, "max": 4.0, "step": 0.1,
     "value": 2.5, "unit": "m",
     "description": "Surface that any frame measured nearer than this is kept without the angle test. ARCore depth, "
                    "which sets the size of the learned depth, rarely reaches past 2.5 m."},
    {"id": "sorRatio", "stage": "sor", "label": "Allowed spread", "min": 0.2, "max": 5.0, "step": 0.1, "value": 2.0,
     "unit": "std",
     "description": "Each point's mean distance to its 20 nearest neighbours is compared with the mean and spread of "
                    "that distance over the whole raw room. Points farther than the mean plus this many standard "
                    "deviations are removed. Open3D's tutorial uses 2.0. The distances come from the raw room and "
                    "are not recomputed after earlier stages."},
    {"id": "radiusCm", "stage": "radius", "label": "Search radius", "min": 1.0, "max": 15.0, "step": 0.5,
     "value": 5.0, "unit": "cm",
     "description": "The size of the neighbourhood counted by the next slider. Open3D's tutorial uses 5 cm. The "
                    "fused surface has a point about every 2 cm."},
    {"id": "radiusMin", "stage": "radius", "label": "Minimum neighbours", "min": 1, "max": 60, "step": 1,
     "value": 16, "unit": "points",
     "description": "Points with fewer than this many other kept points inside the search radius are removed. "
                    "Open3D's tutorial uses 16 in 5 cm; a flat 5 cm disc of 2 cm-spaced surface holds about 20."},
    {"id": "linkCm", "stage": "chain", "label": "Link distance", "min": 1.0, "max": 10.0, "step": 0.25,
     "value": 5.0, "unit": "cm",
     "description": "Two kept points closer than this can be neighbouring links in one chain. Smaller values break "
                    "chains at smaller gaps. The fused surface has a point about every 2 cm, so values under about "
                    "2.5 cm start splitting real surfaces. The trials used 5 cm and 3 cm."},
    {"id": "linkMinNeighbours", "stage": "chain", "label": "Neighbours needed to extend a chain", "min": 1,
     "max": 40, "step": 1, "value": 10, "unit": "points",
     "description": "A point passes the chain on only if at least this many points, itself included, lie within the "
                    "link distance (DBSCAN's min_points; the trials used 10). 1 is plain chain linking. Higher values "
                    "stop chains running through thin, sparse bridges such as a sheet of stray edge points. A point "
                    "that touches a chain but is too sparse to extend it still joins it; a point touching no chain "
                    "is removed."},
    {"id": "linkNormalDeg", "stage": "chain", "label": "Maximum normal difference for a link", "min": 5,
     "max": 180, "step": 5, "value": 180, "unit": "°",
     "description": "Two neighbours link only if their surface directions differ by less than this. 90 or more links "
                    "any neighbours. PCL's conditional clustering example uses 30°, which stops a chain turning a "
                    "sharp corner, such as from a wall onto a sheet of stray points, but also separates walls from "
                    "the floor."},
    {"id": "pieceMin", "stage": "chain", "label": "Minimum piece size", "min": 1, "max": 100000, "step": 0.05,
     "value": 1000, "unit": "points", "log": True,
     "description": "Pieces (whole chains) with fewer points than this are removed. 1,000 points is about 0.4 m² of "
                    "surface at 2 cm spacing; the trials used 1,000."},
    {"id": "pieceKeep", "stage": "chain", "label": "Keep only the largest pieces", "min": 1, "max": 10000,
     "step": 0.05, "value": 10000, "unit": "pieces", "log": True,
     "description": "After the size test, keep at most this many pieces, largest first, and remove the rest. 2DGS "
                    "keeps the 1,000 largest when it cleans meshes made from Gaussians. 1 keeps only the biggest "
                    "piece."},
    {"id": "heightMax", "stage": "display", "label": "Hide above height", "min": 0.0, "max": 1.0, "step": 0.05,
     "value": 1.0, "unit": "m",
     "description": "Hides everything higher than this, such as the ceiling, so the room can be seen from above. "
                    "Heights run from the lowest point of the room."},
    {"id": "splatScale", "stage": "display", "label": "Splat size", "min": 0.3, "max": 3.0, "step": 0.1,
     "value": 1.0, "unit": "×",
     "description": "Scales how large each drawn splat is. Smaller splats show gaps and stray points more clearly; "
                    "larger ones look more solid."},
]
FUSION_VOXEL_M = 0.02  # sitescan.fusion fuses at 2 cm; splats are that wide


def tuner_data(folder: Path, session: Path, views: list[int]) -> dict:
    """Raw points with photo colours and normals, each stage's per-point evidence, and camera bookmarks."""
    cloud = o3d.io.read_point_cloud(str(folder / "raw.ply"))
    cloud.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=3 * FUSION_VOXEL_M, max_nn=30))
    points = np.asarray(cloud.points)
    a = np.load(folder / "attributes.npz")
    low, high = float(points[:, 1].min()), float(points[:, 1].max())
    params = [p | {"max": round(high - low, 2), "value": round(high - low, 2)} if p["id"] == "heightMax" else p
              for p in PARAMS]
    return {
        "up": [0, 1, 0], "sceneName": session.name, "lowest": low, "splatSigma": [FUSION_VOXEL_M, 0.1 * FUSION_VOXEL_M],
        "positions": encode_positions(points),
        "colours": encode_array((np.asarray(cloud.colors) * 255).round().astype(np.uint8), "u8"),
        "normals": encode_normals(np.asarray(cloud.normals)),
        "seen": encode_array(np.minimum(a["seen"], 255).astype(np.uint8), "u8"),
        "seeThrough": encode_array(np.rint(a["see_through"] * 255).astype(np.uint8), "u8"),
        # unmeasured points get the largest value, so no trusted distance keeps them
        "nearestMm": encode_array(np.rint(np.minimum(a["nearest_m"] * 1000, 65535)).astype(np.uint16), "u16"),
        "angleTenths": encode_array(np.rint(np.minimum(a["second_angle_deg"] * 10, 255)).astype(np.uint8), "u8"),
        "knnTenthMm": encode_array(np.rint(np.minimum(a["knn_mean_m"] * 1e4, 65535)).astype(np.uint16), "u16"),
        "compare": focus_cameras(session, views), "stages": STAGES, "params": params,
    }


def tuner_page(data: dict) -> str:
    n = data["positions"]["count"]
    body = f"""<style>
  .tuner-layout {{ display: grid; grid-template-columns: minmax(0, 1fr) 400px; gap: 16px; align-items: start; }}
  .tuner-layout .viewer {{ height: 78vh; }}
  #tuner-controls {{ max-height: 78vh; overflow-y: auto; padding-right: 6px; }}
  .tuner-stage {{ border: 1px solid var(--rule); border-radius: var(--radius); padding: 8px 12px; margin: 0 0 10px; }}
  .tuner-stage legend {{ font-weight: 600; padding: 0 4px; }}
  .tuner-stage p, .param p {{ margin: 2px 0 6px; font-size: .82rem; color: var(--ink-2); }}
  .param {{ margin: 8px 0 10px; }}
  .param label {{ display: flex; justify-content: space-between; gap: 8px; font-size: .9rem; }}
  .param output {{ font-family: var(--mono); }}
  .param input[type=range] {{ width: 100%; }}
  .tuner-stage.off .param {{ opacity: .45; }}
  .btn-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }}
  #stats {{ font-family: var(--mono); font-size: .82rem; white-space: pre-wrap; }}
  #settings {{ width: 100%; height: 9em; font-family: var(--mono); font-size: .8rem; }}
  @media (max-width: 900px) {{ .tuner-layout {{ grid-template-columns: 1fr; }} #tuner-controls {{ max-height: none; }} }}
</style>
<div class="page" style="max-width: 1500px">
  <div class="eyebrow">Clean-up tuner · {html.escape(data["sceneName"])}</div>
  <h1>Tune the clean-up on the raw room</h1>
  <p class="lede">The room as fused, before any clean-up: {n:,} points. Tick a stage to switch it on; release a
    slider to recompute. Stages run top to bottom, each on the points the earlier ones kept. Ticking a stage starts it
    at the setting the trials used.</p>
  <div class="tuner-layout">
    <div>
      {viewer_html()}
      <div class="btn-row" id="views"></div>
      <div class="btn-row">
        <label><input type="checkbox" id="show-removed"> Show removed points, coloured by the stage that removed
          them</label>
        <label><input type="checkbox" id="as-points"> Draw as points (faster)</label>
      </div>
      <div id="legend" class="btn-row"></div>
      <div id="stats">Loading…</div>
    </div>
    <aside id="tuner-controls" aria-label="Clean-up settings"></aside>
  </div>
  <h2>Current settings</h2>
  <p>Copy these to report a setting that cleans the room well.</p>
  <textarea id="settings" readonly></textarea>
  <p class="note">Built by tools/demos/cleanup_tuner.py from research/experiments/surface_cleanup/cleanup_attributes.py. Everything runs in this
    page; nothing is fetched. Background: research/surface_denoising/README.md.</p>
</div>"""
    return build_page("Clean-up tuner", "The raw fused room with every clean-up stage on sliders.", body, data,
                      ["viewer.js"], read_web("page_tuner.js"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--attributes", type=Path, required=True, help="research.experiments.surface_cleanup.cleanup_attributes output folder")
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--views", type=int, nargs="*", default=[], help="recorded frames to add as camera bookmarks")
    args = parser.parse_args()
    data = tuner_data(args.attributes, args.session, args.views)
    size = write_page(args.out.parent, args.out.name, tuner_page(data), max_bytes=40_000_000)
    print(f"{args.out.resolve()}: {data['positions']['count']:,} points, {size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
