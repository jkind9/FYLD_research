# Models

Model weights live here and stay out of git. [`manifest.toml`](manifest.toml) is tracked:
it records each model's name, source, revision, SHA-256 hash and licence, so a run can be
traced to the exact weights it used.

| Path | Used by | Licence |
|---|---|---|
| `depth_anything_v2_metric_indoor_small/` | `sitescan.depth` in both pipelines | Apache-2.0 (Small model) |
| `yolo26x.pt` | `sitescan.objects` (experimental) | AGPL-3.0 or commercial (Ultralytics); not cleared for a proprietary product |
| `ZipDepth/`, `Video-Depth-Anything/` | Depth trials in `research/experiments/02_stereo_depth` and `research/evaluation/layers` | See each upstream repository |

Download sources and hashes are in the manifest. `sitescan.objects.load_detector` refuses a
detector file whose hash differs from the one the counts were measured with.
