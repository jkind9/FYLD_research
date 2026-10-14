# Stream A: measure the Redmi on real walks

Task92 prepared the v1 capture and scoring for Task75. There are no tape-measured phone results yet. The phonecheck APK is retired; current APKs are listed in the [deployment index](../../mobile_deployments/README.md). FYLD capture uses v2; the receiver commands and scoring steps below describe historical v1 sessions. The accuracy scorer still needs v2 support before applying this procedure to a new capture. Task61 owns the acceptance limits, so these scores do not label a walk as passing or failing.

## Install and receive

For a new recording, install FYLD capture from the deployment index and follow the [v2 capture instructions](README.md#the-capture-app-and-pc-receiver-task96-14-october-2026). It retains the **ARCore and privacy notice** button. Open it to check that the text scrolls and that the Google Privacy Policy link opens.

Start the host in the repository root:

```text
.venv-yolo\Scripts\python experiments/01_camera_capture_delivery/host/receiver.py --out outputs/field_accuracy/indoor-01 --sessions 1
```

Use the computer address printed by the receiver, on the same Wi-Fi as the phone. Press **Stream to computer**. Press **Stop streaming** after the walk. The receiver writes one session subfolder containing `session.json`, `frames.jsonl`, JPEGs and available raw depth. Keep that folder intact. A stream saved before Task87 has no versioned session header or depth and cannot be scored by this tool.

To measure host processing speed on the same walk, use this instead of the receiver command (both use port 8765):

```text
.venv-yolo\Scripts\python -m src.live.run --listen 8765 --out outputs/field_accuracy/indoor-01-live
```

After stopping the phone stream, wait for the host to finish and save the final surface and summary. Score the received session under `outputs/field_accuracy/indoor-01-live/sessions/<received-session>`, not the host's `updates.jsonl`: dropped processing updates must not remove poses from the tracking check. Object counts are still known to be too high; this task does not validate them.

## Set up independent measurements

1. Choose stations A, B and C. Mark a repeatable phone placement at each: the same rear camera centre, height and facing direction. A simple phone holder on fixed supports is better than judging the position by hand. Put a labelled card in view at each station so its stopped frames can be found later.
2. Measure the straight 3D distances A-B and A-C with a tape. These are distances between the camera placements, not from the camera to a printed card. Record tape uncertainty and how closely the phone can be replaced. A wall marker observed from different positions is not itself a camera-position reference.
3. Measure the route length along the planned loop independently. Use the sloping distance on stairs. The scorer uses this length only to express closure drift as a percentage; it never uses ARCore's estimated path to set scale.
4. Record at least three loops: one indoors, one including stairs, and one outdoors within Wi-Fi coverage. Return to station A with the camera at its original position and orientation. Keep camera height consistent on level ground. For stairs, record the vertical separation and a sloping tape distance between landings. Note lighting, surfaces, motion blur and any interruptions. Repeating the indoor loop three times will help separate placement error from tracking variation.
5. Start streaming before the first station. Wait for **TRACKING**, hold at A for a few seconds, walk through B and C, and finish with another hold at A. Keep the camera aimed at textured surroundings while walking. Stop only after the final hold. Keep a separate session and measurement file for each walk.

Do not infer station distances from ARCore, learned depth, or the reconstructed surface. Those are the outputs being tested. For each checkpoint, select one received frame from the middle of its stationary hold by opening the corresponding JPEG. `frames/000120.jpg` means sequence 120. Note the exact chosen sequence; the screen's frame count is not a sequence identifier.

## Write the measurements and score

Save a JSON file beside each session. The numbers below are an example, not measurements of the Redmi:

```json
{
  "walk": "indoor-01",
  "environment": "indoor",
  "notes": "Example only. Replace all sequences and tape distances after capture.",
  "tape_uncertainty_mm": 5,
  "placement_repeatability_mm": 10,
  "loop": {"start_seq": 120, "end_seq": 1800, "tape_length_m": 14.0},
  "distances": [
    {"name": "A-B", "from_seq": 120, "to_seq": 650, "tape_m": 3.1},
    {"name": "A-C", "from_seq": 120, "to_seq": 1100, "tape_m": 5.0}
  ]
}
```

```text
.venv-yolo\Scripts\python experiments/01_camera_capture_delivery/host/accuracy.py --session outputs/field_accuracy/indoor-01/<received-session> --measurements outputs/field_accuracy/indoor-01/measurements.json --out outputs/field_accuracy/indoor-01/scores.json
```

The scorer refuses missing or untracked checkpoints, reversed loop endpoints, repeated or decreasing timestamps/sequences, nonfinite poses, and nonpositive or nonfinite tape lengths. It preserves the measurements and session header, including any `control: reference` label from stand-in data. Such data does not establish phone accuracy.

| Output | Meaning |
|---|---|
| `loop.closure_mm` | Distance between the live camera positions at the two holds at A |
| `loop.closure_percent_of_tape_length` | Closure distance divided by the independently measured loop length, times 100 |
| `loop.turn_error_deg` | Rotation between the camera orientations at those holds; returning at a different angle contributes to this |
| `distances` | Each tape distance, estimated 3D distance, signed error in mm and absolute error in percent |
| `tracking.tracked_fraction` | Fraction of received frames with a pose within the chosen loop interval |
| `tracking.lost_events` | Transitions from tracking to no pose, within that interval |
| `tracking.failure_frames` | Received frames without a pose, grouped by ARCore failure reason |
| `tracking.missing_sequence_numbers`, `longest_received_gap_s` | Missing transmitted sequences and longest timestamp gap between received frames; tracking during a gap is unknown |
| `tracking.sampled_path_m` | Sum of distances between successive received tracked positions, excluding transitions across an untracked frame; a sampled path, not measured distance walked |
| `tracking.anchor_corrections` | Number of anchor pose updates received in the selected interval |

These are the camera poses logged live. No similarity alignment, scale fitting, smoothing or later anchor correction is applied. ARCore may revise its world coordinates during a walk; closure and station distances therefore include the effect of those changes. The anchor-correction count makes that limitation visible. It does not measure the displacement of a final corrected surface. Tracking loss between received frames is also unknown. Placement error and tape uncertainty must accompany the reported errors.

## What remains after capture

For each environment, report the distance errors, closure drift, tracking loss, received gaps and capture conditions. Run the saved session through `src.live.run --replay` if live processing was not measured during capture. Report surface/map error and object-count error separately when independent references exist.

Task75 also calls for Task67's offline COLMAP path on the same images. Its runner currently accepts TUM and ICL datasets, not phone sessions. Add that input adapter after the first measured capture. Reserve one measured distance for setting COLMAP's otherwise unknown scale and score on other distances; fitting scale to every test distance would hide the error. Do not substitute ARCore as the ground truth for that comparison. Task75 stays open for the real captures and comparison; Task61 stays open for acceptance limits.
