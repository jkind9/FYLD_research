# Task21 geometry and identity replay

This experiment replays the eleven checked provisional detections from six TUM Freiburg1 desk frames. It compares five fixed rules for connecting same-class observations to persistent object IDs. The camera poses and Task20 appearance vectors are supplied inputs. Task21 runs on CPU, loads no model, and makes no GPU forwards.

## Open the viewer

Open `runs/20261004T143434.634726Z_33f59456f7d34e50a64020ed6e0613bb/review.html` in a browser. Choose a condition to inspect each observation, its measured scene position, its decision and the object position after each frame. The page also lists scorer-only surface-coordinate differences across views. Its labels support evaluation only; the association method receives no identity labels.

## Trial result

The selected frames are 23, 104, 268, 359, 405 and 560. Frame 268 has no cup detection. It records the cup's last estimate and keeps the accepted vote count at two. The cup is detected before the gap at frame104 and returns at frame359.

Each condition keeps the cup on one ID from frame104 through frame359. The IDs are stable within a condition and intentionally differ between conditions:

| Condition | Cup ID | Resolved observations | Unresolved | Wrong merges | Wrong splits |
|---|---|---:|---:|---:|---:|
| geometry-last | `067f5dd4924351a6b8164861552fb4f8` | 11 | 0 | 0 | 0 |
| geometry-viewmedian | `285fe0a247b5586bbbfb40a22b8c9961` | 11 | 0 | 0 | 0 |
| appearance-viewmedian | `3768809845545d589cd018754f049548` | 7 | 4 | 0 | 0 |
| combined-last | `abe24dab19095dc4ac41fe78a5a24454` | 11 | 0 | 0 | 0 |
| combined-viewmedian | `be7211538a005d12bb359ab16ce56c8c` | 11 | 0 | 0 | 0 |

The frame104 cup surface median is `[0.57854, 0.67703, 0.83302] m`. Its return at frame359 is `[0.56472, 0.68080, 0.81903] m`. The observed change is `[-0.01382, 0.00377, -0.01399] m`, or 20.0mm in length. At the end of the replay, the last cup measurement minus the median of independent view representatives is `[0.01481, -0.04726, 0.03162] m`, or 58.8mm in length. Those differences describe sampled visible surfaces. They are not object-centre error or calibrated coordinate uncertainty.

The input receipt includes all six source frames, including the empty gap frame. It records the polygon-supported camera and world medians, box-supported camera and world medians from the existing `localise_detection` helper, and the box-minus-polygon differences for each observation. The box is a separate support comparison because it may include background depth.

## Association and location rules

All proposals in a frame are assigned together. Matching requires the same session and scene origin. Geometry must pass fixed gates against both the first accepted position and the current estimate. Appearance helps identity matching only; it never changes coordinate weights. Tied alternatives that change the selected assignments leave every changed observation unresolved. Same-class duplicate proposals with box IoU at least 0.90 and world separation at most 0.02m are all unresolved and add no position votes.

The five conditions are geometry with the last accepted position, geometry with the median of independent views, appearance with that median, combined geometry and appearance with the last position, and combined geometry and appearance with the view median. One source frame can contribute at most one position vote. Frames within 5cm and 10 degrees of an earlier representative share one vote. The estimate preserves every observation coordinate and uses either the last accepted coordinate or a coordinate-wise median of representatives.

## Reproduce checks

The exact Task20 source run, descriptor cache and settings are pinned in the Task21 task file. To rerun the CPU replay, use the repository Python environment:

```powershell
.venv-yolo/Scripts/python.exe -m experiments.06_object_recognition.experiments.04_geometry_identity.run
```

Each replay invocation publishes a new immutable run. To check the accepted run without running inference or publishing another run, set `TASK21_VERIFIED_RUN` to its directory and run:

```powershell
$env:TASK21_VERIFIED_RUN = 'experiments/06_object_recognition/experiments/04_geometry_identity/runs/20261004T143434.634726Z_33f59456f7d34e50a64020ed6e0613bb'
.venv-yolo/Scripts/python.exe -m pytest -q -p no:cacheprovider experiments/06_object_recognition/experiments/04_geometry_identity/tests
Remove-Item Env:\TASK21_VERIFIED_RUN
```

The accepted run's completion manifest SHA256 is `75a1b943ab087d846a87d71289b4e118063fad8bac2010694e1521499046d6f7`. Verification found 172 files and status `complete`. Run timing was 1.749 seconds for construction through report publication, excluding the final manifest hash and completion publication. Edge loaded the saved page with 11 observation rows, six frame histories and eight coordinate-comparison rows. Switching to the combined view-median condition showed no page errors or network requests.

## Limits and follow-up

This is a small, previously inspected, provisional reference set. It supports within-session diagnostics only. Four of the five conditions recover the cup return; geometry-only and combined rules resolve both distinct same-class monitor identities in this sample. Appearance-only leaves those monitor observations unresolved. The synthetic tests cover ambiguous assignments, duplicate proposals, repeated-view vote caps, missing geometry, changed coordinates, failed matches, session/world/segment boundaries, restarts and pose revisions. They do not establish performance on unseen recordings. Task16 remains pending review; Task13 was not run or modified. The Python review found that a different capture session could reuse an existing ID. A regression failed before the session guard and passed after it.

## Scoped follow-ups

[Task31](../../../../task_list/stale/31_compare_provisional_object_ids_and_duplicate_relationships.md) owns provisional births and explicit duplicate/alias policy; [Task32](../../../../task_list/closed/32_investigate_spatial_support_and_position_uncertainty.md) owns spatial supports/calibration; [Task35](../../../../task_list/stale/35_measure_error_propagation_and_sequential_fusion.md) owns sequential error/fusion. Every detection should retain a unique observation ID, and missing depth means unknown position. Confirmed inventory remains distinct from provisional/rejected candidates. Task32's descriptive support summary remains in this package; its isolated support-aware association handoff is under `../07_spatial_uncertainty/association.py`. These new questions do not close Task21, which remains pending review.

## Public identity scoring boundary

The scorer is now `importlib.import_module("experiments.06_object_recognition.experiments.04_geometry_identity.validation").score_identity`. Its body and interpretation are unchanged; `run._score` remains the same compatibility import. The evaluation report calls the public validation owner. Experiment commands, settings, old runs and source snapshots stay intact. [Root sequencing and independent reference boundary](../../../../src/walkthrough/README.md).
