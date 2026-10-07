# Task board

## Objectives and current position, 7 October 2026

A phone walkthrough should give useful site measurements and count each physical object once, including after a revisit. Three goals govern the work, and the code should stay modular and easy to follow while we get there.

| Goal | What we must prove | Current evidence |
|---|---|---|
| Accuracy | Dimensions, defined area and object counts agree with independent measurements on separate test recordings. Missing coverage and uncertain answers stay visible. | Short camera/surface controls and object demonstrations exist. No real depth method, no site-area calculation, no complete phone/worksite test and no independently scored count. |
| Latency | A representative walkthrough produces usable outputs within an agreed wait; live checks update at an agreed rate. | Desktop component timings exist. No measured complete-process time and no agreed maximum wait. |
| Phone deployment | The useful workload runs on the phone with acceptable sustained resource use and offline behaviour. | Redmi camera inventory was exported, with 0 captured images. No measurement or counting workload has run on the phone. |

The owner ruled on 7 October 2026 that deployment must be on a phone. Development and accuracy checks stay on existing recorded data (TUM and similar) until phone work resumes. Calibration is only trustworthy when this project's own app records it per frame; a plain video from an unknown phone does not carry it. Whether the phone only records (with processing hosted) or also processes is still open and owned by [Task61](open/61_agree_field_acceptance_limits_and_the_phone_proces.md).

[Task51](open/51_agree_success_criteria_and_the_first_deployment_ta.md) owns the first software run: existing layers on prerecorded footage with its available references, current model classes, processed on MasterPC. It is pipeline integration, not deployment or accuracy. Field decisions that Task51 held before its 6 October rescope (site, objects, survey, storage, numeric limits, phone processing split) now belong to Task61.

## Board pruning, 7 October 2026

[Task60](open/60_prune_task_board_to_the_accuracy_latency_and_mobil.md) cut the board from 32 live tasks to 11 open ones. Finished pending-review work was closed with its commit receipts. The fixed-snapshot external validation those tasks were waiting for was waived, because those review sessions are not relaunched automatically; a source claim is rechecked by whichever task uses it. Optional object-identity and review refinements moved to `stale/` and return only when Task56 shows a measured failure they would fix.

## Next order

One task may be active. `task.js ready --next` follows the bold numbers below.

| Order | Task | Direct output | Start condition / completion boundary |
|---|---|---|---|
| 1 | **51** — [Build the first prerecorded walkthrough pipeline](open/51_agree_success_criteria_and_the_first_deployment_ta.md) | Six-layer run on a TUM recording with an offline visual index; method and source recorded for every view. | A software-control run completed on 7 October; the contract test is outstanding. Not deployment or accuracy evidence. |
| 2 | **54** — [Implement real metric depth](open/54_implement_and_validate_real_metric_depth.md) | Method-produced distances in metres, error and coverage against an independent reference, time and memory. | Can start now on recorded data. The route must have a path that runs on the phone (ARCore Depth API or a small converted model). The phone trial needs Tasks52/53. |
| 3 | **55** — [Implement dimensions and area](open/55_implement_site_dimensions_and_area_measurement.md) | Known-shape tests, real units and observed/unknown coverage. | Can start now. The field region definition comes from Task61 before Task56's physical comparison. |
| 4 | **61** — [Agree field acceptance limits and the phone processing split](open/61_agree_field_acceptance_limits_and_the_phone_proces.md) | Owner record of site, objects, survey, storage, numeric limits and what runs on the phone. | Owner decision; unanswered items stay pending and name the task they block. |
| 5 | **52** — [Build a usable phone recording](open/52_build_and_verify_a_usable_phone_recording.md) | Original images, calibration, clocks, hashes and explicit available/missing depth and motion data. | Reader/export software passes on fixtures and the APK builds. Physical capture waits until phone work resumes and needs handset access. |
| 6 | **53** — [Collect independent measurements and identities](open/53_collect_independent_scene_measurements_and_object_.md) | Surveyed dimensions/area, human inventory, uncertainty and separate test-session roles. | After Task61. Survey before predictions; capture with Task52's verified recorder. |
| 7 | **57** — [Check the phone workload early](open/57_deploy_and_measure_the_useful_edge_workload.md) | On-phone compatibility, offline start-up and memory evidence. | After Task61; does not wait for the desktop benchmark. Also owns the pinned-container APK rebuild moved from Task24. |
| 8 | **56** — [Benchmark the complete walkthrough](open/56_benchmark_complete_walkthrough_accuracy_time_and_m.md) | Same-recording measurement and count errors, complete time, peak memory and a verdict against each goal. | Needs Tasks52-55. Starts with the existing simple counting method. References enter scoring only. Now also the place where distinct counts are proven (Task09 archived). |
| 9 | **57** — [Complete sustained phone deployment](open/57_deploy_and_measure_the_useful_edge_workload.md) | Deployed workload, comparable answers, sustained delay, memory, heat, battery, offline use and restart behaviour. | Uses Task56's frozen baseline and Task52's capture contract. |

