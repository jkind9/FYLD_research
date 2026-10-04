# Dataset storage

This folder holds downloaded inputs and their acquisition records. The [dataset experiment plan](../experiments/datasets/README.md) explains which reference data can replace each unfinished piece of the phone-to-map system.

Git retains this guide and JSON acquisition, inspection and geometry records. Images, depth files, point clouds and compressed archives are excluded. A receipt in a fresh clone is evidence of the original acquisition, not proof that its payload is present locally; verify or acquire the data before running an experiment.

## Available and proposed inputs

| Input | Local status | Purpose |
| --- | --- | --- |
| TUM Freiburg1 xyz | Acquired under `tum/rgbd_dataset_freiburg1_xyz/`; original archive under `archives/` | Test camera tracking with supplied depth; test fusion with supplied poses |
| TUM Freiburg1 desk | Acquired under `tum/rgbd_dataset_freiburg1_desk/`; original archive under `archives/` | Preselected held-out camera tracking check for Task 13 |
| Middlebury quarter-resolution stereo pairs and left-view reference disparities | Acquired and extracted under `middlebury/dataset/MiddEval3/`; 15 labelled training pairs and 15 test pairs with no public reference | Test stereo depth without a phone or network connection |
| ICL-NUIM living-room trajectory 2 and reference surface | Acquired; Task03 coordinate controls and Task04 nine-view surface scoring completed | Bounded reconstruction control without estimated depth or poses |
| Analytic planes, steps and rectangular depressions | Planned; generated fixtures do not exist yet | Test bird's-eye heights, dimensions and unknown areas with exact answers |
| Phone recordings | Not collected | Test actual dual-camera access and outdoor transfer of the methods |

The existing TUM archive contains 448,204,271 bytes. Its locally computed SHA-256 is `a0236d97b8c30cd93b653656d2b6c293ff7c982a4130ef2a1a8beecdb124ef98`. This is a reproducibility fingerprint; a publisher checksum was not found. The [publisher](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) states that the data is CC BY 4.0 unless otherwise specified. Cite Sturm and colleagues, IROS 2012, when using it.

## Records to retain

Middlebury acquisition totals 44,493,200 compressed bytes. [acquisition.json](middlebury/acquisition.json) records official URLs and local SHA256 fingerprints; no publisher checksum is claimed. Extraction checked ZIP CRCs, path safety and the expected stereo/calibration/reference files. [EXTRACTION.json](middlebury/dataset/EXTRACTION.json) records 120 entries and 50,105,243 expanded bytes. No stereo algorithm or geometry adapter has run yet.

Use `middlebury/dataset/MiddEval3/trainingQ/` for public reference labels. The downloaded test images have no public labels and cannot provide a local accuracy score. Reference disparity is not already depth in metres; conversion must use each scene's calibration, principal-point offset and declared baseline units.

For every acquisition retain the official source URL, resolved URL, retrieval date, compressed byte count, local checksum, licence evidence and extraction destination. Keep raw inputs unchanged. A manifest should identify the exact scenes, frame identifiers and units used in each run. Downloading a file does not establish that its coordinate conventions or reference labels were correctly loaded.

Large archives and image sequences stay outside version control. Preserve licence attribution when sharing derived material. Results belong with the experiment that produced them; a dataset directory should not become an output directory.

## TUM format reminder

The registered colour and depth images have distinct timestamps. Associate them explicitly rather than assuming matching filenames. Depth PNG values divided by 5000 give metres; zero is invalid. Pose translations are metres and quaternion order is `qx qy qz qw`. The publisher has already applied its Freiburg depth correction. Use sequence-appropriate calibration and record any conversion. [Official formats and camera parameters](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats).

## Recorded object revisit inventory

Visual inspection on 3 October 2026 found a cup look-away and return in TUM Freiburg1 desk. The same white cup is visible at RGB timestamp `1305031454.127701`, is physically out of view at independently checked `1305031463.059810`, and is visible again at `1305031466.095840`. The desk, pen holder, telephone, keyboard and monitors show that the camera returns to the same desk scene. TUM Freiburg1 xyz is not a valid return clip: the cup remains in view in the alleged gap frames `1305031116.143441` and `1305031116.943296`. Task17 supplies six desk frames with independent RGB-only agent-reviewed cup/monitor identities and coarse provisional supports. These are not human ground truth or formal segmentation references.

The xyz and desk recordings show multiple monitors, keyboards and books across changed viewpoints. No second physical cup was verified. Desk depth has 25.44% missing pixels in its existing inspection. The recordings do not establish scene absence, full occlusion and recovery, controlled in-plane rotation or lighting change, object movement, or tracking-origin reset. No phone recording exists. Preserve desk's role as Task13's held-out tracking sequence and do not run its full sequence during the object replay.

An indoor Kinect sequence can check software behaviour. It cannot demonstrate that the Samsung S23 or Redmi Note 11 Pro supplies synchronized stereo, nor that either phone measures excavation geometry accurately.

