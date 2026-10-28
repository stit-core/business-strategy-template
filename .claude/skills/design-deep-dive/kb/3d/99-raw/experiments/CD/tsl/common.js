// CD2 · опыт WebGPU/TSL (14-code-3d/08): одна сцена — крупно точёная крышка сустава J2 (профиль capX «Звена») на белом корпусе,
// окружение RoomEnvironment (PMREM), ключевой свет, Neutral 1,22. Материал крышки — процедурная шлифовка: шероховатость = база +
// кольца точения (шум по радиусу) + штрихи по окружности (шум по углу), 0 байт карт. Варианты: TSL на WebGPU, тот же TSL на откате
// WebGL2 (forceWebGL), GLSL onBeforeCompile на WebGLRenderer.
export function capProfile(r) {
  return [[0, -0.022], [r, -0.022], [r, -0.012], [0.96 * r, -0.003], [0.9 * r, 0.002], [0.8 * r, 0.002], [0.78 * r, -0.001],
    [0.76 * r, 0.002], [0.42 * r, 0.003], [0.3 * r, 0.008], [0.15 * r, 0.011], [0, 0.012]];
}
export function build(THREE, capMat, RoomEnvironment, renderer) {
  const scene = new THREE.Scene();
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.9;
  const key = new THREE.DirectionalLight('#ffffff', 2.2); key.position.set(-2, 3, 4); scene.add(key);
  const cap = new THREE.Mesh(new THREE.LatheGeometry(capProfile(0.2).map(([a, b]) => new THREE.Vector2(a, b)), 192), capMat);
  cap.geometry.rotateZ(-Math.PI / 2); cap.geometry.translate(0.246, 0, 0);
  const shell = new THREE.Mesh(new THREE.CylinderGeometry(0.235, 0.235, 0.46, 128), new THREE.MeshPhysicalMaterial({ color: '#f2f2f0', roughness: 0.36, clearcoat: 1, clearcoatRoughness: 0.08 }));
  shell.geometry.rotateZ(Math.PI / 2);
  const g = new THREE.Group(); g.add(cap, shell); g.rotation.y = -0.75; scene.add(g);
  const camera = new THREE.PerspectiveCamera(30, 1.6, 0.05, 20);
  return { scene, camera, g };
}
export async function run(renderer, scene, camera, g, opts) {
  const q = new URLSearchParams(location.search), dur = +q.get('ms') || 2500;
  const place = (a) => { camera.position.set(Math.sin(a) * 1.25 + 0.2, 0.18, Math.cos(a) * 1.25); camera.lookAt(0.12, 0, 0); };
  place(0);
  const t0 = performance.now();
  await opts.render(); await opts.sync();
  const first = performance.now() - t0;
  for (let i = 0; i < 5; i++) { place(i * 0.01); await opts.render(); } await opts.sync();
  await new Promise((r) => setTimeout(r, 300));
  const dts = []; let prev = 0; const start = performance.now();
  await new Promise((done) => {
    const loop = async () => {
      const now = performance.now(); if (prev) dts.push(now - prev); prev = now;
      if (now - start > dur) return done();
      place(Math.sin((now - start) / 600) * 0.3); await opts.render(); requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  });
  place(0); await opts.render(); await opts.sync();
  const med = (a) => { const b = [...a].sort((x, y) => x - y); return b[Math.floor(b.length / 2)]; };
  window.__res = { backend: opts.backend(), frames: dts.length, frame_med: +med(dts).toFixed(3), frame_p90: +[...dts].sort((x, y) => x - y)[Math.floor(dts.length * 0.9)].toFixed(3),
    stalls50: dts.filter((x) => x > 50).length, first_ms: Math.round(first), init_ms: Math.round(opts.initMs) };
  window.__done = true;
}
