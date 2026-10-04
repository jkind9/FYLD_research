/* Page 01: one frame from colour and depth to 3D points. */
(() => {
  const D = DemoData.raw;
  document.getElementById("img-rgb").src = D.images.rgb;
  document.getElementById("img-depth").src = D.images.depth;
  document.getElementById("img-missing").src = D.images.missing;
  document.getElementById("legend").style.background = D.legend.gradient;

  const host = document.getElementById("viewer");
  let V;
  try { V = new DemoViewer(host.querySelector("canvas"), { up: D.up }); } catch (e) { showError(host, e); return; }

  const pos = DemoData.positions(D.points);
  V.addPoints("rgb", pos, DemoData.array(D.rgb), { size: 0.006, worldSize: true });
  V.addPoints("depth", pos, DemoData.array(D.depthColours), { size: 0.006, worldSize: true, visible: false });

  const k = D.intrinsics, lines = [], colors = [];
  frustumLines(D.pose, k.fx, k.fy, k.width, k.height, 0.35, lines, colors, [255, 255, 255]);
  V.addLines("camera", new Float32Array(lines), new Uint8Array(colors));

  const lo = D.points.min, hi = D.points.max;
  const orbit = () => V.frameBox(lo, hi, { yaw: -2.3, pitch: 0.55, distance: 0.75 });
  const fromCamera = () => V.lookFromPose(D.pose, k.fy, k.height);
  fromCamera();

  document.getElementById("from-camera").addEventListener("click", fromCamera);
  document.getElementById("orbit").addEventListener("click", orbit);
  document.querySelectorAll("[data-colour]").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("[data-colour]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    V.setVisible("rgb", b.dataset.colour === "rgb");
    V.setVisible("depth", b.dataset.colour === "depth");
  }));
})();
