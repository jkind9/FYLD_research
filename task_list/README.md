# Task board

## Objectives and current position, 6 October 2026

A phone walkthrough should give useful site measurements and count each physical object once, including after a revisit. Three goals govern the work.

| Goal | What we must prove | Current evidence |
|---|---|---|
| Accuracy | Dimensions, defined area and object counts agree with independent measurements on separate test recordings. Missing coverage and uncertain answers stay visible. | Short camera/surface controls and object demonstrations exist. No complete phone/worksite test, independent final count or implemented site-area calculation. |
| Latency | A representative walkthrough produces usable outputs within an agreed wait; live checks update at an agreed rate. | Desktop component timings exist. No measured complete-process budget or accepted maximum wait. |
| Edge deployment | The useful workload runs on the chosen phone or nearby computer, with acceptable sustained resource use and offline behaviour. | Redmi camera inventory was exported, with 0 captured images. No useful measurement/counting workload has been measured on the target device. |

[Task51](open/51_agree_success_criteria_and_the_first_deployment_ta.md) now owns the first software run: connect existing layers for prerecorded footage and its available references, use current model classes, and process on MasterPC with GPU available. The runner exports an offline visual index with method and source recorded for each stage view. This is pipeline integration, not deployment. The Redmi remains selected for later capture/live checks. Field acceptance limits, frame skipping, and resolution choices remain pending.

Hosted and edge processing are both in scope. Every hosted stage need not run on the phone. Task51 states what runs where and what the user can do without a network.

## Next experiment order and gaps

This is the current order. It replaces the earlier object-first queue and blanket deferral of edge work. One task may be active. Task58's organisation work is complete and verified with deterministic software controls. Task51's prerecorded pipeline scope is confirmed, its plan review passed, and its implementation is underway; product acceptance choices remain open. Task52's reader and export-validator engineering can use synthetic fixtures and the unchanged camera profile. Physical capture, survey and acceptance runs still need the selected device and later owner decisions.

Keep `task_list/` for task records, its README, constitution and journal only. Root pytest discovery skips this folder. `.gitignore` ignores every Python file, pytest cache, pytest folder and job-allocation probe there, so accidental scratch stays out of Git. `tools/check.py` stops before pytest when it finds any unexpected file or folder in the task board. It places pytest files under a temporary system folder and removes that folder on exit. Put one-off diagnostic files there too. Before handing off, check `git status --short --untracked-files=all` and scan `task_list/` for unexpected files.

The Task52 reader/export checks use fixture images and pass on this host. Its
current Camera2 sources also passed the cached WSL warm build, with the pinned
package and source hashes verified. No image from the Redmi has been validated.
ADB access, handset confirmation, installation and capture remain outstanding.
Scored capture also needs Task51 site and survey choices.

