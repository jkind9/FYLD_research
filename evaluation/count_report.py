"""Why a live run counted the objects it did: new identities split by distance, confidence and sightings.

    python -m src.live.count_report <live run folder>/updates.jsonl

A new identity just past the matching distance (0.35 m) from an object of the same class suggests the same
object placed in a different spot; one far from any suggests a separate object or a false detection. An identity
seen once is weaker evidence than one seen in 3 or more updates. None of this is checked against a real inventory.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

DISTANCE_BINS = ((0.7, "0.35-0.7 m"), (1.5, "0.7-1.5 m"), (float("inf"), "over 1.5 m"))
CONFIDENCE_SPLIT = 0.5


def _distance_bin(nearest: float | None) -> str:
    if nearest is None:
        return "none"
    return next(name for limit, name in DISTANCE_BINS if nearest < limit)


def report(updates: Path) -> dict:
    rows = [d for line in Path(updates).read_text(encoding="utf-8").splitlines() if line.strip()
            for d in json.loads(line).get("detections", [])]
    new = [d for d in rows if d["outcome"] == "new"]
    sightings = Counter(d["object_id"] for d in rows if d["object_id"] is not None)
    label = {d["object_id"]: d["label"] for d in new}
    by_sightings = Counter("3 or more" if n >= 3 else str(n) for n in sightings.values())
    return {
        "detections": len(rows),
        "identities": len(new),
        "unresolved_detections": sum(d["outcome"].startswith("unresolved") for d in rows),
        "new_by_nearest_same_class": {name: sum(_distance_bin(d["nearest_same_class_m"]) == name for d in new)
                                      for name in ["none", *(n for _, n in DISTANCE_BINS)]},
        "new_by_confidence": {"under 0.5": sum(d["confidence"] < CONFIDENCE_SPLIT for d in new),
                              "0.5 and over": sum(d["confidence"] >= CONFIDENCE_SPLIT for d in new)},
        "identities_by_sightings": {k: by_sightings.get(k, 0) for k in ("1", "2", "3 or more")},
        "counts": dict(Counter(label.values())),
        "counts_seen_3_or_more": dict(Counter(label[o] for o, n in sightings.items() if n >= 3)),
    }


def main(argv: list[str] | None = None) -> int:
    path = Path((argv or sys.argv[1:])[0])
    result = report(path)
    (path.parent / "count_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
