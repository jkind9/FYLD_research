# SkyeBrowse: measured 3D models from ordinary video (commercial, hosted)

**Take-away:** SkyeBrowse is the closest commercial match to this repository's layers 1–4 on the hosted route. Upload an ordinary video from an Android phone, iPhone, 360 camera or drone, and its cloud service returns a 3D model you can measure in. It doesn't detect or count site objects as far as published. Its accuracy figures are sales claims and should be checked against a known reference before relying on them.

Checked on 5 October 2026 from the company website and news coverage. Nothing was uploaded or tested. Part of the [end-to-end product research](../README.md).

## At a glance

| Question | Answer |
|---|---|
| Type | Commercial cloud service with web viewer |
| Input | `.mp4` or `.mov` video from phones, body cameras, action cameras, 360 cameras or drones. Optional drone flight logs improve location. |
| Output | A navigable 3D model as a point cloud or mesh with real-world X, Y, Z coordinates. The web viewer allows walking through, zooming and measuring. |
| Where it runs | Cloud. Around 1 minute of processing per minute of video (vendor figure). |
| Works from an Android phone with no laser sensor | Yes |
| Measures in metres | Yes. Vendor-stated accuracy depends on the plan: Standard 2–6 inches (5–15 cm), Premium 0.25 inch, Premium Advanced 0.1 inch. No ground control points are needed. |
| Counts each object once | No for site objects. Product names include "Crowd Counter", "Interior AI" and "3D AI", but no published detail on object detection or counting. "AI moving object removal" is offered on a higher tier. |
| Viewable in VR | Mentioned as a feature on the company site; not checked |
| Cost | Free tier with unlimited uploads (two models processing at a time). Commercial models about $24.99 each, with a $5 first-model offer at the time of checking. |
| Status | Established; used in public safety, drones and construction |

## How it works

SkyeBrowse calls its method videogrammetry: building 3D from the frames of a continuous video instead of from separate photos. The cloud service:

1. Takes thousands of frames from the video.
2. Works out the camera path from how the frames overlap.
3. Builds the 3D structure, then adds colour and detail from the frames.

Guidance is to film in steady, overlapping passes. The company says one person with a phone can capture a building interior in under 15 minutes.

## Evidence and limits

- Accuracy tiers are the company's own claims. The "court-admissible" and "survey-grade" wording comes from marketing. The page doesn't explain how real-world scale is set from phone video without a reference.
- No published object detection or counting for site objects.
- Data goes to SkyeBrowse's cloud. For utility sites, data location and retention terms need checking.

## Compared with this repository

| This repository's layer | Does SkyeBrowse cover it? |
|---|---|
| 1. Capture | Yes, any ordinary video |
| 2. Depth | Internal, not exposed |
| 3. Camera position | Internal, not exposed |
| 4. 3D model and measurement | Yes |
| 5. Objects | No |

If SkyeBrowse's accuracy holds up on a worksite, there is little reason to build a separate hosted measurement pipeline. This repository's layer-by-layer pipeline would then be most useful as the reference that SkyeBrowse is scored against, and as the 3D base that object counting builds on.

## How to test it here

1. Film one scene that has a reference, such as a room measured with a tape or a laser measure. Upload the video to the free tier.
2. Measure five known distances in the SkyeBrowse viewer and compare them with the reference.
3. Export the model if allowed. Score it the same way as this repository's layer 4 point surface (average distance to the reference model).

## Sources

- [SkyeBrowse: 3D walkthrough from video](https://www.skyebrowse.com/news/posts/3d-walkthrough)
- [SkyeBrowse vs Polycam (vendor comparison)](https://www.skyebrowse.com/news/posts/skyebrowse-vs-polycam)
- [SkyeBrowse speed and quality upgrades (DroneXL)](https://dronexl.co/2024/06/30/skyebrowse-3d-modeling-speed-quality)
- [SkyeBrowse in public safety (Pilot Institute)](https://pilotinstitute.com/skyebrowse-public-safety-drones/)
