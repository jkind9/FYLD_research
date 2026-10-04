/* Dependency-free WebGL2 viewer for the demo pages: points, lines and Gaussian splats.
 * Camera convention matches OpenCV: x right, y down, z forward. The splat projection follows
 * the standard EWA approach used by 3D Gaussian splatting renderers. */
"use strict";

const DemoData = (() => {
  const raw = JSON.parse(document.getElementById("demo-data").textContent);
  const TYPES = { f32: Float32Array, u8: Uint8Array, i8: Int8Array, u16: Uint16Array, i16: Int16Array, u32: Uint32Array };
  function bytes(b64) {
    const s = atob(b64);
    const out = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
    return out;
  }
  function array(enc) {
    const b = bytes(enc.b64);
    return new TYPES[enc.dtype](b.buffer, b.byteOffset, b.byteLength / TYPES[enc.dtype].BYTES_PER_ELEMENT);
  }
  function positions(enc) {
    const b = bytes(enc.b64);
    const q = new Uint16Array(b.buffer, b.byteOffset, b.byteLength / 2);
    const out = new Float32Array(q.length);
    for (let i = 0; i < q.length; i += 3) {
      for (let a = 0; a < 3; a++) out[i + a] = enc.min[a] + (q[i + a] / 65535) * (enc.max[a] - enc.min[a]);
    }
    return out;
  }
  return { raw, array, positions };
})();

const V3 = {
  sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
  add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
  scale: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
  dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
  cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
  norm: (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; },
};

const SPLAT_VS = `#version 300 es
precision highp float; precision highp int;
uniform highp sampler2D u_pos; uniform highp sampler2D u_cova; uniform highp sampler2D u_covb;
uniform mat4 u_view, u_proj; uniform vec2 u_focal, u_viewport; uniform float u_scale;
in vec2 a_corner; in uint a_index;
out vec4 v_color; out vec2 v_pos;
void main() {
  ivec2 uv = ivec2(int(a_index & 2047u), int(a_index >> 11u));
  vec4 p = texelFetch(u_pos, uv, 0); vec4 ca = texelFetch(u_cova, uv, 0); vec4 cb = texelFetch(u_covb, uv, 0);
  vec4 cam = u_view * vec4(p.xyz, 1.0);
  vec4 pos2d = u_proj * cam;
  float clip = 1.2 * pos2d.w;
  if (cam.z < 0.02 || pos2d.x < -clip || pos2d.x > clip || pos2d.y < -clip || pos2d.y > clip) {
    gl_Position = vec4(0.0, 0.0, 2.0, 1.0); return;
  }
  float s2 = u_scale * u_scale;
  mat3 Vrk = s2 * mat3(ca.x, ca.y, ca.z, ca.y, ca.w, cb.x, ca.z, cb.x, cb.y);
  mat3 J = mat3(u_focal.x / cam.z, 0., -(u_focal.x * cam.x) / (cam.z * cam.z),
                0., -u_focal.y / cam.z, (u_focal.y * cam.y) / (cam.z * cam.z), 0., 0., 0.);
  mat3 T = transpose(mat3(u_view)) * J;
  mat3 cov2d = transpose(T) * Vrk * T;
  cov2d[0][0] += 0.3; cov2d[1][1] += 0.3;
  float mid = 0.5 * (cov2d[0][0] + cov2d[1][1]);
  float radius = length(vec2(0.5 * (cov2d[0][0] - cov2d[1][1]), cov2d[0][1]));
  float l1 = mid + radius, l2 = mid - radius;
  if (l2 < 0.0) { gl_Position = vec4(0.0, 0.0, 2.0, 1.0); return; }
  vec2 dir = normalize(vec2(cov2d[0][1], l1 - cov2d[0][0]));
  vec2 major = min(sqrt(2.0 * l1), 1024.0) * dir;
  vec2 minor = min(sqrt(2.0 * l2), 1024.0) * vec2(dir.y, -dir.x);
  float packed = cb.z;
  float r = mod(packed, 256.0), g = mod(floor(packed / 256.0), 256.0), b = floor(packed / 65536.0);
  v_color = vec4(r / 255.0, g / 255.0, b / 255.0, p.w);
  v_pos = a_corner;
  vec2 center = pos2d.xy / pos2d.w;
  gl_Position = vec4(center + a_corner.x * major / u_viewport + a_corner.y * minor / u_viewport, 0.0, 1.0);
}`;
const SPLAT_FS = `#version 300 es
precision highp float;
in vec4 v_color; in vec2 v_pos; out vec4 fragColor;
void main() {
  float A = -dot(v_pos, v_pos);
  if (A < -4.0) discard;
  float B = exp(A) * v_color.a;
  fragColor = vec4(B * v_color.rgb, B);
}`;
const POINT_VS = `#version 300 es
precision highp float;
uniform mat4 u_view, u_proj; uniform float u_size, u_focal; uniform int u_world;
in vec3 a_pos; in vec3 a_color; out vec3 v_color;
void main() {
  vec4 cam = u_view * vec4(a_pos, 1.0);
  gl_Position = u_proj * cam;
  gl_PointSize = u_world == 1 ? clamp(u_size * u_focal / max(cam.z, 0.01), 1.0, 64.0) : u_size;
  v_color = a_color;
}`;
const POINT_FS = `#version 300 es
precision highp float;
in vec3 v_color; out vec4 fragColor;
void main() {
  vec2 c = gl_PointCoord - 0.5;
  if (dot(c, c) > 0.25) discard;
  fragColor = vec4(v_color, 1.0);
}`;
const LINE_VS = `#version 300 es
precision highp float;
uniform mat4 u_view, u_proj; in vec3 a_pos; in vec3 a_color; out vec3 v_color;
void main() { gl_Position = u_proj * (u_view * vec4(a_pos, 1.0)); v_color = a_color; }`;
const LINE_FS = `#version 300 es
precision highp float; in vec3 v_color; out vec4 fragColor;
void main() { fragColor = vec4(v_color, 1.0); }`;

