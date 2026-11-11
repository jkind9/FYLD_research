# Product tests

Tests of `sitescan/` and `apps/`. The default lane runs in about 10 seconds.

| Lane | Command | What it checks |
|---|---|---|
| Behaviour (default) | `.venv/Scripts/python.exe -B -m pytest` | Small hand-made inputs with known answers, one file per stage plus the pipelines |
| Golden | `.venv/Scripts/python.exe -B -m pytest -m golden` | Both orchestrators on the committed fixture recording; every output number matches the saved one within 0.1% or 1 mm. Needs the local depth weights |
| Everything | `.venv/Scripts/python.exe -B -m pytest -c pytest-full.ini` | This lane plus every test under `evaluation/`, `experiments/` and `tools/` (about 1,600 tests) |

| Path | What it holds |
|---|---|
| `test_sitescan_<stage>.py` | Behaviour tests of one stage |
| `test_pipelines.py` | The live and room orchestrators on synthetic frames, and the command line |
| [`golden/`](golden/README.md) | The golden-output runner and its test |
| [`fixtures/`](fixtures/README.md) | The 20-frame public test recording and its saved outputs |

Rules: one test for each branch, loop or parser; test what a stage computes, not how it
rejects input; no tests of exact error messages.
