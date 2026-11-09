# How LingBot-Map works, and which parts this project can use

Written 8 November 2026 from LingBot-Map's code (commit b9dd1b1, `third_party/lingbot-map`), its checkpoint and its paper ([saved PDF](papers/lingbot_map_2604.14141.pdf)), plus measurements on the 15 October Redmi walk. What the model is and its benchmark claims are in [lingbot_map.md](lingbot_map.md); the runs are in [experiments/lingbot_map](../../experiments/lingbot_map/README.md).

**Take-away:** LingBot-Map is a VGGT-style transformer that keeps a structured memory of earlier frames. Used whole, its map looked no better than this project's cleaned room build (owner's judgement from the viewer, 8 November). Its depth works better as a part. Sized frame by frame to ARCore depth, as this project's pipeline already does, it had 38% lower error than Depth Anything V2 on the same 72 frames. Its confidence map marks its worst pixels.

Terms: a **token** is one small piece of an image the network works on, here a 14 × 14 pixel patch, described by 1,024 numbers. **Attention** lets each token look at other tokens and borrow from them. A **cache** keeps earlier frames' tokens so new frames can look at them without recomputing them.

## What happens to one frame

| Step | Component (parameters) | What it does |
|---|---|---|
| 1. Prepare | — | Turn upright, resize to 518 pixels wide, crop to 518 × 518 |
| 2. Encode | Image encoder, DINOv2 ViT-L/14 with registers (304 M, 26%) | 1,369 patch tokens (37 × 37), plus 6 learned summary tokens: 1 camera, 4 register, 1 scale |
| 3. Look within the frame | 24 frame-attention blocks (302 M, 26%) | Each token looks at the other tokens of the same frame |
| 4. Look across frames | 24 global-attention blocks (302 M, 26%), alternating with step 3 | Each token looks at the cached tokens of earlier frames (next section) |
| 5. Camera | Camera head (216 M, 19%) | From the camera token: 9 numbers (position 3, rotation as a quaternion 4, field of view 2), refined over 4 passes. It has its own cache across frames |
| 6. Depth | Depth head, DPT (33 M, 3%) | Reads 4 intermediate layers and upsamples to a depth map and a confidence map at 518 × 518 |

Total 1,158 M parameters. This checkpoint has no 3D-point head; points come from depth and the camera. Positions are given to attention as rotations of the token's numbers by its frame number, row and column (3D RoPE), so tokens know where and when they come from.

## The memory: what a new frame looks at (Geometric Context Attention)

| Part | What is kept | Why |
|---|---|---|
| Anchor frames | The first n frames (default 8), all tokens, forever | They fix the scene's scale and coordinate frame. They are processed together first, looking at each other both ways |
| Recent window | The last k frames (default 64), all tokens | Detailed geometry for the current view |
| Trajectory memory | For each older frame, only its 6 summary tokens | Long-range consistency at almost no cost: an evicted frame shrinks from 1,375 tokens to 6 |
| The frame itself | All its tokens | — |

Frames enter the cache one by one. With a keyframe interval above 1, only every Nth frame is stored, though every frame still gets a pose and depth. For very long videos a windowed mode restarts the memory every window and joins windows by best fit with size. In training the scene is scaled by the anchor frames' mean point distance, which is why outputs have no real-world size.

The same structure appears in classical SLAM: fixed reference frames, a window of recent keyframes optimised in full, and compressed summaries of older ones. Here a network learns it instead of a solver computing it.

## Measured on this project's PC

| Item | Value |
|---|---|
| Memory per frame in the window | About 0.2 GB of GPU memory with PyTorch's attention (keys and values for 1,375 tokens × 24 layers) |
| Default window on a 16 GB card | Does not fit this way: 2.8 GB model + 68 frames × 0.2 GB ≈ 16.4 GB. The authors fit it in 13.3 GB with FlashInfer's paged cache (Linux) |
| Speed | 1.27 frames per second on an RTX 5070 Ti under Windows (48-frame window); 0.09 on the CPU (16-frame window). The authors report 12 on an RTX 4090 |
| Code problems found | An all-true attention mask that blocked fast attention; a loader that puts the 32-bit checkpoint on the GPU; frames read twice on Windows. Fixes in the [experiment](../../experiments/lingbot_map/README.md) |

## Which parts this project can take

| Part | Usable? | Evidence or reason |
|---|---|---|
| **Its depth, sized per frame by ARCore**, in place of Depth Anything V2 | Most promising | Same frames, Task109's method: mean relative error against ARCore depth 0.039 against 0.063 (72 frames, lower in 60); against tracked points 0.078 against 0.098 (55 frames, lower in 51); on the GPU run 0.042 against 0.060 (17 frames). The cost is a 1.16 B-parameter model on a GPU instead of 25 M on a CPU. ARCore depth reaches about 2.5 m, so this measures near-range shape |
| **Its confidence map**, as a weight in clean-up | Promising | Per-frame-sized depth against tracked points, by confidence quarter: middle half 0.162 wide in the least confident quarter, 0.071 in the most confident. Partly distance (median 3.2 m against 1.5 m) |
| **Its whole map with one size per walk** | Not better | The owner judged the viewer no better than the cleaned room build. Measured: depth scatter about twice the room build's, 40% too near beyond 4 m (CPU, 16-frame window) |
| **Its camera path** | Not needed now | Within 0.12 m RMSE of ARCore's over 6.7 m. ARCore already gives metres and gravity on the phone |
| **The memory design**, as an idea | Yes | Anchors for scale, a recent window in full, summaries of older frames. It matches the fragments-and-anchors design in `src/live/fragments.py` and could guide which frames the clean-up vote keeps |
| **The encoder alone**, for object re-identification | Possible, heavy | Its DINOv2 ViT-L gives per-patch appearance features. Stage 06 considered DINOv2 ViT-S for this; one shared encoder could serve depth and objects |
| **The camera or depth head on its own** | No | Both read the trunk's tokens. Without the 909 M-parameter trunk they have nothing to read |
| **Training a smaller copy** | Not now | The authors trained on 26 datasets over about 21,500 GPU hours for one stage. A small model distilled from it would still need large data and GPU time |

## Next test this suggests

Build the room with LingBot-Map's depth in place of Depth Anything V2. Keep everything else the same: per-cell sizing to ARCore depth, the visibility vote and the largest-pieces filter. Compare it by eye and against ARCore's tracked points by distance, on the frames both runs share. The current run holds every third frame, which gives 73 frames with fresh ARCore depth against the room build's 134. A whole-walk GPU run of about 5 minutes would cover every frame.
