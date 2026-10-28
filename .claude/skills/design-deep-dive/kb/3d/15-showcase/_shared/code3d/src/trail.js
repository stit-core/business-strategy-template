// trail.js · общий код 3D «Звена» (_shared/code3d) · приём 10 «след инструмента»: точка захвата оставляет короткий
// гаснущий след — «программируют рукой»: путь, который рука только что прошла (IK за курсором, «первое движение»).
// Кольцевой буфер точек (позиция + время рождения); точки — с равным шагом по пути (3,5 см): пунктир путевых точек (сплошная линия
// читалась «проволокой» рядом с кабелем). Шейдер точек: размер и яркость по возрасту, аддитивно, ниже порога bloom (3,4 HDR) — след не «горит» неоном.
// Жизнь 0,4 с: укладывается в хвост 0,45 с (0 кадров в покое, motion_check EG-A11Y-16/17). Один вызов на кадр.
import { BufferGeometry, BufferAttribute, Points, ShaderMaterial, AdditiveBlending, Color, Vector3 } from 'three';

export function createTrail({ max = 96, life = 0.4, size = 0.075, color = '#ff6a2a', k = 2.2, step = 0.035 } = {}) {
  const pos = new Float32Array(max * 3), born = new Float32Array(max).fill(-1e6);
  const g = new BufferGeometry();
  const aPos = new BufferAttribute(pos, 3), aBorn = new BufferAttribute(born, 1);
  g.setAttribute('position', aPos); g.setAttribute('born', aBorn);
  const c = new Color(color);
  const m = new ShaderMaterial({
    transparent: true, depthWrite: false, blending: AdditiveBlending, toneMapped: true,
    uniforms: { uNow: { value: 0 }, uLife: { value: life }, uSize: { value: size }, uPx: { value: 1 }, uCol: { value: new Vector3(c.r * k, c.g * k, c.b * k) } },
    vertexShader: `attribute float born; uniform float uNow, uLife, uSize, uPx; varying float vA;
      void main() { float a = clamp((uNow - born) / uLife, 0.0, 1.0); vA = 1.0 - a;
        vec4 mv = modelViewMatrix * vec4(position, 1.0); gl_Position = projectionMatrix * mv;
        gl_PointSize = a >= 1.0 ? 0.0 : uSize * uPx * (0.35 + 0.65 * vA) / -mv.z; }`,
    fragmentShader: `uniform vec3 uCol; varying float vA;
      void main() { vec2 d = gl_PointCoord - 0.5; float r = dot(d, d) * 4.0; if (r > 1.0) discard;
        gl_FragColor = vec4(uCol * vA * vA * (1.0 - r), 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const pts = new Points(g, m);
  pts.frustumCulled = false; pts.renderOrder = 3; pts.visible = false;
  let head = 0, last = null, lastT = -1e6, acc = 0;
  const tmp = new Vector3();
  function add(p, t) {
    pos[head * 3] = p.x; pos[head * 3 + 1] = p.y; pos[head * 3 + 2] = p.z; born[head] = t;
    head = (head + 1) % max;
  }
  return {
    mesh: pts,
    // p — мировая точка захвата сейчас, t — время (с); moving — рука движется (иначе новые точки не рождаются).
    // Точки — с равным шагом по пути (step): пунктир «путевых точек» записанной траектории, а не сплошная «проволока»
    push(p, t, moving) {
      if (moving && last) {
        const d = last.distanceTo(p);
        if (d > 1e-4 && d < 1.2) {                                     // скачок (смена сцены, мгновенная поза) — без линии через кадр
          let s0 = step - acc, n = 0;
          while (s0 <= d && n < 32) { add(tmp.copy(last).lerp(p, s0 / d), lastT + ((t - lastT) * s0) / d); s0 += step; n++; }
          acc = d - (s0 - step);
          if (n) { aPos.needsUpdate = true; aBorn.needsUpdate = true; }
        }
      } else acc = 0;
      if (!last) last = new Vector3();
      last.copy(p); lastT = t;
    },
    // true — след ещё виден (кадры нужны); px — половина высоты буфера рисования в пикселях (как scale у PointsMaterial)
    update(t, px) {
      m.uniforms.uNow.value = t; m.uniforms.uPx.value = px;
      let alive = false;
      for (let i = 0; i < max; i++) if (t - born[i] < life) { alive = true; break; }
      pts.visible = alive;
      return alive;
    },
    reset() { born.fill(-1e6); aBorn.needsUpdate = true; last = null; pts.visible = false; },
    dispose() { g.dispose(); m.dispose(); },
  };
}
