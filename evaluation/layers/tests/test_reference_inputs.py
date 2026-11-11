"""Reference adapters match independently and release decoded inputs as they advance."""

import gc
import weakref
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from experiments.shared.contracts import Calibration
from src.walkthrough.steps.contracts import ColourFrame, RGBDFrame
from src.walkthrough.steps.depth import RecordedSensorDepth
from src.walkthrough.steps.tracking import ReferencePoses

CAMERA = Calibration(2, 2, 2, 2, 0.5, 0.5, "x-right_y-down_z-forward")
# Original tables: data/tum/rgbd_dataset_freiburg1_xyz/{rgb,depth}.txt, first 20 rows.
# Literal source timestamps keep this regression portable without the image download.
XYZ_COLOUR_TIMES = (
    1305031102.175304,
    1305031102.211214,
    1305031102.243211,
    1305031102.275326,
    1305031102.311267,
    1305031102.343233,
    1305031102.375329,
    1305031102.411258,
    1305031102.443271,
    1305031102.475318,
    1305031102.511219,
    1305031102.543220,
    1305031102.575286,
    1305031102.611233,
    1305031102.643265,
    1305031102.675285,
    1305031102.711263,
    1305031102.743234,
    1305031102.775472,
    1305031102.811232,
)
XYZ_DEPTH_TIMES = (
    1305031102.160407,
    1305031102.194330,
    1305031102.226738,
    1305031102.262886,
    1305031102.295279,
    1305031102.329195,
    1305031102.363013,
    1305031102.394772,
    1305031102.427815,
    1305031102.462395,
    1305031102.494271,
    1305031102.526330,
    1305031102.562224,
    1305031102.594158,
    1305031102.626818,
    1305031102.663273,
    1305031102.695165,
    1305031102.728423,
    1305031102.763549,
    1305031102.794978,
)
XYZ_NEAREST_ROWS = (
    0,
    2,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    11,
    11,
    12,
    14,
    14,
    15,
    16,
    17,
    18,
    19,
)


def colour_frame(index: int, timestamp: float | None) -> ColourFrame:
    return ColourFrame(f"frame-{index}", timestamp, CAMERA, np.zeros((2, 2, 3), np.uint8))


def rgbd_frame(index: int, timestamp: float) -> RGBDFrame:
    return RGBDFrame(
        f"frame-{index}",
        timestamp,
        timestamp,
        CAMERA,
        np.zeros((2, 2, 3), np.uint8),
        np.ones((2, 2)),
        np.ones((2, 2), bool),
    )


def write_depth_table(root: Path, timestamps: tuple[float, ...]) -> None:
    (root / "depth.txt").write_text(
        "".join(f"{timestamp:.6f} depth/{index}.png\n" for index, timestamp in enumerate(timestamps)),
        encoding="utf-8",
    )


