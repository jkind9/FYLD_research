# sitescan

Shared processing stages for room reconstruction from a phone recording.
Install the locked environment from the repository root. It builds `.venv`, with CPU-only PyTorch:

```powershell
uv sync --all-extras
```

| Stage | Headline function | Takes | Gives |
|---|---|---|---|
| [Session](session/README.md) | `session.frames(folder)` | A recording folder | RGB frames, depth, tracked points and matrix poses |
| [Depth](depth/README.md) | `depth.load_model(path)`, `depth.predict(model, image, pose)` | Local weights, RGB and optional pose | Depth and validity on the recorded grid |
| [Scale](scale/README.md) | `scale.fit_one(...)`, `scale.fit_grid(...)` | Learned depth, validity and metric targets | One factor or a per-pixel scale field |
| [Fusion](fusion/README.md) | `Fragments.integrate(...)` | Scaled depth, RGB and corrected anchors | World surface points and aligned colours |
| [Cleanup](cleanup/README.md) | `cleanup.clean_room(points, views)` | Surface and depth evidence | Mask retaining supported large pieces |
| [Mapping](mapping/README.md) | `mapping.measure_site(surface, cameras)` | Surface points and camera positions | Areas, dimensions, height and plane normal |

Objects move next, followed by the
two pipelines. Until they move, run the existing entry points:

```text
python -B -m src.live.room_build --session <recording> --out <new folder>
python -B -m src.live.run --replay <recording> --out <new folder>
```

Run these commands with `.venv/Scripts/python.exe`. Object counting remains experimental. The package stages
import no experiment or interface code. See [DESIGN.md](../DESIGN.md) for the move order.
