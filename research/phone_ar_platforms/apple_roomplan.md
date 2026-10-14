# Apple RoomPlan

**Take-away:** RoomPlan offers an indoor room model from supported Apple hardware. Its simplified walls and furniture are useful for room planning, but are a different output from a measured irregular work surface.

## Platform and sources

Apple developer overview and documentation. RoomPlan was presented in the WWDC22 material linked by Apple. The platform sources were checked on 1 October 2026; they are not a fixed scientific benchmark.

- [Official RoomPlan overview](https://developer.apple.com/augmented-reality/roomplan/)
- [Official API documentation and sample-code entry point](https://developer.apple.com/documentation/roomplan)
- [Apple developer terms and agreements](https://developer.apple.com/support/terms/)

## What it does

Apple describes a Swift interface powered by ARKit that uses the camera and LiDAR scanner on supported iPhones and iPads. It recognizes room components and produces a floor-plan-style 3D representation.

The overview's **Parametric representation** section says USD or USDZ exports include dimensions and placement of components such as walls and cabinets, together with furniture types. “Parametric” means the model represents recognized objects through dimensions and structure rather than recording every small surface detail.

## Evidence and limits

Apple's **Real-time scanning with LiDAR** section describes capture guidance and live progress feedback. The overview provides no independently verified frame-rate, resolution or dimensional-error benchmark for this project's intended scene. Those fields are not checked here. No handset has been selected or captured.

A room component model can simplify imperfect or partially observed surfaces. Therefore an attractive floor plan must be checked against independent dimensions before its measurements are adopted. It should not be treated as a dense observation of every recess, opening or obstacle.

## Relevance to a site capture

Our interpretation is that RoomPlan could be tested for indoor fit-out or room documentation. Its suitability for an open construction site, temporary works or uneven terrain is unproven. Define whether the required area is a room floor plan or an observed surface before choosing it.

Separate source observations from model assumptions in any viewer. A recognized wall or cabinet is not proof of empty space behind it. Coaching should guide only captures available from safe approved positions, and missing rooms or inaccessible regions should remain explicit.

No RoomPlan code or phone session was executed here. Company SDK and sample-code permission must be checked under the applicable Apple agreements; a public overview does not resolve those obligations.

## Questions for the next experiment

1. Does the intended indoor scene fit the recognized room components?
2. How do exported dimensions compare with independent measurements?
3. Can incomplete observations be retained clearly instead of appearing as a complete plan?
