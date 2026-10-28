"""bpyx — проверенные помощники Python API для Blender 5.2 (ИИ-агент, фон и MCP).

Проверено: Blender 5.2.2 LTS (Python 3.13), тесты — test_bpyx.py (запуск через scripts/3d/blender_run.py).
База знаний: kb/3d/03-bpy-api/ (01 модель данных, 02 ноды, 03 дрейф версий, 04 ошибки нейросетей).

Принципы:
- только data API, где это возможно (быстро, не зависит от выделения, активного объекта и окна);
- операторы — только где без них нельзя (UV-развёртка, модификатор-ассет), с явным temp_override и проверкой {'FINISHED'};
- ноды ищутся по type/bl_idname (имена нод переводятся в локализованном интерфейсе), сокеты — по identifier или
  имени СРЕДИ ДОСТУПНЫХ, режим ноды (data_type и т. п.) задаётся до поиска сокетов, каждая связь проверяется is_valid;
- перечисления проверяются по фактическому списку (RNA занижает динамические: движки, view transform, цвет. пространства);
- функции возвращают созданные объекты и печатают предупреждения с префиксом [bpyx], но не глотают ошибки.

Подключение: в фоне — `sys.path.insert(0, SNIPPETS); import bpyx`; в MCP (execute_blender_code) — то же в первом вызове
(+ `sys.dont_write_bytecode = True; importlib.reload(bpyx)` после правок файла), дальше `import bpyx` в каждом вызове.
Подробно — README.md рядом.
"""
from __future__ import annotations

import ast
import difflib
import math
import os
import re
import time

import bpy
import bmesh
from mathutils import Matrix, Quaternion, Vector

__version__ = "1.0.0"
TESTED_WITH = (5, 2, 2)
GEOMETRY_TYPES = {"MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES", "POINTCLOUD", "VOLUME", "GREASEPENCIL"}

__all__ = [
    "version_at_least", "rna_has", "enum_values", "set_enum", "did_you_mean",
    "ensure_object_mode", "clear_scene", "ensure_collection", "link",
    "mesh_object", "primitive", "convert_to_mesh",
    "add_modifier", "apply_modifiers", "apply_transforms", "smooth_by_angle",
    "world_bbox", "put_on_floor", "center_objects", "origin_to_center", "object_stats", "scene_report",
    "srgb_to_linear", "color", "find_node", "node", "sock", "set_input", "link_sockets", "principled",
    "assign_material", "layout_tree", "assert_valid_links",
    "look_at", "add_camera", "add_light", "three_point_lights", "frame_camera",
    "set_engine", "set_color_management", "render_still",
    "export_glb", "uv_unwrap",
    "gn_tree", "gn_modifier", "gn_inputs", "gn_set_input", "view3d_override",
]


# ====================================================================== служебное и интроспекция

def _warn(msg: str) -> None:
    print(f"[bpyx] ВНИМАНИЕ: {msg}")


def version_at_least(major: int, minor: int = 0, patch: int = 0) -> bool:
    """True, если запущенный Blender не старше major.minor.patch. [5.2.2]"""
    return tuple(bpy.app.version) >= (major, minor, patch)


def did_you_mean(name: str, pool, n: int = 8) -> list:
    """Похожие имена: сначала близкие по написанию, потом содержащие подстроку (без учёта регистра). [5.2.2]"""
    pool = list(pool)
    low = {str(x).lower(): x for x in pool}
    close = [low[x] for x in difflib.get_close_matches(str(name).lower(), list(low), n=n, cutoff=0.55)]
    sub = [x for x in pool if str(name).lower() in str(x).lower() and x not in close]
    return (close + sub)[:n]


def rna_has(obj_or_type, name: str) -> bool:
    """Есть ли RNA-свойство или функция `name` у объекта или типа bpy.types.X. [5.2.2]

    Не используйте hasattr(bpy.types.X, 'prop'): на КЛАССЕ он видит только Python-члены (всегда False для RNA)."""
    rna = obj_or_type.bl_rna
    return name in rna.properties or name in rna.functions


def enum_values(owner, prop: str) -> list:
    """Фактические допустимые значения перечисления `owner.prop` (включая динамические). [5.2.2]

    RNA занижает динамические перечисления (движки рендера, view transform, look, цветовые пространства,
    denoiser): enum_items может вернуть 1 значение или пустой список. Способ: присвоить заведомо неверное значение —
    TypeError перечисляет допустимые; объект при этом не меняется."""
    p = owner.bl_rna.properties.get(prop)
    if p is None or p.type != "ENUM":
        raise AttributeError(f"{owner.bl_rna.identifier}.{prop} — не перечисление")
    cur = getattr(owner, prop)
    probe = {"__bpyx_invalid__"} if isinstance(cur, set) else "__bpyx_invalid__"
    try:
        setattr(owner, prop, probe)
    except TypeError as e:
        m = re.search(r"not found in \((.*)\)", str(e))
        if m:
            try:
                return [x for x in ast.literal_eval("(" + m.group(1) + ",)") if isinstance(x, str)]
            except (ValueError, SyntaxError):
                pass
    return [i.identifier for i in p.enum_items]


def set_enum(owner, prop: str, value: str, aliases: dict | None = None) -> str:
    """Присвоить значение перечисления с понятной ошибкой (список допустимых + похожие). [5.2.2]"""
    value = (aliases or {}).get(value, value)
    try:
        setattr(owner, prop, value)
        return getattr(owner, prop)
    except TypeError:
        vals = enum_values(owner, prop)
        raise ValueError(f"{owner.bl_rna.identifier}.{prop} = {value!r}: нет такого значения; допустимо {vals}; "
                         f"похожие {did_you_mean(value, vals)}") from None


def ensure_object_mode() -> None:
    """Выйти в Object Mode, если активен другой режим (данные меша синхронизируются при выходе). [5.2.2]"""
    ctx = bpy.context
    if ctx.mode != "OBJECT" and ctx.view_layer.objects.active is not None and bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")


def view3d_override():
    """Словарь для context.temp_override(**d) с областью VIEW_3D и регионом WINDOW текущего экрана, или None. [5.2.2]

    В фоне (blender -b и bpy из PyPI) есть окно с экраном «Layout» и областью VIEW_3D, но context.area = None;
    с этим override работают view3d.* (camera_to_view_selected, view_all). Без экрана с VIEW_3D — None."""
    wm = bpy.context.window_manager
    for win in wm.windows:
        scr = win.screen
        for area in (scr.areas if scr else []):
            if area.type == "VIEW_3D":
                reg = next((r for r in area.regions if r.type == "WINDOW"), None)
                if reg is not None:
                    return {"window": win, "screen": scr, "area": area, "region": reg}
    return None


# ====================================================================== сцена, коллекции, объекты

