# sitescan

The product package: room surfaces, site measurements and object counts from a phone
recording. Each stage is a folder of plain functions on arrays; the two orchestrators in
`pipelines/` decide which stage runs on which frame. Only `session/` reads recordings and
only `io.py` writes results.

Install the locked environment from the repository root. It builds `.venv`, with CPU-only PyTorch:

```powershell
uv sync --all-extras
```

## Stages

| Stage | Headline function | Takes | Gives |
|---|---|---|---|
| [Session](session/README.md) | `session.frames(folder, trajectory, calibration)`, `session.read_tum(path, source=...)` | A recording folder; optionally a tracker trajectory and phone calibration | Frames with RGB, ARCore depth, tracked points, poses (ARCore's or the tracker's) and anchor events |
| [Depth](depth/README.md) | `depth.load_model(path)`, `depth.predict(model, image, pose)` | Local weights, RGB and optional pose | Depth and validity on the recorded grid, right shape and wrong scale |
| [Triangulate](triangulate/README.md) | `Triangulator().sparse(grey, camera, pose)`, `.dense(...)` | Grey images with known poses | Metric depth at matched features with its error; a plane-sweep depth map with confidence |
| [Scale](scale/README.md) | `scale.fit_one(...)`, `scale.fit_grid(...)`, `scale.fit_power(...)` | Learned depth, validity, metric targets and optional weights | One factor, a per-pixel scale field, or one that changes with distance |
| [Fusion](fusion/README.md) | `Fragments.integrate(...)`, `Fragments.surface()` | Scaled depth, RGB, pose and keyframe | World surface points that follow ARCore's anchor corrections |
| [Cleanup](cleanup/README.md) | `cleanup.clean_room(points, views)` | Surface points and the views that made them | Masks after the visibility vote and after keeping the largest pieces |
| [Mapping](mapping/README.md) | `mapping.measure_site(surface, cameras)` | Surface points and camera positions | Area, length, width, height and floor plane |
| [Objects](objects/README.md) (experimental) | `objects.load_detector(path)`, `Objects.update(...)` | RGB, scaled depth, pose and anchors | Detections placed in 3D and counted |

Shared records (`Camera`, `Frame`, `MeasuredDepth`, `Trajectory`, `Calibration`) are in [types.py](types.py). Every public
function, with its arguments and a link to its code, is in the
[function index](../README.md#function-index) in the root README.

## Without ARCore

Both pipelines can run without ARCore's poses or depth. The session reader takes an open
tracker's trajectory (TUM format) and the phone's calibration, turns the tracker's world so
+y is up, and starts an anchor once a second. The pipelines then size learned depth by depth
triangulated along that path, chosen by name: `scale_sources=("sparse",)` for triangulated
features, or `("dense", "sparse")` for plane-sweep depth first. ARCore stays the default, and
its outputs are unchanged. The design is in
[DESIGN section 7.15](../DESIGN.md#715-removing-arcore-five-changes). The tracker itself runs
outside the package, and no phone recording has yet been run this way.

## Orchestrators

| Orchestrator | Headline call | What it does |
|---|---|---|
| [Room](pipelines/README.md) | `pipelines.build_room(folder, model, settings, trajectory, calibration)` | Every frame with a scale source (by default fresh ARCore depth), fused, then cleaned and measured once |
| [Live](pipelines/README.md) | `pipelines.LiveProcessor(model, detector, settings)`, `run_live(...)` | The newest frame once per update, under a second each |

Run either from the command line (see [apps/README.md](../apps/README.md)):

```text
.venv/Scripts/python.exe -B -m apps.cli room   --session <recording> --out <new folder>
.venv/Scripts/python.exe -B -m apps.cli replay --session <recording> --out <new folder>
```

The [walkthrough notebook](../notebooks/00_sitescan_walkthrough.ipynb) runs both, then repeats
their steps one stage call at a time on the committed test recording.

## Rules

Imports point down: `apps` imports `pipelines`, `pipelines` import stages and `io`, stages
import other stages and `types`. No stage imports an experiment, reads a file other than
model weights, or parses arguments. Inputs are checked where they enter (the session reader,
the receiver, the command line, model files); inside, functions trust their types.
