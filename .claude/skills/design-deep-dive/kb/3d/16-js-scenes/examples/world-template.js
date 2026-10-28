/* Шаблон длинной сцены-мира: закреплённая сцена на всю ширину страницы, где много объектов движется одновременно.
   WebGL2 без библиотек: процедурный квартал из инстансов коробок (≈ 800 домов — один вызов), улицы и бегущие по ним импульсы
   считает шейдер земли (ни одного объекта в JS за кадр), путь камеры — монотонные кубики по ключам прокрутки, мир в мире —
   тот же квартал в масштабе 1 : 16 в центре площади; HDR-кадр → свечение (1/4 … 1/64) → тон Khronos PBR Neutral → sRGB.
   Контракт — как у scene-template.js: регистрация в window.STAGE_SCENES, рантайм stage-runtime.js (режим beats) зовёт
   setVisible, scrub, setIdle, setPlaying, setTexture, destroy; стенд — setTime, setHover, tap, pulse, redraw, info.

   Сюжет на 5 тактов (точки покоя p; у разметки data-beats="0,0.25,0.5,0.75,1"):
     0 — орбита над кварталом (кадр-постер) · 0,25 — дома поднялись волной от центра · 0,5 — пролёт вдоль улицы к площади ·
     0,75 — над площадью, в ней виден такой же квартал · 1 — внутри малого квартала: кадр повторяет заставку (покой с 0,92).
   Нормы: крупные формы движутся только прокруткой; своя жизнь — импульсы по улицам (мелкие, периоды 3–7 с на линию, без
   общей фазы); вспышек нет, касание — одна волна, не чаще 3 раз в секунду; тихая колонка текста у начала строки (ПК) и
   полосы сверху/снизу (телефон); края кадра — в фон места; плотность ≤ 2 под бюджетом 4,6 / 1,9 МП, множитель 0,7…1.
   Импульсы и окна фильтруются по следу пикселя: вдали они уходят к средней яркости, а не мерцают.
   Цена на Iris Xe (redraw + readPixels): 4,2–5,5 мс при 1440 × 760 DPR 2 (4,4 МП), 2,5–3,3 мс при 390 × 600 DPR 2 (0,94 МП);
   вызовов отрисовки ≈ 16 за кадр (небо, 2 уровня × земля и дома, 5 + 4 прохода свечения, сведение). */
