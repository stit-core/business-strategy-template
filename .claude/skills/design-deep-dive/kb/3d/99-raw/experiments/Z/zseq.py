"""zseq — кадры и секвенции «Звена» для страницы B (дорожка Z2, фаза 2), Blender 5.2.2.

Сюжет — формулы scene.js v3 (CD/src/scene.js: storyFrame, scanFrame) один в один для неподвижного кадра (без IK, пробуждения и
пружины — они зависят от скорости ввода): позы, разнос по модулям, доворот кольца, «подскок», свет колец (питание гаснет при разносе,
загорается при фиксации, вспышка), камера кода (дуга, дистанция 5,9 → 10,2 м, fov 30°, setViewOffset). Сдвиг кадра переводится в
единицы Blender: при sensor_fit VERTICAL shift меряется в долях ВЫСОТЫ кадра, у three setViewOffset — в долях ширины (x) и высоты (y).
Первый отрезок сюжета B (t 0…1, уход hero) — «кран» от камеры постера H4m к камере кода в t = 1.

Сцены:
  story — вся рука, студия S1 неподвижна в мире (под камеру H4m); ореол — экранный, в градиенте фона, держится за рукой;
          светодиоды колец — свои материалы на модуль, вспышка фиксации — оранжевая лампа у кольца (светит и корпуса, и пол).
  scan  — сустав J3 крупно (×2,45, поза и камера scanFrame); усиленный рентген: плоскость скана режет корпус и ВСЮ начинку
          (сечение шейдером: выше плоскости — корпус «призраком», начинка убрана; изнанка ниже плоскости — плоская «крышка сечения»),
          кромка скана светится на корпусе; слои привода расходятся вдоль оси, ротор и генератор волн вращаются; тёплая лампа —
          только медь, холодная контровая — сталь, ореол дымки за суставом.

    blender -b blend/zveno_render_h3.blend --python zseq.py -- --scene story|scan --jobs jobs.json [--engine cycles|eevee]
          [--samples 48] [--budget 840] [--out DIR]
    jobs.json: [{"name": "f000", "t": 0.0, "mobile": false, "res": [1280, 800]}, …] — кадры, уже лежащие на диске, пропускаются.
"""
import json
import math
import os
import sys
import time

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
for p in (R + "/03-bpy-api/snippets", R + "/99-raw/experiments/D1/_lib", Z + "/lib", Z):
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bpyx  # noqa: E402
import d1lib as D  # noqa: E402
import zkin as K  # noqa: E402
import zpass as ZP  # noqa: E402
import zstudio as S  # noqa: E402
import zrender as ZR  # noqa: E402

PI = math.pi
# Z3: ореол сюжета (k, r) и пиковая мощность лампы вспышки — константы + переопределение из задания кадра (halo_k, halo_r, flash_w)
HALO_STORY = (6.5, 0.42)        # Z3: к H4m (кольцо фона за рукой L* 37, пик ≈ 45–50); было 3,0 / 0,55 (it3: 28 / 32)
HALO_STORY_M = (6.0, 0.3)
HALO_SCAN = (2.4, 0.42)
FLASH_W = 6.0                   # Z3: 320 Вт в 5 см от лака → 24 Вт в 0,7 м (≈ 1,5 ключа — всё ещё «лосось» на корпусах) → 6 Вт (≈ 0,35 ключа): вспышку несут LED и лак кольца
S.ENV_MASK = (0.45, 0.75)          # пол не отражает софтбоксы HDRI у горизонта (пятно на полу при камере кода, t 1,8)


