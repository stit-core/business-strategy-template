/* Шаблон сцены набора: один полноэкранный фрагментный шейдер WebGL2, свой цикл кадров, без библиотек.
   Копия файла → scenes/<имя>.js; строка регистрации — с тем же <имя>. Рантайм страницы (stage-runtime.js) зовёт:
   setVisible, scrub, setIdle, setPlaying, setTexture, destroy; стенд — ещё setTime, setHover, tap, pulse, redraw, info.

   Uniforms шейдера: uRes (px буфера), uTime (с), uP (прогресс 0..1 — уже сглажен пружиной рантайма), uPointer (x, y в −1..1
   от центра холста, присутствие 0..1), uTap (импульс касания 1→0, τ 0,55 с), uTapAt (точка касания −1..1), uTex0..3 + uTexOn
   (текстуры слотов 0..3, 1 — пришла), uBg (фон места, линейный, после обратной «пятки» тона), uShift (сдвиг объектива: центр
   героя в долях полукадра), uQuiet / uQuietY (тихие зоны HTML-текста).

   Нормы набора: плотность пикселей ≤ 2 под бюджетом пикселей холста (4,6 МП ПК, 1,9 МП телефон), адаптивный множитель
   0,7…1; кадр рисуется только когда что-то меняется, одна собственная жизнь — ≈ 30 кадров/с; вне экрана и в скрытой
   вкладке — 0 кадров; колебания крупных форм — период ≥ 10 с или шум без ведущей частоты (полосы 2,5–6 с нет), вспышки
   ≤ 3 в секунду; текст — HTML-слоем страницы, не в холсте; в window — только строка регистрации; кадр при заданных p и t
   одинаков (постеры и раскадровки снимает стенд).

   opts: mobile, rtl (зеркальная композиция: сдвигается кадр, геометрия и текстуры не зеркалятся), variant (место на
   странице), background (hex фона места), palette ({bg, haze, key, cool} — hex), layout ({shift: [x, y], quiet: [x0, x1, k],
   quietY: [низ, верх, k низа, k верха]}), driven (прогресс ведёт рантайм; своих окон автодвижения нет), idle (своя жизнь
   включена), maxDpr, pxMax, preserve (стенд: сохранять буфер), onReady(handle|null) — асинхронная сборка, onStatus(code, log),
   onFrame({w, h, anchors}) — якоря для HTML-подписей. */
