---
id: "53"
title: Collect independent scene measurements and object identities
status: open
priority: HIGH
type: infra
blocked_by: [52, 61]
blocks: []
verification_test: "experiments/06_object_recognition/datasets/tests/test_reference_bank.py"
plan_reviewed: null
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
  source: "15 October board review; evidence below"
  field: "Collect independent scene measurements and object identities"
  baseline_value: "One inspected development walk; zero independent surveyed phone scene banks"
  target: "One sealed independent scene bank with whole-session roles and recoverable private inputs"
created: 2026-10-06
last_updated: 2026-10-15
superseded_by: null
---

# Task 53: Collect independent scene measurements and object identities

## In plain English

Collect the independent measurements and human object inventory needed to score the system. Keep those answers separate from the images given to the methods. Record how the private inputs can be recovered without publishing household footage.

## Current evidence

The house walk exists and has already been reconstructed and inspected. It is development data, not a blind evaluation recording. Tasks96-99 replaced the old recorder with v2; Task61 now owns unresolved survey, retention and acceptance decisions. Task40's reference design remains useful. No surveyed dimensions, independent complete inventory or held-out phone bank has been received.

## Plan

1. Resolve only Task61 choices needed for acquisition: scene/region, objects/revisits, survey instruments and uncertainty, reviewer, storage/recovery and session roles. Preserve genuine ambiguity in object identity.
2. Reuse the existing dataset manifest, publisher and reference separation under `experiments/06_object_recognition/datasets/` and Task40's design. Confirm current call paths before adding the planned `prepare_controlled_scene.py` and tests; historical line numbers are not evidence of implementation.
3. Collect references before reviewing predictions. Put each whole session in exactly one of enrollment, validation or evaluation; never split adjacent frames across roles. Create new held-out captures if the development walk influenced settings.
4. Test first for mixed-session-role rejection, evaluator-only truth exclusion from method manifests, units/frame links/uncertainty, missing recovery inputs and changed hashes. Publish the method/evaluator manifest pair together only after cross-validation.
5. Keep originals and survey data outside Git. A tracked release receipt records hashes, bundle IDs and the owner-approved offline retrieval procedure. Verify ignore rules and fresh-checkout recovery. The currently local capture folder is not an agreed backup policy.

## Invariants and completion

Independent answers enter scorers only, never depth, camera tracking or identity matching. Phone depth is not independent surface truth; unavailable geometry truth stays unavailable. Preserve existing provisional desk manifests and scorers. Interrupted publication cannot expose half a manifest pair. Finish with a recoverable versioned bank and explicit unavailable measures; no inferred inventory or model confidence is relabelled human truth. CPU only; no acquisition begins until its needed owner choices and capture readiness exist. Task102's same-walk diagnosis can proceed without this bank.
