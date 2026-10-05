"""Readable Markdown tables for a stage report and a comparison."""


def _cell(value: object) -> str:
    """Markdown table cells cannot contain a raw pipe."""
    return str(value).replace("|", r"\|")


def _number(value: float | None) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, int):
        return str(value)
    return f"{value:.4g}"


def table(report: dict) -> str:
    lines = [
        f"# {report['title']}",
        "",
        "| Stage | Dataset | Reference | Input | Method | Measure | Value | Unit | Samples | Coverage | Note |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for entry in report["sections"]:
        if entry["status"] == "unavailable":
            lines.append(
                f"| {_cell(entry['stage'])} | | | | | | unavailable | | | | {_cell(entry['reason'])} |"
            )
            continue
        reference = f"{entry['reference']['id']} ({entry['reference']['kind']})"
        if not entry["measures"]:
            lines.append(
                f"| {_cell(entry['stage'])} | {_cell(entry['dataset'])} | "
                f"{_cell(reference)} | {entry['input_mode']} | | | scored, no measures | | | | |"
            )
        for item in entry["measures"]:
            lines.append(
                "| "
                + " | ".join(
                    map(
                        _cell,
                        [
                            entry["stage"],
                            entry["dataset"],
                            reference,
                            entry["input_mode"],
                            item["method"],
                            item["name"],
                            _number(item["value"]),
                            item["unit"],
                            str(item["samples"]),
                            item["coverage"],
                            item["reason"] or "",
                        ],
                    )
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def comparison_table(rows: list[dict]) -> str:
    lines = [
        "| Stage | Method | Measure | Baseline | Candidate | Change | Verdict | Not comparable because |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                map(
                    _cell,
                    [
                        row["stage"],
                        row["method"],
                        row["name"],
                        _number(row["baseline"]),
                        _number(row["candidate"]),
                        "" if row["change"] is None else _number(row["change"]),
                        row["verdict"] or "",
                        row["reason"] or "",
                    ],
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"
