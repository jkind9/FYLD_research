# Measuring construction progress from top-down views

**Take-away:** A top-down image can be useful for interpreting a reconstructed site. Its visual appearance alone does not prove accurate distances or complete coverage.

## Citation and sources

Aritra Pal, Jacob J. Lin, Shang-Hsien Hsieh and Mani Golparvar-Fard. *Activity-level construction progress monitoring through semantic segmentation of 3D-informed orthographic images.* Automation in Construction, volume 157, article 105157, January 2024.

- [Author university record and abstract](https://experts.illinois.edu/en/publications/activity-level-construction-progress-monitoring-through-semantic-/)
- [Publisher DOI](https://doi.org/10.1016/j.autcon.2023.105157)

The DOI contains 2023; the university record gives the publication date as January 2024.

## What the source shows

The method combines construction photographs with a planned building model linked to a schedule, called four-dimensional building information modelling (4D BIM). It reconstructs an observed point cloud and creates views with parallel projection, called orthographic images. A model labels image regions by activity or material. The results help estimate completed work and annotate the building model.

The abstract describes two building projects and an average error below six percentage points in activity completion. That is a progress-estimation result. It is not a six-percent geometric error, a distance error or a trench-measurement result. The full experimental settings, runtime, hardware and public implementation have not been verified here.

## How we would use it

Our first map should answer simpler questions: where are observed surfaces, what heights do they have, and which areas remain unknown? Activity labels can follow once geometry and the meaning of each class are validated.

For a utility excavation, useful labels might differ from the building activities studied in this paper. We would need labelled site examples and a clear definition of completion. A planned model may be unavailable. That changes the problem rather than merely changing a parameter.

Keep three measurements separate: physical accuracy, observed coverage and activity classification. A successful classifier can still operate on a distorted or incomplete reconstruction.

## Limits and permissions

No local reproduction has been run. An official code or weight release was not verified. Access to a publication does not grant dataset or model reuse rights.

## Questions to carry forward

1. What decision would a top-down map help a remote manager make?
2. Can that decision be evaluated without assuming a complete planned building model?
