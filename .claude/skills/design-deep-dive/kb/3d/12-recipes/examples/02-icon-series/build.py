# Сгенерировано run_recipes.py из 12-recipes/02-icon-series.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 35
# Blender 5.2.2 — [проверено] рецепт 02: серия из 3 иконок (формы — 3d 05/04 §3, паспорт — 3d 06/02 §6)
import sys, math, bpy
from mathutils import Matrix, Vector
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "02-icon-series"
S = dict(unit=0.1, edge_k=0.38, corner_k=0.22, power=2.4, rough=0.35, coat=0.3, tilt_deg=14,
         primary="#635BFF", primary_dark="#4B44D6", accent="#FFD60A", white="#FFFFFF")
PASSPORT = {"radius": 0.5, "lens": 85, "az": 35, "el": 25, "margin": 1.35, "E_key": 2.0, "world": ("#F4F4F6", 0.25),
            "view": "Khronos PBR Neutral", "size": (512, 512), "samples": 32}
MAT = {}


def mats():
    for k in ("primary", "primary_dark", "accent", "white"):
        MAT[k] = bpyx.principled(f"Icon_{k}", base_color=S[k], roughness=S["rough"], coat_weight=S["coat"])[0]


def stand_up(objs, face_front=True):
    """Лицом к −Y (повороты — в вершины), один наклон серии, на пол."""
    Rm = Matrix.Rotation(math.radians(S["tilt_deg"]), 4, "Z")
    if face_front:
        Rm = Rm @ Matrix.Rotation(math.radians(90), 4, "X")
    bpy.context.view_layer.update()
    for o in objs:
        o.matrix_world = Rm @ o.matrix_world
        bpyx.apply_transforms(o, rotation=True, scale=True)
    bpyx.put_on_floor(objs)


def icon_chat(coll):
    u = S["unit"]; w, h, t = u, u * 0.78, u * 0.34
    body = D.rounded_slab("Chat_Body", w, h, t, min(w, h) * 0.45, (t * S["edge_k"], t * S["edge_k"]), coll,
                          kind="squircle", squircle_n=3.2, corner_seg=10, edge_seg=6, power=S["power"])
    x0, y0 = -w * 0.26, -h * 0.40
    path = D.bezier_pts([(x0, y0, t / 2), (x0 - w * 0.02, y0 - h * 0.12, t / 2), (x0 - w * 0.10, y0 - h * 0.20, t / 2),
                         (x0 - w * 0.19, y0 - h * 0.26, t / 2)], 24)
    tail = D.sweep("Chat_Tail", path, D.circle_pts(t * 0.42, 20), coll, scale=lambda k: 1.0 - 0.72 * k ** 1.3)
    dots = []
    for i, dx in enumerate((-0.22, 0.0, 0.22)):
        r = w * 0.058
        d = bpyx.primitive("uvsphere", f"Chat_Dot{i}", radius=r, segments=24, rings=12, collection=coll)
        d.location = (dx * w, 0.02 * h, t + r * 0.30)          # утоплена на 70 % радиуса — врастает, не парит
        bpyx.assign_material(d, MAT["white"]); dots.append(d)
    bpyx.assign_material(body, MAT["primary"]); bpyx.assign_material(tail, MAT["primary"])
    objs = [body, tail] + dots
    stand_up(objs)
    return objs


def icon_bell(coll):
    u = S["unit"]
    side = D.catmull_rom_pts([(0.041, 0.010), (0.049, 0.013), (0.046, 0.022), (0.038, 0.037), (0.034, 0.056),
                              (0.029, 0.071), (0.019, 0.083), (0.008, 0.0868)], 40)   # гладкий профиль — без полос
    bell = D.lathe("Bell_Body", [(0.0, 0.010)] + side + [(0.0, 0.087)], coll, segments=64, smooth_angle=50)
    clap = bpyx.primitive("uvsphere", "Bell_Clapper", radius=u * 0.085, segments=32, rings=16, collection=coll)
    clap.location = (0, 0, 0.010 - u * 0.03)
    knob = bpyx.primitive("torus", "Bell_Knob", radius=u * 0.07, minor_radius=u * 0.028, segments=32, rings=12,
                          collection=coll)
    knob.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    knob.location = (0, 0, 0.087 + u * 0.03)
    bpyx.assign_material(bell, MAT["accent"]); bpyx.assign_material(knob, MAT["accent"])
    bpyx.assign_material(clap, MAT["primary_dark"])
    objs = [bell, clap, knob]
    stand_up(objs, face_front=False)
    return objs


