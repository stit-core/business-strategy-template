# VD — дуэль «нейросеть против Blender»: флакон Velmora (бриф облёта Kling 3, галерея ai-media 01-mouse-scrub) в Cycles.
# Blender 5.2.2, запуск только в фоне через очередь:
#   python3 slot_run.py --heavy --label VD-… -- python3 blender_run.py velmora.py --timeout 900 -- \
#       --scheme S1 --views f000,f030 --res 640x360 --samples 32 --out DIR [--mask] [--blend file.blend] [--caustics]
#   облёт (фаза 2): --orbit N,deg0,deg1 [--dist k0,k1] [--frames a-b] [--mask-frames 0,30,60]  → DIR/<tag>_NNN.png
#       (deg1 − deg0 = 360 — петля без повтора последнего кадра; иначе концы включены: 61,0,25 → шаг 25/60°)
# Паспорт в метрах — P ниже (и в velmora/art-direction.md). Сборка идемпотентна: коллекции ASSET_velmora, STAGE, LIGHTS.
# v6 (фаза 2, VD2): лента — мягкие отражатели с растушёванным краем вместо ламп (видны только ленте, прозрачны для
# остальных: light linking + «прозрачный + эмиссия»), волна толщины плёнки вдоль ленты и полосы у кромок, скруглённая
# кромка (наклон нормали), растворение концов; камень — полированный гранит с искрой (зерно + чешуйки под лаком);
# «воздух» — свечение стены скользящим светом по складкам + Glare в композиторе; вторичное движение ленты rib_sway.
# Поворотный стол: камера и студия неподвижны, флакон с постаментом и лентой вращается (корень Turntable) — свет остаётся
# «как на фото» в любом ракурсе; облёт нейросети 25° + наезд → ракурсы f000/f030/f060 (0 / 12,5 / 25°, дистанция 1 → 0,89).
import json
import math
import os
import sys
import time

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

SNIPPETS = "/home/mm/Документы/app-design/blender-research/03-bpy-api/snippets"
sys.path.insert(0, SNIPPETS)
import bpyx  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "tex")

P = dict(
    # флакон: корпус Ø 60 × 92 мм, 32 рифлёные грани глубиной 1 мм, стенка 2,5 мм, дно 12 мм; крышка Ø 34,4 × 34,4 мм
    R=0.030, H=0.092, r_bottom=0.006, r_shoulder=0.013, neck_r=0.0095, neck_h=0.012, bore_r=0.0066,
    flutes=32, flute_depth=0.0013, flute_seg=16, wall=0.0016, base=0.012,
    cap_r=0.0172, cap_h=0.0344, cap_gap=0.0004,
    label_arc=0.054, label_h=0.0164, label_z=0.047, label_lift=0.00025, label_t=0.00015,
    fill_gap=0.00005, fill_top=0.086,
    # постамент: чёрный мрамор 340 × 240 × 160 мм, повёрнут −32°; флакон в 100 мм от левого торца и 90 мм от переднего края
    block=(0.34, 0.24, 0.16), block_rot=-36.0, bottle_uv=(-0.09, -0.03), block_bevel=0.0015,
    # лента: плёнка 34 мм шириной, 1,6 оборота закрута, концы сходят на нет
    ribbon_w=0.050, ribbon_t=0.0011, ribbon_twist=1.6 * 2 * math.pi, ribbon_phase=math.radians(70),
    ribbon_ctrl=[(-0.32, 0.22, 0.30), (-0.20, 0.16, 0.22), (-0.125, 0.125, 0.165), (-0.05, 0.10, 0.125),
                 (0.025, 0.085, 0.092), (0.07, 0.07, 0.063), (0.115, 0.05, 0.028), (0.17, 0.02, 0.02),
                 (0.23, -0.03, 0.045)],
    # камера: 100 мм, ровная (вертикали прямые), высота 150 мм над постаментом, флакон на правой трети
    lens=100.0, cam_z=0.15, cam_d=0.976, shift_x=-0.23, center_y=0.465, fstop=8.0,
    # студия: циклорама на полу −160 мм, стена в 0,85 м за флаконом
    floor_z=-0.16, wall_y=0.85, cyc_r=0.12,
    film_ior=1.7, film_nm=(250.0, 480.0), dome_w=7.0, film_back_w=0.0, glow_w=40.0,        # v5 1,62; v6b 1,8 — «мыльная плёнка»
    # ---- v6 (фаза 2) ----
    # лента: отражатели вместо ламп (rib_env), шероховатость, скруглённая кромка (доля ширины, наклон °), свечение торца,
    # ширина концов (доля) и растворение концов (доля длины)
    rib_env=True, rib_rough=0.06, rib_edge=0.03, rib_edge_tilt=65.0, rib_rim_glow=0.0, rib_end_w=0.35, rib_fade=0.10,
    rib_edge_glow=1.5, rib_edge_glow_w=0.015,
    rib_shader="disp", rib_ior=1.50, rib_disp=0.03,     # v6c: три Glass R/G/B — дисперсия на клине кромки
    # толщина плёнки, нм: середина + волна вдоль ленты (число волн, шум фазы, рад) + прибавка у кромок
    film_mid=400.0, film_amp=150.0, film_waves=1.4, film_noise=2.5, film_edge=120.0,
    # яркость отражателей ленты (излучение, «как видит камера»): главный сверху-справа, полоса сверху, перед, левый, небо
    env_main=1.8, env_top=3.0, env_front=0.45, env_left=1.2, env_sky=0.10,
    # v6b: купол с долями (азимут °, угол места °, угловой радиус σ °, яркость, K) — по карте направлений 06-look/dir
    env_mode="dome", env_base=0.16,
    env_lobes=[(50, 38, 26, 3.4, 5600), (8, 22, 14, 1.75, 6000), (-5, 68, 16, 2.5, 6500), (-70, 40, 24, 2.0, 6500),
               (105, 14, 10, 2.9, 5200), (-130, 30, 20, 1.4, 6500)],   # v6d: ×1,25 к v6c — лента светится (i3)
    # полосы-«стрип-боксы» (азимут, угол места, наклон длинной оси °, длина °, ширина σ °, яркость, K): резкие штрихи
    # вдоль складок (v6c: узкие круглые доли давали «боке-кружки» — геликоид ленты отражает точку пятном)
    env_strips=[(40, 45, 72, 60, 2.8, 9.0, 6500), (85, 35, 104, 50, 2.6, 10.0, 5600), (-45, 40, 80, 50, 2.6, 8.0, 6500)],
    # v6d: горизонтальная полоса (30°, 62°) убрана — вместе с вертикальными рисовала на ленте «X»
    rib_sway=12.0,             # вторичное движение: фаза закрута + rib_sway·sin(поворот стола), ° (0 — жёсткая; дуга 25°: +5°)
    stone="granite",           # granite | marble (v5)
    gr_grain=450.0, gr_warp=0.0012, gr_mottle=16.0, gr_mottle_amp=0.6, gr_flake=0.012, gr_flake_scale=2400.0,
    gr_jitter=0.35, gr_rough=0.35, gr_flake_rough=0.06, gr_coat_rough=0.035, gr_flake_col="#8a8680",
    gr_c0="#050506", gr_c1="#0e0f10", gr_c2="#242527", gr_c3="#4a4b4d",
    plinth_fill=False,         # v6: постамент вне Fill (лак зеркалил софтбокс — передняя грань 100/255 против 13 у эталона)
    graze_w=0.6,               # скользящий свет слева по передней грани постамента (только постамент), Вт; 0 — нет
    glow2=True, glow2_w=60.0, glow2_pos=(0.32, 0.62, 0.78), glow2_aim=(0.02, 0.85, 0.30), glow2_size=32.0,
    glow2_k=6600.0, wall_sheen_tint="#5f5f5f",   # v6d: свечение только за лентой (зона текста тёмная), нейтральнее (ΔE фона)
    glare=0.2, glare_thr=1.5,  # сила Glare (Fog Glow) и порог бликов (сцена-линейно); i2: 0,3 / 1,0 — пересвет 0,71 %
    sheen_w=0.5,               # низкий контровой «горизонт» (блеск столешницы), Вт — v5 0,33
)
VIEWS = {"f000": (0.0, 1.0), "f030": (12.5, 0.945), "f060": (25.0, 0.89), "f180": (180.0, 1.0),
         "f090": (90.0, 1.0), "f270": (270.0, 1.0)}


# ====================================================================== утилиты геометрии

