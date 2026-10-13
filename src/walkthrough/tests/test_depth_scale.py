"""Scale corrections for depth whose size is wrong by a different amount in each frame.

A synthetic textured plane is rendered from six known camera positions. The "base" depth
is the true depth times a different factor per frame (1.0 to 1.6), which is the failure seen
with Depth Anything on TUM. Each scale source must undo that factor.
"""

import json
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
from PIL import Image

from src.walkthrough.steps import depth as depth_step
from src.walkthrough.steps import depth_scale
from src.walkthrough.steps.contracts import Calibration, ColourFrame, DepthPrediction

WIDTH, HEIGHT, FOCAL = 320, 240, 260.0
CAMERA = Calibration(WIDTH, HEIGHT, FOCAL, FOCAL, 159.5, 119.5, "x-right_y-down_z-forward")
PLANE_Z0, PLANE_SLOPE = 2.0, 0.25  # world plane z = 2.0 + 0.25 x
POSITIONS = [(0.0, 0.0, 0.0), (0.06, 0.01, 0.02), (0.12, 0.0, 0.05), (0.18, -0.01, 0.03), (0.24, 0.0, 0.0), (0.30, 0.01, -0.02)]
FACTORS = [1.0, 1.3, 0.9, 1.6, 1.1, 0.95]
TEXTURE_SIZE, PIXELS_PER_M = 1000, 300.0
_noise = np.random.default_rng(7).integers(0, 256, (TEXTURE_SIZE, TEXTURE_SIZE)).astype(np.uint8)
TEXTURE = cv2.normalize(cv2.GaussianBlur(_noise, (0, 0), 2.5), None, 0, 255, cv2.NORM_MINMAX)


def _render(position):
    """Colour image and true camera-axis depth of the plane seen from `position` (no rotation)."""
    u, v = np.meshgrid(np.arange(WIDTH, dtype=float), np.arange(HEIGHT, dtype=float))
    ray_x, ray_y = (u - CAMERA.cx) / FOCAL, (v - CAMERA.cy) / FOCAL
    depth = (PLANE_Z0 + PLANE_SLOPE * position[0] - position[2]) / (1.0 - PLANE_SLOPE * ray_x)
    world_x, world_y = position[0] + depth * ray_x, position[1] + depth * ray_y
    map_x = (world_x * PIXELS_PER_M + TEXTURE_SIZE / 2).astype(np.float32)
    map_y = (world_y * PIXELS_PER_M + TEXTURE_SIZE / 2).astype(np.float32)
    grey = cv2.remap(TEXTURE, map_x, map_y, cv2.INTER_LINEAR)
    return np.repeat(grey[:, :, None], 3, axis=2), depth


SCENE = [_render(p) for p in POSITIONS]


def _frames(colours=None):
    colours = colours or [colour for colour, _ in SCENE]
    return [ColourFrame(f"f{i}", float(i), CAMERA, colour) for i, colour in enumerate(colours)]


def _pose(position):
    matrix = np.eye(4)
    matrix[:3, 3] = position
    return matrix


@dataclass(frozen=True)
class FakeBase:
    """A base depth method that is right in shape but wrong in scale by FACTORS[i]."""

    depths: tuple = tuple(true * factor for (_, true), factor in zip(SCENE, FACTORS, strict=True))
    name: str = field(default="fake_base", init=False)
    control: str | None = field(default=None, init=False)

    def load(self):
        def predict(frames, *, run):
            for frame in frames:
                depth = self.depths[int(frame.frame_id[1:])]
                yield DepthPrediction(frame.frame_id, depth.copy(), np.isfinite(depth))

        return predict


class FakeRecorded:
    """Stands in for RecordedSensorDepth: the true depth of the synthetic plane."""

    def __init__(self, root):
        self.root = root

    def load(self):
        def read(frames, *, run):
            for frame in frames:
                true = SCENE[int(frame.frame_id[1:])][1]
                yield DepthPrediction(frame.frame_id, true, np.ones(true.shape, dtype=bool))

        return read


@pytest.fixture
def references(monkeypatch):
    monkeypatch.setattr(depth_scale, "RecordedSensorDepth", FakeRecorded)
    poses = [(float(i), _pose(p)) for i, p in enumerate(POSITIONS)]
    monkeypatch.setattr(depth_scale, "read_reference_poses", lambda path: poses)


def _corrected(scale, frames=None):
    method = depth_scale.ScaleCorrected(FakeBase(), scale)
    return list(method.load()(iter(_frames() if frames is None else frames), run=None))


def _ratios(predictions):
    """Median output/true depth per frame."""
    return np.array(
        [np.median(p.depth[p.valid] / SCENE[i][1][p.valid]) for i, p in enumerate(predictions)]
    )


def test_reference_frame_scale_recovers_true_depth_in_every_frame(references):
    out = _corrected(depth_scale.ReferenceFrameScale(Path("tum")))

    for (_, true), prediction in zip(SCENE, out, strict=True):
        np.testing.assert_allclose(prediction.depth, true, atol=1e-6)


