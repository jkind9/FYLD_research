# Shared experiment infrastructure

| File | Responsibility |
|---|---|
| `contracts.py` | Frozen observation/calibration/pose records, metre units and origin identity |
| `phone_session.py` | Verified Camera2 images with original sensor-grid calibration and explicit missing streams |
| `geometry.py` | Axial depth, calibrated depth/mask checks, projection, proper poses, reference basis conversion and time association |
| `runs.py` | Unique run lifecycle, source/environment/configuration snapshot and artifact validation |
| `timing.py` | Monotonic stage timing, explicit frame counts and weighted throughput |
| `exporting.py` | Lossless stage arrays, coloured point clouds, visual rasters and 3D previews |
| `requirements.txt` | Direct dependency versions used for CPU validation |

OpenCV is a shared CPU dependency because the walkthrough imports segmentation and classical appearance modules at startup. Models still load only when selected.

Install with `python -m pip install -r experiments/shared/requirements.txt` from the repository root. Run `python -B tools/check.py -q` for CPU tests with caches outside the repository. The working environment is Python 3.12.10; dependency versions reflect that environment. A clean isolated installation and edge-device packaging remain separate checks.

`read_phone_session` takes a Camera2 report, the exported bundle folder and the
phone-session export validator. It rechecks image hashes, decodes every JPEG,
and checks decoded dimensions against the report. It keeps camera intrinsics in
their named sensor grid, with the active-array rectangles, crop and rotation.
It marks the calibration grid ready for metric work only when the recorded
distortion-correction mode is OFF. Corrected or unreported modes keep their raw
metadata and a reason that geometry is not ready. Missing depth, pose and world
identifiers remain missing with an explanation. Fixture tests do not prove that
a physical phone produces matching records.

`Run(root, repo, configuration)` creates a unique run containing `input/`,
`output/`, `debug/` and `metadata/`. Use it as a context manager. Put every selected
input and its matching stage artifacts inside that directory before leaving the
context. Successful exit creates a hash inventory, validates it and writes the
completion receipt last. `stop_incomplete(reason)` retains partial outputs and timing, records failed status with `IncompleteRun`, and writes no completion manifest. An exception marks the run failed. A killed process
leaves the run marked running. `verify_run(path)` rejects incomplete runs and
changed, missing or extra artifacts.

Metadata records the commit, tracked working and staged differences, untracked
file names, configuration, installed package versions, Python, operating system,
CPU information, invocation and UTC runtime. It snapshots experiment Python and
requirement files, including the dataset acquisition module and dirty code. The
snapshot excludes run directories and caches. Input data and external model
weights must be copied or recorded with content hashes by the experiment caller.
Hashes detect accidental changes; they do not authenticate an external publisher.

Run metadata includes `metadata/timing.json`. Wrap operations with
`with run.measure("odometry_pairs", frames=1):` and set the number of unique
processed images with `run.set_processed_frames(count)`. Each sample records
seconds, count, completion status and frames per second (FPS). A stage's FPS is
its total successful sample count divided by its total successful sample time.
An odometry sample counts an image pair; use a stage name that makes the unit
clear. A backend returning tracking failure still completed a computation, so
record tracking success separately from timing. A raised exception records a
failed timing sample, excluded from successful stage throughput.

Whole-run FPS uses the unique image count and elapsed time from Run construction
through timing publication. It includes snapshots, loading, computation,
evaluation and reporting. Final manifest hashing and completion publication
happen afterward and are excluded. Stages can overlap when nested, so their
times must not be added to infer whole-run time. Unknown counts, zero elapsed
time and failed whole runs have unavailable FPS (`null`). Failed runs retain
available timing metadata. Failed status is recorded even if timing metadata
cannot be written. Existing callers keep their elapsed/start/end fields; callers
without the wrapper have no invented frame count. Existing completed runs remain
unchanged and readable with their original timing schema.