The read-only check on 2 October 2026 found 798 listed colour images, 798 listed depth images and 3,000 finite reference poses. All listed images exist; only the first colour/depth pair was decoded in this check. The original sequence was left unchanged. [Inspection receipt](icl_nuim/tum_inspection.json).

For registered PNGs, the publisher recommends the default camera parameters `fx=fy=525`, `cx=319.5`, `cy=239.5`, with no additional image undistortion. Its separately measured Freiburg1 colour calibration is `fx=517.3`, `fy=516.5`, `cx=318.6`, `cy=255.3`, with nonzero distortion. These are different choices: an adapter must declare its projection/distortion policy. Applying infrared-camera calibration directly to registered depth is inappropriate. Do not multiply the supplied depth by the already applied Freiburg1 correction of 1.035. [Publisher calibration guidance](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats).

## ICL acquisition and verified contents

Both official HTTPS downloads completed on 2 October 2026. They are the clean TUM-compatible living-room trajectory 2 and its separate reference point cloud. Permission is CC BY 3.0; cite Handa, Whelan, McDonald and Davison, ICRA 2014. [Publisher specification and licence](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html).

| Asset | Compressed bytes | Extracted payload bytes | Verified contents |
| --- | ---: | ---: | --- |
| `archives/living_room_traj2_frei_png.tar.gz` | 429,825,445 | 481,610,533 | 881 colour PNGs, 881 depth PNGs, associations and 880 reference poses |
| `archives/living-room.ply.tar.gz` | 89,545,763 | 269,522,228 | 9,982,296 points with colour and normals; no triangle faces |

Paths in this table are relative to `icl_nuim/`. Total compressed bytes are 519,371,208; total extracted payload bytes are 751,132,761. Each archive has a sibling JSON acquisition receipt with official/resolved URL, retrieval time, byte count and local SHA-256. These local hashes identify the downloads; no publisher checksum was found:

```text
trajectory archive  1b94a59ab814d9202d0d33369d123ecf734c3503298990319cc336b9aecf54d8
surface archive     a99b8a140fb90fb6bee5ab81921ee7391a7054f0234dc9434944566de1c91692
```

The [trajectory extraction receipt](icl_nuim/trajectory2/EXTRACTION.json) records 1,766 archive members; the [surface receipt](icl_nuim/reference_surface/EXTRACTION.json) records one. Extraction checked safe paths, member/payload limits, exact file sizes and the gzip checksum through the end of the stream. The [content inspection](icl_nuim/inspection.json) records hashes for every PNG, successful decoding of all 1,762 PNGs at 640 by 480, finite poses and finite point positions/normals. The reference PLY is a binary little-endian point cloud with 27 bytes per point and one trailing newline. Its header declares no physical units; the metric interpretation comes from the benchmark conventions.

