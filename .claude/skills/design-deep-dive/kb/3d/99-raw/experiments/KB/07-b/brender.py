"""brender.py — кадры B (предрендер) для страниц «Ё», фаза 2 (v2, дорожка KB2).

python3 $R/99-raw/tools/slot_run.py --heavy --label KB2-b-<режим> -- python3 $R/99-raw/tools/blender_run.py brender.py \
    --blend ../01-build/kb_snow.blend --timeout 900 -- РЕЖИМ [аргументы]
Режимы:
  hero2 [SPP] [desk,mob] [PCT] — постер первого экрана: десктоп 1920×1200 и телефон 780×1688 (портрет), S2 + полосы-блики
                                 по фаскам, f/2,8 на Ё; + маска (циклорама — holdout) и точки верха колпачков для kbtop.py
  typing [SPP]                 — раздел «Напечатайте»: камера T (сверху-спереди) 1600×900, «Снег», прозрачный фон + ловец;
                                 кадр «все вверх» + 4 кадра «нажато» (группы по чётности ряда и места в ряду: соседи
                                 никогда не нажаты в одном кадре) + обводы клавиш (вверх/вниз) → cams/T_keys.json
  explode [SPP]                — разборка: 4 станции (0; 0,35; 0,65; 1), камера X, 1600×1000, прозрачный фон + ловец
  cost                         — кадр оборота 0: EEVEE-RT 64 (ловец спрятан — его в EEVEE нет) и Cycles 20 + OIDN; маска
  turn CW d|m I0 I1 [SPP]      — оборот: d — кадры 10°·i (i ∈ [I0, I1), 36 на круг), 1280×800; m — телефон, кадры
                                 15° + 30°·i (12 углов, которых нет в d), 720×450; студия S1, прозрачный фон + ловец
Прозрачные кадры сводятся на цвет раздела вне Blender (encode.py): фон кадра = фон страницы (ΔE 0).
Камеры каждого режима — в cams/<имя>.json (для кода A и гибрида C).
"""
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import kbb  # noqa: E402
import kbp  # noqa: E402
import kbr  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "hero2"
OUT = os.path.join(HERE, "out")
CAMS = os.path.join(HERE, "cams")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CAMS, exist_ok=True)
M = {"alpha": bpy.data.materials["KC_alpha"], "mod": bpy.data.materials["KC_mod"], "accent": bpy.data.materials["KC_accent"],
     "case": bpy.data.materials["Case_Body"], "chamfer": bpy.data.materials["Case_Chamfer"], "plate": bpy.data.materials["Plate"],
     "sw": bpy.data.materials["Switch_Housing"]}
case = [bpy.data.objects["Case_Top"], bpy.data.objects["Case_Bottom"]]
focus = bpy.data.objects["hotspot_yo"]
mn, mx = bpyx.world_bbox(case)
C0 = (mn + mx) / 2
R0 = (mx - mn).length / 2
keys = [o for o in bpy.data.objects if o.name.startswith("Key_")]
KEYS = {k["id"]: k for k in kbp.keys()}
TRAVEL = kbp.DECK["travel"]


def key_group(kid):
    """Группа кадра «нажато»: чётность ряда × чётность места в ряду — соседи слева/справа/спереди/сзади в разных кадрах."""
    k = KEYS[kid]
    row = [q for q in kbp.keys() if q["row"] == k["row"]]
    idx = [q["id"] for q in row].index(kid)
    return (k["row"] % 2) * 2 + (idx % 2)


def clear_stage():
    st = D.fresh_collection("STAGE")
    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o, do_unlink=True)
    return st


def own(cam, st):
    for c in cam.users_collection:
        c.objects.unlink(cam)
    st.objects.link(cam)
    return cam