def icon_folder(coll):
    u = S["unit"]; w, h, t = u, u * 0.74, u * 0.07
    e = (t * S["edge_k"], t * S["edge_k"])
    back = D.rounded_slab("Folder_Back", w, h, t, min(w, h) * S["corner_k"] * 0.6, e, coll, corner_seg=8, edge_seg=4,
                          power=S["power"])
    tab = D.rounded_slab("Folder_Tab", w * 0.42, h * 0.3, t, h * 0.08, e, coll, corner_seg=8, edge_seg=4, power=S["power"])
    tab.location = (-w * 0.29, h * 0.5, 0)
    paper = D.rounded_slab("Folder_Paper", w * 0.84, h * 0.86, t * 0.35, h * 0.04, (t * 0.1, t * 0.1), coll,
                           corner_seg=4, edge_seg=2)
    paper.location = (0, h * 0.06, t)
    front = D.rounded_slab("Folder_Front", w, h * 0.84, t, min(w, h) * S["corner_k"] * 0.6, e, coll, corner_seg=8,
                           edge_seg=4, power=S["power"])
    front.location = (0, -h * 0.08, t + t * 0.35)
    D.set_origin(front, (0, -h * 0.5, t + t * 0.35))           # pivot на оси сгиба — панель приоткрыта на 16°
    front.rotation_euler = (math.radians(-16), 0, 0)
    for o, k in ((back, "primary_dark"), (tab, "primary_dark"), (front, "primary"), (paper, "white")):
        bpyx.assign_material(o, MAT[k])
    objs = [back, tab, paper, front]
    stand_up(objs)
    return objs


def apply_passport(objects, P=PASSPORT):
    """Паспорт серии D2 (06/02 §6): нормировка, key/fill/rim от r, мир, камера 85 мм, Neutral."""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = P["size"]
    mn, mx = bpyx.world_bbox(objects); c = (mn + mx) / 2; k = P["radius"] / ((mx - mn).length / 2)
    root = bpy.data.objects.new("PassportRoot", None); bpyx.link(root); root.location = (c.x, c.y, mn.z)
    for o in objects:
        o.parent = root; o.matrix_parent_inverse = root.matrix_world.inverted()
    root.scale = (k, k, k); root.location = (0, 0, 0); bpy.context.view_layer.update()
    mn, mx = bpyx.world_bbox(objects); c = (mn + mx) / 2; r = (mx - mn).length / 2; d = 4 * r
    for name, az, el, share, sz in (("Key", 40, 45, 1.0, 2.0), ("Fill", -70, 15, 0.35, 3.0), ("Rim", 170, 50, 0.6, 1.5)):
        a, e = math.radians(az), math.radians(el)
        bpyx.add_light("AREA", name, c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d,
                       c, energy=math.pi * d * d * P["E_key"] * share, size=r * sz)
    rk.d2lib.world_color(*P["world"])
    a, e = math.radians(P["az"]), math.radians(P["el"])
    cam = bpyx.add_camera(location=c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * 6,
                          target=c, lens=P["lens"])
    bpyx.frame_camera(cam, objects, margin=P["margin"])
    bpyx.set_color_management(P["view"])
    catcher = bpyx.primitive("plane", "ShadowCatcher", size=6.0, location=(0, 0, mn.z))
    catcher.is_shadow_catcher = True                              # тень → альфа (только Cycles)
    return cam


for i, (name, fn) in enumerate((("chat", icon_chat), ("bell", icon_bell), ("folder", icon_folder))):
    rk.reset(keep_numbers=i > 0); mats()
    coll = D.fresh_collection(f"ASSET_icon_{name}")
    objs = fn(coll)
    rk.ship(SLUG, coll.name, f"icon_{name}", preset="static_hero", optimize="meshopt")   # GLB-вариант до нормировки
    apply_passport(objs)
    bpyx.set_engine("CYCLES")                                     # ловец теней есть только в Cycles; CPU + OIDN
    bpy.context.scene.cycles.device = "CPU"; bpy.context.scene.cycles.use_denoising = True
    rk.render(SLUG, f"icon-{name}-3d", res=PASSPORT["size"], samples=PASSPORT["samples"], transparent=True)
rk.save(SLUG, passport=PASSPORT, series=S)