def clear_scene(scene=None, *, purge: bool = True) -> dict:
    """Удалить все объекты сцены и её вложенные коллекции через data API; затем сироты (purge). [5.2.2]

    Не сбрасывает настройки и интерфейс (в отличие от wm.read_factory_settings), но удаляет ВСЕ объекты сцены (со скрытыми
    и исключёнными) и глобально чистит сирот — только для своего фонового файла; в сцене человека — уборка по тегу. Мир сцены сохраняется (у него есть пользователь — сцена). Возвращает счётчики удалённого."""
    scene = scene or bpy.context.scene
    ensure_object_mode()
    n_obj = 0
    for ob in list(scene.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
        n_obj += 1
    n_coll = 0

    def drop(coll):
        nonlocal n_coll
        for ch in list(coll.children):
            drop(ch)
            coll.children.unlink(ch)
            if ch.users == 0:
                bpy.data.collections.remove(ch)
                n_coll += 1
    drop(scene.collection)
    purged = 0
    if purge:
        purged = bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    return {"objects": n_obj, "collections": n_coll, "orphans_purged": purged}


def ensure_collection(name: str, parent=None, scene=None):
    """Коллекция `name`, привязанная к parent (по умолчанию — корневая коллекция сцены). [5.2.2]

    Коллекция из bpy.data.collections.new без привязки не видна: её объекты не рендерятся и не экспортируются."""
    scene = scene or bpy.context.scene
    parent = parent or scene.collection
    coll = bpy.data.collections.get(name)
    if coll is None or coll.library is not None:
        coll = bpy.data.collections.new(name)
    if not any(ch == coll for ch in parent.children) and coll != parent:
        parent.children.link(coll)
    return coll


def link(ob, collection=None):
    """Привязать объект к коллекции (по умолчанию — корневой коллекции сцены), если ещё не привязан. [5.2.2]

    Объект без коллекции: users=0, нет в scene.objects, нельзя сделать активным, не сохраняется в .blend."""
    collection = collection or bpy.context.scene.collection
    if collection not in ob.users_collection:
        collection.objects.link(ob)
    return ob


def mesh_object(name: str, verts, faces=(), edges=(), *, collection=None, location=(0, 0, 0), smooth: bool = False,
                validate: bool = True):
    """Меш-объект из списков вершин/граней (from_pydata + validate + update), привязанный к коллекции. [5.2.2]

    from_pydata(vertices, edges, faces) требует ВСЕ три аргумента (в 5.2 два → TypeError); рёбра выводятся из граней,
    если edges пуст; грани по умолчанию плоские (smooth=False)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [tuple(e) for e in edges], [tuple(f) for f in faces],
                   shade_flat=not smooth)
    if validate and me.validate(verbose=False):
        _warn(f"{name}: validate() исправил геометрию (вырожденные грани/рёбра удалены)")
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    return link(ob, collection)


def _torus_bmesh(bm, R, r, seg, ring, uv_layer):
    vs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(ring):
            b = 2 * math.pi * j / ring
            vs.append(bm.verts.new(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a),
                                    r * math.sin(b))))
    for i in range(seg):
        for j in range(ring):
            i2, j2 = (i + 1) % seg, (j + 1) % ring
            f = bm.faces.new((vs[i * ring + j], vs[i2 * ring + j], vs[i2 * ring + j2], vs[i * ring + j2]))
            if uv_layer is not None:
                us = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                for loop, (u, v) in zip(f.loops, us):
                    loop[uv_layer].uv = (u / seg, v / ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def primitive(kind: str, name: str | None = None, *, size: float = 2.0, radius: float = 1.0, depth: float = 2.0,
              segments: int = 32, rings: int = 16, subdivisions: int = 2, minor_radius: float = 0.25,
              x_segments: int = 1, y_segments: int = 1, location=(0, 0, 0), collection=None,
              smooth: bool | None = None, smooth_angle: float = 30.0, uv: bool = True):
    """Примитив через bmesh.ops без операторов: cube, uvsphere, icosphere, cylinder, cone, plane/grid, circle,
    torus, monkey. Центр — в начале координат меша, объект ставится в `location`. [5.2.2]

    - size — полный размер куба/плоскости (cube size=2 → от −1 до 1); radius/depth — для сфер/цилиндров/конусов;
    - uv=True — UV-слой «UVMap» создаётся ДО create_* (иначе calc_uvs молча ничего не делает);
    - smooth=None: куб/плоскость — плоские, остальное — гладкое + острые рёбра по углу smooth_angle (путь 5.2 вместо
      use_auto_smooth); circle создаётся с заливкой одной n-гонной гранью (cap_ends) — для веера треугольников
      используйте cylinder/cone."""
    k = kind.lower()
    name = name or k.capitalize()
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap") if uv else None
    if k == "cube":
        bmesh.ops.create_cube(bm, size=size, calc_uvs=uv)
    elif k in ("uvsphere", "sphere"):
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius, calc_uvs=uv)
    elif k == "icosphere":
        bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=radius, calc_uvs=uv)
    elif k in ("cylinder", "cone"):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius,
                              radius2=radius if k == "cylinder" else 0.0, depth=depth, calc_uvs=uv)
    elif k in ("plane", "grid"):
        # bmesh create_grid: size — половина стороны
        bmesh.ops.create_grid(bm, x_segments=x_segments, y_segments=y_segments, size=size / 2.0, calc_uvs=uv)
    elif k == "circle":
        bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=segments, radius=radius, calc_uvs=uv)
    elif k == "torus":
        _torus_bmesh(bm, radius, minor_radius, segments, max(3, rings), uvl)
    elif k in ("monkey", "suzanne"):
        bmesh.ops.create_monkey(bm, calc_uvs=uv)
    else:
        bm.free()
        raise ValueError(f"primitive: неизвестный вид {kind!r}; есть cube, uvsphere, icosphere, cylinder, cone, "
                         f"plane, grid, circle, torus, monkey")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth is None:
        smooth = k not in ("cube", "plane", "grid", "circle")
    if smooth:
        me.shade_smooth()
        if k not in ("uvsphere", "sphere", "icosphere", "torus", "monkey"):
            me.set_sharp_from_angle(angle=math.radians(smooth_angle))
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    return link(ob, collection)


def convert_to_mesh(ob, *, keep_original: bool = False):
    """Текст/кривую/поверхность/мета-шар (или меш с модификаторами) → новый меш-объект без оператора. [5.2.2]

    bpy.data.meshes.new_from_object(вычисленный объект) — меш с модификаторами, extrude и bevel; материалы
    переназначены на оригинальные. Новый объект получает имя, матрицу и коллекции исходного."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    if me is None:
        raise ValueError(f"{ob.name}: у объекта типа {ob.type} нет геометрии")
    name, mw, colls = ob.name, ob.matrix_world.copy(), list(ob.users_collection)
    new = bpy.data.objects.new(name + "_mesh", me)
    for c in colls or [bpy.context.scene.collection]:
        c.objects.link(new)
    new.matrix_world = mw
    if not keep_original:
        bpy.data.objects.remove(ob, do_unlink=True)
        new.name = name
        me.name = name
    return new


# ====================================================================== модификаторы и трансформации

def add_modifier(ob, mtype: str, name: str | None = None, **props):
    """Добавить модификатор с проверкой имён свойств по RNA (ошибка с подсказкой, а не молчание). [5.2.2]

    Неверный тип → TypeError Blender со списком типов; несовместимый тип (GREASE_PENCIL_* на меше) → modifiers.new
    возвращает None — здесь ValueError. Типичные устаревшие имена: bevel.use_only_vertices → affect='VERTICES',
    mirror.use_x → use_axis=(True, False, False), boolean solver 'FAST' → 'FLOAT'."""
    m = ob.modifiers.new(name or mtype.replace("_", " ").title(), mtype)
    if m is None:
        raise ValueError(f"модификатор {mtype} неприменим к объекту {ob.name} типа {ob.type}")
    pool = [p.identifier for p in m.bl_rna.properties]      # до remove(): после него m — висячая ссылка
    bad = [k for k in props if k not in pool]
    if bad:
        ob.modifiers.remove(m)
        raise AttributeError(f"{mtype}: нет свойств {bad}; похожие: "
                             f"{ {b: did_you_mean(b, pool, 4) for b in bad} }")
    for k, v in props.items():
        setattr(m, k, v)
    return m


def apply_modifiers(ob, *, count: int | None = None):
    """Применить модификаторы (все или первые `count`) без оператора: меш из вычисленного объекта. [5.2.2]

    Сохраняет материалы, группы вершин и веса; теряет shape keys (предупреждение). Общий меш (users > 1) не
    трогается — объект получает новый. Инстансы GN без Realize Instances в меш НЕ попадают."""
    if ob.type != "MESH":
        raise ValueError(f"{ob.name}: apply_modifiers для MESH; текст/кривые — convert_to_mesh()")
    mods = list(ob.modifiers)
    if not mods:
        return ob
    if ob.data.shape_keys:
        _warn(f"{ob.name}: shape keys будут потеряны при применении модификаторов")
    keep_state = {}
    if count is not None:
        for m in mods[count:]:
            keep_state[m.name] = m.show_viewport
            m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = ob.data
    for m in (mods if count is None else mods[:count]):
        ob.modifiers.remove(m)
    for n, st in keep_state.items():
        ob.modifiers[n].show_viewport = st
    new_me.name = old.name
    ob.data = new_me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


def apply_transforms(ob, *, location: bool = False, rotation: bool = True, scale: bool = True):
    """«Apply transforms» без оператора: перенести вращение/масштаб (и перенос) в данные меша/кривой. [5.2.2]

    Мировое положение вершин не меняется; дети остаются на месте (пересчитывается их matrix_parent_inverse).
    Общие данные (users > 1) сначала копируются, чтобы не испортить другие объекты."""
    if ob.data is None or not hasattr(ob.data, "transform"):
        raise ValueError(f"{ob.name}: у типа {ob.type} нет данных для transform()")
    mb = ob.matrix_basis.copy()
    loc, rot, sca = mb.decompose()
    keep = Matrix.LocRotScale(Vector() if location else loc, Quaternion() if rotation else rot,
                              Vector((1, 1, 1)) if scale else sca)
    applied = keep.inverted() @ mb
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    ob.data.transform(applied)
    ob.matrix_basis = keep
    for ch in ob.children:
        ch.matrix_parent_inverse = applied @ ch.matrix_parent_inverse
    bpy.context.view_layer.update()
    return ob


def smooth_by_angle(ob, angle: float = 30.0, *, method: str = "DATA"):
    """Гладкое затенение с острыми рёбрами по углу (замена удалённого в 4.1 use_auto_smooth). [5.2.2]

    method='DATA' — Mesh.shade_smooth() + Mesh.set_sharp_from_angle(angle): разрушающе, без модификатора, сразу
    экспортируется; method='MODIFIER' — оператор object.shade_auto_smooth: модификатор-ассет «Smooth by Angle»
    (входы Input_1 = угол), неразрушающе, но для экспорта нужен export_apply или apply_modifiers()."""
    if ob.type != "MESH":
        raise ValueError(f"{ob.name}: нужен MESH")
    if method.upper() == "DATA":
        ob.data.shade_smooth()
        ob.data.set_sharp_from_angle(angle=math.radians(angle))
        return None
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob],
                                   selected_editable_objects=[ob]):
        r = bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))
    if r != {"FINISHED"}:
        raise RuntimeError(f"shade_auto_smooth → {r}")
    return ob.modifiers[-1]


