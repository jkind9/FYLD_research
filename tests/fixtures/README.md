# Test fixtures

## `tum_desk_20`: the committed recording

Twenty frames (3.2 s) of the TUM RGB-D `freiburg1_desk` recording, in recording format v2. It is a stand-in for a phone walk, not ARCore data:

- Poses are the recording's motion-capture ground truth.
- "ARCore depth" is the Kinect depth, cut down to 160 × 120, on 7 of the 20 frames.
- Each frame has 20 tracked points taken from the Kinect depth.
- There are 3 anchors, one per second, and no anchor corrections.

Source: Sturm et al., "A Benchmark for the Evaluation of RGB-D SLAM Systems", IROS 2012, <https://cvg.cit.tum.de/data/datasets/rgbd-dataset>. Licence: CC BY 4.0. The images were re-encoded as JPEG quality 80.

Rebuild it from the local copy of the recording (needs `data/tum/rgbd_dataset_freiburg1_desk`):

```text
python -B -m tests.fixtures.build
```

The script keeps every 5th frame, takes the first 20, and rewrites today's stand-in output (format v1) as v2.

## `tum_desk_20_golden.json`: saved outputs

The outputs of today's code on `tum_desk_20`, saved before any stage moved into `sitescan/`:

- `room`: `src.live.room_build` with its defaults (4 m far limit, 2 cm voxel, 16 threads). 7 frames fused, 55,872 raw points, 51,962 after clean-up.
- `live`: `src.live.processor.LiveProcessor` fed every frame and updated after each one, without threads or timing, objects off. 20 updates, 73,191 points at the end.

Timings are left out. Rebuild the outputs only when a behaviour change is adopted on purpose:

```text
python -B -m tests.golden.run --session tests/fixtures/tum_desk_20 --out tests/fixtures/tum_desk_20_golden.json
```

The test lane: `python -B -m pytest -m golden tests/golden`. It needs the depth model weights (see `models/manifest.toml`) and skips without them. Counts may differ by 0.1% and lengths by 1 mm.

## The 15 October walk: local only

The full room build on `20261015_093913_walk` is the second reference. It shows a home, so neither the recording nor its output is in git. Saved run: `outputs/baseline_d859867/room_15oct/summary.json`: 134 frames fused, 676,855 raw points, 554,067 after clean-up, map 6.35 × 3.30 m.
