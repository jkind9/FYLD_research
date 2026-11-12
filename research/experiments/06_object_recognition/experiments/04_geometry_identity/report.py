"""Write a small, self-contained review page for condition and coordinate histories."""

from __future__ import annotations

import html
import json
from pathlib import Path


def write_report(run_path: Path) -> None:
    history = json.loads(
        (run_path / "output/frame_history.json").read_text(encoding="utf-8")
    )
    summary = json.loads((run_path / "output/summary.json").read_text(encoding="utf-8"))
    payload = json.dumps(
        {"history": history, "summary": summary}, ensure_ascii=False
    ).replace("</", "<\\/")
    options = "".join(
        f'<option value="{html.escape(name)}">{html.escape(name)}</option>'
        for name in history
    )
    page = """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Task21 object identity and geometry review</title>
<style>
body{font:16px system-ui,sans-serif;margin:2rem;max-width:1100px;color:#19232d} select{font:inherit;padding:.4rem}
table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border-bottom:1px solid #ccd4da;padding:.5rem;text-align:left;vertical-align:top}
.unresolved{color:#8a4300} .matched,.new{color:#087443} code{white-space:nowrap}
</style><h1>Task21 identity and measured positions</h1>
<p>Previously inspected desk views; coordinates are measured visible surfaces. They are not object centres or calibrated errors.</p>
<label for="condition">Condition </label><select id="condition">__OPTIONS__</select>
<p id="counts"></p><div id="records"></div><h2>Object estimates after each frame</h2><div id="tracks"></div>
<h2>Measured coordinate differences across views</h2><div id="coordinates"></div>
<script id="data" type="application/json">__PAYLOAD__</script><script>
const data=JSON.parse(document.getElementById('data').textContent), select=document.getElementById('condition');
function cell(value){const td=document.createElement('td');td.textContent=value===null||value===undefined?'unavailable':typeof value==='object'?JSON.stringify(value):String(value);return td}
function table(headers,rows){const t=document.createElement('table'),head=t.createTHead().insertRow();headers.forEach(h=>{const th=document.createElement('th');th.textContent=h;head.appendChild(th)});const body=t.createTBody();rows.forEach(row=>{const tr=body.insertRow();row.forEach(v=>tr.appendChild(cell(v)))});return t}
function render(){
  const name=select.value, frames=data.history[name], root=document.getElementById('records'), tracks=document.getElementById('tracks'), coordinates=document.getElementById('coordinates');
  root.replaceChildren(); tracks.replaceChildren(); coordinates.replaceChildren();
  const decisions=[]; frames.forEach(frame=>frame.observations.forEach(row=>decisions.push([frame.frame_id,row])));
  const score=data.summary.conditions[name].score;
  document.getElementById('counts').textContent=`${decisions.length} observations; ${score.unresolved} unresolved; ${score.wrong_merge_object_ids.length} wrong-merge IDs; ${score.wrong_split_reference_ids.length} split references.`;
  root.appendChild(table(['Frame','Observation','Class','Measured scene position (m)','Decision','Object ID','Reason','Candidates','Rejected candidates','Location vote'],decisions.map(([frame,row])=>[frame,row.observation_id,row.category,row.position_world_m,row.decision,row.object_id,row.reason,row.candidates,row.rejected_candidates,row.location_vote])));
  frames.forEach(frame=>{
    const heading=document.createElement('h3'); heading.textContent=`Frame ${frame.frame_id}`; tracks.appendChild(heading);
    tracks.appendChild(table(['Object ID','Class','Position estimate (m)','Last surface (m)','View representatives'],frame.tracks.map(row=>[row.object_id,row.category,row.location.estimate_m,row.location.last_m,row.location.representative_count])));
  });
  coordinates.appendChild(table(['Reference ID (scorer only)','From to','Elapsed (s)','Surface coordinate delta (m)','Delta length (m)','Same assigned object ID'],score.coordinate_comparisons_scorer_only.map(row=>[row.reference_identity_scorer_only,`${row.from_observation} to ${row.to_observation}`,row.elapsed_s,row.world_surface_delta_m,row.world_surface_delta_norm_m,row.same_assigned_object_id])));
}
select.addEventListener('change',render); render();</script></html>"""
    page = page.replace("__OPTIONS__", options).replace("__PAYLOAD__", payload)
    (run_path / "review.html").write_text(page, encoding="utf-8", newline="\n")
