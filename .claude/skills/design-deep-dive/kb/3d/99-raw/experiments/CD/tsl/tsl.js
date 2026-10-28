import * as THREE from 'three/webgpu';
import { positionLocal, float, vec3, length, atan, mx_noise_float } from 'three/tsl';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { build, run } from './common.js';
const q = new URLSearchParams(location.search);
const canvas = document.getElementById('c'); canvas.style.width = '960px'; canvas.style.height = '600px';
const ti = performance.now();
const renderer = new THREE.WebGPURenderer({ canvas, antialias: true, forceWebGL: q.has('gl') });
renderer.setPixelRatio(1.5); renderer.setSize(960, 600, false);
renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 1.22;
await renderer.init();
const m = new THREE.MeshPhysicalNodeMaterial({ color: '#50555e', metalness: 0.9, roughness: 0.3 });
const p = positionLocal, r = length(p.yz), ang = atan(p.z, p.y);
const rings = mx_noise_float(vec3(r.mul(900), 0.5, 0.5)).mul(0.5).add(0.5);           // кольца точения по радиусу
const streak = mx_noise_float(vec3(ang.mul(60), r.mul(24), 1.5)).mul(0.5).add(0.5);   // штрихи по окружности
m.roughnessNode = float(0.2).add(rings.mul(0.12)).add(streak.mul(0.06));
const { scene, camera, g } = build(THREE, m, RoomEnvironment, renderer);
const initMs = performance.now() - ti;
await run(renderer, scene, camera, g, {
  initMs,
  render: async () => renderer.render(scene, camera),
  sync: async () => { if (renderer.backend.isWebGPUBackend) await renderer.backend.device.queue.onSubmittedWorkDone(); else { const gl = renderer.backend.gl; gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); } },
  backend: () => (renderer.backend.isWebGPUBackend ? 'webgpu' : 'webgl2-fallback'),
});
