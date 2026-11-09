# SLAM3R: real-time dense reconstruction from one camera

**Take-away:** SLAM3R turns ordinary video into a dense 3D point cloud at 20+ fps on an RTX 4090D, without solving camera poses. Its licence is CC BY-NC-SA 4.0, which forbids commercial use, so it can only be a reference. Added 8 November 2026 from an owner-supplied link. The paper was saved; code and weights were not downloaded or run.

## Citation and sources

Yuzheng Liu, Siyan Dong, Shuzhe Wang, Yingda Yin, Yanchao Yang, Qingnan Fan and Baoquan Chen (Peking University). "SLAM3R: Real-Time Dense Scene Reconstruction from Monocular RGB Videos." CVPR 2025 (highlight). arXiv 2412.09401.

- [Code](https://github.com/pku-vcl-3dv/slam3r) · [paper](https://arxiv.org/abs/2412.09401) · weights: [image-to-points](https://huggingface.co/siyan824/slam3r_i2p), [local-to-world](https://huggingface.co/siyan824/slam3r_l2w) · [saved PDF](papers/slam3r_2412.09401.pdf)

## What it does

| Question | Answer |
|---|---|
| Input | Ordinary video; no camera parameters needed |
| Output | A dense point map per frame, all in one world frame, building one point cloud. No explicit camera poses, depth maps, splats or meshes |
| Method | Two networks built on DUSt3R. The first predicts 3D points for a short sliding window of frames (5 at the start, then 11). The second places each window's points into the growing scene |
| Input size | 224 × 224 centre crop |
| Speed | "20+ FPS" on one NVIDIA RTX 4090D (24 GB) |
| Scale | Not stated; DUSt3R-style outputs have no real-world size |
| Licence | Code CC BY-NC-SA 4.0 (non-commercial, share-alike). The weights cards state no licence |
| Runs on | CUDA (PyTorch 2.5, cu118). No CPU or phone path |

## Evidence and limits

The authors score point-cloud accuracy and completeness on 7-Scenes and Replica after aligning to the reference with Umeyama and ICP. They claim the best results among methods faster than 1 fps. Their own limitation: with no camera solving there is no global bundle adjustment, and "the poses derived from our scene point cloud prediction still fall short of SLAM systems that specialize in camera localization." No result was reproduced here.

## Relevance here

- **Licence rules it out** for anything beyond a reference run on recorded data.
- **224 × 224 input** is coarse for a room; small objects and thin edges will be lost.
- **GPU only**, so not a Task74 CPU candidate.
- For the same job, [LingBot-Map](lingbot_map.md) is Apache-2.0 and outputs poses as well as depth.

Related: [MASt3R-SLAM](../camera_tracking_and_slam/mast3r_slam.md), also built on the DUSt3R family.
