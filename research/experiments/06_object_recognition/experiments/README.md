# Object recognition sub-experiments

This folder holds the numbered trials of [experiment 06, object recognition](../README.md). Each trial asks one question about finding objects in recorded frames, telling them apart across views, or keeping one identity for one physical object. Most trials reuse the same small recording: six frames, or the 60-frame sequence they come from, of the TUM Freiburg1 desk scene.

The labels in these trials are coarse and were inspected earlier, so results are descriptive checks of the software and the recording. They are not accuracy on unseen data.

| Folder | Question | Status | Entry point |
|---|---|---|---|
| [`01_detection/`](01_detection/README.md) | Do saved YOLO26x boxes find and place objects correctly? | Scored on six frames against coarse outlines, on 5,000 COCO photos for box placement, and on the desk recording for box wobble over time. | `run`; `placement_run`, `jitter_run` |
| [`02_segmentation/`](02_segmentation/README.md) | Does a classical mask (filled rectangle, GrabCut, Canny contour) give a better depth reading of an object than its box? | Descriptive run on six frames. No accuracy claim is possible with the coarse outlines. A planned comparison has not started. | `run` |
| [`03_appearance/`](03_appearance/README.md) | Can colour and texture alone tell the same object from another across views? | Run on eleven observations. The learned features ranked one monitor wrongly; ORB and SIFT matched no recorded pair. The learned features need a CUDA GPU to recompute. | `run` |
| [`04_geometry_identity/`](04_geometry_identity/README.md) | Do position rules, with or without appearance, connect sightings of one object? | Five rules replayed on eleven sightings. Four recover the cup's return after an empty frame. | `run` |
| [`05_replay/`](05_replay/README.md) | Do the best rules hold on the full 60-frame recording, shown in a browser viewer? | Published. The cup keeps one ID across the empty frame. Needs the saved inputs of an earlier run. | `run` |
| [`06_identity_policy/`](06_identity_policy/README.md) | Does letting a new object start an identity at any frame fix detections that went unassigned? | Replayed on the 60 frames. Unassigned detections fall from 226 to 56. No independent labels exist to check the new IDs. | `cached_replay` |
| [`07_spatial_uncertainty/`](07_spatial_uncertainty/README.md) | Does matching on the whole visible surface of a box beat matching on one median depth? | A matching module is built and tested. It is not wired into the published replay and has no scored comparison. | none (library) |
| [`08_spatial_uncertainty_latency/`](08_spatial_uncertainty_latency/README.md) | Does reusing exact nearest-neighbour indexes speed up that surface matching? | Timed on 60 frames. The speed-up is 1.05 times, which the README calls inconclusive. | `run.py` |

## How to run it

Run from the repository root with the project environment, CPU unless a row above says otherwise. The usual form is:

```text
.venv/Scripts/python.exe -B -m research.experiments.06_object_recognition.experiments.<folder>.run
```

Each trial publishes a new run folder under its own `runs/` and never edits an old one. Several trials read the saved outputs of an earlier trial, so a fresh checkout needs those run folders; each trial's README names them. `08_spatial_uncertainty_latency/run.py` has no command-line options and starts a full timing run when executed.

## Where results are recorded

Each trial's README holds its own results. The overall status and the plan for experiment 06 are in the [experiment 06 README](../README.md).
