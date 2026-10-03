# Geometry validation using supplied depth and camera poses

## What is implemented now

**There is no implemented tracker or depth predictor yet.** The current program takes a dataset's supplied depth and supplied camera positions/orientations. It converts those known inputs into three-dimensional points and checks that our coordinate handling is correct. This supporting experiment checks geometry conventions for both camera pose estimation and surface reconstruction. It is separate from numbered pipeline stages; work task 03 delivered this control.

| Question | Current answer |
|---|---|
| Did the program predict depth from RGB? | No. It decoded the supplied depth PNG into metres. |
| Did it infer camera movement between frames 1, 2 and 3? | No. It read their supplied poses from the dataset's pose table. |
| Did it generate 3D geometry? | Yes. It placed each valid depth pixel in camera coordinates, then in the common world using the supplied pose. |
| Did it fuse the observations into a reconstructed surface? | No. Per-frame points remain separate. Fusion and surface evaluation belong to task 04. |
| Did it measure prediction accuracy? | No. There were no predictions to compare with independent references. |
| What does the tiny projection error mean? | A pixel converted into 3D and projected back lands on its original location. This checks arithmetic consistency, not depth or tracking accuracy. |

## What each stage does and saves

For pixel column `u`, row `v` and supplied camera-axis depth `Z`, the program computes `X=(u-cx)*Z/fx`, `Y=(v-cy)*Z/fy`, and retains `Z`. It then applies the supplied rotation and translation: `point_world = R * point_camera + t`. Nothing in this process estimates the camera pose.

| Stage | Input and operation | Output under `output/<frame-id>/` | What to inspect |
|---|---|---|---|
| Original observation | Copy RGB/depth PNGs and read the exact matching supplied pose | Originals and observation record under `input/<frame-id>/` | Image identity, calibration and pose source |
| Supplied depth in metres | Divide raw PNG depth by 5000; mark invalid pixels | `depth.npy`, `mask.npy` | Depth image and validity mask; visual scale comes from the legend |
| Camera-space points | Convert each valid depth pixel to XYZ using calibration | `camera.npy`, `camera.ply`, `pixels.npy`, `rgb.npy` | Camera-space cloud; `pixels.npy` maps each point to its original row/column |
| Common-world points | Apply that observation's supplied camera-to-world pose | `world.npy`, `world.ply` | World-space cloud, plus the joint scene and supplied-camera views |
| Reference-coordinate points | Apply the fixed publisher conversion, including its reflection | `model.npy`, `model.ply` | Same points in the reference coordinate convention; the word model in this filename does not mean a learned model or fused surface |
| Projection consistency | Project camera-space points back onto their source image | `projection_error.npy` | Horizontal/vertical pixel differences; a numerical consistency check |
| Stage provenance | Record frames, units, transforms, valid count and timing | `stages.json` | Connect each output and debug image to its exact input |

The coordinate-channel images (`camera_x.png`, `world_z.png`, and similar files) show a coordinate value at each original valid pixel. They are diagnostic images, not additional predictions. The review page explains each stage and links its numerical arrays and point clouds. A joint scene view overlays the supplied observations in the same world; a separate camera-position view magnifies their small movement. Both use supplied poses and do not test tracking.

## How to validate a run

