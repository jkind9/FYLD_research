# User-supplied ORB and depth sources

Checked on 2 October 2026. All eight supplied links are accounted for below. They add three useful directions: sparse tracked geometry can improve dense depth, learned depth can assist tracking, and lighting can densify a phone reconstruction. These remain distinct experiments because each has a different source of scale and error.

The [current ORB comparison](../README.md) covers contemporary alternatives. The [Android implementation review](../android/README.md) covers the supplied Android repository in more detail. Older papers here are useful design evidence; they do not establish present-day superiority.

## 1. Mobile photometric stereo with keypoint-based SLAM for dense 3D reconstruction

Maxence Remy and colleagues, 3DV 2019, DOI 10.1109/3DV.2019.00069. [Supplied university PDF](https://www.cvg.ait.kyushu-u.ac.jp/papers/2019/3DV2019_Max.pdf) was readable.

The method combines ORB camera poses and sparse points with recovering shape from changing illumination (photometric stereo). Its Huawei P20 demonstrations use the phone flashlight, calibrated 960×720 images and fixed capture settings. This is useful evidence that ordinary phone hardware can support a dense-reconstruction route beyond stereo matching.

The scene assumptions are restrictive: close stationary objects, diffuse surfaces and dark surroundings. Scale is arbitrary, and dense CPU reconstruction takes 9–19 minutes. The examples emphasize dense appearance rather than independently surveyed metric surface error. No reusable code/licence release was verified. For our reconstruction experiment, test lighting-based densification separately from pose quality; it does not establish outdoor work-area measurement.

## 2. Scale aware dense dynamic SLAM for monocular, stereo and RGBD cameras

Nuo Cen, Yi Xu, Tuck-Whye Wong and Yao Zheng, Scientific Reports 16:10285, 2026. [Supplied Nature article](https://www.nature.com/articles/s41598-026-41208-9) was accessible.

SDMFusion combines ORB-SLAM3, predicted metric depth from Depth Anything V2, YOLO11s segmentation and motion checks. It is a current hybrid reference for rejecting moving features while building dense geometry. In monocular mode, scale comes from learned pseudo-depth; it still needs an independent physical-dimension check.

Reported experiments use an i9/RTX 4080 SUPER and Jetson AGX Orin timing, plus RealSense-equipped drone capture. Authors report five trials without post-hoc scale correction; dense-map assessment is qualitative, and dominant moving objects remain difficult. No phone result or system repository was verified. Article CC BY-NC-ND 4.0 does not establish code or model permissions. Test dynamic-feature rejection with supplied depth/poses before judging the full combined pipeline.

## 3. DF-ORB-SLAM

[Supplied repository](https://github.com/834810269/DF-ORB-SLAM) describes monocular SLAM with estimated depth and optical flow. Visible files follow ORB-SLAM2, with [inherited GPLv3 terms](https://github.com/834810269/DF-ORB-SLAM/blob/master/LICENSE.txt).

The README has a title and two images, with no paper citation, reproducible benchmark or build guide. No phone result or dynamic-object filtering claim was established. Eighteen commits are visible, but the latest update date could not be verified because history/API retrieval failed. This is a code-inspection lead, not a validated current ORB successor. Weight/dependency terms and its actual pose/depth interface remain unresolved.

## 4. Monocular based 3D depth estimation and SLAM integration

Yasser E. El-Alfy and Uthman Baroudi, Drone Systems and Applications 13:1–14, 2025, DOI 10.1139/dsa-2024-0025. The [exact supplied ScienceDirect URL](https://www.sciencedirect.com/org/science/article/pii/S2564493925000062) is identified through indexed primary content and the [author university record](https://pure.kfupm.edu.sa/en/publications/monocular-based-3d-depth-estimation-and-slam-integration/). Direct publisher fetches returned 403; exact publication-day records conflict, so only the year is retained.

It feeds learned depth into a MATLAB ORB-SLAM2 example. Depth-factor/calibration settings are adjusted to predicted scale. The abstract claims 34–54% trajectory improvement, with one TUM office sequence and preliminary Tello drone work. This supports investigating the connection between depth and tracking; it does not establish phone performance or robust metric scale. Training separation, parameter adjustment, compute and dense-surface accuracy need checking. No code/checkpoint permission was verified.

## 5. Monocular Depth Estimation enhancement by depth from SLAM Keypoints

Lorenzo Andraghetti, Bologna master's thesis, academic year 2017/18, defended 5 October 2018. [Supplied PDF](https://amslaurea.unibo.it/id/eprint/16626/1/tesi.pdf) and [university record](https://amslaurea.unibo.it/id/eprint/16626/) were accessible.

Sparse depth/disparity guides a Monodepth-derived dense model. The actual landmarks come from stereo ORB-SLAM2 because correct scale is required. For the ResNet model trained on KITTI and evaluated on KITTI odometry 03, Table 6.6 reports absolute-relative depth error 0.1380 for the baseline, 0.1008 with sparse SLAM input and 0.0966 with sparse reference input. Much of the other testing uses sampled ground truth; a reduced Eigen split has 652 rather than 697 images.

This is useful for a supplied-sparse-depth control followed by a real tracker-input test. It does not demonstrate self-scaling monocular phone capture. Strong sparse-input loss can overfit inaccurate points; IMU/GPS scale is future work. No handset runtime or current code/weight terms were identified.

## 6. Depth Reconstruction Based Visual SLAM Using ORB Feature Extraction

Yatharth Ahuja and colleagues, Journal of Image and Graphics 10(4):172–177, December 2022, DOI 10.18178/joig.10.4.172-177. The [supplied Semantic Scholar PDF](https://pdfs.semanticscholar.org/a72c/681a600ad735fc1c8b91a754dc6f778092a6.pdf) matches the [publisher PDF](https://www.joig.net/uploadfile/2022/1027/20221027050852736.pdf) and [publisher record](https://www.joig.net/index.php?a=show&c=index&catid=79&id=310&m=content).

Predicted depth feeds RGB/depth ORB mapping. A reported NYU-V2 depth RMSE of 0.4025 lacks enough established protocol/unit detail for a wider ranking. Its two-image ORB feature timings, approximately 0.3 seconds each, are not full-system phone throughput. The KITTI map is qualitative; no quantitative trajectory comparison establishes better metric SLAM. DenseNet169 versus ResNet architecture descriptions conflict. Article CC BY-NC-ND 4.0 does not establish implementation/weight terms. Keep as a hybrid design lead with weak validation evidence.

## 7. ORBSLAM datasets review

Patrick de Kok, 12 November 2018. [Supplied author's blog](https://pkok.github.io/2018/11/12/) was accessible.

This historical thesis-planning note lists practical dataset checks: shutter type, synchronized camera/IMU streams, sensor placement, extrinsic calibration, reference coverage and noise models. It adds a useful capture checklist, not an implementation result. Its suggested IMU-to-camera sampling ratio is an experiment preference rather than a universal requirement. It predates ORB-SLAM3; current publisher specifications and permissions should govern actual data selection. Blog content declares CC BY-SA 4.0 unless otherwise stated.

## 8. ORB-SLAM2-based AR on Android

[Supplied repository](https://github.com/muziyongshixin/ORB-SLAM2-based-AR-on-Android) is an actual on-device monocular demonstration. The author warns it may be out of date and says they have not worked on SLAM for a long time; the README reports roughly 10 FPS on Xiaomi Mi6/Snapdragon 835. It is a useful JNI/native-camera integration reference, with old OpenCV/NDK dependencies. It does not demonstrate current S23/Redmi support, stereo, inertial fusion or metric scale. Build and inherited licence details are in the [Android review](../android/README.md).

## Experimental connections

| Direction | Independent first test | What must not be assumed |
| --- | --- | --- |
| Sparse geometry improves dense depth | Supply reference sparse depth, then replace it with tracked stereo landmarks | Tracker landmarks have correct scale and no outliers |
| Learned depth assists tracking | Compare supplied benchmark depth and predicted depth on identical images | A metric-labelled model predicts reliable metres in a new scene |
| Moving-feature rejection improves tracking | Change masking/motion checks while holding depth, calibration and images fixed | Removing all recognized people/vehicles preserves enough stationary evidence |
| Torch-based densification | Supply known poses, fixed exposure and controlled illumination | Dark-room close-up results transfer to outdoor sites |
| Android execution | Replay the same saved capture through desktop and native builds | An APK or demo video establishes calibration, accuracy or sustained throughput |

These sources justify tests, not new acceptance thresholds. Known geometry and independent physical dimensions remain the references for surface and area accuracy.