def write_pose_table(root: Path, timestamps: tuple[float, ...]) -> Path:
    path = root / "groundtruth.txt"
    path.write_text(
        "".join(f"{timestamp:.6f} {index} 0 0 0 0 0 1\n" for index, timestamp in enumerate(timestamps)),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def encoded_depth(monkeypatch):
    """Mock only image decoding; real table readers and adapter matching still run."""
    opened = []

    def open_depth(path):
        opened.append(Path(path).name)
        image = Image.fromarray(np.full((2, 2), (int(Path(path).stem) + 1) * 100, np.uint16))
        image.format = "PNG"
        return image

    monkeypatch.setattr(Image, "open", open_depth)
    return opened


def test_xyz_first_twenty_depth_frames_reuse_nearest_recording(tmp_path, encoded_depth):
    write_depth_table(tmp_path, XYZ_DEPTH_TIMES)
    estimate = RecordedSensorDepth(tmp_path).load()
    predictions = list(
        estimate(
            (colour_frame(index, timestamp) for index, timestamp in enumerate(XYZ_COLOUR_TIMES)),
            run=None,
        )
    )
    assert [prediction.frame_id for prediction in predictions] == [f"frame-{index}" for index in range(20)]
    assert encoded_depth == [f"{index}.png" for index in XYZ_NEAREST_ROWS]
    for prediction, index in zip(predictions, XYZ_NEAREST_ROWS, strict=True):
        np.testing.assert_array_equal(prediction.depth, np.full((2, 2), (index + 1) * 100 / 5000))
        assert prediction.valid.all()


@pytest.mark.parametrize("adapter", ["depth", "pose"])
def test_reference_reuse_preserves_incoming_frame_order(tmp_path, encoded_depth, adapter):
    timestamps = (2.0, 1.0, 2.0)
    if adapter == "depth":
        write_depth_table(tmp_path, (1.0, 2.0))
        estimate = RecordedSensorDepth(tmp_path, tolerance_s=0).load()
        predictions = list(estimate((colour_frame(i, t) for i, t in enumerate(timestamps)), run=None))
        assert [prediction.frame_id for prediction in predictions] == [
            "frame-0",
            "frame-1",
            "frame-2",
        ]
        assert encoded_depth == ["1.png", "0.png", "1.png"]
    else:
        estimate = ReferencePoses(write_pose_table(tmp_path, (1.0, 2.0)), tolerance_s=0).load()
        records = estimate((rgbd_frame(i, t) for i, t in enumerate(timestamps)), run=None)
        assert [record.frame_id for record in records] == [
            "frame-0",
            "frame-1",
            "frame-2",
        ]
        assert [record.timestamp_s for record in records] == list(timestamps)
        assert [record.pose.matrix[0, 3] for record in records] == [1, 0, 1]
        assert all(record.status == "supplied" and record.pose.source == "supplied" for record in records)


def test_pose_matching_reuses_reference_at_real_xyz_collisions(tmp_path):
    # The XYZ depth clock supplies the collision pattern; pose translations are markers.
    estimate = ReferencePoses(write_pose_table(tmp_path, XYZ_DEPTH_TIMES)).load()
    records = estimate(
        (rgbd_frame(index, timestamp) for index, timestamp in enumerate(XYZ_COLOUR_TIMES)),
        run=None,
    )
    assert [record.frame_id for record in records] == [f"frame-{index}" for index in range(20)]
    assert all(record.status == "supplied" and record.pose is not None for record in records)
    assert [record.pose.matrix[0, 3] for record in records] == list(XYZ_NEAREST_ROWS)


@pytest.mark.parametrize("adapter", ["depth", "pose"])
def test_equal_distance_chooses_earlier_reference_at_inclusive_boundary(tmp_path, encoded_depth, adapter):
    if adapter == "depth":
        write_depth_table(tmp_path, (1.0, 3.0))
        estimate = RecordedSensorDepth(tmp_path, tolerance_s=1).load()
        prediction = next(estimate(iter([colour_frame(0, 2.0)]), run=None))
        np.testing.assert_array_equal(prediction.depth, np.full((2, 2), 0.02))
        assert encoded_depth == ["0.png"]
    else:
        estimate = ReferencePoses(write_pose_table(tmp_path, (1.0, 3.0)), tolerance_s=1).load()
        record = estimate(iter([rgbd_frame(0, 2.0)]), run=None)[0]
        assert record.pose.matrix[0, 3] == 0
        assert record.status == "supplied"


@pytest.mark.parametrize("adapter", ["depth", "pose"])
@pytest.mark.parametrize("source,reference", [(1.02, 1.0), (1.0, 1.02)])
def test_decimal_tolerance_boundary_is_included(tmp_path, encoded_depth, adapter, source, reference):
    if adapter == "depth":
        write_depth_table(tmp_path, (reference,))
        estimate = RecordedSensorDepth(tmp_path, tolerance_s=0.02).load()
        prediction = next(estimate(iter([colour_frame(0, source)]), run=None))
        assert prediction.frame_id == "frame-0"
        assert encoded_depth == ["0.png"]
    else:
        estimate = ReferencePoses(write_pose_table(tmp_path, (reference,)), tolerance_s=0.02).load()
        record = estimate(iter([rgbd_frame(0, source)]), run=None)[0]
        assert record.status == "supplied" and record.pose is not None


def test_real_depth_gap_raises_with_frame_identity(tmp_path, encoded_depth):
    write_depth_table(tmp_path, (1.0,))
    predictions = RecordedSensorDepth(tmp_path, tolerance_s=0.02).load()(
        iter([colour_frame(0, 1.0), colour_frame(1, 1.1)]),
        run=None,
    )
    assert next(predictions).frame_id == "frame-0"
    with pytest.raises(ValueError, match="frame-1: No sensor depth within 0.02 s"):
        next(predictions)
    assert encoded_depth == ["0.png"]


def test_missing_reference_pose_has_lost_status_and_reason(tmp_path):
    estimate = ReferencePoses(write_pose_table(tmp_path, (1.0,))).load()
    records = estimate(iter([rgbd_frame(0, 1.0), rgbd_frame(1, 1.1)]), run=None)
    assert records[0].status == "supplied" and records[0].pose is not None
    assert records[1].frame_id == "frame-1" and records[1].timestamp_s == 1.1
    assert records[1].status == "lost" and records[1].pose is None
    assert records[1].reason == "No ground-truth pose within 0.02 s"


@pytest.mark.parametrize("adapter", ["depth", "pose"])
def test_reference_adapters_release_previous_decoded_frames(tmp_path, encoded_depth, adapter):
    first_references = []

    def frames() -> Iterator[ColourFrame | RGBDFrame]:
        for index in range(4):
            if index == 2:
                gc.collect()
                assert all(
                    reference() is None for reference in first_references
                ), "adapter retained the first decoded frame"
            frame = colour_frame(index, index + 1.0) if adapter == "depth" else rgbd_frame(index, index + 1.0)
            if index == 0:
                first_references.extend([weakref.ref(frame), weakref.ref(frame.colour)])
                if adapter == "pose":
                    first_references.extend([weakref.ref(frame.depth), weakref.ref(frame.valid)])
            yield frame

    if adapter == "depth":
        write_depth_table(tmp_path, (1.0, 2.0, 3.0, 4.0))
        output = list(RecordedSensorDepth(tmp_path).load()(frames(), run=None))
    else:
        output = ReferencePoses(write_pose_table(tmp_path, (1.0, 2.0, 3.0, 4.0))).load()(frames(), run=None)
    assert len(output) == 4


@pytest.mark.parametrize("adapter", ["depth", "pose"])
@pytest.mark.parametrize("tolerance", [-1, float("nan"), float("inf"), None, "bad"])
def test_reference_choices_reject_invalid_tolerance(tmp_path, adapter, tolerance):
    with pytest.raises(ValueError, match="tolerance"):
        if adapter == "depth":
            RecordedSensorDepth(tmp_path, tolerance_s=tolerance)
        else:
            ReferencePoses(tmp_path / "groundtruth.txt", tolerance_s=tolerance)


@pytest.mark.parametrize("field", ["units_per_metre", "max_depth_m"])
@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), None, "bad"])
def test_recorded_depth_rejects_invalid_scale_or_range(tmp_path, field, value):
    with pytest.raises(ValueError, match=field):
        RecordedSensorDepth(tmp_path, **{field: value})


