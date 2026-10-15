"""The recorded Redmi surface becomes an offline, navigable splat scene."""

import base64
import importlib
import json
import re
import subprocess
import sys

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def capture(tmp_path):
    surface = tmp_path / "surface.ply"
    points = [(x / 5, y / 5, -1) for x in range(3) for y in range(3)]
    surface.write_text("ply\nformat ascii 1.0\nelement vertex 9\n"
                       "property float x\nproperty float y\nproperty float z\nend_header\n"
                       + "\n".join(" ".join(map(str, p)) for p in points))
    session = tmp_path / "synthetic_walk"
    (session / "frames").mkdir(parents=True)
    (session / "session.json").write_text(json.dumps({"version": 2}))
    rows = []
    for seq in range(3):
        Image.new("RGB", (640, 480), (20, 80, 140)).save(session / "frames" / f"{seq:06d}.jpg")
        rows.append({"seq": seq, "camera_t_ns": seq * 1_000_000_000,
                     "arcore": None if seq == 0 else {
                         "pose": [0, 0, 0, 0, 0, 0, 1], "intrinsics": [400, 400, 320, 240]}})
    (session / "frames.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
    return surface, session


def export_capture(capture, out):
    surface, session = capture
    return subprocess.run([sys.executable, "-B", "-m", "tools.demos.capture_scene",
                           "--surface", str(surface), "--session", str(session), "--out", str(out)],
                          check=False, capture_output=True, text=True)


def test_cli_writes_a_single_offline_html_with_real_scene_counts(capture, tmp_path):
    out = tmp_path / "viewer.html"
    result = export_capture(capture, out)
    assert result.returncode == 0, result.stderr
    doc = out.read_text()
    data = json.loads(re.search(r'<script type="application/json" id="demo-data">(.*?)</script>', doc, re.DOTALL)[1])
    assert data["splat"]["positions"]["count"] == 9
    assert data["source"]["points"] == 9 and data["source"]["frames"] == 3
    assert data["up"] == [0, 1, 0]
    assert "surface-derived" in doc and "Height colours" in doc
    assert 'id="fit-scene"' in doc and 'id="top-view"' in doc
    assert 'id="download-ply"' in doc and "data:image/jpeg;base64," in doc
    assert not re.search(r'<script[^>]+src=|<link[^>]+href="https?', doc)


def test_bookmarks_use_arcore_camera_axes_and_normals_are_valid(capture):
    surface, session = capture
    scene = importlib.import_module("tools.demos.capture_scene").load_scene(surface, session, 0.06)
    assert [c["frame"] for c in scene["compare"]] == [1, 2]
    np.testing.assert_allclose(scene["compare"][0]["pose"], np.diag([1, -1, -1, 1]))
    normals = np.frombuffer(base64.b64decode(scene["splat"]["normals"]["b64"]), dtype=np.int8).reshape(-1, 3)
    assert np.all(np.linalg.norm(normals, axis=1) > 120)
    assert scene["compare"][0]["fy"] == 400


@pytest.mark.parametrize("voxel", [0, -0.1, float("nan")])
def test_invalid_splat_spacing_is_rejected(capture, voxel):
    surface, session = capture
    with pytest.raises(ValueError, match="voxel"):
        importlib.import_module("tools.demos.capture_scene").load_scene(surface, session, voxel)


def test_empty_surface_is_rejected(capture):
    surface, session = capture
    surface.write_text(surface.read_text().split("end_header")[0].replace("vertex 9", "vertex 0") + "end_header\n")
    with pytest.raises(ValueError, match="points"):
        importlib.import_module("tools.demos.capture_scene").load_scene(surface, session, 0.06)


def test_session_without_posed_images_is_rejected(capture):
    surface, session = capture
    (session / "frames.jsonl").write_text(json.dumps({"seq": 0, "camera_t_ns": 0, "arcore": None}))
    with pytest.raises(ValueError, match="posed"):
        importlib.import_module("tools.demos.capture_scene").load_scene(surface, session, 0.06)


def test_other_session_version_is_rejected(capture):
    surface, session = capture
    (session / "session.json").write_text(json.dumps({"version": 1}))
    with pytest.raises(ValueError, match="v2"):
        importlib.import_module("tools.demos.capture_scene").load_scene(surface, session, 0.06)


@pytest.mark.parametrize("field", ["pose", "intrinsics", "camera_t_ns"])
def test_non_finite_bookmarks_do_not_produce_broken_html(capture, tmp_path, field):
    _, session = capture
    rows = [json.loads(line) for line in (session / "frames.jsonl").read_text().splitlines()]
    if field == "camera_t_ns":
        rows[0][field] = float("nan")
    else:
        rows[1]["arcore"][field][0] = float("inf")
    (session / "frames.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
    out = tmp_path / "invalid.html"
    result = export_capture(capture, out)
    assert result.returncode != 0
    assert "finite" in result.stderr
    assert not out.exists()


def test_interrupted_capture_is_not_labelled_completed(capture):
    surface, session = capture
    (session / "session.json").write_text(json.dumps({"version": 2, "end_reason": "interrupted"}))
    exporter = importlib.import_module("tools.demos.capture_scene")
    doc = exporter.scene_page(exporter.load_scene(surface, session, 0.06))
    assert "completed walk" not in doc
    assert "recorded span" in doc