def cam_json(name, cam, res, extra=None):
    j = {"name": name, "res": list(res), "location": list(cam.matrix_world.translation),
         "quaternion_wxyz": list(cam.matrix_world.to_quaternion()), "sensor_width_mm": cam.data.sensor_width,
         "sensor_height_mm": cam.data.sensor_height, "sensor_fit": cam.data.sensor_fit, "lens_mm": cam.data.lens,
         "shift_x": cam.data.shift_x, "shift_y": cam.data.shift_y, "clip": [cam.data.clip_start, cam.data.clip_end],
         "focus_world": list(focus.matrix_world.translation),
         "focus_distance_m": (cam.matrix_world.translation - focus.matrix_world.translation).length,
         "fstop": cam.data.dof.aperture_fstop if cam.data.dof.use_dof else None, "center": list(C0), "radius": R0,
         "exposure": bpy.context.scene.view_settings.exposure, "view": bpy.context.scene.view_settings.view_transform}
    j.update(extra or {})
    json.dump(j, open(os.path.join(CAMS, f"{name}.json"), "w"), indent=1)
    return j


def project(cam, res, pts):
    """Мировые точки N×3 → пиксели N×2 (начало — левый верх), с учётом shift и sensor_fit (матрица камеры Blender)."""
    dg = bpy.context.evaluated_depsgraph_get()
    P = np.array(cam.calc_matrix_camera(dg, x=res[0], y=res[1], scale_x=1.0, scale_y=1.0))
    V = np.array(cam.matrix_world.inverted())
    h = np.c_[pts, np.ones(len(pts))] @ (P @ V).T
    ndc = h[:, :2] / h[:, 3:4]
    return np.c_[(ndc[:, 0] + 1) / 2 * res[0], (1 - ndc[:, 1]) / 2 * res[1]]


def key_world_verts(o, dz=0.0, step=1):
    me = o.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)[::step].copy()
    co[:, 2] += dz
    mw = np.array(o.matrix_world)
    return (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]


def hull(pts, max_pts=40):
    P = sorted(set(map(tuple, np.round(pts, 1).tolist())))
    if len(P) < 3:
        return [list(p) for p in P]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    h = lo[:-1] + up[:-1]
    if len(h) > max_pts:
        idx = np.linspace(0, len(h), max_pts, endpoint=False).astype(int)
        h = [h[i] for i in idx]
    return [[round(x, 1), round(y, 1)] for x, y in h]


def top_point(o):
    top = max((Vector(v.co) for v in o.data.vertices), key=lambda p: p.z - 0.3 * abs(p.x) - 0.3 * abs(p.y))
    return o.matrix_world @ Vector((0.0, top.y * 0.2, top.z - 0.0006))


def keytops_metric(cam, res, name):
    """Экранные точки верха колпачков в формате kbtop.py: {id: [x, y, материал]}."""
    sc = bpy.context.scene
    pts = {}
    for o in keys:
        u, v, z = world_to_camera_view(sc, cam, top_point(o))
        if 0 <= u <= 1 and 0 <= v <= 1 and z > 0:
            pts[o.name[4:]] = [round(u * res[0], 1), round((1 - v) * res[1], 1), o.material_slots[0].material.name]
    json.dump(pts, open(os.path.join(CAMS, f"{name}_keytops.json"), "w"), ensure_ascii=False)
    return pts


def key_map(cam, res, name):
    """Карта клавиш для HTML-слоя B и для касаний: центр верха, обвод (выпуклая оболочка колпачка вверху и внизу хода),
    группа кадра «нажато», код клавиши, надписи."""
    out = {}
    for o in keys:
        kid = o.name[4:]
        k = KEYS[kid]
        up = project(cam, res, key_world_verts(o, 0.0, 3))
        dn = project(cam, res, key_world_verts(o, -TRAVEL, 3))
        c = project(cam, res, np.array([list(top_point(o))]))[0]
        out[kid] = {"code": k["code"], "row": k["row"], "w": k["w"], "role": k["role"], "l1": k["l1"], "l2": k["l2"],
                    "l3": k["l3"], "group": key_group(kid), "x": round(float(c[0]), 1), "y": round(float(c[1]), 1),
                    "hull": hull(np.r_[up, dn]), "hull_up": hull(up, 28)}
    json.dump({"res": list(res), "travel_m": TRAVEL, "keys": out}, open(os.path.join(CAMS, f"{name}_keys.json"), "w"),
              ensure_ascii=False)
    return out


