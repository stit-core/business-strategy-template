"""run_stamp.py — клип штампа «СДАНО» (дорожка SD, итерация SD2): чёрный штамп стоит на акте рядом с местом оттиска,
его берут (упреждение — лёгкий наклон), переносят дугой, ставят с покачиванием, возвращают на место; 38 кадров @24 (1,58 с).

Камера — перспектива с матрицей, параллельной листу (взгляд строго вниз + сдвиг объектива): плоскость листа в кадре без
перекоса, масштаб одинаков по всему листу, поэтому оттиск и тень ложатся на плоскую HTML-страницу без искажений, а сам
штамп виден сверху-спереди (≈ 17° от вертикали) за счёт смещения камеры, а не наклона. Оттиск дорисовывается в дообработке
(stamp_comp.py) точно по плоскости: отсюда в JSON — отображение «мм листа → пиксели» по трём точкам world_to_camera_view.

Кадр листа X ∈ [−170; 92] мм, Y ∈ [−40; 88] мм (262 × 128), оттиск 90 × 40 мм с центром (0; 0), поворот −4°; место
штампа (−100; 4), поворот +6°. Свет — солнце слева (чуть сверху по кадру), угол места 60°, 3°; свод белый 0,55 — тени
вправо, на свежий оттиск. Плёнка прозрачная + ловец теней (лист = страница, фон уходит в mix-blend-mode: multiply).
    blender -b --python run_stamp.py -- OUT_DIR [--samples 32] [--res 800x391] [--frames all|0,14,31]"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402

import sdano_lib as S  # noqa: E402
import bpyx  # noqa: E402
import d1lib as D  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(argv[0]) if argv else f"{S.X_OUT}/renders/stamp"
opt = lambda n, d: argv[argv.index(n) + 1] if n in argv else d  # noqa: E731
samples = int(opt("--samples", "32"))
RES = tuple(int(v) for v in opt("--res", "800x391").split("x"))
FPS, NF = 24, 38
MM = 0.001
FRAME = dict(x0=-170, x1=92, y0=-40, y1=88)            # мм листа
CAM = dict(x=-30, y=-160, h=560)                       # мм: камера смещена «к зрителю» (−Y) — видна передняя грань
IMP = dict(x=0.0, y=0.0, rz=-4.0)                      # оттиск: центр колодки при ударе
REST = dict(x=-100.0, y=4.0, rz=6.0)                   # место штампа на листе
os.makedirs(f"{out}/frames", exist_ok=True)


# ---------------------------------------------------------------------- модель (м; Z вверх; начало — центр низа резины)
def build():
    C = D.fresh_collection("ASSET_stamp")
    blk = bpyx.principled("ST_Black", base_color="#18191b", roughness=0.34, specular_ior_level=0.5)[0]
    knob_m = bpyx.principled("ST_KnobBlack", base_color="#161719", roughness=0.26, specular_ior_level=0.55)[0]
    rub = bpyx.principled("ST_Rubber", base_color="#2b2b2d", roughness=0.85)[0]
    lab, p = bpyx.principled("ST_Label", roughness=0.8)
    t = lab.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(f"{out}/stamp_label.png", check_existing=True)
    t.interpolation = "Cubic"
    bpyx.link_sockets(lab.node_tree, (t, "Color"), (p, "Base Color"))
    parts = []
    die = D.rounded_slab("St_Die", 0.090, 0.040, 0.004, 0.003, (0.0006, 0.0), C, corner_seg=6, edge_seg=1)
    bpyx.assign_material(die, rub)
    mount = D.rounded_slab("St_Mount", 0.096, 0.046, 0.020, 0.006, (0.0015, 0.003), C, corner_seg=8, edge_seg=3, power=2.4)
    mount.location.z = 0.004
    bpyx.assign_material(mount, blk)
    # этикетка — передняя полоса верхней грани (сверху-спереди середину колодки закрывает ручка: превью «С…О»)
    label = D.rounded_slab("St_Label", 0.070, 0.014, 0.0005, 0.0015, 0.0, C, corner_seg=4)
    label.location = (0.0, -0.0145, 0.024 - 0.0001)
    me = label.data
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (c.x / 0.070 + 0.5, c.y / 0.014 + 0.5)
    bpyx.assign_material(label, lab)
    neck = D.lathe("St_Neck", [(0.0, 0.0), (0.0135, 0.0), (0.0118, 0.003), (0.009, 0.009), (0.0086, 0.027), (0.0108, 0.035), (0.0, 0.035)],
                   C, segments=48, smooth_angle=50)
    neck.location.z = 0.024
    bpyx.assign_material(neck, blk)
    knob = D.lathe("St_Knob", [(0.0, 0.0), (0.0105, 0.0), (0.0165, 0.004), (0.0203, 0.011), (0.0206, 0.017), (0.0185, 0.025),
                                (0.0125, 0.0315), (0.0, 0.0335)], C, segments=64, smooth_angle=60)
    knob.location.z = 0.058
    bpyx.assign_material(knob, knob_m)
    parts = [die, mount, label, neck, knob]
    root = bpy.data.objects.new("St_Root", None)
    C.objects.link(root)
    for o in parts:
        o.parent = root
    return root, parts


# ---------------------------------------------------------------------- движение (мм, градусы); кадры 0…47
def sstep(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# фазы в кадрах @24: покой 0–2 · упреждение 2–4 · перенос 4–12 · удар 12–14 · прижим 14–18 · возврат 18–27 · посадка 27–31 ·
# покой 31–37. Удар (касание) — кадр 14 (0,58 с): с него на листе оттиск (stamp_comp.py)
PH = dict(ant=(2, 4), go=(4, 12), hit=(12, 14), press=(14, 18), back=(18, 27), land=(27, 31))
CONTACT = 14


def pose(f):
    """(x, y, z, rx, ry, rz): покой → упреждение → перенос дугой → опускание с ускорением → прижим с покачиванием → возврат
    дугой → посадка с затуханием → покой. Наклоны — в сторону движения (запаздывание поворота за переносом)."""
    x, y, z, rx, ry, rz = REST["x"], REST["y"], 0.0, 0.0, 0.0, REST["rz"]

    def ph(k):
        a, b = PH[k]
        return (f - a) / (b - a)
    if f < PH["ant"][0]:
        pass
    elif f < PH["go"][0]:                         # упреждение: наклон от цели, штамп «берут»
        s = sstep(ph("ant"))
        ry, z = -2.0 * s, 1.0 * s
    elif f < PH["hit"][0]:                        # перенос дугой к месту оттиска
        s = ph("go")
        e = sstep(s)
        x, y = lerp(REST["x"], IMP["x"], e), lerp(REST["y"], IMP["y"], e)
        z = 1.0 + 30.0 * math.sin(math.pi * min(s * 1.15, 1.0)) * (1 - 0.35 * s) + 11.0 * s
        rz = lerp(REST["rz"], IMP["rz"], sstep(min(1.0, s * 1.2)))
        ry = lerp(-2.0, 0.0, s) + 4.5 * math.sin(math.pi * s)          # наклон в сторону движения (+X)
    elif f < PH["press"][0]:                      # опускание с ускорением — удар
        s = ph("hit")
        x, y, rz = IMP["x"], IMP["y"], IMP["rz"]
        z = 12.0 * (1 - s * s)
    elif f < PH["back"][0]:                       # прижим: покачивание ±1,2°
        s = ph("press")
        x, y, rz = IMP["x"], IMP["y"], IMP["rz"]
        ry = 1.2 * math.sin(2 * math.pi * s) * (1 - s)
        rx = 0.8 * math.sin(2 * math.pi * s + 1.3) * (1 - s)
    elif f < PH["land"][0]:                       # возврат дугой
        s = ph("back")
        e = sstep(s)
        x, y = lerp(IMP["x"], REST["x"], e), lerp(IMP["y"], REST["y"], e)
        z = 26.0 * math.sin(math.pi * min(s * 1.1, 1.0)) * (1 - 0.3 * s) + 7.0 * s
        rz = lerp(IMP["rz"], REST["rz"], sstep(min(1.0, s * 1.15)))
        ry = -4.0 * math.sin(math.pi * s)                                # наклон в сторону движения (−X)
    elif f < PH["land"][1]:                       # посадка с затуханием
        s = ph("land")
        z = 7.0 * (1 - sstep(s))
        ry = 1.2 * math.sin(math.pi * s * 1.5) * (1 - s)
    return x, y, z, rx, ry, rz


def apply_pose(root, f):
    x, y, z, rx, ry, rz = pose(f)
    root.location = (x * MM, y * MM, z * MM)
    root.rotation_euler = Euler((math.radians(rx), math.radians(ry), math.radians(rz)), "XYZ")


# ---------------------------------------------------------------------- сцена
t0 = time.time()
bpyx.clear_scene()
root, parts = build()
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 0, NF - 1
for f in range(NF):                               # ключи на каждый кадр (для размытия движения)
    apply_pose(root, f)
    root.keyframe_insert("location", frame=f)
    root.keyframe_insert("rotation_euler", frame=f)
if root.animation_data and root.animation_data.action:                 # 5.x: F-кривые — в channelbag слота (дрейф №68)
    from bpy_extras import anim_utils
    ad = root.animation_data
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for crv in cb.fcurves:
        for kp in crv.keyframe_points:
            kp.interpolation = "LINEAR"
st = D.fresh_collection("STAGE")
pl = bpyx.primitive("plane", "SD_ShadowCatcher", size=1.2, location=(-0.04, 0.02, 0.0), collection=st)
pl.is_shadow_catcher = True
# камера: взгляд строго вниз, матрица параллельна листу, кадр — сдвигом объектива
PW = (FRAME["x1"] - FRAME["x0"]) * MM
cd = bpy.data.cameras.new("SD_StampCam")
cd.sensor_fit = "HORIZONTAL"
cd.sensor_width = 36.0
cd.lens = 36.0 * CAM["h"] / (FRAME["x1"] - FRAME["x0"])
cd.clip_start, cd.clip_end = 0.01, 5.0
fx, fy = (FRAME["x0"] + FRAME["x1"]) / 2, (FRAME["y0"] + FRAME["y1"]) / 2
cd.shift_x = (fx - CAM["x"]) / (FRAME["x1"] - FRAME["x0"])
cd.shift_y = (fy - CAM["y"]) / (FRAME["x1"] - FRAME["x0"])
cam = bpy.data.objects.new("SD_StampCam", cd)
cam.location = (CAM["x"] * MM, CAM["y"] * MM, CAM["h"] * MM)
cam.rotation_euler = (0.0, 0.0, 0.0)
st.objects.link(cam)
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RES[0], RES[1], 100
# свет: солнце слева и чуть сверху по кадру (−X, +Y), угол места 60°, мягкое 3°; свод белый
L = D.fresh_collection("STAGE_LIGHT")
az_dir = Vector((-0.94, 0.34, 0.0)).normalized()
el = math.radians(60)
sun_dir = Vector((az_dir.x * math.cos(el), az_dir.y * math.cos(el), math.sin(el)))
bpyx.add_light("SUN", "Sun", tuple(sun_dir * 1.0), (0, 0, 0), energy=2.4, size=math.radians(3.0), collection=L)
S.world_color("#ffffff", 0.55)
S.cycles(samples)
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
bpy.context.view_layer.update()


# отображение листа (мм) → пиксели кадра (сверху вниз) по трём точкам
def px_of(xmm, ymm):
    u, v, _ = world_to_camera_view(sc, cam, Vector((xmm * MM, ymm * MM, 0.0)))
    return [u * RES[0], (1 - v) * RES[1]]


mapping = {"o": px_of(0, 0), "x10": px_of(10, 0), "y10": px_of(0, 10)}
build_s = round(time.time() - t0, 2)
which = opt("--frames", "all")
frames = list(range(NF)) if which == "all" else [int(v) for v in which.split(",")]
# кадры покоя одинаковы: 0–1 и 31–37 рендерим по одному (0 и 31), остальные — копии в дообработке
REST_END = PH["land"][1]
render_list = [f for f in frames if not (f == 1 or f > REST_END)] if which == "all" else frames
times = {}
for f in render_list:
    sc.frame_set(f)
    r = bpyx.render_still(f"{out}/frames/f{f:03d}.png", resolution=RES, samples=samples, transparent=True)
    times[f] = r["sec"]
    print("STAMP", f, r["sec"], flush=True)
tris = sum(bpyx.object_stats(o).get("tris", 0) for o in parts)
bpy.ops.wm.save_as_mainfile(filepath=f"{out}/stamp.blend")
S.save_json(f"{out}/stamp_clip.json", {
    "fps": FPS, "frames": NF, "res": RES, "frame_mm": FRAME, "cam_mm": CAM, "imp": IMP, "rest": REST, "mapping_px": mapping,
    "px_per_mm": round((mapping["x10"][0] - mapping["o"][0]) / 10, 4), "contact_frame": CONTACT, "phases": PH, "rendered": render_list,
    "copies": {"1": 0, **{str(f): REST_END for f in range(REST_END + 1, NF)}}, "samples": samples, "tris": tris, "build_s": build_s,
    "render_s": {str(k): v for k, v in times.items()}, "render_s_total": round(sum(times.values()), 1),
    "lens_mm": cd.lens, "shift": [cd.shift_x, cd.shift_y], "light": "sun el 60°, 3°, 2,4 Вт/м² из (−0,94; 0,34); свод #fff 0,55"})
print("STAMP done", json.dumps({"total_s": round(sum(times.values()), 1), "px_per_mm": (mapping["x10"][0] - mapping["o"][0]) / 10}))
