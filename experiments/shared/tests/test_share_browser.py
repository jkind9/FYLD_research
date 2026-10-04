"""A recipient receives only HTML; geometry and previews remain usable offline."""

import shutil
from pathlib import Path

import pytest

from experiments.shared.share import export_share
from experiments.shared.tests.test_share import make_source


def test_moved_viewer_images_and_controls_without_network(tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if not edge.exists():
        pytest.skip("browser verification requires local Edge")
    source = tmp_path / "source"
    make_source(source)
    export_share(source, tmp_path / "export.html")
    moved = tmp_path / "recipient" / "viewer.html"
    moved.parent.mkdir()
    shutil.copyfile(tmp_path / "export.html", moved)
    # The recipient cannot resolve any original source file.
    source.rename(tmp_path / "unavailable-original")
    with sync.sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=str(edge),
            headless=True,
            args=["--disable-gpu", "--disable-webgl"],
        )
        context = browser.new_context(offline=True)
        page = context.new_page()
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                external.append(request.url) if request.url != moved.as_uri() else None
            ),
        )
        page.goto(moved.as_uri())
        pixels = lambda: page.locator("#scene").evaluate("c => c.toDataURL()")
        initial = pixels()
        for expected in ("0", "1"):
            page.locator("#previous" if expected == "0" else "#next").click()
            assert f"Frame {expected}" in page.locator("#details").inner_text()
            page.wait_for_function(
                "Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)"
            )
            assert page.locator("#sources img").count() == 3
        page.locator("#scene").focus()
        page.keyboard.press("ArrowRight")
        assert pixels() != initial
        page.locator("#reset").click()
        assert pixels() == initial
        box = page.locator("#scene").bounding_box()
        x, y = box["x"] + 100, box["y"] + 100
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x + 80, y + 40)
        page.mouse.up()
        assert pixels() != initial
        before_zoom = pixels()
        page.mouse.wheel(0, -200)
        page.wait_for_function("true")
        page.wait_for_timeout(100)
        assert pixels() != before_zoom
        before_reference = pixels()
        page.locator("#reference").check()
        assert pixels() != before_reference
        page.locator("#reset").click()
        page.locator("#reference").uncheck()
        assert pixels() == initial
        assert errors == [] and external == []
        browser.close()
