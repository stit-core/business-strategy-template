/* fonarik.js — «фонарик инженера» (15-showcase «Сдано», вариант C, ветка L1).
   Переосвещение готового кадра Blender по его же проходам: альбедо, нормали в пространстве камеры, высота точки над полом
   (из прохода глубины) и AO. Сцена гаснет до полумрака, луч фонаря идёт за курсором (телефон — касание и один короткий
   показ при первом появлении плана), даёт тени стен и «находит» дефекты: булавка в конусе отмечается в HTML (кольцо,
   подсказка, пункт акта).
   Правила: постер = LCP (<img> кадра B, он же текстура «дня»); WebGL2 — после load в простое; reduce, saveData, без WebGL2 —
   только постер; один контекст; DPR ≤ 2 (телефон ≤ 1,5); кадры только по требованию — 0 кадров в покое.
   Модель: орто-изометрия (az −45°, el 35,264°), экранные оси (u, w) в метрах: P = u·R + w·U + s·F, s = (0,8165·w − h)/0,57735.
   Фонарь — точка на постоянной высоте 2,6 м, смещённая от цели на OFF (запад-северо-запад: тени вправо, как у солнца B);
   цель и фонарь сглаживаются в мировых координатах (фонарь — с запаздыванием: тени «качаются», а не прыгают на срезах стен).
   Конус 8°/17° + рассеяние до 38°, спад 1/r². Тень — марш от точки к фонарю в мировых XY по карте высот СВЕРХУ
   (fx-td: мягкий верх и низ первого тела, клетка 2 см; лучи BVH в Blender), полутень по вертикальному зазору, растёт с
   расстоянием. Итог = день·0,12 (полумрак только по макету — бумага остаётся днём) + альбедо·свет фонаря → мягкое плечо
   только на макете. */
const FR = { u0: -4.9, u1: 3.7, w0: -0.6, w1: 8.5 };          // кадр десктопа в экранных осях, м (renders/v2)
const H_OFF = -0.02, H_RANGE = 1.8;                           // высота в канале B карты fx-nh и в fx-td
const TD = { x0: -0.42, y0: -0.42, cell: 0.02, nx: 508, ny: 366 };   // карта сверху (renders/topdown/topdown.json)
const MOB_CROP = [335, 105, 1737, 1863], FULL = [1800, 1905]; // телефонный кадр — вырезка того же рендера
const OFF = [-2.1, 1.1], LAMP_Z = 2.6;                        // фонарь: смещение от цели по плану (м) и высота над полом
// точки самих дефектов (мир, м): 1 — середина трещины; 2 — лента по шву окна на подоконнике 0,87 м; 3 — пол у основания булавки
// (уклон); 4 — розетка на восточной стене спальни, 0,5 м. «Нашёл» = точка внутри конуса 13° (яркое пятно — до 8…17°)
const DEF = { 1: [2.5, 4.25, 0.0], 2: [2.0, 6.42, 0.87], 3: [3.25, 3.4167, 0.0], 4: [9.233, 4.6667, 0.5] };
const TIPS = { 1: 'Трещина в стяжке', 2: 'Продувает окно', 3: 'Уклон пола 9 мм', 4: 'Розетка без заземления' };
const FOUND_COS = Math.cos(13 * Math.PI / 180);
const Rv = [0.70710678, -0.70710678, 0], Uv = [0.40824829, 0.40824829, 0.81649658], Fv = [0.57735027, 0.57735027, -0.57735027];
// показ на телефоне (один раз, 2,24 с = 4 × база 560 мс): окно (2) → трещина (1) → уклон (3), с 1,64 с свет возвращается за 0,6 с
const TOUR = [[2, 0], [1, 0.75], [3, 1.3]], TOUR_MS = 1640;

const VS = `#version 300 es
out vec2 vUv;
void main() { vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));   /* треугольник на весь кадр */
  vUv = vec2(p.x, 1.0 - p.y); gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0); }`;

