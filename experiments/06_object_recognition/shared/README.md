# Object observation contracts

These records keep original image evidence separate from the answers used to
score object recognition. They use the existing camera calibration and pose
records in `experiments/shared`.

`observations.ObjectObservation` is a frozen record keyed by source, session,
frame and observation identifiers. It copies pixel polygons, boxes, source
hashes and method provenance into immutable tuples. Pixel coordinates follow the
original calibrated image grid. Optional camera and world positions use metres.
Missing depth cannot supply a metric position. A world position needs an explicit
world, segment and pose revision. `validate_observations` rejects repeated keys.

`pose_revisions.PoseRevision` records a camera-to-world pose using the existing
`Pose` contract. Its key contains run, world, segment, frame and revision. Each
frame origin has one root revision. Parents must be present in the same run,
world, segment and frame; cycles are rejected by `validate_pose_revisions`.
Provenance and source hashes belong to each revision. This contract does not
publish rebuilt geometry or change the identity database.

`manifest.validate_manifest(manifest, repo, verify_sources=True)` validates the
desk reference schema version 1. It checks original file hashes, safe paths,
calibrated colour/depth dimensions, unsigned 16-bit raw depth, the inherited
depth policy, pixel supports, category consistency, partitions and revisit
evidence. Metadata source hashes are checked too. `verify_sources=False` checks
the record structure without reading source images; it still rejects unsafe paths.

`manifest.method_inputs(manifest)` returns a separate copy through an explicit
field list. It contains calibration, depth policy and frame capture information.
Labels, coverage, source metadata, annotation provenance, scenario evidence,
semantic visit names and revisit links remain evaluator-only. Enrollment and
evaluation partitions identify which frames can populate the reference gallery.
Consumers should validate the full manifest before projecting method inputs.

The source annotation is a provisional, agent-reviewed recording from one desk
session. Its coarse masks do not establish segmentation accuracy or performance
on unseen sessions. See the datasets README for preparation and offline handoff.
