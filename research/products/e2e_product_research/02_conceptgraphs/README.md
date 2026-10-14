# ConceptGraphs: a 3D map of individual objects (open source)

**Take-away:** ConceptGraphs is the closest research match to this repository's layer 5. It places each detected object in 3D and decides whether a new sighting is an object already seen or a new one, using 3D overlap plus appearance. That is the same rule this repository tests. It needs depth and camera positions supplied, and it runs on a GPU.

Checked on 5 October 2026 from the paper and the code repository. Nothing was installed or run. Part of the [end-to-end product research](../README.md).

## At a glance

| Question | Answer |
|---|---|
| Type | Research system with released code |
| Input | Colour images with matching depth images and a camera position for each frame (posed RGB-D). The newer branch also accepts depth video from an iPhone. |
| Output | A 3D map where each object is a separate point cloud with a caption, plus a graph of how objects relate (for example "cup on table") |
| Where it runs | A GPU computer (tested with CUDA 11.8). Mostly batch processing; the `ali-dev` branch adds a live version with a viewer. |
| Works from an Android phone with no laser sensor | Not directly. It needs depth and camera positions. ARCore depth and positions could supply them, but that is untested. |
| Measures in metres | Yes, if the depth and camera positions are in metres. It doesn't measure the site itself. |
| Counts each object once | Yes, this is its core step: sightings are merged into one object when they overlap in 3D and look alike |
| Viewable in VR | Not built in. The 3D map can be exported and viewed elsewhere. |
| Licence | MIT for the code. The models it calls (SAM, Grounding DINO, CLIP, LLaVA or GPT-4) have their own licences. |
| Status | Published at ICRA 2024. Main branch maintained for batch use; `ali-dev` branch is a faster rewrite. |

## How it works

For each frame:

1. **Find objects.** SAM proposes outlines of every object. A detector such as Grounding DINO or YOLO can be used instead to find named objects.
2. **Describe them.** CLIP turns each outline into an appearance feature.
3. **Lift to 3D.** The depth inside each outline, with the camera position, gives a small 3D point cloud for that object.
4. **Merge or create.** Each new sighting is compared with the objects already in the map:
   - by **3D overlap** between point clouds
   - by **appearance** similarity of the CLIP features

   If both are high enough (configurable thresholds, default 0.8 for the appearance and text settings), the sighting joins that object. Otherwise it becomes a new object.
5. **Caption and link.** A vision-language model (LLaVA or GPT-4) writes a caption for each object and the relations between them.

## Evidence and limits

- Tested on indoor rooms (Replica, a synthetic indoor set) and in a simulator (AI2Thor). Not tested outdoors or on worksites.
- Depends on good depth and camera positions. With noisy phone depth, 3D overlap becomes less reliable, which is what this repository's layers 2–3 measure.
- The thresholds are set by hand. Identical objects placed close together, such as a row of cones, are the hard case for any overlap-plus-appearance rule. The paper doesn't report on it.
- SAM, CLIP and a vision-language model on every frame is heavy. This is the cost FYLD's brief wants to avoid.

## Compared with this repository

| This repository's layer | Does ConceptGraphs cover it? |
|---|---|
| 2. Depth | No, it needs depth supplied |
| 3. Camera position | No, it needs positions supplied (it uses GradSLAM for fusion) |
| 4. 3D model | Only object point clouds, not a measured site model |
| 5. Objects | Yes: detection, outlines, appearance, and the "same or new" decision in 3D |

This repository's layer 5 uses the same idea: an object that comes back appears at the same 3D place, so position plus appearance can decide "same object" or "new object". The difference is cost. This repository tests whether cheap boxes and simple masks are good enough before using SAM.

## How to test it here

1. Feed it the TUM desk recording with the reference depth and camera path, the same inputs layer 5 uses.
2. Compare its merged objects with this repository's reviewed identities: count, splits and merges.
3. Repeat with cheap detector boxes in place of SAM, to see whether the merge step still holds.
4. Record time and GPU memory for each step, so cost can be compared directly.

## Sources

- [ConceptGraphs paper (arXiv 2309.16650)](https://arxiv.org/pdf/2309.16650)
- [ConceptGraphs code repository](https://github.com/concept-graphs/concept-graphs)
- [Project page (Mila)](https://mila.quebec/en/conceptgraphs)
