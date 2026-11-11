"""One offline page for a clean-up trial: the room before clean-up, what the visibility vote removes, and the scores.

python -B -m tools.demos.cleanup_scene --trial <experiments.surface_cleanup.denoise_trial folder> --session <v2 session> --out <viewer.html>

The page embeds the walk's photos, so it stays local.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from sitescan.session import wire_v1

from .capture_scene import load_scene, scene_page, upright_view
from .page import write_page

LABELS = {
    "baseline": "Before clean-up (room_build rules)",
    "masks": "Edge and side-on masks",
    "near_first": "Near-first weights",
    "vote": "Visibility vote (evidence under 4 m)",
    "vote_far": "Visibility vote (evidence to 8 m)",
    "sor": "Statistical outlier removal",
    "radius": "Radius outlier removal",
    "clusters": "Floating-piece removal, 5 cm join",
    "clusters_3cm": "Floating-piece removal, 3 cm join",
    "vote_far_clusters_3cm": "Vote (8 m), then floating pieces (3 cm)",
    "tracked_sizing": "Tracked-point size in every cell without ARCore depth",
    "far_sizing": "Tracked-point size beyond 2.5 m only",
    "far_sizing_vote": "Tracked-point size beyond 2.5 m, then the vote",
    "far_sizing_vote_far": "Tracked-point size beyond 2.5 m, then the vote (8 m)",
    "seen_3": "Kept only where seen by 3 frames",
    "seen_5": "Kept only where seen by 5 frames",
    "vote_far_seen_3_clusters_3cm": "Vote (8 m), seen by 3, floating pieces (3 cm)",
    "wide": "Far surface needs views from 2 more spots (3 degrees)",
    "wide_6deg": "Far surface needs views from 2 more spots (6 degrees)",
    "wide_2m": "Spots rule, with one-spot depth trusted only under 2.0 m",
    "wide_pieces": "Spots rule, then mostly-unsupported pieces removed",
    "vote_far_wide": "Vote (8 m), then the spots rule",
    "vote_far_wide_pieces": "Vote (8 m), spots rule, mostly-unsupported pieces removed",
}
HEADERS = ("Variant", "Points", "Floating points", "Blocked, door views", "Blocked, stair views",
           "Blocked, under 2.5 m", "Blocked, 2.5 m and beyond", "ARCore depth covered",
           "Points over 10 cm below the floor", "Door tracked points with surface within 10 cm",
           "Stair tracked points with surface within 10 cm", "Behind, door views", "Behind, stair views")


def results_table(results: dict) -> str:
    """The trial's variants as an HTML table, in run order."""
    rows = []
    for name, v in results["variants"].items():
        cells = (LABELS.get(name, name), f"{v['surface_points']:,}", f"{v['floating_points']:,}",
                 f"{v['blocked_share_door_frame_65']:.1%}", f"{v['blocked_share_stairs_frame_420']:.1%}",
                 f"{v['blocked_sight_line_share_from_0.0_m']:.1%}", f"{v['blocked_sight_line_share_from_2.5_m']:.1%}",
                 f"{v['arcore_depth_within_5cm']:.1%}", f"{v['below_floor_10cm_points']:,}",
                 *(f"{v[key]:.1%}" if key in v else "not measured"
                   for key in ("within_10cm_door_frame_65", "within_10cm_stairs_frame_420", "behind_share_door_frame_65",
                               "behind_share_stairs_frame_420")))
        rows.append("<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in cells) + "</tr>")
    head = "<tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in HEADERS) + "</tr>"
    return f'<div class="table-wrap"><table>{head}{"".join(rows)}</table></div>'


def focus_cameras(session: Path, seqs: list[int]) -> list[dict]:
    """Camera bookmarks for chosen recorded frames, such as the door and stair views the trial scores."""
    rows = [json.loads(line) for line in (session / "frames.jsonl").read_text(encoding="utf-8").splitlines()]
    poses = {row["seq"]: row["arcore"] for row in rows if row.get("arcore") and row["arcore"].get("pose") is not None}
    cameras = []
    for seq in seqs:
        view = upright_view(session, seq, wire_v1.world_from_camera_cv(poses[seq]["pose"]), poses[seq]["intrinsics"])
        cameras.append({"frame": seq, "label": f"Frame {seq}", "photo": view["photo"], "pose": view["pose"],
                        "fy": view["fy"], "height": view["height"], "width": view["width"]})
    return cameras


def report(results: dict, kept: str) -> str:
    base, chosen = results["variants"]["baseline"], results["variants"][kept]
    return f"""
  <section>
    <h2>Clean-up trial on this walk (Tasks120, 122 and 124)</h2>
    <p>The scene above is the room fused under <code>room_build</code>'s rules. "Show what the clean-up removes"
      paints red what "{html.escape(LABELS.get(kept, kept))}" deletes; "Hide what the clean-up removes" shows the
      room after it. It removed {base['surface_points'] - chosen['surface_points']:,} of {base['surface_points']:,}
      points.</p>
    <p><b>Floating points</b>: points in pieces under about 0.4 m² that touch no other surface within 5 cm.
      <b>Blocked</b>: ARCore saw each of its tracked points from the camera, so the line between them must be empty.
      This is the share of points along those lines that still have surface within 4 cm; door and stair views use
      the frames within about 1 s of frames 65 and 420. Lower is better. <b>Within 10 cm</b>: the share of those
      views' tracked points that still have surface within 10 cm; higher means less real surface was deleted.
      <b>Behind</b>: the same count from just past each tracked point to 1 m past it, where an echo copy behind the
      wall would sit; a room seen through an open door also counts there, so it never reaches zero.
      Tracked points used for sizing are never used for scoring.</p>
    <p><b>Spots rule</b>: frames taken from one standing spot share one guess at the size of far depth, so they agree
      with each other even when wrong. Surface further than 2.5 m from every camera that measured it is kept only if
      two more cameras, whose view of it differs by at least 3 degrees from the first, measured it at the same depth
      (COLMAP's geometric filter). <b>Mostly-unsupported pieces</b>: neighbouring points within 3 cm with normals
      under 30 degrees apart form one piece (PCL's conditional clustering); a piece is removed whole when most of its
      points fail the spots rule.</p>
    {results_table(results)}
    <p class="note">Tracked points are ARCore's own triangulation, not ground truth. One walk; settings not tuned.
      Everything ran on the CPU. Details: research/surface_denoising/README.md.</p>
  </section>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trial", type=Path, required=True, help="experiments.surface_cleanup.denoise_trial output folder")
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--voxel", type=float, default=0.03, help="display cell size in metres (Task115 used 3 cm)")
    parser.add_argument("--kept", default="vote", help="variant whose removals are shown; it must only remove points")
    parser.add_argument("--views", type=int, nargs="*", default=[], help="recorded frames to add as camera bookmarks")
    args = parser.parse_args()
    results = json.loads((args.trial / "results.json").read_text(encoding="utf-8"))
    data = load_scene(args.trial / "baseline.ply", args.session, args.voxel, kept=args.trial / f"{args.kept}.ply")
    data["compare"] += focus_cameras(args.session, args.views)
    size = write_page(args.out.parent, args.out.name, scene_page(data, report(results, args.kept)),
                      max_bytes=20_000_000)
    print(f"{args.out.resolve()}: {data['splat']['positions']['count']:,} splats, {size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
