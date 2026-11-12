# Evaluation

Scoring outside the product: stand-in recordings made from public datasets, scores of the
pipelines' outputs against reference data, and the layer-by-layer runner. `sitescan/` never
imports anything here. Measured results of the pipelines are in [results.md](results.md).

| Path | What it does | Run it |
|---|---|---|
| [`stand_in.py`](stand_in.py) | Writes a TUM or ICL clip as a phone recording, with the clip's true path and depth sensor standing in for ARCore. Its `session.json` says `control: reference` | `python -B -m research.evaluation.stand_in --recording tum:data/tum/rgbd_dataset_freiburg1_xyz --out <folder>` |
| [`score.py`](score.py) | Scores a live run's surface against the ICL living-room reference model | `python -B -m research.evaluation.score --run <live run> --icl data/icl_nuim` |
| [`count_report.py`](count_report.py) | Splits a live run's new object identities by distance to the nearest same-class object, confidence and sightings | `python -B -m research.evaluation.count_report <live run>/updates.jsonl` |
| [`depth_check.py`](depth_check.py) | Fused learned depth against ARCore's tracked points, by distance and by whether the grid cell had its own ARCore depth | `python -B -m research.evaluation.depth_check --session <recording> --out <check.json>` |
| [`orientation_control.py`](orientation_control.py) | Learned depth from the image as recorded against the image turned upright, both scored on ARCore depth | `python -B -m research.evaluation.orientation_control --session <recording> --out <folder>` |
| [`landmark_probe.py`](landmark_probe.py) | Where each frame puts one red object, from ARCore depth and from learned depth; finds doubled surfaces | `python -B -m research.evaluation.landmark_probe --session <recording> --first 660 --last 730 --out <probe.json>` |
| [`layers/`](layers/README.md) | The layer-by-layer runner: each layer fed known-correct inputs, so its error is its own | `python -B -m research.evaluation.layers.cli --help` |
| [`stage_report/`](stage_report/README.md) | One accuracy report per run, stage by stage, and a comparison of two reports | `python -B -m research.evaluation.stage_report.run --help` |
| [`tests/`](tests/) | Tests of the scripts above | `python -B -m pytest -c pytest-full.ini evaluation` |

## References after ARCore

**Update, 12 November 2026.** The product will not use ARCore ([owner decision 10](../../PROJECT_PLAN.md#owner-decisions-in-force)). `depth_check.py`, `orientation_control.py` and `landmark_probe.py` score against ARCore depth or tracked points. They remain valid on the existing recordings, as one estimate compared with another. They are not the reference for the product route. New scores use two references:

- tape-measured distances from the next recording round;
- points triangulated along the open tracker's path, held out from any sizing fit.

`stand_in.py` writes public clips into ARCore's fields of a recording. That is still the quickest way to feed known poses and depth through the pipelines until `sitescan/` takes poses from outside a recording ([DESIGN 7.15](../../DESIGN.md#715-removing-arcore-five-changes)).

## Known debt

Some of these still import experiment code: `stand_in.py` reads clips through
`research.experiments.sfm.src.sequences`, `score.py` uses the ICL reader in `research/experiments/sfm` and the
surface scorer in `research/experiments/04_surface_reconstruction`, and `layers/` uses the shared
contracts in `research/experiments/shared`. Moving those readers here is listed under Refactor status in the
[root README](../../README.md#refactor-status).
