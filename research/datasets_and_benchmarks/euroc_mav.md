# EuRoC MAV: stereo and inertial tracking with reference motion

Michael Burri, Janosch Nikolic, Pascal Gohl, Thomas Schneider, Joern Rehder, Sammy Omari, Markus W. Achtelik and Roland Siegwart. **The EuRoC micro aerial vehicle datasets.** International Journal of Robotics Research, 2016. [Paper DOI](https://doi.org/10.1177/0278364915620033). [Current official ASL dataset page and parser link](https://projects.asl.ethz.ch/datasets/euroc-mav/). [Current data DOI](https://doi.org/10.3929/ethz-b-000690084).

## Main takeaway

EuRoC is a useful reference for testing camera motion from a calibrated stereo pair and inertial measurements. It tests a different sensor contract from the current single RGB camera plus supplied depth. It is a flying-robot dataset, so phone results cannot be inferred directly.

## What is supplied

The publisher describes monochrome stereo images, synchronized inertial data, camera calibration, camera-to-inertial calibration and reference motion/structure. Its **Available Data** section lists **two WVGA cameras at 20 FPS** and an inertial measurement unit at **200 Hz**. Reference systems include Vicon and a Leica MS50 tracker/structure scan. [Official data specification](https://projects.asl.ethz.ch/datasets/euroc-mav/).

Inputs are the sensor observations and calibration. A tracking algorithm would output its estimated trajectory and possibly a map, compared with the independent references. The dataset itself is not a depth estimator or phone application.

## Evidence and caveats

The publisher's specification and **Known issues** section were checked. The page notes independent camera exposure, limits to reference synchronization and possible laser-tracker degradation during dynamic motion. Exact numerical resolution, algorithm hardware, runtime and paper benchmark tables have **not been checked** here. Capture rates must not be read as processing rates.

The current page says files moved to the ETH Research Collection. The data DOI is verified as a publisher link, but archive fetching and terms remain **unverified**. No archive access, download or execution is claimed. The dataset paper DOI and data DOI identify different things.

## Relevance to FYLD and scale

EuRoC could test a future stereo/inertial backend before phone integration. It would help reveal calibration and timing mistakes that a simple RGB-D adapter cannot expose. A stereo baseline gives a physical scale source when its calibration is used correctly. Inertial observations add units and timing requirements; they do not remove the need to validate scale and drift.

FYLD phones may not expose synchronized dual cameras or inertial observations with the same quality. Their exposure, rolling shutter, stabilization and camera switching need separate capture checks. Safe worksite recordings also differ from a robot flying through a prepared space. Independent site dimensions and surface coverage remain necessary.

## Licence and two next questions

Dataset permission for company R&D is unresolved in this review. The parser's code licence and any estimator/checkpoint terms are separate and have not been cleared here. No pretrained weights are inherent to the dataset.

1. What are the current archive licence terms, and do they permit the proposed company experiment?
2. Which synchronization and calibration errors most affect scale when adapting the same estimator to actual phone recordings?
