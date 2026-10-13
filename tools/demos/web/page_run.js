/* Walkthrough run report: frame sliders, per-frame error charts and 3D views. */
(() => {
  const D = DemoData.raw;
  const NS = "http://www.w3.org/2000/svg";

  // A line chart of one per-frame series, with a dashed line at its mean and a few gridlines.
  // Missing values (null) leave a break in the line; negative values get a zero line.
  // `reference` draws a second dashed line at a target value, for example 1.0 for a scale ratio.
  function chart(id, values, { unit = "", label = "", scale = 1, digits = 2, color, reference } = {}) {
    const svg = document.getElementById(id);
    const v = (values || []).map((x) => (x === null || x === undefined || !Number.isFinite(x) ? null : x * scale));
    const known = v.filter((val) => val !== null);
    if (!svg || !known.length) { if (svg) svg.remove(); return; }
    const ink = getComputedStyle(document.body).color, line = color || ink;
    const W = 640, H = 220, L = 58, R = 12, T = 18, B = 34;
    const hi = Math.max(0, ...known, reference ?? 0), lo = Math.min(0, ...known);
    const pad = 0.15 * (hi - lo || 1), top = hi + pad, bottom = lo < 0 ? lo - pad : 0;
    const span = top - bottom, magnitude = Math.pow(10, Math.floor(Math.log10(span / 4)));
    const step = magnitude * ([1, 2, 5].find((m) => span / 4 <= m * magnitude) || 10);
    const x = (i) => L + (v.length > 1 ? i / (v.length - 1) : 0.5) * (W - L - R);
    const y = (val) => H - B - ((val - bottom) / span) * (H - T - B);
    const el = (tag, attrs, text) => { const e = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, a]) => e.setAttribute(k, a)); if (text) e.textContent = text; svg.appendChild(e); return e; };
    for (let g = Math.ceil(bottom / step) * step; g <= top; g += step) {
      el("line", { x1: L, x2: W - R, y1: y(g), y2: y(g), stroke: ink, "stroke-opacity": Math.abs(g) < step / 2 ? 0.45 : 0.12 });
      el("text", { x: L - 6, y: y(g) + 4, "text-anchor": "end", "font-size": 11, fill: ink, "fill-opacity": 0.6 }, `${+g.toFixed(digits)}${unit}`);
    }
    const mean = known.reduce((a, b) => a + b, 0) / known.length;
    el("line", { x1: L, x2: W - R, y1: y(mean), y2: y(mean), stroke: "#f97316", "stroke-dasharray": "5 4" });
    let caption = `${label}; dashed line: mean ${mean.toFixed(digits)}${unit}`;
    if (reference !== undefined) {
      el("line", { x1: L, x2: W - R, y1: y(reference), y2: y(reference), stroke: "#2dd4bf", "stroke-dasharray": "2 3" });
      caption += `; dotted: ${reference}${unit}`;
    }
    el("text", { x: L + 6, y: T - 4, "font-size": 11, fill: "#f97316" }, caption);
    let run = [];
    const flush = () => { if (run.length > 1) el("polyline", { points: run.join(" "), fill: "none", stroke: line, "stroke-width": 2 }); run = []; };
    v.forEach((val, i) => {
      if (val === null) { flush(); return; }
      run.push(`${x(i)},${y(val)}`);
      el("circle", { cx: x(i), cy: y(val), r: 2.5, fill: line });
    });
    flush();
    el("text", { x: (W + L) / 2, y: H - 6, "text-anchor": "middle", "font-size": 11, fill: ink, "fill-opacity": 0.6 }, "frame");
  }

  // A slider that shows one sampled frame at a time.
  function slider(frames, show) {
    const input = document.getElementById("frame"), label = document.getElementById("frame-label");
    input.max = String(frames.length - 1);
    const update = () => { const f = frames[+input.value]; label.textContent = `${+input.value + 1} of ${frames.length}: ${f.id}`; show(f); };
    input.addEventListener("input", update); update();
  }

  function viewer(up) {
    const host = document.getElementById("viewer");
    try { return new DemoViewer(host.querySelector("canvas"), { up }); } catch (e) { showError(host, e); return null; }
  }

  function bounds(points) {
    const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    points.forEach((p) => p.forEach((c, a) => { lo[a] = Math.min(lo[a], c); hi[a] = Math.max(hi[a], c); }));
    return [lo, hi];
  }

  function path(V, name, points, rgb) {
    if (points.length < 2) { V.addPoints(name, new Float32Array(points.flat()), new Uint8Array(points.flatMap(() => rgb)), { size: 8 }); return; }
    const pos = [], col = [];
    for (let i = 1; i < points.length; i++) { pos.push(...points[i - 1], ...points[i]); col.push(...rgb, ...rgb); }
    V.addLines(name, new Float32Array(pos), new Uint8Array(col));
    V.addPoints(name + "-dots", new Float32Array(points.flat()), new Uint8Array(points.flatMap(() => rgb)), { size: 6 });
  }

  if (D.page === "01_depth.html") {
    const set = (id, src) => { const img = document.getElementById(id); if (src) { img.src = src; img.parentElement.hidden = false; } else img.parentElement.hidden = true; };
    slider(D.frames, (f) => { set("img-rgb", f.rgb); set("img-predicted", f.predicted); set("img-reference", f.reference); set("img-error", f.error); });
    chart("chart-absrel", D.absRel, { label: "Relative error (AbsRel) per frame", digits: 3 });
    chart("chart-rmse", D.rmse, { unit: " m", label: "Root-mean-square error per frame", digits: 2 });
    chart("chart-scale", D.scaleRatio, { label: "Predicted / sensor distance per frame", digits: 2, reference: 1 });
    chart("chart-fitted", D.fittedAbsRel, { label: "AbsRel left after a per-frame scale and shift fit", digits: 3 });
  }

  if (D.page === "02_camera.html") {
    const V = viewer(D.up);
    if (V) {
      D.segments.forEach((s, i) => { path(V, `est-${i}`, s.estimated, [249, 115, 22]); if (s.reference.length) path(V, `ref-${i}`, s.reference, [45, 212, 191]); });
      const [lo, hi] = bounds(D.segments.flatMap((s) => [...s.estimated, ...s.reference]));
      V.frameBox(lo, hi, { yaw: -1.9, pitch: 0.5, distance: 1.6 });
    }
    if (D.scored) chart("chart-camera", D.errorsMm, { unit: " mm", label: "Camera position error per frame", digits: 0 });
  }

  if (D.page === "03_surface.html") {
    const V = viewer(D.up);
    if (V) {
      V.addPoints("surface", DemoData.positions(D.points), DemoData.array(D.rgb), { size: 2 });
      if (D.cameras.length) V.addPoints("cameras", new Float32Array(D.cameras.flat()), new Uint8Array(D.cameras.flatMap(() => [255, 255, 255])), { size: 7 });
      V.frameBox(D.points.min, D.points.max, { yaw: -2.2, pitch: 0.55, distance: 0.9 });
    }
    chart("chart-gap1", D.gapLag1, { unit: " mm", scale: 1000, label: "Surface gap to the previous frame", digits: 0 });
    chart("chart-gap10", D.gapLag10, { unit: " mm", scale: 1000, label: "Surface gap to the frame 10 earlier", digits: 0 });
    chart("chart-gapsigned10", D.gapSignedLag10, { unit: " mm", scale: 1000, label: "Signed gap to the frame 10 earlier (later minus earlier)", digits: 0 });
  }

  if (D.page === "05_objects.html") {
    slider(D.frames, (f) => { document.getElementById("img-objects").src = f.image; });
  }
})();
