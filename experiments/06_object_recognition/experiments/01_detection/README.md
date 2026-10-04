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
