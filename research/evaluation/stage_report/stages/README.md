# Stage scorers for the accuracy report

This folder holds one wrapper per pipeline stage. Each wrapper re-scores a finished run's saved outputs and returns one section of the per-stage report built by [`research/evaluation/stage_report`](../README.md).

A wrapper does three things. It checks that the run is complete and unchanged, and optionally that its manifest hash matches a pinned value. It re-scores the saved outputs with the owning experiment's own scorer. It refuses to return a section if the new score differs from the score the run stored. No model is run again.

| File | What it does |
|---|---|
| `common.py` | Shared steps. `verified_run(path, pinned_sha256)` verifies the run and its manifest hash. `owner(module)` imports an owner scorer by name, because folder names starting with a digit cannot be imported with `import`. `scope(items)` fingerprints which items were scored. `require_keys` and `require_same` refuse runs that did not store a score or whose score does not reproduce. |
| `camera.py` | `camera_section(run_path, dataset=...)` scores the camera path against motion-capture poses with [`03_camera_pose_estimation/src/evaluation.py`](../../../experiments/03_camera_pose_estimation/src/README.md). Reads `output/poses.json` and `input/evaluation/groundtruth.txt`. |
| `detection.py` | `detection_section(...)` re-scores every detection method at overlap thresholds 0.3, 0.5 and 0.7 with the one-to-one matcher in `06_object_recognition/experiments/01_detection/scoring.py`. Includes an empty-prediction control. |
| `surface.py` | `surface_section(...)` replays the point-surface distance totals from the run's saved per-frame distances with [`04_surface_reconstruction/src/evaluation.py`](../../../experiments/04_surface_reconstruction/src/README.md). |
| `identity.py` | `identity_section(...)` scores merges, splits and unresolved counts for every identity condition with the scorer in `06_object_recognition/experiments/04_geometry_identity/validation`. |

Every `*_section` function takes the run folder, a `dataset` name, an optional `pinned_sha256`, an `input_mode` (`isolated` or `chained`) and a `reference_kind`.

Segmentation, depth support, 3D position and count have no wrapper yet.

## How to run it

The wrappers are not run alone. [`../run.py`](../run.py) calls them with the pinned run folders:

```text
.venv/Scripts/python.exe -B -m research.evaluation.stage_report.run --runs-root <checkout holding the run folders>
```

Run folders are not in Git, so `--runs-root` names a checkout that has them. Tests:

```text
.venv/Scripts/python.exe -B -m pytest research/evaluation/stage_report/tests
```

## Where results are recorded

The report format, the comparison rules and the first report are in the [evaluation README](../README.md).