function compile(gl, vs, fs) {
  const prog = gl.createProgram();
  for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
    const sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh));
    gl.attachShader(prog, sh);
  }
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
  const loc = (n) => gl.getUniformLocation(prog, n);
  return { prog, loc };
}

function floatTexture(gl, data, width, height) {
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, width, height, 0, gl.RGBA, gl.FLOAT, data);
  for (const p of [gl.TEXTURE_MIN_FILTER, gl.TEXTURE_MAG_FILTER]) gl.texParameteri(gl.TEXTURE_2D, p, gl.NEAREST);
  for (const p of [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T]) gl.texParameteri(gl.TEXTURE_2D, p, gl.CLAMP_TO_EDGE);
  return tex;
}

class DemoViewer {
  constructor(canvas, opts = {}) {
    this.canvas = canvas;
    const gl = canvas.getContext("webgl2", { antialias: true, premultipliedAlpha: true, alpha: true });
    if (!gl) throw new Error("This page needs WebGL2, which this browser does not provide.");
    this.gl = gl;
    this.up = V3.norm(opts.up || [0, 0, 1]);
    const ref = Math.abs(this.up[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
    this.e1 = V3.norm(V3.cross(this.up, V3.cross(ref, this.up)));
    this.e2 = V3.cross(this.up, this.e1);
    this.fovY = (opts.fovDeg || 50) * Math.PI / 180;
    this.fixedFocal = null;
    this.target = [0, 0, 0]; this.dist = 3; this.yaw = 0.6; this.pitch = 0.5;
    this.eye = null; this.forward = null;
    this.layers = new Map();
    this.listeners = [];
    this.splatScale = 1.0;
    this.progs = {
      splat: compile(gl, SPLAT_VS, SPLAT_FS), point: compile(gl, POINT_VS, POINT_FS), line: compile(gl, LINE_VS, LINE_FS),
    };
    this.quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-2, -2, 2, -2, 2, 2, -2, 2]), gl.STATIC_DRAW);
    this._controls();
    new ResizeObserver(() => this.redraw()).observe(canvas);
    this.redraw();
  }

  _buffer(data) {
    const gl = this.gl, b = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
    return b;
  }

  addPoints(name, positions, colors, opts = {}) {
    const gl = this.gl, vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    this._attrib(this.progs.point.prog, "a_pos", this._buffer(positions), 3, gl.FLOAT, false);
    this._attrib(this.progs.point.prog, "a_color", this._buffer(colors), 3, gl.UNSIGNED_BYTE, true);
    gl.bindVertexArray(null);
    this.layers.set(name, { kind: "point", vao, count: positions.length / 3, visible: opts.visible !== false,
      size: opts.size || 2, world: opts.worldSize ? 1 : 0, order: opts.order || 1 });
    this.redraw();
  }

  addLines(name, positions, colors, opts = {}) {
    const gl = this.gl, vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    this._attrib(this.progs.line.prog, "a_pos", this._buffer(positions), 3, gl.FLOAT, false);
    this._attrib(this.progs.line.prog, "a_color", this._buffer(colors), 3, gl.UNSIGNED_BYTE, true);
    gl.bindVertexArray(null);
    this.layers.set(name, { kind: "line", vao, count: positions.length / 3, visible: opts.visible !== false, order: opts.order || 2 });
    this.redraw();
  }

  /* Flat Gaussians: covariance = st^2 (I - n n^T) + sn^2 n n^T, built here from normals and sigmas. */
  addSplats(name, positions, normals, colors, alphas, tangentSigma, normalSigma, opts = {}) {
    const gl = this.gl, n = positions.length / 3, W = 2048, H = Math.ceil(n / W);
    const pos = new Float32Array(W * H * 4), ca = new Float32Array(W * H * 4), cb = new Float32Array(W * H * 4);
    for (let i = 0; i < n; i++) {
      let nx = normals[3 * i], ny = normals[3 * i + 1], nz = normals[3 * i + 2];
      const l = Math.hypot(nx, ny, nz) || 1; nx /= l; ny /= l; nz /= l;
      const st = tangentSigma[i] * tangentSigma[i], sn = normalSigma[i] * normalSigma[i], d = sn - st;
      pos.set([positions[3 * i], positions[3 * i + 1], positions[3 * i + 2], alphas[i] / 255], 4 * i);
      ca.set([st + d * nx * nx, d * nx * ny, d * nx * nz, st + d * ny * ny], 4 * i);
      cb.set([d * ny * nz, st + d * nz * nz, colors[3 * i] + 256 * colors[3 * i + 1] + 65536 * colors[3 * i + 2], 0], 4 * i);
    }
    const layer = { kind: "splat", count: n, visible: opts.visible !== false, order: 0, positions,
      tex: [floatTexture(gl, pos, W, H), floatTexture(gl, ca, W, H), floatTexture(gl, cb, W, H)],
      index: new Uint32Array(n), depth: new Float32Array(n), counts: new Uint32Array(65536 + 1) };
    layer.vao = gl.createVertexArray();
    gl.bindVertexArray(layer.vao);
    this._attrib(this.progs.splat.prog, "a_corner", this.quad, 2, gl.FLOAT, false);
    layer.indexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, layer.indexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, layer.index, gl.DYNAMIC_DRAW);
    const loc = gl.getAttribLocation(this.progs.splat.prog, "a_index");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribIPointer(loc, 1, gl.UNSIGNED_INT, 0, 0);
    gl.vertexAttribDivisor(loc, 1);
    gl.bindVertexArray(null);
    this.layers.set(name, layer);
    this.redraw();
  }

  _attrib(prog, name, buffer, size, type, normalized) {
    const gl = this.gl, loc = gl.getAttribLocation(prog, name);
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, size, type, normalized, 0, 0);
  }

  setVisible(name, visible) { const l = this.layers.get(name); if (l) { l.visible = visible; this.redraw(); } }
  setPointSize(name, size) { const l = this.layers.get(name); if (l) { l.size = size; this.redraw(); } }
  remove(name) { this.layers.delete(name); this.redraw(); }
  onRender(fn) { this.listeners.push(fn); }

  frameBox(min, max, opts = {}) {
    this.target = V3.scale(V3.add(min, max), 0.5);
    this.dist = Math.max(0.02, Math.hypot(max[0] - min[0], max[1] - min[1], max[2] - min[2]) * (opts.distance || 0.9));
    if (opts.yaw !== undefined) this.yaw = opts.yaw;
    if (opts.pitch !== undefined) this.pitch = opts.pitch;
    this.eye = null; this.fixedFocal = null;
    this.redraw();
  }

  setOrbit(target, dist, yaw, pitch) {
    this.target = target; this.dist = dist; this.yaw = yaw; this.pitch = pitch;
    this.eye = null; this.fixedFocal = null; this.redraw();
  }

  /* Look exactly from a recorded camera: camera-to-world 4x4 (row-major nested), focal fy in source pixels. */
  lookFromPose(T, fyPixels, sourceHeight) {
    this.eye = [T[0][3], T[1][3], T[2][3]];
    this.forward = [T[0][2], T[1][2], T[2][2]];
    this.down = [T[0][1], T[1][1], T[2][1]];
    this.fixedFocal = fyPixels / sourceHeight;
    this.target = V3.add(this.eye, V3.scale(this.forward, 1.5));
    this.dist = 1.5;
    const back = V3.scale(this.forward, -1);
    this.pitch = Math.asin(Math.max(-0.99, Math.min(0.99, V3.dot(back, this.up))));
    this.yaw = Math.atan2(V3.dot(back, this.e2), V3.dot(back, this.e1));
    this.redraw();
  }

  /* Orbit view placed behind a recorded camera: looking where it looked, from a little further back. */
  viewBehindPose(T, ahead, back) {
    this.lookFromPose(T, 525, 480);
    this.target = V3.add(this.eye, V3.scale(V3.norm(this.forward), ahead));
    this.dist = ahead + back;
    this.eye = null; this.fixedFocal = null;
    this.redraw();
  }

  _camera() {
    if (this.eye) {
      const f = V3.norm(this.forward), y = V3.norm(this.down), x = V3.cross(y, f);
      return { eye: this.eye, x, y, f };
    }
    const cp = Math.cos(this.pitch);
    const dir = V3.add(V3.add(V3.scale(this.e1, cp * Math.cos(this.yaw)), V3.scale(this.e2, cp * Math.sin(this.yaw))), V3.scale(this.up, Math.sin(this.pitch)));
    const eye = V3.add(this.target, V3.scale(dir, this.dist));
    const f = V3.scale(dir, -1), x = V3.norm(V3.cross(f, this.up)), y = V3.cross(f, x);
    return { eye, x, y, f };
  }

  _matrices(w, h) {
    const c = this._camera();
    const R = [c.x, c.y, c.f], t = R.map((r) => -V3.dot(r, c.eye));
    const view = new Float32Array(16);
    for (let r = 0; r < 3; r++) { view[r] = R[r][0]; view[4 + r] = R[r][1]; view[8 + r] = R[r][2]; view[12 + r] = t[r]; }
    view[15] = 1;
    const fy = this.fixedFocal ? this.fixedFocal * h : 0.5 * h / Math.tan(this.fovY / 2), fx = fy;
    const zn = 0.01, zf = 200;
    const proj = new Float32Array([2 * fx / w, 0, 0, 0, 0, -2 * fy / h, 0, 0, 0, 0, zf / (zf - zn), 1, 0, 0, -(zf * zn) / (zf - zn), 0]);
    return { view, proj, fx, fy, cam: c };
  }

  project(p) {
    const m = this._last;
    if (!m) return null;
    const c = m.cam, d = V3.sub(p, c.eye), z = V3.dot(d, c.f);
    if (z < 0.01) return null;
    const dpr = this._dpr;
    return { x: (m.fx * V3.dot(d, c.x) / z + m.w / 2) / dpr, y: (m.fy * V3.dot(d, c.y) / z + m.h / 2) / dpr, z };
  }

  _sortSplats(layer, cam) {
    const n = layer.count, p = layer.positions, depth = layer.depth, f = cam.f, e = cam.eye;
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < n; i++) {
      const z = (p[3 * i] - e[0]) * f[0] + (p[3 * i + 1] - e[1]) * f[1] + (p[3 * i + 2] - e[2]) * f[2];
      depth[i] = z; if (z < lo) lo = z; if (z > hi) hi = z;
    }
    const counts = layer.counts; counts.fill(0);
    const k = 65535 / Math.max(hi - lo, 1e-6), keys = new Uint16Array(n);
    for (let i = 0; i < n; i++) { const key = ((depth[i] - lo) * k) | 0; keys[i] = key; counts[key + 1]++; }
    for (let i = 1; i <= 65536; i++) counts[i] += counts[i - 1];
    for (let i = 0; i < n; i++) layer.index[counts[keys[i]]++] = i;
    const gl = this.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER, layer.indexBuffer);
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, layer.index);
  }

  redraw() {
    if (this._pending) return;
    this._pending = true;
    requestAnimationFrame(() => { this._pending = false; this._draw(); });
  }

  _draw() {
    const gl = this.gl, canvas = this.canvas;
    this._dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(1, Math.round(canvas.clientWidth * this._dpr)), h = Math.max(1, Math.round(canvas.clientHeight * this._dpr));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    gl.viewport(0, 0, w, h);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    const m = this._matrices(w, h);
    this._last = { ...m, w, h };
    const layers = [...this.layers.values()].filter((l) => l.visible).sort((a, b) => a.order - b.order);
    for (const l of layers) {
      if (l.kind === "splat") this._drawSplats(l, m, w, h);
      else this._drawSimple(l, m);
    }
    for (const fn of this.listeners) fn(this);
  }

  _drawSplats(l, m, w, h) {
    const gl = this.gl, P = this.progs.splat;
    this._sortSplats(l, m.cam);
    gl.useProgram(P.prog);
    gl.disable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    gl.blendFuncSeparate(gl.ONE_MINUS_DST_ALPHA, gl.ONE, gl.ONE_MINUS_DST_ALPHA, gl.ONE);
    gl.uniformMatrix4fv(P.loc("u_view"), false, m.view);
    gl.uniformMatrix4fv(P.loc("u_proj"), false, m.proj);
    gl.uniform2f(P.loc("u_focal"), m.fx, m.fy);
    gl.uniform2f(P.loc("u_viewport"), w, h);
    gl.uniform1f(P.loc("u_scale"), this.splatScale);
    ["u_pos", "u_cova", "u_covb"].forEach((name, i) => {
      gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, l.tex[i]); gl.uniform1i(P.loc(name), i);
    });
    gl.bindVertexArray(l.vao);
    gl.drawArraysInstanced(gl.TRIANGLE_FAN, 0, 4, l.count);
    gl.bindVertexArray(null);
    gl.disable(gl.BLEND);
  }

  _drawSimple(l, m) {
    const gl = this.gl, P = l.kind === "point" ? this.progs.point : this.progs.line;
    gl.useProgram(P.prog);
    gl.enable(gl.DEPTH_TEST);
    gl.uniformMatrix4fv(P.loc("u_view"), false, m.view);
    gl.uniformMatrix4fv(P.loc("u_proj"), false, m.proj);
    if (l.kind === "point") {
      gl.uniform1f(P.loc("u_size"), l.size * (l.world ? 1 : this._dpr));
      gl.uniform1f(P.loc("u_focal"), m.fy);
      gl.uniform1i(P.loc("u_world"), l.world);
    }
    gl.bindVertexArray(l.vao);
    gl.drawArrays(l.kind === "point" ? gl.POINTS : gl.LINES, 0, l.count);
    gl.bindVertexArray(null);
  }

  _controls() {
    const c = this.canvas, pointers = new Map();
    let last = null, pinch = null;
    c.addEventListener("contextmenu", (e) => e.preventDefault());
    c.addEventListener("pointerdown", (e) => {
      c.setPointerCapture(e.pointerId);
      pointers.set(e.pointerId, [e.clientX, e.clientY]);
      last = { x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey };
      if (pointers.size === 2) { const [a, b] = [...pointers.values()]; pinch = Math.hypot(a[0] - b[0], a[1] - b[1]); }
    });
    c.addEventListener("pointermove", (e) => {
      if (!pointers.has(e.pointerId) || !last) return;
      pointers.set(e.pointerId, [e.clientX, e.clientY]);
      if (pointers.size === 2) {
        const [a, b] = [...pointers.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
        if (pinch) this._zoom(pinch / d);
        pinch = d; return;
      }
      const dx = e.clientX - last.x, dy = e.clientY - last.y;
      last.x = e.clientX; last.y = e.clientY;
      this._leavePose();
      if (last.pan) {
        const cam = this._camera(), k = this.dist * 0.0015;
        this.target = V3.add(this.target, V3.add(V3.scale(cam.x, -dx * k), V3.scale(cam.y, -dy * k)));
      } else {
        this.yaw -= dx * 0.006;
        this.pitch = Math.max(-1.55, Math.min(1.55, this.pitch + dy * 0.006));
      }
      this.redraw();
    });
    const end = (e) => { pointers.delete(e.pointerId); if (pointers.size < 2) pinch = null; if (!pointers.size) last = null; };
    c.addEventListener("pointerup", end);
    c.addEventListener("pointercancel", end);
    c.addEventListener("wheel", (e) => { e.preventDefault(); this._leavePose(); this._zoom(Math.exp(e.deltaY * 0.0012)); }, { passive: false });
  }

  _leavePose() { if (this.eye) { this.eye = null; this.fixedFocal = null; } }
  _zoom(f) { this.dist = Math.max(0.01, Math.min(100, this.dist * f)); this.redraw(); }
}

