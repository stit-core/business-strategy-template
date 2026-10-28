"""zrender — этюд света, hero и рентген «Звена» (дорожка Z). Открывает собранный .blend, ставит студию/камеру, рендерит
Cycles + маски Workbench (альфа — рука, R — видимый белый лак) для img_metrics.

    blender -b blend/zveno_render.blend --python zrender.py -- --job light --schemes S1,S2,S3,S4 --res 960x540 --samples 32
    blender -b blend/zveno_render.blend --python zrender.py -- --job hero --variant H1 --res 1600x1000 --samples 96
"""
import json
import math
import os
import sys
import time

R = "/home/mm/Документы/app-design/blender-research"
Z = R + "/99-raw/experiments/Z"
for p in (R + "/03-bpy-api/snippets", R + "/99-raw/experiments/D1/_lib", Z + "/lib"):
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bpyx  # noqa: E402
import d1lib as D  # noqa: E402
import zkin as K  # noqa: E402
import zmat as ZM  # noqa: E402
import zpass as ZP  # noqa: E402
import zstudio as S  # noqa: E402

HDRI = "/home/mm/.local/opt/blender-5.2.2-linux-x64/5.2/datafiles/studiolights/world/studio.exr"
PAGE = {"glow": "#1d2026", "mid": "#111316", "edge": "#0d0f12", "page": "#101215"}


def asset():
    coll = bpy.data.collections.get("ASSET_zveno") or bpy.data.collections.get("ASSET_zveno_web")
    obs = [o for o in coll.all_objects if o.type == "MESH"]
    return coll, obs


def robot_only(obs):
    """Для габарита света и кадра — без кабеля (он уходит по полу на 7 м)."""
    return [o for o in obs if not o.name.startswith("base_cable")]


def shell_objs(obs):
    return [o for o in obs if "_shell" in o.name or o.name.endswith("_cup")]


def cam_v2(coll, res):
    c = ZP.V2_CAM
    pos, tgt = K.t2b(c["pos"]), K.t2b(c["target"])
    return S.camera_lookat(coll, pos, tgt, fov_v_deg=c["fov_v_deg"], shift_x=c["shift_x"]), pos, tgt


def cam_product(coll, *, az_three, el_deg, dist, target_three, lens, shift_x, shift_y=0.0, dof=None):
    tgt = K.t2b(target_three)
    d3 = Vector((math.sin(az_three) * math.cos(math.radians(el_deg)), math.sin(math.radians(el_deg)),
                 math.cos(az_three) * math.cos(math.radians(el_deg))))
    pos = tgt + K.t2b(d3) * dist
    return S.camera_lookat(coll, pos, tgt, lens=lens, shift_x=shift_x, shift_y=shift_y, dof=dof), pos, tgt


def orient(lo, pos, target, long_axis):
    """Лампа в pos светит на target (−Z лампы), длинная сторона (X лампы) — вдоль long_axis."""
    z = (Vector(pos) - Vector(target)).normalized()
    la = Vector(long_axis)
    x = (la - z * la.dot(z))
    if x.length < 1e-6:
        x = Vector((1, 0, 0)) - z * z.x
    x.normalize()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(pos)
    lo.matrix_world = m


def strip(coll, name, cam_pos, tgt, az, el, d, sx, sy, E, long_axis, *, spread=180.0):
    pos = Vector(tgt) + S.dir_from(cam_pos, tgt, az, el) * d
    lo = S.area(coll, name, pos, tgt, size=sx, size_y=sy, power=S.light_power(d, E), spread=spread)
    orient(lo, pos, tgt, long_axis)
    return lo


def floor_light(coll, floor_ob, E, *, z=14.0, size=50.0):
    """Ровный свет только на пол (light linking): дальний пол = цвет страницы, мягкая тень руки."""
    lc = D.fresh_collection("Z_FLOOR_RECV")
    if floor_ob.name not in lc.objects:
        lc.objects.link(floor_ob)
    ld = bpy.data.lights.new("L_floor", "SUN")          # солнце: освещённость E одинакова на всём полу
    ld.energy = E; ld.angle = math.radians(50.0)          # большой угол — тень руки мягкая, как AO
    lo = bpy.data.objects.new("L_floor", ld); coll.objects.link(lo)
    lo.rotation_euler = (0.0, 0.0, 0.0)
    lo.light_linking.receiver_collection = lc
    return lo


