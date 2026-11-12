"""The recorded Redmi surface becomes an offline, navigable splat scene."""

import base64
import importlib
import io
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
    doc = out.read_text(encoding="utf-8")
    data = json.loads(re.search(r'<script type="application/json" id="demo-data">(.*?)</script>', doc, re.DOTALL)[1])
    assert data["splat"]["positions"]["count"] == 9
    assert data["source"]["points"] == 9 and data["source"]["frames"] == 3
    assert data["up"] == [0, 1, 0]
    assert "surface-derived" in doc and "height colours" in doc
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


@pytest.mark.parametrize(("camera_z", "facing"), [(0.0, 1), (-2.0, -1)])
def test_splats_take_photo_colours_and_face_the_nearest_camera(capture, camera_z, facing):
    surface, session = capture
    head, body = surface.read_text().split("end_header\n")
    head = head.replace("property float z\n", "property float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\n")
    surface.write_text(head + "end_header\n" + "\n".join(line + " 200 40 10" for line in body.splitlines()))
    rows = [json.loads(line) for line in (session / "frames.jsonl").read_text().splitlines()]
    for row in rows[1:]:
        row["arcore"]["pose"][2] = camera_z  # the wall is at z = -1
    (session / "frames.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
    exporter = importlib.import_module("tools.demos.capture_scene")
    scene = exporter.load_scene(surface, session, 0.06)
    colours = np.frombuffer(base64.b64decode(scene["splat"]["colours"]["b64"]), dtype=np.uint8).reshape(-1, 3)
    assert (colours == [200, 40, 10]).all()
    assert len(base64.b64decode(scene["splat"]["heightColours"]["b64"])) == colours.size
    normals = np.frombuffer(base64.b64decode(scene["splat"]["normals"]["b64"]), dtype=np.int8).reshape(-1, 3)
    assert (np.sign(normals[:, 2]) == facing).all()
    page = exporter.scene_page(scene)
    assert 'id="one-way"' in page and 'id="ceiling"' in page and 'id="floor"' in page
    assert 'id="measure"' in page and 'id="measure-value"' in page


def test_cells_missing_from_the_cleaned_surface_are_flagged_removed(capture, tmp_path):
    surface, session = capture
    head, body = surface.read_text().split("end_header\n")
    kept = tmp_path / "kept.ply"  # the clean-up kept the six points with x < 0.4
    kept.write_text(head.replace("element vertex 9", "element vertex 6") + "end_header\n"
                    + "\n".join(body.splitlines()[:6]))
    exporter = importlib.import_module("tools.demos.capture_scene")
    scene = exporter.load_scene(surface, session, 0.06, kept=kept)
    removed = np.frombuffer(base64.b64decode(scene["splat"]["removed"]["b64"]), dtype=np.uint8)
    lo, hi = np.array(scene["splat"]["positions"]["min"]), np.array(scene["splat"]["positions"]["max"])
    x = lo[0] + np.frombuffer(base64.b64decode(scene["splat"]["positions"]["b64"]), dtype=np.uint16).reshape(-1, 3)[:, 0] \
        / 65535 * (hi[0] - lo[0])
    assert (removed == (x > 0.3)).all() and removed.sum() == 3
    assert scene["source"]["removed_points"] == 3
    page = exporter.scene_page(scene, report="<h2>Trial</h2>")
    assert 'id="show-removed"' in page and 'id="hide-removed"' in page and "<h2>Trial</h2>" in page
    assert 'id="show-removed"' not in exporter.scene_page(exporter.load_scene(surface, session, 0.06))


PORTRAIT = [0, 0, 0, 0, 0, -0.7071068, 0.7071068]  # ARCore pose turned -90 degrees about z: image right points down


def portrait(session):
    rows = [json.loads(line) for line in (session / "frames.jsonl").read_text().splitlines()]
    for row in rows[1:]:
        row["arcore"]["pose"] = PORTRAIT
    (session / "frames.jsonl").write_text("\n".join(json.dumps(row) for row in rows))


def photo_size(url):
    return Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).size


def test_portrait_bookmarks_show_upright_photos_from_upright_cameras(capture):
    surface, session = capture
    portrait(session)
    bookmark = importlib.import_module("tools.demos.capture_scene").load_scene(surface, session, 0.06)["compare"][0]
    width, height = photo_size(bookmark["photo"])
    assert height > width
    assert (bookmark["width"], bookmark["height"]) == (480, 640)
    np.testing.assert_allclose(np.array(bookmark["pose"])[:3, 1], [0, -1, 0], atol=1e-6)  # image down is world down


