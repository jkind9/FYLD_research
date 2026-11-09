/* Capture viewer, frame by frame: each room-build frame's camera, upright photo and the points it added. */
(() => {
  const T = DemoData.raw.timeline, V = window.sceneViewer;
  if (!T || !V) return;
  const n = T.seq.length, po = T.pointOffsets, ao = T.arcoreOffsets;
  const points = DemoData.positions(T.points), arcore = DemoData.positions(T.arcore);
  const solid = (count, rgb) => {
    const out = new Uint8Array(count * 3);
    for (let i = 0; i < out.length; i += 3) out.set(rgb, i);
    return out;
  };
  V.addPoints("tl-built", points, DemoData.array(T.colours), { size: 0.012, worldSize: true, visible: false });
  const path = [];
  for (let i = 1; i < n; i++) {
    for (const k of [i - 1, i]) path.push(T.poses[k][0][3], T.poses[k][1][3], T.poses[k][2][3]);
  }
  V.addLines("tl-path", new Float32Array(path), solid(path.length / 3, [230, 40, 40]), { visible: false });

  const made = new Set();
  const frameLayers = (k) => {
    if (!made.has(k)) {
      const p = points.subarray(po[k] * 3, po[k + 1] * 3), a = arcore.subarray(ao[k] * 3, ao[k + 1] * 3);
      V.addPoints(`tl-frame-${k}`, p, solid(p.length / 3, [255, 140, 0]), { size: 0.02, worldSize: true, visible: false });
      V.addPoints(`tl-arcore-${k}`, a, solid(a.length / 3, [0, 220, 255]), { size: 0.02, worldSize: true, visible: false });
      made.add(k);
    }
    return [`tl-frame-${k}`, `tl-arcore-${k}`];
  };

  const slider = document.getElementById("tl-slider"), play = document.getElementById("tl-play");
  const follow = document.getElementById("tl-follow"), caption = document.getElementById("tl-caption");
  const photo = document.getElementById("tl-photo"), modeButton = document.querySelector('[data-mode="timeline"]');
  let current = 0, active = false, timer = null;

  const show = (k) => {
    frameLayers(current).forEach((name) => V.setVisible(name, false));
    current = k;
    V.layers.get("tl-built").count = po[k + 1];
    V.layers.get("tl-path").count = 2 * k;
    const lines = [], colours = [];
    frustumLines(T.poses[k], T.fx[k], T.fy[k], T.width[k], T.height[k], 0.3, lines, colours, [230, 40, 40]);
    V.addLines("tl-camera", new Float32Array(lines), new Uint8Array(colours), { visible: active });
    frameLayers(k).forEach((name) => V.setVisible(name, active));
    slider.value = String(k);
    photo.src = T.photos[k];
    caption.textContent = `Step ${k + 1} of ${n} · recorded frame ${T.seq[k]} at ${T.labels[k]} · ` +
      `${po[k + 1] - po[k]} learned points, ${ao[k + 1] - ao[k]} ARCore points`;
    if (active && follow.checked) V.lookFromPose(T.poses[k], T.fy[k], T.height[k]);
    V.redraw();
  };
  const setActive = (on) => {
    active = on;
    ["tl-built", "tl-path", "tl-camera", ...frameLayers(current)].forEach((name) => V.setVisible(name, on));
    if (!on && timer) { clearInterval(timer); timer = null; play.textContent = "Play"; }
  };

  document.querySelectorAll("[data-mode]").forEach((b) => b.addEventListener("click", () => setActive(b.dataset.mode === "timeline")));
  const enter = () => { if (!active) modeButton.click(); };
  slider.addEventListener("input", () => { enter(); show(Number(slider.value)); });
  follow.addEventListener("change", () => show(current));
  play.addEventListener("click", () => {
    enter();
    if (timer) { clearInterval(timer); timer = null; play.textContent = "Play"; return; }
    if (current === n - 1) show(0);
    play.textContent = "Pause";
    timer = setInterval(() => {
      if (current === n - 1) { clearInterval(timer); timer = null; play.textContent = "Play"; return; }
      show(current + 1);
    }, 150);
  });
  show(0);
})();
