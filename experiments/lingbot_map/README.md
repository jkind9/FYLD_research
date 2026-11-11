# LingBot-Map on the 15 October walk (Task128)

LingBot-Map turns ordinary video into a camera pose and a depth map for every frame, as frames arrive. Its public demo shows a 25,000-frame multi-room walk mapped from above, with the walked camera path drawn through it. That is the output this project is aiming for. This experiment runs it on this project's own Redmi walk and measures it against ARCore. Research note: [research/feed_forward_3d/lingbot_map.md](../../research/feed_forward_3d/lingbot_map.md).

**CPU only for now.** The owner reserved this PC's GPU for another project on 8 November 2026. LingBot-Map is built for an NVIDIA GPU (the authors report 12 frames per second on an RTX 4090), so CPU runs here are slow and are used for measurement, not speed.

## What is compared

LingBot-Map gives no real-world size. ARCore is not ground truth either, so every number below says how well two estimates agree.

1. **Size and camera path.** One best fit with size (Umeyama, through Open3D's point-to-point estimate with scaling) maps LingBot-Map's camera centres onto ARCore's. This gives one size for the walk and the path difference left over.
2. **Depth by distance.** LingBot-Map's depth, times that size, against ARCore's tracked points in each frame, grouped by distance. This is the check Task117 ran on the room build's fused depth. There, depth beyond 3 m came out about 15% too near and caused the door echoes.
3. **Point cloud.** Every third frame's depth (every second pixel, confidence at least 1.5, under 10 m), placed in ARCore's world and thinned to 2 cm. It is measured against the room build's cleaned surface and can be opened in the project's viewer.

## How the frames are fed in

- The Redmi records portrait walks on their side (Task109). All 779 posed frames of this walk are portrait, so every frame is turned 90° clockwise, as LingBot-Map's `--rotate_clockwise_90` does.
- LingBot-Map then resizes each 480 × 640 upright frame to 518 × 686 and crops 84 rows from the top and bottom, to 518 × 518 (its default crop mode). `compare.processed_pixels` maps ARCore pixels through the same three steps; the tests check it against `numpy.rot90`.
- Streaming mode: the first 8 frames fix the scale, and a keyframe interval keeps at most 320 frames in the cache (LingBot-Map's defaults). The window of recent frames kept in full is 16 on the CPU instead of the default 64, to stay under the RAM guard (see Results). Attention uses PyTorch's built-in kernel (FlashInfer is not installed).

## Memory

The owner watches RAM while runs go. `run.py` keeps it bounded:

- Outputs are 16-bit `.npy` files that `compare.py` reads memory-mapped, one frame at a time.
- 3D points per pixel are dropped as soon as inference ends; `compare.py` rebuilds points from depth.
- The temporary turned frames that LingBot-Map's loader writes are deleted.
- A watchdog ends the run if its RAM passes `--max-ram-gb` (default 18 GB).

## Run it

```text
experiments\lingbot_map\.venv\python -B experiments/lingbot_map/run.py --frames <session>/frames --model third_party/lingbot-map-weights/lingbot-map.pt --out <run folder> --device cpu --stride 3 --window 16 [--first 10]
.venv\Scripts\python -B -m experiments.lingbot_map.compare --run <run folder> --session <session> --surface outputs/cleanup/room_build_clean_up_093913/surface.ply
```

Set `PYTHONIOENCODING=utf-8` first: LingBot-Map prints characters the Windows console code page cannot show. Setup of `experiments/lingbot_map/.venv` (Python 3.10, torch 2.8.0 cu128, LingBot-Map at commit b9dd1b1) is recorded in `research/repositories.json`.

## Results

### CPU and number type, first 10 frames (8 November 2026)

AMD Ryzen 9 9950X, 16 threads, `lingbot-map.pt`. The authors run inference in bfloat16 on the GPU, with the output heads kept in 32-bit. On the CPU the heads also run in bfloat16, because LingBot-Map switches autocast off for them on CUDA only. The table measures what that costs.

| | 32-bit | bfloat16 |
|---|---|---|
| Inference, 10 frames | 55.4 s (0.18 frames/s) | 33.3 s (0.30 frames/s) |
| Peak RAM | 15.8 GB | 12.7 GB |
| Depth against 32-bit | — | mean difference 0.27%; 90% of pixels within ±0.8% |
| Camera rotation against 32-bit | — | at most 0.028° |

bfloat16 is used from here on. The differences are far below the 5% level the depth check works at. Most of the peak RAM is loading: the 32-bit model and its checkpoint (4.6 GB each) are both in memory until the trunk is cast to bfloat16. These runs tested the code path only: frame 18 is the first with ARCore tracked points.

**Duplicate frames.** LingBot-Map's loader collects both `*.jpg` and `*.JPG`. Windows file names ignore case, so every frame was loaded twice. The 10-frame runs above were 5 frames, each given twice (both columns had the same input, so the comparison stands). `run.py` now asks for `.jpg` only.

### Memory against window size

The first full-walk attempt (every third frame, 64-frame window, 8 threads) loaded each frame twice and passed the 18 GB guard after 60 frames had entered the cache, at 11.9 s per frame. Memory grows by about 0.22 GB for every frame held in the window. The paper's Table 9 (Oxford Spires, 8 anchor frames) gives trajectory error by window size: 11.2 m at 16 frames, 8.0 m at 32, 5.5 m at 48, 5.3 m at 64 (the default) and 5.3 m at 128. A second attempt with a 48-frame window and unique frames passed the guard after 35 frames. A one-line change storing the cache keys in bfloat16 was tried and gave bit-identical output and the same 14.0 GB peak at 20 frames, so the keys were already bfloat16; it was reverted. From the measured points (14.0 GB at 20 frames, 18 GB at about 35), memory grows by about 0.27 GB per frame held, so the default 64-frame window needs about 24 GB on the CPU. The full run below uses a 16-frame window, the smallest in the paper's table.

**Rotations.** On the CPU the camera head also runs in bfloat16, which leaves LingBot-Map's rotation matrices up to 0.4% off orthonormal (determinant 0.997–1.004; the 32-bit run is exact). `compare.nearest_rotations` snaps each to the nearest true rotation before points are placed.

### Full walk, every third frame, 16-frame window (8 November 2026)

274 frames (10 per second of walk), streaming mode, `lingbot-map.pt`, bfloat16, 8 threads. Inference took 3,026 s (0.09 frames per second) and peaked at 17.8 GB, just under the guard. Memory kept growing after the window filled, so the guard is needed even at this window size.

| Measure | LingBot-Map | Room build, for reference (Task117) |
|---|---|---|
| Size (one number for the walk) | 1.353 from the camera path; 1.397 from depth at tracked points (3% apart) | Sized per frame and per grid cell to ARCore depth |
| Camera path against ARCore, after one best fit with size | RMSE 0.118 m, maximum 0.30 m, over a 6.70 m walk (260 frames) | ARCore's path |
| Depth ÷ ARCore tracked point, 0–1 m: median (middle half) | 1.14 (0.93–1.20), 448 point views | 1.04 (1.00–1.07) own-size cells; 1.10 (1.04–1.17) fallback |
| 1–2 m | 0.99 (0.93–1.13), 6,476 | 1.02 (0.97–1.06); 1.00 (0.95–1.06) |
| 2–3 m | 0.97 (0.90–1.05), 9,478 | 0.98 (0.94–1.02); 0.94 (0.85–1.01) |
| 3–4 m | 0.95 (0.82–1.12), 2,183 | 0.86 (0.77–0.92); 0.84 (0.72–0.97) |
| Over 4 m | 0.60 (0.37–0.87), 1,391 | Not fused (the room build stops at 4 m) |
| Point cloud against the cleaned room surface | median 9.6 cm apart; 33% of LingBot-Map's points within 5 cm; 41% of the room surface within 5 cm of LingBot-Map's | — |

What this shows:

- **One size per walk is enough.** The size fitted to ARCore's path and the size fitted to ARCore's tracked points agree within 3%. LingBot-Map's scale holds across the walk.
- **The camera path follows ARCore's** to 0.12 m RMSE over 6.7 m. It separates only at the last standing spot, by up to 0.30 m. Neither path is ground truth.
- **Depth medians are right from 1 to 4 m.** At 3–4 m it is 5% too near, against 14–16% for the room build, the error behind the door echoes. But its middle half is about twice as wide at every distance. Each frame's depth wobbles in scale, while the room build re-sizes every frame to ARCore depth.
- **Beyond 4 m it is badly too near** (median 0.60). Far surfaces fan into smears in the top-down view.
- **The map is recognisable but blurrier** than the cleaned room build. The two agree within 5 cm on only a third of their points.

Limits: the 16-frame window is a quarter of the default. In the paper this window raised trajectory error from 5.3 m to 11.2 m on a long outdoor sequence, so this run understates LingBot-Map. A fair test at the default 64-frame window needs about 24 GB of RAM on the CPU, or a GPU (the spare RTX 4060 laptop). ARCore is a reference, not ground truth. One walk.

### GPU attempt, 15-minute window (8 November 2026)

The owner lent this PC's RTX 5070 Ti (16 GB) for up to 15 minutes to test the default setting. The GPU was idle, with 13.4 GB free. Same 274 frames, every run stopped early:

| Try | Setting | Result |
|---|---|---|
| 1 | Default: 64-frame window, 8 anchor frames, frames on the GPU | 28.5 s per frame; the RAM guard stopped it at frame 37 after 5 minutes |
| 2 | 48-frame window, frames kept in system RAM | No progress reported before the 4-minute stop |
| 3 | 64-frame window, 4 anchor frames (paper: 5.4 m against 5.3 m with 8) | 12–17 s per frame and rising at frame 28; 3-minute stop |

On the GPU it ran no faster than on the CPU, so the default setting is still untested. The probable cause, not yet proven by a memory trace: on Windows PyTorch cannot grow GPU memory blocks in place (the log says `expandable_segments not supported on this platform`). LingBot-Map's plain-PyTorch attention rebuilds its whole cache with `torch.cat` on every frame. So GPU memory fragments, spills into shared system memory, and every frame then crosses the PCIe bus. System RAM rising until the guard tripped fits that. The authors' 12 frames per second on an RTX 4090 uses FlashInfer, a paged cache that avoids the copies; it runs on Linux, not Windows.

Next, when the GPU is free again: the same run under Linux with FlashInfer, in the WSL2 Ubuntu already installed on this PC. First check GPU memory per frame for 20 frames, to confirm the spill.

`run.py` changes from this attempt: frames stay in system RAM (LingBot-Map moves one at a time to the device), and `--anchors` sets the number of anchor frames.

### 100 frames on the GPU (8 November 2026, second short slot)

At the owner's suggestion the sample was shortened to 100 frames: the first 300 frames of the walk, every third frame, about the first 10 seconds. Four causes of the slowness were found and fixed, one at a time:

1. **An attention mask that does nothing.** While streaming, LingBot-Map passes an all-true mask "to ensure same kernel as batch mode". An all-true mask changes nothing, but any mask stops PyTorch from using its fast attention kernels. Removing it gave bit-identical output on the CPU and made the GPU about ten times faster (from 25–28 s to 2.7 s per frame).
2. **Loading straight onto the GPU.** demo.py's loader puts the 32-bit checkpoint and a 32-bit model copy on the GPU (8.9 GB) before the trunk is cast to bfloat16. `run.py` now loads and casts on the CPU, so 2.8 GB reaches the GPU.
3. **Cache keys in 32-bit.** Under CUDA autocast the cached keys leave their normalisation and position encoding in 32-bit. They are now stored in bfloat16 like the values, as FlashInfer's cache stores them. This also gave bit-identical output on the CPU.
4. **A fragmenting memory pool.** Each frame the cache grows by one frame, and on Windows (no expandable segments) the freed smaller blocks pile up: 4.7 GB of 11.6 GB reserved was unused after 17 frames. `run.py` now hands freed blocks back after every frame on the GPU.

Changes 1 and 3 are in [attention_no_mask.patch](attention_no_mask.patch). Apply it with `git -C third_party/lingbot-map apply ../../experiments/lingbot_map/attention_no_mask.patch`.

Even with these, the default 64-frame window does not fit on a 16 GB card this way: 2.8 GB of model plus about 0.2 GB for each frame held gives 16.4 GB of live memory. The run used a 48-frame window and 4 anchor frames (the paper's Table 9: 5.4 m with 4 anchors at the default window, 5.5 m at 48 frames, against 5.3 m). It took 78.8 s, 1.27 frames per second, with the GPU's memory close to full; a 20-frame probe without the per-frame release ran at 4–5 frames per second. Peak system RAM was 17.1 GB, mostly the CPU-side load.

Scored on the same 100 frames, against the full CPU run cut to the same frames:

| Same 100 frames | GPU: 48-frame window, 4 anchors | CPU: 16-frame window, 8 anchors |
|---|---|---|
| Size from path / from depth | 1.198 / 1.202 | 1.220 / 1.229 |
| Path against ARCore (1.13 m of path, mostly turning on the spot) | RMSE 0.024 m, max 0.060 m | RMSE 0.028 m, max 0.059 m |
| Depth ÷ ARCore tracked point, 0–1 m | 1.06 (1.01–1.07) | 1.07 (1.04–1.09) |
| 1–2 m | 1.04 (1.00–1.13) | 1.06 (1.02–1.14) |
| 2–3 m | 0.98 (0.90–1.05) | 0.94 (0.88–1.03) |
| 3–4 m | 0.99 (0.87–1.05) | 1.01 (0.89–1.07) |
| Over 4 m | 0.88 (0.68–0.97) | 0.90 (0.70–0.99) |

On this stretch the three-times-larger window barely changes the result. Depth medians are within about 5% at every distance up to 4 m, and 12% too near beyond 4 m. The spread (middle half 0.15–0.23 wide at 1–3 m) stays about twice the room build's (0.09 at 1–2 m). The small CPU window is therefore not the main reason for the scatter. The 100 frames span only 1.1 m of movement, so the full-walk path result needs a GPU run of the whole walk.

### LingBot-Map's depth as a part: sized per frame, against Depth Anything V2

The owner judged the LingBot-Map viewer no better than the cleaned room build. The whole-map runs give it one size for the whole walk. This project's pipeline instead sizes every frame's depth to ARCore. So the depth was also scored the way the pipeline would use it, by Task109's method. On the same frames, each model's depth gets one size per frame (median of ARCore depth over model depth on shared pixels), then mean relative error and the share of pixels within 25%. Depth Anything V2 Metric Small runs on the upright image, as the room build does.

| Frames | Reference | LingBot-Map | Depth Anything V2 | LingBot-Map lower in |
|---|---|---|---|---|
| CPU run, 72 frames with fresh ARCore depth | ARCore raw depth | 0.039, 99.7% within 25% | 0.063, 98.5% | 60 of 72 frames |
| CPU run, 55 frames | ARCore tracked points | 0.078, 93.6% | 0.098, 90.6% | 51 of 55 |
| GPU run, 17 frames | ARCore raw depth | 0.042, 99.5% | 0.060, 98.5% | 14 of 17 |
| GPU run, 13 frames | ARCore tracked points | 0.081, 94.2% | 0.102, 90.8% | 12 of 13 |

LingBot-Map's depth has a better shape: 38% lower error against ARCore depth, and 20% lower against tracked points, which reach farther. Its confidence map also marks its worst pixels. Against tracked points, per-frame-sized depth has a middle half 0.162 wide in its least confident quarter and 0.071 wide in its most confident; part of that is distance (median 3.2 m against 1.5 m). The test this points to is a room build with LingBot-Map's depth in place of Depth Anything V2 ([parts note](../../research/feed_forward_3d/lingbot_map_how_it_works.md#next-test-this-suggests)). The scoring script is not yet in the repository: it was run from a scratch file while another session held the task board.

Local outputs: `outputs/lingbot_map/lingbot_map_15oct_first100_gpu/` (with `lingbot-map-first100-gpu-viewer.html`) and `outputs/lingbot_map/lingbot_map_15oct_stride3_cpu_first100/` (the CPU run cut to the same frames), each with `compare.json` and `lingbot_cloud.ply`; VRAM logs in `outputs/lingbot_map/lingbot_map_15oct_first100_gpu_vram.csv`.

Local outputs (not in git): `outputs/lingbot_map/lingbot_map_15oct_stride3_cpu/` holds `compare.json`, `lingbot_cloud.ply` (494,264 points at 2 cm), `topdown.png` (both maps from above with the camera paths) and `lingbot-map-15oct-viewer.html` (203,305 splats, 4.7 MB, embeds photos).
