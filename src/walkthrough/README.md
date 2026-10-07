# Recorded walkthrough runner

The runner follows six layers in the project diagram. Each has one method choice with a written input and output contract. Swapping a depth model or detector means changing that choice. Experiments remain independently runnable.

1. Camera capture and input validation.
2. Depth in metres.
3. Camera position.
4. Observed surface.
5. Site dimensions and area.
6. Object recognition and counting.

## How one layer runs

Choose a method, load it, predict, check and save its output, record its status, then export pictures. The six calls are explicit in `pipeline.py`. A layer reads saved outputs from earlier layers; methods receive decoded inputs through their own contract. Expected missing inputs and errors become named status rows. Unexpected errors stop the run.

Every run also creates `output/visualizations/index.html` and `manifest.json`. The page shows saved RGB input, predicted depth, a binary validity mask with its valid-pixel count, and a colour overlay showing valid coverage on the source image. It also shows estimated camera paths, coloured point clouds, mapping measurements or an explicit no-geometry note, and object boxes with provisional IDs or an explicit zero-proposal count. Software-control object boxes are labelled synthetic in the image. The manifest names each stage's producer and each visual's source and producing method. PNG previews include the method in their image footer and metadata. Coloured PLY exports include the producing method and source frame in their header. The surface PLY keeps every reconstructed point; only the labelled cloud preview is evenly sampled for display. Separate tracking worlds and segments get separate cloud previews, so unrelated coordinates are not combined. These views never feed back into predictions or scores. Skipped or unavailable stages stay visible with their status and do not get invented visuals.

## Choosing methods

```python
from pathlib import Path
from src.walkthrough.config import PipelineSpec
from src.walkthrough.pipeline import run
from src.walkthrough.steps.capture import TumSequence

spec = PipelineSpec(
    run_root=Path("outputs/walkthrough"),
    repo=Path.cwd(),
    source=TumSequence(Path("data/tum/rgbd_dataset_freiburg1_xyz")),
)
result = run(spec)
print(result.complete, result.controls, result.steps)
```

This records RGB, then reports that real depth is unavailable. A complete measurement needs methods for all six layers.

| Layer | Available choices | Gap |
|---|---|---|
| Capture | `PhoneExport(report, bundle)`, `TumSequence(root)` | Video-file and live-stream readers are later work |
| Depth | `RecordedSensorDepth(root)` reference control | Task54 supplies validated real metric depth |
| Tracking | `CpuOdometry()`, `ReferencePoses(groundtruth)` reference control | More tracking methods can use the same sequence contract |
| Surface | `MetricPoints()` | Fused meshes and splats need a later contract |
| Mapping | A method implementing `MappingMethod` | Task55 supplies real dimensions and area |
| Objects | `Yolo26x(checkpoint)` inside `ObjectSettings` | Supply an acquired checkpoint and reviewed counting distances |

`ClassicalSegmentation(method)` and `ClassicalAppearance()` are optional object diagnostics. They save evidence without changing counting. All imports are at file level; model construction happens inside `load()`. Shared CPU requirements include OpenCV because these diagnostics import it.

Method combinations can be compared without changing the runner:

```python
from dataclasses import replace
from itertools import product

for depth_method, detector in product(depth_choices, detector_choices):
    chosen = replace(spec, depth=depth_method,
                     objects=replace(spec.objects, detector=detector))
    result = run(chosen, scores=score_requests)
```

The choices and score requests in this example are supplied by the caller. A grid report and complete per-layer accuracy scoring remain later work.

## Adding a method

A frozen choice records its name, settings and control label. Its `load()` returns the callable used by that layer. Here is a complete software-only depth example:

```python
from dataclasses import dataclass, field
import numpy as np
from src.walkthrough.steps.contracts import DepthPrediction

@dataclass(frozen=True)
class FlatDepth:
    name: str = field(default="flat_depth", init=False)
    control: str = field(default="software", init=False)

    def load(self):
        return self.estimate

    def estimate(self, frames, *, run):
        for frame in frames:
            shape = (frame.calibration.height, frame.calibration.width)
            yield DepthPrediction(frame.frame_id, np.full(shape, 2.0),
                                  np.ones(shape, dtype=bool))
```

A real choice uses `control=None` and builds its model in `load()`. Depth and tracking receive the whole sequence, so methods may read all frames before returning results. A per-image method can loop over the iterator. No saved artifact paths are passed into a depth or tracking method.

## Layer contracts

`steps/contracts.py` owns the shared shapes and readers. `steps/artifacts.py` re-exports saved-output types for the existing visual module. Each layer declares its method protocol beside its choices.

