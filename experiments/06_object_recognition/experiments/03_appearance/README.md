# Object appearance across recorded views

This trial compares observations of one cup and two distinct monitors. It uses six recorded views and eleven coarse, provisional image supports. The supports were drawn from the recording and inspected earlier. The results are a descriptive check of those views. They do not establish accuracy on unseen recordings.

Four methods use the same crops: image correlation after subtracting the mean (ZNCC), local binary features (ORB), local gradient features (SIFT), and pooled features from the existing YOLO26x detector. The detector features have not been trained or validated specifically for object identity. No new model or weights are acquired.

## Inputs and separation

The frozen Task17 publication and original RGB images are verified against their recorded hashes. The original annotation JSON has hash `a786adc5f814ad9773712397f46ba79d8d40dc5c174fe17045336440cdffd920`. Its published serialization has hash `27fe047dac254161ea823d6c55aeb28e16bd88cd993f1e4bf8fbdee40d4741d3`. These contain the same annotation data.

Method inputs contain opaque observation keys, copied RGB, anonymous support files and explicit boxes. Identity labels and enrollment/evaluation joins live in the evaluator input. Descriptor methods receive arrays, never source filenames or identity answers. Coarse supports are an explicit supplied input condition, not predicted masks.

Each box is rounded outward and clamped to the image. Pixels outside its support become black. RGB is resized with bilinear interpolation and support with nearest-neighbour interpolation to 128 by 128. This changes aspect and can distort appearance. At the learned-feature boundary RGB is explicitly converted to contiguous BGR for the installed predictor, which converts it back to RGB and letterboxes to 640.

## Methods and decisions

Correlation requires at least sixteen jointly supported pixels and nonzero variation. Feature matching uses two neighbours, a 0.75 distance ratio, mutual matches and at least four non-collinear matches and inliers. A two-dimensional homography checks local consistency. Its transform is not a camera pose or a distance in metres.

All twenty-five same-class pairs are retained, including observations of distinct monitors in the same frame. Four enrollment observations form the gallery. Seven evaluation observations are ranked against the gallery of the same class. Missing descriptors and uncertain results remain visible. Scores within 0.000001 tie. A tie between different objects produces no identity assignment. No threshold is fitted on these inspected views.

## Run and inspect

Use the already installed pinned environment:

```powershell
.venv-yolo/Scripts/python.exe -B -m experiments.06_object_recognition.experiments.03_appearance.run
```

The command verifies inputs, constructs the existing checkpoint directly, requests one embedding per crop and publishes a new run. The first request also causes the installed predictor's full-model CUDA warmup. The recorded first-call cost includes that warmup. GPU runtime, precision, pooled layer, vector length and checkpoint hashes are checked and recorded. No automatic download or silent CPU fallback occurs.

Open the resulting `review.html`. It shows every crop, every pair, evaluator labels, all gallery rankings, missing results, ties and measured feature costs. Its JSON and source snapshot are included in the verified completion manifest. An interrupted run remains incomplete; restart creates a new directory. Output paths inside an existing run are rejected before creating files.

After a genuine GPU publication is accepted, its completion manifest is pinned in `cache.py`. `--cache <accepted-run>` reuses descriptors only when input, configuration and feature-producing code hashes match. Changes to crops or extraction code invalidate reuse. Changes confined to scoring or presentation can use the recorded vectors without another GPU extraction.

## Public adapter

`adapter.prepare_crop(rgb, support, bbox)` returns a crop with read-only RGB and support arrays. `adapter.describe_classical(crop)` extracts the two local descriptor types. `features.FeatureExtractor(checkpoint).extract(crop)` extracts a verified CUDA0 FP32 vector. `compare.compare_descriptors(left, right)` returns four nullable evidence records. Later trials can use the same adapter with detector boxes while naming that different support condition.

## Deployment and limits

The scoped requirements pin `opencv-python==5.0.0.93`, whose effective runtime is OpenCV 5.0.0, and NumPy 2.4.2. The existing pilot requirements pin Ultralytics 8.4.172 and the inherited Torch runtime is 2.11.0+cu128. Do not install OpenCV contrib alongside the regular OpenCV distribution. A fresh source handoff needs the verified Task17 publication, its original source files and the existing checkpoint. Nothing downloads implicitly.

