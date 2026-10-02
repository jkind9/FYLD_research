# Six independent scene-mapping experiments

The objective is to find out whether a phone capture can produce a repeatable, measurable representation of the visible work area and identify distinct objects across repeated views. We will build and evaluate six pieces independently, then connect them. The first prototype is preserved in [the Task 00 archive](../archive/task00_prototype/README.md).

The six pieces are camera capture and delivery, stereo depth, camera tracking, 3D reconstruction, bird's-eye mapping and object recognition with persistent counting. Capture and delivery share one experiment because the first practical question is whether useful camera observations can reach an experiment. Its camera tests and network tests still have separate measurements.

## The pieces

| Piece and plan | Takes in | Produces | Independent test |
|---|---|---|---|
| [01: Camera capture and delivery](01_camera_capture_delivery/README.md) | Selected phone, camera settings and recording request | Images with camera identity, capture times and available calibration; delivery records | Inspect saved phone captures; replay known files to test delivery separately |
| [02: Stereo depth](02_stereo_depth/README.md) | Paired images and stereo calibration | Depth in metres, valid-pixel mask and confidence if the method supplies it | Recorded calibrated stereo and reference disparities; no phone or tracking required |
| [03: Camera tracking](03_tracking/README.md) | Images, calibration, time and optional depth or motion-sensor readings | Camera positions and orientations, tracking status | Dataset observations with held-out reference poses; no stereo implementation required |
| [04: 3D reconstruction](04_reconstruction/README.md) | Depth observations, camera poses and calibration | Observed scene geometry and observation evidence | Supplied depth and exact poses against a separate reference surface; no tracker required |
| [05: Bird's-eye mapping](05_birds_eye_mapping/README.md) | Geometry, a declared reference plane and selected region | Top-down views, heights, observed coverage and defined area measurements | Analytic shapes with known heights, boundaries and holes; no reconstruction required |
| [06: Object recognition and counting](06_object_recognition/README.md) | Images, optional depth/poses and prior object observations | Object labels, persistent identities, supporting views and distinct counts | Checked detections and known poses first; separately labelled revisits and inventory |

The [dataset guide](datasets/README.md) explains suitable recorded inputs, references, permissions and download status. The [research reading guide](../research/sources/README.md) explains the underlying methods.

## Development data coverage

Each experiment README names its initial inputs and independent reference. Current coverage on 2 October 2026 is:

| Experiment | Development inputs | Independent reference | Readiness |
| --- | --- | --- | --- |
| Camera capture and delivery | S23/Redmi recordings for capture; acquired Middlebury images for file delivery replay | Actual device capability/timing records; original file hashes and frame identifiers for delivery | Phone recordings and replay tests remain part of implementation |
| Stereo depth | Acquired Middlebury quarter-resolution training pairs | Published disparity, masks and scene calibration | Data ready; choose development/held-out scenes before tuning |
| Camera tracking | Acquired TUM Freiburg1 xyz colour/depth | Motion-capture poses kept outside tracker inputs | Development data ready; selected Freiburg1 desk remains to be acquired before held-out evaluation |
| Reconstruction | Acquired ICL living-room trajectory 2 depth/poses, matched IDs 1..880 | Separate acquired living-room reference point cloud | Data ready; task 03 must verify geometry before scoring |
| Bird's-eye mapping | Independently specified known shapes; acquired ICL point cloud as a later complex input | Expected dimensions, heights, areas and observation masks from fixture definitions | Known-shape fixtures must be created with the first tests |
| Object recognition and counting | Existing images for geometry association controls; labelled object walkthrough still needed | Manually checked masks, persistent object identities and inventory | No task-specific recognition or revisit benchmark has been acquired |

No KITTI download is needed to begin these independent stages. Recorded car-mounted observations cannot resolve phone camera access or replace exact expected map measurements. Outdoor validation and a later comparison using stereo depth inside tracking still need suitable data; neither is claimed complete by this initial development coverage.

## Independent does not mean isolated forever

Each piece must accept saved observations or fixtures. Its first tests substitute known inputs for the earlier piece. We then replace those inputs with measured outputs from another piece and check what changes.

For example, test reconstruction first with supplied depth and reference poses. Replace the poses with estimates to measure tracking's contribution to surface error. Replace supplied depth with stereo predictions to measure depth's contribution. Do not change both at once in the first comparison.

Map projection starts from independently specified geometry. Its expected areas and heights must come from the fixture definition, not be generated by the projection code under test.

No downstream stage is required to succeed before an upstream experiment can report a useful failure. A handset that cannot expose a usable camera pair is a capture result. It is not evidence that the stereo algorithm fails.

## Where a piece runs is a separate choice

Stereo depth can run on a phone, a desktop or a hosted backend while accepting the same kind of observation. Recorded processing is the first control; live streaming is an additional condition. Hosting and HTTP are not required to evaluate stereo depth.

Possible later assemblies include:

- Phone capture → phone depth → desktop or backend tracking and reconstruction.
- Phone capture → delivered stereo images → backend depth, tracking and reconstruction.
- Phone-provided depth and poses → reconstruction and map projection.

These are proposed combinations. None has been validated on the available phones. Comparing placement must include delivery delay and data volume as well as algorithm processing time.

## Available devices

| Device reported by the user | What is established | First checks |
|---|---|---|
| Samsung S23 | Available; installing a test app is acceptable | Record exact model identifier, operating-system version, exposed physical cameras and simultaneous stream support |
| Redmi Note 11 Pro | Available; installing a test app is acceptable | Confirm exact model and 4G/5G variant before choosing an implementation; inspect exposed cameras and calibration |

Multiple rear lenses do not establish simultaneous access to a useful stereo pair. Android's [multi-camera documentation](https://developer.android.com/media/camera/camera2/multi-camera) makes support dependent on the device implementation and camera grouping. The first experiment records actual support on both devices. Strong internet is helpful but does not establish capture timing, sustained upload performance or camera calibration.

The planned phone test app packages Python with [python-for-android](https://github.com/kivy/python-for-android). A native camera API bridge handles camera-specific access. [Experiment 01](01_camera_capture_delivery/README.md) records that approach, the supplied streaming leads and the Linux build-environment prerequisite. Selecting the tool does not establish camera support or a completed APK.

## The information pieces must exchange

The following are proposed requirements for a small shared data format. Choose the concrete schema when implementing the first producer and consumer; do not create a general framework in advance.

| Information | Required meaning |
|---|---|
| Observation identity | Session, frame and camera identifiers; source file or original observation retained |
| Capture time | Units, clock source and relationship between cameras declared; keep it distinct from arrival time |
| Camera geometry | Intrinsics for the actual image size/crop, distortion convention and relative camera pose where needed |
| Depth | Metres and declared definition, such as camera-axis distance; invalid values and valid mask explicit |
| Camera poses | Transform direction, coordinate axes, scale source, tracked/lost status and segment/world-frame identifiers explicit; unresolved origins cannot be fused together |
| Geometry | Coordinate frame, units and observed support; unseen space is not treated as empty |
| Map reference | Plane origin/axes, source of vertical direction, grid size and selected surface statistic recorded |

Confidence is method-specific unless calibrated and tested. A generic confidence number must not silently become a probability of correctness. Missing calibration or uncertain scale must be reported rather than guessed.

## What each experiment records

Every run should retain its input selection, configuration, implementation version, outputs, timings and failures. Report published paper results separately from local measurements. Retain unknown regions through depth, geometry and projection.

Start with controls and a simple baseline. Test normal inputs, boundaries and a failure condition. Keep evaluation references out of the estimated method's inputs. Separate development examples from held-out evaluation scenes before tuning; a dataset labelled training can still supply withheld local evaluation scenes.

Numeric product acceptance limits, processing budgets and tunable settings have not been selected. Agree and record them before running a comparison. A completed experiment may conclude that a method is unsuitable; completion is an evidenced decision, not a requirement for a positive result.

Only promote code to [shared src](../src/README.md) after its behaviour is established and another experiment needs it. Until then, implementation belongs with the experiment that owns the question.

## Build order

Experiment 01 starts with device inspection and a small recording. Experiments 02–05 can proceed without that capture using [dataset inputs and fixtures](datasets/README.md). Tracking and reconstruction are separate experiments even if a chosen library provides both; record which outputs and references are used for each question.

Connect pieces after their independent controls pass. Then run matched-input comparisons and, finally, permitted site captures. Indoor benchmark success is preparation for a site trial, not a site-performance result.

## Current status

### Priority work: reference data and geometric controls

The main implementation starts with a verified observation/pose contract and a reconstruction control with supplied poses. Without them, a distorted map cannot be attributed to tracking versus reconstruction. Check phone-camera feasibility alongside this work, without blocking the dataset control. Object association begins with checked observations and known poses, then adds detector predictions and estimated geometry separately.

| Task | Purpose | Dependency |
|---|---|---|
| [02: research and standard reference data](../task_list/closed/02_verify_standard_tracking_and_reconstruction_refere.md) | Complete: formats/permissions checked, both ICL assets acquired, held-out TUM sequence selected | None |
| [03: known-geometry contracts](../task_list/open/03_define_observation_and_pose_contracts_with_known_g.md) | Define units, timestamps, transforms and segments; establish independent controls | 02 |
| [04: supplied-pose reconstruction](../task_list/open/04_evaluate_reconstruction_with_supplied_depth_and_po.md) | Measure fusion/surface error without a tracker | 03 |
| [05: supplied-depth tracking](../task_list/open/05_evaluate_tracking_with_supplied_benchmark_depth.md) | Measure camera movement error without stereo estimation | 03 |
| [08: phone feasibility](../task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md) | Inspect both phones and retain capture/calibration evidence | None; run alongside geometry work |
| [09: recognition and persistent counting](../task_list/open/09_evaluate_scene_object_recognition_and_persistent_counting.md) | Test labels, identities and revisit counts independently | 03 for 3D association; 04 for reconstructed-map integration |

Task 04 is the first reconstruction implementation after task 03. Task 05 can proceed independently after task 03. Task 08 is an early device check; task 09 can begin label and fixture planning before reconstruction, but map integration follows task 04. These remain open plans. Actual test paths, tunable settings and numerical acceptance limits must be recorded before code or experiment runs.

These are plans, not newly executed experiments. Task 00 supplied literature and preliminary desktop results. Its integrated implementation is archived; final code review, package validation, coverage measurement and post-fix reruns were unfinished when the objective changed. Any reused code must be validated in its new owning experiment.
