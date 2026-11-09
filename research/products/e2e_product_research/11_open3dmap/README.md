# Open3Dmap: Android capture, cloud COLMAP and a splat portal

Reviewed 9 November 2026. **Recommendation: keep as a capture/workflow reference; do not adopt it as our reconstruction core.** Its intended chain overlaps our Android phone-to-PC setup, but the checked source has incomplete runtime pieces, no demonstrated metric calibration or distinct-object counter, and a noncommercial repository licence. The [SceneView comparison](../../sceneview_open3dmap_review_2026-11-09.md) gives the relative priority.

Main resolved to commit [`f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622`](https://github.com/x4dqn/Open3Dmap/commit/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622), dated 20 August 2025. The GitHub API reported the same date for its last push. A more recent repository `updated_at` timestamp does not establish recent code work. No app, backend or trainer was run. Open3Dmap is a separate project from the `isl-org/Open3D` geometry library we already use.

## Questions that matter to this project

| Question | Checked answer |
|---|---|
| Input | Android ARCore camera captures and a scan-level GPS location. The README also promises IMU and transform exports; the reviewed active capture path does not establish a synchronised sensor recording. |
| Processing | Upload images to Firebase, run COLMAP sparse reconstruction on the server, then train Gaussian splats through Brush. A Gaussian splat is a coloured, transparent 3D blob fitted to reproduce photographs. |
| Output | Portal and PLY export code exist. The README's broader export and federation list contains planned features. |
| Real-world dimensions | No demonstrated ARCore-pose/depth constraint or scale recovery in the reviewed COLMAP path. A GPS tag and a declared scale field do not measure a scene. |
| Objects counted once | No detector, 3D object association or count-validation implementation established in the reviewed flow. |
| Whole chain on the phone | No: reconstruction is cloud-side and advertised browser training requires WebGPU. |
| Licence | Root `LICENSE` states CC BY-NC 4.0. Do not treat it as a permissively licensed codebase for FYLD reuse. |
| Execution status here | Source review only; runtime, dimensional error and device support unknown. |

Sources: [README](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/README.md), [root licence](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/LICENSE).

## What the capture code actually records

The active `ARScanActivity` checks ARCore tracking, attempts capture every 150 ms and scores blur, lighting and focus. It accepts a frame at score 65 or above and uploads at most the first 2,000 accepted images. Its JPEG path applies a fixed 90° rotation. The reviewed `captureFrame` appends image bytes; the upload call passes images with the scan record. It does not pair each accepted image with an exported camera pose, intrinsics, raw depth or IMU sample in that path.

These limits apply to the inspected path, not every possible APK behaviour. They are enough to avoid treating the README's export tree as a verified replacement for our phone session v2. The fixed rotation also cannot replace our per-frame orientation and camera-model handling.

Source: [capture activity](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/Android%20App/Scanner/app/src/main/java/com/openarmap/openarscanner/ui/ARScanActivity.kt).

The Android dependency file uses ARCore 1.41.0 and legacy Sceneform 1.17.1. **This app is not shown using the modern `sceneview/sceneview` SDK.** The two supplied repositories should be evaluated separately. Source: [Android dependencies](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/Android%20App/Scanner/app/build.gradle).

The repository layer adds concurrent image uploads, JPEG size control and scan metadata management. Those are application plumbing, not reconstruction or calibration. Source: [upload repository](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/Android%20App/Scanner/app/src/main/java/com/openarmap/openarscanner/repository/ARScanRepository.kt).

**Project inference:** quality feedback is the useful idea. Our [proposed frame selection](../../../../DESIGN.md) already considers choosing a sharp frame from a run of similar views. A scalar quality score should supplement viewpoint change, overlap and depth freshness. Keeping only the first images would lose later-room coverage on long walks.

## COLMAP: real commands, but also synthetic success

The Python converter runs CPU SIFT feature extraction, exhaustive matching and the sparse mapper with one OPENCV camera. It relaxes several matching and triangulation thresholds. It does not show dense depth fusion or known-ARCore-pose triangulation. No metric pose prior is passed in this converter, so scale would need a separate constraint.

Source: [COLMAP converter](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/open3dmap-web/functions/colmap_converter.py).

The Firebase function checks for COLMAP, but when it is missing calls `createMockCOLMAPResults`. That writes fixed camera/image/point records and a dummy database, uploads them, and returns success with `isMockData: true`. The synthetic branch is labelled; nevertheless, a successful request is not evidence that reconstruction occurred. Any evaluation must check the flag and inspect actual registered cameras and reprojection error.

Source: [cloud function and mock branch](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/open3dmap-web/functions/index.js).

A separate binary manager's `downloadStaticBinary()` is a placeholder that throws. This does not prove that every deployment lacks COLMAP; it means this helper cannot install the required binary as written. Source: [binary manager](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/open3dmap-web/functions/colmap-binary.js).

**Project inference:** use our existing [COLMAP research](../../../structure_from_motion/colmap.md) for geometric work. Our near-term question is metric triangulation using ARCore poses, not an unconstrained sparse model followed by appearance training. Exhaustive matching is also a batch process whose pair count grows quadratically with the image count.

## Browser Brush training: integration code is not a complete runtime

`brush-integration.js` requests a WebGPU adapter and dynamically imports `../brush-wasm-pkg/brush_wasm.js`. It invokes trainer APIs and exports/uploads PLY data. The trainer page invokes training and export functions as well.

However, the complete recursive Git tree at the pinned revision contains no `brush-wasm-pkg/brush_wasm.js`, Rust trainer source, `.wasm` file or advertised `build-brush-wasm.js`. The README's claim that prebuilt WASM artefacts are included is not supported by that tree. A separately provisioned or hosted build may exist, but it was not established here. Therefore the browser trainer is not verified as runnable from this public checkout.

Sources: [integration](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/open3dmap-web/js/brush-integration.js), [trainer page](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/open3dmap-web/brush-trainer.html), [complete tree receipt](https://api.github.com/repos/x4dqn/Open3Dmap/git/trees/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622?recursive=1).

## GPS and SplatJSON

SplatJSON describes a model together with an anchor, local transform, scale, provenance and links between scans. It is useful as a metadata design reference. Its `scale` is supplied metadata, not an algorithm that discovers metres; an anchor is not evidence of accurate alignment of overlapping scans. The document calls the format MIT-licensed, while the repository root is CC BY-NC 4.0. Keep that scope distinction explicit; do not apply the format statement to the whole app.

Source: [SplatJSON specification](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/docs/splatjson-spec.md).

**Project inference:** global location could later index site visits. Our current indoor geometry needs accurate local metres, gravity, frame timestamps and pose revisions. GPS anchoring does not replace any of those, and the inspected converter does not establish scale through GPS alignment.

## Suggested checks, not run

No Open3Dmap execution is recommended before the current refactor. If the capture app is revisited later, inspect one exported session for per-image pose, intrinsics, timestamp and sensor files before installing it as a recording alternative. If the backend is revisited, require real COLMAP output and supply the missing trainer runtime before assessing the end-to-end claim.

For code reuse, resolve the repository's noncommercial terms first or use separately licensed upstream components directly. Our [splat research](../../../gaussian_splatting/README.md) remains deferred by the owner; this repository supplies no new measurement evidence that changes that decision.
