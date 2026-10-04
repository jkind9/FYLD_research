/* Page 03: ICL point surface in real or error colours, with optional reference model and cameras. */
(() => {
  const D = DemoData.raw;
  document.getElementById("legend").style.background = D.legend.gradient;
  const host = document.getElementById("viewer");
  let V;
  try { V = new DemoViewer(host.querySelector("canvas"), { up: D.up }); } catch (e) { showError(host, e); return; }

  const pos = DemoData.positions(D.points);
  V.addPoints("rgb", pos, DemoData.array(D.rgb), { size: 0.014, worldSize: true, visible: false });
  V.addPoints("error", pos, DemoData.array(D.error), { size: 0.014, worldSize: true });
  V.addPoints("reference", DemoData.positions(D.reference), DemoData.array(D.referenceRgb), { size: 0.012, worldSize: true, visible: false });

  const lines = [], colors = [], cams = [], cc = [];
  D.cameras.forEach((c) => {
    cams.push(...c.position); cc.push(255, 255, 255);
    lines.push(...c.position, ...c.position.map((v, a) => v + c.forward[a] * 0.35));
    colors.push(255, 255, 255, 255, 255, 255);
  });
  V.addPoints("cameras", new Float32Array(cams), new Uint8Array(cc), { size: 9 });
  V.addLines("camera-dirs", new Float32Array(lines), new Uint8Array(colors));
  V.frameBox(D.points.min, D.points.max, { yaw: 2.2, pitch: 0.75, distance: 0.85 });

  const toggle = (attr, fn) => document.querySelectorAll(`[data-${attr}]`).forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(`[data-${attr}]`).forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    fn(b.dataset[attr]);
  }));
  toggle("colour", (v) => { V.setVisible("rgb", v === "rgb"); V.setVisible("error", v === "error"); });
  toggle("ref", (v) => V.setVisible("reference", v === "on"));
})();
