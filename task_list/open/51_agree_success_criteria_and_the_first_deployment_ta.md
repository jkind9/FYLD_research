---
id: "51"
title: Agree success criteria and the first deployment target
status: in_progress
priority: HIGH
type: decision
approval_status: planning authorised 2026-10-06; execution requires task-specific review and frozen settings
blocked_by: []
blocks: [53, 54, 55, 57]
verification_test: ""
plan_reviewed: 2026-10-06 PASS
files:
  - .gitignore
  - pytest.ini
  - data/README.md
  - experiments/01_camera_capture_delivery/README.md
  - task_list/open/51_agree_success_criteria_and_the_first_deployment_ta.md
  - task_list/open/52_build_and_verify_a_usable_phone_recording.md
  - task_list/open/53_collect_independent_scene_measurements_and_object_.md
  - task_list/README.md
  - README.md
  - experiments/01_camera_capture_delivery/README.md
docs:
  - data/README.md
  - task_list/README.md
  - README.md
  - experiments/01_camera_capture_delivery/README.md
baseline_metric:
  source: task_list/README.md and reuse evidence below
  field: agree success criteria and the first deployment target
  baseline_value: "0 owner-agreed complete-system acceptance records"
  target: "1 recorded decision covering accuracy, latency, deployment, workload and held-out protocol"
created: 2026-10-06
last_updated: 2026-10-06
superseded_by: null
---

# Task51: Agree success criteria and the first deployment target

## Clarifications

### Session 2026-10-06

- The owner selected the available Redmi for capture and live checks, with final processing on a named host.
- The owner asked to leave every numeric accuracy, wait-time and device-use limit pending.
- The site/use case, target objects and revisit conditions, final host choice, and independent survey/inventory method remain pending. The supplied Redmi capability report identifies model 2201116TG; its ARCore runtime support still needs an on-device check. Do not start acceptance runs that need the other choices.
- All numeric accuracy, coverage, waiting-time, live-update, sustained-use, memory, battery and heat targets remain pending, as requested.

### Recommendations submitted 2026-10-06; owner confirmation pending

