# Feed-forward splat models: a splat scene from many frames in one pass

**Take-away:** four open model families predict a Gaussian splat scene from a set of frames in seconds, with no per-scene training. YoNoSplat and AnySplat are MIT-licensed. YoNoSplat can take this project's ARCore poses and intrinsics as input, which makes it the best fit to try first. WorldMirror takes poses, intrinsics and depth, and outputs the closest match to SpAItial Echo-3's exports, but its licence does not cover use in the UK. Depth Anything 3's splat output is non-commercial. None outputs metres by itself. All need a GPU. Added 8 November 2026 while reviewing [SpAItial Echo-3](../products/e2e_product_research/10_spaitial_echo3/README.md). Nothing was run.

**Status: deferred (owner, 8 November 2026).** The project's measure is the dimensional accuracy of objects that YOLO detects and places in 3D. Splat scenes do not serve that, so these models are kept as references and will probably not be tried.

Terms: a **Gaussian splat** is a small soft blob with a position, orientation, width, colour and transparency; many thousands of them show a scene that looks like a photograph from any angle. **Feed-forward** means the network outputs the result in one pass, unlike [splat training](../gaussian_splatting/README.md), which adjusts the blobs for minutes to hours per scene. A **prior** here is extra input the model can use if given, such as known camera poses.

## The models

| | YoNoSplat | AnySplat | WorldMirror 1 and 2 | Depth Anything 3 (Giant) |
|---|---|---|---|---|
| Paper | [arXiv 2511.07321](papers/yonosplat_2511.07321.pdf), ICLR 2026 | [arXiv 2505.23716](papers/anysplat_2505.23716.pdf) | [arXiv 2510.10726](papers/worldmirror_2510.10726.pdf), ICML 2026; version 2 in [HY-World 2.0, arXiv 2604.14268](papers/hy_world_2_2604.14268.pdf) | [arXiv 2511.10647](papers/depth_anything_3_2511.10647.pdf) |
| Group | ETH Zurich and Microsoft | Shanghai AI Laboratory and others | Tencent Hunyuan | ByteDance Seed |
| Code | [cvg/YoNoSplat](https://github.com/cvg/YoNoSplat) | [OpenRobotLab/AnySplat](https://github.com/OpenRobotLab/AnySplat) | [HunyuanWorld-Mirror](https://github.com/Tencent-Hunyuan/HunyuanWorld-Mirror), [HY-World-2.0](https://github.com/Tencent-Hunyuan/HY-World-2.0) | [Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) |
| Licence | MIT (code; the model card also lists MIT) | MIT, code and models | Tencent community licence; see below | Code Apache-2.0; splat-capable checkpoints CC BY-NC 4.0 |
| Input | Any number of images, posed or unposed, with or without intrinsics | Unposed, uncalibrated images or video | Images or video, with any mix of poses, intrinsics and depth | Images or video, optional poses and intrinsics |
| Output | Splats, camera poses, intrinsics, rendered depth | Splats, depth, camera poses and intrinsics | Splats, depth, normals, point maps, camera poses and intrinsics | Depth, confidence, poses, intrinsics, splats (Giant models only) |
| Speed and size | 100 views at 280 × 518 in 2.69 s on an NVIDIA GH200. Checkpoints trained at 224 × 224 on RealEstate10K or DL3DV, 2–32 views | "hundreds of input views" in "a few seconds" | Splat output at 518 × 378 on one H20: 7.6 GB for 16 views, 17.8 GB for 64, 60.5 GB for 256; 360 views at most. WorldMirror 2 has about 1.2B parameters | Giant: 1.15–1.40B parameters |
| Metric scale | No. Scale is normalised in training; given intrinsics help | No | No; intrinsics "resolve scale ambiguity", poses fix it | Only the metric and nested models; the nested Giant output "is already in meters" |

## Licence limits that matter here

- **WorldMirror and HY-World 2.0.** Both licences open with "THIS LICENSE AGREEMENT DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA". Clause 5(c) forbids using the model, its outputs or results outside that territory. A product with over 1 million monthly users needs a separate licence from Tencent. So use from the UK is not licensed, even for research.
- **Depth Anything 3.** Only the Giant checkpoints have the splat output, and they are CC BY-NC 4.0 (non-commercial). The Small, Base and Metric-Large models are Apache-2.0 but output no splats.
- **YoNoSplat and AnySplat.** MIT, no limits on territory or use.

## Other projects found in the same search

Not checked in detail:

- [StreamSplat](https://pypi.org/project/streamsplat/) (ICLR 2026): feed-forward splats from uncalibrated video as it arrives, aimed at moving scenes. No metres.
- [vid2scene](https://github.com/samuelm2/vid2scene): phone video to a splat scene by structure from motion (GLOMAP or VGGT), then gsplat training. Not feed-forward.
- [SculptForge](https://radiancefields.com/sculptforge-trains-gaussian-splats-from-phone-video): trains splats from phone video on the user's own machine with COLMAP and Brush. Not feed-forward.

## How one would fit this project, if splats are ever wanted

1. Pick 16–32 frames from a Redmi walk, spread along the path.
2. Run YoNoSplat with the ARCore poses and intrinsics as priors, so the scene comes out in ARCore's metres.
3. Compare the splat centres and rendered depth with the fused surface of the same walk, and the renders with held-out frames.
4. Try AnySplat on the same frames without poses, then fit its poses to ARCore's to set the scale. The gap between the two runs shows how much the phone poses help.

All four need an NVIDIA GPU. Under the current CPU-only rule this would be a laptop experiment on the RTX 4060 (8 GB), if the owner calls it essential. WorldMirror's figure of 7.6 GB for 16 views suggests that size of run is near the laptop's limit.

## Relation to other notes

- These models predict splats; [VGGT](vggt.md), [LingBot-Map](lingbot_map.md) and [SLAM3R](slam3r.md) predict points and poses. WorldMirror and Depth Anything 3 do both.
- Generated fill for areas the capture missed is a separate step: [generative repair](../gaussian_splatting/generative_repair.md) and Difix3D+ in the [gaussian splatting papers](../gaussian_splatting/README.md#papers).
