---
id: "42"
title: Examine the ARCore toolkit for capture, depth and telemetry
status: open
priority: HIGH
type: decision
approval_status: proposed; investigation only; phone runs stay with tasks 08 and 24
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - research/arcore/README.md
  - research/README.md
docs:
  - research/arcore/README.md
  - experiments/01_camera_capture_delivery/README.md
baseline_metric:
  source: experiments/01_camera_capture_delivery/README.md
  field: ARCore features examined against project needs
  baseline_value: "0 ARCore features inventoried or recorded on either phone; 2 of 2 test phones listed by Google with Depth API support"
  target: "Every listed ARCore and Android sensor feature mapped to a project layer, with availability on both phones recorded where a phone check is approved"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task 42 — Examine the ARCore toolkit for capture, depth and telemetry

## In plain English

ARCore is Google's augmented-reality toolkit for Android phones. It already tracks where the phone is, estimates depth and records sensor data, and it has outdoor features that use Google's Street View data. Both test phones are listed by Google as supporting it. This task makes a full inventory of what ARCore and the phone's other sensors can supply, and works out which of those could replace or check parts of the project's own pipeline. It is investigation only: it produces a written inventory and a plan for a phone recording, not a finished app.

## What

Write `research/arcore/README.md`: one row per feature, saying what it gives, its units, timing and accuracy notes, whether it works offline, which layer it serves, and whether it is listed as available on the Galaxy S23 and Redmi Note 11 Pro. Features to examine:

**Camera and tracking (layers 1 and 3)**
- Camera pose per frame and tracking state, including the reason tracking failed (too dark, too fast, too few features).
- Camera intrinsics for the image and texture streams, camera configuration choice (resolution, frame rate, depth sensor use) and per-frame image metadata such as exposure and sensor timestamp.
- [Shared camera access](https://developers.google.com/ar/develop/java/camera-sharing): full-resolution Camera2 frames while ARCore tracks, instead of the default 640×480 tracking image.
- Feature point cloud: sparse 3D points with confidence and stable IDs.

**Depth (layer 2)**
- [Depth API](https://developers.google.com/ar/develop/depth) (smoothed) and [Raw Depth](https://developers.google.com/ar/develop/java/depth/raw-depth) with per-pixel confidence; whether the phone uses a depth sensor or depth from motion; usable range.
- [Geospatial Depth](https://developers.google.com/codelabs/arcore-scene-semantics-geospatial-depth): phone depth combined with Street View building and terrain geometry, documented up to 65 m outdoors.

**Scene structure and outdoor features (layers 4 and 5)**
- Planes: horizontal and vertical, with outline polygons (rough floor area on site).
- Hit testing: casting a ray into the scene to measure distances, as phone measuring apps do.
- [Scene Semantics](https://developers.google.com/codelabs/arcore-scene-semantics-geospatial-depth): a per-pixel outdoor label (sky, building, tree, road, sidewalk, vehicle, person and others, 12 at launch) with confidence. This could separate road surface from people and vehicles.
- [Streetscape Geometry](https://developers.googleblog.com/en/build-transformative-augmented-reality-experiences-with-new-arcore-and-geospatial-features/): building and terrain meshes within about 100 m of the phone.
- Augmented Images: detecting a known printed marker, which could act as a scale reference of known size.

**Location and revisits (identifying a site)**
- [Geospatial API](https://developers.google.com/ar/develop/geospatial): latitude, longitude, altitude and heading with accuracy estimates, using Google's visual positioning where Street View coverage exists.
- Anchors and Cloud Anchors: saving a location and finding it again on a later visit.

**Recording and playback (layer 1)**
- [Recording and Playback](https://developers.google.com/ar/develop/recording-and-playback): one MP4 with camera, IMU and ARCore data, replayable on a desktop, including custom data tracks for extra telemetry.

**Phone telemetry outside ARCore**
- Android sensors: accelerometer, gyroscope, magnetometer, barometer (height changes), and GNSS location, including raw GNSS measurements where the phone exposes them. Record rates and timestamps relative to camera frames.

For each feature, note which project layer it could replace (for example, ARCore pose as the on-phone stand-in for layer 3), which it could check, and what it cannot do (for example, confidence values are not calibrated error bars).

## Why

The project is building its own depth and camera tracking, while ARCore already supplies both on the two test phones. ARCore's outdoor features (Geospatial, Scene Semantics, Streetscape Geometry, Geospatial Depth) bear directly on outdoor street works, site location and range beyond the current 4 m depth limit. None of this has been examined in one place. Knowing what the phone gives for free decides what the capture app records and which of the project's own layers matter most.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Room-mapping platform research covering ARCore, ARKit and RoomPlan exists | task 37 | research README section G | task_list/open/37_research_arcore_arkit_and_roomplan_mapping.md:51 |
| ARCore pose, Raw Depth and anchors already summarised from primary sources | research README section G | task 37 | research/README.md:163 |
| ARCore Recording and Playback and native pose already reviewed for SLAM use | Android SLAM review | layer 3 | research/orb_slam/android/README.md:19 |
| ARCore Raw Depth source note exists | research source notes | layer 2 | research/sources/06_arcore_raw_depth.md:3 |
| Phone capability checks have an owner | task 08 | layer 1 | task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:51 |
| App build and packaging have an owner | task 24 | layer 1 | task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:36 |

Split with task 37: this task owns the feature-by-feature ARCore and Android sensor inventory and the plan for an ARCore recording. Task 37 keeps the cross-platform comparison with ARKit and RoomPlan and the transferable mapping techniques.

Steps:
1. Inventory every feature above from Google's primary documentation, with links and documentation dates.
2. Map each feature to the layer it serves, and whether it works offline.
3. Check Google's device list and documentation for each feature's support on both phones. Mark anything not yet confirmed on the handset as unknown.
4. Propose a short ARCore recording on each phone, to be carried out under tasks 08 and 24: which features to turn on, what to save, and a capability report to produce.
5. Note how ADVIO, which contains ARCore paths with an independent reference (see task 41), could score ARCore's tracking before any phone recording.

## Hyperparameters

hyperparameters n/a: research and inventory only; no experiment is run in this task.

## Invariants and recovery

invariants n/a: research and planning only. Any phone recording or app change happens under tasks 08 and 24 with their own scope.

## Verification

- **Contract check:** every feature row links a primary Google or Android source and states its documentation date. Phone availability is either taken from a dated official listing or marked unknown. No vendor accuracy or range figure is presented as a project measurement.
- **Before/after:** before, 0 ARCore features inventoried; both phones are on Google's Depth API list (checked 4 October 2026). After, the full inventory with layer mapping and a recording plan handed to tasks 08 and 24.

tests n/a: research document only; no code.

## Receipts

| field | value |
|---|---|
| closing commit | (fill in) |
| files changed | (fill in) |
| test | (fill in) |
| before / after | (fill in) |
| result | (fill in) |

Notes / caveats / follow-ups:

-