| Layer | Method receives and returns | Saved output and checks |
|---|---|---|
| Capture | Source reads itself and returns image rows | `capture.json`, original bytes; at least one image, unique IDs, source hashes, withheld-input reasons |
| Depth | All `ColourFrame` rows to one `DepthPrediction` per frame in order | `depth.json`, depth/mask NPZ files; camera-axis metres on calibrated grid, boolean mask, trusted pixels finite and positive |
| Tracking | All `RGBDFrame` rows to one `PoseRecord` per frame in order | `tracking.json`; valid camera-to-world transforms in metres, world/segment labels, no lost frame |
| Surface | One depth grid, mask, calibration and pose to world points | `surface.json`, NPY files; finite N by 3, one point per valid pixel in row-major mask order, origin and metre labels |
| Mapping | Surface manifest and run folder to named measurements | `mapping.json`; non-empty measurements, each real measurement has a finite numeric `value` and non-empty `units` |
| Objects | Image path to detections and original image size | `objects.json`, optional mask files; calibrated grid, frame IDs, box/label/object ID/association fields, counts per origin |

Surface point order preserves correspondence with source colours. Subsampled or fused surfaces need the later surface contract and visual changes. Tracking's current shared RGB-D record requires trusted depth strictly below 4 metres. A different depth model may return a wider range, but this tracking input refuses it rather than silently clipping it.

## Testing one layer on its own

```python
from dataclasses import replace
from src.walkthrough.steps.depth import RecordedSensorDepth
from src.walkthrough.steps.tracking import ReferencePoses

root = spec.source.root
controlled = replace(spec, depth=RecordedSensorDepth(root),
                     tracking=ReferencePoses(root / "groundtruth.txt"))
result = run(controlled)
assert result.controls["depth"] == "reference"
assert not result.is_measurement
```

A reference control supplies recorded depth or camera poses so later layers can be tested without errors inherited from that estimator. It is the only route for reference data into a method. Ordinary capture withholds supplied depth and poses and records why. All other references remain in scoring requests. Supplied poses reach surface and objects only under a labelled tracking reference control. Their saved source remains `supplied`.

Each reference adapter matches a frame independently to the nearest recorded timestamp within `tolerance_s` (default 0.02 seconds). Nearby frames may reuse a reference. Equal-distance matches choose the earlier timestamp, and the tolerance boundary is included. A genuine depth gap fails the layer with the frame named. A missing pose produces a `lost` record; tracking refuses to publish a complete layer with unplaced frames. Experiment and scoring association still uses its original one-to-one matching.

Reference adapters keep the reference table in memory and consume decoded colour or RGB-D frames as they arrive. They retain no sequence-wide image list. Recorded depth exposes `units_per_metre=5000.0` and `max_depth_m=4.0`, inherited from experiment 03's TUM reader. The range is exclusive: trusted pixels have depth below the maximum. These fields appear in saved run settings. A wider reference range still meets tracking's documented 4-metre restriction only if its valid mask excludes longer depths.

Controls use `software` for fixed fixtures and `reference` for recorded answers. `result.json` names every chosen control. Any control makes `is_measurement` false. This flag describes the source of predictions; it does not establish physical accuracy or phone fitness. Real-method results still report those as unmeasured until independently validated.

## Run recorded input

From the repository root:

```powershell
python -B -m src.walkthrough.cli --dataset data/tum/rgbd_dataset_freiburg1_xyz --run-root outputs/walkthrough
python -B -m src.walkthrough.cli --report <camera-report.json> --bundle <export-folder> --run-root <output-folder>
```

The ordinary TUM command returns exit code 2 with the Task54 depth reason today. The scorer records the tracking reference path and hash even when predictions are unavailable. The command line exposes no software fixtures or reference-control methods.

`--partial` allows a layer to run when its own required inputs exist. Otherwise it waits for every earlier layer. `--steps capture` requests a capture-only diagnostic; all six status rows remain visible, and it cannot verify as a complete walkthrough. Optional flags are `--checkpoint`, `--max-distance-m`, `--ambiguity-margin-m`, `--segmentation rectangle|grabcut|canny` and `--appearance`. These do not supply the missing depth or mapping methods.

## What each run saves

| Location | Contents |
|---|---|
| `input/` | Original image bytes, phone report or recorded-source facts |
| `output/predictions/` | Six layer manifests and numeric arrays where available |
| `output/result.json` | Status, reason, method, frames and artifact for each layer; controls and measurement eligibility |
| `output/scores.json` | Independent scores or explicit reasons they are unavailable |
| `output/visualizations/` | Offline index, manifest, labelled images and full coloured point clouds |
| `metadata/` | Settings, environment, source snapshot, timing, prediction hashes and run status |

