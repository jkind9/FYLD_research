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

Existing entry points remain `src.live.denoise_trial`, `src.live.cleanup_attributes`,
`tools.demos.cleanup_scene` and `tools.demos.cleanup_tuner`. `src.live.clean` forwards the
old names. Their input and output file formats are unchanged.

Run `python -B -m pytest -q src/live/tests/test_clean.py` to check the retained methods.
