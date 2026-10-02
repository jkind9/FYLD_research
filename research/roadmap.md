# Research roadmap

The active plan is [six independent experiments](../experiments/README.md). The earlier integrated prototype is [archived](../archive/task00_prototype/README.md), with preliminary results and unfinished validation recorded. Its old sequential development order no longer governs this project.

| Piece | First independent input | Evidence before connecting it |
|---|---|---|
| Camera capture and delivery | Actual Samsung S23 and Redmi Note11Pro capture; recorded files for delivery controls | Accessible cameras, calibration and timing; original observations preserved through transfer |
| Stereo depth | Middlebury images, calibration and reference disparities | Depth/disparity error, valid coverage and compute cost; geometry conversion verified |
| Camera tracking | TUM colour/depth with held-out reference poses | Movement error, drift, failures and explicit segment handling |
| Reconstruction | Proposed ICL living-room depth and supplied poses, with a separate reference surface | Surface distance and observed coverage; no depth or tracker implementation required |
| Bird's-eye mapping | Analytic geometry with independently specified expected answers | Heights, boundaries, area definition, reference plane and unknown regions preserved |
| Object recognition and persistent counting | Checked detections/masks, reference depth/poses and independently labelled identities | Labels, duplicate/missed counts, incorrect merges and unresolved revisit associations reported separately |

The 2 October recommendation starts implementation with task 03's geometry contracts, then task 04's supplied-input reconstruction. Task 08 checks both phones alongside that work. Task 09 adds [recognition and inventory](../experiments/06_object_recognition/README.md): begin association controls with checked observations, then compare detector predictions and reconstructed geometry. Current datasets support geometry controls, but a labelled site-object/revisit benchmark remains missing. Scene/activity classification is separate from object identity.

The [dataset guide](../experiments/datasets/README.md) gives download status, permissions and format caveats. The [reading guide](sources/README.md) gives the source background. Depth, tracking, reconstruction and map projection can be investigated before phone capture succeeds.

Connect pieces by replacing one reference input at a time. Use matching observations for the comparison: the TUM starter cannot supply stereo pairs, so a stereo-to-tracking integration test needs a different verified sequence. Execution on the phone or backend remains a separate measured choice.

Agree numeric acceptance limits from the intended work-area and inventory decisions before trials. Benchmark performance prepares the software for a site test; it does not establish site accuracy or safe clearance. Multi-session identity, activity labels and hosting remain later possibilities. Compare phone, local edge and backend placement without treating a component benchmark as combined-workload evidence.
