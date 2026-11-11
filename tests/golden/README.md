# Golden outputs

A golden output is a saved result from known-good code. A rewrite must reproduce it.

| Path | What it does |
|---|---|
| [`run.py`](run.py) | Runs the room build and the live processor on a recording and writes their outputs as JSON. The live processor is fed every frame and updated after each one, without threads or timing, so the result does not depend on machine load. Objects are off |
| [`test_golden.py`](test_golden.py) | Compares a fresh run with `tests/fixtures/tum_desk_20_golden.json`: same keys, counts within 0.1%, lengths within 1 mm |

Run the check with `.venv/Scripts/python.exe -B -m pytest -m golden` (about 25 s). Rewrite
the saved outputs only after a reviewed behaviour change:

```text
.venv/Scripts/python.exe -B -m tests.golden.run --session tests/fixtures/tum_desk_20 --out tests/fixtures/tum_desk_20_golden.json
```
