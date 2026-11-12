# Package-only app and report validator

This folder holds the smallest Android app the build route can package, and the Python checks for camera reports exported by the Camera2 diagnostic app. It belongs to [experiment 01, camera capture and delivery](../README.md).

| File | What it does |
|---|---|
| `main.py` | One line, `print(42)`. It is the Python source packaged into the smoke APK (an app that only proves the build chain works). It requests no permissions and reads no camera. |
| `capture_report.py` | Validates a camera report (`report.json`) and the files next to it before they are shown or exported. |

`capture_report.py` exposes three functions, each stricter than the last:

- `validate_report(report)` checks the report fields (`schema_version` 1, session ID, device fields, a unique ID and status for each check, one record for each captured image) and returns a copy.
- `validate_export(report, bundle_root)` also requires `status` to be `complete`, then checks that every listed file exists inside `bundle_root` with the recorded size and SHA-256 hash.
- `validate_phone_session_export(report, bundle_root)` also requires at least one image, a passing `single_camera_control` check, and that this check's details match every exported image.

`research/experiments/shared/phone_session.py` takes `validate_phone_session_export` as an argument when it reads an export. `src/walkthrough/steps/capture.py` imports the module by its path.

The report format here is the Camera2 diagnostic report (`schema_version`, checks with `id`). The FYLD capture app writes a different check report (`schema`, checks with `name`), which [`host/report.py`](../host/README.md) validates.

## How to run it

Neither file has a command line. `main.py` runs only inside the APK, built by [`build/`](../build/README.md). Check the validator with:

```text
.venv/Scripts/python.exe -m pytest research/experiments/01_camera_capture_delivery/tests/test_capture_report.py
```

## Where results are recorded

The build and export results are in the [experiment 01 README](../README.md).
