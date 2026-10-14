"""Check a Redmi check-app report and count its results.

    python experiments/01_camera_capture_delivery/host/report.py <report.json>

Every check must say PASS, FAIL or SKIPPED; FAIL and SKIPPED must give a reason, so nothing is left unknown.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

STATUSES = ("PASS", "FAIL", "SKIPPED")


def validate(report: dict) -> dict:
    if report.get("schema") != 1:
        raise ValueError("report schema must be 1")
    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("report needs a non-empty list of checks")
    for check in checks:
        name = check.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("every check needs a name")
        if check.get("status") not in STATUSES:
            raise ValueError(f"{name}: status must be one of {STATUSES}")
        if check["status"] != "PASS" and not check.get("reason"):
            raise ValueError(f"{name}: a {check['status']} check must give a reason")
        if not isinstance(check.get("detail", {}), dict):
            raise TypeError(f"{name}: detail must be an object")
    return report


def summarise(report: dict) -> dict[str, int]:
    return {status: sum(c["status"] == status for c in report["checks"]) for status in STATUSES}


def main() -> int:
    report = validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    for check in report["checks"]:
        print(f"{check['status']:8} {check['name']:24} {check.get('reason', '')}")
    print(summarise(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
