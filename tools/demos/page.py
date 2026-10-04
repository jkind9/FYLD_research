"""Assemble single-file demo pages: inline CSS, inline JavaScript and embedded JSON data."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent / "web"

# A page must not fetch anything: no external scripts, stylesheets, images, fonts or imports.
EXTERNAL_RESOURCE = re.compile(
    r"<script[^>]*\ssrc=|<link[^>]*\shref=[\"']https?:|<img[^>]*\ssrc=[\"']https?:|url\([\"']?https?:|@import",
    re.IGNORECASE,
)

PAGES = [
    ("00_overview.html", "Overview"),
    ("01_depth_to_3d.html", "Depth to 3D"),
    ("02_camera_tracking.html", "Camera path"),
    ("03_surface_accuracy.html", "Surface accuracy"),
    ("04_gaussian_splats.html", "Gaussian splats"),
    ("05_birds_eye_map.html", "Bird's-eye map"),
    ("06_objects_in_3d.html", "Objects"),
]


def nav_html(active: str) -> str:
    """Top navigation linking every demo page by relative file name."""
    items = []
    for file, label in PAGES:
        cls = ' class="active" aria-current="page"' if file == active else ""
        items.append(f'<a href="{file}"{cls}>{html.escape(label)}</a>')
    return '<nav class="demo-nav" aria-label="Demo pages">' + "".join(items) + "</nav>"


def layout(active: str, eyebrow: str, title: str, lede: str, main_html: str, footer: str) -> str:
    """Standard page body: navigation, heading block, content and provenance footer."""
    return (
        nav_html(active)
        + '<div class="page">'
        + f'<div class="eyebrow">{eyebrow}</div><h1>{html.escape(title)}</h1><p class="lede">{lede}</p>'
        + main_html
        + f'<div class="footer">{footer}</div></div>'
    )


def viewer_html(element_id: str = "viewer", hint: str = "Drag to rotate · right-drag or Shift-drag to pan · scroll or pinch to zoom",
                style: str = "") -> str:
    """A 3D viewer container with a canvas, a label overlay and an interaction hint."""
    extra = f' style="{style}"' if style else ""
    return (f'<div class="viewer" id="{element_id}"{extra}><canvas aria-label="Interactive 3D view"></canvas>'
            f'<div class="labels"></div><div class="hint">{html.escape(hint)}</div></div>')


def read_web(name: str) -> str:
    """Return a file from tools/demos/web."""
    return (WEB / name).read_text(encoding="utf-8")


def build_page(title: str, description: str, body_html: str, data: dict, scripts: list[str], page_js: str) -> str:
    """Return a complete HTML document that works offline from a single file."""
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    js = "\n".join(read_web(s) for s in scripts) + "\n" + page_js
    if "</script" in js.lower():
        raise ValueError("inline JavaScript must not contain a closing script tag")
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html.escape(description)}">
<title>{html.escape(title)}</title>
<style>
{read_web("style.css")}
</style>
</head>
<body>
{body_html}
<script type="application/json" id="demo-data">{payload}</script>
<script>
{js}
</script>
</body>
</html>
"""
    if EXTERNAL_RESOURCE.search(doc):
        raise ValueError(f"page '{title}' references an external resource")
    return doc


def write_page(out_dir: Path, file_name: str, doc: str, max_bytes: int) -> int:
    """Write a page and return its size; refuse pages over the size budget."""
    size = len(doc.encode("utf-8"))
    if size > max_bytes:
        raise ValueError(f"{file_name} is {size / 1e6:.1f} MB, over the {max_bytes / 1e6:.0f} MB budget")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / file_name).write_text(doc, encoding="utf-8", newline="\n")
    return size
