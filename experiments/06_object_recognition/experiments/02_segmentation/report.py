"""Offline expandable source/mask/depth comparison; no network dependencies."""

import json
from html import escape
from pathlib import Path


def write_report(path: Path, receipt: dict) -> None:
    sections = []
    for frame in receipt["frames"]:
        key = escape(frame["frame_id"])
        prompts = []
        for prompt in frame["prompts"]:
            methods = "".join(
                f'<figure><figcaption>{escape(row["method"])}: {escape(row["status"])}</figcaption><a href="{escape(row["mask"])}"><img src="{escape(row["overlay"])}" alt="{escape(row["method"])} selected support"></a><pre>{escape(json.dumps(row, indent=2))}</pre></figure>'
                for row in prompt["methods"]
            )
            prompts.append(
                f'<details><summary>{escape(prompt["condition"])} / {escape(prompt["prompt_key"])}</summary><div class="methods">{methods}</div></details>'
            )
        sections.append(
            f'<section><h2>Frame {key}</h2><div class="source"><img src="input/rgb/{key}.png" alt="original recording RGB"><img src="debug/{key}_valid_depth.png" alt="white valid measured depth; black missing or excluded depth"></div>{"".join(prompts)}<details><summary>Evaluator-only predicted box accounting</summary><pre>{escape(json.dumps(frame["predicted_box_evaluator"], indent=2))}</pre></details></section>'
        )
    html = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Classical mask and depth support controls</title><style>body{font:16px system-ui;background:#15202b;color:#eee;margin:24px}img{max-width:100%;width:640px}section{margin-bottom:32px}details{margin:12px 0}summary{cursor:pointer}.source,.methods{display:flex;flex-wrap:wrap;gap:12px}figure{margin:0;max-width:640px}pre{white-space:pre-wrap}a{color:#9cf}</style><h1>Classical mask and measured depth support</h1><p>Six already inspected RGB-D views. Oracle boxes are explicit prompts. Coarse references cannot establish mask accuracy. Green shows selected pixels. White in depth validity means measured depth within 0â€“4 metres; it is not an object mask.</p><p>Coordinate differences compare measured camera surfaces with rectangle support. They are not location error or calibrated uncertainty. Learned masks unavailable: no acquired mask weights and no new models/downloads. No new detector inference.</p><a href="output/results.json">All results and settings</a>'
        + "".join(sections)
        + "</html>"
    )
    (path / "review.html").write_text(html, encoding="utf-8")
