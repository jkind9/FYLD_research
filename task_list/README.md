# Task list

## Current records, 5 October 2026

This board separates measured controls and bounded proofs of concept from untested investigations. Task30 completed documentation/research only. Preserve Task13 frozen settings and unfinished code; leave Task16/21/22 pending review. Closed receipts are historical evidence and are not rewritten by the new backlog.

| Task | State | Evidence or outstanding question |
|---|---|---|
| [00: first prototype](archive/00_finish_and_validate_the_phase_1_scene_mapping_prot.md) | Superseded | Preliminary research/runs preserved; integrated validation unfinished |
| [01: experiment organisation](closed/01_organise_independent_scene_mapping_experiments.md) | Closed | Six independent boundaries and preserved prototype evidence |
| [02: standard references](closed/02_verify_standard_tracking_and_reconstruction_refere.md) | Closed | Acquired ICL depth/poses and independent surface; selected TUM desk |
| [03: geometry contracts](closed/03_define_observation_and_pose_contracts_with_known_g.md) | Closed | Known-coordinate control and source/stage exports |
| [04: supplied-input surface](closed/04_evaluate_reconstruction_with_supplied_depth_and_po.md) | Closed | Nine ICL views; 7.85 mm mean reference distance and 22.29% coverage within 5 cm |
| [05: tracking baseline](closed/05_evaluate_tracking_with_supplied_benchmark_depth.md) | Closed baseline | Thirty TUM observations; 6.93 mm camera-position error and 2.14 image pairs/s |
| [06: recovered research](closed/06_recover_interrupted_research_and_review_current_or.md) | Closed | Original research and source corrections preserved |
| [07: mobile mapping products](closed/07_review_mobile_stereo_mapping_products_against_the_.md) | Closed | Product evidence and map-rate/depth-rate limits separated |
| [08: phone feasibility](open/08_check_phone_capture_feasibility_alongside_reconstr.md) | In progress, awaiting image-control export | Redmi capability report passes integrity validation; rear/front IDs and no advertised concurrent sets. Supplied session has no images; ARCore skipped because SDK absent; Samsung availability unconfirmed |
| [09: inventory umbrella](open/09_evaluate_scene_object_recognition_and_persistent_counting.md) | Open | Checked persistence plus bounded child trials; independent inventory and wider cases remain |
| [10: repository publication](closed/10_prepare_research_repository_and_publish_initial_main.md) | Closed | Initial main snapshot and publication exclusions recorded |
| [11: geometry review](closed/11_explain_geometry_control_outputs_and_show_supplied.md) | Closed | Explained supplied-input/source-coordinate views |
| [12: folder separation](closed/12_separate_geometry_validation_from_camera_pose_esti.md) | Closed | Supplied-pose control separated from camera estimation |
| [13: frozen full tracking](open/13_validate_frozen_tracking_settings_on_full_developm.md) | Open, unfinished | Preserve frozen settings and partial code; full xyz/held-out desk tracking not run; 573 desk pairs acquired |
| [14: labelled 3D inspection](closed/14_add_labelled_3d_stage_inspection_and_camera_motion.md) | Closed | Camera/surface viewers with explicit observed/reference/result labels |
| [15: owner plan review](closed/15_prepare_recorded_video_recognition_plan_for_owner_.md) | Closed | Outline approved 3 October; later task-specific authorisations remain distinct |
| [16: broader research protocol](pending_review/16_research_segmentation_recognition_and_camera_corre.md) | Pending review | Exploratory work does not approve the broad model/protocol comparisons |
| [17: provisional reference](closed/17_prepare_labelled_revisit_inputs_and_object_observa.md) | Closed | Six agent-reviewed desk frames; complete selected cup coverage, monitor positive subset; no human gold |
| [18: cached detection check](closed/18_evaluate_object_detection_on_frozen_labelled_obser.md) | Closed | Four of five cup references matched; monitor accuracy unscorable as full inventory |
| [19: classical mask control](closed/19_evaluate_classical_and_edge_device_object_segmenta.md) | Closed | 45 masks across 15 prompts; coordinate changes/costs, no demonstrated accuracy improvement |
| [20: appearance control](closed/20_compare_object_appearance_matching_across_viewpoin.md) | Closed | ZNCC and existing YOLO features tested; one wrong monitor ranking; ResNet50 untested |
| [21: identity association](pending_review/21_associate_object_identities_with_geometry_and_appe.md) | Pending review | Geometry-only and combined rules each resolve eleven provisional observations; broader necessity unproved |
| [22: recorded replay](pending_review/22_build_recorded_video_camera_surface_and_inventory_.md) | Pending review | Accepted sixty-frame/457-proposal viewer and six-frame automatic comparison; final browser-launch limit retained |
| [23: surface review controls](open/23_embed_interactive_surface_review_and_explain_depth.md) | Approved, open, unfinished | Preserve partial edits; acquired publication/source-hash checks and finished reviews remain |
| [24: APK build recovery](pending_review/24_recover_and_reproduce_android_apk_build_inside_cap.md) | Pending review | Repository-owned cached WSL build verified; clean dependency and compatible container builds remain blocked. Task08 owns handset checks |
| [25: camera revisits/correction](open/25_compare_feature_seeded_odometry_and_verified_camer.md) | Approved outline, later | After Task13 and Task16 review; sidecar contract exists, correction production/comparison unperformed |
| [26: standalone camera/surface](closed/26_export_self_contained_shareable_offline_viewers.md) | Closed | Portable offline viewers preserve supplied-input evidence |
| [27: xyz cup localisation](closed/27_localise_yolo_cup_detections_in_recorded_rgbd.md) | Closed | One YOLO26x detection projected with measured depth and supplied poses; separate from desk cup |
| [28: desk cup replay](closed/28_replay_cup_revisits_with_persistent_object_ids.md) | Closed | Sixty sampled desk frames; persistent cup ID across detector gap/return, not continuous physical absence |
| [29: portable replay and spread](closed/29_export_replay_and_review_reconstruction_and_identi.md) | Closed | All nineteen cup proposals exported; sixteen assigned box RMS 72.8 mm / centre RMS 82.3 mm; surface repeatability only |
| [30: documentation reconciliation](closed/30_reconcile_experimental_evidence_and_research_backl.md) | Closed | Evidence/source review complete; 226 local links/anchors checked and ten proposed follow-ups; no experiment started |

