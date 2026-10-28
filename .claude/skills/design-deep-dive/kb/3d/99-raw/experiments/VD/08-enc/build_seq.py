#!/usr/bin/env python3
"""VD/08-enc — доставка облёта Blender для страницы b-blender той же лестницей, что у эталона нейросети
(ai-media-research/99-raw/experiments/B/10-scrub-delivery/build_scrub.py — прочитан, не запускался): три секвенции кадров
(AVIF 1280 q55 s6 4:2:0, WebP 1280 q76, AVIF 960 q55), шесть видео (AV1 CRF 32 / H.264 CRF 22, GOP 1 / 4 / 8, BT.709 с
полными тегами, без звука, faststart), постер из кадра 0 рендера (PNG → Pillow → AVIF q55 / WebP q82), manifest.json
в той же схеме (+ встраивание в HTML делает страница). Кодеры — те же сборки: avifenc 1.4.2, cwebp 1.6.0 (копия в VD/tools/bin),
ffmpeg 7.1.5 (SVT-AV1 preset 8, lp=2; x264 preset slow).

Отличия от эталона — по делу: исходник — PNG sRGB без потерь из Cycles (не видео), поэтому кадры кодируются из PNG прямо,
матрица входа — RGB → BT.709 (у Kling — BT.601 → BT.709); видео 12 к/с (61 кадр = 5,08 с, как 5,04 с эталона при 24 к/с и
каждом 2-м кадре). Круг 360°: 72 кадра через 5° → порядок −180°…+180° (фас в середине, точка покоя 0,5) + замыкающий кадр
(73 файла), чтобы край ползунка = спина флакона с обеих сторон.

    python3 build_seq.py arc  SRC_DIR TAG OUT_DIR       # 61 кадр дуги 25° → OUT_DIR (assets/)
    python3 build_seq.py full SRC_DIR TAG OUT_DIR       # 72 кадра круга → OUT_DIR (assets/full360/)
    [--only frames|video|poster|manifest] [--threads 4]
Результаты: OUT_DIR/manifest.json, results_<mode>.json рядом со скриптом (вес, SSIM к PNG, время)."""
import json
import os
import shutil
import subprocess
import sys
import time

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(os.path.dirname(HERE), "tools", "bin")
TMP = "/tmp/claude-1000/-home-mm-----------app-design/d8f53347-66a5-40ec-a709-75f4623c7b47/scratchpad/vd3enc"  # VD3: своя временная папка
TAGS = ("scale=out_color_matrix=bt709:out_range=tv,"
        "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv")
META = ["-movflags", "+faststart"]
VIDEO = [("orbit-h264-g1", "h264", 1, 22), ("orbit-h264-g4", "h264", 4, 22), ("orbit-h264-g8", "h264", 8, 22),
         ("orbit-av1-g1", "av1", 1, 32), ("orbit-av1-g4", "av1", 4, 32), ("orbit-av1-g8", "av1", 8, 32)]
SEQ = [("seq-avif-1280", "avif", 1280, 55), ("seq-webp-1280", "webp", 1280, 76), ("seq-avif-960", "avif", 960, 55)]
FPS = 12


def ordered_sources(mode, src, tag):
    """Список PNG в порядке показа. arc: 000…060. full: 72 кадра (0°, 5°, …, 355°) → −180°…+180° с замыканием (73)."""
    fs = sorted(f for f in os.listdir(src) if f.startswith(tag + "_") and f[len(tag) + 1:len(tag) + 4].isdigit()
                and f.endswith(".png") and "_mask" not in f)
    if mode == "arc":
        return [os.path.join(src, f) for f in fs]
    n = len(fs)
    half = n // 2
    order = [fs[(half + i) % n] for i in range(n)] + [fs[half]]
    return [os.path.join(src, f) for f in order]


def run(cmd):
    t0 = time.time()
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return round(time.time() - t0, 2)


def stage_pngs(srcs):
    """Кадры в TMP с номерами 000… (для ffmpeg image2) — копии, без перекодирования."""
    d = os.path.join(TMP, "png")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    for i, s in enumerate(srcs):
        shutil.copy(s, os.path.join(d, f"f{i:03d}.png"))
    return os.path.join(d, "f%03d.png")


