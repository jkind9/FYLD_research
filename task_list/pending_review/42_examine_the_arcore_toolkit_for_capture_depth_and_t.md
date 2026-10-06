---
id: "42"
title: Examine the ARCore toolkit for capture, depth and telemetry
status: pending_review
priority: HIGH
type: decision
approval_status: research only; no ARCore phone run or app change authorised; any recording needs a separate owner decision and scoped task
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: 2026-10-05 PASS
files:
  - task_list/pending_review/42_examine_the_arcore_toolkit_for_capture_depth_and_t.md
  - research/arcore/README.md
  - research/README.md
  - experiments/01_camera_capture_delivery/README.md
  - task_list/README.md
docs:
  - research/arcore/README.md
  - research/README.md
  - experiments/01_camera_capture_delivery/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/01_camera_capture_delivery/README.md
  field: ARCore and Android sensor features mapped to project needs and exact device evidence
  baseline_value: "0 of 24 listed features have a current consolidated feature-by-feature inventory; the Galaxy S23 and Redmi Note 11 Pro product families are listed for Depth API; exact handset runtime checks are absent"
  target: "24 of 24 planned feature rows have primary-source links, layer, output/units, timing/accuracy limits, network/offline needs and dated device-list/runtime status; no phone run"
created: 2026-10-04
last_updated: 2026-10-05
superseded_by: null
---

# Task 42 — Examine the ARCore toolkit for capture, depth and telemetry

## In plain English

ARCore is Google's augmented-reality toolkit for Android phones. It can track a phone and provide depth on supported devices. Some outdoor features use Google's Street View data. Google's current public list includes the Galaxy S23 family and Redmi Note 11 Pro product names with Depth API support. The project's exact handset variants and runtime support still need checking. The Samsung handset is not confirmed available, and the received Redmi report APK did not include ARCore. This task inventories the tools and sensors, then proposes a recording plan for separate owner review. It does not build or run an app.

## What

Write `research/arcore/README.md`: one row per feature, saying what it gives, its units, timing and accuracy notes, whether it works offline, which layer it serves, whether Google's device table enumerates that feature, the product-family device-list result where the table applies, the exact handset SKU status, and runtime status. Distinguish “listed”, “not listed”, “not enumerated by this table”, “not applicable”, and “not tested”; “not listed” does not mean unsupported.

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

The acceptance inventory has exactly these 24 row names, so the denominator cannot change between reviews:

1. Camera pose, tracking state and failure reason.
2. Camera intrinsics for CPU image and GPU texture.
3. Camera configuration: resolution, frame-rate range and depth-sensor use.
4. Per-frame image metadata: exposure and sensor timestamp.
5. Shared Camera / Camera2 image access.
6. Feature point cloud, confidence and IDs.
7. Full Depth API image.
8. Raw Depth image and confidence.
9. Geospatial Depth.
10. Plane detection and outlines.
11. Hit testing.
12. Scene Semantics labels and confidence.
13. Streetscape Geometry.
14. Augmented Images.
15. Geospatial location, heading and accuracy estimates.
16. Local anchors.
17. Cloud Anchors.
18. Recording and Playback of camera/sensor data.
19. Custom recording tracks.
20. Accelerometer.
21. Gyroscope.
22. Magnetometer.
23. Barometer.
24. GNSS location and raw measurements.

For each feature, note which project layer it could replace (for example, ARCore pose as the on-phone stand-in for layer 3), which it could check, and what it cannot do (for example, confidence values are not calibrated error bars).

## Why

The project is building its own depth and camera tracking. ARCore may supply alternative inputs on supported phones, but support must be checked for the exact model and at runtime. Its outdoor features (Geospatial, Scene Semantics, Streetscape Geometry, Geospatial Depth) may help with street works, site location and range beyond the current 4 m depth limit. This task compares their documented outputs with the project's needs; it does not establish phone performance or accuracy.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Room-mapping platform research covering ARCore, ARKit and RoomPlan exists | Task37 | research README section G | task_list/pending_review/37_research_arcore_arkit_and_roomplan_mapping.md:51 |
| Phone product-family evidence exists, but does not confirm a hardware SKU or runtime ARCore support | Task08 | Task42 device-status rows | task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:48 |
| ARCore pose, Raw Depth and anchors already summarised from primary sources | research README section G | Task42 source inventory | research/README.md:153-155 |
| ARCore Recording and Playback and native pose already reviewed for SLAM use | Android SLAM review | layer 3 | research/orb_slam/android/README.md:19 |
| ARCore Raw Depth source note exists | research source notes | layer 2 | research/sources/06_arcore_raw_depth.md:3 |
| Phone capability checks have an owner | task 08 | layer 1 | task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:51 |
| A smoke-app build and export path exists; it does not provide an ARCore recorder | Task24 | build handoff only | task_list/pending_review/24_recover_and_reproduce_android_apk_build_inside_cap.md:40 |

