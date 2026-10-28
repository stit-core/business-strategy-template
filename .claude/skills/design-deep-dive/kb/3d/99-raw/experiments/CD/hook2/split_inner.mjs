// split_inner.mjs · CD3, крюк v2 · разрезать GLB «Звена» (meshopt + квантование, выгрузка Z) на основной (без j3_inner) и начинку
// (только j3_inner со слоями j3in_*) — стенд для glb.innerUrl. Без gltf-transform (его нет в npm-trial): уровень JSON + meshoptimizer 1.1.1.
//   node split_inner.mjs IN.glb OUT_MAIN.glb OUT_INNER.glb [--inner-ao keep|drop]
// Буферы (bufferView), которыми пользуется только одна часть, копируются СЖАТЫМИ как есть (фильтры meshopt сохраняются); общий
// индексный буфер (gltf-transform пишет индексы всех мешей одним видом TRIANGLES) декодируется и пережимается отдельно для каждой части.
// Настоящий экспорт (Z) должен выгружать части раздельно — у начинки свой атлас AO; здесь атлас руки (если keep) копируется в начинку.
import fs from 'node:fs';
import { MeshoptDecoder } from '/home/mm/.cache/blender-research/npm-trial/node_modules/meshoptimizer/meshopt_decoder.mjs';
import { MeshoptEncoder } from '/home/mm/.cache/blender-research/npm-trial/node_modules/meshoptimizer/meshopt_encoder.js';

const [inp, outMain, outInner] = process.argv.slice(2);
const innerAO = (process.argv.find((a) => a.startsWith('--inner-ao=')) || '--inner-ao=keep').split('=')[1];
await MeshoptDecoder.ready; await MeshoptEncoder.ready;

function readGLB(p) {
  const b = fs.readFileSync(p);
  const jl = b.readUInt32LE(12); const json = JSON.parse(b.subarray(20, 20 + jl).toString('utf8'));
  const bl = b.readUInt32LE(20 + jl); const bin = b.subarray(28 + jl, 28 + jl + bl);
  return { json, bin };
}
const { json: J, bin: BIN } = readGLB(inp);
const nodes = J.nodes;
const parent = new Map(); nodes.forEach((n, i) => (n.children || []).forEach((c) => parent.set(c, i)));
const innerRoot = nodes.findIndex((n) => n.name === 'j3_inner' || (n.extras && n.extras.zveno_inner));
if (innerRoot < 0) throw new Error('нет j3_inner');
const sub = new Set(); (function walk(i) { sub.add(i); (nodes[i].children || []).forEach(walk); })(innerRoot);

// сжатые байты вида: ext.buffer (0) ext.byteOffset/byteLength; распакованный размер — bufferView.byteLength (буфер-заглушка 1)
function viewBytes(v) { const e = v.extensions && v.extensions.EXT_meshopt_compression; if (!e) return BIN.subarray(v.byteOffset || 0, (v.byteOffset || 0) + v.byteLength); return BIN.subarray(e.byteOffset || 0, (e.byteOffset || 0) + e.byteLength); }
function decodeView(i) {
  const v = J.bufferViews[i], e = v.extensions.EXT_meshopt_compression;
  const out = new Uint8Array(e.count * e.byteStride);
  MeshoptDecoder.decodeGltfBuffer(out, e.count, e.byteStride, viewBytes(v), e.mode, e.filter);
  return out;
}

