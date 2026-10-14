# Research reading guide

This guide orders the 21 source notes, which now sit in the topic folders listed in the [research README](README.md). Each note explains the idea, the evidence, its limits and its relevance to capturing a work area. Research papers, official developer documentation, dataset descriptions and product context are identified separately.

Start with [the background explanation](start_here.md). Then read the construction capture paper, MobiDepth and the TUM dataset note. Together they explain capture quality, phone depth and how to evaluate a first reconstruction.

## Recommended first reading

| Order | Source | What you should get from it |
|---|---|---|
| 1 | [Construction capture guidance](construction_site_context/construction_capture_guidance.md) | Why useful viewpoints matter before reconstruction |
| 2 | [MobiDepth](depth_estimation/mobidepth.md) | How phone camera differences and timing affect depth |
| 3 | [TUM RGB-D](datasets_and_benchmarks/tum_rgbd.md) | What a controlled tracking benchmark can establish |
| 4 | [Open3D RGB-D](camera_tracking_and_slam/open3d_rgbd.md) | How depth observations become a shared reconstruction |
| 5 | [COLMAP](structure_from_motion/colmap.md) | What overlapping ordinary images can reconstruct |
| 6 | [Construction progress from top-down images](construction_site_context/construction_orthographic_progress.md) | How map interpretation differs from geometric accuracy |

## Phone depth and capture APIs

| Source | Main question |
|---|---|
| [MobiDepth](depth_estimation/mobidepth.md) | Can two phone cameras produce depth fast enough? |
| [HiMoDepth](depth_estimation/himodepth.md) | Can phone stereo preserve more image detail? |
| [MobileStereoNet](depth_estimation/mobilestereonet.md) | How can a learned stereo network become smaller? |
| [BANet](depth_estimation/banet.md) | What does a newer mobile stereo model offer? |
| [HyperSight](depth_estimation/hypersight.md) | Can camera motion help with longer-range depth? |
| [ARCore Raw Depth](phone_ar_platforms/arcore_raw_depth.md) | What depth and confidence does Android expose? |
| [Apple RoomPlan](phone_ar_platforms/apple_roomplan.md) | What does an indoor LiDAR room API actually provide? |

## Reconstructing several views and tracking movement

| Source | Main question |
|---|---|
| [VGGT](feed_forward_3d/vggt.md) | Can a learned model jointly estimate several geometric quantities? |
| [VGGT-Omega](feed_forward_3d/vggt_omega.md) | How does the newer release extend that route? |
| [InfiniteVGGT](feed_forward_3d/infinite_vggt.md) | How can reconstruction handle longer image sequences? |
| [COLMAP](structure_from_motion/colmap.md) | What does conventional image reconstruction require? |
| [RTAB-Map](camera_tracking_and_slam/rtabmap.md) | How can revisiting a place reduce accumulated drift? |
| [Open3D RGB-D](camera_tracking_and_slam/open3d_rgbd.md) | How can supplied depth support tracking and fusion? |
| [MASt3R-SLAM](camera_tracking_and_slam/mast3r_slam.md) | Can learned image matching support an online map? |

## Datasets and evaluation

| Source | What it helps test |
|---|---|
| [TUM RGB-D](datasets_and_benchmarks/tum_rgbd.md) | Camera tracking with colour, depth and reference poses |
| [ETH3D](datasets_and_benchmarks/eth3d.md) | Stereo and reconstruction against independent references |
| [EuRoC MAV](datasets_and_benchmarks/euroc_mav.md) | Camera tracking with synchronized stereo and motion sensors |
| [ICL-NUIM](datasets_and_benchmarks/icl_nuim.md) | Tracking and, where available, surfaces in controlled synthetic scenes |

## Construction use and product context

| Source | Why it is included |
|---|---|
| [Construction capture guidance](construction_site_context/construction_capture_guidance.md) | Real-site evidence about collecting useful photographs |
| [Construction progress from top-down images](construction_site_context/construction_orthographic_progress.md) | A downstream use for reconstructed views |
| [FYLD public context](construction_site_context/fyld_public_context.md) | Potential users and decisions; company context rather than technical validation |

## Reading cautions

Processing rates from different papers are not a fair ranking when hardware, resolution or included stages differ. A code licence does not automatically cover trained weights or datasets. Check the note's permission status before selecting a company experiment.

Sources were checked on 1 October 2026. Most methods have not been reproduced locally. Open questions are retained so the next experiment can test them instead of treating them as established facts.