Implementation tests, coverage and hash checks remain in owning receipts. They support software correctness; experimental progress is explained through data, measurements, references and limitations.

## Proposed follow-ups and ownership

New Tasks31-40 are open, unstarted and proposed. HIGH priorities indicate evidence/identity risks and scheduling value; they are not execution approval. Before start, complete exact scope/tests, reference/settings decisions and required plan review. No scaffold, acquisition or model execution is created by this board.

| Task | Priority | Dependencies | Question / boundary |
|---|---|---|---|
| [31: Compare provisional object IDs and duplicate relationships](open/31_compare_provisional_object_ids_and_duplicate_relationships.md) | HIGH | Task21, Task22, Task40 | Can provisional births and explicit duplicate relationships retain new/returning objects without inflating confirmed inventory or hiding uncertainty? |
| [32: Investigate spatial support and position uncertainty](pending_review/32_investigate_spatial_support_and_position_uncertainty.md) | HIGH | Task40 | Support component built and tested; independent calibration, usefulness and matching thresholds remain for validation |
| [33: Compare object appearance, context and spatial association](open/33_compare_object_appearance_context_and_spatial_association.md) | MED | Task31, Task32, Task40, Task16 | Which appearance/context evidence and spatial trade-off reduce false merges/splits at acceptable full processing cost? |
| [34: Evaluate segmentation for position and observed dimensions](open/34_evaluate_segmentation_for_position_and_observed_dimensions.md) | HIGH | Task40 | Does foreground segmentation reduce background-depth contamination and improve repeatability/absolute error or dimensions relative to rectangles? |
| [35: Measure error propagation and sequential fusion](open/35_measure_error_propagation_and_sequential_fusion.md) | HIGH | Task32, Task34, Task40 | Which errors dominate the pixel-to-fusion chain, and under what conditions do additional independent views reduce or reinforce error? |
| [36: Compare surface representations and visual realism](open/36_compare_surface_representations_and_visual_realism.md) | MED | Research/design independent | Which representation improves review/navigation at suitable cost without obscuring geometry error or missing coverage? |
| [37: Research ARCore, ARKit and RoomPlan mapping](open/37_research_arcore_arkit_and_roomplan_mapping.md) | MED | Research/design independent | Which accessible APIs and capture/correction/revisit techniques can supply the project's measurement records, and which require new hardware or algorithms? |
| [38: Research longer-range fusion and driving evaluation](open/38_research_long_range_fusion_and_driving_evaluation.md) | MED | Research/design independent | Which sensor/data/uncertainty representation can test the intended range, and what can KITTI/nuScenes references actually establish? |
| [39: Record future 3D review and measurement requirements](open/39_record_future_3d_review_and_measurement_requirements.md) | LOW | Research/design independent | What evidence and measurement interactions are needed for later 3D review without hiding rejected/uncertain observations or overstating accuracy? |
| [40: Plan independent references and hard-case acquisition](open/40_plan_independent_references_and_hard_case_acquisition.md) | HIGH | Research/design independent | Which independent identity/mask/anchor/extent/surface references and hard cases are necessary and practical for the proposed comparisons? |
| [44: Build a per-stage accuracy log for end-to-end runs](open/44_build_a_per_stage_accuracy_log_for_end_to_end_runs.md) | HIGH | None; first slice uses existing accepted runs | One report per run scoring every stage (camera path, detection, segmentation, depth support, 3D position, surface, identity, count) against reference data, marking unscorable stages as unavailable, separating a stage's own error from error passed down from earlier stages, and comparing two runs stage by stage |
| [45: Measure detection position error in cluttered scenes](open/45_measure_detection_position_error_in_cluttered_scen.md) | HIGH | Run 5 October in branch `experiment/45-…` (worktree `.worktrees/task-45`); awaiting diff review and merge | How far detector boxes land from true object outlines in clutter, how much they wobble frame to frame on stationary objects, and how much background they include. Results: found boxes are tight (median centre offset 1.6 px on 20,036 COCO boxes; clutter correlation 0.10); desk wobble is 1.8 px on clean boxes, near the 1.4 px measurement floor, but 5.8 px where boxes touch the image edge or have poor depth; of 588 lost tracks, 449 were gone, 60 were claimed by another track, 53 had no depth and 26 were one-to-one jumps |

