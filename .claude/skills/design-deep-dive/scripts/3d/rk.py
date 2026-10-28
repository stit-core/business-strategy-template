"""rk — набор рецептов 12-recipes. Blender 5.2.2 LTS, glTF-IO 5.2.40.

Тонкая обёртка над проверенными помощниками, чтобы код рецепта был «паспорт → build(P) → проверки → рендер → экспорт»;
помощники лежат рядом, в scripts/3d/:
  bpyx    — сцена, цвет hex → линейный, материалы, камера, рендер
  d1lib   — формы (rounded_slab, lathe, sweep, text/svg, точки), студия, кадр
  d1exp   — glb_info, gltf_optimize, sheet
  d2lib   — циклорама, свет от габарита P = π·d²·E
  presets — 6 пресетов экспорта + команды постобработки
  scene_audit, passport_asserts — проверки кодом
Подключение в блоке рецепта: sys.path.insert(0, "<корень скилла>/scripts/3d"); import rk
"""
import json, math, os, subprocess, sys, time

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402
ROOT = str(kbpaths.kb("3d"))
for _p in (str(kbpaths.scripts("3d")),):  # bpyx, d1lib, d1exp, d2lib, presets — scripts/3d
    if _p not in sys.path:
        sys.path.insert(0, _p)
import bpyx            # noqa: E402
import d1lib as D      # noqa: E402
import d1exp as DX     # noqa: E402
import d2lib           # noqa: E402
import presets         # noqa: E402

NODE_DIR = str(kbpaths.node_home())  # npm-зависимости — $DDD_HOME/node
NODE_BIN = os.path.dirname(kbpaths.node())
GLTFPACK = str(kbpaths.bin_dir("gltfpack-1.2", "gltfpack"))
TOKTX_DIR = str(kbpaths.bin_dir("KTX-Software-4.4.2-Linux-x86_64", "bin"))
AGX_TO_NEUTRAL = 2.5 / 5.85     # d1lib.stage откалиброван под AgX (E_key ≈ 5,85 Вт/м²); под Neutral нужен E_key 2–3
T0 = time.time()
NUM = {}                        # числа рецепта → examples/<slug>/numbers.json


def out_dir(slug):
    d = f"{ROOT}/12-recipes/examples/{slug}"
    os.makedirs(d, exist_ok=True)
    return d


def reset(keep_numbers=False):
    """Чистая сцена без сброса настроек (bpyx.clear_scene); keep_numbers=False — ещё таймер и numbers.json с нуля
    (серия в одном прогоне — keep_numbers=True со второго ассета).
    ВНИМАНИЕ: clear_scene удаляет ВСЕ объекты сцены и сирот — только для фонового процесса (blender -b) или своей сцены;
    в сцене человека (MCP с окном) не вызывать: пересоздавать только свою коллекцию D.fresh_collection (I 02/01 §2)."""
    global T0
    if not keep_numbers:
        T0 = time.time()
        NUM.clear()
    bpyx.clear_scene()


def neutral(samples=32, engine="EEVEE", transparent=False, exposure=0.0):
    """Вид Khronos PBR Neutral (пара к three NeutralToneMapping, ΔE 0,23–0,36)."""
    sc = D.render_setup(samples=samples, view="Khronos PBR Neutral", look="None", transparent=transparent, engine=engine)
    sc.view_settings.exposure = exposure
    return sc


def studio(objs, bg="#EDEDF0", E_key=2.5, az=35.0, backdrop=True, world=0.4):
    """Студия D1 (key/fill/rim от габарита + циклорама цвета страницы) с мощностью под Neutral: E_key 2–3 Вт/м².
    Каталожный свет (ключ az + 45° — ≈ 83° к главной грани: белый кейс рецепта 01 — L* 68, стена L* 55–59) — для рабочих
    превью и рецептов 01–12; для героя — studio_hero (рецепт 13)."""
    return D.stage(objs, bg=bg, az=az, power=E_key / 5.85, backdrop=backdrop, world_strength=world)


