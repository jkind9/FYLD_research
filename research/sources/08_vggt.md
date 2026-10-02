# VGGT: Visual Geometry Grounded Transformer

**Take-away:** VGGT predicts cameras and scene geometry together from images. It is a useful image-only research baseline, but predicted geometry still needs independent checks of scale, coverage and accuracy.

## Citation and sources

Jianyuan Wang, Minghao Chen, Nikita Karaev, Andrea Vedaldi, Christian Rupprecht and David Novotny. *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition* (CVPR), 2025. arXiv:2503.11651.

- [Author paper record and abstract](https://arxiv.org/abs/2503.11651)
- [Official code and model entry point](https://github.com/facebookresearch/vggt)

## What it does

Traditional image reconstruction often estimates matching points, camera positions and geometry through several optimization stages. VGGT uses a trained network to predict camera parameters, depth, 3D point maps and point tracks directly from one or more views.

These outputs describe the estimated scene and how its cameras relate to it. They could provide a starting point for reconstruction or other visual tasks. They are model predictions rather than independent measurements of the actual site.

## Evidence and limits

The arXiv **abstract** claims results across camera estimation, multi-view depth, dense points and point tracking. It also claims sub-second reconstruction, but the corresponding hardware, resolution, image count and timing boundary have not been checked here. This note therefore adopts no throughput figure for planning phone execution.

This review verified metadata, abstract claims and the official code link. It did not reproduce benchmark tables. No evidence here establishes on-device phone performance, construction-scene reliability or metric area accuracy.

## Relevance to a site capture

Our proposed comparison would run image-only geometry separately from a sensor-depth baseline. Use independent measured dimensions to assess scale, keeping those references out of estimation inputs where they serve as validation. Count failures and missing surfaces alongside successful reconstructions.

A rendered new view can look plausible despite geometry errors or learned completion of unseen regions. Evaluate exported coordinates and source-view consistency, then test them against measured references. Do not use photorealism as an area accuracy metric. Workers should record from approved safe positions; insufficient coverage must remain an acceptable unknown result.

No VGGT weights or code were fetched or executed here. Exact code and checkpoint permissions for company use remain unresolved and must be checked separately.

## Questions for the next experiment

1. Is metric scale stable across repeated image-only captures of measured geometry?
2. What errors occur with low overlap, repeated textures or moving people?
3. After permission review, what image count and processing time fit the intended hardware?