def catcher(st, size=4.0):
    pl = bpyx.primitive("plane", "ShadowCatcher", size=size, collection=st)
    pl.location = (C0.x, C0.y, 0.0)
    pl.is_shadow_catcher = True
    return pl


def chamfer_strip(st, cam, point, normal, along, name, E=2.4, dist=0.34, length=0.5, width=0.012):
    """Лампа-полоса по зеркальной формуле: блик ляжет длинной линией на фаску с нормалью normal в точке point."""
    v = (cam.matrix_world.translation - point).normalized()
    n = normal.normalized()
    r = (2 * n.dot(v) * n - v).normalized()
    pos = point + r * dist
    return kbr.area(st, name, pos, point, E, dist, length, width, xdir=along)


def rig_S2_noset(st, az):
    """S2 без циклорамы и без лампы фона (для прозрачного кадра с ловцом)."""
    d = 3.5 * R0
    E = 4.0
    kbr.area(st, "S2_Key", kbr.sph(C0, az - 55, 16, d), C0, E, d, 1.4 * R0, 3.5 * R0)
    kbr.area(st, "S2_RimL", kbr.sph(C0, -150, 22, d), C0, E * 1.2, d, 5.0 * R0, 0.2 * R0, xdir=(0, 1, 0))
    kbr.area(st, "S2_RimR", kbr.sph(C0, 140, 22, d), C0, E * 1.2, d, 5.0 * R0, 0.2 * R0, xdir=(0, 1, 0))
    kbr.area(st, "S2_Top", kbr.sph(C0, 180, 62, d), C0, E * 0.25, d, 2.5 * R0)
    kbr.area(st, "S2_Front", kbr.sph(C0, az + 10, 40, 4 * R0), C0, E * 0.18, 4 * R0, 4 * R0)   # мягкая заливка сверху-спереди
    kbr.world("#FFFFFF", 0.0)


def rig_S1_noset(st, az, rims=False, world=0.05):
    d = 3.5 * R0
    E = 1.0
    kbr.area(st, "S1_Key", kbr.sph(C0, az + 38, 48, d), C0, E, d, 2.4 * R0, 1.8 * R0)
    kbr.area(st, "S1_Fill", kbr.sph(C0, az - 70, 18, 4 * R0), C0, E * 0.27, 4 * R0, 3 * R0)
    kbr.area(st, "S1_StripFront", kbr.sph(C0, az + 78, 57, d), C0, E * 0.45, d, 5.0 * R0, 0.18 * R0, xdir=(1, 0, 0))
    kbr.area(st, "S1_StripLeft", kbr.sph(C0, az - 120, 25, d), C0, E * 1.0, d, 5.0 * R0, 0.18 * R0, xdir=(0, 1, 0))
    kbr.area(st, "S1_RimR", kbr.sph(C0, az + 160, 30, d), C0, E * 0.9, d, 1.5 * R0)
    if rims:
        kbr.area(st, "S1_RimL", kbr.sph(C0, az - 160, 26, d), C0, E * 0.8, d, 4.0 * R0, 0.2 * R0, xdir=(0, 1, 0))
    kbr.world("#FFFFFF", world)


def fit_cam(name, az, el, lens, margin, res, target=None, frame_objs=None, fstop=None, shift=(0.0, 0.0)):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = res[0], res[1], 100
    objs = frame_objs or case
    mn_, mx_ = bpyx.world_bbox(objs)
    c = target if target is not None else (mn_ + mx_) / 2
    cam = bpyx.add_camera(name, kbr.sph(c, az, el, 2.0), c, lens=lens)
    cam.data.sensor_fit = "HORIZONTAL" if res[0] >= res[1] else "VERTICAL"
    cam.data.sensor_width = 36.0
    cam.data.sensor_height = 36.0
    bpyx.frame_camera(cam, objs, margin=margin)
    cam.data.shift_x, cam.data.shift_y = shift
    if fstop:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.aperture_blades = 7
        cam.data.dof.aperture_rotation = math.radians(12)
        cam.data.dof.focus_object = focus
    return cam


