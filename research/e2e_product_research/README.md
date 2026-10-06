# Existing end-to-end products and open-source projects

Web search carried out on 5 October 2026. It asks one question: does a product or open-source project already do what this repository is trying to do?

The target, as stated in the root README, is:

1. Take a phone video of a worksite.
2. Produce a 3D model of the visible site, measured in metres.
3. Count distinct objects such as cones and barriers, so an object that leaves the camera view and comes back is counted once, not twice.
4. Do this either on a server (the phone only records) or on the phone itself, ideally on an ordinary Android phone with no laser depth sensor.

The [edge products review](../edge_products/README.md) covers stereo cameras and small edge computers. This file covers phone apps, cloud services and open-source code.

## Per-product notes

One folder per product or project, for the eight most relevant to this repository's full chain: phone video, then a real 3D scene, then objects detected and counted once. Each note follows the same layout: a one-paragraph take-away, a table of the same questions, how it works, evidence and limits, which of this repository's layers it covers, and a short test plan.

| Note | Kind | Why it is here |
|---|---|---|
| [01 IGGT](01_iggt/README.md) | Open source, server | Closest open-source match to layers 2–5 in one step: ordinary images in, 3D model with separate objects out |
| [02 ConceptGraphs](02_conceptgraphs/README.md) | Open source, server | Closest research match to layer 5: places objects in 3D and merges repeat sightings by 3D overlap plus appearance |
| [03 CountVid](03_countvid/README.md) | Open source, server | Strongest open baseline for counting distinct objects in a video, in 2D only |
| [04 Apple RoomPlan](04_apple_roomplan/README.md) | Commercial, on the phone | Only finished product that measures and places objects in 3D on the phone; needs an iPhone with a laser sensor |
| [05 Android on the phone](05_android_on_phone_kit/README.md) | Toolkits and samples | ARCore, Lightship, the ARCore ML sample and RTAB-Map: everything needed on Android except the "same or new object" rule |
| [06 ViaSight ZoneSure](06_viasight_zonesure/README.md) | Commercial, hosted | Nearest product aimed at the same objects: phone video checks of cones and signs at road works |
| [07 SkyeBrowse](07_skyebrowse/README.md) | Commercial, hosted | Closest commercial match to layers 1–4: measured 3D model from ordinary Android video |
| [08 Scaniverse](08_scaniverse/README.md) | Commercial, on the phone | Phone capture to a real 3D scene viewed in a VR headset; no objects or checked measurement |

OVSeg3R (ordinary video in, labelled 3D objects out) would sit next to IGGT, but no public code was found, so it is covered inside the IGGT note.

## Contents

