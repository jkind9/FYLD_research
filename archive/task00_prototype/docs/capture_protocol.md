# Phase 2: phone capture trial

The next experiment tests whether ordinary FYLD phone recordings can recover useful observed surfaces. The desktop sample supplies registered depth; ordinary phone video may supply only colour. Successful desktop RGB-D tracking does not establish phone-video feasibility.

## Collect safe, measurable examples

Agree the capture area and safe viewpoints with the site lead under the site's risk assessment. Stay outside exclusion zones. Never enter or lean over an excavation for a better view. Stop when movement would distract an operator or approach plant. Safety takes priority over complete coverage; missing surfaces remain unknown.

Record from several permitted positions with overlapping views and gradual motion. Include fixed textured surroundings as well as the target. A stationary pan offers little translation for image-only depth recovery. Avoid camera switching, digital zoom or stabilization changes during a take unless those changes are deliberately being tested. Keep the original media.

Measure independent reference distances and heights using an approved method from safe positions. Record method, uncertainty, endpoints and coordinate reference. Reserve some references for evaluation; references used to set scale cannot also serve as independent evidence of scale accuracy.

## Proposed trial matrix

These are initial trial sizes to agree with the site team, not acceptance thresholds. Start with 15–30 second takes, then 60–120 second takes to expose drift and heating. Use at least one ordinary Android phone and one iPhone; add depth-capable devices separately if available. Record exact model, operating system and camera settings.

| Condition | Controlled comparison | Evidence to retain |
|---|---|---|
| Textured, static, well lit | Reference take with deliberate overlap | Reference distances, coverage and tracking |
| Plain soil or concrete | Same route with few visible features | Failure location and unknown area |
| Wet or reflective surfaces | Dry/wet comparison only where safely available | Lighting, depth holes and reflection errors |
| Moving people or plant | Permitted observation from a protected position | Moving regions and false geometry |
| Occluded trench or assets | Several permitted viewpoints | Surfaces still hidden after capture |
| Low light | Existing safe lighting conditions | Exposure, noise and tracking loss |
| Blur or faster motion | Safe handheld variation on a clear route | Frame quality, gaps and accepted frames |
| Revisit | Return to an earlier viewpoint | Accumulated drift; current method has no loop closure |

Report failed takes alongside successful ones. Existing risk-assessment footage may lack translation, overlap, calibration or clear surfaces. Audit it before assuming it can be mapped.

## Capture manifest proposal

| Field group | Required meaning |
|---|---|
| Identity | Schema version, session ID, camera ID, frame index; chunk ID and sequence if chunked |
| Source | Original media name/hash, device model, OS, capture application version |
| Time | Capture Unix time, monotonic clock and units, clock origin/association; media presentation timestamp and timebase |
| Image | Stored width/height, orientation, crop, lens/camera selection, codec, nominal and measured frame rate |
| Calibration | Intrinsic matrix at stored resolution, distortion model/coefficients, treatment applied, calibration revision/source |
| Optional pose | Timestamp, transform direction, units, reference frame, tracking state and reset identifier |
| Optional inertial/depth | Separate timestamps, units, sensor calibration, depth kind and scale, image registration and validity/confidence encoding |
| Transfer receipt | Server receipt time, received bytes/hash and acknowledgement; kept separate from capture time |
| Reference/privacy | Measurement method/uncertainty, authorised use, access and retention decision |

Variable frame rate, dropped frames and duplicates must retain actual timestamps. Never derive time solely as `frame_index / nominal_fps`. Pose resets must start a new segment. A server clock cannot substitute for a camera timestamp.

A browser recorder is an RGB-only trial until capabilities are measured. Do not promise synchronized dual cameras, native motion-tracking poses or depth through a browser. A native app is a separate option: [ARCore Depth](https://developers.google.com/ar/develop/java/depth/quickstart) requires a supported device, and the [device list](https://developers.google.com/ar/devices) must be checked. Apple's [RoomPlan](https://developer.apple.com/augmented-reality/roomplan/) uses camera and LiDAR for room floor plans; its indoor representation is not evidence that it maps outdoor excavations.

Keep footage local for the first replay trial. Record consent and retention decisions before sharing identifiable people or sensitive site details. Proceed to a backend trial only when the capture manifest and independent references make results interpretable.