(window.STAGE_SCENES = window.STAGE_SCENES || {})['world'] = function (canvas, opts) {
  'use strict';
  opts = opts || {};
  function status(code, log) { if (opts.onStatus) { opts.onStatus(code, log); } }
  var gl = null;
  try {
    gl = canvas.getContext('webgl2', { antialias: false, alpha: false, depth: false, stencil: false, premultipliedAlpha: false,
      preserveDrawingBuffer: !!opts.preserve, powerPreference: 'high-performance' });
  } catch (e) { gl = null; }
  if (!gl) { status('no-webgl'); return null; }
  var HDR = !!gl.getExtension('EXT_color_buffer_float');
  var SITE = !!opts.variant, MOB = !!opts.mobile, RTL = !!opts.rtl;

  // ---------- цвет ----------
  var PAL = { bg: '#16181D', haze: '#2B3340', street: '#4A6684', pulse: '#F4DDB8', light: '#EBD8B8', roof: '#23272F', facade: '#2E3440' };
  Object.keys(opts.palette || {}).forEach(function (k) { PAL[k] = opts.palette[k]; });
  function srgbToLin(c) { return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
  function hexLin(h) { var n = parseInt(String(h).replace('#', ''), 16); return [srgbToLin(((n >> 16) & 255) / 255), srgbToLin(((n >> 8) & 255) / 255), srgbToLin((n & 255) / 255)]; }
  function preTone(h) {
    var c = hexLin(h), m = Math.min(c[0], c[1], c[2]), off = 0.04;
    if (m < 0.04) { var x = Math.sqrt(m / 6.25); off = x - m; if (x >= 0.08) { off = 0.04; } }
    return [c[0] + off, c[1] + off, c[2] + off];
  }
  function g3(a) { return 'vec3(' + a.map(function (x) { return x.toFixed(6); }).join(', ') + ')'; }
  var BG = preTone(opts.background || PAL.bg), BGL = hexLin(opts.background || PAL.bg);
  function clamp(x, a, b) { return x < a ? a : (x > b ? b : x); }
  function smooth(a, b, x) { var t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); }
  function mix(a, b, t) { return a + (b - a) * t; }

  // ---------- мир: детерминированный план — тот же квартал при каждом запуске (постеры и раскадровки совпадают) ----------
  function rng(seed) { var s = seed >>> 0; return function () { s = (s + 0x6D2B79F5) >>> 0; var t = Math.imul(s ^ (s >>> 15), s | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  var R = rng(20261028), G = 18, SUB = 1 / 16, WAVE_V = 4.0, WAVE_T = 3.5;
  var BLD = [];
  for (var i = -G; i <= G; i += 1) {
    for (var j = -G; j <= G; j += 1) {
      if (Math.abs(i) <= 1 && Math.abs(j) <= 1) { continue; }                                   // площадь
      var r = Math.hypot(i, j), edge = G - 1.5 + 1.2 * Math.sin(Math.atan2(j, i) * 3 + 1.1);
      if (r > edge || R() < 0.08) { continue; }                                                // неровный край и скверы
      var down = 1 - smooth(2, 15, r);
      var H = 0.12 + 0.22 * R() + down * (0.35 + 1.6 * Math.pow(R(), 1.6));
      BLD.push(i, j, 0.30 + 0.08 * R(), 0.30 + 0.08 * R(), H, R(), 0.6 * smooth(1.5, G, r) + 0.1 * R(), 0);
    }
  }
  var NB = BLD.length / 8;

  // ---------- шейдеры ----------
  var COMMON = ['#version 300 es', 'precision highp float;',
    'uniform mat4 uVP; uniform vec3 uCam; uniform vec4 uLevel; uniform float uTime; uniform vec3 uBg; uniform float uK;',
    'uniform vec4 uQA; uniform vec4 uQB; uniform vec2 uVp;',
    'const vec3 HAZE = ' + g3(hexLin(PAL.haze)) + '; const vec3 STREET = ' + g3(hexLin(PAL.street)) + ';',
    'const vec3 PULSE = ' + g3(hexLin(PAL.pulse)) + '; const vec3 LIGHT = ' + g3(hexLin(PAL.light)) + ';',
    'const vec3 ROOF = ' + g3(hexLin(PAL.roof)) + '; const vec3 FACADE = ' + g3(hexLin(PAL.facade)) + ';',
    // дымка — в единицах уровня: малый квартал в дымке так же, как большой
    'float fogF(vec3 w){ float d = length(w - uCam)/uLevel.w; return 1.0 - exp(-d*0.045); }',
    'float quietK(vec2 uv){',
    '  float x = mix(uv.x, 1.0 - uv.x, uQA.w), q = uQA.z*(1.0 - smoothstep(uQA.x, uQA.y, x));',
    '  q = max(q, uQB.z*(1.0 - smoothstep(uQB.x - 0.12, uQB.x, uv.y)));',
    '  return max(q, uQB.w*smoothstep(1.0 - uQB.y, 1.0 - uQB.y + 0.12, uv.y));',
    '}',
    // точный ящичный фильтр полосы ширины w пикселем шириной fw и периодической решётки таких полос
    'float band(float d, float w, float fw){ fw = max(fw, 1e-5); return max(0.0, min(d + 0.5*w, 0.5*fw) - max(d - 0.5*w, -0.5*fw))/fw; }',
    'float pI(float x, float T, float w){ float k = floor(x/T + 0.5); return k*w + clamp(x - k*T + 0.5*w, 0.0, w); }',
    'float pulses(float x, float T, float w, float fw){ fw = max(fw, 1e-5); return (pI(x + 0.5*fw, T, w) - pI(x - 0.5*fw, T, w))/fw; }',
    'float h1(float n){ return fract(sin(n*127.1 + 311.7)*43758.5453); }',
    'float h2(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7)))*43758.5453); }'
  ].join('\n');
  var VS_FULL = '#version 300 es\nin vec2 aP;\nout vec2 vUv;\nvoid main(){ vUv = aP*0.5 + 0.5; gl_Position = vec4(aP, 0.0, 1.0); }';
  var FS_SKY = [COMMON,
    'in vec2 vUv; out vec4 o; uniform vec3 uR, uU, uF; uniform vec2 uKf, uShift;',
    'void main(){',
    '  vec2 n = vUv*2.0 - 1.0 - uShift;',
    '  vec3 rd = normalize(uF + uR*n.x*uKf.x + uU*n.y*uKf.y);',
    '  float e = max(rd.y, 0.0);',
    '  vec3 c = uBg + HAZE*0.35*exp(-e*9.0) + STREET*0.05*exp(-e*30.0);',      // дымка у горизонта, тонкая полоса света
    '  o = vec4(c, 1.0);',
    '}'].join('\n');
  // земля: улицы по полуцелым линиям (каждая 4-я — главная), импульсы данных бегут по линиям — всё считает шейдер
  var VS_GROUND = [COMMON, 'in vec2 aP; uniform float uHalf; out vec2 vL; out vec3 vW;',
    'void main(){ vL = aP*uHalf; vW = uLevel.xyz + vec3(vL.x, 0.0, vL.y)*uLevel.w; gl_Position = uVP*vec4(vW, 1.0); }'].join('\n');
  var FS_GROUND = [COMMON,
    'in vec2 vL; in vec3 vW; out vec4 o; uniform float uClip, uFlow; uniform vec4 uCursor; uniform vec4 uWave[3];',
    'void main(){',
    '  if (max(abs(vL.x), abs(vL.y)) > uClip) { discard; }',
    '  vec2 fw = fwidth(vL), q = vL - 0.5, k = floor(q + 0.5), d = q - k;',
    '  vec2 major = vec2(mod(k.x, 4.0) < 0.5 ? 1.0 : 0.0, mod(k.y, 4.0) < 0.5 ? 1.0 : 0.0);',
    '  vec2 w = mix(vec2(0.05), vec2(0.12), major);',
    // покрытие линии; когда пиксель шире линии в разы — к средней яркости (ни муара, ни дрожи вдали)
    '  float lx = mix(band(d.x, w.x, fw.x), w.x, smoothstep(0.25, 0.6, fw.x)), lz = mix(band(d.y, w.y, fw.y), w.y, smoothstep(0.25, 0.6, fw.y));',
    '  float line = max(lx, lz);',
    // импульсы: у каждой линии своя скорость, период и направление (без общей фазы — нет ведущей частоты на кадр)
    '  float pulse = 0.0;',
    '  for (int a = 0; a < 2; a++){',
    '    float id = a == 0 ? k.x : k.y + 101.0, along = a == 0 ? vL.y : vL.x, across = a == 0 ? d.x : d.y;',
    '    float fa = a == 0 ? fw.y : fw.x, fc = a == 0 ? fw.x : fw.y, ww = a == 0 ? w.x : w.y;',
    '    float v = 0.5 + 0.7*h1(id), T = 3.0 + 4.0*h1(id + 7.0), dir = h1(id + 3.0) < 0.5 ? -1.0 : 1.0;',
    '    float b = mod(uTime*v - along*dir + h1(id + 11.0)*T, T), db = min(b, T - b);',
    '    float hr = max(0.05, 1.3*fa), ha = max(ww, 1.2*fc);',
    '    float head = exp(-db*db/(hr*hr))*exp(-across*across/(ha*ha))*(0.05/hr);',            // энергия головы сохраняется вдали
    '    float trail = exp(-b/0.8)*0.35*(a == 0 ? lx : lz);',
    '    pulse += head*6.0 + trail;',
    '  }',
    '  float cu = uCursor.z*exp(-dot(vL - uCursor.xy, vL - uCursor.xy)*uCursor.w);',
    '  float wv = 0.0;',
    '  for (int i = 0; i < 3; i++){ vec4 W = uWave[i]; if (W.w > 0.5){ float rr = length(vL - W.xy) - W.z*' + WAVE_V.toFixed(2) + ';',
    '    wv += exp(-rr*rr/0.05)*exp(-W.z/1.2); } }',
    '  float qk = quietK(gl_FragCoord.xy/uVp);',
    '  vec3 c = uBg*1.15 + HAZE*0.25*exp(-dot(vL, vL)/90.0);',
    '  c += STREET*line*(0.5 + 0.9*max(major.x, major.y))*(1.0 + 3.0*cu)*(1.0 - 0.5*qk);',
    '  c += PULSE*pulse*uFlow*(1.0 + 1.5*cu)*(1.0 - 0.95*qk) + LIGHT*(wv*2.5*line + wv*0.12);',
    '  c = mix(c, uBg, fogF(vW));',
    '  o = vec4(mix(uBg, c, uK), 1.0);',
    '}'].join('\n');
  // дома: инстансы коробок без дна; высота растёт волной по одному uniform (задержка — от центра), окна — фильтр по следу
  var VS_BLD = [COMMON, 'in vec3 aP; in vec3 aN; in vec4 aBox; in vec4 aMeta; uniform float uRise;',
    'out vec3 vW; out vec3 vN; out vec3 vLoc; flat out vec4 vInfo;',
    'void main(){',
    '  float t = clamp((uRise - aMeta.z)/0.3, 0.0, 1.0); t = t*t*(3.0 - 2.0*t);',
    '  float h = mix(0.03, aMeta.x, t);',
    '  vec3 loc = vec3(aBox.x + aP.x*aBox.z, aP.y*h, aBox.y + aP.z*aBox.w);',
    '  vW = uLevel.xyz + loc*uLevel.w; vN = aN; vLoc = loc; vInfo = vec4(h, aMeta.y, t, 0.0);',
    '  gl_Position = uVP*vec4(vW, 1.0);',
    '}'].join('\n');
  var FS_BLD = [COMMON, 'in vec3 vW; in vec3 vN; in vec3 vLoc; flat in vec4 vInfo; out vec4 o; uniform vec4 uCursor;',
    'void main(){',
    '  vec3 n = normalize(vN); float qk = quietK(gl_FragCoord.xy/uVp);',
    '  float cu = uCursor.z*exp(-dot(vLoc.xz - uCursor.xy, vLoc.xz - uCursor.xy)*uCursor.w);',
    '  vec3 c;',
    '  if (n.y > 0.5) { c = ROOF*(0.9 + 0.4*vInfo.y) + LIGHT*0.02*(1.0 - vInfo.z); }',
    '  else {',
    '    float u = abs(n.x) > 0.5 ? vLoc.z : vLoc.x, v = vLoc.y;',
    '    float fu = fwidth(u), fv = fwidth(v);',
    '    float cov = pulses(u, 0.06, 0.03, fu)*pulses(v, 0.08, 0.04, fv)*step(v, vInfo.x - 0.03);',
    '    float lit = step(0.58, h2(floor(vec2(u/0.06, v/0.08) + 0.5) + vInfo.y*17.0));',
    '    lit = mix(lit, 0.42, smoothstep(0.3, 0.8, max(fu/0.06, fv/0.08)));',                 // вдали — средняя доля окон
    '    float sun = 0.55 + 0.45*max(dot(n, normalize(vec3(-0.6, 0.0, 0.8))), 0.0);',
    '    float rim = band(vInfo.x - v, 0.012, fv)*4.0*vInfo.z*(1.0 - vInfo.z);',             // кромка растущего дома
    '    c = FACADE*sun*0.6 + LIGHT*(cov*lit*(1.1 + 2.0*cu)*(1.0 - 0.9*qk) + rim);',
    '  }',
    '  c = mix(c, uBg, fogF(vW));',
    '  o = vec4(mix(uBg, c, uK), 1.0);',
    '}'].join('\n');
  // свечение: вниз (порог на первом шаге) — вверх сложением — сведение: тон, тихая зона, края в фон, sRGB, дизеринг
  var FS_DOWN = ['#version 300 es', 'precision highp float;', 'in vec2 vUv; out vec4 o; uniform sampler2D uSrc; uniform vec2 uTx; uniform float uThr;',
    'void main(){',
    '  vec3 c = 0.25*(texture(uSrc, vUv + uTx*vec2(-1.0, -1.0)).rgb + texture(uSrc, vUv + uTx*vec2(1.0, -1.0)).rgb',
    '         + texture(uSrc, vUv + uTx*vec2(-1.0, 1.0)).rgb + texture(uSrc, vUv + uTx*vec2(1.0, 1.0)).rgb);',
    '  if (uThr > 0.0) { float l = max(c.r, max(c.g, c.b)); c *= max(l - uThr, 0.0)/max(l, 1e-4); }',
    '  o = vec4(min(c, vec3(60.0)), 1.0);',
    '}'].join('\n');
  var FS_UP = ['#version 300 es', 'precision highp float;', 'in vec2 vUv; out vec4 o; uniform sampler2D uSrc; uniform vec2 uTx;',
    'void main(){ vec3 c = 0.25*(texture(uSrc, vUv + uTx*vec2(-0.75, -0.75)).rgb + texture(uSrc, vUv + uTx*vec2(0.75, -0.75)).rgb',
    '  + texture(uSrc, vUv + uTx*vec2(-0.75, 0.75)).rgb + texture(uSrc, vUv + uTx*vec2(0.75, 0.75)).rgb); o = vec4(c*0.85, 1.0); }'].join('\n');
  var FS_COMP = [COMMON, 'in vec2 vUv; out vec4 o; uniform sampler2D uScene, uBloom; uniform vec3 uEdge;',
    'vec3 neutralTone(vec3 c){',
    '  const float sc = 0.76; const float ds = 0.15;',
    '  float x = min(c.r, min(c.g, c.b)); float off = x < 0.08 ? x - 6.25*x*x : 0.04; c -= off;',
    '  float pk = max(c.r, max(c.g, c.b)); if (pk < sc) { return c; }',
    '  const float d = 1.0 - sc; float np = 1.0 - d*d/(pk + d - sc); c *= np/pk;',
    '  float g = 1.0 - 1.0/(ds*(pk - np) + 1.0); return mix(c, vec3(np), g);',
    '}',
    'vec3 oetf(vec3 c){ c = clamp(c, 0.0, 1.0); return mix(c*12.92, 1.055*pow(c, vec3(1.0/2.4)) - 0.055, step(vec3(0.0031308), c)); }',
    'float hash(vec2 p){ p = fract(p*vec2(443.897, 441.423)); p += dot(p, p.yx + 19.19); return fract((p.x + p.y)*p.x); }',
    'void main(){',
    '  float qk = quietK(vUv);',
    '  vec3 sc = texture(uScene, vUv).rgb; float L = dot(sc, vec3(0.2126, 0.7152, 0.0722));',
    '  sc = mix(sc, uBg + (sc - uBg)/(1.0 + 4.0*L), qk);',                                  // тихая зона: яркое сжато, оттенок держится
    '  vec3 c = neutralTone(sc + texture(uBloom, vUv).rgb*0.45*(1.0 - 0.6*qk));',
    '  vec2 e = min(vUv, 1.0 - vUv);',
    '  c = mix(uEdge, c, smoothstep(0.0, 0.07, e.y)*smoothstep(0.0, 0.02, e.x));',            // верх и низ — в фон места
    '  o = vec4(oetf(c) + (hash(gl_FragCoord.xy + fract(uTime)*17.0) - 0.5)/255.0, 1.0);',
    '}'].join('\n');

  // ---------- сборка программ: асинхронно, если есть KHR_parallel_shader_compile ----------
  var khr = gl.getExtension('KHR_parallel_shader_compile');
  var SRC = { sky: [VS_FULL, FS_SKY], ground: [VS_GROUND, FS_GROUND], bld: [VS_BLD, FS_BLD], down: [VS_FULL, FS_DOWN], up: [VS_FULL, FS_UP], comp: [VS_FULL, FS_COMP] };
  var ATTR = { sky: ['aP'], ground: ['aP'], bld: ['aP', 'aN', 'aBox', 'aMeta'], down: ['aP'], up: ['aP'], comp: ['aP'] };
  var P = {};
  Object.keys(SRC).forEach(function (k) {
    var p = gl.createProgram(), vs = gl.createShader(gl.VERTEX_SHADER), fs = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(vs, SRC[k][0]); gl.compileShader(vs); gl.shaderSource(fs, SRC[k][1]); gl.compileShader(fs);
    gl.attachShader(p, vs); gl.attachShader(p, fs);
    ATTR[k].forEach(function (a, i) { gl.bindAttribLocation(p, i, a); });
    gl.linkProgram(p);
    P[k] = { p: p, vs: vs, fs: fs, u: {} };
  });
  function U(pr, n) { if (!(n in pr.u)) { pr.u[n] = gl.getUniformLocation(pr.p, n); } return pr.u[n]; }
  function loseGl() { try { var x = gl.getExtension('WEBGL_lose_context'); if (x) { x.loseContext(); } } catch (err) { /* уже потерян */ } }
  function linked() {
    if (gl.isContextLost()) { return null; }
    var bad = Object.keys(P).filter(function (k) { return !gl.getProgramParameter(P[k].p, gl.LINK_STATUS); })[0];
    if (bad) { status('shader-error', bad + ': ' + (gl.getShaderInfoLog(P[bad].fs) || gl.getShaderInfoLog(P[bad].vs) || gl.getProgramInfoLog(P[bad].p))); return null; }
    return rest();
  }
  if (opts.onReady) {
    var off = false;
    var poll = function () {
      if (off) { return; }
      if (gl.isContextLost()) { opts.onReady(null); return; }
      if (khr && Object.keys(P).some(function (k) { return !gl.getProgramParameter(P[k].p, khr.COMPLETION_STATUS_KHR); })) { setTimeout(poll, 40); return; }
      var h = linked(); if (!h) { loseGl(); } opts.onReady(h);
    };
    setTimeout(poll, 0);
    return { pending: true, destroy: function () { off = true; loseGl(); } };
  }
  return linked();

  function rest() {
    // ---------- буферы: полный кадр, квад земли, коробка дома + инстансы ----------
    function vao(build) { var v = gl.createVertexArray(); gl.bindVertexArray(v); build(); gl.bindVertexArray(null); return v; }
    function buf(data, target) { var b = gl.createBuffer(); gl.bindBuffer(target || gl.ARRAY_BUFFER, b); gl.bufferData(target || gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); return b; }
    var vaoFull = vao(function () { buf(new Float32Array([-1, -1, 3, -1, -1, 3])); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0); });
    var vaoQuad = vao(function () { buf(new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1])); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0); });
    var BOX = [], BIX = [];
    [[1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1], [0, 1, 0]].forEach(function (n) {
      var b = BOX.length / 6, a = n[1] ? [1, 0, 0] : [-n[2], 0, n[0]], u = n[1] ? [0, 0, 1] : [0, 1, 0];
      [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(function (s) {
        var p = [n[0] + a[0] * s[0] + u[0] * s[1], n[1] + a[1] * s[0] + u[1] * s[1], n[2] + a[2] * s[0] + u[2] * s[1]];
        BOX.push(p[0], n[1] ? 1 : (p[1] + 1) / 2, p[2], n[0], n[1], n[2]);
      });
      BIX.push(b, b + 1, b + 2, b + 1, b + 3, b + 2);
    });
    var vaoBld = vao(function () {
      buf(new Float32Array(BOX));
      gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 24, 0);
      gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 24, 12);
      buf(new Uint16Array(BIX), gl.ELEMENT_ARRAY_BUFFER);
      buf(new Float32Array(BLD));
      gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 32, 0); gl.vertexAttribDivisor(2, 1);
      gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 4, gl.FLOAT, false, 32, 16); gl.vertexAttribDivisor(3, 1);
    });

    // ---------- цели: HDR-кадр с глубиной и цепочка свечения 1/4 … 1/64 ----------
    var FMT = HDR ? { i: gl.RGBA16F, t: gl.HALF_FLOAT } : { i: gl.RGBA8, t: gl.UNSIGNED_BYTE };
    function tex(w, h) {
      var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, FMT.i, w, h, 0, gl.RGBA, FMT.t, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      return t;
    }
    var RT = null;
    function freeRT() {
      if (!RT) { return; }
      gl.deleteFramebuffer(RT.fb); gl.deleteTexture(RT.tx); gl.deleteRenderbuffer(RT.db);
      RT.lv.forEach(function (l) { gl.deleteFramebuffer(l.fb); gl.deleteTexture(l.tx); });
      RT = null;
    }
    function makeRT(w, h) {
      freeRT();
      RT = { w: w, h: h, tx: tex(w, h), fb: gl.createFramebuffer(), db: gl.createRenderbuffer(), lv: [] };
      gl.bindRenderbuffer(gl.RENDERBUFFER, RT.db); gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH_COMPONENT24, w, h);
      gl.bindFramebuffer(gl.FRAMEBUFFER, RT.fb);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, RT.tx, 0);
      gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, RT.db);
      var lw = w, lh = h;
      for (var i = 0; i < 5; i += 1) {
        lw = Math.max(1, Math.ceil(lw / (i ? 2 : 4))); lh = Math.max(1, Math.ceil(lh / (i ? 2 : 4)));
        var l = { w: lw, h: lh, tx: tex(lw, lh), fb: gl.createFramebuffer() };
        gl.bindFramebuffer(gl.FRAMEBUFFER, l.fb); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, l.tx, 0);
        RT.lv.push(l);
      }
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    }

    // ---------- путь камеры: ключи [p, глаз x y z, цель x y z, поле зрения°, сдвиг объектива x y], монотонные кубики ----------
    // Высота глаза интерполируется в asinh-пространстве: спуск с орбиты к улице и в малый квартал идёт без излома скорости.
    var O_IN = [0, 0.002, 0];
    var K0 = MOB ? [0, -14, 30, 16, 0, 0, 0, 44, 0, -0.10] : [0, -16, 22, 18, 0, 0, 0, 34, SITE ? 0.30 : 0, 0];
    function inner(k, p) { return [p, O_IN[0] + SUB * k[1], O_IN[1] + SUB * k[2], O_IN[2] + SUB * k[3], O_IN[0] + SUB * k[4], O_IN[1] + SUB * k[5], O_IN[2] + SUB * k[6], k[7], k[8], k[9]]; }
    var KEYS = MOB ? [
      K0,
      [0.25, -9, 12, 10, 0, 0.4, 0, 50, 0, -0.08],
      [0.50, -6.5, 1.0, 0.5, 0, 0.7, 0.5, 64, 0, -0.06],
      [0.75, -0.7, 2.6, 0.7, 0, 0, 0, 56, 0, -0.08],
      inner(K0, 0.92), inner(K0, 1)
    ] : [
      K0,
      [0.25, -9, 9, 10, 0, 0.5, 0, 40, SITE ? 0.28 : 0, 0],
      [0.50, -6.5, 0.9, 0.5, 0, 0.6, 0.5, 52, SITE ? 0.24 : 0, 0],
      [0.75, -0.6, 2.2, 0.6, 0, 0, 0, 46, SITE ? 0.26 : 0, 0],
      inner(K0, 0.92), inner(K0, 1)
    ];
    function tf(ch, v) { return ch === 2 ? Math.asinh(v / 0.5) : v; }
    function itf(ch, v) { return ch === 2 ? Math.sinh(v) * 0.5 : v; }
    var NK = KEYS.length, TAN = [];
    for (var ch = 1; ch < KEYS[0].length; ch += 1) {
      var dd = [], m = [], q;
      for (q = 0; q < NK - 1; q += 1) { dd.push((tf(ch, KEYS[q + 1][ch]) - tf(ch, KEYS[q][ch])) / (KEYS[q + 1][0] - KEYS[q][0])); }
      m.push(dd[0]);
      for (q = 1; q < NK - 1; q += 1) { m.push(dd[q - 1] * dd[q] <= 0 ? 0 : (dd[q - 1] + dd[q]) / 2); }
      m.push(dd[NK - 2]);
      for (q = 0; q < NK - 1; q += 1) {                                                         // Фриче — Карлсон: без перелёта
        if (dd[q] === 0) { m[q] = 0; m[q + 1] = 0; continue; }
        var al = m[q] / dd[q], be = m[q + 1] / dd[q], s2 = al * al + be * be;
        if (s2 > 9) { var tau = 3 / Math.sqrt(s2); m[q] = tau * al * dd[q]; m[q + 1] = tau * be * dd[q]; }
      }
      TAN[ch] = m;
    }
    function chan(ch, p) {
      var k = 0; while (k < NK - 2 && p > KEYS[k + 1][0]) { k += 1; }
      var x0 = KEYS[k][0], hh = KEYS[k + 1][0] - x0, t = clamp((p - x0) / hh, 0, 1), t2 = t * t, t3 = t2 * t;
      var y0 = tf(ch, KEYS[k][ch]), y1 = tf(ch, KEYS[k + 1][ch]);
      return itf(ch, (2 * t3 - 3 * t2 + 1) * y0 + (t3 - 2 * t2 + t) * TAN[ch][k] * hh + (-2 * t3 + 3 * t2) * y1 + (t3 - t2) * TAN[ch][k + 1] * hh);
    }
    function camera(p) {
      var e = [chan(1, p), chan(2, p), chan(3, p)], t = [chan(4, p), chan(5, p), chan(6, p)], fov = chan(7, p), sx = chan(8, p), sy = chan(9, p);
      if (RTL) { e[2] = -e[2]; t[2] = -t[2]; sx = -sx; }                                        // кадр зеркален, мир — нет
      var fx = t[0] - e[0], fy = t[1] - e[1], fz = t[2] - e[2], fl = Math.hypot(fx, fy, fz); fx /= fl; fy /= fl; fz /= fl;
      var rx = -fz, rz = fx, rl = Math.hypot(rx, rz) || 1; rx /= rl; rz /= rl;
      var ux = -rz * fy, uy = rz * fx - rx * fz, uz = rx * fy;
      var asp = st.w / st.h, f = 1 / Math.tan(fov * Math.PI / 360);
      var near = clamp(Math.max(0.002, e[1]) * 0.05, 0.0015, 0.5), far = near * 12000;          // ближняя плоскость — по высоте
      var V = [rx, ux, -fx, 0, 0, uy, -fy, 0, rz, uz, -fz, 0, -(rx * e[0] + rz * e[2]), -(ux * e[0] + uy * e[1] + uz * e[2]), fx * e[0] + fy * e[1] + fz * e[2], 1];
      var Pm = [f / asp, 0, 0, 0, 0, f, 0, 0, -sx, -sy, (far + near) / (near - far), -1, 0, 0, 2 * far * near / (near - far), 0];
      var M = new Float32Array(16);
      for (var c = 0; c < 4; c += 1) { for (var r2 = 0; r2 < 4; r2 += 1) { var s = 0; for (var k = 0; k < 4; k += 1) { s += Pm[k * 4 + r2] * V[c * 4 + k]; } M[c * 4 + r2] = s; } }
      return { e: e, R: [rx, 0, rz], U: [ux, uy, uz], F: [fx, fy, fz], vp: M, asp: asp, f: f, sx: sx, sy: sy };
    }

    // ---------- состояние ----------
    var maxDpr = opts.maxDpr || 2, pxMax = opts.pxMax || (MOB ? 1.9e6 : 4.6e6);
    var st = { time: 0, p: 0, pT: 0, ptr: { x: 0, y: 0, on: false }, hv: { x: 0, y: 0, a: 0 }, waves: [], lastTap: -1e9,
      visible: true, alive: true, idle: opts.idle !== false, userPaused: false, dirty: false, raf: 0, last: 0,
      w: 0, h: 0, dpr: 1, scale: 1, frames: [], draws: 0 };
    var QA = SITE && !MOB ? [0.34, 0.6, 1, RTL ? 1 : 0] : [0, 0, 0, 0];
    // телефон: подписи — нижние 32 % (всегда тише), заставка и финал — верхние 42 % (только на крайних тактах)
    function quietB(p) { return SITE && MOB ? [0.32, 0.42, 0.6, 0.7 * Math.max(1 - smooth(0.03, 0.2, p), smooth(0.86, 0.92, p))] : [0, 0, 0, 0]; }
    function resize() {
      var r = canvas.getBoundingClientRect(), cw = Math.max(1, r.width), ch2 = Math.max(1, r.height);
      var dpr = Math.min(window.devicePixelRatio || 1, maxDpr, Math.sqrt(pxMax / (cw * ch2)));
      dpr = Math.max(0.5, dpr) * st.scale;
      var w = Math.max(1, Math.round(cw * dpr)), h = Math.max(1, Math.round(ch2 * dpr));
      st.dpr = dpr;
      if (w !== st.w || h !== st.h) { canvas.width = w; canvas.height = h; st.w = w; st.h = h; }
      if (!RT || RT.w !== st.w || RT.h !== st.h) { makeRT(st.w, st.h); }
    }
    // курсор и касание: луч → плоскость земли; в малом квартале — в его единицах
    function hitAt(cam, x, y) {
      var nx = x - cam.sx, ny = y - cam.sy;
      var d = [cam.F[0] + (cam.R[0] * nx * cam.asp + cam.U[0] * ny) / cam.f, cam.F[1] + (cam.R[1] * nx * cam.asp + cam.U[1] * ny) / cam.f,
        cam.F[2] + (cam.R[2] * nx * cam.asp + cam.U[2] * ny) / cam.f];
      if (d[1] > -1e-4) { return null; }
      var t = -cam.e[1] / d[1], px = cam.e[0] + d[0] * t, pz = cam.e[2] + d[2] * t;
      var inn = st.p > 0.45 && Math.abs(px) < (G + 1) * SUB && Math.abs(pz) < (G + 1) * SUB;
      return { x: inn ? (px - O_IN[0]) / SUB : px, z: inn ? (pz - O_IN[2]) / SUB : pz, inner: inn, dist: t };
    }

    // ---------- кадр ----------
    function level(pr, cam, lv) {
      gl.useProgram(pr.p);
      gl.uniformMatrix4fv(U(pr, 'uVP'), false, cam.vp);
      gl.uniform3f(U(pr, 'uCam'), cam.e[0], cam.e[1], cam.e[2]);
      gl.uniform4f(U(pr, 'uLevel'), lv.o[0], lv.o[1], lv.o[2], lv.s);
      gl.uniform1f(U(pr, 'uTime'), st.time); gl.uniform3f(U(pr, 'uBg'), BG[0], BG[1], BG[2]); gl.uniform1f(U(pr, 'uK'), lv.k);
      gl.uniform4f(U(pr, 'uQA'), QA[0], QA[1], QA[2], QA[3]); var qb = quietB(st.p); gl.uniform4f(U(pr, 'uQB'), qb[0], qb[1], qb[2], qb[3]);
      gl.uniform2f(U(pr, 'uVp'), st.w, st.h);
      gl.uniform4f(U(pr, 'uCursor'), lv.cur[0], lv.cur[1], lv.cur[2], lv.cur[3]);
    }
    function drawLevel(cam, lv) {
      var pr = P.ground; level(pr, cam, lv);
      gl.uniform1f(U(pr, 'uHalf'), G + 2); gl.uniform1f(U(pr, 'uClip'), lv.clip); gl.uniform1f(U(pr, 'uFlow'), lv.flow);
      gl.uniform4fv(U(pr, 'uWave'), lv.wv);
      gl.bindVertexArray(vaoQuad); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      pr = P.bld; level(pr, cam, lv); gl.uniform1f(U(pr, 'uRise'), lv.rise);
      gl.bindVertexArray(vaoBld); gl.drawElementsInstanced(gl.TRIANGLES, 30, gl.UNSIGNED_SHORT, 0, NB);   // все дома — один вызов
      st.draws += 2;
    }
    function full(pr) { gl.useProgram(pr.p); gl.bindVertexArray(vaoFull); gl.drawArrays(gl.TRIANGLES, 0, 3); }
    function draw() {
      resize();
      var cam = camera(st.p);
      var cur = [0, 0, 0, 1], curIn = [0, 0, 0, 1];
      if (st.hv.a > 0.003) {
        var hit = hitAt(cam, st.hv.x, st.hv.y);
        if (hit) { var rr = 0.06 * hit.dist / (hit.inner ? SUB : 1), cv = [hit.x, hit.z, st.hv.a, 1 / (rr * rr)]; if (hit.inner) { curIn = cv; } else { cur = cv; } }
      }
      var wo = new Float32Array(12), wi = new Float32Array(12);
      st.waves.forEach(function (w, i) { var a = w.inner ? wi : wo; a[i * 4] = w.x; a[i * 4 + 1] = w.z; a[i * 4 + 2] = w.age; a[i * 4 + 3] = 1; });
      var pxW = 2 / (cam.f * st.h), dIn = Math.hypot(cam.e[0] - O_IN[0], cam.e[1] - O_IN[1], cam.e[2] - O_IN[2]);
      // малый квартал, пока он крошечный в кадре, гасит импульсы пропорционально размеру пикселя: квартал, а не белый ком
      var flowIn = clamp(0.03 / Math.max(1e-6, pxW * dIn / SUB), 0.3, 1);
      var outer = { o: [0, 0, 0], s: 1, rise: smooth(0.04, 0.25, st.p), clip: 1e4, k: 1 - smooth(0.8, 0.95, st.p), flow: 1, cur: cur, wv: wo };
      var inn = { o: O_IN, s: SUB, rise: 0, clip: G + 1, k: 1, flow: flowIn, cur: curIn, wv: wi };
      gl.bindFramebuffer(gl.FRAMEBUFFER, RT.fb);
      gl.viewport(0, 0, st.w, st.h);
      gl.disable(gl.BLEND); gl.depthMask(true); gl.clearDepth(1); gl.clear(gl.DEPTH_BUFFER_BIT);
      gl.disable(gl.DEPTH_TEST);
      var pr = P.sky; gl.useProgram(pr.p);
      gl.uniform3f(U(pr, 'uR'), cam.R[0], cam.R[1], cam.R[2]); gl.uniform3f(U(pr, 'uU'), cam.U[0], cam.U[1], cam.U[2]); gl.uniform3f(U(pr, 'uF'), cam.F[0], cam.F[1], cam.F[2]);
      gl.uniform2f(U(pr, 'uKf'), cam.asp / cam.f, 1 / cam.f); gl.uniform2f(U(pr, 'uShift'), cam.sx, cam.sy); gl.uniform3f(U(pr, 'uBg'), BG[0], BG[1], BG[2]);
      full(pr);
      gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.LEQUAL);
      if (outer.k > 0.003) { drawLevel(cam, outer); }
      if (st.p > 0.45) { drawLevel(cam, inn); }                                               // мир в мире: те же буферы, другой масштаб
      gl.disable(gl.DEPTH_TEST);
      var src = RT.tx, sw = RT.w, sh = RT.h;
      pr = P.down;
      RT.lv.forEach(function (l, i) {
        gl.bindFramebuffer(gl.FRAMEBUFFER, l.fb); gl.viewport(0, 0, l.w, l.h); gl.useProgram(pr.p);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, src); gl.uniform1i(U(pr, 'uSrc'), 0);
        gl.uniform2f(U(pr, 'uTx'), (i ? 1 : 1.5) / sw, (i ? 1 : 1.5) / sh); gl.uniform1f(U(pr, 'uThr'), i ? 0 : 0.75);
        full(pr); src = l.tx; sw = l.w; sh = l.h;
      });
      pr = P.up; gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
      for (var i = RT.lv.length - 1; i > 0; i -= 1) {
        var lo = RT.lv[i], hi = RT.lv[i - 1];
        gl.bindFramebuffer(gl.FRAMEBUFFER, hi.fb); gl.viewport(0, 0, hi.w, hi.h); gl.useProgram(pr.p);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, lo.tx); gl.uniform1i(U(pr, 'uSrc'), 0); gl.uniform2f(U(pr, 'uTx'), 1 / lo.w, 1 / lo.h);
        full(pr);
      }
      gl.disable(gl.BLEND);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, st.w, st.h);
      pr = P.comp; gl.useProgram(pr.p);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, RT.tx); gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, RT.lv[0].tx);
      gl.uniform1i(U(pr, 'uScene'), 0); gl.uniform1i(U(pr, 'uBloom'), 1); gl.uniform1f(U(pr, 'uTime'), st.time);
      gl.uniform3f(U(pr, 'uBg'), BG[0], BG[1], BG[2]); gl.uniform3f(U(pr, 'uEdge'), BGL[0], BGL[1], BGL[2]);
      gl.uniform4f(U(pr, 'uQA'), QA[0], QA[1], QA[2], QA[3]); var qb = quietB(st.p); gl.uniform4f(U(pr, 'uQB'), qb[0], qb[1], qb[2], qb[3]);
      full(pr);
      st.draws += 1;
    }

    // ---------- цикл кадров: кадр — когда что-то меняется; только своя жизнь — ≈ 30 кадров/с; вне экрана — 0 ----------
    function running() { return st.alive && st.visible && !document.hidden; }
    function ambient() { return st.idle && !st.userPaused; }
    function settling() {
      return Math.abs(st.pT - st.p) > 1e-4 || st.waves.length > 0 || st.dirty ||
        Math.abs((st.ptr.on ? st.ptr.x : st.hv.x) - st.hv.x) > 0.002 || Math.abs((st.ptr.on ? st.ptr.y : st.hv.y) - st.hv.y) > 0.002 ||
        Math.abs((st.ptr.on ? 1 : 0) - st.hv.a) > 0.002;
    }
    function step(now) {
      st.raf = 0;
      if (!running()) { st.last = 0; return; }
      var busy = settling();
      if (!busy && !ambient()) { st.last = 0; st.frames = []; return; }
      if (!busy && st.last && now - st.last < 31) { st.raf = requestAnimationFrame(step); return; }
      var dt = st.last ? Math.min(0.05, (now - st.last) / 1000) : 1 / 60; st.last = now;
      if (busy) {
        if (st.frames.length >= 40) { st.frames.shift(); } st.frames.push(dt);
        if (st.frames.length >= 40) {
          var md = st.frames.slice().sort(function (a, b) { return a - b; })[20];
          if (md > 0.024 && st.scale > 0.7) { st.scale = Math.max(0.7, st.scale * 0.85); st.frames = []; }
          else if (md < 0.0125 && st.scale < 1) { st.scale = Math.min(1, st.scale / 0.85); st.frames = []; }
        }
      }
      if (ambient()) { st.time += dt; }
      st.p += (st.pT - st.p) * (1 - Math.exp(-dt / 0.12)); if (Math.abs(st.pT - st.p) < 1e-4) { st.p = st.pT; }
      var k = 1 - Math.exp(-dt / 0.35);
      if (st.ptr.on) { st.hv.x += (st.ptr.x - st.hv.x) * k; st.hv.y += (st.ptr.y - st.hv.y) * k; }
      st.hv.a += ((st.ptr.on ? 1 : 0) - st.hv.a) * (1 - Math.exp(-dt / 0.5)); if (Math.abs((st.ptr.on ? 1 : 0) - st.hv.a) < 0.002) { st.hv.a = st.ptr.on ? 1 : 0; }
      st.waves.forEach(function (w) { w.age += dt; }); st.waves = st.waves.filter(function (w) { return w.age < WAVE_T; });
      draw(); st.dirty = false;
      st.raf = requestAnimationFrame(step);
    }
    function kick() { if (!st.raf && running()) { st.last = 0; st.raf = requestAnimationFrame(step); } }
    function change() { if (st.raf) { st.dirty = true; } else { draw(); kick(); } }
    function addWave(x, y) {
      var now = performance.now(); if (now - st.lastTap < 340) { return; } st.lastTap = now;
      var hit = hitAt(camera(st.p), x, y); if (!hit) { return; }
      st.waves.unshift({ x: hit.x, z: hit.z, inner: hit.inner, age: 0 }); st.waves = st.waves.slice(0, 3);
    }

    // ---------- ввод ----------
    function local(e) {
      var r = canvas.getBoundingClientRect();
      return [clamp(((e.clientX - r.left) / r.width) * 2 - 1, -1, 1), clamp(1 - ((e.clientY - r.top) / r.height) * 2, -1, 1)];
    }
    function onMove(e) { if (e.pointerType === 'touch') { return; } var q2 = local(e); st.ptr = { x: q2[0], y: q2[1], on: true }; kick(); }
    function onLeave() { st.ptr.on = false; kick(); }
    var down0 = null;
    function onDown(e) { down0 = { x: e.clientX, y: e.clientY }; }
    function onUp(e) { if (down0 && Math.abs(e.clientX - down0.x) + Math.abs(e.clientY - down0.y) < 6) { var q2 = local(e); addWave(q2[0], q2[1]); kick(); } down0 = null; }
    canvas.style.touchAction = 'pan-y';
    canvas.addEventListener('pointermove', onMove); canvas.addEventListener('pointerleave', onLeave);
    canvas.addEventListener('pointerdown', onDown); canvas.addEventListener('pointerup', onUp);
    var ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(function () { if (!st.raf && st.alive) { draw(); } }) : null;
    if (ro) { ro.observe(canvas); }
    var lost = function (ev) { ev.preventDefault(); st.alive = false; if (st.raf) { cancelAnimationFrame(st.raf); st.raf = 0; } status('context-lost'); };
    canvas.addEventListener('webglcontextlost', lost);

    draw();
    status('ready');
    kick();

    return {
      setVisible: function (v) { st.visible = !!v; if (v) { kick(); } },
      wake: kick,
      scrub: function (p) { st.pT = clamp(p, 0, 1); if (!st.raf) { st.p = st.pT; } change(); },
      setIdle: function (on) { st.userPaused = !on; kick(); },
      setPlaying: function (on) { st.userPaused = !on; kick(); },
      isPlaying: function () { return !st.userPaused; },
      setTexture: function () { return false; },                                               // мир текстур не берёт
      setTime: function (t) { st.time = t; if (!st.raf) { draw(); } },
      setHover: function (x, y, on) { st.ptr = { x: x, y: y, on: on !== false }; st.hv = { x: x, y: y, a: on === false ? 0 : 1 }; if (!st.raf) { draw(); } },
      tap: function (x, y) { st.lastTap = -1e9; addWave(x || 0, y || 0); if (!st.raf) { draw(); } kick(); },
      pulse: function (v) { if (st.waves[0]) { st.waves[0].age = (1 - (v == null ? 1 : v)) * WAVE_T; } if (!st.raf) { draw(); } },
      redraw: function () { st.p = st.pT; draw(); },
      info: function () { return { w: st.w, h: st.h, dpr: +st.dpr.toFixed(3), scale: st.scale, draws: st.draws, instances: NB, hdr: HDR, beats: [0, 0.25, 0.5, 0.75, 1] }; },
      destroy: function () {
        st.alive = false;
        if (st.raf) { cancelAnimationFrame(st.raf); st.raf = 0; }
        if (ro) { ro.disconnect(); }
        canvas.removeEventListener('pointermove', onMove); canvas.removeEventListener('pointerleave', onLeave);
        canvas.removeEventListener('pointerdown', onDown); canvas.removeEventListener('pointerup', onUp);
        canvas.removeEventListener('webglcontextlost', lost);
        freeRT(); loseGl();
      }
    };
  }
};
