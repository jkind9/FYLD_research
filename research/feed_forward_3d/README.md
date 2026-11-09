# Feed-forward 3D models

Networks that output 3D points, depth and camera poses for many frames in one pass. Task74 scores the ones with usable licences.

## Notes

| Note | What it covers |
|---|---|
| [vggt.md](vggt.md) | VGGT |
| [vggt_omega.md](vggt_omega.md) | VGGT-Omega |
| [infinite_vggt.md](infinite_vggt.md) | InfiniteVGGT: streaming input |
| [lingbot_map.md](lingbot_map.md) | LingBot-Map: pose and depth per frame from plain video as it arrives; 12 fps on an RTX 4090; Apache-2.0; no metres (8 November) |
| [lingbot_map_how_it_works.md](lingbot_map_how_it_works.md) | How LingBot-Map works (encoder, frame and global attention, anchor/window/summary memory, camera and depth heads, with parameter counts) and which parts this project can use. Its depth sized per frame by ARCore beat Depth Anything V2 on the same frames (8 November) |
| [slam3r.md](slam3r.md) | SLAM3R: dense points from plain video at 20+ fps on an RTX 4090D; non-commercial licence (8 November) |
| [feed_forward_splats.md](feed_forward_splats.md) | YoNoSplat, AnySplat, WorldMirror and Depth Anything 3: a splat scene from many frames in one pass, with licences; YoNoSplat (MIT) takes phone poses (8 November) |

## Papers

Saved 13 October 2026 from arXiv or the authors' pages. Paper results are the authors' claims.

| File | Why it is here |
|---|---|
| [vggt_2503.11651.pdf](papers/vggt_2503.11651.pdf) | VGGT, CVPR 2025 |
| [mapanything_2509.13414.pdf](papers/mapanything_2509.13414.pdf) | MapAnything: metric 3D; an Apache-2.0 checkpoint exists |
| [depth_anything_3_2511.10647.pdf](papers/depth_anything_3_2511.10647.pdf) | Depth Anything 3: depth and poses from any views; Small and Base are Apache-2.0 |
| [dust3r_mast3r_vggt_aerial_evaluation_2507.14798.pdf](papers/dust3r_mast3r_vggt_aerial_evaluation_2507.14798.pdf) | Independent check of DUSt3R, MASt3R and VGGT against classic methods |
| [lingbot_map_2604.14141.pdf](papers/lingbot_map_2604.14141.pdf) | LingBot-Map, saved 8 November 2026 |
| [slam3r_2412.09401.pdf](papers/slam3r_2412.09401.pdf) | SLAM3R, CVPR 2025, saved 8 November 2026 |
| [yonosplat_2511.07321.pdf](papers/yonosplat_2511.07321.pdf) | YoNoSplat, ICLR 2026: splats from posed or unposed images; saved 8 November 2026 |
| [anysplat_2505.23716.pdf](papers/anysplat_2505.23716.pdf) | AnySplat: splats from unposed images; saved 8 November 2026 |
| [worldmirror_2510.10726.pdf](papers/worldmirror_2510.10726.pdf) | WorldMirror, ICML 2026: splats, depth, normals and cameras, with optional pose, intrinsics and depth input; saved 8 November 2026 |
| [hy_world_2_2604.14268.pdf](papers/hy_world_2_2604.14268.pdf) | HY-World 2.0, including WorldMirror 2.0 and generated world expansion; saved 8 November 2026 |

## Course lectures

From the 3D vision course in [3d_vision_fundamentals](../3d_vision_fundamentals/README.md).

| Lecture | Covers |
|---|---|
| [14_applications_of_3d_computer_vision_and_graphics.pdf](../3d_vision_fundamentals/lectures/14_applications_of_3d_computer_vision_and_graphics.pdf) | Feed-forward reconstruction with VGGT |
