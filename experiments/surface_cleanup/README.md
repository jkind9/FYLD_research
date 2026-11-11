# Surface cleanup trials

These filters were tried and rejected for the adopted room build. Their implementations
remain here for the cleanup tuner and for reproducing comparisons. Product code uses
only [visibility voting and largest pieces](../../sitescan/cleanup/README.md).

| Trial | Functions | Where |
|---|---|---|
| Depth-edge mask | `edge_mask` | `masks.py` |
| Surface viewing-angle mask | `view_angle_mask` | `masks.py` |
| Near-first fusion weights | `near_first_passes` | `masks.py` |
| Statistical, radius and density-cluster outliers | `keep_after` | `filters.py` |
| Separate-viewing-spot support | `wide_support` | `support.py` |
| Pieces grouped by normals and suspect majority | `piece_majority` | `filters.py` |

`views_measuring` and `spot_evidence` retain the tuner diagnostics. Shared depth sampling
comes from `sitescan.cleanup.vote.measurements`; experiments import the product stage.
Trial defaults and arithmetic are preserved. Their evidence and reasons for rejection
are in [surface denoising](../../research/surface_denoising/README.md).

| Script | What it does | Run it |
|---|---|---|
| [`denoise_trial.py`](denoise_trial.py) | Fuses the room-build frames several ways and scores each against held-out ARCore tracked points | `python -B -m experiments.surface_cleanup.denoise_trial --session <recording> --out <folder>` |
| [`cleanup_attributes.py`](cleanup_attributes.py) | The raw fused room and, per point, the evidence each clean-up stage tests, for the tuner page | `python -B -m experiments.surface_cleanup.cleanup_attributes --session <recording> --out <folder>` |

`tools.demos.cleanup_scene` and `tools.demos.cleanup_tuner` turn their outputs into offline
pages. The adopted vote and piece filter are imported from `sitescan.cleanup`.

Run `python -B -m pytest -c pytest-full.ini experiments/surface_cleanup` to check the retained methods and the trials.
