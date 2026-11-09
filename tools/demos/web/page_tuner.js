/* Clean-up tuner: the raw fused room, with each clean-up stage recomputed in the browser from slider values.
 * Stages run in order on the points earlier stages kept. Vote, seen, spots and statistical outliers threshold
 * per-point evidence computed in Python; radius outliers and chain linking search neighbours here. */
(() => {
  const D = DemoData.raw;
  const P = DemoData.positions(D.positions), n = P.length / 3;
  const photo = DemoData.array(D.colours), q = DemoData.array(D.normals);
  const N = new Float32Array(3 * n);
  for (let i = 0; i < n; i++) {
    const l = Math.hypot(q[3 * i], q[3 * i + 1], q[3 * i + 2]) || 1;
    for (let a = 0; a < 3; a++) N[3 * i + a] = q[3 * i + a] / l;
  }
  const seen = DemoData.array(D.seen), seeThrough = DemoData.array(D.seeThrough);
  const nearestMm = DemoData.array(D.nearestMm), angleTenths = DemoData.array(D.angleTenths);
  const knn = DemoData.array(D.knnTenthMm);
  let knnSum = 0, knnSq = 0;
  for (let i = 0; i < n; i++) { const d = knn[i] / 1e4; knnSum += d; knnSq += d * d; }
  const knnMean = knnSum / n, knnStd = Math.sqrt(Math.max(knnSq / n - knnMean * knnMean, 0));
  const lo = D.positions.min, hi = D.positions.max;

  const ORDER = ["vote", "seen", "spots", "sor", "radius", "chain"];
  const COLOURS = { vote: [230, 40, 40], seen: [255, 140, 0], spots: [235, 215, 0], sor: [170, 70, 230],
    radius: [40, 130, 255], chain: [255, 60, 200] };
  const value = {}, enabled = {};
  const panel = document.getElementById("tuner-controls");
  const shown = (p, v) => (p.log ? Math.round(10 ** v) : v);

  for (const stage of D.stages) {
    const box = document.createElement("fieldset");
    box.className = "tuner-stage";
    const legend = document.createElement("legend");
    if (stage.id === "display") {
      legend.textContent = stage.label;
    } else {
      const tick = document.createElement("input");
      tick.type = "checkbox"; tick.id = `on-${stage.id}`;
      enabled[stage.id] = false; box.classList.add("off");
      tick.addEventListener("change", () => { enabled[stage.id] = tick.checked; box.classList.toggle("off", !tick.checked); update(); });
      const name = document.createElement("label");
      name.htmlFor = tick.id; name.textContent = ` ${stage.label}`;
      legend.append(tick, name);
    }
    const about = document.createElement("p");
    about.textContent = stage.description;
    box.append(legend, about);
    for (const p of D.params.filter((x) => x.stage === stage.id)) {
      const wrap = document.createElement("div");
      wrap.className = "param";
      const label = document.createElement("label"), out = document.createElement("output"), input = document.createElement("input");
      input.type = "range"; input.id = `p-${p.id}`;
      input.min = p.log ? Math.log10(p.min) : p.min; input.max = p.log ? Math.log10(p.max) : p.max; input.step = p.step;
      input.value = p.log ? Math.log10(p.value) : p.value;
      label.htmlFor = input.id;
      label.append(document.createTextNode(p.label), out);
      const text = document.createElement("p");
      text.textContent = p.description;
      const show = () => {
        value[p.id] = shown(p, Number(input.value));
        out.textContent = `${value[p.id].toLocaleString()} ${p.unit}`.trim();
      };
      show();
      input.addEventListener("input", () => { show(); if (stage.id === "display") display(); });
      input.addEventListener("change", () => { if (stage.id !== "display") update(); });
      wrap.append(label, input, text);
      box.append(wrap);
    }
    panel.append(box);
  }
  document.getElementById("legend").innerHTML = ORDER.map((s) =>
    `<span><span style="display:inline-block;width:.8em;height:.8em;border-radius:2px;background:rgb(${COLOURS[s]})"></span> ` +
    `${D.stages.find((x) => x.id === s).label}</span>`).join(" ");

  /* Points sorted by grid cell. Cell keys and point order are packed into one float so a native sort does both. */
  function grid(ids, cell) {
    const inv = 1 / cell, ny = Math.floor((hi[1] - lo[1]) * inv) + 3, nz = Math.floor((hi[2] - lo[2]) * inv) + 3;
    const SH = 2 ** 21, packed = new Float64Array(ids.length);
    for (let j = 0; j < ids.length; j++) {
      const i = ids[j];
      const key = (Math.floor((P[3 * i] - lo[0]) * inv) + 1) * ny * nz + (Math.floor((P[3 * i + 1] - lo[1]) * inv) + 1) * nz +
        Math.floor((P[3 * i + 2] - lo[2]) * inv) + 1;
      packed[j] = key * SH + j;
    }
    packed.sort();
    const sorted = new Uint32Array(ids.length), keys = [], starts = [];
    for (let j = 0, last = -1; j < ids.length; j++) {
      const key = Math.floor(packed[j] / SH);
      sorted[j] = ids[packed[j] - key * SH];
      if (key !== last) { keys.push(key); starts.push(j); last = key; }
    }
    starts.push(ids.length);
    const offsets = [];
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) offsets.push(dx * ny * nz + dy * nz + dz);
    return { sorted, keys: Float64Array.from(keys), starts: Uint32Array.from(starts), offsets };
  }

  function findCell(keys, key) {
    let a = 0, b = keys.length - 1;
    while (a <= b) {
      const m = (a + b) >> 1;
      if (keys[m] === key) return m;
      if (keys[m] < key) a = m + 1; else b = m - 1;
    }
    return -1;
  }

  /* Calls visit(a, b) for every ordered pair of points within radius whose normals differ by under maxDeg,
   * including each point with itself. */
  function pairs(g, radius, maxDeg, visit) {
    const r2 = radius * radius, cosMax = maxDeg >= 90 ? -1 : Math.cos(maxDeg * Math.PI / 180);
    const { sorted, keys, starts, offsets } = g;
    for (let c = 0; c < keys.length; c++) {
      for (const off of offsets) {
        const d = off === 0 ? c : findCell(keys, keys[c] + off);
        if (d < 0) continue;
        for (let s = starts[c]; s < starts[c + 1]; s++) {
          const a = sorted[s], ax = P[3 * a], ay = P[3 * a + 1], az = P[3 * a + 2];
          for (let t = starts[d]; t < starts[d + 1]; t++) {
            const b = sorted[t], dx = P[3 * b] - ax, dy = P[3 * b + 1] - ay, dz = P[3 * b + 2] - az;
            if (dx * dx + dy * dy + dz * dz > r2) continue;
            if (cosMax > -1 && Math.abs(N[3 * a] * N[3 * b] + N[3 * a + 1] * N[3 * b + 1] + N[3 * a + 2] * N[3 * b + 2]) < cosMax) continue;
            visit(a, b);
          }
        }
      }
    }
  }

  function keptIds(removedBy) {
    let m = 0;
    for (let i = 0; i < n; i++) if (!removedBy[i]) m++;
    const ids = new Uint32Array(m);
    for (let i = 0, j = 0; i < n; i++) if (!removedBy[i]) ids[j++] = i;
    return ids;
  }

  /* DBSCAN as in Open3D's cluster_dbscan: a point with at least minPts neighbours (itself included) is a core point;
   * core points within the link distance join one piece; other points join a piece they touch, or are noise. */
  function chainPieces(ids, eps, minPts, maxDeg) {
    const g = grid(ids, eps), count = new Uint32Array(n);
    pairs(g, eps, maxDeg, (a) => { count[a]++; });
    const parent = new Int32Array(n), border = new Int32Array(n).fill(-1);
    for (const i of ids) parent[i] = i;
    const root = (i) => { while (parent[i] !== i) { parent[i] = parent[parent[i]]; i = parent[i]; } return i; };
    pairs(g, eps, maxDeg, (a, b) => {
      if (count[b] < minPts) return;
      if (count[a] >= minPts) { const ra = root(a), rb = root(b); if (ra !== rb) parent[ra] = rb; } else if (border[a] < 0) border[a] = b;
    });
    const piece = new Int32Array(n).fill(-1);
    for (const i of ids) piece[i] = count[i] >= minPts ? root(i) : border[i] >= 0 ? root(border[i]) : -1;
    return piece;
  }

  const cache = {};
  function cached(name, key, compute) {
    if (cache[name]?.key !== key) cache[name] = { key, result: compute() };
    return cache[name].result;
  }

  const removedBy = new Uint8Array(n);
  let report = "";
  function update() {
    const t0 = performance.now(), removed = {}, notes = [];
    removedBy.fill(0);
    const drop = (stage, test) => {
      let k = 0;
      for (let i = 0; i < n; i++) if (!removedBy[i] && test(i)) { removedBy[i] = ORDER.indexOf(stage) + 1; k++; }
      removed[stage] = k;
    };
    if (enabled.vote) drop("vote", (i) => seeThrough[i] > value.voteMax * 255 + 0.5);
    if (enabled.seen) drop("seen", (i) => seen[i] < value.seenMin);
    if (enabled.spots) drop("spots", (i) => nearestMm[i] >= value.spotNear * 1000 && angleTenths[i] < value.spotAngle * 10 - 0.5);
    if (enabled.sor) drop("sor", (i) => knn[i] / 1e4 > knnMean + value.sorRatio * knnStd);
    const upstream = JSON.stringify(["vote", "seen", "spots", "sor"].map((s) => enabled[s]))
      + JSON.stringify(D.params.filter((p) => ["vote", "seen", "spots", "sor"].includes(p.stage)).map((p) => value[p.id]));
    if (enabled.radius) {
      const r = value.radiusCm / 100, need = value.radiusMin;
      const count = cached("radius", `${upstream}|${r}`, () => {
        const c = new Uint32Array(n);
        pairs(grid(keptIds(removedBy), r), r, 180, (a) => { c[a]++; });
        return c;
      });
      drop("radius", (i) => count[i] - 1 < need);
    }
    if (enabled.chain) {
      const eps = value.linkCm / 100;
      const key = `${upstream}|${enabled.radius}|${value.radiusCm}|${value.radiusMin}|${eps}|${value.linkMinNeighbours}|${value.linkNormalDeg}`;
      const piece = cached("chain", key, () => chainPieces(keptIds(removedBy), eps, value.linkMinNeighbours, value.linkNormalDeg));
      const size = new Map();
      for (let i = 0; i < n; i++) if (!removedBy[i] && piece[i] >= 0) size.set(piece[i], (size.get(piece[i]) || 0) + 1);
      const ranked = [...size.entries()].sort((x, y) => y[1] - x[1]);
      const keep = new Set(ranked.filter(([, s], k) => s >= value.pieceMin && k < value.pieceKeep).map(([id]) => id));
      let noise = 0, kept = 0;
      for (let i = 0; i < n; i++) if (!removedBy[i] && piece[i] < 0) noise++;
      for (const [id, s] of ranked) if (keep.has(id)) kept += s;
      drop("chain", (i) => !keep.has(piece[i]));
      const total = ranked.reduce((t, [, s]) => t + s, 0);
      notes.push(`Chain linking: ${ranked.length.toLocaleString()} pieces, ${keep.size.toLocaleString()} kept; ` +
        `largest holds ${ranked.length ? (100 * ranked[0][1] / total).toFixed(1) : 0}% of linked points; ` +
        `${noise.toLocaleString()} points touched no chain`);
    }
    const left = n - Object.values(removed).reduce((t, k) => t + k, 0);
    report = `Kept ${left.toLocaleString()} of ${n.toLocaleString()} points (${(100 * left / n).toFixed(1)}%), ` +
      `computed in ${Math.round(performance.now() - t0)} ms\n` +
      ORDER.filter((s) => enabled[s]).map((s) => `  removed by ${D.stages.find((x) => x.id === s).label}: ${removed[s].toLocaleString()}`).join("\n") +
      (notes.length ? `\n${notes.join("\n")}` : "");
    document.getElementById("stats").textContent = report;
    document.getElementById("settings").value = JSON.stringify({
      stages: ORDER.filter((s) => enabled[s]),
      settings: Object.fromEntries(D.params.filter((p) => p.stage !== "display" && enabled[p.stage]).map((p) => [p.id, value[p.id]])),
      kept_points: left, total_points: n,
    }, null, 1);
    paint();
  }

  const V = new DemoViewer(document.querySelector("#viewer canvas"), { up: D.up });
  const sigmaT = new Float32Array(n).fill(D.splatSigma[0]), sigmaN = new Float32Array(n).fill(D.splatSigma[1]);
  function paint() {
    const showRemoved = document.getElementById("show-removed").checked;
    const visible = (i) => !removedBy[i] || showRemoved;
    const colour = (i, a) => (removedBy[i] ? COLOURS[ORDER[removedBy[i] - 1]][a] : photo[3 * i + a]);
    if (document.getElementById("as-points").checked) {
      let m = 0;
      for (let i = 0; i < n; i++) if (visible(i)) m++;
      const pos = new Float32Array(3 * m), col = new Uint8Array(3 * m);
      for (let i = 0, j = 0; i < n; i++) {
        if (!visible(i)) continue;
        for (let a = 0; a < 3; a++) { pos[3 * j + a] = P[3 * i + a]; col[3 * j + a] = colour(i, a); }
        j++;
      }
      V.remove("splats");
      V.addPoints("points", pos, col, { size: D.splatSigma[0], worldSize: true });
    } else {
      const col = new Uint8Array(3 * n), alpha = new Uint8Array(n);
      for (let i = 0; i < n; i++) {
        alpha[i] = visible(i) ? 230 : 0;
        for (let a = 0; a < 3; a++) col[3 * i + a] = colour(i, a);
      }
      V.remove("points");
      V.addSplats("splats", P, N, col, alpha, sigmaT, sigmaN);
    }
    display();
  }
  function display() {
    V.cut = [-1e9, D.lowest + value.heightMax + 1e-6];
    V.splatScale = value.splatScale;
    V.redraw();
  }
  document.getElementById("show-removed").addEventListener("change", paint);
  document.getElementById("as-points").addEventListener("change", paint);

  const views = document.getElementById("views");
  const button = (text, act) => {
    const b = document.createElement("button");
    b.className = "btn"; b.textContent = text; b.addEventListener("click", act);
    views.append(b);
  };
  button("Whole room", () => V.frameBox(lo, hi, { yaw: 0.6, pitch: 0.5, distance: 1.05 }));
  button("From above", () => V.frameBox(lo, hi, { yaw: 0, pitch: 1.55 }));
  for (const c of D.compare) button(`From frame ${c.frame}`, () => V.lookFromPose(c.pose, c.fy, c.height));
  V.frameBox(lo, hi, { yaw: 0.6, pitch: 0.5, distance: 1.05 });
  update();
  window.cleanupTuner = { report: () => report, value, enabled, update };
})();
