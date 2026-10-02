# Licence and execution decisions

Checked on 1 October 2026. Public download access is separate from permission to use code, datasets and pretrained weights. The decisions below govern this company research workspace; unresolved terms remain unresolved.

| Asset | Primary licence evidence | Decision and local status |
| --- | --- | --- |
| TUM colour/depth dataset | Publisher [License section](https://cvg.cit.tum.de/data/datasets/rgbd-dataset#license): CC BY 4.0 unless stated otherwise; accompanying code BSD-2-Clause | Permitted baseline with attribution. Freiburg1 xyz archive downloaded; short subset executed. No model weights needed. |
| Open3D | [Official MIT licence](https://github.com/isl-org/Open3D/blob/main/LICENSE) | Used for the colour/depth baseline. Retain notices when redistributing. |
| COLMAP 3.12.6 | [Pinned COPYING.txt](https://github.com/colmap/colmap/blob/3.12.6/COPYING.txt), BSD-3-Clause | Source cloned at `4d5b60e19ad268072adaf1267d21fa38a9a828ca`, not built from that checkout. A separate pycolmap 3.12.6 wheel ran a preliminary sparse CPU experiment. Dependencies need their own notices. |
| RTAB-Map 0.22.1 | [Pinned LICENSE](https://github.com/introlab/rtabmap/blob/0.22.1/LICENSE), BSD-3-Clause | Source cloned at `df6300e0ba3e90058f90b09c4d646279366d3516`. Not built or executed. Optional components need separate review. |
| MASt3R-SLAM code | [Official licence](https://github.com/rmurai0610/MASt3R-SLAM/blob/main/LICENSE.md), CC BY-NC-SA 4.0 | Company use permission not established. Not fetched or executed. |
| MASt3R checkpoints | [Separate CHECKPOINTS_NOTICE](https://github.com/naver/mast3r/blob/main/CHECKPOINTS_NOTICE) | Dataset and model restrictions must be reviewed independently of the SLAM code. Not downloaded. |
| MobileStereoNet code | [Official repository](https://github.com/cogsys-tuebingen/mobilestereonet), Apache-2.0 | Code is a reference lead. Checkpoint terms and training-data implications unresolved; no weights run. |
| BANet code | [Official LICENSE](https://github.com/gangweix/BANet/blob/main/LICENSE), MIT | Code is a reference lead. Weight permissions unresolved; no weights run. |
| ETH3D data | [Current publisher site](https://eth3d.ethz.ch/), CC BY-NC-SA 4.0 | Company R&D permission not established. No download or execution. The former `www.eth3d.net` address is obsolete here. |
| EuRoC | [Current ASL page](https://projects.asl.ethz.ch/datasets/euroc-mav/) and [data DOI](https://doi.org/10.3929/ethz-b-000690084) | Current official location identified; licence and download access not cleared in this run. Not downloaded or executed. |
| ICL-NUIM | [Publisher page](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html), CC BY 3.0 | Optional synthetic benchmark with attribution. Not downloaded or executed. |
| VGGT family / InfiniteVGGT | [VGGT repository](https://github.com/facebookresearch/vggt), [Omega project](https://vggt-omega.github.io/), [InfiniteVGGT paper](https://arxiv.org/abs/2601.02281) | Metadata verified; exact code and checkpoint terms not yet reviewed. No company execution clearance claimed. |
| ARCore / RoomPlan | [Google developer policies](https://developers.google.com/terms), [Apple developer agreements](https://developer.apple.com/support/terms/) | Future platform integration requires applicable SDK terms and capture privacy review. No phone session executed. |

The executed baseline avoids restricted pretrained models. This decision does not grant permission to unrelated optional assets. Repository tags are reference snapshots, not claims that those tags are the newest releases. Machine-readable checkout details are in [repositories.json](repositories.json).
