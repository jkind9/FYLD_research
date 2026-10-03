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
