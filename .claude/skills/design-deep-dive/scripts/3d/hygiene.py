# Blender 5.2.2 — [проверено] гигиена СВОЕГО файла агента: отчёт и чистка
# (в сцене человека не применять: удаляет скрытое, далёкое и сирот всего файла).
import re

import bpy
from mathutils import Vector

DUP = re.compile(r"^(.*)\.\d{3}$")


def _world_center(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return sum(pts, Vector()) / 8


def _mat_signature(mat):
    """Материал как данные: типы нод, значения несвязанных входов, картинки, связи. Имя не входит."""
    if not mat.node_tree:
        return ("no-tree", tuple(round(x, 4) for x in mat.diffuse_color))
    nodes = []
    for n in sorted(mat.node_tree.nodes, key=lambda n: (n.bl_idname, n.name)):
        vals = []
        for s in n.inputs:
            v = getattr(s, "default_value", None)
            if s.is_linked or v is None:
                continue
            if isinstance(v, float):
                v = round(v, 4)
            elif not isinstance(v, (str, int)):
                try:
                    v = tuple(round(float(x), 4) for x in v)       # цвет, вектор
                except TypeError:
                    v = str(v)
            vals.append((s.identifier, v))
        img = getattr(n, "image", None)
        nodes.append((n.bl_idname, tuple(vals), img.filepath if img else None))
    links = sorted((l.from_node.bl_idname, l.from_socket.identifier, l.to_node.bl_idname, l.to_socket.identifier)
                   for l in mat.node_tree.links)
    return (tuple(nodes), tuple(links), mat.blend_method if hasattr(mat, "blend_method") else None)


def hygiene_report(export_coll=None, far=100.0):
    sc = bpy.context.scene
    bpy.context.view_layer.update()                                      # matrix_world актуальна
    kinds = ("objects", "meshes", "materials", "images", "node_groups", "actions", "cameras", "lights", "collections")
    rep = {"ids": {k: len(getattr(bpy.data, k)) for k in kinds}}
    rep["dup_names"] = sorted(f"{k}:{i.name}" for k in kinds for i in getattr(bpy.data, k) if DUP.match(i.name))
    rep["orphans"] = sorted(f"{k}:{i.name}" for k in kinds for i in getattr(bpy.data, k)
                            if i.users == 0 and not i.use_fake_user)
    rep["fake_users"] = sorted(f"{k}:{i.name}" for k in kinds for i in getattr(bpy.data, k) if i.use_fake_user)
    rep["far_objects"] = sorted(o.name for o in sc.objects if o.type == "MESH" and _world_center(o).length > far)
    exp = list(export_coll.all_objects) if export_coll else list(sc.objects)
    rep["hidden_in_export"] = sorted(o.name for o in exp if o.hide_render or o.hide_viewport or not o.visible_get())
    sigs = {}
    for m in bpy.data.materials:
        if m.users:
            sigs.setdefault(_mat_signature(m), []).append(m.name)
    rep["dup_materials"] = sorted(v for v in sigs.values() if len(v) > 1)
    imgs = {}
    for im in bpy.data.images:
        if im.filepath:
            imgs.setdefault(bpy.path.abspath(im.filepath), []).append(im.name)
    rep["dup_images"] = sorted(v for v in imgs.values() if len(v) > 1)
    rep["packed_bytes"] = sum(pf.packed_file.size for im in bpy.data.images for pf in im.packed_files)
    rep["stacked_modifiers"] = sorted(f"{o.name}:{t}×{n}" for o in sc.objects
                                      for t in {m.type for m in o.modifiers}
                                      for n in [sum(m.type == t for m in o.modifiers)] if n > 1)
    unused = []
    for o in sc.objects:
        if o.type == "MESH" and len(o.material_slots) > 1:
            used = {p.material_index for p in o.data.polygons}
            if len(used) < len(o.material_slots):
                unused.append(f"{o.name}:{len(o.material_slots) - len(used)}/{len(o.material_slots)}")
    rep["unused_slots"] = sorted(unused)
    rep["extra_uv"] = sorted(f"{m.name}:{len(m.uv_layers)}" for m in bpy.data.meshes if len(m.uv_layers) > 1)
    rep["cameras_in_scene"] = sum(o.type == "CAMERA" for o in sc.objects)
    return rep


def remove_unused_slots(ob):
    """Убрать неиспользуемые слоты, сохранив назначение граней (materials.clear/pop обнуляют material_index — C1)."""
    me = ob.data
    idx = [0] * len(me.polygons)
    me.polygons.foreach_get("material_index", idx)
    used = sorted(set(idx))
    keep = [me.materials[i] for i in used]
    remap = {old: new for new, old in enumerate(used)}
    me.materials.clear()
    for m in keep:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", [remap[i] for i in idx])
    me.update()
    return len(used)


def hygiene_clean(export_coll=None, far=100.0, dedupe_modifiers=True):
    """Чистка своего файла: мусорные объекты, повторные модификаторы, лишние слоты, дубли материалов и картинок,
    лишние камеры, сироты, суффиксы .001. Возвращает счётчики."""
    sc = bpy.context.scene
    bpy.context.view_layer.update()                                      # matrix_world актуальна
    done = {"objects_removed": 0, "modifiers_removed": 0, "slots_removed": 0, "materials_merged": 0,
            "images_merged": 0, "cameras_removed": 0, "renamed": 0}
    exp = set(export_coll.all_objects) if export_coll else set(sc.objects)
    for o in list(sc.objects):                                           # «удалённые» сдвигом и спрятанные
        if o.type == "MESH" and (_world_center(o).length > far or (o in exp and (o.hide_render or o.hide_viewport))):
            bpy.data.objects.remove(o, do_unlink=True)
            done["objects_removed"] += 1
    for o in [o for o in sc.objects if o.type == "CAMERA" and o != sc.camera]:
        bpy.data.objects.remove(o, do_unlink=True)
        done["cameras_removed"] += 1
    if dedupe_modifiers:                                                  # Bevel ×5 подряд — ошибка повтора шага
        for o in sc.objects:
            seen = set()
            for m in reversed(list(o.modifiers)):                        # оставить последний каждого типа
                t = m.type                                               # до remove: потом ссылка висячая
                if t in seen:
                    o.modifiers.remove(m)
                    done["modifiers_removed"] += 1
                else:
                    seen.add(t)
    for o in sc.objects:
        if o.type == "MESH" and len(o.material_slots) > 1:
            before = len(o.material_slots)
            done["slots_removed"] += before - remove_unused_slots(o)
    groups = {}
    for m in sorted(bpy.data.materials, key=lambda m: (len(m.name), m.name)):
        if m.users:
            groups.setdefault(_mat_signature(m), []).append(m)
    for ms in groups.values():
        for dup in ms[1:]:
            dup.user_remap(ms[0])
            done["materials_merged"] += 1
    imgs = {}
    for im in sorted(bpy.data.images, key=lambda i: (len(i.name), i.name)):
        if im.filepath:
            imgs.setdefault(bpy.path.abspath(im.filepath), []).append(im)
    for ims in imgs.values():
        for dup in ims[1:]:
            dup.user_remap(ims[0])
            done["images_merged"] += 1
    done["orphans_purged"] = bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.cameras):
        for idb in list(coll):
            m = DUP.match(idb.name)
            if m and m.group(1) not in coll:
                idb.name = m.group(1)
                done["renamed"] += 1
    return done
