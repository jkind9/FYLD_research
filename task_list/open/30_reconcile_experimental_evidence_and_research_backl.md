---
id: "30"
title: Reconcile experimental evidence and research backlog
status: in_progress
priority: MED
type: decision
blocked_by: []
blocks: []
verification_test: ""
plan_reviewed: null
files:
  - .gitattributes
  - .gitignore
  - README.md
  - experiments/**/README.md
  - experiments/README.md
  - research/**/README.md
  - research/README.md
  - data/README.md
  - task_list/**
docs:
  - README.md
  - experiments/README.md
  - experiments/06_object_recognition/README.md
  - research/README.md
  - task_list/README.md
baseline_metric:
  source: README.md:87
  field: stale current-status claims
  baseline_value: "1 root statement says no recognition inference has run"
  target: "0 such statements; all nine requested workstreams have explicit owners"
created: 2026-10-04
last_updated: 2026-10-04
superseded_by: null
---

# Task30: reconcile experimental evidence and research backlog

## In plain English

Make the project records explain what has been measured and what remains uncertain. Check saved evidence, correct outdated descriptions and give each next investigation a clear question. This session ends with documentation and planning, without starting another experiment.

## What

Reconcile root, experiment, research and board READMEs with accepted artifacts. Add scoped follow-ups for observation identity, spatial uncertainty, appearance, segmentation, sequential errors, surface representations, room mapping, longer-range evaluation and future review requirements. Preserve unrelated edits and historical receipts.

## Why

The root still says no recognition inference has run, while accepted desk replay and appearance receipts exist. Earlier plans mix completed bounded controls with unperformed broad comparisons. Test totals do not establish scientific progress or physical accuracy.

## How

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Accepted viewer and portable measurements already exist | replay publication and Task29 exports | root and research summaries | experiments/06_object_recognition/experiments/05_replay/README.md:5; experiments/06_object_recognition/experiments/05_replay/runs/shareable/task22_20261004/cup_repeatability.json:1 |
| Appearance result includes a wrong monitor ranking | Task20 | comparison backlog | experiments/06_object_recognition/experiments/03_appearance/README.md:56 |
| Mask coordinate changes are not accuracy scores | Task19 | segmentation follow-up | experiments/06_object_recognition/experiments/02_segmentation/README.md:5 |
| Task09 already owns the inventory umbrella | Task09 | new bounded follow-ups | task_list/open/09_evaluate_scene_object_recognition_and_persistent_counting.md:35 |

- Inspect board, READMEs, saved results and source artifacts without inference.
- Browse primary documentation/papers and qualify the supplied display-conversion article.
- Revise stale text, links and diagrams; retain useful existing content.
- Create proposed tasks with comparisons, references, measures, dependencies, costs and decisions.
- Check local links, task invariants, source claims and session preservation; record actual checks.
- Owner follow-up authorises repository tidying, ignore updates, commit and push. Ignore generated caches/test databases without deleting completed runs or unrelated dirty work; publish only reviewed documentation/board/ignore files.

## Invariants and recovery

invariants n/a: documentation-only work; no runtime state or experiment settings change. Task13 unfinished code/settings, Task16/21/22 review states, source runs and historical receipts are preserved. New follow-ups remain open and unstarted. An interrupted documentation edit can be reviewed through the working diff; no source artifact is republished.

## Hyperparameters

hyperparameters n/a: no inference, model acquisition, training, full tracking sequence or numerical experiment. Future parameters and success thresholds remain decisions for their owning tasks.

## Verification

Documentation contract: check all changed local Markdown destinations and diagram status labels; cross-check accepted viewer counts, cup spread definitions, association outcomes, book policy and depth cutoff against saved artifacts/source. All nine requested workstreams must have explicit owners and reference/measurement requirements. Run task lint and read-only audit, distinguishing planned missing paths and inherited findings from new defects. Compare session-boundary hashes of non-documentation dirty files and accepted artifacts.

Before: 1 root statement says no recognition inference has run. Target: 0 such current-status statements and 9 covered workstreams. No accuracy or runtime improvement is claimed.

tests n/a: documentation/research only; existing implementation test receipts remain supporting history. No implementation suite or experiment is executed.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Documentation evidence commit pending below; no implementation commit in this task |
| Files changed | Root/data/experiment/research READMEs; stage06 evidence READMEs; board and Tasks08/09/24/25; new proposed Tasks31-40; .gitignore and .gitattributes. Frozen source annotation and unchanged historical board receipts included for publication links. |
| Test status | Documentation checks: 16 READMEs, 226 local destinations/fragments, 0 broken; 4 Mermaid blocks structurally checked, 0 fence/quote/bracket errors. No rendered-diagram/browser retest or implementation suite. |
| Before measurement | 1 stale root inference statement; nine requested workstream owners absent; current board included nonexistent mobile-deployment documentation declarations |
| After measurement | Stale root statement removed; all 9 workstreams plus shared reference acquisition have 10 open proposed owners, each with question/evidence/comparison/reference/measures/dependencies/cost/decision. Task lint: 41 tasks, 0 errors/warnings. |
| Delta | +10 scoped plans; stale visibility/status/ownership and 2 broken fragment links corrected; missing mobile-deployment docs redirected to stage01; no experiment measurement changed |
| Decision-gate outcome | Documentation/research complete and reviewed with concrete fixes applied. User authorised tidy/ignore/commit/push; scoped publication in progress. Task13 preserved; Task16/21/22 pending review; Tasks31-40 unstarted. |

Evidence checks: fresh agent verified Task17 publication hashes and Task18/19/20/21/27/22 manifests (103/206/140/172/72/258 members respectively), with no size/hash failures. Task29's five receipt-listed hashes matched; copied HTML equals source; six ZIP members passed CRC. CSV recomputation from all 19 cup proposals confirmed the 16 assigned observations: box RMS 72.785494 mm, maximum pair 291.669423 mm; centre RMS 82.285053 mm, maximum pair 317.024892 mm. Independently counted 95 books as 1 new/4 matched/90 unresolved outside gate and traced restrictive birth policy; source depth cutoff remains <4 m.

Primary-source review covered all A?I: assignment, calibration/extended objects, appearance, masks, sequential correction, surfaces/novel views, ARCore/ARKit/RoomPlan, KITTI/nuScenes and future review requirements. Alpha3D returned a landing shell; its article claims remain unverified. No source result was treated as a local experiment or hardware capability.

Independent documentation review found stale pilot absence/Task17 status, nonexistent Task24 README instructions, Task25 downstream ownership and weak evidence line pointers. Each was corrected; targeted recheck accepted the main fixes and named two last pointers, now corrected. Numeric results and requested limitations matched saved evidence.

Preservation check: 17 protected initial dirty code/configuration files, Task13/16/21/22 task records and accepted replay/export files retain identical SHA256. Ignore checks cover caches, scratch SQLite sidecars, completed runs, generated reference publication and APK bundles without deleting them. No packages, weights, downloads, training, inference or full Task13 sequence.

Read-only audit: 185 findings = 153 inherited size findings, 25 explicit waiver/open notes, 5 unstamped proposed HIGH plans and 2 planned Task24/25 test paths. The HIGH plans require review before start; inherited vendor/saved-source/unfinished files remain preserved. The unratified constitution remains a draft. These findings are not waived as experimental success.

Remaining publication step: commit the reviewed documentation/board/ignore files, record the evidence commit, close this documentation task and push the closure. Unrelated dirty implementation stays outside these commits.

Publication byte check caught automatic CRLF-to-LF normalization of the newly tracked frozen annotation. A path-specific -text attribute preserves its exact sealed SHA256 a786adc5f814ad9773712397f46ba79d8d40dc5c174fe17045336440cdffd920 in Git. The working file and completed receipts are unchanged; index-byte agreement is checked before committing.
