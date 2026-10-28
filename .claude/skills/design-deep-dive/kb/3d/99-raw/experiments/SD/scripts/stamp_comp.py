"""stamp_comp.py — дообработка клипа штампа «СДАНО» (дорожка SD, итерация SD2).

Кадры Cycles (RGBA: штамп + тень ловца теней) → оттиск по плоскости листа (аффинное отображение «мм листа → пиксели» из
stamp_clip.json: матрица камеры параллельна листу, перекоса нет) с кадра касания → «запекание» на белый #ffffff (на странице
клип лежит с mix-blend-mode: multiply — белое исчезает и на бумаге акта, и на фоне секции) → окно у краёв кадра (тень и свод
гаснут к краю, дальняя тень свода гаснет по расстоянию от силуэта штампа: у края и вдали от штампа ровно #fff, иначе
на странице проступил бы прямоугольник клипа) → кодирование:
  stamp.webm  — VP9 (основной, Chrome/Firefox/Safari 17+), без звука, yuv420p, BT.709;
  stamp.mp4   — H.264 High (запас: старые Safari), faststart;
  stamp-start.webp / stamp-end.webp — первый (штамп на месте, оттиска нет) и последний кадр (штамп на месте + оттиск);
  конечный кадр = состояние без JS и в reduce.
    python3 stamp_comp.py RENDER_DIR OUT_ASSETS_DIR [--crf-vp9 36] [--crf-264 26]"""
import json
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image
from scipy import ndimage

PPM_INK = 12.0          # px/мм текстуры оттиска (stamp_tex.py)
INK_MM = (90.0, 40.0)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ink_layer(meta, ink, res):
    """Альфа оттиска в кадре: для пикселя p — точка листа x = M⁻¹(p − o), поворот на −rz вокруг центра оттиска,
    координаты текстуры (u, v) = ((x′ + 45)·12, (20 − y′)·12). PIL.Image.transform(AFFINE): выход → вход."""
    mp = meta["mapping_px"]
    o = np.array(mp["o"]); ex = (np.array(mp["x10"]) - o) / 10.0; ey = (np.array(mp["y10"]) - o) / 10.0
    M = np.array([[ex[0], ey[0]], [ex[1], ey[1]]])            # мм → px
    Mi = np.linalg.inv(M)
    imp = meta["imp"]
    a = np.radians(-imp["rz"])
    Rm = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])  # поворот листа → оси оттиска
    c = np.array([imp["x"], imp["y"]])
    # u = 12·( (R·(Mi·(p − o) − c)).x + 45 ),  v = 12·(20 − (R·(Mi·(p − o) − c)).y)
    A = Rm @ Mi
    t = -A @ o - Rm @ c
    S = np.array([[PPM_INK, 0.0], [0.0, -PPM_INK]])
    B = S @ A
    tt = S @ t + np.array([INK_MM[0] / 2 * PPM_INK, INK_MM[1] / 2 * PPM_INK])
    data = (B[0, 0], B[0, 1], tt[0], B[1, 0], B[1, 1], tt[1])
    al = ink.getchannel("A").transform(res, Image.AFFINE, data, resample=Image.BICUBIC, fillcolor=0)
    return np.asarray(al).astype(np.float64) / 255.0


