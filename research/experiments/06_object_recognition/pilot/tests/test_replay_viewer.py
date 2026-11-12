"""Offline browser checks for synchronized replay controls."""

import importlib
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

viewer = importlib.import_module(
    "experiments.06_object_recognition.pilot.replay_viewer"
)


def _frame(index, image, visible, cloud_stop, camera_position):
    position = [0.1, 0.2, 1.0]
    detection = {
        "xyxy": [1.0, 2.0, 10.0, 12.0],
        "label": "cup",
        "class_id": 41,
        "confidence": 0.9,
        "object_id": "object-0001" if visible else None,
        "association": "new" if visible else "unresolved_no_position",
    }
    return {
        "frame_index": index,
        "frame_id": str(index),
        "timestamp_s": 10.0 + index / 30,
        "rgb": image,
        "camera_origin_world_m": camera_position,
        "point_count": 100,
        "cloud_start": 0 if index == 0 else cloud_stop - 2,
        "cloud_stop": cloud_stop,
        "tracks": {
            "object-0001": {
                "object_id": "object-0001",
                "label": "cup",
                "class_id": 41,
                "last_position_m": position,
                "last_frame_index": 0,
                "observation_count": 1,
            }
        },
        "failures": [] if visible else [{"association": "unresolved_no_position"}],
        "detections": [detection] if visible else [],
    }


def test_offline_replay_keeps_marker_and_updates_rgb_cloud_and_camera(tmp_path):
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if not edge.exists():
        pytest.skip("Local Edge is required for the replay viewer check")
    input_root = tmp_path / "input"
    (input_root / "rgb").mkdir(parents=True)
    Image.new("RGB", (640, 480), "red").save(input_root / "rgb/0.png")
    Image.new("RGB", (640, 480), "blue").save(input_root / "rgb/1.png")
    observations = [
        _frame(0, "rgb/0.png", True, 1, [0.0, 0.0, 0.0]),
        _frame(1, "rgb/1.png", False, 3, [0.1, 0.0, 0.0]),
    ]
    points = np.array([[0.0, 0.0, 1.0], [0.1, 0.0, 1.0], [0.2, 0.0, 1.0]], dtype=float)
    colours = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255]], dtype=np.uint8)
    html_path = tmp_path / "review.html"
    viewer.write_replay_review(html_path, input_root, observations, points, colours, 20)

    with sync_playwright() as tool:
        browser = tool.chromium.launch(
            executable_path=str(edge),
            headless=True,
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        )
        context = browser.new_context(
            offline=True, viewport={"width": 1400, "height": 1000}
        )
        page = context.new_page()
        errors, console_errors, external = [], [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        page.on(
            "request",
            lambda request: (
                external.append(request.url) if request.url.startswith("http") else None
            ),
        )
        page.goto(html_path.as_uri())
        try:
            page.wait_for_function(
                "document.querySelector('.js-plotly-plot')?.data?.length === 3",
                timeout=8000,
            )
        except PlaywrightTimeoutError:
            script_checks = page.evaluate(
                """() => Array.from(document.scripts).map((script, index) => {
                    try { new Function(script.textContent); return `${index}: ok (${script.textContent.length})`; }
                    catch (error) { return `${index}: ${error.message} at ${error.lineNumber}:${error.columnNumber}; ${error.stack} (${script.textContent.length})`; }
                })"""
            )
            raise AssertionError(
                f"Plotly did not initialize: page errors={errors}, console={console_errors}, scripts={script_checks}"
            ) from None
        first_image = page.locator("#rgb").get_attribute("src")
        assert page.locator(".js-plotly-plot").evaluate("g=>g.data[0].x.length") == 1
        assert (
            page.locator(".js-plotly-plot")
            .evaluate("g=>g.data[2].text[0]")
            .startswith("object-0001")
        )

        page.locator("#seek").evaluate(
            "el=>{el.value='1';el.dispatchEvent(new Event('input',{bubbles:true}))}"
        )
        page.wait_for_function(
            "document.querySelector('#counter').textContent === '2 / 2'"
        )
        assert page.locator("#rgb").get_attribute("src") != first_image
        assert page.locator(".js-plotly-plot").evaluate("g=>g.data[0].x.length") == 3
        assert page.locator(".js-plotly-plot").evaluate("g=>g.data[1].x.length") == 2
        assert (
            "out of view; marker retained" in page.locator("#object-info").inner_text()
        )
        assert not errors and not console_errors and not external
        context.close()
        browser.close()
