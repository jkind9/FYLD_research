"""Full-length clip maker and the per-run scale-drift summary."""

import importlib
import json

import numpy as np
import pytest
from PIL import Image

scale_drift = importlib.import_module("experiments.02_stereo_depth.scale_drift")

HEADER = "# timestamp filename\n"


def _recording(root, rgb_times, depth_times):
    """A tiny TUM-style folder: RGB and depth tables, images and a ground-truth file."""
    for folder in ("rgb", "depth"):
        (root / folder).mkdir(parents=True)
    rows = []
    for t in rgb_times:
        Image.new("RGB", (4, 3)).save(root / f"rgb/{t:.6f}.png")
        rows.append(f"{t:.6f} rgb/{t:.6f}.png")
    (root / "rgb.txt").write_text(HEADER + "\n".join(rows) + "\n")
    rows = []
    for t in depth_times:
        Image.fromarray(np.full((3, 4), 5000, dtype=np.uint16)).save(root / f"depth/{t:.6f}.png")
        rows.append(f"{t:.6f} depth/{t:.6f}.png")
    (root / "depth.txt").write_text(HEADER + "\n".join(rows) + "\n")
    (root / "groundtruth.txt").write_text("# timestamp tx ty tz qx qy qz qw\n1.0 0 0 0 0 0 0 1\n")


def _table(path):
    return [line.split() for line in path.read_text().splitlines() if line and not line.startswith("#")]


def test_clip_drops_rows_without_depth_keeps_every_second_and_pairs_nearest_depth(tmp_path):
    rgb = [1.00, 1.03, 1.07, 1.10, 1.13, 1.17, 1.20, 1.23]
    depth = [1.071, 1.101, 1.131, 1.168, 1.199, 1.229]  # nothing within 0.02 s of 1.00 or 1.03
    _recording(tmp_path / "source", rgb, depth)

    summary = scale_drift.make_clip(tmp_path / "source", tmp_path / "clip")

    kept = _table(tmp_path / "clip/rgb.txt")
    assert [float(t) for t, _ in kept] == [1.07, 1.13, 1.20]
    assert [float(t) for t, _ in _table(tmp_path / "clip/depth.txt")] == [1.071, 1.131, 1.199]
    assert summary["frames"] == 3 and summary["dropped_without_depth"] == 2
    assert summary["largest_gap_s"] == pytest.approx(0.07)
    assert all((tmp_path / "clip" / name).is_file() for _, name in kept)
    assert (tmp_path / "clip/groundtruth.txt").read_text() == (tmp_path / "source/groundtruth.txt").read_text()
    assert "every 2nd" in (tmp_path / "clip/CLIP_SOURCE.txt").read_text()


def test_clip_with_a_gap_the_tracker_would_split_is_refused(tmp_path):
    rgb = [1.00, 1.03, 1.07, 1.10, 1.30, 1.33]
    _recording(tmp_path / "source", rgb, rgb)

    with pytest.raises(ValueError, match="0.1 s"):
        scale_drift.make_clip(tmp_path / "source", tmp_path / "clip")
    assert not (tmp_path / "clip").exists()


def test_clip_finds_the_nested_desk_folder(tmp_path):
    nested = tmp_path / "tum" / "seq" / "seq"
    _recording(nested, [1.0, 1.03, 1.07], [1.0, 1.03, 1.07])

    summary = scale_drift.make_clip(tmp_path / "tum", tmp_path / "clip", sequence="seq")

    assert summary["source"] == str(nested)


