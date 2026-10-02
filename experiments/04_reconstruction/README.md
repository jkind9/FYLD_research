# Experiment 04: reconstruction of observed surfaces

## The piece we are testing

Can depth observations and camera poses produce an accurate three-dimensional representation of visible surfaces? This piece owns reconstruction. It does not estimate depth, solve camera movement or produce a bird's-eye map.

Begin with supplied poses and depth from datasets. This needs neither a phone nor an implementation of Experiments 01–03. See the [dataset plan](../datasets/README.md). Replace one input at a time later to measure how upstream errors affect surfaces.

## Development dataset and reference

Develop against acquired clean ICL-NUIM living-room trajectory 2 at `data/icl_nuim/trajectory2/`. Use colour/depth pairs and supplied poses with matching IDs 1 through 880; preserve raw frame 0 but exclude it from supplied-pose runs because it has no pose. All 881 raw colour/depth pairs decoded successfully, and all 880 pose rows contain finite values. [Inspection receipt](../../data/icl_nuim/inspection.json).

Evaluate against the separately acquired `data/icl_nuim/reference_surface/living-room.ply`, containing 9,982,296 reference points with colour and normals. Keep it outside reconstruction inputs. Calibration, depth units and the fixed conversion between trajectory and surface coordinates are recorded in [conventions.json](../../data/icl_nuim/conventions.json). Task 03 must independently verify this geometry contract before scoring. Data acquisition is complete; the adapter and reconstruction methods have not yet run. No additional public dataset is needed for the initial reconstruction control.

## Input and output agreement

Input contains timestamped depth in metres, validity masks, calibration and corresponding camera poses. Optional colour needs an explicit registration relationship. Poses map from the depth camera into a declared world frame and carry segment and frame identifiers. Keep unresolved tracking segments in separate reconstructions; reject fusion across origins until a recorded transform establishes the relationship. Record timestamp interpolation and rejected associations.

Output is an observed surface representation, initially a point cloud, with a fused surface or mesh as a separate comparison. Coordinates retain frame and units. Store observation provenance and processing settings. Absent surfaces remain unobserved; an attractive closed mesh does not establish measured coverage.

Known gravity or site references can be supplied. Neither follows merely because a model looks level in a viewer.

## Proposed steps and comparisons

1. Verify transforms and depth conversion with known-geometry fixtures.
2. Use ICL-NUIM living-room depth and supplied poses after checking calibration and formats.
3. Compare direct accumulation with surface fusion, recording filtering and resolution choices.
4. Evaluate against the living-room reference surface, kept outside reconstruction inputs.
5. Repeat with estimated poses and alternative depth while preserving comparable observations.

The office scene lacks the same explicit reference surface. It cannot silently substitute for the living-room geometry evaluation.

## Measurements, failures and decision

Measure surface-distance error and missing coverage separately. Report representation size, runtime, memory and changes across repeated inputs. Declare how comparable surfaces are selected; a small accurate patch cannot stand for successful reconstruction of the whole scene.

Include pose discontinuities, invalid depth, inconsistent units, contradictory observations and interruption. Decide whether processing can resume from stored inputs or must restart. Label partial results.

Agree numeric accuracy and coverage limits from the intended output before acceptance runs. Choose representations by measured geometry and consumer needs.

## Dependencies and first tasks

Use a desktop CPU control first. Candidate versions observed in the archived environment are Python3.12.10, NumPy2.4.2, Pillow12.3.0, Open3D0.19.0 and pytest9.0.2; SciPy1.17.1 can support geometry evaluation, while Matplotlib3.10.8 and psutil7.2.2 support reporting. These observations are not a verified clean-install lock. Pin a fresh working environment before running comparisons. No CUDA, learned weights or phone is needed.

The [official Open3D0.19 RGB-D integration tutorial](https://www.open3d.org/docs/0.19.0/tutorial/pipelines/rgbd_integration.html) supplies the volume-integration reference. Verify its extrinsic direction against the shared contract; do not copy settings without provenance. Direct accumulation is the simpler first control. ICL's separate reference surface is essential for measuring surface accuracy.

[Task 02: standard references](../../task_list/closed/02_verify_standard_tracking_and_reconstruction_refere.md) is complete. Begin with [Task 03: geometry contracts](../../task_list/open/03_define_observation_and_pose_contracts_with_known_g.md); [Task 04: reference-pose reconstruction](../../task_list/open/04_evaluate_reconstruction_with_supplied_depth_and_po.md) establishes the surface control. [Task 05: tracking](../../task_list/open/05_evaluate_tracking_with_supplied_benchmark_depth.md) can proceed in parallel after task 03. Compare supplied versus estimated poses only after both independent controls exist.

## Research and reuse

[ICL-NUIM](../../research/sources/18_icl_nuim.md) supplies controlled surface comparison. [Open3D](../../research/sources/13_open3d_rgbd.md) informs fusion choices. [COLMAP](../../research/sources/11_colmap.md) offers an image-based comparison whose scale needs separate establishment. [Construction capture guidance](../../research/sources/19_construction_capture_guidance.md) explains viewpoint limitations.

Promote a surface agreement when Experiment 05 consumes it alongside synthetic geometry independently of the reconstructor. Check dataset, tool and weight permissions separately. No result is claimed here. See the [experiment guide](../README.md).