`export_frame` saves depth, mask, valid pixel positions, camera/world/model point
arrays and projection errors without reducing their precision. It exports each
cloud as an ASCII PLY file with matching RGB values. Pixel positions use row,
column order `(v, u)`. Projection error arrays preserve both pixel deltas when
provided; the image shows their length. Full-resolution debug images
show depth, mask, coordinate channels and projection errors. `legends.json`
records each image's value range and units. Invalid pixels are black.
Each cloud also has a 3D preview with metre axes and equal scale. The previews
include every point. Raw arrays and PLY files retain the exact numeric values.

These helpers use CPU operations only. Every GPU run requires user approval
before execution. The helpers do not probe or import a GPU backend.

## Experiment owners

[Geometry validation](../geometry_validation/README.md) owns the supplied-depth/supplied-pose control. [Camera pose estimation](../03_camera_pose_estimation/README.md) now produces estimated poses through a CPU backend; [surface reconstruction](../04_surface_reconstruction/README.md) has a measured supplied-input baseline. Shared records do not depend on the estimator package, device placement or a transport service. Pose revisions and tracking resets must remain explicit when these stages are connected.


## Labelled offline inspection

The shared inspection adapter exports an offline three-dimensional viewer using processor-based Canvas2D projection. It shows camera orientation, frame order, source images and available reference geometry. Source measurements, independent reference answers, estimates and computed comparisons carry observed input, ground truth, predicted output and evaluated output labels in both captions and artifact metadata.

`visualization.py` owns finite drawing geometry, paired display sampling and colour depth previews. `inspection.py` adapts saved camera and surface outputs. `publication.py` creates a new verified run from a complete source. All copied numerical files retain their original bytes. Original computation configuration and timings are archived beneath `metadata/computation/`; nested inspection copies resolve the original computation recursively. `metadata/publication.json` links the numerical timing record. New publication timing reports no processing FPS.

Run `python -B -m experiments.shared.publication --source <complete-run> --stage 03 --runs <stage-runs>` or use stage `04`. Open the returned `viewer.html` directly in a browser. It needs no server or network packages. Drag to orbit, scroll to zoom and step observations with the controls. Display sampling is deterministic and recorded alongside full counts. It changes no scores or stored point arrays. GPU use is not required. Optional browser tests use Playwright and Edge with GPU and WebGL disabled; unavailable browser dependencies produce explicit skips.

## Share a viewer as one file

Export a completed inspection with:

```powershell
python -B -m experiments.shared.share --source <complete-inspection-run> --output <destination-outside-source>/viewer.html
```

Send the resulting HTML file. Recipients save it and open it in a JavaScript-enabled browser. All scene geometry, drawing code and preview images are embedded; no server, internet connection or neighbouring files are needed. Frame stepping, orbit, zoom and the reference overlay work as in the original viewer. This export uses the existing display samples and performs no inference or scoring.

Images are RGB PNG previews with a maximum edge of 320 pixels and no upscaling. Nearest-neighbour resizing preserves missing-depth colours. Use `--max-edge <pixels>` to change display resolution. Captions preserve input/reference/result labels and include per-frame distance bounds and colour encoding. Preview links open the reduced picture; original depth, arrays, source code and workstation metadata are omitted. The source run identifier and manifest hash remain for traceability. This file is for inspection, not numerical measurement.

The exporter verifies the source inventory before and after conversion. It rejects incomplete or changed sources, non-contained images and output paths inside the source. Publication replaces the destination atomically after validation. Existing completed runs remain unchanged. Generated share files are local artifacts under ignored `runs/shareable/` folders; a fresh clone needs a complete inspection run before it can regenerate them.

## Root runner provenance

The six-step runner reuses `Run`, `verify_run`, the timing ledger, shared calibration/pose records and geometry primitives. `artifact_inventory(path)` exposes the existing publication hash/link checks. Source snapshots now also include dirty and untracked Python sources under `src/walkthrough` when present, with the same exclusions for generated runs. Repositories without that folder retain their experiment inventory. Prediction hashes are recorded while the run is running, checked after scoring, then included in final publication. [Runner lifecycle](../../src/walkthrough/README.md).
