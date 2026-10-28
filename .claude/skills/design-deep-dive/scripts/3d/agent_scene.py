# Blender 5.2.2 — [проверено] работа агента в чужой сцене:
# тег вместо имени, своя коллекция, своя сцена превью, уборка только своего, «правка поверх» (ручные правки -> overrides).
import json

import bpy
from mathutils import Matrix

AGENT, ASSET, PART = "agent", "asset", "part"          # ключи custom properties
DATA_KINDS = ("meshes", "curves", "cameras", "lights", "worlds", "node_groups", "images", "actions")


def tag(idb, agent, asset, part=None):
    idb[AGENT], idb[ASSET] = agent, asset
    if part is not None:
        idb[PART] = part
    return idb


def mine(seq, agent, asset=None, part=None):
    return [i for i in seq if i.get(AGENT) == agent and (asset is None or i.get(ASSET) == asset)
            and (part is None or i.get(PART) == part)]


def own_collection(scene, agent, asset, part="asset", prefix="ASSET_"):
    """Своя коллекция: ищется по тегу (имя может стать .001 или быть переименовано человеком)."""
    coll = next(iter(mine(bpy.data.collections, agent, asset, part)), None)
    if coll is None:
        coll = tag(bpy.data.collections.new(f"{prefix}{asset}"), agent, asset, part)
    if not any(c == coll for c in scene.collection.children):
        scene.collection.children.link(coll)
    return coll


def evict_foreign(coll, scene, agent):
    """Чужой объект в моей коллекции (человек положил руками) не удаляется, а переносится в корень сцены."""
    moved = []
    for ob in list(coll.objects):
        if ob.get(AGENT) != agent:
            if len(ob.users_collection) == 1:
                scene.collection.objects.link(ob)
            coll.objects.unlink(ob)
            moved.append(ob.name)
    return moved


def _base_color(mat):
    p = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    return p.inputs["Base Color"] if p else None


def capture_manual_edits(agent, asset):
    """Что человек изменил после прошлой сборки: matrix_world частей и Base Color материалов (сверка с записанным)."""
    edits = {}
    for ob in mine(bpy.data.objects, agent, asset):
        built, key = ob.get("built_mw"), ob.get(PART)
        cur = [x for row in ob.matrix_world for x in row]
        if built is not None and key and max(abs(a - b) for a, b in zip(cur, built)) > 1e-6:
            edits.setdefault(key, {})["matrix_world"] = cur
    for mat in mine(bpy.data.materials, agent, asset):
        built, key, sock = mat.get("built_color"), mat.get(PART), _base_color(mat)
        if built is not None and key and sock and max(abs(a - b) for a, b in zip(sock.default_value, built)) > 1e-6:
            edits.setdefault(key, {})["base_color"] = list(sock.default_value)
    return edits


def clear_own(agent, asset):
    """Удалить только помеченное: свои объекты, затем свои данные без пользователей (не orphans_purge всего файла)."""
    obs = mine(bpy.data.objects, agent, asset)
    for ob in obs:
        bpy.data.objects.remove(ob, do_unlink=True)
    removed = len(obs)
    for kind in DATA_KINDS:
        seq = getattr(bpy.data, kind)
        for idb in mine(seq, agent, asset):
            if idb.users == 0:
                seq.remove(idb)
                removed += 1
    return removed


def own_material(agent, asset, part, name, color):
    """Материал по тегу и роли; имя — только метка. Чужой материал с тем же именем не трогается."""
    mat = next(iter(mine(bpy.data.materials, agent, asset, part)), None)
    if mat is None:
        mat = tag(bpy.data.materials.new(name), agent, asset, part)
    _base_color(mat).default_value = color
    return mat


def apply_overrides(overrides, agent, asset):
    for ob in mine(bpy.data.objects, agent, asset):
        mw = overrides.get(ob.get(PART), {}).get("matrix_world")
        if mw:
            ob.matrix_world = Matrix([mw[i * 4:i * 4 + 4] for i in range(4)])
    for mat in mine(bpy.data.materials, agent, asset):
        col = overrides.get(mat.get(PART), {}).get("base_color")
        if col:
            _base_color(mat).default_value = col


def record_built(agent, asset):
    bpy.context.view_layer.update()
    for ob in mine(bpy.data.objects, agent, asset):
        ob["built_mw"] = [x for row in ob.matrix_world for x in row]
    for mat in mine(bpy.data.materials, agent, asset):
        mat["built_color"] = list(_base_color(mat).default_value)


def preview_scene(agent, asset, coll):
    """Своя сцена для камеры, света, мира и настроек рендера: сцена человека не меняется."""
    sc = next(iter(mine(bpy.data.scenes, agent, asset)), None)
    if sc is None:
        sc = tag(bpy.data.scenes.new(f"PREVIEW_{asset}"), agent, asset)
    if not any(c == coll for c in sc.collection.children):
        sc.collection.children.link(coll)
    return sc


def begin(scene, agent, asset, keep_manual=True):
    """Начало идемпотентной сборки поверх чужой сцены. Возвращает (коллекция, overrides, отчёт)."""
    coll = own_collection(scene, agent, asset)
    moved = evict_foreign(coll, scene, agent)
    edits = capture_manual_edits(agent, asset)
    overrides = json.loads(coll.get("overrides", "{}")) if keep_manual else {}
    if keep_manual:
        for k, v in edits.items():
            overrides.setdefault(k, {}).update(v)
    removed = clear_own(agent, asset)
    return coll, overrides, {"moved_foreign": moved, "manual_edits": sorted(edits), "removed_own": removed,
                             "overrides_kept": sorted(overrides)}


def finish(coll, overrides, agent, asset):
    apply_overrides(overrides, agent, asset)
    coll["overrides"] = json.dumps(overrides)
    record_built(agent, asset)
