// Валидация glTF/GLB официальным валидатором Khronos (npm gltf-validator). Печатает JSON-отчёт.
// node validate.mjs file.glb [--max 200]
import fs from 'node:fs';
import path from 'node:path';
import validator from 'gltf-validator';
const file = process.argv[2];
if (!file) { console.error('usage: node validate.mjs file.glb|file.gltf'); process.exit(2); }
const max = process.argv.includes('--max') ? +process.argv[process.argv.indexOf('--max') + 1] : 200;
const data = new Uint8Array(fs.readFileSync(file));
const dir = path.dirname(path.resolve(file));
const report = await validator.validateBytes(data, {
  uri: path.basename(file),
  maxIssues: max,
  externalResourceFunction: (uri) => new Promise((resolve, reject) => {
    const p = path.resolve(dir, decodeURIComponent(uri));
    fs.readFile(p, (err, d) => err ? reject(err.toString()) : resolve(new Uint8Array(d)));
  }),
});
console.log(JSON.stringify(report, null, 1));
