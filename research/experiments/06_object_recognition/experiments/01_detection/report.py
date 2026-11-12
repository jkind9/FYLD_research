"""Offline RGB overlays retain every proposal and separately drawn references."""

import base64
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw


def write_report(
    destination: Path, frames: list[dict], proposals: list[dict], results: dict
) -> None:
    """Publish static overlays plus an offline inspectable HTML comparison."""
    cards = []
    for frame, predictions in zip(frames, proposals, strict=True):
        frame_id = frame["frame_id"]
        with Image.open(destination / "input/rgb" / f"{frame_id}.png") as source:
            image = source.copy()
        draw = ImageDraw.Draw(image)
        for label in frame["labels"]:
            draw.rectangle(label["bbox_xyxy"], outline="#00ff70", width=3)
            draw.text(
                tuple(label["bbox_xyxy"][:2]),
                "reference " + label["instance_id"],
                fill="#00ff70",
            )
        for index, proposal in enumerate(predictions["proposals"]):
            draw.rectangle(proposal["xyxy"], outline="#ffad40", width=2)
            text = f'{index}: {proposal["label"]} {proposal["confidence"]:.3f}'
            draw.text(tuple(proposal["xyxy"][:2]), text, fill="#ffad40")
        overlay = destination / "debug" / f"{frame_id}.png"
        image.save(overlay)
        uri = "data:image/png;base64," + base64.b64encode(overlay.read_bytes()).decode(
            "ascii"
        )
        diagnostics = {
            name: next(row for row in value["thresholds"] if row["threshold"] == 0.5)[
                "frames"
            ][frames.index(frame)]
            for name, value in results.items()
        }
        cards.append(
            f'<section><h2>Source frame {html.escape(frame_id)}</h2><img alt="Reference and prediction boxes for frame {html.escape(frame_id)}" src="{uri}"><details><summary>All proposals and primary diagnostics</summary><pre>{html.escape(json.dumps({"proposals": predictions["proposals"], "diagnostics": diagnostics}, indent=2))}</pre></details></section>'
        )
    summary = {
        method: [
            {"threshold": row["threshold"], "summary": row["summary"]}
            for row in value["thresholds"]
        ]
        for method, value in results.items()
    }
    payload = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Six-frame detection diagnostics</title>
<style>body{{background:#14202b;color:#eef5fa;font:16px system-ui;max-width:1100px;margin:auto;padding:24px}}img{{max-width:100%;height:auto}}section{{border-top:1px solid #667;padding:20px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}summary{{cursor:pointer}}</style>
<h1>Six-frame detection diagnostics</h1><p>Orange: cached YOLO26x proposals. Green: independent coarse RGB references. All proposals are shown.</p>
<p>Already inspected within-session smoke check. Cup labels are complete. Monitor labels cover a positive subset: unmatched monitor proposals are unscored; no monitor precision, recall or false-positive claim. Empty predictions are a software accounting control.</p>
<details open><summary>Every overlap threshold: 0.3, 0.5 and 0.7</summary><pre>{html.escape(json.dumps(summary, indent=2))}</pre></details>{''.join(cards)}</html>"""
    (destination / "review.html").write_text(payload, encoding="utf-8")
