# Cup detection inside a recorded 3D scene

This experiment finds a cup in one recorded image, then marks a measured point on it inside the coloured depth cloud. Open the standalone HTML report to rotate, zoom and switch between camera and scene coordinates. It includes the original detection image and the supporting depth pixel.

The owner authorised GPU execution on 3 October 2026, delegated a good pretrained model and a suitable single frame, and required detection review before coordinate mapping. We selected YOLO26x with the initial prediction defaults. This narrower trial does not approve Task16's full protocol. Task13's unfinished tracking work and approved settings remain intact.

## Inputs and method

Freiburg1 xyz RGB `1305031128.547399.png` is paired with depth `1305031128.555639.png`. Both images are 640 by 480. Original input hashes match the existing archive-member record. The detector receives RGB only; its cup box refers to the original image. No manually drawn mask enters the method.

Detection is published and visually inspected first. A separate mapping run opens supplied camera poses as an integration control. It reuses 0.02-second timestamp pairing, registered depth divided by 5000, positive depth below 4 metres, the existing TUM calibration and reference-quaternion normalisation. No camera tracking sequence runs.

The existing calibrated projection creates camera-coordinate points. The supplied camera-to-world transform places the scene cloud and marker in one scene coordinate system. We compare the coordinate-wise median of all valid box pixels with the measured pixel nearest the box centre. Box support and nearest-distance use pixel centres at array indices plus one half. Calibrated backprojection keeps the existing integer pixel indices. Full saved clouds retain the original row/column pair for every point.

The red cross marks a visible surface sample, not the full object's centre. Both methods can include background inside the box. Missing depth produces no invented position. The depth range and valid fraction describe support; they are not statistical uncertainty. Missing supplied poses prevent publication of world coordinates.

## Initial evidence

Open the [interactive cloud with the cup marked](runs/20261003T175727.913404Z_352c685ab5d24f16b31b50aa2cf50fb4/review.html), or the [static preview](runs/20261003T175727.913404Z_352c685ab5d24f16b31b50aa2cf50fb4/review.png). Drag to rotate and scroll to zoom. The red cross is the cup surface measurement. The [original detection image](runs/20261003T173943.511670Z_54a40c632f704b8685e9ed4568355c28/debug/detections.png) was inspected before mapping.

YOLO26x found the visible cup at confidence 0.827695, with box `[381.031, 140.710, 432.334, 210.231]`. Visual inspection confirmed the cup box. Other labels are imperfect, including a game controller labelled remote. This is a visual check, not a scored detection benchmark.

The box contains 3519 pixels and 3439 valid depth measurements spanning 0.8394 to 1.0906 metres. Scene coordinates use motion-capture poses. Independent object-position accuracy and persistent identity recovery still need Tasks17 and 21.

The full cloud contains 230405 measured points. The marked pixel is row 175, column 406, at depth 0.8866 metres. Its camera coordinates are `(0.146078, -0.108925, 0.886600)` metres. Its scene coordinates are `(0.603606, 0.685479, 0.859663)` metres. The box-wide median is 0.050927 metres away from this sample. These are two definitions of observed position, not independently measured errors.

Task27 records immutable run links and final measurements. Revised mapping editions consume the original verified detections; previous editions remain unchanged. `output/cloud.npz` contains all camera/world points, RGB values and source pixels. HTML displays 20000 points selected by the existing integer-linspace sampler. Red markers are kept independently of display sampling.

## Reproduce on this machine

