# Scaniverse: phone-made 3D scenes you can walk round in a VR headset (commercial, free)

**Take-away:** Scaniverse is the clearest existing route from a phone capture to a real 3D scene viewed in a VR headset, as opposed to Depth Surge 3D's flat video with added depth. It builds a photo-realistic 3D model (a Gaussian splat) entirely on an Android phone or iPhone. Niantic's free Quest app shows it in a headset. It is a viewing tool: it has no object detection or counting, and measuring is limited.

Checked on 5 October 2026 from Niantic's product pages and community forum. Nothing was installed or tested. Part of the [end-to-end product research](../README.md).

## At a glance

| Question | Answer |
|---|---|
| Type | Free app from Niantic Spatial, with enterprise features |
| Input | Live phone camera on iOS or Android. The wider platform also takes 360 camera and drone data. |
| Output | Gaussian splats (a photo-realistic 3D format made of many small coloured blobs) and meshes. Exports include Niantic's open-source SPZ splat format, which Niantic says cuts file size by 90%, plus USDZ. |
| Where it runs | On the phone. No upload or internet needed to make the model. |
| Works from an Android phone with no laser sensor | Yes |
| Measures in metres | Partly. Models can be shown at real size. Shared web links have no measuring tool; Niantic's forum suggests measuring in Blender or CloudCompare with 1 unit set to 1 m. Accuracy is not published. |
| Counts each object once | No |
| Viewable in VR | Yes. "Into the Scaniverse" is a free Meta Quest app, also available as a WebXR site in the Quest browser. |
| Cost | Free app; enterprise terms not published |

## Why it matters for this project

The root README suggests a possible later output: viewing the measured site and its objects in a phone VR headset. Scaniverse shows the viewing side is already solved for realistic scenes. A phone capture becomes a 3D scene that a person can look round in a headset.

What it doesn't do is the part this project is about:

- It has no labelled objects, counts or positions.
- Its sizes are not checked against a reference.
- Its splats look right but are not guaranteed to be the right shape. A splat can look correct from the captured viewpoints and still be the wrong size, so it is not a measuring record.

A combined output would place this project's counted objects, with sizes and positions, as labels inside a Scaniverse-style splat scene.

## Evidence and limits

- No published accuracy in metres.
- Splats are built for appearance, not geometry. Surface-accurate variants exist in research (2D Gaussian splatting), but Scaniverse doesn't say which it uses.
- On-phone processing limits scene size and detail, and depends on the phone.
- Enterprise data terms need checking before any utility site data is used.

## Compared with this repository

| This repository's layer | Does Scaniverse cover it? |
|---|---|
| 1. Capture | Yes, on Android without a laser sensor |
| 2–3. Depth and camera position | Internal, not exposed |
| 4. 3D model | Yes, realistic appearance; measurement accuracy unknown |
| 5. Objects | No |
| Possible VR viewer | Yes, on Meta Quest |

## How to test it here

1. Scan one indoor scene on the Redmi with Scaniverse, and time how long processing takes on the phone.
2. Export the model and measure five known distances in CloudCompare against a tape-measured reference.
3. View it in the Quest app, if a headset is available, to judge whether a splat scene is a useful base for showing counted objects.

## Sources

- [Niantic Spatial capture (Scaniverse) product page](https://www.nianticspatial.com/products/capture)
- [Scaniverse arrives on Android](https://radiancefields.com/scaniverse-arrives-on-android)
- [Into the Scaniverse native app for Meta Quest](https://nianticlabs.com/news/into-the-scaniverse-native-app-meta-quest)
- [Four ways to explore 3D Gaussian splats on Meta Quest](https://api.scaniverse.com/news/four-ways-to-explore-3d-gaussian-splats-on-meta-quest)
- [Scaniverse community: measuring and scale](https://community.scaniverse.com/t/how-do-you-figure-the-scale-of-a-scan/959)
- [Scaniverse community: no measurement tool in web links](https://community.scaniverse.com/t/can-the-measurement-tool-be-used-when-opening-a-scan-via-a-web-browser-link/906)
