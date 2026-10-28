// proxy.js — адаптер до загрузки 3D: помнит расцветку, поворот и разборку; после attach() передаёт всё в 3D-сцену.
export function makeProxy() {
  const st = { cw: 'snow', turn: 0, p: 0, stages: {} };
  let s = null;
  return {
    attach(stage) {
      s = stage;
      s.setColorway(st.cw); s.setTurn(st.turn, false); s.setExplode(st.p);
      for (const [n, [on, r]] of Object.entries(st.stages)) s.onStage(n, on, r);
    },
    press(id, down) { s?.press(id, down); },
    yo() { s?.yo(); },
    hitTest(stage, x, y) { return s ? s.hitTest(stage, x, y) : null; },
    setColorway(cw) { st.cw = cw; s?.setColorway(cw); },
    setTurn(a, smooth) { st.turn = a; s?.setTurn(a, smooth); },
    setExplode(p) { st.p = p; s?.setExplode(p); },
    onStage(n, on, r) { st.stages[n] = [on, r]; s?.onStage(n, on, r); },
  };
}
