"""List runs under outputs/, filter them, and write outputs/index.html linking each run's pages and screenshots.

    python -B -m tools.runs                                  every run, newest first
    python -B -m tools.runs --recording redmi-20261015-0939 --tool room
    python -B -m tools.runs --where scale_sources=dense --grep jump
    python -B -m tools.runs --index                          also write outputs/index.html

A run is a folder outputs/<recording>/<tool>/<yyyymmdd-hhmm>_<label>/ holding run.json (sitescan.runs).
Folders elsewhere under outputs/ are listed as outside the convention.
"""

import argparse
import html
import json
from pathlib import Path

from sitescan.runs import OUTPUTS


def find_runs(root: Path) -> tuple[list[dict], list[Path]]:
    """Every run's record with its folder, newest first; and top folders that hold no runs in the layout."""
    found = []
    for record_path in Path(root).glob("*/*/*/run.json"):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        found.append(record | {"folder": record_path.parent})
    found.sort(key=lambda r: r["folder"].name, reverse=True)
    homes = {r["folder"].parent for r in found}  # the <recording>/<tool> folders
    outside = [p for p in sorted(Path(root).glob("*/*")) if p.is_dir() and p not in homes]
    outside += [p for p in sorted(Path(root).iterdir()) if p.is_file() and p.name != "index.html"]
    return found, outside


def matches(record: dict, recording: str | None, tool: str | None, grep: str | None, where: list[str]) -> bool:
    """Whether a run passes the filters; `where` items are setting=value, compared as text."""
    if recording and record["recording"] != recording or tool and record["tool"] != tool:
        return False
    if grep and grep not in record["label"]:
        return False
    for item in where:
        key, _, value = item.partition("=")
        setting = record.get("settings", {}).get(key)
        if setting is None or value not in (" ".join(map(str, setting)) if isinstance(setting, list) else str(setting)):
            return False
    return True


def short(value) -> str:
    """A setting as text; paths shortened to their last two parts."""
    if isinstance(value, list):
        return " ".join(map(short, value))
    text = str(value).replace("\\", "/")
    return "/".join(text.split("/")[-2:])


def changed(record: dict) -> str:
    """The options typed for this run, short."""
    return " ".join(f"{k}={short(v)}" for k, v in record.get("typed", {}).items())


def headline(numbers: dict) -> str:
    """Fused frames, surface points and map size when a run has them; otherwise its numbers as JSON."""
    parts = []
    if "fused" in numbers.get("frames", {}):
        parts.append(f"{numbers['frames']['fused']:,} frames fused")
    if "surface_points" in numbers:
        parts.append(f"{numbers['surface_points']:,} surface points")
    if "map" in numbers:
        parts.append(f"map {numbers['map']['length_m']:.2f} × {numbers['map']['width_m']:.2f} m")
    return ", ".join(parts) or (json.dumps(numbers) if numbers else "")


def index_page(found: list[dict], outside: list[Path], root: Path) -> str:
    """One local page: runs grouped by recording, with links to their pages and screenshots."""
    rows, recording = [], None
    for r in sorted(found, key=lambda r: (r["recording"], r["folder"].name), reverse=False):
        if r["recording"] != recording:
            recording = r["recording"]
            rows.append(f'<tr><th colspan="5">{html.escape(recording)}</th></tr>')
        files = sorted(r["folder"].glob("pages/*.html")) + sorted(r["folder"].glob("screens/**/*.png"))
        links = " ".join(f'<a href="{f.relative_to(root).as_posix()}">{html.escape(f.relative_to(r["folder"]).as_posix())}</a>'
                         for f in files)
        rows.append(f'<tr><td><a href="{r["folder"].relative_to(root).as_posix()}/run.json">'
                    f'{html.escape(r["folder"].relative_to(root).as_posix())}</a></td><td>{html.escape(r["status"])}</td>'
                    f'<td>{html.escape(changed(r))}</td><td>{html.escape(headline(r.get("numbers", {})))}</td>'
                    f"<td>{links}</td></tr>")
    stray = "".join(f"<li>{html.escape(p.relative_to(root).as_posix())}</li>" for p in outside)
    return f"""<!doctype html><meta charset="utf-8"><title>Runs</title>
<style>body{{font:14px system-ui;margin:16px}}td,th{{border-bottom:1px solid #ddd;padding:4px 8px;text-align:left;
vertical-align:top}}th{{background:#f3f3f3}}</style>
<h1>Runs under outputs/</h1><p>{len(found)} runs. Made by <code>python -B -m tools.runs --index</code>.</p>
<table><tr><th>Run</th><th>Status</th><th>Typed options</th><th>Numbers</th><th>Pages and screenshots</th></tr>
{"".join(rows)}</table>
{f"<h2>Outside the convention</h2><ul>{stray}</ul>" if stray else ""}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=OUTPUTS)
    parser.add_argument("--recording")
    parser.add_argument("--tool")
    parser.add_argument("--grep", help="text in the label")
    parser.add_argument("--where", action="append", default=[], help="setting=value, e.g. scale_sources=dense")
    parser.add_argument("--latest", action="store_true", help="only the newest matching run")
    parser.add_argument("--index", action="store_true", help="write <root>/index.html")
    args = parser.parse_args(argv)
    found, outside = find_runs(args.root)
    shown = [r for r in found if matches(r, args.recording, args.tool, args.grep, args.where)]
    for r in shown[:1] if args.latest else shown:
        print(f"{r['folder'].relative_to(args.root).as_posix():70s} {r['status']:9s} {changed(r)}")
    for p in outside:
        print(f"outside the convention: {p.relative_to(args.root).as_posix()}")
    if args.index:
        (args.root / "index.html").write_text(index_page(found, outside, args.root), encoding="utf-8", newline="\n")
        print(args.root / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
