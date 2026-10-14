# Camera tracking and SLAM

Following the camera through a video, live or offline, with a map, refinement and loop closure. Start with the 13 October review: it explains why the project's tracker, not depth, is the main gap.

## Notes

| Note | What it covers |
|---|---|
| [tracking_review_2026-10-13.md](tracking_review_2026-10-13.md) | Review of 13 October 2026: what is missing, panorama versus 3D, alternatives to COLMAP, phone design |
| [orb_slam/README.md](orb_slam/README.md) | ORB-SLAM3 as the tracking reference, and current alternatives |
| [open3d_rgbd.md](open3d_rgbd.md) | Open3D RGB-D odometry: the project's current tracker |
| [rtabmap.md](rtabmap.md) | RTAB-Map: tracking and mapping with revisits |
| [mast3r_slam.md](mast3r_slam.md) | MASt3R-SLAM: dense reconstruction from one-camera video |

## Papers

Saved 13 October 2026 from arXiv or the authors' pages. Paper results are the authors' claims.

| File | Why it is here |
|---|---|
| [mast3r_slam_2412.12392.pdf](papers/mast3r_slam_2412.12392.pdf) | MASt3R-SLAM: Table 1 gives TUM monocular scores for many systems |
| [dpv_slam_2408.01654.pdf](papers/dpv_slam_2408.01654.pdf) | Deep Patch Visual SLAM (MIT licence) |
| [droid_slam_2108.10869.pdf](papers/droid_slam_2108.10869.pdf) | DROID-SLAM (BSD-3 licence) |
| [orb_slam3_2007.11898.pdf](papers/orb_slam3_2007.11898.pdf) | ORB-SLAM3 (GPLv3) |
| [vggt_slam_2505.12549.pdf](papers/vggt_slam_2505.12549.pdf) | VGGT-SLAM: VGGT batches joined into a map |
| [vggt_long_2507.16443.pdf](papers/vggt_long_2507.16443.pdf) | VGGT-Long: VGGT on long sequences |

## Course lectures

From the 3D vision course in [3d_vision_fundamentals](../3d_vision_fundamentals/README.md).

| Lecture | Covers |
|---|---|
| [08_structure_from_motion_sfm_2.pdf](../3d_vision_fundamentals/lectures/08_structure_from_motion_sfm_2.pdf) | Visual SLAM versus structure from motion, and loop closure |
