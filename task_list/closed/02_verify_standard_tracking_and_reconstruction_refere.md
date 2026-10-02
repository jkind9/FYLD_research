---
id: "02"
title: Verify standard tracking and reconstruction references
status: closed
priority: MED
type: infra
blocked_by: []
blocks: ["03"]
verification_test: experiments/datasets/tests/test_acquisition.py
plan_reviewed: 2026-10-02 PASS
files:
  - experiments/datasets/README.md
  - data/README.md
  - data/icl_nuim/**
  - experiments/datasets/acquisition.py
  - experiments/datasets/tests/test_acquisition.py
  - task_list/README.md
  - task_list/open/03_define_observation_and_pose_contracts_with_known_g.md
docs:
  - experiments/datasets/README.md
  - data/README.md
baseline_metric:
  source: experiments/datasets/README.md
  field: fresh independent controls
  baseline_value: "0 locally acquired ICL reference assets"
  target: "2 verified reference assets and explicit frame/calibration notes"
created: 2026-10-01
last_updated: 2026-10-02
superseded_by: null
---

# Task 02: Verify standard tracking and reconstruction references

## In plain English

Start with trusted examples whose camera movement and surfaces are known. Check the source descriptions, download the missing reconstruction examples and record exactly what arrived. This gives later experiments reliable inputs without waiting for either phone.

## What

Check primary dataset specifications and permission evidence. Acquire ICL living-room trajectory2 plus its reference surface using the already verified official URLs; validate archives and record hashes. Inspect existing TUM without changing it. Identify a separate TUM sequence for later held-out tracking evaluation before downloading it.

## Why

Tracking needs independent camera poses; reconstruction needs an independent surface. TUM provides the former but not a complete reference surface. The ICL office scene cannot substitute for its living room.

## How

| Claim | Existing owner | Consumers | Evidence |
|---|---|---|---|
| Requirements and references already documented | Existing dataset/source/experiment note | This task and downstream experiments | research/sources/18_icl_nuim.md:13 |
| Existing bounded download, extraction and provenance patterns are archived | Prototype acquisition helpers; preserve unchanged, adapt into active acquisition module with ICL attribution and stricter Windows/gzip checks | Archived sample downloader | archive/task00_prototype/src/fyld_scene_mapping/acquisition.py:22; archive/task00_prototype/src/fyld_scene_mapping/acquisition.py:71; archive/task00_prototype/src/fyld_scene_mapping/acquisition.py:164 |

1. Review TUM formats, ICL calibration/conversion and data permissions from linked publisher sources.
2. Check free storage and declared archive sizes: 429825445 and 89545763 bytes. Confirm URLs and sizes again before downloading. Safety limits (storage guards, not estimator hyperparameters): exact expected compressed lengths, 8 GiB expanded total per archive, 2 GiB per member, 10000 members, and at least 18 GiB free before acquisition. Reject traversal, links, special files and duplicate destinations, including Windows case collisions. Bound the complete decompressed tar before parsing; reject metadata reads above 1 MiB. Use new staging directories; refuse overwrite. Finish reading gzip to validate its checksum, then publish extracted data plus its receipt by a directory rename. Partial downloads/staging never count as ready.
3. Retain URLs, local hashes, exact archive variant and extracted completion receipts. Do not claim a local checksum authenticates the publisher.
4. Inspect depth convention, intrinsics, pose direction and reference-surface frame from actual files and publisher readers; resolve their alignment before scoring.
5. Select a held-out tracking sequence independently of the prototype's tuned Freiburg1 xyz; record selection before method tuning.

All five steps completed on 2026-10-02. Archived inputs/helpers remained unchanged. New acquisition tooling uses the archived patterns with ICL-specific attribution and stricter parser/publication checks. Dataset state is persisted only as raw assets plus JSON receipts; no estimator or scoring consumer was added.

## Invariants and recovery

Reference inputs remain unchanged and outside estimated-method inputs. Record units, frame identities and provenance at each boundary. A partial download or run is not ready data. Publish completed records only after required artifacts validate; interrupted work remains identifiable. Separate origins cannot be fused without a documented transform. No phone, cloud service or GPU is required for the initial control.

Downloads use unique *.part files; completed archives remain cache artifacts only. Extraction uses sibling *.staging-<uuid> directories. EXTRACTION.json travels inside the atomically renamed destination; it records validated archive structure, not scoring readiness. Interrupted staging is retained for inspection and never reused as ready. Refuse existing archive/destination overwrites; recover by validating existing archive bytes/hash and extracting to a fresh staging directory. Dataset-specific inspection is recorded in inspection.json; only both receipts together establish acquired reference inputs. Revalidate files before later scoring. No existing adapter consumes these new paths.

The final downloader publishes provenance before the archive rename. A process death can leave a receipt without a payload, which is explicitly incomplete; a new download can finish without trusting that orphan receipt. The extractor validates gzip into a bounded temporary tar before tar metadata parsing, stages required archive members and the receipt together, then renames. Raw data have no process/thread boundary beyond the single local CLI. No deployment is involved; a fresh workstation needs Python 3.12+, the script and declared free space. Geometry conventions are recorded in data/icl_nuim/conventions.json and remain unconsumed until task 03 verifies them.

## Hyperparameters

hyperparameters n/a: research/contracts first; no estimator settings or experimental values selected by this plan. Any later fixture tolerance or sampling choice must be recorded before execution.

## Verification

Acquisition records identify both ICL assets, each required file and its units. A failed or truncated archive is never published as ready. The reference surface is present separately from fusion inputs. Report compressed/expanded sizes, scene counts and any unresolved frame conversion.

Contract tests in experiments/datasets/tests/test_acquisition.py assert unsafe paths/links/collisions, expanded-size violations and truncated gzip raise before publication; valid bounded archives publish exact member bytes and a receipt. Verify actual frame counts, all PNG decoding, finite pose values and PLY structure before declaring the two assets usable. Archive readiness does not imply geometry is ready for scoring; unresolved transforms must block scoring explicitly.

Before: 0 locally acquired ICL reference assets. Target: 2 verified reference assets and explicit frame/calibration notes.

## Receipts

| Field | Value |
|---|---|
| Closing commit | n/a: workspace is not a Git repository; no commit created |
| Files changed | experiments/datasets/acquisition.py; experiments/datasets/tests/test_acquisition.py; experiments/datasets/README.md; data/README.md; task_list/README.md; task 03 prerequisite/handoff record; this task; data/icl_nuim raw assets and JSON receipts |
| Test status | 23 passed; acquisition statement coverage 88%; mypy, Ruff and Black checks passed; outputs in data/icl_nuim/verification.json |
| Before measurement | 0 locally acquired ICL reference assets |
| After measurement | 2 acquired and structurally verified assets; 519371208 compressed bytes; 751132761 expanded payload bytes |
| Delta | +2 reference assets; 881 decoded RGB/depth pairs, 880 finite poses, 9982296 finite reference points |
| Outcome | Acquisition/format-evidence target met; coordinate transform documented; scoring remains disabled until task 03 independently validates its adapter |
| Plan review | plan-reviewer PASS before start; PR-1 numeric limits, PR-2 completion/recovery and PR-3 archived reuse ownership addressed in this plan |
| Code review | python-reviewer found oversized PAX allocation; fixed with bounded gzip spool and 1 MiB metadata read cap; regression passes |
| Finished diff review | diff-reviewer DR-1 provenance publication ordering fixed; injected write-failure/retry test passes; final code-reviewer APPROVE with no remaining findings |

Exact archive hashes and HTTP retrieval records are in data/icl_nuim/archives/*.json; they are local fingerprints, not publisher authentication. Gzip checks and required-file counts are in each extracted directory's EXTRACTION.json. data/icl_nuim/inspection.json retains all PNG hashes, complete PNG decoding and PLY/pose validation; data/icl_nuim/publisher_evidence.json retains eight checked source snapshots. Existing TUM was inspected read-only (798 RGB, 798 depth, 3000 poses); the first RGB/depth images were decoded, not every TUM image. Freiburg1 desk is predeclared in held_out_tracking.json and remains undownloaded/unevaluated.

The publisher page lists 882 images, but this exact archive has 881 pairs indexed 0..880 and poses indexed 1..880. Match IDs exactly, preserve raw image 0 and exclude it from supplied-pose runs. Supereight's source reader guidance confirms the missing first pose. The PLY is a point cloud with normals, not a triangle mesh.

Task 03 already owns geometry adapters, round-trip projection and empirical reference-frame tests. Those implementation checks are excluded from this acquisition task's acceptance; no surface score or accuracy claim is authorized here. conventions.json records the publisher transform, its reflection (determinant -0.9999992263) and the algebraic pose-world conversion so scoring cannot silently assume identity alignment. This is a named existing downstream task, not an unfinished acquisition check.

Testing evidence: the first test collection failed because acquisition.py did not yet exist. Explicit unsafe-input, truncation, metadata-allocation and provenance-write regressions now pass. Sandboxed Python temporary directories hit Windows ACL failures before assertions; approved runs outside the sandbox passed. Generated test directories were removed using checked paths confined to data/icl_nuim. No benchmark result or tunable estimator setting was selected.
