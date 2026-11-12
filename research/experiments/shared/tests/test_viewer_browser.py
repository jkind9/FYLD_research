"""Browser regression for failed and empty observations; CPU Canvas2D only."""

from pathlib import Path

import pytest

from experiments.shared.visualization import write_viewer


@pytest.mark.parametrize("count", [0, 2])
def test_viewer_without_poses(tmp_path, count):
    sync = pytest.importorskip(
        "playwright.sync_api",
        reason="optional browser verification requires Playwright",
    )
    edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if not edge.exists():
        pytest.skip("browser verification requires the local Edge executable")
    frames = [
        {
            "id": str(i),
            "order": i,
            "segment": None,
            "camera": None,
            "reference_camera": None,
            "images": [],
            "status": "failed",
            "caption": "No pose",
        }
        for i in range(count)
    ]
    write_viewer(
        tmp_path,
        {
            "title": "No poses",
            "frames": frames,
            "note": "Observed inputs remain inspectable",
        },
    )
    with sync.sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=str(edge),
            headless=True,
            args=["--disable-gpu", "--disable-webgl"],
        )
        page = browser.new_page(viewport={"width": 600, "height": 800})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((tmp_path / "viewer.html").as_uri())
        assert page.locator("#details").inner_text()
        if count:
            page.locator("#previous").click()
            assert "Frame 0" in page.locator("#details").inner_text()
            page.locator("#next").click()
            assert "Frame 1" in page.locator("#details").inner_text()
        else:
            assert page.locator("#next").is_disabled()
        size = page.locator("#scene").bounding_box()
        assert size and abs(size["width"] / size["height"] - 1200 / 560) < 0.03
        assert errors == []
        browser.close()


def test_viewer_pointer_and_keyboard_pan_reset_view(tmp_path):
    sync = pytest.importorskip(
        "playwright.sync_api",
        reason="optional browser verification requires Playwright",
    )
    edge = Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
    if not edge.exists():
        pytest.skip("browser verification requires the local Edge executable")
    write_viewer(
        tmp_path,
        {
            "title": "Pan controls",
            "frames": [
                {
                    "id": "one",
                    "order": 0,
                    "segment": "desk",
                    "camera": None,
                    "reference_camera": None,
                    "points": [[-1.0, 0.0, 0.0]],
                    "colours": [[255, 0, 0]],
                    "images": [],
                    "status": "visible",
                    "caption": "Two test points",
                }
            ],
            "note": "Pan with pointer and keyboard",
        },
    )
    with sync.sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=str(edge),
            headless=True,
            args=["--disable-gpu", "--disable-webgl"],
        )
        page = browser.new_page(viewport={"width": 900, "height": 800})
        page.goto((tmp_path / "viewer.html").as_uri())
        canvas = page.locator("#scene")
        point_position = """(canvas) => {
          const pixels = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
          for (let y = 0; y < canvas.height; y++) for (let x = 0; x < canvas.width; x++) {
            const offset = (y * canvas.width + x) * 4;
            if (pixels[offset] === 255 && pixels[offset + 1] === 0 && pixels[offset + 2] === 0) return [x, y];
          }
          return null;
        }"""
        start = canvas.evaluate(point_position)
        assert start is not None
        bounds = canvas.bounding_box()
        assert bounds
        dx, dy = 20, 12
        page.mouse.move(bounds["x"] + bounds["width"] / 2, bounds["y"] + bounds["height"] / 2)
        page.mouse.down(button="right")
        page.mouse.move(
            bounds["x"] + bounds["width"] / 2 + dx,
            bounds["y"] + bounds["height"] / 2 + dy,
        )
        page.mouse.up(button="right")
        after_pointer = canvas.evaluate(point_position)
        assert after_pointer != start
        page.locator("#reset").click()
        assert canvas.evaluate(point_position) == start

        canvas.focus()
        page.keyboard.press("Shift+ArrowRight")
        after_keyboard = canvas.evaluate(point_position)
        assert after_keyboard[0] == start[0] - 24
        assert after_keyboard[1] == start[1]
        page.locator("#reset").click()
        assert canvas.evaluate(point_position) == start
        browser.close()
