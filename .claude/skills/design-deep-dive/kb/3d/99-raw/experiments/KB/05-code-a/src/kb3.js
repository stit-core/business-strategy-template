// kb3.js — клавиатура «Ё» чистым кодом (three r186), дорожка KB, вариант A. Тот же паспорт, что у Blender
// (passport.json, метры, оси Blender: X вправо, Y назад, Z вверх); вся сборка — в группе, повёрнутой в Y-вверх three.
// Колпачок Cherry: кольца скруглённого прямоугольника постоянной топологии (стенка с выпуклостью → скругление кромки →
// вогнутый верх), нормали верха — аналитические (цилиндрическая выемка), UV — проекция на верх → ячейка атласа canvas.
// Все 68 колпачков — одна геометрия и один материал (1 вызов), свитчи — InstancedMesh (1 вызов), корпус — 2 группы.
import {
  BufferGeometry, Float32BufferAttribute, Vector3, Matrix4, Quaternion, Group, Mesh, InstancedMesh, BoxGeometry,
  PlaneGeometry, MeshPhysicalMaterial, MeshStandardMaterial, Color, CanvasTexture, SRGBColorSpace, RepeatWrapping,
  LinearMipmapLinearFilter, NoColorSpace, Object3D,
} from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const MM = 0.001;
const V3 = Vector3;

// ---------------------------------------------------------------- кольцо скруглённого прямоугольника, постоянная топология
export function rrectRing(a, b, r, nc, nx, ny) {
  r = Math.max(0, Math.min(r, a, b));
  const cx = a - r, cy = b - r, pts = [];
  const arc = (ox, oy, a0) => { for (let i = 0; i < nc; i++) { const t = (a0 + 90 * i / nc) * Math.PI / 180; pts.push([ox + r * Math.cos(t), oy + r * Math.sin(t)]); } };
  const side = (x0, y0, x1, y1, n) => { for (let i = 0; i < n; i++) { const t = i / n; pts.push([x0 + (x1 - x0) * t, y0 + (y1 - y0) * t]); } };
  arc(cx, cy, 0); side(cx, b, -cx, b, nx);
  arc(-cx, cy, 90); side(-a, cy, -a, -cy, ny);
  arc(-cx, -cy, 180); side(-cx, -b, cx, -b, nx);
  arc(cx, -cy, 270); side(a, -cy, a, cy, ny);
  return pts;
}

export function keycapDims(P, w, profile) {
  const K = P.keycap, rw = K.rows[profile];
  const wb = w * P.U - K.gap, wt = wb - K.top_shrink_w;
  const mult = K.dish_wide.find(([lim]) => w <= lim + 1e-9)[1];
  return { w, wb, db: K.depth_b, wt, dt: K.depth_t, h: rw.h, tilt: rw.tilt, yoff: rw.yoff, dish: rw.dish * mult };
}

