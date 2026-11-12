# Tools

Developer tools. Nothing in `sitescan/` imports them.

| Path | What it does | Run it |
|---|---|---|
| [`check.py`](check.py) | Runs the full test suite with every cache and temporary file under the system temp folder, after checking that `task_list/` holds only task records | `.venv/Scripts/python.exe -B tools/check.py` |
| [`function_index.py`](function_index.py) | Rewrites the function index in the root README from the code: every public function and class in `sitescan/` and `apps/`, with arguments, first docstring line and a link. `--check` exits 1 when the README is out of date | `.venv/Scripts/python.exe -B -m tools.function_index` |
| [`runs.py`](runs.py) | Lists runs under `outputs/` from their `run.json`, filtered by recording, tool, label text or setting; `--index` writes `outputs/index.html` with links to each run's pages and screenshots and flags folders outside the layout | `.venv/Scripts/python.exe -B -m tools.runs [--index]` |
| [`demos/`](demos/README.md) | Builders for offline single-file HTML pages: the demo pages, room viewers, the clean-up tuner and run reports | See its README |
| [`tests/`](tests/) | Tests of the tools above | `.venv/Scripts/python.exe -B -m pytest -c pytest-full.ini tools` |

Run `python -B -m tools.function_index` after adding, renaming or documenting a public
function; `tools/tests/test_function_index.py` fails until the README matches the code.
