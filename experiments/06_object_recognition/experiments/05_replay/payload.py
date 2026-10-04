"""Build the self-contained synchronized RGB, camera, cloud and object viewer."""

from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image


def _image(path: Path) -> str:
    with Image.open(path) as source:
        stream = BytesIO()
        source.convert("RGB").save(stream, format="JPEG", quality=90, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(stream.getvalue()).decode(
        "ascii"
    )


def _frustum(pose: dict | None) -> list[list[float]]:
    if not pose:
        return []
    matrix = np.asarray(pose["T_world_camera"], dtype=float)
    camera = np.asarray(
        [
            [0, 0, 0],
            [-0.0914, -0.0686, 0.15],
            [0.0914, -0.0686, 0.15],
            [0.0914, 0.0686, 0.15],
            [-0.0914, 0.0686, 0.15],
            [-0.0914, -0.0686, 0.15],
        ],
        dtype=float,
    )
    world = camera @ matrix[:3, :3].T + matrix[:3, 3]
    return [[float(x) for x in point] for point in world]


def write(
    output: Path,
    run_path: Path,
    frames: list[dict],
    observations: dict,
    points: np.ndarray,
    colours: np.ndarray,
    automatic: dict,
    proposal_frames: list[dict],
) -> int:
    if len(frames) != 60 or points.shape != (20000, 3) or colours.shape != points.shape:
        raise ValueError("Task22 requires the exact frozen 60-frame/20k-point baseline")
    detection_data = json.loads(
        (run_path / "input/baseline_detections.json").read_text(encoding="utf-8")
    )
    proposals = []
    for frame in detection_data["frames"]:
        matching = {
            row["detection_index"]: row
            for row in observations["frames"][frame["frame_index"]]["detections"]
        }
        for index, row in enumerate(frame["proposals"]):
            located = matching.get(index, {})
            proposals.append(
                {
                    "frame_index": frame["frame_index"],
                    "proposal_index": index,
                    "object_id": located.get("object_id"),
                    "association": located.get("association", "unavailable"),
                    "position_world_m": located.get("world_position_m"),
                    **row,
                }
            )
    if len(proposals) != 457:
        raise ValueError("Baseline proposal accounting must equal 457")
    payload_frames = []
    for index, frame in enumerate(frames):
        source = observations["frames"][index]
        payload_frames.append(
            {
                "index": index,
                "frame_id": frame["frame_id"],
                "timestamp": frame["timestamp_s"],
                "image": _image(run_path / "input" / source["rgb"]),
                "camera": source["camera_origin_world_m"],
                "pose": _frustum(source["pose"]),
                "cloud_start": source["cloud_start"],
                "cloud_stop": source["cloud_stop"],
                "point_count": source["point_count"],
                "detections": source["detections"],
                "tracks": source["tracks"],
                "failures": source["failures"],
            }
        )
    scene = {
        "points": np.asarray(points, dtype=float).tolist(),
        "colours": np.asarray(colours, dtype=np.uint8).tolist(),
        "frames": payload_frames,
        "automatic": automatic["conditions"],
        "proposals": proposals,
        "proposal_frame_indexes": [
            row["source_selection_index"] for row in proposal_frames
        ],
        "auto_observations": automatic["frames"],
    }
    data = json.dumps(scene, separators=(",", ":"), allow_nan=False).replace(
        "<", "\\u003c"
    )
    from plotly.offline import get_plotlyjs

    page = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task22 recorded object replay</title><style>
body{font:15px system-ui,sans-serif;margin:16px;color:#192832;background:#f2f5f6}h1{margin:0}.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0}.bar button,.bar select{font:inherit;padding:6px}#seek{flex:1;min-width:220px}.grid{display:grid;grid-template-columns:minmax(320px,1fr) minmax(420px,1.2fr);gap:12px}.panel{background:#fff;border:1px solid #cfd8dc;border-radius:8px;padding:12px;min-width:0}.image{position:relative}.image img{width:100%;display:block}.image svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}#plot{height:620px}.small{color:#51636c;font-size:13px}.data{white-space:pre-wrap;max-height:220px;overflow:auto}.wide{margin-top:12px;max-height:340px;overflow:auto}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border-bottom:1px solid #dae1e4;padding:4px;text-align:left} @media(max-width:900px){.grid{grid-template-columns:1fr}#plot{height:480px}}</style></head><body>
<h1>Recorded RGB-D object replay</h1><p class="small">YOLO26x boxes are projected through measured depth and supplied camera poses. Markers show visible surface samples, not physical object centres. Task16's broader protocol remains pending review.</p>
<div class="bar"><label>Condition <select id="condition"><option value="baseline">Task28 baseline · 60 frames</option><option value="combined-last">Automatic boxes · combined, last position</option><option value="combined-viewmedian">Automatic boxes · combined, independent-view median</option></select></label><button id="play">Play</button><button id="prev">Previous</button><button id="next">Next</button><input id="seek" type="range" min="0" max="59" value="0"><span id="count"></span><label>Speed <select id="speed"><option>0.5</option><option selected>1</option><option>2</option></select>x</label></div>
<div class="grid"><section class="panel"><h2>Recording</h2><div class="image"><img id="rgb" alt="Selected RGB frame"><svg id="boxes" viewBox="0 0 640 480"></svg></div><div id="frame" class="data"></div></section><section class="panel"><h2>Camera, growing colour cloud and object positions</h2><div id="plot"></div><div id="objects" class="data"></div></section></div>
<section class="panel wide"><h2>All detector proposals</h2><label>Filter by class <select id="class"><option value="all">All classes</option></select></label><div id="proposalcount"></div><table><thead><tr><th>Frame</th><th>Class</th><th>Score</th><th>Object ID</th><th>Scene position (m)</th></tr></thead><tbody id="proposals"></tbody></table></section>
<section class="panel wide"><h2>Observation history by object</h2><label>Object ID <select id="object"><option value="">Choose an ID seen so far</option></select></label><pre id="history" class="data">Choose an object to inspect its observations through the selected frame.</pre></section>
<section class="panel wide"><h2>Automatic observations and failed associations</h2><div id="details" class="data"></div></section><script>__PLOTLY__</script><script>const D=__DATA__;let i=0,timer=null;const colors=['#df3e36','#326da8','#e58a24','#218c75','#9064a6','#be4e7b','#6a994e'];const color=id=>{let h=0;for(const c of String(id||'?'))h=(h*31+c.charCodeAt(0))>>>0;return colors[h%colors.length]};const plot=document.getElementById('plot');
const traces=[{type:'scatter3d',mode:'markers',name:'Accumulated RGB-D points',x:[],y:[],z:[],marker:{size:2,color:[],opacity:.68},hoverinfo:'skip'},{type:'scatter3d',mode:'lines+markers',name:'Camera path',x:[],y:[],z:[],line:{color:'#253746',width:4},marker:{size:3,color:'#253746'}},{type:'scatter3d',mode:'lines',name:'Current camera frustum',x:[],y:[],z:[],line:{color:'#ed7d31',width:5},hoverinfo:'skip'},{type:'scatter3d',mode:'markers+text',name:'Persistent object markers',x:[],y:[],z:[],text:[],textposition:'top center',marker:{size:8,color:[]},hovertemplate:'%{text}<br>%{x:.3f}, %{y:.3f}, %{z:.3f} m<extra></extra>'}];
const layout={margin:{l:0,r:0,b:0,t:0},legend:{orientation:'h'},scene:{aspectmode:'data',xaxis_title:'Scene X (m)',yaxis_title:'Scene Y (m)',zaxis_title:'Scene Z (m)'}};
function autoAt(frameIndex,cond){let chosen=null;for(const f of D.automatic[cond])if(f.frame_index<=frameIndex)chosen=f;return chosen}
function update(n){i=Math.max(0,Math.min(59,n));const f=D.frames[i],cond=document.getElementById('condition').value;document.getElementById('rgb').src=f.image;let cloud=D.points.slice(0,f.cloud_stop),rgb=D.colours.slice(0,f.cloud_stop);Plotly.restyle(plot,{x:[cloud.map(p=>p[0])],y:[cloud.map(p=>p[1])],z:[cloud.map(p=>p[2])],'marker.color':[rgb.map(c=>`rgb(${c[0]},${c[1]},${c[2]})`)]},[0]);const path=D.frames.slice(0,i+1).map(x=>x.camera).filter(Boolean);Plotly.restyle(plot,{x:[path.map(p=>p[0])],y:[path.map(p=>p[1])],z:[path.map(p=>p[2])]},[1]);let rays=f.pose;Plotly.restyle(plot,{x:[rays.map(p=>p[0])],y:[rays.map(p=>p[1])],z:[rays.map(p=>p[2])]},[2]);let markers=[],boxes=[];if(cond==='baseline'){for(const [id,t] of Object.entries(f.tracks)){if(t.last_position_m)markers.push({id,label:t.label,pos:t.last_position_m,visible:f.detections.some(d=>d.object_id===id),last:t.last_frame_index+1});}boxes=f.detections;}else{const state=autoAt(i,cond);if(state){for(const t of state.tracks){if(t.position_m)markers.push({id:t.object_id,label:t.category,pos:t.position_m,visible:t.last_frame_id===String(f.frame_id),last:t.last_frame_id});}if(state.frame_index===i)boxes=state.observations;}}
const svg=document.getElementById('boxes');svg.replaceChildren();for(const b of boxes){const xy=b.xyxy||b.bbox_xyxy;if(!xy)continue;let rect=document.createElementNS('http://www.w3.org/2000/svg','rect');rect.setAttribute('x',xy[0]);rect.setAttribute('y',xy[1]);rect.setAttribute('width',xy[2]-xy[0]);rect.setAttribute('height',xy[3]-xy[1]);rect.setAttribute('fill','none');rect.setAttribute('stroke',color(b.object_id));rect.setAttribute('stroke-width','2');svg.append(rect);let label=document.createElementNS('http://www.w3.org/2000/svg','text');label.setAttribute('x',xy[0]);label.setAttribute('y',Math.max(14,xy[1]-3));label.setAttribute('fill',color(b.object_id));label.setAttribute('stroke','white');label.setAttribute('stroke-width','.5');label.textContent=`${b.label||b.category} ${b.object_id||b.decision||'unresolved'}`;svg.append(label);}
Plotly.restyle(plot,{x:[markers.map(t=>t.pos[0])],y:[markers.map(t=>t.pos[1])],z:[markers.map(t=>t.pos[2])],text:[markers.map(t=>`${t.id} · ${t.label}${t.visible?'':' (last seen)'}`)],'marker.color':[markers.map(t=>color(t.id))]},[3]);document.getElementById('frame').textContent=`Frame ${i+1}/60 · source ${f.frame_id} · ${f.timestamp.toFixed(6)} s\nCamera position (scene metres): ${f.camera?f.camera.map(x=>x.toFixed(3)).join(', '):'unavailable'}\nNew RGB-D points: ${f.point_count} · accumulated display points: ${f.cloud_stop}\n${cond==='baseline'?'Cached Task28 detector replay.':'Automatic condition sampled at indexes 0, 9, 27, 37, 42, 59; unsampled frames retain the last marker.'}`;document.getElementById('objects').textContent=markers.length?markers.map(t=>`${t.id} · ${t.label} · ${t.visible?'visible':'out of view; last position retained'} · ${t.pos.map(x=>x.toFixed(3)).join(', ')} m`).join('\n'):'No object position has been accepted yet.';document.getElementById('count').textContent=`${i+1} / 60`;document.getElementById('seek').value=i;
const state=cond==='baseline'?null:autoAt(i,cond);document.getElementById('details').textContent=state?JSON.stringify(state.observations.map(o=>({id:o.observation_id,category:o.category,decision:o.decision,object_id:o.object_id,position_camera_m:o.position_camera_m,position_world_m:o.position_world_m,reason:o.reason,candidates:o.candidates})),null,2):'Select an automatic condition at one of its six sampled source frames to inspect every decision.';syncHistory(cond,i);}
function syncHistory(cond,limit){const select=document.getElementById('object'),previous=select.value,ids=new Set();if(cond==='baseline'){for(const frame of D.frames.slice(0,limit+1))for(const id of Object.keys(frame.tracks))ids.add(id)}else for(const frame of D.automatic[cond])if(frame.frame_index<=limit)for(const track of frame.tracks)ids.add(track.object_id);select.replaceChildren();const empty=document.createElement('option');empty.value='';empty.textContent='Choose an ID seen so far';select.append(empty);for(const id of [...ids].sort()){const option=document.createElement('option');option.value=id;option.textContent=id;select.append(option)}select.value=ids.has(previous)?previous:'';showHistory(cond,limit)}
function showHistory(cond,limit){const id=document.getElementById('object').value;if(!id){document.getElementById('history').textContent='Choose an object ID. The list only includes IDs observed by the current frame.';return}const rows=[];if(cond==='baseline'){for(const frame of D.frames.slice(0,limit+1)){for(const observation of frame.detections)if(observation.object_id===id)rows.push({frame:frame.frame_id,observation_id:observation.detection_index,category:observation.label,decision:observation.association,position_camera_m:observation.camera_position_m,position_world_m:observation.world_position_m});for(const failure of frame.failures||[])if((failure.candidates||[]).some(candidate=>candidate.object_id===id))rows.push({frame:frame.frame_id,category:failure.label,decision:'unresolved candidate',reason:failure.reason,candidates:failure.candidates})}}else for(const frame of D.automatic[cond])if(frame.frame_index<=limit)for(const observation of frame.observations)if(observation.object_id===id||(observation.candidates||[]).some(candidate=>candidate.object_id===id)||(observation.rejected_candidates||[]).some(candidate=>candidate.object_id===id))rows.push({frame:observation.frame_id,observation_id:observation.observation_id,category:observation.category,decision:observation.object_id===id?observation.decision:'candidate only',reason:observation.reason,position_camera_m:observation.position_camera_m,position_world_m:observation.position_world_m,candidates:observation.candidates,rejected_candidates:observation.rejected_candidates,location:observation.location});document.getElementById('history').textContent=JSON.stringify({object_id:id,observations_through_current_frame:rows},null,2)}
function stop(){if(timer)clearTimeout(timer);timer=null;document.getElementById('play').textContent='Play'}function step(){if(i>=59){stop();return}timer=setTimeout(()=>{update(i+1);step()},300/Number(document.getElementById('speed').value))}document.getElementById('play').onclick=()=>{if(timer)stop();else{document.getElementById('play').textContent='Pause';step()}};document.getElementById('prev').onclick=()=>{stop();update(i-1)};document.getElementById('next').onclick=()=>{stop();update(i+1)};document.getElementById('seek').oninput=e=>{stop();update(Number(e.target.value))};document.getElementById('condition').onchange=()=>update(i);
const classes=[...new Set(D.proposals.map(p=>p.label))].sort();for(const c of classes){let o=document.createElement('option');o.value=c;o.textContent=c;document.getElementById('class').append(o)}function fillProposals(){let c=document.getElementById('class').value;let rows=D.proposals.filter(p=>c==='all'||p.label===c);document.getElementById('proposalcount').textContent=`${rows.length} / 457 proposals`;const body=document.getElementById('proposals');body.replaceChildren();for(const p of rows){let tr=document.createElement('tr');for(const value of [p.frame_index+1,p.label,p.confidence.toFixed(3),p.object_id||p.association,p.position_world_m?p.position_world_m.map(x=>x.toFixed(3)).join(', '):'unavailable']){let td=document.createElement('td');td.textContent=value;tr.append(td)}body.append(tr)}}document.getElementById('class').onchange=fillProposals;document.getElementById('object').onchange=()=>showHistory(document.getElementById('condition').value,i);
Plotly.newPlot(plot,traces,layout,{responsive:true,displaylogo:false}).then(()=>{fillProposals();update(0)});
</script></body></html>"""
    page = page.replace("__PLOTLY__", get_plotlyjs()).replace("__DATA__", data)
    output.write_text(page, encoding="utf-8")
    return len(proposals)
