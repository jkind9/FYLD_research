# Depth

Predicts camera-plane depth from one RGB image. `load_model` loads the local model once
and returns a callable on arrays. `predict(model, image, pose)` turns the image upright
for prediction, then restores the depth and validity to the recorded pixel grid.
Omitting `pose` keeps the recorded orientation, as the current live pipeline requires.
The scale stage must fit these depths to measured distances before fusion.

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| `image` | H × W × 3 uint8 RGB | Recorded pixel grid |
| `pose` | Optional 4 × 4 float64 `world_from_camera` | Metres; OpenCV camera axes in ARCore world, y up |
| `model` | Callable taking RGB, returning depth and validity arrays | Loaded once; no recording or calibration object |
| Returned depth | H × W float64; NaN where invalid | Learned camera-plane metres, with scale bias |
| Returned validity | H × W bool | Finite, positive depth no greater than `max_depth_m` |

## How it works

1. Choose the clockwise quarter turns that bring image down closest to world down, when a pose is supplied.
2. Pass a contiguous upright RGB array to the loaded model, whose training images were upright.
3. Resize model output with bicubic interpolation to the input image dimensions, with `align_corners=False`.
4. Convert to float64 metres and mask nonfinite, nonpositive and over-limit pixels, preserving existing results.
5. Reverse the image rotation on both outputs so scale and fusion keep their recorded pixel coordinates.

## Run it

Run in `.venv-sitescan` from the repository root; weights stay local:

```python
from sitescan import depth, session

model = depth.load_model("data/models/depth_anything_v2_metric_indoor_small")
frame = next(session.frames("tests/fixtures/tum_desk_20"))
learned, valid = depth.predict(model, frame.image, frame.pose)
print(learned.shape, learned.dtype, valid.shape, valid.dtype)
# (480, 640) float64 (480, 640) bool
```

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| Model | Depth Anything V2 Metric Indoor Small | Adopted CPU model; local weights only | [Model manifest](../../models/manifest.toml) |
| `device` | `cpu` | Current live target; the GPU is reserved for other work | [Project plan](../../PROJECT_PLAN.md) |
| `threads` | 16 | About 250 ms per depth frame on the desktop CPU; None preserves the caller's thread setting | [Measured chain](../../DESIGN.md#2-where-the-project-is) |
| `max_depth_m` | 20 m | Preserve the adopted model adapter's validity range | [Adapter tests](../../src/walkthrough/tests/test_adapters.py) |
| `pose` | None | Preserve recorded input for existing live callers; room callers supply a pose | [Current pipeline differences](../../DESIGN.md#3-what-the-code-looks-like-today) |
| Upright rule | World down | Upright input reduced ARCore AbsRel from 0.080 to 0.058 on 20 frames | [Orientation experiment](../../experiments/01_camera_capture_delivery/README.md#depth-and-orientation-probe-7-november-2026-task106) |

## Limits

The model reads 1.34–1.41 times too far on indoor reference recordings, with per-frame
factors from 0.86 to 2.09. Fused shape errors remain about 8–16 cm even with known camera
positions. Edges can mix foreground and background depth. These outputs need the scale
and cleanup stages. The validity mask keeps positive values below 0.1 m for compatibility;
fusion applies its own 0.1 m near limit. A phone runtime has not been measured.

`load_model` currently uses Transformers and PyTorch internally. A later runtime can
return the same array callable without changing `predict` or adding a wrapper class.
The old walkthrough keeps only record adaptation and experiment input checks.

## Tests

`python -B -m pytest -q tests/test_sitescan_depth.py src/live/tests/test_orientation_control.py`
checks all four rotations, restoring the recorded grid, camera projections under rotation,
recorded input without a pose, contiguous model input, masking, interpolation and local
model loading. Walkthrough adapter tests check its retained record contract. The golden
lane checks both orchestrators with real local weights; full-room checks preserve counts
and map dimensions.
