# Learning: 3D from a phone walkthrough, explained from the start

This folder teaches the ideas behind this repository to someone who has not worked on SLAM or 3D vision before. Each chapter explains one part of the problem from first principles, shows what this project measured, and points to the code and notes that hold the detail. It is built from the project's research notes (`research/`) and experiment results (`experiments/`) as of 14 October 2026.

## The problem in one paragraph

A person walks through a worksite filming with a phone. We want two things from that video: a 3D model of the site in real metres, so we can read off sizes and areas, and a count of distinct objects, where an object that leaves the view and comes back is counted once. A video is a stack of flat pictures. To turn it into 3D we need to know, for every frame, **how far away each pixel is** (depth) and **where the camera was** (camera pose). With both, every pixel lands at one point in a shared 3D space. Everything else (surfaces, top-down maps, areas, object positions) is built on that.

## The pipeline at a glance

```text
 phone video ──► 1 capture ──► 2 depth per pixel ──► 3 camera pose per frame
                                       │                       │
                                       └──────────┬────────────┘
                                                  ▼
                                      4 surfaces in metres (fusion)
                                                  │
                         ┌────────────────────────┴───────────────┐
                         ▼                                        ▼
            5 top-down map, sizes, areas           6 objects: detect, place in 3D,
                                                     match across views, count
```

The project builds and tests each box on its own with known inputs, then connects them. The repository code that runs all six in order is `src/walkthrough/`.

## Reading order

| # | Chapter | You will learn |
|---|---|---|
| 0 | [Glossary](00_glossary.md) | Every term used in these chapters, in one place |
| — | [How the methods fit together](methods_inputs_and_outputs.md) | SLAM against structure from motion, where surfaces and objects come from, what kind of thing each name is (toolkit, system, algorithm or model), and every method's inputs and outputs. Read it after chapter 0 and come back to it often. |
| 1 | [Cameras, images and coordinates](01_cameras_and_coordinates.md) | The pinhole camera, calibration, poses, and how a pixel becomes a 3D point |
| 2 | [Depth](02_depth.md) | Four ways to get depth, metric against relative depth, and why learned depth's size drifts |
| 3 | [Camera tracking and SLAM](03_camera_tracking_and_slam.md) | Odometry, drift, maps, loop closure, motion sensors, and why our first tracker failed |
| 4 | [Structure from motion](04_structure_from_motion.md) | Features, matching, triangulation, bundle adjustment, and why photos alone have no size |
| 5 | [Dense surfaces](05_dense_surfaces.md) | Fusion, multi-view stereo, learned depth sized to tracked points, and how surfaces are scored |
| 6 | [Maps and measurement](06_maps_and_measurement.md) | Ground planes, height grids, unknown against empty, and area |
| 7 | [Objects and counting](07_objects_and_counting.md) | Detection, segmentation, 3D placement, identity across views |
| 8 | [The phone](08_phone_and_deployment.md) | What ARCore gives, the 1 frame per second floor, and the design the results point to |
| 9 | [Measuring accuracy](09_evaluation_and_datasets.md) | Benchmarks, reference data, and the scores used everywhere in the project |
| 10 | [What we have learned so far](10_findings_timeline.md) | The project's main results in the order they were found, with numbers |
| 11 | [Inside ARCore](11_inside_arcore.md) | How the phone's tracker works: IMU and camera fusion, the MSCKF filter, mapping and loop closure, depth from motion, and what the Redmi measured |
| 12 | [Rebuilding ARCore from open parts](12_rebuilding_arcore.md) | Replacing ARCore with open-source parts: camera and motion-sensor clocks, exposure and rolling shutter, the project's raw recorder, measuring the time offset, calibration and choosing a tracker |

Chapters 1 to 4 are the core of SLAM. If you only have an hour, read 1, 3, 4 and 10.

## How to use the chapters

- Each chapter stands on its own and defines its terms the first time they appear.
- "Project result" boxes quote measured numbers from this repository; they link to the experiment that produced them.
- "Try it" sections give commands you can run from the repository root. Most need the recorded TUM or ICL data on disk (see chapter 9) and one of the project's Python environments.
- Published numbers from papers are the authors' claims. Numbers measured here say so.

## Where to go next

- The [research folder](../research/README.md) holds the papers and source notes behind each chapter, grouped by topic.
- The [lecture slides](../research/3d_vision_fundamentals/README.md) from a university 3D vision course cover the maths in more depth; each chapter names the matching lecture.
- The [experiments folder](../experiments/README.md) holds the code, settings and full result tables.