# ====================================================================== габариты и статистика

def _geo_objects(objects=None, scene=None):
    scene = scene or bpy.context.scene
    objs = objects if objects is not None else [o for o in scene.objects if o.visible_get()]
    return [o for o in objs if o.type in GEOMETRY_TYPES or (o.type == "EMPTY" and o.instance_type == "COLLECTION")]


def world_bbox(objects=None, scene=None):
    """(min, max) габаритов в мировых координатах по вычисленной геометрии (модификаторы, GN, extrude текста). [5.2.2]
    Инстансы GN без Realize в габарит не входят (у объекта из одних инстансов он вырожден) — брать прокси или `depsgraph.object_instances`.

    Берётся bound_box ОРИГИНАЛЬНОГО объекта после обновления depsgraph: в 5.2.2 он отражает вычисленную геометрию.
    bound_box у ob.evaluated_get(dg) для FONT/CURVE НЕ учитывает extrude/bevel (кольцо r=1: ±2 вместо ±1.1)."""
    objs = _geo_objects(objects, scene)
    if not objs:
        raise ValueError("world_bbox: нет объектов с геометрией")
    bpy.context.evaluated_depsgraph_get()   # гарантировать вычисление
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return Vector(map(min, *pts)), Vector(map(max, *pts))


def put_on_floor(objects, z: float = 0.0):
    """Сдвинуть объекты (корневые, без родителя в наборе) так, чтобы нижняя точка общих габаритов была на z. [5.2.2]"""
    objects = [objects] if not isinstance(objects, (list, tuple, set)) else list(objects)
    mn, _ = world_bbox(objects)
    dz = z - mn.z
    for o in objects:
        if o.parent not in objects:
            o.location.z += dz
    bpy.context.view_layer.update()
    return dz


def center_objects(objects, axes: str = "XY", target=(0.0, 0.0, 0.0)):
    """Сдвинуть объекты так, чтобы центр их общих габаритов по осям `axes` совпал с target. [5.2.2]"""
    objects = [objects] if not isinstance(objects, (list, tuple, set)) else list(objects)
    mn, mx = world_bbox(objects)
    c = (mn + mx) / 2
    d = Vector((0, 0, 0))
    for i, ax in enumerate("XYZ"):
        if ax in axes.upper():
            d[i] = target[i] - c[i]
    for o in objects:
        if o.parent not in objects:
            o.location += d
    bpy.context.view_layer.update()
    return d


def origin_to_center(ob):
    """Origin в центр локальных габаритов геометрии без оператора origin_set; объект визуально не сдвигается. [5.2.2]"""
    if ob.data is None or not hasattr(ob.data, "transform"):
        raise ValueError(f"{ob.name}: нет данных для transform()")
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    bpy.context.evaluated_depsgraph_get()
    c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8
    ob.data.transform(Matrix.Translation(-c))
    ob.matrix_world = ob.matrix_world @ Matrix.Translation(c)
    bpy.context.view_layer.update()
    return c


