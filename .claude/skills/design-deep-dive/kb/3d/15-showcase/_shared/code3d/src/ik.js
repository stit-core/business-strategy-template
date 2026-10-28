// ik.js · общий код 3D «Звена» (_shared/code3d) · приём «ik»: рука тянется к указателю (аналитическая IK)
// Плечо на оси основания; звенья J2→J3 1,21 м, J3→кисть 0,97 м, кисть→точка захвата 0,42 м. Решение — углы тех же шарниров, что у поз.
import { clamp } from './util.js';
import { L1, L2 } from './rig.js';

export const SH_Y = 0.34 + 0.36 + 0.235, LA = 0.2 + L1 + 0.23, LB = 0.17 + L2 + 0.18, LC = 0.42;
export const wrapNear = (a, ref) => ref + ((((a - ref + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) - Math.PI;

// P — параметры позы (look): tilt — наклон инструмента вниз от линии на цель (рад), reach — доля полной длины, дальше которой цель
// подтягивается (рука не выпрямляется «в струну»). A — точка, куда смотрит инструмент (фаза 2: настоящая точка указателя, когда цель
// досягания упёрлась в границу текста — рука не лезет в текст, а УКАЗЫВАЕТ на курсор); null — смотреть на цель с наклоном tilt.
export function solveIK(T, prevJ1, out, P = {}, A = null) {
  const tilt = P.tilt ?? 0.55, reach = P.reach ?? 1;
  const r = Math.max(0.45, Math.hypot(T.x, T.z));
  const up = clamp(T.y, 0.35, 2.5) - SH_Y;
  // рука тянется «от себя»: ось f звена смотрит от цели (как в рабочей позе v2), углы — зеркально
  out.j1 = wrapNear(Math.atan2(T.x, T.z) + Math.PI, prevJ1);
  let ang = Math.atan2(up, r) - tilt;                              // инструмент смотрит на цель с наклоном вниз
  if (A) {                                                         // прицел: A в вертикальной плоскости руки (r вдоль направления на T)
    const ra = (A.x * T.x + A.z * T.z) / r, ua = A.y - SH_Y, dr = ra - r, du = ua - up;
    if (dr * dr + du * du > 0.0025) ang = clamp(Math.atan2(du, dr), -1.45, 0.5);
  }
  const tu = Math.cos(ang), tv = Math.sin(ang);
  let wu = r - LC * tu, wv = up - LC * tv, d = Math.hypot(wu, wv);
  const dmax = (LA + LB) * reach - 0.03, dmin = Math.abs(LA - LB) + 0.08;
  if (d > dmax) { wu *= dmax / d; wv *= dmax / d; d = dmax; } else if (d < dmin) { wu *= dmin / d; wv *= dmin / d; d = dmin; }
  const g = Math.acos(clamp((LA * LA + d * d - LB * LB) / (2 * LA * d), -1, 1));
  const e1 = Math.atan2(wv, wu) + g;                               // локоть вверх
  const eu = LA * Math.cos(e1), ev = LA * Math.sin(e1);
  const t2 = Math.atan2(eu, ev), a2 = Math.atan2(wu - eu, wv - ev), a3 = Math.atan2(tu, tv);
  out.j2 = clamp(-t2, -1.3, 1.3); out.j3 = clamp(-(a2 - t2), -2.75, 2.75); out.wr = clamp(-(a3 - a2), -2.1, 2.1); out.roll = P.roll ?? 0.35;
  return out;
}
