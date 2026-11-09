# Mobile3DRecon: live meshing from one phone camera

**Take-away:** Mobile3DRecon builds a room mesh live on 2018 mid-range Android phones from the ordinary camera and a visual-inertial tracker. Depth comes from multi-view stereo between keyframes about 0.6 m apart: the pixel is matched in earlier frames whose camera positions are known, then triangulated. It runs on one CPU thread in 70 ms per keyframe on a Snapdragon 710. This is the step the project's [far-depth review](../surface_denoising/README.md#getting-far-depth-right-what-other-systems-do) lists next for depth beyond ARCore's 2.5 m. No code was released. Added 8 November 2026 from an owner-supplied link; the paper was read in full; nothing was run.

## Citation and sources

Xingbin Yang, Liyang Zhou, Hanqing Jiang, Zhongliang Tang, Yuanbo Wang (SenseTime Research), Hujun Bao and Guofeng Zhang (State Key Lab of CAD&CG, Zhejiang University). "Mobile3DRecon: Real-time Monocular 3D Reconstruction on a Mobile Phone." IEEE Transactions on Visualization and Computer Graphics 26(12):3446-3456, December 2020, the ISMAR 2020 special issue. DOI 10.1109/TVCG.2020.3023634. The project page says it won the ISMAR 2020 best paper award.