(window.STAGE_SCENES = window.STAGE_SCENES || {})['template'] = function (canvas, opts) {
  'use strict';
  opts = opts || {};
  function status(code, log) { if (opts.onStatus) { opts.onStatus(code, log); } }
  var gl = null;
  try {
    gl = canvas.getContext('webgl2', { antialias: false, alpha: false, depth: false, stencil: false, premultipliedAlpha: false,
      preserveDrawingBuffer: !!opts.preserve, powerPreference: 'high-performance' });
  } catch (e) { gl = null; }
  if (!gl) { status('no-webgl'); return null; }

  // ---------- цвет: расчёт в линейном пространстве, выход — sRGB вручную ----------
  // Палитра по умолчанию нейтральная (графит, тёплый ключ, холодный отсвет); бренд подставляет свои hex через opts.palette.
  var PAL = { bg: '#16181D', haze: '#2B3340', key: '#F1E4CF', cool: '#9FB3C6' };
  Object.keys(opts.palette || {}).forEach(function (k) { PAL[k] = opts.palette[k]; });
  function srgbToLin(c) { return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
  function hexLin(h) {
    var n = parseInt(String(h).replace('#', ''), 16);
    return [srgbToLin(((n >> 16) & 255) / 255), srgbToLin(((n >> 8) & 255) / 255), srgbToLin((n & 255) / 255)];
  }
  // Обратная «пятка» тона Khronos PBR Neutral: такой фон после тона попадает ровно в hex места (ΔE ≈ 0 на стыке с секцией).
  function preTone(h) {
    var c = hexLin(h), m = Math.min(c[0], c[1], c[2]), off = 0.04;
    if (m < 0.04) { var x = Math.sqrt(m / 6.25); off = x - m; if (x >= 0.08) { off = 0.04; } }
    return [c[0] + off, c[1] + off, c[2] + off];
  }
  function g3(a) { return 'vec3(' + a.map(function (x) { return x.toFixed(6); }).join(', ') + ')'; }

  // ---------- шейдер сцены: здесь живёт вся картинка ----------
  var FS = [
    '#version 300 es',
    'precision highp float;',
    'out vec4 fragColor;',
    'uniform vec2 uRes; uniform float uTime; uniform float uP; uniform vec3 uPointer; uniform float uTap; uniform vec2 uTapAt;',
    'uniform vec3 uBg; uniform vec2 uShift; uniform vec4 uQuiet; uniform vec4 uQuietY;',
    'uniform sampler2D uTex0; uniform sampler2D uTex1; uniform sampler2D uTex2; uniform sampler2D uTex3; uniform vec4 uTexOn;',
    'const vec3 HAZE = ' + g3(hexLin(PAL.haze)) + ';',
    'const vec3 KEY = ' + g3(hexLin(PAL.key)) + ';',
    'const vec3 COOL = ' + g3(hexLin(PAL.cool)) + ';',
    // тон Khronos PBR Neutral: тёмное почти без изменений (пятка), светлое плавно сжимается к белому без смены оттенка
    'vec3 neutralTone(vec3 c){',
    '  const float sc = 0.76; const float ds = 0.15;',
    '  float x = min(c.r, min(c.g, c.b)); float off = x < 0.08 ? x - 6.25*x*x : 0.04; c -= off;',
    '  float pk = max(c.r, max(c.g, c.b)); if (pk < sc) { return c; }',
    '  const float d = 1.0 - sc; float np = 1.0 - d*d/(pk + d - sc); c *= np/pk;',
    '  float g = 1.0 - 1.0/(ds*(pk - np) + 1.0); return mix(c, vec3(np), g);',
    '}',
    'vec3 oetf(vec3 c){ c = clamp(c, 0.0, 1.0); return mix(c*12.92, 1.055*pow(c, vec3(1.0/2.4)) - 0.055, step(vec3(0.0031308), c)); }',
    'float hash(vec2 p){ p = fract(p*vec2(443.897, 441.423)); p += dot(p, p.yx + 19.19); return fract((p.x + p.y)*p.x); }',
    // тихая зона текста: колонка у начала строки (x0 — сила 1, x1 — 0; rtl — от правого края) и полосы сверху/снизу (телефон)
    'float quietK(vec2 uv){',
    '  float x = mix(uv.x, 1.0 - uv.x, uQuiet.w);',
    '  float q = uQuiet.z*(1.0 - smoothstep(uQuiet.x, uQuiet.y, x));',
    '  q = max(q, uQuietY.z*(1.0 - smoothstep(uQuietY.x - 0.12, uQuietY.x, uv.y)));',
    '  q = max(q, uQuietY.w*smoothstep(1.0 - uQuietY.y, 1.0 - uQuietY.y + 0.12, uv.y));',
    '  return q;',
    '}',
    // края кадра уходят в фон места: светлого прямоугольника у края нет (ширина спада — в высотах кадра)
    'float edgeK(vec2 uv){ vec2 m = min(uv, 1.0 - uv)*uRes/uRes.y; return smoothstep(0.0, 0.24, m.x)*smoothstep(0.0, 0.17, m.y); }',
    'void main(){',
    '  float asp = uRes.x/uRes.y, px = 1.0/uRes.y;',
    '  vec2 uv = gl_FragCoord.xy/uRes;',
    '  vec2 q = (gl_FragCoord.xy - 0.5*uRes)/uRes.y;',                       // кадр в высотах, центр — 0
    '  vec2 half_ = vec2(0.5*asp, 0.5);',
    '  vec2 c = uShift*half_;',                                              // герой — по сдвигу объектива
    '  vec2 ptr = uPointer.xy*half_;',
    '  c += (ptr - c)*0.06*uPointer.z;',                                     // герой чуть тянется к курсору
    '  float r = length(q - c);',
    // своя жизнь: «дыхание» — сумма синусов с периодами 13,7 и 21,1 с (без общей доли, нет ведущей частоты)
    '  float br = 0.008*(sin(uTime*6.2832/13.7) + 0.6*sin(uTime*6.2832/21.1 + 1.3));',
    '  float R = 0.14 + 0.24*uP + br;',
    '  float core = exp(-pow((r - R)/(0.004 + 1.5*px), 2.0));',              // ядро не тоньше ≈ 1,5 px буфера
    '  float halo = exp(-pow((r - R)/0.07, 2.0))*0.28 + exp(-abs(r - R)/0.22)*0.04;',
    '  vec3 col = uBg + HAZE*exp(-r*r*4.0)*0.5;',
    '  float ang = atan(q.y - c.y, q.x - c.x);',
    '  vec3 lc = mix(COOL, KEY, 0.5 + 0.5*sin(ang + 0.6));',                // тёплый ключ сверху-слева, холодный отсвет напротив
    '  col += lc*(core*1.6 + halo*(0.6 + 0.8*uPointer.z));',
    // текстура слота 0 (sRGB-текстура приходит линейной): диск внутри кольца, кадр «по заполнению»
    '  if (uTexOn.x > 0.5){',
    '    vec2 t = (q - c)/(1.6*R) + 0.5; vec2 e = min(t, 1.0 - t);',
    '    float a = smoothstep(0.0, 2.0*px/(1.6*R), R*0.78 - r)*step(0.0, min(e.x, e.y));',
    '    col = mix(col, texture(uTex0, vec2(t.x, 1.0 - t.y)).rgb*0.9, a);',
    '  }',
    // касание: одно кольцо от точки касания
    '  vec2 tp = uTapAt*half_;',
    '  float tr = length(q - tp) - (1.0 - uTap)*0.45;',
    '  col += KEY*uTap*exp(-tr*tr/0.0004)*0.9;',
    // тихая зона: яркое сжато по яркости (оттенок держится), поле — в тон места
    '  float qk = quietK(uv);',
    '  float L = dot(col, vec3(0.2126, 0.7152, 0.0722));',
    '  col = mix(col, uBg + (col - uBg)/(1.0 + 6.0*L), qk);',
    '  col = mix(uBg, col, edgeK(uv));',
    // тон → sRGB → дизеринг ±½ младшего разряда (шум зависит от t: кадр при заданном t детерминирован)
    '  vec3 o = oetf(neutralTone(col)) + (hash(gl_FragCoord.xy + fract(uTime)*17.0) - 0.5)/255.0;',
    '  fragColor = vec4(o, 1.0);',
    '}'
  ].join('\n');
  var VS = '#version 300 es\nin vec2 aP;\nvoid main(){ gl_Position = vec4(aP, 0.0, 1.0); }';

  // ---------- сборка программы: асинхронно, если есть KHR_parallel_shader_compile ----------
  var khr = gl.getExtension('KHR_parallel_shader_compile');
  var prog = gl.createProgram();
  var vsh = gl.createShader(gl.VERTEX_SHADER); gl.shaderSource(vsh, VS); gl.compileShader(vsh);
  var fsh = gl.createShader(gl.FRAGMENT_SHADER); gl.shaderSource(fsh, FS); gl.compileShader(fsh);
  gl.attachShader(prog, vsh); gl.attachShader(prog, fsh); gl.bindAttribLocation(prog, 0, 'aP'); gl.linkProgram(prog);
  function loseGl() { try { var x = gl.getExtension('WEBGL_lose_context'); if (x) { x.loseContext(); } } catch (err) { /* уже потерян */ } }
  function linked() {
    if (gl.isContextLost()) { return null; }
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      status('shader-error', gl.getShaderInfoLog(fsh) || gl.getShaderInfoLog(vsh) || gl.getProgramInfoLog(prog));
      return null;
    }
    return rest();
  }
  if (opts.onReady) {
    // ручка «в сборке»: рантайм может снять сцену до готовности (destroy освобождает контекст сразу)
    var off = false;
    var poll = function () {
      if (off) { return; }
      if (gl.isContextLost()) { opts.onReady(null); return; }
      if (khr && !gl.getProgramParameter(prog, khr.COMPLETION_STATUS_KHR)) { setTimeout(poll, 40); return; }
      var h = linked(); if (!h) { loseGl(); } opts.onReady(h);
    };
    setTimeout(poll, 0);
    return { pending: true, destroy: function () { off = true; loseGl(); } };
  }
  return linked();

  function rest() {
    var vao = gl.createVertexArray(); gl.bindVertexArray(vao);
    var vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);   // один треугольник на весь кадр
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.useProgram(prog);
    var U = {};
    ['uRes', 'uTime', 'uP', 'uPointer', 'uTap', 'uTapAt', 'uBg', 'uShift', 'uQuiet', 'uQuietY', 'uTex0', 'uTex1', 'uTex2', 'uTex3', 'uTexOn']
      .forEach(function (k) { U[k] = gl.getUniformLocation(prog, k); });

    // ---------- текстуры: 4 слота, прозрачный тексель, пока картинка не пришла ----------
    // Цвет (фото) — SRGB8_ALPHA8: выборка отдаёт линейное значение; данные (маски, поля) — RGBA8 (setTexture(i, img, {data: true})).
    var aniso = gl.getExtension('EXT_texture_filter_anisotropic');
    var tex = [];
    for (var i = 0; i < 4; i += 1) {
      var t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 0]));
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.uniform1i(U['uTex' + i], i);
      tex.push({ tx: t, ok: false });
    }

    // ---------- раскладка кадра: сдвиг объектива и тихие зоны текста по месту ----------
    var mobile = !!opts.mobile, rtl = !!opts.rtl, L = opts.layout || {};
    // место на странице: ПК — герой ≈ на 2/3 ширины (колонка текста у начала строки), телефон — по центру; без места — центр
    var shift = L.shift || (opts.variant ? (mobile ? [0, 0.06] : [0.33, 0]) : [0, 0]);
    if (rtl) { shift = [-shift[0], shift[1]]; }
    var quiet = L.quiet || (mobile ? [0, 0, 0] : [0.34, 0.6, opts.variant ? 1 : 0]);
    var quietY = L.quietY || (mobile && opts.variant ? [0.32, 0.42, 0.8, 0.6] : [0, 0, 0, 0]);
    var BG = preTone(opts.background || PAL.bg);

    // ---------- бюджет пикселей и плотность ----------
    var maxDpr = opts.maxDpr || 2, pxMax = opts.pxMax || (mobile ? 1.9e6 : 4.6e6);
    var SCALE_MIN = 0.7, SCALE_DOWN = 0.85, SLOW = 0.024, FAST = 0.0125, WIN = 40;
    var st = { time: 0, p: 0, pT: 0, ptr: { x: 0, y: 0, on: false }, hv: { x: 0, y: 0, a: 0 }, tap: 0, tapAt: [0, 0], lastTap: -1e9,
      visible: true, alive: true, idle: opts.idle !== false, userPaused: false, dirty: false, raf: 0, last: 0,
      w: 0, h: 0, cssW: 0, cssH: 0, dpr: 1, scale: 1, frames: [], draws: 0 };

    function resize() {
      var r = canvas.getBoundingClientRect(), cw = Math.max(1, r.width), ch = Math.max(1, r.height);
      var dpr = Math.min(window.devicePixelRatio || 1, maxDpr, Math.sqrt(pxMax / (cw * ch)));
      dpr = Math.max(0.5, dpr) * st.scale;
      var w = Math.max(1, Math.round(cw * dpr)), h = Math.max(1, Math.round(ch * dpr));
      st.cssW = cw; st.cssH = ch; st.dpr = dpr;
      if (w !== st.w || h !== st.h) { canvas.width = w; canvas.height = h; st.w = w; st.h = h; }
    }
    function draw() {
      resize();
      gl.viewport(0, 0, st.w, st.h);
      gl.useProgram(prog); gl.bindVertexArray(vao);
      for (var i = 0; i < tex.length; i += 1) { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, tex[i].tx); }
      gl.uniform2f(U.uRes, st.w, st.h);
      gl.uniform1f(U.uTime, st.time);
      gl.uniform1f(U.uP, st.p);
      gl.uniform3f(U.uPointer, st.hv.x, st.hv.y, st.hv.a);
      gl.uniform1f(U.uTap, st.tap);
      gl.uniform2f(U.uTapAt, st.tapAt[0], st.tapAt[1]);
      gl.uniform3f(U.uBg, BG[0], BG[1], BG[2]);
      gl.uniform2f(U.uShift, shift[0], shift[1]);
      gl.uniform4f(U.uQuiet, quiet[0], quiet[1], quiet[2], rtl ? 1 : 0);
      gl.uniform4f(U.uQuietY, quietY[0], quietY[1], quietY[2], quietY[3]);
      gl.uniform4f(U.uTexOn, tex[0].ok ? 1 : 0, tex[1].ok ? 1 : 0, tex[2].ok ? 1 : 0, tex[3].ok ? 1 : 0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      st.draws += 1;
      if (opts.onFrame) {
        // якорь героя в CSS px холста: по нему HTML-подпись встаёт рядом с героем
        var ax = (0.5 + 0.5 * shift[0]) * st.cssW, ay = (0.5 - 0.5 * shift[1]) * st.cssH;
        opts.onFrame({ w: st.cssW, h: st.cssH, anchors: [{ x: ax, y: ay }] });
      }
    }

    // ---------- цикл кадров: кадр только когда что-то меняется ----------
    function running() { return st.alive && st.visible && !document.hidden; }
    function ambient() { return st.idle && !st.userPaused; }                                 // своя жизнь сцены
    function settling() {
      var tx = st.ptr.on ? st.ptr.x : st.hv.x, ty = st.ptr.on ? st.ptr.y : st.hv.y;
      return Math.abs(st.pT - st.p) > 1e-4 || st.tap > 0 || st.dirty ||
        Math.abs(tx - st.hv.x) > 0.002 || Math.abs(ty - st.hv.y) > 0.002 || Math.abs((st.ptr.on ? 1 : 0) - st.hv.a) > 0.002;
    }
    function step(now) {
      st.raf = 0;
      if (!running()) { st.last = 0; return; }
      var busy = settling();
      if (!busy && !ambient()) { st.last = 0; st.frames = []; return; }                    // в покое — 0 кадров
      // только своя жизнь: ≈ 30 кадров в секунду достаточно медленному движению и оставляет странице её прокрутку
      if (!busy && st.last && now - st.last < 31) { st.raf = requestAnimationFrame(step); return; }
      var dt = st.last ? Math.min(0.05, (now - st.last) / 1000) : 1 / 60; st.last = now;
      if (busy) {
        // адаптивная плотность: медиана 40 кадров; вниз ×0,85 при > 24 мс (не ниже 0,7), вверх при < 12,5 мс; окно — заново
        if (st.frames.length >= WIN) { st.frames.shift(); } st.frames.push(dt);
        if (st.frames.length >= WIN) {
          var md = st.frames.slice().sort(function (a, b) { return a - b; })[WIN >> 1];
          if (md > SLOW && st.scale > SCALE_MIN) { st.scale = Math.max(SCALE_MIN, st.scale * SCALE_DOWN); st.frames = []; }
          else if (md < FAST && st.scale < 1) { st.scale = Math.min(1, st.scale / SCALE_DOWN); st.frames = []; }
        }
      }
      if (ambient()) { st.time += dt; }
      st.p += (st.pT - st.p) * (1 - Math.exp(-dt / 0.12));                                  // прогресс сглажен рантаймом; здесь — дотяг
      if (Math.abs(st.pT - st.p) < 1e-4) { st.p = st.pT; }
      var k = 1 - Math.exp(-dt / 0.35);
      if (st.ptr.on) { st.hv.x += (st.ptr.x - st.hv.x) * k; st.hv.y += (st.ptr.y - st.hv.y) * k; }
      st.hv.a += ((st.ptr.on ? 1 : 0) - st.hv.a) * (1 - Math.exp(-dt / 0.5));
      if (Math.abs((st.ptr.on ? 1 : 0) - st.hv.a) < 0.002) { st.hv.a = st.ptr.on ? 1 : 0; }
      st.tap *= Math.exp(-dt / 0.55); if (st.tap < 0.003) { st.tap = 0; }
      draw();
      st.dirty = false;
      st.raf = requestAnimationFrame(step);
    }
    function kick() { if (!st.raf && running()) { st.last = 0; st.raf = requestAnimationFrame(step); } }
    // одна отрисовка на изменение: при живом цикле — пометка «грязный кадр», без цикла — кадр сразу
    function change() { if (st.raf) { st.dirty = true; } else { draw(); kick(); } }

    // ---------- ввод: курсор (без касаний), касание — импульс в точке, не чаще 3 раз в секунду ----------
    function local(e) {
      var r = canvas.getBoundingClientRect();
      return [Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width) * 2 - 1)), Math.max(-1, Math.min(1, 1 - ((e.clientY - r.top) / r.height) * 2))];
    }
    function onMove(e) { if (e.pointerType === 'touch') { return; } var q = local(e); st.ptr = { x: q[0], y: q[1], on: true }; kick(); }
    function onLeave() { st.ptr.on = false; kick(); }
    var down = null;
    function onDown(e) { down = { x: e.clientX, y: e.clientY }; }
    function onUp(e) {
      var now = performance.now();
      if (down && Math.abs(e.clientX - down.x) + Math.abs(e.clientY - down.y) < 6 && now - st.lastTap > 340) {
        st.lastTap = now; st.tap = 1; st.tapAt = local(e); kick();
      }
      down = null;
    }
    canvas.style.touchAction = 'pan-y';                                                        // палец прокручивает страницу
    canvas.addEventListener('pointermove', onMove); canvas.addEventListener('pointerleave', onLeave);
    canvas.addEventListener('pointerdown', onDown); canvas.addEventListener('pointerup', onUp);
    var ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(function () { if (!st.raf && st.alive) { draw(); } }) : null;
    if (ro) { ro.observe(canvas); }
    // потеря контекста: стоп цикла и статус — рантайм показывает постер и может оживить сцену заново на следующем подлёте
    var lost = function (ev) { ev.preventDefault(); st.alive = false; if (st.raf) { cancelAnimationFrame(st.raf); st.raf = 0; } status('context-lost'); };
    canvas.addEventListener('webglcontextlost', lost);

    draw();
    status('ready');
    kick();

    return {
      setVisible: function (v) { st.visible = !!v; if (v) { kick(); } },
      wake: kick,
      scrub: function (p) { st.pT = Math.max(0, Math.min(1, p)); if (!st.raf) { st.p = st.pT; } change(); },
      setIdle: function (on) { st.userPaused = !on; kick(); },
      setPlaying: function (on) { st.userPaused = !on; kick(); },
      isPlaying: function () { return !st.userPaused; },
      setTexture: function (i, img, o) {
        var u = tex[i]; if (!u || !img) { return false; }
        var data = !!(o && o.data);
        try {
          gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, u.tx);
          gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
          gl.texImage2D(gl.TEXTURE_2D, 0, data ? gl.RGBA8 : gl.SRGB8_ALPHA8, gl.RGBA, gl.UNSIGNED_BYTE, img);
          gl.generateMipmap(gl.TEXTURE_2D); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
          if (aniso) { gl.texParameterf(gl.TEXTURE_2D, aniso.TEXTURE_MAX_ANISOTROPY_EXT, 4); }
          u.ok = !gl.getError();
        } catch (err) { u.ok = false; }
        change();
        return u.ok;
      },
      // стенд: кадр по заданным параметрам (без живого цикла — сразу)
      setTime: function (t) { st.time = t; if (!st.raf) { draw(); } },
      setHover: function (x, y, on) { st.ptr = { x: x, y: y, on: on !== false }; st.hv = { x: x, y: y, a: on === false ? 0 : 1 }; if (!st.raf) { draw(); } },
      tap: function (x, y) { st.tap = 1; st.tapAt = [x || 0, y || 0]; if (!st.raf) { draw(); } kick(); },
      pulse: function (v) { st.tap = v == null ? 1 : v; if (!st.raf) { draw(); } },
      redraw: function () { st.p = st.pT; draw(); },
      info: function () { return { w: st.w, h: st.h, dpr: +st.dpr.toFixed(3), scale: st.scale, draws: st.draws }; },
      destroy: function () {
        st.alive = false;
        if (st.raf) { cancelAnimationFrame(st.raf); st.raf = 0; }
        if (ro) { ro.disconnect(); }
        canvas.removeEventListener('pointermove', onMove); canvas.removeEventListener('pointerleave', onLeave);
        canvas.removeEventListener('pointerdown', onDown); canvas.removeEventListener('pointerup', onUp);
        canvas.removeEventListener('webglcontextlost', lost);
        loseGl();                                                                              // контекст освобождается сразу
      }
    };
  }
};