def ssim(path, pattern):
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-framerate", str(FPS), "-i", pattern, "-lavfi",
                        "[0:v]format=yuv420p[a];[1:v]scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[b];[a][b]ssim",
                        "-f", "null", "-"], capture_output=True, text=True)
    line = [ln for ln in r.stderr.splitlines() if "SSIM Y:" in ln]
    return float(line[-1].split("All:")[1].split()[0]) if line else None


def frames_types(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames", "-show_entries", "frame=key_frame",
                        "-of", "json", path], capture_output=True, text=True)
    k = [f.get("key_frame") for f in json.loads(r.stdout).get("frames", [])]
    return {"frames": len(k), "keyframes": k.count(1)}


def build_video(res, pattern, out, threads):
    for name, codec, g, crf in VIDEO:
        o = os.path.join(out, f"{name}.mp4")
        if codec == "h264":
            enc = ["-vf", f"{TAGS},format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
                   "-g", str(g), "-keyint_min", str(g), "-sc_threshold", "0", "-profile:v", "high"]
        else:
            enc = ["-vf", f"{TAGS},format=yuv420p10le", "-c:v", "libsvtav1", "-preset", "8", "-crf", str(crf),
                   "-g", str(g), "-svtav1-params", f"lp=2:keyint={g}"]
        secs = run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", pattern, "-an", "-threads", str(threads),
                    *enc, "-r", str(FPS), *META, o])
        row = {"codec": codec, "gop": g, "crf": crf, "kb": round(os.path.getsize(o) / 1024, 1), "secs": secs,
               "ssim_all": ssim(o, pattern), **frames_types(o)}
        res["video"][name] = row
        print(name, row, flush=True)


def build_frames(res, srcs, out, threads):
    os.makedirs(TMP, exist_ok=True)
    for folder, fmt, w, q in SEQ:
        d = os.path.join(out, folder)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        tot, t0 = 0, time.time()
        for i, s in enumerate(srcs):
            im = Image.open(s).convert("RGB")
            if im.width != w:
                im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            tmp_png = os.path.join(TMP, "_r.png")
            im.save(tmp_png)
            o = os.path.join(d, f"f{i:03d}.{fmt}")
            if fmt == "avif":
                subprocess.run([os.path.join(BIN, "avifenc"), "-q", str(q), "-s", "6", "-y", "420", "-j", str(threads), tmp_png, o],
                               check=True, capture_output=True)
            else:
                subprocess.run([os.path.join(BIN, "cwebp"), "-q", str(q), "-m", "6", "-sharp_yuv", tmp_png, "-o", o],
                               check=True, capture_output=True)
            tot += os.path.getsize(o)
        mid = len(srcs) // 2
        fm = os.path.join(d, f"f{mid:03d}.{fmt}")
        dec = []
        for _ in range(5):
            t1 = time.time()
            if fmt == "avif":
                subprocess.run([os.path.join(BIN, "avifdec"), "-j", "1", fm, os.path.join(TMP, "_d.png")], check=True, capture_output=True)
            else:
                subprocess.run([os.path.join(BIN, "dwebp"), fm, "-o", os.path.join(TMP, "_d.png")], check=True, capture_output=True)
            dec.append((time.time() - t1) * 1000)
        dec.sort()
        h = round(720 * w / 1280)
        row = {"format": fmt, "width": w, "q": q, "frames": len(srcs), "total_kb": round(tot / 1024, 1),
               "per_frame_kb": round(tot / 1024 / len(srcs), 1), "secs": round(time.time() - t0, 1),
               "decode_cli_ms_median_incl_png_write": round(dec[2], 1),
               "decoded_mb_in_memory_rgba": round(len(srcs) * w * h * 4 / 2 ** 20)}
        res["frames"][folder] = row
        print(folder, row, flush=True)


def build_poster(res, out, src0):
    """Постер = кадр 0 рендера (PNG → Pillow → AVIF q55 s6 / WebP q82 m6). У эталона — кадр 0 AV1 GOP 4 (его умолчание
    на касании); у нас на десктопе постер сменяет секвенция AVIF: из AV1 постер темнее исходника на 1,5 уровня (из PNG —
    0,6), поэтому берём PNG (проба 08-enc, 25.09)."""
    im = Image.open(src0).convert("RGB")
    im.save(os.path.join(out, "poster.avif"), quality=55, speed=6)
    im.save(os.path.join(out, "poster.webp"), quality=82, method=6)
    res["poster"] = {"avif_kb": round(os.path.getsize(os.path.join(out, "poster.avif")) / 1024, 1),
                     "webp_kb": round(os.path.getsize(os.path.join(out, "poster.webp")) / 1024, 1)}
    print("poster", res["poster"], flush=True)


