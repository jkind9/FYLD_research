# CountVid: counting distinct objects in a video (open source)

**Take-away:** CountVid is the strongest open-source baseline for the counting half of this project. You give it a video and a description such as "traffic cone", and it returns how many distinct cones appear across the whole video. It works only in 2D image tracking, with no 3D position, so it is a useful yardstick for whether 3D position really helps.

Checked on 5 October 2026 from the paper and the code repository. Nothing was installed or run. Part of the [end-to-end product research](../README.md).

## At a glance

| Question | Answer |
|---|---|
| Type | Research model with released code |
| Input | A video plus a text description ("penguin", "traffic cone") or one or more example boxes of the object |
| Output | A running count per frame, a total count of distinct objects, an outline of each object, and an annotated video |
| Where it runs | A GPU computer. Needs CUDA, GCC 11.3 or newer, SAM 2 and detectron2. No speed figures published. |
| Works from an Android phone with no laser sensor | Yes as input (ordinary video). Processing is on a server. |
| Measures in metres | No |
| Counts each object once | Yes, this is its purpose, by following each object through the video with image tracking |
| Viewable in VR | No; it outputs 2D video and counts |
| Licence | MIT for the code. SAM 2.1 and the other models it uses have their own licences. |
| Status | AAAI 2026, from the University of Oxford Visual Geometry Group |

## How it works

1. **Find the objects in each frame.** CountGD-Box, an open-world counting model, finds every object matching the text or example.
2. **Follow them through the video.** SAM 2.1 tracks each object's outline from frame to frame.
3. **Count each one once.** Tracks that belong to the same object are joined, and the number of distinct tracks gives the total.

The authors built a test set called VideoCount from existing tracking videos (TAO, MOT20) and from science videos (penguins, crystals growing in X-ray footage). Each video has both a running count and a total.

## Evidence and limits

- The test videos are not first-person walkthroughs and contain no worksite objects.
- Image tracking can lose an object when it leaves the view for a long time and comes back from a different angle. That is the case this repository's 3D approach is meant to handle, and CountVid doesn't use 3D position.
- SAM 2.1 tracking on every frame is heavy. FYLD's brief names SAM as working but too heavy.
- The authors note the reference counts for the crystal videos have up to 5% error in crowded later frames.

## Compared with this repository

| This repository's layer | Does CountVid cover it? |
|---|---|
| 1–4. Capture, depth, camera position, 3D model | No |
| 5. Objects | Detection, outlines and counting, in 2D only |

CountVid answers "how many?" and nothing about where or how big. This repository's layer 5 answers all three, but only if the 3D layers below it are good enough. CountVid is therefore the fair comparison for the counting result alone.

## How to test it here

1. Run CountVid on the TUM desk recording with prompts for the reviewed object classes (for example "cup", "monitor").
2. Compare its total with this repository's count, against the same reviewed identities.
3. Find the hard case: an object that leaves the view and returns. Check whether CountVid counts it twice and whether the 3D rule doesn't.
4. Record time per frame and GPU memory, so the cost difference is measured, not assumed.

## Sources

- [CountVid paper (arXiv 2506.15368)](https://arxiv.org/abs/2506.15368)
- [CountVid code and VideoCount dataset](https://github.com/niki-amini-naieni/CountVid)
- [AAAI 2026 paper page](https://ojs.aaai.org/index.php/AAAI/article/view/37214)