def object_stats(ob) -> dict:
    """Статистика вычисленного объекта: вершины, треугольники, n-гоны, материалы, габариты, модификаторы. [5.2.2]"""
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    d = {"name": ob.name, "type": ob.type, "modifiers": [m.type for m in ob.modifiers],
         "materials": [s.material.name if s.material else None for s in ob.material_slots],
         "scale_applied": all(abs(s - 1) < 1e-6 for s in ob.scale)}
    me = None
    try:
        me = oe.to_mesh()
    except RuntimeError:
        me = None
    if me is not None:
        d.update(verts=len(me.vertices), faces=len(me.polygons),
                 tris=sum(len(p.vertices) - 2 for p in me.polygons),
                 ngons=sum(1 for p in me.polygons if len(p.vertices) > 4),
                 uv_layers=[u.name for u in me.uv_layers])
        oe.to_mesh_clear()
    if ob.type in GEOMETRY_TYPES:
        mn, mx = world_bbox([ob])
        d["dims"] = [round(x, 4) for x in (mx - mn)]
    return d


def scene_report(scene=None, *, do_print: bool = True) -> dict:
    """Короткий отчёт по сцене для конца скрипта: объекты по типам, треугольники, материалы, габариты, камера,
    движок, view transform. Печатает одну строку JSON. [5.2.2]"""
    import json
    scene = scene or bpy.context.scene
    objs = list(scene.objects)
    geo = [o for o in objs if o.type in GEOMETRY_TYPES]
    tris = 0
    for o in geo:
        s = object_stats(o)
        tris += s.get("tris", 0)
    rep = {"blender": bpy.app.version_string, "objects": len(objs),
           "by_type": {t: sum(1 for o in objs if o.type == t) for t in sorted({o.type for o in objs})},
           "tris": tris, "materials": sorted({s.material.name for o in geo for s in o.material_slots if s.material}),
           "camera": scene.camera.name if scene.camera else None, "engine": scene.render.engine,
           "view_transform": scene.view_settings.view_transform}
    if geo:
        mn, mx = world_bbox(geo)
        rep["bbox_min"] = [round(x, 3) for x in mn]
        rep["bbox_max"] = [round(x, 3) for x in mx]
    if do_print:
        print("SCENE_REPORT", json.dumps(rep, ensure_ascii=False))
    return rep


# ====================================================================== цвет, материалы, ноды

def srgb_to_linear(c: float) -> float:
    """sRGB (как в CSS/hex) → линейный (как в Blender default_value). [5.2.2]"""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def color(value, alpha: float | None = None) -> tuple:
    """Цвет → RGBA для сокетов Blender (линейный). [5.2.2]

    '#RRGGBB' / '#RRGGBBAA' / 'RRGGBB' — трактуется как sRGB (CSS) и переводится в линейный;
    (r, g, b[, a]) float 0..1 — уже линейный (как принимает Blender);
    (r, g, b) int 0..255 — трактуется как sRGB 8 бит (предупреждение)."""
    if isinstance(value, str):
        h = value.strip().lstrip("#")
        if len(h) not in (6, 8):
            raise ValueError(f"color: ожидается '#RRGGBB[AA]', получено {value!r}")
        rgb = [srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)]
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (*rgb, a if alpha is None else alpha)
    v = list(value)
    if len(v) not in (3, 4):
        raise ValueError(f"color: нужно 3 или 4 компоненты, получено {len(v)}")
    if all(isinstance(x, int) for x in v[:3]) and max(v[:3]) > 1:
        _warn(f"color {value}: целые > 1 — считаю sRGB 0..255")
        v = [srgb_to_linear(x / 255) for x in v[:3]] + ([v[3] / 255 if v[3] > 1 else v[3]] if len(v) == 4 else [])
    a = v[3] if len(v) == 4 else 1.0
    return (float(v[0]), float(v[1]), float(v[2]), float(a if alpha is None else alpha))


def find_node(tree, kind: str, *, required: bool = False):
    """Первая нода дерева с node.type == kind или bl_idname == kind (не по имени: имена переводятся). [5.2.2]

    Пример: find_node(mat.node_tree, 'BSDF_PRINCIPLED') или 'ShaderNodeBsdfPrincipled'. У новых нод GN type —
    не enum (например, 'GeometryNodeInputInstanceBounds'), поэтому bl_idname надёжнее."""
    for n in tree.nodes:
        if n.type == kind or n.bl_idname == kind:
            return n
    if required:
        raise KeyError(f"в дереве {tree.name} нет ноды {kind}; есть {[(n.bl_idname, n.type) for n in tree.nodes]}")
    return None


def node(tree, idname: str, *, location=None, label: str | None = None, inputs: dict | None = None, **props):
    """Создать ноду по bl_idname, задать свойства (режимы — ДО сокетов) и значения входов. [5.2.2]

    Неизвестный bl_idname → RuntimeError Blender «Node type X undefined» (подсказка через bpy_probe nodes)."""
    n = tree.nodes.new(idname)
    pool = [p.identifier for p in n.bl_rna.properties]      # до remove(): после него n — висячая ссылка
    for k, v in props.items():
        if k not in pool:
            tree.nodes.remove(n)
            raise AttributeError(f"{idname}: нет свойства {k!r}; похожие {did_you_mean(k, pool)}")
        setattr(n, k, v)
    if location is not None:
        n.location = location
    if label:
        n.label = label
    for k, v in (inputs or {}).items():
        set_input(n, k, v)
    return n


def sock(n, key, *, out: bool = False):
    """Сокет ноды по identifier или имени СРЕДИ ДОСТУПНЫХ (enabled); int — индекс. Ошибка — с подсказкой. [5.2.2]

    Причины: node.inputs['A_Color'] даёт KeyError для Mix/Map Range (поиск по identifier выключен), недоступные
    сокеты по строке не находятся, индексы сдвигаются между версиями (Principled inputs[7] в 5.2 — 'Weight')."""
    coll = n.outputs if out else n.inputs
    if isinstance(key, int):
        return coll[key]
    for s in coll:
        if s.identifier == key and s.enabled:
            return s
    for s in coll:
        if s.name == key and s.enabled:
            return s
    hidden = [s.identifier for s in coll if (s.identifier == key or s.name == key) and not s.enabled]
    if hidden:
        modes = {p.identifier: getattr(n, p.identifier) for p in n.bl_rna.properties
                 if p.type == "ENUM" and p.identifier not in bpy.types.Node.bl_rna.properties}
        raise KeyError(f"{n.bl_idname}: сокет {key!r} есть ({hidden}), но недоступен при режиме {modes}")
    avail = [s.name for s in coll if s.enabled]
    raise KeyError(f"{n.bl_idname}: нет {'выхода' if out else 'входа'} {key!r}; доступны {avail}; "
                   f"похожие {did_you_mean(key, avail, 5)}")


