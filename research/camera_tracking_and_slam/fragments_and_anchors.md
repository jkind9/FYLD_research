# Fragments and anchors: keeping a fused surface consistent when the camera path is corrected

**Take-away:** fuse depth into short pieces of surface (*fragments*), each stored in its own local frame, and place each fragment in the world with a pose that can change later. A path correction then moves whole fragments instead of forcing a re-fusion. The project's live processor (`src/live/fragments.py`, Task89) does this with one fragment per 10 ARCore keyframe anchors.

## Sources

- Sungjoon Choi, Qian-Yi Zhou and Vladlen Koltun. **Robust Reconstruction of Indoor Scenes.** CVPR 2015. [Paper](https://openaccess.thecvf.com/content_cvpr_2015/papers/Choi_Robust_Reconstruction_of_2015_CVPR_paper.pdf), saved locally as `papers/robust_reconstruction_indoor_choi_cvpr2015.pdf`. The basis of Open3D's reconstruction system (MIT licence).
- Google ARCore reference, [Frame](https://developers.google.com/ar/reference/java/com/google/ar/core/Frame) (`getUpdatedAnchors`: "Returns the anchors that were changed by the Session.update() that returned this Frame") and [Session.createAnchor](https://developers.google.com/ar/reference/java/com/google/ar/core/Session). Checked 14 October 2026.

## What the paper does

The input RGB-D video is cut into k-frame segments ("k = 50 in all experiments"). Each segment is tracked with RGB-D odometry and fused into its own surface, a *fragment*. In the paper's words, fragments "integrate out some of the noise in the range data" and "have a larger footprint in the scene than individual images without suffering from significant odometry drift". The global model is then built by registering fragments to each other and optimising their poses, with a robust method (line processes) that switches off wrong loop-closure matches even when they outnumber the right ones.

## How the project uses the idea

ARCore already does the global part: it corrects its own path and reports the correction as moved anchors. So the project keeps only the fragment half:

1. The phone starts an anchor at the camera pose once a second (phone session v1).
2. The computer fuses each processed frame into the fragment of its keyframe group (10 keyframes, about 10 s), relative to that group's first anchor as known at that moment.
3. The surface is every fragment's points placed with its anchor's latest pose. A correction costs one matrix multiply per fragment.

Limits: frames inside one fragment all follow its first anchor, not their own, so a correction that bends the path within 10 s is applied as a rigid move of the whole fragment. Neighbouring fragments are not fused with each other, so where they overlap the surface has two layers until they agree.

## Questions

1. How often, and by how much, does ARCore move anchors on a real walk (Task75 walks will log this)?
2. Is 10 keyframes per fragment the right size: shorter costs less to extract and bends better, longer averages more noise?