def test_reference_global_scale_applies_one_factor_to_every_frame(references):
    out = _corrected(depth_scale.ReferenceGlobalScale(Path("tum")))

    applied = [p.diagnostics["scale"] for p in out]
    assert len(set(applied)) == 1
    assert applied[0] == pytest.approx(float(np.median([1 / f for f in FACTORS])))


def test_overlap_chain_makes_scale_consistent_from_colour_frames_alone():
    raw = np.array(FACTORS)
    assert raw.max() / raw.min() - 1 > 0.75  # the base varies by 78%

    ratios = _ratios(_corrected(depth_scale.OverlapChainScale()))

    assert ratios.max() / ratios.min() - 1 < 0.03


def test_overlap_chain_keeps_the_base_models_overall_size():
    ratios = _ratios(_corrected(depth_scale.OverlapChainScale()))

    # Corrections are normalised to median 1, so overall size stays the base model's typical one.
    assert np.median(ratios) == pytest.approx(1 / np.median([1 / f for f in FACTORS]), rel=0.03)


def test_pose_triangulated_scale_gives_metric_depth_with_exact_poses(references):
    out = _corrected(depth_scale.PoseTriangulatedScale(Path("groundtruth.txt"), noise_m=0.0))

    ratios = _ratios(out)
    assert np.all(np.abs(ratios - 1) < 0.03)
    assert all(p.diagnostics["points"] >= 20 for p in out)


def test_chain_anchored_to_triangulated_points_is_both_consistent_and_metric(references):
    chain_only = _ratios(_corrected(depth_scale.OverlapChainScale()))
    out = _corrected(
        depth_scale.AnchoredScale(
            depth_scale.OverlapChainScale(), depth_scale.PoseTriangulatedScale(Path("groundtruth.txt"), noise_m=0.0)
        )
    )

    ratios = _ratios(out)
    assert abs(np.median(chain_only) - 1) > 0.03  # the chain alone keeps the base model's size
    assert np.all(np.abs(ratios - 1) < 0.03)  # anchored: right size in every frame
    anchors = {p.diagnostics["anchor"] for p in out}
    assert len(anchors) == 1  # one factor for the whole run
    assert out[0].diagnostics["consistent_scale"] * anchors.pop() == pytest.approx(out[0].diagnostics["scale"])


def test_anchor_ignores_frames_whose_metric_scale_was_interpolated(monkeypatch):
    @dataclass(frozen=True)
    class Fixed:
        values: tuple
        interpolated: tuple
        name: str = field(default="fixed", init=False)
        control: str | None = field(default=None, init=False)

        def load(self):
            return lambda frames, base: [
                depth_scale.FrameScale(v, {"interpolated": i}) for v, i in zip(self.values, self.interpolated, strict=True)
            ]

    anchored = depth_scale.AnchoredScale(Fixed((1.0, 1.0, 1.0), (False,) * 3), Fixed((2.0, 9.0, 2.0), (False, True, False)))

    scales = anchored.load()(_frames()[:3], [None] * 3)

    assert [s.scale for s in scales] == [2.0, 2.0, 2.0]


def test_anchored_control_label_comes_from_its_metric_source():
    chain = depth_scale.OverlapChainScale()
    anchored = depth_scale.AnchoredScale(chain, depth_scale.PoseTriangulatedScale(Path("g")))

    assert anchored.control == "reference"
    assert anchored.name == "overlap_chain_scale+anchored_to+pose_triangulated_scale"


def test_pose_triangulated_scale_fills_a_frame_without_a_pose(monkeypatch):
    monkeypatch.setattr(depth_scale, "RecordedSensorDepth", FakeRecorded)
    poses = [(float(i), _pose(p)) for i, p in enumerate(POSITIONS) if i != 2]
    monkeypatch.setattr(depth_scale, "read_reference_poses", lambda path: poses)

    out = _corrected(depth_scale.PoseTriangulatedScale(Path("groundtruth.txt"), noise_m=0.0))

    assert out[2].diagnostics["interpolated"] is True
    assert out[2].diagnostics["scale"] == pytest.approx(
        (out[1].diagnostics["scale"] + out[3].diagnostics["scale"]) / 2
    )


def test_control_labels_say_which_sources_use_recorded_answers():
    assert depth_scale.ReferenceFrameScale(Path("t")).control == "reference"
    assert depth_scale.ReferenceGlobalScale(Path("t")).control == "reference"
    assert depth_scale.PoseTriangulatedScale(Path("g")).control == "reference"
    chain = depth_scale.OverlapChainScale()
    assert chain.control is None
    assert not any(isinstance(getattr(chain, f.name), Path) for f in fields(chain))  # holds no reference
    assert depth_scale.ScaleCorrected(FakeBase(), chain).control is None
    assert depth_scale.ScaleCorrected(FakeBase(), depth_scale.ReferenceFrameScale(Path("t"))).control == "reference"