def set_eevee(samples=64):
    sc = bpy.context.scene
    bpyx.set_engine("BLENDER_EEVEE")
    ee = sc.eevee
    for k, v in (("use_raytracing", True), ("taa_render_samples", samples), ("use_shadows", True),
                 ("shadow_ray_count", 2), ("shadow_step_count", 8), ("use_fast_gi", False)):
        if bpyx.rna_has(ee, k):
            setattr(ee, k, v)
    sc.render.film_transparent = True
    return sc


def turn_setup(res, cw, exposure=None, world=None):
    kbb.apply_colorway(M, cw)
    st = clear_stage()
    piv = bpy.data.objects.new("TurnPivot", None)
    st.objects.link(piv)
    piv.location = (C0.x, C0.y, 0.0)
    cam = own(fit_cam("Cam_R", -20.0, 28.0, 85.0, 1.12, res), st)
    rig_S1_noset(st, -20.0, world=TURN_LOOK[cw][1] if world is None else world)
    cat = catcher(st)
    bpy.context.view_layer.update()
    for o in list(st.objects):
        if o is not piv and o is not cat:
            mw = o.matrix_world.copy()
            o.parent = piv
            o.matrix_parent_inverse = piv.matrix_world.inverted()
            o.matrix_world = mw
    kbr.view("Khronos PBR Neutral", exposure=TURN_LOOK[cw][0] if exposure is None else exposure)
    return st, piv, cam, cat


TURN_LOOK = {"snow": (0.10, 0.45), "graphite": (0.0, 0.45), "linen": (0.15, 0.45)}   # (экспозиция, мир) — подбор режимом look:
# верх белых колпачков 89–91 L* на фоне раздела (при −0,25/0,05 было 66,8 — «серая» клавиатура на светлом)


