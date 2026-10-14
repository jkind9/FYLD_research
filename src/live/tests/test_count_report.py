"""count_report splits new live identities by distance to the nearest same-class object, confidence and sightings."""

import json

from src.live import count_report


def detection(label, confidence, outcome, object_id, nearest):
    return {"label": label, "confidence": confidence, "outcome": outcome, "object_id": object_id, "nearest_same_class_m": nearest}


RECORDS = [
    {"detections": [detection("chair", 0.9, "new", "object-0001", None), detection("cup", 0.3, "new", "object-0002", None)]},
    {"detections": [detection("chair", 0.8, "matched", "object-0001", 0.1),
                    detection("chair", 0.4, "new", "object-0003", 0.5)]},
    {"detections": [detection("chair", 0.7, "matched", "object-0001", 0.2),
                    detection("chair", 0.6, "new", "object-0004", 2.0),
                    detection("chair", 0.6, "unresolved_ambiguous", None, 0.3)]},
    {"stage_ms": {}},  # an update skipped before detection has no detections
]


def test_split_of_new_identities(tmp_path):
    path = tmp_path / "updates.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in RECORDS))
    report = count_report.report(path)
    assert report["identities"] == 4 and report["unresolved_detections"] == 1
    assert report["new_by_nearest_same_class"] == {"none": 2, "0.35-0.7 m": 1, "0.7-1.5 m": 0, "over 1.5 m": 1}
    assert report["new_by_confidence"] == {"under 0.5": 2, "0.5 and over": 2}
    assert report["identities_by_sightings"] == {"1": 3, "2": 0, "3 or more": 1}
    assert report["counts"] == {"chair": 3, "cup": 1}
    assert report["counts_seen_3_or_more"] == {"chair": 1}
