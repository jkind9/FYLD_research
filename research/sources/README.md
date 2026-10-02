# Research reading guide

This collection has one Markdown note for each of 21 sources. Each note explains the idea, the evidence, its limits and its relevance to capturing a work area. Research papers, official developer documentation, dataset descriptions and product context are identified separately.

Start with [the background explanation](00_start_here.md). Then read the construction capture paper, MobiDepth and the TUM dataset note. Together they explain capture quality, phone depth and how to evaluate a first reconstruction.

## Recommended first reading

| Order | Source | What you should get from it |
|---|---|---|
| 1 | [Construction capture guidance](19_construction_capture_guidance.md) | Why useful viewpoints matter before reconstruction |
| 2 | [MobiDepth](01_mobidepth.md) | How phone camera differences and timing affect depth |
| 3 | [TUM RGB-D](15_tum_rgbd.md) | What a controlled tracking benchmark can establish |
| 4 | [Open3D RGB-D](13_open3d_rgbd.md) | How depth observations become a shared reconstruction |
| 5 | [COLMAP](11_colmap.md) | What overlapping ordinary images can reconstruct |
| 6 | [Construction progress from top-down images](20_construction_orthographic_progress.md) | How map interpretation differs from geometric accuracy |

## Phone depth and capture APIs

| Source | Main question |
|---|---|
| [MobiDepth](01_mobidepth.md) | Can two phone cameras produce depth fast enough? |
| [HiMoDepth](02_himodepth.md) | Can phone stereo preserve more image detail? |
| [MobileStereoNet](03_mobilestereonet.md) | How can a learned stereo network become smaller? |
| [BANet](04_banet.md) | What does a newer mobile stereo model offer? |
| [HyperSight](05_hypersight.md) | Can camera motion help with longer-range depth? |
| [ARCore Raw Depth](06_arcore_raw_depth.md) | What depth and confidence does Android expose? |
| [Apple RoomPlan](07_apple_roomplan.md) | What does an indoor LiDAR room API actually provide? |

## Reconstructing several views and tracking movement

| Source | Main question |
|---|---|
| [VGGT](08_vggt.md) | Can a learned model jointly estimate several geometric quantities? |
| [VGGT-Omega](09_vggt_omega.md) | How does the newer release extend that route? |
| [InfiniteVGGT](10_infinite_vggt.md) | How can reconstruction handle longer image sequences? |
| [COLMAP](11_colmap.md) | What does conventional image reconstruction require? |
| [RTAB-Map](12_rtabmap.md) | How can revisiting a place reduce accumulated drift? |
| [Open3D RGB-D](13_open3d_rgbd.md) | How can supplied depth support tracking and fusion? |
| [MASt3R-SLAM](14_mast3r_slam.md) | Can learned image matching support an online map? |

## Datasets and evaluation

| Source | What it helps test |
|---|---|
| [TUM RGB-D](15_tum_rgbd.md) | Camera tracking with colour, depth and reference poses |
| [ETH3D](16_eth3d.md) | Stereo and reconstruction against independent references |
| [EuRoC MAV](17_euroc_mav.md) | Camera tracking with synchronized stereo and motion sensors |
| [ICL-NUIM](18_icl_nuim.md) | Tracking and, where available, surfaces in controlled synthetic scenes |

## Construction use and product context

| Source | Why it is included |
|---|---|
| [Construction capture guidance](19_construction_capture_guidance.md) | Real-site evidence about collecting useful photographs |
| [Construction progress from top-down images](20_construction_orthographic_progress.md) | A downstream use for reconstructed views |
| [FYLD public context](21_fyld_public_context.md) | Potential users and decisions; company context rather than technical validation |

## Reading cautions

Processing rates from different papers are not a fair ranking when hardware, resolution or included stages differ. A code licence does not automatically cover trained weights or datasets. Check the note's permission status before selecting a company experiment.

Sources were checked on 1 October 2026. Most methods have not been reproduced locally. Open questions are retained so the next experiment can test them instead of treating them as established facts.
