# 9. Measuring accuracy

A 3D result that looks right can be badly wrong. This chapter covers the recorded data the project tests on, the reference answers that come with it, and the scores used in every other chapter, including one scoring mistake the project made and corrected.

## The rule: references only score

A *reference* (or ground truth) is an independently measured answer: a motion-capture camera path, a depth sensor's reading, a surveyed surface. It may be used to score a method and nothing else. If a reference leaks into a method (for example, choosing settings by looking at the scored result), the score no longer says how the method would do without it. Where the project uses a reference inside a method on purpose, to find an upper bound, the row is labelled a *control* (for example "best-fit size", "exact per-frame size").

## Recordings used

| Recording | What it is | Reference answers | Used for |
|---|---|---|---|
| TUM RGB-D `freiburg1_xyz` | Kinect colour and depth, handheld over a desk, the camera moved mainly along its x, y and z axes; 399 frames at every second frame | Motion-capture camera path; Kinect depth | Tracking, depth, surfaces (Kinect-fused reference) |
| TUM RGB-D `freiburg1_desk` | Same sensor, a sweep round a cluttered desk; 298 frames at every second frame | Same | Same; harder, more rotation |
| ICL-NUIM living room 2 | Rendered (synthetic) colour and depth of a living room; 440 frames at every second frame | Exact camera path; exact surface model | Surfaces against an exact reference; large textureless walls |

TUM is real but its reference surface is itself built from Kinect depth, so it carries sensor noise and about 30 mm of timing error between the camera and the motion-capture clock. ICL is exact but synthetic: no real lens, no motion blur. Neither is a worksite, and neither is a phone. Results here say what a method can do under controlled conditions, not on site.

Formats: images 640 × 480; depth as 16-bit PNG, divide by 5,000 for metres, zero means missing; paths as `time x y z qx qy qz qw` lines. Licences: TUM data CC BY 4.0. See [research/datasets_and_benchmarks](../research/datasets_and_benchmarks/README.md) for these and other candidates (ETH3D, EuRoC).

## Scores for a camera path

Lining up comes first, because an estimated path lives in its own coordinate frame.

| Score | How | When to use |
|---|---|---|
| **First frame** | Pin both paths together at frame 1, then measure | The project's early score. Not standard; see below. |
| **Best fit (rigid)** | Find the rotation and shift that line the whole path up best (Umeyama/Horn method), then RMSE of position error | Methods that know real size (depth sensor, IMU) |
| **Best fit with size** | Same, plus one overall scale factor | Image-only methods, which have no size. The score published for monocular SLAM. |
| **Relative pose error, 1 s** | Error of each 1-second motion | Drift, independent of where the path started |

> **Project result: the first-frame score roughly doubled the error and hid the path's size.** Rescoring the same saved paths: Kinect-depth tracker on xyz 67 mm first-frame against 34 mm best fit; on desk 220 mm against 112 mm. Raw Depth Anything's xyz path was about 16 times too long (fitted size 0.06), which first-frame scoring did not show. All camera results in these chapters use best fit. (Task70, `experiments/03_camera_pose_estimation/src/evaluation.py`.)

The fitted size itself is informative: well below 1 means the estimated path is too long, above 1 too short.

## Scores for depth

- **AbsRel**: mean of `|predicted − true| / true`.
- **RMSE** in metres, and **δ1**: share of pixels within 25% of the truth.
- **Raw** (is it right in metres?) against **aligned** (fit each frame's scale and shift to the reference first: is the shape right?). Report both and say which.

## Scores for a surface

- **Accuracy**: distance from each reconstructed point to the nearest reference point (mean, RMSE, share within 5 cm).
- **Coverage**: share of the reference with a reconstructed point within 5 cm.

Always both (chapter 5 explains why).

## Speed

Say what was timed. "Frames per second" can mean the model alone, or the whole run including reading files, preparing inputs and saving outputs; the project reports both where it can. Published speeds belong to the authors' hardware. The owner's floor is 1 frame per second end to end.

## Habits worth copying

- **Seal every run.** Each run folder records its inputs (with hashes), settings, code snapshot, timing and outputs, and is never overwritten (`experiments/shared/runs.py`).
- **Write settings down with their source.** Every script has a `HYPERPARAMETERS` table saying where each value came from: inherited, owner ruling, or "proposed, not ruled".
- **Pick the setting before seeing the score it is judged on.** Task72 chose each recording's SfM run by camera score before any surface was scored.
- **Keep negative results.** Prompt Depth Anything (Task79) and the failed fr1 calibration are recorded with their numbers.

## Further reading

- [TUM RGB-D note](../research/datasets_and_benchmarks/tum_rgbd.md), [ICL-NUIM note](../research/datasets_and_benchmarks/icl_nuim.md), [dataset catalogue](../research/datasets_and_benchmarks/dataset_catalog.md).
- `experiments/datasets/README.md` for download status and permissions.
- `research/start_here.md`, "Five different things to measure".
