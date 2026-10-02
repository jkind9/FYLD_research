# Task 00 prototype: preserved evidence

The first implementation combined supplied colour/depth observations, camera tracking, point-cloud fusion and map projection. The objective changed to five independently tested pieces. This snapshot preserves the prototype without making it the active shared implementation.

## What is retained

- `src/`, `scripts/`, `tests/`, the two entry scripts and package configuration contain the first implementation.
- `outputs/` retains the supplied-pose, estimated-pose and sparse image-only results.
- `environments/` retains the measured software/hardware snapshot.
- `docs/` retains the earlier architecture and future deployment proposals.
- `.github/` retains the old prototype test workflow; it is not active CI for the new experiments.
- [inventory.json](inventory.json) records old paths, current archive paths, byte counts and SHA256 hashes for moved first-party source, documents and result artifacts, excluding Python bytecode and test-session temporary files.

Input data remains under the repository's [data folder](../../data/README.md). Reference repositories remain under root `third_party/`. Existing virtual environments remain at their original paths because moving them breaks their installed paths.

An interrupted attempt to move the COLMAP checkout left a partial recovery copy under this archive's ignored `third_party/` directory. All copied files were restored to the original checkout, and both root reference checkouts verified clean at their pinned revisions. The recovery copy is retained because moving its protected metadata was denied. It is not another active reference repository.

## Preliminary evidence

The supplied-pose colour/depth run used 120 TUM observations. Its near-zero trajectory disagreement follows from supplying reference poses; it does not demonstrate successful tracking.

The estimated-pose run accepted 120 observations and measured approximately 0.02315 m trajectory error after rigid alignment. These results predate the final review fixes and were not repeated after every change.

The separate pycolmap CPU run registered 120 images in its largest component, exported 8,217 sparse points and measured 0.7854 pixel mean reprojection error in 172.32 seconds. Its scale is arbitrary. Image consistency is not a measurement of physical surface accuracy.

Twenty-six tests passed before the review fixes. Additional targeted tests were added later, but final suite validation, >=80% coverage, installed-package setup verification and fresh-context review of the finished implementation remained incomplete.

## Using this snapshot

The archive is not promised to run unchanged from its new location. Entry scripts, virtual environments and manifests can contain original paths. Consult [Task 00's receipts](../../task_list/archive/00_finish_and_validate_the_phase_1_scene_mapping_prot.md) and [the new plans](../../experiments/README.md).

Copy or adapt only the component needed by a named experiment. Preserve its provenance, write independent contract tests and record new measurements. Old result artifacts must not be relabelled as results from the new implementation.
