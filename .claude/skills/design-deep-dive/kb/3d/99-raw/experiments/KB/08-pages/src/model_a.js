// model_a.js — вариант A: клавиатура «Ё» целиком кодом (three r186) по тому же паспорту, что у Blender (passport.json, метры,
// оси Blender внутри группы, повёрнутой в Y-вверх). Фаза 2: горизонтальное дно, пескоструй 0,52 + зерно (тайловые карты
// canvas), латунная плита 200 × 40 × 6 мм и полоса, «esc» на верхней грани Ё, пластина с вырезами, свитчи — инстансы
// простых форм, слои разборки по нормали деки (тот же закон, что kbb.apply_explode).
// Все 68 колпачков — одна геометрия и один материал (1 вызов): у вершины индекс клавиши, нажатие — сдвиг в вершинном
// шейдере по массиву uPress[68]; надписи — атлас canvas шрифтом страницы (Onest).
import {
  BufferGeometry, Float32BufferAttribute, Vector3, Matrix4, Group, Mesh, InstancedMesh, MeshPhysicalMaterial,
  MeshStandardMaterial, MeshBasicMaterial, Color, CanvasTexture, SRGBColorSpace, RepeatWrapping, LinearMipmapLinearFilter,
  NoColorSpace, Object3D, Shape, Path, ExtrudeGeometry, CylinderGeometry, BoxGeometry, PlaneGeometry, ShadowMaterial,
} from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const MM = 0.001;
const V3 = Vector3;
const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const lin = (c) => new Color().setRGB(c[0], c[1], c[2]);

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

// ---------------------------------------------------------------- колпачок Cherry кольцами (система колпачка)
function keycapGeometry(kd, P, phone) {
  const K = P.keycap;
  const nc = phone ? 4 : 6, nx = Math.max(3, Math.round(kd.w * 3)), ny = 3;
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
  const nTop0 = rings.length - 1;
  const KC = phone ? 3 : 5;
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
  return g;
}

// ---------------------------------------------------------------- атлас надписей (canvas, Onest), по расцветке
function legendAtlas(P, cw, keys, ppm, marginMM = 4.5, W = 2048) {
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
  const cap = 0.708;
  const text = (s, xmm, ymm, capmm, wght, align, col, ox, oy, alpha = 1) => {
    if (!s) return;
    g.font = `${wght} ${capmm / cap * ppm}px Onest`; g.fillStyle = col; g.textAlign = align; g.textBaseline = 'alphabetic';
    g.globalAlpha = alpha; g.fillText(s, ox + xmm * ppm, oy + ymm * ppm); g.globalAlpha = 1;
  };
  const map = {};
  for (const c of cells) {
    const { k, kd } = c; const role = k.role;
    g.fillStyle = role === 'accent' ? cw.accent : cw[role]; g.fillRect(c.x, c.y, c.w, c.h);
    const ox = c.x + marginMM * ppm, oy = c.y + marginMM * ppm;
    const wt = kd.wt * 1000, dt = kd.dt * 1000, ix = 1.7, it = 1.55, ib = 1.65;
    const L1 = cw.legend1, L2 = cw.legend2;
    if (k.id === 'yo') {
      text('Ё', wt / 2, dt / 2 + 2.9, 6.2, 640, 'center', cw.legend_accent, ox, oy);
      text('esc', wt - 1.7, dt - 1.65, 1.75, 520, 'right', cw.legend_accent, ox, oy, 0.6);   // Esc = Fn + Ё (верхняя грань)
    } else if (k.id === 'space') { /* без надписи */ } else if (role === 'mod') {
      if ('←→↑↓'.includes(k.l1)) text(k.l1, wt / 2, dt / 2 + 1.5, 3.0, 500, 'center', L1, ox, oy);
      else text(k.l1, ix, it + 2.1, 2.1, 480, 'left', L1, ox, oy);
    } else if (k.row === 0 || k.id === 'bsl') {
      text(k.l1, ix, dt - ib, 3.1, 520, 'left', L1, ox, oy);
      if (k.l3) { text(k.l2, ix, it + 2.4, 2.4, 480, 'left', L2, ox, oy); text(k.l3, wt - ix, it + 2.4, 2.4, 480, 'right', L1, ox, oy); } else text(k.l2, ix, it + 2.4, 2.4, 480, 'left', L1, ox, oy);
    } else if (k.id === 'slash') {
      text(`${k.l1} ${k.l3}`, ix, it + 3.3, 3.3, 520, 'left', L1, ox, oy); text(k.l2, wt - ix, dt - ib, 2.5, 470, 'right', L2, ox, oy);
    } else {
      text(k.l1, ix, it + 3.4, 3.4, 540, 'left', L1, ox, oy); text(k.l2, wt - ix, dt - ib, 2.5, 470, 'right', L2, ox, oy);
    }
    map[k.id] = { off: [ox / W, 1 - (oy + dt * ppm) / H], scl: [wt * ppm / W, dt * ppm / H] };
  }
  const tex = new CanvasTexture(cv);
  tex.colorSpace = SRGBColorSpace; tex.anisotropy = 8; tex.minFilter = LinearMipmapLinearFilter;
  return { tex, map, size: [W, H] };
}

