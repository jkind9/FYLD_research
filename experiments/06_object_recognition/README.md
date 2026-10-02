# Experiment 06: object recognition and persistent counting

This experiment asks what objects are visible and which observations refer to the same object. Its output is a labelled inventory with supporting views, locations where geometry permits, and unresolved matches. Looking away and returning should not automatically increase the count.

## Start independently

Begin with manually checked detections or pixel masks and supplied depth/camera poses. This tests association without detector or tracker error. Task 03 verifies geometry; task 04 supplies the later measured reconstruction. Existing images can exercise projection, but acquired datasets are not a labelled worksite inventory benchmark.

Select a small labelled walkthrough with target classes, persistent identities, revisits and independent dimensions. Separate development and held-out scenes before tuning. Test stationary objects first, then moved equipment and identical neighbours. Scene/activity classification is a separate output.

## Recognition and geometry work together

Recognise objects in selected images, locate valid observations using depth and poses, then associate them with persistent records. Keep location, extent, appearance, original views, frame/segment identity and uncertainty. Correct locations when map poses change. Missing depth cannot supply an invented metric location.

Geometry can improve recognition across views. Recognition can also help tracking exclude moving features. Evaluate these directions separately; excluding a person from static geometry does not erase the inventory observation.

## Research comparisons

| Reference | Contribution | Comparison |
|---|---|---|
| [Monocular SLAM Supported Object Recognition](https://arxiv.org/html/1506.01732v1), 2015 | Map-based proposals and recognition across views | Multi-view design with modern recognition; no established phone performance |
| [Visual SLAM for Dynamic Environments](https://pmc.ncbi.nlm.nih.gov/articles/PMC9571647/), 2022 | ORB-SLAM3, detection and optical flow | Recognition helping tracking; not persistent inventory evidence |
| [SemanticFusion](https://arxiv.org/abs/1609.05130) | Image labels fused into a dense map | Fixed-class multi-view labels |
| [ConceptGraphs](https://concept-graphs.github.io/) / [ConceptFusion](https://concept-fusion.github.io/) | Semantic 3D records and text queries | Desktop references before edge simplification |
| [YOLO-World](https://github.com/AILab-CVC/YOLO-World) | Text-defined detection | Compare with a small model for chosen classes |
| [MobileSAM](https://github.com/ChaoningZhang/MobileSAM) | Lightweight prompted masks | Boundaries/overlap; masks alone supply neither names nor persistent IDs |
| [OpenMask3D](https://github.com/OpenMask3D/openmask3d) | Point-cloud and posed-image object segmentation | Offline reconstruction-based comparison |

The supplied [ScienceDirect link](https://www.sciencedirect.com/org/science/article/pii/S1546221823007208) returned an access error during the 2 October review. Its identity and claims remain unverified; obtain its title or DOI before adopting it. Paper results are not locally reproduced results. Check code and checkpoint permissions before company use.

The [edge review](../../research/edge_products/README.md) connects site measurements and counting. The [construction progress reference](../../research/sources/20_construction_orthographic_progress.md) concerns activity interpretation with planned building information, a separate question from identifying individual utility-site objects.

## Deployment and measurements

Compare phone-only, portable local edge computing and a backend. Begin with selected-frame recognition and compact records. Measure geometry updates, recognition latency, stalls, memory, temperature and energy together; component rates cannot establish complete-system throughput.

Measure labels, identity, location and inventory separately. Count duplicates, misses, incorrect merges and unresolved matches. Include looking away, occlusion, another return route, moved objects, tracking loss, restart/replay and map correction. A correct total can hide compensating errors.

Before implementation, select scoped contract tests and review state/persistence. Before runs, stamp vocabulary, model, splits, sampling, thresholds and scoring settings. Product limits remain unselected. [Task 09](../../task_list/open/09_evaluate_scene_object_recognition_and_persistent_counting.md) owns the work; no recognition or counting method has run.
