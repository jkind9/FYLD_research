# Classical masks and measured depth support

This bounded control compares a filled rectangle, GrabCut and the largest filled Canny contour on six already inspected RGB-D frames. Eleven manually checked boxes are explicit oracle prompts. Four cached YOLO26x cup boxes form a separate predicted-prompt condition. Methods receive RGB and boxes, without reference polygons or identities. Depth is used after mask generation.

Coarse provisional reference polygons cannot establish mask accuracy. Real results therefore show selected area, raw and processed valid-depth counts, the median camera coordinates and their spread. Coordinate differences compare each mask with rectangle support. They are not object location error or calibrated uncertainty. Exact synthetic masks alone test overlap, boundary and split/merge scoring.

No learned segmentation weights are acquired. The existing YOLO26x checkpoint supplies detector boxes, not instance masks. Learned segmentation branches remain unavailable under the instruction to avoid new models and downloads. No new detector inference runs.

## Run and review

Use the existing installed environment:

```powershell
.venv-yolo/Scripts/python.exe -B -m experiments.06_object_recognition.experiments.02_segmentation.run
```

The command verifies Task17's frozen publication and original archive-member hashes. It also verifies the accepted Task28 cache when available. `--cache` can name its offline copy. An explicit missing or invalid cache path fails before publication. If the default optional cache is absent, the receipt marks the predicted condition unavailable. `--output` selects a new run root; destinations inside an existing run are rejected before mutation. Each publication captures source code, environment, settings, masks, original images, overlays and completion hashes. Interrupted runs remain incomplete; restart creates a fresh directory.

Fresh deployment uses an isolated environment and `requirements.txt`. It pins one OpenCV package, opencv-python 5.0.0.93, whose runtime version is 5.0.0, plus inherited shared dependencies. No installs were needed for this run. Transfer original inputs and verified publications offline; no automatic downloads occur.

## Accepted measured result

The accepted publication is `runs/20261004T073228.246785Z_2716be65637647e2a0a499e5c493df1f/review.html`. It verifies 206 artifacts with completion manifest SHA256 `f3c7dddf0c7e047959e79895c611dd09fd5e0f0f677133974472fe1177060ec7`. The earlier publication remains preserved and verified; this fresh run captures the reviewed provenance fixes.

It records 45 masks across 15 prompts. Rectangle and Canny each produce nonempty masks for all 15 prompts. GrabCut produces 12 nonempty and 3 empty masks. Empty support has null coordinates. A nonempty Canny mask can still contain no eligible measured depth; that also has null coordinates. The gap frame has no cup prompt. Predicted-box accounting retains the single missing cup reference and all matched boxes.

Internal run time is 5.762825 seconds, including source snapshots, mask processing, depth summaries and artifact/report writing. Final completion hashing and preflight are outside that timer. Mask-generation totals are 0.000258 seconds for rectangles, 3.879175 for GrabCut and 0.005046 for Canny. These totals cover 15 prompts each. They are descriptive measurements on this installed PC, without warmup or repeated benchmarking.

The largest observed coordinate changes involve monitor surfaces and background support. Their magnitude does not identify which method is more accurate. Full vectors, selected pixels and depth counts are saved for inspection. No formal mask accuracy, background-contamination truth, phone performance or generalisation claim is available.

## Verification

Focused controls cover malformed boxes/grids, clipping, minimum support, empty contours, GrabCut failure, exact synthetic overlap and boundaries, touching instances, split/merge detection, missing/out-of-range depth, rectangle agreement with existing localization, source-copy failure, inventory tampering and nested/aliased output rejection. An offline Edge check expands prompt details and verifies every image loads without network requests or page errors. Final review and accepted publication receipts are recorded in Task19.

Final verification: 28 focused tests pass with 92% production statement coverage. Ruff, package-based mypy and direct Black formatting checks pass. Independent Python/code review and fresh finished diff review both pass. The actual six-frame offline Edge report loads all 57 images without page errors or network requests.

## Next question, without reopening Task19

[Task34](../../../../task_list/open/34_evaluate_segmentation_for_position_and_observed_dimensions.md) owns the new independent comparison of rectangles, classical masks, checked-foreground oracle supports and authorised learned masks. It requires pixel/physical references to judge background contamination, repeatability, absolute error and observed dimensions. Task19's coordinate differences and cost ledger remain historical evidence; they do not prove improved location or size accuracy. Whole-object dimensions require separate coverage/reference evidence.
