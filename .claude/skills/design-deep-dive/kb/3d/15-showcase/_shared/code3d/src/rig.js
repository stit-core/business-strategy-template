// rig.js · общий код 3D «Звена» (_shared/code3d) · кинематика: имена модулей и шарниров, позы, разнос.
// Это и есть контракт гибрида: модуль GLB с именем из ORDER ставится матрицей T(разнос) · piv[k].matrixWorld · R(доворот),
// поэтому его геометрия должна лежать в системе своего шарнира (точка — шарнир, оси three: Y вверх). Метры — как здесь.
import { Object3D, Group } from 'three';
import { lerp } from './util.js';

export const L1 = 0.78, L2 = 0.62;                                  // длины труб звеньев L1, L2 (м)
export const ORDER = ['base', 'j1', 'j2', 'l1', 'j3', 'l2', 'wrist', 'grip'];
// шарнир → родитель, смещение от родителя (м, в покое), ось вращения; высоты шарниров в позе REST: j1 0,34 · j2 0,935 · j3 2,145 ·
// wrist 3,115 · grip 3,415 (l1 = j2, l2 = j3 — звено висит на шарнире сустава)
export const PIVOTS = {
  base: [null, [0, 0, 0], null], j1: ['base', [0, 0.34, 0], 'y'], j2: ['j1', [0, 0.36 + 0.235, 0], 'x'], l1: ['j2', [0, 0, 0], null],
  j3: ['l1', [0, 0.2 + L1 + 0.23, 0], 'x'], l2: ['j3', [0, 0, 0], null], wrist: ['l2', [0, 0.17 + L2 + 0.18, 0], 'x'], grip: ['wrist', [0, 0.3, 0], 'y'],
};
export const POSE_WORK = { j1: -0.62, j2: 0.42, j3: -1.95, wr: -0.72, roll: 0.35 };
export const POSE_REST = { j1: 0, j2: 0, j3: 0, wr: 0, roll: 0 };
export const POSE_FIRST = { j1: -1.15, j2: 0.5, j3: -1.85, wr: -0.85, roll: 0.3 };
export const blendPose = (a, b, t) => Object.fromEntries(Object.keys(a).map((k) => [k, lerp(a[k], b[k], t)]));
export const EXPLODE = {                                             // [dx, dy, dz, наклон] при полном разносе
  base: [0, 0, 0, 0], j1: [-0.55, 0.06, 0.12, 0.12], j2: [0.62, 0.16, 0.08, -0.16], l1: [-0.7, 0.26, -0.06, 0.1],
  j3: [0.72, 0.36, 0.12, -0.14], l2: [-0.64, 0.46, 0.08, 0.12], wrist: [0.6, 0.56, -0.08, -0.18], grip: [-0.26, 0.7, 0.14, 0.14],
};

// невидимые шарниры (Object3D): поза вращает их, видимые модули лежат в корне и получают матрицу шарнира
export function createPivots() {
  const piv = Object.fromEntries(ORDER.map((k) => [k, new Object3D()]));
  for (const k of ORDER) {
    const [parent, off] = PIVOTS[k];
    piv[k].name = 'piv.' + k;
    piv[k].position.set(off[0], off[1], off[2]);
    if (parent) piv[parent].add(piv[k]);
  }
  const rig = new Group(); rig.name = 'rig'; rig.add(piv.base);
  return { piv, rig };
}
export function applyPose(piv, rig, p) {
  piv.j1.rotation.y = p.j1; piv.j2.rotation.x = p.j2; piv.j3.rotation.x = p.j3; piv.wrist.rotation.x = p.wr; piv.grip.rotation.y = p.roll;
  rig.updateMatrixWorld(true);
}
