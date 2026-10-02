# Datasets for independent experiments

The depth, tracking and reconstruction pieces can be tested before either phone is connected. The method under test receives reference inputs in place of outputs from unfinished pieces. For example, reconstruction can receive published depth and camera poses, so a bad surface cannot be blamed on our stereo method or tracking method.

Sources were checked on 1 October and rechecked for TUM/ICL on 2 October 2026. The shortlist below separates small software checks from later outdoor validation. Middlebury's starter and both ICL reference assets are acquired and structurally verified. Geometry readers and algorithm comparisons have not yet been implemented.

## Which dataset tests which piece?

| Piece | Start with | Supply as input | Keep separate for scoring | What this isolates |
| --- | --- | --- | --- | --- |
| Stereo depth | Middlebury quarter-resolution training pairs | Left/right images and calibration | Reference disparity and valid-pixel masks | Matching quality, metric conversion and invalid depth handling |
| Camera tracking | TUM RGB-D | Colour, supplied depth, calibration and timestamps | Motion-capture camera trajectory | Pose estimation without our depth estimator |
| Surface reconstruction | ICL-NUIM living room | Rendered depth, calibration and supplied poses | Published reference surface | Fusion without stereo or tracking errors |
| Bird's-eye output | Exact generated geometry, then ICL reference geometry | Points/surfaces with declared axes and dimensions | Independently specified heights, boundaries and masks | Projection, scale, height selection and unknown-area handling |

Published inputs must be adapted to the same small data contract used by phone captures. Execution can be on a workstation, phone or backend. A dataset is not evidence about phone execution time or network performance.

## 1. Middlebury: the small stereo starter