A completed baseline may fail a product target. Publish that result and the failing condition. Missing required input or reference evidence is a blocker, not a zero error.

Completed foundations: [Task13](closed/13_validate_frozen_tracking_settings_on_full_developm.md) froze the camera tracking baseline on full TUM xyz and desk runs. [Task58](closed/58_organise_six_step_walkthrough_orchestration.md) built the six-step runner in `src/walkthrough`, and [Task59](closed/59_make_walkthrough_layers_swappable.md) gave each layer one method choice and a written contract (805 full-suite tests passed). Task56 consumes that runner; it must not combine unrelated stage trials or add another orchestrator.

Keep `task_list/` for task records, its README, constitution and journal only. Root pytest discovery skips this folder. `.gitignore` ignores every Python file, pytest cache, pytest folder and job-allocation probe there. `tools/check.py` stops before pytest when it finds any unexpected file or folder in the task board. Put one-off diagnostic files in a temporary system folder. Before handing off, check `git status --short --untracked-files=all` and scan `task_list/` for unexpected files.

## Later, only if Task56 shows a need

| Task | Purpose | State |
|---|---|---|
| [25: camera drift correction](open/25_compare_feature_seeded_odometry_and_verified_camer.md) | Correct camera drift on revisits. Compare against ARCore's own tracking first if the phone route uses it. | Open, LOW, blocked by Task56 |
| [36: surface display and realism](open/36_compare_surface_representations_and_visual_realism.md) | Better 3D surfaces for the later 3D/VR review goal. A nicer display is not an accuracy result. | Open, LOW, blocked by Task56 |
| [23: viewer controls](stale/23_embed_interactive_surface_review_and_explain_depth.md) | Embedded surface viewer with pan/zoom and depth-mask counts. Partial work is committed; Task51's visual index covers per-stage review. | Stale |
| [31: provisional IDs and duplicates](stale/31_compare_provisional_object_ids_and_duplicate_relationships.md) | Identity history schema. Its motivating defect was fixed by Task46 (unresolved books 90 to 5). | Stale |
| [33: appearance and context matching](stale/33_compare_object_appearance_context_and_spatial_association.md) | Add appearance cues if geometry-only identity makes measured mistakes. | Stale |
| [34: classical masks](stale/34_evaluate_segmentation_for_position_and_observed_dimensions.md) | Rectangle, GrabCut and Canny masks on COCO with answer-key boxes. Cannot show site accuracy, and the methods are not phone candidates. | Stale |
| [35: error accumulation](stale/35_measure_error_propagation_and_sequential_fusion.md) | Explain how errors build up across stages and views. Task56's per-stage report already separates inherited error. | Stale |

## Closed or archived on 7 October 2026

