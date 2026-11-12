"""Runs are listed and filtered from their run.json files, and the index links their pages."""

import re

from sitescan.runs import REPO, finish_run, new_run
from tools import runs

# Scripts that still choose their own output path. New scripts take --label and use sitescan.runs; a script
# leaves this list when it moves over.
STILL_TAKE_OUT = {
    "apps/receiver/capture_receiver.py",
    "research/evaluation/depth_check.py",
    "research/evaluation/landmark_probe.py",
    "research/evaluation/orientation_control.py",
    "research/evaluation/stand_in.py",
    "research/evaluation/stage_report/run.py",
    "research/experiments/02_stereo_depth/run.py",
    "research/experiments/06_object_recognition/experiments/01_detection/jitter_run.py",
    "research/experiments/06_object_recognition/experiments/01_detection/placement_run.py",
    "tools/demos/build.py",
    "research/experiments/01_camera_capture_delivery/host/accuracy.py",
    "research/experiments/01_camera_capture_delivery/host/receiver.py",
    "research/experiments/02_stereo_depth/marigold.py",
    "research/experiments/02_stereo_depth/scale_drift.py",
    "research/experiments/02_stereo_depth/sparse_scale.py",
    "research/experiments/06_object_recognition/experiments/01_detection/run.py",
    "research/experiments/06_object_recognition/experiments/02_segmentation/run.py",
    "research/experiments/06_object_recognition/experiments/03_appearance/run.py",
    "research/experiments/06_object_recognition/experiments/04_geometry_identity/run.py",
    "research/experiments/lingbot_map/run.py",
    "research/experiments/open_vio/calibration/compare.py",
    "research/experiments/open_vio/calibration/prepare.py",
    "research/experiments/open_vio/calibration/to_sitescan.py",
    "research/experiments/sfm/dump_da3_depth.py",
    "research/experiments/sfm/dump_depth.py",
    "research/experiments/sfm/dump_prompt_depth.py",
    "research/experiments/shared/share.py",
    "tools/demos/capture_scene.py",
    "tools/demos/cleanup_scene.py",
    "tools/demos/cleanup_tuner.py",
    "tools/demos/run_report.py",
    "tools/demos/screenshot.py",
}


def test_no_new_script_picks_its_own_output_path():
    takes_out = re.compile(r"add_argument\(\s*\"--out(put)?\"")
    found = {path.relative_to(REPO).as_posix() for folder in ("apps", "sitescan", "tools", "research")
             for path in (REPO / folder).rglob("*.py")
             if "tests" not in path.parts and takes_out.search(path.read_text(encoding="utf-8", errors="ignore"))}
    assert found <= STILL_TAKE_OUT, f"use --label and sitescan.runs instead: {sorted(found - STILL_TAKE_OUT)}"


def test_runs_are_listed_filtered_and_indexed_and_strays_are_flagged(tmp_path, capsys):
    room = new_run("tum-desk-20", "room", "sweep-jump125", {"scale_sources": ["dense", "sparse"]},
                   {"max_scale_jump": 1.25}, root=tmp_path)
    finish_run(room, {"surface_points": 5})
    (room / "pages").mkdir()
    (room / "pages" / "viewer.html").write_text("<p>page</p>")
    new_run("tum-desk-20", "live", "first", {"scale_sources": ["arcore_depth"]}, root=tmp_path)
    (tmp_path / "room_15oct" / "arcore_default").mkdir(parents=True)  # an old-style folder

    found, outside = runs.find_runs(tmp_path)
    assert {r["tool"] for r in found} == {"room", "live"}
    assert outside == [tmp_path / "room_15oct" / "arcore_default"]
    assert [r["tool"] for r in found if runs.matches(r, None, None, None, ["scale_sources=dense"])] == ["room"]
    assert [r["tool"] for r in found if runs.matches(r, "tum-desk-20", "live", None, [])] == ["live"]
    assert not [r for r in found if runs.matches(r, None, None, "nothing-like-it", [])]

    assert runs.main(["--root", str(tmp_path), "--index", "--grep", "jump"]) == 0
    printed = capsys.readouterr().out
    assert "sweep-jump125" in printed and "max_scale_jump=1.25" in printed and "outside the convention" in printed
    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert 'href="tum-desk-20/room/' in page and "pages/viewer.html" in page and "room_15oct/arcore_default" in page
