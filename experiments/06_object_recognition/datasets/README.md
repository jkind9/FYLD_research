# Recorded object reference inputs

Task17 prepares six original RGB-D views from TUM Freiburg1 desk: timestamps 1305031454.127701, 1305031457.091655, 1305031463.059810, 1305031466.095840, 1305031467.627532 and 1305031472.795640. The [frozen annotation file](desk_smoke_v1.json) contains source paths/hashes, calibration, partitions, reference IDs and scenario evidence.

The same white cup appears before and after the camera looks away. Frame268 at 1305031463.059810 contains no cup pixels. Two nearby black/silver monitor enclosures have separate reference identities. Cup coverage is complete on these six frames; monitors are a non-exhaustive subset. Their IDs were drawn from original RGB inspection, without reading detector outputs. A fresh agent independently checked identity and visibility. This is not human ground truth. Coarse polygon supports are provisional and excluded from formal segmentation scoring.

Two pre-gap frames are enrollment; four later frames are evaluation; validation is empty. These already inspected views support a within-session smoke control, with no tuning, blind accuracy or new-object/session generalisation claim. Image derivatives must remain in their parent frame's partition. A camera look-away does not establish that an object is absent from the scene.

## Prepare and inspect

Use the existing Python environment and pinned dependencies in `experiments/shared/requirements.txt`. No model, inference or download is required.

```powershell
python -B -m experiments.06_object_recognition.datasets.prepare
python -B -m experiments.06_object_recognition.datasets.prepare --verify
python -B tools/check.py experiments/06_object_recognition/shared/tests experiments/06_object_recognition/datasets/tests
```

[Open the prepared reference review](../../../data/object_revisits/desk_smoke_v1/review.html). `publication.json` seals source copies, separate method inputs, evaluator annotations, masks and overlays with SHA256. Preparation validates source hashes/dimensions, writes a fresh staging directory, checks artifacts, then renames it. Existing destinations are refused. A failed staging directory remains unpublished for inspection; restart uses a new destination. Verification rejects missing, extra or changed artifacts and rechecks original sources. There is no resume or overwrite.

Method inputs exclude identities, labels, masks, annotation provenance, revisit answers and reference-pose metadata. Evaluator annotations stay separate. Supplied camera poses may be loaded only in a named reference-pose control; estimated-pose methods must not consume groundtruth.txt.

## Offline source handoff

A fresh checkout requires the already acquired source payload. Copy the RGB/depth files and rgb.txt, depth.txt and groundtruth.txt named in the frozen annotation file to `data/tum/rgbd_dataset_freiburg1_desk/rgbd_dataset_freiburg1_desk/`. Preserve the sibling `EXTRACTION.json` from the acquired project for archive provenance. The original archive was checked against local SHA256 `e983d6830916e66dc4a46a71368046b149b283de87769690e7aa4e0b9483530c`; the publisher supplies no checksum. Preparation verifies each frozen source SHA256 and fails on unavailable or changed files. It does not fetch data implicitly. See [source acquisition records](../../../data/README.md) for attribution and original format.

Raw registered depth is unsigned16 PNG, divided by5000 for metres; zero means missing. Preserve raw bytes. The existing processed-depth adapter excludes values at or beyond4metres. This distinction is recorded in the manifest. No hole filling is used. Calibration is 640x480, focal lengths525, centre319.5/239.5, camera axes right/down/forward; RGB/depth pairing tolerance is0.02seconds.

## Recorded gaps

The 13-case registry marks cup return, distinct monitors, viewpoint, uncontrolled background change, partial occlusion and depth holes present. Scene absence and full-occlusion recovery are unusable. Controlled object rotation, lighting change, relocation, origin reset and phone capture are absent. These require separately acquired recordings before broad robustness claims. Synthetic invalid-input/reset controls can check software behavior but cannot supply that footage. Task13 remains unfinished with its frozen tracking settings; this preparation does not run it.

## Independent reference follow-up

[Task40](../../../task_list/open/40_plan_independent_references_and_hard_case_acquisition.md) owns shared reference and missing-capture design. It preserves this provisional six-frame publication. Human-checked pixel masks, surveyed physical anchors/visible surfaces/full dimensions, instrument uncertainty and new-session hard cases require separate acquisition/authorisation. Identical-looking objects seen only in separate views need independent identity evidence or an explicitly ambiguous reference, rather than guessed labels.

Retain camera/calibration/timestamp/world/revision and depth-measurement lineage. Session-disjoint validation/calibration and held-out evaluation must keep nearby frames/derivatives together. Task13's desk hold-out is already inspected by this object stream, so it cannot be called an independent end-to-end hold-out across these components. Frozen camera settings remain unchanged.