def set_input(n, key, value):
    """Задать default_value входа: цвет приводится к RGBA (color()), размерность проверяется. [5.2.2]"""
    s = sock(n, key)
    if not hasattr(s, "default_value"):
        raise TypeError(f"{n.bl_idname}.{s.name}: у сокета типа {s.type} нет default_value (нужна связь)")
    if s.type == "RGBA":
        value = color(value)
    s.default_value = value
    return s


def link_sockets(tree, from_socket, to_socket):
    """Связь с проверкой: from/to — сокет или (нода, ключ). Невалидная связь (Shader → Color, недоступный сокет)
    Blender создаёт молча с is_valid=False — здесь ValueError. [5.2.2]"""
    if isinstance(from_socket, tuple):
        from_socket = sock(from_socket[0], from_socket[1], out=True)
    if isinstance(to_socket, tuple):
        to_socket = sock(to_socket[0], to_socket[1])
    lk = tree.links.new(from_socket, to_socket)
    if not lk.is_valid:
        tree.links.remove(lk)
        raise ValueError(f"невалидная связь {from_socket.node.name}.{from_socket.identifier} ({from_socket.type}) → "
                         f"{to_socket.node.name}.{to_socket.identifier} ({to_socket.type})")
    return lk


PRINCIPLED_ALIASES = {  # имена 3.x → 5.2 (переименованы в 4.0)
    "specular": "Specular IOR Level", "subsurface": "Subsurface Weight", "transmission": "Transmission Weight",
    "clearcoat": "Coat Weight", "clearcoat_roughness": "Coat Roughness", "clearcoat_normal": "Coat Normal",
    "coat": "Coat Weight", "sheen": "Sheen Weight", "emission": "Emission Color", "subsurface_color": "Base Color",
    "specular_tint": "Specular Tint",
}


def _principled_key(p, key: str) -> str:
    names = [s.name for s in p.inputs]
    if key in names:
        return key
    k = key.lower().replace(" ", "_")
    if k in PRINCIPLED_ALIASES:
        new = PRINCIPLED_ALIASES[k]
        if key not in ("coat",):
            _warn(f"Principled: {key!r} → {new!r} (переименован в 4.0)")
        return new
    for nm in names:
        if nm.lower().replace(" ", "_") == k:
            return nm
    raise KeyError(f"Principled: нет входа {key!r}; похожие {did_you_mean(key, names, 5)}")


def principled(name: str, *, reuse: bool = True, **inputs):
    """Материал с Principled BSDF 5.2 и значениями входов. Возвращает (material, principled_node). [5.2.2]

    Ключи — имена сокетов («Base Color») или snake_case (base_color, emission_strength); старые имена 3.x
    (specular, transmission, clearcoat, sheen, emission, subsurface) переводятся с предупреждением. Цвета — через
    color() (hex '#RRGGBB' = sRGB). Эмиссия видна только при emission_strength > 0 (по умолчанию 0).
    use_nodes не нужен: в 5.x новый материал сразу с деревом (use_nodes устарел, удаление в 6.0)."""
    mat = bpy.data.materials.get(name) if reuse else None
    if mat is None:
        mat = bpy.data.materials.new(name)
    if mat.node_tree is None:           # < 5.0
        mat.use_nodes = True
    tree = mat.node_tree
    p = find_node(tree, "BSDF_PRINCIPLED")
    out = find_node(tree, "OUTPUT_MATERIAL")
    if out is None:
        out = tree.nodes.new("ShaderNodeOutputMaterial")
    if p is None:
        p = tree.nodes.new("ShaderNodeBsdfPrincipled")
        p.location = (out.location.x - 300, out.location.y)
    if not out.inputs["Surface"].is_linked:
        link_sockets(tree, p.outputs["BSDF"], out.inputs["Surface"])
    for k, v in inputs.items():
        set_input(p, _principled_key(p, k), v)
    return mat, p


def assign_material(ob, mat, *, replace: bool = True, slot: int | None = None):
    """Назначить материал: replace=True — единственный материал объекта; slot=i — в слот i; иначе добавить слот.
    Материал пишется в данные (link='DATA'), общий меш получит его у всех владельцев. [5.2.2]"""
    mats = ob.data.materials
    if slot is not None:
        while len(mats) <= slot:
            mats.append(None)
        mats[slot] = mat
    elif replace:
        mats.clear()
        mats.append(mat)
    else:
        mats.append(mat)
    return mat


def layout_tree(tree, *, dx: float = 280.0, dy: float = 200.0) -> int:
    """Раскладка нод колонками по глубине от выходной ноды (для человека; на результат не влияет). [5.2.2]

    Использует location_absolute (в 5.2 location ноды внутри рамки — относительно рамки)."""
    outs = [n for n in tree.nodes if n.type in ("OUTPUT_MATERIAL", "OUTPUT_WORLD", "GROUP_OUTPUT", "OUTPUT_LIGHT")
            or n.bl_idname == "NodeGroupOutput"]
    if not outs:
        outs = [n for n in tree.nodes if not any(s.is_linked for s in n.outputs)]
    depth = {o: 0 for o in outs}
    frontier = list(outs)
    while frontier:
        nxt = []
        for n in frontier:
            for s in n.inputs:
                for lk in s.links:
                    fn = lk.from_node
                    if depth.get(fn, -1) < depth[n] + 1 and depth[n] < 100:
                        depth[fn] = depth[n] + 1
                        nxt.append(fn)
        frontier = nxt
    cols = {}
    for n, d in depth.items():
        cols.setdefault(d, []).append(n)
    for d, ns in cols.items():
        for i, n in enumerate(ns):
            pos = (-d * dx, -i * dy + (len(ns) - 1) * dy / 2)
            if hasattr(n, "location_absolute"):
                n.location_absolute = pos
            else:
                n.location = pos
    return len(cols)


def assert_valid_links(tree) -> int:
    """Проверить, что все связи дерева валидны; вернуть их число. Иначе ValueError со списком. [5.2.2]"""
    bad = [f"{lk.from_node.name}.{lk.from_socket.identifier} → {lk.to_node.name}.{lk.to_socket.identifier}"
           for lk in tree.links if not lk.is_valid]
    if bad:
        raise ValueError(f"{tree.name}: невалидные связи {bad}")
    return len(tree.links)


# ====================================================================== камера и свет

def look_at(ob, target, *, track: str = "-Z", up: str = "Y"):
    """Повернуть объект (камеру/свет: они смотрят вдоль −Z) на точку target. [5.2.2]

    rotation_euler = (target − location).to_track_quat('-Z', 'Y'); проверено проекцией: цель в центре кадра."""
    bpy.context.view_layer.update()
    direction = Vector(target) - ob.matrix_world.translation
    if direction.length < 1e-9:
        raise ValueError("look_at: цель совпадает с позицией объекта")
    q = direction.to_track_quat(track, up)
    if ob.parent is not None:
        q = ob.parent.matrix_world.to_quaternion().inverted() @ q
    if ob.rotation_mode == "QUATERNION":
        ob.rotation_quaternion = q
    else:
        ob.rotation_euler = q.to_euler(ob.rotation_mode)
    return ob