const FS = `#version 300 es
precision highp float;
uniform sampler2D uPoster, uAlb, uNH, uAO, uTD;
uniform vec4 uCrop; uniform vec3 uT, uL; uniform float uDark, uPower; uniform int uDbg;
in vec2 vUv; out vec4 o;
const vec3 R = vec3(0.70710678, -0.70710678, 0.0), U = vec3(0.40824829, 0.40824829, 0.81649658), F = vec3(0.57735027, 0.57735027, -0.57735027);
const vec4 FR = vec4(${FR.u0.toFixed(3)}, ${FR.u1.toFixed(3)}, ${FR.w0.toFixed(3)}, ${FR.w1.toFixed(3)});
const float HO = ${H_OFF.toFixed(3)}, HR = ${H_RANGE.toFixed(3)};
const vec4 TD = vec4(${TD.x0.toFixed(3)}, ${TD.y0.toFixed(3)}, ${(1 / (TD.nx * TD.cell)).toFixed(6)}, ${(1 / (TD.ny * TD.cell)).toFixed(6)});
vec3 s2l(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 l2s(vec3 c) { c = max(c, 0.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }
vec3 world(vec2 uv, float h) { float u = FR.x + uv.x * (FR.y - FR.x), w = FR.w - uv.y * (FR.w - FR.z);
  return u * R + w * U + ((0.81649658 * w - h) / 0.57735027) * F; }
vec4 nhN(vec2 uv) { ivec2 sz = textureSize(uNH, 0); return texelFetch(uNH, clamp(ivec2(uv * vec2(sz)), ivec2(0), sz - 1), 0); }
vec3 shoulder(vec3 c) { float pk = max(c.r, max(c.g, c.b)); const float s = 0.76, d = 0.24;
  if (pk < s) return c; float np = 1.0 - d * d / (pk + d - s); c *= np / pk; float g = 1.0 - 1.0 / (0.15 * (pk - np) + 1.0); return mix(c, vec3(np), g); }
/* тень: от точки к фонарю в мировых XY по карте сверху (R — мягкий верх стоящих тел, G/B — низ/верх парящих, вне их —
   пустой интервал); постоянное число шагов (80: ≤ 2,2 см по плану) — точки луча скользят непрерывно вместе с приёмником;
   наименьший зазор по вертикали → полутень ширины 2 см + 6 % расстояния (контактные тени резкие, дальние мягче) */
float shadowTD(vec3 P0, vec3 Lp) {
  vec3 D = Lp - P0;
  float tm = clamp((1.8 - P0.z) / max(D.z, 1e-3), 0.0, 1.0);          /* выше 1,8 м заслонять нечему (каска 1,77) */
  float dl = length(D), res = 1.0;
  for (int i = 1; i <= 80; i++) {
    float t = tm * float(i) / 80.0;
    vec3 Q = P0 + D * t;
    vec3 m = texture(uTD, (Q.xy - TD.xy) * TD.zw).rgb * HR + HO;    /* R — верх стоящих, G/B — низ/верх парящих */
    float c = min(Q.z - m.r, max(m.g - Q.z, Q.z - m.b));             /* зазор; < 0 — луч внутри тела */
    res = min(res, c / (0.02 + 0.06 * dl * t));
    if (res < -1.0) break;
  }
  return smoothstep(-1.0, 1.0, res);
}
void main() {
  vec3 poster = texture(uPoster, vUv).rgb;
  if (uDark <= 0.0005) { o = vec4(poster, 1.0); return; }
  vec2 uf = uCrop.xy + vUv * uCrop.zw;
  vec4 nh = nhN(uf);                                         /* приёмник — ближайший тексель: без «висящих» точек на силуэтах */
  vec3 alb = s2l(texture(uAlb, uf).rgb); float ao = texture(uAO, uf).r;
  vec2 nxy = nh.rg * 2.0 - 1.0;
  vec3 N = normalize(nxy.x * R + nxy.y * U - sqrt(max(0.0, 1.0 - dot(nxy, nxy))) * F);
  float h = nh.b * HR + HO;
  vec3 P = world(uf, h);
  vec3 Ld = uL - P; float dist = length(Ld); vec3 L = Ld / dist;
  float ct = dot(-L, normalize(uT - uL));
  float core = smoothstep(0.9563, 0.9903, ct);
  float cone = core + 0.06 * smoothstep(0.788, 0.9563, ct);
  float ndl = max(dot(N, L), 0.0);
  float sh = 1.0;
  if (core * ndl > 0.002) sh = shadowTD(P + N * 0.07, uL);   /* 7 см от поверхности: дальше «ореола» мягкой карты */
  sh = mix(1.0, sh, clamp(core * 12.0, 0.0, 1.0));            /* рассеяние за краем конуса — без тени */
  if (uDbg == 1) { o = vec4(vec3(sh), 1.0); return; }
  if (uDbg == 2) { o = vec4(vec3(ndl * cone), 1.0); return; }
  if (uDbg == 3) { o = vec4(vec3(clamp(h / 1.8, 0.0, 1.0)), 1.0); return; }
  if (uDbg == 4) { float tp = texture(uTD, (P.xy - TD.xy) * TD.zw).r * HR + HO; o = vec4(vec3(clamp(0.5 + (tp - h) * 2.0, 0.0, 1.0)), 1.0); return; }
  float fall = dot(uT - uL, uT - uL) / (dist * dist);
  vec3 E = vec3(1.0, 0.93, 0.82) * uPower * cone * ndl * fall * sh;
  float red = smoothstep(0.18, 0.40, alb.r - max(alb.g, alb.b));
  vec3 day = s2l(poster);
  float model = smoothstep(-0.016, -0.008, h);                 /* бумага (h = −0,02) — это страница: она остаётся днём */
  float dk = uDark * model;
  vec3 lit = day * (1.0 - 0.88 * dk) * mix(vec3(1.0), vec3(0.78, 0.85, 1.05), dk)
           + alb * E * (1.0 + 0.9 * red) * mix(1.0, ao, 0.4)
           + alb * (0.10 * uPower * cone * fall) * ao * vec3(1.0, 0.93, 0.82) * model      /* отражённый свет в пятне, AO */
           + day * red * (1.0 - smoothstep(0.02, 0.06, abs(h - 0.34))) * 0.8 * dk;          /* лазерная линия светится и в темноте */
  o = vec4(l2s(mix(lit, shoulder(lit), dk)), 1.0);             /* плечо — только на макете: белая бумага остаётся #fff */
}`;