log = {"mode": MODE, "argv": argv, "t0": time.strftime("%H:%M:%S")}
t_all = time.time()
if MODE == "hero2":
    SPP = int(argv[1]) if len(argv) > 1 else 128
    WHICH = (argv[2] if len(argv) > 2 else "desk,mob").split(",")
    PCT = int(argv[3]) if len(argv) > 3 else 100
    fw = focus.matrix_world.translation.copy()
    deck = bpy.data.objects["KB_deck"]
    Rd = deck.matrix_world.to_3x3()
    n_top = (Rd @ Vector((0, 0, 1))).normalized()
    CONF = {"desk": ((1920, 1200), 0.34, (-0.10, 0.02), 100.0),
            "mob": ((780, 1688), 0.31, (0.0, 0.13), 100.0)}      # портрет: Ё в нижней части, верх кадра — под текст
    for tag in WHICH:
        res0, dist, shift, lens = CONF[tag]
        res = (int(res0[0] * PCT / 100), int(res0[1] * PCT / 100))
        st = clear_stage()
        sc = bpy.context.scene
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = res[0], res[1], 100
        cam = bpyx.add_camera(f"Cam_H2_{tag}", kbr.sph(fw, -22.0, 30.0, dist), fw, lens=lens)
        cam.data.sensor_fit = "HORIZONTAL" if res[0] >= res[1] else "VERTICAL"
        cam.data.sensor_width = cam.data.sensor_height = 36.0
        cam.data.shift_x, cam.data.shift_y = shift
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = 2.8
        cam.data.dof.aperture_blades = 7
        cam.data.dof.aperture_rotation = math.radians(12)
        cam.data.dof.focus_object = focus
        own(cam, st)
        cyc = kbr.rig_S2(st, C0, R0, -22.0, "#0D0E10")
        bpy.context.view_layer.update()
        # полосы-блики: левая фаска (вдоль Y) и передняя фаска у угла (вдоль X) — точки на фасках рядом с Ё
        W2, D2 = kbp.case_dims()["W"] / 2, kbp.case_dims()["D"] / 2
        top_y = lambda y: kbp.CASE["h_front"] + (y + D2) * math.tan(math.radians(kbp.CASE["angle"]))   # noqa: E731
        pL = Vector((-W2 + 0.5e-3, fw.y - 0.01, top_y(fw.y) - 0.5e-3))
        nL = (Vector((-1, 0, 0)) + n_top).normalized()
        chamfer_strip(st, cam, pL, nL, Rd @ Vector((0, 1, 0)), "Strip_ChamferL", E=1.5, length=0.6)   # 2,2 → пересвет 1,24 %
        pF = Vector((-W2 + 0.03, -D2 + 0.5e-3, top_y(-D2) - 0.5e-3))
        nF = (Vector((0, -1, 0)) + n_top).normalized()
        chamfer_strip(st, cam, pF, nF, Vector((1, 0, 0)), "Strip_ChamferF", E=1.1, length=0.6)
        kbr.view("Khronos PBR Neutral", exposure=-0.35)
        sfx = "" if PCT == 100 else f"_p{PCT}"
        r = kbr.render(os.path.join(OUT, f"hero2_{tag}{sfx}.png"), res, samples=SPP)
        m = kbr.render_mask(os.path.join(OUT, f"mask_hero2_{tag}{sfx}.png"), res, [cyc], samples=8)
        cam_json(f"H2v2_{tag}", cam, res0)
        keytops_metric(cam, res, f"H2v2_{tag}{sfx}")
        log[tag] = {"sec": r["sec"], "mask_sec": m["sec"], "spp": SPP, "res": list(res),
                    "lights": {o.name: round(o.data.energy, 3) for o in st.objects if o.type == "LIGHT"}}
        print("KB_B", tag, json.dumps(log[tag], ensure_ascii=False))