def main():
    a = sys.argv[1:]
    rdir, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    crf9 = int(a[a.index("--crf-vp9") + 1]) if "--crf-vp9" in a else 36
    crf4 = int(a[a.index("--crf-264") + 1]) if "--crf-264" in a else 26
    t0 = time.time()
    meta = json.load(open(f"{rdir}/stamp_clip.json"))
    W, H = meta["res"]
    NF, fps, contact = meta["frames"], meta["fps"], meta["contact_frame"]
    copies = {int(k): v for k, v in meta["copies"].items()}
    ink = Image.open(f"{rdir}/stamp_ink.png").convert("RGBA")
    ink_a = ink_layer(meta, ink, (W, H))
    ink_rgb = np.array(ink.getpixel((ink.width // 2, ink.height // 2))[:3], np.float64) / 255.0
    # окно у краёв: по 5 % ширины/высоты → 0 на самом краю (объект туда не заходит — проверяется ниже)
    yy, xx = np.mgrid[0:H, 0:W]
    ex_, ey_ = 0.05 * W, 0.05 * H
    win = smoothstep(0, ex_, xx + 0.5) * smoothstep(0, ex_, W - xx - 0.5) * smoothstep(0, ey_, yy + 0.5) * smoothstep(0, ey_, H - yy - 0.5)
    band = win < 0.999
    cdir = f"{rdir}/comp"
    os.makedirs(cdir, exist_ok=True)
    worst_band_alpha = 0.0
    edge_de = []
    for f in range(NF):
        src = copies.get(f, f)
        im = np.asarray(Image.open(f"{rdir}/frames/f{src:03d}.png").convert("RGBA")).astype(np.float64) / 255.0
        A = im[..., 3]
        worst_band_alpha = max(worst_band_alpha, float((A[band] > 0.9).sum()))          # пикселей штампа в полосе окна
        # дальняя тень свода гаснет по расстоянию от силуэта штампа (как у иконок): у штампа тень сохраняется (≤ 0,25 H),
        # дальше exp(−(d − 0,25 H)/0,12 H) — бумага вдали ровно белая, прямоугольник клипа на странице не проступает
        obj = A > 0.95
        if obj.any():
            dist = ndimage.distance_transform_edt(~obj)
            A = np.where(obj, A, A * np.where(dist < 0.25 * H, 1.0, np.exp(-(dist - 0.25 * H) / (0.12 * H))))
        A = A * win
        base = np.ones((H, W, 3))
        if f >= contact:
            ia = ink_a[..., None]
            base = base * (1 - ia) + ink_rgb * ia
        rgb = im[..., :3] * A[..., None] + base * (1 - A[..., None])
        fr = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
        if H % 2:                                              # H.264/VP9 4:2:0 — чётные стороны: добить белой строкой снизу
            fr = np.concatenate([fr, np.full((1, W, 3), 255, np.uint8)], 0)
        Image.fromarray(fr).save(f"{cdir}/f{f:03d}.png")
        ring = np.concatenate([fr[0], fr[-1], fr[:, 0], fr[:, -1]]).astype(np.int32)
        edge_de.append(int(255 - ring.min()))
    # кодирование
    res = {}
    color = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
    vp9 = ["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{cdir}/f%03d.png", "-c:v", "libvpx-vp9",
           "-pix_fmt", "yuv420p", "-crf", str(crf9), "-b:v", "0", "-row-mt", "1", "-deadline", "good", "-cpu-used", "1",
           "-g", str(NF), "-an", *color, f"{out}/stamp.webm"]
    h264 = ["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{cdir}/f%03d.png", "-c:v", "libx264",
            "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", str(crf4), "-preset", "slow", "-movflags", "+faststart",
            "-an", *color, f"{out}/stamp.mp4"]
    for nm, cmd in (("webm", vp9), ("mp4", h264)):
        t1 = time.time()
        subprocess.run(cmd, check=True)
        res[nm] = {"kb": round(os.path.getsize(f"{out}/stamp.{'webm' if nm == 'webm' else 'mp4'}") / 1024, 1),
                   "enc_s": round(time.time() - t1, 1)}
    for nm, f in (("start", 0), ("end", NF - 1)):
        im = Image.open(f"{cdir}/f{f:03d}.png")
        im.save(f"{out}/stamp-{nm}.webp", "WEBP", quality=86, method=6)
        res[f"{nm}_webp_kb"] = round(os.path.getsize(f"{out}/stamp-{nm}.webp") / 1024, 1)
    # декодированный VP9: последний кадр против PNG (ΔE) и край кадра
    dec = f"{rdir}/comp_dec_last.png"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-sseof", "-0.1", "-i", f"{out}/stamp.webm", "-frames:v", "1", dec], check=True)
    d = np.asarray(Image.open(dec).convert("RGB")).astype(np.int32)
    p = np.asarray(Image.open(f"{cdir}/f{NF - 1:03d}.png").convert("RGB")).astype(np.int32)
    res["vp9_last_vs_png_mean_abs"] = round(float(np.abs(d - p).mean()), 2)
    res["vp9_edge_min"] = int(np.concatenate([d[0], d[-1], d[:, 0], d[:, -1]]).min())
    # бумага вдали от штампа и оттиска в последнем кадре (PNG): доля пикселей < 254 и минимум
    pl = np.asarray(Image.open(f"{cdir}/f{NF - 1:03d}.png").convert("L")).astype(np.int32)
    far = ndimage.distance_transform_edt(pl > 250) > 0.3 * H
    res["paper_far_min"] = int(pl[far].min()) if far.any() else None
    res["paper_far_pct_below_254"] = round(float((pl[far] < 254).mean() * 100), 2) if far.any() else None
    res.update({"frames": NF, "fps": fps, "duration_s": round(NF / fps, 3), "res": [W, H + H % 2], "contact_frame": contact,
                "edge_min_png_by_frame_max_drop": max(edge_de), "object_px_in_edge_band_max": int(worst_band_alpha),
                "comp_s": round(time.time() - t0, 1), "crf": {"vp9": crf9, "h264": crf4}})
    json.dump(res, open(f"{rdir}/stamp_web.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