def add_camera(name: str = "Camera", location=(0.0, -6.0, 3.0), target=(0.0, 0.0, 0.0), *, lens: float = 50.0,
               collection=None, set_active: bool = True, clip_start: float = 0.01, clip_end: float = 1000.0):
    """Камера, смотрящая на target, опционально активная камера сцены (без неё рендер: «Cannot render, no camera»). [5.2.2]"""
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start, cd.clip_end = clip_start, clip_end
    cam = bpy.data.objects.new(name, cd)
    cam.location = location
    link(cam, collection)
    look_at(cam, target)
    if set_active:
        bpy.context.scene.camera = cam
    return cam


def add_light(kind: str = "AREA", name: str | None = None, location=(3.0, -3.0, 4.0), target=(0.0, 0.0, 0.0), *,
              energy: float = 500.0, size: float = 1.0, color_rgb=(1.0, 1.0, 1.0), collection=None,
              use_shadow: bool = True):
    """Источник света (POINT, SUN, SPOT, AREA), направленный на target. [5.2.2]

    energy — Вт для POINT/SPOT/AREA, Вт/м² для SUN (1–10 — уже солнечный день); size — для AREA сторона (size),
    для POINT/SPOT — радиус мягкости (shadow_soft_size); у SUN — угловой диаметр в радианах (angle)."""
    kind = kind.upper()
    ld = bpy.data.lights.new(name or kind.title(), kind)
    ld.energy = energy
    ld.color = color_rgb
    ld.use_shadow = use_shadow
    if kind == "AREA":
        ld.size = size
    elif kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size
    elif kind == "SUN":
        ld.angle = size if size < math.pi else math.radians(size)
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = location
    link(lo, collection)
    if target is not None:
        look_at(lo, target)
    return lo


def three_point_lights(objects=None, *, power: float = 1.0, collection=None, prefix: str = "Key") -> list:
    """Студийный свет key/fill/rim, размер и мощность по габаритам объектов (калибровка render_views.py:
    900 Вт на 7 м ≈ нормальная экспозиция при AgX; под Khronos PBR Neutral — `power` ≈ 0,33–0,5: E_key 2–3 Вт/м², blender `06/02 §2`). Возвращает [key, fill, rim]. [5.2.2]"""
    mn, mx = world_bbox(objects)
    c = (mn + mx) / 2
    r = max((mx - mn).length / 2, 1e-3)
    d = r * 4.0
    k = 900.0 * (d / 7.0) ** 2 * power
    out = []
    for nm, az, el, pw, sz in (("Key", 40, 45, k, r * 2.0), ("Fill", -70, 15, k * 0.35, r * 3.0),
                               ("Rim", 170, 50, k * 0.6, r * 1.5)):
        a, e = math.radians(az), math.radians(el)
        loc = c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
        out.append(add_light("AREA", f"{prefix}_{nm}" if prefix != "Key" else nm, loc, c, energy=pw, size=sz,
                             collection=collection))
    return out


def _world_points(objects=None, scene=None):
    """Мировые координаты вершин вычисленной геометрии (модификаторы, GN, extrude текста) как массив numpy (N, 3);
    у объектов без меша (инстансер коллекции, волосы, облако точек, объём) — 8 углов bound_box. Инстансы GN без Realize
    не входят (как в world_bbox). [5.2.2]"""
    import numpy as np
    objs = _geo_objects(objects, scene)
    if not objs:
        raise ValueError("_world_points: нет объектов с геометрией")
    dg = bpy.context.evaluated_depsgraph_get()
    chunks = []
    for o in objs:
        pts = None
        if o.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}:
            oe = o.evaluated_get(dg)
            try:
                me = oe.to_mesh()
            except RuntimeError as e:          # нет меша у вычисленного объекта — берём bound_box ниже
                _warn(f"_world_points: {o.name}: to_mesh — {e}; беру углы bound_box")
                me = None
            if me is not None:
                if len(me.vertices):
                    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
                    me.vertices.foreach_get("co", co)
                    pts = co.reshape(-1, 3).astype(np.float64)
                oe.to_mesh_clear()
        if pts is None:
            pts = np.array([tuple(c) for c in o.bound_box], dtype=np.float64)
        m = np.array(o.matrix_world, dtype=np.float64)
        chunks.append(pts @ m[:3, :3].T + m[:3, 3])
    return np.concatenate(chunks)


def frame_camera(cam, objects=None, *, margin: float = 1.1, extra_points=()):
    """Поставить камеру (с текущим направлением) так, чтобы объекты целиком вошли в кадр; margin > 1 — поля.
    Кадр считается по ТЕКУЩЕМУ разрешению сцены — задать `render.resolution_x/y` до вызова. [5.2.2]
    extra_points — мировые точки, которые тоже должны войти в кадр (например, концы тени на земле).

    PERSP — Object.camera_fit_coords по 8 углам габарита (как view3d.camera_to_view_selected), камера отводится от центра
    габарита в margin раз. ORTHO — своя проекция вершин на оси камеры:
    camera_fit_coords для ORTHO точен только в квадратном кадре — в 16:9 ответ зависит от исходного ortho_scale и
    режет модель (9,8 м в кадре при нужных ≥ 11,5 м). ortho_scale —
    сторона кадра по sensor_fit (AUTO: большая сторона с учётом pixel_aspect), центр объектов — в центре кадра с учётом
    shift_x/y; ближняя точка — в 1 м + clip_start перед камерой, clip_end растёт, если дальняя точка за ним."""
    if cam.data.type == "ORTHO":
        import numpy as np
        pts = _world_points(objects)
        if len(extra_points):
            pts = np.concatenate([pts, np.array([tuple(p) for p in extra_points], dtype=np.float64)])
        bpy.context.view_layer.update()
        rot = cam.matrix_world.to_3x3().normalized()
        right, up, fwd = (np.array(v, dtype=np.float64) for v in (rot.col[0], rot.col[1], -rot.col[2]))
        u, v, d = pts @ right, pts @ up, pts @ fwd
        w, h = float(u.max() - u.min()), float(v.max() - v.min())
        r, cd = bpy.context.scene.render, cam.data
        aspect = (r.resolution_x * r.pixel_aspect_x) / (r.resolution_y * r.pixel_aspect_y)   # ширина / высота кадра
        fit = cd.sensor_fit if cd.sensor_fit != "AUTO" else ("HORIZONTAL" if aspect >= 1 else "VERTICAL")
        scale = max((max(w, h * aspect) if fit == "HORIZONTAL" else max(h, w / aspect)) * margin, 1e-6)
        cu = (u.max() + u.min()) / 2 - cd.shift_x * scale       # shift сдвигает кадр на shift × ortho_scale
        cv = (v.max() + v.min()) / 2 - cd.shift_y * scale
        cz = d.min() - 1.0 - cd.clip_start
        cam.location = Vector((right * cu + up * cv + fwd * cz).tolist())
        cd.ortho_scale = scale
        if d.max() - cz > cd.clip_end:
            cd.clip_end = float(d.max() - cz) * 1.01 + 0.1
    else:
        mn, mx = world_bbox(objects)
        corners = [Vector((x, y, z)) for x in (mn.x, mx.x) for y in (mn.y, mx.y) for z in (mn.z, mx.z)]
        corners += [Vector(p) for p in extra_points]
        dg = bpy.context.evaluated_depsgraph_get()
        loc, scale = cam.camera_fit_coords(dg, [c for v in corners for c in v])
        center = (mn + mx) / 2
        cam.location = center + (Vector(loc) - center) * margin
    bpy.context.view_layer.update()
    return cam