The tested environment uses Windows, Python 3.12, torch 2.11.0+cu128, torchvision 0.26.0+cu128 and an NVIDIA GeForce RTX 5070 Ti. A fresh GPU machine needs the appropriate NVIDIA driver and matching [PyTorch installation](https://pytorch.org/get-started/locally/). Installation on a second machine is unverified. Owner authorisation is required for GPU execution and checkpoint acquisition.

Use a separate environment with the existing GPU-enabled PyTorch:

```powershell
python -m venv --system-site-packages .venv-yolo
.venv-yolo/Scripts/python.exe -m pip install -r experiments/06_object_recognition/pilot/requirements.txt
```

Explicitly acquire the [official YOLO26x checkpoint](https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26x.pt) at ignored `checkpoints/yolo26x.pt`. Our 118667365-byte checkpoint has SHA-256 `9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92`. Acquisition metadata is alongside it. Ultralytics and the checkpoint use AGPL-3.0; deployment licence suitability remains unresolved. The runner requires these exact bytes and the basename `yolo26x.pt` before importing the model loader. Other filenames can trigger model substitution in Ultralytics. Alternate models need a separate recorded protocol.

```powershell
.venv-yolo/Scripts/python.exe -B -m experiments.06_object_recognition.pilot.run detect --device 0
```

Inspect the printed run's `debug/detections.png`. Then map that verified run:

```powershell
.venv-yolo/Scripts/python.exe -B -m experiments.06_object_recognition.pilot.run map --detection-run <detection-run-directory> --reviewed
```

Open the second run's `review.html`. Scene data, Plotly and the annotated image are embedded for offline viewing. `review.png` is a static preview. Each run retains input hashes, configuration, installed environment, source snapshot, stage timing and a verified manifest. Failed or incomplete runs cannot be consumed. Copied parent artifacts must match their pinned detection manifest.

## Controls and limits

Analytic and fake-detector controls cover rotated/translated cameras, fractional boxes, foreground/background depth differences, absent depth/poses, changed inputs, changed parent copies and failed publication. The offline Edge check confirms marker coordinates, camera/world switching, rotation and no network requests. Tests do not run the model.

All 41 controls passed on 3 October 2026. Implementation coverage was 91%; formatting, lint and type checks passed. Code review found a half-pixel selection mismatch, an empty-cloud plotting failure, missing verification of copied detector artifacts and alternate checkpoint loading. Each was fixed and has a regression control. The actual saved HTML also rendered offline in Edge without errors or network requests. Final diff review passed after the checkpoint fixes.

```powershell
python -B -m pytest experiments/06_object_recognition/pilot/tests -p no:cacheprovider --basetemp=outputs/task27_checks_unique
```

Use a fresh temporary path each time. On this machine, Windows sandbox permissions prevent pytest from accessing its restricted temporary folders. Successful tests ran outside that sandbox with output confined to this project.

The GPU measurement includes first-call setup and model warmup. It does not measure steady-state throughput or phone performance. Task28 below checks a camera look-away and return with scene coordinates, but independent identity labels remain future work.

## Task28: bounded cup revisit replay

The accepted replay is [run `20261003T200418.845966Z_f20e5b1de3744f47a850ffa3b3ba396b`](runs/20261003T200418.845966Z_f20e5b1de3744f47a850ffa3b3ba396b/review.html). It uses TUM Freiburg1 desk, timestamped `1305031454.127701` through `1305031472.795640`. The selection contains 60 paired RGB-D frames sampled evenly by integer indices from the 322 paired rows in that span. The local YOLO26x checkpoint is unchanged (SHA-256 `9fdd44a31c504547ffb81d2c6d9e6dac3493c8eaa8b0398d3f43bae6c7003e92`). Inference ran on `cuda:0` in FP32 with Task27's 640-pixel, confidence 0.25, IoU 0.7, batch-one settings. No weights were downloaded.

The same plain white cup is visible at `1305031454.127701` and again at `1305031466.095840`. The sampled interval `1305031457.559685` through `1305031465.795937` is a detector miss interval, not continuous physical absence. RGB review found the cup partly visible at `1305031460.891774`; only frame268 at `1305031463.059810` is independently verified empty in the selected reference. The desk, pen holder, telephone, keyboard and monitor stands show that the camera returned to the same setup. YOLO26x recorded no cup detection in 27 selected frames between those views. The first detection after that gap uses the original clip-local ID `object-0005`. Its observed scene position changed by `[+0.0048, -0.0302, +0.0038] m` (3D distance `0.0308 m`) from the last pre-gap position. The camera moved `0.2211 m` between those views. This supports identity survival under the initial 0.35 m position gate; it does not establish accuracy against independent labels.

The replay retained all 457 detector proposals across the 60 frames. It created 18 clip-local object IDs. Repeated `tv` detections use five IDs, so the viewer shows separate same-class instances as requested. Across every class, 226 proposals have unresolved association records: 17 ambiguous alternatives, 189 outside the position gate, 10 without usable depth, and 10 that could not take an already assigned track. Three of the 19 cup detections are unresolved; none creates a second cup ID. The viewer preserves each box, class, confidence, available camera/world coordinates, assigned ID or unresolved reason in the saved JSON. `output/detections.json` contains the detector proposals and GPU metadata; `output/observations.json` contains the depth/pose positions, IDs and coordinate changes; `metadata/status.json` carries the completed manifest hash `e07af81930e80fe7400c0a0b12b26138c3fea6f7533b1b8137b5186a587267a3`.

The accepted run took 6.68 seconds end to end, including input copying, model setup, inference, projection, association and report generation. Detection took 2.38 seconds; depth, pose, localisation and association took 1.47 seconds. The run is a bounded exploratory measurement, not a steady-state or phone-speed claim. The standalone HTML is 12.2 MB and works offline. A direct Edge check stepped through a visible cup frame, a gap frame and the return. The cup's marker stayed at its last accepted location while detections were missing, then the same ID became visible. The cloud had grown to 19,000 points by the return frame and the camera path had 38 positions. The check reported no external requests or page errors.

The earlier xyz selection was rejected: the cup remains visible in the alleged gap frames `1305031116.143441` and `1305031116.943296`. A first desk clip ending at `1305031465.595599` was also rejected because the model did not detect the return before its endpoint. Those bounded exploratory runs remain in their run folders but are not used for the result above. Task13's tracker settings were not changed, and its full sequence was not run. Task16 remains in `pending_review`; this pilot does not approve its broader protocol. Task17 is closed with provisional agent-reviewed labels, observation/revision contracts and explicit scenario gaps. Task40 owns the proposed independent human masks/identities, physical references and additional captures.


### Task17 RGB review correction

A fresh RGB-only review on3October2026 found the cup partly visible at1305031460.891774 during the27-sample YOLO miss interval. The original1305031463.059810 frame is visually verified with no cup pixels, followed by the same cup at1305031466.095840. Thus the replay contains a physical look-away/return, but the detector miss interval is longer than the proven visibility gap. The object-0005 return and30.8mm coordinate difference are unchanged. [Task17's reference set](../datasets/README.md) supplies separately named provisional labels and the corrected gap. No published run artifact was edited.