// ---------------------------------------------------------------- колпачок (система колпачка: 0 — низ юбки по центру)
function keycapGeometry(kd, P) {
  const K = P.keycap;
  const nc = 6, nx = Math.max(3, Math.round(kd.w * 3)), ny = 3;
  const th = kd.tilt * Math.PI / 180;
  const T0 = new V3(0, kd.yoff, kd.h), xt = new V3(1, 0, 0), yt = new V3(0, Math.cos(th), Math.sin(th)), zt = new V3(0, -Math.sin(th), Math.cos(th));
  const ab = kd.wb / 2, bb = kd.db / 2, at = kd.wt / 2, bt = kd.dt / 2;
  const rb = K.corner_b, rt = K.corner_t, fr = 0.9 * MM, bulge = K.bulge;
  const dish = (u) => kd.dish * Math.max(0, 1 - (u / at) ** 2);
  const topPt = (u, v, z) => T0.clone().addScaledVector(xt, u).addScaledVector(yt, v).addScaledVector(zt, z - dish(u));
  const bottom = rrectRing(ab, bb, rb, nc, nx, ny).map(([x, y]) => new V3(x, y, 0));
  const fil = [90, 60, 30, 0].map((phi) => {
    const s = Math.sin(phi * Math.PI / 180), c = Math.cos(phi * Math.PI / 180);
    return rrectRing(at - fr + fr * s, bt - fr + fr * s, rt - fr + fr * s, nc, nx, ny).map(([u, v]) => topPt(u, v, -fr + fr * c));
  });
  const N = bottom.length;
  const walls = [0.33, 0.66].map((s) => bottom.map((p, i) => {
    const t = bottom[(i + 1) % N].clone().sub(bottom[(i + N - 1) % N]);
    const n = new V3(t.y, -t.x, 0).normalize();
    return p.clone().lerp(fil[0][i], s).addScaledVector(n, 4 * s * (1 - s) * bulge);
  }));
  const rings = [bottom, ...walls, ...fil];
  const nTop0 = rings.length - 1;                       // с кольца φ = 0 — верх (нормали аналитические)
  const KC = 5;
  for (let k = 1; k <= KC; k++) {
    const i = fr + (bt - fr) * k / (KC + 0.35);
    rings.push(rrectRing(at - i, bt - i, Math.max(rt - i, 0), nc, nx, ny).map(([u, v]) => topPt(u, v, 0)));
  }
  const center = topPt(0, 0, 0);
  const pos = [], uv = [], idx = [], topFlag = [];
  const pushV = (p, isTop) => {
    pos.push(p.x, p.y, p.z);
    const q = p.clone().sub(T0);
    uv.push((q.dot(xt) + at) / (2 * at), (q.dot(yt) + bt) / (2 * bt));
    topFlag.push(isTop ? 1 : 0);
  };
  rings.forEach((ring, ri) => ring.forEach((p) => pushV(p, ri >= nTop0)));
  pushV(center, true);
  const ci = pos.length / 3 - 1;
  for (let r = 0; r < rings.length - 1; r++) {
    for (let i = 0; i < N; i++) {
      const a = r * N + i, b = r * N + (i + 1) % N, c = (r + 1) * N + (i + 1) % N, d = (r + 1) * N + i;
      idx.push(a, b, c, a, c, d);
    }
  }
  const last = (rings.length - 1) * N;
  for (let i = 0; i < N; i++) idx.push(last + i, last + (i + 1) % N, ci);
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  const nrm = g.attributes.normal;
  for (let vi = 0; vi < topFlag.length; vi++) {
    if (!topFlag[vi]) continue;
    const p = new V3(pos[vi * 3], pos[vi * 3 + 1], pos[vi * 3 + 2]).sub(T0);
    const u = p.dot(xt);
    const slope = Math.abs(u) < at ? 2 * kd.dish * u / (at * at) : 0;
    const n = zt.clone().addScaledVector(xt, -slope).normalize();
    nrm.setXYZ(vi, n.x, n.y, n.z);
  }
  g.userData = { T0, at, bt, kd };
  return g;
}

// ---------------------------------------------------------------- атлас надписей (canvas, шрифт страницы — Onest)
function legendAtlas(P, cw, keys, ppm = 8, marginMM = 4.5, W = 2048) {
  const cells = keys.map((k) => { const kd = keycapDims(P, k.w, k.profile); return { k, kd, w: Math.round((kd.wt * 1000 + 2 * marginMM) * ppm), h: Math.round((kd.dt * 1000 + 2 * marginMM) * ppm) }; });
  let x = 0, y = 0, rowH = 0;
  for (const c of [...cells].sort((a, b) => b.w - a.w)) {
    if (x + c.w > W) { x = 0; y += rowH; rowH = 0; }
    c.x = x; c.y = y; x += c.w; rowH = Math.max(rowH, c.h);
  }
  const H = 2 ** Math.ceil(Math.log2(y + rowH));
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const g = cv.getContext('2d');
  g.fillStyle = cw.alpha; g.fillRect(0, 0, W, H);
  const cap = 0.708;                                     // доля прописной «Н» у Onest (make_atlas.py)
  const font = (capmm, wght) => `${wght} ${capmm / cap * ppm}px Onest`;
  const text = (s, xmm, ymm, capmm, wght, align, col, ox, oy) => {
    if (!s) return; g.font = font(capmm, wght); g.fillStyle = col; g.textAlign = align; g.textBaseline = 'alphabetic';
    g.fillText(s, ox + xmm * ppm, oy + ymm * ppm);
  };
  const map = {};
  for (const c of cells) {
    const { k, kd } = c; const role = k.role;
    const bg = role === 'accent' ? cw.accent : cw[role];
    g.fillStyle = bg; g.fillRect(c.x, c.y, c.w, c.h);
    const ox = c.x + marginMM * ppm, oy = c.y + marginMM * ppm;
    const wt = kd.wt * 1000, dt = kd.dt * 1000, ix = 1.7, it = 1.55, ib = 1.65;
    const L1 = cw.legend1, L2 = cw.legend2;
    if (k.id === 'yo') text('Ё', wt / 2, dt / 2 + 3.25, 6.2, 640, 'center', cw.legend_accent, ox, oy);
    else if (k.id === 'space') { /* без надписи */ }
    else if (role === 'mod') {
      if ('←→↑↓'.includes(k.l1)) text(k.l1, wt / 2, dt / 2 + 1.5, 3.0, 500, 'center', L1, ox, oy);
      else text(k.l1, ix, it + 2.1, 2.1, 480, 'left', L1, ox, oy);
    } else if (k.row === 0 || k.id === 'bsl') {
      text(k.l1, ix, dt - ib, 3.1, 520, 'left', L1, ox, oy);
      if (k.l3) { text(k.l2, ix, it + 2.4, 2.4, 480, 'left', L2, ox, oy); text(k.l3, wt - ix, it + 2.4, 2.4, 480, 'right', L1, ox, oy); }
      else text(k.l2, ix, it + 2.4, 2.4, 480, 'left', L1, ox, oy);
    } else if (k.id === 'slash') {
      text(`${k.l1} ${k.l3}`, ix, it + 3.3, 3.3, 520, 'left', L1, ox, oy); text(k.l2, wt - ix, dt - ib, 2.5, 470, 'right', L2, ox, oy);
    } else {
      text(k.l1, ix, it + 3.4, 3.4, 540, 'left', L1, ox, oy); text(k.l2, wt - ix, dt - ib, 2.5, 470, 'right', L2, ox, oy);
    }
    // UV верха 0..1 → ячейка (canvas: y вниз, flipY у текстуры — v вверх)
    map[k.id] = { off: [ox / W, 1 - (oy + dt * ppm) / H], scl: [wt * ppm / W, dt * ppm / H] };
  }
  const tex = new CanvasTexture(cv);
  tex.colorSpace = SRGBColorSpace; tex.anisotropy = 16; tex.minFilter = LinearMipmapLinearFilter;
  return { tex, map, size: [W, H], canvas: cv };
}