# ---------------------------------------------------------------- свет героя (рецепт 13)
# Схема S1 «Звена» (рецепт 13, 12-recipes/13-wow-light-hero.md): имя, азимут от направления на камеру (+ — вправо на экране;
# None — ключ, см. key_az), подъём °, d/r, размер X/r × Y/r, доля E_key, ось стороны X лампы ("up" — вертикаль, "view" —
# вдоль линии взгляда), spread °. Мощность area-лампы P = π·d²·E (d2lib.light_power), лампы белые.
HERO_RIG = (
    ("Key", None, 38.0, 3.3, 2.4, 1.7, 1.0, "up", 180.0),        # ключ к главной грани, подъём 38°
    ("Strip", 12.0, 76.0, 3.0, 3.4, 0.45, 0.55, "view", 180.0),  # софтбокс-полоса: длинный блик вдоль формы
    ("RimL", -142.0, 24.0, 3.0, 0.32, 2.4, 1.6, "up", 90.0),     # контровые ±140° × 1,4–1,6; spread 90° — без пятен на полу
    ("RimR", 140.0, 30.0, 3.0, 0.32, 2.4, 1.4, "up", 90.0),
    ("Fill", 60.0, 10.0, 4.0, 2.4, 1.8, 0.1, "up", 180.0),
    ("Front", 14.0, 17.0, 5.0, 3.4, 1.9, 0.22, "up", 180.0),     # экран за камерой: глянец и металл «видят» светлое
)


def _neutral(c):
    """Khronos PBR Neutral: линейный Rec.709 → линейный (как Z/lib/zstudio.neutral)."""
    x = min(c)
    off = x - 6.25 * x * x if x < 0.08 else 0.04
    c = [v - off for v in c]
    peak = max(c)
    if peak < 0.76:
        return c
    d = 0.24
    npk = 1 - d * d / (peak + d - 0.76)
    c = [v * npk / peak for v in c]
    g = 1 - 1 / (0.15 * (peak - npk) + 1)
    return [v * (1 - g) + npk * g for v in c]


def inv_neutral(target_lin, iters=300):
    """Вход сцены, который Khronos PBR Neutral превратит в target_lin (линейный; каналы ≤ 0,97 — белое 1,0 недостижимо).
    Итерация x += target − neutral(x): у тёмных — «носок» x − 6,25x², у светлых — сжатие пика."""
    t = [min(max(v, 0.0), 0.97) for v in target_lin[:3]]
    x = list(t)
    for _ in range(iters):
        x = [max(0.0, xi + ti - yi) for xi, ti, yi in zip(x, t, _neutral(x))]
    return tuple(x)


def _hero_dir(az_deg, el_deg):
    a, e = math.radians(az_deg), math.radians(el_deg)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def _hero_orient(lo, pos, target, axis_x):
    """Лампа в pos светит на target (−Z), сторона X — вдоль axis_x."""
    from mathutils import Matrix
    z = (pos - target).normalized()
    x = axis_x - z * axis_x.dot(z)
    if x.length < 1e-6:
        x = Vector((1.0, 0.0, 0.0)) - z * z.x
    x.normalize()
    m = Matrix((x, z.cross(x), z)).transposed().to_4x4()
    m.translation = pos
    lo.matrix_world = m


def _hero_recv(name, objs):
    """Коллекция-приёмник light linking вне сцены (как делает интерфейс Blender): объекты остаются в своих коллекциях."""
    rc = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    for o in list(rc.objects):
        rc.objects.unlink(o)
    for o in objs:
        rc.objects.link(o)
    return rc


