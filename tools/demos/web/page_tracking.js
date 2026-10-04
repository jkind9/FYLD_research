/* Page 02: estimated versus motion-capture camera path, with per-frame error chart. */
(() => {
  const D = DemoData.raw;
  document.getElementById("img-first").src = D.images.first;
  document.getElementById("img-last").src = D.images.last;

  const host = document.getElementById("viewer");
  let V;
  try { V = new DemoViewer(host.querySelector("canvas"), { up: D.up }); } catch (e) { showError(host, e); return; }

  const EST = [249, 115, 22], REF = [45, 212, 191];
  const centre = (T) => [T[0][3], T[1][3], T[2][3]];
  function path(name, poses, rgb) {
    const lines = [], colors = [], pts = [], pc = [];
    poses.forEach((T, i) => {
      pts.push(...centre(T)); pc.push(...rgb);
      if (i > 0) { lines.push(...centre(poses[i - 1]), ...centre(T)); colors.push(...rgb, ...rgb); }
      if (i % 3 === 0) frustumLines(T, 525, 525, 640, 480, 0.04, lines, colors, rgb);
    });
    V.addLines(name + "-lines", new Float32Array(lines), new Uint8Array(colors));
    V.addPoints(name + "-points", new Float32Array(pts), new Uint8Array(pc), { size: 6 });
  }
  V.addPoints("context", DemoData.positions(D.context), DemoData.array(D.contextRgb), { size: 0.006, worldSize: true });
  path("reference", D.reference, REF);
  path("estimated", D.estimated, EST);

  const all = [...D.reference, ...D.estimated].map(centre);
  const lo = [0, 1, 2].map((a) => Math.min(...all.map((p) => p[a])) - 0.015);
  const hi = [0, 1, 2].map((a) => Math.max(...all.map((p) => p[a])) + 0.015);
  const slo = lo.map((v, a) => Math.min(v, D.contextFocus[0][a])), shi = hi.map((v, a) => Math.max(v, D.contextFocus[1][a]));
  const scene = () => V.frameBox(slo, shi, { yaw: -2.2, pitch: 0.5, distance: 0.85 });
  const zoom = () => V.frameBox(lo, hi, { yaw: -1.9, pitch: 0.5, distance: 1.4 });
  scene();
  document.getElementById("fit").addEventListener("click", scene);
  document.getElementById("zoom").addEventListener("click", zoom);

  const svg = document.getElementById("chart"), NS = "http://www.w3.org/2000/svg";
  const W = 640, H = 220, L = 46, R = 12, T = 14, B = 34;
  const max = Math.max(...D.errorsMm, D.rmseMm) * 1.15;
  const x = (i) => L + (i / (D.errorsMm.length - 1)) * (W - L - R), y = (v) => H - B - (v / max) * (H - T - B);
  const el = (tag, attrs, text) => {
    const e = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
    if (text) e.textContent = text;
    svg.appendChild(e); return e;
  };
  const ink = getComputedStyle(document.body).color;
  for (let v = 0; v <= max; v += 5) {
    el("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: ink, "stroke-opacity": 0.12 });
    el("text", { x: L - 8, y: y(v) + 4, "text-anchor": "end", "font-size": 11, fill: ink, "fill-opacity": 0.6 }, `${v} mm`);
  }
  el("line", { x1: L, x2: W - R, y1: y(D.rmseMm), y2: y(D.rmseMm), stroke: "#f97316", "stroke-dasharray": "5 4" });
  el("text", { x: L + 6, y: T + 4, "text-anchor": "start", "font-size": 11, fill: "#f97316" }, `dashed line: typical error ${D.rmseMm.toFixed(1)} mm`);
  el("polyline", { points: D.errorsMm.map((v, i) => `${x(i)},${y(v)}`).join(" "), fill: "none", stroke: ink, "stroke-width": 2 });
  D.errorsMm.forEach((v, i) => el("circle", { cx: x(i), cy: y(v), r: 3, fill: ink }));
  el("text", { x: (W + L) / 2, y: H - 6, "text-anchor": "middle", "font-size": 11, fill: ink, "fill-opacity": 0.6 }, "frame");
})();