The version 3 release provides rectified stereo images and camera calibration. Its 15 training pairs have public reference disparities; the 15 test pairs do not. Quarter-resolution images are roughly 750×500 or smaller. Start with the training pairs for local evaluation. The website currently says online result submission is disabled. [Official download page](https://vision.middlebury.edu/stereo/submit3/).

| Official archive | Publisher download estimate | Status |
| --- | --- | --- |
| [Quarter-resolution input pairs](https://vision.middlebury.edu/stereo/submit3/zip/MiddEval3-data-Q.zip) | 30 MB | Acquired: 30,937,533 bytes |
| [Left-view reference disparities and masks](https://vision.middlebury.edu/stereo/submit3/zip/MiddEval3-GT0-Q.zip) | 13 MB | Acquired: 13,555,667 bytes |

Use calibration from the selected resolution. Disparity is horizontal separation in pixels; it is not metres. The documented conversion is `Z_mm = baseline_mm * focal_length_pixels / (disparity_pixels + doffs_pixels)`. The principal-point offset matters. Exclude unknown/non-finite reference values when scoring. [Dataset and calibration description](https://vision.middlebury.edu/stereo/data/scenes2014/).

The publisher grants use and publication of its images and disparity maps and requests citation of the applicable paper. No noncommercial restriction is stated in that permission. This permission should be retained with the data; do not describe it as an invented Creative Commons licence. Cite Scharstein and colleagues, GCPR 2014, for this release. [Publisher permission and citation instructions](https://vision.middlebury.edu/stereo/data/).

Planned measurements: pixel disparity error, depth error in metres, valid-depth coverage and processing time. Freeze a development/held-out scene split before comparing methods. This is a static indoor benchmark. It does not test motion synchronization, mismatched phone fields of view, heat, or excavation surfaces.

The [2021 mobile collection](https://vision.middlebury.edu/stereo/data/scenes2021/) is a useful later comparison: an iPod touch camera moved by a robot arm, with reference disparity and calibration. It does not represent simultaneously exposed phone rear lenses. The [official archive index](https://vision.middlebury.edu/stereo/data/scenes2021/zip/) lists `all.zip` as 403.7 MiB. Do not fetch all ambient variations for the first experiment.

## 2. TUM: tracking with supplied depth

Freiburg1 xyz is already local. TUM supplies Kinect colour/depth recordings and independently measured camera motion; dataset permission is CC BY 4.0. [Publisher and licence](https://cvg.cit.tum.de/data/datasets/rgbd-dataset). Storage provenance and unit reminders are in [data/README.md](../../data/README.md).

Feed colour and supplied depth to the tracker. Only the evaluator may read the reference trajectory. Report trajectory error after rigid alignment with scale fixed, short-term motion error, successful-frame fraction, failures and processing time. A tracker with no loop closure must be described as such. Do not count copying supplied poses as a tracking result.

The existing sequence can reproduce the preliminary prototype comparison. Freiburg1 desk was selected on 2 October 2026 for held-out tracking, before further tuning; it has not been downloaded or evaluated. Freeze method settings on xyz before testing desk. If its results inform tuning, choose another held-out sequence. Desk includes a sweep across four desks with loop closures, but shares the indoor camera/site; it does not establish transfer to outdoor captures. [Selection receipt](../../data/icl_nuim/held_out_tracking.json), [official sequence description](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download#freiburg1_desk).

## 3. ICL-NUIM: reconstruction with supplied poses

Choose the synthetic living-room scene because the publisher supplies depth, poses and a reference 3D surface. The office scene lacks that explicit surface. The page lists 882 images and 1.9G for trajectory 2, while the acquired clean [TUM-compatible archive](https://www.doc.ic.ac.uk/~ahanda/living_room_traj2_frei_png.tar.gz) actually has 881 colour/depth pairs and 880 supplied poses. The data is CC BY 3.0. [Publisher selection and licence](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html).

Reference surface downloads are linked from the [living-room page](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/living_room.html). The authors' [SurfReg README](https://raw.githubusercontent.com/mp3guy/SurfReg/master/README.md) identifies [living-room.ply.tar.gz](https://www.doc.ic.ac.uk/~ahanda/living-room.ply.tar.gz) as the reference model. This asset is acquired separately from the reconstruction inputs and contains 9,982,296 points with colour and normals, rather than triangle faces.

HTTPS size checks and completed downloads on 2 October 2026 agree: trajectory 2 is 429,825,445 compressed bytes and the surface is 89,545,763. Extraction produced 481,610,533 and 269,522,228 payload bytes respectively. Archive safety/checksum checks passed; every PNG decoded and all pose/point values are finite. Local hashes and source snapshots are retained in [data storage records](../../data/README.md#icl-acquisition-and-verified-contents); no publisher checksum authentication is claimed.

For this 640 by 480 PNG representation, the documented depth conversion is camera-axis metres `raw/5000`, with zero invalid. Use ICL calibration `fx=481.2`, `fy=-480`, `cx=319.5`, `cy=239.5`. Native viewing-ray range needs a separate conversion; it must not be applied again to compatible PNGs. Match image and pose IDs exactly from 1 through 880. Image 0 remains in raw storage but has no supplied pose. These IDs are frame numbers, not seconds. [Publisher calibration](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/codes.html), [source reader guidance](https://raw.githubusercontent.com/ethz-mrl/supereight2/main/README.md).

The trajectory and reference surface have distinct coordinate frames. The publisher's trajectory-2 conversion includes a reflection; converting it to a quaternion would lose part of the mapping. Its matrix and the derived first-camera conversion are retained in [conventions.json](../../data/icl_nuim/conventions.json). Task 03 must test that relation and projection independently before scoring; acquisition alone does not validate an adapter. The publisher comparison measures one-way distance from reconstructed points to the reference, which does not measure missing coverage. [Alignment and scoring implementation](https://raw.githubusercontent.com/mp3guy/SurfReg/master/src/SurfReg.cpp).

Start with supplied depth and supplied poses. Compare reconstructed surfaces against the reference surface, report covered reference area separately from surface error, and restrict comparison to declared visible regions. Then replace one reference input at a time with estimated depth or poses. Artificial noise is a later controlled variation. None of these synthetic results establish outdoor phone accuracy.

## 4. Bird's-eye output: exact shapes first

No download is needed for the first projection check. Generate a plane, a step and a rectangular depression with dimensions chosen and recorded in the experiment plan. Define the expected height grid and observation mask independently of the projection implementation. Test rotated coordinates, negative positions, cell boundaries, multiple heights and missing observations. Unseen cells must remain unknown.

After those checks, use ICL reference geometry as a more complex input. Projecting a reconstructed surface into a second representation is not an independent ground-truth comparison. State the chosen up direction and reference plane explicitly; dataset camera axes do not automatically establish site gravity or a survey datum.

## Later data closer to site conditions

TartanAir V2 offers synthetic synchronized stereo, depth and reference poses. Its publisher states CC BY 4.0 for the dataset and MIT for its toolkit. [Official documentation and licence](https://tartanair.org/). The documented raw cameras have a 0.25 m stereo baseline; this differs from phone geometry. Packed float depth and NED poses need format-specific conversion. [Modalities](https://tartanair.org/modalities.html).

TartanGround includes a simulated `ConstructionSite` environment and global reference point clouds, making it a candidate for depth, tracking and map comparisons in related-looking scenes. Its publisher provides trajectory/modality selection and pre-download size analysis; the complete dataset is approximately 15 TB. A small exact subset, archive size and licence scope must be checked before acquisition. Do not transfer V2 permission to another release without checking. [Official dataset/download documentation](https://tartanair.org/tartanground).

These simulations can expose failure cases. They cannot replace consented outdoor recordings from the S23 and Redmi, with independently measured dimensions and separate held-out captures.

## Datasets not in the starter pack

| Dataset | Reason |
| --- | --- |
| KITTI | Useful outdoor stereo/odometry, but publisher terms specify CC BY-NC-SA 3.0. Company use permission has not been established. [Terms](https://www.cvlibs.net/datasets/kitti/) |
| Scene Flow / FlyingThings3D | Publisher explicitly prohibits commercial use; its FAQ also says there is no metric scene scale. [Terms and FAQ](https://lmb.informatik.uni-freiburg.de/resources/datasets/SceneFlowDatasets.en.html) |
| ETH3D | Existing research notes identify CC BY-NC-SA 4.0; permission for company use remains unresolved. [Existing source summary](../../research/sources/16_eth3d.md) |
| EuRoC MAV | Useful synchronized stereo/inertial data, but current archive availability and terms remain unverified. [Existing source summary](../../research/sources/17_euroc_mav.md) |

## Before an experiment run

Record scene selection, resolution, reference units, calibration, pose direction and valid-pixel rules. Record whether a learned method may already have trained on the benchmark. Use held-out scenes or sequences for the comparison. Choose numeric acceptance limits with the intended site task before interpreting scores as a pass. The current plan deliberately has no assumed accuracy or real-time thresholds.