def studio_hero(objs, *, az=35.0, bg="#EDEDF0", E_key=2.2, key_az=None, key_el=38.0, backdrop="lamp", world=0.1,
                hdri="studio", hdri_strength=0.5, hdri_rot=40.0, engine="CYCLES", face_az=0.0, coll_name="STAGE_HERO"):
    """Свет героя по рецепту 13 (12-recipes/13-wow-light-hero.md; схема S1 «Звена») вместо «каталожного» studio;
    studio и d1lib.stage — свет превью и рецептов 01–12.

    az — азимут камеры (как у camera: 0 — спереди, со стороны −Y; + — вправо), углы ламп — от направления на камеру
    (+ — вправо на экране); r — радиус габарита objs (без кабеля и реквизита: иначе лампы уезжают).
    - ключ: софтбокс 2,4r × 1,7r на d = 3,3r, подъём key_el 38°, по азимуту key_az (None — 38° от камеры в сторону главной
      грани с нормалью по азимуту face_az; 0 — грань к −Y), E_key Вт/м² (2,2–2,4; 5–6 ламп и белый товар — 1,0–1,3 и
      экспозиция −0,25…−0,35); угол ключа к главной грани — в ответе key_to_face_deg (цель 30–45°);
    - полоса-блик 3,4r × 0,45r вдоль линии взгляда (12°/76°, 0,55 E_key); контровые −142°/24° × 1,6 и 140°/30° × 1,4
      (spread 90°); заполнение 60°/10° × 0,1; экран за камерой 14°/17° × 0,22; все лампы белые, камере не видны;
    - мир: лучи камеры — цвет страницы bg через обратную Neutral (inv_neutral), прочие — hdri (встроенный studio.exr,
      обесцвеченный, поворот hdri_rot): в Cycles только отражения (диффузная видимость мира выкл., сила hdri_strength,
      в сценах рецептов — от 0,06 до 0,5), в EEVEE — сила world; без hdri — цвет страницы × world (≤ 0,15);
    - backdrop="lamp" — пол цвета страницы со своей лампой (солнце сверху, угол 50° — мягкая тень касания; альбедо и сила
      считаются так, чтобы пол под Neutral дал bg), предметный свет только на objs (light linking; EEVEE и Cycles) — пол
      без пятна ключа, стык пола с миром-камерой не виден; "catcher" — Cycles: прозрачный кадр + ловец теней, дальше
      neutral(..., transparent=True) и запечь кадр на bg без альфы (out = rgb·a + bg·(1 − a) в sRGB); None — без пола.
    Рендер героя — Cycles (рецепт 13 §8): белый кейс рецепта 01 — главная грань L* 95 (studio — 84), фон к странице ΔE 0,6
    (studio — 3,7). В EEVEE нет отскока от светлого пола — та же схема темнее на ≈ 14 L* (замер: −14,5); engine="EEVEE"
    включает трассировку лучей и быстрый GI (грань 74 → 81) [проверено].
    Вид — Khronos PBR Neutral (rk.neutral). Возвращает dict: coll, lights, key_to_face_deg, floor_E, recv."""
    if backdrop not in ("lamp", "catcher", None):
        raise ValueError(f"studio_hero: backdrop {backdrop!r} — нужно 'lamp', 'catcher' или None")
    eng = engine.upper()
    if backdrop == "catcher" and eng != "CYCLES":
        raise ValueError("studio_hero: ловец теней — только Cycles; для EEVEE backdrop='lamp' или None")
    st = D.fresh_collection(coll_name)
    mn, mx = bpyx.world_bbox(objs)
    c = (mn + mx) / 2
    r = max((mx - mn).length / 2, 1e-3)
    if key_az is None:
        key_az = -38.0 if az - face_az >= 0 else 38.0
    axes = {"up": Vector((0.0, 0.0, 1.0)), "view": -_hero_dir(az, 0.0)}
    lights = []
    for name, a_rel, el, dr, sx, sy, frac, ax, spread in HERO_RIG:
        if name == "Key":
            a_rel, el = key_az, key_el
        d = dr * r
        ld = bpy.data.lights.new(f"Hero_{name}", "AREA")
        ld.shape = "RECTANGLE"
        ld.size, ld.size_y = sx * r, sy * r
        ld.energy = d2lib.light_power(d, frac * E_key)
        ld.color = (1.0, 1.0, 1.0)
        ld.spread = math.radians(spread)
        lo = bpy.data.objects.new(f"Hero_{name}", ld)
        st.objects.link(lo)
        _hero_orient(lo, c + _hero_dir(az + a_rel, el) * d, c, axes[ax])
        lo.visible_camera = False
        lights.append(lo)
    key_face = math.degrees(_hero_dir(az + key_az, key_el).angle(_hero_dir(face_az, 0.0)))
    # мир
    sc = bpy.context.scene
    page = list(bpyx.color(bg)[:3])
    w = bpy.data.worlds.get("HERO_World") or bpy.data.worlds.new("HERO_World")
    sc.world = w
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    b_cam = nt.nodes.new("ShaderNodeBackground")
    b_cam.inputs["Color"].default_value = (*inv_neutral(page), 1.0)
    b_cam.inputs["Strength"].default_value = 1.0
    b_env = nt.nodes.new("ShaderNodeBackground")
    env_diffuse = world * sum(page) / 3                      # вклад мира в диффуз пола (в долях альбедо)
    if hdri:
        path = hdri if os.path.exists(str(hdri)) else os.path.join(
            bpy.utils.system_resource("DATAFILES", path="studiolights/world"), f"{hdri}.exr")
        tc, mp = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeMapping")
        tex, hs = nt.nodes.new("ShaderNodeTexEnvironment"), nt.nodes.new("ShaderNodeHueSaturation")
        tex.image = bpy.data.images.load(path, check_existing=True)
        mp.inputs["Rotation"].default_value[2] = math.radians(hdri_rot)
        hs.inputs["Saturation"].default_value = 0.0
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], hs.inputs["Color"])
        nt.links.new(hs.outputs["Color"], b_env.inputs["Color"])
        if eng == "CYCLES":
            b_env.inputs["Strength"].default_value = hdri_strength
            w.cycles_visibility.diffuse = False              # HDRI только в отражениях: диффуз не заливается
            env_diffuse = 0.0
        else:
            b_env.inputs["Strength"].default_value = world
            import numpy as np                                # средняя яркость обесцвеченного HDRI (HSV: V = max) — для лампы пола
            px = np.empty(len(tex.image.pixels), dtype=np.float32)
            tex.image.pixels.foreach_get(px)
            env_diffuse = world * float(px.reshape(-1, 4)[:, :3].max(axis=1).mean())
    else:
        b_env.inputs["Color"].default_value = (*page, 1.0)
        b_env.inputs["Strength"].default_value = world
    lp, mix = nt.nodes.new("ShaderNodeLightPath"), nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(b_env.outputs["Background"], mix.inputs[1])
    nt.links.new(b_cam.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    if eng.startswith("BLENDER_EEVEE") or eng == "EEVEE":      # отскок от пола и отражения — трассировкой и быстрым GI
        sc.eevee.use_raytracing, sc.eevee.use_fast_gi = True, True
        bpyx.set_enum(sc.eevee, "fast_gi_method", "GLOBAL_ILLUMINATION")
    # фон
    res = {"coll": st, "lights": lights, "key_to_face_deg": round(key_face, 1), "floor_E": None, "recv": None}
    if backdrop is not None:
        floor = bpyx.primitive("plane", "Hero_Floor", size=40.0 * r, location=(c.x, c.y, mn.z), collection=st)
        if backdrop == "catcher":
            floor.is_shadow_catcher = True
            sc.render.film_transparent = True
        else:
            tgt = inv_neutral(page)                           # пол под Neutral = bg: альбедо × E/π = вход Neutral
            k = max(tgt) / 0.9
            mat, _ = bpyx.principled("Hero_Floor", base_color=tuple(v / k for v in tgt), roughness=1.0,
                                     specular_ior_level=0.0)
            bpyx.assign_material(floor, mat)
            sun = bpy.data.lights.new("Hero_FloorSun", "SUN")
            sun.energy = math.pi * max(k - env_diffuse, 0.05)
            sun.angle = math.radians(50.0)                    # мягкая тень касания
            sun.use_shadow_jitter = True                      # EEVEE: без дрожания мягкая тень солнца 50° — полосами
            so = bpy.data.objects.new("Hero_FloorSun", sun)
            st.objects.link(so)
            so.light_linking.receiver_collection = _hero_recv("HERO_RECV_FLOOR", [floor])
            res["recv"] = _hero_recv("HERO_RECV", objs)
            for lo in lights:                                 # предметный свет — только на товар
                lo.light_linking.receiver_collection = res["recv"]
            lights.append(so)
            res["floor_E"] = round(sun.energy, 3)
    NUM["studio_hero"] = {"az": az, "key_az": key_az, "key_el": key_el, "key_to_face_deg": res["key_to_face_deg"],
                          "E_key": E_key, "backdrop": backdrop, "world": world, "hdri": bool(hdri), "engine": eng,
                          "floor_E": res["floor_E"], "r_m": round(r, 4)}
    return res


def camera(objs, az=35.0, el=18.0, lens=85.0, margin=1.15, res=(1024, 1024), shift_y=0.0, ortho=False):
    """Кадр по габаритам (d1lib.frame): сначала разрешение, потом подгонка (D2: кадр зависит от аспекта)."""
    return D.frame(objs, az=az, el=el, lens=lens, margin=margin, res=res, shift_y=shift_y, ortho=ortho)


def render(slug, name, res=(1024, 1024), samples=32, transparent=False):
    r = bpyx.render_still(f"{out_dir(slug)}/{name}.png", resolution=res, samples=samples, transparent=transparent)
    NUM.setdefault("renders", {})[name] = {"sec": r["sec"], "kb": round(r["bytes"] / 1024, 1), "res": list(res)}
    return r["path"]


# ---------------------------------------------------------------- материалы «для веба» (06/01 §2.3)
from io_scene_gltf2.blender.com.material_helpers import create_settings_group, get_gltf_node_name  # noqa: E402

WEB = {
    "plastic_gloss": dict(roughness=0.18, coat_weight=0.5, coat_roughness=0.05),
    "plastic_matte": dict(roughness=0.55),
    "clay": dict(roughness=0.85),
    "rubber": dict(roughness=0.9, specular_ior_level=0.35),
    "ceramic_glaze": dict(roughness=0.45, coat_weight=1.0, coat_roughness=0.05),
    "metal_polished": dict(metallic=1.0, roughness=0.05),
    "metal_satin": dict(metallic=1.0, roughness=0.35),
    "glass": dict(roughness=0.02, ior=1.5, transmission_weight=1.0),
    "glass_frosted": dict(roughness=0.3, ior=1.5, transmission_weight=1.0),
}
METALS = {"aluminum": (0.916, 0.923, 0.924, 1), "silver": (0.991, 0.985, 0.974, 1), "gold": (1.0, 0.773, 0.307, 1),
          "copper": (0.932, 0.623, 0.522, 1), "brass": (0.91, 0.778, 0.423, 1)}


def gltf_output(mat):
    name = get_gltf_node_name()
    node = mat.node_tree.nodes.new("ShaderNodeGroup")
    node.node_tree = bpy.data.node_groups.get(name) or create_settings_group(name)
    return node


def web_material(name, kind, color="#FFFFFF", thickness=0.0, absorption=None, **extra):
    """Материал, который переживает glTF (Principled + факторы). color — hex или ключ METALS; стекло: thickness (м) →
    KHR_materials_volume, absorption = (hex, density) → attenuationColor/Distance."""
    base = METALS.get(color, color)
    mat, bsdf = bpyx.principled(name, base_color=base, **dict(WEB[kind], **extra))
    if kind.startswith("glass"):
        mat.use_raytrace_refraction = True
        mat.thickness_mode = "SPHERE" if thickness > 0.02 else "SLAB"
        if thickness > 0:
            gltf_output(mat).inputs["Thickness"].default_value = thickness
        if absorption:
            va = mat.node_tree.nodes.new("ShaderNodeVolumeAbsorption")
            va.inputs["Color"].default_value = bpyx.color(absorption[0])
            va.inputs["Density"].default_value = absorption[1]
            out = next(n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL")
            mat.node_tree.links.new(va.outputs["Volume"], out.inputs["Volume"])
    mat.use_backface_culling = True
    return mat


# ---------------------------------------------------------------- проверки кодом (scene_audit, passport_asserts)
def _exec_tool(rel, strip_prefix):
    src = open(f"{ROOT}/{rel}", encoding="utf-8").read()
    src = src.rsplit(f'\nprint("{strip_prefix}', 1)[0]          # без печати на уровне модуля
    ns = {"__name__": "rk_tool"}
    exec(compile(src, rel, "exec"), ns)
    return ns


def audit():
    """Аудит сцены scene_audit.py (30 флагов M2–M6). Область — коллекции ASSET_* (студия в STAGE не проверяется)."""
    a = _exec_tool(os.path.relpath(kbpaths.scripts("3d", "scene_audit.py"), ROOT), "AUDIT")["audit"]()
    NUM["audit"] = {"flags": a["flags"], "tris": a["totals"].get("tris"), "draw_calls": a["totals"].get("draw_calls"),
                    "dims_m": a["dims_m"], "frame": a["frame"], "view": a["view_transform"]}
    print("AUDIT", json.dumps(NUM["audit"], ensure_ascii=False))
    return a


def asserts(collection, dims_m, touch=(), max_tris=50000, max_materials=8, tol=0.05, max_gap_m=0.001):
    """Утверждения passport_asserts.py: габарит ±tol, пары частей касаются (зазор ≤ 1 мм), бюджет треугольников и материалов."""
    check = _exec_tool(os.path.relpath(kbpaths.scripts("3d", "passport_asserts.py"), ROOT), "ASSERT")["check"]
    r = check({"collection": collection, "dims_m": list(dims_m), "dims_tol": tol, "touch": [list(t) for t in touch],
               "max_gap_m": max_gap_m, "max_tris": max_tris, "max_materials": max_materials})
    NUM["asserts"] = r
    print("ASSERT", json.dumps(r, ensure_ascii=False))
    assert r["ok"], r["fails"]
    return r


# ---------------------------------------------------------------- экспорт и постобработка (presets.py)
def _run(cmd, cwd=NODE_DIR):
    env = dict(os.environ, PATH=f"{NODE_BIN}:{TOKTX_DIR}:" + os.environ.get("PATH", ""))
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300, env=env)
    if r.returncode != 0:
        raise RuntimeError(" ".join(cmd) + "\n" + r.stderr[-800:])
    return r


def ship(slug, collection, name, preset="static_hero", optimize="meshopt", phone=False, keep_names=True):
    """Экспорт коллекции пресетом presets.py → <name>_raw.glb; постобработка → <name>.glb (веб):
    optimize='meshopt' — gltf-transform optimize (meshopt + квантование, WebP); keep_names=True — без flatten/join (части
    адресуемы из JS); phone=True — ещё <name>_phone.glb: нативный gltfpack -cc -tc -ts 0.5 (KTX2, текстуры ½).
    Метки-пустышки (hotspot_*, extras) — optimize="gltfpack" (-cc -kn -ke): prune/переименование иначе их теряют."""
    d = out_dir(slug)
    raw = D.export_web(f"{d}/{name}_raw.glb", collection, preset)
    res = {"preset": preset, "raw": DX.glb_info(raw["path"])}
    web = f"{d}/{name}.glb"
    if optimize == "meshopt":
        cmd = ["npx", "--no-install", "gltf-transform", "optimize", raw["path"], web, "--compress", "meshopt",
               "--texture-compress", "webp", "--simplify", "false"]
        if keep_names:
            cmd += ["--flatten", "false", "--join", "false"]
        _run(cmd)
    elif optimize == "gltfpack":
        _run([GLTFPACK, "-i", raw["path"], "-o", web, "-cc", "-kn", "-ke"])
    else:
        import shutil
        shutil.copy(raw["path"], web)
    res["web"] = DX.glb_info(web)
    if phone:
        _run([GLTFPACK, "-i", raw["path"], "-o", f"{d}/{name}_phone.glb", "-cc", "-tc", "-ts", "0.5"])
        res["phone"] = DX.glb_info(f"{d}/{name}_phone.glb")
    NUM.setdefault("glb", {})[name] = {k: {kk: v[kk] for kk in ("kb", "tris", "nodes", "materials", "extensionsUsed",
                                                                    "instanced_nodes")} for k, v in res.items() if k != "preset"}
    NUM["glb"][name]["preset"] = preset
    return res


def portable(obj, base):
    """Пути для numbers.json — не пути машины: путь внутри скилла — от папки примера base (`../04-…/x_raw.glb`), вне
    скилла — имя файла. Словари и списки — рекурсивно, остальное — как есть."""
    if isinstance(obj, dict):
        return {k: portable(v, base) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [portable(v, base) for v in obj]
    if isinstance(obj, str) and os.path.isabs(obj):
        skill = os.path.abspath(str(kbpaths.skill()))
        if os.path.commonpath([skill, os.path.abspath(obj)]) == skill:
            return os.path.relpath(obj, base).replace(os.sep, "/")
        return os.path.basename(obj)
    return obj


def save(slug, **extra):
    """numbers.json: время сборки (с), числа рендеров, аудит, утверждения, веса GLB; пути — portable()."""
    NUM.update(extra)
    NUM["sec_total"] = round(time.time() - T0, 1)
    NUM["blender"] = bpy.app.version_string
    p = f"{out_dir(slug)}/numbers.json"
    json.dump(portable(NUM, out_dir(slug)), open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print("NUMBERS", json.dumps({k: NUM[k] for k in ("sec_total",) }), p)
    return p