def obj_from_bm(bm, name, coll, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def arc_pts(c, r, a0, a1, n):
    """Дуга (r, z) окружности центра c радиуса r от угла a0 до a1 (рад), n отрезков, включая концы."""
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def dedup(pts, eps=1e-7):
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append(p)
    return out


def lathe_bm(profile, segments, disp=None):
    """Тело вращения вокруг Z: profile [(r, z, w)] (w — вес рифления 0…1), disp(theta) → 0…1 (0 — гребень, 1 — канавка);
    смещение внутрь по нормали профиля на depth·disp·w делается снаружи (через w, уже умноженный на глубину).
    r ≤ 0 — полюс. Возвращает bmesh (квады + веер у полюсов)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    # нормали профиля (в плоскости r-z) — для смещения рифлей
    n = len(profile)
    norms = []
    for i in range(n):
        a = profile[max(i - 1, 0)]
        b = profile[min(i + 1, n - 1)]
        tr, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tr, tz) or 1.0
        norms.append((tz / L, -tr / L))          # наружу для профиля, идущего снизу вверх снаружи
    rings = []
    for i, (r, z, w) in enumerate(profile):
        if r <= 1e-9:
            rings.append([bm.verts.new((0.0, 0.0, z))])
            continue
        ring = []
        for k in range(segments):
            th = 2 * math.pi * k / segments
            d = (disp(th) * w) if (disp and w > 0) else 0.0
            rr = r - norms[i][0] * d
            zz = z - norms[i][1] * d
            ring.append(bm.verts.new((rr * math.cos(th), rr * math.sin(th), zz)))
        rings.append(ring)
    Ls = [0.0]
    for i in range(1, n):
        Ls.append(Ls[-1] + math.hypot(profile[i][0] - profile[i - 1][0], profile[i][1] - profile[i - 1][1]))
    for j in range(n - 1):
        a, b = rings[j], rings[j + 1]
        v0, v1 = Ls[j] / Ls[-1], Ls[j + 1] / Ls[-1]
        for k in range(segments):
            k2 = (k + 1) % segments
            u0, u1 = k / segments, (k + 1) / segments
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                f = bm.faces.new((a[0], b[k], b[k2])); uvs = ((u0, v0), (u0, v1), (u1, v1))
            elif len(b) == 1:
                f = bm.faces.new((a[k], a[k2], b[0])); uvs = ((u0, v0), (u1, v0), (u0, v1))
            else:
                f = bm.faces.new((a[k], a[k2], b[k2], b[k])); uvs = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
            for loop, uv in zip(f.loops, uvs):
                loop[uvl].uv = uv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


# ====================================================================== материалы (режим «для рендера»: процедуры разрешены)

def nt_links(mat):
    return mat.node_tree, mat.node_tree.links


def mat_glass():
    mat, p = bpyx.principled("VD_Glass", base_color=(1, 1, 1, 1), roughness=0.0, ior=1.52, transmission_weight=1.0)
    nt, L = nt_links(mat)
    va = nt.nodes.new("ShaderNodeVolumeAbsorption")          # толстое дно: едва заметная зелень флинта
    va.inputs["Color"].default_value = (0.93, 0.985, 0.975, 1.0)
    va.inputs["Density"].default_value = 40.0
    out = bpyx.find_node(nt, "OUTPUT_MATERIAL")
    L.new(va.outputs["Volume"], out.inputs["Volume"])
    return mat


def mat_liquid():
    mat, p = bpyx.principled("VD_Cream", base_color="#F6F2EC", roughness=0.30, subsurface_weight=1.0,
                             subsurface_radius=(1.0, 0.82, 0.62), subsurface_scale=0.0020, ior=1.40)   # Subsurface IOR — только у RANDOM_WALK_SKIN
    bpyx.set_enum(p, "subsurface_method", "RANDOM_WALK")
    return mat


def mat_gold():
    """Шампань-золото, шлифовка: анизотропия по касательной вокруг Z + волосяные штрихи в шероховатости (шум, вытянутый
    вдоль Z)."""
    mat, p = bpyx.principled("VD_CapGold", base_color=(0.82, 0.60, 0.38, 1.0), metallic=1.0, roughness=0.22,
                             anisotropic=0.40)
    nt, L = nt_links(mat)
    tg = nt.nodes.new("ShaderNodeTangent"); tg.direction_type = "RADIAL"; tg.axis = "Z"
    L.new(tg.outputs["Tangent"], p.inputs["Tangent"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2600.0, 2600.0, 12.0)     # штрихи вдоль высоты крышки
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0
    nz.inputs["Detail"].default_value = 4.0
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.3, 0.7
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.19, 0.30
    L.new(nz.outputs["Fac"], mr.inputs["Value"]); L.new(mr.outputs["Result"], p.inputs["Roughness"])
    return mat


def mat_label():
    mat, p = bpyx.principled("VD_LabelPaper", roughness=0.62)
    nt, L = nt_links(mat)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ic = nt.nodes.new("ShaderNodeTexImage")
    ic.image = bpy.data.images.load(os.path.join(TEX, "label_color.png"), check_existing=True)
    ic.image.colorspace_settings.name = "sRGB"
    ii = nt.nodes.new("ShaderNodeTexImage")
    ii.image = bpy.data.images.load(os.path.join(TEX, "label_ink.png"), check_existing=True)
    ii.image.colorspace_settings.name = "Non-Color"
    for n in (ic, ii):
        n.interpolation = "Cubic"
        L.new(tc.outputs["UV"], n.inputs["Vector"])
    L.new(ic.outputs["Color"], p.inputs["Base Color"])
    mr = nt.nodes.new("ShaderNodeMapRange")                        # краска чуть глаже бумаги
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.62, 0.42
    L.new(ii.outputs["Color"], mr.inputs["Value"]); L.new(mr.outputs["Result"], p.inputs["Roughness"])
    # волокна бумаги + тиснение краски (буквы вдавлены)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2200.0; nz.inputs["Detail"].default_value = 6.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY_ADD"
    mx.inputs[1].default_value = -0.9
    L.new(ii.outputs["Color"], mx.inputs[0]); L.new(nz.outputs["Fac"], mx.inputs[2])
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.00004
    L.new(mx.outputs["Value"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], p.inputs["Normal"])
    return mat


def mat_marble(name="VD_Marble", base_hex="#111111", vein_hex="#464648", rough=0.09, scale=4.6, vein_w=0.012, ripple=0.14):
    """Полированный чёрный мрамор процедурно: тёмная основа с пятнами + тонкие светлые прожилки (полоса Color Ramp около
    уровня 0,5 шума с искажением) + лёгкая волна шероховатости. ≤ 20 нод."""
    mat, p = bpyx.principled(name, base_color=base_hex, roughness=rough, ior=1.55)
    nt, L = nt_links(mat)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    mp.inputs["Rotation"].default_value = (0.3, 0.2, 0.6)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nv = nt.nodes.new("ShaderNodeTexNoise"); nv.inputs["Scale"].default_value = 1.6
    nv.inputs["Detail"].default_value = 9.0; nv.inputs["Roughness"].default_value = 0.62
    nv.inputs["Distortion"].default_value = 1.1
    L.new(mp.outputs["Vector"], nv.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")                        # прожилки: узкая светлая полоса около 0,5
    els = cr.color_ramp.elements
    els[0].position, els[0].color = 0.5 - vein_w, (0, 0, 0, 1)
    els[1].position, els[1].color = 0.5 + vein_w, (0, 0, 0, 1)
    e = els.new(0.5); e.color = (1, 1, 1, 1)
    L.new(nv.outputs["Fac"], cr.inputs["Fac"])
    nm = nt.nodes.new("ShaderNodeTexNoise"); nm.inputs["Scale"].default_value = 6.0   # пятна основы
    nm.inputs["Detail"].default_value = 5.0
    L.new(mp.outputs["Vector"], nm.inputs["Vector"])
    S_ = bpyx.sock                                                 # у Mix три «A»/«B» разных типов — берём включённый
    mb = nt.nodes.new("ShaderNodeMix"); mb.data_type = "RGBA"; mb.blend_type = "MIX"
    S_(mb, "A").default_value = bpyx.color(base_hex)
    S_(mb, "B").default_value = bpyx.color("#2A2A2A")
    bpyx.link_sockets(nt, nm.outputs["Fac"], S_(mb, "Factor"))
    mv = nt.nodes.new("ShaderNodeMix"); mv.data_type = "RGBA"; mv.blend_type = "MIX"
    S_(mv, "B").default_value = bpyx.color(vein_hex)
    bpyx.link_sockets(nt, cr.outputs["Color"], S_(mv, "Factor"))
    bpyx.link_sockets(nt, S_(mb, "Result", out=True), S_(mv, "A"))
    bpyx.link_sockets(nt, S_(mv, "Result", out=True), p.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")                        # шероховатость: полировка с едва заметной волной
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = rough * 0.7, rough * 1.6
    L.new(nm.outputs["Fac"], rr.inputs["Value"]); L.new(rr.outputs["Result"], p.inputs["Roughness"])
    if ripple > 0:                                                 # следы полировки: шум, вытянутый по диагонали
        mq = nt.nodes.new("ShaderNodeMapping"); mq.inputs["Scale"].default_value = (60.0, 2.5, 60.0)
        mq.inputs["Rotation"].default_value = (0.0, 0.0, 0.7)
        L.new(tc.outputs["Object"], mq.inputs["Vector"])
        nq = nt.nodes.new("ShaderNodeTexNoise"); nq.inputs["Scale"].default_value = 1.0; nq.inputs["Detail"].default_value = 3.0
        L.new(mq.outputs["Vector"], nq.inputs["Vector"])
        bq = nt.nodes.new("ShaderNodeBump"); bq.inputs["Strength"].default_value = ripple
        bq.inputs["Distance"].default_value = 0.0005
        L.new(nq.outputs["Fac"], bq.inputs["Height"]); L.new(bq.outputs["Normal"], p.inputs["Normal"])
    return mat


def mat_ribbon():
    """Переливная плёнка: Principled Thin Wall (лист без преломления толщины) + Thin Film 250…850 нм по шуму вдоль ленты."""
    mat, p = bpyx.principled("VD_RibbonFilm", base_color=(1, 1, 1, 1), roughness=0.08, ior=1.50,
                             transmission_weight=1.0, thin_film_ior=P["film_ior"])
    nt, L = nt_links(mat)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (3.0, 0.6, 1.0)
    L.new(tc.outputs["UV"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 2.0
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.3, 0.7
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = P["film_nm"][0], P["film_nm"][1]
    L.new(nz.outputs["Fac"], mr.inputs["Value"]); L.new(mr.outputs["Result"], p.inputs["Thin Film Thickness"])
    return mat


def mat_backdrop():
    mat, p = bpyx.principled("VD_Backdrop", base_color="#383838", roughness=0.92, sheen_weight=0.6,
                             sheen_roughness=0.45, sheen_tint=P.get("wall_sheen_tint", "#6E655B"))
    return mat


# ---------------------------------------------------------------------- v6 (фаза 2)

def _m(nt, op, a, b=None, c=None, clamp=False):
    """Math-нода: входы — число или сокет (индексы 0/1/2 у Math стабильны); возвращает выход."""
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = float(x)
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[0]


def _v(nt, op, a, b=None, c=None):
    """VectorMath-нода; число → вектор (x, x, x)."""
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    outs = {"DOT_PRODUCT": "Value", "LENGTH": "Value", "DISTANCE": "Value"}
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = (float(x),) * 3
        elif isinstance(x, tuple):
            n.inputs[i].default_value = x
        else:
            nt.links.new(x, n.inputs[i])
    return n.outputs[outs.get(op, "Vector")]


def _smooth(nt, x, lo, hi):
    """smoothstep(lo, hi, x) через Map Range (SMOOTHSTEP, с зажимом)."""
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.data_type = "FLOAT"
    mr.interpolation_type = "SMOOTHSTEP"
    mr.clamp = True
    bpyx.sock(mr, "From Min").default_value = lo
    bpyx.sock(mr, "From Max").default_value = hi
    bpyx.sock(mr, "To Min").default_value = 0.0
    bpyx.sock(mr, "To Max").default_value = 1.0
    nt.links.new(x, bpyx.sock(mr, "Value"))
    return bpyx.sock(mr, "Result", out=True)


def mat_ribbon6(name, side):
    """v6: стеклянная плёнка (1,1 мм, IOR 1,5) + тонкая плёнка IOR film_ior. Толщина плёнки — волна вдоль ленты
    (film_waves волн, фаза шумит на film_noise рад) ± film_amp около film_mid и прибавка film_edge·|2v−1|³ у кромок
    (цветные полосы вдоль кромок). Кромка «скруглена»: у краёв (доля rib_edge ширины) нормаль наклоняется поперёк ленты
    до rib_edge_tilt — край отражает веер направлений и светится линией, как у литой плёнки. side = +1 — лицо,
    −1 — оболочка Solidify (наклон в ту же сторону мира). Концы растворяются (прозрачность по u на долю rib_fade)."""
    mat, p = bpyx.principled(name, base_color=(1, 1, 1, 1), roughness=P["rib_rough"], ior=1.50,
                             transmission_weight=1.0, thin_film_ior=P["film_ior"])
    nt, L = nt_links(mat)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["UV"], sep.inputs["Vector"])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.5, 0.4, 1.0)
    L.new(tc.outputs["UV"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 1.5
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    ph = _m(nt, "MULTIPLY_ADD", nz.outputs["Fac"], P["film_noise"], -0.5 * P["film_noise"])
    arg = _m(nt, "MULTIPLY_ADD", u, 2 * math.pi * P["film_waves"], ph)
    t1 = _m(nt, "MULTIPLY_ADD", _m(nt, "SINE", arg), P["film_amp"], P["film_mid"])
    sv = _m(nt, "MULTIPLY_ADD", v, 2.0, -1.0)                      # −1 … 1 поперёк
    ev = _m(nt, "ABSOLUTE", sv)
    thick = _m(nt, "MULTIPLY_ADD", _m(nt, "POWER", ev, 3.0), P["film_edge"], t1)
    L.new(thick, p.inputs["Thin Film Thickness"])
    if P["rib_edge"] > 0 and P["rib_edge_tilt"] > 0:
        tg = nt.nodes.new("ShaderNodeTangent")
        tg.direction_type = "UV_MAP"
        tg.uv_map = "UVMap"
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        B = _v(nt, "NORMALIZE", _v(nt, "CROSS_PRODUCT", geo.outputs["Normal"], tg.outputs["Tangent"]))
        k = _smooth(nt, ev, 1.0 - 2.0 * P["rib_edge"], 1.0)
        k = _m(nt, "MULTIPLY", _m(nt, "MULTIPLY", k, _m(nt, "SIGN", sv)), side * math.tan(math.radians(P["rib_edge_tilt"])))
        sc_ = nt.nodes.new("ShaderNodeVectorMath")
        sc_.operation = "SCALE"
        L.new(B, sc_.inputs[0])
        L.new(k, bpyx.sock(sc_, "Scale"))
        nn = _v(nt, "NORMALIZE", _v(nt, "ADD", geo.outputs["Normal"], sc_.outputs["Vector"]))
        L.new(nn, p.inputs["Normal"])
    if P["rib_edge_glow"] > 0:        # световод: литая плёнка светится по кромкам (линии эталона по обоим краям)
        eg = _m(nt, "MULTIPLY", _smooth(nt, ev, 1.0 - 2.0 * P["rib_edge_glow_w"], 1.0), P["rib_edge_glow"])
        p.inputs["Emission Color"].default_value = (*kelvin_rgb(6200), 1.0)
        L.new(eg, p.inputs["Emission Strength"])
        mat.cycles.emission_sampling = "NONE"      # не лампа для выборки: видна камере и лучам, шума в свете сцены не даёт
    out = bpyx.find_node(nt, "OUTPUT_MATERIAL")
    if P["rib_fade"] > 0:
        fu = _smooth(nt, _m(nt, "MINIMUM", u, _m(nt, "SUBTRACT", 1.0, u)), 0.0, P["rib_fade"])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader")
        L.new(fu, mx.inputs[0])
        L.new(tr.outputs[0], mx.inputs[1])
        L.new(p.outputs["BSDF"], mx.inputs[2])
        L.new(mx.outputs[0], out.inputs["Surface"])
    return mat


def mat_ribbon7(name, side):
    """v6c: плёнка «как акрил»: три Glass BSDF (R, G, B) с IOR rib_ior ∓ rib_disp — честная дисперсия (в 5.2.2 входа
    Dispersion нет): на ровном листе лучи цветов совпадают (белое стекло), на скошенной кромке-клине расходятся —
    спектральная кайма у бликов и краёв, как у эталона. Тонкая плёнка — слабая (film_ior), кромка — клин (наклон нормали
    лица и оболочки к краю), свечение кромок, растворение концов — как в mat_ribbon6."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["UV"], sep.inputs["Vector"])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.5, 0.4, 1.0)
    L.new(tc.outputs["UV"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 1.5
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    ph = _m(nt, "MULTIPLY_ADD", nz.outputs["Fac"], P["film_noise"], -0.5 * P["film_noise"])
    arg = _m(nt, "MULTIPLY_ADD", u, 2 * math.pi * P["film_waves"], ph)
    t1 = _m(nt, "MULTIPLY_ADD", _m(nt, "SINE", arg), P["film_amp"], P["film_mid"])
    sv = _m(nt, "MULTIPLY_ADD", v, 2.0, -1.0)
    ev = _m(nt, "ABSOLUTE", sv)
    thick = _m(nt, "MULTIPLY_ADD", _m(nt, "POWER", ev, 3.0), P["film_edge"], t1)
    nrm = None
    if P["rib_edge"] > 0 and P["rib_edge_tilt"] > 0:
        tg = nt.nodes.new("ShaderNodeTangent")
        tg.direction_type = "UV_MAP"
        tg.uv_map = "UVMap"
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        B = _v(nt, "NORMALIZE", _v(nt, "CROSS_PRODUCT", geo.outputs["Normal"], tg.outputs["Tangent"]))
        k = _smooth(nt, ev, 1.0 - 2.0 * P["rib_edge"], 1.0)
        k = _m(nt, "MULTIPLY", _m(nt, "MULTIPLY", k, _m(nt, "SIGN", sv)), side * math.tan(math.radians(P["rib_edge_tilt"])))
        sc_ = nt.nodes.new("ShaderNodeVectorMath")
        sc_.operation = "SCALE"
        L.new(B, sc_.inputs[0])
        L.new(k, bpyx.sock(sc_, "Scale"))
        nrm = _v(nt, "NORMALIZE", _v(nt, "ADD", geo.outputs["Normal"], sc_.outputs["Vector"]))
    shader = None
    for col, dn in (((1.0, 0.0, 0.0, 1.0), -1.0), ((0.0, 1.0, 0.0, 1.0), 0.0), ((0.0, 0.0, 1.0, 1.0), 1.0)):
        g = nt.nodes.new("ShaderNodeBsdfGlass")
        g.distribution = "GGX"
        g.inputs["Color"].default_value = col
        g.inputs["Roughness"].default_value = P["rib_rough"]
        g.inputs["IOR"].default_value = P["rib_ior"] + dn * P["rib_disp"]
        g.inputs["Thin Film IOR"].default_value = P["film_ior"]
        L.new(thick, g.inputs["Thin Film Thickness"])
        if nrm is not None:
            L.new(nrm, g.inputs["Normal"])
        if shader is None:
            shader = g.outputs[0]
        else:
            ad = nt.nodes.new("ShaderNodeAddShader")
            L.new(shader, ad.inputs[0])
            L.new(g.outputs[0], ad.inputs[1])
            shader = ad.outputs[0]
    if P["rib_edge_glow"] > 0:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*kelvin_rgb(6200), 1.0)
        L.new(_m(nt, "MULTIPLY", _smooth(nt, ev, 1.0 - 2.0 * P["rib_edge_glow_w"], 1.0), P["rib_edge_glow"]), em.inputs["Strength"])
        ad = nt.nodes.new("ShaderNodeAddShader")
        L.new(shader, ad.inputs[0])
        L.new(em.outputs[0], ad.inputs[1])
        shader = ad.outputs[0]
        mat.cycles.emission_sampling = "NONE"
    out = bpyx.find_node(nt, "OUTPUT_MATERIAL")
    if P["rib_fade"] > 0:
        fu = _smooth(nt, _m(nt, "MINIMUM", u, _m(nt, "SUBTRACT", 1.0, u)), 0.0, P["rib_fade"])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mx = nt.nodes.new("ShaderNodeMixShader")
        L.new(fu, mx.inputs[0])
        L.new(tr.outputs[0], mx.inputs[1])
        L.new(shader, mx.inputs[2])
        shader = mx.outputs[0]
    L.new(shader, out.inputs["Surface"])
    return mat


def mat_ribbon_rim():
    """Торец плёнки (1,1 мм): то же стекло без тонкой плёнки + слабое свечение rib_rim_glow (световод литой плёнки)."""
    mat, p = bpyx.principled("VD_RibbonRim", base_color=(1, 1, 1, 1), roughness=0.05, ior=1.50, transmission_weight=1.0,
                             emission_color=(1.0, 0.97, 0.92, 1.0), emission_strength=P["rib_rim_glow"])
    return mat


def mat_granite(name="VD_Granite"):
    """Полированный тёмный гранит с искрой: зерно (Voronoi, ≈ 1,7 мм) по классам минералов (чёрный / тёмно-серый /
    серый / светлый), пятнистость крупным шумом (скопления светлых зёрен), чешуйки слюды (доля gr_flake, металл,
    своя шероховатость и случайный наклон нормали — искра при повороте) — всё под лаком-полировкой (Coat, 0,035):
    отражение флакона остаётся резким, фактура видна под ним. ≈ 19 нод."""
    mat, p = bpyx.principled(name, base_color="#101112", roughness=P["gr_rough"], ior=1.55, coat_weight=1.0,
                             coat_roughness=P["gr_coat_rough"], coat_ior=1.50)
    nt, L = nt_links(mat)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0.3, 0.2, 0.6)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nm = nt.nodes.new("ShaderNodeTexNoise")
    nm.inputs["Scale"].default_value = P["gr_mottle"]
    nm.inputs["Detail"].default_value = 5.0
    nm.inputs["Roughness"].default_value = 0.65
    nm.inputs["Distortion"].default_value = 0.8
    L.new(mp.outputs["Vector"], nm.inputs["Vector"])
    nd = nt.nodes.new("ShaderNodeTexNoise")                       # искажение ячеек: зёрна неправильной формы
    nd.inputs["Scale"].default_value = P["gr_grain"] * 0.35
    nd.inputs["Detail"].default_value = 2.0
    vd = _v(nt, "MULTIPLY_ADD", nd.outputs["Color"], (P["gr_warp"],) * 3, mp.outputs["Vector"])
    L.new(mp.outputs["Vector"], nd.inputs["Vector"])
    vg = nt.nodes.new("ShaderNodeTexVoronoi")
    vg.inputs["Scale"].default_value = P["gr_grain"]
    L.new(vd, vg.inputs["Vector"])
    sg = nt.nodes.new("ShaderNodeSeparateColor")
    L.new(vg.outputs["Color"], sg.inputs["Color"])
    # класс зерна = 0,6·случайное + облака (шум, растянутый ×2,5 вокруг 0,5): в «облаках» больше светлых зёрен
    cls = _m(nt, "MULTIPLY_ADD", sg.outputs[0], 0.6,
             _m(nt, "MULTIPLY_ADD", nm.outputs["Fac"], 2.5 * P["gr_mottle_amp"], -1.25 * P["gr_mottle_amp"] + 0.25))
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.interpolation = "CONSTANT"
    els = cr.color_ramp.elements
    els[0].position, els[0].color = 0.0, bpyx.color(P["gr_c0"])
    els[1].position, els[1].color = 0.55, bpyx.color(P["gr_c1"])
    e = els.new(0.80); e.color = bpyx.color(P["gr_c2"])
    e = els.new(0.93); e.color = bpyx.color(P["gr_c3"])
    L.new(cls, cr.inputs["Fac"])
    vf = nt.nodes.new("ShaderNodeTexVoronoi")
    vf.inputs["Scale"].default_value = P["gr_flake_scale"]
    L.new(mp.outputs["Vector"], vf.inputs["Vector"])
    sf = nt.nodes.new("ShaderNodeSeparateColor")
    L.new(vf.outputs["Color"], sf.inputs["Color"])
    fm = _m(nt, "GREATER_THAN", sf.outputs[1], 1.0 - P["gr_flake"])
    S_ = bpyx.sock
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MIX"
    L.new(fm, S_(mx, "Factor"))
    L.new(cr.outputs["Color"], S_(mx, "A"))
    S_(mx, "B").default_value = bpyx.color(P["gr_flake_col"])
    L.new(S_(mx, "Result", out=True), p.inputs["Base Color"])
    L.new(fm, p.inputs["Metallic"])
    L.new(_m(nt, "MULTIPLY_ADD", fm, P["gr_flake_rough"] - P["gr_rough"], P["gr_rough"]), p.inputs["Roughness"])
    j = P["gr_jitter"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    jit = _v(nt, "MULTIPLY_ADD", vf.outputs["Color"], (2 * j,) * 3, (-j,) * 3)
    L.new(_v(nt, "NORMALIZE", _v(nt, "ADD", jit, geo.outputs["Normal"])), p.inputs["Normal"])   # Coat Normal — ровная
    return mat


def mat_soft(name, E, col=(1.0, 1.0, 1.0), feather=0.4):
    """Мягкий отражатель: яркость E·w(u)·w(v), w = smoothstep от края плоскости на долю feather полуширины;
    «прозрачный + эмиссия» — для предметов вне light linking он прозрачен (а не чёрен, как непрозрачный излучатель)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])   # 0…1 по рамке плоскости (UV у create_grid без слоя нет)
    w = None
    for ax in ("X", "Y"):
        t = sep.outputs[ax]
        edge = _m(nt, "MINIMUM", t, _m(nt, "SUBTRACT", 1.0, t))
        wa = _smooth(nt, edge, 0.0, max(0.5 * feather, 1e-3))
        w = wa if w is None else _m(nt, "MULTIPLY", w, wa)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1.0)
    nt.links.new(_m(nt, "MULTIPLY", w, float(E)), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], bpyx.find_node(nt, "OUTPUT_MATERIAL").inputs["Surface"])
    return m


def mat_lobes(name, lobes, base, el0=5.0, el1=30.0, base_col=(1.0, 1.0, 1.0)):
    """Купол-«студия» ленты без провалов: база base·smoothstep(sin el0, sin el1, z) + доли — мягкие пятна яркости по
    направлениям: amp·exp((d·c − 1)/σ²) (≈ гаусс по углу, σ — угловой радиус), каждая своего цвета (кельвины).
    d — направление от центра купола. «Прозрачный + эмиссия» (для предметов вне light linking купол прозрачен)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    d = _v(nt, "NORMALIZE", tc.outputs["Object"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(d, sep.inputs["Vector"])
    shader = nt.nodes.new("ShaderNodeBsdfTransparent").outputs[0]
    terms = []
    if base > 0:
        w = _smooth(nt, sep.outputs["Z"], math.sin(math.radians(el0)), math.sin(math.radians(el1)))
        terms.append((_m(nt, "MULTIPLY", w, float(base)), base_col))
    for az, el, sig, amp, kel in lobes:
        a, e = math.radians(az), math.radians(el)
        c = (math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))
        s2 = math.radians(sig) ** 2
        dot = _v(nt, "DOT_PRODUCT", d, c)
        w = _m(nt, "EXPONENT", _m(nt, "MULTIPLY_ADD", dot, 1.0 / s2, -1.0 / s2))
        terms.append((_m(nt, "MULTIPLY", w, float(amp)), kelvin_rgb(kel)))
    for az, el, roll, ln, sig, amp, kel in P.get("env_strips", []):
        # полоса-«стрип-бокс»: центр c (азимут/угол места), длинная ось a (roll от горизонтали, °), длина ln°, ширина σ°:
        # w = exp(−(d·n)²/sin²σ) · окно по |d·a| ≤ sin(ln/2) · [d·c > 0]; её отражение в закрученной ленте — штрих вдоль складки
        a_, e_ = math.radians(az), math.radians(el)
        c = Vector((math.sin(a_) * math.cos(e_), -math.cos(a_) * math.cos(e_), math.sin(e_)))
        h = Vector((0.0, 0.0, 1.0)).cross(c).normalized()
        vt = c.cross(h).normalized()
        ax = (h * math.cos(math.radians(roll)) + vt * math.sin(math.radians(roll))).normalized()
        nn = c.cross(ax).normalized()
        s_ = math.sin(math.radians(sig))
        across = _v(nt, "DOT_PRODUCT", d, tuple(nn))
        w = _m(nt, "EXPONENT", _m(nt, "MULTIPLY", _m(nt, "MULTIPLY", across, across), -1.0 / (s_ * s_)))
        half = math.sin(math.radians(ln / 2))
        along = _m(nt, "ABSOLUTE", _v(nt, "DOT_PRODUCT", d, tuple(ax)))
        win = _smooth(nt, _m(nt, "SUBTRACT", half, along), 0.0, 0.3 * half)
        front = _m(nt, "GREATER_THAN", _v(nt, "DOT_PRODUCT", d, tuple(c)), 0.0)
        w = _m(nt, "MULTIPLY", _m(nt, "MULTIPLY", w, win), front)
        terms.append((_m(nt, "MULTIPLY", w, float(amp)), kelvin_rgb(kel)))
    for strength, col in terms:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*col, 1.0)
        nt.links.new(strength, em.inputs["Strength"])
        ad = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(shader, ad.inputs[0])
        nt.links.new(em.outputs[0], ad.inputs[1])
        shader = ad.outputs[0]
    nt.links.new(shader, bpyx.find_node(nt, "OUTPUT_MATERIAL").inputs["Surface"])
    return m


def mat_sky(name, E, el0=8.0, el1=40.0, col=(1.0, 1.0, 1.0)):
    """Тусклое «небо» для ленты: E·smoothstep(sin el0, sin el1, z) по направлению от центра купола (выше — светлее)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nrm = _v(nt, "NORMALIZE", tc.outputs["Object"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nrm, sep.inputs["Vector"])
    w = _smooth(nt, sep.outputs["Z"], math.sin(math.radians(el0)), math.sin(math.radians(el1)))
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1.0)
    nt.links.new(_m(nt, "MULTIPLY", w, float(E)), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], ad.inputs[0])
    nt.links.new(em.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], bpyx.find_node(nt, "OUTPUT_MATERIAL").inputs["Surface"])
    return m


# ====================================================================== детали

def bottle_profiles(P):
    R, H, rb, rs = P["R"], P["H"], P["r_bottom"], P["r_shoulder"]
    nr, nh, br, t, tb = P["neck_r"], P["neck_h"], P["bore_r"], P["wall"], P["base"]
    # наружный профиль снизу вверх: дно → скругление → стенка → плечо → кольцо → шейка → губа
    outer = [(0.0, 0.0), (R - rb - 0.004, 0.0)]
    outer += arc_pts((R - rb, rb), rb, -math.pi / 2, 0.0, 10)
    wall_pts = [(R, rb + (H - rs - rb) * i / 24) for i in range(1, 24)]
    outer += wall_pts
    outer += arc_pts((R - rs, H - rs), rs, 0.0, math.pi / 2, 16)
    ring_in = nr + 0.0016
    outer += [(R - rs - (R - rs - ring_in) * i / 6, H) for i in range(1, 7)]
    outer += arc_pts((ring_in, H + 0.0016), 0.0016, -math.pi / 2, -math.pi, 6)
    outer += [(nr, H + 0.0016 + (nh - 0.0026) * i / 3) for i in range(1, 4)]
    outer += arc_pts(((nr + br) / 2, H + nh - 0.0010), (nr - br) / 2, 0.0, math.pi, 6)
    # внутренний профиль сверху вниз: канал шейки → внутреннее плечо → стенка → дно полости
    inner = [(br, H + nh - 0.0010 - 0.004 * i / 3) for i in range(1, 4)]
    zi_top = H - t * 1.2
    ri = R - t
    rsi = rs - t * 0.8
    inner += [(br + (ri - rsi - br) * i / 5, zi_top) for i in range(1, 6)]
    inner += arc_pts((ri - rsi, zi_top - rsi), rsi, math.pi / 2, 0.0, 12)
    rbi = rb * 0.9
    inner += [(ri, zi_top - rsi - (zi_top - rsi - tb - rbi) * i / 20) for i in range(1, 21)]
    inner += arc_pts((ri - rbi, tb + rbi), rbi, 0.0, -math.pi / 2, 8)
    inner += [(ri - rbi - (ri - rbi) * i / 4, tb) for i in range(1, 5)]
    return dedup(outer), dedup(inner)


def make_bottle(P, coll):
    outer, inner = bottle_profiles(P)
    R, rs = P["R"], P["r_shoulder"]
    depth = P["flute_depth"]
    # вес рифления по профилю: полный на стенке, скруглениях дна и плеча; на кольце плеча сходит к шейке; на дне — 0
    ring_in = P["neck_r"] + 0.0016

    def weight(r, z):
        if z <= 1e-6:
            return 0.0
        if z < P["H"] - 1e-6:
            return depth
        if r <= ring_in:
            return 0.0
        return depth * min(1.0, ((r - ring_in) / (R - rs - ring_in))) ** 1.5

    prof = [(r, z, weight(r, z)) for r, z in outer] + [(r, z, 0.0) for r, z in inner]
    N = P["flutes"]

    def disp(th):   # 0 на гребне, 1 в канавке; гребень скруглён, канавка острая
        return 1.0 - math.sqrt(abs(math.sin(N * th / 2.0)))
    bm = lathe_bm(prof, N * P["flute_seg"], disp)
    ob = obj_from_bm(bm, "Bottle_Glass", coll)
    ob.data.set_sharp_from_angle(angle=math.radians(24))       # острые канавки рифления (гребни остаются гладкими)
    bpyx.assign_material(ob, mat_glass())
    return ob, inner


def make_liquid(P, inner, coll):
    """Крем: полость минус зазор, до уровня fill_top (скрыт под плечом и крышкой). Зазор: у дна — вверх и внутрь,
    на стенке и плече — только внутрь по радиусу (сдвиг вверх у плеча врезал бы крем в стекло)."""
    g = P["fill_gap"]
    z_bot = P["base"] + P["r_bottom"] * 0.9 + 1e-6
    pts = [(r, z) for r, z in reversed(inner)]            # снизу (ось) вверх
    shr = []
    for r, z in pts:
        if z > P["fill_top"]:
            continue
        shr.append((max(r - g, 0.0), z + g if z < z_bot else z))
    top_r = shr[-1][0]
    prof = [(0.0, shr[0][1])] + shr[1:] + [(top_r * 0.5, P["fill_top"]), (0.0, P["fill_top"])]
    bm = lathe_bm([(r, z, 0.0) for r, z in dedup(prof)], 256)
    ob = obj_from_bm(bm, "Bottle_Cream", coll)
    bpyx.assign_material(ob, mat_liquid())
    return ob


def make_cap(P, coll):
    r, h, z0 = P["cap_r"], P["cap_h"], P["H"] + P["cap_gap"]
    prof = [(0.0, z0), (r - 0.0008, z0)] + arc_pts((r - 0.0008, z0 + 0.0008), 0.0008, -math.pi / 2, 0.0, 4)
    prof += [(r, z0 + 0.0008 + (h - 0.0023) * i / 8) for i in range(1, 9)]
    prof += arc_pts((r - 0.0015, z0 + h - 0.0015), 0.0015, 0.0, math.pi / 2, 8) + [(0.0, z0 + h)]
    bm = lathe_bm([(a, b, 0.0) for a, b in dedup(prof)], 192)
    ob = obj_from_bm(bm, "Bottle_Cap", coll)
    bpyx.assign_material(ob, mat_gold())
    return ob


def make_label(P, coll):
    """Бумажная полоса по цилиндру гребней (+0,25 мм): дуга label_arc вокруг фронта (−Y), с толщиной 0,15 мм."""
    R = P["R"] + P["label_lift"]
    ang = P["label_arc"] / R
    nu, nv = 160, 6
    z0 = P["label_z"] - P["label_h"] / 2
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            th = -math.pi / 2 - ang / 2 + ang * i / nu            # слева направо, если смотреть с −Y
            row.append(bm.verts.new((R * math.cos(th), R * math.sin(th), z0 + P["label_h"] * j / nv)))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop, uv in zip(f.loops, ((i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv))):
                loop[uvl].uv = uv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:                                    # нормали наружу (от оси)
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, c.y, 0))) < 0:
            f.normal_flip()
    ob = obj_from_bm(bm, "Bottle_Label", coll)
    m = ob.modifiers.new("Solidify", "SOLIDIFY"); m.thickness = P["label_t"]; m.offset = -1.0
    bpyx.assign_material(ob, mat_label())
    return ob


def make_block(P, coll):
    W, D_, Hh = P["block"]
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(W, D_, Hh), verts=bm.verts[:])
    bmesh.ops.translate(bm, vec=(0, 0, -Hh / 2), verts=bm.verts[:])
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=P["block_bevel"], segments=3, profile=0.5, affect="EDGES",
                    clamp_overlap=True, harden_normals=False)
    ob = obj_from_bm(bm, "Plinth_Marble", coll, smooth=True)
    ob.data.set_sharp_from_angle(angle=math.radians(35))
    a = math.radians(P["block_rot"])
    u, v = P["bottle_uv"]
    # центр блока так, чтобы флакон (начало координат) был в точке (u, v) системы блока
    # верх постамента на 0,1 мм выше дна флакона: врастание вместо совпадающих плоскостей (артефакты трассировки)
    ob.location = Vector((-(u * math.cos(a) - v * math.sin(a)), -(u * math.sin(a) + v * math.cos(a)), 0.0001))
    ob.rotation_euler = (0, 0, a)
    bpyx.assign_material(ob, mat_granite() if P.get("stone") == "granite" else mat_marble())
    return ob


def ribbon_bmesh(P, phase=None):
    """Сетка ленты: путь Catmull-Rom → рамки параллельного переноса (d1lib._frames) + закрут (фаза phase, рад; None —
    P["ribbon_phase"]). Ширина: v5 — sin^0,6 (концы сходят на нет), v6 (rib_env) — почти постоянная, у концов rib_end_w
    ширины (концы растворяет материал). UV: u вдоль, v поперёк. Возвращает (bmesh, длина пути)."""
    sys.path.insert(0, "/home/mm/Документы/app-design/blender-research/99-raw/experiments/D1/_lib")
    import d1lib as D
    path = D.catmull_rom_pts(P["ribbon_ctrl"], 260)
    Pp, T, N, _ = D._frames(path, False)
    n = len(Pp)
    Ls = [0.0]
    for i in range(1, n):
        Ls.append(Ls[-1] + (Pp[i] - Pp[i - 1]).length)
    cols = 24
    ph0 = P["ribbon_phase"] if phase is None else phase
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    grid = []
    for i in range(n):
        t = Ls[i] / Ls[-1]
        Ni = Matrix.Rotation(ph0 + P["ribbon_twist"] * t, 3, T[i]) @ N[i]
        if P.get("rib_env"):
            e = min(t, 1.0 - t) / 0.15
            s = P["rib_end_w"] + (1.0 - P["rib_end_w"]) * (e * e * (3 - 2 * e) if e < 1 else 1.0)
        else:
            s = math.sin(math.pi * t) ** 0.6 if 0 < t < 1 else 0.0
        half = P["ribbon_w"] / 2 * max(s, 0.02)
        grid.append([bm.verts.new(Pp[i] + Ni * (-half + 2 * half * j / cols)) for j in range(cols + 1)])
    for i in range(n - 1):
        for j in range(cols):
            f = bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
            f.smooth = True
            u0, u1 = Ls[i] / Ls[-1], Ls[i + 1] / Ls[-1]
            for loop, uv in zip(f.loops, ((u0, j / cols), (u0, (j + 1) / cols), (u1, (j + 1) / cols), (u1, j / cols))):
                loop[uvl].uv = uv
    return bm, Ls[-1]


def make_ribbon(P, coll):
    """Лента-лист (однослойная сетка + Solidify 1,1 мм). v6: три материала — лицо, оболочка (наклон кромки в ту же
    сторону мира), торец."""
    bm, length = ribbon_bmesh(P)
    ob = obj_from_bm(bm, "Ribbon_Film", coll)
    sm = ob.modifiers.new("Solidify", "SOLIDIFY"); sm.thickness = P["ribbon_t"]; sm.offset = 0.0
    sm.use_even_offset = True
    if P.get("rib_env"):
        sm.material_offset = 1
        sm.material_offset_rim = 2
        mk = mat_ribbon7 if P.get("rib_shader") == "disp" else mat_ribbon6
        bpyx.assign_material(ob, mk("VD_RibbonFilm6", +1.0))
        bpyx.assign_material(ob, mk("VD_RibbonFilm6B", -1.0), slot=1)
        bpyx.assign_material(ob, mat_ribbon_rim(), slot=2)
    else:
        bpyx.assign_material(ob, mat_ribbon())
    if P.get("rib_debug_mirror"):          # отладка: лента — зеркало (видно, что она отражает)
        mm_, _ = bpyx.principled("DBG_RibMirror", base_color=(1, 1, 1, 1), metallic=1.0, roughness=0.0)
        for i_ in range(len(ob.data.materials)):
            ob.data.materials[i_] = mm_
    ob["length_m"] = round(length, 4)
    return ob


def update_ribbon(ob, P, phase):
    """Вторичное движение: пересобрать сетку ленты с другой фазой закрута на месте (объект, модификатор, материалы и
    light linking остаются)."""
    bm, _ = ribbon_bmesh(P, phase)
    bm.normal_update()
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def build(P):
    d = bpy.data.collections.get("ASSET_velmora")
    if d is not None:
        for ob in list(d.all_objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(d)
    C = bpyx.ensure_collection("ASSET_velmora")
    root = bpy.data.objects.new("Turntable", None); C.objects.link(root)
    glass, inner = make_bottle(P, C)
    parts = [glass, make_liquid(P, inner, C), make_cap(P, C), make_label(P, C), make_block(P, C), make_ribbon(P, C)]
    for o in parts:
        o.parent = root
    C["passport"] = json.dumps({k: v for k, v in P.items() if not callable(v)}, ensure_ascii=False, default=str)
    return C, root, parts


# ====================================================================== студия, свет, камера

def stage(P):
    d = bpy.data.collections.get("STAGE")
    if d is not None:
        for ob in list(d.all_objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(d)
    S = bpyx.ensure_collection("STAGE")
    fz, wy, cr = P["floor_z"], P["wall_y"], P["cyc_r"]
    prof = [(-2.2, fz), (wy - cr, fz)]
    prof += [(wy - cr + cr * math.sin(math.pi / 2 * i / 12), fz + cr * (1 - math.cos(math.pi / 2 * i / 12))) for i in range(1, 13)]
    prof += [(wy, fz + cr + 2.2 * i / 20) for i in range(1, 21)]
    bm = bmesh.new()
    nx = 160
    rows = []
    for (y, z) in prof:
        row = []
        for i in range(nx + 1):
            x = -2.0 + 4.0 * i / nx
            k = max(0.0, min(1.0, (z - (fz + cr + 0.01)) / 0.08))           # складки только на стене (видимая полоса)
            fold = 0.030 * k * (math.sin(2 * math.pi * x / 0.13 + 1.7 * math.sin(x * 7.1)) + 0.35 * math.sin(2 * math.pi * x / 0.047))
            row.append(bm.verts.new((x, y + fold, z)))
        rows.append(row)
    for j in range(len(rows) - 1):
        for i in range(nx):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    cyc = obj_from_bm(bm, "Cyclorama", S)
    for f in cyc.data.polygons:                       # нормали к сцене (к −Y и вверх)
        pass
    bpyx.assign_material(cyc, mat_backdrop())
    # пол перед циклорамой — тёмный камень с мягким отражением (переотражение на постаменте, низ кадра слева)
    fl = bpyx.primitive("plane", "Floor_Stone", size=1.0, location=(0, -0.3, fz + 0.0005), collection=S)
    fl.scale = (4.0, 2.4, 1.0)
    bpyx.assign_material(fl, mat_marble("VD_FloorStone", base_hex="#080808", vein_hex="#2A2927", rough=0.22, scale=1.3,
                                        vein_w=0.012, ripple=0.0))
    return S


def world(strength_hdri=0.06, rot_deg=110.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.get("VD_World") or bpy.data.worlds.new("VD_World")
    sc.world = w
    nt = w.node_tree
    for n in list(nt.nodes):
        if n.type not in ("BACKGROUND", "OUTPUT_WORLD"):
            nt.nodes.remove(n)
    bg = bpyx.find_node(nt, "BACKGROUND")
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(rot_deg)
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load("/home/mm/.local/opt/blender-5.2.2-linux-x64/5.2/datafiles/studiolights/world/studio.exr",
                                     check_existing=True)
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 0.0   # серые отражения
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], hs.inputs["Color"]); nt.links.new(hs.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength_hdri
    return w


def kelvin_rgb(k):
    """Приближение цвета АЧТ (Tanner Helland), линейный RGB с нормировкой по максимуму."""
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    srgb = [max(0, min(255, c)) / 255 for c in (r, g, b)]
    lin = [bpyx.srgb_to_linear(c) for c in srgb]
    m = max(lin)
    return tuple(c / m for c in lin)


def area(S, name, az, el, d, sx, sy, power, col=(1, 1, 1), target=(0, 0, 0.063), shape="RECTANGLE", spread=None):
    a, e = math.radians(az), math.radians(el)
    c = Vector(target)
    loc = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = shape; ld.size = sx; ld.size_y = sy; ld.energy = power; ld.color = col
    if spread is not None:
        ld.spread = math.radians(spread)
    lo = bpy.data.objects.new(name, ld); S.objects.link(lo); lo.location = loc
    lo.rotation_euler = (c - loc).to_track_quat("-Z", "Y").to_euler()
    return lo


def soft_panel(S, name, az, el, d, sx, sy, E, col=(1, 1, 1), feather=0.5, target=(0, 0, 0.063), roll=0.0, receivers=None):
    """Отражатель ленты: плоскость sx × sy (м) с растушёванным краем (mat_soft) на азимуте az / угле места el (как
    area(): 0° — к камере, + вправо), на расстоянии d от цели, лицом к цели; roll — поворот вокруг своей оси (°).
    Камере и теням не виден; светит только коллекцию receivers (light linking); для остальных прозрачен."""
    a, e = math.radians(az), math.radians(el)
    c = Vector(target)
    loc = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True)
    ob = obj_from_bm(bm, name, S, smooth=False)
    ob.scale = (sx, sy, 1.0)
    ob.location = loc
    q = (c - loc).to_track_quat("Z", "Y") @ Quaternion((0.0, 0.0, 1.0), math.radians(roll))
    ob.rotation_euler = q.to_euler()
    bpyx.assign_material(ob, mat_soft("VD_" + name, E, col, feather))
    ob.visible_camera = False
    ob.visible_shadow = False
    if receivers is not None:
        ob.light_linking.receiver_collection = receivers
    return ob


def ribbon_env(S, P, only_rib):
    """v6: «студия» ленты — большие мягкие отражатели по карте направлений (06-look/dir: в ракурсах дуэли лента
    отражает верх-перед-право: азимут +15…+105°, угол места +15…+75°; в 360° — ещё верх-перед-лево и бока) и тусклое
    небо выше 8°. Позади сцены (куда уходят лучи сквозь ленту) — ничего: плёнка не «заливается» на просвет."""
    if P.get("env_mode") == "dome":        # v6b: один купол с мягкими долями — непрерывный перелив без провалов
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=2.0)
        dome = obj_from_bm(bm, "Env_Dome", S)
        dome.location = (0.0, 0.0, 0.063)
        bpyx.assign_material(dome, mat_lobes("VD_Env_Dome", P["env_lobes"], P["env_base"], 5.0, 30.0, kelvin_rgb(6500)))
        dome.data.materials[0].cycles.emission_sampling = "NONE"   # ленту (шероховатость 0,06) находят лучи BSDF
        dome.visible_camera = False
        dome.visible_shadow = False
        dome.light_linking.receiver_collection = only_rib
        print("VD_RIBBON_ENV dome", P["env_base"], P["env_lobes"])
        return [dome]
    k56, k60, k65, k52 = kelvin_rgb(5600), kelvin_rgb(6000), kelvin_rgb(6500), kelvin_rgb(5200)
    out = [
        soft_panel(S, "Env_Main", 60, 45, 1.20, 1.10, 0.90, P["env_main"], k56, 0.6, receivers=only_rib),
        soft_panel(S, "Env_Top", 20, 68, 1.00, 1.40, 0.22, P["env_top"], k65, 0.7, receivers=only_rib),
        soft_panel(S, "Env_Front", -10, 22, 1.50, 1.20, 0.50, P["env_front"], k60, 0.8, receivers=only_rib),
        soft_panel(S, "Env_Left", -75, 45, 1.20, 0.90, 0.90, P["env_left"], k65, 0.6, receivers=only_rib),
        soft_panel(S, "Env_Right", 100, 20, 1.10, 0.30, 1.00, 0.8 * P["env_main"], k52, 0.7, receivers=only_rib),
    ]
    if P["env_sky"] > 0:
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=2.0)
        sky = obj_from_bm(bm, "Env_Sky", S)
        sky.location = (0.0, 0.0, 0.063)
        bpyx.assign_material(sky, mat_sky("VD_Env_Sky", P["env_sky"], 8.0, 40.0, k65))
        sky.visible_camera = False
        sky.visible_shadow = False
        sky.light_linking.receiver_collection = only_rib
        out.append(sky)
    print("VD_RIBBON_ENV", [(o.name, [round(x, 3) for x in o.location]) for o in out])
    return out


def compositor(strength, size=0.5, threshold=None):
    """«Воздух» в композиторе 5.x: Glare Fog Glow по сцене-линейным бликам (до вида Neutral); strength ≤ 0 — выкл."""
    sc = bpy.context.scene
    if strength <= 0:
        sc.render.use_compositing = False
        return None
    tree = bpy.data.node_groups.get("VD_Comp") or bpy.data.node_groups.new("VD_Comp", "CompositorNodeTree")
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    if not any(s.name == "Image" for s in tree.interface.items_tree if getattr(s, "in_out", None) == "OUTPUT"):
        tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = tree.nodes.new("CompositorNodeRLayers")
    g = tree.nodes.new("CompositorNodeGlare")
    for key, val in (("Type", "Fog Glow"), ("Quality", "High")):
        try:
            g.inputs[key].default_value = val
        except TypeError as e_:
            print("VD_GLARE", key, e_)
    threshold = P.get("glare_thr", 1.0) if threshold is None else threshold
    g.inputs["Highlights Threshold"].default_value = threshold
    g.inputs["Strength"].default_value = strength
    g.inputs["Size"].default_value = size
    out = tree.nodes.new("NodeGroupOutput")
    tree.links.new(rl.outputs["Image"], g.inputs["Image"])
    tree.links.new(g.outputs["Image"], out.inputs["Image"])
    sc.compositing_node_group = tree
    sc.render.use_compositing = True
    print("VD_GLARE", g.inputs["Type"].default_value, strength, size, threshold)
    return tree


def lights(scheme, P, caustics=False):
    d = bpy.data.collections.get("LIGHTS")
    if d is not None:
        for ob in list(d.all_objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(d)
    S = bpyx.ensure_collection("LIGHTS")
    warm, warm2, cool = kelvin_rgb(4300), kelvin_rgb(5200), kelvin_rgb(6800)     # v2: теплее 3900/4700 — бурый мрамор и фон
    L = []
    if scheme in ("S1", "S3", "S4"):
        # S1 «как у нейросети»: тёплый ключ сверху-справа-сзади (контур и блеск мрамора), мягкий фронт слева (этикетка,
        # полоса на крышке), холодная полоса-контровой слева (светлая линия кромки стекла), свет фона.
        L.append(area(S, "Key_BackRight", 138, 34, 0.52, 0.375, 0.69, 3.6, warm))   # v4: без spread 70° — узкий конус ×3 яркости блика (пересвет R)
        L.append(area(S, "Fill_FrontLeft", -48, 20, 0.78, 0.90, 0.80, 6.5, warm2))       # крупнее: та же освещённость, блик втрое тусклее
        L.append(area(S, "Cap_Card", -48, 20, 0.78, 0.80, 0.80, 1.4, warm2))            # полоса на крышке (только крышка)
        L.append(area(S, "Rim_Left", -128, 12, 0.46, 0.035, 0.55, 1.6, cool))
        L.append(area(S, "Top_Soft", 25, 72, 0.55, 0.50, 0.35, 0.5, warm2))                 # v3: кант крышки без пересвета
        L.append(area(S, "Rib_Strip", -32, 8, 0.62, 0.05, 0.50, 1.4, warm2))            # линии на гранях слева
        if not P.get("rib_env"):     # v5: лампы ленты (пятна-отражения прямоугольников и эллипсов)
            L.append(area(S, "Film_Strip", 118, 40, 0.55, 0.08, 0.40, 4.0, (1, 1, 1), shape="ELLIPSE"))      # только лента (light linking)
            L.append(area(S, "Film_Box", 140, 30, 0.60, 0.50, 0.60, 1.2, (1, 1, 1), shape="ELLIPSE"))
            # «просвет» для ленты: панель за ней, камере не видна, светит только ленту — видна сквозь плёнку (light linking)
            if P["film_back_w"] > 0:   # «просвет» сквозь ленту: 0,35 Вт превратил плёнку в белый атлас (v2ph*) — выключен
                L.append(area(S, "Film_Back", 180, 2, 0.42, 0.62, 0.30, P["film_back_w"], kelvin_rgb(5600), target=(0.0, 0.0, 0.10), shape="ELLIPSE"))        # ровный перелив по ленте
        L.append(area(S, "Sheen_Back", 182, 8.3, 0.75, 1.20, 0.28, P["sheen_w"], kelvin_rgb(6000), target=(0, 0, 0.0)))  # блеск столешницы (перед стеной!)
        if not P.get("rib_env"):
            L.append(area(S, "Film_Dome", 160, 62, 1.10, 2.0, 2.0, P["dome_w"], (1, 1, 1), shape="ELLIPSE"))         # «небо» для ленты: форма читается целиком
            L.append(area(S, "Film_Left", -150, 35, 0.60, 0.35, 0.45, 0.6, (1, 1, 1), shape="ELLIPSE"))      # левый верх ленты
            L.append(area(S, "Film_Top", 170, 70, 0.55, 0.06, 0.60, 1.6, (1, 1, 1), shape="ELLIPSE"))        # штрих-блики вдоль закрута
            L.append(area(S, "Film_Front", -20, 35, 0.70, 0.30, 0.30, 0.8, (1, 1, 1), shape="DISK"))      # лицевые участки ленты
        glow = bpy.data.lights.new("Glow_Backdrop", "SPOT")
        glow.energy = P["glow_w"]; glow.color = kelvin_rgb(P.get("glow2_k", 6000) if P.get("glow2") else 6000)
        glow.spot_size = math.radians(40); glow.spot_blend = 1.0
        glow.shadow_soft_size = 0.35
        go = bpy.data.objects.new("Glow_Backdrop", glow); S.objects.link(go)
        go.location = (0.30, P["wall_y"] - 0.26, 0.95)                # сверху вдоль стены: складки дают вертикальные полосы
        go.rotation_euler = (Vector((0.13, P["wall_y"] + 0.02, 0.02)) - go.location).to_track_quat("-Z", "Y").to_euler()
        if P.get("glow2"):           # v6: скользящий свет справа вдоль стены — складки рисуют вертикальные полосы за лентой
            glow.energy = P["glow2_w"]; glow.spot_size = math.radians(P["glow2_size"]); glow.shadow_soft_size = 0.30
            go.location = Vector(P["glow2_pos"])
            go.rotation_euler = (Vector(P["glow2_aim"]) - go.location).to_track_quat("-Z", "Y").to_euler()
        L.append(go)
    elif scheme == "S2":
        # S2 «канон стекла базы»: две белые вертикальные полосы сзади-сбоку ±135°, софтбокс сверху, фронт-карта снизу,
        # свет фона по центру за флаконом (просвет). Лампы белые (1, 1, 1).
        L.append(area(S, "Strip_L", -135, 12, 0.42, 0.05, 0.60, 2.6))
        L.append(area(S, "Strip_R", 135, 12, 0.42, 0.05, 0.60, 2.6))
        L.append(area(S, "Top_Softbox", 5, 70, 0.50, 0.45, 0.30, 3.2))
        L.append(area(S, "Front_Card", 0, 6, 1.05, 1.0, 0.35, 5.0))
        glow = bpy.data.lights.new("Glow_Backdrop", "SPOT")
        glow.energy = 7.0; glow.spot_size = math.radians(45); glow.spot_blend = 1.0; glow.shadow_soft_size = 0.3
        go = bpy.data.objects.new("Glow_Backdrop", glow); S.objects.link(go)
        go.location = (0.10, 0.10, 0.80)
        go.rotation_euler = (Vector((0.05, P["wall_y"], 0.10)) - go.location).to_track_quat("-Z", "Y").to_euler()
        L.append(go)
    else:
        raise ValueError(scheme)
    if scheme in ("S3", "S4"):
        # S3 «атмосфера»: S1 + дымка в объёме над постаментом и луч сверху-справа (видимые лучи за флаконом)
        beam = bpy.data.lights.new("Beam", "SPOT")
        beam.energy = 60.0; beam.color = warm; beam.spot_size = math.radians(16); beam.spot_blend = 0.6
        beam.shadow_soft_size = 0.02
        bo = bpy.data.objects.new("Beam", beam); S.objects.link(bo)
        bo.location = (0.55, 0.70, 1.15)
        bo.rotation_euler = (Vector((0.02, 0.35, 0.0)) - bo.location).to_track_quat("-Z", "Y").to_euler()
        if scheme == "S4":                                   # луч сверху за лентой — «лучи» эталона в видимой полосе фона
            beam.energy = 45.0; beam.spot_size = math.radians(9); beam.spot_blend = 0.5; beam.color = kelvin_rgb(5200)
            bo.location = (0.10, 0.55, 1.10)
            bo.rotation_euler = (Vector((0.03, 0.58, -0.10)) - bo.location).to_track_quat("-Z", "Y").to_euler()
        L.append(bo)
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        hz = obj_from_bm(bm, "Haze_Volume", S, smooth=False)
        hz.scale = (1.6, 0.62, 1.3); hz.location = (0.15, 0.50, 0.50)
        if scheme == "S4":                                   # дымка только за лентой: передний план и флакон чистые
            hz.scale = (0.9, 0.40, 1.3); hz.location = (0.0, 0.56, 0.49)
        mh = bpy.data.materials.new("VD_Haze")
        nt = mh.node_tree
        for n in list(nt.nodes):
            if n.type != "OUTPUT_MATERIAL":
                nt.nodes.remove(n)
        vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Density"].default_value = 0.05 if scheme == "S3" else 0.35
        vs.inputs["Anisotropy"].default_value = 0.55
        nt.links.new(vs.outputs["Volume"], bpyx.find_node(nt, "OUTPUT_MATERIAL").inputs["Volume"])
        bpyx.assign_material(hz, mh)
        hz.visible_shadow = False
    for lo in L:                     # лампы не видны камере (только в отражениях и преломлениях)
        lo.visible_camera = False
    ribbon = bpy.data.objects.get("Ribbon_Film")
    if ribbon is not None:           # light linking Cycles: огромный зеркальный блик софтбокса «заливал» ленту белым
        no_rib = bpy.data.collections.get("LL_no_ribbon") or bpy.data.collections.new("LL_no_ribbon")
        only_rib = bpy.data.collections.get("LL_only_ribbon") or bpy.data.collections.new("LL_only_ribbon")
        for c in (no_rib, only_rib):
            if ribbon.name not in c.objects:
                c.objects.link(ribbon)
        for c, state in ((no_rib, "EXCLUDE"), (only_rib, "INCLUDE")):   # collection_objects — без поиска по имени
            co = c.collection_objects[list(c.objects).index(ribbon)]   # у CollectionObject есть только light_linking
            co.light_linking.link_state = state
        no_bd = bpy.data.collections.get("LL_no_backdrop") or bpy.data.collections.new("LL_no_backdrop")
        for nm in ("Cyclorama", "Floor_Stone"):
            ob_ = bpy.data.objects.get(nm)
            if ob_ is not None and ob_.name not in no_bd.objects:
                no_bd.objects.link(ob_)
        for i_, co in enumerate(no_bd.collection_objects):
            co.light_linking.link_state = "EXCLUDE"
        cap = bpy.data.objects.get("Bottle_Cap")
        no_bd_cap = bpy.data.collections.get("LL_no_backdrop_cap") or bpy.data.collections.new("LL_no_backdrop_cap")
        only_cap = bpy.data.collections.get("LL_only_cap") or bpy.data.collections.new("LL_only_cap")
        for ob_ in [bpy.data.objects.get(n) for n in ("Cyclorama", "Floor_Stone")] + [cap]:
            if ob_ is not None and ob_.name not in no_bd_cap.objects:
                no_bd_cap.objects.link(ob_)
        for co in no_bd_cap.collection_objects:
            co.light_linking.link_state = "EXCLUDE"
        if cap is not None and cap.name not in only_cap.objects:
            only_cap.objects.link(cap)
        for co in only_cap.collection_objects:
            co.light_linking.link_state = "INCLUDE"
        no_rib_bd = bpy.data.collections.get("LL_no_ribbon_backdrop") or bpy.data.collections.new("LL_no_ribbon_backdrop")
        for ob_ in [ribbon] + [bpy.data.objects.get(n) for n in ("Cyclorama", "Floor_Stone")]:
            if ob_ is not None and ob_.name not in no_rib_bd.objects:
                no_rib_bd.objects.link(ob_)
        for co in no_rib_bd.collection_objects:
            co.light_linking.link_state = "EXCLUDE"
        for lo in L:                 # v5: ключ без spread светил пол и стену слева (ΔE фона 3,3, вес в зоне текста 0,17)
            if lo.name.startswith("Key"):
                lo.light_linking.receiver_collection = no_rib_bd
        for lo in L:
            if lo.name.startswith("Fill"):
                lo.light_linking.receiver_collection = no_bd_cap
            elif lo.name.startswith("Cap_"):
                lo.light_linking.receiver_collection = only_cap
            elif lo.name.startswith(("Rib", "Rim", "Front", "Strip")):
                lo.light_linking.receiver_collection = no_bd
        for lo in L:
            if lo.name.startswith("Film"):
                lo.light_linking.receiver_collection = only_rib
            elif lo.name.startswith(("Top", "Glow", "Beam", "Kick", "Front", "Sheen")):   # Key — выше (без ленты и фона)
                lo.light_linking.receiver_collection = no_rib
        if P.get("rib_env"):         # v6: у ленты своя «студия» — лампы флакона её не светят (прямоугольник Fill на плёнке)
            no_bdcr = bpy.data.collections.get("LL_no_backdrop_cap_ribbon") or bpy.data.collections.new("LL_no_backdrop_cap_ribbon")
            for ob_ in [ribbon, cap] + [bpy.data.objects.get(n) for n in ("Cyclorama", "Floor_Stone")]:
                if ob_ is not None and ob_.name not in no_bdcr.objects:
                    no_bdcr.objects.link(ob_)
            for co in no_bdcr.collection_objects:
                co.light_linking.link_state = "EXCLUDE"
            plinth = bpy.data.objects.get("Plinth_Marble")
            if not P.get("plinth_fill", True) and plinth is not None and plinth.name not in no_bdcr.objects:
                no_bdcr.objects.link(plinth)
            for co in no_bdcr.collection_objects:
                co.light_linking.link_state = "EXCLUDE"
            for lo in L:
                if lo.name.startswith("Fill"):
                    lo.light_linking.receiver_collection = no_bdcr
                elif lo.name.startswith(("Rib", "Rim", "Front", "Strip")):
                    lo.light_linking.receiver_collection = no_rib_bd
            if P.get("graze_w", 0) > 0 and plinth is not None:    # фактура передней грани без зеркального пятна
                only_pl = bpy.data.collections.get("LL_only_plinth") or bpy.data.collections.new("LL_only_plinth")
                if plinth.name not in only_pl.objects:
                    only_pl.objects.link(plinth)
                for co in only_pl.collection_objects:
                    co.light_linking.link_state = "INCLUDE"
                gz = area(S, "Graze_Plinth", -100, 10, 0.70, 0.30, 0.20, P["graze_w"], kelvin_rgb(5600), target=(0.0, -0.10, -0.07))
                gz.visible_camera = False
                gz.light_linking.receiver_collection = only_pl
                L.append(gz)
        if P.get("glow2"):           # v6: свечение стены — только стена (без камня, флакона и ленты: фон без бурой мути)
            only_bd = bpy.data.collections.get("LL_only_backdrop") or bpy.data.collections.new("LL_only_backdrop")
            cyc = bpy.data.objects.get("Cyclorama")
            if cyc is not None and cyc.name not in only_bd.objects:
                only_bd.objects.link(cyc)
            for co in only_bd.collection_objects:
                co.light_linking.link_state = "INCLUDE"
            for lo in L:
                if lo.name.startswith("Glow"):
                    lo.light_linking.receiver_collection = only_bd
        if P.get("rib_env") and scheme in ("S1", "S3", "S4"):
            ribbon_env(S, P, only_rib)
        print("VD_LIGHTLINK", {lo.name: (lo.light_linking.receiver_collection.name if lo.light_linking.receiver_collection else None) for lo in L})
    if caustics:
        for lo in L:
            if lo.type == "LIGHT" and lo.name.startswith(("Key", "Kick", "Strip", "Sheen")):   # v6: + низкий контровой
                lo.data.cycles.is_caustics_light = True
    return S, L


def camera(P, view):
    turn, k = VIEWS[view]
    return camera_k(P, k), turn


def camera_k(P, k):
    """Камера на дистанции cam_d·k (наезд эталона: 1 → 0,89 за 25°); ровная, сдвиги объектива держат кадр."""
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        cd = bpy.data.cameras.new("VD_Cam")
        cam = bpy.data.objects.new("VD_Cam", cd)
        bpyx.ensure_collection("STAGE").objects.link(cam)
        sc.camera = cam
    cd = cam.data
    cd.lens = P["lens"]; cd.sensor_width = 36.0; cd.sensor_fit = "AUTO"
    d = P["cam_d"] * k
    cam.location = (0.0, -d, P["cam_z"])
    cam.rotation_euler = (math.radians(90), 0.0, 0.0)          # ровная камера: вертикали параллельны
    zc = 0.063                                                  # середина высоты флакона
    w_res, h_res = sc.render.resolution_x, sc.render.resolution_y
    a = (P["cam_z"] - zc) / d * (cd.lens / cd.sensor_width)      # смещение центра флакона вниз, в долях ширины
    b = (0.5 - P["center_y"]) * h_res / w_res
    cd.shift_x = P["shift_x"]
    cd.shift_y = -(a + b)
    cd.dof.use_dof = True
    cd.dof.focus_distance = d - 0.022                           # между осью и этикеткой
    cd.dof.aperture_fstop = P["fstop"]
    cd.dof.aperture_blades = 7
    cd.clip_start, cd.clip_end = 0.01, 20.0
    return cam


def render_setup(samples, res, exposure=0.0):
    sc = bpy.context.scene
    bpyx.set_engine("CYCLES")
    cy = sc.cycles
    cy.device = "CPU"; cy.samples = samples; cy.use_denoising = True; cy.denoiser = "OPENIMAGEDENOISE"
    cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.01
    cy.max_bounces = 24; cy.diffuse_bounces = 3; cy.glossy_bounces = 16; cy.transmission_bounces = 24
    cy.transparent_max_bounces = 8; cy.volume_bounces = 1
    cy.blur_glossy = 0.6; cy.sample_clamp_indirect = 6.0
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.use_persistent_data = True
    bpyx.set_color_management("Khronos PBR Neutral", look="None", exposure=exposure)
    sc.display_settings.display_device = "sRGB"
    ims = sc.render.image_settings
    ims.file_format = "PNG"; ims.color_mode = "RGB"; ims.color_depth = "8"
    return sc


def render_masks(path_obj, path_label, parts_obj, label):
    """Силуэт флакона (стекло + крышка + этикетка) и этикетки — Workbench, плоский свет, цвет объекта, вид Standard."""
    sc = bpy.context.scene
    keep = (sc.render.engine, sc.view_settings.view_transform, sc.render.use_persistent_data)
    comp = sc.render.use_compositing
    sc.render.use_compositing = False           # Glare не должен размывать маски
    bpyx.set_engine("BLENDER_WORKBENCH")
    sh = sc.display.shading
    sh.light = "FLAT"; sh.color_type = "OBJECT"
    sh.background_type = "VIEWPORT"; sh.background_color = (0, 0, 0)
    sc.display.render_aa = "8"
    bpyx.set_color_management("Standard")
    hidden = []
    for ob in sc.objects:
        if ob.type == "MESH":
            ob.color = (0, 0, 0, 1)
        if ob.name.startswith(("Haze", "Env_")):     # Workbench не знает visible_camera: отражатели ленты прячем
            ob.hide_render = True; hidden.append(ob)
    out = []
    for path, white in ((path_obj, parts_obj), (path_label, [label])):
        for ob in sc.objects:
            if ob.type == "MESH":
                ob.color = (1, 1, 1, 1) if ob in white else (0, 0, 0, 1)
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        out.append(path)
    for ob in hidden:
        ob.hide_render = False
    sc.render.engine = keep[0]
    bpyx.set_color_management(keep[1], look="None")
    sc.render.use_compositing = comp
    return out


# ====================================================================== запуск

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(n, d=None):
        return argv[argv.index(n) + 1] if n in argv else d
    scheme = opt("--scheme", "S1")
    views = opt("--views", "f000").split(",")
    res = tuple(int(x) for x in opt("--res", "640x360").split("x"))
    samples = int(opt("--samples", "32"))
    out = opt("--out", os.path.join(HERE, "..", "02-light"))
    tag = opt("--tag", scheme)
    exposure = float(opt("--exposure", "0"))
    for kv in [argv[i + 1] for i, a in enumerate(argv) if a == "--set"]:      # --set ключ=json: правка паспорта
        k, v = kv.split("=", 1)
        P[k] = json.loads(v)
        if k == "ribbon_phase" or k == "ribbon_twist":
            P[k] = math.radians(P[k]) if k == "ribbon_phase" else P[k] * 2 * math.pi
        print("VD_SET", k, P[k])
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    bpyx.clear_scene()
    C, root, parts = build(P)
    stage(P)
    world()
    S, L = lights(scheme, P, caustics="--caustics" in argv)
    if "--caustics" in argv:
        glass = next(o for o in parts if o.name == "Bottle_Glass")
        glass.cycles.is_caustics_caster = True
        for o in parts:
            if o.name.startswith("Plinth"):
                o.cycles.is_caustics_receiver = True
    render_setup(samples, res, exposure)
    compositor(P["glare"])
    if opt("--border"):                       # область кадра (доли, начало — левый верх): проба фактуры в полном масштабе
        bx0, by0, bx1, by1 = [float(x) for x in opt("--border").split(",")]
        rs = bpy.context.scene.render
        rs.use_border = True
        rs.use_crop_to_border = True
        rs.border_min_x, rs.border_max_x = bx0, bx1
        rs.border_min_y, rs.border_max_y = 1.0 - by1, 1.0 - by0
    t_build = time.time() - t0
    ribbon = next(o for o in parts if o.name == "Ribbon_Film")
    phase0 = P["ribbon_phase"]
    # кадры: (имя, поворот стола °, множитель дистанции)
    jobs = []
    if opt("--orbit"):
        n_, a0, a1 = [float(x) for x in opt("--orbit").split(",")]
        n_ = int(n_)
        k0, k1 = [float(x) for x in opt("--dist", "1,1").split(",")]
        loop = abs(abs(a1 - a0) - 360.0) < 1e-6
        for i in range(n_):
            f = i / n_ if loop else (i / (n_ - 1) if n_ > 1 else 0.0)
            jobs.append((f"{i:03d}", a0 + (a1 - a0) * f, k0 + (k1 - k0) * f))
        if opt("--frames"):
            lo_, hi_ = [int(x) for x in opt("--frames").split("-")]
            jobs = [j for j in jobs if lo_ <= int(j[0]) <= hi_]
        if loop:        # VD3 26.09: круг — сначала чётные (шаг 10°), потом нечётные: при нехватке времени круг собирается из чётных
            jobs = [j for j in jobs if int(j[0]) % 2 == 0] + [j for j in jobs if int(j[0]) % 2 == 1]
    else:
        jobs = [(v, VIEWS[v][0], VIEWS[v][1]) for v in views]
    mask_frames = set(opt("--mask-frames", "").split(",")) - {""}
    budget = float(opt("--budget", "0"))
    stats = {"scheme": scheme, "res": res, "samples": samples, "build_s": round(t_build, 1), "views": {},
             "tris": sum(bpyx.object_stats(o).get("tris", 0) for o in parts), "orbit": opt("--orbit"),
             "dist": opt("--dist"), "rib_sway_deg": P["rib_sway"], "glare": P["glare"]}
    last_dt = 0.0
    for name, turn, k in jobs:
        path = os.path.join(out, f"{tag}_{name}.png")
        if "--skip-existing" in argv and os.path.exists(path):
            continue
        if budget > 0 and (time.time() - t0) + last_dt * 1.1 > budget:     # тяжёлый запуск ≤ 15 мин (KIT §2)
            print(f"VD_BUDGET_STOP next={name} elapsed={time.time() - t0:.0f}s", flush=True)
            stats["budget_stop_next"] = name
            break
        cam = camera_k(P, k)
        root.rotation_euler = (0, 0, math.radians(turn))
        phase = phase0 + math.radians(P["rib_sway"]) * math.sin(math.radians(turn))
        if abs(P["rib_sway"]) > 1e-9:
            update_ribbon(ribbon, P, phase)
        bpy.context.view_layer.update()
        sc = bpy.context.scene
        sc.render.filepath = path
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t1
        last_dt = dt
        stats["views"][name] = {"path": path, "render_s": round(dt, 1), "turn_deg": round(turn, 4), "k": round(k, 5),
                                "ribbon_phase_deg": round(math.degrees(phase), 3),
                                "shift_y": round(cam.data.shift_y, 4), "cam_d": round(-cam.location.y, 4)}
        print(f"VD_RENDER {name} {dt:.1f} s turn={turn:.3f} k={k:.4f} → {path}", flush=True)
        if "--mask" in argv and (not mask_frames or name in mask_frames):
            label = next(o for o in parts if o.name == "Bottle_Label")
            objs = [o for o in parts if o.name in ("Bottle_Glass", "Bottle_Cap", "Bottle_Label", "Bottle_Cream")]
            render_masks(os.path.join(out, f"{tag}_{name}_mask.png"), os.path.join(out, f"{tag}_{name}_mask_label.png"), objs, label)
            render_setup(samples, res, exposure)
            compositor(P["glare"])
    if opt("--blend"):                        # после ракурсов: в файле есть камера (qa_pipeline: no_camera) и последний поворот
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(opt("--blend")), compress=True)
    stats["total_s"] = round(time.time() - t0, 1)
    sfx = f"_{jobs[0][0]}-{jobs[-1][0]}" if (opt("--orbit") and jobs) else ""
    json.dump(stats, open(os.path.join(out, f"{tag}_stats{sfx}.json"), "w"), ensure_ascii=False, indent=1)
    print("VD_STATS", json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
