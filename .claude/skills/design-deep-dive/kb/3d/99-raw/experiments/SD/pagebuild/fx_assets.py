"""fx_assets.py — данные «фонарика инженера» (C, ветка L1) из проходов Blender (renders/v2, run_v2.py / passes_convert.py).

  fx-albedo.webp — проход Diffuse Color (альбедо, sRGB), 1440 × 1524, WebP q85 (с потерями — цвет);
  fx-ao.webp     — AO 450 × 476 (медиана 3 + гаусс σ 1,6 на половинном, ×½, серый WebP q80): нужен только для
                   «отражённого» света фонаря в углах — плавный, четверти разрешения хватает (альфа альбедо весила бы +50…185 КБ);
  fx-nh.webp     — одна текстура без потерь 900 × 952 RGB: R, G — нормаль в пространстве камеры (x, y; z = √(1 − x² − y²),
                   видимые грани смотрят на камеру), B — ВЫСОТА точки над полом h (8 бит, −0,02…1,78 м, шаг 7 мм).
                   (SD2 хранил в A «теневую» экранную высоту — тень по ней давала «кольчугу» дуг; SD3 убрал.)
  fx-td.webp     — SD3: карта высот СВЕРХУ для теней (renders/topdown, scripts/topdown_hf.py — лучи BVH вниз в Blender),
                   клетка 2 см, 508 × 366, без потерь. R — «мягкий» верх СТОЯЩИХ на полу тел (стены, фигура, иглы, ванна;
                   закрытие 5 × 5 — щели ламелей одним телом, расширение 3 × 3 + гаусс σ 1 клетка — мягкий боковой край ±4 см);
                   G, B — низ и верх «ПАРЯЩИХ» тел (головки булавок 1,37…1,67, радиаторы 0,12…0,62, раковина), вне их —
                   сторож: пустой интервал (низ 1,88 > верх −0,02). Билинейная выборка сжимает интервал к краю тела до пустого —
                   край тени гладкий, без крапинок (одна общая размытая карта давала «юбку» под головками: лучи под краем
                   головки то затенены, то нет). Шейдер идёт от точки к фонарю в мировых XY и берёт наименьший зазор.
Почему высота, а не глубина: у орто-изометрии (az −45°, el 35,264°) точка пикселя с экранными координатами (u, w) и высотой h
восстанавливается точно: P = u·R + w·U + s·F, s = (0,8165·w − h)/0,57735 (R, U, F — оси камеры), глубина = 30 + s. 8 бит
высоты дают 7 мм — точнее, чем нужно тени, и сжимаются в 27 КБ против ≈ 150 КБ у 16-битной упаковки глубины (hi/lo байты).
Проверка формулы: глубина прохода → h = 0,8165·w − 0,57735·(d − 30) даёт −0,02 на бумаге у верхнего и нижнего края кадра
(dmin/dmax прохода), 0 на полу, 1,10 на срезе стен, 1,77 на каске.
    python3 fx_assets.py"""
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

R = "/home/mm/Документы/app-design/blender-research"
X = f"{R}/99-raw/experiments/SD"
V = f"{X}/renders/v2"
OUT = f"{X}/pagebuild/assets"
H_OFF, H_RANGE = -0.02, 1.8


