# Android on the phone: ARCore, Lightship and the ARCore ML sample

**Take-away:** No finished Android app was found that measures a site and counts each object once. The pieces exist and run on ordinary Android phones without a laser sensor:

- **Google ARCore** gives camera position and depth.
- **Niantic Lightship** gives a live 3D mesh and object boxes.
- **Google's ARCore ML sample** shows how to pin each detected object at a 3D position.

What nobody provides is the rule that decides whether a new sighting is an object already seen or a new one, and evidence that the measurements are accurate. Those two gaps are what this repository's layer 5 and its scoring work on.

Checked on 5 October 2026 from developer documentation and code repositories. Nothing was built or run on a phone. Part of the [end-to-end product research](../README.md).

## At a glance

| Piece | What it gives on the phone | Android, no laser sensor | Open source | Status |
|---|---|---|---|---|
| [Google ARCore](https://developers.google.com/ar/develop/machine-learning) | Camera position and orientation for each frame, depth images, outdoor pixel labels (road, building and so on), location with heading | Yes, on [supported devices](https://developers.google.com/ar/devices) | No (free to use) | Maintained |
| [Niantic Lightship ARDK / NSDK](https://lightship.dev/docs/ardk/3.3/how-to/ar/object_detection) | A live 3D mesh on phones without a laser sensor; pixel labels (ground, sky, building and more); 2D boxes round objects from 200+ types | Yes | No | Rebranded to Niantic Spatial SDK; Unity first, with Kotlin and Swift listed |
| [ARCore ML sample](https://github.com/googlesamples/arcore-ml-sample) | Detects objects with ML Kit in camera frames and places an AR anchor (a fixed 3D point) on each one, with a label | Yes | Yes, Apache 2.0, Kotlin | **Archived by Google on 19 April 2026**; read-only |
| [Ar-Object-Detection](https://github.com/Kashif-E/Ar-Object-Detection) | Same idea with a custom TensorFlow Lite detector | Yes | Yes | Hobby project |
| [RTAB-Map](https://github.com/introlab/rtabmap) | 3D mapping with drift correction, mesh and point cloud export. Has an Android build in its repository. | Yes, uses ARCore | Yes, BSD | Maintained. A current Play Store listing was not confirmed. |

## How a working on-phone counter would fit together

1. **Camera position and depth:** ARCore, every frame.
2. **Detection:** a small detector running on the phone's AI chip. Lightship's built-in boxes, ML Kit, or a custom model such as RF-DETR Nano or YOLO26 nano.
3. **Place each detection in 3D:** take the depth inside the box (or a hit test at the box centre, as the ARCore ML sample does) and the camera position, giving a 3D point in metres.
4. **Same or new object:** compare the new 3D point and its appearance with objects already found. **No product or sample found does this step.** The ARCore ML sample adds a new anchor for every detection.
5. **Show the count:** labels pinned in the live camera view, and a running count.
6. **Measure the site:** Lightship's mesh or RTAB-Map's map for rough areas, uploaded later for a full hosted model.

## Evidence and limits

- None of these pieces publishes accuracy for object positions on a phone. ARCore depth quality is device-dependent and gets worse with distance.
- The ARCore ML sample's default classifier knows only 5 coarse categories, and the repository is archived. It is a starting point, not a dependency.
- Lightship's object boxes are 2D. Placing them in 3D is left to the developer.
- Lightship and ARCore are free to use but not open source. Their terms need checking before anything ships.
- Battery, heat and sustained speed on the Redmi are untested for all of these.

## Compared with this repository

| This repository's layer | Covered on the phone by |
|---|---|
| 1. Capture | ARCore recording, or the phone camera |
| 2. Depth | ARCore depth |
| 3. Camera position | ARCore tracking; RTAB-Map adds drift correction |
| 4. 3D model | Lightship mesh or RTAB-Map, rough only |
| 5. Objects | Detection and 3D placement are available; **the "same or new" decision and counting are missing** |

## How to test it here

1. Build the ARCore ML sample on the Redmi as it is. Walk past three objects twice and count how many anchors it creates. The expected result is roughly one anchor per detection, which shows the size of the duplicate problem.
2. Add this repository's "same or new" rule from layer 5 to the same app, and repeat.
3. Record frame rate, battery and phone temperature over a 5-minute walk.

## Sources

- [ARCore: using camera images for machine learning](https://developers.google.com/ar/develop/java/machine-learning)
- [ARCore supported devices](https://developers.google.com/ar/devices)
- [ARCore ML sample repository](https://github.com/googlesamples/arcore-ml-sample)
- [Lightship object detection how-to](https://lightship.dev/docs/ardk/3.3/how-to/ar/object_detection)
- [Lightship ARDK 3.3 release notes](https://www.lightship.dev/docs/ardk/release_notes/release3.3/)
- [Niantic Spatial SDK overview](https://www.nianticspatial.com/docs/nsdk/?source=lightship&platform=unity)
- [Ar-Object-Detection repository](https://github.com/Kashif-E/Ar-Object-Detection)
- [RTAB-Map repository](https://github.com/introlab/rtabmap)
