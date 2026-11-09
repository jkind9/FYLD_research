# LingBot-Map: streaming 3D reconstruction from video

**Take-away:** one network turns an ordinary video into a camera pose and a depth map per frame as frames arrive, at 12 fps on an RTX 4090. Placed along its own path, those depth maps form the multi-room map with a walked camera path that this project is aiming for. Code is Apache-2.0. It is built for an NVIDIA GPU, gives no real-world size, and has no loop closure, so ARCore would supply metres. Added 8 November 2026 from an owner-supplied link; cloned and tested on the CPU in Task128 ([experiment](../../experiments/lingbot_map/README.md)).

## Citation and sources

Lin-Zhuo Chen, Jian Gao, Shangzhan Zhang, Yihang Chen, Ka Leong Cheng, Yipengjing Sun, Liangxiao Hu, Nan Xue, Xing Zhu, Yujun Shen, Yao Yao and Yinghao Xu (Robbyant, an Ant Group company). "LingBot-Map: Geometric Context Transformer for Streaming 3D Reconstruction." arXiv 2604.14141, v3 8 September 2026. The repository calls it an ECCV 2026 best-paper candidate.

- [Code](https://github.com/robbyant/lingbot-map) · [paper](https://arxiv.org/abs/2604.14141) · [weights](https://huggingface.co/robbyant/lingbot-map) · [project page](https://technology.robbyant.com/lingbot-map) · [saved PDF](papers/lingbot_map_2604.14141.pdf)

## What it does

| Question | Answer |
|---|---|
| Input | Ordinary video or an image folder. No poses, depth, intrinsics or motion-sensor data |
| Output | For each frame, a camera pose and a depth map, using only that frame and earlier ones. Point clouds come from back-projecting the depth |
| Network | VGGT-style transformer on a DINOv2-Large backbone |
| Long recordings | Three kinds of memory: the first 8 frames fix the scale ("anchor"), the 64 most recent frames keep full detail, and older frames shrink to 6 tokens each. The authors claim "nearly constant memory and computation per frame" over 10,000+ frames. A windowed mode resets memory for recordings over about 3,000 frames |
| Scale | Arbitrary. Training normalises each scene by its mean point distance, so outputs are not in metres |
| Loop closure | None. Drift is reduced by the memory of older frames only |
| Speed | At 518 × 378 with the default settings: ATE 5.3 m on Oxford Spires, 20 fps on an H800 and 12 fps on an RTX 4090 (paper Table 9). The paper's memory table gives 13.28 GB for the 64-frame window against 36.06 GB for full attention, on an unnamed GPU |
| Licence | Code Apache-2.0. The weights card shows Apache-2.0 but has no separate weights licence. The sky-mask model it downloads has a licence that was not checked |
| Runs on | CUDA 12.8, PyTorch 2.8, FlashInfer. No CPU or phone path. A community fork targets an 8 GB RTX 4060 |

## Evidence and limits

Trajectory error (ATE) is in metres after best fit with size (Sim(3) alignment). On Oxford Spires the authors report ATE 5.37 m against 18.16 m for CUT3R and 28.41 m for StreamVGGT, other streaming models. Over the full 3,840-frame sequence, theirs rises to 5.60 m and CUT3R's to 32.47 m. These figures, the speeds and the memory were read from the saved PDF. A summary of the other tables gives ATE 0.43, 0.08 and 0.21 on ETH3D, 7-Scenes and Tanks and Temples; those three were not checked against the PDF. The authors list missing loop closure as their first limitation. No result was reproduced here.

## Relevance here

**It produces the output this project is chasing.** The repository's demo shows a multi-room walk of 25,000 frames, seen from above, with the walked camera path drawn through a 3D map of every room. The map is each frame's depth placed along the model's own camera path. So one model covers depth, camera path and a fused point map: layers 2-4 of this project's six. An earlier version of this note called it "layers 2 and 3 only" and set it aside for needing a GPU. The owner corrected that on 8 November 2026: judge methods by output first, and work out phones and hardware afterwards.

What it still lacks for this project:

- **Metres.** Its size is arbitrary. One best fit with size between its camera path and ARCore's gives the size for a whole walk. That is one number per walk, not the per-frame, per-cell sizing the current pipeline needs.
- **Clean-up.** The demo map shows spikes at wall edges, the same flying-pixel kind of floater the [surface clean-up](../surface_denoising/README.md) work removes.
- **Objects.** No detection or counting.
- **Hardware.** It is designed for an NVIDIA GPU. This PC's GPU is reserved for another project for now, so Task128 tests it on the CPU first. A spare RTX 4060 laptop can take essential GPU checks.

Why it could fix the door echoes: the current pipeline sizes each frame's learned depth on its own, so a door 4 m away lands at a different distance in each frame. LingBot-Map predicts each frame's depth using the earlier frames as context, so one door should land in one place.

## Result on this project's walk (Task128, CPU)

Run on the 15 October Redmi walk, every third frame (274 frames), on the CPU with a 16-frame window instead of the default 64, to stay under an 18 GB RAM limit. Inference took 50 minutes (0.09 frames per second). Against ARCore ([full table](../../experiments/lingbot_map/README.md#full-walk-every-third-frame-16-frame-window-8-november-2026)):

- One size per walk works: the size fitted to ARCore's path (1.353) and to its tracked points (1.397) agree within 3%.
- The camera path follows ARCore's to 0.118 m RMSE over 6.7 m.
- Depth medians are within 5% from 1 to 4 m, including 3–4 m, where the room build is 14–16% too near. But the spread is about twice the room build's, and beyond 4 m depth is 40% too near.
- Seen from above, the room is recognisable but blurrier than the cleaned room build.

The small window understates the model: in the paper it raised trajectory error from 5.3 m to 11.2 m on a long sequence. A fair test at the default window needs about 24 GB of RAM on the CPU, or a GPU. A 15-minute attempt on this PC's RTX 5070 Ti under Windows ran no faster than the CPU (12–28 s per frame), probably because GPU memory overflowed into system memory. Without FlashInfer, which needs Linux, the cache is rebuilt every frame and Windows cannot grow GPU memory blocks in place. A second short slot found and fixed four causes, among them an all-true attention mask that blocked PyTorch's fast kernels. With those fixes, 100 frames ran on the GPU at 1.27 frames per second with a 48-frame window. On those frames the larger window barely changed the result compared with the CPU's 16-frame window. Depth medians were within about 5% up to 4 m, but the scatter stayed about twice the room build's. The default 64-frame window still does not fit on a 16 GB card without FlashInfer, which needs Linux.

Related: [InfiniteVGGT](infinite_vggt.md) (also bounded memory for long streams), [SLAM3R](slam3r.md), [Lumina and the open-source parts](../gaussian_splatting/lumina_open_source_parts.md).