/* Small helpers shared by page scripts. */
function frustumLines(T, fx, fy, w, h, depth, out, colors, rgb) {
  const corners = [[0, 0], [w, 0], [w, h], [0, h]].map(([u, v]) => {
    const c = [(u - w / 2) / fx * depth, (v - h / 2) / fy * depth, depth];
    return [0, 1, 2].map((r) => T[r][0] * c[0] + T[r][1] * c[1] + T[r][2] * c[2] + T[r][3]);
  });
  const o = [T[0][3], T[1][3], T[2][3]];
  const segs = [[o, corners[0]], [o, corners[1]], [o, corners[2]], [o, corners[3]],
    [corners[0], corners[1]], [corners[1], corners[2]], [corners[2], corners[3]], [corners[3], corners[0]]];
  for (const [a, b] of segs) { out.push(...a, ...b); colors.push(...rgb, ...rgb); }
}

function hexColor(i) {
  const palette = [[0xe6, 0x4b, 0x35], [0x4d, 0xbb, 0xd5], [0x00, 0xa0, 0x87], [0x3c, 0x54, 0x88], [0xf3, 0x9b, 0x7f],
    [0x84, 0x91, 0xb4], [0x91, 0xd1, 0xc2], [0xdc, 0x00, 0x00], [0x7e, 0x61, 0x48], [0xb0, 0x9c, 0x85],
    [0xff, 0xb4, 0x00], [0x8e, 0x44, 0xad], [0x2e, 0xcc, 0x71], [0xe8, 0x43, 0x93], [0x16, 0xa0, 0x85],
    [0xd3, 0x54, 0x00], [0x27, 0xae, 0x60], [0x5d, 0x6d, 0x7e]];
  return palette[i % palette.length];
}

function showError(el, err) {
  el.innerHTML = "";
  const p = document.createElement("p");
  p.className = "viewer-error";
  p.textContent = String(err && err.message ? err.message : err);
  el.appendChild(p);
}
