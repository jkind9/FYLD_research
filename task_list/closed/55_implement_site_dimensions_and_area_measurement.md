---
id: "55"
title: Implement site dimensions and area measurement
status: closed
priority: HIGH
type: infra
approval_status: planning authorised 2026-10-06; owner delegated execution and first settings on 2026-10-07 ("Progress the project and tasks as much as you can")
blocked_by: []
blocks: []
verification_test: "experiments/05_birds_eye_mapping/tests/test_measurement.py"
plan_reviewed: 2026-10-07 PASS
files:
  - experiments/05_birds_eye_mapping/**
  - src/walkthrough/steps/mapping.py
  - src/walkthrough/steps/surface.py
  - src/walkthrough/steps/contracts.py
  - src/walkthrough/visualization.py
  - src/walkthrough/cli.py
  - src/walkthrough/tests/**
docs:
  - experiments/05_birds_eye_mapping/README.md
  - src/walkthrough/README.md
  - task_list/README.md
baseline_metric:
  source: task_list/README.md and reuse evidence below
  field: implemented site-area calculations with independent known-shape tests; walkthrough runs with a real mapping layer
  baseline_value: "0 site-area calculations; 0 known-shape tests; 0 of 9 recorded walkthrough runs with a real mapping layer"
  target: "1 tested measurement component passing 8 known-shape tests; 1 real-method walkthrough run with all 6 layers complete and a top-down map visual"
created: 2026-10-06
last_updated: 2026-10-07
superseded_by: null
---

# Task55: Implement site dimensions and area measurement

## In plain English

Turn the 3D points the earlier steps produce into sizes in metres: how long and wide the seen area is, how much ground was seen, and how much inside that area was never seen. First check it on made-up shapes whose answers are known in advance. Then plug it into the full walkthrough so every run ends with a top-down picture showing what was seen, how high it was, and what was missed.

## Board update, 7 October 2026

Task51 was rescoped on 6 October 2026 to the first prerecorded pipeline. Field decisions (site, boundary, survey) belong to Task61. The known-shape tests and the walkthrough adapter need no field decision. The owner asked on 7 October 2026 to progress the project as far as possible; the settings below were chosen by the assistant under that delegation and are labelled so.

## What

1. `experiments/05_birds_eye_mapping/measure.py`: a seeded NumPy RANSAC dominant-plane fit refined by least squares (SVD) on its inliers, an in-plane basis from the principal axes of the projected points, and a grid footprint measurement over metric points with an explicit up vector: observed footprint area, area on the plane itself, region rectangle (length and width), unknown area inside that rectangle, height range above the plane, plus the grids (observed mask, highest point per cell). It never guesses "up"; the caller passes it.
2. `experiments/05_birds_eye_mapping/preview.py`: a top-down image of one footprint (height colours, unseen cells grey, scale bar in metres).
3. `src/walkthrough/steps/surface.py` and `SurfaceShard`: each shard also records `camera_centre_m`, the camera position in that origin's world (the translation of the pose already read at surface.py:66). Mapping then knows which side of the plane the cameras were on without reading another layer's files.
3b. `src/walkthrough/steps/mapping.py`: a `GridFootprint` mapping method. It measures each tracking origin separately (separate worlds are never combined) and orients up towards that origin's mean camera centre. The estimator may return either the existing plain measurements dict or a `MappingResult(measurements, maps)`; `maps` holds per-origin metadata (world, segment, plane source, plane point and normal, basis, grid origin, cell size, or a skip reason) and in-memory grids. `mapping.run` validates first, then saves each grid as `output/predictions/mapping/<index>.npz` and lists it in a new optional `maps` field, so a validation failure leaves no orphan grids. Measurement values are cast to plain `float`.
4. `src/walkthrough/visualization.py`: render each saved map with `preview.py` and list it in the visual manifest.
5. `src/walkthrough/cli.py`: `--mapping grid-footprint`.

## Why

Mapping is the only walkthrough layer without a method, so no run completes all six layers. A coloured point cloud is not a size answer. The first real runs (Task51, 7 October) produce metric surfaces that this layer can measure.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Mapping is a swappable method receiving the saved surface and run path, returning named measurements | `MappingMethod`, `mapping.run` | pipeline step 5 | src/walkthrough/steps/mapping.py:13-19,22-44 |
| Completed mapping needs finite values with explicit units | `mapping.validate` | pipeline | src/walkthrough/steps/mapping.py:47-61 |
| Surface shards are per-frame Nx3 metre points with world and segment IDs | `SurfaceShard` | mapping | src/walkthrough/steps/contracts.py:123-135; src/walkthrough/steps/surface.py:80-92 |
| Mapping output type has methods, control, measurements | `MappingOutput` | visualization, scoring | src/walkthrough/steps/contracts.py:138-141 |
| Mapping visual today is a data card only | `visualization.mapping` | visual index | src/walkthrough/visualization.py:581-597 |
| Shared transforms exist; no plane fit or grid projection exists | experiments/shared/geometry.py | — | experiments/shared/geometry.py:55-77; searched `ransac`, `segment_plane`, `fit_plane` in experiments/ and src/: none |
| Grid method, unknown-not-empty rule and output list are already described | experiment 05 README | this task | experiments/05_birds_eye_mapping/README.md:11-20 |

### Steps

1. Write `experiments/05_birds_eye_mapping/tests/test_measurement.py` first. Expected answers come from the shape definitions, not from the production projection. Each shape has one sample exactly at its corner (0, 0), which fixes the grid origin there, and every other sample at x = 0.005 + 0.01k, so no sample can fall on a cell edge (multiples of 0.05 m from the corner). Shapes: (a) flat 2 m x 3 m rectangle on that lattice (k = 0..199 by 0..299), up = +z: footprint 6.00 m² exactly (40 x 60 cells), length 3.00 m and width 2.00 m exactly (the region spans observed cell edges); (b) the same rectangle without the points in x in [0.5, 1.5) and y in [1.0, 2.0) (hole edges on cell edges): observed 5.00 m², unknown 1.00 m², region still 2.00 m x 3.00 m; (c) the rectangle rotated 30° about the up axis and tilted 20°, with the plane found by RANSAC (not declared) and up given: footprint within perimeter x cell (0.50 m²) of 6.00 m² and length/width within two cells (0.10 m); (d) a 0.5 m x 0.5 m axis-aligned board 0.8 m above the centre of shape (a), with the floor under it still sampled: footprint 6.00 m² and plane area 6.00 m² (unchanged), maximum height 0.80 m within 1 cm; also the same board in a corner leaves footprint 6.00 m² because the basis uses plane inliers only; (e) RANSAC on a noisy floor (2 mm noise) with 30% off-plane clutter recovers the normal within 1° and is identical for the same seed; (f) empty input, non-finite points and a non-metre unit label raise `ValueError`; (g) cell size must be positive and finite; (h) the walkthrough adapter keeps two tracking origins separate, names measurements per origin, skips an origin with fewer than 3 points with a recorded reason, and fails only when every origin is skipped.
2. Implement `measure.py` and `preview.py` to pass them.
3. Add `camera_centre_m` to surface shards; `GridFootprint` and `MappingResult` to `src/walkthrough/steps/mapping.py`; the optional `maps` field to `MappingOutput`; the map render in `visualization.mapping` (drawing code lives in `experiments/05_birds_eye_mapping/preview.py` so visualization.py stays under 800 lines); `--mapping grid-footprint` in the CLI; and the mapping row of the layer-contract table in src/walkthrough/README.md. Tests: surface shard field, adapter, plain-dict compatibility and CLI choice in `src/walkthrough/tests/`.
4. Run the real 30-frame Task51 clip with Kinect depth (reference control) and with Depth Anything; record the measurements and check the top-down image by eye.
5. Update experiment 05 README (status, method, settings, results), walkthrough README and the board.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Surface layer | GridFootprint | Nx3 float points in metres, per (world_id, segment_id), plus `camera_centre_m` per shard (new) | sealed run files | src/walkthrough/steps/surface.py:66,80-92 |
| GridFootprint | mapping.validate, visualization, later Task56 report | measurements `{value, units}`; per-origin npz grids with cell size, grid origin, plane point/normal and basis | sealed run files, hashed before scoring | src/walkthrough/pipeline.py:88-92 |
| measure.py | preview.py | observed mask and max-height grid in metres above the plane; unseen cells NaN | regenerated from points | this task |

- Source of truth: saved surface points plus the declared settings; any measurement is recomputable.
- Separate tracking origins are never merged; each gets its own plane and grid.
- The plane is the dominant plane found by RANSAC, labelled `fitted_dominant_plane`; it is not a surveyed site floor. On a desk recording it is the desk top.
- Unseen cells are unknown, never empty ground. The unknown area is only counted inside the region rectangle; space outside it is not claimed either way.
- Process death: the pipeline's run folder stays incomplete; rerun into a fresh folder.
- Backward compatibility: `maps` is optional and a plain measurements dict is still accepted, so the existing fixture `no_site_measurements` (src/walkthrough/tests/providers.py:45) keeps working. `camera_centre_m` is a new shard field; nothing reads shards by exact key set.

## Hyperparameters

| name | value | source |
|---|---|---|
| cell size | 0.05 m | confirmed 2026-10-07 (owner delegated: "Progress the project and tasks as much as you can"); example value in experiments/05_birds_eye_mapping/README.md:12 |
| plane source | dominant plane by RANSAC over all points of one origin | confirmed 2026-10-07 (owner delegated) |
| RANSAC inlier distance | 0.02 m | confirmed 2026-10-07 (owner delegated) |
| RANSAC iterations | 500 | confirmed 2026-10-07 (owner delegated) |
| RANSAC fit sample | 50,000 points, uniform without replacement | confirmed 2026-10-07 (owner delegated) |
| random seed | 0 | confirmed 2026-10-07 (owner delegated) |
| plane band for plane area | ±0.02 m (same as inlier distance) | confirmed 2026-10-07 (owner delegated) |
| up direction | plane normal oriented towards the origin's mean camera centre (from `camera_centre_m`); `measure.py` itself takes an explicit up vector | confirmed 2026-10-07 (owner delegated) |
| plane refinement | least-squares (SVD) refit on RANSAC inliers | confirmed 2026-10-07 (owner delegated) |
| in-plane basis | principal axes of the plane inliers (points within the plane band) projected onto the plane, so clutter cannot turn the grid; first axis = larger spread; each axis's sign chosen so its largest-magnitude component is positive | confirmed 2026-10-07 (owner delegated) |
| grid origin | minimum projected coordinate on each in-plane axis | confirmed 2026-10-07 (owner delegated) |
| observed cell | at least 1 point | confirmed 2026-10-07 (owner delegated) |
| origin skip | an origin with fewer than 3 points is skipped with a reason; the layer fails only if all are skipped | confirmed 2026-10-07 (owner delegated) |
| preview height colours | 0 m to the origin's highest cell; unseen cells grey | confirmed 2026-10-07 (owner delegated) |
| region rectangle | bounding rectangle of observed cells in the principal-axis grid, measured on cell edges | confirmed 2026-10-07 (owner delegated) |
| height summary per cell | highest point above the plane | inherited experiments/05_birds_eye_mapping/README.md:13 (highest-surface rule) |
| units | metres and square metres | inherited experiments/05_birds_eye_mapping/README.md:19,56-57 |

## Verification

- Contract test `experiments/05_birds_eye_mapping/tests/test_measurement.py`: the shape assertions in How step 1, each with the expected value written from the shape definition.
- Walkthrough test: `GridFootprint` on two synthetic origins returns separately named measurements, writes one npz per origin, passes `mapping.validate`, and the visual manifest lists one map image per origin.
- Before: 0 site-area calculations, 0 runs with real mapping. After: the Task51 30-frame clip completes all six layers with real methods (Kinect-depth control and Depth Anything), with numbers recorded below. No physical accuracy is claimed: there is no surveyed reference for the desk (Task53).

## Receipts

| Field | Value |
|---|---|
| Closing commit | `bfb70f2` |
| Files changed | New: `experiments/05_birds_eye_mapping/measure.py`, `preview.py`, `tests/test_measurement.py`, `src/walkthrough/tests/test_mapping.py`. Changed: `src/walkthrough/steps/mapping.py` (GridFootprint, MappingResult, validate_maps, grids saved after validation), `steps/surface.py` and `steps/contracts.py` (`camera_centre_m`, optional `maps`), `visualization.py` (top-down map per origin), `cli.py` (`--mapping grid-footprint`); experiment 05 README, walkthrough README, task board |
| Test status | 20 known-shape tests pass (`experiments/05_birds_eye_mapping/tests`); 185 walkthrough + experiment 05 tests pass together; Ruff clean. Tests written first and seen failing (module missing; then 7 red for the review findings) |
| Before measurement | 0 site-area calculations; 0 known-shape tests; 0 runs with a real mapping layer |
| After measurement | 30-frame TUM xyz clip, all six layers real, exit 0. Kinect depth: desk plane 2.21 m², seen 4.09 m², region 4.40 x 3.10 m, unknown 9.56 m², 51% of points on the plane. Depth Anything: 7.44 m², 16.37 m², 5.25 x 5.85 m, 14.35 m², 17%. Identical on rerun and after the streaming rewrite. Runs `outputs/task55_real_runs/reviewed_xyz60_every2_{recorded,depth-anything}` |
| Delta | +1 tested measurement component; first runs completing all six layers with real methods; learned depth inflates measured areas 3-4x against sensor depth |
| Decision-gate outcome | Component and walkthrough method done. Physical accuracy unmeasured (no surveyed desk; Task53/Task56). The plane is the dominant fitted plane, not a site floor; a site floor needs Task61's region definition and gravity or a marker |

Plan review 2026-10-07: FAIL. Mapping cannot see camera positions, so "up towards the cameras" was not buildable; shape (a) with edge points gives 6.25 m², not 6.00 m². Revised: camera centres added to surface shards, interior sampling, cell-edge region, a `MappingResult` return type, grids saved after validation, and the remaining settings declared.

Re-review 2026-10-07: PASS after fixing two more findings (edge-sample lattice; clutter turning the grid). The reviewer simulated shapes (a), (b) and (d) in 1,780 runs with exact expected values.

Blind diff review 2026-10-07 found three defects, all fixed with tests written first:
1. One unmeasurable origin (collinear or repeated points, or too few on the plane) failed mapping for every origin. Now each origin is measured separately and a failure is recorded as that origin's skip reason; the layer fails only if no origin can be measured (`test_one_unmeasurable_origin_does_not_hide_the_others`).
2. Each origin loaded all its points at once (about 153 bytes per point, about 52 GB for a 1,362-frame recording) and MemoryError was not caught. `measure.py` now reads points one surface shard at a time through `PointChunks` (three passes; results equal to the in-memory version cell for cell, `test_streamed_chunks_give_exactly_the_in_memory_result`), and refuses grids over 16,000,000 cells (`MAX_GRID_CELLS`, 200 m x 200 m at 5 cm) with a clear reason.
3. A custom map record passed validation and then crashed the visual export. `validate_maps` now checks origin, IDs, skip reason, cell size, plane source and grid shapes before anything is saved (`test_map_records_are_validated_before_the_layer_completes`).
Also handled: surface records saved before `camera_centre_m` existed make that origin skip with a named reason instead of a KeyError.
New setting from the review: grid cell limit 16,000,000 cells, chosen under the owner's delegation (2026-10-07).
