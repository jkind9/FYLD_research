# Grouping surfaces by geometry, colour, texture and embeddings

Research digest, 10 November 2026. Requested alongside a [full RTAB-Map review](../camera_tracking_and_slam/rtabmap.md).

**Assessment:** the proposed grouping is technically relevant and has extensive precedent. It could improve this project's cleanup and object association. It becomes a stronger research direction if persistent surface observations help correct wrong geometry or physical identities under real phone errors. That outcome is a hypothesis, not a result established here.

No grouping method, model or reconstruction was run for this note. Paper performance is author-reported. Proposed designs, failure predictions and experiment choices below are project inferences.

## What the present size filter does

Our adopted cleanup first checks surface support against depth views. It then places points into 2 cm cells, joins occupied cells touching at faces, edges or corners, and keeps the 50 largest components with at least 5,000 points. Those settings removed 122,788 of 676,855 points on one room walk. They do not identify walls, materials or individual objects. [Implementation](../../sitescan/cleanup/pieces.py), [cleanup evidence](README.md#owners-setting-in-the-room-build-task126)

Colour is already retained by fusion and exported with the points. It is not used by `largest_pieces` or the visibility vote. Our room recording also retains images and poses, so a trial can return to source views rather than treating the final coloured cloud as the only evidence. [Fusion stage](../../sitescan/fusion/README.md), [room build](../../src/live/room_build.py)

Size/connectivity filtering has a task limitation: a valid small cone, tool or pipe can be a small disconnected component, while a false sheet can be large or connected to a wall through noise. Point count also depends on sampling and surface coverage. Replacing it with property-aware reasoning is a reasonable experiment even if the method itself is established.

## Four meanings of grouping

| Operation | Question | Example | Does it correct geometry? |
|---|---|---|---|
| Surface segmentation | Which nearby samples form a coherent patch? | Divide a wall, door and floor by orientation and appearance | No, labels alone do not move samples |
| Surface association | Are patches in different views observations of the same physical surface? | Recognize a door after turning back | Supplies possible correction constraints |
| Object assembly | Which surface patches belong to one physical object? | Associate a cone's differently coloured visible sides | Can improve counting without changing geometry |
| Geometric estimation | Which depths or poses explain those observations? | Correct four displaced observations of one door | Yes, if constrained by adequate metric and multi-view evidence |

There are also different relationships to retain: same material, same semantic class, same plane and same physical instance. Two orange cones can share material and class while requiring two inventory IDs. Two white walls can have parallel normals and similar texture while belonging to different parts of the room. A single barrier can have several colours and surface directions.

## Classical precedent: colour and surface properties

| Method | Established approach | Application and limit here |
|---|---|---|
| [PCL RGB region growing](https://pointclouds.org/documentation/tutorials/region_growing_rgb_segmentation.html) | Grows regions by colour and merges neighboring clusters by mean colour; normal tests are available | A direct baseline for colour-based joining; automatic absorption of small regions can erase real inventory |
| [VCCS / supervoxels, CVPR 2013](https://pointclouds.org/documentation/tutorials/supervoxel_clustering.html) | Connected voxel clustering using spatial distance, RGB and surface normals; produces an adjacency graph | Close starting point for our coloured cloud; connectivity does not match disconnected reappearances |
| [LCCP](https://pointclouds.org/documentation/classpcl_1_1_l_c_c_p_segmentation.html) | Groups supervoxels using local convexity | Can separate objects in contact; noisy depth and normals affect the boundaries |
| [CPC](https://pointclouds.org/documentation/classpcl_1_1_c_p_c_segmentation.html) | Adds constrained planar cuts to supervoxel segmentation | Further precedent for joining and splitting geometric patches |
| [Richtsfeld et al., 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC3902499/) | Fits surface patches, computes relations including colour/texture, learns pairwise grouping and uses graph cuts | Very close precedent to the proposed property-based surface graph; not a cure for phone depth-scale bias |
| [TextureNet, CVPR 2019](https://web.stanford.edu/~jingweih/papers/texturenet/) | Learns 3D segmentation features from high-resolution surface texture | Shows texture is richer than mean RGB; requires suitable texture mapping and reconstruction |

A **surface normal** is the direction perpendicular to the surface. A **supervoxel** is a small connected 3D region grouped by local properties. These are useful intermediate patches; neither term implies a complete object.

PCL is a source of algorithms and reference implementations, not an installed Python dependency selected by this note. A first trial should check existing Open3D, NumPy, SciPy and OpenCV facilities before adding a C++ library solely for one grouping function.

## Semantic and embedding precedent

An **embedding** is a numerical description learned from training data. Its similarity can express meaning or appearance. It is not a measurement in metres or a unique object identifier.

| Method | What it adds | Geometry versus identity |
|---|---|---|
| [SemanticFusion, ICRA 2017](https://www.imperial.ac.uk/dyson-robotics-lab/downloads/semanticfusion/) | Accumulates class predictions on an ElasticFusion surface map | Consistent semantic labels; geometric correction still comes from the mapping system |
| [MaskFusion, ISMAR 2018](https://github.com/martinruenz/maskfusion) | Object-aware RGB-D tracking and reconstruction, including separate moving objects | Object models go beyond labels; semantic object SLAM is established |
| [PanopticFusion, 2019](https://arxiv.org/abs/1903.01177) | Volumetric fusion of class and instance labels across frames | Distinguishes background regions from individual objects; reconciles changing image-instance IDs |
| [ConceptFusion, RSS 2023](https://concept-fusion.github.io/) | Accumulates foundation-model features into 3D for multimodal queries | Direct precedent for attaching learned descriptors to surfaces |
| [ConceptGraphs, ICRA 2024](https://concept-graphs.github.io/) | Associates projected image regions across views into objects with descriptors and relationships | Close precedent for persistent 3D association; class similarity is insufficient for instance identity |
| [Volumetric Semantically Consistent 3D Panoptic Mapping](https://arxiv.org/abs/2309.14737) | Confidence-aware semantic/instance fusion and graph refinement | Its actual-SLAM versus reference-trajectory comparisons matter to our supplied-pose results |

Semantic segmentation gives a class such as wall or cone. Instance segmentation distinguishes individual members of a class. Panoptic mapping combines class-labelled background surfaces with separate object instances. Those distinctions are necessary for a map that must measure a floor and also count several identical cones.

## Close 2025–2026 work that narrows novelty

**Region-specific depth correction already exists.** [Region-aware Depth Scale Adaptation with Sparse Measurements, July 2025](https://arxiv.org/html/2507.14879v1) uses segmentation from SAM or OneFormer, then sparse metric observations to fit region-specific corrections. It explicitly discusses colour, texture and shape, and the weakness of fixed image-grid partitions. Replacing our 8 × 6 grid with meaningful regions and fitting local scale is therefore an existing-method baseline.

**Compact feature-guided scale fields already exist.** [Learning Image-Adaptive Scale Fields for Metric Depth Recovery, May 2026](https://arxiv.org/html/2605.07418v1) derives basis maps from depth and intermediate model features, and fits their weights from sparse metric anchors. Reusing backbone features or fitting a low-dimensional scale field is not, by itself, a new contribution. Code availability, training reproduction and CPU timing for these two scale methods were not established here.

**Sparse semantic computation already exists.** [OVI-MAP, CVPR 2026](https://ovi-map.github.io/) separates instance-map construction from semantic feature extraction and selects views for embeddings using object-view coverage. It accepts streaming RGB-D with camera poses. A claim based only on computing descriptors occasionally would overlap this work. [Official code](https://github.com/OVI-MAP/OVI-MAP)

**Online geometric/semantic grouping already exists.** [OnlinePG, CVPR 2026](https://arxiv.org/html/2603.18510v1) builds local segment relationships using geometry, semantics and cross-view consensus, then matches local instances into a global map. Its reported 10–18 FPS uses an RTX 4090 and excludes vision-language mask/feature computation. It requires depth and poses. That speed cannot be treated as an end-to-end CPU or phone result.

These papers establish relevant mechanisms. Their authors' accuracy claims do not establish the best method for our handset or recordings. Implementation and validation would be separate work, including code/model licence checks.

## Surface structure used to improve mapping is also established

[S-Graphs+](https://arxiv.org/abs/2212.11770) jointly models robot keyframes and poses, walls, rooms and floors in an optimizable graph. It uses structured environmental constraints to improve mapping and localization, including construction-site data. This is direct precedent against a broad claim that grouping walls and using their relationships to correct a map is new.

[Hydra](https://github.com/MIT-SPARK/Hydra) incrementally constructs and optimizes hierarchical 3D scene graphs. It is useful prior art for keeping surfaces, objects and places at different levels of a representation. Its robotics implementation is not a measured phone deployment in our conditions.

The proposed research must address a specific failure and improve on established local alignment and structured mapping, rather than claim the general combination of geometry and learned depth. The older arXiv record `2202.01470` is marked withdrawn in its current version; it is excluded as affirmative performance evidence here. [Withdrawal status](https://arxiv.org/abs/2202.01470)

## What could make this useful in our pipeline

Our present failures include repeated door layers, a thick floor and small disconnected pieces. A useful grouping method should address the cause of a selected failure, rather than use one rule for all three. The [denoising record](README.md) distinguishes stale measurements, wrong far-depth scale and unsupported surface.

Property-aware patches could offer three benefits, none yet measured:

1. Preserve a small, repeatedly supported object even if it fails the global component-size threshold.
2. Separate a wall from foreground clutter or a false connecting sheet using orientation and boundaries.
3. Recognize repeated observations of a surface, then use the original rays and metric evidence to estimate a correction.

The first two are segmentation/cleanup improvements. The third could affect metric accuracy. Labelling four displaced doors as the same door leaves four wrong layers unless an estimator uses independent evidence to determine the geometry.

## A bounded candidate experiment

**Hypothesis to test:** persistent surface correspondences can reduce far-depth inconsistency and duplicate identities under ARCore pose revisions, while support and visibility tests limit incorrect joins within the processing budget.

This is not an established novelty claim. Association graphs, reversible decisions, geometric gates and occasional embeddings are all known ideas. A methods paper would need a specific estimator or decision rule that differs from close prior work and produces a reproducible advantage. A systems/evaluation paper could instead contribute a measured answer about their practical interaction.

The smallest proposed sequence is:

1. **Form observation patches before final fusion.** Use image boundaries, available depth and local orientation. Include original frame, pixel support, capture time and placing anchor. Preserve curved and irregular regions rather than forcing everything to a plane.
2. **Describe each patch cheaply.** Record extent, normal distribution, colour statistics, source-image texture and metric-support range. These are proposed descriptors, not calibrated uncertainty values.
3. **Propose cross-view matches.** Project patches into candidate views, compare compatible orientation and image support, and test colour/texture only where the observations can refer to the same region. A tight 3D distance gate alone could reject the displaced layers we are trying to diagnose.
4. **Keep distinct relations.** Nearby, same material, possible same surface and same object have different meanings. A gap from occlusion can disconnect one object; physical contact can connect two objects.
5. **Test a small correction with poses fixed first.** High-confidence surface matches constrain temporal depth correction. Fresh ARCore measurements and sufficiently separated views provide metric evidence. Compare a scale-only model before adding parameters; do not jointly free camera scale and depth scale in the first experiment.
6. **Use learned descriptors on unresolved candidates.** Compare this with colour/texture alone and with every-view descriptors. Feature extraction and model loading count toward cost. Cached offline embeddings are suitable for an accuracy study, not proof of live feasibility.
7. **Recheck after anchor changes.** Observation patches should remain tied to their placing anchors. Pose revisions can change geometric compatibility, so prior merge decisions may need reconsideration.

The correction must operate on observations/depth or an explicit geometric model and then rebuild affected geometry. Averaging final duplicate layers can place a wall at a false midpoint. A consensus of equally biased learned depths is still biased. Where there is insufficient metric support or useful viewpoint change, retain an unsupported estimate rather than claim that a join made it measurable.

Initially, use geometry and inexpensive appearance. Add learned descriptors only if an ablation shows that they solve a specific remaining association error. This is a proposed test order, not a new architecture requirement or an adopted implementation decision.

## Failure cases and observable limits

| Case | Why a property rule can fail | Test or required distinction |
|---|---|---|
| Identical cones | Same colour, shape and semantic descriptor | Keep separate instances when physical evidence distinguishes them |
| Two similar walls or doors | Repeated appearance can support a false revisit | Check camera geometry, view support and contradictory observations |
| Striped barrier or poster on a wall | Appearance splits one physical surface | Permit different appearance patches under one surface/object relationship |
| Shadow, wet surface or auto-exposure | RGB and texture vary with illumination and view | Test changed lighting; normalized appearance remains a heuristic |
| Small valid object | Size-driven merging can absorb it | Evaluate missed inventory and false absorption separately |
| Thin pipe or curved equipment | Plane assumptions distort real shape | Allow nonplanar patches and preserve measured departures from a plane |
| Noisy bridge between surfaces | Connectivity fuses unrelated regions | Test orientation/boundary evidence instead of component size alone |
| Moved equipment | A static-world hypothesis maps it twice or drags the map | Keep motion/changed-instance hypotheses separate |
| Correlated ARCore support | Repeated observations may reuse the same tracked evidence | Count distinct tracks/views and calibrate confidence on held-out captures |
| Weak baseline or blank texture | Multi-view geometry may not determine depth | Report ambiguity and lost measurable coverage |

These are expected failure modes from the representations, not new empirical findings in this project. Neither a semantic embedding nor a normal estimated from biased depth supplies an independent physical reference.

## Controlled comparisons

Keep camera poses, selected frames, depth model and metric-support observations fixed while testing the grouping or correction. Change the camera backend in a separate experiment. In particular, introducing RTAB-Map and embeddings together would prevent attribution of any gain.

| Condition | Purpose |
|---|---|
| Raw ARCore depth, same poses/fusion | Measured-input control; report its smaller coverage |
| Current 8 × 6 scale and adopted cleanup | Reproduce the existing room baseline |
| Geometry/normal patches | Isolate value beyond component size |
| Geometry plus colour | Test the user's cheapest property-based extension |
| Add source-image texture | Test patterns beyond mean colour |
| Add selected-view embeddings | Measure descriptor benefit and full extraction cost |
| Existing region-aware depth scaling | Control for already-published content-based scale correction |
| Add temporal association without correction | Separate better identity from better geometry |
| Use associations to correct depth and rebuild | Test the actual measurement hypothesis |

Use the same implementation of a common step across conditions. Run the current live and offline pipelines as distinct baselines: the best room cleanup and grid fit are not yet evidence of their cost in the live loop. With corrected camera paths, explicitly rebuild or transform all affected observations consistently.

## Data and scores needed

Start with the recorded room for diagnosis, including its door and floor failures. It has no independent surveyed geometry. Then use public RGB-D/reference data to test geometry and controlled phone captures to test the real sensor chain. Split by capture/site, not random neighboring pixels alone, when selecting and reporting the final method.

Capture repeated identical objects seen together and apart, long absences and changed viewpoints, small inventory, repeated textures, lighting changes, moving equipment, short/long baselines and actual anchor revisions. Include independent near and far distances and areas. Supplied-pose controls isolate association; actual tracked poses establish its sensitivity to deployment errors.

Report all of the following:

- Surface error in centimetres together with retained coverage, including distance bands.
- Dimension and area error against independently measured references.
- Incorrect joins, false splits, duplicate IDs, missed objects and identity consistency, separately from total count error.
- Real small-object retention versus removal of false small fragments.
- Median and tail end-to-end update time, memory and hardware; include segmentation and descriptor extraction.
- Error and coverage among outputs marked measurable, plus rejection of unsupported estimates.
- Sensitivity to camera corrections, depth freshness, lighting and repeated appearance.

Lower error after deleting hard surfaces is not sufficient. Fewer clusters can mean more incorrect merges. A cleaner viewer is useful for inspection, but the contribution requires improved physical geometry or identity under a documented resource budget.

The product's existing minimum of one update per second is a constraint to measure, not a speed prediction. An offline accuracy win remains useful research evidence but does not establish the live deployment goal.

## What could support a paper or IP claim

**Already-established territory:** RGB/normal clustering, texture-based grouping, semantic surface labels, embedding fusion, persistent 3D instances, structure-constrained SLAM, region-specific scale and selected-view embeddings.

**Potential applied contribution:** a controlled worksite study showing which of these approaches preserves small objects and improves far-range measurement at a known cost on ordinary phone captures. Negative results can be useful if the dataset and comparisons expose an important failure that prior benchmarks miss.

**Potential methods contribution:** a specific new treatment of temporal surface identity, metric support and upstream pose revisions that demonstrably improves depth correction or controls incorrect joins. This digest does not establish that such a mechanism is absent from all literature or patents. Additional searching should be tied to the exact proposed mechanism.

**Recommended next experiment:** reproduce geometry-plus-colour grouping beside the current size filter, then compare existing region-aware scaling with a temporal version on the same observations. Use the first independent measurements to decide whether the gain is segmentation, identity, depth accuracy or just deletion. Embeddings become justified when the cheaper conditions reveal a measurable association gap.

## Research boundary

Sources cover official algorithm documentation, foundational papers, modern mapping methods and direct 2025–2026 depth-scale predecessors. They were chosen for similarity to the proposed mechanism rather than as a complete leaderboard. No method was installed or timed, and no new accuracy claim is made. Source and weight licences must be checked before adopting a concrete implementation. This is a literature assessment, not patent clearance.
