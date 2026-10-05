# Cached object identities

Replay saved detections to let new objects receive provisional identities even when their class was seen earlier. The command uses recorded scene positions. It runs on the CPU without loading a detector or estimating new geometry.

From the repository root:

```powershell
python -B -m experiments.06_object_recognition.experiments.06_identity_policy.cached_replay
```

The default input is the accepted 60-frame Task22 publication. Its manifest and baseline ledger hashes are pinned in the publisher. To use another completed local run, pass `--source-run <path>`. The source must be inside the repository and contain `input/baseline_observations.json` or `output/observations.json`.

Each invocation prints a fresh output directory under `runs/`. It copies the source ledger into `input/baseline_observations.json`, then writes corrected identities to `output/observations.json`. The output records the source path and manifest and ledger hashes. A hash inventory covers the input snapshot, outputs, configuration and source-code snapshot. The source is checked before replay and again before completion. An interrupted or failed run cannot be loaded as complete.

The recorded frame order, boxes, classes, confidence values, depth-derived positions, camera poses, world and segment identifiers remain unchanged. Matching uses the inherited 0.35 m position limit and 0.05 m ambiguity margin. Valid proposals without an existing candidate can start identities at any frame. Near-tied matches, missing positions and proposals whose candidate was already assigned remain unresolved. Every assigned identity is provisional. New identities can also reflect noisy measurements or duplicate boxes.

Every proposal receives a stable observation identifier derived from the source ledger hash, frame index and proposal index. Object IDs, track histories, unresolved decisions and totals are recomputed together. The JSON output and `output/policy_report.json` report before/after decision reasons and book counts. Association timing excludes inference and geometry. These results measure policy outcomes, not physical object counts or accuracy.

The shared publication tools (`Run` and `verify_run`) create and verify the receipts. The association policy remains owned by `pilot/replay.py`. The publisher's `validate_overlay` function rejects changes to recorded frame or proposal content and settings before demo integration. Displayed totals must be nonnegative integers that agree with the proposal records and final track count.

Run the focused checks with:

```powershell
python -B -m tools.check experiments/06_object_recognition/experiments/06_identity_policy/tests/test_cached_replay.py
```

This cached path does not migrate the object database or replace the broader identity-policy comparison planned in Task31.

## Published result, 5 October 2026

The complete local run is `runs/20261005T102726.235703Z_bace0cc9ceb44abfa9172c16f0f3d53b`. Its 172-file manifest has SHA-256 `a580860117a0b04dab6b400c494b7b70da59696f889628ddbb13cbdb3c0845d2`. It preserves all 60 frames and 457 proposals with unique observation identifiers.

| Policy outcome | Historical | Corrected |
|---|---|---|
| Provisional identities, all classes | 18 | 55 |
| Matched detections | 213 | 346 |
| Unassigned detections | 226 | 56 |
| Unassigned outside the distance limit | 189 | 0 |
| Ambiguous matches | 17 | 37 |
| Missing position | 10 | 10 |
| Candidate already assigned | 10 | 9 |
| Book identities | 1 | 6 |
| Unassigned book detections | 90 of 95 | 5 of 95 |

Association alone took 9.27 ms in this one CPU replay. That excludes inference, localization, file verification, publication and page building; it is not end-to-end latency. More candidate tracks also introduce more ambiguous matches. Independent labels are needed to establish whether new IDs correctly isolate books or split a physical object.

The cup's frame104 and frame359 detections retain `object-0005` across the empty frame268. A separate shifted cup detection starts `object-0011`, so even this return success does not prove a correct cup count. [Demo 06](../../../../demo_outputs/06_objects_in_3d.html) displays the corrected identities and their remaining unassigned cases.
