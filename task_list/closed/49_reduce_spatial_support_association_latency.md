---
id: "49"
title: Reduce spatial-support association latency
status: closed
priority: MED
type: experiment
blocked_by: []
blocks: []
verification_test: experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py
plan_reviewed: null
files:
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py
  - experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py
  - experiments/06_object_recognition/experiments/08_spatial_uncertainty_latency/run.py
  - experiments/06_object_recognition/experiments/08_spatial_uncertainty_latency/tests/test_latency.py
docs:
  - experiments/06_object_recognition/experiments/08_spatial_uncertainty_latency/README.md
  - experiments/06_object_recognition/README.md
  - task_list/README.md
baseline_metric:
  source: experiments/06_object_recognition/experiments/08_spatial_uncertainty_latency/runs/20261005T215109.670881Z_b75b396878c74919898f3d75b274cf78/output/results.json
  field: Task49 median paired control call using frozen Task48 association source across 457 proposals
  baseline_value: "120.481 s per 60-frame call"
  target: "Report measured before/after latency, decision equality, and limitations without a preset speed threshold"
created: 2026-10-05
last_updated: 2026-10-07
superseded_by: null
---

# Task 49 — Reduce spatial-support association latency

## In plain English

Reduce the time needed to compare object positions across repeated views. Reuse the same saved 60-frame recording, 457 object proposals, and association policy. Change only how the spatial comparison is computed, then compare every identity decision and total association time against the saved baseline. Report that the recording has no independent physical object reference, so the comparison cannot show which count is correct.

## What

Reduce repeated nearest-sample search work in Task32's support-aware association while preserving its exact decisions and distance scores. Publish a new isolated run with source and input hashes, environment details, per-frame timing, and a verified manifest. Detailed index-build and query timing are unavailable because the component does not expose those stages. Keep the existing Task48 run immutable.

## Why

Task48's saved timing artifact records one plain, uninstrumented support-association pass at 80.049 seconds. Its median of three instrumented passes is about 80.13 seconds, with 65.57 seconds attributed to symmetric nearest-sample distance queries. Task49 reran the exact frozen Task48 source on the same 60 frames and 457 proposals; that control took 120.481 seconds at the median of three repeats. The reason for the 50.5% difference between these separate runs is unknown, so use only Task49's paired repeats to describe its small latency change. Task48 has no independent object-position or physical-count reference, so this is a latency experiment only.

## How

**Reuse evidence** — every "this already exists / lives here / is owned by X" claim gets a
row, with a real `file:line` in the Evidence column. A claim without evidence is a guess:
the plan-shaped failure this table exists to stop is keyword-level grepping passed off as
tracing (a plan once named the wrong file as the owner of a behaviour and no gate noticed).
If nothing comparable exists, write one row saying so and what you searched.

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Task32 builds support candidates and scores them against existing track support | `association.py` | `associate_frame` and association tests | `experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py:188`, `:287`, `:491` |
| Task48 supplies the frozen comparison input, exact source snapshot, and repeat count | Task48 published run | Task49 paired runner | `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/input/execution_input/evaluator/run_timing.py:13`, `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/input/execution_input/evaluator/compare_association.py:24` |
| Shared run publication records configuration, environment, hashes, timing, and verifies the immutable manifest | `experiments.shared.runs.Run` | Task49 run publisher and consumers | `experiments/shared/runs.py:59`, `:137`, `:229`, `:260` |
| Existing association tests cover support boundaries and decisions; Task49 adds cache reuse and duplicate embedded-ID coverage | `test_association.py` | Task32 and Task49 regression checks | `experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py:150`, `:188` |

The concrete plan was to build exact `cKDTree` indexes once per candidate and track-map entry within each frame, then reuse them across candidate-track comparisons. The symmetric median bidirectional nearest-sample metric, one-to-one assignment, uncertainty records, lineage guards, and birth/abstention policy stayed fixed. Tests assert index reuse and preserve matching when separate map entries have the same embedded ID. The paired runner compares Task48's frozen source and current source on the same 60 frames and 457 proposals, with three repeats per method. It records full-call and per-frame wall times. It does not separate index construction from nearest-neighbour query time because the component exposes no such timing stages. The new run records settings, source and input hashes, environment, results, and a verified manifest. The experiment and its limits are documented in the two declared READMEs and this board.

## Hyperparameters

_Required when this task runs or writes an experiment (type: experiment, or `files:`
touching an experiment directory); otherwise replace this section's body with one line:
`hyperparameters n/a: <reason>`. A tunable value that never gets written down here is a
scientific choice nobody flagged as a choice — how frames are sampled, caps, seeds, model
settings, decode/resolution all shape results silently. Enumerate EVERY one. Only new or
deviating values need a fresh human ruling; inheriting a prior receipt's value unchanged
is a valid source. Run `node ~/.claude/scripts/hyperparam-audit.js <repo root>` first —
any key that diverges from prior use must carry a `deviates ... confirmed <date>` row,
and the ruling comes from the user, not from the model's judgment._

