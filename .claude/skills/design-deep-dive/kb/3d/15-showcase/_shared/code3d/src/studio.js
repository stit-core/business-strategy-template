// studio.js · общий код 3D «Звена» (_shared/code3d) · приём «studio»: студии для PMREM из излучающих панелей
// v2 — одна студия; v3 — по сценам: «сборка» (длинные полосы-блики вдоль корпусов, контровые ±135°) и «скан» (холодная, контрастная).
// Лампы — белые (1,1,1) или холодные; тёплого отражателя в «сборке» нет с фазы 2: он красил точёные крышки в бронзу.
import { Scene, Mesh, SphereGeometry, PlaneGeometry, ShaderMaterial, MeshLambertMaterial, Color, BackSide, DoubleSide } from 'three';

function studioBase(floor = [0.05, 0.05, 0.055], hor = [0.06, 0.062, 0.07], top = [0.018, 0.019, 0.023]) {
  const s = new Scene();
  const v3 = (a) => `vec3(${a.map((x) => x.toFixed(4)).join(',')})`;
  s.add(new Mesh(new SphereGeometry(40, 32, 16), new ShaderMaterial({
    side: BackSide, depthWrite: false,
    vertexShader: 'varying vec3 vD; void main() { vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
    fragmentShader: `varying vec3 vD; void main() { float y = vD.y;
      vec3 c = y < 0.0 ? mix(${v3(floor)}, vec3(0.006), smoothstep(0.0, 0.25, -y)) : mix(${v3(hor)}, ${v3(top)}, smoothstep(0.0, 0.6, y));
      gl_FragColor = vec4(c, 1.0); }`,
  })));
  const quad = new PlaneGeometry(1, 1);
  const lamp = (w, h, x, y, z, color, k, look = [0, 1.2, 0]) => {
    const m = new Mesh(quad, new MeshLambertMaterial({ color: 0x000000, emissive: new Color(color), emissiveIntensity: k, side: DoubleSide }));
    m.scale.set(w, h, 1); m.position.set(x, y, z); m.lookAt(...look); s.add(m); return m;
  };
  return { s, lamp };
}
export function studioV2() {
  const { s, lamp } = studioBase();
  lamp(8, 8, -2.5, 12, 3, '#fdfdff', 5); lamp(1.1, 9, -9, 4, 2, '#ffffff', 8); lamp(1.1, 9, 8.5, 4, -3.5, '#dce6ff', 6);
  lamp(12, 5, 1, 2.5, 13, '#ffffff', 1.6); lamp(7, 6, 8, 3.5, 8, '#ffffff', 2.4); lamp(4, 1.4, 6, 0.4, 6, '#ff6d2e', 0.6);
  return s;
}
// v3 «сборка»: к v2 — две длинные горизонтальные полосы (блик-линия вдоль корпусов суставов, оси которых горизонтальны),
// верхний софтбокс шире и мягче, слабый отскок от пола. opts.warm — сила тёплого отражателя (фаза 1: 0,9; фаза 2: 0 — см. шапку)
export function studioStory(opts = {}) {
  const warm = opts.warm ?? 0;
  const { s, lamp } = studioBase([0.035, 0.036, 0.04]);
  lamp(10, 7, -2, 12, 2, '#fdfdff', 4.2);                         // верх: шире, мягче
  lamp(1.1, 9, -9, 4, 2, '#ffffff', 7);                           // полоса слева (вертикальная)
  lamp(14, 0.7, 0, 6.5, 9, '#ffffff', 6.5);                       // длинная горизонтальная полоса спереди-сверху → линия блика на лаке
  lamp(14, 0.45, 2, 2.2, 10, '#ffffff', 3.8);                     // вторая, ниже — двойная линия на цилиндрах (9 и 5 давали пересвет 2–4 %)
  lamp(1.0, 9, 8.5, 4, -3.5, '#dce6ff', 6.5);                     // контровой справа-сзади (холодный)
  lamp(1.0, 7, -7, 3.5, -6, '#e8eeff', 4.5);                      // контровой слева-сзади — силуэт с двух сторон (±135°)
  lamp(12, 5, 1, 2.5, 13, '#ffffff', 1.3);                        // заливка
  if (warm > 0) lamp(4, 1.4, 6, 0.4, 6, '#ff6d2e', warm);          // отражатель в фирменном цвете (фаза 1) — бронза на крышках
  else lamp(4, 1.4, 6, 0.4, 6, '#e9edf2', opts.low ?? 0.55);      // фаза 2: низкий нейтральный отражатель — крышки «видят» светлое снизу
  lamp(16, 16, 0, -3, 0, '#1a1b1e', 1.0, [0, 1, 0]);              // отскок пола
  return s;
}
// v3 «скан»: холоднее и контрастнее — медь и сталь начинки ловят полосы, белый корпус не «плывёт»
export function studioScan() {
  const { s, lamp } = studioBase([0.02, 0.022, 0.028], [0.03, 0.034, 0.045], [0.01, 0.011, 0.016]);
  lamp(8, 6, -1, 11, 2, '#f4f7ff', 4.5);
  lamp(0.8, 10, -8.5, 4, 3, '#ffffff', 9);
  lamp(0.8, 10, 7.5, 4, -5, '#cfe0ff', 8);
  lamp(0.6, 8, -4, 4, -8, '#bcd3ff', 7);
  lamp(14, 0.6, 0, 5.5, 10, '#ffffff', 7);
  lamp(10, 4, 1, 2.0, 12, '#ffffff', 0.9);
  lamp(3, 1.2, 5, 0.3, 5, '#ff6d2e', 1.2);
  return s;
}
