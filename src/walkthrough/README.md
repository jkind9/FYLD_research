# Six-step recorded walkthrough

This is the canonical runner for a recorded walkthrough. It calls six steps in order:

1. Capture and input validation.
2. Depth.
3. Camera tracking.
4. Surface reconstruction.
5. Mapping, dimensions and area.
6. Object recognition and distinct counting.

Each adapter imports a method from its owning experiment. Experiments still run independently. Earlier five-layer diagrams grouped reconstruction and mapping. They are separate execution steps here.

`pipeline.run` contains six direct calls to the layer run functions, with numbered comments matching this list. It decides which layers can run. Each layer file has one `run` entry that imports its owning method, records timing and exports predictions to `output/predictions/<step>.json`. It handles expected failures in that same file. Input validation happens in step 1. After step 6, the orchestrator exports whole-run results, records prediction hashes, calls the separate `validation.py` and exports scores. Final publication is the last action. Small input conversions stay in their layer files; there is no general execution wrapper.

## Current availability

The phone reader validates original image hashes, calibration metadata and capture clocks. It does not invent missing depth or poses. Real metric depth remains unavailable until Task54 supplies its reviewed method. Mapping, dimensions and defined area remain unavailable until Task55 supplies its method. A normal run therefore stops at depth today. This is an explicit incomplete result, not a successful measurement.

Camera tracking calls the existing tracking kernel and CPU backend with calibrated arrays. Its frozen input contract requires valid depth strictly below 4 metres. The adapter refuses unsupported depth instead of changing the valid mask. It also refuses mixed cameras or clocks. The test-provider pinhole boundary requires unrotated images on the full pre-correction grid, zero skew and explicitly zero distortion. Cropped, resized or corrected phone calibration needs an owning-method conversion and tests. It is refused here instead of assuming how the phone mapped sensor pixels to image pixels.

Surface reconstruction imports `reconstruct_metric` from experiment 04. It uses already-metric depth and estimated camera-to-world poses. It saves every valid observed point in separate shards. Benchmark raw-depth conversion, reference poses and model alignment remain in the historical controls. A display sample is never used for quantitative geometry.

Object recognition imports the existing detector, box-depth localisation and Task46 association function. A checkpoint must already exist and pass the detector owner's checks. The runner uses CPU inference. Supply counting settings explicitly from their reviewed owner; the root package introduces no numerical defaults. Identities and counts stay separate for each world and tracking segment. `whole_site_distinct_count` is always unavailable because this method cannot resolve identity across origins.

Segmentation and classical appearance descriptors are disabled by default. Select `segmentation` or `appearance` explicitly to save their diagnostic evidence. Masks stay in original-grid files, not in a session-sized array list. These optional outputs do not change the simple counting decisions. Learned appearance remains an independently runnable experimental component; the root adapter does not initialise its GPU model.

## Run recorded input

From the repository root:

```powershell
python -B -m src.walkthrough.cli --report <camera-report.json> --bundle <export-folder> --run-root <output-folder>
```

The command currently returns exit code 2 with a named Task54 unavailable result. `--partial` permits independent later steps to run when their own dependencies exist. `--steps capture` requests a capture-only diagnostic. Every result still shows all six slots. A partial or failed result cannot verify as a completed six-step run.

Optional flags are `--checkpoint`, `--max-distance-m`, `--ambiguity-margin-m`, `--segmentation rectangle|grabcut|canny`, and `--appearance`. Supplying them does not supply the missing depth or area algorithms. Existing frozen experiment commands and historical runs are unchanged.

The Python boundary is small:

```python
from pathlib import Path
from src.walkthrough.config import Configuration
from src.walkthrough.pipeline import run

result = run(
    Configuration(
        run_root=Path("outputs/walkthrough"),
        repo=Path.cwd(),
        report=Path("camera-report.json"),
        bundle=Path("phone-export"),
    )
)
print(result.complete, result.steps)
```

`config.py` contains immutable method configuration. It has no reference files or truth labels. `records.py` describes whole-run and step status. Shared calibration and pose records stay in `experiments.shared.contracts`.

## Scoring and publication

`validation.ScoreRequest` carries a separate reference loader and scorer options. Prediction stages never receive it. The runner saves predictions and records their file hashes before calling a loader. Tracking analysis imports experiment 03's validation area. Surface analysis imports experiment 04's validation area and requires compatible reference origins. The scorer reads immutable records or read-only geometry shards. The runner checks every prediction hash again after scoring and finishes the shared `Run` only when all six steps completed.

The detection, segmentation, appearance and identity experiments expose their existing scorers through dedicated validation packages. `validation.score_compatible` dispatches those legacy callable schemas without copying mathematics. It is a standalone compatibility helper; callers must supply the owning scorer's existing positional schema. Complete physical survey adapters for object and site measurements remain Task56 work. Requests for those adapters currently return an explicit unavailable result. Disabled optional components do not import their validation code or load references.

Prediction time, optional diagnostic evidence and scoring have separate timing labels in the shared ledger. Nested timings describe their own scopes and must not be added together as total time. These software controls do not establish total workload latency, memory acceptance or sustained edge performance.

Each fresh run retains original capture bytes, configuration, environment, dirty source snapshots and artifact hashes. Source snapshots include this package as well as experiments. No import starts a run, creates files, loads a model or downloads data.

## Failure, restart and memory ownership

A missing method is `unavailable`; rejected input or an expected execution error is `failed`; dependent steps are `skipped`. A stopped result stays inspectable with failed run status and no complete manifest. An unexpected error propagates and the shared run wrapper records it. Scoring errors or changed predictions prevent publication. Never retry into an old directory. A retry creates a fresh run with its own origin namespace.

Capture retains the shared reader's encoded image bytes only during input validation and saving. Downstream steps pass metadata and file handles. Tracking decodes current/previous RGB-D frames, then releases them; it retains pose/status records. Surface reconstruction writes one full geometry shard at a time. Object recognition decodes one frame at a time and retains proposals and track state, not all session images. Optional masks are files. Actual peak memory still needs measurement in Tasks56/57.

Historical surface recovery now checks the extracted fault-control source. A prior snapshot missing that source, or one with different control code, is explicitly refused. Original run evidence stays untouched.

## Software checks

```powershell
python -B tools/check.py src/walkthrough/tests
```

The fixtures in `tests/providers.py` are deterministic software controls. They are accepted only when `software_control=True`, and never exposed as CLI methods. They test execution order, calibrated coordinates, origin separation, failures, import safety and scoring integrity. They provide no real depth or area method and no physical accuracy evidence. Tasks54/55 supply those methods; Tasks56/57 supply the measured complete and sustained-device evidence.
