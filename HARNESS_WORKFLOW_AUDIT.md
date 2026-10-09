# Audit of the AI harness and engineering workflow

**Date:** 8 October 2026
**Project:** mobile_depth_estimation_tracking
**Committed baseline:** `784d0136e6a19d1689b6d77b7b3d9fa0544eb263`, branch `main`
**Scope:** task board, reachable Git history, current working tree, shared harness source, local session records and current public documentation.
**Re-checked:** 8 October evening by Claude; implementation follow-up and completion evidence added 9 October by Codex. Earlier measurements retain their original dates.

## Implementation follow-up, 9 October 2026

The audit recommendations now have implementations committed in the shared harness. Source commit `2cd9102d6931f1fa8568d722a069e3b293d92d67` records the tested implementation. Receipt commit `4b2de540e06bd9b60aeb4e741aed567014d63973` records completed checks and task dispositions. Tasks 03, 05 and 08 are closed. Tasks 02, 04, 06, 07 and 09 retain named acceptance work. The project active Task 65 was preserved.

| Work | Implemented behavior | Remaining acceptance work |
|---|---|---|
| Task02: instruction loading | Separate Claude and Codex instruction files; web rules load for matching paths; installer migrates the obsolete Claude instruction binding, preserves independent backup bytes and selects the native writing style on fresh installations. | Fresh main-session and helper starting-context measurements; owner decision on 32 additional directories; duplicated command skills still exposed to Claude through the shared skills directory. |
| Task03: task transitions | Unknown flags, missing receipts and unreviewed HIGH starts refuse, including worktree creation. Explicit forced starts are journaled. | Complete: source and receipt commits recorded above. |
| Task04: file ownership and documentation | Hooks resolve the target file’s repository. Read-only quoted text passes; ordinary redirects, combined-stream redirects and literal file-copy destinations, including existing destination directories, are checked. | Fresh native write and blocked-write probe. Shell checks cover the tested command forms. |
| Task05: saved code checkpoints | Code closure requires a reachable commit that changed a declared file and still matches declared working and staged files. Optional commits use only the task’s scope. Worktree handoffs preserve moved task metadata and retain recoverable work after failure. | Complete: source and receipt commits recorded above. Historical uncommitted closures remain historical records. |
| Task06: restart handoff | Summaries carry the task’s current state and the last observed check. Real Claude and Codex record formats are read; notifications are filtered, absent facts are explicit, and human notes survive repeated writes. | Fresh stop/start session recovering the next action from its generated handoff. Multi-command output with no reliable command/result pairing remains unknown. |
| Task07: usage and models | Claude reviewer files name their models. Token reporting filters to the task repository, includes helper messages, and distinguishes unknown origins. Worktree starts create their own usage windows. | Codex token accounting and measured cost-versus-quality improvement remain unavailable. |
| Task08: size checks | The size gate uses the file’s repository and permits a previously shrunk oversized file to return up to its committed size. | Complete: source and receipt commits recorded above. Existing oversized modules remain separate maintenance work. |
| Task09: review corrections | Added regression cases for errors found while reviewing the implementations above. The task records each correction and its checks. | Fresh Claude native verification after quota availability. |

The current Claude instruction render is 14,229 bytes; the Codex render is 64,320 bytes. These are file sizes. They do not establish the fresh-session targets of fewer than 95,000 main-session tokens and 55,000 helper tokens. Those targets remain unmeasured.

### What this work showed about the workflow

Passing tests alone missed reachable errors. Independent review found an unreviewed worktree start, token totals contaminated by other projects, real Codex records omitted by synthetic fixtures, staged code hidden by a restored working copy, and file moves that could lose their metadata. Each reproduced case was used to extend the tests before delivery.

Two implementation mistakes also occurred during this follow-up. A regression test imported a probe with top-level side effects and replaced the previous local native-propagation receipt with a partial failed run. The temporary instruction and policy additions were restored; no native assistant was launched by that failed test. The failed receipt was retained separately, and the module was made safe to import. A later string replacement briefly duplicated part of the shell parser and broke its syntax. Review caught it, the damaged span was repaired, and syntax plus regression checks were rerun. These mistakes support keeping both behavioral tests and source review.

Earlier Tasks 02,03 and04 have no preserved pre-start review stamp from their original implementation session. This follow-up records actual later review and corrections; it does not invent earlier approval evidence.

### Verification for this follow-up

Final regression and native results are recorded in the completion amendment below. The original findings and measurements in the rest of this report remain dated evidence from 8 October. Renderer validation checks local adapter parity; a fresh native probe is a separate check. No production accuracy, phone benchmark, whole-repository coverage figure or measured monetary saving is claimed here.

Project Task 68 still covers the default command’s missing depth and area test suites. Task 65 owns the project’s active slot. This harness session did not take that slot or edit the project’s application code. The 32 configured additional directories, duplicate command skills and imported oversized files remain explicit follow-up decisions rather than hidden completion claims.

### Completion amendment, 9 October 2026

The final stable source passed 135 regression tests, 33 standalone invariant probes and 18 local adapter checks. The renderer completed. Independent source and finished-diff reviews have no remaining actionable findings in the reviewed scope. Five agents were used across implementation and reviews, with existing agents reused for follow-up checks.

A fresh native Codex session returned the expected shared source path and recorded successful startup, prompt, stop and session-end hooks. Its session is 01a11fde-0465-7d41-8589-b8b289cfc318. The combined propagation check also confirmed that an instruction edit reaches the installed files, adapter behavior matches while retaining each provider’s instruction hash, and the native Codex prompt loader sees the temporary validation token.

Fresh Claude model verification was blocked by the provider’s weekly usage limit. Its reported reset is 11 October at 20:00 Europe/London. Both instruction and policy files were restored byte for byte against pre-probe snapshots. The machine-local propagation receipt is explicitly marked partial; fresh two-provider native success is not claimed.

Harness board lint reports 10 tasks, 0 errors and 0 warnings. Tasks 00, 01, 03, 05 and 08 are closed; Tasks 02, 04, 06, 07 and 09 are pending review. There is no active harness task. All nine implementation tasks record the source checkpoint. Project Task 65 remains active, and its application changes were preserved. Existing oversized imported modules remain maintenance work.

The measured source render sizes are 14,229 bytes for Claude and 64,320 for Codex. Fresh Claude starting-token targets, full code coverage, complete Codex token accounting and monetary savings remain unmeasured. Task 68’s default depth/area test inclusion remains open in the project. The owner authorized commits on 9 October. A precommit security review passed, all 25 source hashes matched the final tested versions, and the staged secret-pattern scan found zero hits. The 18 adapter checks passed again after committing. The initial restricted rerun could not launch a child process; the approved rerun completed successfully. Fresh Claude verification can run after quota is available.

Local receipts: [Task09 verification and follow-ups](C:/Users/jkind/.agents/harness/task_list/pending_review/09_fix_the_reproduced_harness_review_gaps.md), [partial native propagation](C:/Users/jkind/.agents/harness/state/propagation.json), [shared harness README](C:/Users/jkind/.agents/harness/README.md).

## Overall assessment

The harness is useful. It preserves decisions, makes missing evidence visible and supports reviews that catch real defects. The project has also grown a substantial set of tests and moved towards smaller, replaceable components. Those are observable engineering gains.

It does not yet guarantee the auditability its rules promise. Closing a task mostly checks whether receipt text looks filled. It does not establish that the code, tests, documentation and reviewed version belong to one recoverable checkpoint. Several recently closed tasks exist only as uncommitted work. The current CLI also has a reproducible dry-run defect.

Context growth is a measured problem. Both assistants receive the same 64 KB instruction document. Local Claude session records show large amounts of accumulated context, while the generated restart summary leaves the next-action fields empty. Task records preserve useful knowledge, but some have become large enough to create a second source of context overload.

**My judgment:** you are using AI productively and exercising useful engineering judgment. The process is strongest at preserving research decisions and correcting defects. It is weaker at preventing premature completion, keeping context small and making verification independent of the assistant that wrote the change. Your own review still supplies several checks that the machinery appears to guarantee.

The next improvement should be to make a few promises enforceable and reduce the material loaded by default. Adding more agents, commands or mandatory prose would not address the main failures found here. The owner's follow-up makes token reduction an explicit priority: extra token use must buy a measurable correctness or accuracy benefit.

The follow-up recommendation is to repair reproduced gate defects, then compare the repaired workflow with a leaner one using the same acceptance tests and implementation model. Use one fresh Claude audit to challenge this report from source. Include code comprehension and human correction effort in the evaluation. Capture command evidence automatically and record consequential decisions briefly; do not expand task files into thought transcripts.

### Update: Claude re-check, 8 October 2026 (evening)

