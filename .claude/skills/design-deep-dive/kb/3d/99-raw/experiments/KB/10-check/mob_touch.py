#!/usr/bin/env python3
"""mob_touch.py — телефон 390×844 (касание): набор касанием по картинке в окне левой половины + кнопка «Правая половина».
    python3 mob_touch.py PAGE_DIR OUT_DIR   → «ёлка» касаниями (Ё, → Л, ← К, А), снимки, размер клавиши в CSS px.
"""
import json, os, shutil, signal, socket, subprocess, sys, time
from playwright.sync_api import sync_playwright
R = "/home/mm/Документы/app-design/blender-research"
SCR = "/tmp/claude-1000/-home-mm-----------app-design/d8f53347-66a5-40ec-a709-75f4623c7b47/scratchpad/kb3"
GPU = ["--use-gl=angle", "--use-angle=gl", "--ignore-gpu-blocklist", "--enable-gpu"]
PAGE, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
PORT = int(os.environ.get("KB_PORT", "8793"))
os.makedirs(OUT, exist_ok=True)
TK = json.load(open(f"{R}/99-raw/experiments/KB/07-b/cams/T_keys.json"))
copy = os.path.join(SCR, "kb_serve_mt_" + os.path.basename(PAGE)); shutil.rmtree(copy, ignore_errors=True); shutil.copytree(PAGE, copy)
srv = subprocess.Popen([sys.executable, f"{R}/99-raw/experiments/F1/02-hero-variants/serve_br.py", copy, str(PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(240):
    try: socket.create_connection(("127.0.0.1", PORT), timeout=0.2).close(); break
    except OSError: time.sleep(0.25)
log = {"errors": [], "console": []}
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, args=GPU)
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: log["errors"].append(str(e)[:300]))
        pg.on("console", lambda m: log["console"].append(f"{m.type}: {m.text}"[:300]))
        pg.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load"); pg.wait_for_timeout(800)
        pg.evaluate("(()=>{const el=document.querySelector('#typed'); window.scrollTo(0, el.getBoundingClientRect().top + scrollY - 40);})()")
        pg.wait_for_timeout(5000)
        def key_xy(kid):
            fr = pg.evaluate("(()=>{const r=document.querySelector('#stage-type .frame').getBoundingClientRect(); const s=document.querySelector('#stage-type').getBoundingClientRect(); return [r.left,r.top,r.width,r.height,s.left,s.top,s.width,s.height]})()")
            k = TK["keys"][kid]; W, H = TK["res"]
            return fr[0] + k["x"] / W * fr[2], fr[1] + k["y"] / H * fr[3], fr
        x, y, fr = key_xy("yo")
        log["frame_rect"] = fr; log["key_css_px"] = round(82 * fr[2] / 1600, 1)
        pg.screenshot(path=os.path.join(OUT, "t0_left.png"))
        def tap(kid):
            x, y, _ = key_xy(kid); pg.touchscreen.tap(x, y); pg.wait_for_timeout(260); return [round(x), round(y)]
        log["tap_yo"] = tap("yo")
        pg.click("#half"); pg.wait_for_timeout(900)
        log["scroll_after_half"] = pg.evaluate("document.querySelector('#stage-type').scrollLeft")
        log["half_label"] = pg.inner_text("#half")
        pg.screenshot(path=os.path.join(OUT, "t1_right.png"))
        log["tap_k"] = tap("k")
        pg.click("#half"); pg.wait_for_timeout(900)
        log["tap_r"] = tap("r"); log["tap_f"] = tap("f")
        # свайп по сцене не должен печатать
        x, y, _ = key_xy("s")
        pg.evaluate("""([x,y])=>{const el=document.querySelector('#stage-type');
          const mk=(t,xx)=>new PointerEvent(t,{pointerId:7,pointerType:'touch',clientX:xx,clientY:y,bubbles:true});
          el.dispatchEvent(mk('pointerdown',x)); el.dispatchEvent(mk('pointercancel',x+60));}""", [x, y])
        pg.wait_for_timeout(300)
        log["typed"] = pg.inner_text("#typed-text")
        pg.screenshot(path=os.path.join(OUT, "t2_typed.png"))
        log["kb"] = pg.evaluate("window.__kb || null")
        ctx.close(); b.close()
finally:
    srv.send_signal(signal.SIGTERM); srv.wait(timeout=5)
json.dump(log, open(os.path.join(OUT, "mob_touch.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: log.get(k) for k in ("typed", "key_css_px", "scroll_after_half", "half_label", "errors")}, ensure_ascii=False))