Task09 retains the inventory objective and checked-store history. Tasks31-35 own new isolated comparisons rather than silently enlarging Tasks19-22. Task40 owns shared independent-reference/capture design; it does not turn Task17 provisional labels into human gold. Task37 owns room-platform research; Task38 owns driving/range suitability; their research can proceed before optional acquisitions. Task39 is a later application requirement, not a build task. Task23/24 keep their existing scopes. Task25 stays behind frozen Task13 and broader protocol review; Task35 can start with analytic/supplied-pose controls without triggering either camera run.

## Next-experiment order and gaps

Added 5 October 2026 at the owner's request: end-to-end tests should produce a per-stage accuracy log against reference data. **Task44** builds that log from existing runs first (no new inference). **Task45** adds detection box placement error and wobble, the first measure aimed at the cluttered-scene position variation; it uses COCO val2017 (downloaded 5 October) and the local TUM desk recording, because ScanNet++ needs an owner access request. Tasks 32, 34 and 35 report into the Task44 format.

1. **Task40 reference design and owner review.** Inventory existing data first; define physical anchor versus visible surface versus whole size, reference uncertainty, independent identity/pixel-mask review and session splits. Required gaps include survey/reference access, annotation labour, new-session/hard-case capture permissions, exact device support and any needed sensor hardware. No new acquisition is authorised by Task30.
2. **Task31 policy comparison on cached proposals.** Hold detection/depth/poses fixed and compare restrictive births with provisional objects/duplicate links. Initial software/policy accounting can use desk; physical accuracy needs Task40 hard cases. Task21/22 outcome review remains a prerequisite.
3. **Task34 rectangle/classical/checked-foreground control.** Hold boxes/depth/poses fixed; isolate background-depth selection before any learned mask. Pixel masks and physical/surface/extent references are required to claim improvement.
4. **Task32 spatial supports and uncertainty.** Use fixed checked supports and explicit anchors; compare point gates/simple regions/multiple hypotheses. Task34 results can inform support selection but are not a hard prerequisite for an oracle-mask initial control. Independent reference coverage/calibration decides whether uncertainty claims are justified.
5. **Task33 appearance/context plus spatial association.** Fix crops/gallery/supports first; use existing ZNCC/YOLO caches before authorised ResNet50/context models. Independent hard negatives, separate validation and model terms/weights/runtime permission are needed. Test geometry-only too.
6. **Task35 sequential error/fusion.** Perturb one stage at a time, then combine; compare individual and growing estimates. Independent measurement lineage matters more than frame count. Real pose-correction comparisons wait for Task13/25 separately.
7. **Task36 representation controls.** Denser display then fixed-depth/pose patches/mesh; texture/photogrammetry/splat/NeRF later with separate geometry/visual references and resource approval. Task23 remains the current review-controls owner.

