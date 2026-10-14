# Structure from motion (standalone)

This folder answers one question: **can the camera path and the scene's 3D structure be recovered from the images alone, more accurately than the walkthrough's depth-based tracker?** It runs established structure-from-motion software on recordings we already have and scores the result against their true camera paths and surfaces. It does not change the six-layer walkthrough in `src/walkthrough`; its saved outputs are files that later tasks read.

The owner asked for this on 13 October 2026: standalone SfM experiments in their own folder, on existing data, with speed and edge deployment in mind but not the focus. Tasks: [67](../../task_list/open/67_track_the_camera_without_depth_so_depth_scale_erro.md) (camera path), [71](../../task_list/open/71_rebuild_surfaces_from_the_recorded_camera_poses_to.md) (surfaces from true poses), [72](../../task_list/open/72_scale_learned_depth_to_the_image_only_tracker_s_3d.md) (dense structure from the SfM path), [76](../../task_list/open/76_read_saved_sfm_camera_paths_and_points_into_the_wa.md) (walkthrough readers). Background: [the tracking review](../../research/camera_tracking_and_slam/tracking_review_2026-10-13.md).

## How it works

Structure from motion (SfM) finds the same points in many images, then solves every camera position and every 3D point together so that the points project back onto the images (bundle adjustment). From images alone the result has no real-world size; one overall size must come from elsewhere (a known distance, the phone's motion tracking, or a depth model).

One run takes one recording and one feature type:

1. **Features**: SIFT (classic) or ALIKED (learned), per image.
2. **Matching**: each image against its 10 neighbours in time plus a few further back (sequential matching with quadratic overlap); SIFT by nearest descriptor, ALIKED by LightGlue (learned).
3. **Mapping**, twice on the same matches: the incremental mapper (adds one image at a time, refines often) and the global mapper (GLOMAP: solves all rotations, then all positions, then refines once).
4. **Export** per mapper: the camera path, the sparse 3D points and which pixel in which frame saw each point.
5. **Scores** per mapper: camera path against the true path (Task70's best-fit scores), frames placed, and a size set once from Depth Anything's depth at the observed points.

## Running

COLMAP is the official 4.2.1 Windows build without CUDA, downloaded on 2026-10-13 from `https://github.com/colmap/colmap/releases/download/4.2.1/colmap-x64-windows-nocuda.zip` (SHA-256 `c493d88cb4a43f21afba42cb55bf786e5434a0420e73db0ba1454c5d8b3686ae`) and unpacked to `third_party/colmap-4.2.1-windows-nocuda/` (ignored by Git). The pycolmap 4.2.1 Windows wheel can read models but aborts on ALIKED extraction, so every COLMAP stage runs through the command-line build and pycolmap only reads the saved models.

```text
python -m venv .venv-sfm
.venv-sfm\Scripts\python -m pip install -r experiments\sfm\requirements.txt
.venv-sfm\Scripts\python -m experiments.sfm.run_sfm --recording tum:outputs/task65_clips/rgbd_dataset_freiburg1_desk_every2 ^
    --features sift --run-root experiments/sfm/runs/tum_desk ^
    --depth-run outputs/task65_runs/desk/depth-anything/20261008T160022.468281Z_86f38337bb0b4db9ad2a2126b3a0b646
.venv-sfm\Scripts\python -m pytest experiments\sfm\tests -p no:cacheprovider --import-mode=importlib
```

`--recording` is `tum:<folder>` (a TUM recording or Task65 clip with `rgb.txt` and `groundtruth.txt`) or `icl:<folder>` (an ICL-NUIM trajectory folder). `--depth-run` names a finished walkthrough run whose Depth Anything maps set the size. The tests need `.venv-sfm` (pycolmap) and skip elsewhere; the end-to-end test also needs the COLMAP build and takes about 5 s.

| File | Responsibility |
|---|---|
| `src/sequences.py` | Recording readers: ordered images, frame IDs, times, camera, ground truth (ICL converted to a right-handed y-down world) |
| `src/reconstruct.py` | COLMAP command-line stages with timing and logs; models read back with pycolmap |
| `src/export.py` | `frames.json` (every frame's model and camera-to-world pose, or unplaced), `trajectory.txt` (largest model, TUM format, SfM units), `points.npz`, `observations.npz` |
| `src/scoring.py` | Camera scores through experiment 03's `evaluate`; size from a depth model |
| `run_sfm.py` | Command line, `HYPERPARAMETERS`, one sealed run folder per recording and feature type |

Each run folder holds `input/sequence.json` (images with SHA-256), `debug/colmap/` (database, models, logs), `output/<mapper>/` (exports and `scores.json`), `output/summary.json` and the usual metadata (timing, source snapshot, manifest).

## Settings

| Setting | Value | Source |
|---|---|---|
| TUM camera | PINHOLE 525, 525, 319.5, 239.5, no distortion | TUM page's recommended default, also experiment 03; the published fr1 distortion set failed (below) |
| ICL camera | PINHOLE 481.2, 480, 319.5, 239.5 | data/icl_nuim/conventions.json, fy sign flipped with the reference |
| Calibration refinement | off | proposed by Claude 2026-10-13 |
| Features | SIFT ≤ 8,192; ALIKED_N16ROT ≤ 2,048, score ≥ 0.2 | COLMAP 4.2.1 defaults |
| Matching | sequential, overlap 10, quadratic overlap, no loop detection; SIFT brute force or ALIKED LightGlue | COLMAP 4.2.1 defaults |
| Mappers | incremental and global, defaults, seed 0, multiple models kept | COLMAP defaults; seed proposed by Claude |
| Frames | TUM: Task65 every-2nd clips (xyz 399, desk 298); ICL: every 2nd posed frame (440) | Task65; ICL spacing proposed by Claude |
| Size from depth model | median over frames of median(Depth Anything / SfM depth) at observed points, ≥ 20 points per frame | proposed by Claude 2026-10-13 |
| Devices | CPU only, 32 threads | owner 2026-10-08 |

## Results

Camera path error on the same every-2nd-frame clips as Task65. "Best fit with size" lines up the whole path and fits one overall size: the score published for image-only methods, and the fairest comparison of path shape. "Depth-model size" sets the size from Depth Anything instead (deployable without other sensors) and then lines up the path; it inherits Depth Anything's overall bias.

### All runs (from `python -m experiments.sfm.report`)

| Recording | Camera | Features | Mapper | Placed (largest model) | Models | Best fit with size | Fitted size | Depth-model size, error | Seconds | Frames per second |
|---|---|---|---|---:|---:|---:|---:|---|---:|---:|
| trajectory2 | icl | sift | global | 429 / 440 | 1 | 57.2 mm | 0.275 | —, — | 62 | 7.09 |
| trajectory2 | icl | sift | incremental | 433 / 440 | 1 | 34.1 mm | 0.277 | —, — | 195 | 2.26 |
| trajectory2 | icl | aliked | global | 440 / 440 | 1 | 947.1 mm | 0.038 | —, — | 195 | 2.26 |
| trajectory2 | icl | aliked | incremental | 438 / 440 | 1 | 475.8 mm | 0.243 | —, — | 271 | 1.63 |
| rgbd_dataset_freiburg1_desk_every2 | fr1 | sift | global | failed | — | — | — | — | — | — |
| rgbd_dataset_freiburg1_desk_every2 | fr1 | sift | incremental | failed | — | — | — | — | — | — |
| rgbd_dataset_freiburg1_desk_every2 | default | aliked | global | 298 / 298 | 1 | 446.6 mm | 0.170 | 0.995, 3622 mm | 231 | 1.29 |
| rgbd_dataset_freiburg1_desk_every2 | default | aliked | incremental | 298 / 298 | 1 | 21.5 mm | 0.233 | 0.324, 339 mm | 321 | 0.93 |
| rgbd_dataset_freiburg1_desk_every2 | default | sift | global | 298 / 298 | 1 | 23.6 mm | 0.238 | 0.338, 361 mm | 79 | 3.78 |
| rgbd_dataset_freiburg1_desk_every2 | default | sift | incremental | 298 / 298 | 1 | 24.0 mm | 0.234 | 0.330, 357 mm | 123 | 2.42 |
| rgbd_dataset_freiburg1_xyz_every2 | default | sift | global | 399 / 399 | 1 | 11.9 mm | 0.048 | 0.062, 58 mm | 134 | 2.97 |
| rgbd_dataset_freiburg1_xyz_every2 | default | sift | incremental | 399 / 399 | 1 | 11.9 mm | 0.048 | 0.062, 58 mm | 340 | 1.17 |
| rgbd_dataset_freiburg1_xyz_every2 | default | aliked | global | 399 / 399 | 1 | 185.8 mm | 0.000 | 0.064, 35405 mm | 382 | 1.05 |
| rgbd_dataset_freiburg1_xyz_every2 | default | aliked | incremental | 399 / 399 | 1 | 12.4 mm | 0.048 | 0.061, 55 mm | 507 | 0.79 |


"Placed" counts frames in the largest model. "Seconds" is extraction + matching + that mapper, offline over the whole clip on 32 CPU threads. The two failed desk rows use the published fr1 distortion set (below).

### Against the walkthrough tracker and published results (best fit with size)

| Recording | SfM, SIFT | Walkthrough tracker, Kinect depth | Walkthrough tracker, Depth Anything + overlap chain | Published monocular SLAM, every frame |
|---|---:|---:|---:|---:|
| TUM fr1/xyz, 399 frames | 11.9 mm (both mappers) | 34 mm | 128 mm | 9-12 mm |
| TUM fr1/desk, 298 frames | 24.0 mm incremental, 23.6 mm global | 112 mm | 438 mm | 16-18 mm |
| ICL living room 2, 440 frames | 34.1 mm incremental (433 placed), 57.2 mm global (429 placed) | not run | not run | — |

Walkthrough rows are Task65 runs rescored by Task70; published rows are the MASt3R-SLAM paper's Table 1 (ORB-SLAM3, DPV-SLAM, DROID-SLAM, MASt3R-SLAM), which use every frame rather than every second one.

What this shows:

- **From images alone, SfM places every TUM frame in one model and its path shape is 2.9 times (xyz) and 4.7 times (desk) closer to the truth than the walkthrough tracker fed with the Kinect sensor's own depth.** It is close to the published systems that use every frame. The walkthrough tracker, not only learned depth, limits the camera path.
- **The incremental mapper is more accurate on ICL (34 against 57 mm) and equal on TUM; the global mapper is 1.6-3.1 times faster (desk 79 against 123 s, xyz 134 against 340 s, ICL 62 against 195 s).** ICL's synthetic room has large textureless walls; the global mapper drops 11 frames there.
- **ALIKED + LightGlue (learned features) helps only with the incremental mapper on TUM, and fails elsewhere.** Incremental: desk 21.5 mm (the best desk result), xyz 12.4 mm (SIFT 11.9 mm). Global: desk 447 mm and xyz 186 mm with a fitted size near 0, so its positions collapsed although every frame was registered. On ICL both ALIKED mappers are far worse than SIFT. ALIKED keeps about 450 keypoints per TUM frame against SIFT's 1,800-2,800, and LightGlue on CPU makes ALIKED runs 2-4 times slower. SIFT with the incremental mapper is the safe default; the ALIKED-incremental desk gain (2.5 mm) is within what a different seed might give and was not repeated.
- **A size taken from Depth Anything inherits its bias.** On desk it gives 0.330-0.338 against a true 0.234-0.238, on xyz 0.062 against 0.048: Depth Anything reads 1.3-1.4 times too far on these frames, the bias Task54 measured (raw metres 34-45% off). The path then misses by 58 mm (xyz) and 357-361 mm (desk) because of size alone. A metric size needs another source, such as ARCore on the phone.
- **Depth Anything's per-frame size against the SfM points spreads ±22% on desk** (10th-90th percentile 0.28-0.44 against a median 0.33), the frame-to-frame size change Task65 diagnosed. Task72 sizes each frame to the SfM points to remove it.

**The published fr1 distortion set failed.** With FULL_OPENCV (k1 0.2624, k2 -0.9531, p1 -0.0054, p2 0.0026, k3 1.1633), matching on desk still found 2,171 verified pairs with 490,031 inlier matches, but the incremental mapper found no initial image pair and the global mapper triangulated no points. The cause is not established; the large sixth-order term may distort the undistorted bearings near the image edges. Every other TUM run uses the default set.

**Edge view.** These runs are offline over whole clips: 1.2-7.1 frames per second end to end on a 32-thread desktop CPU, with matching and the incremental mapper the costly steps. A phone would not run this; ARCore tracks the camera live from the same kind of features plus the motion sensors. What carries over is the evidence that an image-feature path with joint refinement beats frame-to-frame depth alignment, and the saved sparse points per frame, which are what Task72 uses to size learned depth (ARCore exposes the same kind of points).

## Surfaces from the true camera poses (Task71)

Each recording's frames are fused along its true camera path (Open3D TSDF, 1 cm voxels on ICL, 2 cm on TUM, depth 0.1-4 m) and scored against a reference with experiment 04's scorer at 5 cm. ICL's reference is the publisher's surface model; TUM's is Kinect depth fused along the motion-capture path with the same settings, so it carries the Kinect's own error and the motion-capture timing error (about 30 mm on the 30-frame clip), and TUM has no separate sensor row. Run with `python -m experiments.sfm.run_dense`; table from `python -m experiments.sfm.report --dense`.

| Recording | Depth | Poses | Mean distance to reference | RMSE | Points within 5 cm | Reference covered within 5 cm | Points |
|---|---|---|---:|---:|---:|---:|---:|
| trajectory2 | sensor | true | 11.1 mm | 13.0 mm | 100.0% | 25.0% | 972042 |
| trajectory2 | model | true | 167.4 mm | 226.4 mm | 26.9% | 16.2% | 4228416 |
| trajectory2 | model-frame-reference | true | 81.7 mm | 143.9 mm | 52.8% | 21.6% | 2563520 |
| trajectory2 | model-run-reference | true | 87.6 mm | 144.2 mm | 47.9% | 20.7% | 3183753 |
| rgbd_dataset_freiburg1_desk_every2 | model | true | 398.7 mm | 509.5 mm | 4.7% | 13.7% | 438645 |
| rgbd_dataset_freiburg1_desk_every2 | model-frame-reference | true | 129.3 mm | 190.2 mm | 30.3% | 47.5% | 259650 |
| rgbd_dataset_freiburg1_desk_every2 | model-run-reference | true | 200.7 mm | 276.6 mm | 22.4% | 30.6% | 225798 |
| rgbd_dataset_freiburg1_xyz_every2 | model | true | 467.3 mm | 532.9 mm | 1.4% | 5.6% | 316830 |
| rgbd_dataset_freiburg1_xyz_every2 | model-frame-reference | true | 158.2 mm | 210.1 mm | 23.4% | 49.2% | 182685 |
| rgbd_dataset_freiburg1_xyz_every2 | model-run-reference | true | 151.5 mm | 193.6 mm | 20.7% | 45.7% | 189386 |


`model` is raw Depth Anything V2 Metric Small; `model-frame-reference` resizes each frame to the sensor depth (least squares through zero, a reference control and the best any per-frame size correction can do); `model-run-reference` applies one size for the whole run (reference control).

What this shows:

- **The coordinate handling is right.** ICL's rendered depth lands 11.1 mm from the publisher's model on average, every point within 5 cm, covering the 25% of the room the camera saw.
- **Correcting size cuts the surface error by 2-3 times, but Depth Anything's shape error remains.** Even with exact poses and an exact size for every frame, its surface is 82 mm (ICL), 129 mm (desk) and 158 mm (xyz) from the reference on average, and only 23-53% of its points are within 5 cm. Raw it is 167, 399 and 467 mm.
- **One size for the whole run is nearly as good as a size per frame on xyz and ICL, but not on desk** (201 against 129 mm), where Depth Anything's size changes most between frames.
- So the best possible result for Task72 (Depth Anything resized to SfM points along the SfM path) is about these per-frame-reference rows. Getting closer to the sensor needs better depth shape, which points to multi-view stereo along the SfM path or a stronger depth model, not more size correction.

ICL scoring is slow (8-17 minutes per run) because its reference model has millions of points; TUM runs take about 10 seconds.

## Dense structure from the SfM path (Task72)

Depth Anything is resized frame by frame to the SfM points each frame observed (points with track length ≥ 3 and reprojection error ≤ 2 px; median ratio, or size and shift), then fused along the SfM camera path with Task71's settings. The SfM path is the best Task67 setting per recording by camera score: desk ALIKED incremental, xyz and ICL SIFT incremental. "Best-fit size" sets the SfM world's metric size from the true path (upper bound; the phone would use ARCore); "depth-model size" sets it from Depth Anything (deployable without other sensors). The surface is placed in the reference world by the rotation and shift fitted to the true camera centres, for scoring only.

| Recording | Depth | Poses | Mean distance to reference | RMSE | Points within 5 cm | Reference covered within 5 cm | Points |
|---|---|---|---:|---:|---:|---:|---:|
| trajectory2 | model-sfm-size | SfM (best-fit size) | 92.4 mm | 150.8 mm | 47.0% | 22.8% | 3640285 |
| trajectory2 | model-sfm-size-shift | SfM (best-fit size) | 83.5 mm | 134.1 mm | 49.2% | 22.8% | 3453246 |
| trajectory2 | model | SfM (best-fit size) | 168.7 mm | 228.1 mm | 25.5% | 15.7% | 4240977 |
| trajectory2 | sparse | SfM (best-fit size) | 77.1 mm | 395.1 mm | 82.9% | 4.2% | 9146 |
| trajectory2 | model-sfm-size | SfM (depth-model size) | 173.8 mm | 263.1 mm | 32.6% | 18.1% | 4261491 |
| rgbd_dataset_freiburg1_desk_every2 | model-sfm-size | SfM (best-fit size) | 150.6 mm | 208.5 mm | 26.7% | 40.7% | 229355 |
| rgbd_dataset_freiburg1_desk_every2 | model-sfm-size-shift | SfM (best-fit size) | 178.0 mm | 260.9 mm | 24.7% | 50.7% | 332351 |
| rgbd_dataset_freiburg1_desk_every2 | model | SfM (best-fit size) | 394.1 mm | 504.0 mm | 5.4% | 16.0% | 443153 |
| rgbd_dataset_freiburg1_desk_every2 | sparse | SfM (best-fit size) | 47.5 mm | 89.3 mm | 74.2% | 19.8% | 9039 |
| rgbd_dataset_freiburg1_desk_every2 | model-sfm-size | SfM (depth-model size) | 391.1 mm | 485.7 mm | 5.1% | 16.6% | 459033 |
| rgbd_dataset_freiburg1_xyz_every2 | model-sfm-size | SfM (best-fit size) | 198.6 mm | 263.5 mm | 17.9% | 42.3% | 216047 |
| rgbd_dataset_freiburg1_xyz_every2 | model-sfm-size-shift | SfM (best-fit size) | 146.5 mm | 196.5 mm | 24.5% | 50.8% | 187690 |
| rgbd_dataset_freiburg1_xyz_every2 | model | SfM (best-fit size) | 465.3 mm | 528.0 mm | 1.5% | 5.8% | 325472 |
| rgbd_dataset_freiburg1_xyz_every2 | sparse | SfM (best-fit size) | 57.3 mm | 102.1 mm | 64.0% | 20.5% | 25097 |
| rgbd_dataset_freiburg1_xyz_every2 | model-sfm-size | SfM (depth-model size) | 483.3 mm | 549.6 mm | 1.4% | 7.6% | 306358 |

What this shows:

- **Depth Anything resized to the SfM points reaches about the Task71 limit.** Mean distance 92 mm (ICL), 151 mm (desk) and 147-199 mm (xyz), against 82, 129 and 158 mm with true poses and an exact per-frame size. Raw Depth Anything along the same path is 169, 394 and 465 mm.
- **A metric size from Depth Anything is not usable**: its overall bias carries straight into the surface.
- **The sparse SfM points are the most accurate geometry** (64-83% within 5 cm) but cover only 4-20% of the reference.
- **The remaining error is Depth Anything's shape.** Multi-view stereo along the SfM path is the next comparison; COLMAP's PatchMatch stereo needs CUDA and the owner's GPU permission.

## Real-world size from a few metric readings (Task78)

The SfM world has no real-world size. A phone can supply some from ARCore depth readings at tracked points. Here the depth camera stands in: a reading is its depth at the pixel where an SfM point was seen, divided by that point's depth in the SfM world (metres per SfM unit). The size is the median of N readings. Readings come from points with track length ≥ 3 and reprojection error ≤ 2 px, and depth camera depth of 0.1-4 m. Two rules:

- **Per run**: N readings drawn from the whole run. N is the total the phone must take.
- **Per frame**: N readings drawn in every frame; each frame gets a median and the run size is the median over frames. The total is about N times the frame count.

100 random draws per setting (one for "all"). The SfM runs are Task72's. Run with `python -m experiments.sfm.run_metric_points`. No noise is added to the depth camera readings, so ARCore's own error is not simulated.

Camera path after sizing (best-fit rigid error, median over draws, 10th-90th percentile in brackets) and size error against the best-fit size:

| Recording | Best fit with size | Per run, 5 | Per run, 20 | Per run, 100 | All readings | Per frame, 5 (about 1,500-2,200 readings) |
|---|---:|---|---|---|---|---|
| TUM xyz | 11.9 mm | 13.9 mm (13.1-15.3), size -3.9% | 13.7 mm (13.3-14.2), -3.7% | 13.8 mm (13.6-14.0), -3.7% | 13.8 mm, -3.7% | 13.7 mm, -3.7% |
| TUM desk | 21.5 mm | 24.4 mm (21.6-34.3), -1.1% | 24.2 mm (22.0-28.4), -1.3% | 23.7 mm (22.5-25.2), -1.2% | 23.9 mm, -1.2% | 24.2 mm, -1.3% |
| ICL | 34.1 mm | 34.1 mm (34.1-36.5), 0.0% | 34.1 mm (34.1-34.5), +0.1% | 34.1 mm, +0.1% | 34.1 mm, +0.1% | 34.1 mm, +0.1% |

Surface from Task72's row (Depth Anything resized per frame to the SfM points, fused along the SfM path), with the draw whose size error is the median over the 100 per-run draws. Mean distance to the reference:

| Recording | Best-fit size (Task72) | 5 readings | 20 readings | 100 readings | All readings |
|---|---:|---:|---:|---:|---:|
| TUM xyz | 198.6 mm | 165.3 mm | 166.2 mm | 165.8 mm | 165.8 mm |
| TUM desk | 150.6 mm | 146.5 mm | 155.8 mm | 155.1 mm | 155.2 mm |
| ICL | 92.4 mm | 93.5 mm | 93.0 mm | 92.9 mm | 92.7 mm |

What this shows:

- **20 metric readings in the whole run are enough.** The path error is 1.15 times (xyz), 1.13 times (desk) and 1.0 times (ICL) the best-fit error, and the surface is within 1.03 times of the best-fit row or better. The target (within 1.2 times) is met on all three recordings.
- **More readings do not help past 20.** With every reading (110,000-440,000) the path is no better. What remains is the depth camera's own bias: its readings give a size 3.7% small on xyz and 1.2% small on desk against the motion-capture path. Five readings are enough on the median draw but the spread is wider (desk 10th-90th percentile path error 21.6-34.3 mm against 22.0-28.4 mm for 20).
- **Readings in every frame add nothing.** Per frame gives the same size as per run with 100 to 400 times more readings. One short burst of readings is enough; it need not repeat.
- **The sensor-based size gives a better xyz surface than the path-fitted size** (166 against 199 mm), because the surface is scored against the same depth camera. This is not a gain in accuracy of the SfM path.
- **For the phone:** a one-off set of about 20 depth readings at tracked points, spread over the walk, fixes the size to within a few percent when the readings are as accurate as a Kinect. ARCore's depth accuracy at those points is not tested here (Task75 and Task52 own that).

## Prompt Depth Anything fed with SfM points (Task79)

Prompt Depth Anything (Small, 25.1M parameters, Apache-2.0 code and checkpoint) takes a low-resolution depth map as a second input and returns full-resolution depth in metres. It was trained on iPhone lidar. Here the map is built per frame from that frame's SfM points (track length ≥ 3, reprojection error ≤ 2 px, at least 20 points), multiplied by the 20-reading size from Task78, on a 192 × 256 grid for the 480 × 640 image. Two fills between points: *linear* (triangulated interpolation) and *nearest* point. The model's depth is fused along the SfM path with the same size, scoring and reference as the rows above. Run with `dump_prompt_depth.py` (`.venv-yolo`) and `run_dense --depth model`. Mean distance to the reference:

| Recording | Depth Anything resized to the SfM points (Task78, 20 readings) | Prompt DA, linear fill | Prompt DA, nearest fill | Task71 ceiling (true poses, exact size per frame) |
|---|---:|---:|---:|---:|
| TUM xyz | 166.2 mm | 167.9 mm | 176.5 mm | 158 mm |
| TUM desk | 155.8 mm | 216.7 mm | 212.8 mm | 129 mm |
| ICL | 93.0 mm | 146.5 mm | 146.4 mm | 82 mm |

Points within 5 cm: xyz 23.0% (linear) against 21.1%; desk 23.6% against 26.8%; ICL 34.4% against 46.6%.

Speed on 16 CPU threads: model alone 2.6-2.8 frames per second; with the prompt build 2.2-2.6 frames per second end to end (linear fill costs 0.04-0.07 s per frame, nearest 0.02-0.03 s). Above the owner's 1 fps floor on a desktop CPU; phone speed is not measured.

What this shows:

- **Prompt Depth Anything does not beat Depth Anything resized to the same points.** It ties on xyz and is 39% worse on desk and 58% worse on ICL. The target (20% better on two of three recordings) is not met.
- **The prompt is too sparse and too noisy for this model.** It was trained on dense lidar maps. A few hundred SfM points per frame leave most of the grid filled by interpolation, and the model also rescales its output to the prompt's smallest and largest depth, so any point outside the interpolated range is clipped.
- **Linear against nearest fill makes little difference** (xyz 168 against 177 mm, desk 217 against 213 mm, ICL 146.5 against 146.4 mm).
- **Depth Anything resized per frame to the points stays the best learned-depth result here.** The remaining gap to the Task71 ceiling (xyz 8 mm, desk 27 mm, ICL 11 mm) is small compared with the gap to the sensor.
- Not tried: a denser prompt (for example SfM points plus the sparse points of neighbouring frames reprojected into this frame), fine-tuning the model on sparse prompts, or the Large model (340M parameters, too slow for the floor on a phone).

## Status and handover, 13 October 2026 (overnight)

- Done (Task67): this folder's code, 11 tests, and SIFT runs on TUM xyz, TUM desk (both calibrations) and ICL living room 2; results above.
- Done: ALIKED + LightGlue runs on desk, xyz and ICL (5.7, 9.5 and 4.9 minutes).
- Done (Task71): fusion, references and surface scoring; true-pose rows above.
- Done (Task72, 14 October): all 15 dense-structure runs; table above.

## Status and handover, 14 October 2026

- Done (Task78): size from N metric readings; 20 readings are enough.
- Done (Task79): Prompt Depth Anything fed with SfM points; no gain over Depth Anything resized to the points.
- Not run: multi-view stereo along the SfM path (COLMAP patch_match_stereo, needs CUDA). The owner's GPU permission line was left blank, so it stays unrun. It is now the main untried route to a better dense surface.
- Task80 (Depth Anything 3 Small, single and posed modes) is running: `%TEMP%/da3_80_queue.sh`, log `%TEMP%/da3_80_queue.log`. Setup: `git clone https://github.com/ByteDance-Seed/Depth-Anything-3 third_party/depth-anything-3` at commit 3d835ec1a5802d64a8b8b15f817a1ab54809bfe4, and `.venv-yolo/Scripts/python.exe -m pip install --no-deps --target third_party/da3-deps moviepy==1.0.3 trimesh plyfile pillow_heif decorator proglog imageio_ffmpeg pycolmap==4.2.1 evo natsort argcomplete`; run with `PYTHONPATH=<repo>/third_party/depth-anything-3/src;<repo>/third_party/da3-deps`. When it says `QUEUE DONE`: `report.py --dense` over the dense_* folders (rows labelled `DA3 Small <mode>, 20 readings`), add a table here, read each dump's `index.json` for fps, add a research row, `task.js finish 80`. Follow-up queue `%TEMP%/da3_80b_queue.sh` (log `%TEMP%/da3_80b_queue.log`, starts when the first queue ends): posed mode with 5 consecutive frames gave 546-814 mm on TUM because Depth Anything 3 sets its depth size from a pose fit (`api.py` `_align_to_input_extrinsics_intrinsics`), which a window spanning about 0.3 s of motion cannot constrain. The follow-up scores the posed dumps sized to SfM points, and a `--stride 10` variant (window members 10 frames apart) both raw and sized. Then Task76 (walkthrough readers).