function build(keepNodes, rootList, label) {
  const J2 = { asset: J.asset, extensionsUsed: [...(J.extensionsUsed || [])], extensionsRequired: [...(J.extensionsRequired || [])] };
  const nodeMap = new Map(), meshMap = new Map(), matMap = new Map(), texMap = new Map(), imgMap = new Map(), smpMap = new Map(), accMap = new Map();
  const outNodes = [], outMeshes = [], outMats = [], outTex = [], outImg = [], outSmp = [], outAcc = [], outViews = [];
  const order = [...keepNodes].sort((a, b) => a - b);
  order.forEach((i) => { nodeMap.set(i, outNodes.length); outNodes.push(null); });
  const mapIdx = (map, arr, src, fn) => { if (map.has(src)) return map.get(src); const k = arr.length; map.set(src, k); arr.push(null); arr[k] = fn(); return k; };
  const sampler = (s) => mapIdx(smpMap, outSmp, s, () => ({ ...J.samplers[s] }));
  const image = (s) => mapIdx(imgMap, outImg, s, () => ({ ...J.images[s], __view: J.images[s].bufferView }));
  const texture = (t) => mapIdx(texMap, outTex, t, () => { const T = JSON.parse(JSON.stringify(J.textures[t]));
    if (T.sampler !== undefined) T.sampler = sampler(T.sampler); if (T.source !== undefined) T.source = image(T.source);
    for (const ex of Object.values(T.extensions || {})) if (ex.source !== undefined) ex.source = image(ex.source); return T; });
  const remapTex = (o) => { if (!o || typeof o !== 'object') return; for (const [k, v] of Object.entries(o)) { if (v && typeof v === 'object') { if (k.endsWith('Texture') && v.index !== undefined) v.index = texture(v.index); remapTex(v); } } };
  const material = (m) => mapIdx(matMap, outMats, m, () => { const M = JSON.parse(JSON.stringify(J.materials[m]));
    if (label === 'inner' && innerAO === 'drop') delete M.occlusionTexture; remapTex(M); return M; });
  // индексные accessor'ы общего вида TRIANGLES — собираются заново; остальные accessor'ы — со своими видами
  const idxParts = [];                                            // [новый accessor, исходный accessor]
  const accessor = (a, isIndex) => { const had = accMap.has(a); const k = mapIdx(accMap, outAcc, a, () => ({ ...J.accessors[a] })); if (isIndex && !had) idxParts.push([k, a]); return k; };
  const mesh = (m) => mapIdx(meshMap, outMeshes, m, () => { const M = JSON.parse(JSON.stringify(J.meshes[m]));
    for (const p of M.primitives) { for (const k of Object.keys(p.attributes)) p.attributes[k] = accessor(p.attributes[k], false);
      if (p.indices !== undefined) p.indices = accessor(p.indices, true); if (p.material !== undefined) p.material = material(p.material); }
    return M; });
  for (const i of order) { const n = JSON.parse(JSON.stringify(nodes[i])); if (n.mesh !== undefined) n.mesh = mesh(n.mesh);
    if (n.children) n.children = n.children.filter((c) => keepNodes.has(c)).map((c) => nodeMap.get(c)); if (n.children && !n.children.length) delete n.children;
    outNodes[nodeMap.get(i)] = n; }
  // виды: вершинные — копия сжатых байтов; индексные — декодировать общий вид и пережать свою часть одним видом
  const chunks = []; let off0 = 0, off1 = 0;
  const pad4 = (x) => (x + 3) & ~3;
  const pushComp = (bytes) => { const o = off0; chunks.push([o, bytes]); off0 = pad4(off0 + bytes.length); return o; };
  const viewMap = new Map();
  const copyView = (vi) => { if (viewMap.has(vi)) return viewMap.get(vi); const v = JSON.parse(JSON.stringify(J.bufferViews[vi]));
    const e = v.extensions && v.extensions.EXT_meshopt_compression;
    if (e) { e.byteOffset = pushComp(viewBytes(J.bufferViews[vi])); e.buffer = 0; v.buffer = 1; v.byteOffset = off1; off1 = pad4(off1 + v.byteLength); }
    else { v.byteOffset = pushComp(viewBytes(J.bufferViews[vi])); v.buffer = 0; }
    const k = outViews.length; outViews.push(v); viewMap.set(vi, k); return k; };
  outAcc.forEach((A, k) => { if (!idxParts.some(([n]) => n === k)) A.bufferView = copyView(A.bufferView); });
  if (idxParts.length) {                                          // все индексы части — одним новым видом TRIANGLES (u16/u32 — как было)
    const decoded = new Map(); let total = 0; const parts = [];
    const size = J.bufferViews[J.accessors[idxParts[0][1]].bufferView].extensions.EXT_meshopt_compression.byteStride;
    for (const [nk, a] of idxParts) { const A = J.accessors[a]; if (!decoded.has(A.bufferView)) decoded.set(A.bufferView, decodeView(A.bufferView));
      const src = decoded.get(A.bufferView); const es = J.bufferViews[A.bufferView].extensions.EXT_meshopt_compression.byteStride;
      if (es !== size) throw new Error('разный размер индексов'); const b0 = A.byteOffset || 0;
      parts.push([nk, src.subarray(b0, b0 + A.count * size)]); total += A.count; }
    const all = new Uint8Array(total * size); let p = 0;
    for (const [nk, bytes] of parts) { outAcc[nk].byteOffset = p; all.set(bytes, p); p += bytes.length; }
    const enc = MeshoptEncoder.encodeGltfBuffer(all, total, size, 'TRIANGLES');
    const v = { buffer: 1, byteOffset: off1, byteLength: all.length, target: 34963,
      extensions: { EXT_meshopt_compression: { buffer: 0, byteOffset: pushComp(enc), byteLength: enc.length, byteStride: size, mode: 'TRIANGLES', count: total } } };
    off1 = pad4(off1 + all.length);
    const k = outViews.length; outViews.push(v); for (const [nk] of parts) outAcc[nk].bufferView = k;
  }
  outImg.forEach((I) => { I.bufferView = copyView(I.__view); delete I.__view; });
  // имя сцены — не «inner» (так по контракту крюка может называться узел начинки)
  Object.assign(J2, { scene: 0, scenes: [{ name: 'zveno_' + label + '_scene', nodes: rootList.map((i) => nodeMap.get(i)) }], nodes: outNodes, meshes: outMeshes,
    materials: outMats, textures: outTex, images: outImg, samplers: outSmp, accessors: outAcc, bufferViews: outViews,
    buffers: [{ byteLength: off0 }, { byteLength: off1, extensions: { EXT_meshopt_compression: { fallback: true } } }] });
  for (const k of ['textures', 'images', 'samplers']) if (!J2[k].length) delete J2[k];
  if (!J2.textures) { J2.extensionsUsed = J2.extensionsUsed.filter((e) => e !== 'EXT_texture_webp' && e !== 'KHR_texture_basisu'); J2.extensionsRequired = J2.extensionsRequired.filter((e) => e !== 'EXT_texture_webp' && e !== 'KHR_texture_basisu'); }
  const bin = Buffer.alloc(pad4(off0)); for (const [o, b] of chunks) Buffer.from(b.buffer, b.byteOffset, b.length).copy(bin, o);
  let js = Buffer.from(JSON.stringify(J2), 'utf8'); js = Buffer.concat([js, Buffer.alloc(pad4(js.length) - js.length, 0x20)]);
  const head = Buffer.alloc(12); head.write('glTF', 0); head.writeUInt32LE(2, 4); head.writeUInt32LE(12 + 8 + js.length + 8 + bin.length, 8);
  const c0 = Buffer.alloc(8); c0.writeUInt32LE(js.length, 0); c0.write('JSON', 4);
  const c1 = Buffer.alloc(8); c1.writeUInt32LE(bin.length, 0); c1.writeUInt32LE(0x004e4942, 4);
  return Buffer.concat([head, c0, js, c1, bin]);
}
const all = new Set(nodes.map((_, i) => i));
const mainNodes = new Set([...all].filter((i) => !sub.has(i)));
const roots = J.scenes[J.scene || 0].nodes;
const main = build(mainNodes, roots, 'main');
const inner = build(sub, [innerRoot], 'inner');
fs.writeFileSync(outMain, main); fs.writeFileSync(outInner, inner);
const tris = (set) => [...set].reduce((s, i) => { const n = nodes[i]; if (n.mesh === undefined) return s; return s + J.meshes[n.mesh].primitives.reduce((t, p) => t + (p.indices !== undefined ? J.accessors[p.indices].count / 3 : 0), 0); }, 0);
console.log(JSON.stringify({ in: inp, in_bytes: fs.statSync(inp).size, main_bytes: main.length, inner_bytes: inner.length, inner_ao: innerAO,
  main_tris: tris(mainNodes), inner_tris: tris(sub), inner_layers: (nodes[innerRoot].children || []).map((c) => nodes[c].name) }));
