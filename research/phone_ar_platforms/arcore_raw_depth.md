# ARCore Raw Depth

**Take-away:** ARCore Raw Depth is a practical Android route to depth plus confidence. Its missing pixels and capture metadata matter more for measurement than a smooth depth preview.

## Platform and sources

Google ARCore developer documentation and codelab. These are living platform sources, checked on 1 October 2026, rather than one research paper with a fixed benchmark.

- [Official Raw Depth codelab](https://codelabs.developers.google.com/codelabs/arcore-rawdepthapi)
- [Frame API: acquireRawDepthImage16Bits and confidence](https://developers.google.com/ar/reference/java/com/google/ar/core/Frame)
- [Official codelab code](https://github.com/googlecodelabs/arcore-rawdepthapi)

## What it does

ARCore supplies depth estimates during a supported device's camera session. Raw depth avoids the screen-space smoothing used to make depth look complete. Google explains that it can be more geometrically accurate but contain missing data and be less aligned with the camera image.

The depth image and separate confidence image can support geometry analysis. A reconstruction also needs camera intrinsics, frame timing and poses in a documented coordinate convention. Native depth access alone is not a completed site mapper.

## Verified API facts

The **Frame API's acquireRawDepthImage16Bits section** specifies a single 16-bit plane containing millimetres to the camera plane. Invalid pixels have depth zero and confidence zero. It describes typical sizes around **160×120**, with some devices reaching **640×480**, and warns that sizes may change.

These are API descriptions, not measurements of a chosen phone. Runtime, sustained frame rate, energy and outdoor range accuracy have not been checked here. Device support must be established before capture.

## Facts the phone stream relies on (checked 14 October 2026)

Used by `experiments/01_camera_capture_delivery/phone_session_v1.md` (Task87):

- **Rate and newness.** The Frame reference: "Typically there are about 10 updates to the raw depth data per second"; "The depth images between those updates are a 3D reprojection"; a depth image is new when its `Image.getTimestamp()` differs from the previous one.
- **Units.** "Each pixel contains the distance in millimeters to the camera plane"; 0 means no depth; confidence 0-255, and "removing depth pixels below a confidence threshold of half confidence (128) tends to work well".
- **Which camera model.** The official codelab's `DepthData` uses `frame.getCamera().getTextureIntrinsics()` (the GPU texture, not the CPU image), scales x values by `depthWidth / textureWidth` and y values by `depthHeight / textureHeight`, back-projects a pixel as `(d (x - cx) / fx, d (cy - y) / fy, -d)` and places it with `camera.getPose()` of the same frame. On the Redmi the depth image is 160 x 90 (16:9) while the CPU image is 640 x 480 (4:3), so the two fields of view differ and the image intrinsics must not be used for depth.
- **Camera pose.** `Camera.getPose()` is an OpenGL camera pose: +X right, +Y up, looking along -Z, "at the center of exposure of the center row of the image".

## Relevance to a site capture

Our proposed test would export raw depth, confidence, poses, calibration and timestamps together. Check whether successive frames represent new depth or reused estimates. Reject invalid values before fusion. Measure repeatability against independent lengths and report observed coverage alongside area.

Interpolated colours in a renderer are not additional depth observations. Occluded and low-confidence regions should remain unknown. Capture instructions should let a worker decline inaccessible views without treating that as successful full coverage.

No ARCore phone recording or codelab execution occurred in this workspace. Review the [Google developer terms](https://developers.google.com/terms) and the exact sample licence before company integration; SDK access is separate from sample-code permission.

## Questions for the next experiment

1. Which intended phones provide raw depth and confidence reliably?
2. How much valid coverage and measured distance error occur outdoors?
3. Can exported timestamps and poses preserve alignment throughout sustained capture?
