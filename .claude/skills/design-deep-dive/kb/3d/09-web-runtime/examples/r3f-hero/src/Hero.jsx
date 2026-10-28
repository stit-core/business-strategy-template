// R3F 9.8 + drei 10.7.8 + three r186 — hero-сцена для React-проекта
import { createRoot } from 'react-dom/client';
import { Suspense, useEffect, useLayoutEffect, useState } from 'react';
import * as THREE from 'three';
import { Canvas, useThree } from '@react-three/fiber';
import { useGLTF, Center, Environment, Lightformer, ContactShadows, Float, PresentationControls } from '@react-three/drei';

const params = new URLSearchParams(location.search);
const MODEL = params.get('model') || './sculpture.glb';
const reduceMQ = matchMedia('(prefers-reduced-motion: reduce)');

function useReducedMotion() {
  const [reduce, setReduce] = useState(reduceMQ.matches);
  useEffect(() => {
    const on = () => setReduce(reduceMQ.matches);
    reduceMQ.addEventListener('change', on);
    return () => reduceMQ.removeEventListener('change', on);
  }, []);
  return reduce;
}

// Стоп рендера вне экрана и в скрытой вкладке: frameloop 'never', при возврате — прежний режим и один кадр
function PauseWhenHidden({ mode }) {
  const { gl, setFrameloop, invalidate } = useThree();
  useEffect(() => {
    let visible = true;
    const apply = () => { setFrameloop(visible && !document.hidden ? mode : 'never'); invalidate(); };
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; apply(); });
    io.observe(gl.domElement);
    document.addEventListener('visibilitychange', apply);
    apply();
    return () => { io.disconnect(); document.removeEventListener('visibilitychange', apply); };
  }, [gl, mode, setFrameloop, invalidate]);
  return null;
}

function Model() {
  const { scene } = useGLTF(MODEL);          // drei → GLTFLoader + MeshoptDecoder из three-stdlib
  return <Center><primitive object={scene} /></Center>;   // Center: центр габарита модели → в 0
}

// Служебное: флаг готовности, сведения для замера и bench (N кадров с readPixels → мс/кадр)
function Probe() {
  const { gl, scene, camera } = useThree();
  useLayoutEffect(() => {
    const ctx = gl.getContext(); const px = new Uint8Array(4);
    window.__bench = (n = 120) => {
      const t = [];
      for (let i = 0; i < n + 5; i++) {
        const t0 = performance.now(); gl.render(scene, camera);
        ctx.readPixels(0, 0, 1, 1, ctx.RGBA, ctx.UNSIGNED_BYTE, px);
        if (i >= 5) t.push(performance.now() - t0);
      }
      t.sort((a, b) => a - b);
      return { frames: n, ms_avg: +(t.reduce((a, b) => a + b, 0) / n).toFixed(2), ms_p95: +t[Math.floor(n * 0.95)].toFixed(2),
        px: [gl.domElement.width, gl.domElement.height] };
    };
    requestAnimationFrame(() => requestAnimationFrame(() => {
      window.__info = { three: THREE.REVISION, toneMapping: gl.toneMapping, outputColorSpace: gl.outputColorSpace,
        dpr: gl.getPixelRatio(), shadowMap: gl.shadowMap.enabled, calls: gl.info.render.calls, triangles: gl.info.render.triangles,
        programs: gl.info.programs ? gl.info.programs.length : null };
      window.__ready = true;
    }));
  }, [gl, scene, camera]);
  return null;
}

function Hero() {
  const reduce = useReducedMotion();
  const mode = reduce ? 'demand' : 'always';     // reduce → кадр только по запросу (0 draw calls в покое)
  return (
    <Canvas
      frameloop={mode}
      dpr={[1, 1.5]}                              // потолок DPR 1,5 (телефон)
      camera={{ position: [0, 0.15, 2.3], fov: 30 }}
      gl={{ toneMapping: THREE.NeutralToneMapping }}  // вместо ACES по умолчанию у R3F — ближе к цвету бренда
      onCreated={({ gl }) => gl.domElement.setAttribute('aria-hidden', 'true')}
    >
      <PauseWhenHidden mode={mode} />
      <Suspense fallback={null}>
        <PresentationControls global snap polar={[-0.15, 0.25]} azimuth={[-0.7, 0.7]} enabled={!reduce}>
          <Float speed={reduce ? 0 : 1.4} rotationIntensity={reduce ? 0 : 0.35} floatIntensity={reduce ? 0 : 0.5}>
            <Model />
          </Float>
        </PresentationControls>
        <ContactShadows position={[0, -0.335, 0]} opacity={0.5} scale={3} blur={2.4} far={1} resolution={256} frames={1} color="#3b2f5a" />
        {/* Окружение без файлов: студия из Lightformer, снимается кубокамерой один раз (frames = 1) */}
        <Environment resolution={256}>
          <Lightformer form="rect" intensity={3} position={[0, 4, -3]} scale={[8, 3, 1]} />
          <Lightformer form="rect" intensity={1.5} position={[-4, 1, 1]} rotation-y={Math.PI / 2} scale={[4, 6, 1]} />
          <Lightformer form="rect" intensity={1} position={[4, 0.5, 2]} rotation-y={-Math.PI / 2} scale={[4, 4, 1]} color="#ffe2c4" />
          <Lightformer form="ring" intensity={2} position={[0, 2, 4]} scale={2} />
        </Environment>
        <Probe />
      </Suspense>
    </Canvas>
  );
}

export function mount(el) { createRoot(el).render(<Hero />); }
