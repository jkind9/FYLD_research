# InfiniteVGGT: Visual Geometry Grounded Transformer for Endless Streams

**Take-away:** InfiniteVGGT studies how to keep image-based geometry running over long streams without storing every earlier frame. Long operation and bounded memory do not by themselves guarantee stable site measurements.

## Citation and sources

Shuai Yuan, Yantai Yang, Xiaotian Yang, Xupeng Zhang, Zhonghao Zhao, Lingming Zhang and Zhipeng Zhang. arXiv preprint, submitted 5 January 2026. arXiv:2601.02281. A final conference venue has not been verified.

- [Author paper record and abstract](https://arxiv.org/abs/2601.02281)
- [Author-linked official code](https://github.com/AutoLab-SAI-SJTU/InfiniteVGGT)

## What it does

A method that considers all earlier images can become too expensive as a recording grows. Forgetting older views can also lose information needed to keep geometry consistent.

InfiniteVGGT proposes a bounded rolling memory for a streaming geometry network. It prunes stored attention information as new frames arrive, aiming to retain useful scene context while controlling memory. The input is a sequence of images. The output concerns continuing visual geometry estimation rather than a certified map of the work area.

## Evidence and limits

The **arXiv abstract** claims improved long-term stability and introduces Long3D, a benchmark with sequences of about **10,000 frames**. This verifies what the authors propose and claim. Detailed evaluation tables, exact hardware, resolution and runtime have not been checked for this note. No benchmark result was reproduced here.

“Endless” describes the intended streaming design. A finite benchmark cannot prove an error-free infinite run, recovery after every failure or persistent accuracy across changing site conditions. Those are separate questions for application testing.

## Relevance to a site capture

Our proposed experiment would test whether dimensions remain stable after a long walk and a return to an earlier location. Include periods of weak texture and moving objects. Compare early and late geometry against independent references, and preserve tracking failures instead of hiding them in a smooth visualization.

A stable-looking rendered sequence is not proof that the underlying map has stopped drifting. Area outputs must still explain scale, observation coverage and uncertain boundaries. Workers should capture only from approved safe locations; longer recording is not a reason to demand inaccessible views.

Neither code nor weights were downloaded or executed in this workspace. Exact code, checkpoint and benchmark permissions for company use remain unresolved.

## Questions for the next experiment

1. Does revisiting a measured region expose accumulated scale or pose error?
2. What is lost when old frame information is removed?
3. After permissions are checked, can a long recording remain within the actual hardware budget?
