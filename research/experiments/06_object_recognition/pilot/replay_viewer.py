"""Self-contained synchronized viewer for a bounded RGB-D identity replay."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import numpy as np
from PIL import Image


def _data_uri(path: Path) -> str:
    with Image.open(path) as source:
        image = source.convert("RGB")
        from io import BytesIO

        encoded = BytesIO()
        image.save(encoded, format="JPEG", quality=90, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(encoded.getvalue()).decode(
        "ascii"
    )


def _initial_tracks(frame: dict, frame_index: int) -> list[dict]:
    records = []
    visible = {
        item["object_id"]
        for item in frame["detections"]
        if item.get("object_id") is not None
    }
    for object_id, track in sorted(frame["tracks"].items()):
        records.append(
            {
                "object_id": object_id,
                "label": track["label"],
                "class_id": track["class_id"],
                "position_m": track["last_position_m"],
                "last_frame_index": track["last_frame_index"],
                "visible_now": object_id in visible,
            }
        )
    return records


def _frame_payload(input_root: Path, observations: list[dict]) -> list[dict]:
    result = []
    for frame_index, frame in enumerate(observations):
        rgb_path = input_root / frame["rgb"]
        result.append(
            {
                "frame_index": frame_index,
                "frame_id": frame["frame_id"],
                "timestamp_s": frame["timestamp_s"],
                "image": _data_uri(rgb_path),
                "boxes": [
                    {
                        "xyxy": item["xyxy"],
                        "label": item["label"],
                        "class_id": item["class_id"],
                        "confidence": item["confidence"],
                        "object_id": item["object_id"],
                        "association": item["association"],
                    }
                    for item in frame["detections"]
                ],
                "camera_position_m": frame["camera_origin_world_m"],
                "camera_path_m": [
                    prior["camera_origin_world_m"]
                    for prior in observations[: frame_index + 1]
                    if prior["camera_origin_world_m"] is not None
                ],
                "cloud_stop": frame["cloud_stop"],
                "point_count": frame["point_count"],
                "tracks": _initial_tracks(frame, frame_index),
                "failures": frame["failures"],
                "detections": frame["detections"],
            }
        )
    return result


def _payload_script(frames: list[dict], points: np.ndarray, colours: np.ndarray) -> str:
    scene = {
        "points": np.asarray(points, dtype=float).reshape(-1, 3).tolist(),
        "colours": np.asarray(colours, dtype=np.uint8).reshape(-1, 3).tolist(),
        "frames": frames,
    }
    return json.dumps(scene, separators=(",", ":"), allow_nan=False).replace(
        "<", "\\u003c"
    )


def write_replay_review(
    output: Path,
    input_root: Path,
    observations: list[dict],
    points: np.ndarray,
    colours: np.ndarray,
    display_cap: int,
) -> None:
    if not observations:
        raise ValueError("Replay viewer requires at least one selected frame")
    if points.ndim != 2 or points.shape[1:] != (3,) or colours.shape != points.shape:
        raise ValueError("Replay viewer needs paired XYZ and RGB points")
    if len(points) > display_cap:
        raise ValueError("Replay cloud exceeds its declared display cap")

    try:
        from plotly.offline import get_plotlyjs  # type: ignore[import-untyped]
    except ImportError as error:
        raise RuntimeError(
            "Plotly is required to write the offline replay viewer"
        ) from error

    payload = _payload_script(_frame_payload(input_root, observations), points, colours)
    plotly_js = get_plotlyjs()
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recorded cup return replay</title>
<style>
body{font:15px system-ui,sans-serif;color:#17232e;margin:18px;background:#f5f7f8}h1{font-size:24px;margin:0 0 8px}
.controls{display:flex;align-items:center;gap:9px;margin:12px 0;flex-wrap:wrap}.controls button,.controls select{font:inherit;padding:6px 10px}
#seek{flex:1;min-width:220px}.layout{display:grid;grid-template-columns:minmax(320px,1fr) minmax(420px,1.25fr);gap:14px}
.panel{background:white;border:1px solid #d8dfe3;border-radius:8px;padding:12px;min-width:0}.image-wrap{position:relative;width:100%;line-height:0}
#rgb{display:block;width:100%;height:auto}.overlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
#scene{width:100%;height:630px}.meta{white-space:pre-wrap;line-height:1.45}.small{color:#50616d;font-size:13px}
@media(max-width:900px){.layout{grid-template-columns:1fr}#scene{height:520px}}
</style></head><body>
<h1>Recorded cup return</h1>
<p class="small">The detector sees RGB only. Supplied TUM poses place measured depth samples in one scene frame. Markers show observed box-depth positions, not physical object centres. Clip-local labels use same-class position matching; unresolved matches stay unresolved.</p>
<div class="controls"><button id="play">Play</button><button id="prev">Previous</button><button id="next">Next</button>
<input id="seek" type="range" min="0" value="0"><span id="counter"></span><label>Speed <select id="speed"><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="2">2x</option></select></label></div>
<div class="layout"><section class="panel"><h2>RGB recording</h2><div class="image-wrap"><img id="rgb" alt="Selected original RGB frame"><svg id="boxes" class="overlay" viewBox="0 0 640 480" preserveAspectRatio="none"></svg></div><div id="frame-info" class="meta"></div></section>
<section class="panel"><h2>Growing coloured point cloud and camera path</h2><div id="scene"></div><div id="object-info" class="meta"></div></section></div>
<script>__PLOTLY__</script><script>const REPLAY=__DATA__;
const palette=['#e63946','#386cb0','#f28e2b','#2a9d8f','#8e5ea2','#d45087','#6a994e','#bc6c25','#577590','#b56576'];
const colourFor=id=>{let n=0;for(const c of id)n=(n*31+c.charCodeAt(0))>>>0;return palette[n%palette.length]};
const trace={type:'scatter3d',mode:'markers',name:'Accumulated RGB-D points',x:[],y:[],z:[],marker:{size:2,color:[],opacity:.72},hoverinfo:'skip'};
const cameraTrace={type:'scatter3d',mode:'lines+markers',name:'Camera path',x:[],y:[],z:[],line:{color:'#263238',width:4},marker:{size:4,color:'#263238'}};
const objectTrace={type:'scatter3d',mode:'markers+text',name:'Object IDs (last observed position)',x:[],y:[],z:[],text:[],textposition:'top center',marker:{size:8,color:[]},hovertemplate:'%{text}<br>X %{x:.3f} m<br>Y %{y:.3f} m<br>Z %{z:.3f} m<extra></extra>'};
const layout={margin:{l:0,r:0,b:0,t:8},showlegend:true,legend:{orientation:'h'},scene:{aspectmode:'data',xaxis_title:'Scene X (m)',yaxis_title:'Scene Y (m)',zaxis_title:'Scene Z (m)'}};
const graph=document.getElementById('scene');let current=0,timer=null;
function update(index){current=Math.max(0,Math.min(REPLAY.frames.length-1,index));const f=REPLAY.frames[current];
 const cloud=REPLAY.points.slice(0,f.cloud_stop),rgb=REPLAY.colours.slice(0,f.cloud_stop);
 Plotly.restyle(graph,{x:[cloud.map(p=>p[0])],y:[cloud.map(p=>p[1])],z:[cloud.map(p=>p[2])],'marker.color':[rgb.map(c=>`rgb(${c[0]},${c[1]},${c[2]})`)]},[0]);
 const path=f.camera_path_m;Plotly.restyle(graph,{x:[path.map(p=>p[0])],y:[path.map(p=>p[1])],z:[path.map(p=>p[2])]},[1]);
 const tracks=f.tracks;Plotly.restyle(graph,{x:[tracks.map(o=>o.position_m[0])],y:[tracks.map(o=>o.position_m[1])],z:[tracks.map(o=>o.position_m[2])],text:[tracks.map(o=>`${o.object_id} · ${o.label}${o.visible_now?'':' (last seen)'}`)],'marker.color':[tracks.map(o=>colourFor(o.object_id))]},[2]);
 Plotly.relayout(graph,{'scene.xaxis.autorange':true,'scene.yaxis.autorange':true,'scene.zaxis.autorange':true});
 document.getElementById('rgb').src=f.image;
 const overlay=document.getElementById('boxes');overlay.replaceChildren();
 for(const b of f.boxes){const [x1,y1,x2,y2]=b.xyxy;const color=b.object_id?colourFor(b.object_id):'#606c76';const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');
  rect.setAttribute('x',x1);rect.setAttribute('y',y1);rect.setAttribute('width',x2-x1);rect.setAttribute('height',y2-y1);rect.setAttribute('fill','none');rect.setAttribute('stroke',color);rect.setAttribute('stroke-width','2');overlay.append(rect);
  const text=document.createElementNS('http://www.w3.org/2000/svg','text');text.setAttribute('x',x1);text.setAttribute('y',Math.max(15,y1-4));text.setAttribute('fill',color);text.setAttribute('font-size','13');text.setAttribute('stroke','white');text.setAttribute('stroke-width','0.5');text.textContent=`${b.label} ${b.object_id||b.association} ${b.confidence.toFixed(2)}`;overlay.append(text);}
 const pos=f.camera_position_m?f.camera_position_m.map(v=>v.toFixed(3)).join(', '):'unavailable';
 document.getElementById('frame-info').textContent=`Frame ${current+1}/${REPLAY.frames.length} · ${f.timestamp_s.toFixed(6)} s\nCamera scene position (m): ${pos}\nRGB-D points in this frame: ${f.point_count}\nDetections: ${f.detections.length} · unresolved associations: ${f.failures.length}`;
 document.getElementById('object-info').textContent=tracks.length?tracks.map(o=>`${o.object_id} · ${o.label} · ${o.visible_now?'visible':'out of view; marker retained'} · last seen frame ${o.last_frame_index+1} · scene (${o.position_m.map(v=>v.toFixed(3)).join(', ')}) m`).join(String.fromCharCode(10)):'No located object markers yet.';
 document.getElementById('seek').value=String(current);document.getElementById('seek').max=String(REPLAY.frames.length-1);document.getElementById('counter').textContent=`${current+1} / ${REPLAY.frames.length}`;
}
function step(){if(current>=REPLAY.frames.length-1){stop();return;}const old=REPLAY.frames[current].timestamp_s,next=REPLAY.frames[current+1].timestamp_s;const scale=Number(document.getElementById('speed').value);timer=setTimeout(()=>{update(current+1);step();},Math.max(16,(next-old)*1000/scale));}
function stop(){if(timer!==null)clearTimeout(timer);timer=null;document.getElementById('play').textContent='Play';}
document.getElementById('seek').addEventListener('input',e=>{stop();update(Number(e.target.value));});
document.getElementById('prev').addEventListener('click',()=>{stop();update(current-1);});document.getElementById('next').addEventListener('click',()=>{stop();update(current+1);});
document.getElementById('play').addEventListener('click',()=>{if(timer!==null){stop();}else{document.getElementById('play').textContent='Pause';step();}});
Plotly.newPlot(graph,[trace,cameraTrace,objectTrace],layout,{responsive:true,displaylogo:false}).then(()=>update(0));
</script></body></html>"""
    page = page.replace("__PLOTLY__", plotly_js).replace("__DATA__", payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
