"""assets_b.py — ассеты B/C фазы 2 из рендера v2: десктопный кадр (4 ширины, AVIF/WebP), телефонный портретный кадр (вырезка
того же рендера — та же плотность, та же камера), координаты булавок и якоря подписей комнат (площади по геометрии)."""
import json, math, os
from PIL import Image
R = "/home/mm/Документы/app-design/blender-research"; X = f"{R}/99-raw/experiments/SD"; V = f"{X}/renders/v2"
OUT = f"{X}/pagebuild/assets"; os.makedirs(OUT, exist_ok=True)
mk = json.load(open(f"{V}/B2_marks.json")); cam = mk["camera"]; FR = mk["frame_uw"]; W, H = mk["res"]
ppm = W / (FR["u1"] - FR["u0"])
def uv_px(p):
    x, y, z = p
    u = (x - y) / math.sqrt(2); w = (x + y) * 0.408248 + z * 0.816497
    return (u - FR["u0"]) * ppm, (FR["w1"] - w) * ppm
# проверка своей проекции по Blender (головка 1)
h1 = mk["marks"]["1"]; px, py = uv_px((2.5, 4.25, 1.52)); assert abs(px - h1["head_u"] * W) < 1.5 and abs(py - h1["head_v"] * H) < 1.5, (px, py)
im = Image.open(f"{V}/B2.png").convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im); flat = bg.convert("RGB")
sizes = {}
def enc(img, base, widths):
    for w in widths:
        fr = img if w == img.width else img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
        for ext, kw in (("avif", {"quality": 60}), ("webp", {"quality": 80, "method": 6})):
            p = f"{OUT}/{base}-{w}.{ext}"; fr.save(p, ext.upper(), **kw); sizes[os.path.basename(p)] = round(os.path.getsize(p) / 1024, 1)
enc(flat, "iso-desk", (720, 1080, 1440, 1800))
# телефон: u −3,3…3,4, w −0,4…8,0 (все 4 булавки, портрет ≈ 0,8)
MU0, MU1, MW0, MW1 = -3.3, 3.4, -0.4, 8.0
cx0, cx1 = (MU0 - FR["u0"]) * ppm, (MU1 - FR["u0"]) * ppm
cy0, cy1 = (FR["w1"] - MW1) * ppm, (FR["w1"] - MW0) * ppm
crop = flat.crop((round(cx0), round(cy0), round(cx1), round(cy1)))
enc(crop, "iso-mob", (390, 780, 1170))
pins = {}
for k, m in mk["marks"].items():
    hx, hy = m["head_u"] * W, m["head_v"] * H
    pins[k] = {"x": round(hx / W * 100, 2), "y": round(hy / H * 100, 2),
               "xm": round((hx - cx0) / (cx1 - cx0) * 100, 2), "ym": round((hy - cy0) / (cy1 - cy0) * 100, 2), "what": m["what"]}
rooms_w = {"Гостиная": ("14,6 м²", (3.2, 5.85, 0.0)), "Спальня": ("11,3 м²", (6.6, 5.3, 0.0)), "Коридор": ("8,3 м²", (6.2, 3.5, 0.0)),
           "Прихожая": ("11,2 м²", (3.0, 2.05, 0.0)), "С/у": ("4,1 м²", (5.7, 1.95, 0.0))}
# SD2: «С/у» была на (4,8; 0,46; 0,56) — срез южной стены у правого края кадра (92,7 %). Видимый пол санузла начинается за
# тенью перегородки w2: точка пола видна, если x − 4,39 > 1,1 (срез 1,1 м, подъём луча = расстояние по оси) → x ≥ 5,5;
# (5,7; 1,95) — пол между раковиной и ванной, 87,8 % × 59,1 % кадра, над полотном двери d4 (зазор 0,1 м)
rooms = {}
for nm, (area, p) in rooms_w.items():
    x, y = uv_px(p)
    if 0 < x < W * 0.97 and 0 < y < H:
        rooms[nm] = {"area": area, "x": round(x / W * 100, 2), "y": round(y / H * 100, 2)}
meta = {"desk": {"w": W, "h": H, "frame_uw": FR}, "mob": {"w": crop.width, "h": crop.height, "crop_px": [round(cx0), round(cy0), round(cx1), round(cy1)],
        "frame_uw": [MU0, MU1, MW0, MW1]}, "pins": pins, "rooms": rooms, "sizes_kb": sizes}
json.dump(meta, open(f"{OUT}/assets_b.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(meta, ensure_ascii=False)[:1800])
