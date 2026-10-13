"""The run report: six offline pages built from a finished run, with the scorer's error series."""

import json
import re

import numpy as np

from src.walkthrough import pipeline, validation
from src.walkthrough.steps.contracts import DepthPrediction
from src.walkthrough.tests.test_adapters import config  # noqa: F401  (fixture)
from tools.demos import run_pages
from tools.demos.page import EXTERNAL_RESOURCE


def _page_data(path):
    text = path.read_text(encoding="utf-8")
    match = re.search(r'<script type="application/json" id="demo-data">(.*?)</script>', text, re.DOTALL)
    return text, json.loads(match.group(1).replace("<\\/", "</"))


def test_report_has_six_offline_pages_with_scored_depth_series(config, tmp_path):  # noqa: F811
    def reference_at_2_5_m(frames, *, run):
        # The software depth fixture predicts 2.0 m everywhere, so every frame is 20% too near.
        for frame in frames:
            shape = (3, 4)
            yield DepthPrediction(frame.frame_id, np.full(shape, 2.5), np.ones(shape, dtype=bool))

    result = pipeline.run(
        config, scores=(validation.ScoreRequest("depth", lambda: reference_at_2_5_m),)
    )
    pages = run_pages.write_report(result.path, tmp_path / "report")

    assert [page.name for page in pages] == [name for name, _ in run_pages.PAGES]
    scores = json.loads((result.path / "output/scores.json").read_text())
    expected = [row["abs_rel"] for row in scores["depth"]["result"]["per_frame"]]
    _, depth = _page_data(tmp_path / "report" / "01_depth.html")
    assert depth["absRel"] == expected
    assert np.allclose(expected, 0.2)
    assert len(depth["frames"]) == len(expected)
    for page in pages:
        html_text = page.read_text(encoding="utf-8")
        assert result.path.name in html_text  # each page names its run
        assert not EXTERNAL_RESOURCE.search(html_text)  # no script, style, image or font is fetched
    _, camera = _page_data(tmp_path / "report" / "02_camera.html")
    assert camera["scored"] is False  # no camera reference was requested for this run


def _strict(text):
    """Parse page data the way a browser does: bare NaN or Infinity is an error."""
    def refuse(token):
        raise ValueError(f"page data contains {token}")

    match = re.search(r'<script type="application/json" id="demo-data">(.*?)</script>', text, re.DOTALL)
    return json.loads(match.group(1).replace("<\\/", "</"), parse_constant=refuse)


def test_depth_page_charts_each_frames_scale_and_surface_page_charts_the_gap(config, tmp_path):  # noqa: F811
    def reference_at_2_5_m(frames, *, run):
        for frame in frames:
            yield DepthPrediction(frame.frame_id, np.full((3, 4), 2.5), np.ones((3, 4), dtype=bool))

    result = pipeline.run(config, scores=(validation.ScoreRequest("depth", lambda: reference_at_2_5_m),))
    pages = run_pages.write_report(result.path, tmp_path / "report")

    scores = json.loads((result.path / "output/scores.json").read_text())
    per_frame = scores["depth"]["result"]["per_frame"]
    depth = _strict((tmp_path / "report" / "01_depth.html").read_text(encoding="utf-8"))
    assert depth["scaleRatio"] == [row["scale_ratio"] for row in per_frame]
    assert np.allclose(depth["scaleRatio"], 0.8)  # 2.0 m predicted against 2.5 m: 20% too near
    assert depth["fittedAbsRel"] == [row["fitted_abs_rel"] for row in per_frame]

    surface = _strict((tmp_path / "report" / "03_surface.html").read_text(encoding="utf-8"))
    assert len(surface["gapLag1"]) == len(per_frame)
    assert surface["gapLag1"][0] is None  # the first frame has nothing earlier: null, not NaN
    assert [row["lag"] for row in surface["gapByLag"]] == [1, 5, 10, 20, 29]
    for page in pages:
        _strict(page.read_text(encoding="utf-8"))  # every page parses without NaN


def test_page_data_turns_nan_into_null():
    from tools.demos import run_report

    cleaned = run_report.json_safe({"a": float("nan"), "b": [1.0, np.float32("inf")], "c": np.float64(2.5)})

    assert cleaned == {"a": None, "b": [1.0, None], "c": 2.5}


def test_report_defaults_to_a_folder_beside_the_run(config):  # noqa: F811
    result = pipeline.run(config)

    pages = run_pages.write_report(result.path)

    assert pages[0].parent == result.path.with_name(result.path.name + "-report")
    overview = pages[0].read_text(encoding="utf-8")
    assert "frame per second floor" in overview
