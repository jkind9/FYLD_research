# Apps

Ways to start an orchestrator. Nothing here is a step of the method: each file parses
arguments or receives bytes, then calls `sitescan.pipelines`.

| Path | What it does |
|---|---|
| [`cli.py`](cli.py) | One command with three verbs: `room`, `replay` and `live` |
| [`receiver/`](receiver/README.md) | The TCP receiver the capture app sends recordings to |

## Run it

From the repository root, in the environment built by `uv sync --all-extras`:

```text
.venv/Scripts/python.exe -B -m apps.cli room   --session <recording> --out <new folder>
.venv/Scripts/python.exe -B -m apps.cli replay --session <recording> --out <new folder> [--speed 1.0] [--no-objects]
.venv/Scripts/python.exe -B -m apps.cli live   --port 8766 --out <new folder> [--no-objects]
```

| Verb | What it runs | Writes |
|---|---|---|
| `room` | `build_room` on a saved recording | `surface.ply` (cleaned), `raw_surface.ply`, `frames.npz` (per-frame cameras and sampled points), `summary.json` |
| `replay` | `LiveProcessor` fed a saved recording at its recorded speed (`--speed 0` as fast as possible) | `updates.jsonl` (one line per update), `surface.ply`, `summary.json` |
| `live` | The capture receiver plus `LiveProcessor`, until the app ends the session | The same, plus the recording under `<out>/sessions/` |

`room` takes `--far` (default 4.0 m), `--voxel` (0.02 m), `--piece-cell` (default: the voxel),
`--supported-only` (a trial: fuse only pixels whose grid cell has its own ARCore scale) and
`--threads` (16). `replay` and `live` take `--voxel`, `--threads`, `--no-objects`,
`--depth-model` and `--detector-model`. A run never overwrites an existing folder.

Counting objects needs the `objects` extra and `models/yolo26x.pt`; add `--no-objects` without them.

## Limits

The receiver has no authentication or encryption: use it on a local network only. Allow the
port through the Windows firewall for private networks the first time.

## Tests

`tests/test_pipelines.py` checks the command's refusal to overwrite a run.
The receiver's tests are in [experiments/01_camera_capture_delivery/tests](../experiments/01_camera_capture_delivery/tests/),
with the fake phone that writes test recordings.