# ====================================================================== рендер и цвет

ENGINE_ALIASES = {"EEVEE": "BLENDER_EEVEE", "BLENDER_EEVEE_NEXT": "BLENDER_EEVEE", "EEVEE_NEXT": "BLENDER_EEVEE",
                  "WORKBENCH": "BLENDER_WORKBENCH", "Cycles": "CYCLES", "cycles": "CYCLES", "eevee": "BLENDER_EEVEE"}


def set_engine(name: str = "BLENDER_EEVEE", scene=None) -> str:
    """Движок рендера по имени или псевдониму (EEVEE, BLENDER_EEVEE_NEXT → BLENDER_EEVEE в 5.x). [5.2.2]

    Список движков RNA занижает (enum_items даёт один) — присваиваем и ловим TypeError со списком допустимых."""
    scene = scene or bpy.context.scene
    target = ENGINE_ALIASES.get(name, name)
    try:
        scene.render.engine = target
    except TypeError:
        if target == "BLENDER_EEVEE":          # 4.2–4.5
            try:
                scene.render.engine = "BLENDER_EEVEE_NEXT"
                return scene.render.engine
            except TypeError:
                pass
        raise ValueError(f"движок {name!r} не принят; допустимо {enum_values(scene.render, 'engine')}") from None
    return scene.render.engine


def set_color_management(view_transform: str = "AgX", look: str | None = None, *, exposure: float = 0.0,
                         gamma: float = 1.0, scene=None) -> dict:
    """View transform/look/экспозиция с проверкой по фактическому списку (5.2: Standard, ACES 1.3, ACES 2.0,
    Khronos PBR Neutral, AgX, Filmic, Filmic Log, False Color, Raw; looks 'AgX - Punchy' и др.). [5.2.2]

    Для совпадения с three.js: 'Khronos PBR Neutral' ↔ THREE.NeutralToneMapping, 'AgX' ↔ THREE.AgXToneMapping,
    'Standard' ↔ без тонмаппинга."""
    scene = scene or bpy.context.scene
    vs = scene.view_settings
    set_enum(vs, "view_transform", view_transform)
    if look is not None:
        set_enum(vs, "look", look)
    vs.exposure, vs.gamma = exposure, gamma
    return {"view_transform": vs.view_transform, "look": vs.look}


def render_still(filepath: str, *, resolution=(1024, 1024), engine: str | None = None, samples: int | None = None,
                 transparent: bool = False, file_format: str = "PNG", color_depth: str = "8", quality: int = 90,
                 camera=None, scene=None) -> dict:
    """Отрендерить кадр в файл (фон и GUI). Абсолютный путь, проверка камеры и результата. [5.2.2]

    samples: EEVEE — eevee.taa_render_samples (16 даёт зерно в мягких тенях, 64 — чисто); Cycles — samples на CPU
    с OIDN. В 5.x media_type ставится до file_format; форматы PNG/JPEG/WEBP/AVIF/OPEN_EXR пишутся в фоне."""
    scene = scene or bpy.context.scene
    r = scene.render
    if engine:
        set_engine(engine, scene)
    if camera is not None:
        scene.camera = camera
    if scene.camera is None:
        raise RuntimeError("render_still: у сцены нет камеры (scene.camera) — add_camera()")
    r.resolution_x, r.resolution_y = int(resolution[0]), int(resolution[1])
    r.resolution_percentage = 100
    r.film_transparent = transparent
    ims = r.image_settings
    if "media_type" in ims.bl_rna.properties and getattr(ims, "media_type", "IMAGE") != "IMAGE":
        ims.media_type = "IMAGE"
    set_enum(ims, "file_format", file_format)
    if file_format in ("PNG", "WEBP", "AVIF", "OPEN_EXR", "TIFF"):
        ims.color_mode = "RGBA" if transparent or file_format != "JPEG" else "RGB"
    if file_format in ("PNG", "OPEN_EXR", "TIFF") and "color_depth" in ims.bl_rna.properties:
        try:
            ims.color_depth = color_depth if file_format != "OPEN_EXR" else ("16" if color_depth == "8" else color_depth)
        except TypeError:
            pass
    if file_format in ("JPEG", "WEBP", "AVIF"):
        ims.quality = quality
    if samples is not None:
        if r.engine == "BLENDER_EEVEE" or r.engine.startswith("BLENDER_EEVEE"):
            scene.eevee.taa_render_samples = samples
        elif r.engine == "CYCLES":
            scene.cycles.samples = samples
    path = os.path.abspath(bpy.path.abspath(filepath))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r.filepath = path
    t0 = time.time()
    ret = bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    if ret != {"FINISHED"} or not os.path.exists(path):
        raise RuntimeError(f"render_still: {ret}, файл {path} не создан")
    return {"path": path, "sec": round(dt, 2), "bytes": os.path.getsize(path), "engine": r.engine}


# ====================================================================== экспорт

GLTF_DEFAULTS = {"export_format": "GLB", "export_yup": True}


def export_glb(filepath: str, objects=None, *, apply_modifiers: bool = True, **params) -> dict:
    """Экспорт GLB с проверкой параметров по RNA оператора (неизвестные — пропуск с предупреждением и подсказкой). [5.2.2]

    objects=None — вся сцена; иначе временно выделяются только эти объекты (+ дети) и use_selection=True, после —
    выделение восстанавливается. Путь делается абсолютным (относительный уходит в cwd процесса). Подробные пресеты
    и что переживает экспорт — kb/3d/08-export-gltf/."""
    op = bpy.ops.export_scene.gltf
    valid = {p.identifier for p in op.get_rna_type().properties}
    kw = dict(GLTF_DEFAULTS)
    kw["export_apply"] = apply_modifiers
    kw.update(params)
    for k in list(kw):
        if k not in valid:
            _warn(f"export_glb: параметра {k!r} нет в {op.idname_py()} 5.2 — пропущен; похожие {did_you_mean(k, valid, 4)}")
            kw.pop(k)
    path = os.path.abspath(bpy.path.abspath(filepath))
    if kw.get("export_format", "GLB") == "GLB" and not path.lower().endswith(".glb"):
        path += ".glb"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ensure_object_mode()
    vl = bpy.context.view_layer
    saved_sel = [o for o in vl.objects if o.select_get()]
    saved_act = vl.objects.active
    try:
        if objects is not None:
            chosen = set()
            for o in objects:
                chosen.add(o)
                chosen.update(o.children_recursive)
            for o in vl.objects:
                o.select_set(o in chosen)
            kw["use_selection"] = True
        ret = op(filepath=path, **kw)
    finally:
        for o in vl.objects:
            o.select_set(o in saved_sel)
        vl.objects.active = saved_act
    if ret != {"FINISHED"} or not os.path.exists(path):
        raise RuntimeError(f"export_glb: {ret}, файл {path} не создан")
    return {"path": path, "bytes": os.path.getsize(path), "params": kw}


