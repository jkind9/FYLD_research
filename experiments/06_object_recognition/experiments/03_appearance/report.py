"""Offline evidence review with every crop, pair, unavailable result and tie."""

import json
from html import escape
from pathlib import Path


def write_report(path: Path, result: dict) -> None:
    gallery = "".join(
        f'<figure><img src="debug/{escape(row["key"])}.png" alt="masked RGB crop {escape(row["key"])}"><figcaption>{escape(row["key"])} / {escape(row["category"])} / {escape(row["partition"])} / evaluator identity {escape(row["identity"])}</figcaption></figure>'
        for row in result["observations"]
    )
    headers = "<tr><th>Pair</th><th>Independent identity</th><th>ZNCC</th><th>ORB</th><th>SIFT</th><th>YOLO pooled cosine</th></tr>"
    pairs = "".join(
        "<tr><td>"
        + escape(p["left"])
        + " / "
        + escape(p["right"])
        + "</td><td>"
        + ("same" if p["same_identity"] else "different")
        + "</td>"
        + "".join(
            f'<td><details><summary>{r["score"] if r["score"] is not None else "unavailable"}</summary><pre>{escape(json.dumps(r,indent=2))}</pre></details></td>'
            for r in p["scores"].values()
        )
        + "</tr>"
        for p in result["pairs"]
    )
    (path / "review.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Object appearance evidence</title><style>body{font:16px system-ui;background:#17212c;color:#eee;margin:24px}figure{display:inline-block;margin:10px;width:190px}img{width:128px}table{border-collapse:collapse;width:100%}td,th{padding:8px;border:1px solid #667}pre{white-space:pre-wrap}a{color:#9df}</style><h1>Object appearance across recorded views</h1><p>Every crop uses an explicitly supplied coarse provisional support. These six views were already inspected. Scores describe this recording; they are not probabilities or blind accuracy. YOLO features come from the existing detection checkpoint and are not established identity embeddings. A tie between different objects remains ambiguous. Crop aspect changes to 128 by 128; the learned predictor then letterboxes to 640.</p><a href="output/results.json">All scores, settings, costs and joins</a><h2>All observations</h2>'
        + gallery
        + "<h2>All same-class observation pairs</h2><table>"
        + headers
        + pairs
        + "</table><h2>Gallery rankings and unresolved cases</h2><pre>"
        + escape(json.dumps(result["queries"], indent=2))
        + "</pre><h2>Measured feature runtime</h2><pre>"
        + escape(json.dumps(result["feature_receipt"], indent=2))
        + "</pre></html>",
        encoding="utf-8",
    )
