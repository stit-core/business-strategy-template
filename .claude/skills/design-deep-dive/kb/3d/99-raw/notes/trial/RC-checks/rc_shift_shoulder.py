#!/usr/bin/env python3
"""RC · проверки чистой арифметикой (системный Python, без Blender и браузера), 26.09.2026.

1) Сдвиг кадра Blender ↔ доля кадра (как setViewOffset three): shift меряется в долях стороны, по которой вписан сенсор
   (AUTO — большая сторона кадра, HORIZONTAL — ширина, VERTICAL — высота). Сверка с замером дорожки Z: «та же камера, что v2»
   при sensor_fit VERTICAL и shift_x −0,2 сдвинула кадр на 0,125 ширины вместо 0,2 → центр J2 0,519 W против 0,595 W у v2
   (Z/rules.md, фаза 2; лист zveno/judge/sheet_z_pair_same-cam.jpg).
2) «Фонарик» SD: мягкое плечо shoulder() из pagebuild/src/fonarik.js, применённое ко всему кадру, переводит белую бумагу
   (линейное 1,0) в 0,88 → sRGB 241 — серый прямоугольник сцены в полумраке (пиксели shots/sd2_c4, sd3_c5: 240–241 при 255 вокруг).
"""


def shift_for(frac_w, frac_h, W, H, sensor_fit="AUTO"):
    """Доли кадра (x — ширины вправо, y — высоты вниз, как setViewOffset three) → (shift_x, shift_y) Blender."""
    S = max(W, H) if sensor_fit == "AUTO" else (W if sensor_fit == "HORIZONTAL" else H)
    return frac_w * W / S, -frac_h * H / S


def frac_of(shift_x, W, H, sensor_fit="AUTO"):
    """Обратное: какой доле ширины равен shift_x Blender."""
    S = max(W, H) if sensor_fit == "AUTO" else (W if sensor_fit == "HORIZONTAL" else H)
    return shift_x * S / W


# 1) Z: 1600×1000, VERTICAL, хотели 0,2 ширины
sx, sy = shift_for(0.2, 0.0, 1600, 1000, "VERTICAL")
assert abs(sx - 0.32) < 1e-9 and sy == 0.0
got = frac_of(0.2, 1600, 1000, "VERTICAL")            # что получилось в фазе 1
assert abs(got - 0.125) < 1e-9
assert abs((0.2 - got) - (0.595 - 0.519)) < 0.002      # разница центров J2 на листе Z: 0,076 ширины
# AUTO, альбом 16:9 (KIT §4.4: shift_x −0,17 → центр объекта на 0,67 ширины)
assert shift_for(0.17, 0.0, 1920, 1080, "AUTO") == (0.17, -0.0)
# портрет телефона KB (780×1688, VERTICAL): +0,13 высоты вниз по кадру → shift_y +0,13 опускает предмет
assert abs(shift_for(0.0, -0.13, 780, 1688, "VERTICAL")[1] - 0.13) < 1e-9
print("shift: VERTICAL 1600x1000, 0,2 ширины → shift_x", round(sx, 3), "; shift_x 0,2 без пересчёта = доля ширины", got)


# 2) плечо «фонарика» (копия формулы fonarik.js, стр. 43–44) и sRGB
def shoulder(c):
    pk = max(c)
    s, d = 0.76, 0.24
    if pk < s:
        return list(c)
    npk = 1 - d * d / (pk + d - s)
    c = [v * npk / pk for v in c]
    g = 1 - 1 / (0.15 * (pk - npk) + 1)
    return [v * (1 - g) + npk * g for v in c]


def l2s(x):
    return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055


paper = shoulder([1.0, 1.0, 1.0])[0]
px = round(l2s(paper) * 255)
assert abs(paper - 0.88) < 1e-9 and px == 241
print("shoulder: бумага 1,0 → %.3f линейно → sRGB %d (замер на снимках 240–241)" % (paper, px))
print("RC_CHECK_OK")
