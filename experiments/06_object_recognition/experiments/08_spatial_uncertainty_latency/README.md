# Spatial support association latency

This experiment measures whether reusing exact nearest-neighbour indexes makes spatial-support object association faster. It times only the association component. It does not measure detector, depth, pose, hosted service, or phone performance.

## Comparison

Both methods processed the same 60 frames and 457 proposals reconstructed from the Task48 frozen inputs. The control uses Task48's saved association source. The changed method reuses one exact SciPy `cKDTree` per candidate and track-map entry within each frame. The distance metric, thresholds, depth samples, poses, class labels, birth policy, duplicate policy, and one-to-one assignment stayed fixed. The three repeats ran baseline-first, cached-first, then baseline-first.

| Method | Median full association time | Median per proposal | Repeats (seconds) |
|---|---:|---:|---|
| Frozen Task48 source in Task49 paired run | 120.481 s | 263.635 ms | 116.393, 120.481, 122.465 |
| Cached indexes | 114.268 s | 250.039 ms | 114.268, 112.359, 122.504 |

The medians differ by 5.2% (1.05× speedup). The three paired repeat changes were 1.83%, 6.74%, and −0.03%; their median is 1.83%. One pair was marginally slower with caching, and the timings vary by several seconds. Treat the speed change as small and inconclusive. All 457 association outputs matched across methods and repeats. This is output preservation, not an accuracy score.

Task48's earlier saved timing run recorded 80.049 seconds for one plain support-association pass. Task49's frozen-source control median was 120.481 seconds across three repeats. The cause of this separate-run difference is unknown. The cached-index comparison uses paired repeats from the Task49 run, where both methods shared the same inputs and timing conditions. Do not compare Task49's absolute timing with Task48's earlier single pass as if they were a direct speedup test.

There is no independent physical identity or position reference for these proposals, so object accuracy and physical counts are unavailable. The run reports full component and per-frame timings. It does not separate index construction from nearest-neighbour queries. Measurements came from one Windows desktop process with Python 3.12.10, NumPy 2.4.2, and SciPy 1.17.1; other processes may have shared the CPU. These timings do not predict hosted end-to-end or phone latency.

## Reproduce and inspect

Run from the repository root with `python -B experiments/06_object_recognition/experiments/08_spatial_uncertainty_latency/run.py`. The runner copies its inputs and source, records settings, hashes and environment, checks every association output, and verifies a new immutable run folder.

The corrected run's [results](runs/20261005T215109.670881Z_b75b396878c74919898f3d75b274cf78/output/results.json), [settings](runs/20261005T215109.670881Z_b75b396878c74919898f3d75b274cf78/input/settings.json), and [manifest](runs/20261005T215109.670881Z_b75b396878c74919898f3d75b274cf78/metadata/manifest.json) are saved under `20261005T215109.670881Z_b75b396878c74919898f3d75b274cf78`. The manifest is complete with 309 files and SHA-256 `9e080c393ffcc3ea22f811f93f6ab73d3348f2bba9fb4fb8d6358808c758a8b6`. The decision signature SHA-256 is `69be99177851717b504aaccbfc0535e2ba988a394df1d652cf66d49f6e6735b5`.

An earlier complete run, `20261005T213545.108406Z_123832963a6348f396feaf1d471d5a3c`, measured the version before a cache-key edge case was fixed. Keep it for history; use the corrected run above for the current result. The first import attempt, `20261005T213438.624959Z_6b85741f1c5642a88b16545c495353f3`, stopped before timing and remains an incomplete preserved run.
