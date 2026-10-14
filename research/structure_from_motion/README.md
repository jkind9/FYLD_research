# Structure from motion

Solving camera positions and sparse 3D points together from overlapping images, with bundle adjustment. Task67 runs COLMAP 4.2 on the TUM recordings; the comparison of newer methods is in [the tracking review](../camera_tracking_and_slam/tracking_review_2026-10-13.md).

## Notes

| Note | What it covers |
|---|---|
| [colmap.md](colmap.md) | COLMAP: the standard tool, and the project's earlier 120-image CPU run |

## Papers

Saved 13 October 2026 from arXiv or the authors' pages. Paper results are the authors' claims.

| File | Why it is here |
|---|---|
| [glomap_2407.20219.pdf](papers/glomap_2407.20219.pdf) | GLOMAP: global structure from motion, now built into COLMAP 4 |
| [fastmap_2505.04612.pdf](papers/fastmap_2505.04612.pdf) | FastMap: GPU structure from motion; also compares learned methods with classic ones |
| [vggsfm_2312.04563.pdf](papers/vggsfm_2312.04563.pdf) | VGGSfM: learned structure from motion (non-commercial licence) |
| [mast3r_sfm_2409.19152.pdf](papers/mast3r_sfm_2409.19152.pdf) | MASt3R-SfM: structure from motion on the MASt3R prior (non-commercial licence) |
| [g_mast3r_sfm_2606.22856.pdf](papers/g_mast3r_sfm_2606.22856.pdf) | G-MASt3R-SfM: compares COLMAP, VGGSfM, VGGT and MASt3R-SfM on ETH3D |
| [orbit_plus_plus_sfm_360_video_2608.22039.pdf](papers/orbit_plus_plus_sfm_360_video_2608.22039.pdf) | ORBIT++: structure from motion on real 360 degree video; COLMAP's failure rate |

## Course lectures

From the 3D vision course in [3d_vision_fundamentals](../3d_vision_fundamentals/README.md).

| Lecture | Covers |
|---|---|
| [05_epipolar_geometry.pdf](../3d_vision_fundamentals/lectures/05_epipolar_geometry.pdf) | Two-view geometry, essential matrix, why image-only size is unknown |
| [08_structure_from_motion_sfm.pdf](../3d_vision_fundamentals/lectures/08_structure_from_motion_sfm.pdf) | Structure from motion and bundle adjustment |
| [08_structure_from_motion_sfm_2.pdf](../3d_vision_fundamentals/lectures/08_structure_from_motion_sfm_2.pdf) | Incremental structure from motion, loop closure, SLAM, the SfM-to-MVS pipeline |
| [09_multi-view_stereo_mvs.pdf](../3d_vision_fundamentals/lectures/09_multi-view_stereo_mvs.pdf) | Multi-view stereo: dense depth from known camera poses |
| [09_multi-view_stereo_mvs_2.pdf](../3d_vision_fundamentals/lectures/09_multi-view_stereo_mvs_2.pdf) | Plane sweep and cost volumes |
