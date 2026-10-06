# Apple RoomPlan: measuring a room and placing objects, all on the phone

**Take-away:** RoomPlan is the only finished product found that measures a space and places separate objects in 3D, entirely on the phone. It shows the whole idea works as a product. It needs an iPhone or iPad with a laser depth sensor (LiDAR), works indoors, and knows only 16 furniture and appliance types. It cannot run on the Android phones in this project.

Checked on 5 October 2026 from Apple's developer page and Apple's machine learning research article. Nothing was run. Part of the [end-to-end product research](../README.md). The [RoomPlan source note](../../sources/07_apple_roomplan.md) covers the developer interface and export format; this note covers how it finds and tracks objects.

## At a glance

| Question | Answer |
|---|---|
| Type | Apple developer interface (Swift), built into iOS |
| Input | Live camera and laser depth sensor on a supported iPhone or iPad |
| Output | A simplified 3D room model: walls, doors, windows and openings with sizes, plus a labelled 3D box for each detected object. Exports as USD or USDZ. |
| Where it runs | Entirely on the phone. Apple says no processing happens on its servers. |
| Works from an Android phone with no laser sensor | No |
| Measures in metres | Yes. Room parts come with sizes. Apple reports 95% precision and recall for walls and windows, 90% for doors. |
| Counts each object once | Yes, within one scan. Boxes are tracked over time during the scan, then checked again over the whole room at the end. |
| Viewable in VR | USDZ files open in Apple's AR viewer. Headset viewing not checked. |
| Licence | Apple developer terms; not open source |
| Status | Released 2022, part of current iOS |

## How it finds objects and counts them once

Apple's research article describes two parts running together:

1. **Room layout:** separate networks find walls, openings, doors and windows.
2. **3D object detection:**
   - A **local detector** looks at the 3D points gathered so far in the current view and draws 3D boxes round objects. These boxes are "aggregated, tracked over time" and shown live to the user. This is how one sofa stays one sofa as the camera moves.
   - A **global detector** runs once over the whole finished room.
   - A **fusion step** joins both results and moves boxes so they don't cut through walls.

Apple reports 91% average precision and 90% recall for objects across the 16 types, counting a box as correct when it overlaps the true box by at least 30%. The 16 types are: storage, sofa, table, chair, bed, refrigerator, oven, stove, dishwasher, washer/dryer, fireplace, sink, bathtub, toilet, stairs and TV. A typical scan takes about five minutes and covers rooms up to 15 m × 15 m. The models are compressed to run on Apple's neural chip.

## Evidence and limits

- The accuracy figures are Apple's own, on Apple's own data. They were not independently checked here.
- Indoors only, up to about 15 m across. Worksites, roads and outdoor light are out of scope.
- Fixed list of 16 types. Cones, barriers and signs are not among them, and Apple offers no way to add types.
- Within one scan only. There is no return visit on a different day.
- Room parts are simplified into flat shapes, so irregular surfaces are not measured as they are.

## Compared with this repository

| This repository's layer | Does RoomPlan cover it? |
|---|---|
| 1. Capture | Yes, but only on laser-equipped Apple devices |
| 2. Depth | From the laser sensor, not learned from images |
| 3. Camera position | Yes, from Apple's ARKit |
| 4. 3D model | A simplified room model with sizes |
| 5. Objects | Yes: 3D boxes, tracked so each object appears once |

RoomPlan is a working example of the target design: depth plus camera position on the phone, objects placed in 3D, duplicates avoided by tracking in 3D. The open question for this project is whether the same can be done on an Android phone without a laser sensor, using ARCore depth instead, and outdoors.

## How to test it here

Neither test phone can run RoomPlan. If a laser-equipped iPhone becomes available, scan one indoor room. Then compare RoomPlan's object count and room sizes with a tape-measured reference and with this repository's results on the same room.

## Sources

- [Apple RoomPlan developer overview](https://developer.apple.com/augmented-reality/roomplan)
- [Apple machine learning research: 3D parametric room representation with RoomPlan](https://machinelearning.apple.com/research/roomplan)
- [RoomPlan source note in this repository](../../sources/07_apple_roomplan.md)
