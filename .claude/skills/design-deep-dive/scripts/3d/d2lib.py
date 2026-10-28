"""d2lib — помощники поверх bpyx (Blender 5.2.2): циклорама, студийные схемы света от размера ассета, паспорт серии.
Подключение: sys.path.insert(0, "<корень скилла>/scripts/3d"); import d2lib (bpyx подключается сам)."""
import json, math, os, sys
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))  # bpyx.py — рядом
import bpyx


def cyclorama(name="Cyc", width=8.0, depth=6.0, height=4.0, radius=1.2, segments=16, color="#E9E9EC",
              roughness=0.9, collection=None):
    """Бесшовный фон: пол + скруглённый переход + стена (профиль в YZ, выдавлен по X), гладкие нормали."""
    prof = [(0.0, depth / 2)]                              # (y, z): от переднего края пола к стене
    prof = []
    ys = -depth / 2
    prof.append((ys, 0.0))
    y0 = depth / 2 - radius
    prof.append((y0, 0.0))
    for i in range(1, segments):                           # дуга от пола к стене
        a = math.radians(90.0 * i / segments)
        prof.append((y0 + radius * math.sin(a), radius - radius * math.cos(a)))
    prof.append((depth / 2, radius))
    prof.append((depth / 2, height))
    bm = bmesh.new()
    left = [bm.verts.new((-width / 2, y, z)) for y, z in prof]
    right = [bm.verts.new((width / 2, y, z)) for y, z in prof]
    for i in range(len(prof) - 1):
        bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for f in me.polygons:                                  # нормали вверх/к камере
        pass
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    bpyx.link(ob, collection)
    mat, _ = bpyx.principled(name + "_mat", base_color=color, roughness=roughness)
    bpyx.assign_material(ob, mat)
    return ob


def light_power(d, E=2.0):
    """Мощность area-лампы (Вт), дающая освещённость E (Вт/м²) на оси на расстоянии d (м): P = π·d²·E.
    Для Lambert L = ρ·E/π → белый (ρ 0.8) при E ≈ 2–3 даёт 0.5–0.75 линейного — зона 1:1 Khronos PBR Neutral."""
    return math.pi * d * d * E


def studio(objects, scheme="three_point", E_key=2.0, collection=None, prefix="L"):
    """Свет от габаритов ассета: r — радиус описанной сферы, d = 4r. Схемы: three_point (key/fill/rim),
    top_softbox (большой софтбокс сверху + два отражателя-заполнения), rim (контровые с двух сторон + слабый фронт).
    E_key — освещённость от key на ассете (Вт/м²): 2.0 под PBR Neutral, ≈ 4 под AgX."""
    mn, mx = bpyx.world_bbox(objects)
    c = (mn + mx) / 2; r = max((mx - mn).length / 2, 1e-3); d = 4 * r
    rigs = {
        "three_point": [("Key", 40, 45, 1.0, 2.0), ("Fill", -70, 15, 0.35, 3.0), ("Rim", 170, 50, 0.6, 1.5)],
        "top_softbox": [("Top", 10, 80, 1.0, 4.0), ("CardL", -90, 5, 0.25, 3.0), ("CardR", 90, 5, 0.25, 3.0)],
        "rim": [("RimL", -135, 25, 0.9, 1.5), ("RimR", 135, 25, 0.9, 1.5), ("Front", 0, 20, 0.25, 3.0)],
    }
    out = []
    for nm, az, el, share, size_r in rigs[scheme]:
        a, e = math.radians(az), math.radians(el)
        loc = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
        out.append(bpyx.add_light("AREA", f"{prefix}_{nm}", loc, c, energy=light_power(d, E_key * share),
                                  size=r * size_r, collection=collection))
    return out


def world_color(hexcolor="#FFFFFF", strength=0.0):
    w = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = bpyx.color(hexcolor); bg.inputs["Strength"].default_value = strength
    return w
