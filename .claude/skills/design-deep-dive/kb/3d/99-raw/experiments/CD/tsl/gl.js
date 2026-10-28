import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { build, run } from './common.js';
const canvas = document.getElementById('c'); canvas.style.width = '960px'; canvas.style.height = '600px';
const ti = performance.now();
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1.5); renderer.setSize(960, 600, false);
renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 1.22;
// тот же приём на GLSL: градиентный шум (классический Perlin 3D, как mx_noise_float по смыслу) в roughnessFactor
const NOISE = `vec3 h3(vec3 p){ p = vec3(dot(p,vec3(127.1,311.7,74.7)), dot(p,vec3(269.5,183.3,246.1)), dot(p,vec3(113.5,271.9,124.6))); return -1.0 + 2.0*fract(sin(p)*43758.5453123); }
float gnoise(vec3 p){ vec3 i = floor(p), f = fract(p), u = f*f*(3.0-2.0*f);
  return mix(mix(mix(dot(h3(i),f), dot(h3(i+vec3(1,0,0)),f-vec3(1,0,0)),u.x), mix(dot(h3(i+vec3(0,1,0)),f-vec3(0,1,0)), dot(h3(i+vec3(1,1,0)),f-vec3(1,1,0)),u.x),u.y),
             mix(mix(dot(h3(i+vec3(0,0,1)),f-vec3(0,0,1)), dot(h3(i+vec3(1,0,1)),f-vec3(1,0,1)),u.x), mix(dot(h3(i+vec3(0,1,1)),f-vec3(0,1,1)), dot(h3(i+vec3(1,1,1)),f-vec3(1,1,1)),u.x),u.y), u.z); }`;
const m = new THREE.MeshPhysicalMaterial({ color: '#50555e', metalness: 0.9, roughness: 0.3 });
m.onBeforeCompile = (sh) => {
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vLoc;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvLoc = position;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vLoc;\n' + NOISE)
    .replace('#include <roughnessmap_fragment>', `float rr = length(vLoc.yz), aa = atan(vLoc.z, vLoc.y);
      float roughnessFactor = 0.2 + 0.12 * (0.5 + 0.5 * gnoise(vec3(rr * 900.0, 0.5, 0.5))) + 0.06 * (0.5 + 0.5 * gnoise(vec3(aa * 60.0, rr * 24.0, 1.5)));`);
};
m.customProgramCacheKey = () => 'cd2-brushed';
const { scene, camera, g } = build(THREE, m, RoomEnvironment, renderer);
const initMs = performance.now() - ti;
const gl = renderer.getContext();
await run(renderer, scene, camera, g, { initMs, render: async () => renderer.render(scene, camera),
  sync: async () => gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)), backend: () => 'webgl2' });
