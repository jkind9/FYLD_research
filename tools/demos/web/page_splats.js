/* Page 04: desk scene as sparse points, merged points and Gaussian splats, with photo comparison. */
(() => {
  const D = DemoData.raw, S = D.splat;
  const host = document.getElementById("viewer");
  let V;
  try { V = new DemoViewer(host.querySelector("canvas"), { up: D.up }); } catch (e) { showError(host, e); return; }
  window.sceneViewer = V;  // page_capture.js adds its layers to the same viewer

  const pos = DemoData.positions(S.positions);
  const n = pos.length / 3;
  const normalsQ = DemoData.array(S.normals), normals = new Float32Array(normalsQ.length);
  for (let i = 0; i < normalsQ.length; i++) normals[i] = normalsQ[i] / 127;
  const colours = DemoData.array(S.colours), alpha = DemoData.array(S.alpha);
  const st = new Float32Array(n).fill(S.tangentSigma), sn = new Float32Array(n).fill(S.normalSigma);

  let mode = "splats", base = colours, showRemoved = false, hideRemoved = false;
  // Cells a clean-up removed (capture_scene --kept): optionally painted red, or hidden.
  const removed = S.removed && DemoData.array(S.removed);
  // Surface pieces, one set per neighbour rule: each splat's piece rank, largest first, and each piece's size.
  // The sliders pick a rule and keep its largest pieces above a size.
  const rules = S.pieces || [], ranks = [];
  let rank = null, sizes = null, keepPieces = Infinity, minPoints = 0;
  const off = (i) => (hideRemoved && removed[i]) || (rank && (rank[i] >= keepPieces || sizes[rank[i]] < minPoints));
  const paint = (c) => {
    if (c) base = c;
    const shown = showRemoved ? base.map((v, i) => (removed[Math.floor(i / 3)] ? [230, 40, 40][i % 3] : v)) : base;
    V.addSplats("splats", pos, normals, shown, alpha.map((a, i) => (off(i) ? 0 : a)), st, sn, { visible: mode === "splats" });
    let p = pos, c3 = shown;
    const keep = [];
    for (let i = 0; i < n; i++) if (!off(i)) keep.push(i);
    if (keep.length < n) {
      p = new Float32Array(keep.length * 3); c3 = new Uint8Array(keep.length * 3);
      keep.forEach((k, j) => { p.set(pos.subarray(3 * k, 3 * k + 3), 3 * j); c3.set(shown.subarray(3 * k, 3 * k + 3), 3 * j); });
    }
    V.addPoints("points", p, c3, { size: D.voxel * 0.8, worldSize: true, visible: mode === "points" });
  };
  paint(colours);
  if (rules.length) {
    const keepEl = document.getElementById("piece-keep"), minEl = document.getElementById("piece-min");
    const linksEl = document.getElementById("piece-links");
    const pieces = () => {
      const r = Number(linksEl.value);
      ranks[r] = ranks[r] || DemoData.array(rules[r].rank);
      rank = ranks[r]; sizes = rules[r].sizes;
      document.getElementById("piece-links-value").textContent = rules[r].neighbours;
      keepPieces = S.keepStops[Number(keepEl.value)];
      minPoints = S.smallestStops[Number(minEl.value)];
      let count = 0, points = 0;
      sizes.forEach((s, r) => { if (r < keepPieces && s >= minPoints) { count += 1; points += s; } });
      document.getElementById("piece-keep-value").textContent = keepPieces.toLocaleString();
      document.getElementById("piece-min-value").textContent = minPoints.toLocaleString();
      document.getElementById("piece-shown").textContent =
        `showing ${count.toLocaleString()} of ${sizes.length.toLocaleString()} pieces, ${points.toLocaleString()} of ${D.source.points.toLocaleString()} points`;
      paint();
    };
    [keepEl, minEl, linksEl].forEach((el) => el.addEventListener("input", pieces));
    pieces();
  }
  if (removed) {
    document.getElementById("show-removed").addEventListener("input", (e) => { showRemoved = e.target.checked; paint(); });
    document.getElementById("hide-removed").addEventListener("input", (e) => { hideRemoved = e.target.checked; paint(); });
  }
  const heights = S.heightColours && DemoData.array(S.heightColours);
  document.querySelectorAll("[data-colour]").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("[data-colour]").forEach((o) => o.setAttribute("aria-pressed", String(o === b)));
    paint(b.dataset.colour === "height" ? heights : colours);
  }));
  const oneWay = document.getElementById("one-way");
  if (oneWay) {
    const ceiling = document.getElementById("ceiling"), floor = document.getElementById("floor");
    const cut = () => {
      V.oneWay = oneWay.checked;
      V.cut = [Number(floor.value), Number(ceiling.value)];
      document.getElementById("ceiling-value").textContent = `${V.cut[1].toFixed(2)} m`;
      document.getElementById("floor-value").textContent = `${V.cut[0].toFixed(2)} m`;
      V.redraw();
    };
    [oneWay, ceiling, floor].forEach((el) => el.addEventListener("input", cut));
    cut();
  }

  const measure = document.getElementById("measure"), readout = document.getElementById("measure-value");
  if (measure) {
    let on = false, picks = [], down = null;
    // The front-most splat within 8 CSS pixels of the click that the height window and one-way setting still show.
    const pick = (x, y) => {
      const eye = V._camera().eye;
      let best = null;
      for (let i = 0; i < n; i++) {
        const p = [pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]], h = V3.dot(p, V.up);
        if (h < V.cut[0] || h > V.cut[1] || off(i)) continue;
        if (V.oneWay && V3.dot([normals[3 * i], normals[3 * i + 1], normals[3 * i + 2]], V3.sub(eye, p)) < 0) continue;
        const s = V.project(p);
        if (s && Math.hypot(s.x - x, s.y - y) < 8 && (!best || s.z < best.z)) best = { p, z: s.z };
      }
      return best && best.p;
    };
    const draw = () => {
      V.addPoints("measure-ends", new Float32Array(picks.flat()), new Uint8Array(picks.flatMap(() => [255, 220, 0])),
        { size: 0.04, worldSize: true, order: 3 });
      if (picks.length < 2) { V.remove("measure-line"); readout.textContent = "Click the second point."; return; }
      V.addLines("measure-line", new Float32Array(picks.flat()), new Uint8Array([255, 220, 0, 255, 220, 0]), { order: 3 });
      const d = V3.sub(picks[1], picks[0]), total = Math.hypot(d[0], d[1], d[2]), rise = Math.abs(V3.dot(d, V.up));
      const level = Math.sqrt(Math.max(total * total - rise * rise, 0));
      readout.textContent = `${total.toFixed(2)} m (level ${level.toFixed(2)} m, height ${rise.toFixed(2)} m)`;
    };
    measure.addEventListener("click", () => {
      on = !on; picks = [];
      measure.setAttribute("aria-pressed", String(on));
      ["measure-ends", "measure-line"].forEach((name) => V.remove(name));
      readout.textContent = on ? "Click the first point." : "";
    });
    V.canvas.addEventListener("pointerdown", (e) => { down = [e.offsetX, e.offsetY]; });
    V.canvas.addEventListener("pointerup", (e) => {
      if (!on || !down || Math.hypot(e.offsetX - down[0], e.offsetY - down[1]) > 4) return;
      const p = pick(e.offsetX, e.offsetY);
      if (!p) { readout.textContent = "No surface under that click; try again."; return; }
      if (picks.length === 2) picks = [];
      picks.push(p);
      draw();
    });
  }
  if (D.display) V.addPoints("display", DemoData.positions(D.display.positions), DemoData.array(D.display.colours),
    { size: 0.012, worldSize: true, visible: false });

  const fit = () => V.frameBox(S.positions.min, S.positions.max, { yaw: 0.6, pitch: 0.5, distance: 1.05 });
  document.getElementById("fit-scene")?.addEventListener("click", fit);
  document.getElementById("top-view")?.addEventListener("click", () => {
    V.frameBox(S.positions.min, S.positions.max, { yaw: 0, pitch: 1.55 });
  });
  if (D.frameScene) {
    fit();
    V.canvas.tabIndex = 0;
    V.canvas.addEventListener("keydown", (event) => {
      const steps = { ArrowLeft: [-0.12, 0], ArrowRight: [0.12, 0], ArrowUp: [0, 0.12], ArrowDown: [0, -0.12] };
      const step = steps[event.key];
      if (step) {
        event.preventDefault();
        V.setOrbit(V.target, V.dist, V.yaw + step[0], Math.max(-1.55, Math.min(1.55, V.pitch + step[1])));
      } else if (["+", "=", "-"].includes(event.key)) {
        event.preventDefault();
        const distance = Math.max(0.01, Math.min(100, V.dist * (event.key === "-" ? 1.1 : 0.9)));
        V.setOrbit(V.target, distance, V.yaw, V.pitch);
      }
    });
  }

  const setMode = (chosen) => {
    mode = chosen;
    document.querySelectorAll("[data-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === mode)));
    ["splats", "points", "display"].forEach((name) => V.setVisible(name, name === mode));
  };
  document.querySelectorAll("[data-mode]").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
  document.getElementById("splat-scale").addEventListener("input", (e) => { V.splatScale = Number(e.target.value); V.redraw(); });

  const photo = document.getElementById("compare-photo"), caption = document.getElementById("compare-caption");
  const buttons = document.getElementById("compare-buttons");  // the capture viewer's own player shows these instead
  const choose = buttons && ((c, btn) => {
    V.lookFromPose(c.pose, c.fy || D.fy, c.height || D.height);
    photo.src = c.photo;
    caption.textContent = `Real photo from ${D.sceneName || "desk"}, frame ${c.frame}. Drag to explore.`;
    buttons.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
  });
  if (buttons) D.compare.forEach((c, i) => {
    const b = document.createElement("button");
    b.className = "btn";
    b.textContent = c.label || `Frame ${c.frame}`;
    b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", () => choose(c, b));
    buttons.appendChild(b);
    if (i === 1 && !D.frameScene) setTimeout(() => choose(c, b), 0);
  });

  document.getElementById("download-ply").addEventListener("click", () => {
    const props = ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2", "opacity",
      "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"];
    const header = `ply\nformat binary_little_endian 1.0\nelement vertex ${n}\n` +
      props.map((p) => `property float ${p}`).join("\n") + "\nend_header\n";
    const body = new Float32Array(n * props.length);
    const C0 = 0.28209479177387814, ls = Math.log(S.tangentSigma), lt = Math.log(S.normalSigma);
    for (let i = 0; i < n; i++) {
      const o = i * props.length;
      const nx = normals[3 * i], ny = normals[3 * i + 1], nz = normals[3 * i + 2], l = Math.hypot(nx, ny, nz) || 1;
      let w = 1 + nz / l, qx = -ny / l, qy = nx / l, qz = 0;
      if (w < 1e-6) { w = 0; qx = 1; qy = 0; }
      const ql = Math.hypot(w, qx, qy, qz);
      const a = Math.min(Math.max(alpha[i] / 255, 0.01), 0.99);
      body.set([pos[3 * i], pos[3 * i + 1], pos[3 * i + 2], nx / l, ny / l, nz / l,
        (colours[3 * i] / 255 - 0.5) / C0, (colours[3 * i + 1] / 255 - 0.5) / C0, (colours[3 * i + 2] / 255 - 0.5) / C0,
        Math.log(a / (1 - a)), ls, ls, lt, w / ql, qx / ql, qy / ql, qz / ql], o);
    }
    const blob = new Blob([header, body.buffer], { type: "application/octet-stream" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = D.downloadName || "desk_gaussian_splats.ply";
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 5000);
  });
})();