# ---------------------------------------------------------------------------------------------- математика scene.js
def clamp(x, a=0.0, b=1.0):
    return min(b, max(a, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def ease(x):
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def lerp(a, b, t):
    return a + (b - a) * t


def bump(x, a, b, c):
    if x <= a or x >= c:
        return 0.0
    return ease(seg(x, a, b)) if x < b else 1 - ease(seg(x, b, c))


def snap(u):
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    return 1 - math.exp(-6 * u) * math.cos(9 * u)


def blend_pose(p, q, t):
    return {k: lerp(p[k], q[k], t) for k in p}


def rot(axis, a):
    return Matrix.Rotation(a, 4, axis)


# ---------------------------------------------------------------------------------------------- сюжет «модули»
def story_state(t):
    """Неподвижный кадр storyFrame(t): поза, разнос/подскок/доворот по модулям, свет колец, модуляция ключа и контрового."""
    a = clamp(t - 1)
    straighten = ease(seg(a, 0.06, 0.2))
    explode = ease(seg(a, 0.16, 0.34))
    first = ease(seg(a, 0.88, 1.0))
    pose = blend_pose(ZP.POSE_WORK, ZP.POSE_REST, straighten)
    if first > 0:
        pose = blend_pose(ZP.POSE_REST, ZP.POSE_FIRST, first)
    power = 1 - explode
    mods, lock_k, lock_at = {}, 0.0, None
    for i, k in enumerate(ZP.ORDER):
        s0 = 0.52 + i * 0.04
        u = seg(a, s0, s0 + 0.12) if a >= 0.52 else 0.0
        back = ease(u)
        out = explode if a < 0.52 else explode * (1 - back)
        hover = 0.07 * bump(u, 0.2, 0.62, 0.86) if (a >= 0.52 and i > 0) else 0.0
        twist = seg(u, 0, 0.3) * (1 - snap(seg(u, 0.72, 1))) if (a >= 0.52 and i > 0) else 0.0
        lock = seg(a, 0.52, 0.56) if i == 0 else seg(u, 0.86, 0.94)
        lit = power if a < 0.52 else lock
        flash = bump(u, 0.84, 0.92, 1.0) if a >= 0.52 else 0.0
        mods[k] = {"out": out, "hover": hover, "twist": twist, "lit": lit, "flash": flash}
        if flash > lock_k:
            lock_k, lock_at = flash, k
    return {"t": t, "a": a, "pose": pose, "mods": mods, "explode": explode, "straighten": straighten, "first": first,
            "lock_k": lock_k, "lock_at": lock_at,
            "key_k": 1 - 0.12 * bump(a, 0.14, 0.34, 0.56), "rim_k": 1 + 0.45 * bump(a, 0.14, 0.34, 0.56)}


def module_mats_three(st):
    """M_k = T(ex·out, ey·out + hover, ez·out) · W_k · Rx(er·out·0,5) · Ry(er·out + twist·π/2) · Rz(er·out·0,3) — как storyFrame."""
    W = K.pivot_world_three(st["pose"])
    M = {}
    for k in ZP.ORDER:
        m = st["mods"][k]
        ex, ey, ez, er = ZP.EXPLODE[k]
        o = m["out"]
        T = Matrix.Translation(Vector((ex * o, ey * o + m["hover"], ez * o)))
        Rm = rot("X", er * o * 0.5) @ rot("Y", er * o + m["twist"] * PI / 2) @ rot("Z", er * o * 0.3)
        M[k] = T @ W[k] @ Rm
    return M


def code_cam_story(t, mobile=False, st=None):
    """Камера storyFrame кода (оси three): позиция, цель, fov по вертикали, сдвиг кадра (доли ширины / высоты, как setViewOffset)."""
    st = st or story_state(t)
    a = st["a"]
    h_to = ease(clamp(t))
    far = max(st["explode"] * (1 - ease(seg(a, 0.52, 0.9))), st["straighten"] * 0.55 * (1 - st["first"]))
    arc = 0.24 * bump(a, 0.16, 0.42, 0.66) - 0.1 * bump(a, 0.6, 0.8, 0.96)
    low = bump(a, 0.58, 0.8, 0.98)
    push = ease(seg(a, 0.9, 1.0))
    dist = lerp(5.9, 10.2, far) * (1 - 0.08 * push) * (1.3 if mobile else 1.0)
    yaw = lerp(0.62, 0.38, h_to) + lerp(0, -0.18, a) + arc
    ty = lerp(1.28, 2.3, far)
    pos = (math.sin(yaw) * dist, ty + lerp(0.85, 0.45, far) - 0.5 * low, math.cos(yaw) * dist)
    return {"pos": pos, "tgt": (0.05, ty, 0.0), "fov": 30.0,
            "sw": 0.0 if mobile else lerp(-0.2, -0.12, h_to), "sh": lerp(0.18, 0.1, h_to) if mobile else 0.0}


# камера постера B (H4m, фаза 1): az 0,5, подъём 2°, 6,4 м до цели (0,05; 1,18; 0), 50 мм при ширине сенсора 36 мм → fov_v 25,36° (16:10)
def _h4m():
    tgt = (0.05, 1.18, 0.0)
    el, az, d = math.radians(2.0), 0.5, 6.4
    pos = (tgt[0] + math.sin(az) * math.cos(el) * d, tgt[1] + math.sin(el) * d, tgt[2] + math.cos(az) * math.cos(el) * d)
    fov = math.degrees(2 * math.atan(math.tan(math.atan(18 / 50)) / 1.6))
    return {"pos": pos, "tgt": tgt, "fov": fov, "sw": -0.2, "sh": 0.0}


H4M = _h4m()
# телефон: отдельный портретный кадр «по-H4m» — низкая камера, рука в верхних двух третях, низ — под текст
H4M_PHONE = {"pos": None, "tgt": (0.05, 1.3, 0.0), "fov": 30.0, "sw": 0.0, "sh": 0.17, "az": 0.5, "el": 3.0, "dist": 8.6}


def _phone_hero():
    c = dict(H4M_PHONE)
    tgt = c["tgt"]; el = math.radians(c["el"]); az = c["az"]; d = c["dist"]
    c["pos"] = (tgt[0] + math.sin(az) * math.cos(el) * d, tgt[1] + math.sin(el) * d, tgt[2] + math.cos(az) * math.cos(el) * d)
    return c


def _cyl(p):
    return math.atan2(p[0], p[2]), math.hypot(p[0], p[2]), p[1]


def lerp_cam(c0, c1, w):
    y0, r0, h0 = _cyl(c0["pos"]); y1, r1, h1 = _cyl(c1["pos"])
    yaw, rr, hh = lerp(y0, y1, w), lerp(r0, r1, w), lerp(h0, h1, w)
    return {"pos": (math.sin(yaw) * rr, hh, math.cos(yaw) * rr),
            "tgt": tuple(lerp(a, b, w) for a, b in zip(c0["tgt"], c1["tgt"])),
            "fov": lerp(c0["fov"], c1["fov"], w), "sw": lerp(c0["sw"], c1["sw"], w), "sh": lerp(c0["sh"], c1["sh"], w)}


def b_cam_story(t, mobile=False, st=None, code=False):
    """Камера страницы B: t < 1 — кран от постера (H4m / телефонный H4m) к камере кода в t = 1; дальше — камера кода.
    code=True — камера кода везде (кадры судьи «те же камеры, что у a-code»)."""
    if code or t >= 1.0:
        return code_cam_story(t, mobile, st)
    c0 = _phone_hero() if mobile else H4M
    return lerp_cam(c0, code_cam_story(1.0, mobile), ease(clamp(t)))


# ---------------------------------------------------------------------------------------------- сюжет «внутри»
def scan_state(t, mobile=False):
    sweep = ease(seg(t, 0.06, 0.52))
    spread = ease(seg(t, 0.6, 0.92))
    c = lerp(0.26, -0.015, sweep)
    dist = (5.0 if mobile else 4.3) * (1 - 0.05 * bump(t, 0.5, 0.8, 1.01))
    yaw = 0.18 + 0.1 * bump(t, 0.1, 0.45, 0.8)
    cam = {"pos": (math.sin(yaw) * dist, 1.62, math.cos(yaw) * dist), "tgt": (0.0, 1.2, 0.0), "fov": 30.0,
           "sw": 0.0 if mobile else 0.13, "sh": 0.12 if mobile else 0.0}
    sc = 1.9 if mobile else 2.45
    M3 = (Matrix.Translation((0, 1.2, 0)) @ rot("X", 0.42) @ rot("Y", lerp(-0.2, -0.42, t)) @ rot("Z", 0.04)
          @ Matrix.Scale(sc, 4))
    return {"t": t, "c": c, "sweep": sweep, "spread": spread, "spin": t * PI * 6, "cam": cam, "M3": M3, "scale": sc,
            "glow": 3.2 * bump(t, 0.02, 0.3, 0.6) + 0.6}


# ---------------------------------------------------------------------------------------------- камера Blender
def set_camera(cam, c, res):
    """c: оси three, fov по вертикали, sw/sh — сдвиг как setViewOffset (x — доли ширины, y — доли высоты, y вниз)."""
    W, H = res
    cd = cam.data
    cd.sensor_fit = "VERTICAL"; cd.sensor_height = 24.0
    cd.lens = 12.0 / math.tan(math.radians(c["fov"]) / 2)
    cd.shift_x = c["sw"] * W / H          # VERTICAL: shift в долях высоты → доля ширины × W/H
    cd.shift_y = -c["sh"]                 # three: y вниз (объект выше) → Blender: кадр вниз
    cam.location = K.t2b(c["pos"])
    bpyx.look_at(cam, K.t2b(c["tgt"]))
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = W, H


def drop_objects(obs):
    """Удалить невидимое в кадре (память и BVH): объекты + осиротевшие меши."""
    for o in obs:
        bpy.data.objects.remove(o, do_unlink=True)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)


def halo(cam, p3, res, *, r, k):
    """Экранный ореол фона: центр — проекция точки p3 (оси three) текущей камерой."""
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    v = world_to_camera_view(bpy.context.scene, cam, K.t2b(p3))
    S.set_halo(v.x, v.y, r, k, res[0] / res[1])


# ---------------------------------------------------------------------------------------------- движок
def setup_engine(engine, samples):
    sc = bpy.context.scene
    if engine == "eevee":
        bpyx.set_engine("BLENDER_EEVEE")
        ee = sc.eevee
        ee.taa_render_samples = samples
        ee.use_raytracing = True
        ro = ee.ray_tracing_options
        for k, v in (("resolution_scale", "1"), ("trace_max_roughness", 0.6), ("use_denoise", True)):
            try:
                setattr(ro, k, v)
            except (AttributeError, TypeError):
                pass
        ee.ray_tracing_method = "SCREEN"
        ee.use_shadows = True; ee.shadow_ray_count = 2; ee.shadow_step_count = 8
        ee.use_fast_gi = True; ee.fast_gi_method = "GLOBAL_ILLUMINATION"; ee.fast_gi_quality = 0.5
        ee.volumetric_tile_size = "4"; ee.volumetric_samples = 96; ee.use_volumetric_shadows = False
        ee.clamp_surface_indirect = 10.0
        sc.render.film_transparent = False
    else:
        bpyx.set_engine("CYCLES")
        sc.cycles.samples = samples


# ---------------------------------------------------------------------------------------------- сцена «модули»
class Story:
    def __init__(self, engine):
        self.coll, obs = ZR.asset()
        drop_objects([o for o in obs if o.name.startswith("j3_in_")])   # начинка J3 в «модулях» не видна (память, BVH)
        self.coll, obs = ZR.asset()
        self.obs = obs
        self.roots = {k: bpy.data.objects[k] for k in ZP.ORDER}
        c, r, mn, mx = ZR.bbox_r(ZR.robot_only(obs))          # габарит в позе hero (как фаза 1: r ≈ 1,49 м)
        self.r = r
        camc = D.fresh_collection("Z_CAM")
        pos, tgt = K.t2b(H4M["pos"]), K.t2b(H4M["tgt"])
        self.cam = S.camera_lookat(camc, pos, tgt, fov_v_deg=H4M["fov"])
        st, lights, fl, bd, hz = ZR.stage("S1", pos, tgt, r, key_E=2.4, floor_E=1.4)    # свет неподвижен в мире; дымка —
        # не объёмом (шум и цена кадра), а экранным ореолом в градиенте фона (S.set_halo на кадр)
        self.lights = {lo.name: lo for lo in lights}
        self.E0 = {n: lo.data.energy for n, lo in self.lights.items()}
        self.tgt_b = tgt
        # светодиоды и кольца — свои материалы на модуль (свет колец по сюжету)
        self.led, self.ring = {}, {}
        for k in ZP.ORDER:
            for suffix, store in (("_ring_led", self.led), ("_ring", self.ring)):
                ob = bpy.data.objects.get(k + suffix)
                if ob is None or not ob.material_slots:
                    continue
                m = ob.material_slots[0].material.copy(); m.name = f"{ob.material_slots[0].material.name}_{k}"
                ob.material_slots[0].material = m
                store[k] = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        for k, p in self.ring.items():
            bpyx.set_input(p, "Emission Color", "#ff5a1f")
        # вспышка фиксации: оранжевая точечная лампа у кольца (свет по сюжету: корпуса-соседи и пол)
        ld = bpy.data.lights.new("L_story", "POINT"); ld.color = tuple(bpyx.color("#ff6a2a")[:3]); ld.energy = 0.0
        ld.shadow_soft_size = 0.06
        self.story = bpy.data.objects.new("L_story", ld); st.objects.link(self.story)
        setup_engine(engine, 48)

    def frame(self, t, mobile, res, code_cam=False, opts=None):
        opts = opts or {}
        s = story_state(t)
        M = module_mats_three(s)
        for k, e in self.roots.items():
            e.matrix_world = K.to_blender(M[k])
        bpy.context.view_layer.update()
        for k, p in self.led.items():
            m = s["mods"][k]
            bpyx.set_input(p, "Emission Strength", 5.0 * m["lit"] + 34.0 * m["flash"])
        for k, p in self.ring.items():
            bpyx.set_input(p, "Emission Strength", 1.6 * s["mods"][k]["flash"])
        c = b_cam_story(t, mobile, s, code=code_cam)
        set_camera(self.cam, c, res)
        bpy.context.view_layer.update()
        if s["lock_at"] and s["lock_k"] > 1e-3:
            ro = bpy.data.objects.get(s["lock_at"] + "_ring")
            if ro is not None:
                cw = ro.matrix_world @ (sum((Vector(v) for v in ro.bound_box), Vector()) / 8)
            else:                                            # у захвата кольца нет (Z3: пачка падала на f082) — точка модуля
                cw = bpy.data.objects[s["lock_at"]].matrix_world.translation.copy()
            # Z3: свет по сюжету ≈ 0,7 м от кольца к камере и выше (как у A «0,7 м над лаком»); было 0,25 м от оси = 5 см от лака J3
            # (r 0,2 м) — сотни Вт/м² на корпусе при ключе 2,4: весь сустав и пол розовели при любой мощности (it4: 12 и 30 Вт)
            to_cam = (self.cam.matrix_world.translation - cw).normalized()
            self.story.location = cw + to_cam * 0.7 + Vector((0.0, 0.0, 0.25))
            self.story.data.energy = float(opts.get("flash_w", FLASH_W)) * s["lock_k"]
        else:
            self.story.data.energy = 0.0
        for n in ("L_key",):
            self.lights[n].data.energy = self.E0[n] * s["key_k"]
        for n in ("L_rimL", "L_rimR"):
            self.lights[n].data.energy = self.E0[n] * s["rim_k"]
        # ореол за рукой — по проекции цели камеры (как setGlow кода: (0,05; 0,95·tgtY; 0)), чуть выше центра руки
        hk, hr = HALO_STORY_M if mobile else HALO_STORY
        halo(self.cam, (c["tgt"][0], c["tgt"][1] * 0.95 + 0.25, 0.0), res, r=float(opts.get("halo_r", hr)), k=float(opts.get("halo_k", hk)))
        return {"a": round(s["a"], 4), "lock_at": s["lock_at"], "lock_k": round(s["lock_k"], 3)}


# ---------------------------------------------------------------------------------------------- рентген-сечение (шейдер)
CAP = {  # материал → (цвет крышки сечения, металл, шероховатость): сечение «как на техническом разрезе» — светлее детали, полуматовое
    "Z_lamination": ((0.56, 0.58, 0.61), 0.3, 0.45), "Z_copper": ((0.88, 0.40, 0.17), 0.25, 0.4),   # Z3: было (0,9; 0,46; 0,25) м 0,35 — бледно-розовая без оранжевой лампы
    "Z_steelb": ((0.7, 0.71, 0.73), 0.4, 0.35), "Z_steel": ((0.7, 0.71, 0.73), 0.4, 0.35),
    "Z_magnet": ((0.62, 0.62, 0.64), 0.4, 0.35), "Z_pcb": ((0.3, 0.36, 0.16), 0.0, 0.6),
    "Z_blackox": ((0.3, 0.3, 0.32), 0.3, 0.4), "Z_chip": ((0.1, 0.1, 0.11), 0.0, 0.5),
    "Z_encoder": ((0.75, 0.75, 0.77), 0.4, 0.3), "Z_gold": ((0.95, 0.72, 0.3), 0.5, 0.3), "Z_alu": ((0.75, 0.76, 0.78), 0.4, 0.35),
    # корпус: сечение литой стенки (алюминий под белым лаком), крышек (графит), кольца-замка (оранжевый лак)
    "Z_shell": ((0.74, 0.76, 0.79), 0.35, 0.45), "Z_cap": ((0.4, 0.42, 0.45), 0.5, 0.4), "Z_ring": ((0.86, 0.26, 0.09), 0.0, 0.5),
    "Z_led": ((0.86, 0.26, 0.09), 0.0, 0.5),
}


def cut_params_group():
    """Общая группа: нормаль плоскости сечения в мире (задаётся на кадр) — нормаль крышек сечения."""
    ng = bpy.data.node_groups.get("Z_CutN")
    if ng is None:
        ng = bpy.data.node_groups.new("Z_CutN", "ShaderNodeTree")
        ng.interface.new_socket(name="N", in_out="OUTPUT", socket_type="NodeSocketVector")
        cx = ng.nodes.new("ShaderNodeCombineXYZ"); cx.name = "N"
        go = ng.nodes.new("NodeGroupOutput")
        ng.links.new(cx.outputs[0], go.inputs[0])
    return ng


def cut_material(src, empty, *, shell, band=0.0045, accent="#ff5a1f", glow_k=5.0):
    """Копия материала с сечением по плоскости z = 0 пустышки empty (её оси и масштаб — оси сустава):
    z > 0 — убрано: корпус — слабый «призрак» (только блики по Френелю), начинка — прозрачна; изнанка ниже плоскости —
    плоская крышка сечения (нормаль плоскости; цвет — по материалу: стенка корпуса, графит крышек, медь, сталь…);
    у белого корпуса внутренняя стенка (нормаль к оси) — тёмная; кромка скана светится только на лицевой стороне корпуса."""
    base = next((k for k in CAP if src.name.startswith(k)), None)
    col, met, rough = CAP.get(base, ((0.6, 0.6, 0.62), 0.3, 0.4))
    m = src.copy(); m.name = src.name + ("_cutS" if shell else "_cutI")
    nt = m.node_tree
    outs = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"]
    out = next((n for n in outs if n.is_active_output), outs[0])
    if not out.inputs["Surface"].links:
        return m
    solid = out.inputs["Surface"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.object = empty
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; nt.links.new(sep.outputs["Z"], gt.inputs[0]); gt.inputs[1].default_value = 0.0
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    cap = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bpyx.set_input(cap, "Base Color", (*col, 1.0)); bpyx.set_input(cap, "Metallic", met); bpyx.set_input(cap, "Roughness", rough)
    grp = nt.nodes.new("ShaderNodeGroup"); grp.node_tree = cut_params_group()
    nt.links.new(grp.outputs["N"], cap.inputs["Normal"])
    front = solid
    if shell and base == "Z_shell":                       # внутренняя стенка полого корпуса (нормаль к оси) — тёмная, матовая
        vt = nt.nodes.new("ShaderNodeVectorTransform"); vt.vector_type = "NORMAL"; vt.convert_from = "WORLD"; vt.convert_to = "OBJECT"
        nt.links.new(geo.outputs["Normal"], vt.inputs["Vector"])
        tco = nt.nodes.new("ShaderNodeTexCoord")
        sn = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(vt.outputs["Vector"], sn.inputs["Vector"])
        sp = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tco.outputs["Object"], sp.inputs["Vector"])
        m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; nt.links.new(sn.outputs["Y"], m1.inputs[0]); nt.links.new(sp.outputs["Y"], m1.inputs[1])
        m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY_ADD"; nt.links.new(sn.outputs["Z"], m2.inputs[0]); nt.links.new(sp.outputs["Z"], m2.inputs[1])
        nt.links.new(m1.outputs[0], m2.inputs[2])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; nt.links.new(m2.outputs[0], lt.inputs[0]); lt.inputs[1].default_value = -0.02
        wall = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bpyx.set_input(wall, "Base Color", (0.07, 0.073, 0.08, 1.0)); bpyx.set_input(wall, "Roughness", 0.65)
        mw = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lt.outputs[0], mw.inputs[0]); nt.links.new(solid, mw.inputs[1]); nt.links.new(wall.outputs[0], mw.inputs[2])
        front = mw.outputs[0]
    below = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Backfacing"], below.inputs[0]); nt.links.new(front, below.inputs[1]); nt.links.new(cap.outputs[0], below.inputs[2])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    if shell:                                             # призрак убранной половины: прозрачно + блики софтбоксов по Френелю
        lw = nt.nodes.new("ShaderNodeLayerWeight"); bpyx.set_input(lw, "Blend", 0.3)
        pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; nt.links.new(lw.outputs["Facing"], pw.inputs[0]); pw.inputs[1].default_value = 3.0
        ma = nt.nodes.new("ShaderNodeMath"); ma.operation = "MULTIPLY_ADD"; nt.links.new(pw.outputs[0], ma.inputs[0])
        ma.inputs[1].default_value = 0.14; ma.inputs[2].default_value = 0.004; ma.use_clamp = True
        gl = nt.nodes.new("ShaderNodeBsdfGlossy"); bpyx.set_input(gl, "Roughness", 0.22)
        bpyx.set_input(gl, "Color", (0.9, 0.93, 0.97, 1.0))
        ghost = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(ma.outputs[0], ghost.inputs[0]); nt.links.new(tr.outputs[0], ghost.inputs[1]); nt.links.new(gl.outputs[0], ghost.inputs[2])
        removed = ghost.outputs[0]
    else:
        removed = tr.outputs[0]
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(below.outputs[0], mx.inputs[1]); nt.links.new(removed, mx.inputs[2])
    final = mx.outputs[0]
    if shell:                                             # кромка скана: полоса у плоскости, только лицевые грани
        ab = nt.nodes.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; nt.links.new(sep.outputs["Z"], ab.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
        bpyx.set_input(mr, "From Min", 0.0); bpyx.set_input(mr, "From Max", band); bpyx.set_input(mr, "To Min", 1.0); bpyx.set_input(mr, "To Max", 0.0)
        nt.links.new(ab.outputs[0], bpyx.sock(mr, "Value"))
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "SUBTRACT"; fr.inputs[0].default_value = 1.0
        nt.links.new(geo.outputs["Backfacing"], fr.inputs[1])
        ms = nt.nodes.new("ShaderNodeMath"); ms.operation = "MULTIPLY"; nt.links.new(bpyx.sock(mr, "Result", out=True), ms.inputs[0])
        nt.links.new(fr.outputs[0], ms.inputs[1])
        ms2 = nt.nodes.new("ShaderNodeMath"); ms2.operation = "MULTIPLY"; nt.links.new(ms.outputs[0], ms2.inputs[0]); ms2.inputs[1].default_value = glow_k
        em = nt.nodes.new("ShaderNodeEmission"); bpyx.set_input(em, "Color", bpyx.color(accent))
        nt.links.new(ms2.outputs[0], em.inputs["Strength"])
        ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(final, ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
        final = ad.outputs[0]
    nt.links.new(final, out.inputs["Surface"])
    try:
        m.surface_render_method = "DITHERED"
    except (AttributeError, TypeError):
        pass
    m.use_backface_culling = False
    return m


# группы начинки: сдвиг вдоль оси (как scanFrame: медь +0,07·0,9, генератор −0,03·0,9, плата/энкодер −0,07·0,9) и вращение
def inner_group(name):
    n = name[len("j3_in_"):]
    if n.startswith(("stator", "coil", "winding", "endwind")):
        return "motor", 0.063, 0.0
    if n.startswith(("rotor", "mag_")):
        return "motor", 0.063, 1.0
    if n.startswith(("wavegen", "flexbearing", "flexspline")):
        return "wave", -0.027, 1.0
    if n.startswith(("circspline", "csscrew")):
        return "gear", 0.0, 0.0
    if n.startswith(("xrb_in",)):
        return "out", 0.0, -1 / 12
    if n.startswith(("xrb_out", "shaft")):
        return "out", 0.0, 0.0
    if n.startswith(("encoder", "slot_")):
        return "enc", -0.063, -1 / 12
    if n.startswith(("readhead", "pcb", "ic_", "capa_", "smd_")):
        return "enc", -0.063, 0.0
    return "other", 0.0, 0.0


class Scan:
    def __init__(self, engine, mobile=False, inner_mode="cut"):
        # inner_mode: "cut" — плоскость режет и корпус, и всю начинку (Z2); "whole" — режется только корпус, начинка цельная (как у кода
        # A и гибрида C, но материалами Cycles) — Z3: цельные детали читаются сразу, сечение мелких деталей — «ящик с брусками»
        self.inner_mode = inner_mode
        self.coll, obs = ZR.asset()
        self.j3 = bpy.data.objects["j3"]
        keep = set(self.j3.children_recursive)
        drop_objects([o for o in obs if o not in keep])                 # в «скане» видна только J3 (память ≈ −1 ГБ)
        self.coll, obs = ZR.asset()
        self.inner = [o for o in keep if "_in_" in o.name and o.type == "MESH"]
        self.shell = [o for o in keep if o.type == "MESH" and o not in self.inner]
        # пустышка плоскости сечения — ребёнок сустава (локальные оси и масштаб сустава)
        self.cut = bpy.data.objects.new("Z_CUT", None); self.coll.objects.link(self.cut)
        self.cut.parent = self.j3; self.cut.matrix_parent_inverse = Matrix.Identity(4)
        cache = {}
        for group, obj_list in ((True, self.shell), (False, self.inner)):
            if not group and inner_mode == "whole":
                continue
            for o in obj_list:
                for slot in o.material_slots:
                    # у связанных копий (винты, щели энкодера) слот сидит на общем меше: вторая копия видит уже «…_cut*» —
                    # без этой проверки строилось сечение от сечения (171 материал матрёшкой, +0,87 ГБ, кадр ×1,5)
                    if slot.material is None or slot.material.name.endswith(("_cutS", "_cutI")):
                        continue
                    key = (slot.material.name, group)
                    if key not in cache:
                        cache[key] = cut_material(slot.material, self.cut, shell=group)
                    slot.material = cache[key]
        self.base = {o.name: o.matrix_basis.copy() for o in self.inner}
        self.grp = {o.name: inner_group(o.name) for o in self.inner}
        # студия под камеру скана (t = 0,5), габарит сустава в масштабе ×2,45
        st0 = scan_state(0.5, mobile)
        camc = D.fresh_collection("Z_CAM")
        pos, tgt = K.t2b(st0["cam"]["pos"]), K.t2b(st0["cam"]["tgt"])
        self.cam = S.camera_lookat(camc, pos, tgt, fov_v_deg=30.0)
        self.j3.matrix_world = K.to_blender(st0["M3"]); bpy.context.view_layer.update()
        r = 0.36 * st0["scale"]
        st, lights, fl, bd, hz = ZR.stage("S1", pos, tgt, r, key_E=2.4, floor_E=1.4)
        fl.hide_render = True
        self.lights = {lo.name: lo for lo in lights}
        # тёплая лампа — только медь, холодная контровая — сталь и ламинация (light linking)
        cu = D.fresh_collection("Z_CU_RECV"); fe = D.fresh_collection("Z_FE_RECV")
        for o in self.inner:
            mn = o.material_slots[0].material.name if o.material_slots and o.material_slots[0].material else ""
            if mn.startswith("Z_copper"):
                cu.objects.link(o)
            elif mn.startswith(("Z_steel", "Z_lamination", "Z_magnet", "Z_encoder")):
                fe.objects.link(o)
        cvec = (pos - tgt).normalized()
        lw = S.area(st, "L_warm", tgt + Vector((0, 0, 1.35)) + cvec * 0.9, tgt, size=0.7, power=S.light_power(1.6, 5.5),
                    color=(1.0, 0.85, 0.69))
        lw.light_linking.receiver_collection = cu
        side = Vector((cvec.y, -cvec.x, 0)).normalized()
        lc = S.area(st, "L_cold", tgt - cvec * 1.6 + side * 1.2 + Vector((0, 0, 0.9)), tgt, size=0.5,
                    power=S.light_power(2.0, 4.0), color=(0.82, 0.9, 1.0))
        lc.light_linking.receiver_collection = fe
        # свет скана: оранжевая лампа в плоскости сечения светит на начинку, пока скан идёт (как story-свет кода)
        ld = bpy.data.lights.new("L_scan", "AREA"); ld.shape = "DISK"; ld.size = 0.5; ld.color = tuple(bpyx.color("#ff6a2a")[:3])
        self.scan_l = bpy.data.objects.new("L_scan", ld); st.objects.link(self.scan_l)
        inn = D.fresh_collection("Z_INNER_RECV")
        for o in self.inner:
            inn.objects.link(o)
        self.scan_l.light_linking.receiver_collection = inn
        setup_engine(engine, 48)
        # Z3: луч над плоскостью проходил «призрак» корпуса + диск энкодера, 64 щели, плату, чипы — при transparent_max_bounces 16
        # путь обрывался в чёрное (чёрные обрывки над плоскостью в it3); детали целиком выше плоскости скрываются на кадр (frame)
        bpy.context.scene.cycles.transparent_max_bounces = 48
        self.meshes = self.shell if inner_mode == "whole" else self.inner + self.shell

    def frame(self, t, mobile, res, code_cam=True, opts=None):
        opts = opts or {}
        s = scan_state(t, mobile)
        self.j3.matrix_world = K.to_blender(s["M3"])
        self.cut.location = (0.0, 0.0, s["c"])
        for o in self.inner:
            g, dx, spin_k = self.grp[o.name]
            o.matrix_basis = Matrix.Translation((dx * s["spread"], 0, 0)) @ rot("X", s["spin"] * spin_k) @ self.base[o.name]
        bpy.context.view_layer.update()
        inv = self.j3.matrix_world.inverted()
        hidden = 0
        for o in self.meshes:                             # целиком над плоскостью сечения — не рендерить (слои прозрачности и BVH)
            mw = o.matrix_world
            zmin = min((inv @ (mw @ Vector(c))).z for c in o.bound_box)
            o.hide_render = zmin > s["c"] + 1e-3
            hidden += o.hide_render
        bpy.context.view_layer.update()
        n_w = (self.j3.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
        cut_params_group().nodes["N"].inputs[0].default_value = n_w.x
        cut_params_group().nodes["N"].inputs[1].default_value = n_w.y
        cut_params_group().nodes["N"].inputs[2].default_value = n_w.z
        # лампа скана — над плоскостью, светит вниз на начинку
        o_w = self.j3.matrix_world @ Vector((0, 0, s["c"] + 0.1))
        self.scan_l.location = o_w
        bpyx.look_at(self.scan_l, self.j3.matrix_world @ Vector((0, 0, -0.2)))
        # Z3: было 14·(glow − 0,6) + 2 Вт в 0,06 от плоскости — при t 0,5 ≈ 44 Вт/м² оранжевого на крышках сечений (18× ключа):
        # вся начинка лососевая, сталь не отличить от меди; теперь волна света — только во время прохода скана (t 0,1–0,45)
        self.scan_l.data.energy = 1.2 * (s["glow"] - 0.6) + 0.1
        set_camera(self.cam, s["cam"], res)
        hk, hr = HALO_SCAN
        halo(self.cam, (0.0, 1.28, 0.0), res, r=float(opts.get("halo_r", hr if not mobile else 0.3)), k=float(opts.get("halo_k", hk)))
        return {"c": round(s["c"], 4), "spread": round(s["spread"], 3), "hidden": hidden}


# ---------------------------------------------------------------------------------------------- пачка кадров
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(n, d=None):
        return argv[argv.index(n) + 1] if n in argv else d
    scene = opt("--scene", "story")
    engine = opt("--engine", "cycles")
    samples = int(opt("--samples", 48))
    budget = float(opt("--budget", 840))
    out = opt("--out", Z + "/out/seq")
    jobs = json.load(open(opt("--jobs")))
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    fast = "--fast" in argv                              # секвенции: меньше отскоков и мягче адаптивная выборка (кадр дешевле)
    S.render_setup(samples=samples, res=tuple(jobs[0].get("res", [1280, 800])), exposure=0.0,
                   adaptive=0.015 if fast else 0.01,
                   bounces=dict(max_bounces=8, diffuse_bounces=3, glossy_bounces=4, transmission_bounces=4, volume_bounces=0)
                   if fast else None)
    mobile0 = bool(jobs[0].get("mobile"))
    # режим начинки скана: ключ --inner-mode или файл jobs/scan_inner_mode.txt (читается при старте процесса — можно переключить
    # уже поставленную в очередь пачку); по умолчанию "cut"
    mf = os.path.join(Z, "jobs", "scan_inner_mode.txt")
    inner_mode = opt("--inner-mode", open(mf).read().strip() if os.path.exists(mf) else "cut")
    X = Story(engine) if scene == "story" else Scan(engine, mobile0, inner_mode)
    print("ZSEQ inner_mode", inner_mode if scene == "scan" else "-", flush=True)
    setup_engine(engine, samples)
    sc = bpy.context.scene
    if engine == "cycles":
        sc.cycles.samples = samples
    log = {"scene": scene, "engine": engine, "samples": samples, "setup_s": round(time.time() - t0, 1), "frames": []}
    print("ZSEQ setup", log["setup_s"], flush=True)
    for j in jobs:
        path = os.path.join(out, j["name"] + ".png")
        if os.path.exists(path) and not j.get("force"):
            continue
        if time.time() - t0 > budget:
            log["stopped"] = "budget"; break
        res = tuple(j.get("res", [1280, 800]))
        info = X.frame(j["t"], bool(j.get("mobile")), res, code_cam=bool(j.get("code_cam", scene == "scan")), opts=j)
        if "samples" in j:
            if engine == "cycles":
                sc.cycles.samples = j["samples"]
            else:
                sc.eevee.taa_render_samples = j["samples"]
        tt = S.render(path)
        rec = {"name": j["name"], "t": j["t"], "mobile": bool(j.get("mobile")), "res": list(res), "sec": tt, **info}
        if j.get("mask"):
            obs = [o for o in X.coll.all_objects if o.type == "MESH" and not o.hide_render]
            stage = [o for o in bpy.data.collections["STAGE"].all_objects]
            S.render_masks(os.path.join(out, j["name"] + "_mask.png"), obs, ZR.shell_objs(obs), stage_objs=stage)
            setup_engine(engine, samples)
            if engine == "cycles":
                sc.cycles.samples = j.get("samples", samples)
        log["frames"].append(rec)
        print("ZSEQ", json.dumps(rec, ensure_ascii=False), flush=True)
    log["total_s"] = round(time.time() - t0, 1)
    for line in open("/proc/self/status"):                 # пиковая память процесса (замечание оркестратора о памяти)
        if line.startswith("VmHWM"):
            log["vmhwm_mb"] = round(int(line.split()[1]) / 1024)
    lp = os.path.join(out, f"log_{scene}_{engine}_{int(time.time())}.json")
    json.dump(log, open(lp, "w"), indent=1, ensure_ascii=False)
    print("ZSEQ done", log["total_s"], "frames", len(log["frames"]), log.get("stopped", ""), "VmHWM", log.get("vmhwm_mb"), flush=True)


if __name__ == "__main__":
    main()
