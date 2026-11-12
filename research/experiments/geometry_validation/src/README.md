# Geometry control code

This folder turns a dataset's supplied depth images and supplied camera poses into 3D points, one frame at a time, and exports every step so the coordinate handling can be inspected. It belongs to [geometry validation](../README.md), which checks conventions for both camera tracking and surface reconstruction.

Nothing here predicts depth or estimates camera motion. Per-frame points stay separate; fusing them is experiment 04's job.

| File | What it does |
|---|---|
| `run.py` | Entry point. `execute(...)` exports each stage for the chosen ICL-NUIM frames into a published run folder. CPU only. |
| `control.py` | `compute(frame)` returns `Stages`: depth, validity mask, pixel positions, camera-frame points, world points, model-frame points and the projection error. `GeometryBackend` is the interface a future backend must follow. |
| `icl.py` | `load_frame(root, frame_id)` reads one ICL-NUIM frame by its exact image ID. `read_poses` loads the pose table. `select_ids` checks the requested IDs. A pose is never taken by position in the file. |
| `scene.py` | `export_scene` draws the supplied camera poses and each frame's points. |
| `review.py` | `build_review` writes the HTML page that explains each stage and separates file and coordinate checks from accuracy. |

[`04_surface_reconstruction/src/`](../../04_surface_reconstruction/src/README.md) imports `compute`, `Stages` and `Frame` from here.

## How to run it

Run from the repository root, CPU only:

```text
.venv/Scripts/python.exe -B -m research.experiments.geometry_validation.src.run --dataset data/icl_nuim --frame-ids <explicit IDs>
```

`--frame-ids` is required. Tests:

```text
.venv/Scripts/python.exe -B tools/check.py -q research/experiments/geometry_validation/tests
```

## Where results are recorded

What the control shows and its saved runs are in the [geometry validation README](../README.md). Run folders are in [`../runs/`](../runs).
