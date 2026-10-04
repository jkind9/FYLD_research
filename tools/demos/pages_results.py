"""Result pages: camera tracking, surface accuracy and objects in 3D."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tools.demos.geometry import backproject, to_world
from tools.demos.pack import (
    colormap,
    encode_array,
    encode_normals,
    encode_positions,
    image_data_url,
)
from tools.demos.page import build_page, layout, read_web, viewer_html
from tools.demos.pages_scene import (
    SPLAT_THICKNESS,
    SPLAT_WIDTH,
    footer,
    legend_gradient,
)
from tools.demos.sources import (
    REPLAY_RUN,
    SURFACE_FRAMES,
    SURFACE_RUN,
    TRACKING_RUN,
    TUM,
    read_depth_m,
    read_rgb,
)

ERROR_RANGE_M = (0.0, 0.032)


def _quat_pose(row: list[float]) -> np.ndarray:
    """4x4 camera-to-world from a TUM ground-truth row: t x y z qx qy qz qw."""
    tx, ty, tz, qx, qy, qz, qw = row[1:8]
    q = np.array([qw, qx, qy, qz]) / np.linalg.norm([qw, qx, qy, qz])
    w, x, y, z = q
    r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    t = np.eye(4)
    t[:3, :3], t[:3, 3] = r, [tx, ty, tz]
    return t


def _reference_poses(root: Path, timestamps: list[float]) -> list[np.ndarray]:
    rows = [[float(v) for v in line.split()] for line in
            (root / TRACKING_RUN / "input/evaluation/groundtruth.txt").read_text().splitlines() if line and not line.startswith("#")]
    stamps = np.array([r[0] for r in rows])
    return [_quat_pose(rows[int(np.argmin(np.abs(stamps - t)))]) for t in timestamps]


def camera_tracking(root: Path, tracking: dict) -> tuple[str, dict]:
    """Page 02: estimated versus motion-capture camera path for the 30-frame trial."""
    records = tracking["poses"]
    metrics = tracking["metrics"]
    est = [np.asarray(r["pose"]["T_world_camera"]) for r in records]
    ref = _reference_poses(root, [r["timestamp_s"] for r in records])
    align = ref[0] @ np.linalg.inv(est[0])
    est_aligned = [align @ t for t in est]
    expected = np.array([e["estimated_position"] for e in metrics["errors"]])
    got = np.array([t[:3, 3] for t in est_aligned])
    if np.abs(expected - got).max() > 1e-6:
        raise ValueError("re-aligned estimated path does not match the run's scored positions")
    errors_mm = [1000 * e["position_error_m"] for e in metrics["errors"]]
    timing = json.loads((root / TRACKING_RUN / "metadata/timing.json").read_text(encoding="utf-8"))
    pairs = [s for s in timing["samples"] if s["stage"] == "odometry_pairs"]
    pairs_per_s = sum(s["frames"] for s in pairs) / sum(s["elapsed_seconds"] for s in pairs)
    obs = root / TRACKING_RUN / "input/observations"
    rows = json.loads((root / TRACKING_RUN / "output/associations.json").read_text(encoding="utf-8"))["rows"]
    first, last = obs / rows[0]["rgb"], obs / rows[-1]["rgb"]
    first_rgb = read_rgb(first)
    context_cam, pix = backproject(read_depth_m(obs / rows[0]["depth"]), TUM, stride=2)
    context = to_world(context_cam, ref[0])
    data = {
        "up": [0, 0, 1], "estimated": [t.tolist() for t in est_aligned], "reference": [t.tolist() for t in ref],
        "errorsMm": errors_mm, "rmseMm": 1000 * metrics["position_rmse_m"],
        "context": encode_positions(context), "contextFocus": np.percentile(context, [5, 95], axis=0).tolist(), "contextRgb": encode_array(first_rgb[pix[:, 0], pix[:, 1]], "u8"),
        "images": {"first": image_data_url(first_rgb, size=(320, 240)), "last": image_data_url(read_rgb(last), size=(320, 240))},
    }
    span_cm = 100 * float(np.linalg.norm(got.max(0) - got.min(0)))
    stats = {"rmse_mm": 1000 * metrics["position_rmse_m"], "rel_mm": 1000 * metrics["relative_translation_rmse_m"],
             "rot_deg": float(np.degrees(metrics["relative_rotation_rmse_rad"])), "pairs_per_s": pairs_per_s, "frames": len(records)}
    main = f"""