The recording does not supply controlled lighting, rotation, moved-object or identical-neighbour revisit scenarios. Separate synthetic controls expose identical appearances, collinear matches, missing support and runtime failures. Coordinate fusion belongs to the association trial; similarity scores do not measure coordinate precision.

## Recorded result, 4 October 2026

The accepted [offline viewer](runs/20261004T135203.039973Z_fd481f16c8374ca2a0f04d6f0703a16d/review.html) contains eleven observations and twenty-five pairs: sixteen of the same object and nine of different objects. Its completion manifest is `f2b2e47803f160354fff1080a6a94164dc7790b39994bcd2b704c81ca50d27c4`, with 140 verified artifacts.

| Method | Available pairs | Seven gallery queries |
|---|---:|---|
| Correlation | 25 / 25 | 7 correct top-ranked identities |
| ORB | 0 / 25 | 7 unavailable |
| SIFT | 0 / 25 | 7 unavailable |
| Existing YOLO pooled features | 25 / 25 | 6 correct; 1 incorrect |

The learned features ranked the black monitor in frame 405 closer to the silver monitor: cosine 0.954094 against 0.910987 for its own enrollment view. That is a false appearance match in this recording. ORB and SIFT did not provide enough consistent local matches for any recorded pair. The synthetic textured self-match controls did pass. These results show why appearance scores need position checks and uncertainty handling.

There is only one cup identity in the gallery, so the cup's correct rankings cannot demonstrate separation from a second cup. The monitors supply the different-object comparison. Neither the inspected supports nor these rankings establish blind accuracy or a calibrated acceptance threshold.

The existing model returned 768-component vectors from layer 22 (`C3k2`) on CUDA0 in float32. Eleven embedding requests took 4.076556 seconds, including the first call's 3.961634 seconds with full-model warmup. Model construction took 0.629552 seconds and transfers took 0.001344 seconds. The complete descriptor stage, including imports, crop preparation and classical extraction, took 9.676336 seconds. The run ledger measured 11.052647 seconds through timing publication; final manifest hashing is outside that ledger's scope. Process GPU peaks were 404,958,208 allocated bytes and 501,219,328 reserved bytes.

Ultralytics emitted its existing-settings schema migration warning and a deprecated `half` warning. The actual recorded precision remained float32. No Task13 sequence or project settings were edited by this task.

Forty-one focused controls passed with 91% implementation coverage. Ruff, programmatic Black and mypy passed. The code and finished diff were independently reviewed. The final offline Edge check loaded all eleven crops and twenty-five pair rows, with no page errors or external requests. Descriptor reuse pins the exact accepted manifest, feature-producing files, actual detector settings and both annotation hashes. A verified cache read returned eleven rows without inference. No second GPU extraction was required.

## Next comparison, without reopening Task20

[Task33](../../../../task_list/stale/33_compare_object_appearance_context_and_spatial_association.md) will compare object-only/context appearance and spatial trade-offs on fixed inputs. ZNCC and existing YOLO26x pooled features are measured baselines. ResNet50 and contextual embeddings are proposed, untested and require their own acquisition/execution decisions. One incorrect monitor ranking is a recorded failure; it does not establish failure on all objects. Geometry-only and combined rules both resolve the current eleven observations, so wider tests must assess when additional appearance helps.

## Optional walkthrough appearance and validation

Appearance is an optional part of step 6 and is disabled by default. The root adapter explicitly calls the existing crop/classical-descriptor owner when selected; it does not load learned features. `adapter.prepare_crop`, `adapter.describe_classical` and `features.FeatureExtractor` remain in this experiment. `importlib.import_module("experiments.06_object_recognition.experiments.03_appearance.validation")` forwards `label_pairs` and `rank_queries` for their existing schemas. Independent identities remain scorer-only. [Runner contract](../../../../src/walkthrough/README.md).