- [Short answer](#short-answer)
- [How the search was done](#how-the-search-was-done)
- [A look-alike that is not related: Depth Surge 3D](#a-look-alike-that-is-not-related-depth-surge-3d)
- [Comparison tables](#comparison-tables)
- [The closest end-to-end matches](#the-closest-end-to-end-matches)
- [Is anything in this repository new?](#is-anything-in-this-repository-new)
- [What this means for the project](#what-this-means-for-the-project)
- [Suggested checks](#suggested-checks)
- [Limits of this search](#limits-of-this-search)
- [Sources](#sources)

## Short answer

No product or open-source project was found that does the whole job: ordinary phone video in, a measured site model plus a count with each object counted once out, running on a normal Android phone or a hosted service, for street works or utility sites.

Each half exists on its own, and several are mature:

- **Measured 3D models from phone video** are a crowded commercial market (SkyeBrowse, Reconstruct, Polycam, PIX4Dcatch, Matterport).
- **Counting each object once** is solved at road scale by vehicle-mounted asset surveys that place each object by GPS (Vaisala/Xweather RoadAI, Gaist, Blyncsy). Research code solves it indoors, in 3D (ConceptGraphs and others).
- **Both together** exist in two places. Apple RoomPlan does it on an iPhone with a laser sensor, indoors, for 16 furniture types. Two 2025–2026 research projects (OVSeg3R, IGGT) do it from ordinary video on a large GPU, without checking real-world scale.
- **The nearest product aimed at the same objects** is ViaSight ZoneSure (launched late 2025). It films road work zones on a phone and checks cones and signs against US rules. It films from a vehicle and publishes no 3D or counting method.

Not finding something does not prove it doesn't exist. Private products often don't publish how they work.

## How the search was done

About 30 web searches and page reads, grouped by the parts of the problem:

- phone and video measurement apps
- construction site capture
- road asset and work-zone inspection
- counting objects in video
- open-source 3D object mapping
- phone AR toolkits and on-phone samples

Every accuracy figure below is the vendor's or the authors' own claim. Nothing was installed or tested.

## A look-alike that is not related: Depth Surge 3D

[Depth Surge 3D](https://github.com/Tok/depth-surge-3d) came up first because it also uses learned depth on video. It is not the same project.

| | Depth Surge 3D | This repository |
|---|---|---|
| Goal | Make a flat video look 3D in a VR headset | Measure a site and count objects |
| Depth | Depth Anything per frame; scale doesn't matter | Depth in metres, scored against reference depth |
| Camera position | Not estimated | Estimated and scored (6.9 mm error on a short desk recording) |
| 3D model | None; it makes a left-eye and right-eye image from each frame | Point surface scored against a reference model (7.8 mm average error) |
| Objects | None | Detection, outlines, appearance matching and counting |
| Checked against measured truth | No; its README calls the output "pseudo-stereo" | Yes, layer by layer |

The only overlap is the optional phone VR viewer in the root README, and that viewer would show measured results, not made-up depth.

## Comparison tables

Key: ✅ yes · ◐ partly · ❌ no · ? not published

The columns are the same in every table:

- **Measures:** gives sizes, distances or areas in metres.
- **Counts once:** counts objects with each physical object counted once, even after it leaves and re-enters the view.
- **On phone:** the processing happens on the phone. "Capture only" means the phone records and a server does the rest.
- **Android, no laser:** works on an ordinary Android phone without a laser depth sensor (LiDAR), like the Redmi Note 11 Pro used in this project.

### 1. Commercial: the phone records, a server does the work

| Product | Measures | Counts once | On phone | Android, no laser | Notes |
|---|---|---|---|---|---|
| [SkyeBrowse](https://www.skyebrowse.com/news/posts/3d-walkthrough) | ✅ | ❌ | capture only | ✅ | Builds a measured 3D model from continuous video from phones, 360 cameras or drones. Claims centimetre accuracy; the 0.1 inch figure is a sales claim. About 1 minute of processing per minute of video. Closest commercial match to layers 1–4. |
| [Reconstruct](https://blog.reconstructinc.com/turn-existing-360-camera-videos-into-a-measurable-walkthrough-of-your-job-site) | ✅ | ❌ | capture only | ◐ mainly 360 cameras | Measurable walkthrough, point cloud and floor plan of construction sites from 360, phone or drone video. |
| [OpenSpace](https://www.openspace.ai/resources/videos/openspace-3d-scanning-demo/) | ◐ | ❌ | capture only | ❌ 3D scan needs a laser sensor | Helmet 360 camera walkthroughs mapped to building plans. Its 3D scan mode uses the laser sensor in recent iPhones and iPads. |
| [Buildots](https://www.unite.ai/best-ai-tools-for-the-construction-industry/), [Doxel](https://theneuralbase.com/ai-for-real-estate/learn/advanced/tools-buildots-doxel-openspace/) | ◐ | ❌ | capture only | ❌ | Track construction progress against the building design model, using 360 cameras (Buildots) or robots with laser scanners (Doxel). |
| [Matterport](https://matterport.com/news/matterport-launches-property-intelligence-transforming-real-estate) | ✅ | ◐ | capture only | ? | Automatic wall, ceiling and floor-area measurements. Its AI tags objects in a scan as assets. Built for buildings. |
| [ViaSight ZoneSure](https://www.startlandnews.com/2026/02/zikomo-fields-viasight/) | ❌ none published | ◐ | capture only | ✅ [on Play Store](https://play.google.com/store/apps/details?id=ai.viasight.zonesure) | Phone on the windscreen, drive through a work zone, cloud AI checks signs, cones, barrels and lane markings against the US work-zone rules (MUTCD). Outputs GPS-tagged issues and a report. Nearest product aimed at the same objects. |
| [Xweather (Vaisala) RoadAI](https://www.xweather.com/products/roadai), [Gaist](https://gaist.co.uk/solutions), [Blyncsy (Bentley)](https://www.bentley.com/software/blyncsy/) | ◐ road condition | ✅ | ❌ vehicle cameras | n/a | Vehicle video turned into a list of road assets (signs, barriers, bollards, cones), each placed once by GPS. Blyncsy uses images from over 800,000 vehicles. Solves "count each object once" at road scale, not walking pace. |
| [FYLD video risk assessment](https://fyld.ai/faq) | ❌ | ❌ | capture only | ✅ | Workers film the site before starting work; AI finds hazards in the video and audio. This is the product this research would plug into. |

### 2. Commercial: the work happens on the phone

| Product | Measures | Counts once | On phone | Android, no laser | Notes |
|---|---|---|---|---|---|
| [Apple RoomPlan](https://developer.apple.com/augmented-reality/roomplan) | ✅ | ◐ | ✅ | ❌ iPhone/iPad with laser sensor | Room plan in metres, with objects placed in 3D from 16 furniture types. The only finished example of measuring and placing objects together on a phone. Indoors only. |
| [Polycam](https://poly.cam/) | ✅ | ❌ | ? | ✅ photo mode | Photo-based or laser-based scanning. Its "Spatial Report" gives room sizes and wall areas; the vendor claims 2% accuracy. |
| [Scaniverse (Niantic)](https://radiancefields.com/scaniverse-arrives-on-android) | ◐ | ❌ | ✅ | ✅ | Builds a photo-realistic 3D model (a Gaussian splat) entirely on the phone, with no upload. A viewing tool, not a measuring tool. |
| [KIRI Engine](https://www.cgchannel.com/?p=152598) | ◐ | ❌ | ◐ | ✅ | Phone scanning app with Gaussian splats on Android. Aimed at 3D content, not measurement. |
| [PIX4Dcatch](https://geoconnexion.com/news/emlid-and-pix4d-launch-a-mobile-terrestrial-scanning-kit-to-accelerate-data-capture) | ✅ | ❌ | capture only | ◐ | Phone scanning plus an add-on satellite positioning receiver for centimetre accuracy. Sold for documenting trenches and finished utility work. Some modes need a laser sensor. |
| [CamToPlan, AR Plan 3D](https://www.slashgear.com/1433650/best-app-for-measurement-android/) | ◐ | ❌ | ✅ | ✅ | ARCore tape measures: the user taps the points to measure. Google's own Measure app was withdrawn in 2021 for poor accuracy. |
| [Dot3D](https://www.laserscanning-europe.com/en/node/4150) | ✅ | ❌ | ✅ | ❌ | Professional scanning on Android and Windows, with a separate depth-sensor scanner. |

### 3. Phone toolkits (building blocks, not finished apps)

| Toolkit | What it gives on the phone | Android, no laser | Open source |
|---|---|---|---|
| [Google ARCore](https://developers.google.com/ar/develop/machine-learning) | Camera position, depth, outdoor pixel labels (road, building and so on), location with heading | ✅ | ❌ free to use |
| [Niantic Lightship ARDK](https://ar.dev/products/ardk) | A live 3D mesh, pixel labels, and 2D boxes round 200+ object types. The mesh works on phones without a laser sensor. Built on Unity. | ✅ | ❌ |
| [Spectacular AI SDK](https://github.com/SpectacularAI/sdk) | Camera tracking from camera plus motion sensors, and a mapping interface for live or offline 3D models | ◐ | ❌ commercial |

### 4. Open source that runs on the phone

| Project | What it does | What's missing |
|---|---|---|
| [RTAB-Map](https://github.com/introlab/rtabmap) | Phone 3D mapping with drift correction (it notices a revisited place and corrects the path). Exports a mesh or point cloud. Android build in the repository; [iOS app](https://apps.apple.com/app/id1564774365) on the App Store. | No objects. A current Android Play Store listing was not confirmed. |
| [googlesamples/arcore-ml-sample](https://github.com/googlesamples/arcore-ml-sample) (Apache 2.0) | Detects objects on the phone with ML Kit and pins each label at its 3D position using ARCore. | No duplicate removal or counting. The default classifier knows only 5 coarse categories. |
| [Kashif-E/Ar-Object-Detection](https://github.com/Kashif-E/Ar-Object-Detection) | Same idea with a custom TensorFlow Lite detector. | Hobby project. No counting. |
| [Ultralytics object counting](https://docs.ultralytics.com/guides/object-counting/) (AGPL-3.0) | Counts objects that cross a line or enter a region of the image. Exports to phones. | 2D only, so an object that leaves and returns is counted again. |
| [MediaPipe Objectron](https://research.google/blog/real-time-3d-object-detection-on-mobile-devices-with-mediapipe/) | Live 3D boxes round objects on the phone. | Support ended March 2023. Only a few everyday object types. |

### 5. Open source that runs on a server

**Ordinary video in, 3D model with separate objects out (no depth sensor needed):**

| Project | Pipeline | What's missing |
|---|---|---|
| [OVSeg3R](https://arxiv.org/pdf/2509.23541) (ICLR 2026) | MASt3R-SLAM (or VGGT) builds the 3D points and camera path. DINO-X finds and labels objects in each image. Matching image pixels to 3D points turns them into 3D objects. | GPU-heavy. Tested on indoor benchmarks. Real-world scale is not checked. No public code found on 5 October 2026. |
| [IGGT](https://arxiv.org/pdf/2510.22706) ([code](https://gittrend.io/repo/lifuguan/IGGT_official), ICLR 2026) | One model that outputs 3D shape and separate object instances together. MIT licence; weights released. | GPU-heavy. Indoor benchmarks only. Real-world scale is not checked. Downstream task scripts not yet released. |
| [Ov3R](https://openaccess.thecvf.com/content/CVPR2026/papers/Gong_Ov3R_Open-Vocabulary_Semantic_3D_Reconstruction_from_RGB_Videos_CVPR_2026_paper.pdf) (CVPR 2026) | 3D points from video plus SAM outlines, joined into labelled 3D. | Labels surfaces by meaning; separating individual objects is not its focus. |
| [SpatialLM](https://arxiv.org/html/2506.07491v1) (NeurIPS 2025) | Takes a point cloud (from video, depth or laser) and outputs walls, doors, windows and 3D boxes round objects. | Indoor layouts only. |

**Need depth and camera positions supplied (what this repository's layers 2–3 produce):**

| Project | What it does |
|---|---|
| [ConceptGraphs](https://arxiv.org/pdf/2309.16650) | A 3D map of individual objects from depth video. Sightings are matched to objects by 3D position plus appearance. This is the same matching rule this repository's layer 5 tests, so it is the closest research match. |
| [Hydra and Khronos](https://github.com/orgs/MIT-SPARK/repositories) (MIT SPARK lab) | Live 3D maps of places and objects. Khronos also handles objects that move. |
| [panoptic_mapping](https://git.tdem.in/ethz-asl/panoptic_mapping) (ETH Zurich), [Voxblox++](https://arxiv.org/pdf/1903.00268) | Volume maps that keep each object as a separate instance. |
| [EmbodiedSAM](https://github.com/xuxw98/ESAM) (ICLR 2025) | Live 3D object outlines built up frame by frame using SAM. |

**Head-camera research on remembering objects that leave the view:**

| Project | What it shows |
|---|---|
| [Instance tracking in 3D from egocentric video](https://arxiv.org/pdf/2312.04117) and [3D-aware instance tracking](https://openaccess.thecvf.com/content/ACCV2024/papers/Bhalgat_3D-Aware_Instance_Segmentation_and_Tracking_in_Egocentric_Videos_ACCV_2024_paper.pdf) | A still object keeps its 3D position while out of view, so position helps recognise it when it returns. |
| [EAGLE](https://arxiv.org/pdf/2511.08007), [Embodied VideoAgent](https://openaccess.thecvf.com/content/ICCV2025/papers/Fan_Embodied_VideoAgent_Persistent_Memory_from_Egocentric_Videos_and_Embodied_Sensors_ICCV_2025_paper.pdf) | Combine appearance and 3D position in an object memory for head-camera video. |
| [Meta EFM3D / EVL](https://www.projectaria.com/research/efm3d/) | 3D boxes round objects from head-camera video (Project Aria glasses). Code released. |

**Counting only (no 3D):**

| Project | What it does |
|---|---|
| [CountVid](https://github.com/niki-amini-naieni/CountVid) (Oxford, AAAI 2026) | Counts distinct objects in a video from a text prompt like "traffic cone" or an example image. Uses an image counting model plus SAM-style video tracking. Comes with the VideoCount test set. The best open baseline to compare counting against. |
| [SAM3Count](https://openaccess.thecvf.com/content/CVPR2026W/WiCV/papers/Owusu_SAM3Count_for_Zero-Shot_Open_Vocabulary_Counting_in_Images_and_Videos_CVPRW_2026_paper.pdf) (CVPR 2026 workshop) | SAM 3 adapted for counting in video, aimed at reducing double counts. As heavy as SAM. |
| [VSI-Bench](https://arxiv.org/html/2412.14171v1) (CVPR 2025) | A test set of questions on indoor videos, including counting objects and estimating sizes and distances. Shows that AI vision-language models are still poor at this. |

## The closest end-to-end matches

1. **Measuring and counting together, on the phone:** Apple RoomPlan. It needs an iPhone with a laser sensor, works indoors and knows 16 furniture types. It shows the idea works as a product, but it can't run on the Redmi.
2. **Measuring and counting together, on a server, open source:** IGGT. Ordinary video in; a 3D model with separate objects out. That covers this repository's layers 2–5 in one pipeline. It doesn't check real-world scale, wasn't tested outdoors or on worksites, and needs a large GPU. OVSeg3R does the same but has no public code.
3. **On an Android phone without a laser sensor:** nothing complete. The nearest kit is ARCore or Lightship (camera position, depth, live mesh) plus the ARCore ML sample (detections pinned in 3D). Two parts are missing:
   - the rule that decides whether a new sighting is an object already seen or a new one
   - any evidence that the measurements are accurate
4. **Commercial product for the same objects:** ViaSight ZoneSure. It films from a vehicle, checks against US rules, and publishes no counting or 3D method.
5. **Commercial product for measuring from Android video:** SkyeBrowse (hosted). PIX4Dcatch if centimetre accuracy is needed and an add-on GPS receiver is acceptable.

## Is anything in this repository new?

Not at the level of individual methods. Camera tracking, 3D models from depth, object detection, appearance matching, and matching objects by 3D position are all published and available.

Three things could be new, and each would need a targeted literature search to confirm:

1. **The setting.** No published, measured results were found for this exact case: a mid-range Android phone with no laser sensor, outdoors, counting temporary street-works objects that leave the view and come back.
2. **Cost against accuracy.** FYLD's brief says SAM works but is too heavy. A measured answer to "how much cheaper can counting get before it starts double-counting or missing objects?" would be useful. Few papers report count accuracy, compute cost and phone-versus-server deployment together.
3. **Tracing error to its source.** This repository tests each layer with known-good inputs, then swaps in one real layer at a time and measures how much worse the result gets. Breaking final count errors down by layer like this is rare in published work, and it is useful for engineering decisions.

## What this means for the project

- **Measuring the site (layers 1–4) adds little as a product.** SkyeBrowse, Reconstruct and Polycam already sell it. The layer-by-layer pipeline is still useful as a way to measure where error comes from, and as a reference to score those products against.
- **Counting on Android is the real gap:** ARCore or Lightship positions, plus a light rule for "same object or new one", scored against CountVid and SAM 3 on count accuracy, phone speed and battery. No product or open project found does that for street works.
- **Expect the "why not buy it?" question.** ViaSight, Blyncsy and SkyeBrowse are the obvious ones to compare against. A proposal to FYLD should name them and say what they don't do.

## Suggested checks

These are cheap and would turn the vendor claims above into local evidence:

1. Run IGGT on the same TUM desk recording used by layer 5, and compare its objects with this repository's matching results.
2. Run CountVid on the same recording and compare its count with this repository's count.
3. Put one capture through SkyeBrowse or Polycam and score the result against the same reference as the layer 4 point surface.
4. Build the ARCore ML sample on the Redmi, to see how far a detector pinned to ARCore positions gets before any duplicate-removal rule is added.
5. Ask ViaSight whether ZoneSure counts devices, measures spacing, or builds 3D, and whether it works on foot.

## Limits of this search

- The search tool returns US-focused results, so UK street-works tools may be missing. Searches for UK street-works platforms (Symology, Causeway one.network) found inspection and permit software but no published AI checking of photos or video.
- Every accuracy figure is the vendor's or the authors' own claim. Nothing was installed or tested.
- A "?" means the vendor doesn't publish that detail.
- Licences were noted only where the search showed them. ConceptGraphs, IGGT and CountVid use MIT-licensed code, but the models they call (SAM, CLIP, Grounding DINO and others) and IGGT's weights have their own terms, which need checking before any commercial use. Ultralytics is AGPL-3.0 unless an enterprise licence is bought.

## Sources

Phone and cloud measurement:
[SkyeBrowse](https://www.skyebrowse.com/news/posts/3d-walkthrough) ·
[Reconstruct](https://blog.reconstructinc.com/turn-existing-360-camera-videos-into-a-measurable-walkthrough-of-your-job-site) ·
[OpenSpace 3D Scan](https://www.openspace.ai/resources/videos/openspace-3d-scanning-demo/) ·
[Construction AI tools, October 2026](https://www.unite.ai/best-ai-tools-for-the-construction-industry/) ·
[Buildots, Doxel, OpenSpace](https://theneuralbase.com/ai-for-real-estate/learn/advanced/tools-buildots-doxel-openspace/) ·
[Matterport Property Intelligence](https://matterport.com/news/matterport-launches-property-intelligence-transforming-real-estate) ·
[Polycam](https://poly.cam/) ·
[Scaniverse on Android](https://radiancefields.com/scaniverse-arrives-on-android) ·
[KIRI Engine](https://www.cgchannel.com/?p=152598) ·
[PIX4Dcatch and Emlid kit](https://geoconnexion.com/news/emlid-and-pix4d-launch-a-mobile-terrestrial-scanning-kit-to-accelerate-data-capture) ·
[Android measuring apps](https://www.slashgear.com/1433650/best-app-for-measurement-android/) ·
[Dot3D](https://www.laserscanning-europe.com/en/node/4150) ·
[Apple RoomPlan](https://developer.apple.com/augmented-reality/roomplan)

Road and work-zone inspection:
[ViaSight](https://www.viasight.ai/) ·
[ViaSight launch article](https://www.startlandnews.com/2026/02/zikomo-fields-viasight/) ·
[ZoneSure on Google Play](https://play.google.com/store/apps/details?id=ai.viasight.zonesure) ·
[Xweather RoadAI](https://www.xweather.com/products/roadai) ·
[Gaist](https://gaist.co.uk/solutions) ·
[Blyncsy](https://www.bentley.com/software/blyncsy/) ·
[Symology street works software](https://www.symology.co.uk/aurora/) ·
[FYLD FAQ](https://fyld.ai/faq)

Phone toolkits and on-phone open source:
[ARCore machine learning guide](https://developers.google.com/ar/develop/machine-learning) ·
[Lightship ARDK](https://ar.dev/products/ardk) ·
[Spectacular AI SDK](https://github.com/SpectacularAI/sdk) ·
[RTAB-Map](https://github.com/introlab/rtabmap) ·
[RTAB-Map iOS app](https://apps.apple.com/app/id1564774365) ·
[arcore-ml-sample](https://github.com/googlesamples/arcore-ml-sample) ·
[Ar-Object-Detection](https://github.com/Kashif-E/Ar-Object-Detection) ·
[Ultralytics object counting](https://docs.ultralytics.com/guides/object-counting/) ·
[MediaPipe Objectron](https://research.google/blog/real-time-3d-object-detection-on-mobile-devices-with-mediapipe/)

Server-side open source and research:
[OVSeg3R](https://arxiv.org/pdf/2509.23541) ·
[IGGT](https://arxiv.org/pdf/2510.22706) ·
[IGGT code](https://gittrend.io/repo/lifuguan/IGGT_official) ·
[Ov3R](https://openaccess.thecvf.com/content/CVPR2026/papers/Gong_Ov3R_Open-Vocabulary_Semantic_3D_Reconstruction_from_RGB_Videos_CVPR_2026_paper.pdf) ·
[SpatialLM](https://arxiv.org/html/2506.07491v1) ·
[ConceptGraphs](https://arxiv.org/pdf/2309.16650) ·
[MIT SPARK lab (Hydra, Khronos)](https://github.com/orgs/MIT-SPARK/repositories) ·
[panoptic_mapping](https://git.tdem.in/ethz-asl/panoptic_mapping) ·
[Voxblox++](https://arxiv.org/pdf/1903.00268) ·
[EmbodiedSAM](https://github.com/xuxw98/ESAM) ·
[Instance tracking in 3D from egocentric video](https://arxiv.org/pdf/2312.04117) ·
[3D-aware instance tracking in egocentric video](https://openaccess.thecvf.com/content/ACCV2024/papers/Bhalgat_3D-Aware_Instance_Segmentation_and_Tracking_in_Egocentric_Videos_ACCV_2024_paper.pdf) ·
[EAGLE](https://arxiv.org/pdf/2511.08007) ·
[Embodied VideoAgent](https://openaccess.thecvf.com/content/ICCV2025/papers/Fan_Embodied_VideoAgent_Persistent_Memory_from_Egocentric_Videos_and_Embodied_Sensors_ICCV_2025_paper.pdf) ·
[EFM3D](https://www.projectaria.com/research/efm3d/) ·
[CountVid code](https://github.com/niki-amini-naieni/CountVid) ·
[CountVid paper](https://arxiv.org/abs/2506.15368) ·
[SAM3Count](https://openaccess.thecvf.com/content/CVPR2026W/WiCV/papers/Owusu_SAM3Count_for_Zero-Shot_Open_Vocabulary_Counting_in_Images_and_Videos_CVPRW_2026_paper.pdf) ·
[VSI-Bench](https://arxiv.org/html/2412.14171v1)

Not related, checked for comparison:
[Depth Surge 3D](https://github.com/Tok/depth-surge-3d)
