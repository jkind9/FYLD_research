# Research evidence

Original source review: 1 October 2026. [Recovered Claude research](session_recovery/README.md), added on 2 October, records missing edge SLAM sources, phone capture requirements, source corrections and unresolved leads. It also preserves the supplied trace. Read that addendum alongside the older tables; their unknown fields have not all been revised. Paper results are publisher claims, not results reproduced by this project.

Start with the [reading guide and 21 individual source summaries](sources/README.md). The [background explanation](sources/00_start_here.md) introduces depth, camera movement, reconstruction and the different measurements needed to assess a site map.

The current [six-piece experiment plan](../experiments/README.md) connects research to independent tests. Start with verified geometry and supplied-input reconstruction; inspect phones alongside this work. The new [object recognition and persistent counting plan](../experiments/06_object_recognition/README.md) relates the supplied recognition papers to multi-view labels, moving-feature removal and revisit identities. Its ScienceDirect source remains unverified. The [dataset guide](../experiments/datasets/README.md) explains reference inputs for each stage. Earlier implementation and local outputs are preserved in [the prototype archive](../archive/task00_prototype/README.md).

| File | Purpose |
| --- | --- |
| [edge_products/README.md](edge_products/README.md) | Commercial stereo/edge mapping routes, actual map-rate evidence and a shared approach to worksite measurement and distinct-object counting |
| [orb_slam/README.md](orb_slam/README.md) | ORB-SLAM3 as a central tracking reference, current alternatives, 2026 edge implementations and fair benchmark comparisons |
| [session_recovery/README.md](session_recovery/README.md) | Findings recovered from the interrupted Claude session, evidence status, experiment connections and original trace |
| [literature_review.md](literature_review.md) | Primary sources and what they establish |
| [papers.csv](papers.csv) | Searchable evidence table; unknown fields stay explicit |
| [sources.bib](sources.bib) | Verified bibliographic fields |
| [method_comparison.md](method_comparison.md) | Input requirements and evaluation choices |
| [licences.md](licences.md) | Separate code, weight and dataset permissions |
| [dataset_catalog.md](dataset_catalog.md) | Calibration, ground truth and dataset suitability |
| [roadmap.md](roadmap.md) | Later experiments and completion evidence |
| [limitations.md](limitations.md) | Boundaries of the present demonstration |
| [repositories.json](repositories.json) | Pinned reference checkouts and execution status |

The colour/depth baseline uses supplied images from TUM. Its metric scale comes from those depth images. A separate preliminary image-only experiment has arbitrary scale. Final implementation validation remains pending; do not substitute paper benchmarks for local measurements.

The proposed area output describes observed surfaces. Unseen space remains unknown. It does not establish safe clearance, hidden utilities, structural condition or whether a person can safely enter an area.
