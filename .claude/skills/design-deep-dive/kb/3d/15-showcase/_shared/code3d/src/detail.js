// detail.js · общий код 3D «Звена» (_shared/code3d) · приём «detail»: винты (локальные матрицы в системе модуля,
// один InstancedMesh на всю руку), риски колец, швы, атлас маркировки canvas-текстурой и наклейки, кабель у основания.
import {
  Vector3, Quaternion, Matrix4, BoxGeometry, CylinderGeometry, PlaneGeometry, BufferGeometry, Float32BufferAttribute, LatheGeometry,
  Vector2, CanvasTexture, SRGBColorSpace, Mesh, TubeGeometry, CatmullRomCurve3,
} from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { lerp } from './util.js';

export const SCREWS = [];                                          // {k: модуль, m: Matrix4 в системе модуля}
export function addScrew(k, pos, axis, s = 1) {                    // axis — направление «из детали» (нормаль к площадке)
  const q = new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), axis.clone().normalize());
  SCREWS.push({ k, m: new Matrix4().compose(pos, q, new Vector3(s, s, s)) });
}
export function screwGeometry() {                                   // головка винта с внутренним шестигранником: сталь + тёмное гнездо
  const r = 0.0085, h = 0.006;
  const g = new LatheGeometry([[0, 0.0035], [0.45 * r, 0.0035], [0.45 * r, h], [0.86 * r, h], [r, 0.82 * h], [r, -0.002], [0, -0.002]].map(([a, b]) => new Vector2(a, b)), 12);
  const pos = g.attributes.position, col = [];
  for (let i = 0; i < pos.count; i++) { const rr = Math.hypot(pos.getX(i), pos.getZ(i)); const dk = rr < 0.5 * r && pos.getY(i) < h - 1e-4 ? 0.12 : 1; col.push(dk, dk, dk); }
  g.setAttribute('color', new Float32BufferAttribute(col, 3));
  return g;
}
export function ringTicks(r, x, n = 4, axisX = true) {             // риски кольца-замка: видно, что кольцо повернулось на 90°
  const out = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + Math.PI / 4;
    const g = new BoxGeometry(axisX ? 0.02 : 0.008, axisX ? 0.008 : 0.02, 0.006);
    if (axisX) g.translate(x, Math.cos(a) * (r + 0.002), Math.sin(a) * (r + 0.002));
    out.push(g);
  }
  return out;
}
export function seamX(r, x) { const g = new CylinderGeometry(r + 0.0004, r + 0.0004, 0.0028, 64, 1, true); g.rotateZ(Math.PI / 2); g.translate(x, 0, 0); return g; }
export function seamY(r, y) { const g = new CylinderGeometry(r + 0.0004, r + 0.0004, 0.0028, 64, 1, true); g.translate(0, y, 0); return g; }

// атлас маркировки 1024×512: логотип, J1…J4, шильдик основания (цвет «напечатан» в текстуре)
const ATLAS = { logo: [0, 0, 1024, 200], J1: [0, 200, 256, 150], J2: [256, 200, 256, 150], J3: [512, 200, 256, 150], J4: [768, 200, 256, 150],
  plate: [0, 360, 1024, 152] };
