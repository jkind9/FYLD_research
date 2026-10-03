---
id: "04"
title: Evaluate reconstruction with supplied depth and poses
status: closed
priority: MED
type: experiment
blocked_by: []
blocks: []
verification_test: experiments/04_surface_reconstruction/tests/test_surface.py
plan_reviewed: 2026-10-02 PASS
files:
  - experiments/04_surface_reconstruction/**
  - tools/check.py
  - pytest.ini
docs:
  - experiments/04_surface_reconstruction/README.md
  - README.md
  - task_list/README.md
  - experiments/datasets/README.md
  - experiments/README.md
  - experiments/geometry_validation/README.md
baseline_metric:
  source: experiments/04_surface_reconstruction/README.md
  field: fresh independent controls
  baseline_value: "0 independently scored active reconstruction runs"
  target: "Reproducible reference-pose control with surface error, coverage and failure results"
created: 2026-10-01
last_updated: 2026-10-02
superseded_by: null
---

# Task 04: Evaluate reconstruction with supplied depth and poses

## In plain English

Build a surface using known camera positions and measured example depth. Compare it with the published reference shape. This tells us what reconstruction itself gets wrong before adding tracking errors.

## What

Build the reference-pose reconstruction control from verified ICL living-room depth/calibration/poses. Compare direct point accumulation with Open3D surface fusion only after a simple control works. Score against the separate living-room reference surface.

CPU point accumulation and independent scoring now pass analytic and tiny-dataset fixtures. The acquired living-room run remains pending explicit configuration. This task owns pipeline stage 04, not camera motion estimation. Original views and frame identifiers are retained so task 09 can associate object observations with measured geometry. Task 08's phone feasibility check runs alongside this control. Replace reference poses and depth one at a time only after independent controls pass.

## Why

This is the critical geometric control for evaluating later tracking/depth changes. Correct camera poses do not imply correct fusion or surface coverage.

## How

| Claim | Existing owner | Consumers | Evidence |
|---|---|---|---|
| ICL exact-ID adapter already loads supplied metric observations | load_frame | reconstruction input adapter | experiments/geometry_validation/src/icl.py:57 |
| Verified per-frame geometry is available | compute | accumulation control | experiments/geometry_validation/src/control.py:36 |
| Pose origin guard already rejects unresolved frames | require_same_origin | reconstruction fusion | experiments/shared/contracts.py:103 |
| Run publication and artifact checks already exist | Run and verify_run | reconstruction entry point | experiments/shared/runs.py:133 |

1. Write known-surface and invalid-input tests before implementation; use Task03's verified contracts.
2. Start with direct accumulation and explicit validity; keep reference surface out of reconstruction inputs.
3. Add optional CPU Open3D integration as a separate comparison, recording extrinsic direction and all selected settings.
4. Score surface distances in the established shared frame and report reference coverage separately. Avoid fitting scale to hide an error or inferring unseen regions from a closed mesh.
5. Use shared Run/export infrastructure and save matching input, output, debug and metadata stages. Save unique run manifests/results; incomplete runs remain explicitly incomplete. Record failures, timing/memory and visible-reference selection.

6. Keep backend fusion separate from dataset handling and evaluation. Supplied poses are inputs here. A later tracker adapter may revise earlier poses; before integration, define pose revision records and rebuild/update ownership. Preserve the supplied-pose control for matched comparisons.

## Invariants and recovery

Reference inputs remain unchanged and outside estimated-method inputs. Record units, frame identities and provenance at each boundary. A partial download or run is not ready data. Publish completed records only after required artifacts validate; interrupted work remains identifiable. Separate origins cannot be fused without a documented transform. No phone, cloud service or GPU is required for the initial control.

## Hyperparameters

Dataset selection and reporting distance were authorised on 2026-10-02 when the user asked to put a few images through the proposed CPU baseline. Both remain required arguments. Hyperparameter audit on 2026-10-02 reported literal source dictionaries versus serialized receipt values in Task 03 snapshots, not conflicting numeric calibration.

| Name | Value | Source |
|---|---|---|
| scene | clean living-room trajectory 2 | inherited data/icl_nuim/conventions.json:3 |
| depth units per metre | 5000 | inherited experiments/geometry_validation/src/control.py:37 |
| calibration and alignment | copied conventions, exact frame IDs | inherited experiments/geometry_validation/src/icl.py:57 |
| validity | positive finite, every pixel, no clipping or filtering | inherited experiments/geometry_validation/src/run.py:31 |
| frame selection | [1,101,201,301,401,501,601,701,801] | confirmed 2026-10-02 user authorised putting a few images through the proposed CPU baseline |
| distance threshold | 0.05 metres | confirmed 2026-10-02 user authorised proposed inspection run; reporting only, no acceptance limit |
| backend | direct CPU point accumulation, no voxelisation or mesh | n/a first independent control |
| reference selection | all published vertices, no fitted alignment or scale | n/a global coverage includes unseen regions |
| negative controls | depth multiplied by 2; inverse supplied pose | n/a deliberate analytic faults, not scientific optimisation |
| query batch | 100000 points, one CPU query worker | n/a exact-query memory scheduling; no geometry reduction |

## Implementation details

### Interrupted CPU inspection recovery

The nine-frame run stopped externally after seven complete per-frame stage records. It has running status and no completion manifest; preserve it as incomplete. Exact per-frame reverse scoring and distant fault queries consumed 9502.93 seconds over seven frames, whereas geometry itself took milliseconds. For the small authorised inspection, a separate desktop batch evaluator will reconstruct all nine frames again (cheap), score normal points against the full reference, and query reference-to-accumulated-surface distances once using the joined point cloud. This retains exact Euclidean distances and the same denominator. It uses memory proportional to selected points and is explicitly not the mobile backend. A 9,983-point engineering performance probe against the saved seven-frame cloud took 0.185 seconds; no sampled metric is an acceptance result.

Reconstruction and all normal scores are recomputed. Require matching raw inputs, normal model arrays, reference bytes, reporting threshold, fixed settings, NumPy/SciPy versions and relevant scoring code for recovery. Only complete prior runs that pass manifest verification may supply measured fault summaries. Capture the original manifest hashes, validate the exact bytes of each consumed score record, and reverify the prior before publication. Incomplete-prior scores are diagnostic evidence only and are excluded from published metrics. Preserve prior stage/source/status records. Null measurements remain unmeasured and can be recovered repeatedly without crashing. The original interrupted run stays unchanged. The completed baseline contains nine-frame normal measurements and no claimed dataset fault-check measurement; analytic fixtures separately establish fault sensitivity. Plan and diff reviews led to reference/code eligibility checks, corruption rejection and concurrent-change regression tests before closure.

Use the shared full-point cloud preview for the joined observed surface, without point thinning, and link it in the review. Preview memory/time is desktop review cost, separate from per-frame reconstruction. No GPU is involved. The new inspection module requires explicit IDs, distance and recovered-run path; no scientific default changes. The published direct-accumulation baseline can close this task; CPU fusion remains separately configured.

Backend takes Frame records only, guards common origin and exports immutable per-frame point shards with pixel correspondence. Evaluation alone loads the separate binary reference PLY. Use exact nearest-neighbour distances in both directions; reference-to-reconstruction minima update over each shard, so no whole accumulated cloud is needed in memory. Save distance arrays and global coverage denominator; do not call it visible-only coverage. Empty observations contribute no coverage. All-empty reconstruction fails.

Copy and hash inputs before decoding. Copy reference into the evaluation input subfolder; backend never receives it. Save raw RGB/depth, observation, depth/mask/pixels and camera/world/reference-basis arrays, per-frame scores, wrong-scale/wrong-pose scores, aggregate metrics, timing, process peak memory and an HTML review. Shard index is the accumulated surface representation. Run publication reuses shared Run; interruptions restart into a new run. Open3D fusion is a later separately configured comparison, not required to establish direct accumulation.

| Producer/owner | Consumer | Representation | Survives restart? |
|---|---|---|---|
| load_frame, experiments/geometry_validation/src/icl.py:57 | reconstruction backend | Frame, axial metres, exact ID, camera-to-world proper pose | copied raw inputs and observation record |
| compute, experiments/geometry_validation/src/control.py:36 | export and scoring | float64 XYZ, fixed publisher reference basis | saved per-frame NPY shards |
| Run, experiments/shared/runs.py:133 | verify_run | unique directory, atomic status, hash manifest | yes; killed runs stay running and cannot score as complete |

Source of truth is the copied input snapshot. No process or GPU boundary is introduced. Pose source remains supplied. Reconstruction has no reference dependency. Fresh deployments install shared pinned CPU requirements and run analytic fixtures before dataset runs. Existing Task 03 APIs and old runs remain unchanged.

## Verification

An incorrect depth scale or pose direction must worsen the independent geometry score. In a controlled fixture, removing the only observations of a reference patch must reduce its reported coverage. Redundant-view removal may leave coverage unchanged; missing surface must never be labelled observed. Produce supplied-pose surface-error/coverage/timing measurements; no product accuracy threshold is selected yet.

Contract assertions in tests/test_surface.py: known translation yields exact expected points; wrong depth scale and inverse pose increase mean surface distance above zero; removing the sole reference-patch observation changes coverage from 1 to 0.5; invalid arrays/thresholds/origins fail; input arrays remain unchanged. Tiny dataset integration checks copied originals, complete manifests, numerical scores and failed receipts. CPU checks must pass with at least 80% coverage of new code.

Before: 0 independently scored active reconstruction runs. Target: 1 reproducible reference-pose control with surface error, global reference coverage and fault-control results, plus verified artifacts. No product accuracy limit is asserted.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Uncommitted working tree based on 80d4927600bb290040d75d99379d93bb46315451; no commit requested |
| Files changed | experiments/04_surface_reconstruction/src/{backend,dataset,evaluation,export,review,run,inspection,recovery,__init__}.py; tests/test_surface.py; requirements.txt; tools/check.py; pytest.ini; root, reconstruction, dataset, experiment, geometry-control and task-board READMEs; this task |
| Test status | 87 CPU tests pass, including 25 new reconstruction/recovery tests; new code coverage 91.65% (472/515 statements); Ruff and Black pass; mypy passes with missing external stubs ignored |
| Before measurement | 0 independently scored active reconstruction runs |
| After measurement | Nine acquired frames produce 2,732,193 points; mean distance 0.00784716023735381 m, RMSE 0.009156665380712775 m, maximum 0.03150093056109764 m; 2,225,143/9,982,296 reference vertices within 0.05 m = 0.22290893798380654; all observed points within threshold |
| Delta | +25 reconstruction/recovery tests; +1 independently scored acquired-input baseline with complete reviewed publication |
| Outcome | Supplied-depth/supplied-pose point-surface baseline established; gaps remain unobserved; ready for separately controlled tracking/depth substitutions |
| Reviews | Initial plan PASS; recovery plan FAIL on missing reference/code eligibility, fixed then PASS; Python findings on empty controls and malformed summaries fixed with regressions; diff findings on unauthenticated partial records, concurrent changes and null controls fixed and demonstrated RED then GREEN; no finding waived |
| GPU | No GPU imported, probed or workload executed; CPU-only entry point and separate per-run permission requirement documented |
| Deployment | Geometry 0.1223655 s; desktop joined-cloud reverse scoring 171.0361085 s; full-point preview 18.4480662 s; computation before publication 197.4314406 s; peak working set 1,648,340,992 bytes, including scorer/preview. No mobile execution claim |
| Environment | Existing pinned CPU environment used; clean isolated install not tested. Normal filesystem access required for pytest temporary fixtures. Test reviewer temporary repository folder removed |

Completed publication: experiments/04_surface_reconstruction/runs/20261002T145103.184769Z_000165ef2e044376baf54b675172a64e. All 273 artifacts validate; all 68 review links exist. Eighteen copied originals match dataset hashes. Depth/mask/pixel/camera/world/reference/projection arrays for all nine frames exactly match fresh supplied-input geometry; binary PLY points match their arrays. Reference-distance count and covered count match the result. Inspected the accumulated full-point view, original RGB, error raster with metre legend and frame 501 invalid-depth mask.

The initial sequential run 20261002T111323.432090Z_6501d940dfa94f0a8d418ffc1feb2c50 remains incomplete, with seven per-frame records and no manifest. The batch computation completed in 20261002T144439.221160Z_123c9d760b4a4c86bd0a30f23b8a80af. The final publication above preserves all measured numerical arrays and changes earlier recovered-control confidence labels; it retains source publication metadata and separate republication timing. Incomplete-prior fault summaries are retained only as diagnostics and excluded from completed measurements. Dataset fault-check reruns are explicitly waived for this inspection due to expensive distant nearest-neighbour queries; independently specified analytic fault-sensitivity tests pass. CPU Open3D fusion and clean isolated installation are separately configured follow-ups, waived from this direct-control receipt. No named obligation remains within this baseline.

Configuration confirmed on 2026-10-02: IDs [1,101,201,301,401,501,601,701,801], every valid pixel, 0.05 m reporting distance, full reference denominator. This is not a product accuracy limit. No phone, tracking inference, cloud or GPU result is claimed.