def test_name_and_saved_settings_name_both_parts():
    method = depth_scale.ScaleCorrected(FakeBase(), depth_scale.OverlapChainScale())

    assert method.name == "fake_base+overlap_chain_scale"
    saved = json.loads(json.dumps(asdict(method), default=str))
    assert saved["name"] == method.name
    assert saved["scale"]["partners"] == [1, 2, 4, 8]


def test_a_frame_with_no_usable_partner_keeps_the_previous_correction_and_warns():
    colours = [colour for colour, _ in SCENE[:3]]
    colours[2] = np.full_like(colours[2], 128)  # nothing to track
    frames = _frames(colours)

    with pytest.warns(UserWarning, match="f2"):
        out = _corrected(depth_scale.OverlapChainScale(), frames)

    assert out[2].diagnostics["fallback"] is True
    assert out[2].diagnostics["partners_used"] == 0
    assert out[2].diagnostics["scale"] == pytest.approx(out[1].diagnostics["scale"])
    assert out[1].diagnostics["fallback"] is False


def test_no_frames_gives_no_predictions():
    assert _corrected(depth_scale.OverlapChainScale(), frames=[]) == []


def test_inputs_are_not_changed():
    base = FakeBase()
    before = [d.copy() for d in base.depths]
    frames = _frames()
    colours = [f.colour.copy() for f in frames]

    list(depth_scale.ScaleCorrected(base, depth_scale.OverlapChainScale()).load()(iter(frames), run=None))

    assert all(np.array_equal(a, b) for a, b in zip(base.depths, before, strict=True))
    assert all(np.array_equal(f.colour, c) for f, c in zip(frames, colours, strict=True))


@pytest.mark.parametrize("partners", [(), (0,), (1, -2)])
def test_chain_partners_must_be_positive(partners):
    with pytest.raises(ValueError, match="partners"):
        depth_scale.OverlapChainScale(partners=partners)


# Through the depth layer: saved diagnostics, rebuilt masks, refused values.

SMALL = (6, 8)


@dataclass(frozen=True)
class FixedScale:
    """A scale source that applies one chosen value with one chosen diagnostic."""

    value: float = 1.5
    extra: object = None
    name: str = field(default="fixed_scale", init=False)
    control: str | None = field(default=None, init=False)

    def load(self):
        def scale(frames, predictions):
            extra = {} if self.extra is None else {"extra": self.extra}
            return [depth_scale.FrameScale(self.value, extra) for _ in predictions]

        return scale


@dataclass(frozen=True)
class SmallBase:
    depth_m: float = 2.0
    name: str = field(default="small_base", init=False)
    control: str | None = field(default=None, init=False)

    def load(self):
        def predict(frames, *, run):
            for frame in frames:
                depth = np.full(SMALL, self.depth_m)
                depth[0, 0] = 15.0  # 22.5 m after a 1.5x scale: beyond the 20 m cap
                yield DepthPrediction(frame.frame_id, depth, np.ones(SMALL, dtype=bool))

        return predict


def _layer(tmp_path, scale):
    calibration = Calibration(SMALL[1], SMALL[0], 5.0, 5.0, 4.0, 3.0, "x-right_y-down_z-forward")
    rows = []
    for index in range(2):
        Image.fromarray(np.zeros((*SMALL, 3), dtype=np.uint8), mode="RGB").save(tmp_path / f"{index}.png")
        rows.append({"frame_id": f"frame-{index}", "timestamp_s": float(index), "image": f"{index}.png",
                     "calibration": asdict(calibration), "phone_grid": None})
    context = SimpleNamespace(path=tmp_path, measure=lambda *_a, **_k: nullcontext())
    return depth_step.run(context, {"frames": rows}, depth_scale.ScaleCorrected(SmallBase(), scale))


def test_diagnostics_are_saved_as_plain_numbers_and_scaled_pixels_past_the_cap_are_invalid(tmp_path):
    row, output = _layer(tmp_path, FixedScale(1.5, np.float32(0.25)))

    assert row.status == "complete", row.reason
    saved = json.loads((tmp_path / "output/predictions/depth.json").read_text())
    assert saved["frames"][0]["method_diagnostics"] == {"scale": 1.5, "extra": 0.25}
    with np.load(tmp_path / output["frames"][0]["arrays"]) as arrays:
        assert not arrays["valid"][0, 0]
        assert arrays["valid"].sum() == SMALL[0] * SMALL[1] - 1
        assert arrays["depth"][1, 1] == pytest.approx(3.0)


def test_a_nan_diagnostic_fails_the_layer_with_a_named_status(tmp_path):
    row, output = _layer(tmp_path, FixedScale(1.5, float("nan")))

    assert row.status == "failed"
    assert "extra" in row.reason
    assert output is None


def test_a_non_positive_scale_makes_every_pixel_invalid_and_fails_the_frame(tmp_path):
    row, _ = _layer(tmp_path, FixedScale(-1.0))

    assert row.status == "failed"
    assert "scale" in row.reason
