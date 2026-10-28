# Сгенерировано run_recipes.py из 12-recipes/08-sequence-video-alpha.md — блоки «run: system» в напечатанном виде.

# ---- блок со строки 76
# run: system — Python 3 + Pillow + ffmpeg — [проверено] команды кодирования (3d 06/04 §2–3) на кадрах рецепта
import glob, json, os, subprocess
from PIL import Image
EX = os.path.dirname(os.path.abspath(__file__))  # перенос: папка примера
frames = sorted(glob.glob(f"{EX}/seq/f_*.png")); os.makedirs(f"{EX}/web/seq", exist_ok=True)
kb = lambda p: round(os.path.getsize(p) / 1024, 1)  # noqa: E731
tot = {"png": 0, "webp_q80": 0, "avif_q55": 0}
for f in frames:
    im = Image.open(f); b = os.path.basename(f)[:-4]; tot["png"] += os.path.getsize(f)
    im.save(p := f"{EX}/web/seq/{b}.webp", quality=80, method=6); tot["webp_q80"] += os.path.getsize(p)
    im.save(p := f"{EX}/web/seq/{b}.avif", quality=55, speed=6); tot["avif_q55"] += os.path.getsize(p)
IN = f"{EX}/seq/f_%04d.png"
STACK = "[0:v]format=pix_fmts=yuva444p[main];[main]split[main][alpha];[alpha]alphaextract[alpha];[main][alpha]vstack"
cmds = {"turn_vp9_alpha.webm": ["-pix_fmt", "yuva420p", "-c:v", "libvpx-vp9", "-crf", "40", "-b:v", "0", "-deadline", "good", "-row-mt", "1"],
        "turn_stacked_av1.mp4": ["-filter_complex", STACK, "-pix_fmt", "yuv420p", "-c:v", "libaom-av1", "-cpu-used", "6", "-crf", "40",
                                 "-b:v", "0", "-movflags", "+faststart"]}
video = {}
for name, args in cmds.items():
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "24", "-i", IN] + args + ["-an", f"{EX}/web/{name}"], check=True)
    video[name] = kb(f"{EX}/web/{name}")
res = {"frames": len(frames), "seq_total_kb": {k: round(v / 1024, 1) for k, v in tot.items()}, "video_kb": video}
json.dump(res, open(f"{EX}/web/sizes.json", "w"), ensure_ascii=False, indent=1)
print(res)