def render_spp(src, tag):
    """Сэмплы рендера — из статистики пачек velmora.py (<tag>_stats_*.json); VD3: у круга может быть 64, у дуги 128."""
    spp = set()
    for f in os.listdir(src):
        if f.startswith(tag + "_stats") and f.endswith(".json"):
            try:
                st = json.load(open(os.path.join(src, f)))
            except (OSError, ValueError):
                continue
            if st.get("views"):
                spp.add(int(st.get("samples", 0)))
    return "/".join(str(x) for x in sorted(spp)) or "?"


def build_manifest(mode, out, prefix, n_src, spp="128"):
    """Та же схема, что у эталона; пути — относительно страницы (prefix: 'assets' или 'assets/full360')."""
    n = n_src
    k = n_src - 1                  # круг: различных кадров (последний — замыкающий); VD3: 36 через 10° или 72 через 5°
    arc = "25° + наезд 12 %, 61 кадр" if mode == "arc" else f"полный круг 360°, {k} кадр{'а' if k % 10 in (2, 3, 4) and k % 100 not in (12, 13, 14) else 'ов'} через {360 / k:g}° (порядок −180°…+180°)"
    man = {"source": f"Blender 5.2.2 · Cycles {spp} спп + OIDN · {arc} · 0 ₽ · {time.strftime('%d.%m.%Y')}", "fps": FPS, "frames_video": n,
           "duration": round(n / FPS, 4), "step": 1, "video": {}, "frames": {}}
    for name, codec, g, crf in VIDEO:
        p = os.path.join(out, f"{name}.mp4")
        if not os.path.exists(p):
            continue
        man["video"][name] = {"src": f"{prefix}/{name}.mp4", "codec": codec, "gop": g, "crf": crf, "bytes": os.path.getsize(p),
                              "type": 'video/mp4; codecs="av01.0.05M.10"' if codec == "av1" else 'video/mp4; codecs="avc1.64001f"'}
    for folder, fmt, w, q in SEQ:
        d = os.path.join(out, folder)
        if not os.path.isdir(d):
            continue
        fs = sorted(os.listdir(d))
        man["frames"][folder] = {"pattern": f"{prefix}/{folder}/f{{i}}.{fmt}", "count": len(fs), "format": fmt, "width": w,
                                 "height": round(720 * w / 1280), "bytes": sum(os.path.getsize(os.path.join(d, f)) for f in fs)}
    json.dump(man, open(os.path.join(out, "manifest.json"), "w"), ensure_ascii=False, indent=1)
    return man


def main():
    a = sys.argv[1:]
    if len(a) < 4:
        print(__doc__)
        return 2
    mode, src, tag, out = a[:4]
    only = a[a.index("--only") + 1] if "--only" in a else "all"
    threads = int(a[a.index("--threads") + 1]) if "--threads" in a else 4
    os.makedirs(out, exist_ok=True)
    srcs = ordered_sources(mode, src, tag)
    print("кадров:", len(srcs), os.path.basename(srcs[0]), "…", os.path.basename(srcs[-1]))
    rp = os.path.join(HERE, f"results_{mode}.json")
    res = json.load(open(rp)) if os.path.exists(rp) else {}
    res.setdefault("video", {})
    res.setdefault("frames", {})
    res["source"] = {"dir": src, "tag": tag, "mode": mode, "frames": len(srcs), "date": time.strftime("%Y-%m-%d %H:%M")}
    t0 = time.time()
    pattern = stage_pngs(srcs)
    if only in ("all", "frames"):
        build_frames(res, srcs, out, threads)
    if only in ("all", "video"):
        build_video(res, pattern, out, threads)
    if only in ("all", "poster") and mode == "arc":
        build_poster(res, out, srcs[0])
    prefix = "assets" if mode == "arc" else "assets/full360"
    res["spp"] = render_spp(src, tag)
    res["manifest"] = build_manifest(mode, out, prefix, len(srcs), res["spp"])
    res["total_secs"] = round(time.time() - t0, 1)
    json.dump(res, open(rp, "w"), ensure_ascii=False, indent=1)
    print("готово за", res["total_secs"], "с →", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
