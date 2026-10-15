# Task board

## Current position, 15 October 2026

The phone captures; this PC receives, stores and processes. Running inference on the phone comes later inside the same app (owner, 14 October). The immediate goal is to compare reconstructions on the **same walk**, before scoring dimensions or choosing a more realistic display. CPU only. Deployable methods must be live or update at least once per second; offline methods remain labelled references.

FYLD capture 1.2 replaces phonecheck and rawrecorder. The Redmi completed `20261014_220756_walk`: 1,194 frames over 39.88 s, 29.92 fps, zero reported drops or missing/duplicated frame numbers, motion sensors at 423.54 Hz, 10.22 MB/s received and 225 MB stored. CPU replay produced 63 updates at 1.58/s, with no gap over one second. These are Task99 results, not independently measured geometric accuracy or a sustained device test.

The owner judged the reconstructed geometry poor. Task100's interactive Gaussian viewer displays that surface with height colours; it is not photographic Gaussian training. The owner also reported sideways reference photos. The sensor mounting angle is recorded as 90 degrees, and the native JPEG reaches both the viewer and depth model without a display rotation. Whether this harms depth is **untested**. Task102 checks it first, with geometric conventions kept consistent.

Known input gaps: 17 images without matched ARCore records, one final image without Camera2 settings, and no anchor-0 creation record. There are 44 new raw-depth maps, but the 63 replay updates used tracked-point scale 33 times and previous scale 30 times, never raw-depth scale. Export and clock checks wrote outputs but returned status 1 for missing settings. The estimated -2.67 ms clock offset is not independent calibration. No 60 s rest, target video or approximately 3-hour calibration rest has arrived.

