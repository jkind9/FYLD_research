# Depth estimation

How far away each pixel is: phone stereo with two cameras, and learned depth from one image or a video. Project results are in experiments/02_stereo_depth; Task65 showed single-image depth changes size from frame to frame.

## Notes

| Note | What it covers |
|---|---|
| [mobidepth.md](mobidepth.md) | Real-time depth from a phone's two rear cameras |
| [himodepth.md](himodepth.md) | Higher-resolution phone stereo without retraining |
| [mobilestereonet.md](mobilestereonet.md) | A smaller learned stereo network |
| [banet.md](banet.md) | A newer lightweight stereo network for phones |
| [hypersight.md](hypersight.md) | Using camera motion to see further with phone stereo |

## Papers

Saved 13 October 2026 from arXiv or the authors' pages. Paper results are the authors' claims.

| File | Why it is here |
|---|---|
| [video_depth_anything_2501.12375.pdf](papers/video_depth_anything_2501.12375.pdf) | Video Depth Anything: depth that stays consistent across a long video; tried in Task65 (0.77 fps on CPU) |
| [consistent_video_depth_2004.15021.pdf](papers/consistent_video_depth_2004.15021.pdf) | Consistent Video Depth Estimation: adjusts depth so tracked points agree in 3D |
| [prompt_depth_anything_2412.14015.pdf](papers/prompt_depth_anything_2412.14015.pdf) | Prompt Depth Anything: depth guided by a low-resolution metric depth map (trained on iPhone lidar). Small checkpoint is Apache-2.0 (Hugging Face card, 14 October 2026). Task79 prompted it with SfM points: no better than Depth Anything resized to the points, 2.2-2.6 fps on CPU |

## Course lectures

From the 3D vision course in [3d_vision_fundamentals](../3d_vision_fundamentals/README.md).

| Lecture | Covers |
|---|---|
| [06_depth_estimation.pdf](../3d_vision_fundamentals/lectures/06_depth_estimation.pdf) | Depth from two or more views, triangulation and its limits |