<div class="stats">
  <div class="stat"><b>{stats['rmse_mm']:.1f} mm</b><span>typical camera-position error (root-mean-square)</span></div>
  <div class="stat"><b>{stats['rot_deg']:.2f}°</b><span>typical rotation error per step</span></div>
  <div class="stat"><b>{stats['frames']}</b><span>frames, about 1.1 seconds of video</span></div>
  <div class="stat"><b>{stats['pairs_per_s']:.2f}/s</b><span>image pairs tracked per second on a desktop CPU</span></div>
</div>
<div class="stage">
  {viewer_html()}
  <div class="panel">
    <h3>Two paths</h3>
    <p><b style="color:#f97316">Orange</b>: where our tracker thinks the camera went, from colour and depth alone.</p>
    <p><b style="color:#2dd4bf">Teal</b>: where a motion-capture system measured it. The tracker never sees this; it is only used for scoring.</p>
    <p>Both start at the same pose, because the first frame defines the origin. After that, any gap is tracking error. The whole path spans about {span_cm:.0f} cm.</p>
    <p>The coloured points are the first frame's depth, placed with the measured pose, to show where the camera was pointing.</p>
    <div class="controls"><button class="btn" id="fit">Show scene</button><button class="btn" id="zoom">Zoom to path</button></div>
  </div>
</div>
<h2>Error at each frame</h2>
<div class="panel"><svg id="chart" viewBox="0 0 640 220" role="img" aria-label="Position error per frame in millimetres" style="width:100%;height:auto"></svg></div>
<div class="figure-row">
  <figure><img id="img-first" alt="First frame"><figcaption>First frame of the trial</figcaption></figure>
  <figure><img id="img-last" alt="Last frame"><figcaption>Last frame, about 1.1 s later</figcaption></figure>
</div>
<p class="note">This is a short development run on a public indoor recording (TUM RGB-D Freiburg1 xyz). Full-length and held-out runs are prepared but not yet run, and the tracker has no drift correction. Errors grow on longer walks until a revisited place is recognised.</p>
"""
    body = layout("02_camera_tracking.html", '<span class="layer-tag l3">Layer 3 · Camera position</span>', "Where was the camera?",
                  "Every later step needs to know where the camera was for each frame. Here the tracker's answer is drawn next to the motion-capture measurement.",
                  main, footer(TRACKING_RUN, "Open3D RGB-D odometry on CPU; alignment by first pose, scale fixed at one."))
    doc = build_page("Camera path", "Estimated versus measured camera path for a 30-frame trial.", body, data, ["viewer.js"], read_web("page_tracking.js"))
    return doc, stats


def surface_accuracy(root: Path, surface: dict, reference: dict) -> tuple[str, dict]:
    """Page 03: 9-view ICL point surface coloured by distance to the reference model."""
    m = surface["metrics"]
    err = colormap(surface["distance_m"], *ERROR_RANGE_M)
    cams = []
    for fid, stages in zip(SURFACE_FRAMES, surface["stages"]):
        obs = json.loads((root / SURFACE_RUN / "input" / fid / "observation.json").read_text(encoding="utf-8"))
        t = np.asarray(stages["model_from_world"]) @ np.asarray(obs["pose"]["T_world_camera"])
        cams.append({"frame": fid, "position": t[:3, 3].tolist(), "forward": t[:3, 2].tolist()})
    data = {
        "up": [0, 1, 0], "points": encode_positions(surface["points"]), "rgb": encode_array(surface["colours"], "u8"),
        "error": encode_array(err, "u8"), "reference": encode_positions(reference["points"]),
        "referenceRgb": encode_array(reference["colours"], "u8"), "cameras": cams,
        "legend": {"lo": ERROR_RANGE_M[0] * 1000, "hi": ERROR_RANGE_M[1] * 1000, "gradient": legend_gradient("turbo")},
    }
    stats = {"mean_mm": 1000 * m["accuracy"]["mean_m"], "rmse_mm": 1000 * m["accuracy"]["rmse_m"], "max_mm": 1000 * m["accuracy"]["max_m"],
             "coverage_pct": 100 * m["reference_coverage_fraction"], "points": m["accuracy"]["points"], "shown": len(surface["points"])}
    main = f"""
