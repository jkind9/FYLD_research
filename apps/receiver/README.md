# Capture receiver

Receives recordings from the capture app over TCP on the local network. It stores every
message, acknowledges it, and resumes after a dropped connection. The message format is
[sitescan/session/FORMAT.md](../../sitescan/session/FORMAT.md); the framing (a 4-byte length,
a JSON header and a binary payload) is `sitescan/session/protocol.py`.

| Path | What it does |
|---|---|
| [`capture_receiver.py`](capture_receiver.py) | `Receiver(folder, port, on_frame)`: one recording per session id. `Session.open` resumes a stored session. `addresses()` lists this computer's addresses to type into the app |

## Run it

On its own, to record without processing:

```text
.venv/Scripts/python.exe -B -m apps.receiver.capture_receiver --out <folder> [--port 8766]
```

To record and process at the same time, use `python -B -m apps.cli live --out <folder>`.

Each session becomes `<folder>/<session id>/` with `session.json`, `frames.jsonl`,
`cam0/<seq>.png` (grey image), `frames/<seq>.jpg` (colour image), `depth/<seq>.bin` (ARCore
depth), `imu.csv`, `telemetry.jsonl`, `messages.jsonl`, and `summary.json` once the app sends
its end message. A bad message is answered with an error and the connection is closed. A resent
message is acknowledged and not stored again.

## Limits

No authentication or encryption: local network only.

## Tests

`experiments/01_camera_capture_delivery/tests/test_capture_receiver.py` sends recordings from a
fake phone and checks storage, acknowledgements, resends and resumption.
