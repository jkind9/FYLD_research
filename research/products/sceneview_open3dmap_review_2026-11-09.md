# SceneView and Open3Dmap against this project's next steps

Reviewed 9 November 2026. **SceneView is a strong source-code reference for our Android room and object pipeline. Open3Dmap is a lower-priority workflow reference. Neither has been tested here, and neither source review establishes a drop-in replacement.**

Detailed evidence: [SceneView](../phone_ar_platforms/sceneview.md) and [Open3Dmap](e2e_product_research/11_open3dmap/README.md). The [repository register](../repositories.json) records exact commits and review status. Those notes pin source links and separate inspected code, upstream claims and project inference.

## The comparison

| Our requirement | SceneView | Open3Dmap |
|---|---|---|
| Ordinary Android capture | ARCore-based SDK and room-scan demo | ARCore/legacy Sceneform capture app |
| Learned shape scaled into metres | ML depth module robustly fits relative inverse depth to ARCore plane/feature anchors | No demonstrated metric constraint in the reviewed image-to-COLMAP converter |
| Deal with old depth | Explicit freshness states and diagnostics; fallback admits late distinct maps after starvation | No comparable depth-fusion policy established in reviewed flow |
| Build surfaces on a phone | Kotlin surfel fusion and bounded sparse TSDF in demo code | Cloud sparse reconstruction, then advertised browser splat training |
| Count repeated object sightings once | Room-review detector, 3D lifting and surface/footprint merging exist | No corresponding counter established |
| Our target classes | Furniture-oriented map; needs extension for cones/barriers | No detector established |
| Reuse terms | Apache-2.0 repository; model and ARCore terms remain separate | CC BY-NC 4.0 root; SplatJSON document separately states MIT |
| Evidence limit | No Redmi or project-recording measurements | Missing referenced WASM artefacts; cloud has labelled mock-success path; no project measurements |

Primary entry points: [SceneView overview](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/README.md), [Open3Dmap overview](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/README.md). The detailed notes cite the implementation behind each row.

## What this adds to what we already know

The [current design](../../DESIGN.md) uses ARCore pose, learned depth, metric sizing, fragment fusion, cleanup and objects. The owner put the refactor before new experiments on 8 November. The same decision kept ARCore depth as the metric reference and deferred photo-realistic splat output. On 9 November the owner reopened the refactor's timing. The recommendation below distinguishes the shared-pipeline move from the later interface and Android moves.

SceneView supplies Android examples for several missing product details: bounded scale hold, capture-time pose attached to delayed inference, memory limits and user feedback. It also supplies an alternative to our current centre-distance object association. Its room-scan implementation means we should no longer describe it only as a model viewer. The code is a reason to benchmark it; it is not a result showing that Android distinct-object counting or dimensional accuracy is solved.

Open3Dmap demonstrates the intended phone/cloud/browser split, but its checked public tree does not substantiate the complete advertised workflow. It is also not an application built on the current SceneView SDK: the reviewed app depends on legacy Sceneform. Its cloud converter does not use our most useful input, a known metric ARCore path. The name does not connect it to the Open3D library in our Python pipeline.

## Ranked follow-up work

These are proposals, not experiments run or new commitments.

| Priority | Part to compare | Smallest useful check | What it would resolve |
|---|---|---|---|
| 1 | SceneView scale rejection and hold expiry | Replay the 14 and 15 October sessions; score supported and unsupported depth separately | Whether bad or carried scale can be stopped earlier |
| 2, after stable geometry and labels | SceneView object lifting and merging | Same poses, cloud and detections; compare shared-surface/footprint rules with our 0.35 m centre rule; label distinct chairs | Whether our overcount can fall without merging separate objects |
| 2 | SceneView phone implementation | Bounded Redmi demo/export check, then dimensional and sustained-cost measurements | Whether its code can become an Android baseline |
| 2 | Coverage and depth-starvation feedback | Map available telemetry to a few actionable capture prompts | Whether a walker can spot missing observations before ending a recording |
| 3 | SceneView LiteRT depth deployment | Same-frame comparison with our current Small metric model; include calibration and thermal cost | Feasibility of an Android port, not a presumed shape improvement |
| 4 | Open3Dmap quality and metadata design | Compare its quality scores and SplatJSON fields with our session contract | Reusable design ideas without taking on its backend |

Do not substitute SceneView's relative inverse-depth model for our metric model without changing the scale contract. Do not adopt its relaxed stale-depth fallback without replaying our doubled-surface failure. Do not equate a fitted object's box with its independently measured dimensions. These are the main transfer risks.

The [LingBot-Map comparison](../feed_forward_3d/lingbot_map_how_it_works.md) still asks a different question: whether a heavier multi-frame model improves depth shape. SceneView mostly contributes deployment, fitting, fusion and association patterns. Open3Dmap mostly contributes application workflow. Neither provides new evidence that far-depth scaling beyond ARCore's observed range is fixed.

## Reuse and licence decisions, 9 November 2026