| Order | Task | Direct output | Start condition / completion boundary |
|---|---|---|---|
| 1 | **51** — [Build the first prerecorded walkthrough pipeline](open/51_agree_success_criteria_and_the_first_deployment_ta.md) | Use existing prerecorded data and available references, current classes, and MasterPC as local host. A TUM RGB input is the practical source recommendation. | Reuses Task58's runner. Field acceptance, frame stride and resolution remain pending; do not infer deployment or accuracy. |
| 2 | **13** — [Frozen camera tracking baseline](closed/13_validate_frozen_tracking_settings_on_full_developm.md) | The full xyz and desk runs are verified, and the fresh post-fix diff review found no reproducible defect. Desk is held out by sequence but comes from the same indoor sensor/site. | Two verified run manifests. This does not prove phone performance or product acceptance. |
| 3a | **58** - [Organise the six-step walkthrough runner](closed/58_organise_six_step_walkthrough_orchestration.md) | One root runner, small importable experiment components and independent validation imports. | Software implementation and reviews complete. Real depth/mapping and measured product acceptance remain separate work. |
| 3b | **59** - [Make walkthrough layers swappable](open/59_make_walkthrough_layers_swappable.md) | One method choice and written contract per layer; labelled recorded-reference controls; loading, frame and visual timing. | Active implementation. Real depth, mapping, complete accuracy and phone performance remain Tasks54-57. |
| 3b | **52** — [Build a usable phone recording](open/52_build_and_verify_a_usable_phone_recording.md) | Original images, calibration, clocks, hashes and explicit available/missing depth and motion data. | Reader/export engineering can proceed on fixtures using the unchanged camera profile. Physical capture needs handset access and the applicable Task51 decisions; scored capture uses Task53's surveyed scene. |
| 3c | **53** — [Collect independent measurements and identities](open/53_collect_independent_scene_measurements_and_object_.md) | Surveyed dimensions/area, human inventory, uncertainty and separate test-session roles. | After Task51. Survey before predictions; capture with Task52's verified recorder. Reuse Tasks40/41 design. |
| 3d | **57** — [Check the edge workload early](open/57_deploy_and_measure_the_useful_edge_workload.md) | Actual-device compatibility, offline startup and memory evidence. | After Task51; does not wait for the desktop benchmark. This checkpoint alone does not finish Task57. |
| 4a | **54** — [Implement real metric depth](open/54_implement_and_validate_real_metric_depth.md) | Method-produced distances, independent error/coverage, time and memory. | After Task51 for public-data controls; Tasks52/53 supply the phone comparison. Choose a usable route from evidence. |
| 4b | **55** — [Implement dimensions and area](open/55_implement_site_dimensions_and_area_measurement.md) | Known-shape tests, real units and observed/unknown coverage. | After Task51. Analytic controls can precede capture; Task56 owns measured-scene integration. |
| 5 | **56** — [Benchmark the complete walkthrough](open/56_benchmark_complete_walkthrough_accuracy_time_and_m.md) | Same-recording measurement/count errors, complete time, peak memory and a verdict against each goal. | Task58 runner is implemented; needs Task13 and Tasks52-55 results. Start with the simple existing counting method. References enter scoring only. |
| 6 | **57** — [Complete sustained edge deployment](open/57_deploy_and_measure_the_useful_edge_workload.md) | Deployed workload, comparable answers, sustained delay, memory, heat, battery use, offline operation and restart behaviour. | Uses Task56's frozen baseline and Task52's capture contract. Does not require every desktop target to pass. |

A completed baseline may fail a product target. Publish that result and the failing condition. Missing required input/reference evidence is a blocker, not a zero error.

Task58 completed the canonical six-step runner in src/walkthrough, small component extractions and dedicated experiment validation imports. Its CRITICAL priority makes code clarity and maintainability explicit completion requirements. Its software controls and independent reviews passed. It preserves independent experiment commands and the simple Task46 counting method. Missing depth and mapping methods remain explicit gaps for Tasks54/55.

Task56 consumes that runner with actual phone calibration/image grids and estimated inputs downstream. It extends the existing report for dimensions/area and missing count/depth measures. It cannot combine unrelated successful stage trials or create another orchestrator. Benchmark-only runners and historical reports remain intact.

## Improvements after the first complete baseline

Choose improvements from measured failures in Task56. They do not all have to finish before the first complete test.

| Existing owner | Purpose and current boundary |
|---|---|
| [09: inventory goal](open/09_evaluate_scene_object_recognition_and_persistent_counting.md) | Keeps distinct-count requirements and checked persistence. Task56 supplies complete-test evidence; no second orchestrator or identity store. |
| [25: camera correction](open/25_compare_feature_seeded_odometry_and_verified_camer.md) | Follows Task13 and existing protocol review if drift/revisits justify correction. Corrected positions must update dependent geometry. |
| [31: IDs and duplicates](open/31_compare_provisional_object_ids_and_duplicate_relationships.md) | Task46 fixed late births. Broader confirmation/schema work follows Task56 and existing review prerequisites. |
| [33: appearance](open/33_compare_object_appearance_context_and_spatial_association.md) | Add appearance if baseline mistakes justify its cost; retain a geometry-only comparison. |
| [34: masks](open/34_evaluate_segmentation_for_position_and_observed_dimensions.md) | Open, unrun. Existing mask helpers are not a completed Task34 trial. Follows Tasks31 and Task56 and recorded validation gates. |
| [35: error accumulation](open/35_measure_error_propagation_and_sequential_fusion.md) | Explain measured failures or test whether additional independent views help. Task13 no longer waits for Task35. |
| [23: review controls](open/23_embed_interactive_surface_review_and_explain_depth.md), [36: surface representations](open/36_compare_surface_representations_and_visual_realism.md), [39: later app](pending_review/39_record_future_3d_review_and_measurement_requirements.md) | Diagnostic/review work follows a demonstrated measurement or user need; visual output cannot substitute for accuracy. |