- [Paper (Zhejiang University)](http://www.cad.zju.edu.cn/home/gfzhang/projects/mobile-3d-recon.pdf) · [project page with videos](https://zju3dv.github.io/mobile3drecon/) · [saved PDF](../surface_denoising/papers/yang2020_mobile3drecon.pdf) (saved earlier for the clean-up review)
- **Code: none released** (checked 8 November 2026). The project page links only the paper and one baseline method (DPSNet). The GitHub repository [sorcererq/mobile3drecon](https://github.com/sorcererq/mobile3drecon), owned by co-author Hanqing Jiang, holds only that web page. Papers with Code lists no repository.
- **Open code for the parts:**
  - Two-view semi-global matching: OpenCV `cv2.StereoSGBM`, installed here (OpenCV 5.0.0). It needs a rectified pair, which this paper avoids (step 3).
  - Growing TSDF volume: Open3D `ScalableTSDFVolume` and `VoxelBlockGrid`, installed (0.19.0). The project already uses the first.
  - Re-meshing only the parts that changed: [Voxblox](https://github.com/ethz-asl/voxblox) and [OpenChisel](https://github.com/personalrobotics/OpenChisel). CHISEL is the system the paper compares its meshing against.

## What it does

| Question | Answer |
|---|---|
| Input | Live video from the phone's one rear camera, and keyframe poses from a visual-inertial tracker (SenseTime's SenseAR SLAM). The authors write that "any other keyframe-based VIO or SLAM system such as ARCore can be used" |
| Output | A triangle mesh that grows as the user walks, updated at each keyframe. Used in Unity for AR occlusion and physics collisions |
| Hardware | OPPO R17 Pro (Snapdragon 710) and Xiaomi MI8 (Snapdragon 845). Depth runs on one back-end CPU thread and meshing on one CPU thread, so tracking and drawing keep the rest |
| Speed per keyframe | R17 Pro: 70.46 ms depth + 31.13 ms mesh = 101.59 ms. MI8: 38.32 + 18.89 = 57.21 ms. The tracker makes about 5 keyframes a second and tracks at more than 25 fps |
| Size | Metres, from the visual-inertial poses |
| Accuracy | Against the R17 Pro's own time-of-flight (ToF) depth on five indoor and outdoor sequences: depth RMSE 5.7-10.4 cm, mean absolute error 3.0-6.1 cm; mesh RMSE 4.2-5.6 cm (Table 1) |
| Not stated | Image size, depth range, number of depth levels, smoothing penalties |

## The parts, in order

1. **Keyframe poses.** The tracker follows every frame on the front end. A back-end process refines all keyframe poses together and feeds them back.
2. **Pick two reference keyframes.** Each earlier keyframe gets a score. The *baseline* score is a bell curve around 0.6 m of camera movement (spread 0.2 m). The *view* score prefers keyframes whose viewing direction is within 10° of the new one, so the two views overlap. The top two are kept. More references gave better depth but cost time.
3. **Multi-view semi-global matching (SGM), in depth.**
   - Try L depths per pixel, evenly spaced in inverse depth between a near and a far limit (a *plane sweep*).
   - At each depth, project the pixel into both reference keyframes and compare small patches by their *Census* code. A Census code records which neighbours are brighter than the centre pixel; two codes are compared by counting the bits that differ. It keeps edges sharp and is cheap on a phone.
   - Add the two references' costs, weighted by their scores. Because the sweep is over depth, the images need no rectification. Rectification breaks down when the phone moves forward, which is common when walking.
   - SGM then smooths the costs along 8 image directions. A small depth change costs P1 and a jump costs P2. P2 is lowered at strong image edges, where real depth jumps happen.
   - The best depth per pixel is taken, refined between levels by fitting a parabola.
   - ARM NEON instructions made cost computation 2 times and smoothing 8 times faster.
4. **Confidence filter.** Each pixel's uncertainty comes from its SGM costs (the method of Drory et al. 2014). It is weighted by how many pixels in its 5 × 5 neighbourhood differ by more than 2 depth levels. Pixels with confidence below 0.15 are dropped. This removes most errors from pose error and blank walls.
5. **Learned clean-up.** A two-stage network (an image-guided network, then a residual U-Net) takes the filtered depth and the grey image and removes the remaining noise. It was trained on the DeMoN dataset, then on 3,700 pairs from 13 scenes recorded with the R17 Pro, with its ToF depth as the answer. It is 22.9 ms of the 70 ms. End-to-end learned multi-view networks were slower and worse: MVDepthNet took 5.91 s per frame on the R17 Pro, and DPSNet would not run on either phone.
6. **Growing TSDF volume.** An ordinary indexed voxel grid whose index range grows when a point falls outside it. Unlike voxel hashing, no two cubes can share a key, so collisions never need handling. The paper gives 0.06 m as an example voxel size.
7. **See-through removal.** Each existing voxel is projected into the new depth map. If the new depth lies behind the voxel, the camera now sees through it, and its stored distance is pushed below zero, which deletes its cubes. This removes a person who stood still and then walked away, and broken triangles from a bad pose. If a cube projects outside the image or onto a dropped pixel, that depth map's updates to the cube are undone.
8. **Re-mesh only what changed.** Every voxel is marked added, updated, unchanged or deleted. Marching cubes runs only on cubes with an added or updated voxel, and their old triangles are replaced.

## Evidence and limits

- **Compared with three other methods** on the same five sequences: REMODE 19-26 cm depth RMSE, DPSNet 9-13 cm, MVDepthNet 7.5-11.7 cm, Mobile3DRecon 5.7-10.4 cm. On one sequence (Cabinet) MVDepthNet had the lower depth RMSE, 9.58 against 10.43 cm, but the higher mean error.
- **The reference is the phone's ToF depth**, which has its own error, and only pixels where both have depth are scored.
- **The authors' limits:** the mesh cannot follow pose corrections after the back end refines the path, because there is no way to take a depth map back out of the volume. Memory at larger scale is unsolved.

## Relevance here

The project's room build sizes Depth Anything to ARCore depth in an 8 × 6 grid of cells. ARCore's confident depth rarely reaches past 2.5 m, so beyond 3 m the fused depth is about 15% too near, and the hallway door appears as several layers (Task117, [dense_surface_fusion](README.md)).

- **This paper is that missing step, built once on a phone.** Depth is triangulated between keyframes, so it agrees with the camera path and has real size wherever the poses do. Before the learned clean-up it costs 48 ms per keyframe on one core of a Snapdragon 710 (16.75 + 28.55 + 2.26 ms). That is a 2018 mid-range chip; the Redmi's Helio G96 (owner-reported) is a 2021 mid-range chip. Speed on the Redmi is unmeasured.
- **Why 0.6 m matters for far depth.** For the same matching error, triangulation error grows with distance squared divided by baseline. 4 m with a 0.6 m baseline gives the same error as 2 m with a 0.15 m baseline (16 / 0.6 = 4 / 0.15 ≈ 27). ARCore's own depth matches a hand-held phone against a recent keyframe, so its baseline is short; its actual baseline is not published.
- **It fits the live rule.** About 5 keyframes a second on the phone, against the owner's floor of 1 update a second.
- **Two of its parts are already in the project.** Its see-through removal is the project's visibility vote, done inside the volume at each keyframe. Its confidence filter is in the clean-up table of [surface_denoising](../surface_denoising/README.md); learned depth has no confidence of its own.
- **It shares the project's pose-correction problem.** The project's answer is fragments fixed to ARCore anchors ([note](../camera_tracking_and_slam/fragments_and_anchors.md)).

**What to try.** On the 15 October walk, pick reference pairs from the recorded ARCore poses by the 0.6 m and 10° rule. Compute plane-sweep depth with Census costs and SGM on the PC first, since nothing installed does multi-view SGM without rectification. Score it beyond 3 m against ARCore's tracked points with `python -B -m src.live.depth_check`, the test that measured the current 15% error. If it holds within 5% there, use it to size learned depth in the cells ARCore depth misses. COLMAP's PatchMatch stereo would be an offline reference for the same test, but it needs an NVIDIA GPU. This PC's GPU is reserved for another project for now (owner, 8 November 2026), so PatchMatch would be a spare-laptop experiment. Mobile3DRecon's method needs no GPU. How to combine triangulated and learned depth, with other precedents: [triangulation_and_learned_depth.md](triangulation_and_learned_depth.md).