The publisher lists 882 images for trajectory 2, but this exact archive contains 881 pairs numbered 0 through 880. The pose file `livingRoom2.gt.freiburg` contains IDs 1 through 880. Match IDs exactly and omit image 0 from supplied-pose runs. Preserve image 0 in raw storage. Do not shift the pose rows or read IDs as seconds. This missing first pose also appears in the [source implementation's reader guidance](https://raw.githubusercontent.com/ethz-mrl/supereight2/main/README.md).

Depth is 16-bit PNG; the documented TUM-compatible conversion is camera-axis distance `Z_metres=raw/5000`, with zero invalid. Inspected values span 0 through 26,520; there are 4,164,936 zero-valued pixels across the archive. Use ICL calibration `fx=481.2`, `fy=-480.0`, `cx=319.5`, `cy=239.5`. Native POV-Ray `.depth` files instead store distance along the viewing ray; that radial conversion must not be applied a second time to this PNG representation. The negative vertical focal length makes increasing image row point opposite the positive camera Y axis. [Publisher calibration and native reader](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/codes.html), [compatible depth format](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats).

Translations are metres and quaternion order is `qx qy qz qw`. A pose maps a point from camera coordinates into the compatible trajectory's world coordinates. The first supplied pose has identity rotation and translation `(0,0,-2.25)`. Its world is distinct from the native POV-Ray world and the reference-surface frame; files from those representations cannot be substituted directly.

The publisher's SurfReg tool expects a reconstruction expressed relative to the first camera frame. It then applies a trajectory-specific matrix to reach the reference surface. For trajectory 2 that matrix has determinant about -1, so it contains a reflection and cannot be stored as a rotation quaternion. [Publisher alignment contract](https://raw.githubusercontent.com/mp3guy/SurfReg/master/README.md), [matrix source, lines 126–140](https://raw.githubusercontent.com/mp3guy/SurfReg/master/src/SurfReg.cpp).

The exact matrix, pose direction and derived conversion are recorded in [conventions.json](icl_nuim/conventions.json). [Publisher and reader snapshots](icl_nuim/publisher_evidence.json) retain the source text and hashes. These are acquisition-time conversion records. Both historical extraction receipts retain `scoring_ready=false`; they are not rewritten by later work. Task03 subsequently checked projection, pose direction and surface alignment, and Task04 reported the independently referenced nine-view surface control. Keep `reference_surface/` available only to evaluation, separate from the depth and supplied poses used for fusion.

## Acquisition checks and recovery

Run `python experiments/datasets/acquisition.py` from the project root only for a fresh acquisition. The script refuses existing final archives and destinations. Current limits are exact official compressed sizes, 8 GiB extracted payload per archive, 2 GiB per member, 10,000 members, and at least 18 GiB free before downloading. The free-space guard covers a bounded decompressed temporary tar plus extraction. Metadata read requests above 1 MiB are rejected before the tar parser can allocate them. No fetched source code is executed.

Downloads use unique `.part` files. Provenance is published before the completed archive is renamed into place. Extraction first writes a bounded temporary tar and verifies gzip integrity, then writes a unique staging directory with `EXTRACTION.json`, and finally renames the whole directory. Interrupted partial files and staging directories remain identifiable and never count as ready. A receipt without its payload is incomplete. Inspect interrupted files before removing them; validate an existing archive's byte count and receipt hash before calling `publish_archive()` into a new destination. There is no automatic overwrite or resume.

The safety tests run with `python -m pytest experiments/datasets/tests/test_acquisition.py`. They cover unsafe names, links, collisions, payload/header bounds, truncated gzip, short/oversized downloads, redirects, provenance-write failure and overwrite refusal.

For the repository-publication check on 2 October, all 23 tests passed with a fresh directory under Windows TEMP (0.20 seconds). The local `.venv` lacks pytest; the system Python has it. Tests using a temporary directory inside this Documents workspace encountered a Windows rename-permission failure. Use a new, non-existing TEMP directory through pytest's `--basetemp` option when checking this environment; pytest may clean that directory. This test pass checks acquisition code, not geometry accuracy.

Freiburg1 desk was selected on 2 October 2026 as the later held-out tracking sequence, before further tuning. The official 344,011,403-byte archive was downloaded over HTTPS and extracted with gzip, path, member and exact-size checks. The local archive SHA-256 is `e983d6830916e66dc4a46a71368046b149b283de87769690e7aa4e0b9483530c`; the publisher does not list a checksum. Its receipt and extraction record are `archives/rgbd_dataset_freiburg1_desk.tgz.json` and `tum/rgbd_dataset_freiburg1_desk/EXTRACTION.json`. The extracted sequence has 613 RGB rows, 595 depth rows and 573 associated RGB/depth pairs at 0.02 seconds. All 573 paired images decode through the tracking adapter at 640 by 480. Across those depth frames, 25.44% of pixels have no measurement; the adapter preserves them as invalid values. Another 0.015% contain finite depths at or beyond the 4 m processing limit. No smoothing or hole filling is applied. For estimated camera tracking the reference trajectory remains evaluator-only after estimates are saved. Later object/replay controls explicitly consume supplied poses; they do not claim estimated-camera accuracy. The archive is CC BY 4.0 unless otherwise specified; cite Sturm and colleagues, IROS 2012. Freeze settings using Freiburg1 xyz, then evaluate desk without retuning. It is a separate sequence from the same indoor sensor/site, not an independent outdoor scene. [Selection record](icl_nuim/held_out_tracking.json), [publisher sequence description](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download#freiburg1_desk).

On 3 October 2026, the user approved evaluation of all 792 associated Freiburg1 xyz pairs followed by all 573 desk pairs without retuning. Each run has a 30-minute wall-clock limit and a 2 GiB per-process commit limit. Archive-derived SHA-256 values for each image, both timestamp tables and each reference trajectory are in the [member hash record](../experiments/datasets/tum_freiburg1_member_hashes.json). The runner checks selected images before tracking and verifies the reference hash only after the full estimate set has been saved. The supervisor records failed runs after forced termination and preserves complete artifacts if they are rejected for running past the time limit.


## Task17 bounded object reference preparation

[Six-frame reference inputs](../experiments/06_object_recognition/datasets/README.md) preserve original desk RGB/depth hashes and calibration, with separate method inputs and evaluator labels. The corrected verified camera look-away frame is1305031463.059810 (source frame268); the cup returns at1305031466.095840. The earlier claimed long visibility interval was a detector miss interval: the cup remains partly visible at1305031460.891774. Do not equate missing detections with absence from the image or scene.

These agent-authored and independently agent-reviewed labels identify one cup and two distinct monitors. They are not human ground truth; polygon boundaries are provisional and excluded from formal segmentation scoring. Enrollment has2frames and evaluation4, all already inspected within one session. No tuning, blind accuracy or new-session generalisation is claimed. Required missing footage remains in the13-case registry. Task13's held-out tracking settings and unfinished work are preserved.

## Reference and publication follow-up

Task40 plans independent masks, identities, physical anchors/extents and real surfaces before accuracy comparisons. The provisional desk annotation is not upgraded to human gold. Raw sources and completed publications remain local; ignore rules hide generated caches/test databases without deleting evidence. KITTI/nuScenes, new model weights and Apple hardware scans remain unauthorised acquisitions for their respective future tasks.
