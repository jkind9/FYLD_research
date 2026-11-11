"""Stage report format v1: one section per pipeline stage, every measure traceable.

A measure is either a finite number or `None` with a stated reason. Missing stages
are reported as unavailable instead of being left out, so a reader can see what
was not measured as clearly as what was.
"""

import math
from typing import Any

SCHEMA_VERSION = 2  # 2 added the per-section scored-items `scope` fingerprint
STAGES = (
    "camera_path",
    "detection",
    "segmentation",
    "depth_support",
    "object_position",
    "surface",
    "identity",
    "count",
)
REFERENCE_KINDS = frozenset({"independent", "provisional", "analytic", "none"})
INPUT_MODES = frozenset({"isolated", "chained"})
COVERAGES = frozenset({"complete", "subset"})
BETTER = frozenset({"lower", "higher", "neither"})
NOT_YET = "no reference or scorer yet"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a nonempty string")
    return value


def measure(
    method: str,
    name: str,
    value: float | None,
    unit: str,
    *,
    samples: int,
    coverage: str,
    better: str,
    reason: str | None = None,
) -> dict:
    """One scored number, or None with the reason it cannot be scored."""
    if coverage not in COVERAGES:
        raise ValueError(f"coverage must be one of {sorted(COVERAGES)}")
    if better not in BETTER:
        raise ValueError(f"better must be one of {sorted(BETTER)}")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 0:
        raise ValueError("samples must be a nonnegative integer")
    if value is None:
        _text(reason, "reason for an unavailable value")
    elif isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("value must be a number or None")
    elif not math.isfinite(value):
        raise ValueError("value must be finite")
    return {
        "method": _text(method, "method"),
        "name": _text(name, "name"),
        "value": value,
        "unit": _text(unit, "unit"),
        "samples": samples,
        "coverage": coverage,
        "better": better,
        "reason": reason,
    }


def _reference(reference: dict) -> dict:
    keys = ("id", "version", "sha256", "kind")
    if not isinstance(reference, dict) or set(reference) != set(keys):
        raise ValueError(f"reference needs exactly {keys}")
    for key in keys[:3]:
        _text(reference[key], f"reference {key}")
    if reference["kind"] not in REFERENCE_KINDS:
        raise ValueError(f"reference kind must be one of {sorted(REFERENCE_KINDS)}")
    return dict(reference)


def _stage(stage: str) -> str:
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; expected one of {STAGES}")
    return stage


def section(
    stage: str,
    *,
    run: dict,
    dataset: str,
    reference: dict,
    input_mode: str,
    scope: dict,
    measures: list[dict],
    rows: list[dict] | None = None,
) -> dict:
    """A scored stage. `rows` holds per-item evidence behind the summary numbers.

    `scope` fingerprints exactly which items (frames, observations) were scored,
    so two runs over different parts of one sequence are never compared.
    """
    if input_mode not in INPUT_MODES:
        raise ValueError(f"input mode must be one of {sorted(INPUT_MODES)}")
    if not isinstance(run, dict) or set(run) != {"id", "manifest_sha256"}:
        raise ValueError("run needs exactly id and manifest_sha256")
    if (
        not isinstance(scope, dict)
        or set(scope) != {"items", "sha256"}
        or isinstance(scope["items"], bool)
        or not isinstance(scope["items"], int)
        or scope["items"] < 0
    ):
        raise ValueError("scope needs a nonnegative item count and sha256")
    _text(scope["sha256"], "scope sha256")
    keys = [(m["method"], m["name"]) for m in measures]
    if len(keys) != len(set(keys)):
        raise ValueError("measure (method, name) pairs must be unique in a section")
    return {
        "stage": _stage(stage),
        "status": "scored",
        "reason": None,
        "run": {k: _text(v, f"run {k}") for k, v in run.items()},
        "dataset": _text(dataset, "dataset"),
        "reference": _reference(reference),
        "input_mode": input_mode,
        "scope": dict(scope),
        "measures": [dict(m) for m in measures],
        "rows": [dict(r) for r in rows or []],
    }


def unavailable(stage: str, reason: str = NOT_YET) -> dict:
    return {
        "stage": _stage(stage),
        "status": "unavailable",
        "reason": _text(reason, "reason"),
        "measures": [],
        "rows": [],
    }


def build_report(sections: list[dict], *, title: str = "stage report") -> dict:
    """Order sections by pipeline stage and fill every missing stage as unavailable."""
    by_stage: dict[str, dict] = {}
    for entry in sections:
        stage = _stage(entry["stage"])
        if stage in by_stage:
            raise ValueError(f"duplicate section for stage {stage}")
        by_stage[stage] = entry
    return {
        "schema_version": SCHEMA_VERSION,
        "title": _text(title, "title"),
        "sections": [by_stage.get(stage) or unavailable(stage) for stage in STAGES],
    }
