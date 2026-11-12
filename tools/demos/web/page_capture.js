/* Capture viewer: one frame cursor shared by the final surface and the frame-by-frame build-up.
 * The frame's photo sits beside the 3D view; a player, a points-per-step track and a filmstrip sit below. */
(() => {
  const D = DemoData.raw, T = D.timeline, V = window.sceneViewer;
  if (!V) return;
  const $ = (id) => document.getElementById(id);
  const app = $("app"), slider = $("tl-slider"), strip = $("tl-strip"), track = slider.parentElement;
  const playButton = $("tl-play"), follow = $("tl-follow"), measure = $("measure");
  // The room build's steps when the page has them, else the recorded camera bookmarks.
  const frames = T
    ? T.seq.map((seq, k) => ({ seq, pose: T.poses[k], fx: T.fx[k], fy: T.fy[k], width: T.width[k], height: T.height[k],
      photo: T.photos[k], label: T.labels[k] }))
    : D.compare.map((c) => ({ seq: c.frame, pose: c.pose, fx: c.fy, fy: c.fy, width: c.width, height: c.height,
      photo: c.photo, label: c.label }));
  const n = frames.length, SPEEDS = [0.5, 1, 2, 4], STEP_MS = 150;
  const shown = { frame: true, measured: true, camera: true };
  let k = 0, view = "final", timer = null, speed = 1;

  const solid = (count, rgb) => {
    const out = new Uint8Array(count * 3);
    for (let i = 0; i < out.length; i += 3) out.set(rgb, i);
    return out;
  };
  const po = T && T.pointOffsets, ao = T && T.arcoreOffsets;
  const points = T && DemoData.positions(T.points), arcore = T && DemoData.positions(T.arcore);
  if (T) {
    V.addPoints("tl-built", points, DemoData.array(T.colours), { size: 0.012, worldSize: true, visible: false });
    const path = [];
    for (let i = 1; i < n; i++) {
      for (const j of [i - 1, i]) path.push(T.poses[j][0][3], T.poses[j][1][3], T.poses[j][2][3]);
    }
    V.addLines("tl-path", new Float32Array(path), solid(path.length / 3, [230, 40, 40]));
  }
  // A step's own learned depth (orange) and the measured depth that sized it (cyan), made when first shown.
  const made = new Set();
  const frameLayers = (i) => {
    if (!made.has(i)) {
      const p = points.subarray(po[i] * 3, po[i + 1] * 3), a = arcore.subarray(ao[i] * 3, ao[i + 1] * 3);
      V.addPoints(`tl-frame-${i}`, p, solid(p.length / 3, [255, 140, 0]), { size: 0.02, worldSize: true, visible: false });
      V.addPoints(`tl-arcore-${i}`, a, solid(a.length / 3, [0, 220, 255]), { size: 0.02, worldSize: true, visible: false });
      made.add(i);
    }
    return [`tl-frame-${i}`, `tl-arcore-${i}`];
  };

  // Track: one bar per step, its height the points that step added (equal bars for camera bookmarks).
  const added = frames.map((_, i) => (T ? po[i + 1] - po[i] : 1));
  const most = Math.max(1, ...added);
  const bars = added.map((count) => {
    const bar = document.createElement("i");
    bar.style.height = `${Math.max(8, (100 * count) / most)}%`;
    $("tl-bars").appendChild(bar);
    return bar;
  });
  const thumbs = frames.map((f, i) => {
    const b = document.createElement("button"), img = document.createElement("img");
    b.className = "thumb";
    b.title = `Step ${i + 1} · frame ${f.seq} · ${f.label}`;
    img.src = f.photo; img.alt = ""; img.decoding = "async";
    b.appendChild(img);
    b.addEventListener("click", () => { stop(); show(i); });
    strip.appendChild(b);
    return b;
  });

  const show = (next) => {
    const build = view === "build", before = k;
    if (T) frameLayers(before).forEach((name) => V.setVisible(name, false));
    thumbs[before].classList.remove("on");
    k = next;
    const f = frames[k];
    if (T) {
      V.layers.get("tl-built").count = po[k + 1];
      const path = V.layers.get("tl-path");
      path.count = build ? 2 * k : 2 * (n - 1);
      path.visible = shown.camera;
      const [own, measured] = frameLayers(k);
      V.setVisible(own, build && shown.frame);
      V.setVisible(measured, build && shown.measured);
    }
    const lines = [], colours = [];
    frustumLines(f.pose, f.fx, f.fy, f.width, f.height, 0.3, lines, colours, [230, 40, 40]);
    V.addLines("tl-camera", new Float32Array(lines), new Uint8Array(colours), { visible: shown.camera });
    for (let i = Math.min(before, k); i <= Math.max(before, k); i++) bars[i].className = i < k ? "past" : i === k ? "now" : "";
    track.style.setProperty("--at", (k + 0.5) / n);
    slider.value = String(k);
    $("frame-photo").src = f.photo;
    $("photo-caption").textContent = `Frame ${f.seq} · ${f.label}`;
    $("tl-caption").textContent = `${k + 1} / ${n} · ${f.label}` +
      (T ? ` · +${added[k].toLocaleString()} points, ${(ao[k + 1] - ao[k]).toLocaleString()} measured` : "");
    thumbs[k].classList.add("on");
    strip.scrollTo({ left: thumbs[k].offsetLeft - (strip.clientWidth - thumbs[k].offsetWidth) / 2,
      behavior: timer ? "auto" : "smooth" });
    if (follow.checked) V.lookFromPose(f.pose, f.fy, f.height);
    V.redraw();
  };

  const setView = (next) => {
    view = next;
    app.dataset.view = next;
    document.querySelectorAll("button[data-view]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.view === next)));
    if (next === "final") {
      document.querySelector("button[data-mode][aria-pressed='true']")?.click();  // page_splats.js shows the chosen look
    } else {
      ["splats", "points"].forEach((name) => V.setVisible(name, false));
      if (measure.getAttribute("aria-pressed") === "true") measure.click();
    }
    if (T) V.setVisible("tl-built", next === "build");
    show(k);
  };
  document.querySelectorAll("button[data-view]").forEach((b) => b.addEventListener("click", () => setView(b.dataset.view)));

  const stop = () => {
    clearInterval(timer);
    timer = null;
    playButton.setAttribute("aria-pressed", "false");
    playButton.setAttribute("aria-label", "Play");
  };
  const start = () => {
    clearInterval(timer);
    timer = setInterval(() => (k === n - 1 ? stop() : show(k + 1)), STEP_MS / SPEEDS[speed]);
    playButton.setAttribute("aria-pressed", "true");
    playButton.setAttribute("aria-label", "Pause");
  };
  const playPause = () => {
    if (timer) return stop();
    if (k === n - 1) show(0);
    start();
  };
  const step = (by) => { stop(); show(Math.max(0, Math.min(n - 1, k + by))); };

  playButton.addEventListener("click", playPause);
  $("tl-first").addEventListener("click", () => step(-n));
  $("tl-prev").addEventListener("click", () => step(-1));
  $("tl-next").addEventListener("click", () => step(1));
  $("tl-speed").addEventListener("click", (e) => {
    speed = (speed + 1) % SPEEDS.length;
    e.currentTarget.textContent = `${SPEEDS[speed]}×`;
    if (timer) start();
  });
  slider.addEventListener("input", () => { stop(); show(Number(slider.value)); });
  follow.addEventListener("change", () => show(k));
  document.querySelectorAll("button[data-layer]").forEach((b) => b.addEventListener("click", () => {
    shown[b.dataset.layer] = !shown[b.dataset.layer];
    b.setAttribute("aria-pressed", String(shown[b.dataset.layer]));
    show(k);
  }));

  $("toggle-photo").addEventListener("click", (e) => {
    e.currentTarget.setAttribute("aria-pressed", String(!app.classList.toggle("no-photo")));
  });
  $("toggle-tools").addEventListener("click", (e) => {
    const tools = $("tools");
    tools.hidden = !tools.hidden;
    e.currentTarget.setAttribute("aria-pressed", String(!tools.hidden));
  });
  document.querySelectorAll("[data-open]").forEach((b) => b.addEventListener("click", () => $(b.dataset.open).showModal()));
  document.querySelectorAll("dialog").forEach((d) => d.addEventListener("click", (e) => { if (e.target === d) d.close(); }));

  // A click leaves focus where it was, so the arrow keys keep stepping frames; Tab still reaches the canvas to orbit.
  V.canvas.addEventListener("mousedown", (e) => e.preventDefault());
  const keys = {
    " ": playPause, k: playPause,
    ArrowLeft: (e) => step(e.shiftKey ? -10 : -1), ArrowRight: (e) => step(e.shiftKey ? 10 : 1),
    Home: () => step(-n), End: () => step(n),
    c: () => follow.click(), p: () => $("toggle-photo").click(), f: () => $("fit-scene").click(),
    m: () => view === "final" && measure.click(), "?": () => $("help").showModal(),
    b: () => T && setView(view === "build" ? "final" : "build"),
  };
  document.addEventListener("keydown", (e) => {
    const t = e.target, fn = keys[e.key.length === 1 ? e.key.toLowerCase() : e.key];
    if (!fn || e.ctrlKey || e.metaKey || e.altKey || t.closest?.("dialog")) return;
    if (t.matches?.("input") && t !== slider) return;
    if ((t === slider || t === V.canvas) && /^(Arrow|Home|End)/.test(e.key)) return;  // they move the slider or orbit
    e.preventDefault();
    fn(e);
  });

  setView("final");
})();