// шум для фактуры PBT (карта рельефа, тайлом)
function grainTexture(n = 256, seed = 7) {
  const cv = document.createElement('canvas'); cv.width = cv.height = n;
  const g = cv.getContext('2d'); const im = g.createImageData(n, n);
  let s = seed; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < n * n; i++) { const v = 110 + rnd() * 50 | 0; im.data.set([v, v, v, 255], i * 4); }
  g.putImageData(im, 0, 0);
  const t = new CanvasTexture(cv); t.wrapS = t.wrapT = RepeatWrapping; t.colorSpace = NoColorSpace; t.repeat.set(96, 96);
  return t;
}

// ---------------------------------------------------------------- корпус кольцами (как kbb.case_meshes, мировые координаты Blender)
function loft(rings, { closed = false, bandGroups = null, capFirst = false, capLast = false } = {}) {
  const N = rings[0].length, pos = [], groups = [];
  rings.forEach((r) => r.forEach((p) => pos.push(p.x, p.y, p.z)));
  const idx = [];
  const bands = rings.length - 1 + (closed ? 1 : 0);
  for (let bI = 0; bI < bands; bI++) {
    const r0 = bI, r1 = (bI + 1) % rings.length, start = idx.length;
    for (let i = 0; i < N; i++) {
      const a = r0 * N + i, b = r0 * N + (i + 1) % N, c = r1 * N + (i + 1) % N, d = r1 * N + i;
      idx.push(a, b, c, a, c, d);
    }
    groups.push([start, idx.length - start, bandGroups ? bandGroups[bI] : 0]);
  }
  const fan = (ri, flip) => {
    const c = new V3(); rings[ri].forEach((p) => c.add(p)); c.multiplyScalar(1 / N);
    const ci = pos.length / 3; pos.push(c.x, c.y, c.z); const start = idx.length;
    for (let i = 0; i < N; i++) { const a = ri * N + i, b = ri * N + (i + 1) % N; flip ? idx.push(b, a, ci) : idx.push(a, b, ci); }
    groups.push([start, idx.length - start, 0]);
  };
  if (capFirst) fan(0, true);
  if (capLast) fan(rings.length - 1, false);
  const g = new BufferGeometry();
  g.setAttribute('position', new Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  // группы одного материала подряд → слить
  const merged = [];
  for (const [s, c, m] of groups) { const l = merged[merged.length - 1]; if (l && l[2] === m && l[0] + l[1] === s) l[1] += c; else merged.push([s, c, m]); }
  merged.forEach(([s, c, m]) => g.addGroup(s, c, m));
  g.computeVertexNormals();
  return g;
}

function caseGeometries(P) {
  const C = P.case, a = C.angle * Math.PI / 180, W = C.W, D = C.D;
  const top = (y) => C.h_front + (y + D / 2) * Math.tan(a);
  const seam = (y) => top(y) - C.seam_depth / Math.cos(a);
  const Md = new Matrix4().makeRotationX(a).setPosition(0, 0, top(0));
  const outline = (inset) => rrectRing(W / 2 - inset, D / 2 - inset, C.corner - inset, 16, 1, 1);
  const ringZ = (inset, zf) => outline(inset).map(([x, y]) => new V3(x, y, zf(y)));
  const well = (ex, zd) => rrectRing(C.well[0] / 2 + ex, C.well[1] / 2 + ex, C.well_corner + ex, 16, 1, 1)
    .map(([x, y]) => new V3(x, y + C.well_cy, zd).applyMatrix4(Md));
  const v = C.seam_v, ch = C.chamfer, sd = C.seam_depth;
  const topG = loft([ringZ(v, seam), ringZ(0, (y) => seam(y) + v), ringZ(0, (y) => top(y) - ch), ringZ(ch, top),
    well(C.well_chamfer, 0), well(0, -C.well_chamfer), well(0, -sd)], { closed: true, bandGroups: [0, 0, 1, 0, 1, 0, 0] });
  const fb = C.bottom_fillet, fh = C.foot_h;
  const botG = loft([ringZ(fb, () => fh), ringZ(fb * 0.293, () => fh + fb * 0.293), ringZ(0, () => fh + fb),
    ringZ(0, (y) => seam(y) - v), ringZ(v, seam), well(0, -sd), well(0, -C.well_depth)], { capFirst: true, capLast: true });
  return { topG, botG, Md, top };
}

// ---------------------------------------------------------------- сборка
export function buildKeyboard(P, colorway = 'snow') {
  const cw = P.colorways[colorway];
  const root = new Group(); root.name = 'KB_root';
  root.rotation.x = -Math.PI / 2;                        // оси Blender (Z вверх) → three (Y вверх)
  const keys = P.layout;
  const atlas = legendAtlas(P, cw, keys);
  const { topG, botG, Md } = caseGeometries(P);
  const deck = new Group(); deck.name = 'KB_deck'; deck.matrixAutoUpdate = false; deck.matrix.copy(Md);
  root.add(deck);
  // колпачки: прототип на (ширина, ряд), копия со сдвигом и UV ячейки → одна геометрия
  const protos = new Map(), parts = [];
  for (const k of keys) {
    const key = `${k.w}_${k.profile}`;
    if (!protos.has(key)) protos.set(key, keycapGeometry(keycapDims(P, k.w, k.profile), P));
    const g = protos.get(key).clone();
    const uv = g.attributes.uv, m = atlas.map[k.id];
    for (let i = 0; i < uv.count; i++) uv.setXY(i, m.off[0] + uv.getX(i) * m.scl[0], m.off[1] + uv.getY(i) * m.scl[1]);
    g.translate(k.cx, k.cy, P.deck.keycap_bottom);
    parts.push(g);
  }
  const keyG = mergeGeometries(parts);
  const grain = grainTexture();
  const keyMat = new MeshPhysicalMaterial({ map: atlas.tex, roughness: 0.58, metalness: 0, bumpMap: grain, bumpScale: 0.35,
    sheen: 0.04, sheenRoughness: 0.8, sheenColor: new Color('#ffffff'), specularIntensity: 1.0, ior: 1.54 });
  const keyMesh = new Mesh(keyG, keyMat); keyMesh.name = 'Keycaps'; keyMesh.castShadow = keyMesh.receiveShadow = true;
  deck.add(keyMesh);
  // свитчи (видны в щелях) — InstancedMesh
  const S = P.switch;
  const swG = new BoxGeometry(S.top_b[0], S.top_b[1], S.top_h); swG.translate(0, 0, P.deck.plate_top + S.top_h / 2);
  const sw = new InstancedMesh(swG, new MeshStandardMaterial({ color: cw.switch, roughness: 0.45 }), keys.length);
  const o = new Object3D();
  keys.forEach((k, i) => { o.position.set(k.cx, k.cy, 0); o.updateMatrix(); sw.setMatrixAt(i, o.matrix); });
  sw.name = 'Switches'; sw.receiveShadow = true; deck.add(sw);
  // пластина в колодце
  const plateMat = new MeshStandardMaterial({ color: new Color().setRGB(...cw.plate), metalness: 1, roughness: 0.4 });
  const plate = new Mesh(new PlaneGeometry(P.case.well[0], P.case.well[1]), plateMat);
  plate.position.set(0, P.case.well_cy, P.deck.plate_top); plate.receiveShadow = true; deck.add(plate);
  // корпус: тело (пескоструй) и полированные фаски
  const body = new MeshPhysicalMaterial({ color: new Color().setRGB(...cw.case), metalness: 1, roughness: 0.36 });
  const chamfer = new MeshPhysicalMaterial({ color: new Color().setRGB(...cw.case), metalness: 1, roughness: 0.08 });
  const ct = new Mesh(topG, [body, chamfer]); ct.name = 'Case_Top';
  const cb = new Mesh(botG, [body, chamfer]); cb.name = 'Case_Bottom';
  for (const m of [ct, cb]) { m.castShadow = m.receiveShadow = true; root.add(m); }
  return { root, deck, keyMesh, atlas, materials: { keyMat, body, chamfer, plateMat } };
}
