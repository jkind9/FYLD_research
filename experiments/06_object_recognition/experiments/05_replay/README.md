# Recorded object replay

## Open the viewer

Open [the verified replay](runs/20261004T152704.023370Z_84abb8b3b9594dcea8a1e5b2c8aced66/review.html) in a browser. Choose the 60-frame baseline or either automatic association rule. The page shows the RGB recording, camera position and direction, the growing coloured depth cloud, object markers and every cached baseline detection. Filter the 457 baseline proposals by class to inspect each box, persistent ID and measured scene position.

The automatic condition covers six selected frames and 17 cup or monitor boxes. It shows each box with its association decision. Select an ID to inspect its detections and unresolved candidate matches up to the current frame, with camera and scene coordinates. IDs from later frames are not listed while stepping backward. The cup marker stays at its last accepted position through the physically empty frame.

## Recorded result

Both automatic rules kept the cup on one persistent ID from frame104 to its verified return in frame359. At the empty frame268, the viewer retained the ID and last accepted marker from frame104. The two automatic rules have separate ID namespaces by design.

The cup's box-supported visible-surface median changed from `[0.577755, 0.668876, 0.831299] m` at frame104 to `[0.582584, 0.638692, 0.835116] m` at frame359. The difference was `[+0.004830, -0.030184, +0.003817] m`, with length `30.8 mm`. This is a difference between measured visible surfaces. It is not object-centre error or a calibrated uncertainty bound.

The combined last-position rule accepted 13 of 17 observations and left four monitor detections unresolved. The combined independent-view median accepted 14 and left three monitor detections unresolved. Both rules kept five separate monitor IDs in this selected sample. That ID count is descriptive; the monitor references are a non-exhaustive positive subset and do not establish five real monitors or general accuracy. Task21's separate controls cover same-class neighbours, duplicate boxes, near-tied matches and cross-session boundaries.

## Run evidence

The current publication is complete and hash-verified. Its manifest SHA256 is `fd7a7cce28fad27a0eb8af5b81a96f7aa613e825b2fbe8dfacf4191d5939254f`; it contains 258 files. It copies the original 60 RGB and depth pairs, 20,000 display points and baseline ledgers without changing them. The baseline accounts for 457 detector proposals. An earlier publication passed an offline Edge check for condition switching, cup history, retained position, proposal counts, zero page errors and zero external requests. This final publication also clears automatic boxes on unsampled frames, but could not be reopened in a browser during the last verification because Windows denied Playwright's browser process launch.

The 17 actual-box appearance vectors came from the existing YOLO26x checkpoint at CUDA0, float32, pooled layer22 (`C3k2`), with 768 values per crop. The first accepted Task22 run performed those 17 embedding requests. The final viewer publication reused that hash-verified receipt and vectors, so it ran no new detector or feature forwards and loaded no model. No weights or packages were downloaded.

The viewer uses supplied TUM motion-capture poses. It does not use Task13's unfinished estimated camera path. Task16 remains pending review; this exploratory replay does not approve its broader protocol. The provisional labels and inspected views do not support blind accuracy, object-centre error, or new-session generalisation claims.

The first Task22 publication attempt after inference failed while assembling the viewer payload. It is preserved as an incomplete run. Later publications reuse the verified feature receipt and do not repeat GPU work. The current publication also fixes a reviewed output-path issue when the replay is run against a repository path other than this checkout.

## Portable export and repeated coordinates, 4 October 2026

Download or copy [the ZIP package](runs/shareable/task22_replay_20261004.zip), or send [the standalone HTML](runs/shareable/task22_20261004/task22_replay.html) alone. Extract the ZIP and open the HTML in a modern browser; no repository, server or internet is needed. The HTML is an unchanged copy of the verified source, with its original images and display sampling. The ZIP is 6,448,978 bytes and contains the viewer, usage README, [all desk cup detections as CSV](runs/shareable/task22_20261004/cup_desk_observations.csv), [spread definitions and results](runs/shareable/task22_20261004/cup_repeatability.json), [coordinate plot](runs/shareable/task22_20261004/cup_repeatability.png), and export receipt. Full-resolution cloud arrays are not packaged. SHA256 of the ZIP is `3072847e057805cc732bdcb6c8fec10854f8941e38593ad55bb6a016e7bb04cc`.

Task29 verified the original run before and after copying, exact HTML hashes, embedded counts of 60 frames/457 proposals/20,000 points, zero external HTML resource attributes, ZIP CRC, and every archived file hash. It added no model or reconstruction run and did not repeat browser interaction checks. The source publication and its existing browser-check limits are preserved.

The full baseline contains 19 cup-class proposals: 16 assigned to object-0005 and three unresolved. Seventeen proposals have coordinates; two have no usable position. The CSV keeps both rejected and accepted records. The sixteen assigned detections have the following spread around their own coordinate-wise median:

| Position definition | RMS distance from median | Maximum distance from median | Largest pairwise separation |
|---|---:|---:|---:|
| Median of valid depth samples inside the box | 72.8 mm | 260.0 mm | 291.7 mm |
| Depth sample nearest the image-box centre | 82.3 mm | 261.4 mm | 317.0 mm |

These describe repeatability of observed surfaces, with equal weights for correlated nearby frames. All-frame identities were assigned by the baseline, not independently verified. Acceptance already filters observations, so this subset cannot establish unbiased accuracy. The separate all-located summary includes a rejected cup-class proposal far from the assigned cup; it cannot be treated as another confirmed observation of that cup. There is no independently measured physical-centre reference or absolute position-error result.

