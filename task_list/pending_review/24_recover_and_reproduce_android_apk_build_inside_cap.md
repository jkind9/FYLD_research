---
id: "24"
title: Recover and reproduce Android APK build inside capture experiment
status: pending_review
approval_status: approved
priority: MED
type: infra
blocked_by: []
blocks: ["08"]
verification_test: experiments/01_camera_capture_delivery/tests/test_build_recipe.py
plan_reviewed: 2026-10-04 PASS
files:
  - experiments/01_camera_capture_delivery/**
  - .gitignore
  - pytest.ini
docs:
  - experiments/01_camera_capture_delivery/README.md
  - README.md
baseline_metric:
  source: experiments/06_object_recognition/README.md
  field: Recover and reproduce Android APK build inside capture experiment
  baseline_value: "0 repository-owned reproducible APK build recipes"
  target: "1 reproduced smoke build and 1 verified container build route or an explicit recorded container blocker"
created: 2026-10-03
last_updated: 2026-10-04
superseded_by: null
---

# Task 24: Recover and reproduce Android APK build inside capture experiment

## In plain English

Put the phone app build recipe and source files under the capture experiment. Rebuild the existing smoke app from those files, then verify a container route. Export the APK and instructions so phone installation does not depend on the workstation connection.


Documentation reconciliation: the previously declared mobile deployment directory/README does not exist. The existing stage01 README owns capture/build/handoff instructions; no separate documentation directory is created. Historical WSL/APK receipts remain unchanged.

## What

Recover exact WSL smoke-build source/commands and own them in stage01 app/build folders; create pinned reproducible WSL/container tooling and APK export evidence. Task08 retains actual camera capability/capture implementation and handset testing.

## Why

Stage01 currently contains only a README; smoke app/build files remain in WSL home. A verified local installation is not a repo-reproducible build.

## How

### Reuse evidence

| Claim | Existing owner | Callers/consumers | Evidence |
|---|---|---|---|
| Verified WSL route and smoke build are recorded | stage01 toolchain receipt | new build recipe | experiments/01_camera_capture_delivery/README.md:34 |
| Offline APK handoff already belongs to Task08 | phone feasibility plan | mobile deployment | task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:60 |
| Existing first-party smoke source is nine bytes and has no camera feature | WSL smoke source | recovered `experiments/01_camera_capture_delivery/app/main.py` | /home/jkind/android-prep/app/main.py:1 (`print(42)`) |
| Native compile control already exists | WSL first-party C source | recovered `experiments/01_camera_capture_delivery/native/smoke.c` | /home/jkind/android-prep/smoke.c:1 (`int add(int a, int b) { return a + b; }`) |
| Saved distribution fixes bootstrap, ABI, minimum API and recipes | generated p4a dist metadata | build preflight and isolated packaging | /home/jkind/android-prep/p4a-storage/dists/unnamed_dist_1/dist_info.json:1 |
| Generated package and Android toolchain settings are available | saved Gradle project | reconstructed packaging command | /home/jkind/android-prep/p4a-storage/dists/unnamed_dist_1/build.gradle:8; /home/jkind/android-prep/p4a-storage/dists/unnamed_dist_1/build.gradle:24 |
| Saved Gradle wrapper uses the 8.14.3 all archive | generated wrapper properties | isolated build | /home/jkind/android-prep/p4a-storage/dists/unnamed_dist_1/gradle/wrapper/gradle-wrapper.properties:6 |
| No equivalent repository build/export implementation exists | scoped reuse scan | proposed new helpers | experiments/01_camera_capture_delivery/README.md:106 (proposed tree); `rg` of experiments excluding runs found only this outline |

Read/copy only first-party app/build source and dependency provenance from the existing WSL setup; do not copy caches, SDK payloads or credentials. Document proposed app/, native/, build/Dockerfile, build scripts and test ownership. Pin versions/checksums and build from a clean documented environment. Recover the known WSL route before measuring Docker equivalence; do not call the container route verified beforehand. Export APK, signature/manifest/hash record and handoff README in mobile deployment. This smoke APK is not the camera-test deliverable; Task08 supplies offline on-device tests/status and results.

### Concrete recovery sequence, 4 October 2026

1. Copy only the two first-party source files into `experiments/01_camera_capture_delivery/app/main.py` and `experiments/01_camera_capture_delivery/native/smoke.c`. Require SHA-256 `58a44735ffdfa6b14977516ad6e6e642d477999cd361537028f2d6b99e07ad68` and `23cf718c49184de97b2e966b9426178d82ba04d4f3b591c7ed5fcb6b623f7afb`, respectively. Store sanitized generated settings in `experiments/01_camera_capture_delivery/build/toolchain.json`; no absolute home paths, keys, shell history, SDK payloads or build caches go into Git. Add a narrow `.gitignore` exception for first-party stage01 build helpers, since its inherited `build/` rule otherwise hides the recipe. Verify every recipe input/helper is tracked before the commit/fresh-clone check. Record the existing APK as a predecessor with SHA-256 `b54aee1b73cb1e80539e61e57fa6881fb47c5007ddcd9870df61f9751089fdcf`, not as the new reproduced output.
2. Implement `experiments/01_camera_capture_delivery/build/recipe.py` for validated settings, safe argument arrays, provenance and APK checks; `experiments/01_camera_capture_delivery/build/build-apk.sh` for Linux execution; and `experiments/01_camera_capture_delivery/build/export-apk.ps1` for Windows handoff. The installed entry point is `/home/jkind/.venvs/p4a-2026.05.09/bin/p4a apk`. Its `--help` and the saved bootstrap `build.py --help` were inspected read-only. Reconstruct the command with `--bootstrap=sdl2 --requirements=python3 --arch=arm64-v8a --android-api=36 --ndk-api=24 --ignore-setup-py --private=<repo-app-copy> --package=org.fyld.toolchainsmoke --name=FYLDToolchainSmoke --version=0.1 --numeric-version=10241 --minsdk=24 --java-build-tool=gradle`, explicit SDK/NDK/storage/dist paths and debug packaging. This is reconstructed from persisted settings and the installed API; the exact original shell command was not persisted or recovered. Do not claim identical command history.
3. Before invoking a build, verify actual installed versions against the pins below. Pass only explicit allowlisted environment and settings. Run the NDK compile control using installed `aarch64-linux-android24-clang`; verify ELF64 and AArch64 output. A mismatch fails with a recorded prerequisite error rather than selecting another version. Confirm generated Gradle project still uses the inherited plugin, build tools and wrapper before packaging.
4. Run an isolated warm packaging reproduction from a new scratch copy of the saved generated distribution. Keep installed SDK/NDK/p4a and predecessor sources read-only. Pass all nine persisted recipes and the inherited distribution name so perfect-match validation accepts the saved distribution; use `--require-perfect-match --no-allow-replace-dist` so incompatibility fails. Set Gradle offline in the scratch Gradle home and route package-manager proxy requests to a closed localhost port. Copy only cached Gradle state into scratch. This packages the app against already-built Python/SDL libraries. It is not a clean cross-compilation. Record the exact command, cache artifact hashes, exit status, logs and elapsed time.
5. Run a separate clean dependency build in an empty p4a storage directory only from the already-cached source archives, with a new distribution name. Set the offline Gradle init script under `GRADLE_USER_HOME/init.d` and point HTTP/HTTPS/ALL proxy settings at `127.0.0.1:9` with `NO_PROXY` empty. This allows installed p4a and Gradle to use cached inputs while preventing network acquisition. Preserve a separate clean-build receipt and cache hash record. A failed cache-only build records its missing pinned input and does not silently switch versions.
6. Inspect the installed Docker engine and local image digests. Run only cached images with networking disabled and no mounted project data while checking OS/Python/JDK prerequisites. For an eligible pinned image, build from that image without pulls and mount SDK/dependency inputs read-only and scratch/output writable. Do not change daemon configuration or install Docker. Do not call a WSL build a container build. If there is no local compatible image, record the exact image digests and mismatched prerequisites. Leave Task24 in pending review with container build as a named follow-up unless the owner waives it.
7. Verify the new APK with installed build-tools `35.0.0/apksigner verify --verbose --print-certs` and `aapt dump badging`, and inspect archive native paths. Assert package `org.fyld.toolchainsmoke`, version name `0.1`, version code `10241`, min API24, target API36, debug flag and exactly `arm64-v8a` native architecture. Record certificate fingerprints, signature verification output and APK SHA-256, but never copy signing keys. Generated debug keys stay in scratch or the existing external Android home; no release signing is performed. Verify embedded first-party application source corresponds to the recovered hash, allowing recorded bytecode/archive packaging rather than assuming a plain `main.py` ZIP member.
8. Export a new unique `mobile deployment/smoke_<run-id>/` bundle containing the APK and JSON verification receipt. Verify copied bytes and receipt references before an atomic same-directory rename publishes the bundle. Refuse overwrite; an interrupted staging bundle remains unaccepted and never replaces an existing verified APK. Update the existing stage01 README and root README with the actual command, prerequisite paths, output SHA/signature, build scope and container status. The owner will transfer/install the APK. Do not claim handset execution, camera permission, capture support or on-device test results from this packaging smoke app.
9. Keep test scratch outside the repository. Use `python -B tools/check.py ...`, which assigns each run a unique operating-system temp directory for pytest, coverage and tool caches. Ignore stray pytest scratch names and keep pytest from collecting them, while preserving the separate frozen Task13 scratch directory.

### Inherited build pins

| Setting | Value | Provenance |
|---|---|---|
| Ubuntu / host Python / JDK | 24.04.4 / 3.12.3 / 17.0.20.1 | inherited experiments/01_camera_capture_delivery/README.md:34-40 |
| p4a release / release commit | 2026.05.09 / 58d21141f17c889bf8585f5665921d72028f8831 | inherited task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:95 |
| p4a wheel SHA-256 | 79a58606a78ed3cec1aba110876a414d4aa988f082385d68393e208d009e1e94 | inherited task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:97 |
| SDK API / build tools / platform tools | 36 / 35.0.0 / 37.0.1 | inherited experiments/01_camera_capture_delivery/README.md:43-45 |
| NDK / compile minimum | 28.2.13676358 (r28c) / API24 | inherited experiments/01_camera_capture_delivery/README.md:46 |
| Android Gradle Plugin / wrapper | 8.11.0 / 8.14.3 all | inherited saved build.gradle:8 and gradle-wrapper.properties:6 |
| Wrapper all SHA-256 | ed1a8d686605fd7c23bdf62c7fc7add1c5b23b2bbc3721e661934ef4a4911d7c | inherited task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:97 |
| Android Python recipe | 3.14.2 | inherited experiments/01_camera_capture_delivery/README.md:48; saved dist metadata confirms major/minor3.14 only |
| Bootstrap / ABI / setup mode | sdl2 / arm64-v8a / ignore setup.py | inherited saved dist_info.json:1 |
| Package / app label / version | org.fyld.toolchainsmoke / FYLDToolchainSmoke / 0.1 (10241) | inherited saved build.gradle:24-31 and src/main/res/values/strings.xml:8 |

The owner authorised overnight reversible build recovery. These are inherited smoke build settings, not newly selected camera or model settings. Plan review, focused verification and finished diff review remain required before closure. Docker image digest, complete cached dependency hashes, scratch path handling and embedded source verification are execution facts still to recover; do not invent them in advance.

## Invariants and recovery

| Producer/owner | Consumer | Representation | Survives restart? | Evidence |
|---|---|---|---|---|
| Recorded WSL toolchain and smoke-app recipe | clean WSL/container build | pinned dependency versions/checksums, app source and build commands | repository recipe plus provenance | experiments/01_camera_capture_delivery/README.md:34 |
| Recorded verified smoke build and required offline handoff | phone export | arm64 APK plus signature/manifest/SHA256 and installation instructions | exported files proposed | experiments/01_camera_capture_delivery/README.md:52; task_list/open/08_check_phone_capture_feasibility_alongside_reconstr.md:60 |

Source of truth is the recovered first-party recipe and pinned toolchain provenance. Windows/WSL/container filesystem boundaries carry source/build inputs and verified APK outputs. Build in isolated scratch space; interrupted builds cannot replace an exported verified APK. Export a complete verified bundle before changing its handoff pointer; restart rebuilds in clean scratch space. Fresh deployment installs documented prerequisites, builds the smoke app, verifies the APK, then exports it. Preserve the existing WSL installation and receipts. A container blocker remains a named follow-up in pending_review until fixed or explicitly waived by the owner; it is not a verified build route. Camera app/device testing stays in Task08.

Scratch state transitions are preflight -> source copy -> native compile -> package -> signature/manifest/archive verification -> staged export -> verified publish. A failure before publish leaves only an identifiable scratch or staging run; the next invocation uses a new run ID, not a partial prior APK. Run IDs are unique and no shared latest pointer is required. Before and after execution, verify hashes of the two predecessor source files and original APK. All build process argument arrays keep paths separate from shell syntax; reject nonexistent inputs, symlinks that escape approved source/output roots, duplicate destinations and inconsistent APK metadata. Signing secret contents must never appear in receipts or logs. Existing debug certificate identity may change in isolated scratch; record the actual fingerprint and do not require predecessor byte identity.

## Hyperparameters

hyperparameters n/a: build recovery only; inherit the recorded toolchain pins and document any proposed dependency change before using it. This task selects no camera, model or performance-run settings.

## Verification

Contract test: experiments/01_camera_capture_delivery/tests/test_build_recipe.py (proposed where not yet present). The isolated warm packaging build produces an arm64 APK with recorded package/toolchain provenance, verified signature/manifest and exported SHA256. The documented clean dependency route receives a separate actual result or explicit prerequisite gap; it is not certified by the warm build. The first camera-test APK from Task08 must install/run without a PC and show pass/fail/skipped results. Do not require byte-identical debug APKs unless timestamps/signing are reproducibly controlled. No phone compatibility is claimed by compilation.

Focused controls must reject wrong source hash, wrong p4a/NDK/API pins, missing SDK/build tools, unsupported ABI, signature verifier failure, missing native libraries, wrong package/version/minimum/target, malformed verifier output, path escape, failed copy, receipt/APK hash mismatch and destination overwrite. A simulated interruption before publish must leave 0 accepted bundles and preserve any prior bundle; a complete fixture must publish exactly 1 verified bundle. Fixtures use synthetic verifier outputs/APK ZIPs and are labelled controls, never real build evidence. Write the recipe/export controls first or obtain independent test review; target at least 80% changed Python implementation coverage. Actual WSL APK acceptance requires the installed verifier outputs and real hashes, not fixture success. Warm packaging and any cold dependency build each receive their own receipt. Docker runtime readiness and successful container build are separate gates. Measure 1 warm reproduced WSL smoke APK; record cold/container results as passed or unavailable with concrete reasons.

Before: 0 repository-owned reproducible APK build recipes. Target: 1 reproduced smoke build and 1 verified container build route or an explicit recorded container blocker. Targets count completed evidence/control artifacts; they are not operational accuracy thresholds. No performance improvement is assumed. At implementation, write meaningful controls first and observe failure, or obtain independent test review. Cover expected values, empty/one/many boundaries, invalid input, failure/recovery and reference separation. Changed implementation coverage must be at least 80%; lint/type and required integration/browser checks must pass. Record actual measurements and all unresolved follow-ups before closure.

## Receipts

| Field | Value |
|---|---|
| Closing commit | None; this goal remains in progress and no goal work has been committed |
| Files changed | `.gitignore`; `pytest.ini`; `experiments/01_camera_capture_delivery/app/main.py`; `native/smoke.c`; `build/recipe.py`, `verify.py`, `verify_bytecode.py`, `warm.py`, `export.py`, `build-apk.sh`, `export-apk.ps1`, `toolchain.json`, `container-readiness.json`; `tests/test_build_recipe.py`, `tests/test_warm_build.py`; `experiments/01_camera_capture_delivery/README.md`; root `README.md` |
| Test status | 110 focused tests passed in WSL; branch coverage 82% across the five build Python modules; Ruff passed. `apksigner verify --verbose --print-certs` passed and `aapt dump badging` confirmed package `org.fyld.toolchainsmoke`, version `0.1` (10241), min API 24, target API 36, debug flag and only `arm64-v8a`. The Windows run collected 110 tests but could not create/read its temporary test files in the restricted user-temp folder; it did not pass or validate product behaviour. |
| Before measurement | 0 repository-owned reproducible APK build recipes |
| After measurement | Final verified warm cached packaging build completed in 27.34 s. APK SHA-256 `2a1f1f821408d637cbb8416e465b273245c5813013a73684f7f70dab45fc26e5`; source SHA-256 matches recovered `print(42)` source `58a44735ffdfa6b14977516ad6e6e642d477999cd361537028f2d6b99e07ad68`; debug certificate SHA-256 `45e634374292b269842a381e50dc1bb08d6b30db388ed4572a880d9b1670e1c3`. APK and verification record are in ignored `mobile deployment/smoke_20261004_reviewed/`. |
| Delta | Recovered one repository-owned warm packaging route and one verified APK handoff. This APK only runs the existing `print(42)` smoke app; it has no camera permissions, capture UI or depth test. |
| Decision-gate outcome | Warm build, APK provenance, signature, manifest, ABI and offline bundle passed. The compressed Python bundle contains 68 members and is now required by the verifier; the independent diff review passed with no remaining findings. The cache-only clean build stopped at the missing cached JPEG source archive (`sdl2_image` attempted to clone `https://github.com/libsdl-org/jpeg.git`; the local-only proxy blocked access). One repeat attempt used the wrong Gradle cache root and stopped before producing an artifact; the corrected run passed. Docker was available, but none of five inspected local image digests had the required Ubuntu 24.04.4, Python 3.12.3 and OpenJDK 17.0.20.1 combination. No image was downloaded and no container build was run. Twenty-four disposable pytest scratch folders were removed from the repository root; `.task13_pytest_tmp_20261003` was retained. `tools/check.py` already routes test scratch to the system temp folder; `.gitignore` and `pytest.ini` now cover stray pytest scratch names, and the default pytest search includes the replay tests. Root and capture READMEs now record the verified warm build, clean/container limitations and pytest scratch policy. Task08 may reuse the verified WSL APK route while the container follow-up remains open. |

still open because the pinned container image/build follow-up remains outstanding; no compatible image was available locally, and no image was downloaded.