function noiseTexture(n, seed, lo, hi, repeat) {
  const cv = document.createElement('canvas'); cv.width = cv.height = n;
  const g = cv.getContext('2d'); const im = g.createImageData(n, n);
  let s = seed; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < n * n; i++) { const v = lo + rnd() * (hi - lo) | 0; im.data.set([v, v, v, 255], i * 4); }
  g.putImageData(im, 0, 0);
  const t = new CanvasTexture(cv); t.wrapS = t.wrapT = RepeatWrapping; t.colorSpace = NoColorSpace; t.repeat.set(repeat, repeat);
  return t;
}
function contactShadow(W, D) {
  const cv = document.createElement('canvas'); cv.width = 512; cv.height = 288;
  const g = cv.getContext('2d');
  g.fillStyle = '#000'; g.fillRect(0, 0, 512, 288);
  g.filter = 'blur(14px)'; g.fillStyle = '#9a9a9a';
  const sx = 512 / 0.46, sy = 288 / 0.26, w = W * sx, h = D * sy;
  g.beginPath(); g.roundRect((512 - w) / 2, (288 - h) / 2, w, h, 16); g.fill();
  g.filter = 'blur(3px)'; g.fillStyle = '#e0e0e0';
  g.beginPath(); g.roundRect((512 - w) / 2 + 4, (288 - h) / 2 + 3, w - 8, h - 6, 12); g.fill();
  const t = new CanvasTexture(cv); t.colorSpace = NoColorSpace;
  return t;
}

// ---------------------------------------------------------------- корпус кольцами (как kbb.case_meshes), дно горизонтально
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
  const fb = C.bottom_fillet, fh = C.foot_h, floorZ = fh + C.floor_skin;
  const botG = loft([ringZ(fb, () => fh), ringZ(fb * 0.293, () => fh + fb * 0.293), ringZ(0, () => fh + fb),
    ringZ(0, (y) => seam(y) - v), ringZ(v, seam), well(0, -sd), well(0, -sd).map((p) => new V3(p.x, p.y, floorZ))], { capFirst: true, capLast: true });
  return { topG, botG, Md, top };
}
// скруглённый прямоугольник (с вырезами) → выдавливание с фаской
function slab(w, d, t, r, holes = [], bevel = 0.3 * MM) {
  const s = new Shape();
  const a = w / 2, b = d / 2;
  s.moveTo(-a + r, -b); s.lineTo(a - r, -b); s.quadraticCurveTo(a, -b, a, -b + r); s.lineTo(a, b - r); s.quadraticCurveTo(a, b, a - r, b);
  s.lineTo(-a + r, b); s.quadraticCurveTo(-a, b, -a, b - r); s.lineTo(-a, -b + r); s.quadraticCurveTo(-a, -b, -a + r, -b);
  for (const [cx, cy, hw, hd] of holes) {
    const h = new Path(); h.moveTo(cx - hw / 2, cy - hd / 2); h.lineTo(cx - hw / 2, cy + hd / 2); h.lineTo(cx + hw / 2, cy + hd / 2); h.lineTo(cx + hw / 2, cy - hd / 2); h.closePath();
    s.holes.push(h);
  }
  const g = new ExtrudeGeometry(s, { depth: t - 2 * bevel, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 1, curveSegments: 4 });
  g.translate(0, 0, bevel);
  return g;
}
// свитч MX простыми формами: низ-куб, верх — усечённая пирамида, шток-крест (группы: 0 корпус, 1 шток)
function switchGeometry(P) {
  const S = P.switch, Dk = P.deck;
  const lower = new BoxGeometry(S.lower[0], S.lower[1], Dk.plate_top - Dk.pcb_top);
  lower.translate(0, 0, (Dk.plate_top + Dk.pcb_top) / 2);
  const top = new CylinderGeometry(S.top_t[0] / Math.SQRT2, S.top_b[0] / Math.SQRT2, S.top_h, 4, 1);
  top.rotateY(Math.PI / 4); top.rotateX(Math.PI / 2); top.translate(0, 0, Dk.plate_top + S.top_h / 2);
  const z0 = Dk.plate_top + S.top_h - 0.6 * MM, z1 = S.stem_top;
  const s1 = new BoxGeometry(S.stem[0], S.stem[1], z1 - z0); s1.translate(0, 0, (z0 + z1) / 2);
  const s2 = new BoxGeometry(S.stem[1], S.stem[0], z1 - z0); s2.translate(0, 0, (z0 + z1) / 2);
  const housing = mergeGeometries([lower.toNonIndexed(), top.toNonIndexed()]);
  const stem = mergeGeometries([s1.toNonIndexed(), s2.toNonIndexed()]);
  const g = mergeGeometries([housing, stem], true);
  g.computeVertexNormals();
  return g;
}

