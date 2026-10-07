---
id: "51"
title: Define and build the first prerecorded walkthrough pipeline
status: open
priority: HIGH
type: infra
approval_status: first prerecorded-pipeline scope confirmed by owner 2026-10-06; field acceptance limits remain pending
blocked_by: []
blocks: [53, 54, 55, 57]
verification_test: "src/walkthrough/tests/test_pipeline.py"
plan_reviewed: 2026-10-06 PASS
files:
  - .gitignore
  - pytest.ini
  - data/README.md
  - experiments/01_camera_capture_delivery/README.md
  - task_list/open/51_agree_success_criteria_and_the_first_deployment_ta.md
  - task_list/open/52_build_and_verify_a_usable_phone_recording.md
  - task_list/open/53_collect_independent_scene_measurements_and_object_.md
  - src/walkthrough/**
  - src/README.md
  - task_list/README.md
  - README.md
docs:
  - data/README.md
  - task_list/README.md
  - README.md
  - experiments/01_camera_capture_delivery/README.md
  - src/walkthrough/README.md
  - src/README.md
baseline_metric:
  source: task_list/README.md and reuse evidence below
  field: run the first prerecorded input through the existing pipeline layers
  baseline_value: "0 prerecorded-video input adapters in src/walkthrough"
  target: "1 prerecorded input adapter with preserved frame identity and explicit missing metadata"
created: 2026-10-06
last_updated: 2026-10-07
superseded_by: null
---

# Task51: Define and build the first prerecorded walkthrough pipeline

## Clarifications

### Session 2026-10-06

- The owner selected the available Redmi for later capture and live checks. That device choice is separate from this prerecorded-file pipeline. Its runtime support and physical capture remain unverified.
- The owner selected existing prerecorded training data as the first pipeline input where it has references suitable for the layer being scored. A construction video may be sourced later if needed.
- The owner selected MasterPC with GPU available as the current local processing host. This is not a deployment or a claim that all stages use the GPU.
- The owner confirmed the current model's supported classes and existing components. No new model or framework is being selected for this integration work.
- The owner deferred camera streaming and FastAPI hosting. Frame skipping and lower resolution are future evaluation dimensions; their values and effects are not yet measured.
- The owner asked to leave numeric product acceptance limits pending. Scene-specific objects, revisit conditions, independent survey method and original-data recovery details are not needed to glue existing referenced training data, but remain open for later field work.
- All numeric accuracy, coverage, waiting-time, live-update, sustained-use, memory, battery and heat targets remain pending, as requested.

### Owner correction 2026-10-06: first integration run

| Choice | Owner decision | Boundary |
|---|---|---|
| First input | Use prerecorded footage. Prefer suitable footage already in the project with usable references; a construction video may be sourced later if existing data does not exercise the needed flow. | No physical site visit or camera capture is part of the first pipeline run. TUM `freiburg1_xyz` is a practical existing-data recommendation, not a separately confirmed dataset choice. Do not treat TUM desk labels as independent ground truth or feed supplied depth/pose references into method predictions. |
| Object classes and model | Use the classes supported by the existing model and connect the established components. | Do not select a new detector, framework, or class list as part of the glue work. |
| Processing host | Use MasterPC with its GPU available for now. | This is the current local processing host, not a deployment or proof that every component uses the GPU. |
| Input delivery | Read local prerecorded files for the first run. A temporary MasterPC upload location is not needed for this training-data integration. | Prepare a clear input boundary so a FastAPI upload adapter or camera-stream client can be added later; do not build either now. |
| Sampling and image size | Support frame skipping and lower-resolution inputs as later evaluation dimensions. | No frame interval, resolution, or performance effect is chosen or claimed here. Preserve source frame IDs, timestamps, and geometry when any conversion is later evaluated. |
| References | Use references already supplied with the selected training data when their scope and provenance match the layer being scored. | Keep references out of runtime methods. Where video has no ground truth, a later task must measure uncertainty against independently labelled examples; model confidence alone is not an error estimate. |
| Depth method | Depth Anything V2 is a candidate to assess against the existing depth contract. | It is not selected, installed, run, or accepted by this decision. Its relative-depth default and metric variants must be distinguished before any metric claim. |
| Earlier phone choice | The Redmi remains the confirmed device for later capture and live checks. | It is outside this prerecorded pipeline run. ARCore support and physical capture remain unverified. |
| Product limits | All numerical accuracy, coverage, timing, live-update, and resource limits remain pending. | The integration run demonstrates code flow only and cannot pass field or deployment acceptance. |

### Earlier field recommendations, still pending for later field acceptance

| Item | Evidence | Recommendation | Owner state |
|---|---|---|---|
| First use case | The project targets worksite walkthroughs (README.md:1-8). Existing TUM desk views have no physical survey (task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:63). | Start with one controlled indoor worksite room or bay that the owner can survey. Keep stationary items in place across visits. | Pending site access and owner choice. |
| Objects and revisits | Existing desk labels show a white-cup return and two similar monitor enclosures, but labels are provisional and there is no measured object anchor (task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:63). | Use owner-selected worksite objects. Include one look-away/return and one similar-looking object that is physically distinct. Record any moved object separately. | Pending object names and revisit conditions. |
| Phone and depth path | The owner selected a Redmi for capture/live checks. Its supplied capability report identifies model 2201116TG, Android 13, and reports camera inventory and permission checks passing; it contains no captured images or ARCore result (experiments/01_camera_capture_delivery/README.md:211-230). Xiaomi's [official Redmi Note 11 Pro guide](https://alsgp0.fds.api.xiaomi.com/xiaomi-b2c-i18n-upload/user-guides/1c100fb724c5e54a94ff40e423c5d7ef.pdf) identifies 2201116TG as Redmi Note 11 Pro. Google's [current ARCore device list](https://developers.google.com/ar/devices) lists Redmi Note 11 Pro with Depth API support. This makes ARCore depth a documented candidate for the reported model. It does not prove ARCore runtime support, delivered depth quality, or metric accuracy on this handset. The capability APK has no ARCore SDK, and the Camera2 report advertises no DEPTH16 stream; those facts do not rule out ARCore's computed Depth API. The local Gradle cache has no `com.google.ar` dependency. The Windows shell has no ADB command or Android SDK path variables. The pinned WSL SDK contains ADB at `/home/jkind/Android/Sdk/platform-tools/adb`; earlier `adb devices -l` returned no devices, `usbipd list` showed no Android handset, and the SDK has no emulator binary or configured AVD. | Keep the Redmi for capture/live checks and test ARCore Depth API on the actual device when it is available. Record runtime support, captured RGB/depth/confidence, calibration and timestamps; do not treat the model list as a depth result. Keep final processing on the owner-selected host. | The exact phone model is identified by the supplied device report and Xiaomi's guide. A cached Camera2 package is verified; physical image export, ARCore runtime support, depth quality, current device connection and host confirmation remain unproved. |
| Final-processing host | Read-only host inventory on 2026-10-06 reports `MasterPC`, AMD Ryzen 9 9950X, Gigabyte X870 GAMING X WIFI7. The frozen CPU tracking runs completed on this host. | Use this PC for final processing unless the owner names another host. | Pending owner confirmation. |
| Independent survey and identities | Task40 requires surveyed anchors, dimensions, a separate frame link, instrument uncertainty and human-reviewed identities (task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:67-73). | Use an available calibrated tape or distance meter to survey the room and selected object anchors. Record instrument details and uncertainty. Have a person record which objects are the same or distinct before viewing predictions. | Pending tool availability and owner method. |
| Raw-data retention and recovery | Media payloads are excluded from Git, and a fresh checkout does not include them (data/README.md:5; .gitignore:78-101). | Keep the original phone export and survey bundle in an owner-controlled location outside Git. Record its location and file hashes so an offline fresh checkout can restore the inputs and verify them. | Pending storage location and recovery method. |
| Numeric limits | The owner explicitly asked to leave every numeric target pending in the 2026-10-06 reply. | Keep all numeric acceptance fields pending. Do not label any trial as a product pass until these limits are agreed. | Pending owner values. |

## In plain English

Define the first software run through the existing layers using recorded video and its available references. Keep the code easy to follow and leave camera streaming and field acceptance for later. Record unresolved accuracy and performance limits without guessing values.

## What

Build the first prerecorded pipeline run using suitable existing footage and matching references, the current model's supported classes, and MasterPC with GPU available. Connect existing stages; do not select or trial a new model. Keep the main flow, run context, per-layer settings, outputs and validation purpose clear in plain English, with flat calls and no nested orchestration. Export visual previews for each stage and record the producing method with every preview. Accept local recorded input now and leave a narrow boundary for future upload or stream adapters. Frame skipping and lower resolution need later per-stage evaluation; no values are assumed. Future field work still needs owner-agreed accuracy, coverage, latency, offline-use, sustained-use, memory, battery, heat, survey and storage limits. The Redmi remains the confirmed phone for later capture/live checks, not the input device for this run.

## Why

The existing runner is organized around a phone export and its layer calls hide the meaning of shared context, broad configuration, and step state. The owner clarified that the immediate need is a readable pipeline run over prerecorded data. A later FastAPI or camera-stream adapter should feed the same layer contracts. That work does not settle field accuracy or deployment limits.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| The first pipeline scope is now owner-confirmed; field limits remain pending | Current task board | pipeline integration and later field tasks | task_list/README.md:13 |
| Device/runtime evidence is limited | Capture experiment | capture and edge plans | experiments/01_camera_capture_delivery/README.md:196 |
| Reference design exists | Task40 | measured-scene plan | task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:65-73 |
| Test and diagnostic scratch belongs outside task records | Task board guidance | future project checks | task_list/README.md:21; tools/check.py:11-27 |
| Controlled-scene source files need full Git exclusion and a retrieval record | Task53 input plan | future checkout and preparation | .gitignore:78-101; data/README.md:5 |
| The canonical runner already has six ordered direct stage calls; it currently accepts phone-session input | Task58 runner | prerecorded pipeline implementation | src/walkthrough/pipeline.py:51; src/walkthrough/steps/capture.py:26 |
| The TUM camera reader owns safe source-path and timestamp parsing plus shared calibration | Camera tracking experiment | local prerecorded RGB input adapter and separate reference loader | experiments/03_camera_pose_estimation/src/dataset.py:14-16,57-76,14-16 |
| Local TUM xyz RGB files are available for a repeatable recorded input | Existing project data | capture/input adapter | data/tum/rgbd_dataset_freiburg1_xyz/rgb.txt |
| TUM xyz ground-truth poses have a dedicated parser and tracking evaluator | Camera tracking experiment | scorer-only tracking reference request | experiments/03_camera_pose_estimation/src/evaluation.py:13-33; data/tum/rgbd_dataset_freiburg1_xyz/groundtruth.txt |
| Score requests separate reference loading from methods but save no reference identity today | Walkthrough scorer | reproducible score record | src/walkthrough/validation.py:20-24,144-194 |

1. Add a local TUM prerecorded input option to the CLI and input adapter. Use the existing safe RGB timestamp reader and shared calibration owner; retain each RGB relative path as frame identity and save its source table index alongside it. This input adapter reads no depth/pose frames. Normalize only shared fields: stable source frame ID, RGB path, source ID, timestamp in seconds with timestamp-source label, and shared `Calibration` when provided. Keep phone crop/grid details in the phone input record; do not make them required fields for every source. Preserve supplied TUM depth and pose on the scorer side. Do not require phone-only CLI arguments for the TUM input path. Missing timestamp or calibration stays absent; a dependent layer must return unavailable before runtime if it requires the missing field. Update the shared image record and the depth/tracking/object consumers to handle absent fields without raising a missing-key error.
2. Keep each layer's runtime, relevant configuration, output, and validation purpose visible in `src/walkthrough/pipeline.py`. Plain-English comments should explain the shared run context, layer-specific settings and what each validation checks. Keep the six calls explicit and avoid nested orchestration or generic dispatch machinery. Current depth and mapping methods are not ready, so the first integration may stop at an unavailable layer; the report must say this plainly and must not imply all six outputs completed.
3. Keep `Configuration` as the validated CLI/run snapshot. Pass its `CaptureConfiguration` view only to input, and its `ObjectConfiguration` view only to object recognition. Keep `StepResult` and `Result` because they record each layer's status and whole-run completion. Keep `ScoreRequest` because it separates reference loading from methods. Keep the `TypedDict` records because each experiment adapter exchanges named data fields. Do not add forwarding classes or duplicate experiment methods.
4. Add an explicit TUM tracking-reference request in the CLI, pass it to `run`, and store its source path and file hash with the score result, including an unavailable result when tracking predictions are not ready. Keep the reference loader and answers out of method calls. Extend `ScoreRequest` to carry that source identity.
5. Leave frame skipping and resolution values unset until their effect is measured per stage. Keep original frame identity, time and calibration lineage.
6. Keep model references out of method inputs. A video without ground truth needs a later uncertainty evaluation against independently labelled examples; confidence scores alone are not validated uncertainty.
7. Treat Depth Anything V2 as a candidate only. Do not claim metric depth unless a selected metric checkpoint and its scale are validated under Task54.
8. Update the declared READMEs to distinguish this local prerecorded pipeline from future phone capture, FastAPI hosting, camera streaming and field acceptance.
9. Keep generated test artifacts out of the task board: root pytest discovery excludes `task_list/`, and ignore rules cover accidental test scripts, caches and job-allocation probe folders there.
10. Export visuals from saved stage outputs: recorded RGB input, predicted depth, its binary validity mask and a colour coverage overlay on the RGB source, the estimated camera path, a full-point coloured PLY with a labelled PNG preview, a mapping measurement card or an explicit no-geometry status, and object boxes with provisional IDs or an explicit zero-proposal count. Write an offline `output/visualizations/index.html` and `manifest.json`; every stage and visual artifact names its producing method and source. Show valid-pixel counts on mask and coverage views. Label software-control object boxes as synthetic. PNG previews include the method in the footer and PNG metadata. PLY headers include the method and source frame. Reuse the existing depth preview and point-cloud display helpers. Clearly label display-only conversions and sampling. Never draw TUM supplied depth or poses as method predictions.

## Invariants and recovery

| Data or side effect | Producer / owner | Consumer | Representation and boundary | Survives restart? |
|---|---|---|---|---|
| Prerecorded video and optional reference files | Local input adapter | Capture/input validation and separate scorer | Preserve source path and hash, stable source frame identity, timestamp in seconds and calibration only with original values and provenance. TUM input reads `rgb.txt` directly; use each RGB relative path as frame identity and save the source table index. The adapter uses only source RGB, timestamp and shared calibration as method input; supplied depth/pose stay in the scorer-only reference path. | The original files remain unchanged. The adapter records source identity and source-provided metadata in the run output. |
| Frame artifacts and visual previews | Input and stage adapters | Later methods, scorers and the offline visual index | Keep numeric predictions unchanged. Each preview names its producing method and source artifact in the visual manifest; display-only colour, projection or point sampling never feeds back into scoring. A point-cloud PLY retains all reconstructed points; any smaller PNG preview records its display sample count. Missing method output is shown as unavailable, not replaced with invented geometry. | The visual manifest, previews, method-labelled prediction records and original numeric artifacts are saved in the run folder and covered by its final hash manifest. |
| Run folder and stage artifacts | `Run` from `experiments/shared/runs.py:151-245`, named `run_context` by the pipeline | Stage writers and final report | The run context owns the output folder, settings snapshot, timing and artifact inventory. See `src/walkthrough/pipeline.py:116-141`. | Interrupted runs remain incomplete. A retry uses a fresh run folder and never resumes by reusing partial outputs. Task58 records this existing behavior in `task_list/closed/58_organise_six_step_walkthrough_orchestration.md:178-182`. |
| Predictions and references | Stage outputs and independent validation inputs | Scorer | Save/hash predictions before scoring; do not pass references into runtime methods. Each score request names its reference source and source-file hash. The TUM scorer hashes one byte payload and parses that same payload. See `src/walkthrough/pipeline.py:116-133` and `src/walkthrough/validation.py:20-24,151-205`. | Saved predictions and the score request's declared reference source are identified in the run record, even when a score is unavailable because predictions are incomplete. A failed validation cannot mark the run complete. |

This task runs locally over prerecorded files. The CLI must allow a reader to select the existing phone-export path or a local prerecorded dataset path without requiring phone-only flags for dataset input. TUM `freiburg1_xyz` is the practical first-input recommendation because it already exists with timestamps and calibration; the owner approved existing data generally but did not name this sequence. The adapter copies only method inputs; supplied depth and pose remain separate references. The TUM walkthrough input reads the RGB timestamp table directly, retains each relative image path as frame identity, and saves the source-table index. It does not pair or load the dataset's depth frames. A shared frame record carries source identity, image path, optional timestamp and optional shared calibration. It does not require phone-only crop-grid fields. Generic video may be ingested only when its reader can preserve available source data; a layer missing a required timestamp or calibration returns unavailable before method execution. No timestamp, calibration or geometry is invented. This task does not add a deployed service or a second process boundary. Existing Task13 inputs and settings remain unchanged. A fresh local run starts from the original selected file and creates a new run folder; if a stage is unavailable or fails, the report keeps that status and does not claim a complete walkthrough. No field storage location, recovery interval, numeric threshold or missing measurement is invented. The draft constitution is not automatically ratified.

## Hyperparameters

hyperparameters n/a: no experiment. This task records owner choices; each execution task must audit and declare its inherited or owner-confirmed settings before it starts.

## Verification

- Contract check: `src/walkthrough/tests/test_pipeline.py` must assert the exact ordered stage calls, the layer-specific inputs passed to each call, that each stage output is validated before the next stage runs, and that an unavailable or failed stage remains incomplete in the final report. Adapter coverage must assert that source frame identity and available metadata are preserved, absent metadata is not fabricated, surface/object frame IDs match their upstream inputs, empty mapping measurements are rejected, and dependent layers do not run without required fields. Visual export checks must assert that the index and manifest include all six stage statuses, every visual records its producer and source, depth masks preserve invalid pixels and report valid-pixel counts, software-control boxes are labelled synthetic, and the PLY retains the full cloud while any preview sampling is labelled. Do not add model, camera or field trials as part of this check.
- Baseline and target: the current source has 0 prerecorded-dataset input adapters in `src/walkthrough`; the target is 1 local TUM adapter that preserves source frame identity and metadata and routes supplied depth/pose only to validation. Record the actual result in Receipts. No metric result is claimed.
- Scoring contract: the TUM CLI builds and passes a tracking `ScoreRequest` naming `groundtruth.txt`; saved scores retain the source path and SHA-256, even when tracking predictions are unavailable. The reference loader stays outside stage inputs.
- The code and `src/README.md` must make the local prerecorded-file flow clear and distinguish it from later upload, stream, field acceptance and uncertainty evaluation. Numeric product limits stay pending.
- `pytest.ini` excludes `task_list/`; ignore rules continue to cover task-board scratch and controlled-scene payloads for later physical work.

The pre-start lint and fresh plan review passed on 2026-10-06. Do not run model trials, phone capture or physical-device checks under this task. Keep Task51 open until its contract checks and software-run evidence are complete; field acceptance limits remain a separate pending decision.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not committed; Task51 remains in progress |
| Files changed | `src/walkthrough/cli.py`, `config.py`, `pipeline.py`, `records.py`, `provenance.py`, `validation.py`, `visualization.py`, `steps/artifacts.py`, `steps/capture.py`, `steps/depth.py`, `steps/tracking.py`, `steps/surface.py`, `steps/mapping.py`, `steps/objects.py`; `src/README.md`, `src/walkthrough/README.md`, `data/README.md`, `task_list/README.md`, root `README.md`, capture experiment README; this task file |
| Test status | The test suite was not run and the contract test was not updated. The two-frame TUM clip completed all six layers in a labelled software-control run at `outputs/task51_visual_e2e_runs/20261007T073231.235212Z_3a03158a79104e3b9481e77c77d41b38`. Its visual manifest lists 6 stage statuses and 17 artifacts; every listed file exists and names a source and producer. The mask labels report 100% valid coverage because the fixture marks all 307,200 pixels valid; the RGB coverage overlay makes this visible. The object overlay labels its one full-frame box as synthetic software-control output, not a detector result. All local links resolve. The two full coloured PLY exports retain all 307,200 points per frame and include the method and source frame in their headers. Fixtures do not measure model accuracy. |
| Before measurement | 0 prerecorded-dataset adapters in `src/walkthrough`; no visual index exported by the walkthrough |
| After measurement | 1 TUM RGB input adapter completed a six-layer software-control run on 2 recorded frames; 6 stage views and 17 method-labelled visual artifacts were exported; no real depth, tracking, mapping or detection method was evaluated; field acceptance limits remain pending |
| Delta | +1 local prerecorded input path; six-layer orchestration and clearer visual exports exercised with software controls |
| Decision-gate outcome | Owner-approved glue scope implemented and exercised with deterministic software providers; no model, capture or field trial started; field/deployment acceptance remains open. Visual outputs do not change stage data contracts, so downstream dependency edges are unchanged. |

still open because the contract test remains outstanding, this run used software controls rather than real depth and mapping methods, and field acceptance limits are pending by owner direction.
