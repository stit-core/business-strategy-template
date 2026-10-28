// three r186 — hero «постер → 3D после LCP» (эталон).
// Сборка: npx esbuild hero.js --bundle --format=esm --splitting --minify --outdir=dist --legal-comments=none
// Постер и 3D — из одного GLB и одной пары тонмаппинга (Neutral); canvas прозрачный — фон рисует CSS.
const CFG = Object.assign({
  modelPhone: 'assets/camera_512.glb',     // ≤ 0,8 МБ: KTX2 ETC1S 512², meshopt
  modelDesktop: 'assets/camera_1k.glb',    // KTX2 ETC1S 1024²
  decoders: 'assets/decoders/',            // копии three@0.186.0/examples/jsm/libs/ со своего домена
  maxDpr: 1.5,
}, window.HERO_CFG || {});
const hero = document.getElementById('hero');
const pauseBtn = document.getElementById('hero-pause');
const posterMode = new URLSearchParams(location.search).has('poster');   // снять постер из того же кадра
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const phone = matchMedia('(max-width: 768px), (pointer: coarse)').matches;
const saveData = !!(navigator.connection && navigator.connection.saveData);
const lowMem = !!(navigator.deviceMemory && navigator.deviceMemory < 2);
const hasWebGL2 = (() => { try { return !!document.createElement('canvas').getContext('webgl2'); } catch (e) { return false; } })();
const T = window.__t = { phone, reduce: reduce.matches, saveData, lowMem, hasWebGL2 };

if (posterMode) boot().catch(fail);
else if (hasWebGL2 && !saveData && !lowMem) {
  const io = new IntersectionObserver((es) => {
    if (!es.some((e) => e.isIntersecting)) return;
    io.disconnect();
    const idle = window.requestIdleCallback || ((cb) => setTimeout(cb, 200));   // Safari без rIC
    const go = () => idle(() => boot().catch(fail), { timeout: 2000 });
    if (document.readyState === 'complete') go(); else addEventListener('load', go, { once: true });
  }, { rootMargin: '200px' });
  io.observe(hero);
} else { T.fallback = 'poster'; window.__ready = true; }

function fail(e) { T.error = String((e && e.stack) || e); console.error(e); hero.classList.remove('is-live'); window.__ready = true; }

function glbExtensions(buf) {
  const dv = new DataView(buf);
  if (dv.getUint32(0, true) !== 0x46546C67) throw new Error('не GLB');
  const json = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, dv.getUint32(12, true))));
  return new Set([...(json.extensionsUsed || []), ...(json.extensionsRequired || [])]);
}