<div class="stats">
  <div class="stat"><b>{stats['mean_mm']:.1f} mm</b><span>average distance from our points to the reference model</span></div>
  <div class="stat"><b>{stats['max_mm']:.1f} mm</b><span>largest distance of any point</span></div>
  <div class="stat"><b>{stats['coverage_pct']:.1f}%</b><span>of the whole room within 5 cm of a point</span></div>
  <div class="stat"><b>{stats['points'] / 1e6:.2f} M</b><span>points measured ({stats['shown']:,} shown here)</span></div>
</div>
<div class="controls">
  <div class="seg" role="group" aria-label="Point colours"><button data-colour="rgb" aria-pressed="false">Real colours</button><button data-colour="error" aria-pressed="true">Error colours</button></div>
  <div class="seg" role="group" aria-label="Reference model"><button data-ref="off" aria-pressed="true">Our points only</button><button data-ref="on" aria-pressed="false">Add reference model</button></div>
</div>
<div class="stage">
  {viewer_html()}
  <div class="panel">
    <h3>How to read this</h3>
    <p>Nine views of a synthetic living room (ICL-NUIM) were turned into 3D points using the depth and camera positions supplied with the dataset. This isolates the surface-building step from depth and tracking errors.</p>
    <p>In error colours, each point shows its distance to the room's separate reference model:</p>
    <div class="legend-bar" id="legend"></div><div class="legend-scale"><span>0 mm</span><span>{ERROR_RANGE_M[1] * 1000:.0f} mm or more</span></div>
    <p>White markers show the nine camera positions.</p>
    <p>Turn on the reference model to see how much of the room the nine views missed. Only {stats['coverage_pct']:.0f}% of it was seen.</p>
  </div>
</div>
<p class="note">Accuracy and coverage are different questions. Points that exist are close to the true surface (mean {stats['mean_mm']:.1f} mm, root-mean-square {stats['rmse_mm']:.1f} mm), but nine views see less than a quarter of the room. A real capture needs many more viewpoints, and real phone depth adds its own error on top of this.</p>
"""
    body = layout("03_surface_accuracy.html", '<span class="layer-tag l4">Layer 4 · Environment</span>', "How close is the 3D surface to the truth?",
                  "A measured result: every point is coloured by its distance to an independent reference model of the same room.",
                  main, footer(SURFACE_RUN, f"Random sample of {stats['shown']:,} of {stats['points']:,} points and {len(reference['points']):,} of {reference['total']:,} reference points."))
    doc = build_page("Surface accuracy", "Point surface of a synthetic room coloured by distance to its reference model.", body, data, ["viewer.js"], read_web("page_surface.js"))
    return doc, stats


def objects_in_3d(replay: dict, scene: dict, voxel_m: float, story: dict, cup: dict) -> tuple[str, dict]:
    """Page 06: object identities across the 60-frame replay, with a timeline and frame boxes."""
    ledger = replay["ledger"]
    track_ids = sorted(ledger["tracks"])
    frames = []
    for f in replay["frames"]:
        dets = []
        for d in f.detections:
            x1, y1, x2, y2 = d["xyxy"]
            dets.append({"box": [round(x1 / 2, 1), round(y1 / 2, 1), round(x2 / 2, 1), round(y2 / 2, 1)], "label": d["label"],
                         "id": d.get("object_id"), "assoc": d.get("association"), "conf": round(float(d["confidence"]), 2),
                         "world": None if d.get("world_position_m") is None else [round(v, 4) for v in d["world_position_m"]]})
        frames.append({"frame": f.frame_id, "pose": np.round(f.pose, 5).tolist(), "dets": dets,
                       "image": image_data_url(read_rgb(f.rgb_path), quality=70, size=(320, 240))})
    tracks = [{"id": t, "label": ledger["tracks"][t]["label"], "count": ledger["tracks"][t]["observation_count"],
               "colour": i} for i, t in enumerate(track_ids)]
    counts = ledger["counts"]
    reasons: dict[str, int] = {}
    unassigned_books = 0
    for f in replay["frames"]:
        for d in f.detections:
            if not d.get("object_id"):
                reasons[d.get("association", "unknown")] = reasons.get(d.get("association", "unknown"), 0) + 1
                unassigned_books += d["label"] == "book"
    alpha = np.where(scene["counts"] >= 4, 235, 160).astype(np.uint8)
    splat = {"positions": encode_positions(scene["positions"]), "normals": encode_normals(scene["normals"]),
             "colours": encode_array(scene["colours"], "u8"), "alpha": encode_array(alpha, "u8"),
             "tangentSigma": voxel_m * SPLAT_WIDTH, "normalSigma": voxel_m * SPLAT_THICKNESS}
    data = {"up": [0, 0, 1], "splat": splat,
            "frames": frames, "tracks": tracks, "story": story, "fy": 525.0 / 2, "imageHeight": 240}
    stats = {"detections": counts["detections"], "objects": counts["object_ids"], "unresolved": counts["unresolved"], "frames": counts["frames"]}
    main = f"""