const q = (s, r = document) => r.querySelector(s);
const fig = q('.plan--iso'), stage = q('.plan__stage'), cvs = q('.plan__fx'), img = q('.plan__img'), hint = q('.plan__hint');
const RM = matchMedia('(prefers-reduced-motion: reduce)'), MOB = matchMedia('(max-width: 60rem)');
const saveData = !!(navigator.connection && navigator.connection.saveData);
const T0 = performance.now();
window.__info = { variant: 'C fonarik', mode: 'poster' };

function world(uv, h) {
  const u = FR.u0 + uv[0] * (FR.u1 - FR.u0), w = FR.w1 - uv[1] * (FR.w1 - FR.w0), s = (0.81649658 * w - h) / 0.57735027;
  return [0, 1, 2].map(i => u * Rv[i] + w * Uv[i] + s * Fv[i]);
}
const norm = v => { const l = Math.hypot(...v) || 1; return v.map(x => x / l); };
const toUV = p => [((p[0] - p[1]) * 0.70710678 - FR.u0) / (FR.u1 - FR.u0), (FR.w1 - ((p[0] + p[1]) * 0.40824829 + p[2] * 0.81649658)) / (FR.w1 - FR.w0)];

if (fig && stage && cvs && img) {
  if (RM.matches || saveData) {
    window.__info.reason = RM.matches ? 'reduce' : 'saveData'; window.__ready = true;
  } else {
    const go = () => (window.requestIdleCallback ? requestIdleCallback(init, { timeout: 2000 }) : setTimeout(init, 300));
    if (document.readyState === 'complete') go(); else addEventListener('load', go, { once: true });
  }
}