## Why something did not run

| Gap | Where to look |
|---|---|
| Missing method or compatible input | Layer status `unavailable`, with the responsible task or missing input |
| Expected error | Layer status `failed`, with error type and message |
| Waiting for another layer | Layer status `skipped`, naming each blocking layer and its status |
| Source data held back from methods | `withheld_from_methods` in `capture.json`, with separate depth and pose reasons |
| Missing scorer | Component entry in `scores.json`, with the Task56 reason |
| Whole run incomplete | `metadata/status.json`: failed, with `IncompleteRun` |

## Measurements and tracing

| Timing label | Work measured | Frame count |
|---|---|---|
| `load_<layer>` | Source preparation or model loading, separate from prediction | None |
| `prediction_<layer>` | Entire layer, including saved outputs | Frames processed; mapping has no frame unit |
| `depth_frame`, `surface_frame`, `objects_frame` | One frame result | 1 |
| `odometry_pairs` | Tracking's existing pair estimation | 1 |
| `diagnostic_segmentation`, `diagnostic_appearance` | One optional diagnostic | 1 |
| `visual_<layer>` | Pictures and offline-page publication | None |
| `scoring` | Reference loading and independent scoring | None |

Times are seconds. Frames per second is successful frames divided by successful elapsed time. Nested timings overlap; never add them. Depth times each next result. A method that processes all frames first puts that waiting time into the first frame sample. Depth, tracking, surface and objects have a whole-layer frame count. The current tracking method also records its pair samples. Peak memory and sustained phone speed remain Task57 work.

A missing method or required counting setting returns its unavailable reason before loading starts, so it creates no `load_<layer>` sample. A selected method whose loader fails still creates a failed loading sample. Tracking, mapping and objects each validate their output once inside the layer, before saving it.

## Scoring and publication

`ScoreRequest(component, load_references, options, reference_file)` keeps answers outside methods. Prediction hashes are saved before scoring, then checked again afterward. The optional reference file is hashed for provenance before its loader runs. Hashing and parsing are separate operations; this version does not promise a single immutable reference-byte snapshot.

Tracking uses experiment 03's scorer, keeping each world and segment separate during alignment. Saved tracking timestamps must match capture. Surface uses experiment 04's scorer and requires references in every scored shard's origin. Other component requests remain unavailable under Task56 without opening references. A missing or unreadable reference for an incomplete component is recorded as unavailable; it does not stop capture-only diagnostics. `Run.stop_incomplete(reason)` saves failed status and timing without a completion manifest. Only all six completed layers publish a complete run.

## Failure, restart and memory

Expected `Unavailable`, `ValueError` and `OSError` failures keep a status row. Other exceptions propagate and the shared run wrapper records failure. Scoring failures and changed predictions prevent publication. Process death leaves a running, unverifiable folder. Retry from the original input into a fresh folder.

The default depth, surface and object loops read and save one frame at a time. Sequence methods may buffer frames when their algorithm needs them; their method choice owns that memory. Tracking retains pose records; object counting retains proposals and tracks per origin. Actual peak memory has not been measured.

## Current availability and mobile deployment

Development and accuracy validation use training, test and pre-existing recordings. Deployment must use a phone capture app so it can record camera calibration for each frame. Whether processing also runs on the phone or on a host remains undecided. The contracts preserve source identity, timestamps and calibration without assuming a desktop source.

Calibration describes focal length in pixels, image centre, image size and lens distortion. A plain MP4 does not supply all the per-frame metadata needed for trustworthy metric geometry. Lens changes, zoom/crop and stabilisation must be recorded or controlled. Task52 owns the missing phone metadata and capture controls. This task adds no capture app or service.

Phone geometry currently requires the full unrotated sensor grid, zero skew and explicitly zero distortion. Unsupported crop/resize/correction geometry is refused. Objects use CPU inference with an acquired checkpoint. Counts stay provisional and separate for each world and segment; no whole-site distinct count is claimed. Real depth, dimensions and complete accuracy remain Tasks54-56 work.

## Software checks

```powershell
python -B tools/check.py src/walkthrough/tests experiments/shared/tests -q
```

The fixtures test execution order, saved contracts, timing, reference labels, scoring integrity, failures and visual exports. They are ordinary method choices labelled `software`, never physical accuracy evidence. Existing frozen experiment commands and historical runs remain unchanged.

Reference regressions embed the first 20 XYZ recording timestamps to catch competing matches without a dataset download. They check genuine gaps, tie and tolerance boundaries, frame release and invalid settings. When the optional XYZ images are installed, two further checks cover all 798 timestamps and a real 20-frame depth, pose and surface run.
