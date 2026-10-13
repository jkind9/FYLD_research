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

Every run also creates `output/visualizations/index.html` and `manifest.json`. The page shows saved RGB input, predicted depth on one fixed colour scale (blue 0 m to yellow 4 m, printed in the image footer; yellow also marks depth at or beyond tracking's 4 m range), a binary validity mask with its valid-pixel count, and a colour overlay showing valid coverage on the source image. It also shows estimated camera paths, coloured point clouds, mapping measurements or an explicit no-geometry note, and object boxes with provisional IDs or an explicit zero-proposal count. Software-control object boxes are labelled synthetic in the image. The manifest names each stage's producer and each visual's source and producing method. PNG previews include the method in their image footer and metadata. Coloured PLY exports include the producing method and source frame in their header. The surface PLY keeps every reconstructed point; only the labelled cloud preview is evenly sampled for display. Separate tracking worlds and segments get separate cloud previews, so unrelated coordinates are not combined. These views never feed back into predictions or scores. Skipped or unavailable stages stay visible with their status and do not get invented visuals.

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

With `DepthAnythingV2Metric`, this runs RGB frames through the local metric model and saves its depth maps. The checkpoint must already exist on disk; model loading is offline. Without that checkpoint, the depth layer reports the missing model clearly. Every layer now has at least one real method, so a run can complete all six layers without software fixtures (see [first real-method runs](#first-real-method-runs-7-october-2026)).

**Its metres are not accurate enough to measure with.** On the TUM indoor recordings, Depth Anything V2 Metric Small reads distances 1.34 times too far on `xyz` and 1.41 times too far on `desk` (median over frames). The factor also changes from frame to frame, from 0.86 to 2.09, so one fixed correction does not fix it: raw AbsRel is 0.34 and 0.45. Treat its output as shape that still needs a per-frame scale source, such as ARCore depth or tracked points on the phone. The measurements and the sparse-point scale test are in [experiment 02](../../experiments/02_stereo_depth/README.md#task54-measurements-on-tum).

| Layer | Available choices | Gap |
|---|---|---|
| Capture | `PhoneExport(report, bundle)`, `TumSequence(root)` | Video-file and live-stream readers are later work |
| Depth | `DepthAnythingV2Metric(checkpoint)` local metric model; `MetricVideoDepthAnything(checkpoint)` video model; `ScaleCorrected(base, scale)` with `OverlapChainScale()` (RGB only), `PoseTriangulatedScale(groundtruth)`, `ReferenceFrameScale(root)` or `ReferenceGlobalScale(root)`; `ScaledZipDepth(...)` and `RecordedSensorDepth(root)` reference controls | Depth Anything V2's raw metres are 34–45% off on TUM, and the error changes from frame to frame. Task65's scale corrections and their results are in [experiment 02](../../experiments/02_stereo_depth/README.md#task65-depth-whose-size-changes-from-frame-to-frame-8-october-2026). |
| Tracking | `CpuOdometry()`, `ReferencePoses(groundtruth)` reference control | More tracking methods can use the same sequence contract |
| Surface | `MetricPoints()` | Fused meshes and splats need a later contract |
| Mapping | `GridFootprint()`: experiment 05's top-down grid over the dominant plane of each tracking origin | The plane is fitted, not surveyed (on a desk recording it is the desk top); no physical reference yet (Task53) |
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
| Depth | All `ColourFrame` rows to one `DepthPrediction` per frame in order; optional per-frame `diagnostics` | `depth.json`, depth/mask NPZ files; camera-axis metres on calibrated grid, boolean mask, trusted pixels finite and positive; diagnostics saved as `method_diagnostics` (finite numbers, booleans or null only) |
| Tracking | All `RGBDFrame` rows to one `PoseRecord` per frame in order | `tracking.json`; valid camera-to-world transforms in metres, world/segment labels, no lost frame |
| Surface | One depth grid, mask, calibration and pose to world points | `surface.json`, NPY files; finite N by 3, one point per valid pixel in row-major mask order, origin and metre labels |
| Mapping | Surface manifest and run folder to named measurements, or a `MappingResult(measurements, maps)` that adds one record per origin with its grids | `mapping.json`; non-empty measurements, each real measurement has a finite numeric `value` and non-empty `units`; optional `maps` (plane, basis, grid origin, cell size, and an NPZ of observed/on-plane/highest-point grids under `output/predictions/mapping/`), saved only after the measurements validate |
| Objects | Image path to detections and original image size | `objects.json`, optional mask files; calibrated grid, frame IDs, box/label/object ID/association fields, counts per origin |

Surface point order preserves correspondence with source colours. Each surface shard also records `camera_centre_m`, its camera position in that origin's world, so mapping knows which side of a plane the cameras were on. Subsampled or fused surfaces need the later surface contract and visual changes. Tracking's shared RGB-D record requires trusted depth strictly below 4 metres; deeper pixels are marked invalid when tracking and objects load their frames, and a frame with none left inside 4 m is refused.

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

Reference adapters keep the reference table in memory and consume decoded colour or RGB-D frames as they arrive. They retain no sequence-wide image list. Recorded depth exposes `units_per_metre=5000.0` and `max_depth_m=4.0`, inherited from experiment 03's TUM reader. The range is exclusive: trusted pixels have depth below the maximum. These fields appear in saved run settings. Tracking and object placement only accept depth below 4 m (experiment 03's working range, `RGBD_MAX_DEPTH_M` in `steps/contracts.py`). When they load RGB-D frames, depth at or beyond 4 m is marked invalid for them; the saved depth layer output is unchanged. A frame with no valid depth left inside 4 m is refused with an `out-of-range` error rather than passed on empty.

Controls use `software` for fixed fixtures and `reference` for recorded answers. `result.json` names every chosen control. Any control makes `is_measurement` false. This flag describes the source of predictions; it does not establish physical accuracy or phone fitness. Real-method results still report those as unmeasured until independently validated.

## Run recorded input

From the repository root:

```powershell
python -B -m src.walkthrough.cli --dataset data/tum/rgbd_dataset_freiburg1_xyz --run-root outputs/walkthrough
python -B -m src.walkthrough.cli --report <camera-report.json> --bundle <export-folder> --run-root <output-folder>
```

Without `--depth`, the depth layer is unavailable and later layers wait, so the command returns exit code 2. The scorer still records the tracking reference path and hash.

### Choosing real methods from the command line

```powershell
.venv-yolo/Scripts/python.exe -B -m src.walkthrough.cli `
  --dataset <tum-recording-or-clip> --run-root outputs/walkthrough `
  --depth depth-anything --device cpu --mapping grid-footprint `
  --detector-checkpoint checkpoints/yolo26x.pt --max-distance-m 0.35 --ambiguity-margin-m 0.05 `
  --partial
```

| Flag | Layer | Choices |
|---|---|---|
| `--depth` | Depth | `depth-anything` (Depth Anything V2 Metric Small, local weights in `--depth-checkpoint`, default `data/models/depth_anything_v2_metric_indoor_small`) or `recorded` (the dataset's own sensor depth, labelled a reference control; needs `--dataset`) |
| `--device` | Depth | `cpu` (default) or `cuda` |
| `--depth zipdepth-scaled`, `--points-per-frame` | Depth | ZipDepth's phone build (default weights `data/models/ZipDepth/checkpoints/zipdepth_base_npu.pth`) scaled each frame from 50 random recorded depth pixels; a labelled reference control that needs `--dataset`, and `data/models/ZipDepth` on `PYTHONPATH` |
| `--depth video-depth-anything` | Depth | Metric Video Depth Anything Small (default weights `data/models/Video-Depth-Anything/checkpoints/metric_video_depth_anything_vits.pth`); needs `data/models/Video-Depth-Anything` on `PYTHONPATH`. It reads the whole clip before returning any frame. |
| `--depth-scale` | Depth | On top of `depth-anything` or `video-depth-anything`, multiplies each frame by one factor: `overlap-chain` (from earlier frames' overlap; colour frames only, no reference), `pose-triangulated` (corners triangulated with the recording's motion-capture poses plus 5 mm noise, standing in for phone tracking; reference control), `overlap-chain-pose-anchor` (the chain's frame-to-frame factors times one run-wide factor from the triangulated points; reference control), `reference-frame` or `reference-global` (fitted to the sensor depth per frame or once per run; reference controls). Reference choices need `--dataset`. The factor each frame got is saved in `depth.json` as `method_diagnostics`. |
| `--pose-noise-m`, `--chain-smoothing-frames` | Depth | Settings for the scale sources above: per-frame translation noise added to the motion-capture poses (default 0.005 m), and a causal median over the last n chain factors (default 1, none). Refused with any other `--depth-scale`. |
| `--detector-device` | Objects | `cpu` (default) or `0` for GPU 0 |
| `--report-pages` | After the run | Builds the interactive report pages described below |
| `--mapping` | Mapping | `grid-footprint` (experiment 05: 5 cm cells over each origin's dominant plane) |
| `--detector-checkpoint` (old spelling `--checkpoint`) | Objects | YOLO26x weights, for example `checkpoints/yolo26x.pt` |
| `--max-distance-m`, `--ambiguity-margin-m` | Objects | Counting settings; 0.35 and 0.05 are the values inherited from experiment 06's pilot (`pilot/replay.py:46`) |
| `--segmentation rectangle\|grabcut\|canny`, `--appearance` | Objects | Optional diagnostics that never change counts |

`--partial` lets a layer run when its own inputs exist, so later layers still run when one layer is unavailable. `--steps capture` requests a capture-only diagnostic; all six status rows stay visible. The `.venv-yolo` environment has every library the real methods need (PyTorch 2.11, Transformers 5.14.1, Open3D 0.19.0, Ultralytics 8.4.172). YOLO prints warnings to standard output ahead of the JSON summary; the same summary is saved in `output/result.json`.

**Frame spacing matters.** Tracking starts a new origin whenever two frames are more than 0.1 s apart. A clip made of every third 30 Hz frame has gaps of about 0.1 s and broke into 16 pieces; every second frame (gaps up to 0.068 s) tracked all 29 steps.

### First real-method runs, 7 October 2026

30 frames of TUM `freiburg1_xyz` (the first 60 RGB frames, every second one; about 2 seconds), CPU only, all six layers real: TUM capture, depth, CPU odometry, metric points, grid footprint mapping and YOLO26x objects. The clip is `outputs/task51_real_clips/rgbd_dataset_freiburg1_xyz_first60_every2` (byte copies of the RGB and nearest depth frames plus the full ground-truth file). Runs are under `outputs/task55_real_runs/reviewed_*` (local, not in Git); each has an `output/visualizations/index.html` showing every handoff. Re-running gives identical numbers.

| Depth source | Tracking steps linked | Camera position error (RMSE) | Step error (RMSE) | Desk-plane area | Seen footprint | Region | Distinct provisional objects |
|---|---|---|---|---|---|---|---|
| Kinect sensor depth (reference control) | 29 of 29 | 0.021 m | 0.009 m | 2.21 m² | 4.09 m² | 4.40 x 3.10 m | 19 |
| Depth Anything V2 Metric Small | 29 of 29 | 0.218 m | 0.059 m | 7.44 m² | 16.37 m² | 5.25 x 5.85 m | 26 |

Depth error carries through every later layer. With learned depth the camera path is about ten times less accurate, the point cloud is stretched (it reaches about 5 m deep, against about 4 m with sensor depth, matching the 1.34x bias), measured areas grow three to four times (more than the 1.8x the distance bias alone would give, because the scale also shifts between frames and smears the surface), and the same object is counted again: the chair is followed for 23 frames with sensor depth but only 10 with Depth Anything. The top-down map makes the difference visible: sensor depth gives patchy coverage with real holes, learned depth one smeared fan. None of these numbers has an independent physical reference yet (Task53), so they show consistency between depth sources, not accuracy.

### Throughput against the 1 frame per second floor

The owner ruled on 7 October 2026 that anything slower than 1 frame per second is not worth using. The same Depth Anything run, all on the MasterPC CPU (Ryzen 9 9950X), from `metadata/timing.json`:

| Part | Seconds for 30 frames | Per frame |
|---|---|---|
| Tracking (CPU odometry) | 14.7 | 0.49 s |
| Depth (Depth Anything V2 Metric Small) | 7.9 | 0.26 s |
| Objects (YOLO26x) | 6.4 | 0.21 s |
| Mapping (grid footprint) | 1.5 | 0.05 s |
| Surface | 0.4 | 0.01 s |
| **Processing, one layer after another** | **30.9** | **1.03 s (0.97 fps)** |
| Model loading, once per run | 7.6 | — |
| Visual export | about 8 | — |

End to end, including loading, visual export and scoring, the run took 48.6 s: 0.62 fps (0.80 fps with Kinect depth, which needs no model). So on this CPU the pipeline sits just under the floor. Every layer alone is faster than 1 fps; tracking is the slowest at about 2 fps. Running depth and objects on the GPU, or letting layers overlap on different frames, would put the desktop pipeline above the floor. The phone is slower than this desktop and is the real test (Task57).

## Interactive run report

`--report-pages`, or `python -B -m tools.demos.run_report <run-folder>` afterwards, writes six offline single-file pages to `<run-folder>-report/`, in the same style as `demo_outputs/`. They read only the run's saved files and `output/scores.json`; the sealed run is not changed.

| Page | What it shows | Error graph against true answers |
|---|---|---|
| `00_overview.html` | Each layer's status, method, reason and frames per second; controls; processing and end-to-end speed against the 1 frame per second floor; headline errors | — |
| `01_depth.html` | Frame slider: colour, predicted depth, the recording's sensor depth and the absolute error, on fixed scales | Relative error (AbsRel) and RMSE per frame; error by true distance; each frame's predicted/sensor distance ratio (does the size change from frame to frame?) and the error a perfect per-frame scale and shift would leave |
| `02_camera.html` | 3D view of the estimated and measured camera paths | Camera position error per frame, with its RMSE |
| `03_surface.html` | 3D points in the colour of their source pixels, with camera positions | No surface reference for TUM. Instead, a self-consistency check: how far each frame's surface sits from an earlier frame's along the view, with the run's own camera path, per frame and for frames 1, 5, 10, 20 and 29 apart. A surface shown several times along the view gives a gap that grows with frame separation. |
| `04_map.html` | Top-down maps and the measurements table | None yet: no surveyed reference |
| `05_objects.html` | Frame slider with detector boxes; provisional identities | None yet: no independent inventory |

Pages show at most 60 evenly spaced frames and 150,000 points; each page says when it samples. The error numbers come from the scorer: when the recording has `depth.txt`, the command line now also scores depth (raw metres against the sensor, per frame and by 0-1, 1-2 and 2-4 m bands), alongside the camera path. Depth scoring happens after predictions are sealed, like tracking, so no method sees the sensor depth unless it is a labelled reference control. Check a report offline with `python -B -m tools.demos.screenshot --pages <report-folder> --out <folder>`.

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