export function makeAtlas(fontFamily) {
  const c = document.createElement('canvas'); c.width = 1024; c.height = 512;
  const x = c.getContext('2d');
  x.clearRect(0, 0, 1024, 512);
  const fam = fontFamily || '"Science Gothic", "Arial Narrow", "DejaVu Sans Condensed", sans-serif';
  // логотип: знак (два кольца) + слово — графит на белом лаке
  x.strokeStyle = '#ff5a1f'; x.lineWidth = 14;
  x.beginPath(); x.arc(90, 100, 46, 0, Math.PI * 2); x.stroke(); x.beginPath(); x.arc(172, 100, 46, 0, Math.PI * 2); x.stroke();
  x.fillStyle = '#2b2e33'; x.textBaseline = 'middle';
  x.font = `800 128px ${fam}`; try { x.fontStretch = 'extra-condensed'; } catch (e) { /* старые движки */ }
  x.fillText('ЗВЕНО', 250, 106);
  // метки суставов — светло-серые на графитовых крышках
  x.font = `700 104px ${fam}`; x.fillStyle = '#c9ccd1'; x.textAlign = 'center';
  ['J1', 'J2', 'J3', 'J4'].forEach((t, i) => x.fillText(t, 128 + i * 256, 278));
  // шильдик основания: светлый текст на тёмном
  x.textAlign = 'left'; x.font = `600 56px ${fam}`; x.fillStyle = '#b9bdc4';
  x.fillText('ЗВЕНО · 24 В · IP54 · 5 кг', 24, 436);
  const t = new CanvasTexture(c); t.colorSpace = SRGBColorSpace; t.anisotropy = 4;
  return t;
}
function uvRect(name) { const [x, y, w, h] = ATLAS[name]; return [x / 1024, 1 - (y + h) / 512, (x + w) / 1024, 1 - y / 512]; }
// наклейка на цилиндр оси Y: радиус r, высоты y0..y1, центр по азимуту a (рад от +Z к +X), угловая ширина span
export function decalCylY(r, y0, y1, a, span, name, n = 18) {
  const [u0, v0, u1, v1] = uvRect(name); const p = [], uv = [], nr = [], idx = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, ang = a - span / 2 + span * t, sx = Math.sin(ang), sz = Math.cos(ang);
    for (let j = 0; j <= 1; j++) { const y = j ? y1 : y0; p.push(sx * r, y, sz * r); nr.push(sx, 0, sz); uv.push(lerp(u0, u1, t), j ? v1 : v0); }
  }
  for (let i = 0; i < n; i++) { const a0 = i * 2; idx.push(a0, a0 + 2, a0 + 1, a0 + 1, a0 + 2, a0 + 3); }
  const g = new BufferGeometry(); g.setAttribute('position', new Float32BufferAttribute(p, 3)); g.setAttribute('normal', new Float32BufferAttribute(nr, 3));
  g.setAttribute('uv', new Float32BufferAttribute(uv, 2)); g.setIndex(idx); return g;
}
// наклейка на торец крышки (плоскость ⊥ X): центр (x, cy, cz), размер w×h, лицом в +X (dir 1) или −X
export function decalCapX(x, cy, cz, w, h, dir, name) {
  const g = new PlaneGeometry(w, h); const [u0, v0, u1, v1] = uvRect(name);
  const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, lerp(u0, u1, uv.getX(i)), lerp(v0, v1, uv.getY(i)));
  g.rotateY(dir > 0 ? Math.PI / 2 : -Math.PI / 2); g.translate(x, cy, cz); return g;
}

// кабель у основания: из разъёма сзади-справа (азимут CABLE_AZ), провисает до пола и уходит к напольному разъёму (не к горизонту:
// в перспективе кабель к горизонту читался «висящим в воздухе»)
export const CABLE_AZ = 2.86;
export function buildCable(material, hq) {
  const dirX = Math.sin(CABLE_AZ), dirZ = Math.cos(CABLE_AZ), sx = dirZ, sz = -dirX;    // вдоль и поперёк
  const pts = [[0.34, 0.14, 0], [0.46, 0.13, 0], [0.62, 0.06, 0.02], [0.85, 0.016, 0.07], [1.25, 0.014, 0.2], [1.75, 0.014, 0.16], [2.2, 0.03, -0.02], [2.36, 0.045, -0.08]]
    .map(([d, y, l]) => new Vector3(dirX * d + sx * l, y, dirZ * d + sz * l));
  const port = new CylinderGeometry(0.075, 0.085, 0.03, 32); port.translate(pts[7].x, 0.015, pts[7].z);   // напольный разъём
  const cable = new Mesh(mergeGeometries([new TubeGeometry(new CatmullRomCurve3(pts, false, 'catmullrom', 0.5), 90, 0.014, 10, false).toNonIndexed(), port.toNonIndexed()]), material);
  cable.castShadow = hq; cable.receiveShadow = hq;
  return cable;
}