def test_room_build_frames_become_a_frame_by_frame_timeline(capture, tmp_path):
    surface, session = capture
    portrait(session)
    frames = tmp_path / "frames.npz"
    pose = np.eye(4)
    pose[:3, :2] = [[0, -1], [-1, 0], [0, 0]]
    pose[:3, 2] = [0, 0, -1]
    np.savez(frames, seq=np.array([1, 2]), poses=np.stack([pose, pose]), intrinsics=np.array([[400, 400, 320, 240]] * 2),
             sizes=np.array([[640, 480]] * 2), points=np.random.default_rng(0).random((5, 3)),
             colours=np.full((5, 3), 200, np.uint8), point_offsets=np.array([0, 2, 5]),
             arcore=np.random.default_rng(1).random((3, 3)), arcore_offsets=np.array([0, 1, 3]))
    exporter = importlib.import_module("tools.demos.capture_scene")
    data = exporter.load_scene(surface, session, 0.06, frames)
    timeline = data["timeline"]
    assert timeline["seq"] == [1, 2] and timeline["pointOffsets"] == [0, 2, 5] and timeline["arcoreOffsets"] == [0, 1, 3]
    assert timeline["points"]["count"] == 5 and timeline["arcore"]["count"] == 3
    assert all(photo_size(p)[1] > photo_size(p)[0] for p in timeline["photos"])
    np.testing.assert_allclose(np.array(timeline["poses"][0])[:3, 1], [0, -1, 0], atol=1e-6)
    page = exporter.scene_page(data)
    assert 'data-view="build"' in page and "carried ARCore depth" in page  # no run summary: the old wording

    (tmp_path / "summary.json").write_text(json.dumps(
        {"pose_source": "basalt", "scale": {"frames_per_source": {"dense": 1, "sparse": 1}}}))
    page = exporter.scene_page(exporter.load_scene(surface, session, 0.06, frames))
    assert "Poses: basalt" in page and "plane-sweep depth or triangulated feature points" in page
    assert "ARCore&#x27;s depth was not used" in page or "ARCore's depth was not used" in page
    assert "carried ARCore depth" not in page and "the world origin of the poses (basalt)" in page


def test_frame_by_frame_leaves_out_points_the_clean_up_removed(capture, tmp_path):
    surface, session = capture
    head, body = surface.read_text().split("end_header\n")
    (tmp_path / "raw_surface.ply").write_text(  # the raw room: the shown surface plus one point the clean-up removed
        head.replace("element vertex 9", "element vertex 10") + "end_header\n" + body + "\n3 3 3")
    frames = tmp_path / "frames.npz"
    np.savez(frames, seq=np.array([1, 2]), poses=np.stack([np.eye(4)] * 2), intrinsics=np.array([[400, 400, 320, 240]] * 2),
             sizes=np.array([[640, 480]] * 2), points=np.array([[0, 0, -1], [3, 3, 3], [0.41, 0.4, -1], [2.9, 3, 3]]),
             colours=np.full((4, 3), 200, np.uint8), point_offsets=np.array([0, 2, 4]),
             arcore=np.zeros((2, 3)), arcore_offsets=np.array([0, 1, 2]))
    exporter = importlib.import_module("tools.demos.capture_scene")
    data = exporter.load_scene(surface, session, 0.06, frames)
    assert data["timeline"]["pointOffsets"] == [0, 1, 2] and data["timeline"]["points"]["count"] == 2
    assert "Points the clean-up removed are left out" in exporter.scene_page(data)


