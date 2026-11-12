"""Every run writes outputs/<recording>/<tool>/<yyyymmdd-hhmm>_<label>/ with a run.json saying what made it."""

import json
from datetime import datetime

import pytest

from sitescan import runs

FIXTURE = runs.REPO / "tests" / "fixtures" / "tum_desk_20"


class Noon(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 11, 12, 12, 0, 30).astimezone()


def test_a_run_folder_is_named_by_recording_tool_time_and_label_and_records_its_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(runs, "datetime", Noon)
    folder = runs.new_run("tum-desk-20", "room", "sweep-jump125", {"far": 4.0}, {"far": 4.0}, root=tmp_path,
                          inputs=(tmp_path / "earlier",))
    assert folder == tmp_path / "tum-desk-20" / "room" / "20261112-1200_sweep-jump125"
    record = json.loads((folder / "run.json").read_text(encoding="utf-8"))
    assert record["status"] == "running" and record["settings"] == {"far": 4.0} and record["typed"] == {"far": 4.0}
    assert record["private"] is False and record["inputs"] == [str(tmp_path / "earlier")]
    assert len(record["code"]["commit"]) == 40
    runs.finish_run(folder, {"surface_points": 10})
    record = json.loads((folder / "run.json").read_text(encoding="utf-8"))
    assert record["status"] == "complete" and record["numbers"] == {"surface_points": 10} and "finished" in record
    with pytest.raises(FileExistsError):  # the same minute and label: never overwritten
        runs.new_run("tum-desk-20", "room", "sweep-jump125", {}, root=tmp_path)


@pytest.mark.parametrize("label", ["Sweep", "sweep_jump", "a-b-c-d-e", "", "sweep-"])
def test_labels_are_one_to_four_lowercase_words_joined_by_hyphens(tmp_path, label):
    with pytest.raises(ValueError, match="label"):
        runs.new_run("tum-desk-20", "room", label, {}, root=tmp_path)


def test_run_paths_stay_short(tmp_path):
    with pytest.raises(ValueError, match="characters"):
        runs.new_run("a-recording-with-a-very-long-name-indeed-yes", "a-long-tool-name", "four-long-label-words",
                     {}, root=tmp_path)


def test_unlisted_recordings_count_as_private(tmp_path):
    folder = runs.new_run("someone-else", "room", "first", {}, root=tmp_path)
    assert json.loads((folder / "run.json").read_text(encoding="utf-8"))["private"] is True


def test_recordings_are_found_by_short_name_and_named_from_their_folder(tmp_path):
    assert runs.session_path("tum-desk-20") == FIXTURE
    assert runs.recording_name(FIXTURE) == "tum-desk-20"
    assert runs.session_path(str(tmp_path)) == tmp_path and runs.recording_name(tmp_path) == tmp_path.name


def test_typed_options_are_the_ones_on_the_command_line_except_where_the_run_goes():
    argv = ["room", "--session", "x", "--label", "y", "--root", "z", "--max-scale-jump", "1.25",
            "--scale-sources", "dense", "sparse"]
    values = {"max_scale_jump": 1.25, "scale_sources": ["dense", "sparse"], "far": 4.0, "session": "x"}
    assert runs.typed_options(argv, values) == {"max_scale_jump": 1.25, "scale_sources": ["dense", "sparse"]}
