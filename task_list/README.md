# Task list

## Current records

| Task | State | Outcome |
|---|---|---|
| [00: first prototype](archive/00_finish_and_validate_the_phase_1_scene_mapping_prot.md) | Superseded | Research and preliminary results preserved; integrated validation unfinished when the objective changed |
| [01: independent experiment organisation](closed/01_organise_independent_scene_mapping_experiments.md) | Closed | Five modular plans, cleaned active layout, dataset starter and preserved prototype evidence |
| [02: standard references](closed/02_verify_standard_tracking_and_reconstruction_refere.md) | Closed | Both ICL assets acquired and structurally verified; 880 posed image pairs identified; held-out TUM desk selected; geometry tests remain task 03 |
| [06: recovered research and current tracking](closed/06_recover_interrupted_research_and_review_current_or.md) | Closed | Original Claude evidence preserved; current ORB comparison, eight supplied sources and Android implementation review linked from research |
| [07: mobile stereo products](closed/07_review_mobile_stereo_mapping_products_against_the_.md) | Closed | Four product routes reviewed; live map-rate evidence separated from depth rates; shared site measurement and object counting approach captured |
| [03: geometry contracts](open/03_define_observation_and_pose_contracts_with_known_g.md) | Open, first | Verify units, projection, pose direction and reference-surface alignment |
| [04: reconstruction control](open/04_evaluate_reconstruction_with_supplied_depth_and_po.md) | Open, next | Measure supplied-depth/supplied-pose surface error and coverage before replacing inputs |
| [08: phone feasibility](open/08_check_phone_capture_feasibility_alongside_reconstr.md) | Open, alongside 03/04 | Inspect both phones; establish accessible streams, timing and calibration |
| [09: recognition and persistent counting](open/09_evaluate_scene_object_recognition_and_persistent_counting.md) | Open | Add checked-observation identity controls, then recognition and measured-map integration |
| [05: tracking control](open/05_evaluate_tracking_with_supplied_benchmark_depth.md) | Open | Independently measure tracking after task 03; substitute poses into reconstruction later |
| [10: repository publication](closed/10_prepare_research_repository_and_publish_initial_main.md) | Closed | 119-file initial snapshot published on main; remote SHA verified; data/environment exclusions and review limitations recorded |

The [experiment guide](../experiments/README.md) is the active technical plan. These records track work and evidence rather than implementation dependencies.

The agreed implementation order is task 03, then task 04. Run the small phone-feasibility check in task 08 alongside them. Task 09 can begin vocabulary/data planning now, but 3D association uses task 03's contracts and reconstructed-map integration follows task 04. Task 05 remains independently testable after task 03. No implementation or experimental acceptance thresholds have been selected by this board update.

Work in this project is tracked as tasks. One file per task. The folder a task sits
in is its state:

| folder | meaning |
|---|---|
| `open/` | being worked on now (status `in_progress` = the active one), or waiting to be picked up (`open`) |
| `pending_review/` | finished, waiting for a human to check it |
| `closed/` | done and signed off |
| `archive/` | dropped, or rolled into another task |

There's no app and no database — the folder is the board, and `git` is the history.