| Task(s) | Outcome |
|---|---|
| [32](closed/32_investigate_spatial_support_and_position_uncertainty.md), [47](closed/47_fix_task32_association_lint_findings.md), [48](closed/48_paired_validation_of_median_point_and_task32_suppo.md), [49](closed/49_reduce_spatial_support_association_latency.md) | Matching objects by their whole depth-point region instead of one centre point, its fixes, a paired comparison and a speed-up. Code in `14957e6`. Far slower than centre-point matching; Task49 kept all 457 decisions and cut time by 1.83%. No independent position truth, so no accuracy claim. |
| [44](closed/44_build_a_per_stage_accuracy_log_for_end_to_end_runs.md), [45](closed/45_measure_detection_position_error_in_cluttered_scen.md) | Per-stage report (`c3bd9ef`) and detector placement error (`cf68ccc`). Remaining measures belong to Task56. |
| [21](closed/21_associate_object_identities_with_geometry_and_appe.md), [22](closed/22_build_recorded_video_camera_surface_and_inventory_.md) | Exploratory identity and replay trials on supplied camera poses (`8140ba0`). Historical evidence; no physical count. |
| [24](closed/24_recover_and_reproduce_android_apk_build_inside_cap.md) | APK warm build verified and reused by Task52. Container rebuild moved to Task57. |
| [16](closed/16_research_segmentation_recognition_and_camera_corre.md), [37](closed/37_research_arcore_arkit_and_roomplan_mapping.md), [38](closed/38_research_long_range_fusion_and_driving_evaluation.md), [39](closed/39_record_future_3d_review_and_measurement_requirements.md), [40](closed/40_plan_independent_references_and_hard_case_acquisition.md), [41](closed/41_investigate_candidate_test_datasets_and_trial_exis.md), [42](closed/42_examine_the_arcore_toolkit_for_capture_depth_and_t.md) | Research and plans kept as reference. Task53 executes Task40's reference design; Tasks52/54/57 own real phone checks. |
| [08](archive/08_check_phone_capture_feasibility_alongside_reconstr.md), [09](archive/09_evaluate_scene_object_recognition_and_persistent_counting.md) | Archived: superseded by Task52 (phone recording) and Task56 (proven counts). |

## Historical completed work

Closed tasks prove their bounded work, not completion of the three goals. Preserve their settings and receipts. The tracking baseline used 30 Freiburg1 xyz frames spanning 1.136 seconds; object demonstrations used supplied benchmark camera positions.

