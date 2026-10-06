# ViaSight ZoneSure: phone video checks of road work zones (commercial)

**Take-away:** ZoneSure is the nearest commercial product aimed at the same objects as this project: cones, signs and barrels at road works. A phone mounted on a vehicle windscreen films a drive through the work zone. Cloud AI then checks the layout against the US work-zone rules and flags problems such as wrong cone spacing or missing signs. It films from a vehicle, not on foot, and publishes nothing about 3D models, measurement accuracy or how it avoids counting a cone twice.

Checked on 5 October 2026 from the company website, its Play Store listing and a news interview. Nothing was installed or tested. Part of the [end-to-end product research](../README.md).

## At a glance

| Question | Answer |
|---|---|
| Type | Commercial app plus cloud service |
| Company | ViaSight, Kansas City, USA. Founded early 2025 by Zikomo Fields (CEO) and Mayura Gunarathne. |
| Input | Smartphone video recorded while driving through a work zone, phone on the windscreen |
| Output | A punch list of issues with GPS locations, condition scores, confidence levels, AI remarks, annotated images and an audit-ready report. Faces and number plates are blurred. |
| What it checks | Lane markings, signs, cones, barrels and other traffic control devices, against the US Manual on Uniform Traffic Control Devices (MUTCD). The founder names cone spacing, missing signs, and cones knocked over or moved by weather. |
| Where it runs | Phone records; analysis in the cloud |
| Works on Android without a laser sensor | Yes, on the Google Play Store as "Zone Sure" |
| Measures in metres | Not published. Checking cone spacing implies some distance estimate, but the method and accuracy are not stated. |
| Counts each object once | Not published |
| 3D model or VR view | None published |
| Cost | Not published |
| Customers | Pilot with a toll road operator in Portugal; work with Minnesota DOT and SRF Consulting on a related study; in talks with a large US transport company |

## Evidence and limits

- All capability claims come from the company and an interview. No accuracy figures are published.
- Built around US rules. UK street works follow the Safety at Street Works and Road Works code and Chapter 8 of the Traffic Signs Manual, which set different layouts and spacings.
- Drive-through only. FYLD's workers film on foot around a single dig site, which is a different camera path and scale.
- Checking spacing between cones needs each cone located, and each counted once along the taper. ViaSight may solve the same duplicate problem this repository works on, but it doesn't say how.

## Compared with this repository

| This repository's layer | Does ZoneSure cover it? |
|---|---|
| 1. Capture | Yes, phone video, vehicle-mounted |
| 2–4. Depth, camera position, 3D model | Not published |
| 5. Objects | Detects work-zone devices and checks rules. Counting method not published. |

ZoneSure is evidence that phone video checks of street-works layouts are commercially credible. It is also the product FYLD is most likely to compare this work against.

## Questions to ask ViaSight

1. Does it work from video filmed on foot?
2. Does it count each device once, and how?
3. How does it measure cone spacing, and how accurate is it in metres?
4. Can the rules be swapped for the UK street works code?
5. Is analysis on the phone or in the cloud, and what does it cost per inspection?

## Sources

- [ViaSight website](https://www.viasight.ai/)
- [Startland News interview, February 2026](https://www.startlandnews.com/2026/02/zikomo-fields-viasight/)
- [Zone Sure on Google Play](https://play.google.com/store/apps/details?id=ai.viasight.zonesure)
- [SRF Consulting podcast on lane-keeping in work zones](https://www.srfconsulting.com/unboxed-ep-0001/)
