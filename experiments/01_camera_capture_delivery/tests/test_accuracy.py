"""Field scores use tape measurements and named camera placements, never fitted scale."""

import copy
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HOST = Path(__file__).resolve().parents[1] / "host"
sys.path.insert(0, str(HOST))
import accuracy


def frame(seq, xyz, *, state="TRACKING", turn=(0, 0, 0, 1), corrections=None):
    return SimpleNamespace(seq=seq, t_ns=(seq + 1) * 1_000_000_000,
                           tracking=state, failure="NONE" if xyz is not None else "INSUFFICIENT_FEATURES",
                           pose=None if xyz is None else (*xyz, *turn), anchor_updates=corrections or {})


@pytest.fixture
def walk():
    frames = [frame(0, (0, 0, 0)), frame(1, (3, 0, 0)), frame(2, (3, 0, 4)),
              frame(3, (0, 0, 4)), frame(4, (0.03, 0.04, 0))]
    measured = {"walk": "indoor-01", "environment": "indoor",
                "loop": {"start_seq": 0, "end_seq": 4, "tape_length_m": 14},
                "distances": [{"name": "A-B", "from_seq": 0, "to_seq": 1, "tape_m": 3.1}]}
    return frames, measured


def test_metric_distance_and_closure_are_not_scale_fitted(walk):
    result = accuracy.score(*walk)
    assert result["loop"]["closure_mm"] == pytest.approx(50)
    assert result["loop"]["closure_percent_of_tape_length"] == pytest.approx(100 * 0.05 / 14)
    assert result["loop"]["turn_error_deg"] == 0
    distance = result["distances"][0]
    assert distance["estimated_m"] == 3
    assert distance["signed_error_mm"] == pytest.approx(-100)
    assert distance["absolute_error_percent"] == pytest.approx(100 * 0.1 / 3.1)


def test_stairs_use_full_3d_distance_and_quaternion_sign_does_not_change_turn(walk):
    frames, measured = walk
    frames[1] = frame(1, (0, 3, 4))
    frames[-1] = frame(4, (0, 0, 0), turn=(0, 0, 0, -1))
    measured["environment"] = "stairs"
    assert accuracy.score(frames, measured)["distances"][0]["estimated_m"] == 5
    assert accuracy.score(frames, measured)["loop"]["turn_error_deg"] == 0
    frames[-1] = frame(4, (0, 0, 0), turn=(0, 0, 1, 0))
    assert accuracy.score(frames, measured)["loop"]["turn_error_deg"] == 180


def test_quaternion_rounding_does_not_create_a_turn_error(walk):
    frames, measured = walk
    frames[0] = frame(0, (0, 0, 0), turn=(0, 0, 0, 0.9999))
    frames[-1] = frame(4, (0, 0, 0), turn=(0, 0, 0, 0.9999))
    assert accuracy.score(frames, measured)["loop"]["turn_error_deg"] == 0


def test_tracking_loss_is_counted_once_and_path_does_not_bridge_it(walk):
    frames, measured = walk
    frames[2] = frame(2, None, state="PAUSED")
    frames[3] = frame(3, None, state="STOPPED")
    result = accuracy.score(frames, measured)
    assert result["tracking"]["lost_events"] == 1
    assert result["tracking"]["tracked_fraction"] == 0.6
    assert result["tracking"]["failure_frames"] == {"INSUFFICIENT_FEATURES": 2}
    assert result["tracking"]["sampled_path_m"] == 3


def test_selected_interval_excludes_setup_and_reports_gaps_and_corrections(walk):
    frames, measured = walk
    frames[2].anchor_updates = {1: (0, 0, 0, 0, 0, 0, 1), 2: (0, 0, 0, 0, 0, 0, 1)}
    frames.pop(3)
    frames.insert(0, frame(-1, None, state="PAUSED"))
    result = accuracy.score(frames, measured)["tracking"]
    assert result["frames"] == 4
    assert result["lost_events"] == 0
    assert result["missing_sequence_numbers"] == 1
    assert result["longest_received_gap_s"] == 2
    assert result["anchor_corrections"] == 2


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
@pytest.mark.parametrize("target", ["loop", "distance"])
def test_invalid_tape_measurement_is_refused(walk, target, value):
    frames, measured = walk
    if target == "loop":
        measured["loop"]["tape_length_m"] = value
    else:
        measured["distances"][0]["tape_m"] = value
    with pytest.raises(ValueError, match="positive finite"):
        accuracy.score(frames, measured)


@pytest.mark.parametrize("bad", ["missing", "untracked", "reverse", "outside"])
def test_checkpoint_must_be_received_tracking_and_in_selected_order(walk, bad):
    frames, measured = walk
    if bad == "missing":
        measured["distances"][0]["to_seq"] = 99
    elif bad == "untracked":
        frames[1] = frame(1, None, state="PAUSED")
    elif bad == "reverse":
        measured["loop"].update(start_seq=4, end_seq=0)
    else:
        measured["loop"]["start_seq"] = 2
    with pytest.raises(ValueError, match="checkpoint|start_seq"):
        accuracy.score(frames, measured)


@pytest.mark.parametrize("bad", ["empty", "sequence", "timestamp", "nonfinite"])
def test_invalid_trajectory_is_refused(walk, bad):
    frames, measured = walk
    if bad == "empty":
        frames.clear()
    elif bad == "sequence":
        frames[1].seq = 0
    elif bad == "timestamp":
        frames[1].t_ns = frames[0].t_ns
    else:
        frames[1].pose = (float("nan"), 0, 0, 0, 0, 0, 1)
    with pytest.raises(ValueError, match="frames|increasing|finite"):
        accuracy.score(frames, measured)


def test_cli_reads_receiver_session_and_preserves_reference_control_label(tmp_path):
    fixture = HOST.parent / "phonecheck/app/src/test/resources/session_v1"
    header = json.loads((fixture / "frame_header.json").read_text())
    payload = (fixture / "frame_payload.bin").read_bytes()
    session = tmp_path / "session"
    (session / "frames").mkdir(parents=True)
    headers = []
    for seq, x in enumerate((0, 3, 0)):
        row = copy.deepcopy(header)
        row.update(seq=seq, t_ns=(seq + 1) * 1_000_000_000, pose=[x, 0, 0, 0, 0, 0, 1], points=[], anchors=[])
        row.pop("depth")
        row.pop("anchor")
        headers.append(json.dumps(row))
        (session / "frames" / f"{seq:06d}.jpg").write_bytes(payload[:4])
    (session / "frames.jsonl").write_text("\n".join(headers))
    (session / "session.json").write_text(json.dumps({"type": "session", "version": 1, "device": {}, "control": "reference"}))
    measured = tmp_path / "measurements.json"
    measured.write_text(json.dumps({"walk": "synthetic", "environment": "indoor",
        "loop": {"start_seq": 0, "end_seq": 2, "tape_length_m": 6},
        "distances": [{"name": "A-B", "from_seq": 0, "to_seq": 1, "tape_m": 3}]}))
    output = tmp_path / "scores.json"
    run = subprocess.run([sys.executable, str(HOST / "accuracy.py"), "--session", str(session),
                          "--measurements", str(measured), "--out", str(output)], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    result = json.loads(output.read_text())
    assert result["session"]["control"] == "reference"
    assert result["loop"]["closure_mm"] == 0
    assert result["distances"][0]["signed_error_mm"] == 0
