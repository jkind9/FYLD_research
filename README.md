# FYLD scene-mapping research

This repository studies whether phone captures can produce useful, measurable maps of visible work areas and identify distinct objects across repeated views. Work is organised into six independent experiments so each stage can be tested before connecting the pipeline.

Start with the [experiment plan](experiments/README.md). It explains the six pieces, their inputs and outputs, independent controls and the role of the Samsung S23 and Redmi Note 11 Pro. The [dataset guide](experiments/datasets/README.md) explains how to test the later stages without phone capture. The [task list](task_list/README.md) records priorities and completion evidence.

The [research reading guide](research/sources/README.md) links the individual source summaries covering phone depth, reconstruction, tracking, evaluation datasets and construction-site use.

The [background explanation](research/sources/00_start_here.md) introduces the pipeline. The [research index](research/README.md) links the comparison table, bibliography, dataset catalogue and permission checks.

The [Task 00 prototype](archive/task00_prototype/README.md) preserves preliminary desktop runs and their limitations. [Shared src](src/README.md) is ready to build incrementally. No experiment has yet established performance on either phone or on construction sites.

The active folders are `experiments/`, `research/`, `src/`, `data/` and `task_list/`. `archive/` holds earlier work. Local virtual environments and fetched reference repositories are ignored runtime resources.

## Starting point

Task 03 now has a [CPU geometry control with per-input stage exports](experiments/geometry_validation/README.md#implemented-geometry-control). It accepts an explicit subset of the acquired ICL data and records source/version/settings alongside the original inputs, numerical outputs and visuals. GPU runs require the user's permission before execution.

Use `python -B tools/check.py -q` for checks. It stores pytest temporary files, coverage, lint caches and Python bytecode policy outside the repository under the operating system's temporary folder. Pytest's repository cache is disabled. Use `python -B` for experiment commands, `ruff check --no-cache` for linting, and an external `--cache-dir` for direct mypy calls. Existing generated caches were removed. Git metadata, editor settings, registered worktrees and virtual environments are retained because they are not disposable test caches.

Task 04 now has a [measured CPU surface baseline](experiments/04_surface_reconstruction/README.md#implemented-cpu-baseline): nine supplied-depth/supplied-pose views produce 2.73 million observed points, with 7.85 mm mean reference distance and 22.29% whole-reference coverage within 5 cm. Task 08 prepared the WSL python-for-android toolchain and built a verified arm64 smoke APK; camera support on both phones remains untested. Task 09 now has a checked-input SQLite identity store with 10 passing controls, but no object recognition or labelled revisit evaluation. Task 05 now has a [30-frame CPU tracking trial](experiments/03_camera_pose_estimation/README.md#completed-cpu-trial): 2.14 image pairs/s for tracking, 1.69 frames/s including reporting, and 6.93 mm camera-position error. Task 13 has acquired the held-out desk archive and matched 573 RGB/depth timestamps; full-sequence and held-out tracking evaluation remain outstanding. Shared run metadata records stage times and FPS.

The first intended result is a measured reconstruction with a verifiable object inventory. No phone performance or construction-site accuracy has been established. Processing placement remains a comparison between the phone, a local edge computer and a backend.

## Experiment layout

The implemented control lives in [geometry_validation](experiments/geometry_validation/README.md). It consumes known depth and known camera poses. [03_camera_pose_estimation](experiments/03_camera_pose_estimation/README.md) estimates camera motion on CPU; [04_surface_reconstruction](experiments/04_surface_reconstruction/README.md) builds and scores supplied-input surfaces. Shared mathematics and run exports live in [experiments/shared](experiments/shared/README.md).

See the [folder tree and processing flow](experiments/README.md#folder-structure-and-processing-flow) for all six stages and where object identity fits. An existing SLAM package can supply a backend within these boundaries. The current geometry control has not estimated camera motion or validated such a package.

## Repository contents

Git includes research summaries, plans, task receipts, first-party source and tests, and dataset acquisition/calibration records. Raw datasets, downloaded reference repositories, model weights, virtual environments, caches, generated geometry and raw assistant transcripts remain local. The historical prototype is retained as an archive, with unfinished validation stated explicitly.

A fresh clone does not contain benchmark images or reference surfaces. Follow [dataset acquisition and verification](data/README.md) before running data-dependent work. Environment observations in the archive are historical records, not a current installation guarantee. Raw session evidence referenced by the recovery review is also local-only; the reviewed summaries and source inventory are included.


## Reading the experiment outputs

Each inspection view distinguishes observed input, ground truth, predicted output and evaluated output. Observed input is a captured measurement. Ground truth is an independent reference answer. Predicted output is an estimate made by our code. Evaluated output is a computed surface or comparison against a reference. Being supplied as an input does not by itself make a value ground truth.

Stage 03 uses measured Kinect colour and depth from TUM. Its camera reference poses come from an independent motion-capture system. The depth can contain noise and missing pixels; it is not a depth-model prediction. Stage 04 uses clean synthetic ICL depth and supplied reference poses to establish the reconstruction baseline. Its reconstructed point surface and distance maps are results generated by our code. [TUM data description](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) and [ICL data description](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html).

The 16-bit source depth images contain measurements rather than display colours. Use the labelled depth-in-metres preview and its missing-pixel mask to inspect them. Keep the linked originals for numerical work. Visual previews must not fill holes or smooth measurements without declaring that transformation.

Open the [camera-motion inspection](experiments/03_camera_pose_estimation/runs/20261002T195923.778722Z_8bcaf965d8dc496192563205df59d85c/viewer.html) or the [reconstructed point-surface inspection](experiments/04_surface_reconstruction/runs/20261002T195928.219822Z_55d2d0bfa455453eb2289a5e717490c1/viewer.html). Both are verified CPU-only inspection publications with frame stepping, source images and explicit reference labels. Original runs and numerical results are preserved.
