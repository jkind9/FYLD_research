# Experiment 06: object recognition and persistent inventory

## What is established

This experiment has a bounded recorded RGB-D proof of concept with supplied camera poses. It detects objects, projects measured depth, compares appearance and identity rules, and replays source-linked observations. It has not established general object inventory accuracy, calibrated position uncertainty or phone performance.

| Owner and evidence | Completed measurement | Limits |
|---|---|---|
| [Task27 single-view xyz pilot](pilot/README.md) | One visually reviewed YOLO26x cup detection and measured depth projected into scene coordinates | Different recording from desk. No verified physical identity connecting the two cups; surface sample is not object centre. |
| [Task17 reference preparation](datasets/README.md) | Six desk RGB-D frames, three identities, eleven provisional observations | RGB-only agent review; cup coverage complete on selected frames, monitor positives non-exhaustive. No human gold/blind benchmark; masks coarse. |
| [Task18 detection](experiments/01_detection/README.md) | Cached YOLO26x finds four of five cup references and six annotated monitor positives | Coarse, inspected frames; no monitor precision/recall because reference coverage is partial. |
| [Task19 segmentation](experiments/02_segmentation/README.md) | Forty-five rectangle/GrabCut/contour masks on fifteen prompts; depth coordinate differences and desktop costs | No positional/size improvement proved; no learned mask result. |
| [Task20 appearance](experiments/03_appearance/README.md) | ZNCC: seven correct gallery rankings; existing YOLO features: six correct, one wrong monitor ranking; ORB/SIFT unavailable on recorded pairs | One cup identity cannot test separation from another cup. ResNet50 and contextual embeddings remain untested. |
| [Task21 identity](experiments/04_geometry_identity/README.md) | Five conditions on eleven provisional observations; geometry-only and combined conditions each resolve all eleven; appearance-only leaves four unresolved | Does not prove both evidence types always necessary. Task21 stays pending review. |
| [Task22 replay](experiments/05_replay/README.md) | Sixty-frame/457-proposal baseline plus six-frame/17-box automatic comparison; source-linked ID histories | Supplied poses; inspected POC. Task22 stays pending review. |

[Open the accepted Task22 viewer](experiments/05_replay/runs/20261004T152704.023370Z_84abb8b3b9594dcea8a1e5b2c8aced66/review.html). Its final publication is hash-verified; the preceding browser check and final browser-launch limitation remain in its README/receipts. Task30 did not repeat browser interaction.

[Task29 portable HTML](experiments/05_replay/runs/shareable/task22_20261004/task22_replay.html), [ZIP](experiments/05_replay/runs/shareable/task22_replay_20261004.zip), [all cup proposals](experiments/05_replay/runs/shareable/task22_20261004/cup_desk_observations.csv), [spread results](experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json) and [plot](experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.png) preserve the accepted source publication.

Nineteen desk cup proposals include sixteen assigned, three unresolved and two without position. On the sixteen assigned observations, box-median and centre-sample RMS spread are 72.8 mm and 82.3 mm; maximum pairwise distances are 291.7 mm and 317.0 mm. These are correlated, association-selected visible-surface measurements, not absolute physical-centre accuracy. The 30.8 mm before/return difference concerns only two views.

The baseline's 95 book proposals have one new ID, four matches and 90 unresolved outside the position gate. Once an old same-class track exists, the birth policy denies new IDs to later unmatched candidates. The baseline uses geometry-only association; this does not establish failed book appearance matching. Task31 owns the explicit policy comparison.

## Current data and acquisition gaps

Freiburg1 xyz and desk provide acquired RGB-D images, calibration, timestamps and motion-capture poses. TUM depth is a measured input with holes/noise, not a predicted depth model. Reference poses are deliberately consumed by the named supplied-pose controls. Estimated-pose comparisons remain unperformed; Task13's frozen settings/full sequence are untouched.

Desk return evidence includes cup-visible frame104 at 1305031457.091655, no cup pixels in frame268 at 1305031463.059810, and return frame359 at 1305031466.095840. Twenty-seven sampled views without YOLO cup detections are not twenty-seven physically absent views. The earlier xyz gap candidate still contained the cup and is not accepted absence evidence.

