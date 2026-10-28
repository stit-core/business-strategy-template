// ktx2.js · общий код 3D «Звена» (_shared/code3d, крюк v2) — KTX2Loader отдельным чанком: качается, только если
// сборка с --ktx2 (define __CD_KTX2__) и GLB содержит KHR_texture_basisu (или glb.ktx2 задан явно — тогда параллельно с GLB).
// Транскодер basis (basis_transcoder.js + .wasm, three 0.186.0) — со своего домена: build.sh --ktx2 кладёт его в <страница>/js/basis/;
// путь по умолчанию считается от этого чанка (js/chunks/ → ../basis/), свой путь — glb.ktx2: 'путь/к/basis/'.
// Один загрузчик на страницу (KTX2Loader предупреждает о нескольких), воркеров 2 (6 текстур, главная — атлас AO 2048²).
// detectSupport: на Linux (Mesa) three сам выключает эмулируемые ETC/ASTC — ETC1S идёт в BC1/BC3, UASTC — в BC7.
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js';

let L = null;
export function ktx2Loader(renderer, path, workers) {
  if (!L) {
    L = new KTX2Loader();
    L.setTranscoderPath(path || new URL('../basis/', import.meta.url).href);
    L.setWorkerLimit(workers || 2);
    L.detectSupport(renderer);
  }
  return L;
}
export function ktx2Release() { if (L) { L.dispose(); L = null; } }
