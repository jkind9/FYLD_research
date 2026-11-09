# Generative repair of splat scenes: ArtiFixer and World-from-Motion

**Take-away:** both models use a large video diffusion model to repaint rendered views of a splat scene where the capture was thin, then train the splats again on the repainted views. The scenes look more complete. The new content is invented, so neither suits a measured site record. Both need an 80 GB-class NVIDIA GPU. Added 8 November 2026 from two owner-supplied links. Nothing was downloaded beyond the papers, and nothing was run.

Terms: a **video diffusion model** is a network trained to produce video by removing noise step by step, guided by inputs such as rendered frames and camera paths. **Distilling** here means training a fresh splat scene on the model's corrected frames, so the fix is kept in 3D.

## ArtiFixer (NVIDIA, SIGGRAPH 2026)

Riccardo de Lutio, Tobias Fischer, Yen-Yu Chang, Yuxuan Zhang, Jay Zhangjie Wu, Xuanchi Ren, Tianchang Shen, Katarina Tothova, Zan Gojcic and Haithem Turki. "ArtiFixer: Enhancing and Extending 3D Reconstruction with Auto-Regressive Diffusion Models." No arXiv number is linked.

- [Code](https://github.com/nv-tlabs/ArtiFixer) · [project page](https://research.nvidia.com/labs/sil/projects/artifixer/) · [weights](https://huggingface.co/nvidia/ArtiFixer) · [saved paper](papers/artifixer_siggraph2026.pdf)

| Question | Answer |
|---|---|
| Input | A COLMAP scene (images, cameras, sparse points). The pipeline first trains a splat scene (NVIDIA 3DGUT), renders it from the source cameras, then corrects those renders. The model's inputs are rendered colour and opacity, camera ray maps and optional text |
| Output | Corrected frames and video. **ArtiFixer3D** trains a new splat scene on them; **ArtiFixer3D+** runs the corrector again on that scene's renders |
| Models | Built on Wan 2.1 (14B and 1.3B) and on NVIDIA Cosmos3-Nano |
| Speed | At 4 denoising steps on one GPU, the 14B model runs at 8.36 fps and the 1.3B model at 34.38 fps; 101.77 fps for 1.3B with 1 step on 4 GPUs. Tested on A100 80 GB, H100 and GB200 |
| Results | On Nerfbusters and DL3DV, the authors claim 1–3 dB higher PSNR (a photo-match score) than earlier methods. Example: ArtiFixer 3D (14B) on DL3DV, PSNR 20.43, SSIM 0.719, LPIPS 0.252 |
| Licence | Code Apache-2.0. Weights: "Use of the model is governed by the NVIDIA License", linked to the NVIDIA One-Way Non-Commercial License; "for research and development only" |
| Runs on | Linux, NVIDIA Ampere or newer, Docker. A Cosmos3-Nano checkpoint is about 63.2 GB |
| Scale | Metric scale is estimated during data preparation with MoGe, a learned depth model |

## World-from-Motion (Stanford and NVIDIA, NeurIPS 2026)

Liyuan Zhu, Shengyu Huang, Amrita Mazumdar, Tianye Li, Zan Gojcic, Gordon Wetzstein, Iro Armeni, Shalini De Mello and Alex Trevithick. "World from Motion: Generative Dynamic Gaussian Reconstruction from Monocular Video." arXiv 2607.01202, revised 23 October 2026. GradientSpaces, the GitHub organisation, is Iro Armeni's group at Stanford.

- [Code](https://github.com/GradientSpaces/World-from-Motion) · [project page](https://research.nvidia.com/labs/amri/projects/world-from-motion/) · [checkpoint](https://huggingface.co/liyzzz/World-from-Motion) · [saved paper](papers/world_from_motion_2607.01202.pdf)

| Question | Answer |
|---|---|
| Input | One ordinary video of a scene with moving things. Camera poses and depth are estimated upstream (Depth Anything 3); a first moving-splat reconstruction comes from MoSca, Shape-of-Motion or WorldTree |
| Output | A moving (4D) splat scene that can be viewed from new positions and times, plus 3D motion tracks |
| Model | Wan2.1-VACE-14B, fine-tuned; the checkpoint is 8.30B parameters in 16.6 GB |
| Speed | Offline. One DyCheck job (alignment, rendering, generation and scoring of 219 frames) took about 34 minutes on one 80 GB H100 |
| Results | DyCheck, covisible pixels: mPSNR 20.26 against 19.75 for WorldTree and 19.32 for MoSca. 3D tracking PCK@0.05: 0.862 against MoSca's 0.824 |
| Licence | Code Apache-2.0; checkpoint listed as Apache-2.0; separately downloaded Wan parts keep their own licences |
| Released | Partly: code and the DyCheck checkpoint are public; the general video-pipeline weights "will be added when the assets are published" |
| Runs on | A100 or H100 with 80 GB; keep 250 GB free for model files |

## Relevance to this project

- **Not for measurement.** The model card says it directly: "Generated views are plausible completions, not observations." A repainted wall behind a sofa has no measurement behind it.
- **Possible use for viewing.** If the owner later wants a nicer-looking room to walk through, a repaired splat could sit on top of the measured surface. Any repainted area would have to be marked as unobserved.
- **Moving people.** World-from-Motion targets scenes with motion. Site captures will contain people. For a measured static record, masking people out (Lumina Studio does this automatically) is the simpler route.
- **Hardware and licences rule them out for now.** Both need an 80 GB-class GPU, and ArtiFixer's weights are non-commercial.

Related: [Lumina and the open-source parts](lumina_open_source_parts.md), [surface clean-up methods](../surface_denoising/README.md).
