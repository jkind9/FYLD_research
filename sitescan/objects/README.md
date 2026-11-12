# Objects (experimental)

Finds objects in a colour image, places each one in 3D from the scaled depth, and counts
them by matching each sighting to the objects already seen. **It overcounts.** On two
public desk recordings the live pipeline ended with 51 and 45 identities for scenes with
far fewer objects (details under Limits). The stage keeps today's behaviour so that a
better matching rule can be measured against it.

The detector is YOLO26x, loaded through Ultralytics. Ultralytics is AGPL-3.0 or
commercial, and that choice is not settled, so this stage is not cleared for a
proprietary product.

## Inputs and outputs

| Name | Shape and type | Units and axes |
|---|---|---|
| `image` | H × W × 3 uint8 RGB | The recorded pixel grid |
| `Detection` | `xyxy`, `label`, `class_id`, `confidence` | Box corners in original image pixels; COCO class; score 0–1 |
| `depth`, `valid` | H × W float and bool | Scaled camera-plane metres on the same grid |
| `camera` | `sitescan.types.Camera` | Pixel intrinsics |
| `world_from_camera` | 4 × 4 float64 | Metres; OpenCV camera axes in ARCore world |
| `box_position(...)` | 3 floats, or `None` | World metres |
| `Objects.update(...)` | One dict per detection | `label`, `confidence`, `outcome`, `object_id`, `nearest_same_class_m` |
| `Objects.counts()` | `{label: count}` | Objects counted so far |

## How it works

1. **Detect.** Run YOLO26x at 640 pixels with a 0.25 score floor and keep every box in original image pixels.
2. **Place.** Back-project the valid depth pixels whose centres fall inside the box, take the coordinate-wise median and move it to the world. The box also covers background, so this is a visible-surface sample, not the object's centre.
3. **Follow corrections.** Each counted object is stored relative to the anchor of the keyframe it was last seen from. When ARCore corrects that anchor, the object moves with the surface fused from the same keyframe.
4. **Match.** Within each class, assign sightings to objects one to one by the shortest total distance, up to 0.35 m. A sighting whose next-best assignment is within 0.05 m of the best is left unresolved, not guessed.
5. **Count.** A placed sighting with no object in reach starts a new object. Sightings without depth, ambiguous ones, and ones whose nearest object was already taken this frame start nothing.

## Run it

Needs the `objects` extra and the local weights at `models/yolo26x.pt`:

```python
import numpy as np
from sitescan import objects, session
from sitescan.pipelines import DETECTOR_MODEL

detect = objects.load_detector(DETECTOR_MODEL)
frame = next(session.frames("tests/fixtures/tum_desk_20"))
print([(d.label, round(d.confidence, 2)) for d in detect(frame.image)][:3])
```

Matching needs no weights:

```python
from sitescan.objects import associate_frame

rows, tracks, _ = associate_frame([{"class_id": 41, "label": "cup", "world_position_m": [0, 0, 1]}], {}, 1)
print(rows[0]["association"], rows[0]["object_id"])
# new object-0001
```

## Settings

| Name | Default | Why | Evidence |
|---|---|---|---|
| Detector | YOLO26x, SHA-256 `9fdd44a3…` | The checkpoint the counting results were measured with | [Pilot README](../../research/experiments/06_object_recognition/pilot/README.md) |
| `imgsz`, `conf`, `iou` | 640, 0.25, 0.7 | Ultralytics defaults, kept for comparable results | [Detection experiment](../../research/experiments/06_object_recognition/experiments/01_detection/README.md) |
| `max_distance_m` | 0.35 m | Tuned for cups placed from reference depth at every frame | [Object experiments](../../research/experiments/06_object_recognition/README.md) |
| `ambiguity_margin_m` | 0.05 m | Leaves near-ties unresolved instead of guessing | [Object experiments](../../research/experiments/06_object_recognition/README.md) |

## Limits

- Live replays of two public desk recordings (TUM fr1 xyz and fr1 desk, 14 October 2026) ended with 51 and 45 new identities. 23 and 21 of them appeared 0.35–0.7 m from an object of the same class. The cause is position scatter: learned depth inside a box moves a chair or screen further than 0.35 m between views. Counting only objects seen 3 or more times still left 9 chairs and 7 screens on fr1 xyz.
- No real scene has a counted inventory yet, so no count has been scored against the truth.
- Objects follow ARCore's anchor corrections today. Owner decision 10 plans an open tracker's keyframe poses as anchors ([DESIGN section 7.15](../../DESIGN.md#715-removing-arcore-five-changes)).
- The box median mixes object and background depth; a segmentation mask would place objects better (trial in the object experiments).

## Tests

`python -B -m pytest -q tests/test_sitescan_objects.py` checks placement in world metres,
boxes without depth, new and matched sightings, far and other-class sightings, ambiguous
ties, an object already taken in the same frame, and objects following an anchor
correction. `tests/test_pipelines.py` runs counting inside the live pipeline.