def test_splats_carry_their_surface_piece_and_the_sliders_start_at_the_room_rule(capture):
    surface, session = capture
    room = [(x / 100, y / 100, -1) for x in range(10) for y in range(10)]  # 100 touching points
    speck = [(1 + x / 100, 0, -1) for x in range(3)]  # 3 points, 0.9 m away
    surface.write_text("ply\nformat ascii 1.0\nelement vertex 103\nproperty float x\nproperty float y\n"
                       "property float z\nend_header\n" + "\n".join(" ".join(map(str, p)) for p in room + speck))
    exporter = importlib.import_module("tools.demos.capture_scene")
    data = exporter.load_scene(surface, session, 0.06)
    splat = data["splat"]
    rule = splat["pieces"][0]
    assert rule["neighbours"] == 0 and rule["sizes"] == [100, 3]
    assert [r["neighbours"] for r in splat["pieces"]] == list(exporter.NEIGHBOUR_STOPS)
    lo, hi = np.array(splat["positions"]["min"]), np.array(splat["positions"]["max"])
    x = lo[0] + np.frombuffer(base64.b64decode(splat["positions"]["b64"]), dtype=np.uint16).reshape(-1, 3)[:, 0] \
        / 65535 * (hi[0] - lo[0])
    rank = np.frombuffer(base64.b64decode(rule["rank"]["b64"]), dtype=np.uint32)
    assert (rank == (x > 0.5)).all()
    assert splat["keepStops"][splat["keepAt"]] == 50 and splat["smallestStops"][splat["smallestAt"]] == 5000
    page = exporter.scene_page(data)
    assert 'id="piece-keep"' in page and 'id="piece-min"' in page and 'id="piece-links"' in page


def test_a_run_folder_gives_the_page_its_inputs_and_place_and_every_thins_the_frames(capture, tmp_path):
    surface, session = capture
    run = tmp_path / "run"
    run.mkdir()
    (run / "run.json").write_text(json.dumps({"recording": str(session)}))  # an unlisted recording: its folder
    (run / "surface.ply").write_text(surface.read_text())
    np.savez(run / "frames.npz", seq=np.array([0, 1, 2]), poses=np.stack([np.eye(4)] * 3),
             intrinsics=np.array([[400, 400, 320, 240]] * 3), sizes=np.array([[640, 480]] * 3),
             points=np.array([[0, 0, -1], [0.2, 0, -1], [0.4, 0, -1]]), colours=np.full((3, 3), 200, np.uint8),
             point_offsets=np.array([0, 1, 2, 3]), arcore=np.zeros((3, 3)), arcore_offsets=np.array([0, 1, 2, 3]))
    importlib.import_module("tools.demos.capture_scene").main(["--run", str(run), "--every", "2"])
    doc = (run / "pages" / "viewer.html").read_text(encoding="utf-8")
    data = json.loads(re.search(r'<script type="application/json" id="demo-data">(.*?)</script>', doc, re.DOTALL)[1])
    assert data["timeline"]["seq"] == [0, 2] and data["timeline"]["pointOffsets"] == [0, 1, 2]


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


def test_the_player_steps_frames_on_one_screen_with_and_without_the_room_build(capture, tmp_path):
    sync = pytest.importorskip("playwright.sync_api", reason="the browser check needs Playwright")
    surface, session = capture
    frames = tmp_path / "frames.npz"
    np.savez(frames, seq=np.array([1, 2]), poses=np.stack([np.eye(4)] * 2), intrinsics=np.array([[400, 400, 320, 240]] * 2),
             sizes=np.array([[640, 480]] * 2), points=np.array([[0, 0, -1], [0.2, 0, -1], [0.4, 0, -1]]),
             colours=np.full((3, 3), 200, np.uint8), point_offsets=np.array([0, 1, 3]),
             arcore=np.zeros((2, 3)), arcore_offsets=np.array([0, 1, 2]))
    exporter = importlib.import_module("tools.demos.capture_scene")
    pages = {"build": exporter.scene_page(exporter.load_scene(surface, session, 0.06, frames)),
             "bookmarks": exporter.scene_page(exporter.load_scene(surface, session, 0.06))}
    with sync.sync_playwright() as p:
        browser = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        for name, doc in pages.items():
            (tmp_path / f"{name}.html").write_text(doc, encoding="utf-8")
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
            page.goto((tmp_path / f"{name}.html").as_uri())
            assert page.inner_text("#tl-caption").startswith("1 / 2")
            page.keyboard.press("ArrowRight")
            assert page.inner_text("#tl-caption").startswith("2 / 2")
            assert page.evaluate("document.documentElement.scrollHeight") <= 800  # one screen, no page scroll
            if name == "build":
                assert "+2 points" in page.inner_text("#tl-caption")
                page.keyboard.press("b")
                assert page.get_attribute("#app", "data-view") == "build"
                assert page.evaluate("sceneViewer.layers.get('tl-built').count") == 3
                page.keyboard.press("Home")
                assert page.evaluate("sceneViewer.layers.get('tl-built').count") == 1
            assert errors == []
            page.close()
        browser.close()