The largest assigned deviation is frame523. Original RGB inspection shows the cup clipped by the top image edge. The valid depth pixel used for its centre sample is about 19.7 pixels away from the box centre. This identifies a measurement-quality concern; it does not establish which source of error caused its 260 mm deviation. The two return views' 30.8 mm difference therefore does not describe the full repeat-detection spread. Accepted box-median camera depths range from 0.58 to 1.354 m.

Task27's original marked cup is from Freiburg1 xyz and has one measured view. This is a different recording from the Freiburg1 desk cup above. Two real recorded sequences have therefore been exercised, but labelled identity recovery and automatic association comparison have used only the one desk scene. The synthetic living-room surface control and static stereo pairs do not supply a second real identity benchmark.

## Identity evidence and proposed investigation

The existing small labelled Task21 control does not prove both appearance and position are always necessary. Geometry-only and combined rules each resolve all eleven provisional observations; appearance-only leaves four unresolved. Task20 also records one incorrect monitor appearance ranking. Using both kinds of evidence is a reasonable next design choice, with wider independent tests still needed. Motion and appearance are also combined in the established [Deep SORT research](https://arxiv.org/abs/1703.07402); its results are not measurements of this project.

The present exploratory gates are 0.35 m for position and 0.80 cosine similarity for the combined rules, with equal normalized cost weights. They are inherited trial choices, not calibrated same-object boundaries. The next investigation should measure matching and mistaken-merging rates across distance/similarity settings on independent recordings, with absolute location error and repeatability recorded separately. Appearance indicates identity compatibility and does not by itself determine coordinate precision.

For future consolidation, use one-to-one assignments within each frame, measured position uncertainty, and a record of distinct objects seen together. Two boxes can still be duplicate detector predictions; independent spatial supports provide stronger evidence of two physical objects. Identical-looking neighbours seen only in separate views may be unresolvable when geometry is also uncertain. Preserve that uncertainty rather than forcing a merge. Keep every observation and its source crop, then compare robust location estimates without letting repeated nearby frames dominate.

The current depth adapter excludes depth at or beyond 4 m. Indoor cup results cannot support street-scale accuracy. A future benchmark should measure 3D position error, coordinate spread and mistaken merges/splits by camera distance, viewing angle, visibility and object separation. A one-degree angular error produces about 175 mm lateral displacement at 10 m, illustrating why the current fixed position gate cannot simply be transferred to every range. [KITTI tracking](https://www.cvlibs.net/datasets/kitti/eval_tracking.php) supplies street recordings, calibration, stereo/LiDAR and track labels; [nuScenes](https://www.nuscenes.org/nuscenes) supplies camera, LiDAR, ego-pose and 3D-box evidence. Neither has been downloaded or tested here. Dataset suitability, reference conventions and terms need checking before acquisition.

## Smoother and more realistic reconstruction: research only

The current replay caps displayed points at 20,000 across sixty frames. Task27 saves 230,405 measured points for its single frame but also displays only 20,000. Denser display would improve visible coverage without adding information to the captured depth. A surface representation is a separate reconstruction step, with depth noise, missing surfaces and camera alignment still limiting detail.

| Representation | What it provides | Research implication |
|---|---|---|
| Dense points or small oriented surface patches | More continuous-looking measured surfaces | Useful display comparison before fitting a surface; missing capture remains missing |
| Depth fused into a surface and extracted as triangles | Connected, noise-reduced surface geometry | Natural first comparison for these registered RGB-D inputs |
| Mesh with photographs applied as textures | Detailed appearance on explicit geometry | Suitable visual layer for object selection and measurements if geometry/scale are verified |
| Gaussian splatting or a neural radiance field | Realistic views synthesized from captured images | Candidate for an immersive visual layer, with geometry and metric measurements separately validated |

[Open3D depth integration](https://www.open3d.org/docs/release/tutorial/t_reconstruction_system/integration.html) combines noisy RGB-D observations using known poses and extracts a triangle mesh. It is the closest extension of the current supplied-depth control. [COLMAP](https://colmap.github.io/tutorial) reconstructs camera poses and dense geometry from images and supports meshing and texture mapping. [3D Gaussian Splatting](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) optimizes a scene representation for realistic rendering from new viewpoints. These are investigated options, not installed or executed comparisons in this task. A visually convincing rendering does not establish accurate object dimensions.

Panorama stitching supports looking around from a capture location. Walking through the environment with parallax requires a three-dimensional reconstruction. A future supplied video can support an exploratory metric object map directly when registered depth, calibration, timestamps and poses are available. Ordinary monocular video needs additional depth/pose reconstruction and a metric scale reference; the unfinished estimated-camera pipeline is not yet a verified upload-and-map product.

A later review app could link a picked object to every source frame and crop, show individual measured points beside its fused estimate, expose rejected matches, and allow distance and size measurements. Distance tools should identify the selected endpoints and coordinate uncertainty. Size estimates need foreground geometry and adequate viewpoint coverage; a bounding box or partially observed surface does not establish the whole object's dimensions. This is a recorded future requirement, with no app implementation started.

## Book birth-policy accounting

The baseline has 95 book detections: one new ID, four matches and 90 unresolved outside the position gate. In `pilot/replay.py`, an unmatched candidate cannot receive a new ID if an older track of that class exists. Baseline association is geometry-only. This is a restrictive birth-policy limitation, not evidence of book appearance failure. [Task31](../../../../task_list/stale/31_compare_provisional_object_ids_and_duplicate_relationships.md) owns its comparison with provisional IDs and explicit possible duplicates. The accepted run and Task22 pending-review state remain unchanged.