This section is the adoption recommendation, distinct from the inspected-code facts in the two detailed notes. It updates the [project sequence](../../PROJECT_PLAN.md#next-steps) and the [design's transfer rules](../../DESIGN.md#713-learning-from-sceneview-and-open3dmap). No external source code was copied into the product in this task.

| Material | What we can take | Boundary |
|---|---|---|
| SceneView fitting, projection, fusion and object-merging source | Adapt selected Apache-2.0 files or port selected functions, after checking their own headers and dependencies | Record pinned source and local changes; meet the redistribution conditions. A translation does not remove attribution duties |
| SceneView scheduling and capture guidance | Use its source as a design reference for source-frame metadata, a single inference in flight, scale-hold expiry and useful capture prompts | Keep our current timing, pose-correction and measurement contracts. Do not inherit the stale-depth relaxation or filled geometry as measured truth |
| Depth Anything V2 Small | An upstream Apache-2.0 model family to compare for Android deployment | Check the exact metric/relative checkpoint, conversion and runtime. Base/Large/Giant upstream models have noncommercial terms. A family name or code licence does not clear every weight file |
| YOLOX-Tiny detector path | A candidate permissive detector control from the Apache-2.0 YOLOX project | Check the exact converted asset and its provenance. Furniture labels and lower compute do not establish target-class recall or parity with YOLO26x |
| Open3Dmap app/backend source | Reference only for the proposed proprietary FYLD route unless separate permission is obtained | Its root CC BY-NC 4.0 licence covers noncommercial reuse. Private company research should not be assumed to be outside that condition |
| SplatJSON document and generic scan metadata | Consider needed fields such as provenance, location, transform and units | The document states MIT, but the reviewed root licence differs. Confirm the precise reusable artefact before copying a schema/example. Our own session format can express the requirements without adopting the app |

Apache-2.0 permits commercial adaptation and does not generally require publishing our own source. When distributing covered work, include the licence, preserve relevant source notices, mark changed files and carry over relevant upstream NOTICE attribution if supplied. Apply this to each adopted file and its dependencies, rather than treating a repository badge as an audit of every bundled artefact. Source: [SceneView's pinned Apache licence, section 4](https://github.com/sceneview/sceneview/blob/5ba0247805c4820629601153f84fda5e152c0a24/LICENSE).

Open3Dmap's root explicitly states CC BY-NC 4.0. That condition concerns the purpose of use, not just whether code is sold directly. Do not copy or translate the implementation into the proposed commercial product and call it independent code. Learn the requirements, then use our existing implementation or separately licensed upstream tools. Sources: [root licence](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/LICENSE), [Creative Commons legal code, sections 1 and 2](https://creativecommons.org/licenses/by-nc/4.0/legalcode.en). The [format's MIT statement](https://github.com/x4dqn/Open3Dmap/blob/f17dab79e72d47fa2e6286a33d1a1eb3b8ac6622/docs/splatjson-spec.md#license) has narrower stated scope.

Model terms checked against the [Depth Anything V2 authors' licence section](https://github.com/DepthAnything/Depth-Anything-V2#license) and [YOLOX licence](https://github.com/Megvii-BaseDetection/YOLOX/blob/main/LICENSE). These support candidate selection, not clearance of every downloaded conversion. SceneView pins conversion hashes in its source; no model file was downloaded or audited here.

There is also an existing dependency to resolve: our [detector acquisition record](../../experiments/06_object_recognition/pilot/README.md) and [loader](../../experiments/06_object_recognition/pilot/detector.py) use YOLO26x through Ultralytics. The record already marks deployment suitability unresolved. Ultralytics offers AGPL-3.0 and Enterprise terms; evaluate the applicable obligations, obtain suitable commercial terms, or select a separately licensed detector before proprietary deployment. AGPL is not a blanket ban on commercial use. Source: [Ultralytics licensing](https://www.ultralytics.com/license). Do not combine a detector replacement with the first association comparison, because that would change two causes at once.

## When to refactor

**Recommendation: begin with the baseline and the shared chain next.** More SceneView or Open3Dmap experiments are not needed to establish that session reading, depth, scale, fusion and cleanup should be shared. Waiting for every research question would make each new result harder to compare across the live and offline copies.

The stopping point for structural work is [DESIGN phases 0–3](../../DESIGN.md#11-migration-plan): identify and preserve the baseline, extract adopted stages, and make both pipelines reproduce it. Keep the experimental counter's current behaviour. No method changes belong in that move. Full-walk output, relevant tests and live update cost must pass before method trials resume.

After that check, first align the live path with the room build's established orientation, scale-grid and freshness fixes. Then test scale-support rejection and a bounded hold of the last scale. Continue the separate far-depth triangulation work. Object association follows stable geometry and labelled distinct objects. A refitted box is still an estimate until checked against independent dimensions.

The later CLI, receiver, viewer, Android folder move and repository cleanup should finish incrementally; their completion need not block these trials. A new phone recording, GPU slot or SceneView phone benchmark is not a prerequisite to the shared Python move. Read-only research and independent measurements can continue while a stage is being extracted, but changes to that stage wait until its move is verified.

This refines the earlier all-refactor-before-experiments wording. It does not record owner approval of a start date or start implementation. The remaining package/environment choices are still listed in the design.

## Review boundary

Inspected public repository metadata, complete file trees and selected source files at pinned revisions. Local comparison used the design, live sizing, room build and existing LingBot-Map findings. No builds, dependency installs, model downloads, cloud calls that execute jobs, APK runs, new recordings or reconstruction benchmarks were performed. All new material is research documentation.
