# Phase 4: hosted processing proposal

The filename is retained from the original brief. Hosting follows phone capture and local backend trials, so it is Phase 4 of five. Nothing has been deployed, uploaded or purchased.

The initial local RGB-D comparison processed 120 frames covering about 3.9 seconds of capture in roughly 2 seconds with supplied poses and 19 seconds with estimated poses. These are preliminary CPU runs; use the completed evaluation receipts for final numbers and timing scope. They do not predict the cost of phone RGB-only depth estimation.

The inspected PC has 64 GB RAM and a 16 GB RTX 5070 Ti. The baseline does not use the GPU. An observed peak working set of about 645 MB is a process-lifetime measurement, not isolated per-job memory. It cannot establish worker concurrency or justify a GPU purchase.

## Measure before selecting capacity

Benchmark representative phone recordings, including failed and long takes. Separate process cold start, model loading if added, steady reconstruction, export and queue delay. Record peak resident memory per worker, optional GPU memory, CPU utilization and storage throughput. Run 1, 2 and 4 simultaneous jobs only within safe resource limits, and report throughput together with the 95th percentile wait and completion time.

Choose CPU hosting first if the selected validated pipeline remains CPU based. Add GPU capacity only when a permitted method needs it and measurements show a benefit. Model licence, device memory and operator support are part of that choice. Local CUDA speed does not imply phone portability.

## Cost worksheet

These formulas contain assumptions, not current provider prices. Obtain dated prices only after region, service and capacity are selected.

| Item | Estimate |
|---|---|
| Upload bytes | `bitrate_bits_per_second * duration_seconds / 8` |
| Retained media | `jobs_per_day * bytes_per_job * retention_days` |
| Worker hours | `jobs_per_month * measured_processing_seconds / 3600 / measured_utilization` |
| Compute charge | `worker_hours * selected_hourly_rate` |
| Storage charge | `retained_GB_month * selected_storage_rate` |
| Transfer charge | `chargeable_outbound_GB * selected_egress_rate` |

For example, an assumed 8 Mb/s recording lasting 60 seconds is about 60 MB before container overhead. One hundred such recordings per day retained for 30 days would use about 180 GB for originals alone. Results, replicas, retries and logs add storage. The bitrate is a planning example, not a capture setting or market price.

A hosted design would use durable object storage for media/results, a persistent job queue and records, and bounded compute workers. Require authenticated job ownership, encrypted transport, region and retention decisions, deletion checks and operational failure reporting. Separate capture time from receipt time. Preserve input hashes, method revisions and settings so a result can be reproduced.

Proceed only after the local backend survives restart/retry tests and the phone results meet agreed measurement goals. Then validate queue behavior, cold starts, cancellation, access control and deletion under load. Report what is still unknown before deciding instance size, concurrency or annual cost.
