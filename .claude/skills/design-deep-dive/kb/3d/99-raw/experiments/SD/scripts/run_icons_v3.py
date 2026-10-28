"""run_icons_v3.py — серия из 5 приборов, итерация SD2 (правка оркестратора: рулетка и фонарь мелкие, серые квадраты фона).
Отличия от v2: (1) текстура полотна рулетки — tape_tex.png (в v2 имя совпадало с рендером tape.png → полотно чёрное);
(2) рулетка стоит диском к камере (поворот −45° вокруг Z), полотно вытянуто на 38 мм вправо — компактный силуэт;
(3) фонарь лежит по диагонали 20° к оси X, головой к зрителю (на экране ≈ 51°), чуть наклонён (лежит на ободе головы и хвоста);
(4) кадр — по проекции предмета без концов тени с запасом margin 2,4: тень целиком в кадре, паспорт высоты — дообработкой
    icons_web.py (кадр по маске: высота предмета 56 % кадра, ширина ≤ 80 %; дальняя тень гаснет по расстоянию от предмета).
Прежний текст v2:
Серия из 5 приборов инженера одним паспортом (фаза 2): настоящие силуэты, читаемые на 96–128 px.
Паспорт: орто-изометрия квартиры (az −45°, el 35,264°), свет H_ICON (свод 0,78 + солнце 65° с северо-запада), матовое белое
(шерох. 0,5) + чёрная резина (0,8) + одна красная точка; у тепловизора вместо точки — тепловая карта на экране (единственное
цветное пятно). Реальные размеры в метрах; кадр 1024², большая сторона проекции = 1/margin кадра (предмет 44–63 % высоты).
    blender -b --python run_icons_v3.py -- OUT_DIR [--items laser,thermal,moisture,tape,flashlight] [--samples 64] [--margin 2.4]"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import sdano_lib as S  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(argv[0]) if argv else f"{S.X_OUT}/renders/icons_v3"
opt = lambda n, d: argv[argv.index(n) + 1] if n in argv else d  # noqa: E731
items = opt("--items", "laser,thermal,moisture,tape,flashlight").split(",")
samples = int(opt("--samples", "64"))
size = int(opt("--size", "1024"))
margin = float(opt("--margin", "2.4"))
os.makedirs(out, exist_ok=True)
SER = dict(body="#ebe9e4", body_rough=0.5, rubber="#1c1d20", rubber_rough=0.8, glass="#0e0f11", glass_rough=0.06, steel="#a9adb3",
           red="#cf2419")


def mats():
    M = S.materials(S.P)
    M["body"] = bpyx.principled("IC_Body", base_color=SER["body"], roughness=SER["body_rough"], specular_ior_level=0.4)[0]
    M["rubber"] = bpyx.principled("IC_Rubber", base_color=SER["rubber"], roughness=SER["rubber_rough"])[0]
    M["glass"] = bpyx.principled("IC_Glass", base_color=SER["glass"], roughness=SER["glass_rough"], specular_ior_level=0.7)[0]
    M["steel"] = bpyx.principled("IC_Steel", base_color=SER["steel"], metallic=1.0, roughness=0.28)[0]
    M["dot"] = bpyx.principled("IC_Red", base_color=SER["red"], roughness=0.45)[0]
    return M


def tex_material(name, png, emission=1.0, rough=0.25):
    m, p = bpyx.principled(name, roughness=rough, emission_strength=emission)
    t = m.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(png, check_existing=True)
    t.interpolation = "Linear"
    bpyx.link_sockets(m.node_tree, (t, "Color"), (p, "Base Color"))
    bpyx.link_sockets(m.node_tree, (t, "Color"), (p, "Emission Color"))
    return m


def uv_planar(ob, axis_u, axis_v, flip_u=False):
    """UV 0..1 по габариту в плоскости (axis_u, axis_v) — для экрана/табло."""
    me = ob.data
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    co = [v.co for v in me.vertices]
    ui, vi = "xyz".index(axis_u), "xyz".index(axis_v)
    u0, u1 = min(c[ui] for c in co), max(c[ui] for c in co)
    v0, v1 = min(c[vi] for c in co), max(c[vi] for c in co)
    for poly in me.polygons:
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            u = (c[ui] - u0) / max(u1 - u0, 1e-9)
            uvl.data[li].uv = (1 - u if flip_u else u, (c[vi] - v0) / max(v1 - v0, 1e-9))


def heatmap_png(path, w=240, h=180):
    """Тепловая карта окна (палитра «железо»): холодный откос, тёплое продувание по шву — одно цветное пятно."""
    from PIL import Image
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    t = 0.30 + 0.25 * np.exp(-((xx - 0.5) ** 2 / 0.08 + (yy - 0.55) ** 2 / 0.12))
    t += 0.45 * np.exp(-((xx - 0.22) ** 2 / 0.004 + (yy - 0.5) ** 2 / 0.09))      # полоса по шву окна
    t = np.clip(t, 0, 1)
    stops = [(0.0, (10, 8, 40)), (0.3, (80, 10, 110)), (0.55, (190, 30, 60)), (0.75, (240, 110, 20)), (0.9, (250, 200, 60)),
             (1.0, (255, 250, 210))]
    rgb = np.zeros((h, w, 3))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        m = (t >= a) & (t <= b)
        k = ((t - a) / (b - a))[..., None]
        rgb = np.where(m[..., None], np.array(ca) * (1 - k) + np.array(cb) * k, rgb)
    im = Image.fromarray(rgb.astype(np.uint8), "RGB")
    im.save(path)
    return path


def lcd_png(path, text="18,4", w=200, h=90):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (w, h), (46, 50, 46))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 58)
    d.text((w - 12, h // 2 + 2), text, fill=(214, 222, 206), font=f, anchor="rm")
    d.text((10, 10), "%", fill=(170, 180, 160), font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18))
    im.save(path)
    return path


def tape_png(path, w=600, h=60):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (238, 236, 230))
    d = ImageDraw.Draw(im)
    for i in range(0, w, 6):
        L = h * (0.55 if i % 60 == 0 else 0.35 if i % 30 == 0 else 0.2)
        d.line([(i, 0), (i, L)], fill=(28, 29, 32), width=2 if i % 60 == 0 else 1)
    im.save(path)
    return path


# ---------------------------------------------------------------------- предметы (метры; «лицо» — к −Y или к камере)
def laser(C, M):
    """Нивелир-кубик 72×62×88: белый корпус, чёрные резиновые бамперы сверху и снизу, окно-крест (два щелевых окна
    тёмного стекла) на лицевой грани −Y с красной апертурой в центре, чёрный ползунок блокировки маятника сверху."""
    W, Dp, H = 0.072, 0.062, 0.088
    body = D.rounded_slab("L_Body", W, Dp, H, 0.012, (0.004, 0.01), C, corner_seg=8, edge_seg=4, power=2.4)
    body.location.z = 0.006
    bpyx.assign_material(body, M["body"])
    for nm, z0, hh in (("L_BumperLow", 0.0, 0.016), ("L_BumperTop", H - 0.012, 0.022)):
        b = D.rounded_slab(nm, W + 0.007, Dp + 0.007, hh, 0.0155, (0.004, 0.005), C, corner_seg=8, edge_seg=3)
        b.location.z = z0
        bpyx.assign_material(b, M["rubber"])
    zc = 0.006 + H * 0.5
    for nm, (ww, hh) in (("L_WinV", (0.011, 0.05)), ("L_WinH", (0.05, 0.011))):
        w = D.rounded_slab(nm, ww, hh, 0.004, 0.0045, (0.0, 0.0015), C, corner_seg=5, edge_seg=2)
        w.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
        w.location = (0.0, -Dp / 2 + 0.001, zc)
        bpyx.assign_material(w, M["glass"])
    frame = D.rounded_slab("L_WinFrame", 0.058, 0.058, 0.002, 0.008, 0.0, C, corner_seg=6)
    frame.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    frame.location = (0.0, -Dp / 2 + 0.0015, zc)
    bpyx.assign_material(frame, M["rubber"])
    dot = bpyx.primitive("uvsphere", "L_Aperture", radius=0.0042, segments=32, rings=16, collection=C)
    dot.data.transform(Matrix.Scale(0.4, 4, (0, 1, 0)))
    dot.location = (0.0, -Dp / 2 - 0.0035, zc)
    bpyx.assign_material(dot, M["dot"])
    sl = D.rounded_slab("L_Slider", 0.03, 0.013, 0.006, 0.006, (0.0, 0.0025), C, corner_seg=4, edge_seg=2)
    sl.location = (0.0, 0.006, 0.006 + H + 0.008)
    bpyx.assign_material(sl, M["rubber"])
    return [body, frame, dot, sl] + [bpy.data.objects[n] for n in ("L_BumperLow", "L_BumperTop", "L_WinV", "L_WinH")]


def thermal(C, M):
    """Тепловизор-пистолет: голова 72×112×78, экран 3,5" на задней грани (−Y, к камере) с тепловой картой, кнопки,
    объектив вперёд (+Y), чёрная рукоять под наклоном назад, курок."""
    Wh, Dh, Hh = 0.072, 0.112, 0.078
    zh = 0.125
    head = D.rounded_slab("T_Head", Wh, Dh, Hh, 0.016, (0.012, 0.014), C, corner_seg=8, edge_seg=4, power=2.4)
    head.location = (0, 0, zh)
    bpyx.assign_material(head, M["body"])
    bez = D.rounded_slab("T_Bezel", 0.064, 0.056, 0.004, 0.008, (0.0, 0.0015), C, corner_seg=6, edge_seg=2)
    bez.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    bez.location = (0, -Dh / 2 + 0.0012, zh + Hh * 0.55)
    bpyx.assign_material(bez, M["rubber"])
    scr = D.rounded_slab("T_Screen", 0.056, 0.042, 0.0015, 0.004, 0.0, C, corner_seg=5)
    scr.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    scr.location = (0, -Dh / 2 - 0.0031, zh + Hh * 0.55 + 0.002)        # перед рамкой (рамка выступает на 2,8 мм)
    uv_planar(scr, "x", "z", flip_u=False)
    bpyx.assign_material(scr, tex_material("T_Heat", f"{out}/heatmap.png", emission=1.1))
    for i, dx in enumerate((-0.016, 0.0, 0.016)):
        b = D.rounded_slab(f"T_Btn{i}", 0.011, 0.007, 0.003, 0.0033, (0.0, 0.001), C, corner_seg=4, edge_seg=1)
        b.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
        b.location = (dx, -Dh / 2 - 0.001, zh + 0.012)
        bpyx.assign_material(b, M["rubber"])
    lens = D.lathe("T_Lens", [(0.0, 0.0), (0.024, 0.0), (0.025, 0.004), (0.025, 0.022), (0.021, 0.026), (0.0, 0.026)], C,
                   segments=48, smooth_angle=40)
    lens.data.transform(Matrix.Rotation(math.radians(-90), 4, "X"))
    lens.location = (0, Dh / 2 - 0.004, zh + Hh * 0.52)
    bpyx.assign_material(lens, M["rubber"])
    grip = D.rounded_slab("T_Grip", 0.042, 0.05, 0.13, 0.017, (0.008, 0.008), C, corner_seg=8, edge_seg=3, power=2.4)
    grip.data.transform(Matrix.Rotation(math.radians(12), 4, "X"))
    grip.location = (0, -0.006, 0.0)
    bpyx.assign_material(grip, M["rubber"])
    trig = D.rounded_slab("T_Trigger", 0.014, 0.016, 0.028, 0.006, (0.003, 0.003), C, corner_seg=4, edge_seg=2)
    trig.data.transform(Matrix.Rotation(math.radians(12), 4, "X"))
    trig.location = (0, 0.026, 0.093)
    bpyx.assign_material(trig, M["rubber"])
    return [head, bez, scr, lens, grip, trig] + [bpy.data.objects[f"T_Btn{i}"] for i in range(3)]


def moisture(C, M):
    """Влагомер игольчатый: белый корпус 40×24×126, две стальные иглы сверху (Ø 2 мм, 11 мм, шаг 13), чёрный рант иглодержателя,
    ЖК-табло «18,4 %» на лицевой грани −Y, красная кнопка питания, чёрный низ."""
    W, Dp, H = 0.04, 0.024, 0.126
    body = D.rounded_slab("M_Body", W, Dp, H, 0.011, (0.004, 0.006), C, corner_seg=8, edge_seg=4, power=2.4)
    bpyx.assign_material(body, M["body"])
    foot = D.rounded_slab("M_Foot", W + 0.003, Dp + 0.003, 0.018, 0.0125, (0.003, 0.003), C, corner_seg=8, edge_seg=2)
    bpyx.assign_material(foot, M["rubber"])
    cap = D.rounded_slab("M_Head", W - 0.006, Dp - 0.004, 0.01, 0.009, (0.0, 0.003), C, corner_seg=8, edge_seg=2)
    cap.location.z = H - 0.002
    bpyx.assign_material(cap, M["rubber"])
    pins = []
    for i, dx in enumerate((-0.0065, 0.0065)):
        p = D.lathe(f"M_Pin{i}", [(0.0, 0.0), (0.001, 0.0), (0.001, 0.009), (0.0004, 0.0115), (0.0, 0.0118)], C, segments=16,
                    smooth_angle=40)
        p.location = (dx, 0.0, H + 0.007)
        bpyx.assign_material(p, M["steel"])
        pins.append(p)
    lcd = D.rounded_slab("M_LCD", 0.03, 0.017, 0.0015, 0.0025, 0.0, C, corner_seg=4)
    lcd.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    lcd.location = (0, -Dp / 2 - 0.0006, H * 0.66)
    uv_planar(lcd, "x", "z")
    bpyx.assign_material(lcd, tex_material("M_LCDmat", f"{out}/lcd.png", emission=0.25, rough=0.2))
    btn = bpyx.primitive("uvsphere", "M_Power", radius=0.0045, segments=32, rings=16, collection=C)
    btn.data.transform(Matrix.Scale(0.45, 4, (0, 1, 0)))
    btn.location = (0, -Dp / 2 - 0.0012, H * 0.44)
    bpyx.assign_material(btn, M["dot"])
    return [body, foot, cap, lcd, btn] + pins


def tape(C, M):
    """Рулетка: корпус 68×36×70 (белый) с чёрной резиновой накладкой по кромке, полотно вытянуто на 38 мм (светлое с
    делениями), чёрный крюк на конце, красная кнопка стопора сверху. v3: вся рулетка повёрнута на −45° вокруг Z — диск к
    камере (35° от оси взгляда), полотно уходит по экрану вправо; силуэт компактнее (было 9 см полотна по диагонали)."""
    W, Dp, H = 0.068, 0.036, 0.07
    case = D.rounded_slab("TP_Case", W, H, Dp, 0.02, (0.006, 0.006), C, corner_seg=10, edge_seg=4, power=2.4)
    case.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))      # стоит «диском» к −Y: толщина Dp по Y
    case.data.transform(Matrix.Translation((0, Dp / 2, H / 2)))
    bpyx.assign_material(case, M["body"])
    band = D.rounded_slab("TP_Band", W + 0.004, H + 0.004, Dp * 0.62, 0.022, (0.0015, 0.0015), C, corner_seg=10, edge_seg=2)
    band.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    band.data.transform(Matrix.Translation((0, Dp * 0.31, (H + 0.004) / 2 - 0.002)))
    bpyx.assign_material(band, M["rubber"])
    hub = D.lathe("TP_Hub", [(0.0, 0.0), (0.012, 0.0), (0.012, 0.002), (0.0, 0.0022)], C, segments=40, smooth_angle=40)
    hub.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    hub.location = (0, -Dp / 2 - 0.0002, H * 0.52)
    bpyx.assign_material(hub, M["rubber"])
    L = 0.038
    blade = D.rounded_slab("TP_Blade", L, 0.019, 0.0012, 0.001, 0.0, C, corner_seg=2)
    blade.location = (W / 2 + L / 2 - 0.004, 0, 0.0035)
    uv_planar(blade, "x", "y")
    bpyx.assign_material(blade, tex_material("TP_BladeMat", f"{out}/tape_tex.png", emission=0.0, rough=0.35))
    hook = D.rounded_slab("TP_Hook", 0.004, 0.021, 0.012, 0.001, 0.0, C, corner_seg=2)
    hook.location = (W / 2 + L - 0.004, 0, 0.0)
    bpyx.assign_material(hook, M["rubber"])
    btn = D.rounded_slab("TP_Lock", 0.016, 0.012, 0.006, 0.004, (0.0, 0.002), C, corner_seg=4, edge_seg=2)
    btn.location = (0.012, 0, H - 0.001)
    bpyx.assign_material(btn, M["dot"])
    parts = [case, band, hub, blade, hook, btn]
    root = bpy.data.objects.new("TP_Root", None)
    C.objects.link(root)
    for o in parts:
        o.parent = root
    root.rotation_euler = (0, 0, math.radians(-45))      # диск к камере, полотно по экрану вправо
    bpy.context.view_layer.update()
    return parts


def flashlight(C, M):
    """Фонарь инспекционный: трубка Ø 25 × 150, чёрная головка Ø 34 с линзой, чёрные рифлёные кольца хвата, красная
    кнопка на торце; лежит на листе по диагонали, головой к зрителю (линза видна эллипсом)."""
    prof = [(0.0, 0.0), (0.0105, 0.0), (0.0125, 0.003), (0.0125, 0.118), (0.0145, 0.122), (0.017, 0.128), (0.017, 0.152),
            (0.0165, 0.154), (0.0, 0.154)]
    body = D.lathe("F_Body", prof, C, segments=48, smooth_angle=35)
    bpyx.assign_material(body, M["body"])
    head = D.lathe("F_Head", [(0.0125, 0.0), (0.0172, 0.006), (0.0172, 0.033), (0.0162, 0.0355), (0.0, 0.0355)], C, segments=48,
                   smooth_angle=35)
    head.location.z = 0.12
    bpyx.assign_material(head, M["rubber"])
    lens = D.lathe("F_Lens", [(0.0, 0.0), (0.0138, 0.0), (0.0, 0.0012)], C, segments=48, smooth_angle=60)
    lens.location.z = 0.1552
    bpyx.assign_material(lens, M["glass"])
    rings = []
    for i in range(5):
        r = bpyx.primitive("torus", f"F_Knurl{i}", radius=0.0127, minor_radius=0.0014, segments=40, rings=10, collection=C)
        r.location.z = 0.03 + i * 0.012
        bpyx.assign_material(r, M["rubber"])
        rings.append(r)
    tail = D.lathe("F_Tail", [(0.0, 0.0), (0.006, 0.0), (0.006, 0.0025), (0.0, 0.004)], C, segments=32, smooth_angle=40)
    tail.location.z = -0.0035
    bpyx.assign_material(tail, M["dot"])
    parts = [body, head, lens, tail] + rings
    root = bpy.data.objects.new("F_Root", None)
    C.objects.link(root)
    for o in parts:
        o.parent = root
    # v3: лёжа по диагонали — ось под 20° к X, линза к зрителю (−cos20°, −sin20°, 0): на экране ось идёт под ≈ 51°,
    # габарит почти квадратный (v2: почти горизонтально, высота 20 % кадра); наклон 1,9° — лежит на ободе головы (r 17,2)
    # и хвоста (r 12,5), а не висит
    root.rotation_euler = (math.radians(-88.1), 0, math.radians(110))
    root.location = (0, 0, 0.0128)
    bpy.context.view_layer.update()
    return parts


BUILD = {"laser": laser, "thermal": thermal, "moisture": moisture, "tape": tape, "flashlight": flashlight}
log = {}
for it in items:
    t0 = time.time()
    bpyx.clear_scene()
    M = mats()
    C = D.fresh_collection(f"ASSET_{it}")
    objs = BUILD[it](C, M)
    bpy.context.view_layer.update()
    mn, mx = bpyx.world_bbox(objs)
    st = D.fresh_collection("STAGE")
    pl = bpyx.primitive("plane", "SD_ShadowCatcher", size=5.0, location=((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z), collection=st)
    pl.is_shadow_catcher = True
    cam = S.camera_iso(objs, res=(size, size), margin=margin)      # v3: по предмету, тень влезает запасом margin
    S.light_scheme("H_ICON", objs)
    r = S.render(f"{out}/{it}.png", (size, size), samples)
    S.render_mask(f"{out}/{it}_mask.png", (size, size))
    tris = sum(bpyx.object_stats(o).get("tris", 0) for o in objs)
    log[it] = {"render_s": r["sec"], "total_s": round(time.time() - t0, 1), "dims_mm": [round(v * 1000, 1) for v in (mx - mn)], "tris": tris}
    print("ICON", json.dumps({it: log[it]}, ensure_ascii=False))
    bpy.ops.wm.save_as_mainfile(filepath=f"{out}/{it}.blend")
S.save_json(f"{out}/icons.json", {"series": SER, "margin": margin, "log": log, "samples": samples, "size": size,
                                  "camera": "ortho az -45 el 35.264", "light": "H_ICON", "version": "v3"})
