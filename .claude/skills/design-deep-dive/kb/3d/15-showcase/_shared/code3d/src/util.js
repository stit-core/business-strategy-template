// util.js · общий код 3D «Звена» (_shared/code3d) · кривые времени и обратный тон Neutral
import { Color } from 'three';

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const seg = (t, a, b) => clamp((t - a) / (b - a));
export const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
export const lerp = (a, b, t) => a + (b - a) * t;
export const bump = (x, a, b, c) => (x <= a || x >= c ? 0 : x < b ? ease(seg(x, a, b)) : 1 - ease(seg(x, b, c)));
export const snap = (u) => (u <= 0 ? 0 : u >= 1 ? 1 : 1 - Math.exp(-6 * u) * Math.cos(9 * u));

// Khronos PBR Neutral: обратная функция для тёмных цветов (фон, туман, горизонт). Сцена пропускает фон через тот же тон-маппинг,
// что и предметы (иначе туман на полу и фон расходятся ступенькой на горизонте), поэтому цвет страницы задаётся «до тона»:
// Neutral(exp·x) = hex. Для x < 0.08 у Neutral «носок» x − 6,25x² снимается со всех каналов — тёмный серый темнеет в 5–10 раз.
export function preTone(hex, exposure) {
  const c = new Color(hex);                                       // линейные значения
  const ym = Math.min(c.r, c.g, c.b);
  let off;
  if (ym < 0.04) { const xm = Math.sqrt(ym / 6.25); off = xm - ym; } else off = 0.04;
  return new Color((c.r + off) / exposure, (c.g + off) / exposure, (c.b + off) / exposure);
}
