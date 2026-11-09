# Real-time 3D tracking and reconstruction on mobile phones (Prisacariu et al., 2015)

**Take-away:** An iPhone system that builds the 3D shape of one object, such as a statue, a shoe or a teddy bear, from its outline in each frame rather than from depth. It also tracks the phone from that same outline. It copes with blank, untextured objects, motion blur and people moving in the background. It recovers only the outer hull: dents and hollows that never show on the outline are lost, and thin parts are hard. Tracking runs at 31 fps on an iPhone 5s; one shape update takes 0.5 s. The phone code was not released; the desktop tracker it builds on (PWP3D) can be downloaded. It does not apply to rooms. Two parts carry over: the gyroscope gives rotation while vision gives position, and the shape is held as inside/outside probabilities per voxel. Added 8 November 2026 from an owner-supplied link; the paper was read in full; nothing was run.

## Citation and sources

Victor Adrian Prisacariu, Olaf Kähler, David W. Murray (University of Oxford) and Ian D. Reid (University of Adelaide). "Real-Time 3D Tracking and Reconstruction on Mobile Phones." IEEE Transactions on Visualization and Computer Graphics 21(5):557-570, 2015. DOI 10.1109/TVCG.2014.2355207. It extends the ISMAR 2013 paper "Simultaneous 3D tracking and reconstruction on a mobile phone" (pages 89-98).

- [Paper (Oxford)](https://www.robots.ox.ac.uk/~victor/pdfs/reco3d_tvcg.pdf) · [saved PDF](papers/prisacariu2015_mobile_object_reconstruction.pdf)
- **Code for the phone system: none found** (checked 8 November 2026: the authors' pages, the Oxford Active Vision code list, GitHub search, and the Oxford repository record, which has no files).
- **Code for the parts:**
  - PWP3D, the outline tracker (Prisacariu and Reid, IJCV 2012), is on the [Oxford Active Vision code page](https://code.active.vision) as PerseusLib: [one object and view, Visual Studio 2008](http://www.robots.ox.ac.uk/~victor/software/perseuslib/perseuslib_beta1.zip) and [several objects and views, Visual Studio 2010](http://www.robots.ox.ac.uk/~victor/software/perseuslib/perseuslib_beta2.zip). A CMake port is at [lumark/PWP3D](https://github.com/lumark/PWP3D), with no licence file.
  - [LibISR](https://github.com/carlren/LibISR), from the same lab: object tracking and reconstruction with an implicit shape, from colour-and-depth cameras. Free for non-commercial use.
  - [InfiniTAM](https://github.com/victorprad/InfiniTAM), from Kähler, Prisacariu and colleagues: depth fusion into a hashed TSDF volume, built to run on phones and tablets as well as PCs. Oxford University Innovation licence. This is the lab's closer relative of the project's fusion; Mobile3DRecon cites it.

## What it does

| Question | Answer |
|---|---|
| Input | Live colour video from an iPhone; the phone's orientation from its gyroscope and accelerometer (Apple Core Motion); 5-10 object masks the user makes at the start, each with the phone's orientation |
| Output | One object's shape: a 128 × 128 × 128 voxel volume holding the probability of being inside the object, with the surface at 0.5. Textured results and 3D-printed copies are shown |
| Hardware | iPhone 5 and 5s; desktop Intel Core i7-3960X. Tracking needs no GPU |
| Speed | Tracking 9.3 ms on the desktop, 43.3 ms on the iPhone 5 and 31.7 ms on the 5s (107, 23 and 31 fps). Adding a frame to the volume: 18 ms, 198 ms, and 143 ms on the 5s CPU or 88 ms on its GPU. Shape update: 102, 667 and 504 ms |
| Schedule | Tracking every frame; a frame is added every 3rd frame; the shape is updated after every 5 added frames. Shapes settled within 300-400 added frames, 1-2 minutes of video |
| Size | None. Outlines carry no real size, and the shape is rescaled to fill the volume |
| Accuracy | Against PTAM's path: 11.3 mm and 2.5° mean difference. On a second sequence, 129 mm and 12.0° without the gyroscope and 11.4 mm and 1.3° with it |

## The parts, in order

1. **Colour models.** Object and background are each described by a colour histogram (32 bins per channel). The user makes 5-10 masks from different sides at the start. During the scan the histograms are blended according to how close the phone's orientation is to each mask's.
2. **Per-pixel probabilities.** Each pixel gets the probability that it shows the object or the background.
3. **Tracking from the outline.** The current shape (a 64³ copy of the volume) is drawn from the current pose. The pose is adjusted until the drawn outline best separates object pixels from background pixels; this is a *level-set* energy, from PWP3D. Three shortcuts make it fast on a phone:
   - The shape is drawn at 40 × 30 pixels, then refined only around the edge, 10 times faster than a full draw.
   - Distances are computed only in a narrow band around the outline, not over the whole image.
   - The pose solver (Levenberg-Marquardt) runs coarse to fine, 2-3 times faster.
4. **Rotation from the gyroscope.** Different poses of an object can give the same outline, so outline-only tracking fails. Between frames the rotation comes from the phone's motion sensors and vision solves only for position. One visual rotation step every 10 frames corrects slow gyroscope drift.
5. **Add frames to the volume.** Each added frame's object and background probabilities are projected into the 128³ volume. A running average, with its weight capped at 250, lets early frames fade; those were tracked against a poor shape.
6. **Find the shape.** A global optimisation (continuous max-flow, with a smoothness term) splits the volume into inside and outside. One step runs after every 5 added frames, and the result goes back to the tracker.

## Evidence and limits

- On a synthetic human figure, using probabilities that account for how common object and background pixels are ("posteriors") beat plain colour likelihoods by over 20% in overlap with the true shape when the colour models were corrupted.
- Adding a frame every frame converged fastest; every 10th frame was worst.
- **The authors' limits:** outlines cannot show hollows, such as the inside of a hat or a shoe. Very thin parts such as leaves and fingers fail. Shiny highlights and shadows change colours and mislead the histograms. Large gyroscope drift spoils rotation.

## Relevance here

- **Not a room method.** The project builds whole rooms; an outline hull of a room means nothing.
- **For counted objects it suggests a shape without depth.** The project already has masks per object (the SAM family) and ARCore poses. Projecting mask probabilities from many views into a small voxel grid gives a closed outer shape and a rough volume for each object (a *visual hull*), even where learned depth is poor. It misses hollows. Not planned; noted for [object counting](../../experiments/06_object_recognition/README.md).
- **Gyroscope for rotation, vision for position:** ARCore already combines the camera and motion sensors, so there is nothing to add to tracking.
- **Fading early evidence:** the capped running average is a way to let a corrected pose or a moved object outvote old frames. The project's visibility vote weights frames by distance, not by age.