<div class="stats">
  <div class="stat"><b>{stats['frames']}</b><span>frames of desk video, each with depth and camera pose</span></div>
  <div class="stat"><b>{stats['detections']}</b><span>detections by the YOLO26x detector</span></div>
  <div class="stat"><b>{stats['objects']}</b><span>distinct object identities kept</span></div>
  <div class="stat"><b>{cup['rms_mm']:.0f} mm</b><span>spread of the cup's 3D position over {cup['n']} sightings</span></div>
</div>
<div class="controls">
  <button class="btn" id="play">▶ Play</button>
  <label class="inline" style="flex:1;min-width:220px">Frame <input type="range" id="timeline" min="0" max="{len(frames) - 1}" value="0"></label>
  <span id="frame-label" class="mono"></span>
</div>
<div class="stage">
  {viewer_html()}
  <div class="panel">
    <h3 id="count-title">Objects so far</h3>
    <canvas id="frame-canvas" width="320" height="240" style="width:100%;border-radius:8px;border:1px solid var(--rule)"></canvas>
    <p id="frame-summary"></p>
    <div class="chips" id="chips"></div>
  </div>
</div>
<h2>The cup leaves and comes back</h2>
<p>The brief's counting problem in miniature. The cup is seen in frame {story['before']}, is out of view in frame {story['gap']}, and is back in frame {story['after']}. Because each sighting has a 3D position, the returning cup lands where the cup was before and keeps the same identity, so it is counted once.</p>
<div class="controls"><button class="btn" data-jump="before">Frame {story['before']}: cup seen</button><button class="btn" data-jump="gap">Frame {story['gap']}: out of view</button><button class="btn" data-jump="after">Frame {story['after']}: back, same identity</button></div>
<h2>Where it still goes wrong</h2>
<p>Grey markers are detections the rules could not assign: {stats['unresolved']} of {stats['detections']}.</p>
<ul>
<li>{reasons.get('unresolved_outside_gate', 0)} were more than 0.35 m from every known object of their class. A deliberately strict rule then refuses to create a second identity for a class that already has one, so these stay unassigned rather than risk a wrong merge.</li>
<li>{reasons.get('unresolved_ambiguous', 0)} were close to two known objects at once, too close to call.</li>
<li>{reasons.get('unresolved_no_position', 0)} had no usable depth, so no 3D position.</li>
<li>{reasons.get('unresolved_track_already_assigned', 0)} matched an object that another box in the same frame had already claimed.</li>
</ul>
<p>Books are the largest group ({unassigned_books}), because several books lie on the desk but only one book identity exists. A softer rule, which allows provisional identities and records possible duplicates, is the next comparison.</p>
<p class="note">Positions are points on each object's visible surface, read from depth inside its detection box, using the recording's motion-capture camera path rather than our tracker's. They move a little as the camera moves round an object, which is part of the {cup['rms_mm']:.0f} mm spread. There is no surveyed true position for these objects yet.</p>
"""
    body = layout("06_objects_in_3d.html", '<span class="layer-tag l5">Layer 5 · Objects</span>', "Counting objects that leave and come back",
                  "Each detection is placed in 3D using depth and the camera pose, then matched to the objects already found. Scrub through the 60 frames to watch the count build up.",
                  main, footer(REPLAY_RUN, f"Scene shown as {len(scene['positions']):,} Gaussian splats built from merged depth; frame images at half resolution."))
    doc = build_page("Objects in 3D", "Object detections and identities across a 60-frame desk recording.", body, data, ["viewer.js"], read_web("page_objects.js"))
    return doc, stats