def stage(scheme, cam_pos, tgt, r, *, floor_E=1.4, key_E=3.0, haze_d=0.0, glow=True):
    st = S.stage_collection("STAGE")
    cam_pos, tgt = Vector(cam_pos), Vector(tgt)
    v = (cam_pos - tgt); v.z = 0; v.normalize()
    up = Vector((0, 0, 1))
    lights = []
    ZM.MAT_CACHE.clear()
    fl = S.floor(st, "render")
    if scheme == "S4":
        p = next(n for n in fl.active_material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        p.inputs["Base Color"].default_value = bpyx.color("#cfcac3")
        for l in list(p.inputs["Roughness"].links):
            fl.active_material.node_tree.links.remove(l)
        p.inputs["Roughness"].default_value = 0.55
    # фон = CSS-градиент страницы (radial-gradient 120% 90% at 70% 40%) в экранных координатах через обратный Neutral;
    # пол растворяется в том же градиенте — без линии горизонта и без «ступеньки» на странице
    if scheme == "S4":
        grad = [(0.0, "#eeebe6"), (0.6, "#dcd7d0"), (1.0, "#cdc7bf")]
    elif scheme == "S2":
        grad = [(0.0, "#15181c"), (0.6, "#0f1114"), (1.0, "#0b0c0f")]
    else:
        grad = [(0.0, PAGE["glow"]), (0.6, PAGE["mid"]), (1.0, PAGE["edge"])]
    world, ng = S.world_page(grad, hdri=HDRI, hdri_strength=0.5 if scheme != "S4" else 0.8, hdri_rot=40.0)
    S.floor_fade(fl, ng, r0=2.6, r1=7.5)
    bd = None
    d = 3.3 * r
    if scheme in ("S1", "S3", "S1H"):
        kE = key_E * (0.8 if scheme == "S3" else 1.0)
        lights.append(strip(st, "L_key", cam_pos, tgt, -38, 38, d, 2.4 * r, 1.7 * r, kE, up))   # крупнее: та же E, отражение тусклее
        lights.append(strip(st, "L_top", cam_pos, tgt, 12, 76, 3.0 * r, 3.4 * r, 0.45 * r, 0.55 * kE, -v))
        lights.append(strip(st, "L_rimL", cam_pos, tgt, -142, 24, 3.0 * r, 0.32 * r, 2.4 * r, 1.6 * kE, up, spread=90))
        lights.append(strip(st, "L_rimR", cam_pos, tgt, 140, 30, 3.0 * r, 0.32 * r, 2.4 * r, 1.4 * kE, up, spread=90))
        lights.append(strip(st, "L_fill", cam_pos, tgt, 60, 10, 4.0 * r, 2.4 * r, 1.8 * r, 0.1 * kE, up))
        lights.append(strip(st, "L_front", cam_pos, tgt, 14, 17, 5.0 * r, 3.4 * r, 1.9 * r, 0.22 * kE, up))   # экран за камерой: металл и лак «видят» светлое
        lights.append(strip(st, "L_catch", cam_pos, tgt, 24, 10, 5.0 * r, 0.3 * r, 2.6 * r, 0.3 * kE, up))    # полоса у камеры: радиальный блик крышек
    elif scheme == "S2":
        kE = key_E * 0.9
        lights.append(strip(st, "L_key", cam_pos, tgt, -62, 12, 3.0 * r, 0.9 * r, 1.4 * r, kE, up))
        lights.append(strip(st, "L_rimL", cam_pos, tgt, -135, 28, 3.0 * r, 0.28 * r, 2.6 * r, 2.0 * kE, up, spread=80))
        lights.append(strip(st, "L_rimR", cam_pos, tgt, 135, 28, 3.0 * r, 0.28 * r, 2.6 * r, 2.0 * kE, up, spread=80))
        floor_E *= 0.7
    elif scheme == "S4":
        kE = key_E * 0.75
        lights.append(strip(st, "L_top", cam_pos, tgt, 0, 80, 3.0 * r, 3.6 * r, 2.4 * r, kE, -v))
        lights.append(strip(st, "L_key", cam_pos, tgt, -45, 30, 3.5 * r, 2.2 * r, 1.8 * r, 0.8 * kE, up))
        lights.append(strip(st, "L_fill", cam_pos, tgt, 55, 15, 4.0 * r, 2.8 * r, 2.2 * r, 0.35 * kE, up))
        floor_E = 6.5
    asset_coll = bpy.data.collections.get("ASSET_zveno") or bpy.data.collections.get("ASSET_zveno_web")
    for lo in lights:                                 # предметный свет — только на руку: пол без пятен и бликов софтбоксов
        lo.light_linking.receiver_collection = asset_coll
    lights.append(floor_light(st, fl, floor_E))
    hz = None
    if scheme == "S1H":                               # дымка за рукой: светит только своя лампа, и только дымку
        hz = S.haze(st, (tgt.x, tgt.y, 3.5), (30.0, 30.0, 7.0), density=haze_d or 0.0022, anisotropy=0.6)
        hc = D.fresh_collection("Z_HAZE_RECV")
        hc.objects.link(hz)
        back = tgt - v * 4.5 + up * 0.2                  # низко за рукой, светит на камеру: ореол за силуэтом, а не луч сверху
        lb = S.area(st, "L_glow", back, tgt + v * 4.0 + up * 1.0, size=2.0, power=S.light_power(4.5, 0.6 * key_E),
                    spread=50.0)
        lb.light_linking.receiver_collection = hc
        lights.append(lb)
    if scheme == "S3":
        hz = S.haze(st, (tgt.x, tgt.y, 6.0), (40.0, 40.0, 12.0), density=haze_d or 0.003, anisotropy=0.55)
        back = tgt - v * 5.0 + up * 3.4
        lb = S.area(st, "L_haze", back, tgt + v * 2.0 - up * 0.8, size=1.2, power=S.light_power(5.0, 1.2 * key_E),
                    spread=28.0)
        lb.light_linking.receiver_collection = None
        lights.append(lb)
    return st, lights, fl, bd, hz


def bbox_r(obs):
    mn, mx = bpyx.world_bbox(obs)
    return (mn + mx) / 2, (mx - mn).length / 2, mn, mx


def do_render(tag, out_dir, *, samples, masks=True):
    coll, obs = asset()
    st = bpy.data.collections.get("STAGE")
    t = S.render(os.path.join(out_dir, f"{tag}.png"), samples=samples)
    info = {"tag": tag, "sec": t}
    if masks:
        stage_objs = [o for o in st.all_objects] if st else []
        stage_objs += [o for o in bpy.data.objects if o.name.startswith("Z_") and o.type == "MESH" and o not in obs]
        S.render_masks(os.path.join(out_dir, f"{tag}_mask.png"), obs, shell_objs(obs), stage_objs=stage_objs)
    return info


# ------------------------------------------------------------------ рентген сустава J3
def xray_material(src, c, band=0.007, accent="#ff5a1f"):
    """Копия материала: ниже плоскости z = c (локальные оси модуля) — исходный материал, выше — «рентген» (прозрачность +
    свечение по Френелю), по линии скана — оранжевая кромка (как скан страницы: «кромка у среза светится»)."""
    m = src.copy(); m.name = src.name + "_xray"
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    solid = out.inputs["Surface"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; nt.links.new(sep.outputs["Z"], sub.inputs[0]); sub.inputs[1].default_value = c
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; nt.links.new(sub.outputs[0], gt.inputs[0]); gt.inputs[1].default_value = 0.0
    ab = nt.nodes.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; nt.links.new(sub.outputs[0], ab.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
    bpyx.set_input(mr, "From Min", 0.0); bpyx.set_input(mr, "From Max", band); bpyx.set_input(mr, "To Min", 1.0); bpyx.set_input(mr, "To Max", 0.0)
    nt.links.new(ab.outputs[0], bpyx.sock(mr, "Value"))
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; nt.links.new(lw.outputs["Facing"], pw.inputs[0]); pw.inputs[1].default_value = 2.8
    ma = nt.nodes.new("ShaderNodeMath"); ma.operation = "MULTIPLY_ADD"; nt.links.new(pw.outputs[0], ma.inputs[0])
    ma.inputs[1].default_value = 0.42; ma.inputs[2].default_value = 0.012
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = bpyx.color("#dde6f2"); em.inputs["Strength"].default_value = 0.55
    gh = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(ma.outputs[0], gh.inputs[0]); nt.links.new(tr.outputs[0], gh.inputs[1]); nt.links.new(em.outputs[0], gh.inputs[2])
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(gt.outputs[0], mx.inputs[0]); nt.links.new(solid, mx.inputs[1]); nt.links.new(gh.outputs[0], mx.inputs[2])
    eb = nt.nodes.new("ShaderNodeEmission"); eb.inputs["Color"].default_value = bpyx.color(accent)
    ms = nt.nodes.new("ShaderNodeMath"); ms.operation = "MULTIPLY"; nt.links.new(bpyx.sock(mr, "Result", out=True), ms.inputs[0]); ms.inputs[1].default_value = 7.0
    nt.links.new(ms.outputs[0], eb.inputs["Strength"])
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(mx.outputs[0], ad.inputs[0]); nt.links.new(eb.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Surface"])
    m.blend_method = "HASHED" if "blend_method" in m.bl_rna.properties else m.blend_method
    return m


def xray_scene(c_cut=0.03):
    coll, obs = asset()
    j3 = bpy.data.objects["j3"]
    keep = set(o for o in j3.children_recursive)
    for o in obs:
        o.hide_render = o not in keep
    # поза как у крупного сустава в сцене «Внутри» кода: big.rotation (0.42, −0.3, 0.04), позиция (0, 1.2, 0), масштаб 1
    M3 = Matrix.Translation((0, 1.2, 0)) @ Matrix.Rotation(0.42, 4, "X") @ Matrix.Rotation(-0.3, 4, "Y") @ Matrix.Rotation(0.04, 4, "Z")
    j3.matrix_world = K.to_blender(M3)
    bpy.context.view_layer.update()
    inner = [o for o in keep if "_in_" in o.name]
    shellish = [o for o in keep if o not in inner and o.type == "MESH"]
    cache = {}
    for o in shellish:
        loc = o.matrix_basis.translation
        if ("capscrew" in o.name or "etch" in o.name) and loc.z > c_cut - 0.01:
            o.hide_render = True                      # крепёж и гравировка в «просвеченной» половине не висят в воздухе
            continue
        for slot in o.material_slots:
            if slot.material is None:
                continue
            if slot.material.name not in cache:
                cache[slot.material.name] = xray_material(slot.material, c_cut)
            slot.material = cache[slot.material.name]
    return j3, inner, shellish


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(n, d=None):
        return argv[argv.index(n) + 1] if n in argv else d
    job = opt("--job", "light")
    res = tuple(int(x) for x in opt("--res", "960x540").split("x"))
    samples = int(opt("--samples", 32))
    out_dir = opt("--out", Z + "/out/" + job)
    os.makedirs(out_dir, exist_ok=True)
    coll, obs = asset()
    c, r, mn, mx = bbox_r(robot_only(obs))
    log = {"job": job, "res": res, "samples": samples, "bbox_c": list(c), "bbox_r": r, "renders": []}
    S.render_setup(samples=samples, res=res, exposure=float(opt("--exposure", 0.0)))
    camc = D.fresh_collection("Z_CAM")
    if job == "light":
        cam, pos, tgt = cam_v2(camc, res)
        for sch in opt("--schemes", "S1,S2,S3,S4").split(","):
            stage(sch, pos, tgt, r, key_E=float(opt("--keyE", 2.2)))
            log["renders"].append(do_render(sch, out_dir, samples=samples))
            print("RENDERED", sch, log["renders"][-1])
    elif job == "hero":
        var = opt("--variant", "H1")
        sch = opt("--scheme", "S1")
        spec = json.loads(opt("--cam", "{}") or "{}")
        if not spec:
            cam, pos, tgt = cam_v2(camc, res)
        else:
            cam, pos, tgt = cam_product(camc, **spec)
        stage(sch, pos, tgt, r, key_E=float(opt("--keyE", 2.2)), floor_E=float(opt("--floorE", 1.4)),
              haze_d=float(opt("--haze", 0.0)))
        log["renders"].append(do_render(f"{var}_{sch}", out_dir, samples=samples))
    elif job == "xray":
        j3, inner, shellish = xray_scene(float(opt("--cut", -0.015)))
        # камера как в scanFrame кода, приведённая к масштабу 1 (код: ×2,45 на 4,3 м): расстояние 1,755 м, высота +0,171 м
        yaw = 0.28
        pos3 = (math.sin(yaw) * 1.755, 1.2 + 0.171, math.cos(yaw) * 1.755)
        cam = S.camera_lookat(camc, K.t2b(pos3), K.t2b((0, 1.2, 0)), fov_v_deg=30.0, shift_x=0.13)
        pos, tgt = cam.location.copy(), K.t2b((0, 1.2, 0))
        st, lights, fl, bd, hz = stage("S1", pos, tgt, 0.36, key_E=float(opt("--keyE", 2.4)))
        fl.hide_render = True
        # своя лампа на начинку (light linking — только внутренние детали): медь и зубья читаются сквозь «рентген»
        ic = D.fresh_collection("Z_INNER_RECV")
        for o in inner:
            ic.objects.link(o)
        cvec = (Vector(pos) - Vector(tgt)).normalized()
        li = S.area(st, "L_inner", Vector(tgt) + Vector((0, 0, 0.55)) + cvec * 0.35, tgt, size=0.3,
                    power=S.light_power(0.65, float(opt("--innerE", 3.5))))
        li.light_linking.receiver_collection = ic
        log["renders"].append(do_render("xray_j3", out_dir, samples=samples, masks=True))
    log["cam"] = {"pos": list(bpy.context.scene.camera.location), "lens": bpy.context.scene.camera.data.lens}
    json.dump(log, open(os.path.join(out_dir, f"log_{job}_{int(time.time())}.json"), "w"), indent=1, default=str)
    print("ZRENDER", json.dumps(log, default=str)[:2000])


if __name__ == "__main__":
    main()
