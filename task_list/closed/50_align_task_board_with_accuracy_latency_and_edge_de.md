---
id: "50"
title: Align task board with accuracy latency and edge deployment
status: closed
priority: MED
type: decision
approval_status: board restructuring authorised by the owner on 2026-10-06
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - task_list/**
  - README.md
  - experiments/README.md
  - experiments/06_object_recognition/README.md
  - experiments/06_object_recognition/experiments/02_segmentation/README.md
  - experiments/01_camera_capture_delivery/README.md
  - experiments/02_stereo_depth/README.md
  - experiments/05_birds_eye_mapping/README.md
  - experiments/evaluation/README.md
  - experiments/06_object_recognition/datasets/README.md
docs:
  - task_list/README.md
  - README.md
  - experiments/README.md
baseline_metric:
  source: task_list/README.md before this change
  field: missing executable goal milestones
  baseline_value: "0 scoped tasks for actual depth, site area, complete walkthrough benchmarking, or sustained edge deployment"
  target: "7 scoped plans covering success criteria, capture, references, depth, area, complete benchmarking and edge deployment"
created: 2026-10-06
last_updated: 2026-10-06
superseded_by: null
---

# Task50: Make the board serve the three project goals

## In plain English

Make the work plan lead to accurate measurements and object counts, an acceptable wait, and useful processing on the chosen device. Put the missing complete tests ahead of optional method refinements. Preserve earlier evidence and make unfinished work easy to distinguish from completed experiments.

## What

Rewrite the board around accuracy, latency and edge deployment. Add Tasks51-57 with explicit owners, outputs, prerequisites and verification. Promote Task13's frozen full-tracking baseline. Return unrun Task34 to open and hand completed Task49 to pending review. Align current README summaries without changing source code, experimental settings, historical receipts or the draft constitution.

## Why

The owner requested a targeted board after the 2026-10-06 review found untested final outputs and deferred edge work. Existing research plans do not acquire references or deploy the workload. Completing narrow experiments does not establish complete-system accuracy, timing or device operation.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| The intended outputs are measured geometry and distinct object counts | Root README | all task owners | README.md:3 |
| Depth has no implemented method | Experiment02 | surface and object stages | experiments/02_stereo_depth/README.md:7 |
| Site area has no code | Experiment05 | final site-size answer | experiments/05_birds_eye_mapping/README.md:7 |
| Reporting joins separate component trials | Task44 evaluation package | complete benchmark | experiments/evaluation/README.md:49 |
| The current timing comparison is component-only | Task49 | latency decisions | experiments/06_object_recognition/experiments/08_spatial_uncertainty_latency/README.md:3 |
| Edge work was deferred | Previous board | execution queue | task_list/README.md:121 before this change |

- [x] Create one concise queue and seven concrete missing-work plans.
- [x] Preserve all earlier task evidence and the dated review handoff below.
- [x] Correct task state, priority and current ownership summaries.
- [x] Align project/experiment READMEs and repair references to moved tasks.
- [x] Check task lint, next-task selection, local links and plan completeness.
- [x] Independently review the changed board and close this documentation task.

## Invariants and recovery

invariants n/a: documentation and task-state maintenance only; no runtime or deployed state changes. Task IDs and historical experiment receipts remain intact. The previous handoff is preserved below. Its snapshots predate this restructuring and must not be used as the current source set.

## Hyperparameters

hyperparameters n/a: no model, dataset, capture or experiment is run. Future settings and numerical product limits belong to Task51 and the reviewed execution plans.

## Verification

Contract check: task lint reports 0 errors, the next-task selector returns 51, every local task link resolves, and each new plan has scope, prerequisites, measurable completion and receipts. No pending-review task is described as a completed product test when that test has not run.

Before: 0 concrete depth/area/complete-benchmark/edge tasks, Task13 behind object refinements, and edge work explicitly deferred. Target: 7 concrete plans, Task13 early, and an early device check followed by a sustained device benchmark.

## Receipts

| Field | Value |
|---|---|
| Closing commit | No commit requested; documentation changes will remain in the working tree |
| Files changed | task_list/README.md; Tasks09/13/31/33/34/35/36/49/50-57; root and experiment README alignment; moved-task links. Source code, runtime settings and historical experiment receipts were not changed. |
| Test status | Task lint: 58 tasks, 0 errors/warnings. 165 local board/task/README links resolve. Dependency graph has 0 cycles. All seven new plans pass deterministic structure checks; Task51 review stamp is PASS, implementation plans52-57 await their exact settings and pre-start review. Changed-file whitespace check passes. |
| Before measurement | 0 scoped depth/area/complete-benchmark/edge tasks |
| After measurement | 7 concrete plans for criteria/capture/references/depth/area/complete benchmarking/edge; Task13 early; Task34 open and unrun; Task49 pending review; next task51 |
| Delta | 7 missing-work plans added; object refinements follow the complete baseline; early and sustained device checks have an owner |
| Decision-gate outcome | PASS: independent board_validation plan-reviewer on 2026-10-06. Corrected stale reference/validity-mask claims, historical queue wording and the Task55-to-56 physical-scoring handoff. Task51 ready for owner decisions; other outlines are not implementation approval. |

tests n/a: no source code changed; task/link/plan checks verify the documentation.
No experiment, device operation or source-code change was executed. The board update is complete; product acceptance choices remain the explicitly owned next Task51 step.

## Historical review handoff, recorded 5 October 2026

This is the earlier review record, preserved for traceability. It is not the current execution queue. All mentioned immutable snapshots predate the 6 October board changes; future review must use a new source snapshot.

Task40's earlier fixed snapshot review by Claude passed the protocol structure. Snapshot: `C:/Users/jkind/AppData/Local/Temp/fyld_goal_review_snapshot_20261005_b`, baseline `684468d01c1f32b98b531c2922bd409583716150`, manifest SHA-256 `86E41AC18C3F0432D1C1ADA0CC5C9B245D47845E1AD2F5A24B7A2B33CF55E5F4`, worktree patch SHA-256 `C6852B38E3F9F284D98941A1AA9A69560F0622B39D83DE15A73B3AB927411523`. The checked Task40 plan and dataset README matched the manifest hashes. Claude found four corrections: the development-session exclusion list omitted other desk users; the Task48 state sentence was stale; the depth hash citation omitted its check line; and each invariants row had an undeclared fifth evidence column. It also found that full 3D boundary scoring needs surveyed endpoint/corner coordinates, orientation and uncertainty. Four claims were UNPROVEN because ignored run artifacts or the review journal were absent from the snapshot. These findings were corrected. A fresh plan-reviewer agent returned PASS on the corrected plan and `task.js review 40 PASS` recorded it; this does not replace Claude's independent technical review. Task40 is pending review for a new pinned Claude check and owner decisions. Task41's research-only inventory has a filled receipt and is pending Claude source validation. Task37's official API/device-source matrix is complete and awaits its pinned Claude source check. No dataset was downloaded and no phone capture or performance test was run.

Snapshot `fyld_goal_review_snapshot_20261005_e` remains an immutable earlier snapshot at `C:/Users/jkind/AppData/Local/Temp/fyld_goal_review_snapshot_20261005_e`, baseline `684468d01c1f32b98b531c2922bd409583716150`, manifest SHA-256 `069FCADB67F9D8A4373ADAF491C0DFF254A9552AE6EC2A392D16A65118181A4F`, patch SHA-256 `7E98F19364C4859227749B88E8308EC95C0C68695D02CFC1B540C025089BB4D0`. It includes Task17/20/21/22/44/45 evidence and records missing Task45 run folders, Task48 scratch files/run, and Task44 source runs. It predates Task42's current feature inventory and the corrected Task37 device-list claim, so it is not the current review snapshot. Do not review it as the latest source set. A new immutable snapshot is required before Claude checks Tasks16, 21, 22, 32, 34, 37, 40, 41, 42, 44, 45, 47 and 48. Each applicable technical claim still needs PASS/FAIL/UNPROVEN; a recorded review is not owner approval.

The prior Claude handoff snapshots `fyld_goal_review_snapshot_20261005_f` through `_h` remain unchanged. Snapshot g used baseline `684468d01c1f32b98b531c2922bd409583716150`, manifest SHA-256 `af83d90137b06d7c9fef6901aed7522902e5becf3655070d1829ecadda455016`, and patch SHA-256 `3a0ffdcc9b0ba6773ba2df06aa2109efc3ef9142aa89e773d438fd464cae1f77`; it contained 8,618 files and all recorded hashes were rechecked. The existing Claude session `b26acd3f-d0ce-46e0-832e-1538bd5e9231` was given the technical handoffs. A separate fresh Claude session `8a2ced4c-4cdb-4985-ad2b-26322fc16c48` was given only the Task32 code diff and touched paths, without the implementation rationale. Its diff package is `C:/Users/jkind/AppData/Local/Temp/fyld_task32_adversarial_diff_20261005`, diff SHA-256 `0f4993a27fcc411f031e06fceded91700e9fca92cfafa1b2fe30c1ac7f6298b2`, manifest SHA-256 `ca4f5a6b83935829347feb5cd1b02e8d22724400505601f443f56be4f5526725`. At 21:49 London both CLI processes returned the session-limit message without review findings. Snapshot h included the corrected Task34 receipt but predates the external-input table. The current fixed snapshot is `C:/Users/jkind/AppData/Local/Temp/fyld_goal_review_snapshot_20261005_i`, baseline `684468d01c1f32b98b531c2922bd409583716150`, manifest SHA-256 `a47ce04354dc130a174c22d197f13aea5b8f18ecf2b22bd61c04265f57a0af2d`, patch SHA-256 `e31102176ef493be3d111688d7d2becec4966797a5b61b13a7f4cb1e90edc44d`; its 8,618 files (2,570,499,407 bytes) passed a full hash/size recheck. Its task-board copy predates this paragraph; no task source changed afterward. The user will prompt Claude after the reported 02:30 London reset, using Sonnet 5.5 high, and return the evidence. Codex must not start or resume Claude sessions. Use i unless a source or task file changes before the prompt. The separate Task32 diff package remains fixed. Task45 Part A/Part B source runs and Task44 child source runs are absent from snapshot i; related claims remain UNPROVEN unless exact artifacts are found.

Claude technical handoffs for Tasks16, 21, 22, 32, 34, 37, 38, 39, 40, 41, 42, 44, 45, 47 and 48 were attempted at 21:35 London time on 5 October against snapshot g. The CLI session limit ended both the technical review and fresh diff review before either returned findings. The owner will prompt Claude after the reported 02:30 reset. Task48's Claude-owned scratch scripts and results were recovered read-only. Codex reproduced all three measurements on the pinned Task22/Task46 inputs, excluded Task17's six-frame provisional labels from the 60-frame result, and published a verified run. The original computation folder is preserved as failed because its final file-count check also counted directories; the new publication run records this and verifies the copied inputs and output manifest. Task39's proposal is included for source checking, but owner acceptance remains outstanding. A PASS/FAIL/UNPROVEN is not owner approval. Task24 is held for a later review alongside mobile build work.

Task39's proposed review requirements are recorded in the object-recognition README and await owner review; no application or accuracy result is approved. Task23's existing implementation paths are clean, but its owner agreement for the shared viewer work is still to be established before resuming those controls.

Keep this order live against task dependencies and approval fields:

1. Task40 reference planning and Task41 public-source inventory are complete and await independent Claude checks; Task41's source-choice recommendation also awaits the owner's decision. Task37/42 research is complete and awaits Claude. The fixed snapshot `fyld_goal_review_snapshot_20261005_f` is unchanged; its recorded source gaps remain UNPROVEN.
2. The owner will prompt Claude after the reported 02:30 London reset, using Sonnet 5.5 high and verified snapshot i. Tasks16, 21, 22, 32, 34, 37, 38, 39, 40, 41, 42, 44, 45, 47 and 48 still need technical checks. No returned validation evidence is available. Task48 remains a negative desktop comparison, not a counting result.
3. Resolve Task16 protocol choices and the reviewed Task21/22 input records. The owner asked for more time on Task16 choices, Task41 source selection and Task08 handset evidence. Continue Task31's identity and duplicate policy alongside Task32 geometry, reusing Task46's birth fix and keeping its six-frame fixture separate from the 60-frame replay.
4. Extend Tasks44/45 only for missing stage measures under separately scoped work. Task44's current composite report is not one end-to-end experiment; Task45 source run folders are absent from the pinned snapshot.
5. Finish Task34's mask comparison after Task31 and the independent Task21/22/32/48 gates clear. Its plan has five recorded FAIL reviews and a sixth fresh PASS. The inherited prompt bounds, RGB decode/runtime and quantile settings are declared, and the start gates require manual review. Do not start its run until Task31 and all independent gates clear.
6. Complete Task33 from existing ZNCC/YOLO caches after its geometry and protocol dependencies, with a geometry-only control. Then complete Task35's analytic and supplied-pose controls, changing one error source at a time and including correlated errors and cases where extra views worsen estimates.
7. After Task35, finish Task13's frozen full-sequence validation and documented acceptance defects. Then complete approved Task25 camera correction and compare real correction only after prerequisites.
8. Complete Task09 from child-task evidence, separating isolated controls from chained predictions on the same recording where possible.
9. Complete Task23's existing review controls once ownership of shared viewer files is agreed. Then do Task36 representation comparisons and retain Task39 as requirements only.
10. Task08's cached APK and capability export are recorded; it is pending the owner's rear-camera image export and Samsung S23 availability answer. The owner asked for more time. Task24's cached build passed; its clean dependency/container follow-ups remain separately pending.
11. Task38's KITTI/nuScenes comparison is recorded and awaits the owner's decision on Task41's trial recommendation. Any outdoor/worksite acquisition remains separately authorized.

External inputs still needed:

| Missing input | Owner | Affected tasks | Smallest action |
|---|---|---|---|
| Independent Claude review evidence; none has returned | User | 16, 21, 22, 32, 34, 37, 38, 39, 40, 41, 42, 44, 45, 47, 48 | After the reported reset, prompt Claude with Sonnet 5.5 high using snapshot i and the separate Task32 diff package; return claim verdicts and evidence. If reviewed source files change, use a new snapshot. |
| Accept or revise the documented Task16 protocol and recognition/segmentation shortlist | User | 16 and dependent comparisons 25/33 | Review the existing proposal and record acceptance or requested changes; do not choose numerical experiment settings here. |
| Accept or revise Task41's proposed dataset shortlist | User | 41, 38, and any later outdoor/worksite trial | Choose the proposed source set or name revisions. This does not authorize downloads or captures. |
| Rear-camera control export with original JPEG and capture metadata; Samsung S23 availability | User | 08 and later phone checks | Run one rear-camera control, export that session's ZIP, and state whether an S23 is available. |
| Accept or revise the proposed product review requirements | User | 39 and any later application task | Review the seven proposed actions and record acceptance or changes; this does not authorize app implementation. |
| Agreement on who owns the shared viewer files | User | 23 and dependent Task36 review work | Name the owner for the files shared by the viewer and existing controls. |

Only one task may be `in_progress`. Independent research or validation can move earlier when another task awaits it. Preserve each open and pending-review item in the queue until its receipt and approval state are reconciled.
