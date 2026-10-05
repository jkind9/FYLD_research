"""Stage-by-stage comparison of two reports, and own-versus-inherited error.

A measure is only compared when both reports scored it against the same
reference, dataset, input mode and coverage. Otherwise the row says why not.
No pass/fail limits are applied; the verdict only states direction.
"""

from typing import Any

from experiments.evaluation.schema import SCHEMA_VERSION

SECTION_KEYS = (
    ("dataset", "dataset"),
    ("input_mode", "input mode"),
    ("scope", "scored items"),
)
MEASURE_KEYS = ("coverage", "unit", "better")


def _measures(report: dict) -> dict[tuple[str, str, str], tuple[dict, dict]]:
    found = {}
    for entry in report["sections"]:
        for item in entry["measures"]:
            found[(entry["stage"], item["method"], item["name"])] = (entry, item)
    return found


def _mismatch(first: tuple[dict, dict], second: tuple[dict, dict]) -> list[str]:
    (left_section, left), (right_section, right) = first, second
    reasons = [
        label for key, label in SECTION_KEYS if left_section[key] != right_section[key]
    ]
    if left_section["reference"] != right_section["reference"]:
        reasons.append("reference")
    for key in MEASURE_KEYS:
        if left[key] != right[key]:
            reasons.append(key)
    if left["value"] is None or right["value"] is None:
        reasons.append("value unavailable")
    return reasons


def _verdict(change: float, better: str) -> str:
    if change == 0:
        return "same"
    if better == "neither":
        return "changed"
    improved = change < 0 if better == "lower" else change > 0
    return "better" if improved else "worse"


def compare(baseline: dict, candidate: dict) -> list[dict]:
    """One row per (stage, method, measure) seen in either report."""
    for label, report in (("baseline", baseline), ("candidate", candidate)):
        if report.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"{label} report has format version {report.get('schema_version')}; "
                f"compare needs format version {SCHEMA_VERSION}. Rebuild it."
            )
    before, after = _measures(baseline), _measures(candidate)
    rows = []
    for key in sorted(set(before) | set(after)):
        stage, method, name = key
        row: dict[str, Any] = {
            "stage": stage,
            "method": method,
            "name": name,
            "baseline": before[key][1]["value"] if key in before else None,
            "candidate": after[key][1]["value"] if key in after else None,
            "change": None,
            "verdict": None,
        }
        if key not in before or key not in after:
            side = "baseline" if key not in before else "candidate"
            row.update(comparable=False, reason=f"method/measure missing from {side}")
        elif reasons := _mismatch(before[key], after[key]):
            row.update(comparable=False, reason="differs in " + ", ".join(reasons))
        else:
            change = row["candidate"] - row["baseline"]
            better = after[key][1]["better"]
            row.update(
                comparable=True,
                reason=None,
                change=change,
                verdict=_verdict(change, better),
                better=better,
            )
        rows.append(row)
    return rows


def _loss(own: float, total: float, better: str) -> float:
    """Positive when the chained result is worse than the isolated one."""
    return total - own if better == "lower" else own - total


def inherited(isolated: dict, chained: dict) -> list[dict]:
    """Split a stage's chained result into its own part and the loss passed down.

    Both sections must score the same stage, dataset, reference and items; only
    the input mode differs. `inherited_loss` is positive when feeding the stage
    earlier predictions made it worse, whichever direction is better. Measures
    with no better direction are left out.
    """
    if (isolated["input_mode"], chained["input_mode"]) != ("isolated", "chained"):
        raise ValueError("input mode must be isolated then chained")
    for key in ("stage", "dataset", "reference", "scope"):
        if isolated[key] != chained[key]:
            raise ValueError(f"isolated and chained sections differ in {key}")
    own = {(m["method"], m["name"]): m for m in isolated["measures"]}
    rows = []
    for item in chained["measures"]:
        base = own.get((item["method"], item["name"]))
        if base is None or base["value"] is None or item["value"] is None:
            continue
        for key in MEASURE_KEYS:
            if base[key] != item[key]:
                raise ValueError(f"{item['name']} differs in {key}")
        if item["better"] == "neither":
            continue
        rows.append(
            {
                "method": item["method"],
                "name": item["name"],
                "unit": item["unit"],
                "better": item["better"],
                "own": base["value"],
                "total": item["value"],
                "inherited_loss": _loss(base["value"], item["value"], item["better"]),
            }
        )
    return rows
