"""Turn one walkthrough run's prepared data into six offline pages, in the demo page style."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from . import run_report as source
from .page import build_page, read_web, viewer_html, write_page

PAGES = [
    ("00_overview.html", "Overview"),
    ("01_depth.html", "Depth"),
    ("02_camera.html", "Camera path"),
    ("03_surface.html", "Surface"),
    ("04_map.html", "Map"),
    ("05_objects.html", "Objects"),
]
MAX_PAGE_BYTES = 40_000_000
MIN_FPS = 1.0  # owner's floor, 7 October 2026: anything slower is not worth using


def write_report(run_path: Path, output_dir: Path | None = None) -> list[Path]:
    """Write all six pages for `run_path` and return their paths."""
    run_path = Path(run_path)
    output_dir = Path(output_dir) if output_dir else run_path.with_name(run_path.name + "-report")
    run = source.load_run(run_path)
    builders = [_overview, _depth, _camera, _surface, _map, _objects]
    written = []
    for (file_name, _), builder in zip(PAGES, builders, strict=True):
        doc = builder(run, file_name)
        write_page(output_dir, file_name, doc, MAX_PAGE_BYTES)
        written.append(output_dir / file_name)
    return written


def _nav(active: str) -> str:
    links = "".join(
        f'<a href="{name}"{" class=\"active\" aria-current=\"page\"" if name == active else ""}>{html.escape(label)}</a>'
        for name, label in PAGES
    )
    return f'<nav class="demo-nav" aria-label="Run report pages">{links}</nav>'


def _page(run: dict[str, Any], active: str, tag: str, title: str, lede: str, main: str,
          data: dict[str, Any], scripts: list[str]) -> str:
    footer = (f"Run <code>{html.escape(run['path'].name)}</code>. Built from its saved files and "
              "<code>output/scores.json</code>; nothing is re-estimated.")
    body = (_nav(active) + '<div class="page">' + f'<div class="eyebrow">{tag}</div><h1>{html.escape(title)}</h1>'
            f'<p class="lede">{lede}</p>' + main + f'<div class="footer">{footer}</div></div>')
    page_js = "" if not scripts else read_web("page_run.js")
    return build_page(title, lede, body, source.json_safe({"page": active, **data}), scripts, page_js)


def _missing(what: str) -> str:
    return f'<p class="note">No {html.escape(what)} in this run, so there is nothing to show on this page.</p>'


def _fmt(value: Any, pattern: str, missing: str = "—") -> str:
    return missing if value is None else pattern.format(value)


def _overview(run: dict[str, Any], name: str) -> str:
    view = source.overview_data(run)
    rows = "".join(
        f"<tr><td>{html.escape(r['name'])}</td><td>{html.escape(r['status'])}</td>"
        f"<td>{html.escape(r.get('method') or '—')}</td><td>{_fmt(r['fps'], '{:.1f}')}</td>"
        f"<td>{html.escape(r['reason'])}</td></tr>"
        for r in view["rows"]
    )
    fps = view["processing_fps"]
    verdict = ("meets" if fps is not None and fps >= MIN_FPS else "is below") + f" the {MIN_FPS:g} frame per second floor"
    head = view["headline"]
    stats = [
        (_fmt(view["frames"], "{}"), "frames processed"),
        (_fmt(fps, "{:.2f} fps"), f"processing, one layer after another; {verdict}"),
        (_fmt(view["end_to_end_fps"], "{:.2f} fps"), "end to end, including model loading, pictures and scoring"),
        (_fmt(head.get("tracking_rmse_m"), "{:.3f} m"), "camera position error against the reference (RMSE)"),
        (_fmt(head.get("depth_abs_rel"), "{:.3f}"), "depth error against the recording's sensor (AbsRel)"),
    ]
    controls = view["controls"]
    control_note = (
        "<p class=\"note\">This run uses reference controls (" + html.escape(", ".join(f"{k}: {v}" for k, v in controls.items()))
        + "). Recorded answers entered those layers, so the run is not a measurement of those methods.</p>"
        if controls else ""
    )
    main = (
        '<div class="stats">' + "".join(f'<div class="stat"><b>{b}</b><span>{html.escape(s)}</span></div>' for b, s in stats) + "</div>"
        + control_note
        + '<h2>The six layers</h2><div class="table-wrap"><table><thead><tr><th>Layer</th><th>Status</th><th>Method</th>'
        "<th>Frames per second</th><th>Reason</th></tr></thead><tbody>" + rows + "</tbody></table></div>"
        + "<p class=\"note\">Scores: " + html.escape(", ".join(f"{k} {v}" for k, v in view["score_status"].items()) or "none requested")
        + ". Error numbers exist only where the recording has true answers: sensor depth and a measured camera path for TUM.</p>"
    )
    title = "Walkthrough run " + ("complete" if view["complete"] else "incomplete")
    return _page(run, name, '<span class="layer-tag l1">Run summary</span>', title,
                 "What each layer did on this recording, how fast, and how far its answers are from the true ones.",
                 main, {}, [])


def _depth(run: dict[str, Any], name: str) -> str:
    data = source.depth_data(run)
    tag = '<span class="layer-tag l2">Layer 2 · Depth</span>'
    if data is None:
        return _page(run, name, tag, "Depth", "Distance from the camera for every pixel.", _missing("depth output"), {}, [])
    overall = data["overall"] or {}
    stats = [
        (_fmt(overall.get("abs_rel"), "{:.3f}"), "typical relative error (AbsRel): 0.10 means 10% too near or far"),
        (_fmt(overall.get("rmse_m"), "{:.3f} m"), "root-mean-square error in metres"),
        (_fmt(overall.get("delta1"), "{:.1%}"), "pixels within 25% of the true distance"),
        (_fmt(overall.get("valid_coverage"), "{:.1%}"), "of sensor pixels that also got a predicted depth"),
    ]
    score_note = ("" if data["scoreStatus"] == "scored" else
                  f'<p class="note">Depth was not scored: {html.escape(str(data["scoreReason"]))}</p>')
    sampled = (f"Showing {len(data['frames'])} of {data['frameCount']} frames, evenly spaced."
               if len(data["frames"]) < data["frameCount"] else f"All {data['frameCount']} frames.")
    main = (
        '<div class="stats">' + "".join(f'<div class="stat"><b>{b}</b><span>{html.escape(s)}</span></div>' for b, s in stats) + "</div>"
        + score_note
        + '<div class="panel"><label class="inline">Frame <input type="range" id="frame" min="0" value="0"></label> '
        '<span id="frame-label"></span></div>'
        '<div class="figure-row">'
        '<figure><img id="img-rgb" alt="Colour frame"><figcaption>Colour frame (method input)</figcaption></figure>'
        '<figure><img id="img-predicted" alt="Predicted depth"><figcaption>Predicted depth, 0 m blue to 4 m red</figcaption></figure>'
        '<figure><img id="img-reference" alt="Sensor depth"><figcaption>Sensor depth (reference), same colours; black = no reading</figcaption></figure>'
        '<figure><img id="img-error" alt="Depth error"><figcaption>Absolute error, 0 m dark to 0.5 m bright</figcaption></figure>'
        "</div>"
        f'<p class="note">{sampled} Method: {html.escape(data["method"])}'
        + (f' (control: {html.escape(data["control"])})' if data["control"] else "") + ".</p>"
        '<h2>Error at each frame</h2><div class="panel"><svg id="chart-absrel" viewBox="0 0 640 220" role="img" '
        'aria-label="Relative depth error per frame" style="width:100%;height:auto"></svg></div>'
        '<div class="panel"><svg id="chart-rmse" viewBox="0 0 640 220" role="img" aria-label="Depth RMSE per frame in metres" '
        'style="width:100%;height:auto"></svg></div>'
        '<h2>Is the scale the same in every frame?</h2>'
        '<p class="note">Median predicted distance divided by the sensor distance, per frame: 1.00 is right, 1.30 is 30% too far. '
        "A line that moves up and down means each frame has a different size, and the same surface lands at different "
        "distances when frames are combined.</p>"
        '<div class="panel"><svg id="chart-scale" viewBox="0 0 640 220" role="img" aria-label="Scale ratio per frame" '
        'style="width:100%;height:auto"></svg></div>'
        '<div class="panel"><svg id="chart-fitted" viewBox="0 0 640 220" role="img" '
        'aria-label="Relative error left after fitting each frame&#39;s scale and shift" style="width:100%;height:auto"></svg></div>'
        '<p class="note">The second chart is the error left after fitting each frame\'s scale and shift to the sensor. '
        "It uses the sensor, so it shows what a perfect per-frame scale would leave, not what the method achieved.</p>"
        + _bands_table(data["bands"])
    )
    return _page(run, name, tag, "How far away is each pixel?",
                 "The depth layer's answer for each frame next to the recording's own depth sensor, and the error between them.",
                 main, data, ["viewer.js"])


def _bands_table(bands: dict[str, Any] | None) -> str:
    if not bands:
        return ""
    rows = "".join(
        f"<tr><td>{html.escape(name)}</td><td>{_fmt(b.get('abs_rel'), '{:.3f}')}</td><td>{_fmt(b.get('rmse_m'), '{:.3f}')}</td>"
        f"<td>{_fmt(b.get('delta1'), '{:.1%}')}</td><td>{b.get('scored_pixels', 0):,}</td></tr>"
        for name, b in bands.items()
    )
    return ('<h2>Error by true distance</h2><div class="table-wrap"><table><thead><tr><th>Sensor distance</th><th>AbsRel</th>'
            "<th>RMSE (m)</th><th>Within 25%</th><th>Pixels</th></tr></thead><tbody>" + rows + "</tbody></table></div>")


def _camera(run: dict[str, Any], name: str) -> str:
    data = source.camera_data(run)
    tag = '<span class="layer-tag l3">Layer 3 · Camera position</span>'
    if data is None:
        return _page(run, name, tag, "Camera path", "Where the camera was for each frame.", _missing("tracking output"), {}, [])
    if data["scored"]:
        stats = [
            (f"{data['rmseMm']:.1f} mm", "typical camera-position error (RMSE)"),
            (f"{data['stepRmseMm']:.1f} mm", "typical error per step between frames"),
            (f"{data['tracked'][0]} of {data['tracked'][1]}", "frame-to-frame steps tracked"),
            (str(len(data["segments"])), "separate path pieces (a lost step starts a new one)"),
        ]
        lead = '<div class="stats">' + "".join(f'<div class="stat"><b>{b}</b><span>{html.escape(s)}</span></div>' for b, s in stats) + "</div>"
        chart = ('<h2>Error at each frame</h2><div class="panel"><svg id="chart-camera" viewBox="0 0 640 220" role="img" '
                 'aria-label="Camera position error per frame in millimetres" style="width:100%;height:auto"></svg></div>'
                 f'<p class="note">Alignment: {html.escape(data["alignment"])}.</p>')
    else:
        lead = f'<p class="note">Tracking was not scored: {html.escape(str(data["reason"]))}. Only the estimated path is shown.</p>'
        chart = ""
    main = (lead + '<div class="stage">' + viewer_html() + '<div class="panel"><h3>Two paths</h3>'
            '<p><b style="color:#f97316">Orange</b>: where the tracker placed the camera.</p>'
            '<p><b style="color:#2dd4bf">Teal</b>: the measured camera path, used only for scoring.</p>'
            f'<p>Method: {html.escape(data["method"])}.</p></div></div>' + chart)
    return _page(run, name, tag, "Where was the camera?",
                 "The tracker's camera path next to the measured one, and the gap between them at every frame.",
                 main, data, ["viewer.js"])


def _surface(run: dict[str, Any], name: str) -> str:
    data = source.surface_data(run)
    tag = '<span class="layer-tag l4">Layer 4 · Surface</span>'
    if data is None:
        return _page(run, name, tag, "Surface", "The 3D points the run produced.", _missing("surface output"), {}, [])
    main = ('<div class="stage">' + viewer_html() + '<div class="panel"><h3>Observed points</h3>'
            f'<p>{data["shown"]:,} of {data["total"]:,} points, every {max(1, round(data["total"] / max(data["shown"], 1)))}th one, '
            "in the colour of the pixel they came from. White dots are camera positions.</p>"
            f'<p>Method: {html.escape(data["method"])}. There is no independent surface reference for this recording, '
            "so this page shows shape, not error.</p></div></div>" + _gap_section(data))
    return _page(run, name, tag, "What did the run see in 3D?",
                 "Every frame's depth placed in one space using the camera path.", main, data, ["viewer.js"])


def _gap_section(data: dict[str, Any]) -> str:
    """The surface-gap table and charts: is the same surface repeated along the view?"""
    if not data["gapByLag"]:
        return ""
    rows = "".join(
        f"<tr><td>{r['lag']}</td><td>{_fmt(r['medianAbsM'], '{:.3f}')}</td><td>{_fmt(r['medianSignedM'], '{:+.3f}')}</td>"
        f"<td>{r['pairs']}</td></tr>"
        for r in data["gapByLag"]
    )
    return (
        "<h2>Is the same surface repeated?</h2>"
        '<p class="note">Each frame\'s points are moved into an earlier frame\'s camera with the run\'s own camera path and '
        "compared with that frame's depth where both see a surface. With consistent depth the gap stays small however far "
        "apart the frames are. When each frame has a different scale, the gap grows with the frames' distance in time, and "
        "the 3D view shows the same surface several times. Hidden surfaces are not compared; frames in different tracking "
        "pieces are never paired.</p>"
        '<div class="table-wrap"><table><thead><tr><th>Frames apart</th><th>Median gap (m)</th>'
        "<th>Median signed gap (m), later minus earlier</th><th>Frame pairs</th></tr></thead><tbody>" + rows + "</tbody></table></div>"
        '<div class="panel"><svg id="chart-gap1" viewBox="0 0 640 220" role="img" aria-label="Surface gap to the previous frame" '
        'style="width:100%;height:auto"></svg></div>'
        '<div class="panel"><svg id="chart-gap10" viewBox="0 0 640 220" role="img" aria-label="Surface gap to the frame 10 earlier" '
        'style="width:100%;height:auto"></svg></div>'
        '<div class="panel"><svg id="chart-gapsigned10" viewBox="0 0 640 220" role="img" '
        'aria-label="Signed surface gap to the frame 10 earlier" style="width:100%;height:auto"></svg></div>'
    )


def _map(run: dict[str, Any], name: str) -> str:
    data = source.map_data(run)
    tag = '<span class="layer-tag l4">Layer 4 · Map and measurements</span>'
    if data is None:
        return _page(run, name, tag, "Map", "Top-down map and sizes.", _missing("mapping output"), {}, [])
    rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{v['value']:.3f}</td><td>{html.escape(v['units'])}</td></tr>"
        if isinstance(v, dict) and isinstance(v.get("value"), (int, float)) else
        f"<tr><td>{html.escape(k)}</td><td colspan=2>{html.escape(str(v))}</td></tr>"
        for k, v in data["measurements"].items()
    )
    figures = "".join(
        f'<figure><img src="{m["image"]}" alt="Top-down map, origin {m["origin"]}"><figcaption>Origin {m["origin"]} '
        f'({html.escape(str(m.get("plane_source")))})</figcaption></figure>'
        if m.get("image") else f'<p class="note">Origin {m["origin"]} skipped: {html.escape(str(m.get("skipped")))}</p>'
        for m in data["maps"]
    )
    main = (f'<div class="figure-row">{figures}</div><h2>Measurements</h2><div class="table-wrap"><table><thead><tr>'
            "<th>Measurement</th><th>Value</th><th>Units</th></tr></thead><tbody>" + rows + "</tbody></table></div>"
            f'<p class="note">Method: {html.escape(data["method"])}. No surveyed reference exists for this recording yet, '
            "so sizes are not checked against reality. Grey cells were never seen; they are not empty ground.</p>")
    return _page(run, name, tag, "How big is it?", "The surface seen from above, with sizes and unseen area.", main, {}, [])


def _objects(run: dict[str, Any], name: str) -> str:
    data = source.objects_data(run)
    tag = '<span class="layer-tag l5">Layer 5 · Objects</span>'
    if data is None:
        return _page(run, name, tag, "Objects", "Detected objects and their identities.", _missing("object output"), {}, [])
    tracks = "".join(
        f"<tr><td>{html.escape(str(origin.get('segment_id')))}</td><td>{html.escape(t['object_id'])}</td><td>{html.escape(t['label'])}</td>"
        f"<td>{t['observation_count']}</td><td>{html.escape(t['identity_state'])}</td></tr>"
        for origin in data["origins"] for t in origin["tracks"]
    )
    counts = ", ".join(f"origin {o.get('segment_id')}: {o['distinct_provisional_count']}" for o in data["origins"])
    main = ('<div class="panel"><label class="inline">Frame <input type="range" id="frame" min="0" value="0"></label> '
            '<span id="frame-label"></span></div><figure><img id="img-objects" alt="Detections on the frame" style="width:100%">'
            "</figure>"
            f'<p class="note">Distinct provisional objects per origin: {html.escape(counts)}. {html.escape(str(data["claim"]))}. '
            "No independent inventory exists for this recording, so counts show consistency, not accuracy.</p>"
            '<h2>Identities</h2><div class="table-wrap"><table><thead><tr><th>Origin</th><th>Object</th><th>Class</th>'
            "<th>Frames seen</th><th>State</th></tr></thead><tbody>" + tracks + "</tbody></table></div>")
    return _page(run, name, tag, "What objects are there?",
                 "Detector boxes on each frame and the provisional identities they were given.", main, data, ["viewer.js"])
