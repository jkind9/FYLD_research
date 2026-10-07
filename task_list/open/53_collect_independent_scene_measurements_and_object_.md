---
id: "53"
title: Collect independent scene measurements and object identities
status: open
priority: HIGH
type: infra
approval_status: planning authorised 2026-10-06; execution requires task-specific review and frozen settings
blocked_by: [61]
blocks: []
verification_test: "experiments/06_object_recognition/datasets/tests/test_reference_bank.py"
plan_reviewed: 2026-10-06 PASS
files:
  - .gitignore
  - experiments/06_object_recognition/datasets/**
  - experiments/datasets/**
  - data/controlled_scene/**
docs:
  - experiments/06_object_recognition/datasets/README.md
  - experiments/datasets/README.md
  - data/README.md
  - task_list/README.md
baseline_metric:
  source: task_list/README.md and reuse evidence below
  field: collect independent scene measurements and object identities
  baseline_value: "0 independent physical object-position/count references and 0 surveyed phone test scenes"
  target: "1 versioned independently measured scene bank with separate development and held-out session roles"
created: 2026-10-06
last_updated: 2026-10-07
superseded_by: null
---

# Task53: Collect independent scene measurements and object identities

## In plain English

Create a test scene whose correct measurements and object identities are known independently. Measure it and check the objects before looking at the program's answers. Film revisits and difficult cases so we can tell whether the program misses objects or counts the same one twice.

## Board update, 7 October 2026

Task51 was rescoped on 6 October 2026 to the first prerecorded pipeline. Where this file refers to Task51 decisions for field work (site, objects, survey method, storage and retrieval, numeric limits, phone processing split), Task61 now owns them. This task is now blocked by Task61 instead of Task51. Task40's reference design, which this task executes, closed on 7 October 2026 and stays the design source.

## What

Execute the reference design from Task40, using the scene and session policy agreed in Task51. Own the surveyed scene, object registry, human labels/masks needed for chosen measures, dimensions/areas/control points and reference uncertainty. Task52 supplies recorder engineering; Task53 owns scored-scene arrangement and session selection. Reuse an approved public source from Task41 only for questions its independent references actually answer; record access/terms and do not substitute benchmark sensor depth for independent truth.

## Why

Current identity labels are agent-reviewed and physical centres/counts are unknown. Task40/41 plan references and sources but do not collect them.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Detailed physical-reference design exists | Task40 | scene collection and scorers | task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:65-73 |
| Existing desk publisher stages paired artifacts and exposes them with one directory rename, but its manifest does not represent surveyed site truth or enforce session-level roles | dataset publisher | current desk dataset consumers only | experiments/06_object_recognition/datasets/prepare.py:169-203; experiments/06_object_recognition/shared/manifest.py:205-278 |
| Additional source inventory does not acquire data | Task41 | optional public-source selection | task_list/closed/41_investigate_candidate_test_datasets_and_trial_exis.md:35 |

Task53 will define and validate a controlled-scene manifest under `experiments/06_object_recognition/datasets/`. It will keep method inputs and evaluator-only truth in one versioned publication directory, validate that each complete capture session has exactly one role, and keep survey units, frame links, uncertainty, object identity and ambiguity labels out of method inputs. The existing desk schema and pinned desk scorer remain unchanged. Task56 must consume the new pair through a declared adapter before scoring it.

1. Confirm scene access, instruments, reviewers, target classes, session/sample choices and any public-source access before acquisition. Do not assume access from this planning task.
2. Measure anchors, observable dimensions, site boundary/area and independent control points; record units, frames, orientation and instrument/setup uncertainty. Define the survey-to-method frame link without fitting scored targets.
3. Fix a physical object registry and event plan: revisit, similar distinct neighbours, occlusion, distance/motion and camera loss where required by Task51. Preserve genuinely ambiguous identity truth.
4. Survey/label before inspecting model predictions. Task52 can build the recorder alongside survey preparation; only its verified recorder supplies the scored phone captures.
5. Assign each complete phone session to exactly one existing manifest role: `enrollment`, `validation`, or held-out `evaluation`. Decide these roles before selecting model or camera settings. If settings or calibration are selected from collected sessions, keep enrollment, validation and evaluation sessions separate. If no setting selection uses collected data, record that fact and leave the validation role unused. Do not split adjacent frames from one session across roles. Add a controlled-scene manifest and validator under the declared dataset scope. Reject sessions assigned to multiple roles, method-input truth fields, missing units/frame links/uncertainty, and altered reference hashes. Publish the method-input and evaluator-only manifests together inside one staged directory, validate both and their cross-references, then expose the pair with one atomic directory rename. Do not change the provisional desk manifest or pinned desk scorer.
6. Keep raw phone and survey payloads outside Git. `.gitignore` must exclude every file below `data/controlled_scene/input/`, including JSON source manifests and sidecars; verify this with `git check-ignore` before collection. Before acquisition, Task51 must record the owner's approved storage location and the exact offline steps for retrieving a bundle; if either is missing, stop. Have Task52 export the original phone session as a self-contained bundle. Copy it to `data/controlled_scene/input/phone/<session-id>/` and copy the separately sealed survey/reference bundle to `data/controlled_scene/input/reference/<scene-id>/` on the chosen host. Before publishing, create the tracked receipt `experiments/06_object_recognition/datasets/releases/<release-id>.yaml` with the release ID, bundle IDs, source-manifest hashes, and the applicable retrieval procedure recorded in Task51. Run `python -B experiments/06_object_recognition/datasets/prepare_controlled_scene.py --input-root data/controlled_scene/input --release-id <release-id>`. The command checks each source hash, required sidecar and reference link before publishing. A fresh checkout reads the tracked release receipt, retrieves both bundles from the Task51-approved location, copies them into the named input folders and verifies their manifest hashes before preparation. Missing bundles, payloads or hash agreement stop preparation. Do not claim that ignored phone media is contained in Git.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Independent survey/human reviewer | evaluator adapter only | metres, frame/session IDs, instrument uncertainty, physical IDs and explicit ambiguous/missing labels | versioned evaluator bundle survives | task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:67 |
| Task52 export and independent survey/reference bundle | controlled-scene preparation command | original phone payload under `input/phone/`, separate truth bundle under `input/reference/`; bundle IDs and source hashes recorded in the tracked release receipt | retained outside Git at the Task51-approved storage location and restored using the receipt's release ID | task_list/open/52_build_and_verify_a_usable_phone_recording.md:55-60; data/README.md:5 |
| Recorded observations | method adapters | original image/depth/pose/calibration and one role per whole session; no truth IDs | sealed method bundle survives | experiments/06_object_recognition/shared/manifest.py:205-278 |
| Controlled-scene publisher | dataset readers | paired manifests and shared version/hash links in one publication directory | both bundles appear together or neither does | experiments/06_object_recognition/datasets/prepare.py:169-203 |

Source of truth is independent survey and human review, never model outputs. References cross into scorers only through the evaluator adapter. Raw phone and survey payloads remain outside Git at the owner-approved Task51 storage location. A tracked release receipt names each bundle and manifest hash and points to the recorded retrieval procedure. A fresh checkout uses that receipt and Task51 decision to retrieve the same payloads and verifies hashes before preparation. If the approved location cannot supply either bundle, preparation stops until the owner restores it. Missing or hash-mismatched inputs stop preparation before publication. A failed publication remains in staging and is not visible as a usable dataset; retries use fresh paths. One directory rename publishes both bundles, so a process stop cannot expose only one side. Reference corrections create a new version and invalidate comparisons against earlier versions. First use requires both validated manifests and their cross-reference checks; old provisional desk references remain unchanged and are not relabelled as independent.

## Hyperparameters

| name | value | source |
|---|---|---|
| scene, object classes, instruments, reviewed views, capture/session counts, splits and uncertainty limits | pending Task51 and scene-access decisions | n/a planning only; owner-confirmed values required before acquisition |
| reference semantics and separation | anchors, dimensions, uncertainty and evaluator-only truth | inherited task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:67 |

## Verification

`experiments/06_object_recognition/datasets/tests/test_reference_bank.py` asserts that assigning frames from one session to more than one of `enrollment`, `validation` and `evaluation` is rejected; evaluator-only truth is absent from the serialized method manifest; missing units, survey-to-method frame links, uncertainty or valid hashes are rejected; missing fresh-checkout input bundles fail with a clear message; altered input files fail hash validation; and the publisher exposes both manifests together only after cross-validation. Every scored item has independent provenance or an explicit unavailable reason. Before 0 surveyed phone test scenes; target 1 sealed scene bank with independent counts/dimensions and the agreed session roles. Missing 3D surface truth must remain unavailable, not be inferred from phone depth. The existing desk manifest and scorer remain byte-for-byte unchanged.

Before starting HIGH work, refine exact scope, audit settings, run task-plan lint and obtain a fresh plan review against current sources. No implementation or acquisition is performed while writing this plan.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | Plan only; implementation not started. After the 2026-10-06 FAIL review, the plan gained a named original-checkout source path, phone/reference input folders, a recorded retrieval path, and fresh-checkout hash checks. |
| Test status | Current plan lint passes. Fresh plan review PASS on 6 October 2026 after checking session-role separation, raw-input exclusion and fresh-checkout recovery. No software tests or acquisition run. |
| Before measurement | 0 independent physical object-position/count references and 0 surveyed phone test scenes |
| After measurement | Not measured |
| Delta | Not measured |
| Decision-gate outcome | Plan ready; execution remains blocked by Task51 owner decisions, including approved offline storage and retrieval steps. |

still open because Task51 owner decisions, a passing current plan review, implementation and physical measurement are still pending.
