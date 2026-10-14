# 10. What we have learned so far

The project's main findings in the order they were found, with the numbers behind them. Each line names the task that produced it; task records are in `task_list/`. Dates are 2026.

## Early October: build each layer and run it end to end

- **1-7 October. Six layers, each testable alone.** Capture, depth, tracking, surfaces, mapping and objects each got a written input and output contract and at least one real method. The full six-layer walkthrough first ran on 30 TUM frames on 7 October (Tasks 51, 58, 59).
- **7 October. Learned depth is the wrong size.** Depth Anything V2 Metric Small reads 1.34-1.41 times too far on TUM, raw AbsRel 0.345-0.450 (Task54).
- **7 October. Its shape is good, and a few points fix the size.** With each frame's scale fitted, AbsRel falls to about 0.07; 50 known points per frame are as good as every pixel (Task62).
- **7 October. A speed floor.** Marigold V2 had the best shape (0.036) but took 16.6 s per frame; the owner set 1 frame per second as the minimum for any method (Task62).
- **7 October. Areas come out three to four times too large** with learned depth: desk plane 7.44 m² against 2.21 m² with the Kinect (Task55).

## 8-13 October: why the 3D view repeats surfaces

- **8 October. The size changes every frame.** Depth Anything's size factor moves between 0.86 and 2.09 from frame to frame. Fused, one wall appears several times. The tracker reads each size jump as motion (Task65).
- **8-13 October. Correcting size helps, but not enough.** The overlap chain (carry size forward through tracked corners) cut camera error 41-73%, still leaving 0.37 m on xyz and 1.01 m on desk (Task65).
- **13 October. The scoring was too harsh and hid size.** Switching to the standard best-fit score halved most errors and showed raw Depth Anything's path was 16 times too long (Task70).
- **13 October. The tracker is the main gap.** With the Kinect's own depth, the walkthrough tracker misses by 112 mm on desk; published SLAM gets 16-18 mm. The tracker compares each frame only with the last one, keeps no map, never refines, never closes loops (tracking review).

## 13-14 October: structure from motion and dense surfaces

- **13 October. Images alone give a far better path.** COLMAP places every TUM frame with 11.9 mm (xyz) and 21.5-24 mm (desk) error after best fit with size: 3-5 times better than the old tracker with Kinect depth, close to published SLAM. ICL: 34 mm (Task67).
- **13 October. Learned features and faster mappers are not free wins.** ALIKED + LightGlue helped only with the incremental mapper on TUM; with the global mapper positions collapsed. The global mapper is 1.6-3.1 times faster but dropped frames on ICL (Task67).
- **13 October. Depth Anything cannot supply the world's size.** It makes SfM's world 1.3-1.4 times too large: 357 mm path error on desk from size alone (Task67).
- **13 October. Even perfect poses and size leave a shape error.** With the true path and each frame sized exactly to the sensor, Depth Anything's surface is 82 mm (ICL), 129 mm (desk) and 158 mm (xyz) from the reference. ICL's rendered depth gives 11 mm, so the pipeline itself is right (Task71).
- **14 October. The image-only design reaches that ceiling.** Depth Anything sized to SfM points and fused along the SfM path: 92, 151 and 199 mm (Task72).
- **14 October. Twenty depth readings fix the size.** Twenty metric readings at SfM points, anywhere in the walk, give a path within 1.15 times the best possible and the same surface error. More readings, or readings in every frame, add nothing (Task78).
- **14 October. Prompting depth with sparse points does not help.** Prompt Depth Anything fed with SfM points: no better on xyz, 39% worse on desk, 58% worse on ICL than Depth Anything sized to the same points. It runs at 2.2-2.6 frames per second on the CPU (Task79).
- **14 October. Depth Anything 3 Small wins on synthetic data only.** Given the camera poses and sized to the points: 79 mm on ICL, 15% better than V2. On the real TUM recordings it is two to three times worse (best 238 mm desk, 299 mm xyz). 4.4-5.6 frames per second on the CPU (Task80).
- **14 October. The deployed system must be live.** The owner ruled that tracking and mapping must run live, or update at least once per second, on the phone or a server. Whole-clip structure from motion is therefore a scoring reference, not a deployable part. Everything downstream (per-frame sizing, metric readings, fusion) already works one frame at a time.

## What this adds up to

1. **Get the camera path from a live SLAM system with joint refinement**, not from aligning depth maps. On the phone that is ARCore's tracking. SfM was the offline stand-in used to prove the design on recorded data.
2. **Get the real-world size from a few metric readings or the IMU**, never from a learned depth model's own metres.
3. **Use learned depth only for dense shape**, resized every frame to the tracked points.
4. **The remaining error is the depth model's shape** (8-16 cm average). The untried next step is multi-view stereo along the SfM path, which needs GPU permission.

## Open questions

- How accurate is ARCore on the project's phone, for path, points and depth (Tasks 52, 75)?
- Does any of this hold on a real site walk outdoors?
- How much accuracy is lost when the SfM stand-in is replaced by a live SLAM system that only sees past frames?
- How much better is multi-view stereo than resized learned depth?
- Can objects be counted reliably once positions come from the improved path (Task56)?
- What runs on the phone, and at what speed, memory and battery cost (Tasks 57, 61)?