async function boot() {
  T.boot = performance.now();
  const THREE = await import('three');
  const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
  const { RoomEnvironment } = await import('three/addons/environments/RoomEnvironment.js');
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance', preserveDrawingBuffer: posterMode });
  renderer.setPixelRatio(posterMode ? 1 : Math.min(devicePixelRatio, CFG.maxDpr));
  renderer.toneMapping = THREE.NeutralToneMapping;          // пара к Blender «Khronos PBR Neutral»
  renderer.domElement.setAttribute('aria-hidden', 'true');   // смысл — в alt постера и тексте страницы
  hero.appendChild(renderer.domElement);
  const scene = new THREE.Scene();                           // без scene.background: фон — CSS (01 §2.3)
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 100);

  const url = posterMode || !phone ? CFG.modelDesktop : CFG.modelPhone;
  const buf = await (await fetch(url)).arrayBuffer();
  const ext = glbExtensions(buf);
  const loader = new GLTFLoader();
  if (ext.has('EXT_meshopt_compression') || ext.has('KHR_meshopt_compression')) {
    const { MeshoptDecoder } = await import('three/addons/libs/meshopt_decoder.module.js');
    loader.setMeshoptDecoder(MeshoptDecoder);
  }
  let ktx2 = null;
  if (ext.has('KHR_texture_basisu')) {
    const { KTX2Loader } = await import('three/addons/loaders/KTX2Loader.js');
    loader.setKTX2Loader(ktx2 = new KTX2Loader().setTranscoderPath(CFG.decoders + 'basis/').detectSupport(renderer));
  }
  const gltf = await loader.parseAsync(buf, url.replace(/[^/]*$/, ''));
  ktx2?.dispose();
  const model = gltf.scene;
  model.rotation.y = -0.5;                                   // тот же стартовый ракурс, что у постера
  scene.add(model);
  T.parsed = performance.now();

  // кадр по проекции вершин: силуэт занимает долю fill кадра (сфера и углы AABB у вытянутых объектов дают пустой кадр)
  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model);
  const center = box.getCenter(new THREE.Vector3());
  const corners = [];                                        // выборка ≤ 4000 вершин в мировых координатах
  model.traverse((o) => {
    const pos = o.isMesh && o.geometry.attributes.position;
    if (!pos) return;
    const step = Math.max(1, Math.ceil(pos.count / 1500));
    for (let i = 0; i < pos.count; i += step) corners.push(new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld));
  });
  const dir = new THREE.Vector3(0.62, 0.28, 0.73).normalize();
  const extentAt = (d) => {
    camera.position.copy(center).addScaledVector(dir, d); camera.lookAt(center);
    camera.near = d / 100; camera.far = d * 10; camera.updateProjectionMatrix(); camera.updateMatrixWorld();
    return Math.max(...corners.map((p) => { const q = p.clone().project(camera); return Math.max(Math.abs(q.x), Math.abs(q.y)); }));
  };
  const fit = (fill = 0.86) => {
    const r = hero.getBoundingClientRect();
    renderer.setSize(r.width, r.height, false);
    camera.aspect = r.width / r.height;
    let lo = box.getBoundingSphere(new THREE.Sphere()).radius * 1.01, hi = lo * 60;   // камера вне сферы: проекция монотонна
    for (let i = 0; i < 32; i++) { const mid = (lo + hi) / 2; if (extentAt(mid) > fill) lo = mid; else hi = mid; }
    extentAt(hi);
  };
  fit();
  await renderer.compileAsync(scene, camera);                // тяжёлый первый render не попадёт в кроссфейд
  const timer = new THREE.Timer();
  const draw = () => renderer.render(scene, camera);
  let paused = reduce.matches;
  const base = model.rotation.y;                             // покачивание ±20°, период ≈ 16 с (не 0,2 Гц — XM3 §7.4)
  const tick = () => { timer.update(); model.rotation.y = base + 0.35 * Math.sin(timer.getElapsed() * 0.4); draw(); };
  draw();
  T.firstFrame = performance.now();
  performance.mark('hero-first-frame');                      // метка для ворот качества (05 §6)
  if (posterMode) { window.__ready = true; return; }
  hero.classList.add('is-live');
  new ResizeObserver(() => { fit(); draw(); }).observe(hero);
  let visible = true;
  const update = () => {
    const run = visible && !document.hidden && !paused && !reduce.matches;
    renderer.setAnimationLoop(run ? (timer.reset?.(), tick) : null);   // стоп цикла = 0 вызовов в покое
    if (!run) draw();
    pauseBtn.setAttribute('aria-pressed', String(paused || reduce.matches));
    T.looping = run;
  };
  pauseBtn.hidden = false;                                   // WCAG 2.2.2: автодвижение > 5 с — пауза
  pauseBtn.addEventListener('click', () => { paused = !paused; update(); });
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; update(); }).observe(hero);
  document.addEventListener('visibilitychange', update);
  reduce.addEventListener('change', () => { paused = reduce.matches; update(); });
  update();
  T.model = url; T.ext = [...ext]; T.calls = renderer.info.render.calls;
  T.canvas = [renderer.domElement.width, renderer.domElement.height];
  for (const k of ['boot', 'parsed', 'firstFrame']) T[k] = Math.round(T[k]);
  console.warn('F1 three.js timing ' + JSON.stringify({ boot: T.boot, parsed: T.parsed, firstFrame: T.firstFrame, model: url.slice(-14), calls: T.calls }));
  window.__ready = true;
}
