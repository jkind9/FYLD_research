# Detection diagnostics

Task18 compares the already saved YOLO26x boxes with six independent coarse RGB reference frames from Task17. It performs no new model inference. These images were already inspected in this session, so the result is a small software and recording check. It does not measure accuracy on unseen recordings.

Open the [verified offline overlays](runs/20261004T071442.158193Z_4be5db5d6dca43e4be715c0665e44fcd/review.html) or [full scores](runs/20261004T071442.158193Z_4be5db5d6dca43e4be715c0665e44fcd/output/scores.json). Completion manifest SHA256: `7ee60f385871eeb6288c007bc03a548a233a2fee3e6dcf7cca9a5f583a15e39c`.

Cup labels cover every visible cup in all six frames, including one frame with no cup. Monitor labels cover only selected positives. Unmatched monitor proposals remain unscored. Monitor precision, recall and false-positive counts are unavailable.

At all three overlap thresholds, 0.3, 0.5 and 0.7, four of five cup references match the four predictions. There is one missed cup and no false cup detection. Cup precision is 1.00 and recall is 0.80 on these coarse references. All six annotated monitor positives match; there are 13 monitor proposals. The empty-prediction software control misses all five cups and six annotated monitors. The comparison retains every proposal for every selected frame.

## Reproduce offline

```powershell
.venv-yolo/Scripts/python.exe -B -m experiments.06_object_recognition.experiments.01_detection.run
```

The production entry pins Task17's annotation SHA256 and the exact accepted Task28 completion manifest, `e07af81930e80fe7400c0a0b12b26138c3fea6f7533b1b8137b5186a587267a3`. A transferred copy may be supplied with `--cache`; every artifact must still verify. No substituted predictions, model loader or alternate expected hash can be passed to this entry. Missing source images or cache fail before publication. No weights are downloaded.

The method input ledger contains only source frame, timestamp, RGB path/hash and predecessor selection index. Reference labels enter the scorer and report after extraction. Depth, camera poses and object association outputs are not read by cache extraction. It checks the checkpoint, package, original image grid, device and inherited prediction settings. Ultralytics recorded `half=None` after setup; the independent runtime flag `actual_fp16=False` confirms FP32.

Matching first finds the largest number of one-to-one pairs above the specified intersection-over-union threshold (IoU). Among those assignments it maximises summed overlap. This prevents a broad proposal from taking the only reference available to a neighbouring narrow proposal. Cup totals include all six frames. Empty denominators produce unavailable values, represented by JSON null.

Each fresh run contains six copied source RGB images, independent annotation JSON, a separate method ledger, cached proposals and metadata, every match/miss/unmatched prediction and duplicate candidate, six annotated PNGs and an offline HTML report. Existing runs remain unchanged. Output paths are resolved before publication. A destination within an existing run is rejected, including nested paths and directory aliases. The existing Run contract saves source snapshots and hashes all artifacts before marking completion. A failed copy or report leaves a failed run; restarting uses a new directory.

## Costs and limits

The verified predecessor processed 60 frames in 6.68 seconds, including 2.38 seconds of detection and 1.32 seconds of model load. These remain predecessor costs and are not counted as new six-frame inference. The [new execution companion](runs/20261004T071442.158193Z_4be5db5d6dca43e4be715c0665e44fcd_execution.json) records 6.16 seconds from operating-system process creation through final verification, including imports in this dedicated command. Evaluation entry through verification took 5.30 seconds; cache preflight took 0.199 seconds. The command ran under coverage instrumentation, so this is a verification-run cost. The Windows peak process working set was 124,420,096 bytes. Peak traced Python allocations were 16,652,149 bytes. The allocation tracer is not total process or GPU memory. Run stage timing excludes final manifest publication; the execution companion includes verification. These desktop cached-evaluation costs do not establish phone speed, energy or thermal behaviour.

Other shortlisted detectors are deferred because their weights are not available locally and no new downloads are authorised. Formal accuracy on unseen inputs and mask-boundary accuracy are also deferred because these are already inspected coarse references. No detector-quality threshold or product readiness claim follows from this run.

## Verification