# ====================================================================== UV

def uv_unwrap(ob, method: str = "SMART", *, angle_limit: float = 66.0, island_margin: float = 0.02,
              uv_name: str = "UVMap", cube_size: float = 1.0) -> str:
    """UV-развёртка меша в фоне и в GUI: SMART (smart_project), ANGLE_BASED / CONFORMAL (unwrap), LIGHTMAP
    (lightmap_pack), CUBE (cube_project). Вход в EDIT и выход — сами; выделение/активность восстанавливаются. [5.2.2]

    UV-операторы работают только в EDIT mode (в OBJECT — poll failed); uv.project_from_view в фоне недоступен.
    CUBE проецирует грани куба в один и тот же квадрат (острова перекрываются — годится для тайловой текстуры, не
    для запекания); для запекания — SMART или LIGHTMAP. Возвращает имя UV-слоя."""
    if ob.type != "MESH":
        raise ValueError(f"{ob.name}: нужен MESH")
    vl = bpy.context.view_layer
    if ob.name not in vl.objects:
        raise RuntimeError(f"{ob.name}: объект не в слое вида (не привязан к коллекции сцены?)")
    me = ob.data
    uv = me.uv_layers.get(uv_name) or me.uv_layers.new(name=uv_name)
    me.uv_layers.active = uv
    uv_name = uv.name        # запомнить строку: после mode_set EDIT↔OBJECT ссылка uv указывает на освобождённую память
    del uv
    ensure_object_mode()
    saved_sel = [o for o in vl.objects if o.select_get()]
    saved_act = vl.objects.active
    for o in saved_sel:
        o.select_set(False)
    ob.select_set(True)
    vl.objects.active = ob
    m = method.upper()
    try:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        if m == "SMART":
            r = bpy.ops.uv.smart_project(angle_limit=math.radians(angle_limit), island_margin=island_margin)
        elif m in ("ANGLE_BASED", "CONFORMAL", "MINIMUM_STRETCH"):
            r = bpy.ops.uv.unwrap(method=m, margin=island_margin)
        elif m == "LIGHTMAP":
            r = bpy.ops.uv.lightmap_pack()
        elif m == "CUBE":
            r = bpy.ops.uv.cube_project(cube_size=cube_size)
        else:
            raise ValueError(f"uv_unwrap: метод {method!r}; есть SMART, ANGLE_BASED, CONFORMAL, MINIMUM_STRETCH, LIGHTMAP, CUBE")
    finally:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        ob.select_set(False)
        for o in saved_sel:
            o.select_set(True)
        vl.objects.active = saved_act
    if r != {"FINISHED"}:
        raise RuntimeError(f"uv_unwrap({method}): {r}")
    return ob.data.uv_layers[uv_name].name


# ====================================================================== geometry nodes

def gn_tree(name: str, inputs=(), outputs=(("Geometry", "NodeSocketGeometry"),), *, geometry_input: bool = True):
    """Новое дерево Geometry Nodes с интерфейсом (API 4.0+: tree.interface.new_socket). Возвращает
    (tree, group_input, group_output). [5.2.2]

    inputs: кортежи (name, socket_type[, default[, min, max]]) или dict(name=, socket_type=, default=, min=, max=,
    subtype=, description=). socket_type — только базовые типы (NodeSocketFloat, …Int, …Bool, …Vector, …Color,
    …Rotation, …Matrix, …String, …Menu, …Geometry, …Object, …Collection, …Image, …Material); «FloatFactor» —
    через subtype='FACTOR'."""
    t = bpy.data.node_groups.new(name, "GeometryNodeTree")
    if geometry_input:
        t.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for spec in inputs:
        if isinstance(spec, dict):
            d = dict(spec)
        else:
            d = {"name": spec[0], "socket_type": spec[1]}
            if len(spec) > 2:
                d["default"] = spec[2]
            if len(spec) > 4:
                d["min"], d["max"] = spec[3], spec[4]
        s = t.interface.new_socket(name=d["name"], in_out="INPUT", socket_type=d["socket_type"],
                                   description=d.get("description", ""))
        if "subtype" in d:
            s.subtype = d["subtype"]
        if "min" in d:
            s.min_value = d["min"]
        if "max" in d:
            s.max_value = d["max"]
        if d.get("default") is not None:
            s.default_value = d["default"]
    for spec in outputs:
        t.interface.new_socket(name=spec[0], in_out="OUTPUT", socket_type=spec[1])
    gi = t.nodes.new("NodeGroupInput")
    go = t.nodes.new("NodeGroupOutput")
    gi.location, go.location = (-800, 0), (600, 0)
    return t, gi, go


def gn_inputs(mod) -> dict:
    """{имя сокета: identifier} входов модификатора NODES (5.2: mod.properties.inputs; < 5.2 — интерфейс дерева). [5.2.2]"""
    if hasattr(mod, "properties") and mod.properties is not None:
        return {p.name: p.identifier for p in mod.properties.inputs.bl_rna.properties
                if p.identifier not in ("rna_type", "name")}
    return {i.name: i.identifier for i in mod.node_group.interface.items_tree
            if i.item_type == "SOCKET" and i.in_out == "INPUT"}


def gn_set_input(mod, key: str, value=None, *, attribute: str | None = None):
    """Задать вход модификатора GN по имени сокета или identifier; attribute='name' — брать из атрибута. [5.2.2]

    5.2: mod.properties.inputs.<id>.value / .type='ATTRIBUTE' / .attribute_name (старый mod['Socket_N'] → TypeError);
    < 5.2: IDProperty mod['Socket_N'], mod['Socket_N_use_attribute'], mod['Socket_N_attribute_name'].
    После присвоения вызывается object.update_tag(): в 5.2.2 без него результат не пересчитывается."""
    names = gn_inputs(mod)
    ident = key if key in names.values() else names.get(key) or names.get(key.replace("_", " "))
    if ident is None:
        raise KeyError(f"модификатор {mod.name}: нет входа {key!r}; есть {list(names)}")
    if hasattr(mod, "properties") and mod.properties is not None:
        item = getattr(mod.properties.inputs, ident)
        if attribute is not None:
            item.type = "ATTRIBUTE"
            item.attribute_name = attribute
        else:
            if "type" in item.bl_rna.properties and item.type != "VALUE":
                item.type = "VALUE"
            item.value = value
    else:                                   # Blender 4.x
        if attribute is not None:
            mod[ident + "_use_attribute"] = True
            mod[ident + "_attribute_name"] = attribute
        else:
            mod[ident] = value
    mod.id_data.update_tag()
    return ident


def gn_modifier(ob, tree, name: str | None = None, **values):
    """Модификатор NODES с деревом tree и входами по имени сокета (пробелы в имени можно писать как _). [5.2.2]"""
    m = ob.modifiers.new(name or tree.name, "NODES")
    m.node_group = tree
    for k, v in values.items():
        gn_set_input(m, k, v)
    ob.update_tag()
    return m
