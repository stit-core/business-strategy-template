"""run_objects.py — черновые иконки приборов (лазерный уровень, тепловизор) и штамп «СДАНО» одним паспортом с квартирой:
та же изометрия (орто, az −45°, el 35,264°), тот же свет H_SOFT, матовое белое + чёрное, одна красная точка; прозрачный фон
+ ловец теней, Cycles + OIDN, 1024².
    blender -b --python run_objects.py -- OUT_DIR [--items laser,thermal,stamp] [--samples 64] [--size 1024]"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import sdano_lib as S  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402
from mathutils import Matrix  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(argv[0]) if argv else f"{S.X_OUT}/renders/objects"


def opt(n, d):
    return argv[argv.index(n) + 1] if n in argv else d


items = opt("--items", "laser,thermal,stamp").split(",")
samples = int(opt("--samples", "64"))
size = int(opt("--size", "1024"))
os.makedirs(out, exist_ok=True)

# паспорт серии: материалы квартиры; матовый пластик прибора — шероховатость 0,55 (не глянец), резина 0,8
SER = dict(body="#e6e4df", body_rough=0.55, rubber="#1c1d20", rubber_rough=0.8, glass="#101113", glass_rough=0.08,
           red="#cf2419", margin=1.30)


def mats():
    m = S.materials(S.P)
    m["body"] = bpyx.principled("OB_Body", base_color=SER["body"], roughness=SER["body_rough"], specular_ior_level=0.4)[0]
    m["rubber"] = bpyx.principled("OB_Rubber", base_color=SER["rubber"], roughness=SER["rubber_rough"])[0]
    m["lens"] = bpyx.principled("OB_Lens", base_color=SER["glass"], roughness=SER["glass_rough"], specular_ior_level=0.6)[0]
    m["dot"] = bpyx.principled("OB_Red", base_color=SER["red"], roughness=0.5)[0]
    return m


def laser(C, M):
    """Лазерный нивелир-«кубик»: чёрная опора Ø 70, белый корпус 72×72×78 с чёрным поясом, башня с окном и красной
    точкой-излучателем, чёрная кнопка. Метры, от габарита корпуса."""
    base = D.lathe("L_Base", [(0.0, 0.0), (0.036, 0.0), (0.038, 0.004), (0.038, 0.010), (0.034, 0.014), (0.0, 0.014)], C,
                   segments=48, smooth_angle=40)
    bpyx.assign_material(base, M["rubber"])
    body = D.rounded_slab("L_Body", 0.072, 0.072, 0.078, 0.014, (0.006, 0.01), C, corner_seg=8, edge_seg=4, power=2.4)
    body.location.z = 0.012
    bpyx.assign_material(body, M["body"])
    belt = D.rounded_slab("L_Belt", 0.0745, 0.0745, 0.018, 0.0152, 0.002, C, corner_seg=8, edge_seg=2)
    belt.location.z = 0.012 + 0.024
    bpyx.assign_material(belt, M["rubber"])
    tz = 0.012 + 0.078
    tower = D.lathe("L_Tower", [(0.0, 0.0), (0.024, 0.0), (0.024, 0.024), (0.021, 0.028), (0.0, 0.029)], C, segments=48,
                    smooth_angle=40)
    tower.location.z = tz - 0.003
    bpyx.assign_material(tower, M["body"])
    win = D.lathe("L_Window", [(0.0245, 0.0), (0.0245, 0.016)], C, segments=48, smooth_angle=60)
    win.location.z = tz + 0.006
    bpyx.assign_material(win, M["lens"])
    dot = bpyx.primitive("uvsphere", "L_Emitter", radius=0.0042, segments=24, rings=12, collection=C)
    dot.location = (-0.0172, -0.0172, tz + 0.014)                 # на окне башни, к камере (юго-запад)
    bpyx.assign_material(dot, M["dot"])
    btn = D.rounded_slab("L_Button", 0.02, 0.012, 0.006, 0.005, (0.0, 0.002), C, corner_seg=4, edge_seg=2)
    btn.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    btn.location = (0.012, -0.036 - 0.004, 0.012 + 0.058)
    bpyx.assign_material(btn, M["rubber"])
    return [base, body, belt, tower, win, dot, btn]


def thermal(C, M):
    """Тепловизор-«пистолет»: белая голова 64×118×70 с чёрным объективом к камере (−Y), чёрная рукоять под наклоном,
    курок, красная точка — лазерный целеуказатель у объектива."""
    head = D.rounded_slab("T_Head", 0.064, 0.118, 0.07, 0.018, (0.012, 0.014), C, corner_seg=8, edge_seg=4, power=2.4)
    head.location = (0.0, 0.0, 0.13)
    bpyx.assign_material(head, M["body"])
    grip = D.rounded_slab("T_Grip", 0.042, 0.05, 0.14, 0.016, (0.008, 0.008), C, corner_seg=8, edge_seg=3, power=2.4)
    grip.data.transform(Matrix.Rotation(math.radians(-14), 4, "X"))
    grip.location = (0.0, 0.03, 0.0)
    bpyx.assign_material(grip, M["rubber"])
    ring = D.lathe("T_LensRing", [(0.0, 0.0), (0.026, 0.0), (0.026, 0.02), (0.021, 0.024), (0.0, 0.024)], C, segments=48,
                   smooth_angle=40)
    ring.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    ring.location = (0.0, -0.059 + 0.004, 0.13 + 0.038)
    bpyx.assign_material(ring, M["rubber"])
    glass = D.lathe("T_LensGlass", [(0.0, 0.0), (0.017, 0.0), (0.0, 0.004)], C, segments=48, smooth_angle=60)
    glass.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    glass.location = (0.0, -0.059 - 0.0195, 0.13 + 0.038)
    bpyx.assign_material(glass, M["lens"])
    dot = bpyx.primitive("uvsphere", "T_Laser", radius=0.0035, segments=24, rings=12, collection=C)
    dot.location = (-0.022, -0.059 - 0.001, 0.13 + 0.012)
    bpyx.assign_material(dot, M["dot"])
    trig = D.rounded_slab("T_Trigger", 0.016, 0.014, 0.03, 0.006, (0.003, 0.003), C, corner_seg=4, edge_seg=2)
    trig.data.transform(Matrix.Rotation(math.radians(-14), 4, "X"))
    trig.location = (0.0, -0.012, 0.1)
    bpyx.assign_material(trig, M["rubber"])
    return [head, grip, ring, glass, dot, trig]


def stamp(C, M):
    """Штамп «СДАНО» как напечатанная на 3D-принтере пластина: белый PLA, двойная рамка и буквы выступают на 3 мм,
    слои 0,2 мм — процедурный рельеф (только предрендер); лежит на листе с поворотом −6°, как штамп «Образец» на странице."""
    font = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
    W, Hh, t = 0.15, 0.064, 0.006
    plate = D.rounded_slab("St_Plate", W, Hh, t, 0.006, (0.0, 0.0012), C, corner_seg=6, edge_seg=2)
    outer = D.rounded_slab("St_FrameOut", W - 0.008, Hh - 0.008, 0.003, 0.004, (0.0, 0.0006), C, corner_seg=6, edge_seg=2)
    inner = D.rounded_slab("St_FrameIn", W - 0.014, Hh - 0.014, 0.004, 0.002, 0.0, C, corner_seg=6)
    outer.location.z = t
    inner.location.z = t - 0.0005
    D.boolean_apply(outer, inner)
    txt = D.text_mesh("St_Text", "СДАНО", C, size=0.04, extrude=0.0015, bevel=0.0003, bevel_res=2, resolution_u=10,
                      font_path=font, upright=False)
    mn, mx = bpyx.world_bbox([txt])
    txt.location = (-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, t + 0.0015)
    parts = [plate, outer, txt]
    layer = bpy.data.materials.get("OB_PLA") or bpyx.principled("OB_PLA", base_color=SER["body"], roughness=0.5,
                                                                 specular_ior_level=0.45)[0]
    nt = layer.node_tree
    if not any(n.type == "BUMP" for n in nt.nodes):
        pr = bpyx.find_node(nt, "BSDF_PRINCIPLED", required=True)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.wave_type = "BANDS"
        wave.bands_direction = "Z"
        wave.inputs["Scale"].default_value = 0.31416 / 0.0004   # период Wave по оси = (2π/20)/Scale → слои 0,4 мм по Z
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.5
        bump.inputs["Distance"].default_value = 0.00005
        nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
        nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], pr.inputs["Normal"])
    for o in parts:
        bpyx.assign_material(o, layer)
    root = bpy.data.objects.new("St_Root", None)
    C.objects.link(root)
    for o in parts:
        o.parent = root
    root.rotation_euler = (0, 0, math.radians(-6))
    bpy.context.view_layer.update()
    return parts


def stamp_camera(objs, size):
    from mathutils import Vector
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = size
    mn, mx = bpyx.world_bbox(objs)
    c = (mn + mx) / 2
    a, e = math.radians(-18), math.radians(58)
    dirv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    old = bpy.data.objects.get("SD_Cam")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    cam = bpyx.add_camera("SD_Cam", location=c + dirv * 1.0, target=c, lens=85, clip_start=0.01, clip_end=10)
    cam.data.type = "ORTHO"
    S.frame_ortho(cam, objs, margin=1.22)
    return cam


def stamp_black(C, M):
    parts = stamp(C, M)
    blk = bpyx.principled("OB_PLA_Black", base_color="#1f2023", roughness=0.5, specular_ior_level=0.45)[0]
    src = bpy.data.materials["OB_PLA"].node_tree
    nt = blk.node_tree
    pr = bpyx.find_node(nt, "BSDF_PRINCIPLED", required=True)
    tc = nt.nodes.new("ShaderNodeTexCoord"); wave = nt.nodes.new("ShaderNodeTexWave"); bump = nt.nodes.new("ShaderNodeBump")
    wave.wave_type = "BANDS"; wave.bands_direction = "Z"
    wave.inputs["Scale"].default_value = next(n for n in src.nodes if n.type == "TEX_WAVE").inputs["Scale"].default_value
    bump.inputs["Strength"].default_value = 0.5; bump.inputs["Distance"].default_value = 0.00006
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"]); nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], pr.inputs["Normal"])
    for o in parts:
        bpyx.assign_material(o, blk)
    return parts


def laser2(C, M):
    """Нивелир, итерация 2: корпус 72×62×88 (белый, мягкая кромка), чёрный бампер-основание, на лицевой грани (−Y, к
    камере) — чёрное стеклянное окно лазера с красной точкой-апертурой, сверху — чёрный ползунок блокировки маятника."""
    W, Dp, Hh = 0.072, 0.062, 0.088
    base = D.rounded_slab("L2_Bumper", W + 0.006, Dp + 0.006, 0.014, 0.016, (0.003, 0.004), C, corner_seg=8, edge_seg=3)
    bpyx.assign_material(base, M["rubber"])
    body = D.rounded_slab("L2_Body", W, Dp, Hh, 0.013, (0.004, 0.012), C, corner_seg=8, edge_seg=4, power=2.4)
    body.location.z = 0.010
    bpyx.assign_material(body, M["body"])
    win = D.rounded_slab("L2_Window", 0.046, 0.034, 0.006, 0.008, (0.0, 0.002), C, corner_seg=6, edge_seg=2)
    win.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))          # лицом к −Y
    win.location = (0.0, -Dp / 2 + 0.002, 0.010 + Hh * 0.56)
    bpyx.assign_material(win, M["lens"])
    dot = bpyx.primitive("uvsphere", "L2_Aperture", radius=0.0048, segments=32, rings=16, collection=C)
    dot.data.transform(Matrix.Scale(0.35, 4, (0, 1, 0)))             # плоская апертура в окне, а не шарик
    dot.location = (0.0, -Dp / 2 - 0.0042, 0.010 + Hh * 0.56 + 0.004)
    bpyx.assign_material(dot, M["dot"])
    sl = D.rounded_slab("L2_Slider", 0.026, 0.012, 0.006, 0.005, (0.0, 0.002), C, corner_seg=4, edge_seg=2)
    sl.location = (0.012, 0.008, 0.010 + Hh - 0.001)
    bpyx.assign_material(sl, M["rubber"])
    return [base, body, win, dot, sl]


BUILD = {"laser": laser, "laser2": laser2, "thermal": thermal, "stamp": stamp, "stamp_black": stamp_black}
log = {}
for it in items:
    t0 = time.time()
    bpyx.clear_scene()
    M = mats()
    C = D.fresh_collection(f"ASSET_{it}")
    objs = BUILD[it](C, M)
    bpy.context.view_layer.update()
    mn, mx = bpyx.world_bbox(objs)
    pl = bpyx.primitive("plane", "SD_ShadowCatcher", size=5.0, location=((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z),
                        collection=D.fresh_collection("STAGE"))
    pl.is_shadow_catcher = True
    if it.startswith("stamp"):                       # штамп: круче и почти фронтально — надпись читается
        cam = stamp_camera(objs, size)
    else:
        cam = S.camera_iso(objs, res=(size, size), margin=float(opt("--margin", SER["margin"])),
                           extra_pts=S.shadow_points(objs, -120, 65, h=(mx.z - mn.z) * 0.8))
    S.light_scheme(opt("--scheme", "H_ICON") if not it.startswith("stamp") else "H_SOFT", objs)
    r = S.render(f"{out}/{it}.png", (size, size), samples)
    S.render_mask(f"{out}/{it}_mask.png", (size, size))
    dims = [round(v * 1000, 1) for v in (mx - mn)]
    tris = sum(bpyx.object_stats(o).get("tris", 0) for o in objs)
    log[it] = {"render_s": r["sec"], "total_s": round(time.time() - t0, 1), "dims_mm": dims, "tris": tris}
    print("OBJ", json.dumps({it: log[it]}, ensure_ascii=False))
    bpy.ops.wm.save_as_mainfile(filepath=f"{out}/{it}.blend")
S.save_json(f"{out}/objects.json", {"series": SER, "log": log, "samples": samples, "size": size})
