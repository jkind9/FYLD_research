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
.venv/Scripts/python.exe -B -m apps.cli room   --session <recording> --label <label>
.venv/Scripts/python.exe -B -m apps.cli replay --session <recording> --label <label> [--speed 1.0] [--no-objects]
.venv/Scripts/python.exe -B -m apps.cli live   --port 8766 --label <label> [--no-objects]
```

`--session` takes a recording's short name from [recordings.toml](../recordings.toml), or a folder. Each run
writes `outputs/<recording>/<verb>/<yyyymmdd-hhmm>_<label>/` with `run.json` (settings, typed options, git
commit, status and headline numbers); the live verb's recording name is `live`. A label is one to four lowercase
words joined by hyphens. See "Where outputs go" in the [root README](../README.md#where-outputs-go).

| Verb | What it runs | Writes |
|---|---|---|
| `room` | `build_room` on a saved recording | `surface.ply` (cleaned), `raw_surface.ply`, `voted_surface.ply` (after the vote, before the piece rule), `frames.npz` (per-frame cameras and sampled points), `summary.json` |
| `replay` | `LiveProcessor` fed a saved recording at its recorded speed (`--speed 0` as fast as possible) | `updates.jsonl` (one line per update), `surface.ply`, `summary.json` |
| `live` | The capture receiver plus `LiveProcessor`, until the app ends the session | The same, plus the recording under `<run>/sessions/` |

`room` takes `--far` (default 4.0 m), `--voxel` (0.02 m), `--piece-cell` (default: the voxel),
`--supported-only` (a trial: fuse only pixels whose grid cell has its own ARCore scale),
`--scale-sources` (default `arcore_depth`), `--scale-fit` (`grid` or `power`), `--max-scale-jump`
(a trial: skip a frame whose scale is more than this factor off the last 15 frames' median) and
`--threads` (16). `replay` and `live` take `--voxel`, `--threads`, `--no-objects`,
`--depth-model`, `--detector-model` and `--scale-sources` (default `arcore_depth tracked_points`).
A run never overwrites an existing folder.

`room` and `replay` can take poses from an open tracker instead of ARCore:
`--trajectory <file>` (TUM format), `--calibration <JSON>` (the phone's camera and
`imu_from_camera`), `--trajectory-of imu|camera` (default `imu`, Basalt's output, which needs
the calibration), `--trajectory-up X Y Z` (default `0 0 1`, Basalt's world) and `--tracker`
(the name recorded as the pose source). With `--scale-sources sparse` or `dense sparse`,
learned depth is sized by depth triangulated along the tracker's path. Scale source names are
listed in [sitescan/pipelines/README.md](../sitescan/pipelines/README.md).

Counting objects needs the `objects` extra and `models/yolo26x.pt`; add `--no-objects` without them.

## Limits

The receiver has no authentication or encryption: use it on a local network only. Allow the
port through the Windows firewall for private networks the first time.

## Tests

`tests/test_pipelines.py` checks the command's refusal to overwrite a run.
The receiver's tests are in [research/experiments/01_camera_capture_delivery/tests](../research/experiments/01_camera_capture_delivery/tests/),
with the fake phone that writes test recordings.