Evidence: [capture results](../experiments/01_camera_capture_delivery/README.md#completed-redmi-session-task99), [live processing](../src/live/README.md), [open tracker/calibration results](../experiments/open_vio/README.md), [deployment index](../mobile_deployments/README.md), [Task99](done/99_fix_redmi_frame_json_crash_and_publish_a_timestamp.md), [Task100](done/100_build_offline_gaussian_splat_html_viewer_for_the_r.md).

## Next execution sequence

This is the proposed technical order from the 15 October review, not an owner-ratified set of experimental settings or product limits. One task may be in progress. Missing physical runs stay explicit; a software handover cannot claim they happened. Move to the next unblocked task after finishing bounded work rather than holding the active slot indefinitely.

| Order | Task | Direct output | Start condition / completion boundary |
|---|---|---|---|
| 1 | **102** — [Diagnose the Redmi reconstruction](open/102_diagnose_the_redmi_reconstruction_on_the_same_reco.md) | Orientation control first; then raw-depth versus learned-depth, scale, pose and anchor/fusion controls on identical frames | Existing walk available. Tighten frames/settings and tests before code. Report causes supported by controls, not a promised visual improvement. |
| 2 | **68** — [Include all maintained tests](open/68_add_the_depth_and_area_tests_to_the_default_test_r.md) | Matching default test lists and an omission regression check | Verified: 28 maintained test folders; pytest omits 10 and the runner 11. Close this before broad capture/tracker changes rely on the default check. |
| 3 | **52** — [Finish capture metadata and sustained checks](open/52_build_and_verify_a_usable_phone_recording.md) | Stop/result and anchor completeness, explicit missing ARCore matches, new walk/rest and queue/resource report | Reuse capture 1.2 and v2; tests first. New handset evidence needs owner coordination, not USB. The 60 s rest is not the calibration noise run. |
| 4 | **74** — [Compare remaining CPU 3D models](open/74_compare_feed_forward_3d_models_that_output_camera_.md) | Same-walk candidate depth/camera comparison against the corrected baseline | After Task102. Task80 already tested DA3 Small on TUM/ICL. Future-frame batches are offline diagnostics. |
| 5 | **103** — [Measure Redmi calibration](open/103_measure_redmi_camera_and_imu_calibration_from_owne.md) | Camera/IMU transform, time offset and noise with convergence evidence | Task52 plus owner target video, measured tag and approximately 3-hour rest. Reuse Task90 tools. |
| 6 | **104** — [Compare open trackers on the same walk](open/104_compare_open_trackers_and_surfaces_on_the_same_red.md) | Calibrated VIO/image-only path and fixed-depth surface comparison, failures and CPU cost | After Tasks52, 102 and 103. Reuse Tasks84/91 runners. ARCore/COLMAP disagreement is not independent accuracy. |
| 7 | **75** — [Measure physical ARCore error](open/75_measure_arcore_camera_path_accuracy_on_the_redmi.md) | Three marked loops with tape-distance errors, tracking loss and same-frame offline comparison | Task52 and owner access to measured routes. Task92 built the guide/scorer; capture already has ARCore and the notice. |
| 8 | **61** — [Resolve remaining acceptance/reference choices](open/61_agree_field_acceptance_limits_and_the_phone_proces.md) | Dated owner decisions or explicit pending items, with consumers named | Resolve relevant choices when needed; this is not a gate on Task102. Capture-first, PC processing and CPU-only are already decided. |
| 9 | **53** — [Collect independent references](open/53_collect_independent_scene_measurements_and_object_.md) | Sealed survey/inventory bank, private recovery and whole-session roles | Tasks52 and 61. The inspected house walk is development data, not a blind held-out test after tuning. |
| 10 | **56** — [Benchmark the complete walkthrough](open/56_benchmark_complete_walkthrough_accuracy_time_and_m.md) | Same-session measurement/count errors, complete timing and peak memory | Tasks52, 53 and 61, with frozen methods from comparison work. Reuse existing runners. |

Tasks103/75 need physical input; their position does not prevent other unblocked work. Task61 decisions may be resolved earlier whenever a consumer needs them. Product accuracy remains unproven until independent references exist.

## Review of every previously open task

| Task | Disposition | Evidence and amendment |
|---|---|---|
| 25 | [Stale](stale/25_compare_feature_seeded_odometry_and_verified_camer.md) | Reopen only for a residual path/revisit failure after Tasks102/75; compare existing ARCore corrections and live trackers first. |
| 36 | [Stale](stale/36_compare_surface_representations_and_visual_realism.md) | Task100 supplies display splats. Photographic training and representation comparisons follow a specific question from Task102. |
| 51 | [Archived, superseded](archive/51_agree_success_criteria_and_the_first_deployment_ta.md) | Mapping and six-stage integration/reporting exist in Tasks55/58/59/64, with later capture/replay. Pending field decisions belong to Task61. No new accuracy completion claimed. |
| 52 | Open, narrowed | Recorder/receiver built. Own fidelity gaps, sustained checks and short rest; remove the claim that no images or ARCore exist. |
| 53 | Open, blocked | Keep independent survey/identity separation. Task61 owns decisions; require fresh held-out sessions. |
| 56 | Open, blocked | Keep complete-system scoring. Recognise real replay and mapping; the current walk is not an accuracy test. |
| 57 | [Stale](stale/57_deploy_and_measure_the_useful_edge_workload.md) | On-phone processing deferred by the owner. Capture resource checks move to Task52. Future port and pinned-container rebuild remain documented. |
| 61 | Open, narrowed | Record settled capture/processing choices; retain unresolved survey, reference, retention and numeric acceptance decisions. |
| 63 | [Stale](stale/63_add_scaled_zipdepth_and_gpu_detector_choices_to_th.md) | CPU adapter exists; GPU extension outside scope. Preserve 1.13 processing fps and 0.77 complete fps separately. |
| 68 | Open, expanded, HIGH | Ten/eleven missing test folders, not just two. `src/live` appears only in pytest's default list. |
| 73 | [Stale](stale/73_make_a_stereo_headset_video_from_a_recording_witho.md) | Headset video is a separate later output. Task100 is not stereo-video completion; retain H.264 rule. |
| 74 | Open, rescoped | Task80 already tested DA3 Small. Compare remaining CPU modes on the Redmi; remove completed Task67 blocker. |
| 75 | Open, updated | ARCore recording and scorer exist. Retain physical trials and same-frame comparison; remove alternative logger/app work. |

Thirteen previously open tasks were reviewed. Six leave the active backlog (five deferred, one superseded); seven remain amended. Three missing follow-ups were filed as Tasks102-104. After Task101 closes, ten tasks remain open. No task was marked done merely because its plan was old.

## Review of previously stale tasks

| Task | Disposition and re-entry condition |
|---|---|
| [23](archive/23_embed_interactive_surface_review_and_explain_depth.md) | Archive as superseded by Tasks100/64 controls and reports. Remaining embedded stage-mask details need a specific review use case. |
| [31](stale/31_compare_provisional_object_ids_and_duplicate_relationships.md) | Keep stale. Task46 fixed the original defect; Task93's overcounts need geometry controls and independent references before an identity-schema change. |
| [33](stale/33_compare_object_appearance_context_and_spatial_association.md) | Keep stale. Reopen appearance/context matching only for a residual independently scored failure. |
| [34](stale/34_evaluate_segmentation_for_position_and_observed_dimensions.md) | Keep stale. Oracle-box COCO/classical-mask work does not establish site geometry or phone suitability. |
| [35](stale/35_measure_error_propagation_and_sequential_fusion.md) | Keep stale. Task102 owns immediate causal diagnosis; Task56 owns inherited-error reporting. |
| [76](archive/76_read_saved_sfm_camera_paths_and_points_into_the_wa.md), [77](archive/77_reorder_the_walkthrough_so_camera_tracking_comes_b.md) | Archive as absorbed by Task89, with v2 replay in Tasks96/99. New v2 COLMAP adaptation belongs to Task102/74. |

Earlier plans/receipts remain labelled historical. Re-entry requires fresh scope/evidence, not automatic execution of old pending-review or approval wording.

## Completed results and follow-up ownership

| Records | Bounded result | Remaining owner |
|---|---|---|
| Tasks54/62/65/70 | Depth comparisons, temporal scale diagnosis, standard trajectory scores | Tasks102/74 Redmi comparisons; Task57 eventual phone timing |
| Tasks55/58/59/64 | Mapping, six-step runner, replaceable contracts, visual reports | Task56 complete independent scoring |
| Tasks67/71/72/78/79/80 | SfM and supplied-pose/depth/scale controls; Prompt/DA3 results | Tasks102/74; negative results remain results |
| Tasks81/82/83/86 | Learning, SLAM research and ARCore/open-source terms notes | Consumer rechecks sources; no new research run here |
| Task84 | Live CPU image-only tracker trials on public data | Task104 Redmi comparison and conditional tracked-point export |
| Tasks85/87/88/94/95/96 | Phone probes, v1, raw recorder, capture-first handovers and unified v2 app | Task52 remaining checks; old install instructions are historical |
| Tasks89/93 | Live/replay processing and overcount logging | Task102 scatter diagnosis; Tasks53/56 independent inventory and justified matching correction |
| Task90 | Calibration tooling verified on TUM-VI | Task103 actual Redmi calibration |
| Task91 | Four VIO runners tested on TUM-VI | Task104 Redmi runs; Task57 later port |
| Task92 | Field guide/scorer and ARCore notice | Task75 measured walks; Task61 acceptance choices |
| Tasks97/98/99 | Crash diagnostics, deployment consolidation, capture 1.2 fix and completed session checks | Task52 fidelity/sustained checks; Task103 calibration; AVD remains proposed, uninstalled |
| Task100 | Offline surface-derived Gaussian HTML | Task102 geometry diagnosis; Task36 later photographic/representation work |

Older [closed records](closed/) and [archived records](archive/) remain history, including Task60's 7 October pruning. Completion proves bounded work, not all product goals. The old order and its zero-image/undecided-host assumptions are superseded.

## Workflow and validation

- `open/` holds actionable plans and named dependencies; only one may be `in_progress`. `done/` holds current CLI completions; `closed/` historical receipts; `stale/` deferred plans; `archive/` superseded plans.
- Use `task.js begin`, `files add` and `finish` for current work; the CLI writes its active record. Board migration uses the move command. This review amends older plans at the owner's request, not its own completion record.
- Legacy `task.js lint` and `ready --next` omit `done/`. Their success is partial validation and can falsely warn about superseding IDs in that folder. This review additionally checks every folder, unique IDs, states, dependency targets/cycles, queue coverage, links and the active slot. Historical records use the CLI's line-based frontmatter parser; seven have unquoted colon-bearing values that a strict YAML loader rejects. Amended open plans are checked as YAML; historical receipts are preserved. Harness changes are outside scope.
- Tighten files/settings and write tests before implementation. Historical review PASS is not current validation after rescoping. Settings are proposed by Claude, not owner-ruled. CPU only; long runs use one background START/END queue and completion notification.
- Use `python -B tools/check.py <explicit suites>` until Task68 fixes the default lists. Scratch belongs in OS temporary storage; no `.test_*`, `.pytest-tmp` or `.ruff_cache` in the repo. Task-board records/metadata only, no scripts or payloads.
- Household recordings, photos, APK binaries and derived outputs stay local and ignored. Identify the APK through [mobile_deployments](../mobile_deployments/README.md). Port 8766 is LAN only, without authentication/encryption; internet access needs a tunnel and authentication and is outside scope. Port 8765 stays reserved for v1.

Review record: [Task101](done/101_reconcile_the_task_board_with_capture_and_reconstr.md). Planned tasks are checked for consistency with evidence, not executed or scientifically accepted by this review.