SHAPE = (4, 5)
CAMERA = {"width": 5, "height": 4, "fx": 5.0, "fy": 5.0, "cx": 2.0, "cy": 1.5, "axes": "x-right_y-down_z-forward"}


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def _fake_run(path, depths_m, scale_ratios, camera_errors_m):
    """A finished run with constant-depth frames, identity poses and chosen scores."""
    frames, records, capture = [], [], []
    for index, depth_m in enumerate(depths_m):
        arrays = f"output/predictions/depth/{index:06d}.npz"
        (path / arrays).parent.mkdir(parents=True, exist_ok=True)
        np.savez(path / arrays, depth=np.full(SHAPE, depth_m), valid=np.ones(SHAPE, dtype=bool))
        frame_id = f"f{index}"
        frames.append({"frame_id": frame_id, "arrays": arrays, "calibration": CAMERA, "source": "fake (x.Y)"})
        capture.append({"frame_id": frame_id, "timestamp_s": 10.0 + index})
        pose = {"T_world_camera": np.eye(4).tolist(), "world_id": "w", "segment_id": "0", "source": "estimated",
                "units": "metres", "direction": "camera_to_world"}
        records.append({"frame_id": frame_id, "timestamp_s": 10.0 + index, "pose": pose, "status": "tracked", "reason": ""})
    _write(path / "output/predictions/depth.json", {"frames": frames, "methods": {"depth": "fake (x.Y)"}, "control": None})
    _write(path / "output/predictions/capture.json", {"frames": capture})
    _write(path / "output/predictions/tracking.json", {"records": records})
    _write(path / "output/predictions/mapping.json",
           {"measurements": {"origin 0 plane area": {"value": 2.5, "units": "square metres"}}})
    per_frame = [{"frame_id": f"f{i}", "abs_rel": 0.1, "scale_ratio": s, "fitted_abs_rel": 0.05}
                 for i, s in enumerate(scale_ratios)]
    errors = [{"frame_id": f"f{i}", "position_error_m": e} for i, e in enumerate(camera_errors_m)]
    _write(path / "output/scores.json", {
        "depth": {"status": "scored", "result": {"overall": {"abs_rel": 0.1}, "per_frame": per_frame}},
        "tracking": {"status": "scored", "result": {"position_rmse_m": 0.2, "tracked_edges": 3, "possible_transitions": 3,
                                                    "errors": errors}},
    })
    steps = [{"name": n, "status": "complete", "method": "fake"} for n in
             ("capture", "depth", "tracking", "surface", "mapping", "objects")]
    _write(path / "output/result.json", {"steps": steps, "complete": True, "controls": {}})
    stages = {f"prediction_{n}": {"elapsed_seconds": 1.0, "frames": 4} for n in ("depth", "tracking")}
    _write(path / "metadata/timing.json", {"stages": stages, "processed_frames": 4, "end_to_end_fps": 0.5})
    _write(path / "metadata/configuration.json", {"source": {"root": None}})
    return path


def test_summary_reports_known_numbers_for_two_runs(tmp_path):
    steady = _fake_run(tmp_path / "steady", [2.0] * 4, [1.0, 1.0, 1.0, 1.0], [0.0, 0.01, 0.02, 0.03])
    jumpy = _fake_run(tmp_path / "jumpy", [2.0, 2.2, 2.2, 2.6], [1.0, 1.1, 1.1, 1.3], [0.0, 0.1, 0.1, 0.3])

    rows = [scale_drift.summarise_run(steady, lags=(1, 2)), scale_drift.summarise_run(jumpy, lags=(1, 2))]

    assert rows[0]["surface_gap_m"]["1"]["median_abs_m"] == pytest.approx(0.0)
    assert rows[1]["surface_gap_m"]["1"]["median_abs_m"] == pytest.approx(0.2)  # gaps 0.2, 0.0, 0.4
    assert rows[1]["surface_gap_m"]["2"]["median_abs_m"] == pytest.approx(0.3)  # gaps 0.2, 0.4
    assert rows[1]["surface_gap_m"]["2"]["pairs"] == 2
    assert rows[1]["scale_ratio"]["min"] == pytest.approx(1.0) and rows[1]["scale_ratio"]["max"] == pytest.approx(1.3)
    assert rows[1]["scale_change_vs_camera_error_change"] == pytest.approx(1.0)  # same ranking
    assert rows[1]["camera_rmse_m"] == pytest.approx(0.2)
    assert rows[1]["plane_area_m2"] == pytest.approx(2.5)
    assert rows[1]["depth_layer_fps"] == pytest.approx(4.0)
    assert rows[1]["processing_fps"] == pytest.approx(2.0)
    assert rows[1]["reference_pose_gap_m"] is None  # no recording root saved: not computed
    text = json.dumps(scale_drift.json_safe({"runs": rows}), allow_nan=False)  # no NaN reaches the file
    assert "surface_gap_m" in text


def test_markdown_table_has_one_row_per_run(tmp_path):
    run = _fake_run(tmp_path / "run", [2.0] * 4, [1.0] * 4, [0.0] * 4)
    row = {**scale_drift.summarise_run(run), "label": "steady"}

    table = scale_drift.markdown_table([row])

    assert table.count("\n| steady |") == 1


def test_space_guard_refuses_below_the_minimum(tmp_path):
    with pytest.raises(SystemExit, match="free"):
        scale_drift.check_free_space(tmp_path, minimum_gb=10**9)
    scale_drift.check_free_space(tmp_path, minimum_gb=0)