// ---------------------------------------------------------------- сборка
export async function buildModelA({ phone, quality, idle = async () => {} }) {
  const P = await fetch('assets/data/passport.json').then((r) => r.json());
  await Promise.all(['540 20px Onest', '540 20px Onest'].map((f, i) => document.fonts.load(f, i ? 'Ё' : 'Q')));
  const keys = P.layout;
  const root = new Group(); root.name = 'KB_root';
  const inner = new Group(); inner.rotation.x = -Math.PI / 2; root.add(inner);     // оси Blender → three
  const { topG, botG, Md } = caseGeometries(P);
  const deck = new Group(); deck.matrixAutoUpdate = false; deck.matrix.copy(Md); inner.add(deck);
  const layers = {};
  for (const L of ['keycaps', 'switches', 'stabs', 'plate', 'pcb']) { layers[L] = new Group(); deck.add(layers[L]); }
  // колпачки: одна геометрия, индекс клавиши у вершины
  const protos = new Map(), parts = [], cells = [];          // ячейка атласа — в своём массиве: clone() делит userData
  keys.forEach((k, ki) => {
    const pk = `${k.w}_${k.profile}`;
    if (!protos.has(pk)) protos.set(pk, keycapGeometry(keycapDims(P, k.w, k.profile), P, phone));
    const g = protos.get(pk).clone();
    g.translate(k.cx, k.cy, P.deck.keycap_bottom);
    g.setAttribute('kIdx', new Float32BufferAttribute(new Float32Array(g.attributes.position.count).fill(ki), 1));
    cells.push(k.id);
    parts.push(g);
  });
  const atlases = {};
  const atlasFor = (cw) => (atlases[cw] ||= legendAtlas(P, P.colorways[cw], keys, phone ? 4 : 8, 4.5, phone ? 1024 : 2048));
  await idle();
  const keyG = mergeGeometries(parts);
  const uvBase = Float32Array.from(keyG.attributes.uv.array);
  const applyAtlasUV = (at) => {
    const uv = keyG.attributes.uv; let o = 0;
    for (let pi = 0; pi < parts.length; pi++) {
      const m = at.map[cells[pi]], n = parts[pi].attributes.position.count;
      for (let i = 0; i < n; i++, o++) uv.setXY(o, m.off[0] + uvBase[o * 2] * m.scl[0], m.off[1] + uvBase[o * 2 + 1] * m.scl[1]);
    }
    uv.needsUpdate = true;
  };
  await idle();
  const a0 = atlasFor('snow');
  applyAtlasUV(a0);
  await idle();
  const grain = noiseTexture(256, 7, 110, 160, 96);
  const press = new Float32Array(68);
  const U = { uPress: { value: press }, uYo: { value: 0 }, uYoIdx: { value: keys.findIndex((k) => k.id === 'yo') }, uYoCol: { value: new Color('#E05A2A') } };
  const keyMat = new MeshPhysicalMaterial({ map: a0.tex, roughness: 0.58, metalness: 0, bumpMap: grain, bumpScale: 0.35,
    sheen: 0.04, sheenRoughness: 0.8, sheenColor: new Color('#ffffff'), ior: 1.54 });
  keyMat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, U);
    // KB3: верх нажатой клавиши чуть светлее (как подсветка обвода у B) — эмиссия по глубине нажатия 0…3,8 мм
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float kIdx;\nuniform float uPress[68];\nuniform float uYoIdx;\nvarying float vYo;\nvarying float vPress;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nfloat kbP = uPress[int(kIdx + 0.5)];\ntransformed.z -= kbP;\nvPress = clamp(kbP / 0.0038, 0.0, 1.0);\nvYo = abs(kIdx - uYoIdx) < 0.5 ? 1.0 : 0.0;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uYo;\nuniform vec3 uYoCol;\nvarying float vYo;\nvarying float vPress;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += uYoCol * (0.6 * uYo * uYo * vYo) + vec3(0.09) * vPress;');
  };
  keyMat.customProgramCacheKey = () => 'kb-a-keys-press';
  const keyMesh = new Mesh(keyG, keyMat); keyMesh.name = 'Keycaps'; keyMesh.castShadow = keyMesh.receiveShadow = !!quality.shadows;
  layers.keycaps.add(keyMesh);
  // свитчи — InstancedMesh простых форм
  const swMatH = new MeshStandardMaterial({ roughness: 0.42 }), swMatS = new MeshStandardMaterial({ color: '#EDE4CF', roughness: 0.35 });
  const sw = new InstancedMesh(switchGeometry(P), [swMatH, swMatS], keys.length);
  const o3 = new Object3D();
  keys.forEach((k, i) => { o3.position.set(k.cx, k.cy, 0); o3.updateMatrix(); sw.setMatrixAt(i, o3.matrix); });
  sw.receiveShadow = !!quality.shadows; layers.switches.add(sw);
  // стабилизаторы: корпуса-бруски у 2 / 2,25 / 6,25u
  const stabG = [];
  for (const k of keys) {
    const half = P.stab_half_spacing[String(k.w)];
    if (!half) continue;
    for (const s of [-1, 1]) { const b = new BoxGeometry(6.4 * MM, 11 * MM, 5.4 * MM); b.translate(k.cx + s * half, k.cy + 0.8 * MM, P.deck.plate_top - 0.4 * MM); stabG.push(b); }
  }
  layers.stabs.add(new Mesh(mergeGeometries(stabG), swMatH));
  // пластина с вырезами, плата
  const C = P.case, cut = P.switch.plate_cut;
  const holes = keys.map((k) => [k.cx, k.cy - C.well_cy, cut, cut]);
  const plateMat = new MeshStandardMaterial({ metalness: 1, roughness: 0.5 });
  const plate = new Mesh(slab(C.well[0] - 0.4 * MM, C.well[1] - 0.4 * MM, P.deck.plate_t, 1.2 * MM, holes, 0.12 * MM), plateMat);
  plate.position.set(0, C.well_cy, P.deck.plate_top - P.deck.plate_t); plate.receiveShadow = !!quality.shadows; layers.plate.add(plate);
  const pcb = new Mesh(slab(C.well[0] - 2 * MM, C.well[1] - 2 * MM, P.deck.pcb_t, 1 * MM, [], 0.1 * MM), new MeshStandardMaterial({ color: '#15171A', roughness: 0.5 }));
  pcb.position.set(0, C.well_cy, P.deck.pcb_top - P.deck.pcb_t); layers.pcb.add(pcb);
  // корпус: пескоструй (шероховатость 0,47–0,57 картой + зерно) и полированные фаски
  const rMap = noiseTexture(256, 11, 120, 146, 60);
  const body = new MeshPhysicalMaterial({ metalness: 1, roughness: 1, roughnessMap: rMap, bumpMap: grain, bumpScale: 0.12 });
  body.roughness = 1.0;                                 // карта 0,47–0,57 (120–146 / 255)
  const chamfer = new MeshPhysicalMaterial({ metalness: 1, roughness: 0.12 });
  const ct = new Mesh(topG, [body, chamfer]), cb = new Mesh(botG, [body, chamfer]);
  for (const m of [ct, cb]) { m.castShadow = m.receiveShadow = !!quality.shadows; inner.add(m); }
  // латунь: плита в дне и полоса сзади
  const Wt = P.weight, brass = new MeshStandardMaterial({ color: lin(P.brass), metalness: 1, roughness: 0.3 });
  const weight = new Mesh(slab(Wt.w, Wt.d, Wt.t, Wt.corner, [], 0.4 * MM), brass);
  weight.position.set(0, Wt.y_center, C.foot_h + C.floor_skin + 0.1 * MM); inner.add(weight);
  const strip = new Mesh(slab(Wt.strip_w, Wt.strip_h, 1.2 * MM, Wt.corner, [], 0.25 * MM), brass);
  strip.rotation.x = Math.PI / 2; strip.position.set(0, C.D / 2 + Wt.strip_proud, C.foot_h + C.bottom_fillet + 1.2 * MM + Wt.strip_h / 2); inner.add(strip);
  // тень: карта теней ключа на прозрачный пол (десктоп) + контактная тень canvas (везде)
  const cs = new Mesh(new PlaneGeometry(0.46, 0.26), new MeshBasicMaterial({ color: 0x000000, alphaMap: contactShadow(C.W, C.D), transparent: true, depthWrite: false, toneMapped: false, opacity: 0.55 }));
  cs.position.set(0, 0, 0.0002); cs.renderOrder = -1; inner.add(cs);
  let sf = null;
  if (quality.shadows) {
    sf = new Mesh(new PlaneGeometry(1.2, 1.2), new ShadowMaterial({ opacity: 0.28 }));
    sf.position.z = 0.0003; sf.receiveShadow = true; inner.add(sf);
  }
  const nDeck = new V3(0, 0, 1).applyMatrix4(new Matrix4().extractRotation(Md)).normalize();
  const wBase = weight.position.clone();
  const setCw = (cw) => {
    const c = P.colorways[cw], at = atlasFor(cw);
    if (keyMat.map !== at.tex) { keyMat.map = at.tex; applyAtlasUV(at); }
    body.color.copy(lin(c.case)); chamfer.color.copy(lin(c.case)); plateMat.color.copy(lin(c.plate)); swMatH.color.set(c.switch);
    U.uYoCol.value.set(c.accent);
  };
  setCw('snow');
  const idToIdx = new Map(keys.map((k, i) => [k.id, i]));
  return {
    root,
    setColorway(cw) { setCw(cw); },
    // в разборке тени поднятых слоёв рвутся краем карты — без них; в наборе ключ низкий (16°) → длинная жёсткая тень с прямыми
    // краями (PCFSoft не размывает) — вдвое слабее, форму держит мягкая контактная тень
    setStage(n) { if (sf) { sf.visible = n !== 'x'; sf.material.opacity = n === 'type' ? 0.13 : 0.28; } },
    // шток свитча идёт вниз вместе с колпачком (KB3: иначе при нажатии крестик штока проступает сквозь верх колпачка) —
    // сдвигается весь экземпляр свитча, как у C; корпус свитча под колпачком не виден
    setKeyOffset(id, d) {
      const i = idToIdx.get(id);
      if (i === undefined) return;
      press[i] = d;
      o3.position.set(keys[i].cx, keys[i].cy, -d); o3.updateMatrix(); sw.setMatrixAt(i, o3.matrix); sw.instanceMatrix.needsUpdate = true;
    },
    setExplode(p) {
      const E = P.explode, RG = P.explode_ranges;
      for (const L of ['keycaps', 'switches', 'stabs', 'plate', 'pcb']) {
        const [a, b] = RG[L]; layers[L].position.z = E[L] * smooth((p - a) / (b - a));
      }
      const [a, b] = RG.weight;
      weight.position.copy(wBase).addScaledVector(nDeck, E.weight * smooth((p - a) / (b - a)));
    },
    setYoGlow(t) { U.uYo.value = t; },
    pick(ray) {
      const hit = ray.intersectObject(keyMesh, false)[0];
      if (!hit) return null;
      const ki = keyG.attributes.kIdx.getX(hit.face.a);
      return keys[Math.round(ki)].id;
    },
    info: { tris: keyG.index.count / 3 },
  };
}