Tasks37 and 38 are independent research/selection streams, followed by separately authorised Android/Apple or KITTI/nuScenes acquisitions if justified. Task08 now has actual Redmi capability evidence and needs a separate rear-camera control export with images; Samsung availability is unconfirmed. No concurrent sets are advertised in the supplied report. A browser preview can check basic streaming but cannot measure native concurrent-camera support. Task24's clean dependency and container build follow-up remains in pending review. Task39 requires later review of user journeys/data contracts before a separate implementation task. No task is started merely because it appears first here.

The adapter excludes depth at/beyond 4 m. Indoor controls do not justify outdoor gates or accuracy. Acceptance thresholds, sample sizes, instrument tolerances and model settings remain owner decisions before execution, not numbers invented during documentation.

## Key evidence

Open [the accepted Task22 viewer](../experiments/06_object_recognition/experiments/05_replay/runs/20261004T152704.023370Z_84abb8b3b9594dcea8a1e5b2c8aced66/review.html), [portable ZIP](../experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_replay_20261004.zip), [cup CSV](../experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_desk_observations.csv), [spread definitions/results](../experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json) and [primary-source research coverage](../research/README.md#research-agenda-4-october-2026). Local generated evidence is excluded from Git and needs a verified offline handoff.

The sixteen assigned desk-cup observations have RMS spread 72.8/82.3 mm and maximum pair separation 291.7/317.0 mm for box median/centre sample. These are surface-repeatability statistics, not absolute physical-centre errors. The 30.8 mm return result uses two views. The 95-book result includes a restrictive birth policy, not failed book appearance matching.

## Reconciliation checks and remaining board findings

Task30 source checks verified the accepted publications and portable artifacts; the numeric spread was recomputed from the exported CSV without inference. Missing mobile-deployment documentation declarations were redirected to the existing stage01 README. Task24/25 verification paths are planned tests, not completed files. New HIGH investigations intentionally have no plan-review stamp and cannot start before their reviews/settings/references are complete. The read-only audit also reports inherited oversized reference/vendor/saved-source files; these are preserved rather than refactored or deleted in documentation work.

## Workflow and supporting engineering records

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
`CONSTITUTION.md` is currently an unratified template; it does not yet supply owner-ratified project principles
(versioned, owner-ratified — plans conflicting with it fail review).
Full guide: `~/.claude/task-system/HOWTO.md`.