Manage tasks with the tool (don't move files by hand):

```
node ~/.claude/task-system/task.js list             # open tasks + what's active (* = in_progress)
node ~/.claude/task-system/task.js new "title" --files src/x.py --docs src/README.md
node ~/.claude/task-system/task.js start <id>       # make an open task the active (in_progress) one
node ~/.claude/task-system/task.js move <id> pending_review
node ~/.claude/task-system/task.js move <id> closed   # refused until receipts are filled
```

**Two frontmatter fields the hooks enforce — `files:` and `docs:`** (YAML lists of
repo-relative paths). They link a task to the code it owns *and* the documentation that
code lives under, so neither is forgotten:

- **`files:`** — the code/test files this task touches. The PreToolUse task-gate
  (`~/.claude/scripts/hooks/task-gate.js`) blocks a 2nd+ code write that isn't matched by
  the single in_progress task's `files:` globs. If the work grows, add the new file here.
- **`docs:`** — the README(s)/docs that document this task's code. The Stop completion-gate
  (`~/.claude/scripts/hooks/task-complete-gate.js`) **blocks session end** when a
  code-changing in_progress task either declares no `docs:`, or declares docs that weren't
  updated **this session** (a SessionStart hook, `docs-snapshot.js`, baselines the working
  tree so a doc merely dirty from earlier work doesn't count). Satisfy it by editing the
  listed docs this session, or write a one-line `docs n/a: <reason>`.

The same completion-gate also enforces a **tests floor**: when code changed, a test must have
been added/updated this session (any `tests/` path, or `test_*` / `_test` / `*.spec` / `*.test`
naming), or you write a one-line `tests n/a: <reason>` (rename/comment/pure-doc). The gate only
proves a test was *touched* — the **rigour** is on you (see "Testing standard" below).

A non-blocking Stop reminder (`deps-surface.js`) also lists, for each changed `.py`, the
modules that import it — the dependents you may need to update too.

## Testing standard

The gate checks that a test exists; this section is how you make it a test that would actually
catch a bug. Two failure modes to avoid: **incomplete** (you forgot the empty-input case) and
**tautological** (the test passes no matter what the code does). Different fixes:

**Completeness — walk two checklists.** Don't enumerate hundreds of inputs; test one representative
per *class of behaviour* (equivalence partitioning) plus the *boundaries* between classes.

- **Right-BICEP** — *what* to test: **R**ight (correct result on a known input), **B**oundary
  conditions, **I**nverse (round-trip: `decode(encode(x)) == x`), **C**ross-check (agree with a
  simpler/reference implementation), **E**rror conditions (bad input → the right raise),
  **P**erformance (only when it matters).
- **CORRECT** — *which boundaries*: **C**onformance (shape/format), **O**rdering, **R**ange (values
  in bounds — an invariant), **R**eference (external state; **does it mutate its input?**),
  **E**xistence (null / empty / zero), **C**ardinality (the 0-1-many rule), **T**ime
  (ordering/timeouts/concurrency).

Walk the rows, keep the ones that apply, say why. A pure numeric transform usually earns 4–8 tests
(a couple of happy representatives + empty/one/constant/zero boundaries + one per error path), not
one per row and not one per input.

**Rigour — prove the test is load-bearing.** One of:

1. **Red-first** — write the test (or confirm it) *failing* before the code exists / the fix lands.
   A test you've watched fail for the right reason is proven to bite.
2. **Independent review** — a second pass (person or agent) asks: *"would this test still pass if the
   function returned its input unchanged / returned zeros / was a no-op?"* If yes, it's tautological.
3. **Mutation check** (for load-bearing logic) — flip a `>` to `>=`, a `+` to `-`; the tests must go
   red. The objective measure that a test catches bugs.

**Type/return correctness is not a test's job** — assert it with static typing (mypy/pyright), which
checks every path for free. Reserve tests for *behaviour*: values, shapes, invariants, and raises.

**Golden master** (freeze a whole output and compare) is the far end of "Right" — reach for it only
when the output is too rich to assert any other way (arrays, images, rendered docs), and keep a
tolerance so float noise doesn't false-fail. Prefer a narrow property/threshold when one exists.

Each task file opens with an **In plain English** section — 2–5 sentences a reader with no
project context can follow (what is the objective, and how will it be done? — no acronyms, no
file paths). The completion gate blocks a code-changing session while it is missing or unfilled;
`task.js start` scaffolds it into older files. The rest of the file is the engineering record:
**What** we're doing, **Why**, **How** (lead with a **Reuse evidence** table — one row per
"this already exists" claim, each with a `file:line` in the Evidence column), an
**Invariants and recovery** section for stateful/HIGH work (or `invariants n/a: <reason>`),
how we'll **Verify** it, and a **Receipts** table filled in when it closes.

Before starting a HIGH task, run the plan checks while the plan is still cheap to change:
`node ~/.claude/scripts/task-plan-lint.js <task-file>` (deterministic checks: scope gaps,
invariants + reuse-evidence coverage, numeric baseline, vague criteria), `/clarify-task` if
anything material is vague (≤5 questions, recorded in the file under `## Clarifications`),
then the **plan-reviewer** agent (fresh context, reads the actual code and the project
`CONSTITUTION.md` if present, hunts for a plan claim the code contradicts) — and record its
verdict: `task.js review <id> PASS|FAIL`.

Two board-level companions: `task.js audit` is a read-only drift report (declared docs/tests
that don't exist, HIGH tasks missing invariants or a review stamp, stale README task links,
and an inventory of every `docs n/a:`/`tests n/a:`/`still open because` waiver);
`CONSTITUTION.md` in this folder holds the project's non-negotiable MUST principles
(versioned, owner-ratified — plans conflicting with it fail review).
Full guide: `~/.claude/task-system/HOWTO.md`.