All 60 focused controls passed. Focused tests covered 89% of new implementation statements. Combined tests and the final verified production command covered 97%. Lint, formatting and type checks passed. Independent Python and test review passed after correcting malformed-class validation and tracing cleanup on failed preflight. The final completed report rendered six embedded images in Edge with no page errors or external requests. Final diff review passed after fixing a default-test dependency on a generated local cache and an output path that could change a prior run. The cache check now skips when its optional local data is absent. Four new output-path controls failed before the guard and passed afterward, including a real directory alias. Earlier publications remain verified and unchanged.

The controls cover duplicated predictions, crossed nearby objects, maximal summed overlap, empty denominators, category isolation, invalid source bounds/class/confidence, malformed cache joins, tampering, unavailable caches, incomplete publication and offline report rendering. Fixture runs use tiny clean repositories outside the experiment source tree. Their synthetic metadata exercises validation and is explicitly labelled as a software control, never GPU evidence. The published production path separately rejects those synthetic cache hashes.

## Box position error in clutter (Task45, 5 October 2026)

Task18 only counted a box as found or missed. This section measures **where** the found boxes land, in two parts.

### Part A: placement against hand-drawn outlines (COCO val2017)

The detector (YOLO26x, same settings as above) ran on all 5,000 photos in COCO's 2017 validation set. Every object of the detector's 80 classes is outlined by hand in these photos. Each found box was matched one-to-one to an outline (same matching as Task18, now also accepting each photo's own size) and its error measured. The detector's makers use this set to choose their checkpoint, so these numbers may be optimistic.

| Measure, boxes matched at overlap ≥ 0.5, object not cut off by the image edge (20,036 boxes) | Median | Worst 10% |
|---|---|---|
| Overlap with the reference box (IoU) | 0.91 | below 0.72 |
| Centre offset | 1.6 px | above 7.3 px |
| Centre offset as a share of object size (box diagonal) | 1.6% | above 7.3% |
| Extra background inside the box, beyond what the correct box has | 0.6% | above 10.3% |
| Share of the object's outline inside the box | 99.7% | below 94.6% |

- Small objects are off by a larger share of their size: 2.6% median, 9.0% for the worst 10%. Large objects: 0.9% and 4.6%.
- Small objects also take in more extra background: 1.6% median, 14.7% for the worst 10%.
- **Clutter barely changes placement.** The rank correlation between how much of an object's box is covered by other objects and its centre offset is 0.10, and overlap is −0.08. Once a box is found, nearby objects hardly move it.
- Finding objects is the weaker part: 70% of outlined objects were found at overlap 0.5 (64% at 0.7). 76% of boxes matched an object. A further 1,332 detections fell inside crowd regions, which COCO doesn't outline object by object; these are counted separately, not as false.

Run: `runs/20261005T085845.472152Z_035bf495dc474833a1587fb82c452866` (manifest SHA-256 `817021f3…5aa3`), 198 s on the GPU. The summary is in `output/summary.json`; every matched box is in `output/placement_rows.json` and every image and class count in `output/counts.json`.

### Part B: wobble over time (TUM desk recording)

The detector ran on all 571 frames of the cluttered desk recording that have a motion-capture camera position (2 of 573 fall in a 0.05 s gap in the motion capture and are listed as refused). The depth image is taken up to 20 ms from the colour image. Depth is first moved to the colour image's moment, using the camera positions. Each box is then followed from frame to frame by predicting where its centre should appear next.

For each object followed for at least 5 frames (147 tracks), wobble is measured two ways:

- **Local wobble:** each box against the average 3D position of the same object over the 5 frames either side. This does not count slow, smooth change (an outline changing with viewpoint) as wobble.
- **Frame-to-frame wobble:** the change between consecutive frames, divided by √2.

A **noise floor** comes from tracking well-defined image corners the same way. It shows how much apparent movement comes from camera timing, depth and calibration rather than the detector: about 0.8 px across and 1.1 px down per frame. It rises only slightly when the camera turns faster (0.75 to 0.91 px across).

A box is **flagged** if it touches the image edge, has few valid depth readings in its centre, or has a wide spread of depths there.

| Tracks (radial wobble, mean with 95% interval from resampling tracks) | Local | Frame-to-frame |
|---|---|---|
| Clean: no flagged box (33 tracks) | 1.8 px (1.5–2.2) | 1.5 px (1.3–1.7) |
| Flagged boxes (114 tracks) | 5.8 px (5.0–6.6) | 3.5 px (3.0–4.1) |
| All (147 tracks) | 4.9 px (4.2–5.6) | 3.1 px (2.7–3.5) |

- **Clean boxes barely wobble.** At about 1.5–1.8 px, wobble is close to the noise floor (about 1.4 px combined). Their frame-to-frame correlation is close to independent wobble (median −0.42 across, −0.26 down, against −0.5), so the two estimates agree.
- **Flagged boxes wobble about 3 times more.** 57% of the 4,355 boxes have at least one flag: 49% touch the image edge (the desk is filmed close up), 9% have no depth in their centre, a further 13% have depth but too few readings, and 8% have a wide spread of depths there.
- **On flagged boxes, errors persist over several frames.** Their median frame-to-frame correlation is 0.03 across and −0.16 down, far from −0.5. A flagged box that is off tends to stay off for a few frames, so for these the frame-to-frame number understates the wobble and the local number (5.8 px) is the better guide. Short tracks can also pull lag-1 values toward zero, so this persistence result is descriptive rather than a corrected physical correlation.
- **Most lost tracks are missed detections, not jumps.** A followed box was lost 588 times. In 449 cases the detector found no same-class box within the gate. In 60 cases a nearby same-class box was already claimed by another track, so the outcome is recorded as `claimed` rather than a missed detection. In 53 cases the same object was found again in place but had no depth reading, so it could not be followed. The one-to-one jump count is 26 detections with an unclaimed same-class box between 0.5 and 2 box sizes away (median 229 px). Only 147 of 602 tracks last 5 frames or more.
- Box size changes too: the box width times depth varies by a median of 7% within a track.
- The local estimate includes each frame in its own 11-frame anchor. At the observed track lengths, simulation puts the estimate at about 7–8% below independent wobble; the pairwise estimate is about 3–4% low. These small-track biases are recorded rather than corrected in the reported values.

Run: `runs/20261005T093056.105890Z_0bc39ecbfea04501b7ec8654943fdb13` (the rerun after the reviewer correction). It replaces the earlier run that wrongly counted 179 "jumps" and the intermediate 46-jump run. The corrected run separates nearby boxes already claimed by another track and assigns a jump target at most once.

### What this means for the 3D position spread

A 5 px wobble at 1 m is about 1 cm sideways. The 72.8 mm spread in the desk cup's 3D position (Task29) is far larger, so box wobble is not the main cause. The likely causes are depth taken from the wrong surface or missing (the flagged boxes) and boxes cut off by the image edge. Separately, 449 unclaimed misses plus 60 claimed-neighbour cases break tracks often, which matters for counting and for how many views each object gets. Segmentation (Task34) addresses depth from the wrong surface directly: it can be compared on these same frames and photos with the same measures.

Commands (detector environment, GPU only when free):

```bash
.venv-yolo/Scripts/python.exe -B -m experiments.06_object_recognition.experiments.01_detection.placement_run --data-root <checkout>/data --checkpoint <checkout>/checkpoints/yolo26x.pt
.venv-yolo/Scripts/python.exe -B -m experiments.06_object_recognition.experiments.01_detection.jitter_run --data-root <checkout>/data --checkpoint <checkout>/checkpoints/yolo26x.pt
```

Both refuse to run unless OpenCV 5.0.0 is the version loaded, and Part A refuses unless the COCO extraction matches its recorded archive hashes (see `data/README.md`).

## Independent validation import

The public analysis boundary is `importlib.import_module("experiments.06_object_recognition.experiments.01_detection.validation").evaluate`. It forwards the existing scorer and its compatible frame/proposal schemas without copying scoring mathematics. The six-step runner saves and hashes predictions before scoring. Complete phone-survey adaptation remains Task56 work. [Runner contract](../../../../src/walkthrough/README.md).
