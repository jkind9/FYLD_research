# Limitations

The colour/depth demonstration uses supplied metric frames from one short indoor TUM sequence. A separate image-only demonstration produces sparse points at arbitrary scale. These preliminary experiments check parts of a reconstruction pipeline. They do not establish depth estimation from ordinary smartphone video, on-device throughput or performance on a construction site. Final implementation validation remains pending.

| Limitation | Consequence | Required evidence |
| --- | --- | --- |
| Metric depth is supplied | Scale is inherited from the sensor dataset | Independent phone lengths and depth checks; image-only scale anchors |
| Reference poses are used by the oracle | Oracle geometry isolates tracking error but does not prove a tracker works | Estimated-pose trajectory comparison with failures counted |
| One 120-frame indoor subset | Accuracy and timing do not generalize to other scenes | Longer, dynamic, outdoor and repeated captures |
| World-up transform is explicit but gravity unverified | A projected footprint may use an assumed orientation | Recorded gravity or independent plane/orientation validation |
| Points are fused; mesh is not validated | A point preview does not prove a continuous or watertight surface | Permitted mesh pipeline plus independent surface errors |
| Occlusion and invalid depth leave unknown regions | Area can be underestimated or falsely filled by a later method | Coverage masks and boundary tests that preserve unknown space |
| Tracking can drift or fail | Surface fusion and area can change with camera errors | Revisit/recovery experiments and independent dimensions |
| Textureless, reflective, transparent or moving surfaces | Depth/registration can be unreliable | Captures and failure examples for each relevant condition |
| Optional assets have unresolved terms | Public code links do not clear company execution | Separate code, weight and dataset permission evidence |
| No phone resource measurement | Desktop wall time cannot be called mobile real time | Device-specific latency, memory, heat and energy measurements |

Reported stereo disparity errors, camera trajectory errors and area errors measure different things. Paper hardware and resolutions also differ. No numerical ranking across these sources is claimed.

An observed surface footprint must state its projection plane, units, boundary rule and unknown coverage. It cannot certify working clearance, structural integrity, hidden utilities or legal site boundaries. Those require separate measurements and responsible site procedures.

The research list is a focused set of verified leads, not an exhaustive review. Some primary endpoints failed to fetch, including the EuRoC DOI landing page. Such failures are recorded rather than repaired with guessed metadata or unofficial downloads.
