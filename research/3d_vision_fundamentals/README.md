# 3D vision fundamentals

Lecture slides from Introduction to Computer Vision by Gyeongsik Moon (Visual Computing and AI Lab, Korea University). Many slides credit Andreas Geiger, Davide Scaramuzza and Roni Sengupta. The owner shared them on 13 October 2026 from a public [Google Drive folder](https://drive.google.com/drive/folders/1CJQ5Jt119grvU7wBUwuc5V-3H7dZtioU), last changed 18 December 2025. They are teaching material, not research results. They belong to their authors and are kept here for reading only.

Several lectures have a second file, marked `_2`. The Drive folder held both versions: a different length or a continuation. Both are kept.

## What the course adds for this project

The structure from motion and multi-view stereo lectures describe the standard chain for building 3D from photos or video:

1. Match features between images (lecture 3).
2. Solve camera poses and sparse points together with bundle adjustment: structure from motion, or SLAM for live video (lecture 8).
3. Compute dense depth for each frame from its neighbours, using those poses: multi-view stereo (lecture 9).
4. Fuse the depth into a mesh or other 3D model, then texture it (lectures 9, 12, 13).

The project's walkthrough skips step 3. It uses single-image depth instead and tracks the camera from that depth. Task72 now compares single-image depth with multi-view stereo on the same camera path. The course also explains why an image-only reconstruction has no real-world size (lectures 5 to 8), which is why a size source such as ARCore is needed.

## Lectures

| File | Topic | Relevant to |
|---|---|---|
| [01_introduction.pdf](lectures/01_introduction.pdf) | Course overview and history of computer vision | Background |
| [02_image_formation.pdf](lectures/02_image_formation.pdf) | Camera model, projection, panoramas | Camera model used by every layer |
| [03_2d_features_and_matching.pdf](lectures/03_2d_features_and_matching.pdf) | Features and matching | Tracking, structure from motion |
| [03_2d_features_and_matching_2.pdf](lectures/03_2d_features_and_matching_2.pdf) | Features and matching, second file | Tracking, structure from motion |
| [04_camera_calibration.pdf](lectures/04_camera_calibration.pdf) | Camera calibration | Phone capture (Task52) |
| [05_epipolar_geometry.pdf](lectures/05_epipolar_geometry.pdf) | Two-view geometry, essential and fundamental matrix | Image-only tracking (Task67) |
| [06_depth_estimation.pdf](lectures/06_depth_estimation.pdf) | Triangulation and depth from views | Depth (Tasks 65, 72) |
| [07_recap_and_overview.pdf](lectures/07_recap_and_overview.pdf) | Recap of lectures 1 to 6 | Background |
| [08_structure_from_motion_sfm.pdf](lectures/08_structure_from_motion_sfm.pdf) | Structure from motion, bundle adjustment, global and incremental | Task67 |
| [08_structure_from_motion_sfm_2.pdf](lectures/08_structure_from_motion_sfm_2.pdf) | Incremental structure from motion, loop closure, SLAM, COLMAP | Task67 |
| [09_multi-view_stereo_mvs.pdf](lectures/09_multi-view_stereo_mvs.pdf) | Multi-view stereo | Task72 |
| [09_multi-view_stereo_mvs_2.pdf](lectures/09_multi-view_stereo_mvs_2.pdf) | Plane sweep and cost volumes | Task72 |
| [11_neural_networks.pdf](lectures/11_neural_networks.pdf) | Neural networks | Background |
| [12_3d_representations.pdf](lectures/12_3d_representations.pdf) | Points, meshes, voxels, implicit surfaces | Surfaces (Task36) |
| [12_3d_representations_2.pdf](lectures/12_3d_representations_2.pdf) | 3D representations, second file, including NeRF | Surfaces (Task36) |
| [13_3d_gaussian_splatting_3dgs.pdf](lectures/13_3d_gaussian_splatting_3dgs.pdf) | Gaussian splatting | VR viewing (Task36) |
| [14_applications_of_3d_computer_vision_and_graphics.pdf](lectures/14_applications_of_3d_computer_vision_and_graphics.pdf) | Applications, including VGGT | Task74 |
| [15_deep_generative_models.pdf](lectures/15_deep_generative_models.pdf) | Generative models | Not used |
| [15_deep_generative_models_2.pdf](lectures/15_deep_generative_models_2.pdf) | Generative models, second file | Not used |
| [16_applications_of_deep_generative_models.pdf](lectures/16_applications_of_deep_generative_models.pdf) | Applications of generative models, including 3D | Not used |
| [16_applications_of_deep_generative_models_2.pdf](lectures/16_applications_of_deep_generative_models_2.pdf) | Applications of generative models, second file | Not used |
| [17_robot_kinematics.pdf](lectures/17_robot_kinematics.pdf) | Robot kinematics | Not used |
| [18_reinforcement_learning.pdf](lectures/18_reinforcement_learning.pdf) | Reinforcement learning | Not used |
| [19_vision-language-action_vla_models.pdf](lectures/19_vision-language-action_vla_models.pdf) | Vision-language-action models | Not used |

Lecture 10 was not in the folder.
