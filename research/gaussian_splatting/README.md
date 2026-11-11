# Gaussian splatting: photo-realistic scenes from phone captures

How a phone capture becomes a scene that looks like a photograph from any angle, and which parts of that chain this project can reuse. Started 8 November 2026 after the owner saw a demo of Lumina, a commercial iPhone-capture and desktop-training product.

A **Gaussian splat** is a small soft blob with a position, orientation, width, colour and transparency. **Splat training** adjusts many thousands of them until renders match the photos from the recorded camera poses. It looks right but is not by itself a measurement: depth from the phone is needed to keep the shape true. Drawing an existing surface as splats, as the project's viewer does, is a different thing and is covered in [surface Gaussian viewing](../3d_vision_fundamentals/surface_gaussian_viewing.md).

**Status: deferred (owner, 8 November 2026).** The project's measure is the dimensional accuracy of objects that YOLO detects and places in 3D. Splat scenes look right but do not improve that, so this topic is a reference and will probably not be tried. No iPhone is available, so the iPhone-only products here (Lumina, Echo-3) cannot be tested either.

## Notes

| Note | What it covers |
|---|---|
| [lumina_open_source_parts.md](lumina_open_source_parts.md) | Lumina's pipeline step by step, the open-source part for each step with licence and hardware, what this project can take, and two questions for the owner. Start here |
| [generative_repair.md](generative_repair.md) | ArtiFixer and World-from-Motion: video diffusion models that repaint thin parts of a splat scene. Reference only: the new content is invented |
| [idol.md](idol.md) | One photo to a generated 3D object, including unseen sides. Possible object previews; no published metric accuracy or persistent counting result. Assessed 10 November 2026 |
| [Lumina product note](../products/e2e_product_research/09_lumina/README.md) | The product itself, in the same layout as the other product notes |
| [SpAItial Echo-3 product note](../products/e2e_product_research/10_spaitial_echo3/README.md) | iPhone video, no LiDAR needed, to a metric splat scene with generated fill, processed in the cloud; free routes, terms and open counterparts (8 November) |
| [Feed-forward splat models](../feed_forward_3d/feed_forward_splats.md) | YoNoSplat, AnySplat, WorldMirror, Depth Anything 3: a splat scene in one pass, without per-scene training |

Related notes elsewhere: [LingBot-Map](../feed_forward_3d/lingbot_map.md) and [SLAM3R](../feed_forward_3d/slam3r.md) (streaming 3D from plain video), [Scaniverse](../products/e2e_product_research/08_scaniverse/README.md) (splats trained on the phone), [surface clean-up](../surface_denoising/README.md) (floaters, including splat floater papers and [DN-Splatter](../surface_denoising/papers/turkulainen2025_dn_splatter.pdf)).

## Papers

Saved 8 November 2026 from arXiv or the authors' pages. Each title was checked against the PDF's first page. PDFs are not in Git. Results are the authors' claims.

| File | Why it is here |
|---|---|
| [kerbl2023_3dgs_2308.04079.pdf](papers/kerbl2023_3dgs_2308.04079.pdf) | The original 3D Gaussian Splatting method (SIGGRAPH 2023) |
| [pocketgs_2601.17354.pdf](papers/pocketgs_2601.17354.pdf) | PocketGS: splat training entirely on an iPhone 15 from ARKit or ARCore poses; about 4 minutes, under 3 GB. No code found |
| [ags_mesh_2411.19271.pdf](papers/ags_mesh_2411.19271.pdf) | AGS-Mesh (3DV 2025): rejects phone depth and normals that views disagree on; indoor rooms from smartphones |
| [densifybeforehand_2511.19294.pdf](papers/densifybeforehand_2511.19294.pdf) | Starting splats from LiDAR plus learned depth instead of growing them in training |
| [gs_icp_slam_2403.12550.pdf](papers/gs_icp_slam_2403.12550.pdf) | GS-ICP SLAM (ECCV 2024, MIT): live splat map from RGB-D, up to 107 fps on an RTX 4090 |
| [rtg_slam_2404.19706.pdf](papers/rtg_slam_2404.19706.pdf) | RTG-SLAM (SIGGRAPH 2024, GPL-3.0): about 16 fps with an Azure Kinect on large real rooms |
| [splatam_2312.02126.pdf](papers/splatam_2312.02126.pdf) | SplaTAM (CVPR 2024, BSD-3): RGB-D splat SLAM with an iPhone demo; slow |
| [monogs_2312.06741.pdf](papers/monogs_2312.06741.pdf) | Gaussian Splatting SLAM, "MonoGS" (CVPR 2024): non-commercial licence |
| [2dgs_2403.17888.pdf](papers/2dgs_2403.17888.pdf) | 2D Gaussian Splatting: flat splats for accurate surfaces |
| [pgsr_2406.06521.pdf](papers/pgsr_2406.06521.pdf) | PGSR: plane-based splats for surface reconstruction |
| [milo_2506.24096.pdf](papers/milo_2506.24096.pdf) | MILo: mesh built during splat training, with an indoor setting |
| [cloud2bim_2503.11498.pdf](papers/cloud2bim_2503.11498.pdf) | Cloud2BIM (Automation in Construction 2025): point cloud to a building model with walls and openings, the open counterpart of Lumina's floor plans |
| [artifixer_siggraph2026.pdf](papers/artifixer_siggraph2026.pdf) | ArtiFixer (NVIDIA, SIGGRAPH 2026): diffusion repair of splat renders |
| [world_from_motion_2607.01202.pdf](papers/world_from_motion_2607.01202.pdf) | World-from-Motion (NeurIPS 2026): diffusion repair for scenes with motion |
| [difix3d_plus_2503.01774.pdf](papers/difix3d_plus_2503.01774.pdf) | Difix3D+ (NVIDIA, CVPR 2025): one-step diffusion cleans renders in thinly captured areas; non-commercial licence |