1. **Integrity:** require a complete receipt and verify every artifact hash with `experiments.shared.runs.verify_run`. Compare the copied RGB/depth hashes with the selected source files. This proves files were retained correctly.
2. **Geometry meaning:** run the independent analytic tests, including known translations/rotations, signed calibration, invalid depth, reflections and distinct origins. Those checks can expose wrong scale or transform direction.
3. **Per-input consistency:** confirm image dimensions match calibration, point counts match the validity mask, point-to-pixel correspondence is preserved and projection residuals remain below the `1e-10` pixel arithmetic limit. This is not a field accuracy threshold.
4. **Visual diagnosis:** inspect depth, camera/world/reference point views and supplied camera positions. Unexpected flips, axes or gaps guide investigation, but an attractive cloud alone cannot establish accuracy.
5. **Independent accuracy:** [Task 04's nine-frame CPU surface baseline](../04_surface_reconstruction/README.md#implemented-cpu-baseline) now measures distance and whole-reference coverage against the separate surface. Task 05 must estimate poses without reading reference poses, then compare estimates with held-out camera motion. A depth estimator must compare predictions with reference depth. The 30-frame tracking trial now measures camera-motion error independently. Full development and held-out tracking checks remain task 13. Depth-prediction accuracy remains unmeasured.

Saved-data ingestion, geometry conversion, exports and coordinate checks are available here. Surface reconstruction and independent scoring now live in the separate surface experiment. Tracking inference remains unimplemented.

## Implemented geometry control

The clearer review is available locally at [runs/20261002T100227.141579Z_93c31b333549447389d2ba8f941e8f74/review.html](runs/20261002T100227.141579Z_93c31b333549447389d2ba8f941e8f74/review.html). It adds an explanation of every stage, a validation/limits table, the three observations in one coordinate space and the supplied camera positions in millimetres. It replays the original copied inputs for IDs 1, 2 and 3. All 130 artifacts validate; original input files and all numerical depth/point arrays and point-cloud files are unchanged. Processing and export took 50.45 seconds on CPU. The original run remains intact. These local links require the generated files and will not work in a fresh clone.

The first local CPU inspection on 2 October 2026 processed frames 1, 2 and 3. Its run directory is `runs/20261002T094131.010017Z_cdf718bae0c8460584d323b1e47ebac6/`; open its `review.html` to inspect matched stages. All 124 recorded artifacts validate, original inputs match their source hashes, and each frame retains 307,200 valid depth pixels. The recorded processing/export time was 38.03 seconds, mostly visual and point-cloud export. This is an export/control check; surface accuracy has not been scored. Generated runs remain local and are absent from fresh clones.

Task 03 now supplies a CPU-only control that decodes clean ICL depth, applies supplied camera poses and exports every stage. It does not estimate movement. Its shared records preserve image identifiers, calibration, metres, pose direction and separate world/segment origins. ICL image IDs are not timestamps; this adapter records no capture time.

Run from the repository root after installing [control dependencies](../shared/requirements.txt):

```powershell
python -m pip install -r experiments/shared/requirements.txt
python -B tools/check.py -q
python -B -m experiments.geometry_validation.src.run --dataset data/icl_nuim --frame-ids <explicit IDs>
```

Replace `<explicit IDs>` with the ordered frames you intend to inspect. ID 0 is excluded because it has no supplied pose. There is no implicit stride, frame cap, depth clipping or point thinning. Each run has a unique directory under `runs/`; opening `review.html` shows matching stage visuals for each selected input. All GPU runs require the user's permission beforehand. This command only executes the CPU control.

```text
geometry_validation/
  src/
    icl.py       exact-ID loading, calibration and supplied-pose adapter
    control.py   numerical stages and a callable backend agreement
    run.py       selection, orchestration and timing
    scene.py     joint world-point view and supplied camera-position view
    review.py    stage explanations, numerical links and validation limits
  tests/
    test_contracts.py
    test_review.py
  runs/<unique-id>/
    input/<frame-id>/     original RGB/depth PNGs and observation record
    input/dataset/        copied conventions, pose table and decoder inputs
    output/<frame-id>/    depth, mask, pixel correspondence, points and error arrays;
                          camera/world/reference PLYs and stage records
    debug/<frame-id>/     depth/mask, XYZ rasters, 3D previews, projection error;
                          per-image numerical scales
    metadata/             configuration, frames, timing, environment, Git identity,
                          source snapshot, artifact hashes and completion status
    review.html
```

The numerical arrays retain every valid pixel. Preview intensities use the range recorded in each legend; compare raw values rather than gray levels across frames. Black invalid pixels represent unobserved depth. The fixed reference conversion includes a reflection and is kept separate from proper camera poses. Raw inputs and metadata are copied before decoding. A complete run passes `experiments.shared.runs.verify_run`; failure leaves a failed receipt and partial artifacts, while abrupt termination can leave running status. Restart creates a new run.

Mathematics and portable records live in [shared](../shared/README.md). No CUDA framework, HTTP server or model weights enter those records. Later tracking adapters can produce the same pose agreement on a desktop GPU, edge device or hosted backend. Inference timing and data-transfer timing must be measured separately. A supplied-pose control is never an estimated tracker result.

The [publisher calibration](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/codes.html), [TUM depth/pose format](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats) and [SurfReg reference conversion](https://github.com/mp3guy/SurfReg/blob/master/src/SurfReg.cpp) informed this implementation. Tests verify independent analytic coordinates, invalid values, transform direction, reflections, exact IDs, timestamp boundaries, distinct origins and failed/tampered runs. Surface distance and coverage evaluation remain task 04. Dataset readiness flags remain unchanged.

## Where this fits

[Stage 03: camera pose estimation](../03_camera_pose_estimation/README.md) will estimate rotation and translation from observations. [Stage 04: surface reconstruction](../04_surface_reconstruction/README.md) will combine depth observations using supplied or estimated poses. Both reuse these checked geometry conventions and [shared modules](../shared/README.md).

The existing local runs moved here intact from `03_tracking/runs/`. Their metadata and source snapshots retain historical names and paths. Those records describe the code that actually produced the run; relocation does not change its inputs, outputs or hash inventory. New runs use the experiment identity `geometry_validation`.


## Artifact reference labels

Geometry-control figures and saved artifact metadata distinguish observed colour input, clean synthetic ground-truth depth and supplied poses, and evaluated coordinate or arithmetic outputs. Generated point coordinates and projection residuals are evaluated outputs. Their consistency checks do not measure a depth estimator. Stage 03 now has a separate measured camera-estimation trial; full and held-out validation remain task 13.
