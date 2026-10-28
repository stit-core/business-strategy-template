// capture.js — съёмка кадров со СВОЕЙ страницы (?capture=…): постер первого экрана и запасные кадры (reduce, до загрузки 3D)
// для варианта A — только его код, без кадров Blender. Сцена — на весь экран размером в кадр Blender, фон — цвет раздела.
import { Mesh, PlaneGeometry, ShadowMaterial, CanvasTexture, SRGBColorSpace } from 'three';
import { isPhone } from './page.js';

const BG = { type: '#1C1D20', x: '#EDEFF0', snow: '#EDEFF0', graphite: '#141619', linen: '#EFE8DC' };

export async function capture(what, variant, loadModel) {
  document.documentElement.style.cssText = 'overflow:hidden';
  const [name, arg] = what.split('-');
  const stageName = name === 'hero' ? 'hero' : name === 'turn' ? 'turn' : name;
  const el = document.createElement('div');
  el.id = `stage-${stageName}`;
  el.style.cssText = `position:fixed;inset:0;z-index:9999;background:${name === 'turn' ? BG[arg] : name === 'hero' ? '#0D0E10' : BG[name]}`;
  if (stageName !== 'hero') document.getElementById(`stage-${stageName}`)?.removeAttribute('id');
  document.body.append(el);
  const { createStage3D } = await import('./stage3d.js');
  const buildModel = await loadModel();
  const camFile = name === 'hero' ? `H2v2_${arg}` : { type: 'T', turn: 'R', x: 'X' }[stageName];
  const J = await fetch(`assets/data/${camFile}.json`).then((r) => r.json());
  if (name === 'hero') { J.az = -22; J.exposure = +(new URLSearchParams(location.search).get('ex') || 0.0); }   // A: +0,35 EV к Blender — верх колпачков 79 → ≥ 85 L*
  const s = await createStage3D({ buildModel, cams: { [stageName]: J }, phone: isPhone, variant, quality: { shadows: true } });
  if (name === 'hero') {
    // тёмная студия кодом: фон — градиент «лампы фона» (светлее слева сверху, как свет фона у S2), пол — только тени
    const cv = document.createElement('canvas'); cv.width = 64; cv.height = 40;
    const g = cv.getContext('2d');
    const gr = g.createRadialGradient(4, 2, 2, 18, 14, 70);
    gr.addColorStop(0, '#5B5B5C'); gr.addColorStop(0.45, '#39393B'); gr.addColorStop(1, '#1D1E20');
    g.fillStyle = gr; g.fillRect(0, 0, 64, 40);
    const bg = new CanvasTexture(cv); bg.colorSpace = SRGBColorSpace;
    s.scene.background = bg;
    s.scene.backgroundIntensity = 1;
    const floor = new Mesh(new PlaneGeometry(6, 6), new ShadowMaterial({ opacity: 0.45 }));
    floor.rotation.x = -Math.PI / 2; floor.position.y = 0.0002; floor.receiveShadow = true;
    s.scene.add(floor);
  }
  if (name === 'turn') await s.setColorway(arg);
  if (name === 'x') s.setExplode([0, 0.35, 0.65, 1][+arg]);
  s.onStage(stageName, true, 1);
  s.mount(stageName);
  const post = await import('./post.js');
  const q = new URLSearchParams(location.search);
  // ГРИП постера — по камере Blender (f/2,8, 100 мм, фокус на Ё): px на метр сенсора по sensor_fit, как у Cycles
  const vert = J.sensor_fit === 'VERTICAL';
  const pxPerSensorM = vert ? J.res[1] / (J.sensor_height_mm / 1000) : J.res[0] / (J.sensor_width_mm / 1000);
  const dof = name === 'hero' && q.get('dof') !== '0' ? { focus: J.focus_distance_m, fstop: +(q.get('N') || J.fstop || 2.8), lens: J.lens_mm / 1000,
    pxPerSensorM, maxR: +(q.get('mr') || 64), step: +(q.get('st') || 0.5) } : null;
  await s.enablePost(post, { dof });
  s.st.p = s.st.pT;
  await new Promise((r) => setTimeout(r, 600));
  s.invalidate();
  await new Promise((r) => setTimeout(r, 400));
  window.__capReady = true;
}
