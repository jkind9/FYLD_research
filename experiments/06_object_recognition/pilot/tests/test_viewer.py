"""Offline browser check: marked coordinates and camera/world switching agree."""

import importlib
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

report = importlib.import_module("experiments.06_object_recognition.pilot.report")


def test_offline_marked_cloud_rotates_and_switches_coordinate_frames(tmp_path):
    from playwright.sync_api import sync_playwright

    edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if not edge.exists():
        pytest.skip("Local Edge is required for the viewer check")
    image = tmp_path / "rgb.png"
    Image.new("RGB", (40, 30), "white").save(image)
    camera = np.array([[0.0, 0.0, 1.0], [0.2, 0.0, 1.0], [0.0, 0.2, 1.0]])
    world = camera + [1, 2, 3]
    locations = [
        {
            "detection_index": 0,
            "status": "located",
            "box_median": None,
            "centre_sample": {"world_m": [1, 2, 4], "camera_m": [0, 0, 1]},
        }
    ]
    viewer = tmp_path / "viewer.html"
    report.write_cloud_review(
        viewer, image, camera, world, np.full((3, 3), 128), locations, {}
    )
    with sync_playwright() as tool:
        browser = tool.chromium.launch(
            executable_path=str(edge),
            headless=True,
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        )
        context = browser.new_context(
            offline=True, viewport={"width": 1100, "height": 900}
        )
        page = context.new_page()
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "request",
            lambda request: (
                external.append(request.url) if request.url.startswith("http") else None
            ),
        )
        page.goto(viewer.as_uri())
        page.wait_for_function(
            "document.querySelector('.js-plotly-plot')._fullLayout.scene._scene !== undefined"
        )
        assert page.locator(".js-plotly-plot").evaluate(
            "g=>Array.from(g.data[1].x)"
        ) == [1]
        page.get_by_text("World", exact=True).click()
        page.get_by_text("Camera", exact=True).click()
        page.wait_for_function(
            "document.querySelector('.js-plotly-plot').data[1].x[0] === 0"
        )
        assert page.locator(".js-plotly-plot").evaluate(
            "g=>Array.from(g.data[1].z)"
        ) == [1]
        camera_before = page.locator(".js-plotly-plot").evaluate(
            "g=>JSON.stringify(g._fullLayout.scene.camera)"
        )
        page.mouse.move(450, 430)
        page.mouse.down()
        page.mouse.move(580, 470, steps=12)
        page.mouse.up()
        page.wait_for_function("true")
        camera_after = page.locator(".js-plotly-plot").evaluate(
            "g=>JSON.stringify(g._fullLayout.scene.camera)"
        )
        assert camera_before != camera_after
        page.screenshot(path=str(tmp_path / "viewer_check.png"))
        assert not errors and not external
        context.close()
        browser.close()