Split with Task37: this task owns the feature-by-feature ARCore and Android sensor inventory and a proposal for a possible ARCore recording. Task37 keeps the cross-platform comparison with ARKit and RoomPlan and the transferable mapping techniques. The existing research index and Task37 record now distinguish the listed Redmi product names from the exact `2201116TG` code and its untested runtime support.

Steps:
1. Inventory every feature above from Google's primary documentation, with links and documentation dates.
2. Map each feature to the layer it serves, and whether it works offline.
3. Check Google's current device list feature flags. Record the Galaxy S23 and Redmi Note 11 Pro product-name entries separately from handset access. The list does not identify code `2201116TG` directly. For every inventory row, say whether the public device table enumerates that feature; use “not listed” only when the table has a comparable device entry that omits it, and never treat that status alone as proof of incompatibility. Record the APK's missing ARCore feature and mark runtime availability unverified for both phones.
4. Write a proposed recording plan with exact features, saved fields and capability checks. Tasks08/24 do not currently include an ARCore recorder; any recording requires a separate owner decision, provision of the SDK, and a separately scoped or revised task. This plan authorises no device run or app change.
5. Describe the limits of ADVIO (see Task41): its supplied trajectory is estimated from inertial data and fixation points. It can support comparisons against that dataset trajectory, but it is not surveyed physical position truth and cannot establish absolute tracking accuracy. Keep any such comparison labelled by its reference source and limitations.

## Hyperparameters

hyperparameters n/a: research and inventory only; no experiment is run in this task.

## Invariants and recovery

invariants n/a: research and planning only. A future phone recording needs owner approval, the ARCore SDK and a separately reviewed task or authorized scope change; Tasks08/24 do not currently provide an ARCore recorder.

## Verification

- **Contract check:** the 24 named feature rows below link primary sources and state check date, output/units, timing and accuracy limits, layer, network need, whether the public device table enumerates the feature, applicable product-family/SKU status, and runtime status. “Not listed” is not used as a synonym for “unsupported”. No unverified handset capability or vendor figure is presented as a project measurement.
- **Before/after:** before, 0 of 24 features have a consolidated comparison. Google's list includes the Galaxy S23 and Redmi Note 11 Pro product names for Depth API; it does not identify the exact Redmi code, and neither handset has a runtime ARCore test. After, all 24 rows and a conditional recording proposal are ready for owner review. No phone run is part of this task.

tests n/a: research document only; no code.

## Receipts

| field | value |
|---|---|
| closing commit | None; repository baseline is `684468d01c1f32b98b531c2922bd409583716150`; changes remain uncommitted |
| files changed | `research/arcore/README.md`, `research/README.md`, `experiments/01_camera_capture_delivery/README.md`, `task_list/README.md`, this task record |
| test | Research-only contract check: 24 named feature rows link official sources and report output/units, network needs, limits, layer and support status. `git diff --check` and task-plan lint pass. No phone run or code test applies. |
| before / after | Before: 0 of 24 rows in one feature-by-feature inventory; product-family Depth API flags existed but exact SKU and runtime status were not established. After: 24 rows, dated official source list, separate family/SKU/runtime labels and conditional recording proposal; no project phone measurement. |
| result | Documentation implemented. ADVIO is identified as an estimated-path comparison, not surveyed truth. Independent Claude review of the pinned source set and owner decisions remain outstanding. |

Notes / caveats / follow-ups:

- The recording proposal is not approval to modify or run an app. Task08's current APK omits ARCore; Task24 owns only its print-only smoke-app build/export route.
- Google lists the Galaxy S23 models and Redmi Note 11 Pro product names for Depth API. It does not identify code `2201116TG`. Runtime support, phone accuracy, frame rate, power and worksite suitability were not measured.
- The four platform/source READMEs and this receipt need fixed-snapshot Claude validation. No owner-controlled phone access or SDK decision was assumed.

still open because the completed source inventory needs fixed-snapshot Claude validation before this research task can leave review.

### Plan review history

- 2026-10-05 FAIL: initial plan described ADVIO's estimated trajectory as independent reference truth, failed to state the limits of Google's feature table and omitted Task42 itself from file scope. Corrected those claims and paths; final fresh plan review returned PASS.
