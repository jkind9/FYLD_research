# Structure-from-motion library code

This folder holds the reusable parts of the structure-from-motion (SfM) experiment: reading recordings, running COLMAP, saving its results, scoring camera paths, and giving an image-only 3D world a real-world size. It belongs to the [standalone SfM experiment](../README.md).

SfM recovers camera positions and 3D points from images alone, so its result has no real-world size until one comes from elsewhere. Several files here supply that size from depth readings.

| File | What it does |
|---|---|
| `sequences.py` | `load("tum:<folder>" or "icl:<folder>", every=N)` returns a `Sequence`: image names, timestamps, camera model, ground-truth path and depth file names for a TUM RGB-D or ICL-NUIM recording. |
| `reconstruct.py` | Runs COLMAP through its command-line build with per-stage timing. `Settings` picks `sift` or `aliked` features. `features_and_matches` and `map_models` run the stages, using the incremental or global mapper. `read_models` loads the results. |
| `export.py` | `write(sequence, models, output)` saves the camera path, sparse points and which pixel in which frame saw each point. `largest_model` picks the biggest reconstructed model. |
| `scoring.py` | `score(sequence, rows)` scores a saved camera path against the true path with experiment 03's evaluation. `depth_model_size` and `sized_score` fit a run-wide size from a depth model's readings and score the sized path. |
| `metric_points.py` | `readings(...)` computes metres per SfM unit at the points where a depth camera also measured depth. `run_size` and `frame_size` draw `n` such readings at random and return the resulting size. |
| `dense.py` | `fuse_tsdf` fuses depth images and camera poses into one surface (Open3D TSDF, a voxel grid that averages measured surfaces). `accumulate` keeps the raw points. `fit_size` and `frame_sizes` fit a size per frame from SfM points. `DepthFrame` and `Pinhole` are the inputs. |
| `posed.py` | `windows(count, size, stride)` splits a sequence into overlapping frame windows. `sized_extrinsics` applies a size to world-to-camera poses, for depth models that take camera poses. |
| `prompt.py` | `prompt_map(...)` turns a frame's SfM points into a low-resolution depth prompt for Prompt Depth Anything. |
| `references.py` | `icl_reference(icl_root)` loads the ICL-NUIM reference surface in the same right-handed world as the true poses. |

The scripts that use these modules are one level up: `run_sfm.py`, `run_dense.py`, `run_metric_points.py`, `dump_depth.py`, `dump_da3_depth.py`, `dump_prompt_depth.py` and `report.py`. `research/experiments/live_slam/run_live.py` also imports `scoring` and `sequences`.

## How to run it

Nothing here is a script. Run the entry points from the repository root:

```text
.venv/Scripts/python.exe -m research.experiments.sfm.run_sfm --recording tum:<recording folder> --features sift --run-root <run folder> [--depth-run <finished walkthrough run>]
```

`reconstruct.py` needs the COLMAP 4.2.1 Windows build (no CUDA) unpacked to `third_party/colmap-4.2.1-windows-nocuda/`, which Git ignores. COLMAP and the learned features run on the CPU. Tests:

```text
.venv/Scripts/python.exe -m pytest research/experiments/sfm/tests -p no:cacheprovider --import-mode=importlib
```

## Where results are recorded

Camera-path errors, surface scores and sizing results are in the [SfM README](../README.md). Run folders are in [`../runs/`](../runs).
