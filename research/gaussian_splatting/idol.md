# Idol: a 3D object from one photo

Assessed 10 November 2026 from the owner-supplied model link. **Recommendation: reference only; low priority for the current measurement and counting goals.** No weights were downloaded and no inference was run.

## What the authors provide

[Model card](https://huggingface.co/speridlabs/idol) · [Inference SDK](https://github.com/speridlabs/idol-sdk)

Idol generates a Gaussian splat of one object from one image. A Gaussian splat represents an object with small coloured blobs in 3D. Background removal and cropping isolate the object. The model generates unseen sides as well as visible ones.

The model card reports:

| Item | Published detail |
|---|---|
| Output | Standard 3DGS `.ply`, plus the processed input image and a predicted input camera |
| Size | 32,768 to 1,048,576 Gaussians; default 262,144 |
| GPU memory | 7.2 GB peak |
| Default benchmark | 50 sampling steps; median request time across eight images |
| RTX 4090 | 19.1 seconds per image |
| RTX 3080 | 46.2 seconds per image |
| B300 | 3.4 seconds per image |
| Evaluation | Image similarity and appearance from new viewpoints; no dimensional error in metres reported |

These are author-reported results. The headline claim of under two seconds does not describe the listed default GPU benchmarks. It is not a timing estimate for our system. [Model card and timings](https://huggingface.co/speridlabs/idol#across-gpus)

The SDK requires Python 3.10 or later and PyTorch 2.5 or later. Its default image encoders are gated DINOv3 ViT-H+ and the FLUX.2 VAE. Idol's code and model are labelled Apache-2.0; the encoders have separate access conditions and licences. The SDK also allows supplying another compatible FLUX.2 VAE. [SDK setup](https://github.com/speridlabs/idol-sdk#install)

## Fit to this project

The following judgments are project assessments, not measured Idol results.

| Project need | Assessment |
|---|---|
| Object dimensions and site areas | Low fit. Generated hidden surfaces are not observed geometry. Published visual scores do not establish measurement accuracy or real-world scale. |
| Persistent object counting | Low direct fit. The documented pipeline does not associate sightings through a walkthrough or decide whether a returning object was counted before. |
| Rotatable object previews | Possible fit for displaying a detected cone, barrier or tool. Generated surfaces would need to be identified as such. |
| Extra views for recognition experiments | Possible research use. Generated markings and shapes might change identity cues; any benefit needs an independent recognition test. |

Keep Idol alongside the other deferred splatting methods. Revisit if object previews become a requirement. The current priority remains observed geometry, dimensional accuracy and distinct-object counts, as recorded in the [splatting index](README.md) and [object recognition experiments](../../experiments/06_object_recognition/README.md).