elif MODE == "typing":
    SPP = int(argv[1]) if len(argv) > 1 else 64
    res = (1600, 900)
    st = clear_stage()
    cam = own(fit_cam("Cam_T", -6.0, 52.0, 70.0, 1.06, res), st)
    rig_S2_noset(st, -6.0)
    catcher(st)
    kbr.view("Khronos PBR Neutral", exposure=-0.35)
    kmap = key_map(cam, res, "T")
    cam_json("T", cam, res, {"az": -6.0, "el": 52.0, "margin": 1.06})
    kbb.apply_colorway(M, "snow")
    kbr.cycles(SPP, denoise=True, transparent=True)
    r = bpyx.render_still(os.path.join(OUT, "typing_snow.png"), resolution=res, samples=SPP, transparent=True)
    log["base"] = r["sec"]
    for g in range(4):
        grp = [o for o in keys if kmap[o.name[4:]]["group"] == g]
        grp += [bpy.data.objects["Sw_" + o.name[4:]] for o in list(grp)]      # шток свитча идёт вниз вместе с колпачком
        for o in grp:
            o.location.z -= TRAVEL
        bpy.context.view_layer.update()
        r = bpyx.render_still(os.path.join(OUT, f"typing_snow_p{g}.png"), resolution=res, samples=SPP, transparent=True)
        for o in grp:
            o.location.z += TRAVEL
        log[f"p{g}"] = {"sec": r["sec"], "keys": len(grp) // 2}
        print("KB_B typing group", g, len(grp), r["sec"])
elif MODE == "explode":
    SPP = int(argv[1]) if len(argv) > 1 else 64
    PCT = int(argv[2]) if len(argv) > 2 else 100
    res = (int(1600 * PCT / 100), int(1000 * PCT / 100))
    st = clear_stage()
    kbb.apply_explode(1.0)
    big = [o for o in bpy.data.collections["ASSET_kb"].all_objects if o.type == "MESH"]
    cam = own(fit_cam("Cam_X", -28.0, 24.0, 70.0, 1.10, res, frame_objs=big), st)
    rig_S1_noset(st, -28.0, rims=True, world=0.45)       # светлый раздел: металл отражает «белую студию», а не тьму
    catcher(st)
    kbr.view("Khronos PBR Neutral", exposure=0.10)
    cam_json("X", cam, (1600, 1000), {"az": -28.0, "el": 24.0, "margin": 1.10, "stations": [0.0, 0.35, 0.65, 1.0]})
    # подписи слоёв: экранная точка каждого слоя на станции 1 (для HTML-подписей в B; A/C считают сами)
    labels = {}
    kbr.cycles(SPP, denoise=True, transparent=True)
    sfx = "" if PCT == 100 else f"_p{PCT}"
    for i, p in enumerate((0.0, 0.35, 0.65, 1.0)):
        kbb.apply_explode(p)
        lab = {}
        for L, nm in (("keycaps", "Key_bksp"), ("switches", "Sw_p"), ("plate", "Plate"), ("pcb", "PCB"), ("weight", "Weight"),
                      ("case", "Case_Top")):
            ob = bpy.data.objects[nm]
            mn_, mx_ = bpyx.world_bbox([ob])
            pt = Vector((mx_.x, (mn_.y + mx_.y) / 2, mx_.z))
            xy = project(cam, (1600, 1000), np.array([list(pt)]))[0]
            lab[L] = [round(float(xy[0]), 1), round(float(xy[1]), 1)]
        labels[f"s{i}"] = lab
        r = bpyx.render_still(os.path.join(OUT, f"explode_{i}{sfx}.png"), resolution=res, samples=SPP, transparent=True)
        log[f"p{p}"] = r["sec"]
        print("KB_B explode", p, r["sec"])
    json.dump(labels, open(os.path.join(CAMS, "X_labels.json"), "w"), indent=1)
    kbb.apply_explode(0.0)
elif MODE == "cost":
    res = (1280, 800)
    st, piv, cam, cat = turn_setup(res, "snow")
    cam_json("R", cam, res, {"az": -20.0, "el": 28.0, "margin": 1.12, "frames_desk": 36, "step_desk_deg": 10,
                             "frames_mob": 24, "step_mob_deg": 15, "pivot": list(piv.location)})
    piv.rotation_euler = (0, 0, 0)
    # EEVEE-RT: ловца теней нет — прячем плоскость (сравнение по объекту; тени на полу у EEVEE не будет вовсе)
    cat.hide_render = True
    set_eevee(64)
    t0 = time.time()
    bpyx.render_still(os.path.join(OUT, "cost_eevee_rt64.png"), resolution=res, samples=64, transparent=True)
    log["eevee_rt64_sec"] = round(time.time() - t0, 2)
    set_eevee(16)
    t0 = time.time()
    bpyx.render_still(os.path.join(OUT, "cost_eevee_rt16.png"), resolution=res, samples=16, transparent=True)
    log["eevee_rt16_sec"] = round(time.time() - t0, 2)
    cat.hide_render = False
    for spp in (20, 48):
        kbr.cycles(spp, denoise=True, transparent=True)
        t0 = time.time()
        bpyx.render_still(os.path.join(OUT, f"cost_cycles{spp}.png"), resolution=res, samples=spp, transparent=True)
        log[f"cycles{spp}_sec"] = round(time.time() - t0, 2)
    cat.hide_render = True
    kbr.cycles(8, denoise=False, transparent=True)
    bpyx.render_still(os.path.join(OUT, "cost_mask.png"), resolution=res, samples=8, transparent=True)
    cat.hide_render = False
    print("KB_COST", json.dumps(log))
elif MODE == "shadow":
    # контактная тень пола для гибрида C: ортокамера сверху, клавиатура невидима камере, но бросает тень на ловец
    SPP = int(argv[1]) if len(argv) > 1 else 128
    st = clear_stage()
    ext = (0.46, 0.26)
    res = (1024, 576)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = res[0], res[1], 100
    cam = bpyx.add_camera("Cam_Shadow", (C0.x, C0.y, 1.0), (C0.x, C0.y, 0.0), lens=50)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = ext[0]
    cam.data.sensor_fit = "HORIZONTAL"
    own(cam, st)
    kbr.area(st, "SH_Soft", Vector((C0.x - 0.05, C0.y - 0.10, 0.62)), Vector((C0.x, C0.y, 0.0)), 1.2, 0.62, 0.9, 0.6)
    kbr.world("#FFFFFF", 0.6)
    catcher(st)
    hidden = []
    for o in bpy.data.collections["ASSET_kb"].all_objects:
        if o.type == "MESH":
            o.visible_camera = False
            hidden.append(o)
    kbr.cycles(SPP, denoise=True, transparent=True)
    r = bpyx.render_still(os.path.join(OUT, "shadow_floor.png"), resolution=res, samples=SPP, transparent=True)
    for o in hidden:
        o.visible_camera = True
    json.dump({"extent_m": list(ext), "center_blender": [C0.x, C0.y, 0.0], "res": list(res)},
              open(os.path.join(CAMS, "shadow_floor.json"), "w"), indent=1)
    log["sec"] = r["sec"]
    print("KB_SHADOW", r["sec"])
elif MODE == "look":
    # look CW ANGLE EXP WORLD [SPP] — один кадр оборота 640×400 для подбора экспозиции/мира
    cw, ang, ex, wo = argv[1], float(argv[2]), float(argv[3]), float(argv[4])
    spp = int(argv[5]) if len(argv) > 5 else 20
    res = (640, 400)
    st, piv, cam, cat = turn_setup(res, cw, ex, wo)
    piv.rotation_euler = (0, 0, math.radians(-ang))
    kbr.cycles(spp, denoise=True, transparent=True)
    tag = f"look_{cw}_{int(ang)}_e{ex:+.2f}_w{wo:.2f}"
    r = bpyx.render_still(os.path.join(OUT, "look", tag + ".png"), resolution=res, samples=spp, transparent=True)
    keytops_metric(cam, res, "R_look")
    log.update(tag=tag, sec=r["sec"])
    print("KB_LOOK", tag, r["sec"])
elif MODE == "turn":
    cw, kind, i0, i1 = argv[1], argv[2], int(argv[3]), int(argv[4])
    spp = int(argv[5]) if len(argv) > 5 else 20
    res = (1280, 800) if kind == "d" else (720, 450)
    angles = [10 * i for i in range(i0, i1)] if kind == "d" else [15 + 30 * i for i in range(i0, i1)]
    st, piv, cam, cat = turn_setup(res, cw)
    os.makedirs(os.path.join(OUT, f"turn_{cw}"), exist_ok=True)
    kbr.cycles(spp, denoise=True, transparent=True)
    secs = []
    for a in angles:
        # продукт «поворачивается» под неподвижным студийным светом: камера и свет вращаются вокруг клавиатуры
        piv.rotation_euler = (0, 0, math.radians(-a))
        r = bpyx.render_still(os.path.join(OUT, f"turn_{cw}", f"{kind}_{a:03d}.png"), resolution=res, samples=spp,
                              transparent=True)
        secs.append(r["sec"])
    log.update(cw=cw, kind=kind, angles=angles, spp=spp, sec_frames=secs, sec_mean=round(sum(secs) / max(len(secs), 1), 2))
    print("KB_TURN", cw, kind, i0, i1, round(sum(secs), 1))
log["sec_total"] = round(time.time() - t_all, 1)
json.dump(log, open(os.path.join(OUT, f"log_{MODE}_{'_'.join(argv[1:5])}.json"), "w"), indent=1, ensure_ascii=False)