| name | value | source |
|---|---|---|
| recording selection | all 60 frames and 457 proposals from Task48 | inherited `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/input/execution_input/evaluator/compare_association.py:24` |
| maximum match distance | 0.35 m | inherited `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/input/execution_input/evaluator/compare_association.py:51` |
| ambiguity margin | 0.05 m | inherited `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/input/execution_input/evaluator/compare_association.py:52` |
| depth-layer gap | 0.08 m | inherited `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/input/execution_input/evaluator/compare_association.py:53` |
| support metric | symmetric median bidirectional nearest-sample distance | inherited `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/metadata/source/experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py:236` |
| nearest-neighbour method | exact SciPy `cKDTree`, one worker | inherited `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/metadata/source/experiments/06_object_recognition/experiments/07_spatial_uncertainty/association.py:240` |
| support-aware repeats per implementation | 3 | inherited `experiments/06_object_recognition/experiments/07_spatial_uncertainty/runs/20261005T190553.450639Z_99c53d40233e4d74839dc55d84284d68/input/execution_input/evaluator/run_timing.py:13` |
| timing scope | full association calls and per-frame wall time; no index/query split is instrumented | n/a component exposes no finer timing stages |
| accuracy limits | none; independent object reference is absent | n/a latency comparison only; no accuracy or physical-count claim |

The script itself mirrors this table in a module-level `HYPERPARAMETERS` dict (value +
provenance per entry, written into the result JSON) — the write-time hook blocks an
experiment entry script without one.

## Invariants and recovery

invariants n/a: this task changes a deterministic in-process calculation and publishes immutable per-run files; it adds no persisted live state, process boundary, or deployment path.

For HIGH tasks, the pre-start ritual (each step while the plan is still cheap to change):
1. `node ~/.claude/scripts/task-plan-lint.js <this file>` — deterministic checks (scope,
   invariants/reuse coverage, numeric baseline, vague criteria).
2. `/clarify-task <id>` if anything material is still vague — up to 5 recorded questions.
3. Spawn the `plan-reviewer` agent on this file — fresh context, reads the actual code
   (and the project `CONSTITUTION.md`, if present), hunts for a claim the code contradicts.
4. Record the verdict: `node ~/.claude/task-system/task.js review <id> PASS|FAIL` — the
   stamp lands in `plan_reviewed:` above; `null` means "never reviewed".

## Verification

How we'll know it worked — and it must be a *real* check, not one written to pass.

- **Contract test(s):** `experiments/06_object_recognition/experiments/07_spatial_uncertainty/tests/test_association.py` asserts a two-candidate/two-track frame builds four indexes and preserves both matches. Its duplicate embedded-ID case asserts the nearer track-map entry is matched at zero support distance. The paired replay checks equality of all 457 output rows across three repeats for each method.
- **Rigour — not green-by-construction:** confirm each new test FAILS without the change
  (red-first), or have the tests independently reviewed. A test that passes no matter what the code
  does is worse than none. Scale the depth to how load-bearing the logic is — don't pad a trivial
  change with a dozen tautological tests.
- **Before/after on the real symptom:** In the corrected Task49 run, median full-call time was 120.481 s for the frozen source and 114.268 s with cached indexes across 457 proposals. The median difference was 5.2%; the median paired-repeat reduction was 1.83%, with one pair 0.03% slower. All 457 output rows matched. Index-build versus query time is unavailable because the component does not expose those stages. There is no independent physical identity/position reference, so accuracy and physical count are unavailable. No speed or accuracy threshold was set in advance.

The completion gate expects a test to have been added/updated when code changed. If this change
genuinely warrants none (rename, comment, pure-doc), write a one-line `tests n/a: <reason>`
(mirrors `docs n/a:`).

## Receipts

The experiment is complete and was handed to pending review on 6 October. No further optimization is scheduled. A new scoped improvement requires evidence that independently scored accuracy justifies its cost.

| field | value |
|---|---|
| closing commit | `14957e6` |
| files changed | `association.py`, `test_association.py`, `run.py`, `test_latency.py`, the experiment README, object-recognition README, task-list README, this task file |
| test | 33 focused tests passed; Task49 Python review found no remaining reproducible defect; Ruff passed |
| before / after | 120.481 s to 114.268 s median full-call time; median paired-repeat reduction 1.83% |
| result | 457/457 association rows identical; small and variable latency reduction; accuracy and physical count unavailable |
| review outcome | The separate-run timing discrepancy is reconciled: Task48 records 80.049 s for one plain pass; Task49 records a 120.481 s median for three paired control repeats of the same frozen source. The cause of the cross-run difference is unknown. Task49 remains pending review for a closing commit receipt. |

Notes / caveats / follow-ups:

- Verified corrected run: `experiments/06_object_recognition/experiments/08_spatial_uncertainty_latency/runs/20261005T215109.670881Z_b75b396878c74919898f3d75b274cf78`; 309 files, complete manifest SHA-256 `9e080c393ffcc3ea22f811f93f6ab73d3348f2bba9fb4fb8d6358808c758a8b6`.
- Prior run `20261005T213545.108406Z_123832963a6348f396feaf1d471d5a3c` preserved but superseded after review found a cache collision for duplicate embedded IDs. Initial import-failed run `20261005T213438.624959Z_6b85741f1c5642a88b16545c495353f3` also preserved.
- Pending review of the completed experiment. The paired-repeat reduction is 1.83% and variable. Task56 owns complete-process timing and independently scored accuracy; unchanged decisions here do not prove accuracy.
- The earlier `78.456 s` rationale had no matching measurement in the preserved Task48 artifact and is corrected to `80.049 s`. Task49's comparison uses its own frozen-source control and same-run paired repeats; do not compare its absolute timing directly with Task48's single earlier pass.

## Closure, 2026-10-07

Closed under Task60 with owner approval. Earlier `still open because` lines above are superseded by this note. Code is committed in `14957e6`. The recording has no independent object positions, so no accuracy claim is made. Independently scored accuracy and complete timing belong to Task56; no further work on this method is scheduled unless Task56 shows identity errors it could fix.
