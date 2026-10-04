/* Page 05: top-down map with layer switch, hover height readout and two-point measurement. */
(() => {
  const D = DemoData.raw;
  const canvas = document.getElementById("map"), ctx = canvas.getContext("2d");
  const heights = DemoData.array(D.heights);
  const images = {};
  let layer = "colour", picks = [], hover = null, fit = null;

  const load = (name) => new Promise((resolve) => { const img = new Image(); img.onload = () => resolve(img); img.src = D.images[name]; });
  Promise.all(["colour", "height", "seen"].map(load)).then(([c, h, s]) => { images.colour = c; images.height = h; images.seen = s; draw(); });

  const checker = (() => {
    const p = document.createElement("canvas"); p.width = p.height = 16;
    const g = p.getContext("2d"); g.fillStyle = "#c9c4b8"; g.fillRect(0, 0, 16, 16);
    g.fillStyle = "#b3ad9f"; g.fillRect(0, 0, 8, 8); g.fillRect(8, 8, 8, 8);
    return p;
  })();

  function cellAt(x, y) {
    if (!fit) return null;
    const col = Math.floor((x - fit.x) / fit.s), row = Math.floor((y - fit.y) / fit.s);
    if (col < 0 || row < 0 || col >= D.width || row >= D.height) return null;
    const mm = heights[row * D.width + col];
    return { col, row, seen: mm !== 65535, h: mm === 65535 ? null : mm / 1000 + D.heightOffset };
  }

  function draw() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const s = Math.min((w - 24) / D.width, (h - 24) / D.height);
    fit = { s, x: (w - D.width * s) / 2, y: (h - D.height * s) / 2 };
    ctx.fillStyle = ctx.createPattern(checker, "repeat");
    ctx.fillRect(fit.x, fit.y, D.width * s, D.height * s);
    ctx.imageSmoothingEnabled = false;
    if (images[layer]) ctx.drawImage(images[layer], fit.x, fit.y, D.width * s, D.height * s);
    const scaleM = 0.5, px = scaleM / D.cell * s;
    ctx.fillStyle = "rgba(255,255,255,.85)"; ctx.fillRect(fit.x + 4, fit.y + 4, px + 16, 30);
    ctx.fillStyle = "#1d1f22"; ctx.fillRect(fit.x + 12, fit.y + 24, px, 4);
    ctx.font = "12px system-ui"; ctx.fillText(`${scaleM} m`, fit.x + 12, fit.y + 19);
    ctx.strokeStyle = "#c2410c"; ctx.fillStyle = "#c2410c"; ctx.lineWidth = 2;
    const pts = hover && picks.length === 1 ? [...picks, hover] : picks;
    pts.forEach((p) => { ctx.beginPath(); ctx.arc(fit.x + (p.col + 0.5) * s, fit.y + (p.row + 0.5) * s, 4, 0, 7); ctx.fill(); });
    if (pts.length === 2) {
      ctx.beginPath();
      ctx.moveTo(fit.x + (pts[0].col + 0.5) * s, fit.y + (pts[0].row + 0.5) * s);
      ctx.lineTo(fit.x + (pts[1].col + 0.5) * s, fit.y + (pts[1].row + 0.5) * s);
      ctx.stroke();
    }
  }

  const describe = (c) => (c.seen ? `${c.h.toFixed(2)} m above the floor` : "never seen (unknown)");
  canvas.addEventListener("mousemove", (e) => {
    const r = canvas.getBoundingClientRect(), c = cellAt(e.clientX - r.left, e.clientY - r.top);
    hover = c;
    document.getElementById("readout").textContent = c ? `Height here: ${describe(c)}.` : "Hover over the map to see the height at a point.";
    if (picks.length === 1) draw();
  });
  canvas.addEventListener("click", (e) => {
    const r = canvas.getBoundingClientRect(), c = cellAt(e.clientX - r.left, e.clientY - r.top);
    if (!c) return;
    picks = picks.length >= 2 ? [c] : [...picks, c];
    const out = document.getElementById("measure");
    if (picks.length === 2) {
      const [a, b] = picks, d = Math.hypot(a.col - b.col, a.row - b.row) * D.cell;
      const dh = a.seen && b.seen ? ` Height difference ${Math.abs(a.h - b.h).toFixed(2)} m.` : " One end is unknown, so no height difference.";
      out.textContent = `Distance across the ground: ${d.toFixed(2)} m (±${D.cell.toFixed(2)} m from the cell size).${dh}`;
    } else {
      out.textContent = "Now click a second point.";
    }
    draw();
  });
  document.getElementById("clear-measure").addEventListener("click", () => {
    picks = []; document.getElementById("measure").textContent = "Click two points to measure the distance between them."; draw();
  });
  document.querySelectorAll("[data-layer]").forEach((b) => b.addEventListener("click", () => {
    layer = b.dataset.layer;
    document.querySelectorAll("[data-layer]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    document.getElementById("legend-wrap").hidden = layer !== "height";
    draw();
  }));
  document.getElementById("legend").style.background = D.legend.gradient;
  new ResizeObserver(draw).observe(canvas);
})();
