/* Page 04: desk scene as sparse points, merged points and Gaussian splats, with photo comparison. */
(() => {
  const D = DemoData.raw, S = D.splat;
  const host = document.getElementById("viewer");
  let V;
  try { V = new DemoViewer(host.querySelector("canvas"), { up: D.up }); } catch (e) { showError(host, e); return; }

  const pos = DemoData.positions(S.positions);
  const n = pos.length / 3;
  const normalsQ = DemoData.array(S.normals), normals = new Float32Array(normalsQ.length);
  for (let i = 0; i < normalsQ.length; i++) normals[i] = normalsQ[i] / 127;
  const colours = DemoData.array(S.colours), alpha = DemoData.array(S.alpha);
  const st = new Float32Array(n).fill(S.tangentSigma), sn = new Float32Array(n).fill(S.normalSigma);

  V.addSplats("splats", pos, normals, colours, alpha, st, sn);
  V.addPoints("points", pos, colours, { size: D.voxel * 0.8, worldSize: true, visible: false });
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

  const setMode = (mode) => {
    document.querySelectorAll("[data-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === mode)));
    ["splats", "points", "display"].forEach((name) => V.setVisible(name, name === mode));
  };
  document.querySelectorAll("[data-mode]").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
  document.getElementById("splat-scale").addEventListener("input", (e) => { V.splatScale = Number(e.target.value); V.redraw(); });

  const photo = document.getElementById("compare-photo"), caption = document.getElementById("compare-caption");
  const buttons = document.getElementById("compare-buttons");
  const choose = (c, btn) => {
    V.lookFromPose(c.pose, c.fy || D.fy, c.height || D.height);
    photo.src = c.photo;
    caption.textContent = `Real photo from ${D.sceneName || "desk"}, frame ${c.frame}. Drag to explore.`;
    buttons.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
  };
  D.compare.forEach((c, i) => {
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
