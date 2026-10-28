"""animx — помощники анимации для Blender 5.2. Проверено: Blender 5.2.2 LTS, glTF-IO 5.2.40.

Дополняют bpyx (рядом, scripts/3d/bpyx.py): там нет функций анимации. Всё через data API 5.x
(слои → полосы → channelbag слота), без устаревших action.fcurves / action.id_root.
Подключение: sys.path.insert(0, "<корень скилла>/scripts/3d"); import animx
"""
from __future__ import annotations

import json
import math
import os
import struct

import bpy
from bpy_extras import anim_utils
from mathutils import Euler, Matrix, Quaternion, Vector

__version__ = "0.1.0"


# ------------------------------------------------------------------ ключи и кривые
def key(idblock, data_path: str, frame: float, value=None, *, index: int = -1, interpolation: str | None = None,
        easing: str | None = None, group: str | None = None):
    """Поставить ключ: (опционально) присвоить value, затем keyframe_insert с ИМЕНОВАННЫМИ аргументами (5.x).
    Вернуть список F-кривых этого пути (для index=-1 — все компоненты)."""
    if value is not None:
        if index >= 0:
            getattr(idblock, data_path)[index] = value
        else:
            setattr(idblock, data_path, value)
    kw = {"index": index, "frame": frame}
    if group:
        kw["group"] = group
    ok = idblock.keyframe_insert(data_path, **kw)
    if not ok:
        raise RuntimeError(f"keyframe_insert({data_path!r}, frame={frame}) → False")
    fcs = [fc for fc in fcurves(idblock) if fc.data_path == data_path and (index < 0 or fc.array_index == index)]
    if interpolation or easing:
        for fc in fcs:
            for kp in fc.keyframe_points:
                if abs(kp.co[0] - frame) < 1e-6:
                    if interpolation:
                        kp.interpolation = interpolation
                    if easing:
                        kp.easing = easing
    return fcs


def fcurves(idblock) -> list:
    """F-кривые назначенного действия и слота (5.x: у Action нет .fcurves)."""
    ad = getattr(idblock, "animation_data", None)
    if ad is None or ad.action is None or ad.action_slot is None:
        return []
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return list(cb.fcurves) if cb else []


def set_interpolation(idblock, interpolation: str = "BEZIER", *, easing: str | None = None, handle: str | None = None,
                      back: float | None = None, amplitude: float | None = None, period: float | None = None,
                      data_path: str | None = None):
    """Интерполяция/изинг/ручки для всех ключей (или одного data_path) назначенного слота."""
    n = 0
    for fc in fcurves(idblock):
        if data_path and fc.data_path != data_path:
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = interpolation
            if easing:
                kp.easing = easing
            if handle:
                kp.handle_left_type = kp.handle_right_type = handle
            if back is not None:
                kp.back = back
            if amplitude is not None:
                kp.amplitude = amplitude
            if period is not None:
                kp.period = period
            n += 1
        fc.update()
    return n


def add_cycles(idblock, *, data_path: str | None = None, mode: str = "REPEAT"):
    """Модификатор Cycles на F-кривые (петля в Blender). В glTF сам модификатор НЕ уходит: экспортёр сэмплирует
    только диапазон действия — петля в вебе = LoopRepeat клипа длиной ровно в период."""
    mods = []
    for fc in fcurves(idblock):
        if data_path and fc.data_path != data_path:
            continue
        m = fc.modifiers.new(type="CYCLES")
        m.mode_before = m.mode_after = mode
        mods.append(m)
    return mods


def loop_range(action, frame_start: float, frame_end: float, *, cyclic: bool = True):
    """Ручной диапазон действия: экспортёр glTF берёт int(action.frame_range) как границы клипа."""
    action.use_frame_range = True
    action.frame_start, action.frame_end = frame_start, frame_end
    action.use_cyclic = cyclic
    return tuple(action.frame_range)


# ------------------------------------------------------------------ действия, слоты, NLA
def new_action(name: str, ids, *, reuse_slots: bool = True):
    """Одно действие со слотом на каждый ID (5.x): все объекты «раскрытия» в одном клипе glTF.
    Слот создаётся при присвоении действия объекту и первом fcurve_ensure/keyframe_insert."""
    act = bpy.data.actions.new(name)
    for idb in ids:
        ad = idb.animation_data or idb.animation_data_create()
        ad.action = act
        if ad.action_slot is None:
            slot = act.slots.new(id_type=_id_type(idb), name=idb.name)
            ad.action_slot = slot
    return act


def _id_type(idb) -> str:
    """Тип ID для ActionSlots.new(id_type=…): OBJECT, KEY, MATERIAL, NODETREE, CAMERA, LIGHT, WORLD …"""
    for T, t in ((bpy.types.Object, "OBJECT"), (bpy.types.Key, "KEY"), (bpy.types.Material, "MATERIAL"),
                 (bpy.types.NodeTree, "NODETREE"), (bpy.types.Camera, "CAMERA"), (bpy.types.Light, "LIGHT"),
                 (bpy.types.World, "WORLD"), (bpy.types.Mesh, "MESH")):
        if isinstance(idb, T):
            return t
    return "UNSPECIFIED"


def assign(idblock, action, slot=None):
    """Назначить действие и слот (4.4+: без слота объект НЕ анимирован)."""
    ad = idblock.animation_data or idblock.animation_data_create()
    ad.action = action
    if slot is None and ad.action_slot is None:
        suit = list(ad.action_suitable_slots)
        slot = suit[0] if suit else action.slots.new(id_type="OBJECT", name=idblock.name)
    if slot is not None:
        ad.action_slot = slot
    return ad.action_slot