async function bitmap(url) {
  const r = await fetch(url); const b = await r.blob();
  return createImageBitmap(b, { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
}

async function init() {
  const gl = cvs.getContext('webgl2', { alpha: false, antialias: false, depth: false, stencil: false,
    preserveDrawingBuffer: false, powerPreference: 'low-power' });
  if (!gl) { window.__info.reason = 'no-webgl2'; window.__ready = true; return; }
  const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o);
    if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(o)); return o; };
  const pr = gl.createProgram();
  gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
  if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(pr));
  gl.useProgram(pr);
  const U = n => gl.getUniformLocation(pr, n);
  const un = { crop: U('uCrop'), T: U('uT'), L: U('uL'), dark: U('uDark'), power: U('uPower'), dbg: U('uDbg') };
  ['uPoster', 'uAlb', 'uNH', 'uAO', 'uTD'].forEach((n, i) => gl.uniform1i(U(n), i));
  gl.uniform1f(un.power, 2.1);
  gl.bindVertexArray(gl.createVertexArray());
  const tex = (unit, mip) => { const t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, mip ? gl.LINEAR_MIPMAP_LINEAR : gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return t; };
  const tP = tex(0, true), tA = tex(1, false), tN = tex(2, false), tO = tex(3, false), tT = tex(4, false);
  let posterSrc = '';
  const upPoster = () => {
    if (!img.complete || !img.naturalWidth || img.currentSrc === posterSrc) return;
    posterSrc = img.currentSrc;
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tP);
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.BROWSER_DEFAULT_WEBGL);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, img); gl.generateMipmap(gl.TEXTURE_2D);
  };
  await img.decode().catch(() => {});
  upPoster();
  const [bA, bN, bO, bT] = await Promise.all(['albedo', 'nh', 'ao', 'td'].map(n => bitmap(`assets/fx-${n}.webp`)));
  gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
  [[1, tA, bA], [2, tN, bN], [3, tO, bO], [4, tT, bT]].forEach(([u, t, b]) => {
    gl.activeTexture(gl.TEXTURE0 + u); gl.bindTexture(gl.TEXTURE_2D, t); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, b); });
  // высоты на CPU — для цели луча и проверки «нашёл» (канал B карты fx-nh, 900 × 952)
  const hc = document.createElement('canvas'); hc.width = bN.width; hc.height = bN.height;
  const hx = hc.getContext('2d', { willReadFrequently: true }); hx.drawImage(bN, 0, 0);
  const hd = hx.getImageData(0, 0, hc.width, hc.height).data, HW = hc.width, HH = hc.height;
  const hAt = uv => { const x = Math.min(HW - 1, Math.max(0, uv[0] * HW | 0)), y = Math.min(HH - 1, Math.max(0, uv[1] * HH | 0));
    return hd[(y * HW + x) * 4 + 2] / 255 * H_RANGE + H_OFF; };
  img.addEventListener('load', () => { upPoster(); request(); });

  // ---- состояние: dark 0…1 (полумрак); цель луча aim (uv кадра десктопа) → T (мир, сглажено) → фонарь Lp (мир, с запаздыванием)
  let dark = 0, darkTo = 0, on = false, raf = 0, last = 0, first = true, vis = true, idleT = 0, tour = null, toured = false;
  const aim = [0.45, 0.55], T = [0, 0, 0], Lp = [0, 0, LAMP_Z];
  const found = new Set(); let lit = 0;
  const crop = () => MOB.matches ? [MOB_CROP[0] / FULL[0], MOB_CROP[1] / FULL[1], (MOB_CROP[2] - MOB_CROP[0]) / FULL[0], (MOB_CROP[3] - MOB_CROP[1]) / FULL[1]] : [0, 0, 1, 1];
  const resize = () => { const d = Math.min(devicePixelRatio || 1, MOB.matches ? 1.5 : 2), r = stage.getBoundingClientRect();
    const w = Math.round(r.width * d), h = Math.round(r.height * d);
    if (cvs.width !== w || cvs.height !== h) { cvs.width = w; cvs.height = h; } };
  const toFull = (cx, cy) => { const r = stage.getBoundingClientRect(), c = crop();
    return [c[0] + (cx - r.left) / r.width * c[2], c[1] + (cy - r.top) / r.height * c[3]]; };
  const target = () => world(aim, hAt(aim));
  const snap = () => { const t = target(); for (let i = 0; i < 3; i++) T[i] = t[i]; Lp[0] = T[0] + OFF[0]; Lp[1] = T[1] + OFF[1]; Lp[2] = LAMP_Z; };
  const draw = () => {
    resize(); upPoster();
    gl.viewport(0, 0, cvs.width, cvs.height);
    gl.uniform4fv(un.crop, crop()); gl.uniform3fv(un.T, T); gl.uniform3fv(un.L, Lp);
    gl.uniform1f(un.dark, dark * dark * (3 - 2 * dark));
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    if (first) { first = false; performance.mark('hero-first-frame');
      console.warn('SD timing', { firstFrameMs: Math.round(performance.now() - T0), canvas: [cvs.width, cvs.height] }); }
  };
  const pins = [...stage.querySelectorAll('.pin')], items = [...document.querySelectorAll('.plan__list li')];
  const setHint = () => { if (!hint) return; const n = found.size;
    if (MOB.matches && lit) { hint.textContent = `${lit} · ${TIPS[lit]} — найдено ${n} из 4`; return; }
    hint.textContent = n === 0 ? hint.dataset.idle : n < 4 ? `Найдено ${n} из 4 — ${MOB.matches ? 'коснитесь плана, чтобы найти остальные' : 'ищите дальше'}`
      : 'Все 4 пункта первой страницы акта найдены'; };
  const check = () => {
    const D = norm(T.map((v, i) => v - Lp[i])); let best = 0, bc = FOUND_COS, add = false;
    for (const [k, H] of Object.entries(DEF)) {
      const v = norm(H.map((x, i) => x - Lp[i])), c = v[0] * D[0] + v[1] * D[1] + v[2] * D[2];
      if (dark > 0.6 && c > FOUND_COS) {
        if (c > bc) { bc = c; best = +k; }
        if (!found.has(k)) { found.add(k); add = true; const el = pins.find(p => p.dataset.d === k); el && el.classList.add('is-found');
          items.filter(li => li.dataset.d === k).forEach(li => li.classList.add('is-found')); }
      }
    }
    if (best !== lit) { lit = best; pins.forEach(p => p.classList.toggle('is-lit', +p.dataset.d === best)); add = true; }
    if (add) setHint();
  };
  const tick = ts => {
    const dt = Math.min(0.05, last ? (ts - last) / 1000 : 0.016); last = ts;
    if (tour) tourStep(ts);
    const k1 = 1 - Math.exp(-14 * dt), k2 = 1 - Math.exp(-7 * dt), t = target();
    for (let i = 0; i < 3; i++) T[i] += (t[i] - T[i]) * k1;
    Lp[0] += (T[0] + OFF[0] - Lp[0]) * k2; Lp[1] += (T[1] + OFF[1] - Lp[1]) * k2; Lp[2] = LAMP_Z;
    const sp = darkTo > dark ? dt / 0.45 : dt / 0.6; dark = darkTo > dark ? Math.min(darkTo, dark + sp) : Math.max(darkTo, dark - sp);
    draw(); check();
    const r = stage.getBoundingClientRect(), a = toUV(T), g = toUV([Lp[0] - OFF[0], Lp[1] - OFF[1], T[2]]);
    const px = Math.hypot((aim[0] - a[0]) * r.width, (aim[1] - a[1]) * r.height) + Math.hypot((a[0] - g[0]) * r.width, (a[1] - g[1]) * r.height);
    if (!tour && dark === darkTo && px < 0.5) { raf = 0; last = 0;
      if (dark === 0) { on = false; fig.classList.remove('is-dark', 'fx-on'); pins.forEach(p => p.classList.remove('is-lit')); lit = 0; setHint(); } return; }
    raf = requestAnimationFrame(tick);
  };
  const request = () => { if (!raf && vis) raf = requestAnimationFrame(tick); };
  const startUV = p => {
    aim[0] = p[0]; aim[1] = p[1];
    if (!on) { on = true; snap(); dark = 0; draw(); fig.classList.add('fx-on'); }
    darkTo = 1; fig.classList.add('is-dark'); request();
  };
  const start = (x, y) => { tour = null; startUV(toFull(x, y)); };
  const stop = () => { tour = null; darkTo = 0; fig.classList.remove('is-dark'); request(); };
  // показ на телефоне: цель идёт по точкам дефектов TOUR, потом свет возвращается (один раз за визит, только по видимости)
  const defUV = k => toUV(DEF[k]);
  const tourStep = ts => {
    if (tour.t0 == null) tour.t0 = ts;
    const e = (ts - tour.t0) / 1000;
    let k = 0; while (k < TOUR.length - 1 && e >= TOUR[k + 1][1]) k++;
    const p = defUV(TOUR[k][0]); aim[0] = p[0]; aim[1] = p[1];
    if (e * 1000 >= TOUR_MS) { tour = null; darkTo = 0; fig.classList.remove('is-dark'); }
  };
  const runTour = () => { if (toured || on || RM.matches) return; toured = true;
    const p = defUV(TOUR[0][0]); startUV(p); tour = { t0: null }; };
  stage.addEventListener('pointermove', e => { if (e.pointerType === 'mouse' || e.pointerType === 'pen' || (on && !tour)) start(e.clientX, e.clientY); });
  stage.addEventListener('pointerleave', e => { if (e.pointerType !== 'touch') stop(); });
  stage.addEventListener('pointerdown', e => { if (e.pointerType === 'touch') { toured = true; start(e.clientX, e.clientY);
    clearTimeout(idleT); idleT = setTimeout(stop, 9000); } });
  document.addEventListener('pointerdown', e => { if (on && e.pointerType === 'touch' && !stage.contains(e.target)) stop(); });
  new IntersectionObserver(es => { vis = es[0].isIntersecting;
    if (!vis && on) { cancelAnimationFrame(raf); raf = 0; last = 0; dark = darkTo = 0; on = false; tour = null;
      fig.classList.remove('is-dark', 'fx-on'); pins.forEach(p => p.classList.remove('is-lit')); lit = 0; setHint(); } }).observe(stage);
  if (MOB.matches && matchMedia('(hover: none)').matches) {
    // показ — только после прокрутки посетителя (план ≥ 70 % в кадре): первый экран при загрузке неподвижен (ворота L1:
    // движение на 6-й секунде), и показ не запускается, пока человек его не видит
    const in70 = () => { const r = stage.getBoundingClientRect(); return (Math.min(innerHeight, r.bottom) - Math.max(0, r.top)) / r.height >= 0.7; };
    const onScroll = () => { if (scrollY > 40 && in70()) { removeEventListener('scroll', onScroll); setTimeout(() => { if (in70()) runTour(); }, 350); } };
    addEventListener('scroll', onScroll, { passive: true });
  }
  new ResizeObserver(() => { if (on) request(); }).observe(stage);
  if (hint) { hint.dataset.idle = MOB.matches ? 'Коснитесь плана — фонарь инженера найдёт дефекты' : hint.textContent; hint.textContent = hint.dataset.idle; }
  fig.classList.add('fx-ready');
  window.__info = { variant: 'C fonarik', mode: 'webgl2', kb_textures: null, dpr_cap: MOB.matches ? 1.5 : 2 };
  window.__ready = true;
  // замер для fx_probe: n кадров полумрака с лучом по кругу, синхронизация readPixels 1 px; мс/кадр
  window.__bench = n => {
    const was = { dark, on }; on = true; dark = 1; const px = new Uint8Array(4); const t = [];
    for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2; aim[0] = 0.45 + 0.2 * Math.cos(a); aim[1] = 0.5 + 0.2 * Math.sin(a); snap();
      const t0 = performance.now(); draw();
      gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); t.push(performance.now() - t0); }
    t.sort((x, y) => x - y); dark = was.dark; on = was.on; draw();
    return { frames: n, ms_mean: +(t.reduce((s, x) => s + x, 0) / n).toFixed(2), ms_p50: +t[n >> 1].toFixed(2), ms_p95: +t[Math.floor(n * 0.95)].toFixed(2),
      canvas: [cvs.width, cvs.height] };
  };
  // для кадров судьи и снимков: window.__fonarik.aim(x, y) в долях stage, .off(), .tour()
  window.__fonarik = { aim: (fx, fy) => { const r = stage.getBoundingClientRect(); start(r.left + fx * r.width, r.top + fy * r.height); },
    off: stop, tour: () => { toured = false; runTour(); }, state: () => ({ dark, on, found: [...found], lit, T: [...T], L: [...Lp], tour: !!tour }),
    frame: () => { draw(); }, debug: n => { gl.uniform1i(un.dbg, n | 0); draw(); } };
}
