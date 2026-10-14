# Phone AR platforms

What ARCore and Apple's frameworks give a phone app: camera pose, depth and their accuracy. Task75 measures ARCore on the Redmi.

## Notes

| Note | What it covers |
|---|---|
| [arcore/README.md](arcore/README.md) | ARCore and Android phone telemetry inventory |
| [arcore_raw_depth.md](arcore_raw_depth.md) | ARCore Raw Depth |
| [arcore_internals.md](arcore_internals.md) | How ARCore works inside: MSCKF-style tracking, concurrent odometry and mapping, depth from motion; drift measurements (14 October 2026) |
| [arcore_open_replacement.md](arcore_open_replacement.md) | What would replace each ARCore function with open-source or hand-built parts, with checked licences (14 October 2026) |
| [arcore_commercial_terms.md](arcore_commercial_terms.md) | ARCore commercial terms, required user notice and product risks (14 October 2026) |
| [apple_roomplan.md](apple_roomplan.md) | Apple RoomPlan |

## Papers

Saved 13 October 2026 from arXiv or the authors' pages. Paper results are the authors' claims.

| File | Why it is here |
|---|---|
| [realitycheck_2021_arcore_drift.pdf](papers/realitycheck_2021_arcore_drift.pdf) | RealityCheck: ARCore drift measured on a phone |
| msckf_mourikis_roumeliotis_icra2007.pdf | MSCKF, the filter ARCore's tracking is described as building on |
| proprietary_vio_benchmark_arkit_arcore_2207.06780.pdf | ARCore and ARKit internals as described by Kim et al.; drift table |
| patent_US10802147_concurrent_odometry_mapping.pdf | Google patent: concurrent odometry and mapping |
| patent_US11145075_depth_from_motion.pdf | Google patent: depth from motion |
