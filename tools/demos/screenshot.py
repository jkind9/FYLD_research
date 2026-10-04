"""Open every demo page in headless Chromium, save screenshots and report errors and requests.

Usage: python -B -m tools.demos.screenshot --pages demo_outputs --out <folder> [--click page.html=selector ...]
Network access is blocked; any request other than the page itself or a data URL counts as a failure.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

log = logging.getLogger("demos.screenshot")
GL_ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]


def check(pages: Path, out: Path, clicks: dict[str, list[str]], width: int, height: int, dark: bool) -> int:
    out.mkdir(parents=True, exist_ok=True)
    failures = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(args=GL_ARGS)
        context = browser.new_context(viewport={"width": width, "height": height}, color_scheme="dark" if dark else "light", offline=True)
        for page_file in sorted(pages.glob("*.html")):
            page = context.new_page()
            problems: list[str] = []
            page.on("console", lambda m, problems=problems: problems.append(f"console {m.type}: {m.text}") if m.type in ("error", "warning") else None)
            page.on("pageerror", lambda e, problems=problems: problems.append(f"page error: {e}"))
            url = page_file.resolve().as_uri()
            page.on("request", lambda r, url=url, problems=problems: None
                    if r.url.lower() == url.lower() or r.url.startswith(("data:", "blob:")) else problems.append(f"request: {r.url}"))
            page.goto(url)
            page.wait_for_timeout(2500)
            for selector in clicks.get(page_file.name, []):
                page.click(selector)
                page.wait_for_timeout(1500)
            shot = out / (page_file.stem + ("_dark" if dark else "") + ".png")
            page.screenshot(path=str(shot), full_page=True)
            status = "ok" if not problems else "PROBLEMS"
            failures += bool(problems)
            log.info("%-28s %s %s", page_file.name, status, "; ".join(problems))
            page.close()
        browser.close()
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pages", type=Path, default=Path("demo_outputs"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--click", action="append", default=[], help="page.html=css-selector, clicked before the screenshot")
    parser.add_argument("--width", type=int, default=1360)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--dark", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    clicks: dict[str, list[str]] = {}
    for item in args.click:
        name, _, selector = item.partition("=")
        clicks.setdefault(name, []).append(selector)
    sys.exit(1 if check(args.pages, args.out, clicks, args.width, args.height, args.dark) else 0)


if __name__ == "__main__":
    main()
