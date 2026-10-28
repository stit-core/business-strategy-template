"""kbp — паспорт клавиатуры «Ё» в метрах (дорожка KB, 15-showcase). Без bpy: общий источник чисел для Blender (B, C) и кода (A).

python3 kbp.py  → пишет 15-showcase/keyboard/passport.json (раскладка, профиль, корпус, пластина, свитчи, грузик, ножки, палитры).
Оси: X — вправо, Y — от пользователя (назад), Z — вверх (Blender). «Дека» — наклонная система пластины: начало в центре
верхней плоскости корпуса, повёрнута на угол набора вокруг X. В three: (x, z, −y).
"""
import json
import math
import os

U = 0.01905                                    # 1u, м
MM = 0.001

# ---------------------------------------------------------------- раскладка 65 % (68 клавиш), ЙЦУКЕН + QWERTY
# (id, ширина u, роль, основная надпись (кириллица/цифра), вторая (латиница/символ), третья (RU-символ ряда цифр), код KeyboardEvent.code)
ROW0 = [("yo", 1, "accent", "Ё", "", "", "Backquote"),
        ("1", 1, "alpha", "1", "!", "", "Digit1"), ("2", 1, "alpha", "2", "@", "\"", "Digit2"),
        ("3", 1, "alpha", "3", "#", "№", "Digit3"), ("4", 1, "alpha", "4", "$", ";", "Digit4"),
        ("5", 1, "alpha", "5", "%", "", "Digit5"), ("6", 1, "alpha", "6", "^", ":", "Digit6"),
        ("7", 1, "alpha", "7", "&", "?", "Digit7"), ("8", 1, "alpha", "8", "*", "", "Digit8"),
        ("9", 1, "alpha", "9", "(", "", "Digit9"), ("0", 1, "alpha", "0", ")", "", "Digit0"),
        ("minus", 1, "alpha", "−", "_", "", "Minus"), ("equal", 1, "alpha", "=", "+", "", "Equal"),
        ("bksp", 2, "mod", "backspace", "", "", "Backspace"), ("del", 1, "mod", "del", "", "", "Delete")]
ROW1 = [("tab", 1.5, "mod", "tab", "", "", "Tab"),
        ("q", 1, "alpha", "Й", "Q", "", "KeyQ"), ("w", 1, "alpha", "Ц", "W", "", "KeyW"), ("e", 1, "alpha", "У", "E", "", "KeyE"),
        ("r", 1, "alpha", "К", "R", "", "KeyR"), ("t", 1, "alpha", "Е", "T", "", "KeyT"), ("y", 1, "alpha", "Н", "Y", "", "KeyY"),
        ("u", 1, "alpha", "Г", "U", "", "KeyU"), ("i", 1, "alpha", "Ш", "I", "", "KeyI"), ("o", 1, "alpha", "Щ", "O", "", "KeyO"),
        ("p", 1, "alpha", "З", "P", "", "KeyP"), ("lbr", 1, "alpha", "Х", "[", "", "BracketLeft"),
        ("rbr", 1, "alpha", "Ъ", "]", "", "BracketRight"), ("bsl", 1.5, "alpha", "\\", "|", "/", "Backslash"),
        ("pgup", 1, "mod", "pgup", "", "", "PageUp")]
ROW2 = [("caps", 1.75, "mod", "caps", "", "", "CapsLock"),
        ("a", 1, "alpha", "Ф", "A", "", "KeyA"), ("s", 1, "alpha", "Ы", "S", "", "KeyS"), ("d", 1, "alpha", "В", "D", "", "KeyD"),
        ("f", 1, "alpha", "А", "F", "", "KeyF"), ("g", 1, "alpha", "П", "G", "", "KeyG"), ("h", 1, "alpha", "Р", "H", "", "KeyH"),
        ("j", 1, "alpha", "О", "J", "", "KeyJ"), ("k", 1, "alpha", "Л", "K", "", "KeyK"), ("l", 1, "alpha", "Д", "L", "", "KeyL"),
        ("semi", 1, "alpha", "Ж", ";", "", "Semicolon"), ("quote", 1, "alpha", "Э", "'", "", "Quote"),
        ("enter", 2.25, "mod", "enter", "", "", "Enter"), ("pgdn", 1, "mod", "pgdn", "", "", "PageDown")]
