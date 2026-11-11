# Surface-based object association

This folder holds a module that decides which detected box belongs to which known object by comparing the visible surface inside each box, not one median depth. It is sub-experiment 07 of [experiment 06, object recognition](../../README.md).

For each box, the module keeps every valid depth sample. It splits the samples into separate surface candidates wherever sorted camera depth jumps by more than 0.08 m, so a foreground object and the wall behind it stay apart. It then matches candidates to existing objects one to one, using the median nearest-sample distance between surfaces, and leaves a detection unresolved when two matches are nearly tied.

Visible extent (the box of space the samples span) is reported separately from location uncertainty. Location uncertainty is marked unavailable, because the spread of depth samples has not been calibrated against independent references.

| File | What it does |
|---|---|
| `association.py` | `associate_frame(observations, tracks, next_number, max_distance_m, ambiguity_margin_m)` returns an `AssociationResult` with the decisions, the candidates and the processing time. `surface_candidates(observation)` splits one box into depth candidates. `BoxObservation` holds one box's samples with their source and pose lineage. |
| `tests/test_spatial_association.py` | Tests for depth-layer splitting, one-to-one assignment, duplicate boxes, late births, ties and input immutability. |
| `runs/` | Four saved evaluator runs from 5 October 2026 that compare this module with the box-median method. Two of the four have no `metadata/manifest.json`. |

The module imports its support summary from `04_geometry_identity/spatial_support.py`. [`../08_spatial_uncertainty_latency/`](../08_spatial_uncertainty_latency/README.md) imports `association.py` to time it.

## How to run it

There is no command line. Import the module from the repository root:

```text
.venv/Scripts/python.exe -B -m pytest experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests -p no:cacheprovider
```

It runs on the CPU and needs SciPy.

## Where results are recorded

The module's status and its place in the object-identity chain are in the [experiment 06 README](../../README.md). Its speed is in the [latency trial README](../08_spatial_uncertainty_latency/README.md).
