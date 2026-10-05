# Demo pages

Seven single-file web pages that explain the project visually. Each one opens in a normal browser, works offline and can be emailed or shared on its own. They reuse saved detections, measured depth and camera poses. On 5 October, Task46 recomputed object identities on the CPU to allow new objects at any frame; it repeated no detector, depth or pose inference.

Start with `00_overview.html`. Every page links to the others.

| Page | What it shows | Layer | Size |
|---|---|---|---|
| `00_overview.html` | The problem, the five layers, results so far and a card for each page | All | 0.2 MB |
| `01_depth_to_3d.html` | One desk frame as colour, depth and missing depth, then the same pixels as 3D points you can turn around | 2 · Depth | 1.2 MB |
| `02_camera_tracking.html` | Our tracker's camera path next to the motion-capture path, with the error at each frame (6.9 mm typical) | 3 · Camera position | 0.8 MB |
| `03_surface_accuracy.html` | A synthetic room built from 9 views, each point coloured by its distance to an independent reference model (7.8 mm mean), with the reference model as an overlay | 4 · Environment | 6.8 MB |
| `04_gaussian_splats.html` | The recorded desk as the existing 20,000-point cloud, as merged depth points and as 269,645 Gaussian splats, with a "view from the real camera" comparison and a `.ply` download | 4 · Environment | 5.2 MB |
| `05_birds_eye_map.html` | A top-down colour and height map of the desk with seen and unknown areas, a hover height readout and a two-click measuring tool | 4 · Environment | 0.2 MB |
| `06_objects_in_3d.html` | A 60-frame timeline: detection boxes, provisional identities in 3D, late object arrivals, cup return and remaining unassigned detections | 5 · Objects | 4.1 MB |

## What to say about them

- **Measured results:** the camera path (page 2) and the room surface (page 3) are scored against independent references. The cup position spread (page 6) is a repeatability figure, not error against a true position.
- **Illustrations:** the Gaussian splats (page 4) and the bird's-eye map (page 5) are built from the same measured desk depth. They have no independent reference, so their sizes and distances are not measured results.
- **The splats are not trained.** Each one comes directly from merged depth: one soft flat disc per 0.8 cm cell, lying along the local surface. Full Gaussian splatting goes further and optimises every splat on a GPU until rendered views match the photos. That step was not run. The page explains this.
- All data is from public indoor recordings (TUM RGB-D and ICL-NUIM) on a desktop computer. Nothing here is from a phone or a worksite yet.

## Late object arrivals, 5 October 2026

New same-class objects may now start provisional identities at any frame when they have a valid position and no feasible existing match. Existing identities still match one-to-one. Near-tied matches, missing depth and boxes competing for an already assigned identity remain unassigned.

On the same 60 frames and 457 detections, the corrected policy retains 55 provisional identities instead of 18; unresolved detections fall from 226 to 56. For the 95 book detections, it retains six identities instead of one; unresolved books fall from 90 to five. Those five comprise one ambiguous match and four competing boxes. The remaining overall unresolved cases are 37 ambiguous, ten without position and nine competing boxes.

These counts describe the policy, not the real inventory. Geometry noise can still create duplicate identities. The cup's frame104 and frame359 detections retain their earlier ID, but another shifted cup detection starts a second provisional candidate. The displayed 72.8 mm spread still refers to the historical sixteen assigned cup observations. Task32's next comparison will use the 3D samples throughout each box; segmentation comparisons follow that baseline.

## Rebuilding them

The generated HTML pages and this README are tracked for sharing. The large source runs and datasets remain local. Rebuild from a checkout containing those assets:

```powershell
python -B -m tools.demos.build --source-root .
```

The builder defaults to the verified corrected identity run below. To recompute identities and build from a fresh publication:

```powershell
python -B -m experiments.06_object_recognition.experiments.06_identity_policy.cached_replay
python -B -m tools.demos.build --source-root . --identity-run <printed-run-path>
```

This writes all seven pages here. The builder verifies the identity publication and its original source hashes, and rejects changes to recorded geometry or proposals. It reads these saved runs:

| Run | Used for |
|---|---|
| `experiments/06_object_recognition/experiments/06_identity_policy/runs/20261005T102726.235703Z_bace0cc9ceb44abfa9172c16f0f3d53b` | Pages 0 and 6: corrected identities. Complete 172-file publication; manifest SHA-256 `a580860117a0b04dab6b400c494b7b70da59696f889628ddbb13cbdb3c0845d2`. |
| `experiments/06_object_recognition/experiments/05_replay/runs/20261004T152704.023370Z_84abb8b3b9594dcea8a1e5b2c8aced66` | Pages 1, 4, 5 and 6: 60 desk frames with depth, camera poses and detections |
| `experiments/03_camera_pose_estimation/runs/20261002T164601.734717Z_befb0ccd27ab44daba6d9ac41f9b9ae0` | Page 2: estimated poses, errors and the reference path |
| `experiments/04_surface_reconstruction/runs/20261002T145103.184769Z_000165ef2e044376baf54b675172a64e` | Page 3: room points and their distances to the reference |
| `data/icl_nuim/reference_surface/living-room.ply` | Page 3: reference overlay (a random 200,000-point sample) |

The only computation is presentation work:
- turning saved depth into 3D points with the saved camera poses;
- averaging repeated points in small cells;
- building splats and the top-down grid;
- drawing thumbnails.

Display settings are listed in `tools/demos/build.py` and in each page's footer. To check the pages after rebuilding, run `python -B -m tools.demos.screenshot --out <folder>`. It opens every page in headless Chromium with the network switched off, saves screenshots and reports any script error or network request.

## How they work

Each page is one HTML file with its styles, scripts and data embedded. Positions are stored as 16-bit numbers inside each scene's bounding box, which loses less than a tenth of a millimetre for a room-sized scene. A small built-in WebGL viewer (`tools/demos/web/viewer.js`) draws points, lines and Gaussian splats. It needs a browser with WebGL2, which all current desktop and phone browsers have. The splat drawing follows the standard projection used by 3D Gaussian splatting viewers: each splat is drawn as a soft ellipse and blended from front to back.
