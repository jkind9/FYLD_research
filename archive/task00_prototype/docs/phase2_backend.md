# Phase 3: phone-to-PC backend proposal

The filename is retained from the original brief. In the five-phase sequence, phone recordings are Phase 2 and this backend is Phase 3. No service is implemented by the desktop experiment.

Start with replay of a complete captured clip and manifest on the PC. Reuse the existing geometry and reporting functions through an input adapter. First decide how phone input obtains depth, poses and scale; uploading RGB alone does not satisfy the current RGB-D input contract.

## Proposed local design

Use a small FastAPI interface for submission, job status and result retrieval. Store media/results in local files and job records in SQLite. Give each submission a durable job ID and content hash. Heavy decoding and reconstruction belong in bounded worker processes, outside asynchronous request handlers. Admission limits should prevent more work entering than the PC can finish.

```text
recording + manifest -> bounded upload -> validated durable input
                    -> queued job -> worker process -> validated results
                    -> status/result response
```

Proposed states are `receiving`, `validated`, `queued`, `running`, `succeeded`, `failed` and `cancelled`. Publish success only after all required artifacts and receipts are durable. After a restart, preserve completed results and explicitly recover or fail interrupted jobs. Write into a temporary result directory before publishing a complete result. Retries with the same submission identity must not create duplicate work.

| Boundary | Required behavior |
|---|---|
| Upload/decode | Bound bytes, dimensions, duration and decoded frame budget; reject unsupported content |
| Files | Use server-generated paths; reject path traversal and never trust uploaded filenames |
| Time | Preserve media timestamps/timebase; expose dropped frames, duplicates and pose resets |
| Queue | Bound pending jobs and running workers; return retry guidance when full |
| Worker | Persist failure reason and partial-progress status; cancellation must not publish success |
| Retrieval | Authorise job ownership; return manifest plus unknown mask with map previews |
| Transport | Use authentication and TLS when accessed across a network |
| Retention | Agree media/result expiry; delete associated files and records consistently |

## Replay before live transport

Test deterministic replay, corrupt media, an interrupted upload, process death during export, repeat submission and several concurrent jobs. Compare replay with the direct desktop path on the same observations. Inspect map and trajectory output, not only HTTP success.

Only then consider chunks with session/camera identity, monotonically ordered sequence IDs, hashes and acknowledgements. Reconnection must resume from acknowledged chunks. Apply backpressure rather than silently discard frames. Missing chunks or excessive time gaps split tracking segments; the current estimator stops at its first break. A live extension needs an explicit recovery design before it can join segments.

Use WebRTC only if measured latency requirements justify its additional transport and synchronization work. Full-clip upload and chunk replay provide a simpler reproducible starting point. Measure capture-to-result latency separately from upload, queue, decode, reconstruction and export time. Choose a latency target with FYLD after the first recordings, rather than treating the desktop clip's speed as a product requirement.
