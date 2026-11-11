# Notebooks

| Notebook | What it shows |
|---|---|
| [`00_sitescan_walkthrough.ipynb`](00_sitescan_walkthrough.ipynb) | The room build in one call, then each of its steps by hand (frame choice, depth, scale, fusion, clean-up, mapping) with a picture after each, and a check that the hand-run steps give the same numbers. Then one live update unwrapped the same way, and optional object detection and counting |

The notebook runs on the 20-frame public test recording in `tests/fixtures/tum_desk_20`, on
the CPU, in under a minute. It is saved with its outputs, so it can be read on GitHub without
running it.

## Run it

Install with `uv sync --all-extras` (the `dev` extra holds the Jupyter kernel). Open the notebook in VS Code or Jupyter with the `.venv` interpreter and run all cells. It needs
the depth weights in `models/`; the objects section also needs `models/yolo26x.pt` and skips itself
without it. To re-run it headless and save the outputs:

```text
.venv/Scripts/jupyter-execute.exe --inplace notebooks/00_sitescan_walkthrough.ipynb
```

Only public data goes in a committed notebook: never run it on a household recording and commit the result.