Task17 freezes two enrollment and four evaluation frames, with no validation partition. These are already inspected within-session examples. Similar monitors supply a limited distinct-object case. Controlled lighting/rotation, moved objects, full-occlusion recovery, identical objects in disjoint views, new sessions, phone capture and origin resets require additional evidence. TUM has no acquired independent dense surface or surveyed desk-object centres; ICL's synthetic surface score cannot be transferred to this replay.

The existing adapter retains positive depth below 4 m. Missing or excluded depth means unknown position. Longer-range indoor/outdoor claims need a new independently assessed data/adapter condition, not a silent cutoff change.

## Implemented ownership

The following folders exist and have bounded results; their contents are not still a proposed scaffold.

```text
06_object_recognition/
  src/identity_store.py            checked decisions and atomic persistence
  shared/                         observation, manifest and pose-revision contracts
  datasets/                       frozen provisional desk reference and preparation
  pilot/                          single-view xyz mapping and 60-frame desk replay
  experiments/
    01_detection/                 cached detector scoring
    02_segmentation/              classical support comparison
    03_appearance/                ZNCC/local features/existing YOLO embeddings
    04_geometry_identity/         supplied-input identity comparisons
    05_replay/                    synchronized viewer and portable evidence
```

Reuse the [existing checked identity store](src/identity_store.py), [shared object agreements](shared/README.md) and [common geometry/run contracts](../shared/README.md). Do not introduce a second identity database, camera tracker or geometry library. The pose-revision sidecar contract exists; production of corrected camera paths and committed downstream rebuilds remains later work. Task25 owns camera comparison/correction after Task13; Task35 investigates its effect on object/surface estimates.

## Intended identity behaviour

Every detection retains a unique observation ID and immutable source evidence, including rejected and positionless detections. An unmatched plausible candidate can receive a provisional object ID. Possible duplicates remain explicit relationships until evidence supports unification; unification preserves both ID histories, aliases and decision provenance. A confident returning observation retains the existing object ID.

Provisional candidates, confirmed inventory and rejected detections are separate states. A detector class/score or first ID does not by itself confirm a physical object. Missing depth means unknown position, not an invented location or automatic rejection of all appearance evidence. Unknown world relationships cannot justify metric merging.

Use one-to-one assignment within a view, with an explicit unmatched option. Distinct independently checked foreground supports visible together constrain separate objects; overlapping duplicate boxes alone do not. Identical objects seen only in separate views can remain ambiguous. Task31 will compare this behaviour against the existing restrictive policy rather than silently modifying the completed baseline.

## Evidence flow and future replacements

Solid arrows are exercised paths; dashed arrows are planned comparisons or correction/evaluation additions.

```mermaid
flowchart TD
    I["Benchmark RGB-D, calibration, capture times: acquired"] --> D["YOLO26x boxes: completed bounded POC"]
    D --> M["Optional support: rectangles/classical masks tested; learned planned"]
    I --> M
    M --> G["Depth-supported camera points: completed POC"]
    I --> G
    P["Supplied TUM poses: named control"] --> W["World surface observations: completed POC"]
    G --> W
    D --> A["Appearance: ZNCC/YOLO tested; ResNet50/context planned"]
    I --> A
    A --> ID["Identity rules: bounded Task21/22; Task31 policy planned"]
    W --> ID
    ID --> H["Individual observations and ID histories: completed POC"]
    H --> F["Position/shape estimates: medians tested; calibrated fusion planned"]
    W --> S["Growing point surface: completed POC"]
    H --> V["Accepted replay and portable exports: completed"]
    S --> V
    F --> V
    T["Further observations: sequential comparison planned"] -.-> H
    C["Estimated poses: short Task05 control; Task13 unfinished"] -.-> W
    Q["Task25 pose correction: planned"] -.-> W
    Q -.-> F
    Q -.-> S
    U["Task32 uncertainty supports: planned"] -.-> ID
    U -.-> F
    R["Independent identity/mask/anchor/extent/surface references: Task40 gaps"] -.-> E["Independent scoring: planned broader evaluation"]
    ID -.-> E
    F -.-> E
    S -.-> E
```

Uncertainty about an anchor, geometry of its visible surface and hypotheses about complete dimensions are different records. Detector confidence, cosine scores and raw point spread are not calibrated probabilities. Planned spatial support comparisons include simple regions and multiple foreground/background hypotheses.

## Scoped next investigations