| Task | Historical state | Evidence and limits |
|---|---|---|
| [00: first prototype](archive/00_finish_and_validate_the_phase_1_scene_mapping_prot.md) | Superseded | Preliminary research/runs preserved; integrated validation unfinished |
| [01: experiment organisation](closed/01_organise_independent_scene_mapping_experiments.md) | Closed | Six independent boundaries and preserved prototype evidence |
| [02: standard references](closed/02_verify_standard_tracking_and_reconstruction_refere.md) | Closed | Acquired ICL depth/poses and independent surface; selected TUM desk |
| [03: geometry contracts](closed/03_define_observation_and_pose_contracts_with_known_g.md) | Closed | Known-coordinate control and source/stage exports |
| [04: supplied-input surface](closed/04_evaluate_reconstruction_with_supplied_depth_and_po.md) | Closed | Nine ICL views; 7.85 mm mean reference distance and 22.29% coverage within 5 cm |
| [05: tracking baseline](closed/05_evaluate_tracking_with_supplied_benchmark_depth.md) | Closed baseline | Thirty TUM observations; 6.93 mm camera-position error and 2.14 image pairs/s |
| [06: recovered research](closed/06_recover_interrupted_research_and_review_current_or.md) | Closed | Original research and source corrections preserved |
| [07: mobile mapping products](closed/07_review_mobile_stereo_mapping_products_against_the_.md) | Closed | Product evidence and map-rate/depth-rate limits separated |
| [10: repository publication](closed/10_prepare_research_repository_and_publish_initial_main.md) | Closed | Initial main snapshot and publication exclusions recorded |
| [11: geometry review](closed/11_explain_geometry_control_outputs_and_show_supplied.md) | Closed | Explained supplied-input/source-coordinate views |
| [12: folder separation](closed/12_separate_geometry_validation_from_camera_pose_esti.md) | Closed | Supplied-pose control separated from camera estimation |
| [13: frozen tracking baseline](closed/13_validate_frozen_tracking_settings_on_full_developm.md) | Closed | Full xyz and desk runs verified; desk is held out by sequence but from the same indoor sensor/site |
| [14: labelled 3D inspection](closed/14_add_labelled_3d_stage_inspection_and_camera_motion.md) | Closed | Camera/surface viewers with explicit observed/reference/result labels |
| [15: owner plan review](closed/15_prepare_recorded_video_recognition_plan_for_owner_.md) | Closed | Outline approved 3 October; later task-specific authorisations remain distinct |
| [17: provisional reference](closed/17_prepare_labelled_revisit_inputs_and_object_observa.md) | Closed | Six agent-reviewed desk frames; complete selected cup coverage, monitor positive subset; no human gold |
| [18: cached detection check](closed/18_evaluate_object_detection_on_frozen_labelled_obser.md) | Closed | Four of five cup references matched; monitor accuracy unscorable as full inventory |
| [19: classical mask control](closed/19_evaluate_classical_and_edge_device_object_segmenta.md) | Closed | 45 masks across 15 prompts; coordinate changes/costs, no demonstrated accuracy improvement |
| [20: appearance control](closed/20_compare_object_appearance_matching_across_viewpoin.md) | Closed | ZNCC and existing YOLO features tested; one wrong monitor ranking; ResNet50 untested |
| [26: standalone camera/surface](closed/26_export_self_contained_shareable_offline_viewers.md) | Closed | Portable offline viewers preserve supplied-input evidence |
| [27: xyz cup localisation](closed/27_localise_yolo_cup_detections_in_recorded_rgbd.md) | Closed | One YOLO26x detection projected with measured depth and supplied poses; separate from desk cup |
| [28: desk cup replay](closed/28_replay_cup_revisits_with_persistent_object_ids.md) | Closed | Sixty sampled desk frames; persistent cup ID across detector gap/return, not continuous physical absence |
| [29: portable replay and spread](closed/29_export_replay_and_review_reconstruction_and_identi.md) | Closed | All nineteen cup proposals exported; sixteen assigned box RMS 72.8 mm / centre RMS 82.3 mm; surface repeatability only |
| [30: documentation reconciliation](closed/30_reconcile_experimental_evidence_and_research_backl.md) | Closed | Evidence/source review complete; 226 local links/anchors checked and ten proposed follow-ups; no experiment started |
| [43: Shareable demo visualisations](closed/43_build_shareable_demo_visualisations_from_exported_.md) | Closed | Existing run assets; Seven offline pages; Task46 owns the corrected identity publication and rebuild. |
| [46: Fix late object births and regenerate the object demo](closed/46_fix_late_object_births_and_regenerate_the_object_d.md) | Closed | Same frozen 60-frame baseline; no independent accuracy claim; New same-class objects can start provisional IDs at any frame. Books: 90 to 5 unresolved, 1 to 6 IDs. All classes: 226 to 56 unresolved, 18 to 55 provisional IDs; seven pages rebuilt. Commit f16e8eb. |
| [50: board alignment](closed/50_align_task_board_with_accuracy_latency_and_edge_de.md) | Closed | Documentation-only restructuring around accuracy, latency and edge deployment; no experiment executed |
| [58: six-step runner](closed/58_organise_six_step_walkthrough_orchestration.md) | Closed | One root runner, small importable components and independent validation imports |
| [59: swappable layers](closed/59_make_walkthrough_layers_swappable.md) | Closed | One method choice and written contract per layer; 805 full-suite tests passed |

## Task workflow

- Task frontmatter and folder define state; at most one task is in progress.
- `open/` holds planned, blocked and active work. `pending_review/` holds completed scoped work with a named, actionable handoff; do not park work there waiting for a review nobody will run. `stale/` holds plans that are neither done nor wrong but not currently justified.
- `closed/` requires filled receipts and resolved or explicitly waived follow-ups. Do not rewrite old results when priorities change.
- Before HIGH/stateful code work: tighten scope, lint the plan, freeze settings, obtain fresh plan review and record its verdict.
- Before closing HIGH/stateful code: obtain the required independent finished-diff review. Tests check behaviour, boundaries and failures.
- Documentation belongs in README files; task files hold engineering traceability. The constitution remains an unratified draft.

```powershell
node C:/Users/jkind/.claude/task-system/task.js ready --next
node C:/Users/jkind/.claude/task-system/task.js list
node C:/Users/jkind/.claude/task-system/task.js lint
node C:/Users/jkind/.claude/task-system/task.js audit
```

Next-task selection follows the bold numbers in the "Next order" table. Start only when inputs and review requirements are met. Passing software tests alone do not prove research success.