ROW3 = [("lshift", 2.25, "mod", "shift", "", "", "ShiftLeft"),
        ("z", 1, "alpha", "Я", "Z", "", "KeyZ"), ("x", 1, "alpha", "Ч", "X", "", "KeyX"), ("c", 1, "alpha", "С", "C", "", "KeyC"),
        ("v", 1, "alpha", "М", "V", "", "KeyV"), ("b", 1, "alpha", "И", "B", "", "KeyB"), ("n", 1, "alpha", "Т", "N", "", "KeyN"),
        ("m", 1, "alpha", "Ь", "M", "", "KeyM"), ("comma", 1, "alpha", "Б", ",", "", "Comma"),
        ("period", 1, "alpha", "Ю", ".", "", "Period"), ("slash", 1, "alpha", ".", "/", ",", "Slash"),
        ("rshift", 1.75, "mod", "shift", "", "", "ShiftRight"), ("up", 1, "mod", "↑", "", "", "ArrowUp"),
        ("end", 1, "mod", "end", "", "", "End")]
ROW4 = [("lctrl", 1.25, "mod", "ctrl", "", "", "ControlLeft"), ("lwin", 1.25, "mod", "win", "", "", "MetaLeft"),
        ("lalt", 1.25, "mod", "alt", "", "", "AltLeft"), ("space", 6.25, "alpha", "", "", "", "Space"),
        ("ralt", 1, "mod", "alt", "", "", "AltRight"), ("fn", 1, "mod", "fn", "", "", "Fn"),
        ("rctrl", 1, "mod", "ctrl", "", "", "ControlRight"), ("left", 1, "mod", "←", "", "", "ArrowLeft"),
        ("down", 1, "mod", "↓", "", "", "ArrowDown"), ("right", 1, "mod", "→", "", "", "ArrowRight")]
ROWS = [ROW0, ROW1, ROW2, ROW3, ROW4]
ROW_PROFILE = ["R1", "R2", "R3", "R4", "R4"]    # Cherry: ряд цифр R1 … нижние два ряда R4
HOMING = {"f", "j"}                              # А и О — риски под указательные пальцы

# ---------------------------------------------------------------- профиль колпачков: Cherry (низкий, рядный, цилиндрическая выемка)
KEYCAP = dict(
    gap=1.05 * MM,                 # 19,05 − 18,0: колпачок 1u внизу 18,0 × 18,0 мм
    depth_b=18.0 * MM,
    top_shrink_w=5.2 * MM,         # верх 1u 12,8 мм
    depth_t=14.0 * MM,             # верх вглубь 14,0 мм
    corner_b=1.0 * MM,             # радиус вертикальных рёбер внизу
    corner_t=2.3 * MM,             # радиус углов верха
    bulge=0.12 * MM,               # «выпуклость» стенок (литьё)
    wall=1.25 * MM,                # толщина стенки PBT
    ceil=1.45 * MM,                # потолок полости ниже верха
    stem_d=5.5 * MM, stem_cross=(4.1 * MM, 1.25 * MM), stem_bottom=0.6 * MM,
    rows={  # высота центра верха от низа юбки, наклон верха к пользователю (°), сдвиг верха назад, глубина выемки
        "R1": dict(h=9.4 * MM, tilt=9.0, yoff=0.6 * MM, dish=0.55 * MM),
        "R2": dict(h=7.9 * MM, tilt=5.0, yoff=0.4 * MM, dish=0.55 * MM),
        "R3": dict(h=7.3 * MM, tilt=1.0, yoff=0.3 * MM, dish=0.55 * MM),
        "R4": dict(h=7.9 * MM, tilt=-6.0, yoff=0.0, dish=0.55 * MM),
    },
    dish_wide=[(1.5, 1.0), (2.25, 0.8), (6.25, 0.55)],   # множитель выемки по ширине (u ≤ …)
    homing=dict(len=3.0 * MM, w=0.55 * MM, h=0.28 * MM, v=0.17),  # риска: доля глубины верха от переднего края
)