The [task board](../../task_list/README.md#next-experiment-order-and-gaps) owns priorities and dependencies. [Research coverage](../../research/README.md#research-agenda-4-october-2026) provides sources and platform distinctions.

| Workstream | Owner | Isolated comparison and decision |
|---|---|---|
| A: IDs and possible duplicates | Task31 | Restrictive births versus provisional candidates, one-to-one matching and explicit duplicate relationships; decide auditable inventory behaviour |
| B: Spatial uncertainty | Task32 | Centre gates versus spatial supports/distributions with checked masks/poses; decide whether claimed uncertainty predicts independent errors |
| C: Appearance/spatial association | Task33 | ZNCC/current YOLO/proposed ResNet50/context; object-only versus context, then spatial/appearance ablations; decide evidence/cost trade-offs |
| D: Segmentation/position/size | Task34 | Rectangles/classical/independently checked masks, learned methods only when authorised; decide if masks improve error or just change samples |
| E: Error and sequential fusion | Task35 | Separate pixel/depth/calibration/pose perturbations, then combined; single view versus growing estimates; decide when extra views help or reinforce bias |
| F: Surface display/reconstruction | Task36 | Points, patches, fused/textured meshes, photogrammetry, Gaussian/NeRF; score geometry separately from realism |
| G: AR/VR room mapping | Task37 | ARCore data/API capability; Apple LiDAR controls only with hardware access; decide transferable capture/correction/revisit techniques |
| H: Driving/longer range | Task38 | Research camera/stereo/LiDAR and stationary versus moving-object evaluation; decide data/sensor acquisition |
| I: Later review/measurement application | Task39 | Requirements only: 3D pick-to-source histories and measurement displays; decide review workflow separately from accuracy |
| Shared independent references | Task40 | Design/acquire checked identities/masks, physical anchors/extents/surfaces and new-session hard cases after owner authorisation |

No follow-up runs in Task30. Completed Tasks17-20/27-29 remain historical evidence. Task09 remains the inventory umbrella; Task16/21/22 remain pending review. Tasks23/24 retain their unfinished review/build scopes, and Task25 remains behind Task13.

## Proposed comparison protocol

Task16's [broader shortlist/protocol](../../task_list/pending_review/16_research_segmentation_recognition_and_camera_corre.md) remains pending review. Its RF-DETR/YOLO nano, compact learned masks, DINO and camera-loop comparisons were not all executed. The [research shortlist](../../research/README.md#ranked-shortlist) is a dated source review, not a new model acquisition instruction. ResNet50 is an additional proposed appearance control, not a Task20 result.

Freeze source-session splits before tuning. Keep nearby frames, derivatives and augmentations together. Independent human-checked labels/reference measurements score the methods after predictions; an independently checked foreground mask used as a method input is an explicitly labelled oracle control. Use separate validation and held-out sessions for threshold selection and calibration. A single inspected session supports only a narrow descriptive claim.

Start with stationary objects and supplied poses. Compare rectangle and foreground supports without changing depth/poses; compare spatial models without changing appearance; compare appearance on fixed crops/supports before mixing it with geometry. Introduce estimated depth/poses and pose corrections as separate conditions. Similarity used to nominate a camera correction cannot also be independent evidence confirming the same match.

Report false merges, splits, duplicates, unresolved cases, missed objects, return recovery and inventory precision/recall separately. For time-local moving tracks, report tracking metrics separately from persistent stationary inventory. Report absolute anchor error, visible-surface repeatability and complete-object size error only when their respective independent references exist.

Current 0.35 m position and 0.80 cosine gates and equal combined-cost weights are exploratory inherited settings. They are not validated operating rules. Future settings, resource caps and decision thresholds require the owning task's recorded review/authorisation; no threshold is selected in this documentation session.

## Costs, corrections and limitations

Record model loading/warmup separately from feature/inference calls, depth selection/projection, assignment, persistence, robust fusion, pose correction/rebuild, evaluation and verified publication. Include full run cost, failures, acquisition/annotation labour, peak host/device memory and storage. Task20's recorded timings include GPU warmup; Task19's desktop totals are not repeat-benchmarked mobile results.

Retain original observations/pose revisions. Corrected poses must recompute or invalidate affected world observations, object estimates and surfaces in a new committed generation. Interrupted corrections cannot mix revisions; original runs and ID histories remain readable. These are proposed downstream guarantees, not a completed correction experiment.

Phone capture/energy/thermal behaviour, construction-site accuracy and longer-range operation remain untested. No packages, weights, inference, training, full Task13 sequence or experiment-code changes are part of Task30.
