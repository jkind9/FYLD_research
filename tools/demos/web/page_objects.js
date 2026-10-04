/* Page 06: object identities across the replay, with a timeline, frame boxes and running counts. */
(() => {
  const D = DemoData.raw;
  const host = document.getElementById("viewer");
  let V;
  try { V = new DemoViewer(host.querySelector("canvas"), { up: D.up }); } catch (e) { showError(host, e); return; }

  const GREY = [150, 150, 150];
  const trackIndex = new Map(D.tracks.map((t) => [t.id, t.colour]));
  const colourOf = (id) => (id && trackIndex.has(id) ? hexColor(trackIndex.get(id)) : GREY);
  const css = (rgb) => `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
  const S = D.splat, sp = DemoData.positions(S.positions), sq = DemoData.array(S.normals), sn = new Float32Array(sq.length);
  for (let i = 0; i < sq.length; i++) sn[i] = sq[i] / 127;
  const ns = sp.length / 3;
  V.addSplats("scene", sp, sn, DemoData.array(S.colours), DemoData.array(S.alpha),
    new Float32Array(ns).fill(S.tangentSigma), new Float32Array(ns).fill(S.normalSigma));

  const pathPts = [], pathCols = [];
  D.frames.forEach((f, i) => {
    if (i > 0) { const a = D.frames[i - 1].pose, b = f.pose; pathPts.push(a[0][3], a[1][3], a[2][3], b[0][3], b[1][3], b[2][3]); pathCols.push(255, 210, 90, 255, 210, 90); }
  });
  V.addLines("path", new Float32Array(pathPts), new Uint8Array(pathCols));

  V.viewBehindPose(D.frames[0].pose, 1.2, 0.9);

  const labelsHost = host.querySelector(".labels");
  const labelEls = new Map();
  let labelData = [];
  V.onRender((viewer) => {
    for (const el of labelEls.values()) el.style.display = "none";
    for (const l of labelData) {
      let el = labelEls.get(l.id);
      if (!el) { el = document.createElement("div"); el.className = "label"; labelsHost.appendChild(el); labelEls.set(l.id, el); }
      const p = viewer.project(l.pos);
      if (!p) continue;
      el.style.display = ""; el.style.left = `${p.x}px`; el.style.top = `${p.y}px`;
      el.style.setProperty("--c", css(colourOf(l.id)));
      el.textContent = `${l.label} · ${l.id.replace("object-", "#")}`;
    }
  });

  const images = D.frames.map((f) => { const img = new Image(); img.src = f.image; return img; });
  const fc = document.getElementById("frame-canvas"), ctx = fc.getContext("2d");
  const slider = document.getElementById("timeline");
  let current = 0, centres = new Map();

  function drawFrame(i) {
    const f = D.frames[i], img = images[i];
    const paint = () => {
      ctx.drawImage(img, 0, 0, 320, 240);
      ctx.lineWidth = 2; ctx.font = "11px system-ui";
      for (const d of f.dets) {
        const c = css(colourOf(d.id)), [x1, y1, x2, y2] = d.box;
        ctx.strokeStyle = c; ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        const text = d.id ? `${d.label} ${d.id.replace("object-", "#")}` : `${d.label} ?`;
        const w = ctx.measureText(text).width + 6;
        ctx.fillStyle = c; ctx.fillRect(x1, Math.max(0, y1 - 14), w, 14);
        ctx.fillStyle = "#fff"; ctx.fillText(text, x1 + 3, Math.max(10, y1 - 3));
      }
    };
    if (img.complete) paint(); else img.onload = paint;
  }

  function update(i) {
    current = i; slider.value = String(i);
    const f = D.frames[i];
    document.getElementById("frame-label").textContent = `desk frame ${f.frame} (${i + 1} of ${D.frames.length})`;
    const hist = [], hc = [], cur = [], cc = [], sums = new Map();
    let seen = 0, unresolved = 0;
    D.frames.slice(0, i + 1).forEach((g, gi) => g.dets.forEach((d) => {
      seen++; if (!d.id) unresolved++;
      if (!d.world) return;
      (gi === i ? cur : hist).push(...d.world);
      (gi === i ? cc : hc).push(...colourOf(d.id));
      if (d.id) {
        const s = sums.get(d.id) || { pos: [0, 0, 0], n: 0, label: d.label };
        s.pos = s.pos.map((v, a) => v + d.world[a]); s.n++; sums.set(d.id, s);
      }
    }));
    V.addPoints("history", new Float32Array(hist), new Uint8Array(hc), { size: 6, order: 3 });
    V.addPoints("current", new Float32Array(cur), new Uint8Array(cc), { size: 13, order: 4 });
    const lines = [], colors = [];
    frustumLines(f.pose, 525, 525, 640, 480, 0.25, lines, colors, [255, 210, 90]);
    V.addLines("frustum", new Float32Array(lines), new Uint8Array(colors));
    const inFrame = new Set(f.dets.map((d) => d.id).filter(Boolean));
    labelData = [...sums.entries()].filter(([id]) => inFrame.has(id)).map(([id, s]) => ({ id, label: s.label, pos: s.pos.map((v) => v / s.n) }));
    centres = new Map([...sums.entries()].map(([id, s]) => [id, s.pos.map((v) => v / s.n)]));
    document.getElementById("count-title").textContent = `${sums.size} object${sums.size === 1 ? "" : "s"} counted so far`;
    document.getElementById("frame-summary").textContent =
      `${f.dets.length} detection${f.dets.length === 1 ? "" : "s"} in this frame. ${seen} detections so far, ${unresolved} not assigned to an object (grey).`;
    document.querySelectorAll(".chip").forEach((chip) => chip.setAttribute("aria-pressed", String(sums.has(chip.dataset.id))));
    drawFrame(i);
  }

  const chips = document.getElementById("chips");
  D.tracks.forEach((t) => {
    const b = document.createElement("button");
    b.className = "chip"; b.dataset.id = t.id; b.title = `${t.count} sightings; click to centre the view`;
    b.innerHTML = `<i style="background:${css(hexColor(t.colour))}"></i>`;
    b.appendChild(document.createTextNode(`${t.label} ${t.id.replace("object-", "#")} · ${t.count}`));
    b.addEventListener("click", () => {
      const c = centres.get(t.id);
      if (c) V.setOrbit(c, 0.9, V.yaw, Math.max(V.pitch, 0.4));
    });
    chips.appendChild(b);
  });

  slider.addEventListener("input", () => update(Number(slider.value)));
  let timer = null;
  const play = document.getElementById("play");
  play.addEventListener("click", () => {
    if (timer) { clearInterval(timer); timer = null; play.textContent = "▶ Play"; return; }
    if (current >= D.frames.length - 1) update(0);
    play.textContent = "❚❚ Pause";
    timer = setInterval(() => {
      if (current >= D.frames.length - 1) { clearInterval(timer); timer = null; play.textContent = "▶ Play"; return; }
      update(current + 1);
    }, 450);
  });
  document.querySelectorAll("[data-jump]").forEach((b) => b.addEventListener("click", () => {
    const id = D.story[b.dataset.jump], idx = D.frames.findIndex((f) => f.frame === id);
    if (idx >= 0) update(idx);
  }));
  update(0);
})();
