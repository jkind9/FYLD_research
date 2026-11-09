# Review of SLAM links supplied on 7 November 2026

The owner supplied six links and asked whether they change the project plan. The SLAM Handbook has its own note: [slam_handbook.md](slam_handbook.md). This note covers the other five. Figures are the authors' claims; nothing was installed or run.

## Short answer

None changes the order of work. Two raise points the plan did not name:

1. **Moving people and vehicles are an untested risk.** Three of the links treat moving objects as a main way SLAM fails. Every recording in this project so far is of a static scene.
2. **Object-level SLAM is a known alternative for counting.** It optimises objects together with the camera path, where this project matches objects after tracking.

Two links support choices already made: recording lossless images, and keeping the dense surface separate from the tracker's sparse map.

## The links

| Link | What it is | Effect on the project |
|---|---|---|
| [Islam et al. 2025](https://dl.acm.org/doi/10.1016/j.robot.2024.104871), *Robotics and Autonomous Systems* 185, 104871 | ORB-SLAM3 plus the YOLO detector. Feature points on likely-moving objects are removed, sparse optical flow and multi-view geometry are added, and loop detection is improved. Claims lower trajectory error in dynamic scenes than other learned visual SLAM systems. The publisher page refused access; the abstract was read through [Crossref](https://api.crossref.org/works/10.1016/j.robot.2024.104871) and [Cardiff Metropolitan University](https://pure.cardiffmet.ac.uk/en/publications/advancing-autonomous-slam-systems-integrating-yolo-object-detecti/). No numbers or dataset names were available. | Built on ORB-SLAM3, so GPLv3 and reference only. Supports the moving-objects point. |
| [SLAM-ARLab](https://github.com/Jianxff/SLAM-ARLab) | Hobby Android AR app: ORB-SLAM2 on the phone, Unity for display, YOLOv5 (via NCNN) removing feature points on people and animals. The author reports above 15 fps on a Google Pixel 5 (Snapdragon 765G). GPL-3.0; 39 stars. | Suggests image-only tracking plus a detector can run on a mid-range phone, which matters for the deferred on-phone phase (Task57). The Redmi has a different chip, so the frame rate does not transfer. GPL, so reference only. |
| [Friske 2024](https://arxiv.org/html/2409.01915v1), arXiv 2409.01915 | Rescue robot running SLAM; a PC builds point-cloud maps and sends them to an ARCore phone app that shows them from the user's viewpoint. No accuracy figures. | Confirms two choices. H.264-compressed video had artefacts judged unsuitable for SLAM, which supports recording lossless grey images. ORB-SLAM3's sparse map was too thin to display, so RTAB-Map's dense map was used, which supports keeping the dense surface separate from the tracker. |
| [Zhu, Yuan, Zhang and Chen 2025](https://www.researchgate.net/publication/390939070_Bridging_the_Gap_Between_Semantics_and_Geometry_in_SLAM_A_Semantic-Geometric_Tight-Coupling_Monocular_Visual_Object_SLAM_System), *IEEE Transactions on Robotics* 41: 3078-3098 | Single-camera object SLAM coupling object detections and geometry in one optimisation. ResearchGate refused access; only the title, authors and venue were confirmed, through [dblp](https://dblp.dagstuhl.de/rec/journals/trob/ZhuYZC25.html). | Possibly relevant to counting. Read the full paper with chapter 16 of the handbook before any counting redesign. |
| [Awesome Dynamic SLAM](https://github.com/zhuhu00/awesome_dynamic_slam) | Curated paper list on SLAM with moving objects and lifelong mapping, updated October 2026; MIT licence. Lists NGD-SLAM (IROS 2025) and GeneA-SLAM2 as real-time without a GPU, DynoSAM (T-RO 2025) for estimating moving objects' motion, and the Wild-SLAM dataset with iPhone sequences. | A source of CPU-only candidates if moving objects break tracking on site walks. |

## Proposed follow-up

- Include a walk with people moving through the scene in the next capture round (Task52), and in the tape-measured walks (Task75).
- Read Zhu et al. and handbook chapters 3 and 16 when counting work resumes.