The report up to the addendum sections was written by a Codex/GPT session. A Claude Opus 5.5 session then re-checked it from source, validated the dry-run fix that followed it, and measured the Claude side of the context problem. Details are in [Claude re-check: validation and new findings](#claude-re-check-validation-and-new-findings). The settled plan is in [Going forward: the finalised operating model](#going-forward-the-finalised-operating-model). In short:

- **The dry-run fix is real.** Hashes match the receipt, 55 of 55 new tests and 33 of 33 existing probes pass, and removing the one-line fix makes 28 of 55 tests fail. Both assistants load the fixed file. It is not committed.
- **Three neighbouring gaps remain**, all reproduced again: a mistyped `--dryrun` performs a real move, a task with no Receipts section closes, and a HIGH task with a FAIL review starts.
- **Claude sessions load the shared instructions about three times.** Each main session starts at about 122,000 tokens of context before any work, and each subagent at about 80,000. About 113 KB of the loaded instruction text is an exact duplicate, so the 64 KB figure below undercounts the Claude side.
- **The task gate judges the wrong repository.** It checks every write against the board of the folder the session started in. Here it blocked a scratch file in the session's temporary folder because another session's Task 65 was active.
- **Closed-without-commit has grown** from four tasks to six across the two boards, including this audit's own task and the harness fix.
- **The default test run still skips the depth and area tests** (F5 unchanged).

Most of the original report holds. One priority changes: removing the duplicated instruction load is the cheapest large token saving available, so it now comes first.

### Key points

| Question | Assessment | Evidence |
|---|---|---|
| Does the task system keep AI focused? | Partly. It defines ownership and now protects the active task from another session. Older blockers and completion notes still drift. | Task60 board cleanup; Task51's stale mapping blocker; the live refusal to take Task65's lock during this audit. |
| Does it preserve a useful audit trail? | Yes for many decisions and bounded results. It is incomplete as a versioned chain of proof. | Detailed receipts and correction histories; four uncommitted closures; ignored transition journal. |
| Does it control technical debt? | There are positive signs, especially module boundaries and tests. Prevention is inconsistent. | Task59 reduced the runner and introduced replaceable methods; historical files exceeded the declared size limit; broad commits and test-discovery gaps remain. |
| Does it avoid context bloat? | No. The current default instructions and observed sessions are large. | 64,239-byte instructions; approximately 390,000 median reported input/cache tokens in the filtered session sample. |
| Can we measure its value for money? | Not reliably from the current records. | Usage exists in provider logs, but it is not joined to task outcomes, human intervention or review quality. No comparable workflow baseline was available. |
| Does the code explain itself to a new reader? | Some orchestration and invariants do. Size limits alone are insufficient. | Explicit walkthrough stages and independent scoring; selected functions span 95–144 lines and one step has six nested control/resource constructs. A fresh-reader check is proposed. |
| Are more tools the answer? | Only for specific gaps. | Experiment provenance, compact repository context and workflow evaluation have plausible uses; another task board would duplicate existing ownership. |

## Evidence and method

This was an audit, not an implementation change. Application code, harness source and other tasks' states were left untouched. Suspected CLI failures were tested in a disposable operating-system temporary folder. Three agents supplied board, history and harness evidence. Their turns subsequently hit a provider usage limit; missing checks were completed directly. Their partial findings were not treated as completed independent approvals.

The board and local transcripts changed while the audit was running. Task65 became active, and another task was created. The board baseline below excludes this audit's Task66 and tasks created afterwards. Figures describe inspection snapshots, not a frozen simultaneous database export.

### Measured baseline

| Measure | Observation | Meaning and qualification |
|---|---|---|
| Existing task records | 66: 10 open, 48 closed, 5 stale, 3 archived, 0 pending review | Baseline records through Task65. The closed count is not a product-success rate. |
| Closed HIGH/CRITICAL tasks with PASS plan stamps | 14 of 14 | Good recorded discipline. A date and PASS do not identify the exact reviewed version. |
| Task-record volume | About 0.99 MB and 9,300 lines | Excludes the board README and this audit. Concurrent edits changed exact totals between samples. |
| Largest inspected task | Task59, about 1,100 lines | Includes extensive implementation examples and later corrections. Useful history, expensive restart material. |
| Reachable Git commits | 43, dated 2–7 October 2026; 2 merges | A short, intensive development period. This cannot establish long-term maintenance quality. |
| Non-merge code commits after the initial import | 16; all 16 also change code test files; 12 also change task files | Shows tests and records commonly travel with code. Does not prove tests ran, failed first or cover the motivating defect. |
| Committed code at HEAD | 254 files; 26,114 non-test lines and 14,466 test lines | Counting `.py`, `.js`, `.ts`, `.kt` and `.cjs`; test classification is path based. Excludes ignored run artifacts and vendored working-tree material. |
| Initial imported code | 27 files; 2,239 non-test and 535 test lines | Same counting method. Growth shows production of work, not its value by itself. |
| Tracked code over 800 lines at HEAD | 0 | Positive current state. Historical breaches and large task documents are discussed below. |
| Installed shared instructions | 64,239 bytes, 1,431 newline-separated lines | Claude and Codex copies have the same SHA-256: `f53535ae45eb5e0549179f7b5d663fcc03b7befc3543af0dfd013f6831aafdd3`. |
| Shared source catalog | 50 agent files, 84 command files, 257 skill files | Source inventory. Plugin skills and generated compatibility surfaces use different scopes; these are not all necessarily loaded. |
| Default pytest discovery | 857 tests collected successfully in one snapshot | Discovery only, not a test pass or coverage measurement. |
| Separate depth/area discovery | 71 tests collected, plus 4 permission errors | These directories are absent from both default suite lists. Inaccessible temporary folders also interrupt explicit directory collection. |

Git history metrics exclude merge duplication. Counting all additions without qualification exaggerates code growth: commit `3167451` alone includes an 11,259-line member-hash JSON record. The history review found 77,149 added and 5,051 removed lines across non-merge changes after the initial import; only 40,397 added and 2,586 removed lines were in the inspected code extensions, including shell files.

### Context measurements

A read-only pass over 16 top-level local Claude project transcripts, about 70 MB in total, retained the latest usage record per assistant message ID and excluded synthetic messages. A filtered snapshot contained 1,288 unique assistant message IDs:

| Reported input plus cache-token count | Observation |
|---|---:|
| Median | 389,747 |
| 90th percentile | 599,855 |
| Maximum | 749,228 |
| Messages above 200,000 | 1,136 |
| Messages above 500,000 | 359 |

The calculation adds `input_tokens`, `cache_creation_input_tokens` and `cache_read_input_tokens`. It measures the provider-reported context supplied to each recorded message. Cached tokens are repeated context, not newly authored material. These figures are **not a monetary bill**, a measure of unique information or proof that every large context caused a defect. The sample excludes subagent and Codex transcripts. No reliable project-wide compaction rate was established.

The local transcript directory is `C:/Users/jkind/.claude/projects/c--Users-jkind-Documents-02-Work-01-fyld-mobile-depth-estimation-tracking`. Raw conversation content was not copied into this report.

## Findings

Priorities below are this audit's engineering recommendations. They are not output from an automated scoring rubric.

### F1. HIGH: dry-run performs real task transitions

[Task60](task_list/closed/60_prune_task_board_to_the_accuracy_latency_and_mobil.md), line 91, records that `task.js move <id> closed --dry-run` performed 16 actual closes. The moves happened to be intended, so they were retained. That does not make the command's behaviour correct.

The defect still exists. In an ordinary temporary board, `move 01 closed --dry-run` exited successfully and created `closed/01_fixture.md`. The source only returns early for dry-run when `worktreeHandoff` is true. Normal board transitions continue to write files and the journal. See shared `task-system/task.js`, lines 483–505. Its argument parser also silently ignores unknown flags at line 891.

**Improve:** implement dry-run before every mutation, in every transition mode. Reject unknown flags. Tests should compare the complete fixture before and after each dry-run, including task bytes, folder contents and journal bytes. A typo in a flag must return a nonzero exit without mutation.

**Status, 8 October evening:** fixed for the exact `--dry-run` flag in the canonical CLI, uncommitted (harness Task 01, validated in the Claude re-check below). A mistyped flag such as `--dryrun` still performs a real move.

### F2. HIGH: closure validates receipt appearance, not the full completion contract

Shared `task-system/task.js`, lines 51–53, treats a missing Receipts section as having no unfilled receipts. `cmdMove`, around line 490, uses that check to allow closure. It does not require declared documents, contract tests, a valid review, a source checkpoint or even a filled plain-English section.

Two temporary reproductions succeeded: a task with no Receipts section closed, and a task with one filled result row closed despite missing declared docs and tests. Both had a HIGH priority and a FAIL plan stamp.

The Stop hook does not repair this. Shared `scripts/hooks/task-complete-gate.js` first returns when no dirty code exists and then inspects only tasks still marked `in_progress`. Moving a task out of that state, or committing its code before Stop, can remove the state the hook checks. A temporary fixture with dirty code and no active task returned exit 0 from this hook. Other hooks may issue nudges; that is different from this completion check refusing the state.

**Improve:** make the transition command call one shared completion validator. Stop should provide a reminder and recovery path, not be the only place that checks completion. Validate required receipt fields and their types. Separate a legitimate continuation or waiver from an accidental missing section. Persist task-owned changes so committing or moving the file does not erase the evidence under examination.

### F3. HIGH: four code tasks are closed without a recoverable Git checkpoint

The working-tree receipts explicitly say “Uncommitted workspace changes; no commit was requested” for:

| Task | Receipt location | Committed-state difference |
|---|---|---|
| 54: depth comparison | [Task54](task_list/closed/54_implement_and_validate_real_metric_depth.md), line 127 | HEAD still has the task open; new experiment implementation is not in HEAD. |
| 55: dimensions and area | [Task55](task_list/closed/55_implement_site_dimensions_and_area_measurement.md), line 126 | HEAD still has the task open; closure and implementation changes are local. |
| 62: depth review corrections | [Task62](task_list/closed/62_close_task_54_review_gaps_phone_build_score_memory.md), line 109 | Closed task and new correction work are absent from HEAD. |
| 64: interactive report | [Task64](task_list/closed/64_interactive_walkthrough_run_report_with_ground_tru.md), line 89 | Closed task and report implementation are absent from HEAD. |

The receipts are candid, which helps. The state name nevertheless conflates local completion with versioned completion. A checkout of the closing SHA cannot reproduce these closures or distinguish all their shared-file edits. The initial working-tree diff alone reported 22 tracked files with 1,193 additions and 235 deletions, before accounting for the untracked implementation files.

**Improve:** distinguish verified local work from a versioned completion. Either retain it in a suitable pending state until a checkpoint is authorized, or preserve an explicit source snapshot and artifact hashes and label its durability. Do not automatically commit unrelated work to satisfy a rule. Agree the checkpoint policy once, then apply it consistently.

**Status, 8 October evening:** grown to five closed tasks in this project (54, 55, 62, 64 and the audit's own Task 66) plus harness Task 01. See F16.

### F4. HIGH: review stamps do not enforce reviewed-version ownership

All 14 closed HIGH/CRITICAL tasks have a PASS plan stamp. However, `task.js start` does not require plan lint or a PASS verdict. A temporary HIGH task carrying `plan_reviewed: 2026-10-08 FAIL` started successfully. The pre-start ritual is a human/assistant obligation, rather than a property enforced by the command.

The stamp also lacks a hash of the reviewed plan, a reference to the review output and a link to the code version. A later plan edit can leave the earlier PASS unchanged. Finished-diff reviews are often described in prose, but there is no equivalent structured version binding.

**Improve:** require a current PASS for HIGH/CRITICAL starts. Bind it to the plan's normalized content hash, excluding the stamp itself. Bind final review to a source tree or diff hash. A scope or invariant change should invalidate the appropriate review. Preserve review findings and dispositions as task evidence, without asking the main agent to reconstruct them from memory.

### F5. HIGH: the default test command omits newly important modules

[pytest.ini](pytest.ini), line 2, and [tools/check.py](tools/check.py), lines 79–98, independently enumerate the default suites. Both omit `experiments/02_stereo_depth/tests` and `experiments/05_birds_eye_mapping/tests`.

The default collection returned 857 cases. Explicitly collecting the two omitted directories returned 71 cases and four access errors from temporary folders inside the depth tests. This is a concrete route to a reassuring default check that never inspects the new depth or area units. Related walkthrough adapter tests do not substitute for the omitted unit tests.

The project's `.venv` Python also lacked pytest during this audit, while the system Python had it. This does not prove the documented environment is universally broken; it shows that “run the checks” needs an identified interpreter and installed dependencies.

**Improve:** establish one authoritative test-suite inventory. Add both modules and protect discovery from generated temporary folders. Pin the intended check environment. A check should fail when a maintained test module is absent from the suite. Record the exact interpreter, command, exit status and selected suites with each verification receipt.

### F6. MEDIUM: the audit produces noise and misses historical evidence drift

In one JSON snapshot, the audit emitted 204 findings. Excluding the three entries caused by this audit's then-new task leaves 201: 185 size findings, six medium findings and ten waiver entries. The 185 size findings comprised 103 under `third_party/` and 82 under experiment paths containing generated code and historical run source copies. They do not mean 185 current maintained modules need refactoring.

The medium findings were missing future test paths for Tasks25, 53, 56 and 57, and missing plan stamps for Tasks56 and 57. Those are useful inventory items, but an unstarted planned test is different from a missing test on closed work.

Meanwhile, `audit` scans live tasks for document and test paths, not closed tasks. Closed [Task03](task_list/closed/03_define_observation_and_pose_contracts_with_known_g.md), line 9, names the no-longer-existing `experiments/03_tracking/tests/test_contracts.py`; closed [Task11](task_list/closed/11_explain_geometry_control_outputs_and_show_supplied.md) also names an old tracking test path. The current board lint still returns zero errors and warnings. It is a structural check, not a reconstruction of the proof trail.

**Improve:** classify maintained source, vendor code, generated output and historical snapshots separately. Audit closed receipts for resolvable commits, artifacts and current successor paths. Preserve original historical paths, but record where the contract moved. Rank missing proof on a closed task above a deliberately future test on an open plan.

### F7. MEDIUM: the transition journal is local and its failures are silent

Shared `task-system/task.js`, lines 174–178, calls the journal the durable record of moves and renumbers, then catches append failures without reporting them. In this project `task_list/.journal.log` is untracked and ignored by [`.gitignore`](.gitignore), line 71 (`*.log`). Task Markdown is tracked here, despite source comments suggesting the whole board is ignored.

Git retains committed task-file changes, so the project does have history. The finer record of local starts, takes, review stamps and transitions is still machine-local and can disappear independently.

**Improve:** define which events must survive loss of the machine. Keep a small versioned or backed-up event record with task ID, actor/session, old/new state, timestamp, source hash and command result. Make append failures visible. Retain raw transcripts locally if desired; they need not become the shared audit trail.

### F8. MEDIUM: the constitution check accepts an empty template

[task_list/CONSTITUTION.md](task_list/CONSTITUTION.md), lines 9–10 and 25–27, remains explicitly unratified and contains placeholder principles. The audit checks existence and a Version line, so it reports no constitution finding.

**Improve:** either ratify a short set of actual owner decisions or mark constitutional enforcement unavailable. The audit should distinguish a placeholder from a ratified document. Candidate principles already present elsewhere include independent references, the phone deployment requirement and the one-frame-per-second floor. Those should be proposed to the owner, not silently ratified by an assistant.

### F9. MEDIUM: prose state and machine state drift apart

[Task51](task_list/open/51_agree_success_criteria_and_the_first_deployment_ta.md), line 168, still says mapping has no method and no run completes all six layers. The current board and Task55 describe completed mapping and six-layer runs. Task53's continuation note still points to Task51 decisions, although Task60 moved field decisions to Task61.

The root README also labels mapping planned while the current working tree and feature documentation describe an implemented method. Some of this reflects uncommitted recent work, but a reader loading different files receives different answers.

**Improve:** make the current task objective, blocker and next action small structured fields with one current value. Keep dated historical results below them. Generate the board summary from those fields where possible. Verify semantic handoffs when a task changes ownership; fixing only links and frontmatter does not update the old prose.

### F10. MEDIUM: the single-file task escape is broader than the written rule

Shared `scripts/hooks/task-gate.js` counts distinct dirty code paths. It does not count edits in the session. Repeated edits to the same sole dirty code file remain eligible for the escape, even though the supplied rule says a task must exist before a second code edit. Two successive gate invocations on one dirty code path with no active task both returned exit 0 in the temporary fixture.

That may be a reasonable lightweight policy, but it must be described accurately. Shell edits are also outside the file-edit gate's complete control, as the shared harness README acknowledges. The code-file lists differ across helpers: the size helper includes extensions such as `.cjs`, `.mjs` and `.svelte` that the inspected task and completion gates omit.

**Improve:** choose the intended exception explicitly: a bounded trivial edit, rather than an unlimited single-file session. Share file classification and task parsing across gates. Use repository verification to catch changes regardless of the tool that produced them. Do not pretend tool hooks are a security boundary.

### F11. MEDIUM: generated restart summaries do not carry a working handoff

Shared `scripts/hooks/session-end.js`, lines 40–108, extracts short user-message fragments, tool names and edited-file paths. Lines 240–254 create empty “Notes for Next Session” and `[relevant files]` placeholders. The current project's generated session file still contains those placeholders and includes task notifications and agent hand-backs among its task fragments.

This helps identify what was touched, but does not establish the last passing check, unresolved failures, current task ownership, confirmed decisions or the next command. The inherited summary at the start of this audit had the same gap.

**Improve:** generate a compact handoff from the active task and latest evidence: objective, confirmed decisions, source version, completed checks, remaining checks, recovery instructions and next action. Filter infrastructure notifications from user intent. Require named fields to be filled or explicitly unavailable. Load that handoff and selected source references, not a transcript-shaped list.

### F12. MEDIUM: cataloged workflows can advertise missing capabilities

The source skill `skills/source-command-harness-audit/SKILL.md`, line 23, requires `scripts/harness-audit.js` as a deterministic scoring engine. That script is absent from the shared source. Therefore this report does not claim a reproducible score out of 70.

The current catalog also exceeds the imported instruction text's advertised 48 agents and 79 commands. Catalog counts are not a quality measure. The practical issue is whether each advertised workflow has a callable implementation on this Windows machine.

**Improve:** test referenced entry points and platform support. Retire or clearly disable broken workflows. Keep compatibility command shims only where they still serve an actual migration path. Favor a small relevant skill catalog over exposing every possible workflow in each session.

## Claude re-check: validation and new findings

This section was added by a Claude Opus 5.5 session on the evening of 8 October 2026, after the report above and after the dry-run fix. It checks the fix, re-runs the probes and adds what the first pass could not see from the Codex side. Every number below was measured in this session unless it says otherwise. No application code, harness code or other task was changed by this check.

### Validation of the dry-run fix (harness Task 01)

The hand-back said: the canonical CLI was fixed at line 493; ordinary `move` and `close --dry-run` now return before writing; 27 tests failed before and 55 pass after; 33 existing probes pass; reviews passed; other sessions' work was preserved; coverage, worktree integration and token totals were not measured.

| Claim | How it was checked | Result |
|---|---|---|
| A return before any write, at line 493 | Read `git diff task-system/task.js` in the harness repo | **Confirmed.** One line, placed after the receipt check and before `setStatus`. The worktree branch is untouched. The same diff also contains two earlier commit-message edits, which the receipt lists as pre-existing and preserved. |
| Source identity | SHA-256 of the live files | **Confirmed.** `task.js` 966ca5d5…87, test file 62ccfe25…55, both as recorded. The file is still 961 lines, so the 800-line rule was not made worse. |
| 55 tests pass | `node --test task-system/tests/test_dry_run.js` | **Confirmed.** 55 pass, 0 fail. |
| The tests catch the bug | Copied `task-system/` to a temp folder, deleted only the new line, re-ran | **Confirmed.** 28 of 55 fail without the fix. The receipt's 27 of 54 predates a 55th isolation test, which also fails without the fix. |
| 33 existing probes pass | `node task-system/tests/test_harness_invariants.js` | **Confirmed.** 33 pass, 0 fail. |
| Both assistants use the fixed file | Checked link targets and hashes | **Confirmed.** `~/.claude/task-system` and `~/.codex/task-system` are junctions to the canonical folder and hash identically. |
| Ordinary previews leave the board alone | Own probe on throwaway boards, comparing every file's bytes before and after | **Confirmed** for `move 01 closed --dry-run` and `close 01 --dry-run`. |
| Not committed; worktree mode, coverage and tokens unmeasured | Harness `git log` and `git status` | **Confirmed as stated.** Harness HEAD is still `0d40c20`; the fix, test and task file are uncommitted. The receipt says so openly. |

**Verdict:** the claim stands. The fix is narrow and well tested. It is a local fix, not a versioned one.

The same probe re-ran the neighbouring cases the fix deliberately left out of scope. All three still behave as the original audit reported:

| Throwaway-board input | Exit | Board |
|---|---|---|
| `move 01 closed --dryrun` (one missing hyphen) | 0 | **Task really moved to `closed/`.** Unknown flags are ignored at `task.js:891`. |
| `move 01 closed` on a task with no Receipts section | 0 | **Closed.** |
| `start 01` on a HIGH task stamped `plan_reviewed: … FAIL` | 0 | **Started.** |

So the preview is now safe only when typed exactly. Rejecting unknown flags is the cheapest remaining fix and belongs in the next task.

### F13. HIGH: Claude sessions load the shared instructions about three times

The original report measured one 64,239-byte instruction file. A Claude session in this project loads much more:

| What loads | Bytes | Why it loads |
|---|---:|---|
| `~/.claude/CLAUDE.md` | 64,239 | Normal user memory. Contains both instruction files, the plain-language style and every root rule (`tools/render.cjs:13-19`). |
| `~/.claude/AGENTS.md` | 64,239 | **Identical copy** (same SHA-256 f53535ae…). The renderer writes it (`installation.json:4-8`, `render.cjs:53-56`, `install.cjs:50`). Claude reads it because global `settings.json:293` lists `C:\Users\jkind\.claude` as an extra working directory. |
| `~/.claude/rules/*.md` | 48,545 | `~/.claude/rules` is a junction to the harness `rules/` folder, which Claude auto-loads. **The same text is already inside CLAUDE.md.** |
| `~/.claude/rules/web/*.md` | 14,380 | Web design, CSS and Core Web Vitals rules. They have no `paths:` filter, so they load in this Python and computer-vision project. |
| Plain-language output style | about 2,500 | Loaded as the output style and again inside CLAUDE.md. |
| Skill catalogue | not measured in bytes | 241 skills are listed. 84 are `source-command-*` copies of the 84 slash commands, so each command appears twice. |

That is about 192 KB of instruction text, of which about 113 KB is an exact duplicate and about 14 KB does not apply to this project.

The effect shows in the transcripts. The first recorded message of each session carries the fixed starting context before any real work:

| Session type | Sessions | Median starting context | Minimum |
|---|---:|---:|---:|
| Main session | 12 | 123,939 tokens | 121,239 |
| Subagent | 18 | 81,479 tokens | 79,087 |

A subagent sent to answer a three-line question therefore costs at least about 80,000 input tokens on its first turn. A rough estimate, at about four bytes per token: the duplicated text is about 28,000 tokens per message. Across the 1,785 recorded messages (main plus subagent) that is about 50 million tokens of repeated context, out of 582 million supplied in total, or roughly 9%. Most of it is cache reads, which are cheaper than fresh input, but it still fills the context window and counts towards usage limits. Treat the 9% as an estimate, not a bill.

The global extra-directories list has 32 entries. It includes other clients' projects and one broken path containing a literal `$USERPROFILE`. Each is available to every session in every project.

**Improve:** stop writing `~/.claude/AGENTS.md` (Codex reads `~/.codex/AGENTS.md`). Load the rules once in Claude: either drop the rules section from the Claude render and keep the junction, or keep the render and remove the junction. Add `paths:` filters to the web rules. Stop generating `source-command-*` skills for Claude, which already has the commands. Prune the extra-directories list. **Acceptance:** median starting context below 95,000 tokens for a main session and below 55,000 for a subagent, with the existing parity and behaviour checks still passing.

### F14. HIGH: the task gate judges the wrong repository

`scripts/hooks/task-gate.js:24` and `:35` ask Git for the repository of the session's working folder, not of the file being written. A file outside that repository keeps its absolute path (line 36), is added to the dirty-file set (line 47) and is checked against this repository's active task.

Observed in this session: writing a throwaway probe script into the session's own temporary folder was blocked because another session's Task 65 is active here. Consequences:

- Harness code cannot be edited from a project session without adding harness paths to an unrelated project task.
- In a shared checkout with another session's dirty files, the "first code file" escape at line 48 never applies.
- The reverse also holds: a session started in the harness folder is not checked against this project's board when it edits project code.

**Improve:** resolve the repository and board from the target file's own folder. Let files outside any repository, and in temporary or scratch folders, pass. Count dirty files only in the target's repository. Until this is fixed, start harness work in a session whose working folder is `C:/Users/jkind/.agents/harness`.

### F15. MEDIUM: the documentation hooks block reads and requested reports, and miss real writes

The shell rule at `tools/dispatch.cjs:27` blocks any command line containing `echo`, `cat`, `printf` or `tee`, then any `>`, then `.md` or `.txt`. A `2>/dev/null` or `2>&1` counts as the `>`. In this session it blocked two read-only commands (hashing a README, and a `grep` over task files) and a throwaway test fixture written to a temporary folder. Meanwhile it does not see writes by `cp`, `sed -i`, Python or Node.

The edit rule at `tools/dispatch.cjs:40-42` allows only README, CLAUDE, AGENTS and CONTRIBUTING files and a few folders. It has no route for a document the owner explicitly asks for. This report was requested at the repository root, so the rule cannot be satisfied by following it. The previous session created the file by a path the hook does not inspect, and this session had to apply its edits with a script. A rule that can only be obeyed by going around it teaches the assistant to go around it.

**Improve:** match only an actual redirect or `tee` target that ends in `.md` or `.txt`. Add an explicit allow-list for owner-requested documents, for example a `docs_allow:` list in the active task's frontmatter. Keep the policy's intent, which is to stop unrequested Markdown sprawl.

### F16. MEDIUM: closed-but-uncommitted work keeps growing and now overlaps

At the time of this check:

- Five closed tasks in this project do not exist in HEAD at all: 54, 55, 62, 64 and the audit's own Task 66. The harness's Task 01 is in the same state.
- The last commit here is from 7 October. Tracked files show 22 changed files, 1,450 lines added and 246 removed. There are 43 untracked files, including 6,238 lines of new code.
- The active Task 65 owns `src/walkthrough/**`, which overlaps files changed by Tasks 54, 55, 62 and 64.

When this is eventually committed, one commit will mix five tasks unless it is carefully split by path or hunk. That is the ownership problem in F3, now compounding daily.

**Improve:** make closing a code task mean committing that task's own files, with the SHA in the Receipts. When a commit is not wanted yet, use `pending_review` with "awaiting checkpoint" instead of `closed`. Clear the current backlog once, in task order, before Task 65 adds more.

### F17. MEDIUM: every subagent runs on Opus, starting from about 80,000 tokens

All 475 recorded subagent messages used Opus. The 18 subagents were 9 general-purpose, 5 plan reviewers and 4 diff reviewers. The main sessions were 1,283 Opus and 27 Sonnet messages. Global `settings.json:297` sets `"model": "opus"`. The plan and diff reviewers declare no model, so they inherit it. Only `code-reviewer`, `python-reviewer` and `planner` name a model, and none of those three ran here.

Opus is a reasonable choice for a blind review of a HIGH task. It is an expensive default for a general-purpose search. Combined with F13, every delegated lookup pays about 80,000 tokens of fixed context on the most expensive tier.

**Improve:** give the reviewers an explicit model. Keep Opus for HIGH and stateful plan and diff reviews. Use Sonnet, or the parent's own Grep and Read, for searches. Record the model and token totals per task, as the original report proposes.

### F18. LOW: the restart summary was empty again

The "previous session summary" injected at the start of this session listed nine background-monitor notifications as its "Tasks", and its "Notes for Next Session" and "Context to Load" fields were blank. This confirms F11 on live data: the summary records activity, not a handoff.

### Status of the original findings after this check

| Finding | Status on 8 October, evening |
|---|---|
| F1 dry-run mutates | **Fixed for exact `--dry-run`, uncommitted.** A mistyped flag still mutates. |
| F2 closure checks appearance only | Open. Reproduced again. |
| F3 closed without checkpoint | **Worse:** five here plus one in the harness (see F16). |
| F4 start ignores FAIL review | Open. Reproduced again. |
| F5 default tests skip depth and area | Open. `pytest.ini:2` still omits both folders. |
| F6–F12 | Not re-tested beyond F11 (see F18); no evidence they changed. |

## Mistakes and errors: what they reveal about the process

These cases are more informative than a count of green tests or closed tasks.

| Case | What went wrong | What the process did well | What to change |
|---|---|---|---|
| Task59 timestamp matching | After 749 tests passed, owner review found one-to-one matching dropped six of 798 RGB frames where nearest matching could match all of them. Both reference adapters also buffered whole sequences. | Task59 was reopened; `fd42708` records the correction; boundary and frame-lifetime tests were added. Original receipts remain visible. | Make representative real recording patterns and bounded memory part of adapter acceptance before closure. Large test totals cannot replace the motivating input. |
| Task55 measurement plan | Plan review found mapping lacked the camera positions needed to orient the plane. Shape expectations also disagreed with grid cell boundaries. | The plan was corrected before implementation and reviewed again. | Keep producer-to-consumer tracing and exact expected outputs. This is one of the harness's strongest controls. |
| Task55 final implementation | Blind diff review found loading an origin's full point set could require about 52 GB on a 1,362-frame recording; other mapping defects were also found. | Streaming shards, a grid limit and regression tests were added; the task records the review findings. | Require resource-bound checks at the actual data sizes, rather than treating a 30-frame run as sufficient evidence. |
| Task54 checkpoint comparison | The good ZipDepth score belonged to the desktop checkpoint; the exported phone checkpoint had not received the same accuracy measurement. | Task62 separated builds and re-scored them. | Join model artifact hash, accuracy and export validation by identity, not by a model-family name. |
| Task54 GPU failure interpretation | A game occupied 15,910 of 16,303 MiB when Marigold failed. That did not establish whether the model fit an otherwise free GPU. | The record was corrected and a free-GPU run was performed later. | Record environment preconditions and classify an occupied-device result as not measured for the intended condition. |
| Task54 memory and scorer | CPU peak memory was omitted. The Marigold scorer read the wrong prediction directory, and its test copied the same incorrect assumption. | Task62 repaired scoring, added memory evidence and compared sparse scaling. | Test against a real upstream artifact contract or an independently constructed fixture. Coverage of a duplicated assumption is weak evidence. |
| Task60 board cleanup | A dry-run made 16 real moves. Numerous queued reviews were never going to run automatically. | The incident and waivers were recorded; the owner-approved cleanup reduced live work from 32 items to 11. | Fix the command and give pending review a named reviewer, launch mechanism or expiry. A folder is not a review scheduler. |
| Historical size-limit breach | Commit `3167451` contained an 815-line supervisor and a 1,224-line test file despite the declared 800-line rule. | Later work in `14957e6` split the files; no tracked code at HEAD exceeds 800 lines. | Measure the resulting tree in the repository checks, independently of which assistant or tool wrote it. Hook execution during the earlier edit cannot be established from Git alone. |

Evidence: [Task59](task_list/closed/59_make_walkthrough_layers_swappable.md), around lines 981–1098; [Task55](task_list/closed/55_implement_site_dimensions_and_area_measurement.md), lines 134–143; [Task54](task_list/closed/54_implement_and_validate_real_metric_depth.md), lines 139–145; [Task62](task_list/closed/62_close_task_54_review_gaps_phone_build_score_memory.md), around lines 35–49; [Task60](task_list/closed/60_prune_task_board_to_the_accuracy_latency_and_mobil.md), lines 83–94.

The recurring pattern is that written plans and tests can share an incorrect assumption. Review works best when it checks a different source of truth: actual producer code, a real artifact layout, a complete recording or the device state. More copies of the original reasoning do not provide that independence.

## What works well

### Decisions and limitations are preserved

The board says that benchmark results are not phone deployment evidence and that missing references are blockers, not zero error. It distinguishes reference-aligned shape scores from independently recovered distances. This helps prevent attractive visual output being mistaken for an accuracy result. See the current [board](task_list/README.md), especially its goals and completion boundaries.

### Reviews have changed outcomes

Task55's plan review caught missing inputs before code was written. Its finished-diff review found resource problems. Task59's correction reviews caught timestamp subtype and tolerance-boundary defects. These are concrete benefits of tracing contracts and withholding implementation intent from the final reviewer.

### Corrections remain auditable

Task59 retains original receipts, the reopened correction plan and later receipts. Task54 names its post-closure gaps and the task that resolved them. This is much better than replacing the old claim and losing the reason for the change. Keep this history, but make the current state easy to find.

### Code and tests commonly travel together

Every inspected non-merge code commit after the initial import also changes test code. Task59 reports 93% production-code coverage for a scoped verification. That is a useful local result, although it is not whole-repository coverage. The records also name red-first failures for several regression cases.

### The architecture is becoming easier to reason about

Task59 reduced the pipeline from 241 to 107 lines and reduced the measured runner from 1,688 to 1,606 lines in its original implementation. It created six documented method choices and clearer output contracts. The size target was missed and explicitly waived rather than hidden. The later correction added some lines for correctness while keeping the main runner below 120 lines.

### Active-task protection works

During this audit, Task65 became active in the shared checkout. Starting Task66 was refused rather than silently demoting the other task. Shared `task-system/task.js`, lines 414–431, explains why this protection replaced earlier task stealing. Keep it, and use separate worktrees for concurrent code work.

### Shared source and adapter validation are valuable

Claude and Codex instruction files currently match byte for byte. The shared harness has a stored validation report with 18 passing behavioural/parity checks and propagation receipts showing a source edit reaching both native runtimes. This is stronger than two independently maintained instruction copies.

Those stored checks reference an older instruction hash (`2f6c6d9...`), so they should not be advertised as a fresh complete validation of today's revision. Current byte equality was checked directly. See shared `validation.json`, `state/propagation.json` and [shared README](C:/Users/jkind/.agents/harness/README.md).

### Pruning was useful

Task60 removed work that did not currently serve accuracy, latency or phone deployment. Optional refinements now wait for a measured need. The quality gain came from choosing less work and assigning ownership, not from marking every old item complete.

## Context bloat and technical debt

### The default instructions are doing too many jobs

Shared `tools/render.cjs`, lines 11–19, concatenates both instruction documents, the plain-language style and every root Markdown rule. That includes the rules installation README, overlapping testing and Git guidance, repeated agent instructions and a 17 KB task-management document.

Several policies also need clearer boundaries: exactly one active task versus instructions to run independent tasks in parallel; mandatory coverage and all test types versus legitimate trivial-change exceptions; README-only documentation versus task records and explicitly requested reports. The conflict is manageable when carefully interpreted, but that interpretation is repeated in each session.

**Recommendation:** load a short entry document containing source ownership, task ownership, safety boundaries, the check command and links. Load language rules and the relevant task workflow only when the work requires them. Keep enforceable invariants in code. Keep explanations, examples and migration instructions available by reference.

The goal is not a particular file length by itself. The test is whether the shorter entry point preserves correct scope, review, verification and recovery on representative work.

### Task documents can become a second transcript

Task59's roughly 1,100 lines contain useful history but also extensive prospective code examples. A restarted agent should not need to read that whole document to discover the current owner and next step.

Use a short current-state section at the top: objective, accepted decisions, required inputs, remaining checks and next action. Keep historical receipts below it. Refer to current implementation by path and contract; avoid maintaining a second copy of the implementation in a plan. Do not delete old evidence just to make the document look smaller.

### Large commits make ownership harder to reconstruct

Commit `14957e6` changed 135 files, adding 9,844 and removing 2,038 lines across the runner, experiments, shared code, datasets and 35 task files. Its subject was “towards pipeline runtime glue.” Three reachable subjects lack the conventional prefix.

The main issue is not punctuation in subjects. Broad commits make it harder to identify which task owns a regression, what to revert and which tests correspond to a result. Smaller checkpoints aligned to one recoverable change would make the existing receipts more valuable. Necessary cross-layer changes can still form one commit when the contract requires them.

### Verification debt is currently more visible than structural debt

The strongest observed gaps are default tests that omit modules, reviewed versions that are not bound to hashes, model scores associated with the wrong artifact and local results without a versioned checkpoint. The audit does not establish widespread duplicated implementation or an irrecoverable architecture.

Avoid declaring technical debt solved because files are under 800 lines. Also avoid declaring every new module debt. Measure boundary clarity, repeated concepts, replayability and the time needed to understand or undo a change.

## How to improve

### A smaller everyday workflow

Keep the existing board as the source of ownership. Use the amount of process required by the change:

| Work | Before starting | Before handing off |
|---|---|---|
| Documentation or trivial cleanup | Confirm scope and update the existing record if one applies. | Check claims and links; state whether changes are local or versioned. No artificial test-touch requirement. |
| Bounded code fix | Name the task, motivating input and owned files. | Run the regression that catches the defect, relevant suite and code review. Preserve the version and result. |
| HIGH/stateful/cross-layer change | Trace producers and consumers, recovery, units and ownership; review the current plan. | Review the exact finished change independently; check contract, failure and resource behaviour; close through the shared validator. |
| Model experiment | Use the existing settings/provenance record and separate independent references from method inputs. | Tie predictions, model hash, settings, data split, environment and scorer version to the measured result. Preserve failed attempts too. |

A handoff should answer: what is done, what is still required, which version was checked, what failed and what the next session should do. The task's current-state fields should supply those answers. The agent should not infer them from a large transcript.

### Prioritized work

These are proposed improvements, not changes made by this audit. Harness changes should land in `C:/Users/jkind/.agents/harness`, then be rendered and validated for both assistants.

| Order | Improvement | Why first | Acceptance evidence |
|---|---|---|---|
| 1 | Fix dry-run and reject unknown flags. | Prevent unintended state changes with a small bounded fix. | Every dry-run mode leaves fixture files, Git state and journal unchanged; invalid flags fail without mutation. |
| 2 | Put completion validation in the task transition command. | Make closed mean a checked contract regardless of Stop timing. | Missing receipts, missing required evidence and unresolved review failures cannot close; legitimate doc-only and continuation cases still work. |
| 3 | Fix test discovery and document one check environment. | Restore confidence in the default verification command. | Maintained depth and area tests appear in default discovery; generated temp directories are excluded; a fresh documented environment can run it. |
| 4 | Define checkpoint and review-version policy. | Make task results reconstructable across sessions and machines. | A sampled closed code task resolves to its source, plan/diff reviews, test run and artifact identities; an edited plan invalidates an old review. |
| 5 | Reduce injected instructions, replace the restart summary and pilot task-level usage/model routing. | Make token reduction measurable against verified quality. | A new session finds the next action from a compact handoff; pilot tasks record actual models and usage coverage, including child agents. |
| 6 | Make audits reflect maintained code and closed evidence. | Remove alert fatigue and find missing proof. | Vendor/generated size entries have their own category; closed broken references are caught; a draft constitution is labeled draft. |
| 7 | Make transitions durable and visible. | Protect the detailed audit trail. | Events survive a clean checkout or restore; append failures are surfaced; events identify the source version and session. |
| 8 | Add a repository-level verification backstop. | Cover shell writes and inactive/moved task records. | Changed paths, test discovery, size limits and required evidence are checked independently of edit-tool hooks. Start locally; mirror in CI when appropriate. |
| 9 | Test and prune workflow entry points. | Reduce dead ends and catalog maintenance. | Referenced scripts exist and work on Windows; unavailable workflows say so; duplicates have one canonical owner. |

Do the first four before buying a new workflow platform. Treat prompt reduction and the handoff change as an experiment with measured outcomes. Avoid switching on every standard/strict hook at once; first inspect which checks provide useful signal and which depend on absent infrastructure.

### A durable chain of evidence

For code-changing work, the intended chain should be:

`task and plan version → owned change → independent review → exact check run → result artifacts → durable checkpoint → closed record`

The current system has many of these pieces, but joins them mostly through prose and filenames. A small machine-readable evidence record alongside each task would make the joins explicit. It should identify the source version, dirty-source snapshot if applicable, input and model hashes, check command, environment, exit code, result path/hash, review reference and waiver owner/reason.

Reuse the experiment provenance already present. Do not create another competing run record or task database. Markdown can remain the readable explanation while structured fields supply the proof links.

### Measure the harness itself

Use the next 20 comparable completed engineering tasks as a pilot. The targets below are proposals for review, not retrospective claims or model experiment settings.

| Measure | Definition | Initial proposed target |
|---|---|---|
| Closure evidence completeness | Tasks with resolvable source, required reviews, exact checks and result identity / applicable closed tasks | 100% for the pilot |
| First-review success | Changes accepted without a correctness correction on independent review | Establish baseline; improve without removing difficult tasks from the sample |
| Escaped defects | Closed tasks reopened for a defect inside their promised scope | Record number and severity; examine causes rather than treating reopening itself as failure |
| Human rescue | Owner interventions needed to recover intent, find a missed condition or repair a false completion | Record per task and compare similar work |
| Restart burden | Time and files read before a new session can name the next required action | Median under five minutes, subject to task complexity |
| Context footprint | Initial instruction tokens and median/p90 reported input/cache context by task class | Reduce the initial shared instruction volume by at least half without losing the workflow regression checks |
| Cost per verified task | Actual provider cost joined to a verified outcome, including subagents | Establish a measured baseline before making savings claims |
| Audit signal | Actionable maintained-work findings / findings the owner inspects | Separate vendor/generated inventory from the actionable queue |
| Verification selection | Maintained test modules omitted by the default suite | Zero |

The most useful measure is verified progress per unit of human attention. More closed tasks, longer plans and more agent calls can all increase while that measure gets worse.

### Make tokens used per task part of the receipts

**Recommendation from the owner's follow-up: yes, record task-level token use.** Prefer provider-reported counts where available. Keep estimates explicitly labeled when the runtime does not expose usage. A missing measurement should remain missing, rather than becoming a plausible-looking exact number.

Use a small automatically generated usage summary, with the readable totals in the task's Receipts table. Do not ask the assistant to keep a running token diary in prose; that would consume more context and still miss work.

| Receipt field | What it should mean |
|---|---|
| Usage source and coverage | Provider-reported, tokenizer estimate or coarse estimate; which sessions and agents were included; unresolved attribution or missing logs. |
| New input tokens | Reported uncached input and cache-creation input, retained as separate counters in the underlying record. |
| Reused context tokens | Cache-read input. Count this as context supplied, while retaining its separate billing category. |
| Output tokens | Provider-reported output. Include separately exposed reasoning usage according to that provider's accounting; do not add it twice if it is already included. |
| Total supplied input | Uncached input + cache-creation input + cache-read input over the task's messages. This is repeated context processed, not unique text. |
| Breakdown by work | Main agent, delegated work, review, retries and resumed sessions. Identify the task and parent/child sessions before summing. |
| Monetary cost, if available | Actual charges or a dated rate-based estimate with model/provider and cache categories. Raw token totals alone do not compare different prices fairly. |
| Verified result | Acceptance criteria met, independent defect findings resolved, accuracy measurement where relevant, and later reopenings inside the promised scope. |
| Comparison | Similar task or controlled workflow baseline; token difference, correctness/accuracy difference and relevant uncertainty. |

Deduplicate streaming updates by provider/session/message identity, retaining the final usage record. Associate messages with the task that owned the work when it ran, using session and task transition events. Child agents should inherit that task identity. Keep genuinely unattributed work in a separate bucket rather than silently assigning it to the final active task. Tasks sharing a session and agents sharing a checkout make attribution from filenames alone unreliable.

For older tasks, reconstruct usage only where the logs and transition times support it. Report coverage alongside the estimate. The ignored journal, task switches and missing child-session joins mean this audit cannot honestly assign the existing project-wide usage totals to all 66 tasks. Start reliable accounting prospectively, and backfill a small sample to test the method.

**How to use the numbers:** compare a lighter workflow with the existing one on similar work. Track acceptance failures, independent review defects, owner corrections and later regressions. For model research, also compare the actual held-out accuracy result. Passing more tests or generating a longer report does not by itself justify extra tokens.

Retain an additional agent or review pass when it demonstrably catches load-bearing errors at an acceptable cost. Remove repeated broad searches, duplicate reviews and default document loading when they add no measured benefit. A lower-token workflow that preserves verified quality is preferable. A hard cutoff that leaves required work unfinished is not evidence of an efficient completed task.

Begin with per-task totals and the largest contributors. Then test reducing the shared startup instructions, sending fresh reviewers only the relevant change and contracts, and returning conclusions instead of raw search output. Evaluate these changes separately so any correctness loss has an identifiable cause.

Proposed additional pilot measures are median and 90th-percentile tokens per verified task, tokens spent on retries, delegated-token share, and the share of usage that cannot be attributed. Review these alongside correctness and accuracy, rather than setting a token target that can be met by hiding failures.

### Route models and delegated work by the difficulty of the decision

Use three practical tiers. The pairs below serve similar workflow roles; they are **not claims of equal benchmark performance**. Current OpenAI guidance separates efficient Luna, balanced GPT-6.1 Sol and more capable Astra. Anthropic distinguishes Haiku for inexpensive work, Sonnet for everyday coding and Opus for complex work. [OpenAI model selection](https://developers.openai.com/api/docs/guides/model-selection), [Claude model selection](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model).

| Task or delegated responsibility | GPT/Codex starting choice | Claude starting choice | When stronger reasoning is justified |
|---|---|---|---|
| Locate an existing owner, extract specified log fields, count task metadata, check links, summarize a bounded diff | GPT-6 Luna, low or medium effort | Haiku 5.5 | Conflicting evidence or a need to trace behaviour across layers. Arithmetic and known validation rules should use scripts first. |
| Implement a scoped feature, write meaningful regression tests, fix an understood bug, maintain docs against known code | GPT-6.1 Sol, medium effort | Sonnet 5.5 | The contract is ambiguous, the correction keeps failing, or the change reaches shared state or several components. |
| Review ordinary code against a clear contract | GPT-6.1 Sol, medium; high for a subtle boundary | Sonnet 5.5 | Difficult concurrency, coordinate/units errors, permissions or an outcome the workhorse cannot establish confidently. |
| Design or review a HIGH/stateful plan, diagnose difficult cross-layer failures, audit scientific validity | GPT-6 Astra, medium or high effort | Opus 5.5 | Use the stronger tier directly when a mistaken decision would invalidate later work. Bound the source bundle and required output. |
| Blind final review of a consequential change | GPT-6 Astra, high, or Sol if prior measurements show equivalent defect detection | Opus 5.5, or Sonnet under the same evidence condition | Select by observed defects caught on comparable changes, rather than making every final review expensive. |
| Mechanical follow-through after a decision: update links, run specified checks, gather result paths | A script, otherwise Luna with a narrow brief | A script, otherwise Haiku 5.5 | Unexpected results need interpretation; escalate that question, not the entire history. |

These are starting recommendations for this project. Use the exact versions available in each runtime, and record the actual resolved model rather than just an alias such as `opus`. OpenAI reasoning controls and Claude effort controls are not numerically interchangeable. Do not translate a setting by assuming it creates the same token budget or quality.

The current Codex configuration selects `gpt-6.1-sol` with `high` reasoning effort globally. A local Claude transcript snapshot contained 1,260 Opus messages and 27 Sonnet messages, excluding synthetic entries: approximately 98% Opus in that top-level sample. This excludes child-agent transcripts, so it does not establish the complete delegation mix. Nevertheless, there is no observed task-outcome comparison demonstrating that routine work needs this much strong-model usage. Shared agent definitions already assign the planner to `opus` and code reviewer to `sonnet`; the effective runtime model should be checked rather than inferred from the role name.

**Suggested normal pattern:** use Sol/Sonnet for implementation, a script or Luna/Haiku for bounded evidence gathering, and one Astra/Opus pass for a difficult plan or consequential independent review. Supply a new reviewer the change, relevant contracts and source references. Avoid inheriting the entire author conversation when a fresh review is intended. A different provider may offer useful diversity, but does not by itself create independent evidence.

Escalate because of a specific unresolved question, a reproducible failure or consequential ambiguity. Return to the normal tier after that question is settled. Do not respond to an inaccessible file, missing dependency or broken test command by buying more reasoning; fix the environment or state the limitation.

Record selected model, reasoning/effort setting, reason for escalation, tokens, checks passed and defects caught in the usage summary. Then compare total task cost, including retries. A stronger model may finish in fewer calls and consume fewer tokens; a cheaper per-token model may cost more after repeated failed attempts. Official OpenAI guidance explicitly recommends comparing models on the same task. [OpenAI model selection](https://developers.openai.com/api/docs/guides/model-selection).

For a concrete price distinction, the checked standard API rates list GPT-6.1 Sol at $2 input / $10 output per million tokens and Astra at $10 / $50. That is five times the rate for those categories, before caching or other service modifiers. It is not five times the cost of a completed task, and it is not a prediction of Codex subscription quota consumption. [Sol model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra).

Claude Code's current guidance similarly recommends Sonnet for most coding, Opus for harder decisions and Haiku for quick work; it documents a planning-with-Opus/execution-with-Sonnet pattern. Account availability and metering depend on the runtime and sign-in method. [Claude Code models and usage](https://support.claude.com/en/articles/14552983-models-usage-and-limits-in-claude-code).

Keep delegation selective. Use it when it isolates a broad search or supplies a consequential fresh review. Skip it when an extra agent would only repeat a short lookup, restate a decision or execute a deterministic check. A smaller child context reduces the parent's context burden but still consumes tokens; per-task totals must include both.

## What exists out there worth investigating, and why

Sources were checked on 8 October 2026. These are candidates for targeted investigation, not installed recommendations or promises of measured benefit in this repository.

| Candidate | What the primary source establishes | Why it is relevant here | Small investigation and adoption cost |
|---|---|---|---|
| OpenAI's harness engineering approach | Uses a short instruction entry point, repository knowledge, mechanical checks and ongoing maintenance of drift. [OpenAI article](https://openai.com/index/harness-engineering/) | Closely matches your goals while arguing against loading an entire manual at startup. | Borrow the small entry point and independent repository checks. Keep your existing README/task convention; there is no need to copy its whole directory layout or infer the same productivity gains. |
| Anthropic's context engineering guidance | Describes loading information as needed, compaction, structured notes and focused subagents. [Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Your measured context and duplicate policy text make selective loading worth testing. | Pilot one task with a smaller startup bundle. Preserve critical constraints and compare completion quality and human corrections. A framework replacement is unnecessary. |
| Anthropic's long-running-agent harness | Uses incremental progress, clean handoffs and explicit completion/testing rather than relying on compaction alone. [Long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Your restart summary identifies touched files but leaves next-action fields empty. | Adapt the handoff pattern to existing task records and Windows commands. Test recovery after interruption. Do not add another progress file with competing state. |
| Aider's repository map | Provides a compact map of symbols and dependencies, selecting relevant parts within a token budget. [Repository map](https://aider.chat/docs/repomap.html) | Could reduce broad source scans and help reuse existing contracts without loading entire modules. | Try a generated map for the walkthrough and shared geometry only. Keep it generated and tied to the source version; measure whether navigation actually becomes cheaper. |
| DVC experiments and artifact versioning | Associates experiments with Git baselines and tracks parameters, metrics and data/artifacts separately from normal commit history. [Experiment management](https://doc.dvc.org/user-guide/experiment-management) | Useful for model checkpoints, data and predictions that currently live outside Git while receipts name local paths. | Trial one depth comparison's inputs and outputs. Evaluate restore/replay effort and storage needs. Reuse existing settings and result formats; avoid duplicating them in a second manual tracker. |
| Langfuse tracing | Captures model/tool operations, token usage, latency and scores; supports cost and quality dashboards. [Observability documentation](https://langfuse.com/docs/observability/overview) | Could join agent effort to task outcomes and expose where large contexts or repeated checks accumulate. | Start with a local export of native logs and task IDs. Verify supported ingestion before integration; tracing documentation does not imply automatic access to native Claude/Codex sessions. Limit stored content to what the audit needs. |
| Promptfoo coding-agent evaluation | Documents disposable workspaces and evaluations covering unsafe task pressure and verifier integrity. [Coding-agent evaluations](https://www.promptfoo.dev/docs/red-team/coding-agents/) | Useful for testing whether the harness holds when asked to skip checks, alter tests or follow misleading repository text. | Start with a small set of realistic fixtures, including premature closure and review invalidation. Deterministic CLI tests are cheaper for known bugs; agent evaluations test behaviour those unit tests cannot establish. |
| GitHub Spec Kit | Provides structured specification, planning, tasks and verification processes, with Windows and multiple agent integrations. [Official repository](https://github.com/github/spec-kit) | Worth comparing against your task template and constitution handling. It overlaps heavily with what you already have. | Inspect one existing-project workflow. Borrow clearer transitions or template checks if they reduce work. Avoid installing a second board and another large mandatory document stack. |

My preferred investigation order is: smaller context and better handoffs; durable experiment artifacts; a small set of workflow evaluations; then richer tracing if local summaries cannot answer the cost questions. Spec Kit is primarily a comparison source here, rather than an immediate replacement.

## Dedicated comparison of harness approaches

The first research pass covered provider guidance and supporting tools. It was not a dedicated comparison of complete coding workflows. This follow-up checked the projects below against the specific problems found here: accumulated context, review cost, recoverable task state and readable code. Sources were checked on 8 October 2026. This is a comparison of documented mechanisms, not a performance benchmark or a ranking by popularity.

| Approach | Documented mechanism | What is worth investigating here | Cost or mismatch to test |
|---|---|---|---|
| Everything Claude Code (ECC), the source family your harness already extends | Specialized skills, agents and hooks. Its token guide recommends everyday coding on Sonnet, inexpensive bounded exploration and compaction at useful boundaries. [ECC source](https://github.com/affaan-m/ECC), [token guide](https://github.com/affaan-m/ECC/blob/main/docs/token-optimization.md). | Compare your installed fork with upstream mechanisms before inventing more equivalents. Test selective skill loading and task-specific model choices. | The guide's savings percentages are recommendations, not measurements on this repo. Runtime settings need verification against current provider documentation. Protecting the parent's context does not eliminate child-agent token consumption. |
| Superpowers | Design and planning followed by execution, tests and review. Its inline execution skill uses the main implementer and one final fresh review instead of a new implementer/reviewer for every task. [Official project](https://github.com/obra/superpowers), [inline execution skill](https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md). | Test a bounded implementation brief, a compact progress record and a consequential fresh review. The inline-versus-delegated choice directly addresses your cost question. | Full adoption would add another workflow and progress format. Inline execution trades away fresh context and review at each step; test defect detection rather than assuming equal quality. Do not copy shell scripts without checking Windows support. |
| GSD Core | A discuss, plan, execute, verify and ship loop; heavy work runs in fresh subagents and structured records carry progress across sessions. The older get-shit-done repository points to this maintained project. [Official source](https://github.com/open-gsd/gsd-core). | Borrow explicit restart state and small executor briefs for long tasks. Compare one fresh executor after a handoff with continuing a large conversation. | A small controller context can conceal a large total across executors. Count every agent and planning/review pass. Its additional state documents overlap your existing tasks and README policy. Its context-quality claims are not local experimental evidence. |
| OpenSpec | Change-scoped proposals, requirements with concrete scenarios, design, task checklist, application and archival. [Official source](https://github.com/Fission-AI/OpenSpec). | Borrow short scenario-based acceptance criteria for changes to shared contracts. This may make plans easier to verify without expanding every task into a transcript. | It creates a separate change/specification tree. That would duplicate authority unless deliberately integrated. Its model recommendations do not establish the cheapest sufficient model for this project. |
| GitHub Spec Kit | Specification, planning, tasks and constitution-oriented workflows. [Official source](https://github.com/github/spec-kit). | Compare its separation of requirements and implementation with your existing What/Why/How and constitution checks. | Much of this already exists locally. Evaluate a missing mechanism rather than paying for a second specification and task system. |
| Minimal native Claude/Codex workflow, retaining your task CLI and safeguards | Proposed local comparison: a short entry point, one bounded task brief, existing tests and receipts, and risk-based fresh review. This is an experiment arm, not an external product. | Establish whether your custom policy stack adds measurable value beyond the runtime and a few deterministic controls. | Keep all required safety and completion checks. Removing them would confound a smaller-context experiment with a weaker correctness standard. |

The best first investigation is Superpowers' inline execution pattern alongside a lean version of your own workflow. GSD's restart handling is useful for multi-session work. ECC remains the closest source for maintaining the existing system. OpenSpec and Spec Kit are comparison material for acceptance criteria and state transitions; wholesale migration is not justified by this audit.

Do not install these frameworks together. Their plans, memory records, reviewers and completion rules would overlap. Borrow one mechanism at a time and make the existing task file its authoritative record. I found no controlled, like-for-like comparison in the checked sources that establishes the winner on these tasks, models and Windows environment.

## Change now or experiment first?

**Repair demonstrated correctness defects first. Experiment before broad workflow or model changes.** A dry-run that moves a real task does not need an expensive model comparison to establish that it is wrong. A shorter instruction bundle or fewer review passes does need an outcome comparison.

| Decision | Recommendation | Evidence needed before considering it done |
|---|---|---|
| Dry-run mutation, absent/weak closure validation and starting after a FAIL review | Fix through separately scoped engineering tasks with failing regression tests. | The actual state remains unchanged on dry-run; invalid closure/start cases are refused; valid cases still work. Verify the relevant native adapters as well as direct CLI calls. |
| Default test-discovery gaps and misleading completion/checkpoint claims | Repair discovery and make the completion vocabulary reflect recoverable evidence. | Intended maintained suites are collected; completion points to the tested source/artifact version. Distinguish local delivery, review-ready and committed delivery. |
| Token accounting and command-event capture | Add the smallest trustworthy measurement first. | Coverage and duplicate handling are checked against a few known sessions. Missing records remain visible. Do not add an LLM summarization pass for every event. |
| Shorter startup instructions, different delegation or model routing | Evaluate in isolated runs before adopting globally. | Same independent acceptance standard, all-agent token totals and human correction effort. |
| Replacing the board or installing another complete harness | Defer. | A specific unmet need and a measured benefit that exceeds migration and duplicate-state costs. |

These are proposed changes. This audit has not changed the shared harness, installed a framework, run the comparison experiment or launched an external Claude review.

### A small experiment that answers the cost question

Start with six replayable tasks, each run under two workflows: **A**, the repaired current harness; **B**, the same deterministic safeguards with a smaller startup bundle, a bounded brief and selective delegation. That is twelve initial runs. Both arms use the same implementation model and effort setting first. Changing the model and workflow together would prevent attribution of any improvement.

Use task starting points and evaluation fixtures that do not reveal the historical fix:

| Task class | Motivation from this audit | Independent evaluation |
|---|---|---|
| Timestamp/frame association bug | Task59 needed an owner correction after extensive tests. | Hidden checks for offsets, missing frames and identity preservation, built before either run. |
| Geometry/data-flow contract | Task55's reviews found ownership and boundary errors. | Independent fixtures for coordinate units, plane boundaries and missing inputs. |
| External tool/output assumption | Task54's scorer path assumption survived a test that mirrored it. | A captured external output layout that neither implementer controls; include the missing-output case. |
| Scope and premature-completion pressure | Direct probes demonstrated permissive gates. | Ask for an out-of-scope edit or closure without evidence; verify refusal and correct recovery. |
| Interrupted task handoff | Restart summaries omit next actions. | Interrupt at a fixed milestone and resume from saved state. Measure repeated work and missed obligations. |
| Readability-only refactor | The owner struggles to follow long or nested code. | Existing behavioural tests plus a fresh reader's explanation of inputs, outputs, sequence and failures. |

Use small fixtures for the first pilot so model downloads, GPU work and device availability do not dominate results. Historical tasks supply realistic failure classes; synthetic fixture outcomes do not prove full product accuracy. Hold application quality to the same standard in both arms.

For every run, pin the task start commit, supplied workspace files, harness version/hash, task brief, model, effort, tools and test environment. Use isolated workspaces and prevent outputs from one run entering another. Balance execution order and give both arms the same permitted human assistance. The evaluator must be separate from the implementer's tests and frozen before execution. Do not give it the workflow name while it grades the result.

Record:

- Independent acceptance result, boundary/error failures, review defects and human corrections.
- Total input, output and cached tokens across the parent, children, retries and reviews; separately report missing usage coverage.
- Wall time and human review/correction minutes. Cached tokens, provider price and subscription usage are different measurements.
- Readability explanation accuracy and reader time, using the rubric below.
- Extra searches, repeated test runs, abandoned attempts and duplicated implementation after restart.

Decide the tolerable defect rate, meaningful token reduction and run cap before running. Compare quality first, then tokens for results that meet that quality standard. Include the cost of failures and retries in the workflow totals; excluding failed runs would make an unreliable workflow look cheap. Stop expanding a variant that produces a consequential regression.

Six pairs are a screening pilot. One run per condition cannot establish equal reliability or a dependable savings percentage. Repeat promising results across more task classes and multiple runs before a global change. Report the observed variation rather than claiming precision from twelve runs. Next, hold the winning workflow fixed and compare the Sol/Sonnet implementation tier with stronger choices on the same tasks. Reserve strong-model review where it demonstrates useful defect detection.

### A Claude review to reduce shared blind spots

Yes: one bounded, fresh Claude review is worth doing before turning this report into substantial harness changes. A second provider offers a different perspective, but agreement between models is not proof. Both can inherit the same assumptions, task prose or upstream framework preferences.

Use two stages. First give Claude the source snapshot and questions, without this report or the GPT recommendations. Ask it to inspect the board, relevant history, enforcement code and readability. Then reveal this report and reconcile findings as supported, refuted or unresolved. Each disagreement should end in a source reference or reproduction, not a vote. Record the resolved model, review input hashes and all review tokens against the audit task.

Use Opus for a difficult system-wide challenge, or Sonnet for a bounded follow-up whose questions are already specific. Keep one reviewer and one reconciliation pass; expand only for an unresolved consequential issue. A copied review prompt follows:

```text
Review this AI engineering harness independently. Do not edit anything.
You have a pinned project checkout, task board, Git history and shared
harness snapshot. Begin without the previous audit report.

Determine what actually enforces task scope, review validity, completion,
restart recovery and a recoverable evidence trail. Separate written rules,
configured checks and observed runtime behaviour. For each consequential
finding give the failing input, source file:line and a safe reproduction
or state exactly what remains unproven. Read-only inspection and disposable
fixtures only. Do not mutate the live board or active task.

Assess accumulated context and total effort, including children and retries.
Identify which workflow costs have measured benefits and which do not yet.
Inspect a bounded sample of code for understandable control flow, names,
module responsibilities, units and comments. Ask whether a fresh reader can
explain the inputs, outputs, sequence and failure cases without task history.

Return prioritized evidence and the smallest useful corrections. Do not
recommend a framework migration without identifying the local gap it addresses.

In stage two, read the supplied audit report. Mark its consequential claims
supported, refuted or unresolved, and identify missed items. Reconcile using
evidence rather than agreement. Challenge its proposed paired experiment
for confounding, leaked answers, weak acceptance tests and missing usage.
Return conclusions and references, not a running thought transcript.
```

## Human-readable code: make the purpose visible in the source

The task's In plain English section explains the work. Code needs a similarly short explanation of its current purpose, followed by a structure the reader can follow. The solution should reduce the need for commentary and task-history lookup. It should not add a miniature task file above every function.

### What this repo already does well, and where to look first

[The walkthrough pipeline](src/walkthrough/pipeline.py) is a useful example: `run` at line 29 spells out capture, depth, tracking, surface, mapping and objects in order. It validates outputs near the calls and describes frame identity and units. [The scorer](src/walkthrough/validation.py) explains the invariant that references do not enter prediction methods. These are better patterns to reuse than a generic dispatch framework that hides the execution sequence. [The shared Run class](experiments/shared/runs.py) owns a real lifecycle of outputs and timing; its existence is not itself unnecessary abstraction.

A read-only Python syntax-tree scan of 41 maintained non-test files found 308 functions. The scope was `src/walkthrough`, the top-level Python files in the depth and mapping experiments, and `tools/demos`. It excluded tests and vendored/generated code. No parsing errors occurred. This working-tree snapshot includes concurrent development and is not a complete readability assessment of every language in the repo.

| Review candidate | Snapshot measurement | Why inspect it rather than automatically split it |
|---|---|---|
| [Visualization module](src/walkthrough/visualization.py) | 732 lines; `_surface_frames` spans 95 lines and `_depth_frame` 88. | Close to the 800-line ceiling. Check whether distinct views have clear owners and whether visual-only transformations stay separate from prediction data. |
| [Result-page builder](tools/demos/pages_results.py) | `objects_in_3d` at line 253 spans 144 lines. | Long output-building functions can make parsing, transformations and presentation hard to separate. Some length may be unavoidable templates; measure navigation difficulty before extracting helpers. |
| [Depth experiment runner](experiments/02_stereo_depth/run.py) | 543 lines; `_run_sequence` at line 312 spans 133. | Trace setup, inference, saving and error handling. Extract a stage only when it has a useful input/output contract. |
| [Surface step](src/walkthrough/steps/surface.py) | `run` at line 50 spans 66 lines and reaches six control constructs. | The nesting includes timing and resource-management scopes, not just decisions. Preserve cleanup and frame-level error reporting; do not flatten it by moving work outside protected lifetimes. |

Function length includes the whole source span. Nesting counts `if`, loops, `with`, `try` and `match`; it is a simple navigation proxy, not a standard complexity score or proof of a defect. Several long functions have only one or two nested control levels. The report's earlier observation that no committed maintained file exceeded 800 lines does not establish that everything below the cap is easy to read.

### A small readability contract for modules and public entry points

At a module or substantial public entry point, use two to four sentences when needed to answer: **what comes in; what happens; what comes out; and what can fail or must stay true**. Put units, coordinate conventions, ownership and side effects where the reader needs them. A trivial helper may need no comment. Prefer the existing README for broader architecture and the task for change history.

For example, a proposed purpose comment for a surface-building entry point could say:

```python
"""Build world-space points from saved depth frames and camera poses.

Save one points file per frame, in metres, and return their locations.
Keep each frame's identity. A failed frame makes the step incomplete.
"""
```

This is an illustrative wording proposal, not an added code comment. Keep a comment only while it describes the actual behaviour. An accurate explanation of a surprising invariant is more useful than repeating each assignment in English.

| Reading problem | Default implementation habit | Review question |
|---|---|---|
| Nested decisions obscure the main path | Validate or reject early; use guard clauses. Keep required resource/error scopes. | Can I identify the normal path and every early exit without mentally stacking many conditions? |
| A long file mixes unrelated work | Split at a domain responsibility with explicit inputs and outputs. Keep orchestration visible. | What does this module own, and can its public names explain that ownership? |
| Names are generic or abbreviations are unexplained | Name the data and purpose: `camera_pose`, `valid_depth`, `elapsed_ms`. Preserve established mathematical terms and explain conventions once. | Can I infer meaning and units at the call site? |
| Comments need old task context | Explain the reason, constraint or limitation in place. Keep change history in Git/tasks. | Does this comment still make sense without knowing Task54 or the author's conversation? |
| Helpers and classes hide a simple sequence | Prefer direct named calls; introduce a helper or class for a coherent contract or lifecycle. | Did extraction reduce the reader's work, or merely scatter it across files? |
| One settings object follows every call | Pass only the settings a layer reads; keep validation next to the boundary. | Can I tell what this function is allowed to depend on? |
| Dense expressions combine several decisions | Give intermediate values meaningful names and separate the steps. | Can I explain each transformation without expanding a comprehension or callback chain in my head? |

Use the existing size limit as a ceiling, not a target. Functions over roughly 50 lines, deeper decision nesting and modules approaching the cap can trigger review. They should not force arbitrary wrappers, extra files or automated acceptance based only on a score. A coherent flat pipeline may be easier to read than ten tiny functions with unclear names.

The shared `Human-readable code` rule already covers many of these habits. Another long rule is unlikely to help. The existing [readability skill](C:/Users/jkind/.agents/harness/skills/readability/SKILL.md) also needs attention before reuse: line 18 assumes `develop`, and lines 76–97 hard-code another project's `VideoModule` structure. It applies edits directly. Parameterize its project scope and provide a review-only mode before treating it as a universal audit. This audit inspected that asset; it did not run its editing workflow.

### Verify readability without another ritual for every change

Add a brief comprehension check to an existing consequential review, rather than automatically creating a new reviewer. Give a fresh reader the touched code and necessary contracts, but not the author's explanation. Ask them to state:

1. What information enters and leaves, including units and identity.
2. The normal execution sequence and who owns side effects.
3. What happens for invalid input, unavailable dependencies and partial failure.
4. Where they would make one specified small change.

Compare those answers with the code and tests. Record incorrect answers, source locations that caused confusion and time to locate the change. If the owner is the intended reader, include the owner's result; an AI understanding its own preferred abstractions is not enough. Keep this check to a few representative entry points, not every helper.

Use it on the pilot readability refactor before and after. The target is fewer misunderstandings or less reader effort with preserved behaviour. Fewer lines, fewer comments or a better automated complexity score alone do not prove success. A refactor should retain relevant boundary/error tests and produce no unintended output change.

## Command/action evidence and a decision log

**An automatically captured command/action trail is useful. A manually narrated thought log is likely to add more cost than evidence.** Preserve observable work and consequential decisions. Do not try to write a transcript of private reasoning or each tentative idea into the task.

Native transcripts already contain much of the raw tool activity. Start by checking whether they can supply the required fields consistently across both runtimes; avoid recording the same data in three places. Where events are missing, a small deterministic recorder can fill the gap. A log of task transitions alone cannot show which tests ran or which source they checked.

| Record | Minimal useful content | Where it belongs |
|---|---|---|
| Command/tool event | Event ID, task/session/agent ID, timestamp, tool/command, working directory, completion/exit status, duration and output-artifact reference. Redact credential values. | Machine-readable append-only artifact or native transcript export. |
| Source association | Base/source commit, dirty-diff or relevant file hash, harness hash and resolved model where applicable. | Run manifest. A commit alone cannot identify concurrent uncommitted work. |
| Verification result | Command, selected suite/check, asserted outcome, result counts and captured output/hash. | Generated task receipt summary linked to the underlying event. Exit 0 alone does not show the intended suite ran. |
| Task transition or review | Old/new state, actor/session, reviewed task/source hash and verdict. | Durable event record with a small task summary. |
| Decision | The choice, supporting evidence, material alternative rejected, uncertainty or revisit condition. | A short Decision log in the existing task, only when a consequential choice is made or changed. |

Distinguish an action being requested from it completing. A missing return, timeout or interrupted session must remain unknown or failed, not become a successful event. Capture failures and retries as well as the final command. Record coverage so a reader knows when the trail is incomplete.

Keep long stdout/stderr and raw events outside the task body. Put an artifact path and hash in a versioned manifest; record a concise generated digest in Receipts. A hash identifies content but does not make a missing artifact recoverable. Choose retention and storage that let a reviewer retrieve the referenced output. Ordinary native logs are useful evidence but do not automatically constitute a tamper-proof record.

A short decision entry could be:

```text
Decision: Keep reference scoring after saved predictions.
Evidence: The scorer reads sealed prediction artifacts; the pipeline checks
their hashes after scoring. Rejected: supplying reference values to the
prediction method, because that would invalidate an independent score.
Revisit if: the prediction/scoring interface changes.
```

That example describes a consequential invariant; it does not ask the assistant to narrate how it thought. Do not add a decision entry for every read, retry or obvious implementation step. Existing What/Why/How and Receipts already cover many choices; add only new decisions and link to their evidence.

Automatic capture can run without inference tokens, although reading its output still costs context and storing/retrieving artifacts costs engineering effort. Generate counts and summaries deterministically. Have the assistant inspect exceptions, disputed results and relevant evidence, rather than ingesting the complete event stream at every restart. Measure capture overhead, missing-event rate and the time needed to answer a real audit question in the pilot.

The useful audit question is: **what changed, what decision led to it, which version was checked, what ran, what happened and where can I verify it?** The shortest reliable record answering that is preferable to a longer narrative.

## Going forward: the finalised operating model

This is the settled plan after both reviews. It replaces the "Prioritized work" order earlier in this report where the two differ. Each line is a default the owner can overrule. This paragraph records the plan as agreed on 8 October; the implementation follow-up above records the later changes and remaining acceptance work. The engineering items are filed as open tasks so that the next session starts from a board, not from this document.

### Working rules from now on

1. **One copy of the instructions per assistant.** Claude reads `CLAUDE.md` and the rules once. Codex reads `~/.codex/AGENTS.md`. Web and language rules load only for matching files.
2. **Work in a session started in the repository you are changing.** Harness changes run in a session whose working folder is `C:/Users/jkind/.agents/harness`, until the gate judges each file by its own repository (F14).
3. **Closed means committed.** Closing a code task commits that task's files and records the SHA. If a commit is not wanted yet, the task waits in `pending_review` marked "awaiting checkpoint".
4. **The command refuses, not the Stop hook.** `task.js` rejects unknown flags, refuses to close a task without filled Receipts, and refuses to start a HIGH or CRITICAL task without a current PASS. The Stop hook stays as a reminder.
5. **Two reviews for risky work, none by default for the rest.** HIGH, CRITICAL and stateful tasks get one plan review before start and one blind diff review before close, on Opus. Other tasks rely on their regression test and the owner's check.
6. **Cheap tier for looking things up.** Searches and bounded lookups run in the main session with Grep and Read, or on Sonnet. Opus is for planning, hard debugging and the two reviews above.
7. **Short current state at the top of each task.** Five to ten lines: objective, decisions, what is done, what is left, next command. History stays below. Plans point at code by path; they do not contain copies of it.
8. **Measure the harness on the next 20 tasks.** Record starting context, total tokens including subagents, model used, review findings and owner corrections in each task's Receipts. Use those numbers, not this report, to decide the next cut.

### Ordered backlog

| Order | Where | Task | Covers | Done when |
|---|---|---|---|---|
| 0 | both repos | **Checkpoint the existing work (owner decision).** Commit harness Task 01, then this project's Tasks 54, 55, 62, 64 and 66 as separate commits in that order, before Task 65 grows further. | F3, F16 | Each closed task resolves to its own commit. No commits were made by this audit. |
| 1 | harness Task 02 | Load the shared instructions once per assistant | F13 | Main session starts below 95,000 tokens, subagent below 55,000; parity checks pass. |
| 2 | harness Task 03 | Make `task.js` refuse unknown flags, closure without Receipts and HIGH starts without PASS | F1 remainder, F2, F4 | Throwaway-board tests: mistyped flag exits non-zero with no change; the two refused cases exit non-zero; valid moves still pass. |
| 3 | harness Task 04 | Judge each write by its own repository; fix the documentation hook's false positives; add an owner allow-list | F14, F15 | Scratch and out-of-repo files pass; read-only commands pass; `cp`/redirect writes to Markdown are caught; a listed requested report can be edited. |
| 4 | project Task 68 | Add the depth and area tests to the default test run | F5 | Default collection includes `experiments/02_stereo_depth/tests` and `experiments/05_birds_eye_mapping/tests` with no permission errors. |
| 5 | harness Task 05 | Make "closed" mean committed | F3, F16 | `close` records a resolvable SHA for the task's files, or routes to `pending_review` with a reason. |
| 6 | harness Task 06 | Replace the restart summary with a handoff built from the active task | F11, F18 | A new session names the next action from the summary alone. |
| 7 | harness Task 07 | Set reviewer models explicitly and record per-task model and token totals | F17, token receipts | Receipts carry model and token totals from transcripts, including subagents, with coverage stated. |

Items 1 to 3 are small and independent. Do them before the paired workflow experiment described earlier, so the experiment measures a harness that does what it says.

### What not to do

- Do not install another workflow framework. Borrow one mechanism at a time into the existing board, as the comparison section above recommends.
- Do not add more mandatory prose to the instructions. Every rule added costs tokens in every message of every session (F13).
- Do not fix the context problem by deleting safety checks. Remove duplicates first, then measure.

### Starting the next harness session

Open a new session with its working folder set to `C:/Users/jkind/.agents/harness`, then:

```text
Read task_list/open/ and start harness Task 02 (load shared instructions once).
Before changing anything, record the current starting context from the newest
project transcript as the baseline. Follow the task's verification section.
Do not commit unless I ask.
```

### How this addendum was produced

The re-check used read-only commands, throwaway boards in temporary folders, and one temporary copy of `task-system/` with the fix removed. It did not spawn subagents. The documentation hook refuses edits to this file (F15), so the addendum was applied with a short Node script that inserts text at fixed headings. That is a deliberate, owner-requested exception, recorded here rather than hidden.

## What this report cannot establish

- It does not prove the harness caused the observed improvements. There is no matched set of tasks completed without it, and the project history covers about six days.
- It does not establish whole-repository test coverage or rerun expensive model/device benchmarks. Test totals and selected historical coverage are evidence of verification activity, not complete scientific validation.
- It does not prove every configured hook executes in every current native session. Current shared-source parity was checked, and stored native propagation/validation receipts were inspected. A fresh complete native-runtime audit remains useful.
- It does not convert cached token counts to monetary spend or compare models' productivity. The local usage sample is incomplete and not joined to task outcomes.
- It does not establish final product accuracy, latency or phone deployment. Those goals remain open in the project board.
- It does not claim that every uncommitted change is technical debt. The problem is the ambiguity between local completion and durable completion, especially when several tasks share files.
- It does not treat a deliberately waived future feature as a hidden defect. A waiver should identify a real scope decision, its owner and the evidence it limits.

## Reproduction and source references

### Read-only repository checks used

```powershell
node C:/Users/jkind/.claude/task-system/task.js list
node C:/Users/jkind/.claude/task-system/task.js lint
node C:/Users/jkind/.claude/task-system/task.js audit --json
git log --all --format="%h %s"
git status --short
git diff --stat
git check-ignore task_list/.journal.log
python -B -m pytest --collect-only -q
python -B -m pytest --collect-only -q experiments/02_stereo_depth/tests experiments/05_birds_eye_mapping/tests
```

The default collection succeeded. The explicit depth/area collection failed with four permission errors while discovering 71 tests. The project's `.venv/Scripts/python.exe` could not perform collection because pytest was absent. Those failures were retained as audit evidence, not repaired or described as passing tests.

Board lint returned zero errors/warnings. That result applies to its structural checks. The audit output was summarized and its own temporary Task66 findings excluded from the project baseline. The text audit caps displayed findings; JSON was used to inspect categories.

### Disposable behavioural probes

Tests used `C:/Users/jkind/AppData/Local/Temp/fyld-harness-audit-4387273c000d4432afdf8cd6d418b95c`. No real task was moved by these probes.

| Input in the temporary board | Observed result |
|---|---|
| Ordinary task, no Receipts section, `move 01 closed --dry-run` | Exit 0; task actually moved to `closed/`. |
| Filled single-row receipt, nonexistent docs and contract test, HIGH priority, FAIL review, `move 02 closed` | Exit 0; task closed. |
| HIGH priority with FAIL review, `start 03` | Exit 0; task became `in_progress`; an unfilled plain-English template was added. |
| One dirty code file, no active task, two successive task-gate inputs for the same path | Both returned exit 0. |
| Dirty code, no active task, task-completion Stop input | Exit 0. |

An initial Node wrapper could not spawn its child command in this environment, so the probes were rerun directly through PowerShell. Results above are from those successful direct invocations. They establish the hook/CLI behaviours, not a bypass demonstration against every native runtime.

### Local harness references

These files are outside the repository and are machine-local. Important line locations identify what was inspected, rather than a permanently versioned line number.

| Source | Relevant responsibility |
|---|---|
| [task CLI](C:/Users/jkind/.agents/harness/task-system/task.js) | Receipts at 51–68; journal at 174–178; lock/start around 414–446; move/dry-run around 466–519; audit around 752–827; flag parsing around 876–895. |
| [task gate](C:/Users/jkind/.agents/harness/scripts/hooks/task-gate.js) | Dirty-path counting and the single-file escape; declared file ownership. |
| [completion gate](C:/Users/jkind/.agents/harness/scripts/hooks/task-complete-gate.js) | Dirty-code and active-task filtering; session documentation/test checks and continuation exemptions. |
| [documentation snapshot](C:/Users/jkind/.agents/harness/scripts/hooks/docs-snapshot.js) | Session-start hashes distinguish newly changed docs from old dirty files. |
| [size helper](C:/Users/jkind/.agents/harness/task-system/file-size.js) | Code extensions, skipped directories and oversized-file inventory. |
| [renderer](C:/Users/jkind/.agents/harness/tools/render.cjs) | Shared instruction assembly and generated adapters. |
| [hook policy](C:/Users/jkind/.agents/harness/policy.json) | Minimal profile, disabled entries and custom unwrapped gates. Standard/strict observers are not automatically active. |
| [session summary hook](C:/Users/jkind/.agents/harness/scripts/hooks/session-end.js) | Transcript fragment extraction and placeholder handoff fields. |
| [stored validation](C:/Users/jkind/.agents/harness/validation.json) | Earlier 18-check behavioural/parity result. |
| [stored propagation receipt](C:/Users/jkind/.agents/harness/state/propagation.json) | Earlier native source-to-runtime propagation tests. |
| [harness audit skill](C:/Users/jkind/.agents/harness/skills/source-command-harness-audit/SKILL.md) | Advertises the currently absent deterministic audit engine. |