| Item | Evidence | Recommendation | Owner state |
|---|---|---|---|
| First use case | The project targets worksite walkthroughs (README.md:1-8). Existing TUM desk views have no physical survey (task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:63). | Start with one controlled indoor worksite room or bay that the owner can survey. Keep stationary items in place across visits. | Pending site access and owner choice. |
| Objects and revisits | Existing desk labels show a white-cup return and two similar monitor enclosures, but labels are provisional and there is no measured object anchor (task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:63). | Use owner-selected worksite objects. Include one look-away/return and one similar-looking object that is physically distinct. Record any moved object separately. | Pending object names and revisit conditions. |
| Phone and depth path | The owner selected a Redmi for capture/live checks. Its supplied capability report identifies model 2201116TG, Android 13, and reports camera inventory and permission checks passing; it contains no captured images or ARCore result (experiments/01_camera_capture_delivery/README.md:211-230). Xiaomi's [official Redmi Note 11 Pro guide](https://alsgp0.fds.api.xiaomi.com/xiaomi-b2c-i18n-upload/user-guides/1c100fb724c5e54a94ff40e423c5d7ef.pdf) identifies 2201116TG as Redmi Note 11 Pro. Google's [current ARCore device list](https://developers.google.com/ar/devices) lists Redmi Note 11 Pro with Depth API support. This makes ARCore depth a documented candidate for the reported model. It does not prove ARCore runtime support, delivered depth quality, or metric accuracy on this handset. The capability APK has no ARCore SDK, and the Camera2 report advertises no DEPTH16 stream; those facts do not rule out ARCore's computed Depth API. The local Gradle cache has no `com.google.ar` dependency. The Windows shell has no ADB command or Android SDK path variables. The pinned WSL SDK contains ADB at `/home/jkind/Android/Sdk/platform-tools/adb`; earlier `adb devices -l` returned no devices, `usbipd list` showed no Android handset, and the SDK has no emulator binary or configured AVD. | Keep the Redmi for capture/live checks and test ARCore Depth API on the actual device when it is available. Record runtime support, captured RGB/depth/confidence, calibration and timestamps; do not treat the model list as a depth result. Keep final processing on the owner-selected host. | The exact phone model is identified by the supplied device report and Xiaomi's guide. A cached Camera2 package is verified; physical image export, ARCore runtime support, depth quality, current device connection and host confirmation remain unproved. |
| Final-processing host | Read-only host inventory on 2026-10-06 reports `MasterPC`, AMD Ryzen 9 9950X, Gigabyte X870 GAMING X WIFI7. The frozen CPU tracking runs completed on this host. | Use this PC for final processing unless the owner names another host. | Pending owner confirmation. |
| Independent survey and identities | Task40 requires surveyed anchors, dimensions, a separate frame link, instrument uncertainty and human-reviewed identities (task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:67-73). | Use an available calibrated tape or distance meter to survey the room and selected object anchors. Record instrument details and uncertainty. Have a person record which objects are the same or distinct before viewing predictions. | Pending tool availability and owner method. |
| Raw-data retention and recovery | Media payloads are excluded from Git, and a fresh checkout does not include them (data/README.md:5; .gitignore:78-101). | Keep the original phone export and survey bundle in an owner-controlled location outside Git. Record its location and file hashes so an offline fresh checkout can restore the inputs and verify them. | Pending storage location and recovery method. |
| Numeric limits | The owner explicitly asked to leave every numeric target pending in the 2026-10-06 reply. | Keep all numeric acceptance fields pending. Do not label any trial as a product pass until these limits are agreed. | Pending owner values. |

## In plain English

Agree what a useful first result must do. Decide how accurate the measurements and counts must be, how long the user can wait, and which device must run which parts. Record the choices before selecting or tuning methods.

## What

Own the first acceptance record, including target object classes, scene/range and motion conditions, measured outputs, measurement/count error limits, minimum coverage, maximum complete-result wait, offline feedback requirements, target hardware, sustained-use duration, memory/battery/heat limits, reference uncertainty, session-disjoint test selection and raw-data retention/recovery. Distinguish the phone, a nearby edge computer and a hosted server. The available Redmi is the candidate, not proof of capability; Samsung access is unconfirmed. Decide the baseline methods and licensed checkpoints from existing evidence without assuming a new model is better.

## Why

Current tasks have numerical settings but no shared definition of acceptable product behaviour. Deployment was treated as secondary. The owner now requires accuracy, latency and edge deployment together.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Acceptance choices remain pending | Current task board | all acceptance trials | task_list/README.md:13 |
| Device/runtime evidence is limited | Capture experiment | capture and edge plans | experiments/01_camera_capture_delivery/README.md:196 |
| Reference design exists | Task40 | measured-scene plan | task_list/closed/40_plan_independent_references_and_hard_case_acquisition.md:65-73 |
| Test and diagnostic scratch belongs outside task records | Task board guidance | future project checks | task_list/README.md:21; tools/check.py:11-27 |
| Controlled-scene source files need full Git exclusion and a retrieval record | Task53 input plan | future checkout and preparation | .gitignore:78-101; data/README.md:5 |

1. Present the owner with one short decision table covering the items in What; show measured baselines and explicitly unknown values.
2. Record actual answers and their dates. Do not manufacture numeric limits, scene sizes, sample counts, workloads or settings from this board authorization.
3. Assign whole sessions to enrollment, validation and held-out evaluation roles before model selection. If no settings or calibration are selected from the collected data, record that fact and leave validation unused. Agree how a baseline can fail a product target yet still produce a useful completed report.
4. Update the two declared READMEs with the accepted first-use case and limits. Keep later aspirational use cases separate.
5. Keep generated test artifacts out of the task board: root pytest discovery excludes `task_list/`, and ignore rules cover accidental test scripts, caches and job-allocation probe folders there.
6. Keep phone and survey bundle payloads outside Git, including source-manifest JSON. Record the approved offline retrieval method before acquisition and verify it can restore matching bundles from a fresh checkout.

## Invariants and recovery

invariants n/a: an owner decision record only. Existing frozen Task13 settings and earlier receipts remain unchanged. The draft constitution is not automatically ratified.

## Hyperparameters

hyperparameters n/a: no experiment. This task records owner choices; each execution task must audit and declare its inherited or owner-confirmed settings before it starts.

## Verification

The decision table has an explicit owner answer, unit and date for each required acceptance field. There are 0 silently assumed limits. A missing answer is marked pending and blocks the affected acceptance run. The first hardware/workload and independent test partition are explicitly named. `pytest.ini` excludes `task_list/`; `git check-ignore` confirms that pytest test files, `conftest.py`, pytest caches and `job_alloc_probe_*/` are ignored. It also confirms that phone/reference JSON manifests and binary payloads under `data/controlled_scene/input/` stay out of Git.

Before starting HIGH work, refine exact scope, audit settings, run task-plan lint and obtain a fresh plan review against current sources. No implementation or acquisition is performed while writing this plan.

## Receipts

| Field | Value |
|---|---|
| Closing commit | Not started |
| Files changed | `.gitignore`, `pytest.ini`, project/capture/task-board READMEs, and this task record; owner acceptance decisions remain open |
| Test status | No software tests run for this decision record. The named `job_alloc_probe_8a3c20c6f86a49cfaeb1d62343ac0cfb` folder was absent. A recursive scan found no Python/pytest files, caches or probe directories under `task_list/`; only task Markdown, `README.md`, `CONSTITUTION.md` and the journal were present. `git check-ignore` covers arbitrary `.py` files, pytest cache/folder names and job-allocation probes; pytest discovery excludes `task_list/`. Xiaomi's official guide identifies model 2201116TG as Redmi Note 11 Pro, and Google's current ARCore list marks Redmi Note 11 Pro as supporting Depth API; these sources support an on-device trial, not a runtime result. The Task51 plan lint, board lint and documentation diff check pass. The Task52 APK verification record and actual file hashes match for package `org.fyld.capturecheck`; installation and capture remain unverified. The latest read-only WSL check reports no attached ADB devices, no cached ARCore Gradle dependency, and no emulator or AVD; USB passthrough also shows no Android phone. |
| Before measurement | 0 owner-agreed complete-system acceptance records |
| After measurement | Not measured |
| Delta | Not measured |
| Decision-gate outcome | Open; owner decisions pending |

still open because the owner has not yet recorded the acceptance choices.

tests n/a: this hygiene change only updates ignore/discovery configuration and the task-board instructions; its checks inspect those settings directly.
