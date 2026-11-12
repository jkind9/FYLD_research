# Demo and viewer pages

Builders for offline HTML pages. Each page is one file with its data, scripts and styles
inside, so it opens in a browser without a server or network. The pages read saved outputs;
none reruns a model. Generated pages go under `outputs/`, which git ignores, because they
embed photos.

| File | What it builds or does | Run it |
|---|---|---|
| [`build.py`](build.py) | The seven demo pages from saved experiment runs (overview, depth to 3D, camera tracking, surface accuracy, Gaussian splats, bird's-eye map, objects in 3D) into `outputs/demo_pages/` | `python -B -m tools.demos.build --source-root <checkout with local runs and data>` |
| [`capture_scene.py`](capture_scene.py) | A Gaussian-splat viewer of a recorded walk's surface, with photo bookmarks; `--frames` adds the room build's frame-by-frame view | `python -B -m tools.demos.capture_scene --surface <surface.ply> --session <recording> --out <viewer.html>` |
| [`cleanup_scene.py`](cleanup_scene.py) | The room before clean-up, with switches that show or hide what the visibility vote removes, beside a clean-up trial's scores | `python -B -m tools.demos.cleanup_scene --trial <trial folder> --session <recording> --out <page.html>` |
| [`cleanup_tuner.py`](cleanup_tuner.py) | The raw fused room with every clean-up stage on a switch and every setting on a slider | `python -B -m tools.demos.cleanup_tuner --attributes <attributes folder> --session <recording> --out <page.html>` |
| [`run_report.py`](run_report.py), [`run_pages.py`](run_pages.py) | Six report pages for one run of the layer-by-layer runner in `research/evaluation/layers` | `python -B -m tools.demos.run_report <run folder>` |
| [`screenshot.py`](screenshot.py) | Opens every page in headless Chromium, saves screenshots and reports page errors and network requests | `python -B -m tools.demos.screenshot --pages outputs/demo_pages --out <folder>` |
| [`page.py`](page.py), [`pack.py`](pack.py), [`geometry.py`](geometry.py) | Shared parts: page assembly, compact array encoding, back-projection, splats and top-down grids | Imported by the builders |
| [`pages_overview.py`](pages_overview.py), [`pages_results.py`](pages_results.py), [`pages_scene.py`](pages_scene.py), [`sources.py`](sources.py) | The demo pages' content and the pinned runs they read | Imported by `build.py` |
| [`web/`](web/) | The pages' JavaScript (`viewer.js` and one script per page) and `style.css` | Embedded by `page.py` |
| [`tests/`](tests/) | Tests of the builders, including pages opened in Chromium | `python -B -m pytest -c pytest-full.ini tools/demos` |

Run every command from the repository root with `.venv/Scripts/python.exe`. The trial and
attribute folders come from `research/experiments/surface_cleanup` (`denoise_trial` and `cleanup_attributes`).
The demo pages date from 5 October and describe the research-stage layers; the
[walkthrough notebook](../../notebooks/00_sitescan_walkthrough.ipynb) shows the current pipeline.
