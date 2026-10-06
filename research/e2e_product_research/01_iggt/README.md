# IGGT: ordinary video to a 3D model with separate objects (open source)

**Take-away:** IGGT is the closest open-source match to this repository's layers 2–5 in one step. Ordinary images or video frames go in. A 3D point model comes out, with each object marked as a separate instance across all views. It has not been tested outdoors or on worksites, it doesn't check real-world scale, and part of the code is not released yet.

Checked on 5 October 2026 from the paper and the code repository. Nothing was installed or run. Part of the [end-to-end product research](../README.md).

## At a glance

| Question | Answer |
|---|---|
| Type | Research model with released code and weights |
| Input | A folder of ordinary colour images in order (for example video frames). Depth and camera details are optional and used only for scoring. |
| Output | Depth for each frame, a 3D point model, and object instance masks that stay consistent across views. Exported as `.glb` 3D files (colour, instance masks, feature colouring). |
| Where it runs | A GPU server. The README gives no GPU size; the authors recommend NVIDIA RAPIDS for the clustering step. |
| Works from an Android phone with no laser sensor | Yes as input: it only needs ordinary images. Processing is on a server. |
| Measures in metres | Not shown. The paper doesn't report real-world scale accuracy. |
| Counts each object once | Partly. Instances are grouped across views, so each object should appear once in the 3D output. Counting is not a stated task and was not scored. |
| Viewable in VR | The `.glb` output opens in common 3D and headset viewers. Not tested. |
| Licence | MIT for the code. Weights are on Hugging Face (`lifuguan/IGGT_official`); check their terms separately. |
| Status | ICLR 2026. Core model and `demo.py` released. "Downstream task scripts" not yet released as of the check. |

## How it works

IGGT is one large transformer network. It is trained to do two things at once from the same images:

1. **Shape:** predict depth and 3D points for each image, as models like VGGT do.
2. **Objects:** predict a feature for each pixel such that pixels of the same object get similar features in every view. The authors call the training method "3D-consistent contrastive learning". In plain terms, the model is rewarded when the same physical object looks alike across views and different objects look different.

Clustering those features (DBSCAN in the demo) gives the object instances. The authors built a training and test set for this, InsScene-15K, with images, camera positions, depth and object masks that match across views. They also score on ScanNet, a set of indoor room scans.

## Evidence and limits

- Results are on indoor room data (ScanNet, InsScene-15K). Nothing outdoors, nothing at street scale.
- No published accuracy in metres. A learned model like this can get the shape right but the overall size wrong. For site measurement, scale has to come from somewhere else, such as ARCore depth or a known object.
- No speed or memory figures in the README.
- No object names are given directly. Instances are separated, but labelling them as "cone" or "barrier" needs a separate step, such as matching text and image features.
- The model sees a batch of frames at once. Long walkthroughs may need to be split, and objects then matched between batches. That cross-batch matching is the same problem this repository's layer 5 works on.

## Compared with this repository

| This repository's layer | Does IGGT cover it? |
|---|---|
| 2. Depth | Yes, learned depth from ordinary images, with unknown scale |
| 3. Camera position | Partly. It is built on a VGGT-style model, which predicts camera positions, but this is not the paper's focus. |
| 4. 3D model | Yes, a point model |
| 5. Objects | Separates instances across views. No class names. Counting not scored. |
| Error traced to each layer | No. One network does everything, so errors can't be traced to a layer. |

## How to test it here

1. Run `demo.py` on the TUM desk recording already used by layer 5.
2. Compare its instances with this repository's reviewed identities for the same frames: are the 3 objects each one instance, and are any split or merged?
3. Scale its points with the TUM reference depth, then compare object positions with this repository's 3D positions.
4. Record GPU memory and time per frame, so it can be compared on cost as well as accuracy.

## Related work with no public code

[OVSeg3R](https://arxiv.org/pdf/2509.23541) (ICLR 2026) does something similar. MASt3R-SLAM or VGGT builds the 3D model from video, DINO-X finds objects in each image, and the two are joined into labelled 3D objects. No code link was found on 5 October 2026, so it cannot be tested here yet.

## Sources

- [IGGT paper (arXiv 2510.22706)](https://arxiv.org/abs/2510.22706)
- [IGGT code repository](https://github.com/lifuguan/IGGT_official)
- [IGGT at ICLR 2026](https://iclr.cc/virtual/2026/poster/10007025)
- [OVSeg3R paper](https://arxiv.org/pdf/2509.23541)