# ---------------------------------------------------------------- корпус, дека, пластина, плата, свитчи
CASE = dict(
    bezel_side=11.0 * MM, bezel_top=11.0 * MM, bezel_bottom=12.0 * MM,
    corner=6.0 * MM,               # радиус углов в плане
    h_front=17.0 * MM,             # высота верхней плоскости над столом у переднего края
    angle=6.0,                     # угол набора, °
    foot_h=1.8 * MM,               # силиконовые ножки
    chamfer=1.0 * MM,              # полированная фаска верхней кромки (45°)
    well_clear=0.5 * MM,           # зазор колодца вокруг поля клавиш
    well_corner=1.5 * MM, well_chamfer=0.5 * MM, well_depth=14.0 * MM,
    seam_depth=7.0 * MM,           # шов верх/низ — параллельно верху, 7 мм ниже
    seam_v=0.3 * MM,               # микрофаска кромок шва → V-канавка 0,6 × 0,3 мм
    bottom_fillet=0.8 * MM,
    floor_skin=2.5 * MM,           # дно колодца горизонтально (параллельно столу): сзади место под латунную плиту
    micro_bevel=0.15 * MM,         # отбивка остальных рёбер (ловит свет)
    usb=dict(x=-118.0 * MM, w=9.0 * MM, h=3.3 * MM, below_top=9.0 * MM),
)
DECK = dict(plate_top=-6.0 * MM, plate_t=1.5 * MM, pcb_top=-11.0 * MM, pcb_t=1.6 * MM, keycap_bottom=-0.2 * MM,
            travel=3.8 * MM)
SWITCH = dict(lower=(14.0 * MM, 14.0 * MM), top_b=(15.6 * MM, 15.6 * MM), top_t=(11.8 * MM, 12.6 * MM),
              top_h=5.2 * MM, stem=(4.1 * MM, 1.2 * MM), stem_top=3.4 * MM, plate_cut=14.0 * MM)
STAB = {2: 23.88 * MM / 2, 2.25: 23.88 * MM / 2, 6.25: 100.0 * MM / 2}
WEIGHT = dict(w=200.0 * MM, d=40.0 * MM, t=6.0 * MM, y_center=22.0 * MM, corner=3.0 * MM, engrave="Ё",   # плита в дне ≈ 408 г; +4 мм назад — дека выше на 0,42 мм
              strip_w=200.0 * MM, strip_h=7.0 * MM, strip_proud=0.3 * MM)                                # латунная полоса сзади (вставка)
EXPLODE = dict(keycaps=0.160, switches=0.122, stabs=0.122, plate=0.094, pcb=0.068, weight=0.024, case_top=0.0)   # м по нормали деки; фаза 2: под платой ≈ 44 мм — плиту видно целиком с камеры X (24°)
EXPLODE_RANGES = dict(keycaps=(0.00, 0.30), switches=(0.14, 0.46), stabs=(0.14, 0.46), plate=(0.30, 0.62), pcb=(0.44, 0.78),
                      weight=(0.58, 0.92), case_top=(0.0, 0.0))                                           # доли прокрутки сцены
FEET = dict(d=12.0 * MM, inset=(22.0 * MM, 16.0 * MM))

# ---------------------------------------------------------------- расцветки (hex — sRGB; металлы — линейный цвет Principled)
COLORWAYS = {
    "snow": dict(title="Снег", case=(0.70, 0.71, 0.72), plate=(0.62, 0.64, 0.66), alpha="#E7E8E4", mod="#D3D6D8",
                 legend1="#26292E", legend2="#7A8088", accent="#E05A2A", legend_accent="#FFF6EE", switch="#F4F4F2",
                 page="#EDEFF0", text="#16181B", line="#D5D9DD", accent_text="#B8431A"),
    "graphite": dict(title="Графит", case=(0.045, 0.047, 0.052), plate=(0.06, 0.062, 0.068), alpha="#3A3D42", mod="#2A2C30",
                     legend1="#E4E6E1", legend2="#8F969D", accent="#7BD3B4", legend_accent="#14231D", switch="#2C2F33",
                     page="#141619", text="#EDEEEA", line="#2A2E33", accent_text="#7BD3B4"),
    "linen": dict(title="Лён", case=(0.78, 0.70, 0.56), plate=(0.70, 0.62, 0.50), alpha="#E6DCC7", mod="#C7BBA5",
                  legend1="#3A322B", legend2="#8C8174", accent="#8A5234", legend_accent="#F3E8D6", switch="#EFE6D3",
                  page="#EFE8DC", text="#2A231D", line="#D8CCBA", accent_text="#7A4529"),
}
BRASS = (0.91, 0.778, 0.423)


