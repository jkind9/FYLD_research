---
id: "59"
title: Make each walkthrough layer swappable and simplify the runner
status: closed
priority: HIGH
type: refactor
approval_status: plan requested by owner 2026-10-07; six decisions and contract scope answered 2026-10-07 (see Clarifications)
blocked_by: []
blocks: ["54", "55", "56"]
verification_test: src/walkthrough/tests/test_pipeline.py
plan_reviewed: 2026-10-07 PASS
files:
  - src/walkthrough/**
  - experiments/shared/runs.py
  - experiments/shared/geometry.py
  - experiments/shared/tests/test_runs.py
  - experiments/shared/tests/test_geometry.py
  - experiments/shared/requirements.txt
  - experiments/shared/README.md
  - src/README.md
  - README.md
  - task_list/README.md
  - task_list/closed/59_make_walkthrough_layers_swappable.md
docs:
  - src/walkthrough/README.md
  - src/README.md
  - task_list/README.md
baseline_metric:
  source: "this file, section Why, measured 2026-10-07 08:16 on the Task 51 working tree"
  field: "layers with a swappable method slot and written contract; pipeline.py lines; frame layers with non-null fps"
  baseline_value: "0 of 6 layers; 241 lines; 0 of 4 layers"
  target: "6 of 6 layers; <=120 lines; 4 of 4 layers"
created: 2026-10-07
last_updated: 2026-10-07
superseded_by: null
---

# Task 59: Make each walkthrough layer swappable and simplify the runner

## In plain English

The walkthrough runner passes a recording through six layers: camera capture, depth, camera position, surface, site measurements and object counting. Each layer has one built-in method today, so we cannot swap one depth model or object detector for another, or compare combinations for accuracy, speed and fitness for a phone.

This task gives every layer one method slot with a written contract. The contract says what a method receives and what it must return. Recorded reference data can be fed into a layer, so the layer after it can be tested without inherited errors. The main runner shrinks from 241 to about 115 lines and reads like the six-layer diagram. Every layer records which method ran, how long loading and each frame took, what it saved, and why anything did not run.

---

## What

### The owner's goals, in their words

- **Simplicity**: "a simple easy to read flow that mimics the layers in the project readme".
- **Modularity**: "each layer having swappable methods and modules i.e. marigold for depth anything, video input vs streaming, yolo vs frcnn. Eventually we will test a range of options for each layer and evaluate the accuracy latency and edge capacity of pipelines (sort of like a grid style method)".
- **Maintainability**: "no nested wrappers, easy to read code, no unnecessary lines or lazy imports or behaviour we just simply don't need to account for".

Importing from `experiments/` is fine for now. Later, `steps/*.py` become folders and the components they use move into `src/`.

### Rules every change follows

1. **The pipeline reads like the README diagram.** Six numbered blocks in order. Each block has the same beats: skip or run, check the output, save the pictures.
2. **One method slot per layer.** A method choice is a small frozen record holding the method's name, its own settings and a `load()` that builds the model. Swapping a method means passing a different record.
3. **Run settings are one choice per layer**, so a grid search is a loop over combinations.
4. **Fixtures and reference inputs are ordinary method choices with a `control` label.** `"software"` marks a test fixture. `"reference"` marks recorded reference data fed in as a layer's output. A run with any control is never a measurement.
5. **No checks for states the pipeline cannot produce.**
6. **Imports go at the top of the file, with no exceptions.** Experiment folders start with digits, so they need `importlib.import_module`, at module level. Imported-but-unused is fine. Models still load inside `load()`, because loading a model is work to be timed.
7. **Catch only expected failures**: `Unavailable`, `ValueError`, `OSError`. Anything else stops the run.
8. **Every layer leaves the same trail**: timed loading, timed prediction with a frame count, saved predictions, a status row naming the method, and pictures.
9. **Every layer has a two-part contract.** The method contract is what a method receives and returns. The saved-output contract is what the layer writes and later layers read. Methods never see saved files; later layers never see a method.
10. **Every gap says why.** An unavailable, failed or skipped layer, a held-back input, and an unscored component each record a reason that leads back to the cause.

### Target shape

```text
src/walkthrough/
  cli.py            command line: turns flags into method choices
  config.py         PipelineSpec: the input source plus one method choice per layer
  pipeline.py       six numbered blocks, then scoring and publication
  records.py        StepResult rows and the whole-run Result
  validation.py     scoring after predictions are hashed
  visualization.py  per-layer pictures (Task 51, unchanged)
  steps/
    contracts.py    every layer's method contract and saved-output shapes; shared readers
    capture.py      CaptureSource, PhoneExport, TumSequence, calibration_for, saved_colour_frames
    depth.py        DepthMethod, RecordedSensorDepth (reference control); real method in Task54
    tracking.py     TrackingMethod, CpuOdometry, ReferencePoses (reference control)
    surface.py      SurfaceMethod, MetricPoints
    mapping.py      MappingMethod; real method in Task55
    objects.py      DetectorMethod, Yolo26x, ClassicalSegmentation, ClassicalAppearance, ObjectSettings
  tests/providers.py  fixture methods with control="software"
```

Each layer file reads top to bottom:

1. Module-level experiment imports.
2. The method `Protocol`.
3. The built-in method choices.
4. `run()`.
5. `validate()`.

A grid run is then:

```python
for depth_method, detector in itertools.product(DEPTH_CHOICES, DETECTOR_CHOICES):
    result = run(replace(base, depth=depth_method, objects=replace(base.objects, detector=detector)), scores=scores)
```

---

## Why

Measured at 08:16 on 2026-10-07 on the Task 51 working tree:

| Measure | Value |
|---|---|
| Runner code (excluding tests and `visualization.py`) | 1,688 lines in 12 files |
| `pipeline.py` | 241 lines; about 150 are six copies of one skip-or-run block |
| `importlib.import_module` calls inside functions | 17 |
| `software_control` mentions outside tests | 26 in 8 files |
| Layers with a real method slot | 0 of 6 |
| Timing stages with a frame count | 0 of 6, so every `fps` in `timing.json` is `null` |
| Model loading timed apart from inference | no (YOLO loads inside `prediction_objects`) |
| Walkthrough tests | 21 of 51 fail; the tests lag behind Task 51's in-progress edits |

**Methods are fixed inside the layers.**

- Tracking always builds `CPUOdometry()` (`steps/tracking.py:80`).
- Objects always builds `YoloDetector(checkpoint, "cpu")` (`steps/objects.py:99-103`).
- Depth and mapping accept only a test fixture, through a `test_providers` hook that real methods cannot use.

**The current per-frame shapes exclude most planned methods.** The project README's own candidates need the whole sequence:

- **Depth:** Depth Anything 3, MapAnything.
- **Tracking:** ORB-SLAM3, MASt3R-SLAM, VGGT-SLAM, COLMAP.

**Logic sits in the wrong layer.**

- Phone calibration is converted in depth (`steps/depth.py:21-50`), but it is capture knowledge.
- Objects borrows `tracking.frames` and `surface.pose` (`steps/objects.py:13`).
- Scoring rebuilds poses by hand (`validation.py:113-122`).

**A layer cannot be tested on its own.** Reference data never reaches a method, so tracking methods are always compared on top of whatever depth error exists. The README diagram already lists "Reference camera path: control" and "Recorded sensor depth: stand-in".

**Checks that can never fire:**

| What | Where |
|---|---|
| `step_status` argument with a `!= "pending"` early return | all six layers |
| `if capture is None: raise` | five layers |
| a length check right before `zip(..., strict=True)` | tracking, surface, objects |
| a frame-ID check inside the objects loop | `steps/objects.py:120` |
| an "incomplete step cannot return predictions" branch | every `validate_step` |
| `validate` plus `validate_step` | `steps/capture.py:196-212` |
| two `except` blocks with the same body | `steps/capture.py:185-188` |
| the phone report/bundle check, done three times | `config.py:73-78`, `cli.py:51-54`, `steps/capture.py:175-178` |

**Code that does nothing needed:**

- `score_compatible`, which has no callers (`validation.py:60-98`).
- `_readonly`, which covers the same risk as the prediction-hash check (`validation.py:52-57`).
- A temporary reference file written into the repo root (`cli.py:16-27`); an empty `walkthrough-references-13o_jh04/` folder is left there today.
- The raise-then-catch of `IncompleteRun` (`pipeline.py:231-238`).
- A `backproject()` result that is thrown away, so the depth timing includes building points (`steps/depth.py:78`).

**The `except` lists are too broad.** They include `RuntimeError`, `ImportError` and `KeyError`, which turns bugs into "failed" status rows.

### Background: camera calibration on phones

Calibration is a few numbers that describe how a camera turns the 3D world into an image:

- **Focal length in pixels (`fx`, `fy`):** how zoomed-in the lens is.
- **Image centre (`cx`, `cy`):** the pixel the lens points straight through.
- **Image size** those numbers belong to.
- **Lens distortion.**

The TUM camera is 525, 525, 319.5, 239.5 at 640×480 (`experiments/03_camera_pose_estimation/src/dataset.py:13`).

Every 3D step turns a pixel and its depth into a point with `X = (u − cx)·depth/fx`, `Y = (v − cy)·depth/fy`. A focal length 10% off makes the whole site 10% too wide or narrow, even with perfect depth.

**On a phone it can be recorded, but only by our own capture app.** No make or model list is needed: the app asks Android at runtime, per camera. Availability varies even on one phone. The Redmi rear camera reports 2872.36 px and centre (2000, 1500); its front camera reports nothing (`experiments/01_camera_capture_delivery/README.md:221-222`).

When a camera reports nothing, there are fallbacks:

- focal length in mm and sensor size give an approximate `fx`
- ARCore supplies per-frame calibration on supported phones
- calibration can be estimated from the frames

**Zoom and lens switching** are reported per frame:

- the active physical lens (Android 10+)
- the crop region, from which the calibration can be adjusted exactly: `fx' = fx·scale`, `cx' = (cx − crop_x)·scale`

Electronic stabilisation warps frames by an amount the phone does not report. A lens switch mid-walkthrough breaks tracking. So for walkthroughs the app should lock one lens, the zoom and focus, turn stabilisation off, and still record the per-frame metadata.

**What the app records today:**

- calibration and distortion per camera (`CameraReport.java:106-109`)
- crop region per frame (`CameraCapture.java:187`)
- distortion-correction mode per frame

**Not yet recorded:** per-frame calibration, the active lens, zoom ratio, focal length per frame, stabilisation mode.

A plain mp4 carries none of this. A stream needs a metadata record per frame, and an mp4 needs a sidecar file.

---

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Timing ledger with per-scope frame counts and fps already exists | `TimingLedger.measure` / `.summary` | `Run.measure`, every layer | experiments/shared/timing.py:63, 90-101 |
| Run context exposes timing scopes | `Run.measure` | every layer | experiments/shared/runs.py:173 |
| Run publishes itself on a clean exit, forcing the `IncompleteRun` trick | `Run.__exit__` | `pipeline.run` | experiments/shared/runs.py:262-278 |
| Failure status writing can be reused for incomplete runs | `Run._failed` | `Run.__exit__` | experiments/shared/runs.py:227 |
| Depth grid and mask checks exist inside `backproject` | `geometry.backproject` | depth layer, localisation | experiments/shared/geometry.py:23-29 |
| Depth decoding, timestamp matching and pose building exist | `depth_metres`, `associate_times`, `pose_matrix` | reference controls | experiments/shared/geometry.py:10, 108, 90 |
| Pose serialisation is owned by the shared contract | `Pose.to_dict` | `Record.to_dict`, every saved pose | experiments/shared/contracts.py:59 |
| Tracking is already whole-sequence: frames in, records out | `tracking.track` | tracking layer | experiments/03_camera_pose_estimation/src/tracking.py:39-44 |
| Tracking times each frame pair itself (`odometry_pairs`) | `track()` | `timing.json` | experiments/03_camera_pose_estimation/src/tracking.py:89 |
| CPU odometry and the RGB-D frame record exist | `backend.CPUOdometry`, `dataset.RGBDFrame` | tracking, localisation | experiments/03_camera_pose_estimation/src/backend.py:41; dataset.py:17 |
| TUM depth table reader, 5000 units/m and 4 m limit exist | `dataset.read_table`, `load_frame` | `RecordedSensorDepth` | experiments/03_camera_pose_estimation/src/dataset.py:52, 79, 123-124 |
| TUM ground-truth reader exists | `evaluation.read_references` | `ReferencePoses`, CLI scoring | experiments/03_camera_pose_estimation/src/evaluation.py:13 |
| Per-frame metric points exist | `metric_surface.reconstruct_metric` | surface layer | experiments/04_surface_reconstruction/src/metric_surface.py |
| The YOLO detector loads its model in its constructor | `pilot.detector.YoloDetector` | objects layer | experiments/06_object_recognition/pilot/detector.py:27-51 |
| Every saved proposal carries `association` and `object_id` | `association.associate_frame` | objects validator, visuals | experiments/06_object_recognition/pilot/association.py:140-173 |
| Per-layer picture export exists, one function per layer | `src/walkthrough/visualization.py` (Task 51) | `pipeline.run` | src/walkthrough/visualization.py:196, 215, 300, 365, 509, 528 |
| Module-level experiment imports load no model library | the experiment modules imported here | `import pipeline`, `import cli` | checked 2026-10-07: no torch, ultralytics or open3d; segmentation and appearance add cv2 only (02_segmentation/masks.py:6, 03_appearance/adapter.py:7) |
| No existing method registry or run spec | none | n/a | searched src/ and experiments/shared for `Protocol`, `load(`, `registry`, `METHODS`: nothing comparable |

### Working alongside Task 51

Task 51 is active and owns `src/walkthrough/**`. It is adding `visualization.py`, which the pipeline calls once per layer with `(run_path, status, outputs...)` and which writes `output/visualizations/`. This task:

- **Does not change `visualization.py`.** It keeps the six calls and their arguments, wrapping each in a `visual_<layer>` timing scope.
- **Keeps the saved keys the visual code reads:** `methods.*`, `frames[].image`, `frames[].arrays`, `shards[].points`, `frames[].proposals`.

Two suggestions for that session, not part of this task:

- Make `experiments.shared.exporting._cloud_preview` public, and import it at the top of the file.
- Its `status == "complete"` checks become redundant once each layer returns `None` whenever it is incomplete.

### Layer contracts

Content checks run where the data is in memory, at save time. The validator after each layer checks the saved manifest against the layers it came from.

| Layer | Method receives | Method returns | Layer saves | Units | Checked at save | Checked after the layer |
|---|---|---|---|---|---|---|
| 1 Capture | (source reads itself) | one `ImageArtifact` row per frame | `capture.json`, original bytes | pixels; calibration per frame or `None` | ≥1 frame, image format and size | unique IDs, source hash on every frame, `withheld_from_methods` present |
| 2 Depth | `Iterator[ColourFrame]` (all frames) | `Iterator[DepthPrediction]`, one per frame, same order | `depth.json`, one `.npz` per frame | camera-axis metres on the image grid | `check_depth_grid`; prediction order matches frame order; no extra predictions | IDs match capture |
| 3 Tracking | `Iterator[RGBDFrame]` (all frames) | `list[PoseRecord]`, one per frame, same order | `tracking.json` | 4×4 camera-to-world, metres, world/segment origin | no frame without a pose (reason names the first lost frame) | IDs match capture; every pose rebuilds as a valid transform |
| 4 Surface | one frame's depth, mask, calibration, pose | N×3 world points | `surface.json`, one `.npy` per frame | world metres, labelled origin | finite N×3 | IDs match depth; units metres |
| 5 Mapping | surface manifest and run folder | named measurements | `mapping.json` | each states its units | non-empty | non-empty |
| 6 Objects | one image path per frame | detections on the original grid, metadata with `image_shape_hw` | `objects.json`, optional masks | world metres per detection, IDs per origin | detector grid matches calibration | IDs match capture; every proposal has `xyxy`, `label`, `object_id`, `association`; no whole-site count |

**Depth and tracking take all frames,** so single-frame models, multi-view depth, SLAM and structure-from-motion all fit the same contract. A single-frame method meets it with a loop. Surface and objects stay single-frame, because every method planned for them works one frame at a time.

**Per-frame timing under an all-frames contract.** The layer times each `next()` as `<layer>_frame`: the time until that frame's result is ready. A method that reads every frame first shows all its time on frame one. That is what a phone user would wait for.

### Method choices and controls

```python
@dataclass(frozen=True)
class CpuOdometry:
    """Experiment 03's frozen CPU RGB-D odometry. Needs valid depth below 4 m."""

    name: str = field(default="cpu_odometry", init=False)    # short name for result.json and grids
    control: str | None = field(default=None, init=False)    # None, "software" or "reference"

    def load(self) -> TrackingEstimator:                     # runs inside the load_tracking timing scope
        return functools.partial(pose_tracking.track, backend=pose_backends.CPUOdometry())
```

| `control` | Meaning | Examples |
|---|---|---|
| `None` | a real method | `CpuOdometry`, `MetricPoints`, `Yolo26x`, later `Marigold` |
| `"software"` | a test fixture with fixed outputs | `Fixture("flat_depth", ...)` in `tests/providers.py` |
| `"reference"` | recorded reference data fed in as a layer's output | `RecordedSensorDepth(root)`, `ReferencePoses(groundtruth)` |

`result.json` lists every control under `controls`, and `is_measurement` is false when any is present. Reference controls are the only way reference data reaches a method; every other reference stays in scoring. The objects layer accepts supplied poses only when tracking's output is labelled `"reference"`.

### Measurements and tracing

| Label | Scope | Frames |
|---|---|---|
| `load_<layer>` | `method.load()`: building or loading the model | none |
| `prediction_<layer>` | all frames for the layer, including saving | frames processed |
| `depth_frame`, `surface_frame`, `objects_frame` | one frame, inside the prediction scope | 1 |
| `odometry_pairs` | one frame pair, recorded by experiment 03's `track()` | 1 |
| `diagnostic_segmentation`, `diagnostic_appearance` | one optional object diagnostic | 1 |
| `visual_<layer>` | the `visualization.<layer>` call | none |
| `scoring` | reference loading and scoring | none |

Nested scopes overlap; never add them. Each run leaves:

- `output/predictions/<layer>.json` plus arrays
- `output/result.json`: one row per layer with `status`, `reason`, `method`, `frames`, `artifact`, plus `controls` and `is_measurement`
- `output/scores.json`
- `output/visualizations/`
- `metadata/timing.json`, `metadata/prediction_hashes.json`, and the settings snapshot with every method's name and settings

Peak memory per layer is not measured; that is Task 57.

### Every gap says why

| Gap | Where the reason is |
|---|---|
| no method, or unusable input (`unavailable`) | the layer's row, e.g. "Task54 real metric depth implementation is unavailable" |
| expected error (`failed`) | the layer's row, with the error type and message |
| could not start (`skipped`) | the row names each blocking layer and its status: "Waiting on earlier layers: depth is unavailable, tracking is skipped" |
| source data methods never receive | `withheld_from_methods` in `capture.json`, e.g. TUM `groundtruth.txt` "is a scoring reference; tracking must estimate poses" |
| unscored component | its entry in `scores.json` |
| whole run incomplete | `metadata/status.json`: `failed`, `IncompleteRun` |

### Code: `steps/contracts.py` (owns the contracts)

Keep `steps/artifacts.py` as type re-exports for the unchanged visual module (`src/walkthrough/visualization.py:17`). Keep `ObjectsOutput.synthetic_detector`, which the visual overlay reads (`visualization.py:620`). No runtime provider aliases remain.

`MetricPoints` composes the existing `backproject` and `transform_points` helpers directly (`experiments/shared/geometry.py:20,78`). The surface layer permits supplied poses only when tracking carries `control="reference"`. The frozen experiment's `reconstruct_metric` rejects supplied poses (`experiments/04_surface_reconstruction/src/metric_surface.py:15`), so it cannot implement this broader contract unchanged. Preserve the source label in the saved tracking output and retain every origin.

Declare the installed OpenCV CPU dependency in shared requirements and document it. Module-level segmentation and appearance imports require it even when diagnostics are disabled (`experiments/06_object_recognition/experiments/02_segmentation/masks.py:6`).

```python
"""Every layer's contract: what its method receives and returns, and what the layer saves.

Methods see only the method contract. Later layers see only the saved outputs.
src/walkthrough/README.md, "Layer contracts", lists both with units and checks.
"""

import importlib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, TypedDict

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from experiments.shared.contracts import Calibration, Pose
from experiments.shared.runs import Run

from ..records import Unavailable

# Experiment folders start with digits, so `import` syntax cannot name them.
pose_dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")
pose_tracking = importlib.import_module("experiments.03_camera_pose_estimation.src.tracking")
RGBDFrame = pose_dataset.RGBDFrame  # one frame's RGB, metric depth, valid mask and calibration
PoseRecord = pose_tracking.Record  # one frame's pose (or None) with a status and reason


# ---- Method contracts ----


@dataclass(frozen=True)
class ColourFrame:
    """What a depth method receives per frame."""

    frame_id: str
    timestamp_s: float | None
    calibration: Calibration
    colour: NDArray[np.uint8]


@dataclass(frozen=True)
class DepthPrediction:
    """What a depth method returns per frame: camera-axis metres and a trusted-pixel mask."""

    frame_id: str
    depth: NDArray[np.floating]
    valid: NDArray[np.bool_]


class DepthEstimator(Protocol):
    def __call__(self, frames: Iterator[ColourFrame], *, run: Run) -> Iterator[DepthPrediction]:
        """All frames in, one prediction per frame out, same order. run is for optional inner timing."""


class TrackingEstimator(Protocol):
    def __call__(self, frames: Iterator[RGBDFrame], *, run: Run) -> list[PoseRecord]:
        """All RGB-D frames in, one pose record per frame out, same order. Unplaced frames get pose None and a reason."""


# ---- Saved outputs ----


class ImageArtifact(TypedDict):
    """One saved image and the source facts available for it. Absent facts are None."""

    frame_id: str
    source_id: str
    source_frame_id: str
    source_frame_index: int
    image: str
    image_width: int
    image_height: int
    source_sha256: str
    timestamp_s: float | None
    timestamp_source: str | None
    calibration: dict[str, Any] | None
    calibration_source: str | None
    phone_grid: dict[str, Any] | None


class CaptureOutput(TypedDict):
    methods: dict[str, str]
    frames: list[ImageArtifact]
    withheld_from_methods: dict[str, str]  # each held-back input, with the reason


class DepthArtifact(TypedDict):
    frame_id: str
    arrays: str
    calibration: dict[str, Any]
    source: str
    depth_definition: str


class DepthOutput(TypedDict):
    methods: dict[str, str]
    frames: list[DepthArtifact]
    control: str | None


class TrackingOutput(TypedDict):
    methods: dict[str, str]
    records: list[dict[str, Any]]  # experiment 03's Record.to_dict()
    control: str | None


class SurfaceShard(TypedDict):
    frame_id: str
    points: str
    point_count: int
    world_id: str
    segment_id: str
    units: str


class SurfaceOutput(TypedDict):
    methods: dict[str, str]
    shards: list[SurfaceShard]
    coverage: str


class MappingOutput(TypedDict):
    methods: dict[str, str]
    control: str | None
    measurements: dict[str, Any]


class ObjectsOutput(TypedDict):
    methods: dict[str, str]
    frames: list[dict[str, Any]]
    origins: list[dict[str, Any]]
    whole_site_distinct_count: None
    claim: str
    optional_evidence_changes_counting: bool


# ---- Shared readers ----


def method_label(choice: Any) -> str:
    """The chosen method's short name and class, saved with predictions and shown on visuals."""
    return f"{choice.name} ({type(choice).__module__}.{type(choice).__qualname__})"


def read_pose(row: dict[str, Any]) -> Pose:
    """Rebuild a saved pose, refusing anything but a valid metric camera-to-world transform."""
    if row["units"] != "metres" or row["direction"] != "camera_to_world":
        raise ValueError("Expected metric camera-to-world pose")
    return Pose(row["T_world_camera"], row["world_id"], row["segment_id"], row["source"])


def load_rgbd_frames(run_path: Path, capture: CaptureOutput, depth: DepthOutput) -> Iterator[RGBDFrame]:
    """Yield RGB-D frames one at a time, for one camera and one declared clock."""
    rows = capture["frames"]
    if any(row["timestamp_s"] is None or row["timestamp_source"] is None for row in rows):
        raise Unavailable("Tracking needs a source timestamp and its clock label")
    if len({(row["source_id"], row["timestamp_source"]) for row in rows}) != 1:
        raise ValueError("Tracking requires one camera and one declared capture clock")
    for row, measured in zip(rows, depth["frames"], strict=True):
        with Image.open(run_path / row["image"]) as image:
            colour = np.asarray(image.convert("RGB"))
        with np.load(run_path / measured["arrays"], allow_pickle=False) as arrays:
            yield RGBDFrame(row["frame_id"], row["timestamp_s"], row["timestamp_s"],
                            Calibration(**measured["calibration"]), colour, arrays["depth"], arrays["valid"])
```

### Code: `pipeline.py`

Before: `src/walkthrough/pipeline.py`, 241 lines. After, whole file:

```python
"""Run the six walkthrough layers in README order, then score and publish.

Each block: skip or run, validate the output, save the pictures.
Timing labels: load_<layer>, prediction_<layer>, visual_<layer>, scoring.
"""

from experiments.shared.runs import Run, artifact_inventory, write_json

from . import validation, visualization
from .config import STEP_NAMES, PipelineSpec
from .records import Result, StepResult
from .steps import capture, depth, mapping, objects, surface, tracking

# The layers each one reads. README: a layer may use the output of any layer above it.
READS = {
    "capture": (),
    "depth": ("capture",),
    "tracking": ("capture", "depth"),
    "surface": ("depth", "tracking"),
    "mapping": ("surface",),
    "objects": ("capture", "depth", "tracking"),
}


def run(spec: PipelineSpec, *, scores: tuple[validation.ScoreRequest, ...] = ()) -> Result:
    """Run one walkthrough. The run folder keeps every output, complete or not."""
    status: dict[str, StepResult] = {}
    captured = measured = tracked = reconstructed = mapped = recognised = None
    run_context = Run(spec.run_root, spec.repo, spec.to_dict())
    with run_context:
        # 1. Camera capture
        if reason := skip_reason(spec, status, "capture"):
            status["capture"] = StepResult("capture", "skipped", reason)
        else:
            status["capture"], captured = capture.run(run_context, spec.source)
        if captured is not None:
            capture.validate(captured)
        with run_context.measure("visual_capture"):
            visualization.capture(run_context.path, status["capture"], captured)

        # 2. Depth estimation
        if reason := skip_reason(spec, status, "depth"):
            status["depth"] = StepResult("depth", "skipped", reason)
        else:
            status["depth"], measured = depth.run(run_context, captured, spec.depth)
        if measured is not None:
            depth.validate(captured, measured)
        with run_context.measure("visual_depth"):
            visualization.depth(run_context.path, status["depth"], captured, measured)

        # 3. Camera position estimation
        if reason := skip_reason(spec, status, "tracking"):
            status["tracking"] = StepResult("tracking", "skipped", reason)
        else:
            status["tracking"], tracked = tracking.run(run_context, captured, measured, spec.tracking)
        if tracked is not None:
            tracking.validate(captured, tracked)
        with run_context.measure("visual_tracking"):
            visualization.tracking(run_context.path, status["tracking"], tracked)

        # 4. Surface reconstruction
        if reason := skip_reason(spec, status, "surface"):
            status["surface"] = StepResult("surface", "skipped", reason)
        else:
            status["surface"], reconstructed = surface.run(run_context, measured, tracked, spec.surface)
        if reconstructed is not None:
            surface.validate(measured, reconstructed)
        with run_context.measure("visual_surface"):
            visualization.surface(run_context.path, status["surface"], captured, measured, reconstructed)

        # 5. Mapping, dimensions and area
        if reason := skip_reason(spec, status, "mapping"):
            status["mapping"] = StepResult("mapping", "skipped", reason)
        else:
            status["mapping"], mapped = mapping.run(run_context, reconstructed, spec.mapping)
        if mapped is not None:
            mapping.validate(mapped)
        with run_context.measure("visual_mapping"):
            visualization.mapping(run_context.path, status["mapping"], mapped)

        # 6. Object recognition and counting
        if reason := skip_reason(spec, status, "objects"):
            status["objects"] = StepResult("objects", "skipped", reason)
        else:
            status["objects"], recognised = objects.run(run_context, captured, measured, tracked, spec.objects)
        if recognised is not None:
            objects.validate(captured, recognised)
        with run_context.measure("visual_objects"):
            visualization.objects(run_context.path, status["objects"], captured, recognised)

        result = Result(run_context.path, tuple(status[name] for name in STEP_NAMES), spec.controls)
        write_json(run_context.path / "output/result.json", result.to_dict())

        # Hash predictions before any reference is opened, and check them again after scoring.
        predictions = run_context.path / "output/predictions"
        prediction_hashes = artifact_inventory(predictions)
        write_json(run_context.path / "metadata/prediction_hashes.json", {"files": prediction_hashes})
        with run_context.measure("scoring"):
            score_results = validation.score(run_context.path, result.steps, scores)
        if artifact_inventory(predictions) != prediction_hashes:
            raise ValueError("Prediction artifacts changed during scoring")
        write_json(run_context.path / "output/scores.json", score_results)

        if not result.complete:
            run_context.stop_incomplete("Six-step predictions are incomplete; inspect output/result.json")
    return result


def skip_reason(spec: PipelineSpec, status: dict[str, StepResult], name: str) -> str | None:
    """Say why a layer cannot run, naming each blocking layer and its status; None when it can.

    Without --partial a layer waits for every layer above it. With --partial it
    waits only for the layers it reads (READS).
    """
    if name not in spec.requested:
        return "Not requested"
    needs = READS[name] if spec.partial else STEP_NAMES[: STEP_NAMES.index(name)]
    blocking = [f"{need} is {status[need].status}" for need in needs if status[need].status != "complete"]
    return f"Waiting on earlier layers: {', '.join(blocking)}" if blocking else None
```

Without `--partial` this gives the same run/skip decisions as today (each layer already depended on the one above). With `--partial`, `READS` matches today's rules. Only the reason wording changes.

### Code: `steps/depth.py`, the template every layer follows

```python
"""Layer 2, depth estimation: metric depth for every captured frame. Task54 owns the real method."""

import importlib
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image

from experiments.shared.geometry import associate_times, check_depth_grid, depth_metres
from experiments.shared.runs import Run, write_json

from ..records import StepResult, Unavailable, failed_step
from .capture import calibration_for, saved_colour_frames
from .contracts import CaptureOutput, ColourFrame, DepthArtifact, DepthEstimator, DepthOutput, DepthPrediction, ImageArtifact, method_label

# Experiment folders start with digits, so `import` syntax cannot name them.
tum_dataset = importlib.import_module("experiments.03_camera_pose_estimation.src.dataset")

ARTIFACT = "output/predictions/depth.json"


class DepthMethod(Protocol):
    """A depth method choice, e.g. Marigold or Depth Anything. load() builds the model."""

    name: str
    control: str | None

    def load(self) -> DepthEstimator: ...


@dataclass(frozen=True)
class RecordedSensorDepth:
    """Reference control: TUM sensor depth per frame, so later layers can be compared without depth error."""

    root: Path
    tolerance_s: float = 0.02  # inherited from experiments/03_camera_pose_estimation/src/dataset.py:79
    units_per_metre: float = 5000.0  # inherited from dataset.py:123
    max_depth_m: float = 4.0  # inherited from dataset.py:124 (tracking kernel's frozen range)
    name: str = field(default="recorded_sensor_depth", init=False)
    control: str | None = field(default="reference", init=False)

    def load(self) -> DepthEstimator:
        return self.estimate

    def estimate(self, frames: Iterator[ColourFrame], *, run: Run) -> Iterator[DepthPrediction]:
        depth_rows = tum_dataset.read_table(self.root / "depth.txt")
        depth_times = [timestamp for timestamp, _ in depth_rows]
        for frame in frames:
            match = associate_times([frame.timestamp_s], depth_times, self.tolerance_s)
            if not match:
                raise Unavailable(f"No recorded depth within {self.tolerance_s} s of frame {frame.frame_id}")
            with Image.open(self.root / depth_rows[match[0][1]][1]) as image:
                depth, valid = depth_metres(np.asarray(image), self.units_per_metre)
            yield DepthPrediction(frame.frame_id, depth, valid & (depth < self.max_depth_m))


def run(run_context: Run, capture: CaptureOutput, method: DepthMethod | None) -> tuple[StepResult, DepthOutput | None]:
    """Hand the method every captured frame, then check and save one depth file per frame."""
    if method is None:
        return StepResult("depth", "unavailable", "Task54 real metric depth implementation is unavailable"), None
    frame_count = len(capture["frames"])
    try:
        with run_context.measure("load_depth"):
            estimate = method.load()
        with run_context.measure("prediction_depth", frames=frame_count):
            predictions = estimate(saved_colour_frames(run_context.path, capture), run=run_context)
            rows = [_save_prediction(run_context, predictions, index, frame, method)
                    for index, frame in enumerate(capture["frames"])]
            if next(predictions, None) is not None:
                raise ValueError("Depth method returned more predictions than frames")
            output: DepthOutput = {"methods": {"depth": method_label(method)}, "frames": rows, "control": method.control}
            write_json(run_context.path / ARTIFACT, output)
    except (Unavailable, ValueError, OSError) as error:
        return failed_step("depth", error, method.name), None
    return StepResult("depth", "complete", "Method outputs saved", method.name, frame_count, ARTIFACT), output


def validate(capture: CaptureOutput, output: DepthOutput) -> None:
    """Depth exists for exactly the captured frames, in the same order."""
    if [row["frame_id"] for row in capture["frames"]] != [row["frame_id"] for row in output["frames"]]:
        raise ValueError("Depth output frame identities must match capture")


def _save_prediction(run_context: Run, predictions: Iterator[DepthPrediction], index: int,
                     frame: ImageArtifact, method: DepthMethod) -> DepthArtifact:
    """Take the next prediction, check it belongs to this frame and sits on its grid, then save it."""
    with run_context.measure("depth_frame", frames=1):
        prediction = next(predictions, None)
    if prediction is None or prediction.frame_id != frame["frame_id"]:
        raise ValueError("Depth method must return one prediction per frame, in frame order")
    camera = calibration_for(frame)
    check_depth_grid(prediction.depth, prediction.valid, camera)
    relative = f"output/predictions/depth/{index:06d}.npz"
    path = run_context.path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, depth=prediction.depth, valid=prediction.valid)
    return {"frame_id": frame["frame_id"], "arrays": relative, "calibration": asdict(camera),
            "source": method_label(method), "depth_definition": "camera_axis_z_metres"}
```

A real method (Task 54) is one more frozen dataclass. Its `load()` returns a callable that yields one `DepthPrediction` per frame. Stereo needs a second image field on `ColourFrame` when Task 54 picks it.

### Changes to the other files

Every layer follows the depth template: no `step_status` argument, no upstream-`None` checks, one `try` catching `(Unavailable, ValueError, OSError)`, `load_<layer>` then `prediction_<layer>` with a frame count, `method_label(method)` in `methods`, and a `StepResult` carrying `method` and `frames`.

**`records.py`**
- Delete `IncompleteRun`; it moves to `experiments/shared/runs.py`.
- `StepResult` gains `method: str | None` and `frames: int | None`.
- `failed_step(name, error, method)` maps `Unavailable` to "unavailable" and anything else to "failed: Type: message".
- `Result(path, steps, controls: dict[str, str])` gains properties `complete` (all rows complete) and `is_measurement` (complete and no controls). `to_dict` writes `controls` and `is_measurement` in place of `software_control`.

**`config.py`**
- Replace `Configuration`, `CaptureConfiguration` and `ObjectConfiguration` with one frozen `PipelineSpec`. Its fields are:
  - `run_root`, `repo`, `source`
  - `depth=None`, `tracking=CpuOdometry()`, `surface=MetricPoints()`, `mapping=None`
  - `objects=ObjectSettings()`
  - `requested=STEP_NAMES`, `partial=False`
- The only check left: requested steps must be unique known names.
- `controls` property: `{layer: choice.control}` for each chosen method whose `control` is set.
- `to_dict()` is `json.loads(json.dumps(asdict(self), default=str))`.

**`steps/capture.py`**
- `CaptureSource` protocol: `name`, `control`, `read(run_context) -> list[ImageArtifact]` and `withheld_inputs() -> dict[str, str]`.
- `PhoneExport(report, bundle)` and `TumSequence(root)` take over today's `_read_phone_input` / `_read_tum_input` bodies unchanged.
  - TUM withheld reasons: `depth/` "is a scoring reference; depth methods must estimate it"; `groundtruth.txt` "is a scoring reference; tracking must estimate poses".
  - Phone withheld reasons: "The phone export reader supplies RGB only…" and "…supplies no camera poses".
- `run()` saves `{"methods": {"input": method_label(source)}, "frames": ..., "withheld_from_methods": source.withheld_inputs()}`.
- `calibration_for(frame)` moves here unchanged from `depth.calibration`.
- New `saved_colour_frames(run_path, capture)` yields one `ColourFrame` per saved image.
- One `validate(output)`.

**`steps/tracking.py`**
- `CpuOdometry.load()` returns `functools.partial(pose_tracking.track, backend=CPUOdometry())`. The layer calls `estimate(load_rgbd_frames(...), run=run_context)`, so `odometry_pairs` timing is kept.
- The origin namespace becomes experiment 03's own default: a fresh ID per call, instead of the run folder name.
- New `ReferencePoses(groundtruth, tolerance_s=0.02)` with `control="reference"`. It reads `evaluation.read_references`, matches each frame with `associate_times`, and returns `PoseRecord(..., "supplied", Pose(matrix, "tum_groundtruth", "0", "supplied"), "reference control")`. Unmatched frames get pose `None` and the reason "No ground-truth pose within 0.02 s".
- A lost frame fails the layer with "Tracking could not place N of M frames; first <id>: <reason>".
- The output adds `control`.
- `validate` also calls `read_pose` on every record.

**`steps/surface.py`**
- `MetricPoints.load()` returns a callable composing shared `backproject` and `transform_points`; supplied poses require a labelled tracking reference control.
- Each frame is timed as `surface_frame`.
- Points must be finite N×3 before saving, with one point per valid source pixel in `np.nonzero(valid)` order; otherwise the error names the frame. This preserves the unchanged visual export's RGB correspondence (`src/walkthrough/visualization.py:467-469`). Add a test rejecting a finite surface with too few points. Fused surfaces remain a follow-up.
- Shards are named `{index:06d}.npy`.

**`steps/mapping.py`**
- `method=None` gives "Task55 … unavailable".
- `load()` returns `measure_site(surface_output, run_path) -> dict`.
- The output carries `control`.

**`steps/objects.py`**
- Segmentation and appearance modules are imported at the top.
- `Yolo26x(checkpoint).load()` builds `YoloDetector(checkpoint, "cpu")` inside `load_objects`.
- `ClassicalSegmentation(method)` checks its method name; `ClassicalAppearance()` takes no settings.
- `ObjectSettings(detector, max_distance_m, ambiguity_margin_m, segmentation, appearance)` checks that the distances are finite metres.
- `run` splits into these helpers:
  - `_count`: frame loop, timed per frame as `objects_frame`
  - `_place`: localise one detection
  - `_optional_evidence`
  - `_output`
- The supplied-pose check becomes `pose.source != "estimated" and tracked["control"] != "reference"`, failing with "outside a labelled reference control".
- `validate` checks every proposal has `PROPOSAL_FIELDS = {"xyxy", "label", "object_id", "association"}`.

**`validation.py`**
- `ScoreRequest(component, load_references, options={}, reference_file=None)`. `reference_file` is hashed for provenance before the loader runs.
- `score(run_path, steps, requests)`.
- Components other than tracking and surface return "unavailable" with the Task56 reason, without loading references.
- Remove `score_compatible`, `_readonly`, `load_reference_bytes` and the precomputed hash.
- Tracking scoring rebuilds poses with `read_pose`.

**`cli.py`**
- Build `PipelineSpec` from flags: `PhoneExport` or `TumSequence`, and `Yolo26x` when `--checkpoint` is given.
- TUM scoring is `ScoreRequest("tracking", functools.partial(read_references, file), reference_file=file)`.
- Remove the temporary reference file and the repeated checks.
- Name-to-method lookups for future methods live only here.

**`experiments/shared/runs.py`**
- Add `IncompleteRun`, and `Run.stop_incomplete(reason)`, which calls `self._failed(IncompleteRun(reason))`.
- `__exit__` finishes only when the status is still `running`.
- `status.json` keeps `error_type: IncompleteRun`, as today.

**`experiments/shared/geometry.py`**
- Pull the first two checks of `backproject` out into `check_depth_grid(depth, valid, calibration)`, and have `backproject` call it.

### Phases

0. Owner requested completion of Task59 on 2026-10-07 after cancelling the previous execution. Preserve Task51's uncommitted work and take the active task lock for Task59; no Task51 commit is required. Record the current failing-test baseline, then migrate its stale contract tests as part of this task. Run plan lint and the plan-reviewer, stamp the review, then start Task59. Leave the inaccessible old temporary reference folder alone.
1. Shared helpers: `Run.stop_incomplete`, `check_depth_grid`, `records.py`, `steps/contracts.py`.
2. The six layers, in README order.
3. `config.py` and `pipeline.py`.
4. `validation.py` and `cli.py`.
5. Tests (below).
6. Documentation (below).

### Tests

**Fixtures.** In `tests/providers.py`, each fixture follows its layer's contract:

- `flat_depth(frames, *, run)` yields 2 m everywhere.
- `IdentityBackend` is run as `partial(track, backend=IdentityBackend())`.
- `no_site_measurements(surface, run_path)`.
- `WholeImageDetector`.
- `Fixture(name, runnable)` has `control="software"`.
- `with_controls(spec, **swaps)` fills every layer with a fixture.

| Existing test | Change |
|---|---|
| `test_pipeline.py` (4 tests) | Stubs take the new layer signatures; same assertions. `score` stub takes `(run_path, steps, requests)`. |
| `test_skipped_layer_does_not_access_run_inputs_or_import_methods` | Replace with `test_skipped_layer_is_never_called` (request only capture; five "Not requested" rows). |
| `test_adapters.py` `config` fixture | `with_controls(PipelineSpec(..., PhoneExport(report, bundle), objects=ObjectSettings(max_distance_m=0.35, ambiguity_margin_m=0.05)))`. |
| `test_tracking_range_is_refused_without_clipping` | `out_of_range` follows the depth contract and is passed as a `Fixture`. |
| `test_test_providers_cannot_be_used_as_predictive_methods` | Replace with `test_fixture_marks_run_as_control`: `controls[layer] == "software"`, `is_measurement` false, and `cli --help` lists no fixture. |
| `test_prediction_data_are_readonly` | Delete with `_readonly`. |
| `test_configuration_rejects_unsupported_values` | Parameters move to `ObjectSettings`, `ClassicalSegmentation` and `PipelineSpec`. |
| `test_disabled_optional_validation_never_reads_truth_or_imports` | Rename `test_unscored_components_never_read_truth`; drop the import assertions. |
| `test_actual_six_adapters_keep_origins_and_full_geometry` | Check `withheld_from_methods` has non-empty `depth` and `pose` reasons. |
| `test_score_refuses_complete_status_without_artifact` | Call `validation.score(run_root, steps, requests)`. |
| `test_imports_cli.py` | Still no torch, ultralytics or open3d on import; remove the cv2 and segmentation/appearance assertions. |

| New test | Exact assertion |
|---|---|
| `test_every_completed_layer_records_load_prediction_and_visual_timing` | every completed layer has `load_<layer>` and `prediction_<layer>` (1 successful sample), and `visual_<layer>` exists for all six |
| `test_frame_layers_report_frame_counts_and_fps` | depth, tracking, surface, objects: `frames == N` and `fps > 0` |
| `test_per_frame_samples_exist` | N samples each of `depth_frame`, `surface_frame`, `objects_frame`, each `frames == 1` |
| `test_result_rows_name_method_and_frames` | rows hold `flat_depth`, `identity_backend`, `metric_points`… with `frames == N` (mapping `None`) |
| `test_skip_reason_follows_partial_rule` | mapping unavailable: objects skipped without `--partial`, runs with it. Depth failed: surface reason is "Waiting on earlier layers: depth is failed, tracking is skipped" |
| `test_skip_reasons_trace_to_root_cause` | no depth method: every skipped reason contains "depth is unavailable"; depth's contains "Task54" |
| `test_depth_contract_refuses_wrong_count_or_order` | one too few, one too many, or two swapped predictions: depth `failed` with the matching reason |
| `test_multi_view_depth_fits_contract` | a fixture that reads all frames before yielding completes; the first `depth_frame` sample holds most of the time |
| `test_tracking_lost_frame_reason_is_visible` | one `pose=None` record: tracking `failed`, reason names the frame and its record reason |
| `test_reference_depth_on_tum_sample` | `RecordedSensorDepth` completes with `control == "reference"`, applies the 4 m limit, `is_measurement` false |
| `test_reference_poses_reach_objects_only_under_control` | `ReferencePoses` lets objects run; the same supplied poses without the label fail objects with "outside a labelled reference control" |
| `test_contract_checks_catch_bad_content` | NaN surface points, and a proposal without `object_id`, each fail with the frame named |
| `test_runs.py::test_stop_incomplete_keeps_files_and_refuses_verify` | status `failed`, `error_type == "IncompleteRun"`, no manifest, `verify_run` raises |
| `test_geometry.py::test_check_depth_grid` | raises on wrong shape, non-bool mask, or a valid pixel ≤ 0 or NaN; passes a good grid |

### Documentation

**`src/walkthrough/README.md`**: rewrite with these sections. Keep Task 51's visual-page paragraph as it is.

1. **The six layers.**
2. **How one layer runs:** choice → load → predict → save → status row → check → pictures.
3. **Choosing methods:** a `PipelineSpec` example, then a table of today's choices and gaps per layer, including the two reference controls.
4. **Adding a method:** a frozen dataclass with `name` and `control`, and `load()` returning the method-contract runnable.
5. **Layer contracts:** the table above.
6. **Testing one layer on its own:** the reference controls, and the rule that they are the only way references reach a method.
7. **Run recorded input:** the CLI commands, and today's exit code 2 with the Task54 reason.
8. **What each run saves.**
9. **Why something did not run:** the gap table above.
10. **Measurements and tracing:** the label table above.
11. **Scoring and publication:** hash before scoring, `stop_incomplete`.
12. **Failure, restart and memory.**
13. **Current availability:** phone calibration limits, the 4 m tracking range, counting per origin.
14. **Software checks.**

**Project `README.md`, "Canonical runner and current gaps"**: add the following.

- Each layer has one method slot with a written contract.
- Recorded TUM depth and poses can be fed in as labelled reference controls, and those runs never count as measurements.
- Development uses recorded and benchmark data. Deployment has to be on a phone, because only our capture app can record the per-frame calibration.

**`src/README.md`**: the first paragraph mentions method slots, the contracts in `steps/contracts.py`, reference controls, and links Task 59.

**`task_list/README.md`**: add a Task 59 row after Task 58.

### Follow-up tasks (not in this task)

1. **Joint multi-layer methods.** MapAnything, VGGT and MASt3R estimate depth, poses and calibration together. Allow one method choice to produce several layers' saved outputs, each checked by its own layer validator.
2. **Per-layer scorers for the grid.** Today only tracking and surface are scored. Start with depth against TUM sensor depth (absolute error in mm, relative error). Detection and counting scores stay with Task 56.
3. **Calibration slot.** Calibration becomes a swappable choice: reported by the phone, a known file, or estimated from frames. Each frame records where its calibration came from.
4. **Video-file and stream sources.** `VideoFile(path, calibration)` and `CameraStream(...)` are capture sources with the same `read()` and `withheld_inputs()`. A deployed phone stream must carry per-frame calibration, the active lens, zoom/crop and stabilisation state.
5. **Phone capture metadata (Task 52).** Record the per-frame items the app does not yet capture (see Background), and lock lens, zoom, focus and stabilisation during walkthroughs.
6. **Fused surfaces.** Meshes and splats need a whole-sequence surface contract. The visual export also needs per-point colours from the method, because it colours points from source pixels today.
7. **Grid runner.** Loop over method combinations and collect `result.json`, `timing.json` and `scores.json` into one table. Task 44's per-stage report is the natural place to compare them.
8. **Peak memory per layer (Task 57).** Resident memory at a scope's start and end is not a true peak; a sampler or the system high-water mark is needed.

---

## Invariants and recovery

| Datum | Producer | Consumer | Representation | Survives restart? |
|---|---|---|---|---|
| Method choices | `PipelineSpec` | settings snapshot, `result.json` | JSON from `asdict`; each choice carries `name` and `control` | yes |
| Saved images | `capture.run` | depth, tracking, objects, visuals | `input/images/<index:06d>.<ext>`, original bytes, SHA-256 | yes |
| Depth arrays | `depth.run` | tracking, surface, objects, visuals | `.npz` `depth` (camera-axis m) + `valid` (bool) on the image grid | yes |
| Poses | `tracking.run` | surface, objects, scoring, visuals | 4×4 camera-to-world, m, with world/segment and `source` | yes |
| Surface points | `surface.run` | mapping, scoring, visuals | `.npy` N×3 world m per frame, labelled origin | yes |
| Status rows and controls | layers, `PipelineSpec` | `result.json`, visuals | `StepResult` rows, `controls`, `is_measurement` | yes |
| Timing | `TimingLedger` via `Run.measure` | `timing.json` | seconds + frames per scope, schema 2 (unchanged) | written at finish or failure |
| Run status | `Run` | `verify_run` | `status.json`: running / failed / complete | yes |

- **Source of truth:** the run folder. Every manifest is written before the next layer runs.
- **Process boundaries:** one process and one thread.
- **Death after a layer:** status stays `running` and never verifies. Retry into a fresh run, never the old folder.
- **Incomplete run:** `stop_incomplete` writes `failed`/`IncompleteRun`, keeps all files and writes no manifest. This matches today's result on disk.
- **Fresh deployment:** install shared requirements (including the installed OpenCV CPU package), then `python -B -m src.walkthrough.cli --dataset … --run-root …`. No model loads at import.
- **Backward compatibility:**
  - `result.json` rows gain `method` and `frames`, and `software_control` becomes `controls` and `is_measurement`.
  - `capture.json` replaces the bare `"depth"`/`"pose": "unavailable"` with `withheld_from_methods`.
  - Skip-reason wording changes.
  - Depth and surface files become zero-padded.
  - Origin namespaces come from experiment 03's default ID.
  - The visual code reads none of the changed keys.
  - Frozen experiment commands and historical runs are untouched.

## Hyperparameters

hyperparameters n/a: a refactor. No method settings change. The reference controls reuse experiment 03's frozen values (0.02 s matching tolerance, 5000 depth units per metre, 4 m range; dataset.py:79, 123-124). Counting distances stay supplied by their owner.

## Clarifications

### Session 2026-10-07

| # | Question | Owner answer | Applied |
|---|---|---|---|
| 1 | Keep "parse the same bytes we hashed" for the TUM reference, or hash the file and let the experiment read it? | Accept the simpler version. | one loader plus an optional `reference_file` hashed for provenance |
| 2 | Import OpenCV diagnostics only when chosen? | "No need to overcomplicate the imports, it can be imported and not used, that's fine." | rule 6; all imports at the top |
| 3 | Add `Run.stop_incomplete` and `check_depth_grid` to shared code? | Accept. | as specified |
| 4 | A malformed phone report would stop the run instead of writing a row. | "We haven't even deployed to phone yet… we're focusing on just video for the time being." | no phone-report handling added; `PhoneExport` moves unchanged; recorded sequences are the focus |
| 5 | Keep `"depth"/"pose": "unavailable"` in `capture.json`? | Keep, but "we need visibility over 'why' it didn't reach a method." | `withheld_from_methods` with reasons; skip reasons name the blocking layer; rule 10 |
| 6 | About 3 timing rows per frame in `timing.json`? | "Certainly accept while we're testing and trialling." | per-frame scopes as specified |
| 7 | Does the plan give distinct, swappable contracts per layer? Fold in the gaps? | "Write this all into your report." | all-frames contracts for depth and tracking; the contract table with matching checks; reference controls. Joint methods, scorers, calibration slot and the others listed under Follow-up tasks |

**Owner direction, 2026-10-07: deployment has to be on a mobile phone.** Trustworthy calibration needs our own phone app to record it per frame (see Background). Until then, development and accuracy work use training, test and pre-existing recorded data. Still undecided: whether "on mobile" covers capture only, with processing hosted, or processing too. The project README's "Hosted or on the phone" lists both. Layer contracts must not assume desktop-only inputs.

## Verification

**Contract test:** `src/walkthrough/tests/test_pipeline.py`. It asserts four things:

- each earlier `predictions/<layer>.json` exists before the next layer runs
- `prediction_hashes.json` exists before scoring
- a full fixture run completes, with `is_measurement` false
- a run with no depth method ends with the five expected statuses, reasons tracing to "depth is unavailable", and `verify_run` raising

| Measure | Before | Target |
|---|---|---|
| `pipeline.py` lines | 241 | ≤ 120 |
| Runner code (excluding tests and `visualization.py`) | 1,688 | ≤ 1,450, while adding contracts, controls and timing |
| `importlib.import_module` inside functions | 17 | 0 |
| Runtime `software_control` guards in layers | 6 | 0 |
| Layers with a method slot and written contract | 0 of 6 | 6 of 6 |
| Layers that can take a reference control | 0 | 2 (depth, tracking) |
| Frame layers with non-null `fps` | 0 of 4 | 4 of 4 |
| Layers with loading timed apart from inference | 0 | 5 |
| Skipped rows whose reason names the blocking layer | 0 | all |
| Walkthrough tests | 30 of 51 pass (mid-edit tree) | all pass, plus 14 new tests |
| `python -B tools/check.py -q` | green at Phase 0 | green |
| TUM CLI command | exit 2, Task54 unavailable | unchanged |
| `visualization.py` changes | n/a | none |

Before closing, run the diff-reviewer agent on the whole diff without telling it the intent. Fix or waive each finding here.

## Receipts

| Field | Value |
|---|---|
| Closing commit | b487c9acda764a88910a4ebf5bf65c9568568fa7; source baseline 14957e6f2b706afa33d2db1128175826ed6245f7 |
| Files changed | src/walkthrough/config.py, pipeline.py, records.py, validation.py, cli.py, steps/contracts.py, artifacts.py, capture.py, depth.py, tracking.py, surface.py, mapping.py, objects.py; walkthrough tests/providers.py, test_pipeline.py, test_adapters.py, test_imports_cli.py, test_layers.py, test_contracts.py; experiments/shared/runs.py, geometry.py, requirements.txt, tests/test_runs.py, tests/test_geometry.py; root/src/walkthrough/shared READMEs and task index. Task51's already-written visualization.py is retained unchanged as a required source dependency. The now-unused untracked provenance.py helper was removed. |
| Test status | Full CPU suite: 749 passed, 7 skipped in 280.51 s. Final targeted suite after review fixes and calibration regression: 195 passed in 117.90 s; 93% production-code coverage (tests excluded). Walkthrough has 84 cases, up from 51. Ruff and git diff --check pass. Scoped mypy passes for 15 core files; unchanged visual typing and pipeline's status-dependent optional flow remain outside that scoped check. |
| Before | 21 failed and 30 passed walkthrough cases; targeted walkthrough/shared baseline 21 failed and 135 passed. Pipeline 241 lines; total runner 1688 lines; 0/6 method slots; 0/4 frame-layer throughput counts; 17 function-level import_module calls. |
| After | Pipeline 107 lines; total runner 1606 lines excluding tests/visualization. 6/6 documented method slots; 2 reference controls; 4/4 frame layers have positive fps and correct frame counts; 6 loading/preparation scopes and 6 visual scopes; 0 function-level import_module calls; 0 runtime software_control guards in layers. |
| Delta | Pipeline -134 lines; total runner -82 lines. +6 method slots, +2 recorded-reference controls, +4 frame-layer throughput measurements, +33 walkthrough cases. The original 1450 total-line target is missed by 156 lines, explicitly recorded below. |
| Decision-gate outcome | Plan review PASS after compatibility corrections. Independent code, Python and six-surface diff reviews completed; all concrete findings fixed and pinned by regression checks. Reproduction rechecks PASS. Scope is software infrastructure; no real depth/mapping model, physical accuracy trial, phone deployment or peak-memory claim was made. |

### Completed work

- [x] Preserve the cancelled session's prerequisite source changes, record the red baseline and take the Task59 lock through task.js (Task51 demoted to open).
- [x] Shared depth-grid and incomplete-run contracts; six method choices and saved-output contracts.
- [x] Explicit six-layer runner, independent scoring and recorded-input command line.
- [x] Reference controls, loading/frame/visual timing, method/status tracing, root-cause reasons and unchanged visual compatibility.
- [x] Contract tests, source-time/origin checks, failure tests, reference separation, export tests and README updates.
- [x] Independent plan, code, Python and finished-diff review; full and final focused verification.

### Review findings and resolutions

| Finding | Resolution and evidence |
|---|---|
| Existing visuals imported artifacts.py, read synthetic_detector and require source-point colour correspondence | Retained type re-exports and synthetic_detector. Surface checks finite points and exact valid-pixel count; row-major order is explicit in the contract. Software visual manifest and wrong-count tests pass. No visualization.py edits. |
| Supplied poses were rejected by the frozen reconstruction method | MetricPoints composes existing shared geometry; surface and objects permit supplied poses only with tracking control=reference. Reference source labels remain supplied. |
| Unconditional diagnostics imports needed OpenCV | Declared installed opencv-python 5.0.0.93 in shared requirements; fresh-process import still loads no torch, ultralytics or open3d. |
| Real mapping accepted absent or unitless measurements | Real measurements now require a finite numeric value and nonblank units; labelled software placeholders remain separate. Nine invalid cases and a valid 7 metre measurement pass. |
| Missing phone bundle caused TypeError | Command-line pairing check returns argparse error before creating a run; no duplicated source/config checks. |
| Required metadata was checked only after model loading | Capture clock/calibration preflight precedes method.load. Load-spy regressions assert it is never called for incompatible inputs. |
| Missing scoring file aborted capture-only runs | Incomplete components record reference_unavailable_reason; unsupported scorers do not open references. Completed scoring still propagates missing-reference failure. |
| Tracking scorer combined worlds sharing segment labels | Scoring-only pose keys include both world and segment. Four poses across two worlds now yield 0 m position error and two scored segments; prediction bytes remain unchanged. |
| A tracker could change source timestamps | Tracking validates each returned timestamp against capture and names the frame on failure. |
| A capture row exposed the frozen global calibration dictionary | asdict creates a separate calibration dictionary per row. Mutating one returned row changes neither another row nor a later run's calibration. |
| Frozen method choices did not satisfy writable Protocol fields | Shared MethodChoice declares read-only properties. Dynamic numeric experiment records keep their owning runtime classes and use Any for static aliases; runtime contract checks remain authoritative. |

### Evidence and bounded exceptions

- Full-suite and final coverage logs: outputs/task59_checks/full-suite.log and final-targeted.log. Shared RED log: shared-red.log (6 missing-API failures), followed by 6 passes. New method-slot RED: missing PipelineSpec, followed by successful contract checks.
- Recorded-source smoke run: outputs/task59_checks/cli_runs/20261007T114822.671075Z_bf70ddc66b114f2ea28138adb41d5004. Two existing TUM RGB images were copied into an identified sample. CLI returned 2; capture completed, depth was unavailable with Task54 reason, four later layers were skipped, visual index exists and verify_run refused publication. No model or accuracy measurement was performed.
- Total-size target variance: 1606 rather than <=1450 lines. Independent Python review found no safe 156-line removal while retaining contracts, reference controls, provenance and timing. The runner itself meets <=120 lines. Retain the boundary checks and readable formatting rather than compressing or deleting required behavior. This size estimate is waived at closure; it is not an outstanding feature.
- The old walkthrough-references-13o_jh04 folder is inaccessible on this machine. Cleanup is waived; no current code uses it or creates reference scratch files.
- Whole-project board audit reports pre-existing oversized vendored files under third_party; this task changes no such file. All walkthrough files stay below 800 lines.
- Six agents were used, with the plan reviewer reused for test execution. Windows Black CLI processes hung; verified task-owned formatter processes were stopped and formatting was completed through Black's synchronous API.
- Existing unrelated data/capture documentation changes and Task51's task record remain outside the scoped implementation commit. Historical experiment commands and runs are unchanged.
- The eight items under Follow-up tasks are intentionally separate scope, not unfinished Task59 requirements. Real depth, mapping, complete physical scores, capture metadata, phone processing placement, sustained performance and peak memory remain with their named owners.

## Reopened correction plan, 2026-10-07

### In plain English

Recorded depth incorrectly prevents two colour frames from using the same nearby depth image. Fix both reference inputs to match one frame at a time, keep decoded images out of sequence-wide lists, and report missing methods without pretending loading failed. Keep the existing safety checks and add tests using the real recording's timestamp pattern.

### What and why

Reopen Task 59 after owner review. The XYZ recording has 798 colour frames, six unmatched by the reference adapter's one-to-one association, but zero unmatched by nearest matching within 0.02 s (maximum gap 0.017199993 s). Both adapters retain decoded frames for the entire sequence. Repeated contract traversal and absent-method timing also diverge from the approved examples. Original implementation receipts remain historical; correction receipts will be added separately.

### How: reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Existing matcher is deliberately one-to-one and must remain unchanged | associate_times | frozen experiments and scorers | experiments/shared/geometry.py:91 |
| Recorded depth can use table rows and existing decoding | RecordedSensorDepth, depth_metres | depth.run | src/walkthrough/steps/depth.py:39,70 |
| Recorded poses can use the existing reference reader | ReferencePoses | tracking.run | src/walkthrough/steps/tracking.py:57 |
| NumPy searchsorted already locates adjacent timestamp candidates | associate_times | new reference-only nearest helper | experiments/shared/geometry.py:107 |
| Pipeline repeats output validation done before publication | run | visual consumers | src/walkthrough/pipeline.py:59,79,89 |
| Proposal fields are checked before output assembly and by output validator | _count, validate | objects.run, pipeline.run | src/walkthrough/steps/objects.py:203,296 |

- Add one reference-only nearest-timestamp helper in steps/contracts.py; reuse the readers' finite ordered timestamp checks and validate finite nonnegative tolerance at construction, match with binary search, break equal-distance ties toward the earlier timestamp, include the exact tolerance boundary, and permit reference reuse. Shared one-to-one matching remains untouched.
- Stream RecordedSensorDepth without collecting decoded colour frames; add named units_per_metre and max_depth_m fields with experiment source comments. Retain path/PNG/grid validation and missing-timestamp rejection.
- Stream ReferencePoses into lightweight PoseRecords, never retaining RGB-D frames; unmatched records have status lost and pose None. Ordinary tracking still refuses incomplete placement.
- Keep tracking/mapping/objects validation in their layer before writing, remove the duplicate pipeline calls. Remove the earlier duplicate proposal-field traversal; keep the final object output validator with frame-specific errors. Capture/depth/surface validation is outside this correction scope.
- Return unavailable reasons before load_depth/load_mapping/load_objects timing starts when inputs/methods are missing; real method-load errors still receive failed timing samples.
- Add one-line built-in method docstrings naming their experiment owners.
- Add portable timestamp collision, genuine-gap, tie/boundary, invalid-setting, memory-lifetime, missing-pose-status, single-validation and timing regressions in src/walkthrough/tests/test_reference_inputs.py and test_layers.py. Use the actual first 20 XYZ timestamps, plus a local real-image integration check; portable tests must not depend on an untracked dataset download.
- Update declared READMEs and the task index for this correction.

### Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| Reference table readers | reference-only matcher | finite increasing timestamps in seconds | table files remain unchanged |
| Colour/RGB-D iterator | reference adapters | one decoded frame at a time; same frame IDs/order | capture/depth artifacts remain unchanged |
| Reference adapter | layer saver | one prediction/record per input; reference label; supplied pose only when present | saved JSON/arrays |
| Layer validator | saver and pipeline | malformed outputs fail before publication | run remains incomplete |

Source of truth is the selected recording, not a generated reference file. No new process or persistent state boundary is introduced. A failed or interrupted run keeps the existing incomplete-run behavior and a new run recomputes outputs. Existing method call signatures and scorer association semantics remain unchanged. Added depth fields preserve inherited defaults (5000 units/m, 4 m); no experiment method settings change.

### Verification

Contract tests assert nearest reference reuse at colliding real timestamps, true gaps rejected, tie goes earlier, exact tolerance accepted, invalid timestamps/settings rejected, previous decoded frames collectible before the next frame arrives, lost status on an unmatched pose, and exactly one tracking/mapping/objects validation per pipeline run. Missing methods have zero load samples; a selected loader failure retains one failed sample.

Before/after targets: XYZ missing depth 6/798 -> 0/798; first 20 frames missing 3/20 -> 0/20. Retained decoded frames bounded independently of sequence length. Existing 195 focused checks remain passing; production coverage >=80%. Run a real 20-frame depth/pose/surface integration and the full CPU suite. Review changed Python and finished diff before closure.

### Correction receipts

| Receipt | Result |
|---|---|
| Closing implementation commit | fd427084e38164561f100b3a1e1b24eda56de37f |
| Files changed | pipeline.py; steps/contracts.py, depth.py, tracking.py, mapping.py, objects.py, capture.py, surface.py; tests/test_layers.py, test_reference_inputs.py, test_reference_inputs_real.py; walkthrough README, src README, task index and this record |
| Before | XYZ 6/798 unmatched depth frames, first 20 3/20 unmatched; both reference adapters buffer all decoded frames; three absent-method load stages recorded as failed; tracking/mapping/objects output validation invoked twice, object proposal fields checked three times; missing pose status supplied |
| After | XYZ 0/798 unmatched, first 20 0/20 unmatched; real 20-frame depth/pose/surface run succeeds; first decoded frame and its arrays collectible before frame 3 arrives in both adapters; absent methods/settings create zero load samples; selected loader failures still timed; one output validation per tracking/mapping/objects layer, one object proposal-field traversal; missing pose status lost |
| Delta | Six full-sequence gaps and three first 20 gaps removed; no whole-sequence decoded-frame retention in either adapter; pipeline 107 -> 101 lines, total runner 1606 -> 1629 lines excluding tests/visualization |
| Test status | Full CPU suite 805 passed, 7 optional skips in 186.95 s (outputs/task59_checks/correction_full.log). Focused run after timestamp-subtype and decimal-boundary review fixes: 254 passed in 121.52 s, 93% production coverage, 1363 statements/89 missed (outputs/task59_checks/correction_targeted.log). After the final tracking identity-check consolidation, seven count/order/timestamp/lost/object/publication checks passed in 8.82 s. Portable reference suite 52 passed. Two real-image/table checks passed in 5.51 s. |
| Red-first evidence | Original portable reference cases: 31 failed / 16 passed; timing/duplicate validation cases: 4 failed / 1 passed. NumPy timestamp regression:1 failed then passed. Decimal tolerance regression:4 failed then passed. |
| Static checks | Ruff passes changed Python; in-process Black at 120 reports no changes; scoped mypy passes seven core modules with --explicit-package-bases --follow-imports=silent --ignore-missing-imports. A broader import-following check reports seven existing errors only in unchanged experiments/shared/phone_session.py; that module was not changed. |
| Plan review | correction_plan PASS; corrected its two advisory evidence citations before implementation |
| Code review | correction_code_review APPROVE, no actionable defects |
| Python review | python_review PASS after fixing NumPy float timestamp compatibility and formatting |
| Diff review | correction_diff PASS after fixing decimal tolerance boundary; final tracking consolidation recheck PASS, with independent missing/extra/swapped record reproductions |
| Documentation | Declared walkthrough README, src README and task index updated this session; original shared/root README updates remain documented in the historical implementation receipts |
| Decision outcome | All requested corrections implemented and verified; genuine unmatched depth still fails, unmatched poses remain lost, and the shared one-to-one scorer/experiment matcher is unchanged |

Review findings and resolutions:

- A float subtype such as np.float64 was incorrectly rejected as a source timestamp. Accept float/int subclasses while rejecting bool and nonfinite values; the regression failed before the fix and passes afterward.
- A decimal boundary such as source 1.02 / reference 1.0 / tolerance 0.02 was incorrectly rejected by subtraction rounding. Check the inclusive timestamp interval, matching existing association semantics; four adapter regressions failed before the fix and pass afterward.
- The final tracking cleanup removes its repeated frame-identity traversal, retaining explicit count/lost diagnostics and identity/timestamp/pose validation before saving. Seven boundary/publication checks pass.

Bounded exceptions remain explicit: the original <=1450 total-line estimate was waived in the original receipts. Correctness and setting validation add 23 net lines, so the corrected runner is 1629 lines (179 over that estimate); the main runner remains below 120 lines. Peak memory for the complete application and sustained phone performance remain Task57, not proven by the frame-lifetime tests. Optional real-image tests skip when the dataset is absent; the timestamp collision tests always run. No correction feature remains pending.
