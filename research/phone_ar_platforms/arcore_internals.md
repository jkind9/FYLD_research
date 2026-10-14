# How ARCore works inside: what the public record says

Review of 14 October 2026, after the owner asked for the inner mechanisms of ARCore. ARCore is closed source. Everything here comes from Google's developer documentation, two Google patents, one Google paper, and one independent evaluation that describes ARCore's design. Patents describe what Google invented and claimed; they do not prove the shipping code works exactly that way. The plain-language explanation is in [learning/11_inside_arcore.md](../../learning/11_inside_arcore.md).

## Findings

| Part | What the sources say | Source |
|---|---|---|
| Motion tracking, overall | ARCore detects "visually distinct features ... called feature points" in the camera image and combines them "with inertial measurements from the device's IMU" to estimate the camera pose over time (a form of SLAM) | [ARCore fundamentals](https://developers.google.com/ar/develop/fundamentals) |
| Tracking filter | ARCore uses "the multi-state constraint Kalman filter (MSCKF) style VIO/SLAM algorithms" with "many subsequent variations, called concurrent odometry and mapping (COM)"; ARKit is described as "a tightly-coupled filtering-based VIO algorithm similar to the MSCKF" with a sliding-window filter and bundle adjustment | [Kim et al. 2022, arXiv 2207.06780](https://arxiv.org/abs/2207.06780), authors' description of closed systems |
| Three-part architecture | A front-end motion tracker (camera, depth, inertial input; poses at a "relatively high rate"; keeps a limited history and treats earlier 3D points as fixed); a back-end mapping module (receives feature descriptors periodically, "every five seconds" as an example; solves a non-linear estimation; "relatively slow rate"); a localization module (matches descriptors to stored maps, loop closure, Gauss-Newton or Levenberg-Marquardt; sends a corrected "localized pose" back at a "relatively low rate") | [US 10,802,147 B2](https://patents.google.com/patent/US10802147B2/en), Google, priority 18 May 2016 (Nerurkar, Lynen, Zhao) |
| Planes | ARCore "looks for clusters of feature points that appear to lie on common horizontal or vertical surfaces"; untextured surfaces such as a white wall "may not be detected properly" | ARCore fundamentals |
| Anchors | Poses change as ARCore refines its understanding; anchors keep content fixed to a trackable (plane, point) as that happens | ARCore fundamentals |
| Depth from motion | Monocular depth on one CPU core: keyframe pool of recent well-tracked frames; keyframe chosen by a soft cost of baseline (large), time gap (small), view overlap (large) and tracking error (small); polar rectification so forward motion works; stereo as a conditional random field solved by a PatchMatch/HashMatch hybrid on SIMD; unreliable pixels (untextured, repetitive) invalidated by a decision tree; a planar bilateral solver densifies and removes fronto-parallel bias; an exponential moving average over frames for stability; "late-stage slicing" aligns depth edges with the latest camera image | [US 11,145,075 B2](https://patents.google.com/patent/US11145075B2/en), Google, priority 4 October 2018 (Valentin, Guleryuz, Izadi and others), which names "the off-the-shelf VIO platform of ARCore" as the pose source |
| Depth paper | "Low latency dense depth maps using only a single CPU core" of medium-to-high-end phones, monocular colour camera only; QVGA at 30 Hz on one phone core targeted | [Valentin et al., Depth from Motion for Smartphone AR, ACM TOG 37(6), SIGGRAPH Asia 2018](https://research.google/pubs/depth-from-motion-for-smartphone-ar/) (abstract; full text behind ACM) |
| Raw depth | The Raw Depth API gives the unsmoothed depth with a per-pixel confidence image; more geometrically accurate than the smoothed depth, but with missing values and less aligned to the camera image | [Raw Depth codelab](https://codelabs.developers.google.com/codelabs/arcore-rawdepthapi), [DepthLab](https://github.com/googlesamples/arcore-depth-lab/) |
| MSCKF, the underlying method | A sliding window of past camera poses is kept in the filter state; 3D feature positions are not. When a feature has been seen in several poses, its reprojection constraints update the window without adding the point to the state | [Mourikis & Roumeliotis, ICRA 2007](https://www-users.cse.umn.edu/~stergios/papers/ICRA07-MSCKF.pdf) |

## Measured drift (independent)

Final position error after each walk, ARCore 1.29 on an LG V60, all SLAM features (such as loop closure) switched off by the authors (Kim et al. 2022, Table I):

| Walk | Length | ARCore | ARKit |
|---|---:|---:|---:|
| Indoor corridor | 145 m | 0.12 m | 0.79 m |
| Indoor hallway | 84 m | 0.09 m | 0.14 m |
| Indoor stairs | 114 m | 3.98 m | 0.19 m |
| Outdoor campus | 514 m | 0.07 m | 2.01 m |
| Parking lot | 446 m | 1.14 m | 0.26 m |
| Outdoor roads (in a car) | 3,052 m | 140 m | 2.68 m |

## Measured on the project's Redmi (Task85, 14 October 2026)

Tracking on 100% of 891 frames over a 15 s, 5.5 m walk; `session.update()` 4.9 ms median; median 19 tracked points per frame; raw depth 160 x 90 with 48% of pixels valid and low confidence (median 0.05 on 0-1); the phone's time-of-flight sensor not used by ARCore.

## Papers and patents saved (local only)

| File | Why |
|---|---|
| `papers/msckf_mourikis_roumeliotis_icra2007.pdf` | The filter ARCore's tracking is described as building on |
| `papers/proprietary_vio_benchmark_arkit_arcore_2207.06780.pdf` | Describes ARCore and ARKit internals; drift table above |
| `papers/patent_US10802147_concurrent_odometry_mapping.pdf` | Google's concurrent odometry and mapping architecture |
| `papers/patent_US11145075_depth_from_motion.pdf` | Google's depth-from-motion pipeline |
