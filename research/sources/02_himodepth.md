# HiMoDepth: Efficient Training-Free High-Resolution On-Device Depth Perception

**Take-away:** HiMoDepth addresses the cost of producing detailed stereo depth on a phone. Higher resolution may help describe boundaries, but it does not by itself prove more accurate site dimensions.

## Citation and sources

Jinrui Zhang, Huan Yang, Ju Ren, Deyu Zhang, Bangwen He, Youngki Lee, Ting Cao, Yuanchun Li, Yaoxue Zhang and Yunxin Liu. *IEEE Transactions on Mobile Computing*, 23(5), 4648–4664, May 2024. Published online 11 July 2023. DOI: 10.1109/TMC.2023.3294188.

- [IEEE publisher record and abstract](https://ieeexplore.ieee.org/document/10178038/)
- [Seoul National University record confirming authors and journal metadata](https://snu.elsevierpure.com/en/publications/himodepth-efficient-training-free-high-resolution-on-device-depth/)
- Official code release: not verified.

## What it does

Matching every pixel between two large images can be expensive. Phone lenses and capture timing also differ, so a stereo algorithm cannot safely treat their images as a perfectly matched pair.

HiMoDepth first makes the camera views more comparable by cropping their fields of view and rejecting frames whose timestamps do not match. It then searches for corresponding image locations through a hierarchy, working from coarse information toward finer detail. Its graphics-processor layout reduces memory accesses. The input is on-device dual-camera imagery; the output is a high-resolution depth map. This description follows the publisher abstract.

## Evidence and limits

The IEEE abstract discusses a minimum high-resolution target of **1280×960** and reports evaluation on commodity mobile devices. The exact hardware, runtime tables, energy measurements and dataset details have not been extracted for this note. No frames-per-second figure is adopted.

The result concerns per-frame depth. Tracking, frame fusion, gravity alignment and work-area selection remain separate tasks. Image resolution cannot substitute for an independent distance measurement. Detailed wrong geometry can still look convincing in a renderer.

## Relevance to a site capture

Our interpretation is that boundary quality and sustained phone performance deserve separate tests. Test visible edges against measured references, then repeat while the handset warms up. Keep occluded or unreliable regions unknown. Additional-photo guidance must respect the worker's existing safe capture locations.

The system was not downloaded or executed in this workspace. Company permission for code or any released weights remains unresolved; training-free does not imply permission-free.

## Questions for the next experiment

1. Does higher resolution improve independently measured boundary error on the same capture?
2. What happens to latency and depth coverage during sustained recording?
3. Which camera pairs are actually accessible and calibratable on the chosen handset?
