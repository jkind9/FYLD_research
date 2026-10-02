# BANet: Bilateral Aggregation Network for Mobile Stereo Matching

**Take-away:** BANet is a newer stereo candidate aimed at preserving edges without expensive matching operations. Its value for this project depends on metric accuracy at real work-area boundaries and execution on the selected hardware.

## Citation and sources

Gangwei Xu, Jiaxin Liu, Xianqi Wang, Junda Cheng, Yong Deng, Jinliang Zang, Yurui Chen and Xin Yang. ICCV 2025; acceptance is stated on the author arXiv record. arXiv:2503.03259, submitted March 2025 and revised July 2025.

- [Author paper record and abstract](https://arxiv.org/abs/2503.03259)
- [Official code](https://github.com/gangweix/BANet)
- [Official code licence](https://github.com/gangweix/BANet/blob/main/LICENSE)

## What it does

Stereo matching must compare candidate locations between two camera views. Combining those comparisons can blur edges or lose detail, particularly where surfaces have little texture.

BANet separates matching information into detailed and smooth parts using an attention map. It combines each part differently, then joins their results into a disparity map. The abstract emphasizes a version using 2D convolutions for mobile-friendly computation. Inputs are rectified stereo images. Disparity becomes depth only when the camera focal length and baseline are known.

## Evidence and limits

The abstract reports improved KITTI 2015 results and faster mobile runtime relative to MobileStereoNet-2D. Its numerical improvement is not adopted here because the exact metric denominator and corresponding runtime conditions have not been examined. Device models, runtime tables and input resolution have not been checked for this note.

The authors' benchmark claim is verified as a claim, not reproduced performance. It does not establish outdoor construction accuracy, camera synchronization or successful tracking across a recording.

## Relevance to a site capture

Our proposed experiment would focus on boundary errors and missing observations. Compare methods on identical calibrated frames, using measured edges and distances held outside the estimation inputs. A crisp rendered edge may be confidently wrong. Keep confidence and validity information alongside any visual preview, and do not fill an occluded area merely to close its polygon.

Official code is MIT licensed. Checkpoint terms and company use of pretrained weights remain unresolved. Nothing was fetched or executed here. Further capture must remain within the worker's approved safe positions.

## Questions for the next experiment

1. Does BANet reduce measured boundary error on the same permitted stereo capture?
2. How does it behave on blank, reflective or moving surfaces?
3. What are sustained latency and memory use on the intended device after permissions are cleared?
