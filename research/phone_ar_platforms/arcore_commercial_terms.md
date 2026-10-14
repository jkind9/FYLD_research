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

## Clause-by-clause check, 14 October 2026

Filled in after the owner asked whether a product can be sold with ARCore. Read from the [Google APIs Terms of Service](https://developers.google.com/terms) (10 sections), the [ARCore Additional Terms](https://developers.google.com/ar/develop/terms), the [ARCore SDK licence file](https://github.com/google-ar/arcore-android-sdk/blob/main/LICENSE) and the [ARCore supported-devices page](https://developers.google.com/ar/devices).

| Clause | What it says | What it means for a product |
|---|---|---|
| SDK licence, section 1 | The ARCore library (`.aar` from Google's Maven repository, the C header, release APKs) is "Governed by the ARCore Additional Terms of Service" | The library is not open source; it is licensed under Google's terms |
| SDK licence, section 2 | Other SDK files (samples) are Apache-2.0 | Sample code can be reused freely |
| APIs Terms §1 | Whoever accepts must be able to bind the company | Accept on the company's behalf, not personally |
| APIs Terms §2 | Use only documented access; Google sets usage limits "in our sole discretion"; Google may compete with your product | No fee or limit is stated for on-device ARCore features |
| APIs Terms §3 | Google "may monitor use of the APIs"; may suspend access "without notice" for suspected breaches; app must keep a privacy policy | Product needs a privacy policy covering ARCore |
| APIs Terms §4 (prohibitions) | No sublicensing or building "substantially similar" client for third parties; no reverse engineering; no high-risk use where failure "could lead to death, personal injury, or environmental damage"; no ITAR data; keep Google's notices | Do not resell ARCore as an SDK to others; do not reverse engineer it; the high-risk clause must be assessed against how site measurements are used |
| APIs Terms §5 | Content sent through the APIs is licensed to Google to provide and improve the APIs; non-public user content needs opt-in before exposure to others | Matters for cloud features (Cloud Anchors, Geospatial); on-device tracking and depth send no content |
| APIs Terms §6 | Required attribution; no implied endorsement; Google may name your product when promoting the APIs | Show the ARCore notice; do not market as Google-endorsed |
| APIs Terms §8 | Google may terminate or discontinue the APIs "without liability or other obligation to you" | Business risk: keep tracking replaceable |
| APIs Terms §9 | "AS IS"; Google's total liability capped at what you paid in the previous 6 months (nothing, for a free API); a business user indemnifies Google against claims from its or its users' misuse | Measurement errors are the product owner's liability, not Google's |
| APIs Terms §10 | Changes take effect no sooner than 30 days after posting; California law; courts of Santa Clara County | Terms can change under a shipped product |
| ARCore Additional Terms | App terms must say the app includes ARCore by Google, subject to Google's Terms and Privacy Policy; no products that "substantially replicate" Google products; Cloud Anchors and Geospatial not in child-directed apps | Add the notice and terms wording; the product is not a Google-product replica |
| ARCore privacy requirements | Show "This application runs on Google Play Services for AR (ARCore), which is provided by Google and governed by the Google Privacy Policy" where users can easily find it | Notice screen or menu entry |
| Supported devices | Only listed devices that "originally shipped with the Google Play Store"; in China through vendor app stores; the Redmi Note 11 Pro is listed with Depth API | Phones without Google Play, or not on the list, cannot run it; check the target fleet |

**Answer to "can we sell a product with ARCore":** nothing in these documents forbids selling a product that uses ARCore on-device. The conditions are the notice and privacy policy, no reselling of ARCore itself, no reverse engineering, an assessment of the high-risk clause for site-safety uses, accepting that Google can change or withdraw it and carries no liability, and a device fleet with Google Play. This is a reading of the published terms, not legal advice; have it confirmed by a qualified reviewer before launch. The open-source replacement map is in [arcore_open_replacement.md](arcore_open_replacement.md).

## Used in this project

The Redmi check app (`experiments/01_camera_capture_delivery/phonecheck/`) uses ARCore 1.56.0 on-device features only. Task92 adds an **ARCore and privacy notice** button at the top of its main screen, with Google's required text, links to Google Play Services for AR and Google's privacy policy, and Google/ARCore terms links. It also describes the images, poses, points and depth sent to the selected computer. The APK builds; checking the screen and links on the Redmi remains part of the [field capture](../../experiments/01_camera_capture_delivery/field_accuracy.md). This research notice does not establish that a product's privacy policy or terms have been reviewed.
