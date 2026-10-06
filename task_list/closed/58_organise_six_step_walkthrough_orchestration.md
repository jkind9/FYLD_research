---
id: "58"
title: Organise six-step walkthrough orchestration and importable experiment components
status: closed
priority: CRITICAL
type: infra
approval_status: direct layer-run structure reviewed and software verified 2026-10-06; no product measurement acceptance claimed
blocked_by: []
blocks: [56]
verification_test: src/walkthrough/tests/test_pipeline.py
plan_reviewed: 2026-10-06 PASS
files:
  - src/walkthrough/**
  - pytest.ini
  - tools/check.py
  - task_list/open/56_benchmark_complete_walkthrough_accuracy_time_and_m.md
  - experiments/shared/runs.py
  - experiments/shared/tests/test_runs.py
  - experiments/03_camera_pose_estimation/src/validation/**
  - experiments/03_camera_pose_estimation/tests/test_validation_api.py
  - experiments/04_surface_reconstruction/src/backend.py
  - experiments/04_surface_reconstruction/src/recovery.py
  - experiments/04_surface_reconstruction/src/metric_surface.py
  - experiments/04_surface_reconstruction/src/validation/**
  - experiments/04_surface_reconstruction/tests/test_metric_surface.py
  - experiments/04_surface_reconstruction/tests/test_validation_api.py
  - experiments/04_surface_reconstruction/tests/test_surface.py
  - experiments/06_object_recognition/pilot/association.py
  - experiments/06_object_recognition/pilot/replay.py
  - experiments/06_object_recognition/pilot/tests/test_association_imports.py
  - experiments/06_object_recognition/experiments/01_detection/validation/**
  - experiments/06_object_recognition/experiments/02_segmentation/validation/**
  - experiments/06_object_recognition/experiments/03_appearance/validation/**
  - experiments/06_object_recognition/experiments/04_geometry_identity/validation/**
  - experiments/06_object_recognition/experiments/04_geometry_identity/run.py
  - experiments/06_object_recognition/experiments/04_geometry_identity/tests/test_validation_api.py
  - experiments/evaluation/stages/identity.py
  - experiments/evaluation/tests/test_stages.py
docs:
  - src/README.md
  - src/walkthrough/README.md
  - experiments/README.md
  - experiments/01_camera_capture_delivery/README.md
  - experiments/02_stereo_depth/README.md
  - experiments/03_camera_pose_estimation/README.md
  - experiments/04_surface_reconstruction/README.md
  - experiments/05_birds_eye_mapping/README.md
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/pilot/README.md
  - experiments/06_object_recognition/experiments/01_detection/README.md
  - experiments/06_object_recognition/experiments/02_segmentation/README.md
  - experiments/06_object_recognition/experiments/03_appearance/README.md
  - experiments/06_object_recognition/experiments/04_geometry_identity/README.md
  - experiments/evaluation/README.md
  - experiments/shared/README.md
  - README.md
  - task_list/README.md
baseline_metric:
  source: src/README.md:3 and source inventory below
  field: canonical six-step walkthrough runner
  baseline_value: "0 runners in src/walkthrough; 2 partial cross-layer benchmark runners"
  target: "1 canonical runner with 6 ordered steps; 0 duplicated method or score implementations"
created: 2026-10-06
last_updated: 2026-10-06
superseded_by: null
---

# Task58: Organise six-step walkthrough orchestration

## In plain English

Give the walkthrough one runner that calls six distinct steps in order. Keep each experiment usable on its own, with small components that the runner can import. Make segmentation and appearance optional. Keep independent error checks in each experiment and call them after predictions have been saved. This task organises existing work; later tasks prove depth, site measurements and phone performance.

## What

Create the canonical cross-layer runner under `src/walkthrough/`. This is a small restructure: extract two embedded functions, separate surface fault fixtures, add one metric surface boundary, and wire existing components through explicit imports. Do not redesign algorithms, rebuild every experiment runner or introduce a general plugin framework.

Code clarity and maintainability are release requirements at CRITICAL priority. Every new module has one job and a documented callable boundary. Existing small method/scorer modules stay in their experiments. A validation package may forward imports to an existing scorer; it must contain no duplicate scoring mathematics. Experiment-local trial/control runners remain standalone. All new complete walkthrough sequencing belongs to this root package; historical supplied-input replays remain explicitly labelled controls.

The owner requested six distinct steps on 2026-10-06. Earlier diagrams describe five visual layers by grouping reconstruction and mapping. Update documentation to explain the six execution steps consistently. Segmentation and appearance are optional components of step 6, not additional top-level steps.

Task54 owns real depth and its error analysis. Task55 owns dimensions/area and their error analysis. Task52 owns phone export/readiness. Task56 consumes this runner for independent physical accuracy, total time, peak memory and the complete evaluation report. Task09 retains persistence/inventory policy ownership. Software fixture success does not satisfy the active project's measurement goal.

## Why

Root `src/` has no implementation. The pilot replay combines detection, supplied depth, reference poses, localisation, counting and rendering. The Task22 generation combines historical supplied-input controls. Neither is a predictive six-step walkthrough. Importing these runners wholesale would introduce benchmark settings and reference answers into method execution.

The simple Task46 counting function and the identity scorer are currently embedded in runner files. The surface method delegates to an ICL control with fixed raw-depth units and model alignment. Small explicit boundaries let the root runner reuse these methods without treating benchmark assumptions as phone calibration.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Six experiment boundaries already exist | experiment index | six root steps | experiments/README.md:36 |
| Root implementation is absent | src README | new canonical runner | src/README.md:3 |
| Phone reader preserves absent depth/pose | shared PhoneFrame/read_phone_session | step 1 adapter | experiments/shared/phone_session.py:16; experiments/shared/phone_session.py:164 |
| Tracking kernel and backend are callable | track/CPUOdometry | step 3 adapter | experiments/03_camera_pose_estimation/src/tracking.py:39; experiments/03_camera_pose_estimation/src/backend.py:41 |
| Tracking input has calibrated arrays and a frozen depth-range restriction | RGBDFrame | root tracking adapter; no silent clipping | experiments/03_camera_pose_estimation/src/dataset.py:17 |
| Existing reconstruction assumes ICL raw units and alignment | reconstruct/compute/Frame | metric surface boundary; retain control | experiments/04_surface_reconstruction/src/backend.py:12; experiments/geometry_validation/src/control.py:36; experiments/geometry_validation/src/icl.py:16 |
| Detector and localisation are small reusable components | YoloDetector/localise_detection | step 6 adapter | experiments/06_object_recognition/pilot/detector.py:27; experiments/06_object_recognition/pilot/localisation.py:89 |
| Simple counting method is embedded in replay | associate_frame | replay tests and cached policy trial | experiments/06_object_recognition/pilot/replay.py:127; experiments/06_object_recognition/experiments/06_identity_policy/cached_replay.py:255 |
| Masks already have an independent callable boundary | segment/run_methods | optional step 6 component | experiments/06_object_recognition/experiments/02_segmentation/masks.py:31; experiments/06_object_recognition/experiments/02_segmentation/mask_pipeline.py:43 |
| Appearance components and independent analysis exist | crop/descriptor/feature modules; evaluator | optional step 6 component and validation | experiments/06_object_recognition/experiments/03_appearance/adapter.py:18; experiments/06_object_recognition/experiments/03_appearance/features.py:20; experiments/06_object_recognition/experiments/03_appearance/evaluator.py:6 |
| Identity scorer is embedded and called privately by report | _score | trial runner and report stage | experiments/06_object_recognition/experiments/04_geometry_identity/run.py:164; experiments/evaluation/stages/identity.py:56 |
| Surface recovery verifies historical scorer source | recovery source signatures | keep evaluation.py implementation in place | experiments/04_surface_reconstruction/src/recovery.py:24 |
| Shared records, coordinate mathematics, timing and publication already exist | shared package | all steps and run wrapper | experiments/shared/contracts.py:11; experiments/shared/contracts.py:39; experiments/shared/contracts.py:73; experiments/shared/geometry.py:1; experiments/shared/timing.py:49; experiments/shared/runs.py:137 |
| Source snapshots currently cover only experiments | shared _snapshot/Run._capture | new root runner provenance | experiments/shared/runs.py:79; experiments/shared/runs.py:209 |
| Report builder joins existing results rather than executing methods | evaluation build | Task56 report consumer | experiments/evaluation/run.py:90; experiments/evaluation/run.py:95 |
| Historical replays use supplied reference poses | pilot replay and Task22 generation | controls only | experiments/06_object_recognition/pilot/replay.py:492; experiments/06_object_recognition/experiments/05_replay/generation.py:152 |

### Owner clarification: direct readable flow

Each existing root step module will have one `run` entry. It will integrate its existing method body, timing, expected failure classification and prediction export. There will be no callable execution wrapper and no second `execute` facade. Each run accepts a root-decided StepResult and returns the final StepResult plus its existing typed output or None. A skipped step returns before importing methods or accessing upstream data.

The canonical run will make six explicit calls with numbered comments. It will accumulate statuses, then export whole-run results, hash predictions, call the distinct validation file, check hashes and publish. Only dependency decisions and error formatting are shared pure functions. Existing experiment method implementations, dedicated validation owners and standalone commands remain unchanged. Preprocessing stays beside its layer's run when small; it is not split into extra files without a need. Root tests will target the new run entry and explicitly check skipped/failed steps, original outputs and export failures.

### Six execution steps

| Order | Root adapter | Imported owner and output | Present boundary / missing work |
|---|---|---|---|
| 1 | steps/capture.py | Shared phone reader, under Task52's capture contract; validated frames/calibration/clocks | Recorded input first. Do not acquire a device or fake depth/poses here. |
| 2 | steps/depth.py | Task54 experiment method; metric depth, validity and provenance | Method absent. Explicit unavailable result until reviewed implementation is supplied; fixture provider only in tests/labelled controls. |
| 3 | steps/tracking.py | Tracking track and selected backend; estimated poses/status/segments | Adapt calibrated arrays without TUM loading/constants. Reject unsupported inputs explicitly; retain frozen method limits. |
| 4 | steps/surface.py | Surface experiment metric boundary; full observed geometry per origin | Use estimated pose and method depth. ICL alignment stays control-only; sampled viewer points cannot become quantitative geometry. |
| 5 | steps/mapping.py | Task55 experiment method; dimensions, defined area and observed/unknown coverage | Method absent. Explicit unavailable result until reviewed implementation is supplied. |
| 6 | steps/objects.py | Existing detector, localisation and extracted Task46 association; proposals, identity decisions/counts | Simple box-depth counting first. Segmentation/appearance explicitly selected and disabled by default. |

All root paths above are relative to `src/walkthrough/`. `pipeline.py` owns the six-step order and dependency checks. `config.py` owns explicit immutable configuration; `records.py` owns step status and whole-run results only, reusing shared metric records. `validation.py` dispatches to experiment validation imports after method outputs are sealed. `cli.py` is a thin entrypoint. Importing any of these modules must not start a run, load a model, download a file or create output.

Use explicit `importlib.import_module` names for numbered experiment packages, following existing repository imports. No path mutation, wildcard imports, automatic module discovery or global run state. Keep stage code in its owner. Six adapter modules call methods; they do not copy algorithm or scorer bodies.

### Exact extraction and import inventory

Line ranges refer to the inspected 6 October working tree. Confirm signatures/callers again before implementation; preserve others' edits.

| Source section/functions | Destination/action | Callers and preservation checks |
|---|---|---|
| pilot/replay.py:127-302, associate_frame including nested assignment solver | Move intact to experiments/06_object_recognition/pilot/association.py with numpy and linear_sum_assignment imports | replay imports/re-exports the same signature for existing tests, cached_replay.py:255 and Task46 controls. Keep default settings/provenance at their existing owner; no association policy changes. |
| 04_geometry_identity/run.py:164-225, _score | Move body to that experiment's validation/scoring.py as public score_identity | Keep run._score as compatibility import; change evaluation/stages/identity.py to public validation owner. Move its itertools/numpy/defaultdict requirements as needed; retain imports still used by run. Do not move unused _origin or change scoring interpretation. |
| 04_surface_reconstruction/src/backend.py:18-33, fault_points | Move fault fixture body to src/validation/controls.py | backend re-exports fault_points so standalone run.py controls remain unchanged. Keep reconstruct at backend.py:12-15 and geometry control compute at its existing owner. |
| Surface src/recovery.py:17 SAME_SOURCE and :96 dependency check | Add extracted validation/controls.py to recovery dependency checks and evidence copies | Controls-only changes must invalidate reused negative-control scores. A pre-extraction run missing this source is refused explicitly, with original evidence retained. Update test_surface.py checks for the new dependency. |
| Shared runs.py:79 _snapshot and :195 _capture | Extend shared snapshot coverage to include src/walkthrough source when present, retaining experiments coverage and exclusions | Snapshot dirty/untracked root runner code, refuse symlinks and preserve custom-run-root exclusion. test_runs.py must cover inclusion and hash changes. Existing repositories/runs without this folder retain their current source inventory. Do not build another snapshot helper in root. |
| ICL-specific surface compute boundary at geometry_validation/src/control.py:36-46 | Add src/metric_surface.py in surface experiment using existing shared backproject/transform_points primitives | Accept already-metric arrays, calibrated validity and estimated pose/origin. Return observed geometry, without raw /5000 conversion, supplied first pose or reference model alignment. Keep compute/reconstruct control signatures unchanged. No new surface algorithm or neutral copy of the whole ICL Frame type. |
| Tracking src/evaluation.py:13 read_references and :46 evaluate | Keep implementation; add src/validation/__init__.py explicit exports | Root validation imports through dedicated area. Existing CLI, report and tests can retain historical imports. Never expose reference reader to predictive steps. |
| Surface src/evaluation.py:11 validate_points, :27 nearest, :37 distance_summary, :54 DistanceTotals, :82 SurfaceScorer | Keep implementation; add src/validation/__init__.py explicit exports | Preserve recovery source-signature comparisons and saved source snapshots. Include controls export without importing backend back through validation. |
| Object 01_detection/scoring.py:174 evaluate; 02_segmentation/scoring.py:16 mask_scores and :45 instance_events; 03_appearance/evaluator.py:6 label_pairs and :18 rank_queries | Keep small pure modules; add explicit validation/__init__.py exports in each owning subexperiment | No scoring copies. Facades expose functions for compatible inputs only. Disabled optional components do not import or execute their validation code. |
| Detector :27, localisation :89, masks.segment :31, mask_pipeline.run_methods :43, appearance prepare_crop :18/describe_classical :55/FeatureExtractor :20 | Import at current owners; no relocation | Root adapters supply explicit inputs/configuration. Do not add optional model dependencies to the baseline or change descriptors/masks. |
| pilot/replay.py:403 replay; 05_replay/generation.py:152 execute; automatic.py/payload.py | Keep historical standalone supplied-input control runners; do not import their sequencing into root | Root pipeline is the sole current complete walkthrough runner. Preserve control commands, exports and sealed evidence. No parallel new complete runner in experiments/evaluation. |

Depth and mapping validation packages are created by Tasks54/55 alongside their methods. Until then, their adapters expose unavailable status and accept explicit test providers; do not create placeholder accuracy mathematics. Capture validation remains Task52's export/readiness checks. Matching existing score schemas to a new complete physical survey is Task56 work; structural wiring cannot invent missing measures.

### Implementation checklist

Scope refinement during implementation: `pytest.ini` and `tools/check.py` must discover the new root contract tests in normal repository checks. Their current lists name only experiment/tool tests (`pytest.ini:2`, `tools/check.py:64`). Add the root test directory without changing existing selections or the task-board hygiene guard. This is test wiring, not a second runner or a benchmark command change.

1. Record import/caller baselines and inspect current diffs. Write behaviour, import and failure tests first. Record all inherited settings used by controls; no new experimental settings or hardware choices.
2. Perform the intact counting/scorer/fault-fixture extractions with compatibility imports. Add dedicated validation import surfaces and verify equivalent results on the same inputs.
3. Add the narrow metric surface boundary and six adapters. Keep algorithm calls, input adaptation, output export and evaluation separate. Ground-truth files/identities cannot be fields in method configuration or step inputs.
4. Add the one sequential pipeline and thin CLI. A required missing/failed stage stops dependent execution and leaves an explicit incomplete result. A requested partial run keeps all six slots visible with skipped/unavailable reasons; it cannot advertise full measurements. Validation runs only for available compatible outputs/references.
5. Define a run-local origin boundary around the unchanged counting method: never associate positions across different world/segment IDs. Per-origin counts stay separate; do not sum them into a whole-site distinct count or imply cross-segment identity recovery. Task09/later measured refinements own that policy.
6. Reuse shared Run/verify_run and TimingLedger for provenance, stage costs and sealing, extending the shared source snapshot to include the root runner. Freeze and hash prediction artifacts before scorer access while Run remains running; verify those hashes after scoring, then call Run.finish only for final publication. Scorers receive read-only prediction data and separate references. Record diagnostic/scoring costs separately. Do not materialise all high-resolution session arrays merely to pass them between stages; use owned artifacts/iterators and document their lifetimes. Actual resource acceptance remains Task56/57.
7. Keep files focused (normally 200-400 lines, hard maximum 800); target functions below 50 lines. The intact extracted association function is an explicit temporary size exception: preserve numerical behaviour rather than redesign its nested solver in this organisation task. No new algorithm duplication, implicit I/O, swallowed errors, unexplained globals or circular imports. Methods remain usable without importing src/walkthrough.
8. Update the declared READMEs with six-step order, public import examples, optional components, validation ownership, missing methods, standalone controls and failure/recovery behaviour. Keep tests/scratch outside task_list. Obtain Python/code review and fresh finished-diff review before closure; fix or explicitly record findings.

## Invariants and recovery

| Producer/owner | Consumer | Representation (units/space/schema) | Survives restart? | Evidence |
|---|---|---|---|---|
| Task52/shared phone reader | capture/depth adapter | original grid/crop/rotation, camera ID, nanoseconds plus declared clock; absent pose/depth explicit | source bundle retained externally, verified hashes | experiments/shared/phone_session.py:16 |
| Depth provider/tracking experiment | surface/object adapters | camera-axis depth metres, calibrated same-grid validity; camera-to-world pose with world/segment/source | staged artifacts only after shared run verification | experiments/shared/contracts.py:39; experiments/03_camera_pose_estimation/src/dataset.py:17 |
| Shared geometry/metric surface owner | mapping/measurement owner | full observed points in declared world/segment, metres; no independent truth alignment | sealed geometry artifacts, never viewer sample as source | experiments/shared/contracts.py:103; experiments/shared/geometry.py:1 |
| Extracted Task46 association | object step/count consumer | copied state, same-class geometric decisions; scoped to one origin | only published evidence; no new persistence policy | experiments/06_object_recognition/pilot/replay.py:127 |
| Independent reference owners | experiment validation only | reference data and existing scorer-specific schema, separately labelled supplied controls | retained survey/control inputs; verified report | experiments/03_camera_pose_estimation/src/evaluation.py:13; experiments/06_object_recognition/experiments/04_geometry_identity/run.py:164 |
| Shared run/timing owners | pipeline/report consumer | stage status/provenance, timing scope, hashed artifacts | only verified completed publications count as complete | experiments/shared/runs.py:59; experiments/shared/runs.py:137; experiments/shared/timing.py:49 |

Source of truth: original verified inputs, explicit reviewed settings and method output artifacts. References remain scorer-only. Nanoseconds are converted to seconds explicitly with a recorded clock mapping; no guessed clock alignment. Missing calibration, depth, pose or unresolved origins remain visible. RGB-only input must not be forced into Observation, whose schema requires a pose.

This task adds no worker service or parallel scheduler. Boundaries are ordinary function calls or verified artifact paths. Import/configuration failure produces no run; stage failure leaves an incomplete unsealed run; method success followed by scoring failure preserves method evidence but never publishes a scored success. A retry creates a new run using shared publication rules; no automatic resume or replacement of sealed outputs.

Fresh checkout: restore verified source data/checkpoints from their recorded external location, install only explicitly selected method dependencies, run import/fixture controls, then invoke the root CLI. Offline missing dependencies/data produce a named failure and no download. Numerical benchmark settings, historical source snapshots, stored reports and existing standalone commands remain unchanged. Compatibility imports preserve old public names; a changed source hash is new provenance, not permission to rewrite prior evidence.

## Hyperparameters

hyperparameters n/a: organisation and deterministic software controls only; no new scientific settings, model selections, acceptance limits or device experiments. Six execution steps are owner-requested structure, not an experimental tunable. All method settings remain explicit/inherited from their existing owners. Before any real trial, audit hyperparameters and freeze the complete relevant table in its owning task; this task does not authorise GPU trials.


### Inherited control settings retained

No control settings were changed or new physical trials run. These are the exact existing tables in the two runner files touched by extraction. The root counting configuration requires explicit values; software tests reuse the Task46 0.35-m distance and 0.05-m ambiguity margin. Fixture depths, image sizes, timestamps and reference planes are deterministic test inputs, not experimental settings.

| name | value | source |
|---|---|---|
| experiments.06_object_recognition.pilot: model | `"YOLO26x COCO"` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: checkpoint_sha256 | `"9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92"` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: package | `"ultralytics==8.4.172"` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: device_precision_batch | `["cuda:0", "FP32", 1]` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: prediction_settings | `{"augment": false, "batch": 1, "conf": 0.25, "half": false, "imgsz": 640, "iou": 0.7, "max_det": 300, "rect": true, "save": false, "verbose": false}` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: class_handling | `"retain all detector classes and proposals"` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: sequence_span | `[1305031454.127701, 1305031472.79564]` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: frame_count_cap | `60` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: frame_sampling | `"integer linspace over paired RGB-D rows; include both endpoints"` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: rgb_depth_pose_tolerance_s | `0.02` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: intrinsics | `[640, 480, 525, 525, 319.5, 239.5]` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: depth_units_validity | `[5000, "0 < depth_m < 4"]` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: pose_quaternion | `"finite nonzero quaternion normalized"` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: localisation_support | `["all valid box pixels", "nearest valid pixel to box centre"]` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: association | `{"ambiguity_margin_m": 0.05, "ambiguity_rule": "unresolved when an alternative full-cardinality assignment is within the margin", "assignment": "global maximum-cardinality then minimum total distance", "max_distance_m": 0.35, "outside_gate": "create provisional identity at any frame when no feasible existing-track candidate exists", "position_source": "world-coordinate box median", "retention": "all selected frames; no expiry inside clip", "same_class_only": true}` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: display_sampling | `[500, 20000, "integer linspace"]` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.pilot: repeats | `1` | inherited experiments/06_object_recognition/pilot/replay.py:46; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: reference | `{"cup_ids": 1, "enrollment": 4, "evaluation": 7, "frames": 6, "monitor_ids": 2, "observations": 11, "tuning": false, "validation": 0}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: appearance | `{"device": "no inference; cached FP32 vectors", "manifest_sha256": "f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4", "run": "experiments\\06_object_recognition\\experiments\\03_appearance\\runs\\20261004T135203.039973Z_fd481f16c8374ca2a0f04d6f0703a16d", "vectors": 11}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: conditions | `["geometry-last", "geometry-viewmedian", "appearance-viewmedian", "combined-last", "combined-viewmedian"]` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: geometry | `{"calibration": [640, 480, 525, 525, 319.5, 239.5], "camera_median_then_world_transform": true, "component_quantiles": "NumPy linear", "pixel_centres": true, "raw_missing": 0, "support": "provisional binary polygon", "units_per_metre": 5000, "valid_range_m": [0, 4]}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: pose | `{"revision": "supplied-base-v1", "segment_id": "continuous_capture", "time_tolerance_s": 0.02, "world_id": "tum_freiburg1_desk_mocap"}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: metric_gate | `0.35` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: appearance_gate | `0.8` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: combined_cost | `{"alternative_gap": 0.05, "appearance_weight": 0.5, "geometry_weight": 0.5}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: costs | `{"appearance": "(1-cosine)/2", "comparison": "maximum cardinality, minimum total cost", "geometry": "distance/current_gate", "numeric_tolerance": 1e-12}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: origin_policy | `"session/world/segment must match; unknown origin stays outside metric identities"` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: duplicates | `{"same_class_iou_min": 0.9, "winner": null, "world_distance_max_m": 0.02}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: view_groups | `{"frame_votes": 1, "rotation_max_deg": 10, "translation_max_m": 0.05}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: birth | `"first usable frame per class seeds all valid nonduplicates; later unmatched same-class stays pending"` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: location | `"fixed generation anchor; surface camera median transformed to world; representative median or last; no similarity/confidence weighting; no automatic relocation"` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: spread | `"coordinate min/max/IQR, radial spread and estimate shifts; no covariance or centre-error claim"` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: revision | `"full generation recomputation from camera coordinates; stable IDs and decisions; synthetic relocation only"` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: ordering_ids | `"timestamp then opaque observation key; UUID5 schema/condition/session/origin/first key; exact evidence replay required"` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: execution | `"one serial CPU writer; fresh run; no overwrite; immutable completed-run reader"` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: runtime | `{"numpy": "2.4.2", "opencv": null, "pillow": "12.3.0", "scipy": "1.17.1", "torch": null}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |
| experiments.06_object_recognition.experiments.04_geometry_identity: resource | `{"conditions": 5, "frames": 6, "gpu_forwards": 0, "models_loaded": 0, "observations": 11}` | inherited experiments/06_object_recognition/experiments/04_geometry_identity/run.py:21; unchanged owner provenance |

## Verification

Contract test: `src/walkthrough/tests/test_pipeline.py` asserts the call list is exactly capture, depth, tracking, surface, mapping, objects, once each for a deterministic injected six-step fixture. It asserts 0 scorer calls before method outputs are sealed; no independent truth reaches any method. Missing required providers and deliberate stage errors prevent downstream calls and prevent complete publication. Disabled optional providers have 0 calls/imports/model loads. Changing or crossing an origin cannot reuse a track state or report a whole-site distinct count.

Additional tests assert import produces 0 output files/downloads/model initialisations; every experiment method imports without src/walkthrough; public validation exports return exactly the existing scorer results; association extraction gives identical decisions/state/IDs for existing Task46 boundaries and error inputs. Surface adapter tests use independently specified arrays and expected world points, preserving metric units/calibration/origins and refusing mismatches; no product accuracy target is inferred from these fixtures. Existing camera/surface/replay commands and recovery/source-snapshot checks remain usable, with no altered frozen inputs.

Shared snapshot tests assert dirty/untracked src/walkthrough sources are copied and hashed, and generated run directories remain excluded. Recovery tests assert changing only the extracted fault fixture refuses reuse, and a historical snapshot lacking that dependency fails with a named reason. Prediction mutation during scoring prevents completed publication. These provenance checks are required alongside the six-step fixture.

Before: 0 root walkthrough runners; 2 partial supplied-input runners; 0 root six-step contract checks. After: 1 canonical runner, exactly 6 explicit step slots, 0 duplicate algorithms/scorers, passing meaningful import/compatibility/failure controls. The new path may remain unavailable for real depth/area until Tasks54/55 land. That is a truthful engineering result, not completion of the measured walkthrough goal.

Before start: run task-plan lint, obtain a fresh plan review against current code and draft constitution, and record PASS. Before close: run scoped tests and relevant existing regressions, record before/after and reviewed exceptions, update docs, and obtain Python/code and independent diff reviews. Existing uncommitted changes are preserved and excluded from claims about this task's diff.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No new commit created. Reviewed working-tree implementation based on HEAD `684468d01c1f32b98b531c2922bd409583716150`; existing mixed uncommitted work preserved. Commit/publication is outside this delivery and is not claimed. |
| Files changed | 62 implementation/test/README paths: the root runner and static artifact contracts; intact counting/identity/fault extractions and compatibility imports; validation facades; metric surface boundary; root-source snapshots and recovery dependency checks; normal test discovery. Task58 receipts/board links and Task56's completed dependency are updated separately. |
| Test status | RED tests observed missing modules and old snapshot/recovery behavior before implementation. Consolidated regressions: 643 passed, 7 skipped, 193.45 s. After the final typed boundaries and saved-artifact guard: 88 root/identity checks passed, 56.67 s. After the first readability change: 88 passed, 39.51 s. Final single-entry layer structure: 656 passed, 7 skipped, 188.37 s; production root coverage 89.05%, tests excluded. Strict mypy: 14 production files passed. Scoped Ruff passed with N999 excluded for the required numbered-package convention. Black checks passed. |
| Before measurement | 0 canonical root runners; 2 partial supplied-input benchmark runners; 0 root six-step contract checks. |
| After measurement | 1 canonical root runner with exactly 6 explicit ordered slots. Tests exercise real tracking, full metric backprojection and Task46 association on deterministic inputs. Disabled optional imports/reference loaders have 0 calls; required failures remain unpublishable; different origins have separate counts and no whole-site count. |
| Delta | +1 canonical runner; +6 explicit execution slots. Extracted function bodies are AST-equivalent to their baseline after the identity scorer rename. No algorithm/scoring copies or new measured-product results. |
| Decision-gate outcome | PASS for this organisation task only. Fresh plan review PASS; final code review APPROVE; Python review APPROVE after type fixes; independent finished-diff review found no confirmed defects or unresolved suspicions. Real depth, site measurements and complete/sustained resource acceptance remain unavailable or unmeasured under Tasks54-57. |

### Verification and review evidence, 6 October 2026

- The consolidated command was `python -B tools/check.py src/walkthrough/tests experiments/shared/tests experiments/04_surface_reconstruction/tests experiments/03_camera_pose_estimation/tests experiments/06_object_recognition/pilot/tests experiments/06_object_recognition/experiments/01_detection/tests experiments/06_object_recognition/experiments/02_segmentation/tests experiments/06_object_recognition/experiments/03_appearance/tests experiments/06_object_recognition/experiments/04_geometry_identity/tests experiments/06_object_recognition/experiments/06_identity_policy/tests experiments/evaluation/tests tools/tests -q`.
- The final command was `python -B tools/check.py src/walkthrough/tests experiments/06_object_recognition/experiments/04_geometry_identity/tests -q --cov=src.walkthrough --cov-config=outputs/task58-test-temp/coverage.ini --cov-report=term-missing --cov-fail-under=80`. Coverage excluded test code. CLI subprocess behavior was checked separately; its lines are not instrumented by the parent coverage process.
- Windows sandbox temporary-directory ACLs initially prevented fixture setup. Read-only/import checks ran, but those setup errors are not represented as code passes. Re-running test commands outside that restriction produced the successful receipts above. Parallel Black checks stalled under the same sandbox; owned workers were stopped and successful single-worker checks used. No external Claude sessions were launched.
- The fresh plan review required an explicit failure exit because shared Run auto-finishes clean exits. Missing/failed/partial states now write inspectable results, then fail publication. Prediction files and their hashes exist before a scorer/reference loader runs; mutation, scorer failure or a completed state without an artifact refuses publication.
- Root prediction metadata and file handles have static schemas. Shared Calibration/Pose and the owning experiment's backend/serialized record boundaries remain in place. The initial Python review blocked missing type contracts and a CLI default; both findings and formatting findings were fixed, then re-reviewed. No review finding is waived.
- Captured data with unsupported distortion, skew, rotation, cropped/resized calibration or the tracker's frozen valid-depth range is refused. No phone grid conversion, depth/area algorithm, numerical acceptance target or successful physical measurement was invented. Software-provider inputs are labelled and isolated in tests.
- Snapshot tests cover dirty/untracked root sources, changed hashes, links and custom run roots. Surface recovery rejects controls-only source changes and historical snapshots without the extracted dependency. Original runs and source snapshots were not rewritten.
- All 18 declared READMEs were updated. Local links resolve and both overview diagrams contain six blocks. The task-board audit still reports pre-existing oversized vendor/source files and unrelated open-task metadata gaps; this task does not claim to clean that board.
- The isolated final implementation review diff excludes baseline uncommitted work. SHA256 before the readability follow-up: `9ba9fea9ed9284a748d565d8ca2caaf0b3b3fce77a3ce986814aa05e99cf3b4a`. Commit/publication receipt intentionally states no commit rather than fabricating a SHA or bundling others' changes. There is no outstanding engineering follow-up for Task58; later measurement work has its own tasks.

### Planning receipt, 6 October 2026

- Source mapping inspected the exact extraction bodies, imports, consumers and recovery dependencies. Existing uncommitted work was preserved.
- Fresh plan review identified missing root-source snapshot coverage and a missing extracted-fault recovery dependency. Both corrections and regression assertions are now in scope. The review also prompted explicit prediction hashing before final Run publication and documentation coverage for all six experiment overviews.
- Task-plan lint had no errors; its unstamped-review warning is resolved by the recorded verdict. Board lint scanned 59 tasks with 0 errors and 0 warnings. Task58 links resolve; Task51 remains the only active task.
- Board audit is not clean: it reports the planned src/walkthrough/README.md as absent, plus existing repository findings. That README is an implementation deliverable; no source files, modules or experimental results have been created in this planning session.
- Implementation tests, physical-device checks and measurement runs were not executed. Task56 now depends on this task and consumes its runner instead of owning a second orchestration path.

### First readability follow-up, 6 October 2026

- The owner requested direct flow with inline comments and no unnecessary wrapping. Task58 was reopened before editing. The six calls now appear directly in `pipeline.run`; the extra sequencing function was removed. Dependency checks use early returns. This first revision retained a shared step helper for timing, status and prediction export. The owner rejected that remaining execution wrapper; it was removed in the final revision below. Numbered comments mark each step; separate comments mark result export, prediction hashes, reference validation, score export and final publication.
- Existing behaviour, boundary, compatibility and failure checks were rerun: 88 passed in 39.51 s. Root production coverage is 88.62%. Strict mypy passed 14 files, Ruff passed and single-worker Black passed. No behaviour or data contract was changed.
- Code review and Python review both APPROVE with no findings. This was an intermediate review. The final structure was reviewed again below. The intermediate patch normalized-text SHA256 was `3bde88a79692f698f5d5ce50371de866a840340f5a234df92dee4e1925ea3610`. This patch includes the task-board README, which was previously recorded separately.

### Final direct layer-run structure, 6 October 2026

- Fresh plan review PASS and plan lint passed after the owner requested plain ordered layer calls. Each existing root layer file now has one run entry containing its existing method work, timing, expected-error handling and prediction export. There is no execute facade or callable execution wrapper. The root run makes six explicit calls, then exports results, records prediction hashes, calls the distinct validation file, checks integrity and publishes. Small preprocessing helpers remain beside their layer. Object detector selection, localisation and association are visible in its one run function; optional evidence has its own helper in the same file.
- Updated root tests were RED with 10 missing-run-entry failures before implementation. They now check layer export before the next call, all six non-pending guards without input access or method imports, export failures for each layer and unexpected error propagation. Final consolidated command uses the same regression paths above plus root coverage flags. Result: 656 passed, 7 skipped in 188.37 s. The skipped tests require directory symlink support (2) or explicitly configured pinned historical run folders (5); they are not claimed as passes.
- Root production coverage is 89.05%, with tests excluded. Strict mypy passed 14 production files. Ruff passed. Final single-worker Black checks passed for all 18 package/test files. An initial final-format check identified one pipeline formatting correction; applying it preserved the complete Python syntax tree. No executable change followed the successful regression run.
- Code review APPROVE and Python review APPROVE with no findings. Independent diff review checked all six behavioral surfaces and directly probed skipped guards, dependencies, partial continuation, missing depth and export failure. It found no confirmed defects or unresolved suspicions. The reviewer did not independently rerun the full suite; the executed consolidated result is recorded above.
- The independent reviewed on-disk patch SHA256 was `8bfd1d1b6deab4529ece03658fc1decca9b4b0f5bb9297a6a02d0aca32d2d664`. The final artifact after the syntax-tree-equivalent formatting correction has on-disk SHA256 `89fc33cb8b159ecbfeb6358cacf913e829637e7a59c30b2caf1a03d63651d366`. The independent reviewer compared both artifacts, confirmed identical syntax trees and retained the no-defect verdict for this final artifact. All 31 unrelated tracked diffs matched the starting snapshot; `git diff --check` passed. No commit, external Claude session, historical evidence rewrite, new numerical setting or physical measurement was made.
- Missing real depth and mapping/dimensions/area remain explicitly unavailable. Optional segmentation and appearance stay disabled by default. Physical accuracy, complete workload latency, peak memory and sustained edge operation still need the later tasks' measured evidence. No Task58 engineering follow-up remains outstanding.
