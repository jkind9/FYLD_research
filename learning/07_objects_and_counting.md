# 7. Objects and counting

The second project goal is to count distinct objects in a walkthrough, where an object that leaves the view and comes back is counted once. In 2D this fails: a returning cone looks like a new cone. In 3D it becomes possible, because a returning object reappears at the same place. This chapter covers the chain of steps and where the project stands.

## The chain

1. **Detection.** A neural network draws a box round each object it recognises, with a class name and a confidence. *Closed-set* detectors (YOLO, RF-DETR) know a fixed list; the common COCO list has 80 everyday classes and no traffic cones or barriers, so site objects need fine-tuning. *Open-vocabulary* detectors (Grounding DINO, SAM 3) find objects named in plain text.
2. **Segmentation.** Pick out the object's own pixels inside its box. Depth read from the whole box includes the wall behind, which pulls the object's 3D position backwards. Classical methods (GrabCut, filled outlines) need no model; learned ones are the SAM family (SAM 2 follows an object through video; MobileSAM and EdgeSAM are smaller).
3. **3D placement.** Take the depth at the object's pixels, back-project (chapter 1), move into the world with the camera pose. The result is a point on the object's *visible surface*. It moves as the camera walks round the object, so it is not the object's centre.
4. **Appearance.** Describe how the object looks, so two sightings can be compared: from raw patch comparison (ZNCC), through classic features (ORB, SIFT), to learned descriptions (DINOv2). Appearance helps when positions are uncertain. It cannot separate two identical cones.
5. **Association.** For each new sighting, decide which known object it is, or that it is new.
   - *Short-term tracking* (ByteTrack) links boxes between consecutive frames by overlap and motion, and forgets an object after it has been out of view for a while.
   - *Persistent identity* keeps a record per object (3D position, size, appearance, every sighting) and matches new sightings to records one-to-one within a frame (the Hungarian algorithm), with "new object" always an allowed answer.
6. **Counting.** Count records, not detections. An unmatched sighting becomes a *provisional* object until more evidence confirms it. Report duplicates, misses and wrong merges separately: a correct total can hide one duplicate and one miss.

## Why the rest of the pipeline matters here

Steps 3 and 5 rely on positions. If the camera path drifts (chapter 3) or depth has the wrong size (chapter 2), the same object comes back at a different place and is counted twice. Good counting needs good geometry first.

## Where the project stands

> **Project result: a small recorded proof of concept, not a count accuracy.** With supplied camera poses and Kinect depth on TUM desk frames, YOLO26x found four of five reference cups. Identity rules were compared on eleven provisional observations: geometry-only and geometry-plus-appearance resolved all eleven; appearance-only left four unresolved. A 60-frame replay exposed a rule bug: once one book had an identity, later new books were refused one, leaving 90 of 95 book sightings unresolved. Fixing that rule gave 6 provisional book identities and 5 unresolved. No independently reviewed inventory exists yet, so fewer unresolved sightings does not prove a better count. (`experiments/06_object_recognition/README.md`.)

Cost is the other half of the brief ("SAM works but is very heavy"). The experiments test whether cheap boxes and simple masks are enough before reaching for a heavy segmentation model, and record the time of every step.

## Try it

Open the published object demo in a browser: `demo_outputs/06_objects_in_3d.html`. It shows detections, 3D positions and provisional identities on the desk recording.

## Further reading

- `experiments/06_object_recognition/README.md`: methods table, what is established, and the proposed comparison protocol.
- [research/products](../research/products/README.md) for commercial context.
