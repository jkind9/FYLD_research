# ARCore: commercial use terms

Checked on 14 October 2026 from Google's own pages, after the owner asked whether using ARCore in a product raises commercial issues. This is a reading of the published terms, not legal advice; a product launch should have the terms reviewed by someone qualified.

## Short answer

ARCore can be used in a commercial product. No fee is stated for the core features this project uses (motion tracking, depth, point cloud, planes). The obligations are a user-facing notice, compliance with Google's privacy requirements, and Google's general API terms. The real risks are dependence on Google (it can change or discontinue the service), device coverage (only phones on Google's supported list with Google Play), and a high-risk-use clause to check against how site measurements will be used.

## What the terms require

| Source | What it says |
|---|---|
| [ARCore Additional Terms of Service](https://developers.google.com/ar/develop/terms) (last modified 11 May 2022) | Using ARCore means accepting these terms and the Google APIs Terms of Service; the ARCore terms win where they conflict. The app's own terms must tell users it includes ARCore functionality provided by Google, subject to Google's Terms of Service and Privacy Policy. No building products that "substantially replicate" Google products such as Maps Live View. Cloud Anchors and the Geospatial API may not be used in apps directed to children under COPPA. |
| [ARCore user privacy requirements](https://developers.google.com/ar/develop/privacy-requirements) | Every ARCore app must show, where users can easily find it (for example the main menu or a notice screen): "This application runs on Google Play Services for AR (ARCore), which is provided by Google and governed by the Google Privacy Policy." Cloud Anchors and the Geospatial API need an extra notice when activated ("To power this session, Google will process sensor data (e.g., camera and location).") with a learn-more link. |
| [Google APIs Terms of Service](https://developers.google.com/terms) | §4a.7: no use where failure "could lead to death, personal injury, or environmental damage" (examples given: nuclear facilities, air traffic control, life support). §8a: Google may "discontinue the APIs". §10a: Google may modify the terms. §9: provided "AS IS"; no liability for lost profits or data. §3a: Google "may monitor use of the APIs". §2d: Google may attach additional terms or charges to some uses. |
| [ARCore Android SDK repository](https://github.com/google-ar/arcore-android-sdk) | Downloading the SDK means agreeing to the ARCore Additional Terms; apps must disclose the use of Google Play Services for AR. |

## Risks for this project

| Risk | Why it matters | Mitigation |
|---|---|---|
| Google discontinues or changes ARCore | Google ended its earlier Tango platform; the terms allow discontinuation | Keep tracking behind the walkthrough's tracking contract so another tracker (stella_vslam, BSD-2, tested in `experiments/live_slam`) can replace it |
| Device coverage | ARCore needs a phone on Google's supported list with Google Play and Play Services for AR installed; phones without Google Play cannot run it | Check the fleet's handsets against the list; iPhones would need ARKit instead |
| High-risk-use clause | If measurements are used for safety decisions on site (for example excavation near services), check whether that counts as a use where failure could cause injury | Have the terms reviewed for the intended use; keep a human check on safety decisions |
| Data processing by Google | Google may monitor API use; Cloud Anchors and Geospatial send sensor data to Google | Use only on-device features (tracking, depth); avoid Cloud Anchors and Geospatial unless the privacy notice and data review allow it |

## Used in this project

The Redmi check app (`experiments/01_camera_capture_delivery/phonecheck/`) uses ARCore 1.56.0 on-device features only. It is a test app and does not yet show the required notice; a product build must.
