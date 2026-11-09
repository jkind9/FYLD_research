"""The clean-up viewer's results table comes straight from a denoise_trial results.json."""

from tools.demos import cleanup_scene


def variant(points, floating, door, stairs, near, far, covered, below):
    return {"surface_points": points, "floating_points": floating, "blocked_share_door_frame_65": door,
            "blocked_share_stairs_frame_420": stairs, "blocked_sight_line_share_from_0.0_m": near,
            "blocked_sight_line_share_from_2.5_m": far, "arcore_depth_within_5cm": covered,
            "below_floor_10cm_points": below}


def test_results_table_has_one_row_per_variant_with_its_scores():
    results = {"variants": {"baseline": variant(676853, 12889, 0.064, 0.082, 0.0925, 0.0859, 0.849, 38171),
                            "clusters_3cm": variant(630389, 0, 0.047, 0.067, 0.073, 0.061, 0.842, 36811)}}
    table = cleanup_scene.results_table(results)
    assert table.count("<tr>") == 3  # header and two variants
    assert "Floating-piece removal, 3 cm join" in table and "676,853" in table and "12,889" in table
    assert "6.4%" in table and "4.7%" in table


def test_focus_cameras_add_a_bookmark_for_each_chosen_frame(tmp_path):
    import json

    from PIL import Image

    (tmp_path / "frames").mkdir()
    Image.new("RGB", (64, 48), (90, 120, 150)).save(tmp_path / "frames" / "000065.jpg")
    row = {"seq": 65, "arcore": {"pose": [0, 0, 0, 0, 0, 0, 1], "intrinsics": [50.0, 50.0, 32.0, 24.0]}}
    (tmp_path / "frames.jsonl").write_text(json.dumps({"seq": 64}) + "\n" + json.dumps(row) + "\n")
    [camera] = cleanup_scene.focus_cameras(tmp_path, [65])
    assert camera["frame"] == 65 and camera["label"] == "Frame 65"
    assert camera["photo"].startswith("data:image") and len(camera["pose"]) == 4