def keys():
    """68 клавиш: id, ряд, профиль, x0 (u), ширина, центр в деке (м), роль, надписи, код."""
    out = []
    cols = 16
    x_left = -cols * U / 2
    y_top = 2.5 * U + (CASE["bezel_bottom"] - CASE["bezel_top"]) / 2   # поле клавиш — по центру колодца (он чуть назад)
    for r, row in enumerate(ROWS):
        x = 0.0
        for (kid, w, role, l1, l2, l3, code) in row:
            cx = x_left + (x + w / 2) * U
            cy = y_top - (r + 0.5) * U
            out.append(dict(id=kid, row=r, profile=ROW_PROFILE[r], x_u=x, w=w, cx=cx, cy=cy, role=role, l1=l1, l2=l2,
                            l3=l3, code=code, homing=kid in HOMING))
            x += w
        assert abs(x - cols) < 1e-9, (r, x)
    assert len(out) == 68, len(out)
    return out


def case_dims():
    field_w, field_d = 16 * U, 5 * U
    c = CASE
    W = field_w + 2 * c["well_clear"] + 2 * c["bezel_side"]
    D = field_d + 2 * c["well_clear"] + c["bezel_top"] + c["bezel_bottom"]
    a = math.radians(c["angle"])
    h_back = c["h_front"] + D * math.tan(a)
    well = (field_w + 2 * c["well_clear"], field_d + 2 * c["well_clear"])
    well_cy = (c["bezel_bottom"] - c["bezel_top"]) / 2          # колодец чуть назад (нижняя рамка шире)
    return dict(W=W, D=D, h_back=h_back, well=well, well_cy=well_cy, angle=c["angle"],
                deck_origin_z=c["h_front"] + D / 2 * math.tan(a))


def keycap_dims(w, profile):
    k = KEYCAP
    rw = k["rows"][profile]
    wb = w * U - k["gap"]
    wt = wb - k["top_shrink_w"]
    mult = next(m for lim, m in k["dish_wide"] if w <= lim + 1e-9)
    return dict(wb=wb, db=k["depth_b"], wt=wt, dt=k["depth_t"], h=rw["h"], tilt=rw["tilt"], yoff=rw["yoff"],
                dish=rw["dish"] * mult)


def passport():
    cd = case_dims()
    return {"units": "m", "axes": "Blender: X вправо, Y назад, Z вверх; three: (x, z, −y)", "U": U,
            "layout": keys(), "keycap_profile": "Cherry (рядный R1–R4, цилиндрическая выемка)", "keycap": KEYCAP,
            "case": dict(CASE, **cd), "deck": DECK, "switch": SWITCH, "stab_half_spacing": {str(k): v for k, v in STAB.items()},
            "weight": WEIGHT, "explode": EXPLODE, "explode_ranges": EXPLODE_RANGES, "feet": FEET, "colorways": COLORWAYS, "brass": BRASS,
            "dims_m": [round(cd["W"], 4), round(cd["D"], 4), None]}


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(here, "../../../../15-showcase/keyboard/passport.json"))
    P = passport()
    json.dump(P, open(out, "w"), ensure_ascii=False, indent=1)
    cd = case_dims()
    print(out, "W×D мм:", round(cd["W"] * 1000, 2), round(cd["D"] * 1000, 2), "задняя высота мм:", round(cd["h_back"] * 1000, 2))
    for w, pr in ((1, "R1"), (1, "R3"), (6.25, "R4")):
        print(w, pr, {k: round(v * 1000, 2) if isinstance(v, float) and k not in ("tilt",) else v
                      for k, v in keycap_dims(w, pr).items()})
