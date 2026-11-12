# PC-side tools for phone recordings

This folder holds the host-side helpers of [experiment 01, camera capture and delivery](../README.md): a receiver for the old v1 live stream, a scorer for tape-measured walks, and a checker for check-app reports.

The session readers now live in [`sitescan/session/`](../../../../sitescan/session/README.md), and the capture receiver in `apps/receiver/`.

| File | What it does |
|---|---|
| `accuracy.py` | `score(frames, measured)` scores a v1 walk against a measurements file: loop closure distance and turn, distances between tape-measured checkpoints, tracked fraction, tracking losses, anchor corrections and gaps. It uses the received camera poses as they are, with no alignment or scale fitting. |
| `receiver.py` | `Receiver(root, port=8765)` accepts one v1 phone connection per `serve_one()` call, validates each frame, saves `session.json`, `frames/`, `depth/`, `frames.jsonl`, `report.json` and `summary.json`, and acknowledges each frame. It serves v1 senders only; the capture app sends v2. |
| `report.py` | `validate(report)` and `summarise(report)` check a Redmi check-app report (`schema` 1; every check needs a name and PASS, FAIL or SKIPPED, with a reason unless PASS) and count the results. |

## How to run it

Each file is a script. Run it from the repository root with the project environment:

```text
.venv/Scripts/python.exe research/experiments/01_camera_capture_delivery/host/receiver.py --out research/experiments/01_camera_capture_delivery/runs/phonecheck
.venv/Scripts/python.exe research/experiments/01_camera_capture_delivery/host/accuracy.py --session <session folder> --measurements <measurements.json> --out <scores.json>
.venv/Scripts/python.exe research/experiments/01_camera_capture_delivery/host/report.py <report.json>
```

`receiver.py` prints the PC's addresses to type into the app. The phone and PC must be on the same Wi-Fi, and Windows Firewall must allow the port on private networks. `--port` changes the port (default 8765) and `--sessions N` stops after N connections. The measurements file format is described in [`../field_accuracy.md`](../field_accuracy.md).

## Where results are recorded

The receiver, the report checker and the field-accuracy procedure are described in the [experiment 01 README](../README.md) and [`../field_accuracy.md`](../field_accuracy.md). No tape-measured phone results have been recorded yet.
