# Shared implementation

The canonical [walkthrough runner](walkthrough/README.md) calls six ordered steps: capture/input validation, depth, camera tracking, surface reconstruction, mapping/dimensions/area, and object recognition/distinct counting. Segmentation and appearance are optional and disabled by default. [Task58](../task_list/closed/58_organise_six_step_walkthrough_orchestration.md) records the extraction inventory and software checks.

Each method remains independently usable within its [experiment](../experiments/README.md). Error analysis is imported through each experiment's dedicated validation area after predictions are saved. Reusable records, mathematics and run exports remain in [experiments/shared](../experiments/shared/README.md). The root runner coordinates these pieces. It does not duplicate them.

Task58 is an organisation task with software checks. Real depth and site measurements remain explicitly unavailable until Tasks54/55 supply them. A failed or partial run retains all six statuses and cannot publish complete predictions. The independently measured complete walkthrough remains Task56 work. Earlier five-layer diagrams group reconstruction and mapping together; the runner executes them separately.

The earlier package is preserved in [the Task 00 archive](../archive/task00_prototype/README.md). It is evidence and potential source material, not a validated foundation for the new experiments.
