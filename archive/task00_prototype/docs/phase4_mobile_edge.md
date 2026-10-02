# Phase 5: mobile execution proposal

The filename is retained from the original brief. Running selected processing on the phone is Phase 5 of five. No mobile application or accelerated model is implemented.

Move the smallest useful work first: frame-quality checks, selective frame retention, compression and capture feedback. Keep original timestamps and record which frames were omitted. Test whether these changes preserve tracking and measured geometry before treating reduced upload volume as a success.

Native camera tracking and depth are another path to test. They require supported devices, recorded calibration and clock association, and explicit handling of tracking resets. They are not equivalent to ground-truth poses. [ARCore's depth quickstart](https://developers.google.com/ar/develop/java/depth/quickstart) and [supported-device list](https://developers.google.com/ar/devices) provide Android prerequisites. Apple's [RoomPlan](https://developer.apple.com/augmented-reality/roomplan/) targets room floor plans with camera and LiDAR; outdoor utility mapping requires its own validation.

## Evaluate a portable pipeline

Before moving depth or tracking inference, list every model operation and runtime dependency. Verify a supported mobile runtime can execute them on each target phone. CPU, GPU and platform acceleration paths can differ in memory use, numerical behavior and available operations. Check current Android and Apple runtime documentation when choosing the implementation; do not assume an older acceleration interface remains supported.

Quantization, reduced input resolution and fewer retained frames are separate experiments. Compare each with an unchanged reference using independent measurements, retained observed area and tracking breaks. Record the model revision and conversion settings. A faster model that loses narrow or occluded structures may be unsuitable even if average trajectory error stays small.

| Trial | Measure on each target phone |
|---|---|
| Capture quality checks | Added capture latency, false rejection and retained useful frames |
| Frame selection/compression | Upload bytes, timestamps preserved, map completeness and measurement error |
| Native pose/depth | Calibration, valid depth coverage, drift and reset handling |
| Portable inference | Startup, per-frame latency, memory, supported operations and output differences |
| Sustained use | Battery change, device temperature, thermal slowdown and capture stability |
| Recovery | Backgrounding, camera interruption, low storage and session resume |

Use actual FYLD phone tiers rather than one flagship. Begin with short runs, then repeat realistic capture sessions long enough to expose thermal slowdown. Benchmark foreground capture and processing together; an isolated inference time excludes camera, copying, fusion and display work.

Agree quality, response-time, battery and thermal limits after representative recordings establish a baseline. Those measured limits become go/no-go gates. Current desktop defaults are not product requirements. Keep backend replay as the reference path while testing phone changes, and preserve unknown regions and failure reports in both paths.