def test_recorded_depth_uses_named_scale_and_excludes_maximum(tmp_path, monkeypatch):
    write_depth_table(tmp_path, (1.0,))

    def open_depth(path):
        image = Image.fromarray(np.array([[0, 100], [299, 300]], np.uint16))
        image.format = "PNG"
        return image

    monkeypatch.setattr(Image, "open", open_depth)
    estimate = RecordedSensorDepth(tmp_path, units_per_metre=100, max_depth_m=3).load()
    prediction = next(estimate(iter([colour_frame(0, 1.0)]), run=None))
    np.testing.assert_array_equal(prediction.depth, [[np.nan, 1], [2.99, 3]])
    np.testing.assert_array_equal(prediction.valid, [[False, True], [True, False]])


@pytest.mark.parametrize("timestamp", [None, float("nan"), float("inf"), "bad"])
def test_recorded_depth_refuses_missing_or_invalid_source_time(tmp_path, encoded_depth, timestamp):
    write_depth_table(tmp_path, (1.0,))
    predictions = RecordedSensorDepth(tmp_path).load()(iter([colour_frame(0, timestamp)]), run=None)
    with pytest.raises(ValueError, match="timestamp"):
        next(predictions)
    assert encoded_depth == []


def test_recorded_depth_accepts_numpy_float_timestamp(tmp_path, encoded_depth):
    write_depth_table(tmp_path, (1.0,))
    estimate = RecordedSensorDepth(tmp_path).load()
    prediction = next(estimate(iter([colour_frame(0, np.float64(1.0))]), run=None))
    assert prediction.frame_id == "frame-0"
    assert encoded_depth == ["0.png"]


@pytest.mark.parametrize("adapter", ["depth", "pose"])
def test_reference_adapter_empty_input_returns_empty_output(tmp_path, encoded_depth, adapter):
    if adapter == "depth":
        write_depth_table(tmp_path, (1.0,))
        assert list(RecordedSensorDepth(tmp_path).load()(iter(()), run=None)) == []
        assert encoded_depth == []
    else:
        assert ReferencePoses(write_pose_table(tmp_path, (1.0,))).load()(iter(()), run=None) == []


@pytest.mark.parametrize("adapter", ["depth", "pose"])
@pytest.mark.parametrize("timestamps", [(), (2.0, 1.0), (1.0, 1.0), (float("nan"),)])
def test_reference_adapter_refuses_invalid_reference_tables(tmp_path, adapter, timestamps):
    if adapter == "depth":
        write_depth_table(tmp_path, timestamps)
        choice = RecordedSensorDepth(tmp_path)
    else:
        choice = ReferencePoses(write_pose_table(tmp_path, timestamps))
    with pytest.raises(ValueError):
        choice.load()