def main():
    m = json.load(open(f"{V}/C_passes.json"))
    mk = json.load(open(f"{V}/B2_marks.json"))
    FR = mk["frame_uw"]
    dmin, dmax = m["depth_min_m"], m["depth_max_m"]
    da = np.asarray(Image.open(f"{V}/C_depth_ao.png").convert("RGB")).astype(np.float64)
    d = dmin + (da[..., 0] * 256 + da[..., 1]) / 65535 * (dmax - dmin)
    Hh, Wh = d.shape
    w = FR["w1"] - (np.arange(Hh) + 0.5) / Hh * (FR["w1"] - FR["w0"])
    h = 0.81649658 * w[:, None] - 0.57735027 * (d - 30.0)
    h8 = np.clip(np.round((h - H_OFF) / H_RANGE * 255), 0, 255).astype(np.uint8)
    nrm = np.asarray(Image.open(f"{V}/C_normal_cam.png").convert("RGB"))
    ao = ndimage.gaussian_filter(ndimage.median_filter(da[..., 2], 3), 1.6)
    ao8 = (np.round(ao / 255 * 23) / 23 * 255).astype(np.uint8)
    nh = np.dstack([nrm[..., 0], nrm[..., 1], h8]).astype(np.uint8)
    Image.fromarray(nh).save(f"{OUT}/fx-nh.webp", "WEBP", lossless=True, quality=100, method=6, exact=True)
    back = np.asarray(Image.open(f"{OUT}/fx-nh.webp").convert("RGB"))
    assert int(np.abs(back.astype(int) - nh.astype(int)).max()) == 0, "WebP без потерь изменил данные"
    # SD3: карта высот сверху (верх мягкий, низ точный) — тени фонаря в мировых XY
    td = np.load(f"{X}/renders/topdown/topdown.npy").astype(np.float64)
    tdm = json.load(open(f"{X}/renders/topdown/topdown.json"))
    q8 = lambda a: np.clip(np.round((a - H_OFF) / H_RANGE * 255), 0, 255).astype(np.uint8)  # noqa: E731
    # стоящие тела: закрытие 5 × 5 (10 см) — щели одним телом, расширение 3 × 3 и гаусс σ 1 клетка — мягкий боковой край
    gsoft = ndimage.gaussian_filter(ndimage.grey_dilation(ndimage.grey_closing(td[..., 2], size=(5, 5)), size=(3, 3)), 1.5)
    # парящие: первое тело, низ которого выше пола; ламели радиатора — закрытием маски; вне тел — пустой интервал-сторож
    fm = td[..., 1] > 0.03
    fmc = ndimage.binary_closing(fm, structure=np.ones((5, 5)))
    ftop = np.where(fm, td[..., 0], H_OFF)
    fbot = np.where(fm, td[..., 1], H_OFF + H_RANGE)
    gap = fmc & ~fm
    ftop = np.where(gap, ndimage.grey_dilation(ftop, size=(5, 5)), ftop)
    fbot = np.where(gap, ndimage.grey_erosion(fbot, size=(5, 5)), fbot)
    # размытие σ 1 клетка и у парящих (вместе со сторожем): интервал сужается к краю плавно — зазор вдоль луча гладкий, и
    # минимум по 80 точкам не «гуляет» с шагом (иначе у тонких радиаторов — «пила» полос вдоль тени)
    ftop, fbot = ndimage.gaussian_filter(ftop, 1.0), ndimage.gaussian_filter(fbot, 1.0)
    tdi = np.dstack([q8(gsoft), q8(fbot), q8(ftop)])
    Image.fromarray(tdi).save(f"{OUT}/fx-td.webp", "WEBP", lossless=True, quality=100, method=6, exact=True)
    alb = Image.open(f"{V}/C_albedo.png").convert("RGB")
    albw = alb.resize((1440, round(alb.height * 1440 / alb.width)), Image.LANCZOS)
    albw.save(f"{OUT}/fx-albedo.webp", "WEBP", quality=85, method=6)
    Image.fromarray(ao8).resize((Wh // 2, Hh // 2), Image.BILINEAR).convert("RGB").save(f"{OUT}/fx-ao.webp", "WEBP", quality=80, method=6)
    ab = json.load(open(f"{X}/pagebuild/assets/assets_b.json"))
    meta = {"frame_uw": FR, "h_off": H_OFF, "h_range": H_RANGE, "nh_res": [Wh, Hh], "albedo_res": list(albw.size),
            "full_res": [mk["res"][0], mk["res"][1]], "mob_crop_px": ab["mob"]["crop_px"],
            "h_check": {"paper_top": round(float(h[:4].mean()), 3), "paper_bottom": round(float(h[-4:].mean()), 3),
                        "max": round(float(h.max()), 3)},
            "topdown": {k: tdm[k] for k in ("x0", "y0", "cell", "nx", "ny")},
            "kb": {n: round(os.path.getsize(f"{OUT}/{n}") / 1024, 1) for n in ("fx-albedo.webp", "fx-nh.webp", "fx-ao.webp", "fx-td.webp")}}
    json.dump(meta, open(f"{X}/pagebuild/fxsrc/fx_meta.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
