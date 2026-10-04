/* Offline CPU projection of validated display geometry. */
(() => {
  'use strict';
  const scene = JSON.parse(document.getElementById('scene-data').textContent);
  const canvas = document.getElementById('scene');
  const ctx = canvas.getContext('2d');
  const slider = document.getElementById('frame');
  const segment = document.getElementById('segment');
  const reference = document.getElementById('reference');
  reference.checked = !scene.reference_points;
  let state = {yaw: -0.55, pitch: -0.25, zoom: 1, panX: 0, panY: 0};
  let dragging = null;
  const frames = scene.frames;
  slider.max = Math.max(0, frames.length - 1);
  slider.value = slider.max;
  slider.disabled = frames.length === 0;
  ['previous','next'].forEach(id => {document.getElementById(id).disabled = frames.length === 0;});
  document.getElementById('note').textContent = scene.note;
  [...new Set(frames.map(f => f.segment).filter(v => v !== null))].forEach(value => {
    const option = document.createElement('option');
    option.value = value; option.textContent = value;
    segment.append(option);
  });
  const lastSegment = [...frames].reverse().find(f => f.segment !== null)?.segment;
  if (lastSegment !== undefined) segment.value = String(lastSegment);
  const vertices = [...(scene.reference_points?.points || []), ...frames.flatMap(f => [...(f.points || []), ...(f.camera || []), ...(f.reference_camera || [])])];
  const geometryAvailable = vertices.length > 0;
  const bounds = geometryAvailable ? vertices : [[0,0,0],[1,1,1]];
  const min = [0,1,2].map(axis => bounds.reduce((v,p) => Math.min(v,p[axis]), Infinity));
  const max = [0,1,2].map(axis => bounds.reduce((v,p) => Math.max(v,p[axis]), -Infinity));
  const centre = min.map((v,i) => (v+max[i])/2);
  const span = Math.max(...max.map((v,i) => v-min[i]), 0.01);
  function project(point) {
    const [x,y,z] = point.map((v,i) => v-centre[i]);
    const a = Math.cos(state.yaw)*x + Math.sin(state.yaw)*z;
    const b = -Math.sin(state.yaw)*x + Math.cos(state.yaw)*z;
    const c = Math.cos(state.pitch)*y - Math.sin(state.pitch)*b;
    const d = Math.sin(state.pitch)*y + Math.cos(state.pitch)*b;
    const scale = 440*state.zoom/span;
    return [canvas.width/2+state.panX+a*scale, canvas.height/2+state.panY-c*scale, d];
  }
  function line(a,b,colour,width=2) {
    const p=project(a),q=project(b); ctx.strokeStyle=colour;ctx.lineWidth=width;
    ctx.beginPath();ctx.moveTo(p[0],p[1]);ctx.lineTo(q[0],q[1]);ctx.stroke();
  }
  function camera(points,colour) {
    if (!points) return;
    [1,2,3,4].forEach(i => {line(points[0],points[i],colour);line(points[i],points[i===4?1:i+1],colour);});
  }
  function selectedFrames(index) {
    return frames.slice(0,index+1).filter(f => String(f.segment)===segment.value);
  }
  function draw() {
    const index=Number(slider.value), frame=frames[index];
    ctx.clearRect(0,0,canvas.width,canvas.height);
    const visible=selectedFrames(index);
    const layers=reference.checked && scene.reference_points ? [...visible,scene.reference_points] : visible;
    const points=layers.flatMap(f => (f.points||[]).map((p,i) => ({p:project(p),c:f.colours[i]}))).sort((a,b) => a.p[2]-b.p[2]);
    points.forEach(({p,c}) => {ctx.fillStyle=`rgb(${c.join(',')})`;ctx.fillRect(p[0],p[1],2,2);});
    let previous=null;
    visible.forEach(f => {
      if (previous && f.camera && previous.camera && Number(f.order)===Number(previous.order)+1) {
        line(previous.camera[0],f.camera[0],'#bd3b22',3);
        if(reference.checked && previous.reference_camera && f.reference_camera) line(previous.reference_camera[0],f.reference_camera[0],'#187d5c',3);
      }
      previous=f;
    });
    if(frame && String(frame.segment)===segment.value) {
      camera(frame.camera,'#bd3b22');
      if(reference.checked) camera(frame.reference_camera,'#187d5c');
    }
    const length=span*.18;
    if (geometryAvailable) ['X','Y','Z'].forEach((label,i) => {const p=[...centre];p[i]+=length;line(centre,p,['#b12630','#14844e','#215cd0'][i]);const q=project(p);ctx.fillStyle='#172330';ctx.fillText(label,q[0],q[1]);});
    document.getElementById('details').textContent=frame?`Frame ${frame.id} | ${frame.status}\n${frame.caption}\n${scene.full_count !== undefined ? 'Surface points: '+scene.full_count.toLocaleString()+' full, '+scene.display_count.toLocaleString()+' displayed.\n' : ''}${frame.camera ? 'Camera centre XYZ (m): '+frame.camera[0].map(v=>v.toFixed(5)).join(', ') : 'No estimated pose for this observation.'}`:'No frames';
    const sources=document.getElementById('sources');sources.replaceChildren();
    (frame?.images||[]).forEach(image => {
      const figure=document.createElement('figure'), img=document.createElement('img'), caption=document.createElement('figcaption'), link=document.createElement('a');
      img.src=image.path;img.alt=image.caption;caption.textContent=image.caption+' ';link.href=image.raw;link.textContent=image.raw_label||'Original raw input';caption.append(link);figure.append(img,caption);sources.append(figure);
    });
  }
  slider.addEventListener('input', () => {const f=frames[Number(slider.value)];if(f && f.segment!==null) segment.value=f.segment;draw();});
  segment.addEventListener('change',draw);reference.addEventListener('change',draw);
  ['previous','next'].forEach(id => document.getElementById(id).addEventListener('click',() => {slider.value=Math.min(frames.length-1,Math.max(0,Number(slider.value)+(id==='next'?1:-1)));slider.dispatchEvent(new Event('input'));}));
  document.getElementById('reset').addEventListener('click',() => {state={yaw:-.55,pitch:-.25,zoom:1,panX:0,panY:0};draw();});
  canvas.addEventListener('contextmenu',e=>e.preventDefault());
  canvas.addEventListener('pointerdown',e=>{if(![0,1,2].includes(e.button))return;dragging={x:e.clientX,y:e.clientY,mode:e.button===0&&!e.shiftKey?'orbit':'pan'};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{if(!dragging)return;const dx=e.clientX-dragging.x,dy=e.clientY-dragging.y;if(dragging.mode==='pan'){const bounds=canvas.getBoundingClientRect();state={...state,panX:state.panX+dx*canvas.width/bounds.width,panY:state.panY+dy*canvas.height/bounds.height};}else{state={...state,yaw:state.yaw+dx*.008,pitch:Math.max(-1.5,Math.min(1.5,state.pitch+dy*.008))};}dragging={...dragging,x:e.clientX,y:e.clientY};draw();});
  canvas.addEventListener('pointerup',()=>{dragging=null;});
  canvas.addEventListener('wheel',e=>{e.preventDefault();state={...state,zoom:Math.max(.2,Math.min(10,state.zoom*Math.exp(-e.deltaY*.001)))};draw();},{passive:false});
  canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();if(e.shiftKey){state={...state,panX:state.panX+(e.key==='ArrowLeft'?24:e.key==='ArrowRight'?-24:0),panY:state.panY+(e.key==='ArrowUp'?24:e.key==='ArrowDown'?-24:0)};}else{state={...state,yaw:state.yaw+(e.key==='ArrowLeft'?-.1:e.key==='ArrowRight'?.1:0),pitch:state.pitch+(e.key==='ArrowUp'?-.1:e.key==='ArrowDown'?.1:0)};}draw();});
  draw();
})();
