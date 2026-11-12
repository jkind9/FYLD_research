# Lumina's phone-to-splat pipeline, and the open-source parts that match it

Checked 8 November 2026, after the owner saw a demo of Lumina 3D v2.3 and Lumina Studio v0.1.4 (announced on [r/GaussianSplatting](https://www.reddit.com/r/GaussianSplatting/comments/1xo5id3/lumina_3d_v23_lumina_studio_v014_are_now_available/)). Reddit refuses automated reading, so the thread itself was not read. The pipeline below comes from the vendor's own pages and App Store listing. The open-source parts were checked on their GitHub pages and papers. Nothing was installed or run. Every speed and accuracy figure is the author's or vendor's claim.

The product itself is described in [the Lumina product note](../products/e2e_product_research/09_lumina/README.md).

## Terms used here

- **Gaussian splat**: a small soft blob with a position, orientation, width, colour and transparency. Many thousands of them, drawn on top of each other, show a scene that looks like a photograph from any angle.
- **Splat training**: adjusting every blob until renders of the scene match the photos taken from the recorded camera poses. It is an optimisation run of minutes to hours, usually on a graphics card (GPU). The original method is [Kerbl et al. 2023](papers/kerbl2023_3dgs_2308.04079.pdf).
- **COLMAP dataset**: a folder of images plus three small files: `cameras.txt` (lens numbers), `images.txt` (one pose per image) and `points3D.txt` (sparse 3D points with colours). It is named after the COLMAP structure-from-motion tool. Every common splat trainer reads it.
- **Known-pose export**: writing the phone's own tracked camera poses into a COLMAP dataset, so the slow COLMAP pose-solving step is skipped.
- **LiDAR**: the laser depth sensor in iPhone Pro and iPad Pro models. It measures depth directly, out to about 5 m. The Redmi Note 11 Pro used in this project has none; its depth comes from ARCore working it out from camera motion.

## Short answer

Lumina is a well-built capture app plus a desktop trainer. Its vendor names no new algorithm. The chain is:

1. The iPhone records RGB images, LiDAR depth and ARKit camera poses, with live coverage colouring in the camera view.
2. The phone refines poses and geometry and merges overlapping scans.
3. The project is exported as a COLMAP dataset or Lumina's own `.lumi` file.
4. Lumina Studio on a Windows PC with an NVIDIA GPU (minimum RTX 3060 8 GB) trains the splats, then measures, draws floor plans and exports PLY, SPLAT or SOG.

Every stage has an open-source counterpart. The tables below list them. Three gaps separate Lumina from this project:

- **Depth source.** Lumina depends on LiDAR. Its own roadmap lists "iPad and iPhone without LiDAR" and Android as 2027 work. This project's ARCore depth has a median of 1.58 m and 95% under 2.54 m on the 15 October walk ([dense surface fusion](../dense_surface_fusion/README.md)).
- **Live versus offline.** Only Lumina's capture preview is live. Splat training runs after capture. The owner requires at least one update per second.
- **GPU.** Splat training needs a GPU in practice. The 14 October owner ruling keeps GPU work off for now. This PC has an NVIDIA RTX 5070 Ti, a 16 GB card, so the hardware exists.

## Lumina's pipeline as the vendor states it

| Step | What the vendor states | Where it runs | Not stated |
|---|---|---|---|
| 1. Capture | "Capture RGB images, LiDAR depth and camera poses simultaneously." Manual ISO, shutter, exposure and white balance; "AutoMagic" measures lighting and locks the settings. FHD, or 4K with Pro. Near and far depth limits with a live depth preview. Adaptive point spacing "from 5 cm down to 1 mm" | iPhone or iPad with LiDAR, iOS 26.1+ | Whether depth confidence and motion-sensor data are saved |
| 2. Coverage | Colour-coded marks in the camera view show "which areas are well captured and where additional scanning is needed". Live 2D and 3D map with the camera path. Capture history shows what earlier scans covered | Phone, live | How coverage is scored |
| 3. Refine and merge | "Refine camera poses and captured geometry using RGB images, LiDAR depth, joints and spatial anchors." Overlapping scans are merged "into a single dataset" and the originals kept. Version 2.1 claims "significantly reduced drift"; 2.2 adds a "Tracking Recovery Guide" | Phone ("ON DEVICE") | The method. "Joints" and "spatial anchors" are not defined. Spatial anchors are an ARKit feature; joints may mean links between scans |
| 4. Export | COLMAP datasets with sparse, downsampled or dense points and a 3D crop box, for PostShot, LichtFeld Studio and Brush. Images are undistorted on export (2.1). `.lumi` keeps images, depth, poses, points and merge corrections | Phone | — |
| 5. On-phone training | "Train on Device (BETA)", experimental | Phone | Method, speed, memory |
| 6. Desktop training | Lumina Studio: "All processing on your own PC". Inputs: COLMAP, image folders (runs COLMAP itself), 360° video, RealityScan exports, `.lumi`. Alignment modes Sparse, Dense and Multi Depth. Staged resolution increase, a default target of 3 million splats, depth folders detected automatically with "COLMAP sparse-depth fallback", automatic person masks | Windows 10/11, "NVIDIA CUDA required"; minimum RTX 3060 8 GB, recommended RTX 4090 24 GB | The training method's name |
| 7. Measure and plan | Distances, connected segments and polygon areas. Floor plans (beta) from point clouds or splat centres, with editable walls and openings, exported as GLB, PNG, SVG, DXF and PDF | PC | Accuracy |
| 8. Export splats | PLY with full splat data, SPLAT (base colours), SOG (compressed) | PC | — |

## Open-source parts, step by step

### 1. Capture apps that record images, depth and poses

| Project | Licence | Platform | Records | Use here |
|---|---|---|---|---|
| [Stray Scanner](https://github.com/strayrobots/scanner) | MIT | iPhone with LiDAR | HEVC video, 256 × 192 depth in mm, confidence 0/1/2, per-frame pose and intrinsics in `odometry.csv`, motion sensors in `imu.csv` | Clear file layout to copy. No COLMAP export |
| [NeRFCapture](https://github.com/jc211/NeRFCapture) | MIT | iPhone/iPad, LiDAR optional | ARKit-posed images, depth on LiDAR devices; streams to a PC over the network (CycloneDDS) | Live phone-to-PC streaming; SplaTAM's iPhone demo uses it |
| [ARKit-Scanner](https://github.com/xiongyiheng/ARKit-Scanner) | Apache-2.0 | iPhone with LiDAR | 1920 × 1440 video, 256 × 192 depth, poses, intrinsics, motion sensors, exposure | Another reference layout |
| [OpenQuestCapture](https://github.com/samuelm2/OpenQuestCapture) | MIT | Meta Quest 3/3s | Stereo images, depth, headset poses; COLMAP export via a companion repo | Has the only open coverage display found: "White indicates head-on coverage, while vivid colors indicate grazing angles" |
| [RTAB-Map apps](https://github.com/introlab/rtabmap) | BSD-3-Clause | iPhone/iPad with LiDAR (App Store); Android with ARCore (APK) | Live mapping with loop closure; saves a `.db` database; exports PLY, LAS, OBJ | The nearest open match to Lumina's phone side, on both phone platforms |
| This project's capture app | Project code | Redmi Note 11 Pro, ARCore | 30 fps Camera2 frames, ARCore pose, intrinsics, tracked points, raw depth with confidence, anchor corrections, exposure per frame ([phone session v2](../experiments/01_camera_capture_delivery/phone_session_v2.md)) | Already records the same streams as Lumina, with ARCore depth in place of LiDAR |

What to take from Lumina's capture side: the project's app fixes focus (`Config.FocusMode.FIXED` in `CaptureActivity.java`) but does not lock exposure or white balance, and shows no coverage view. Locked exposure and white balance matter for splat training, which assumes a surface keeps its colour between photos. A near/far depth limit matches the project's finding that ARCore depth beyond about 2.5 m is unreliable.

### 2. Refining poses and merging scans

| Option | Licence | What it does | Fit here |
|---|---|---|---|
| [RTAB-Map](https://github.com/introlab/rtabmap) | BSD-3-Clause | Loop closure and graph optimisation; multi-session merge "loop closures should be detected between them" | Runs on the phone and on a CPU; already in the [SLAM research](../camera_tracking_and_slam/README.md) |
| Open3D multiway registration and coloured ICP | MIT | Aligns overlapping depth fragments into one pose graph | Already used in `sitescan/fusion/fragments.py`; see [open3d_rgbd](../camera_tracking_and_slam/open3d_rgbd.md) |
| COLMAP `point_triangulator` then bundle adjustment | BSD-3-Clause | Keeps the supplied poses, matches features, triangulates points, then optionally refines poses and points together | CPU. A [COLMAP issue](https://www.github.com/colmap/colmap/issues/2537) reports it stalling when supplied rotations are wrong, so check axis conventions first |
| [PocketGS](papers/pocketgs_2601.17354.pdf) (arXiv 2601.17354) | Paper only; no code found | Takes ARKit or ARCore poses as a start, refines them by bundle adjustment on the phone, then builds a dense prior | Shows refinement fits on a phone: see step 5 |
| [Spectacular AI SDK](https://spectacularai.github.io/docs/sdk/tools/nerf.html) | Free for non-commercial use; not open source | Visual-inertial poses for iPhone and Android, using LiDAR or ToF depth when present; writes a nerfstudio dataset | DN-Splatter's README recommends it for phone data. Not reusable commercially without a licence |

### 3. Exporting to a trainer

| Option | Licence | Note |
|---|---|---|
| COLMAP text model | Format | `images.txt` stores world-to-camera poses with the camera looking along +z and y down. ARCore and ARKit give camera-to-world poses with the camera looking along −z and y up. Converting means flipping the y and z camera axes and inverting the pose. The Task100 viewer already converts ARCore poses to these camera axes ([surface Gaussian viewing](../3d_vision_fundamentals/surface_gaussian_viewing.md)) |
| [rgbd2colmap](https://github.com/rwmutel/rgbd2colmap) | None stated, so the code cannot be reused | Converts ARKit-posed RGB-D frames to a COLMAP model for splat training; a working example of the idea |
| [nerfstudio importers](https://docs.nerf.studio/quickstart/custom_dataset.html) | Apache-2.0 | `ns-process-data record3d` and `polycam` read phone LiDAR captures directly; Record3D uses the phone's poses "so COLMAP is not needed" |

### 4. Training splats on a PC

| Trainer | Licence | Hardware | Reads | Writes | Note |
|---|---|---|---|---|---|
| [gsplat](https://github.com/nerfstudio-project/gsplat) | Apache-2.0 | NVIDIA CUDA; Linux and Windows wheels | COLMAP (examples) | Library | Claims "up to 4x less GPU memory with up to 15% less time" than the original code. Basis of nerfstudio's Splatfacto and of DN-Splatter |
| [Brush](https://github.com/ArthurBrussee/brush) | Apache-2.0 | WebGPU through the Burn framework: AMD, NVIDIA and Intel GPUs; Windows, macOS, Linux, Android, browser (Chrome 134+) | COLMAP or nerfstudio; masks from a `masks` folder | Loads PLY | No CUDA needed. Lumina 2.1 added "Brush Dataset Support". The only open trainer that also runs on Android |
| [LichtFeld Studio](https://github.com/MrNeRF/LichtFeld-Studio) | GPL-3.0-or-later | NVIDIA only, compute 7.5+, CUDA 12.8+; Windows prebuilt binaries are paid | COLMAP | PLY, SOG, SPZ, HTML viewer | The open desktop app closest to Lumina Studio; Lumina names it as a target. Usable as a reference tool, like ORB-SLAM3, not to ship |
| [OpenSplat](https://github.com/pierotofy/OpenSplat) (now under WebODM) | AGPL-3.0 | NVIDIA, AMD or Apple GPU, or "entirely on the CPU (~100x slower)" | COLMAP, nerfstudio, OpenSfM, OpenMVG, ODX; masks folder | PLY, SPLAT, SPZ | The only trainer with a CPU path. About 2 GB of GPU memory per million splats |
| [fVDB Reality Capture](https://fvdb-reality-capture.readthedocs.io/) | Apache-2.0 per its docs | NVIDIA | — | — | NVIDIA's open splat and mesh pipeline; not checked further |

### 5. Training on the phone

| Option | Status | Evidence |
|---|---|---|
| [PocketGS](papers/pocketgs_2601.17354.pdf) | Paper, no code or app found | Swift and Metal on an iPhone 15 (A16, 6 GB). Input: ARKit or ARCore poses plus about 50 keyframes. Average 255.2 s after capture, under 3 GB peak memory, 500 training steps. On a 50-image desk scene, 4.3 minutes and about 2% battery. "We study post-capture reconstruction of static scenes rather than online SLAM" |
| Brush on Android | Open source (Apache-2.0) | Android is a supported build target. No phone training speed is published |
| Lumina "Train on Device" | Closed, beta | No figures |
| [Scaniverse](../products/e2e_product_research/08_scaniverse/README.md) | Closed, free | Trains splats on Android and iPhone; no method or figures published |

### 6. Using depth so splats keep the right shape

Plain splat training only matches photos. Floors can come out thick and walls wavy while renders still look right. Depth from the phone pins the shape.

| Method | Licence | What it adds | Evidence |
|---|---|---|---|
| [DN-Splatter](../surface_denoising/papers/turkulainen2025_dn_splatter.pdf) (WACV 2025), [code](https://github.com/maturk/dn-splatter) | Apache-2.0 | A depth loss that is weaker at colour edges (where phone depth is noisy), plus normal priors; starts the splats from 1 million points back-projected from sensor depth; meshes through TSDF (`gs-mesh o3dtsdf`) | On the iPhone MuSHRoom rooms, depth error (AbsRel) falls from 0.0787 (Splatfacto) to 0.0228. Training 36.9 min against Splatfacto's 8.9 min on ScanNet++ (RTX 4090). Suggested sensor-depth weight 0.2 |
| [AGS-Mesh](papers/ags_mesh_2411.19271.pdf) (3DV 2025), [code](https://github.com/XuqianRen/AGS_Mesh) | Code licence not verified | Same group. Filters out depth and normal priors that disagree across views, for "low-resolution depth sensors commonly found in smartphones" | Tested on MuSHRoom (iPhone) and ScanNet++ |
| [DensifyBeforehand](papers/densifybeforehand_2511.19294.pdf) (arXiv 2511.19294) | No code found | Builds the starting cloud from sparse LiDAR plus learned depth, instead of growing splats during training | Paper only |
| Lumina Studio | Closed | "Automatic depth-folder detection" with "COLMAP sparse-depth fallback" | Vendor claim |

AGS-Mesh's filtering is the splat-training form of the [surface clean-up](../surface_denoising/README.md) problem: drop depth that other views contradict. The door echoes on the 15 October walk are that kind of depth.

### 7. Building splats live (Gaussian splat SLAM)

These track the camera and grow the splat map frame by frame. All need an NVIDIA GPU.

| System | Licence | Input | Speed (authors' hardware) |
|---|---|---|---|
| [GS-ICP SLAM](papers/gs_icp_slam_2403.12550.pdf) (ECCV 2024), [code](https://github.com/Lab-of-AI-and-Robotics/GS_ICP_SLAM) | MIT | RGB-D | Up to 107 fps for the whole system on Replica; a 30 fps capped mode. RTX 4090 |
| [RTG-SLAM](papers/rtg_slam_2404.19706.pdf) (SIGGRAPH 2024), [code](https://github.com/MisEty/RTG-SLAM) | GPL-3.0 | RGB-D | About 16 fps with an Azure Kinect, 7.3 GB memory; RTX 4090 |
| [SplaTAM](papers/splatam_2312.02126.pdf) (CVPR 2024), [code](https://github.com/spla-tam/SplaTAM) | BSD-3-Clause | RGB-D; iPhone through NeRFCapture | 0.31 fps on a real home scene, per the RTG-SLAM paper |
| [MonoGS](papers/monogs_2312.06741.pdf) (CVPR 2024), [code](https://github.com/muskie82/MonoGS) | Imperial College licence, non-commercial only | RGB, stereo or RGB-D | 8.34 fps on Replica, RTX 4090, per the RTG-SLAM paper |

GS-ICP SLAM is the open option that clears the 1 fps minimum with room to spare, if a GPU is allowed. It has not been tested on phone depth, which is far noisier than the Replica renders it was scored on.

### 8. Streaming reconstruction from plain video

Two owner-supplied links belong here. Both turn ordinary video into 3D as frames arrive, without depth or poses, on a GPU. Neither gives metres by itself.

| Model | Licence | Speed | Note |
|---|---|---|---|
| [LingBot-Map](../feed_forward_3d/lingbot_map.md) (arXiv 2604.14141) | Apache-2.0 | 20 fps on an H800, 12 fps on an RTX 4090, at 518 × 378 | Pose and depth per frame; scale is arbitrary |
| [SLAM3R](../feed_forward_3d/slam3r.md) (CVPR 2025) | CC BY-NC-SA 4.0 (non-commercial) | 20+ fps on an RTX 4090D, at 224 × 224 | Dense points per frame; no camera solving and no global refinement |

### 9. Repairing and extending splat scenes with generative models

Two owner-supplied links. Both use large video diffusion models to fix or extend rendered views, then train the splats again on the fixed views. Details in [generative repair](generative_repair.md).

| Model | Licence | Hardware | Note |
|---|---|---|---|
| [ArtiFixer](papers/artifixer_siggraph2026.pdf) (NVIDIA, SIGGRAPH 2026) | Code Apache-2.0; weights under an NVIDIA non-commercial licence | NVIDIA Ampere or newer; tested on A100 80 GB, H100, GB200 | Fills gaps and removes artefacts in under-captured views |
| [World-from-Motion](papers/world_from_motion_2607.01202.pdf) (Stanford and NVIDIA, NeurIPS 2026) | Code and checkpoint Apache-2.0 | 80 GB A100 or H100 | For scenes with moving people or objects |

Both invent content where the camera never looked. That is the opposite of what a measurement needs, so they are reference only.

### 10. Meshes from splats

| Method | Licence | Note |
|---|---|---|
| [2DGS](papers/2dgs_2403.17888.pdf) (SIGGRAPH 2024) | Not verified | Flat disc splats that sit on the surface |
| [PGSR](papers/pgsr_2406.06521.pdf) | Not verified | Plane-based splats. One indoor benchmark ([PlanarGS](https://arxiv.org/pdf/2510.23930)) scores it ahead of 2DGS on accuracy and F1, behind on completeness |
| [MILo](papers/milo_2506.24096.pdf) | Parts under the Inria Gaussian-Splatting licence (research and evaluation) | Mesh built during training; "up to 10x fewer Gaussians"; an indoor setting (`--imp_metric indoor`) |
| DN-Splatter `gs-mesh o3dtsdf` | Apache-2.0 | Renders depth from the splats and fuses it with Open3D TSDF, the same fusion this project already uses |

### 11. Measuring and floor plans

| Option | Licence | Note |
|---|---|---|
| [Cloud2BIM](papers/cloud2bim_2503.11498.pdf) (Automation in Construction 177, 2025) | Open source per the paper; licence file not checked | Point cloud to an IFC building model with slabs, walls and openings. DXF would need a conversion step |
| This project's grid footprint (Task55) | Project code | Ground plane, top-down height grid, seen and unknown area ([experiment 05](../experiments/05_birds_eye_mapping/README.md)) |

Lumina draws floor plans from point clouds or splat centres. Splat centres sit near surfaces but are placed for appearance, so a plan from the fused depth surface is the safer source of measurements.

### 12. File formats and viewers

| Item | Licence | Note |
|---|---|---|
| PLY | Format | Holds every splat value; the master copy. The project's viewer already writes standard Gaussian PLY |
| [SPZ](https://github.com/nianticlabs/spz) (Niantic) | MIT | About 10× smaller than PLY |
| [SOG](https://developer.playcanvas.com/user-manual/gaussian-splatting/formats/sog/) (PlayCanvas) | Open specification | Splat values stored as WebP images; "typically ~15–20× smaller" than PLY; for web viewing |
| [splat-transform](https://github.com/playcanvas/splat-transform) | MIT | Converts PLY, SOG, SPZ, GLB, HTML viewer and more. Its GPU compression has a CPU fallback, "often 5-10x slower" |
| [SuperSplat](https://github.com/playcanvas/supersplat) | MIT | Browser editor for cropping and cleaning splats |

## How this project's pipeline compares (8 November 2026)

The stages run in the same order, and both split the work the same way: the phone captures, a PC processes. Lumina is ahead in two places that are not algorithms, the sensor and the care taken at capture. This project is ahead on live processing and objects.

| Stage | Lumina | This project | Gap |
|---|---|---|---|
| Camera settings | Exposure and white balance locked; near/far depth limit | Focus fixed; exposure recorded but not locked; no limit at capture | Small |
| Capture guidance | Live coverage colours, capture history, tracking-recovery guide | None on the phone | Real gap |
| Depth | LiDAR in metres to about 5 m | ARCore depth (median 1.58 m, 95% under 2.54 m) plus learned depth sized to it; about 15% too near beyond 3 m | Main gap; hardware |
| Camera path | ARKit | ARCore | Same class |
| Refinement after capture | "RGB-D refinement" on the phone | None of its own: fragments move with ARCore's anchor corrections, with no re-fusing | Gap |
| Merging scans | Several scans merged into one | One walk only | Later need |
| Fusion | Merged point cloud | TSDF fragments, 2 cm cells | Equivalent |
| Clean-up | Not described; LiDAR depth needs less | Visibility vote, then the largest pieces (Task126) | More here, because the depth is worse |
| Exchange format | COLMAP and `.lumi` | Own session format only | Small |
| Photo-realistic scene | Splat training on a GPU | Surface drawn as splats for display | Ruled out while there is no GPU; not needed for measuring |
| Measuring | Distances, areas, floor plans with walls and openings | Floor plane, top-down grid and areas (Task55) | Lumina's is more finished; neither publishes accuracy |
| Objects | Person masks only | Detection, 3D placement, counted once | This project is ahead |
| Live | Capture preview only | Whole pipeline at 1.58 updates per second on the CPU | This project is stricter |

**Why no ready-made tool covers everything.** The end goal needs all five at once: an ordinary Android phone without LiDAR, at least one update per second, metres, objects counted once, and in time running on the phone. Each tool found drops at least one. The closest is LingBot-Map: its demo builds a multi-room map with the walked camera path from plain video, which covers depth, camera path and the fused map (layers 2-4). It lacks metres (one size fit to ARCore's path could supply them), clean-up and objects, and it is built for a GPU. The owner's direction (8 November) is to find the best method first and think about phones afterwards, so it is being tested in Task128. The parts this project uses now are also off the shelf (ARCore, Depth Anything, Open3D, YOLO). The custom work is depth sizing and clean-up, which exist only because there is no LiDAR.

**Lessons to apply.** Count an area as covered only once ARCore depth has measured it, and show that on the phone, so the walker goes closer to far doors and walls instead of leaving them to fallback sizing. Lock exposure and white balance. Cap fused depth near what ARCore can check (about 3 m), alongside the coverage view; a cap alone left the doorway smeared in Task117. Write COLMAP datasets, which also allow CPU bundle adjustment of the ARCore poses with COLMAP's `point_triangulator` and bundle adjuster. Run RTAB-Map's ARCore app on the Redmi as the off-the-shelf benchmark for layers 1–4.

## What this project can take, in order

1. **A known-pose COLMAP export from the existing recordings.** Images, ARCore poses, intrinsics and ARCore tracked points become `cameras.txt`, `images.txt` and `points3D.txt`; depth maps go alongside. It runs on a CPU, needs no new models, and makes every trainer above usable on the 15 October walk. The one risk is axis conventions (step 3).
2. **Two capture-app features:** lock exposure and white balance once lighting is measured, and show live coverage. A first coverage view can colour each fused surface cell by how many frames saw it and at what angle, as OpenQuestCapture does.
3. **A trainer, deferred: CPU tests only for now (owner, 8 November 2026); the GPU comes free later.** Then Brush first (Apache-2.0, no CUDA, also builds for Android), with gsplat or DN-Splatter for depth-guided runs. Feed it ARCore depth where confidence is high and sized learned depth elsewhere, with AGS-Mesh-style rejection of depth other views disagree with.
4. **Live preview stays the fused surface.** The TSDF surface the project already builds plays the role of Lumina's live 3D map on the CPU. GS-ICP SLAM is the open live-splat option if a GPU is allowed later.
5. **Web viewing:** keep PLY as the master and write SOG or SPZ with splat-transform for sharing.

Not to take: the generative repair models for any measured output, and MonoGS and SLAM3R because their licences forbid commercial use. LichtFeld Studio (GPL) and OpenSplat (AGPL) are fine as reference tools on recorded data, but not to ship.

## Questions for the owner

1. **GPU for offline splat training.** Answered 8 November 2026: CPU tests only for now, because this PC's GPU is busy with another project that has priority. GPU methods stay in view for later, and a spare RTX 4060 laptop can run essential GPU checks.
2. **Is a splat scene an output you want?** It looks like the room but is not a measurement. The measured surface stays the record either way.
3. **A refinement pass after the walk.** Lumina shows a live preview, then refines after capture. Would a short pass after the walk be acceptable if the live view stays at one update per second or faster?

## Limits of this review

- The Reddit thread and its comments were not read. Lumina's site pages are long and mostly images, so parts of the Studio feature list come from summaries of those pages rather than exact text.
- The vendor does not name its tracking, refinement or training methods. "Joints" is undefined.
- Licences marked "not verified" were not read from the repository's licence file.
- No code here was installed or run. Speeds come from different GPUs and datasets and are not directly comparable.

## Sources

- Lumina: [site](https://3d.deluva.de/), [Lumina 3D page](https://3d.deluva.de/index.php/lumina-3d/), [Lumina Studio page](https://3d.deluva.de/index.php/lumina-studio/), [roadmap](https://3d.deluva.de/index.php/roadmap/), [App Store listing](https://apps.apple.com/app/id6759076903), [Lumina 3D Light](https://apps.apple.com/app/id6767272286)
- Repositories and papers are linked in the tables above. Saved PDFs are listed in the [topic README](README.md).