[49: support matching speed](pending_review/49_reduce_spatial_support_association_latency.md) is a finished experiment. Its timing record now explains the difference between Task48's earlier 80.049-second pass and Task49's 120.481-second paired-control median; the cause of that separate-run difference is unknown. The closing commit receipt is still missing, and physical accuracy is unknown. No further optimization is scheduled without evidence that the method's accuracy justifies its cost.

## Existing evidence and review work

Reviews retain their original scopes. Check specific component/source claims needed by the selected baseline; unrelated research approvals are not one blanket gate on every goal. Changed files require a fresh source snapshot.

| Task(s) | State and responsibility |
|---|---|
| [08: phone feasibility](pending_review/08_check_phone_capture_feasibility_alongside_reconstr.md) | Pending owner image export and Samsung availability. Inventory received, usable capture unproved. Task52 owns new recording work. |
| [16: recognition protocol](pending_review/16_research_segmentation_recognition_and_camera_corre.md) | Pending decisions/review. Previous trials do not approve unchosen comparisons; Task51 chooses the first workload. |
| [21: association](pending_review/21_associate_object_identities_with_geometry_and_appe.md), [22: replay](pending_review/22_build_recorded_video_camera_surface_and_inventory_.md) | Bounded supplied-pose trials pending review; no verified physical count. |
| [24: APK build](pending_review/24_recover_and_reproduce_android_apk_build_inside_cap.md) | Cached packaging verified; clean dependency/container follow-up pending. Smoke code does not deploy the workload. |
| [32: spatial support](pending_review/32_investigate_spatial_support_and_position_uncertainty.md), [47: fixes](pending_review/47_fix_task32_association_lint_findings.md), [48: comparison](pending_review/48_paired_validation_of_median_point_and_task32_suppo.md) | Pending review. Task48 is descriptive and far slower than median-point matching; no independent count/position truth. Optional candidate, not a first-baseline requirement. |
| [37: mobile platforms](pending_review/37_research_arcore_arkit_and_roomplan_mapping.md), [38: longer-range sources](pending_review/38_research_long_range_fusion_and_driving_evaluation.md), [42: phone APIs](pending_review/42_examine_the_arcore_toolkit_for_capture_depth_and_t.md) | Research awaiting validation/decisions. Tasks52/54/57 own actual capture, depth and deployment. |
| [40: reference plan](pending_review/40_plan_independent_references_and_hard_case_acquisition.md), [41: source inventory](pending_review/41_investigate_candidate_test_datasets_and_trial_exis.md) | Planning/research pending review. Task53 owns collection; completed research implies no acquired physical references. |
| [44: stage report](pending_review/44_build_a_per_stage_accuracy_log_for_end_to_end_runs.md), [45: detector placement](pending_review/45_measure_detection_position_error_in_cluttered_scen.md) | Infrastructure/detector evidence pending review. Task56 owns complete-run integration and missing report measures. |
| [49: component speed](pending_review/49_reduce_spatial_support_association_latency.md) | Experiment finished, pending review; 457 decisions preserved, no physical accuracy result. |
| [50: board alignment](closed/50_align_task_board_with_accuracy_latency_and_edge_de.md) | Closed documentation-only restructuring. Earlier dated review/snapshot handoff is preserved in its receipt; no experiment executed. |

Earlier immutable snapshots predate these plans and changed paths. Do not relaunch external review sessions automatically. Prepare a current snapshot if independent review is resumed. Device/scene access and numerical decisions are explicit inputs to Tasks51-53.

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

## Task workflow

- Task frontmatter and folder define state; at most one task is in progress.
- `open/` holds planned, blocked and active work. `pending_review/` holds completed scoped work or a named external handoff; an unrun experiment is not complete.
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

Next-task selection follows the bold numbers in the execution table. Start only when inputs and review requirements are met. Passing software tests alone do not prove research success.