def stash(idblock, clip_name: str, *, track_name: str | None = None, start: int | None = None):
    """Текущее действие → своя NLA-дорожка с ОДНОЙ полосой (иначе экспортёр в ACTIONS её пропустит); действие
    переименовывается в clip_name (имя клипа glTF = имя действия); объект освобождается."""
    ad = idblock.animation_data
    act, slot = ad.action, ad.action_slot
    act.name = clip_name
    tr = ad.nla_tracks.new()
    tr.name = track_name or clip_name
    s = tr.strips.new(clip_name, int(act.frame_range[0] if start is None else start), act)
    if s.action_slot is None and slot is not None:
        s.action_slot = slot
    ad.action = None
    return tr, s


def bake_visual(objects, frame_start: int, frame_end: int, *, step: int = 1, clear_constraints: bool = True,
                clear_parents: bool = False, name: str | None = None):
    """Запечь визуальные трансформации (констрейнты, драйверы, физика, родители) в ключи БЕЗ оператора:
    bpy_extras.anim_utils.bake_action_objects. Возвращает [(obj, action)]."""
    opts = anim_utils.BakeOptions(only_selected=False, do_pose=False, do_object=True, do_visual_keying=True,
                                  do_constraint_clear=clear_constraints, do_parents_clear=clear_parents, do_clean=False,
                                  do_location=True, do_rotation=True, do_scale=True, do_bbone=False, do_custom_props=False)
    pairs = [(ob, None) for ob in objects]
    acts = anim_utils.bake_action_objects(pairs, frames=range(frame_start, frame_end + 1, step), bake_options=opts)
    out = []
    for ob, act in zip(objects, acts):
        if name:
            act.name = f"{name}" if len(objects) == 1 else f"{name}_{ob.name}"
        out.append((ob, act))
    return out


# ------------------------------------------------------------------ экспорт и разбор GLB
ANIM_PRESET = dict(
    export_format="GLB", export_yup=True, export_apply=True, export_texcoords=True, export_normals=True,
    export_tangents=False, export_materials="EXPORT", export_image_format="AUTO", export_vertex_color="MATERIAL",
    export_all_vertex_colors=False, export_attributes=False, export_extras=True, export_cameras=False,
    export_lights=False, use_renderable=True, use_visible=True,
    export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True, export_frame_step=1,
    export_optimize_animation_size=True, export_anim_slide_to_zero=True, export_merge_animation="ACTION",
    export_morph=True, export_morph_normal=True, export_morph_animation=True, export_skins=True,
    export_draco_mesh_compression_enable=False, export_meshopt_compression_enable=False,
)


def export_glb(path: str, **overrides) -> dict:
    """Экспорт GLB с анимацией; ключи проверяются по RNA оператора (5.2.40). Для морфов — export_apply=False."""
    kw = dict(ANIM_PRESET)
    kw.update(overrides)
    valid = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    bad = [k for k in kw if k not in valid]
    if bad:
        raise KeyError(f"нет параметров {bad} в export_scene.gltf этой версии")
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = bpy.ops.export_scene.gltf(filepath=path, **kw)
    if r != {"FINISHED"} or not os.path.exists(path):
        raise RuntimeError(f"export → {r}")
    return {"path": path, "bytes": os.path.getsize(path)}


def glb_json(path: str) -> dict:
    data = open(path, "rb").read()
    ln = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20:20 + ln])


def anim_summary(path: str) -> dict:
    """Клипы GLB: имя, каналы (узел, путь, интерполяция, число ключей, время), размер данных анимации."""
    j = glb_json(path)
    acc = j.get("accessors", [])
    bvs = j.get("bufferViews", [])
    comp = {5126: 4, 5123: 2, 5121: 1, 5122: 2, 5120: 1, 5125: 4}
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

    def acc_bytes(i):
        a = acc[i]
        return a["count"] * ncomp[a["type"]] * comp[a["componentType"]]
    clips = []
    total = 0
    seen = set()
    for an in j.get("animations", []):
        chans = []
        for c in an["channels"]:
            s = an["samplers"][c["sampler"]]
            t = c["target"]
            inp = acc[s["input"]]
            for k in (s["input"], s["output"]):
                if k not in seen:
                    seen.add(k)
                    total += acc_bytes(k)
            chans.append({"node": j["nodes"][t["node"]].get("name") if "node" in t else None, "path": t["path"],
                          "pointer": t.get("extensions", {}).get("KHR_animation_pointer", {}).get("pointer"),
                          "interp": s.get("interpolation", "LINEAR"), "keys": inp["count"],
                          "t": [round(inp["min"][0], 4), round(inp["max"][0], 4)]})
        clips.append({"name": an.get("name"), "channels": chans,
                      "duration": max((c["t"][1] for c in chans), default=0)})
    return {"file_bytes": os.path.getsize(path), "anim_data_bytes": total, "clips": clips,
            "extensionsUsed": j.get("extensionsUsed", []), "nodes": [n.get("name") for n in j.get("nodes", [])],
            "skins": len(j.get("skins", [])), "morph_targets": [len(p.get("targets", [])) for m in j.get("meshes", []) for p in m["primitives"]]}


# ------------------------------------------------------------------ рендер кадров для сравнения
def render_frames(frames, out_dir: str, *, prefix: str = "blender_f", resolution=(512, 512), samples: int = 16,
                  transparent: bool = True):
    """Рендер кадров анимации EEVEE (камера сцены) → PNG; для сравнения с three в тех же моментах."""
    sc = bpy.context.scene
    r = sc.render
    r.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = samples
    r.resolution_x, r.resolution_y = resolution
    r.resolution_percentage = 100
    r.film_transparent = transparent
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for f in frames:
        sc.frame_set(int(f))
        p = os.path.join(os.path.abspath(out_dir), f"{prefix}{int(f):04d}.png")
        r.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths
