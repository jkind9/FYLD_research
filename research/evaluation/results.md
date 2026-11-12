# Measured results of the room and live pipelines

Dated measurements of the two orchestrators in `sitescan/pipelines/`. How to run them is
in [sitescan/pipelines/README.md](../../sitescan/pipelines/README.md); this page only records
what runs gave. All runs are CPU only, on a 32-thread desktop, with the depth model on 16
threads, unless a row says otherwise. Output folders under `outputs/` are local only.

## Room build on the 15 October Redmi walk

`python -B -m apps.cli room --session <20261015_093913_walk> --out <folder>`, defaults
(4 m far limit, 2 cm voxel, 8 × 6 scale grid).

| Run | Fused frames | Raw points | Vote removed | Pieces removed | Cleaned points | Length × width | Time |
|---|---:|---:|---:|---:|---:|---|---:|
| Baseline, commit `d859867` (9 November) | 134 | 676,855 | 100,086 | 22,702 | 554,067 | 6.35 × 3.30 m | 82 s (8 November run) |
| After the refactor (11 November) | 134 | 676,855 | 100,086 | 22,702 | 554,067 | 6.35 × 3.30 m | 51 s |

Every number in the two summaries matches, including the scale range (0.453, 0.595, 0.803)
and the plane normal. Frames skipped: 10 with stale depth, 3 with too few depth pixels.
Local outputs: `outputs/refactor/baseline_d859867/room_15oct/` and `outputs/refactor/refactor_2026-11-11/room_15oct/`.

The room is one piece; the next largest holds about 4,400 points. The vote took 2.4–2.6 s.
Its cost grows with frames × points.

## Live replay of the 15 October Redmi walk, before and after the refactor

`python -B -m apps.cli replay --session <20261015_093913_walk> --out <folder>`, objects on,
recorded speed, 822 frames. On 11 November two jobs from another project kept the CPU at
about 76% load, so the old code (commit `9bf3b51`, `apps.cli`) was run straight after the
new code under the same load.

| Code | Updates | Updates per second | Gaps over 1 s | Longest gap | Update, median | Depth model | Map | Objects (own thread) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Before, under load | 34 | 1.24 | 7 | 1.73 s | 675 ms | 255 ms | 245 ms | 363 ms |
| After, under load | 36 | 1.23 | 8 | 1.76 s | 697 ms | 255 ms | 250 ms | 371 ms |
| Before, quiet machine (10 November) | 44 | 1.59 | 0 | 0.85 s | 619 ms | | | |

Stage times match within run-to-run noise. Both stay above one update per second on average;
under load neither keeps every gap under a second. Local outputs:
`outputs/refactor/refactor_2026-11-11/live_15oct*/` and `outputs/refactor/final_refactor/live_isolated/`.

## Live replay of public recordings, 14 October 2026

Stand-in recordings (`python -B -m research.evaluation.stand_in`): the clip's true path and its depth
sensor standing in for ARCore, replayed at recorded speed.

| Recording | Frames received | Updates | Updates per second | Longest gap | Update time, median | Delay, frame to result |
|---|---:|---:|---:|---:|---:|---:|
| TUM fr1 xyz, 2 cm voxel | 796 | 51 | 1.90 | 0.61 s | 526 ms | 585 ms |
| TUM fr1 desk, 2 cm voxel | 596 | 33 | 1.61 | 0.72 s | 621 ms | 661 ms |
| ICL living room, 1 cm voxel | 880 | 28 | 0.89 | 1.47 s | 1,149 ms | 1,170 ms |
| ICL living room, 2 cm voxel | 880 | 37 | 1.22 | 0.98 s | 821 ms | 855 ms |

Median stage times on TUM xyz: depth model 250 ms, map 200 ms, surface 35 ms, fusion 6 ms;
detection 274 ms on its own thread. At 1 cm on ICL, extracting and thinning 2.6 million
surface points costs about 670 ms per update.

ICL surface accuracy (`python -B -m research.evaluation.score`): 46 mm mean distance at 1 cm and
52 mm at 2 cm; 71% and 69% of points within 5 cm; 22% of the room covered from 28–37 fused frames.

## Live replay of the 14 October Redmi walk

`20261014_220756_walk`: 1,194 frames over 39.88 s, replayed at recorded speed with objects on.
63 updates at 1.58 per second, longest gap 0.856 s, none over 1 s, median update 619 ms,
median delay 673 ms, 845,428 surface points, 83 anchor corrections. Scale came from tracked
points in 33 updates and from the previous update in 30. Local outputs:
`outputs/capture/capture_task99_220756/live_verified/`.

## Why live counts are too high, 14 October 2026

`python -B -m research.evaluation.count_report <run>/updates.jsonl` splits the new identities of a live run.

| | TUM xyz | TUM desk |
|---|---:|---:|
| New identities | 51 | 45 |
| ... 0.35–0.7 m from an object of the same class | 23 | 21 |
| ... 0.7–1.5 m away | 7 | 8 |
| ... over 1.5 m away | 3 | 3 |
| ... first of their class, or not placed | 18 | 13 |
| ... detector confidence under 0.5 | 21 | 23 |
| ... seen in only one update | 15 | 14 |
| Chairs / TVs, all identities | 14 / 7 | 5 / 9 |
| Chairs / TVs, seen in 3 or more updates | 9 / 7 | 2 / 7 |

Almost half the new identities appear just past the 0.35 m matching distance from an object
of the same class. Position scatter from learned depth inside a box is the main cause.

## Fixture outputs

`tests/fixtures/tum_desk_20_golden.json` holds both orchestrators' outputs on the committed
20-frame fixture; `pytest -m golden` compares them. See [tests/fixtures/README.md](../../tests/fixtures/README.md).
