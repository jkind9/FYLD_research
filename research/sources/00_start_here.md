# Background: turning a phone capture into a useful site map

A camera records appearance. A useful map also needs distances, camera positions and a clear account of what was actually seen. This guide explains those pieces before the individual source notes.

## From images to a scene

**Depth** is the distance from the camera to a visible surface at an image location. A phone may obtain it from a depth sensor, two cameras or an image-based model. These methods have different requirements and error patterns. A per-frame depth image is not yet a shared map.

**Camera pose** is the camera's position and orientation. To combine several frames, we must know how their cameras moved. Estimating that movement while building a map is simultaneous localization and mapping (SLAM). Small movement errors can accumulate. Recognizing a place seen earlier, called loop closure, can help correct the accumulated error.

**Reconstruction** combines observations into scene points or surfaces. Building camera positions and scene points from overlapping images is structure from motion (SfM). Filling in more surface detail from several views is multi-view stereo (MVS). Image-only reconstruction often has an arbitrary scale. A known distance or another independent scale source is needed before reporting metres.

## From a scene to a top-down map

A point cloud is a collection of estimated surface positions. A mesh joins positions into surfaces. A top-down image can be made by projecting the reconstruction along a chosen vertical direction. With parallel projection, it is an orthographic view.

The vertical direction must be established. A camera's image axes do not automatically tell us gravity. A height grid can record the highest observed surface in each square, but that may hide a lower surface underneath it. Unseen squares should remain unknown. Observed points do not establish that the surrounding space is empty.

## Five different things to measure

1. **Depth error:** do distances to visible surfaces agree with independent measurements?
2. **Tracking error:** do estimated camera positions agree with a reference trajectory?
3. **Surface error:** does the reconstructed shape agree with an independent surface reference?
4. **Coverage:** which required surfaces were actually observed?
5. **Operational value:** does the capture help a worker or manager make the intended decision?

A low tracking error does not prove an accurate surface. A detailed image does not prove complete coverage. A high processing rate does not include capture or upload time unless those stages were measured.

## How to read the source notes

The [reading guide](README.md) groups the sources by the question they answer. Published numbers belong to their stated experiment. Local results are separate. Unknown hardware or licence terms remain marked as unknown.

The current repository has preliminary desktop experiments using supplied colour and depth images. Those experiments do not establish depth estimation from ordinary phone video or construction-site performance. The source notes are background for selecting the next controlled experiment.
