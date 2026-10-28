#!/usr/bin/env python3
"""bpy_probe.py — справочник по Python API, который отвечает сам Blender (JSON). Замена MCP-инструментам
`bpy_api_lookup` и `describe_node_type` без окна и без MCP; плюс то, чего в них нет: доступность сокетов,
фактические значения динамических перечислений, устаревшие (deprecated) свойства, поиск по API.

Запуск — два способа (оба в фоне, --factory-startup, ничего не сохраняют):

  python3 scripts/3d/bpy_probe.py <команда> [аргументы] [--out file.json]
      сам запускает Blender без окна и печатает чистый JSON (удобно агенту: одна команда, парсится json.loads);
  python3 scripts/3d/blender_run.py scripts/3d/bpy_probe.py -- <команда> [аргументы] [--out file.json]
      через общий запускатель (журнал в $DDD_HOME/out/3d/logs/); JSON — между строками
      BPY_PROBE_JSON_BEGIN / BPY_PROBE_JSON_END. Вывод blender_run обрезается до 400 строк — для больших
      ответов (type Object, nodes GeometryNodeTree) добавляй --out.

Команды:
  op <cat.name | bpy.ops.cat.name>       параметры оператора: identifier, тип, умолчание, enum-значения,
                                         флаги; poll() в фоне без окна (False → в фоне без override не пойдёт)
  ops <cat>                              все операторы категории (object, mesh, uv, export_scene, ...) с poll()
  type <Type>                            свойства и функции bpy.types.Type (--own — без унаследованных) +
                                         Python-члены (from_pydata и т. п.)
  type <Type.prop>                       одно свойство; enum — identifier, name, description каждого значения
  type <Type.func>                       функция: параметры и возвращаемые значения
  node <bl_idname> [prop=value ...]      сокеты ноды после переопределений свойств (как describe_node_type):
                                         index, identifier, name, type, bl_idname, default, enabled (доступен
                                         ли при этих свойствах), дубли имён; --tree ShaderNodeTree|GeometryNodeTree|...
  nodes <TreeType> [фильтр]              все ноды, которые создаются в дереве типа ShaderNodeTree /
                                         GeometryNodeTree / CompositorNodeTree / TextureNodeTree;
                                         menu=false — ноды нет в меню Add (устаревшая или служебная)
  enum <путь>                            фактические значения перечисления на живом экземпляре (RNA занижает
                                         динамические): scene.render.engine, scene.view_settings.view_transform,
                                         scene.view_settings.look, object.rotation_mode, material.surface_render_method…
                                         Корни: scene, context, data, world, object, mesh, material, light, camera,
                                         curve, text, image, node_tree, preferences (временные экземпляры создаются
                                         сами), например image.colorspace_settings.name
  modifier [TYPE|ClassName]              без аргумента — все типы модификаторов и их классы; с аргументом —
                                         свойства модификатора (SUBSURF, BEVEL, NODES, WEIGHTED_NORMAL, ...)
  sockets [TreeType]                     допустимые socket_type для tree.interface.new_socket
  search <текст> [--limit N]             типы bpy.types, операторы bpy.ops и члены типов (свойства/функции),
                                         в имени которых есть текст (без учёта регистра)
  deprecated [фильтр]                    все свойства и параметры RNA/операторов, помеченные устаревшими в этой
                                         версии: заметка, версия пометки, версия удаления
  env                                    версии Blender/Python/numpy/glTF-экспортёра, движки, view transform,
                                         looks, аддоны, пути

Примеры:
  python3 scripts/3d/bpy_probe.py node ShaderNodeMix data_type=RGBA
  python3 scripts/3d/bpy_probe.py node ShaderNodeBsdfPrincipled
  python3 scripts/3d/bpy_probe.py op export_scene.gltf --out /tmp/gltf_params.json
  python3 scripts/3d/bpy_probe.py type Object.rotation_mode
  python3 scripts/3d/bpy_probe.py enum scene.render.engine
  python3 scripts/3d/bpy_probe.py nodes GeometryNodeTree instance
  python3 scripts/3d/bpy_probe.py search smooth
  python3 scripts/3d/bpy_probe.py deprecated
  python3 scripts/3d/blender_run.py scripts/3d/bpy_probe.py -- node ShaderNodeMix data_type=RGBA

Коды выхода: 0 — ответ получен; 3 — ответ с полем "error" (неизвестный тип/оператор; есть did_you_mean);
1 — Blender упал; 124 — таймаут. Проверено: Blender 5.2.2 LTS.
"""
import ast
import json
import math
import os
import re
import shutil
import subprocess
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import kbpaths  # noqa: E402

MARK_BEGIN = "BPY_PROBE_JSON_BEGIN"
MARK_END = "BPY_PROBE_JSON_END"

try:
    import bpy  # noqa: F401  — есть только внутри Blender
except ImportError:
    bpy = None


# ------------------------------------------------------------------ формат вывода (общий для обоих режимов)

def dumps_compact(o, level=0, width=160):
    """JSON, где каждый элемент списка — одна строка (удобно читать глазами и грепать; валидный JSON)."""
    pad = " " * level
    one = json.dumps(o, ensure_ascii=False)
    if not isinstance(o, (dict, list)) or len(one) <= width or not o:
        return one
    if isinstance(o, dict):
        items = [f'{pad} {json.dumps(k, ensure_ascii=False)}: {dumps_compact(v, level + 1, width)}' for k, v in o.items()]
        return "{\n" + ",\n".join(items) + "\n" + pad + "}"
    out = []
    for x in o:
        s = json.dumps(x, ensure_ascii=False)
        out.append(pad + " " + (s if len(s) <= 600 or not isinstance(x, (dict, list)) else dumps_compact(x, level + 1, width)))
    return "[\n" + ",\n".join(out) + "\n" + pad + "]"


# ------------------------------------------------------------------ режим «снаружи»: запустить Blender

def outer_main(args):
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    timeout = 180
    user_prefs = False
    rest = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--timeout":
            timeout = int(args[i + 1]); i += 2; continue
        if a == "--user-prefs":
            user_prefs = True; i += 1; continue
        rest.append(a); i += 1
    blender = kbpaths.blender()
    cmd = [blender, "-b"] + ([] if user_prefs else ["--factory-startup"]) + [
        "--python-exit-code", "1", "--python", os.path.abspath(__file__), "--"] + rest
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(json.dumps({"error": f"timeout {timeout}s"}))
        return 124
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    m = re.search(re.escape(MARK_BEGIN) + r"\n(.*?)\n" + re.escape(MARK_END), out, re.S)
    if not m:
        print(out[-6000:])
        print(json.dumps({"error": "no JSON from Blender", "exit": r.returncode}))
        return r.returncode or 1
    data = json.loads(m.group(1))
    print(dumps_compact(data))
    return 3 if isinstance(data, dict) and "error" in data else 0


if bpy is None:
    if __name__ == "__main__":
        sys.exit(outer_main(sys.argv[1:]))
    raise SystemExit(0)


# ------------------------------------------------------------------ режим «внутри Blender»

import warnings  # noqa: E402

warnings.filterwarnings("ignore", category=DeprecationWarning)

TREE_TYPES = ("ShaderNodeTree", "GeometryNodeTree", "CompositorNodeTree", "TextureNodeTree")
TMP = "__bpy_probe_tmp__"


def jsonable(v, depth=0):
    """Значение RNA → JSON: массивы и mathutils → списки, float округлить, ID → имя, set → список."""
    if depth > 3:
        return repr(v)
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):
        if math.isinf(v) or math.isnan(v):
            return str(v)
        return round(v, 6)
    if isinstance(v, (set, frozenset)):
        return sorted(jsonable(x, depth + 1) for x in v)
    if hasattr(v, "bl_rna") and hasattr(v, "name") and isinstance(getattr(v, "name", None), str):
        return {"struct": v.bl_rna.identifier, "name": v.name}
    if hasattr(v, "bl_rna"):
        return {"struct": v.bl_rna.identifier}
    try:
        seq = list(v)
    except TypeError:
        return repr(v)
    return [jsonable(x, depth + 1) for x in seq]


_BIG = 1.0e37


def unbounded(rng):
    """Диапазон без ограничений (±FLT_MAX, ±INT_MAX) — не печатаем, чтобы не шуметь."""
    lo, hi = rng
    try:
        return (lo <= -_BIG or lo <= -2147483647) and (hi >= _BIG or hi >= 2147483647)
    except TypeError:
        return False


def describe_prop(p, owner=None, full_enum=False):
    d = {"identifier": p.identifier, "name": p.name, "type": p.type}
    if getattr(p, "subtype", "NONE") not in ("NONE", ""):
        d["subtype"] = p.subtype
    if getattr(p, "unit", "NONE") not in ("NONE", ""):
        d["unit"] = p.unit
    for flag, key in (("is_readonly", "readonly"), ("is_required", "required"), ("is_output", "output"),
                      ("is_never_none", "never_none"), ("is_hidden", "hidden"), ("is_skip_save", "skip_save")):
        if getattr(p, flag, False):
            d[key] = True
    if getattr(p, "is_deprecated", False):
        d["deprecated"] = {"note": p.deprecated_note, "since": jsonable(p.deprecated_version),
                           "removal": jsonable(p.deprecated_removal_version)}
    t = p.type
    try:
        if t == "ENUM":
            d["enum_flag"] = bool(p.is_enum_flag)
            d["default"] = sorted(p.default_flag) if p.is_enum_flag else p.default
            items = list(p.enum_items)
            if full_enum:
                d["items"] = [{"identifier": i.identifier, "name": i.name, "description": i.description} for i in items]
            else:
                d["items"] = [i.identifier for i in items]
            static = [i.identifier for i in p.enum_items_static]
            if static != [i.identifier for i in items]:
                d["items_static"] = static
        elif t in ("FLOAT", "INT", "BOOLEAN"):
            n = getattr(p, "array_length", 0)
            if n:
                d["array_length"] = n
                dims = [x for x in getattr(p, "array_dimensions", []) if x]
                if len(dims) > 1:
                    d["array_dimensions"] = dims
                d["default"] = jsonable(p.default_array)
            else:
                d["default"] = jsonable(p.default)
            if t != "BOOLEAN":
                rng = [jsonable(p.hard_min), jsonable(p.hard_max)]
                if not unbounded(rng):
                    d["range"] = rng
                soft = [jsonable(p.soft_min), jsonable(p.soft_max)]
                if soft != rng and not unbounded(soft):
                    d["soft_range"] = soft
        elif t == "STRING":
            d["default"] = p.default
        elif t in ("POINTER", "COLLECTION"):
            ft = getattr(p, "fixed_type", None)
            if ft is not None:
                d["fixed_type"] = ft.identifier
    except Exception as e:  # чтение метаданных не должно ронять ответ
        d["meta_error"] = str(e)
    if owner is not None and t != "COLLECTION":
        try:
            d["value"] = jsonable(getattr(owner, p.identifier))
        except Exception:
            pass
        if t == "ENUM" and not p.is_readonly:
            dyn = enum_runtime(owner, p.identifier)
            if dyn is not None and dyn != [i.identifier for i in p.enum_items]:
                d["items_runtime"] = dyn
    if p.description:
        d["description"] = p.description
    return d


def describe_func(f):
    return {"identifier": f.identifier, "description": f.description, "use_self": getattr(f, "use_self", True),
            "parameters": [describe_prop(p) for p in f.parameters if not p.is_output],
            "returns": [describe_prop(p) for p in f.parameters if p.is_output]}


def enum_runtime(owner, attr):
    """Фактический список значений перечисления: присвоить заведомо неверное → TypeError перечисляет допустимые.

    Нужен для динамических перечислений (движки рендера, view transform, look и т. п.), которые RNA занижает.
    Ничего не меняет: неверное присваивание отклоняется до записи."""
    try:
        cur = getattr(owner, attr)
    except Exception:
        return None
    probe = {"__bpy_probe_invalid__"} if isinstance(cur, set) else "__bpy_probe_invalid__"
    try:
        setattr(owner, attr, probe)
    except TypeError as e:
        m = re.search(r"not found in \((.*)\)", str(e))
        if m:
            try:
                v = ast.literal_eval("(" + m.group(1) + ",)")
                return [x for x in v if isinstance(x, str)]
            except Exception:
                return None
        return None
    except Exception:
        return None
    try:  # вдруг принялось (не должно) — вернуть как было
        setattr(owner, attr, cur)
    except Exception:
        pass
    return None


def did_you_mean(name, pool, n=15):
    """Сначала близкие по написанию (difflib), затем содержащие подстроку; без учёта регистра."""
    import difflib
    pool = list(pool)
    low = {x.lower(): x for x in pool}
    close = [low[x] for x in difflib.get_close_matches(name.lower(), list(low), n=n, cutoff=0.6)]
    sub = sorted(x for x in pool if name.lower() in x.lower() and x not in close)
    return (close + sub)[:n]


def all_type_names():
    return [n for n in dir(bpy.types) if not n.startswith("_")]


def op_categories():
    return [c for c in dir(bpy.ops) if not c.startswith("_")]


# ---------------- op / ops

def cmd_op(path, **kw):
    q = path.strip()
    q = q[4:] if q.startswith("bpy.") else q
    q = q[4:] if q.startswith("ops.") else q
    parts = [p.split("(")[0] for p in q.split(".") if p]
    if len(parts) < 2:
        return {"error": f"нужно <категория>.<имя>, получено {path!r}"}
    cat, name = parts[0], parts[1]
    grp = getattr(bpy.ops, cat, None)
    op = getattr(grp, name, None) if grp is not None else None
    try:
        rna = op.get_rna_type() if op is not None else None
    except Exception:
        rna = None
    if rna is None:
        pool = []
        for c in op_categories():
            pool += [f"{c}.{n}" for n in dir(getattr(bpy.ops, c)) if not n.startswith("_")]
        return {"error": f"нет оператора bpy.ops.{cat}.{name}", "did_you_mean": did_you_mean(name, pool)}
    try:
        poll = bool(op.poll())
    except Exception as e:
        poll = f"error: {e}"
    params = [describe_prop(p, full_enum=kw.get("full")) for p in rna.properties if p.identifier != "rna_type"]
    return {"kind": "operator", "call": f"bpy.ops.{cat}.{name}", "bl_idname": op.idname(), "label": rna.name,
            "description": rna.description, "poll_in_background": poll,
            "bl_options": sorted(getattr(op, "bl_options", set()) or []),
            "parameters": params}


def cmd_ops(cat, **kw):
    grp = getattr(bpy.ops, cat, None)
    if grp is None:
        return {"error": f"нет категории bpy.ops.{cat}", "did_you_mean": did_you_mean(cat, op_categories()),
                "categories": op_categories()}
    res = []
    for n in sorted(x for x in dir(grp) if not x.startswith("_")):
        op = getattr(grp, n)
        try:
            rna = op.get_rna_type()
            poll = bool(op.poll())
            res.append({"op": f"{cat}.{n}", "label": rna.name, "poll_in_background": poll,
                        "params": len(rna.properties) - 1})
        except Exception as e:
            res.append({"op": f"{cat}.{n}", "error": str(e)})
    return {"kind": "operator_category", "category": cat, "count": len(res), "operators": res}


# ---------------- type

def python_members(cls, rna):
    names = set(rna.properties.keys()) | set(rna.functions.keys())
    out = []
    for a in dir(cls):
        if a.startswith("_") or a in names or a in ("bl_rna", "rna_type"):
            continue
        out.append(a)
    return sorted(out)


def cmd_type(q, **kw):
    q = q.strip()
    for pre in ("bpy.types.", "types."):
        if q.startswith(pre):
            q = q[len(pre):]
    parts = [p for p in q.split(".") if p]
    cls = getattr(bpy.types, parts[0], None) if parts else None
    if cls is None or not hasattr(cls, "bl_rna"):
        return {"error": f"нет типа bpy.types.{parts[0] if parts else q}",
                "did_you_mean": did_you_mean(parts[0] if parts else q, all_type_names())}
    rna = cls.bl_rna
    if len(parts) == 1:
        base = rna.base
        base_props = set(base.properties.keys()) if (base is not None and kw.get("own")) else set()
        base_funcs = set(base.functions.keys()) if (base is not None and kw.get("own")) else set()
        return {"kind": "type", "identifier": rna.identifier, "name": rna.name, "description": rna.description,
                "base": base.identifier if base is not None else None,
                "own_only": bool(kw.get("own")),
                "properties": [describe_prop(p, full_enum=kw.get("full")) for p in rna.properties
                               if p.identifier != "rna_type" and p.identifier not in base_props],
                "functions": [describe_func(f) for f in rna.functions if f.identifier not in base_funcs],
                "python_members": python_members(cls, rna)}
    member = parts[1]
    p = rna.properties.get(member)
    if p is not None:
        d = describe_prop(p, full_enum=True)
        d.update(kind="property", owner_type=rna.identifier)
        return d
    f = rna.functions.get(member)
    if f is not None:
        d = describe_func(f)
        d.update(kind="function", owner_type=rna.identifier)
        return d
    if hasattr(cls, member):
        obj = getattr(cls, member)
        return {"kind": "python_member", "owner_type": rna.identifier, "identifier": member,
                "python_type": type(obj).__name__, "doc": (getattr(obj, "__doc__", None) or "").strip()[:2000]}
    pool = list(rna.properties.keys()) + list(rna.functions.keys()) + python_members(cls, rna)
    return {"error": f"у {rna.identifier} нет члена {member!r}", "did_you_mean": did_you_mean(member, pool)}


# ---------------- node / nodes

BASE_NODE_PROPS = None


def base_node_props():
    global BASE_NODE_PROPS
    if BASE_NODE_PROPS is None:
        BASE_NODE_PROPS = set(bpy.types.Node.bl_rna.properties.keys())
    return BASE_NODE_PROPS


def tree_order(idname):
    if idname.startswith(("GeometryNode", "FunctionNode")):
        return ["GeometryNodeTree", "ShaderNodeTree", "CompositorNodeTree", "TextureNodeTree"]
    if idname.startswith("CompositorNode"):
        return ["CompositorNodeTree", "GeometryNodeTree", "ShaderNodeTree", "TextureNodeTree"]
    if idname.startswith("TextureNode"):
        return ["TextureNodeTree", "ShaderNodeTree", "GeometryNodeTree", "CompositorNodeTree"]
    return list(TREE_TYPES)


def make_node(idname, tree_type=None):
    """Создать ноду во временном дереве. Возвращает (node, tree, tree_type, cleanup, attempts)."""
    attempts = []
    for tt in ([tree_type] if tree_type else tree_order(idname)):
        tree = None
        try:
            tree = bpy.data.node_groups.new(TMP, tt)
            node = tree.nodes.new(idname)
            return node, tree, tt, (lambda t=tree: bpy.data.node_groups.remove(t)), attempts
        except Exception as e:
            attempts.append(f"{tt}: {e}")
            if tree is not None:
                bpy.data.node_groups.remove(tree)
        if tt == "ShaderNodeTree":  # некоторые шейдерные ноды живут только в материале/мире (выходы)
            for kind in ("materials", "worlds"):
                idb = getattr(bpy.data, kind).new(TMP)
                try:
                    if idb.node_tree is None:
                        idb.use_nodes = True
                    node = idb.node_tree.nodes.new(idname)
                    return node, idb.node_tree, f"{tt} ({kind[:-1]})", (
                        lambda i=idb, k=kind: getattr(bpy.data, k).remove(i)), attempts
                except Exception as e:
                    attempts.append(f"{tt} in {kind[:-1]}: {e}")
                    getattr(bpy.data, kind).remove(idb)
    return None, None, None, None, attempts


def describe_socket(i, s):
    d = {"index": i, "identifier": s.identifier, "name": s.name, "type": s.type, "bl_idname": s.bl_idname}
    if not s.enabled:
        d["enabled"] = False
    if getattr(s, "is_unavailable", False) and s.enabled:
        d["unavailable"] = True
    if s.hide:
        d["hide"] = True
    if s.hide_value:
        d["hide_value"] = True
    if s.is_multi_input:
        d["multi_input"] = True
    if hasattr(s, "default_value"):
        try:
            d["default"] = jsonable(s.default_value)
        except Exception:
            pass
        try:
            p = s.bl_rna.properties["default_value"]
            if p.type in ("FLOAT", "INT"):
                rng = [jsonable(p.hard_min), jsonable(p.hard_max)]
                if not unbounded(rng):
                    d["range"] = rng
            if p.type == "ENUM":
                d["items"] = enum_runtime(s, "default_value") or [x.identifier for x in p.enum_items]
        except Exception:
            pass
    if getattr(s, "description", ""):
        d["description"] = s.description
    return d


def dup_names(sockets):
    seen = {}
    for s in sockets:
        seen.setdefault(s.name, []).append(s.identifier)
    return {k: v for k, v in seen.items() if len(v) > 1}


def parse_value(v):
    try:
        return ast.literal_eval(v)
    except Exception:
        return v


def cmd_node(idname, *overrides, **kw):
    cls = getattr(bpy.types, idname, None)
    if cls is None or not (isinstance(cls, type) and issubclass(cls, bpy.types.Node)):
        pool = [n for n in all_type_names() if "Node" in n]
        return {"error": f"нет типа ноды {idname}", "did_you_mean": did_you_mean(idname, pool)}
    node, tree, tt, cleanup, attempts = make_node(idname, kw.get("tree"))
    if node is None:
        return {"error": f"не удалось создать {idname} ни в одном дереве", "attempts": attempts}
    try:
        applied, warn = {}, []
        for ov in overrides:
            if "=" not in ov:
                warn.append(f"пропущено {ov!r}: нужно свойство=значение")
                continue
            k, v = ov.split("=", 1)
            val = parse_value(v)
            try:
                setattr(node, k, val)
                applied[k] = val
            except Exception as e:
                msg = str(e)
                if isinstance(e, TypeError):
                    items = enum_runtime(node, k)
                    if items:
                        msg += f" | допустимо: {items}"
                warn.append(f"{k}={v!r}: {msg}")
        props = [describe_prop(p, owner=node, full_enum=kw.get("full")) for p in node.bl_rna.properties
                 if p.identifier not in base_node_props()]
        res = {"kind": "node", "bl_idname": idname, "label": node.bl_label, "type": node.type,
               "tree": tt, "description": getattr(node, "bl_description", "") or cls.bl_rna.description,
               "overrides": applied, "properties": props,
               "inputs": [describe_socket(i, s) for i, s in enumerate(node.inputs)],
               "outputs": [describe_socket(i, s) for i, s in enumerate(node.outputs)]}
        di, do = dup_names(node.inputs), dup_names(node.outputs)
        ena_i = dup_names([s for s in node.inputs if s.enabled])
        ena_o = dup_names([s for s in node.outputs if s.enabled])
        if di or do:
            res["duplicate_names"] = {"inputs": di, "outputs": do,
                                      "among_enabled": {"inputs": ena_i, "outputs": ena_o},
                                      "hint": "5.2: inputs['Имя'] ищет по ИМЕНИ среди доступных (enabled) сокетов — сначала "
                                              "задай data_type/operation, потом бери сокет; inputs['identifier'] даёт KeyError, "
                                              "если identifier != имени (даже для доступного) — ищи "
                                              "next(s for s in node.inputs if s.identifier == ID); индекс доступность не учитывает; "
                                              "ссылка, взятая до смены режима, указывает на ставший недоступным сокет (link.is_valid=False)"}
        if warn:
            res["warnings"] = warn
        if attempts:
            res["attempts"] = attempts
        return res
    finally:
        cleanup()


def add_menu_ids():
    """bl_idname нод, упомянутых в меню Add (скрипты bl_ui/node_add_menu_*.py)."""
    import bl_ui
    d = os.path.dirname(bl_ui.__file__)
    ids = set()
    for fn in os.listdir(d):
        if fn.startswith("node_add_menu") and fn.endswith(".py"):
            txt = open(os.path.join(d, fn), encoding="utf-8").read()
            ids |= set(re.findall(r"[\"']((?:Shader|Geometry|Function|Compositor|Texture)Node\w+|Node\w+)[\"']", txt))
    return ids


def node_classes():
    out = []
    for n in all_type_names():
        c = getattr(bpy.types, n, None)
        try:
            if isinstance(c, type) and issubclass(c, bpy.types.Node):
                out.append(n)
        except Exception:
            pass
    return out


def cmd_nodes(tree_type="ShaderNodeTree", flt=None, **kw):
    if tree_type not in TREE_TYPES:
        return {"error": f"тип дерева {tree_type!r}", "did_you_mean": list(TREE_TYPES)}
    menu = add_menu_ids()
    tree = bpy.data.node_groups.new(TMP, tree_type)
    mat = None
    res = []
    try:
        for n in sorted(node_classes()):
            node = None
            where = "group"
            try:
                node = tree.nodes.new(n)
            except Exception:
                if tree_type == "ShaderNodeTree":
                    if mat is None:
                        mat = bpy.data.materials.new(TMP)
                    try:
                        node = mat.node_tree.nodes.new(n)
                        where = "material"
                    except Exception:
                        node = None
            if node is None:
                continue
            item = {"bl_idname": n, "label": node.bl_label, "type": node.type, "in": len(node.inputs),
                    "out": len(node.outputs), "menu": n in menu}
            if where != "group":
                item["only_in"] = where
            res.append(item)
            node.id_data.nodes.remove(node)
    finally:
        bpy.data.node_groups.remove(tree)
        if mat is not None:
            bpy.data.materials.remove(mat)
    if flt:
        f = flt.lower()
        res = [r for r in res if f in r["bl_idname"].lower() or f in r["label"].lower()]
    return {"kind": "node_list", "tree": tree_type, "filter": flt, "count": len(res),
            "note": "menu=false: нода создаётся, но её нет в меню Add (устаревшая/служебная) — не выбирай такие без причины",
            "nodes": res}


# ---------------- enum

def temp_roots():
    made = []

    def new(coll, *a):
        idb = getattr(bpy.data, coll).new(TMP, *a)
        made.append((coll, idb))
        return idb
    scene = bpy.context.scene
    roots = {"bpy": bpy, "C": bpy.context, "D": bpy.data, "context": bpy.context, "data": bpy.data,
             "scene": scene, "view_layer": bpy.context.view_layer, "preferences": bpy.context.preferences}

    class Lazy(dict):
        def __missing__(self, key):
            if key == "world":
                w = scene.world or new("worlds")
                self[key] = w
            elif key == "mesh":
                self[key] = new("meshes")
            elif key == "object":
                me = new("meshes")
                self[key] = new("objects", me)
            elif key == "material":
                self[key] = new("materials")
            elif key == "light":
                self[key] = new("lights", "AREA")
            elif key == "camera":
                self[key] = new("cameras")
            elif key == "curve":
                self[key] = new("curves", "CURVE")
            elif key == "text":
                self[key] = new("curves", "FONT")
            elif key == "image":
                self[key] = new("images", 8, 8)
            elif key == "node_tree":
                self[key] = new("node_groups", "ShaderNodeTree")
            else:
                raise KeyError(key)
            return self[key]
    ns = Lazy(roots)

    def cleanup():
        for coll, idb in reversed(made):
            try:
                getattr(bpy.data, coll).remove(idb)
            except Exception:
                pass
    return ns, cleanup


def cmd_enum(path, **kw):
    path = path.strip()
    if path.startswith("bpy.context."):
        path = "context." + path[len("bpy.context."):]
    if path.startswith("bpy.data."):
        path = "data." + path[len("bpy.data."):]
    if "." not in path:
        return {"error": "нужен путь вида scene.render.engine"}
    owner_expr, attr = path.rsplit(".", 1)
    ns, cleanup = temp_roots()
    try:
        try:
            owner = eval(owner_expr, {"__builtins__": {}}, ns)
        except Exception as e:
            return {"error": f"не удалось вычислить {owner_expr!r}: {e}",
                    "roots": ["scene", "context", "data", "view_layer", "preferences", "world", "object", "mesh",
                              "material", "light", "camera", "curve", "text", "image", "node_tree"]}
        p = owner.bl_rna.properties.get(attr)
        if p is None:
            return {"error": f"у {owner.bl_rna.identifier} нет свойства {attr!r}",
                    "did_you_mean": did_you_mean(attr, owner.bl_rna.properties.keys())}
        if p.type != "ENUM":
            return {"error": f"{attr} — не перечисление, а {p.type}", "property": describe_prop(p, owner=owner)}
        rna_items = [{"identifier": i.identifier, "name": i.name, "description": i.description} for i in p.enum_items]
        runtime = enum_runtime(owner, attr)
        return {"kind": "enum", "path": path, "owner_type": owner.bl_rna.identifier, "current": jsonable(getattr(owner, attr)),
                "enum_flag": bool(p.is_enum_flag), "rna_items": rna_items,
                "runtime_items": runtime,
                "dynamic": runtime is not None and runtime != [i["identifier"] for i in rna_items],
                "note": "runtime_items — что реально принимает присваивание в этой сборке (из текста TypeError); "
                        "rna_items может быть занижен для динамических перечислений"}
    finally:
        cleanup()


# ---------------- modifier

def modifier_types():
    return [i.identifier for i in bpy.types.Modifier.bl_rna.properties["type"].enum_items]


def cmd_modifier(what=None, **kw):
    me = bpy.data.meshes.new(TMP)
    ob = bpy.data.objects.new(TMP, me)
    try:
        if not what:
            res = []
            for t in modifier_types():
                try:
                    m = ob.modifiers.new("m", t)
                except Exception as e:
                    res.append({"type": t, "mesh": False, "error": str(e).splitlines()[0][:120]})
                    continue
                if m is None:  # 5.2: несовместимый с мешем тип — new() молча возвращает None
                    res.append({"type": t, "mesh": False, "note": "modifiers.new() вернул None на меше"})
                    continue
                res.append({"type": t, "class": m.bl_rna.identifier})
                ob.modifiers.remove(m)
            return {"kind": "modifier_list", "count": len(res), "modifiers": res,
                    "note": "mesh=false — тип не для меша (Grease Pencil, Volume); modifiers.new() на меше вернёт None"}
        types = modifier_types()
        t = what
        if what not in types:  # имя класса?
            t = None
            for tt in types:
                try:
                    m = ob.modifiers.new("m", tt)
                except Exception:
                    continue
                if m is None:
                    continue
                cls = m.bl_rna.identifier
                ob.modifiers.remove(m)
                if cls.lower() == what.lower():
                    t = tt
                    break
            if t is None:
                return {"error": f"нет модификатора {what!r}", "did_you_mean": did_you_mean(what, types)}
        try:
            m = ob.modifiers.new("m", t)
        except Exception as e:
            return {"error": f"{t} не добавляется к мешу: {e}"}
        if m is None:
            return {"error": f"{t} не добавляется к мешу: modifiers.new() вернул None (тип для Grease Pencil/Volume)"}
        base = set(bpy.types.Modifier.bl_rna.properties.keys())
        return {"kind": "modifier", "type": t, "class": m.bl_rna.identifier,
                "properties": [describe_prop(p, owner=m, full_enum=kw.get("full")) for p in m.bl_rna.properties
                               if p.identifier not in base],
                "common": sorted(base - {"rna_type"})}
    finally:
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)


# ---------------- sockets (интерфейс групп)

def cmd_sockets(tree_type="GeometryNodeTree", **kw):
    tree = bpy.data.node_groups.new(TMP, tree_type)
    try:
        f = bpy.types.NodeTreeInterface.bl_rna.functions["new_socket"]
        params = [describe_prop(p) for p in f.parameters if not p.is_output]
        valid = None
        try:
            tree.interface.new_socket(name="x", in_out="INPUT", socket_type="__bpy_probe_invalid__")
        except TypeError as e:
            m = re.search(r"not found in \((.*)\)", str(e))
            valid = list(ast.literal_eval("(" + m.group(1) + ",)")) if m else str(e)
        except Exception as e:
            valid = f"{type(e).__name__}: {e}"
        return {"kind": "interface_sockets", "tree": tree_type, "socket_types": valid,
                "new_socket_parameters": params,
                "new_panel": describe_func(bpy.types.NodeTreeInterface.bl_rna.functions["new_panel"])}
    finally:
        bpy.data.node_groups.remove(tree)


# ---------------- search

def cmd_search(text, limit=60, **kw):
    t = text.lower()
    types = [n for n in all_type_names() if t in n.lower()]
    ops = []
    for c in op_categories():
        for n in dir(getattr(bpy.ops, c)):
            if not n.startswith("_") and (t in n.lower() or t in c.lower()):
                ops.append(f"bpy.ops.{c}.{n}")
    members = []
    for n in all_type_names():
        cls = getattr(bpy.types, n, None)
        rna = getattr(cls, "bl_rna", None)
        if rna is None:
            continue
        base = rna.base
        bprops = set(base.properties.keys()) if base is not None else set()
        bfuncs = set(base.functions.keys()) if base is not None else set()
        for k in rna.properties.keys():
            if t in k.lower() and k not in bprops:
                p = rna.properties[k]
                members.append(f"{n}.{k}" + (" [deprecated]" if getattr(p, "is_deprecated", False) else ""))
        for k in rna.functions.keys():
            if t in k.lower() and k not in bfuncs:
                members.append(f"{n}.{k}()")
    limit = int(limit)
    return {"kind": "search", "text": text, "types": types[:limit], "operators": ops[:limit],
            "members": members[:limit],
            "truncated": {"types": max(0, len(types) - limit), "operators": max(0, len(ops) - limit),
                          "members": max(0, len(members) - limit)}}


# ---------------- deprecated

def cmd_deprecated(flt=None, **kw):
    res = []
    for n in all_type_names():
        cls = getattr(bpy.types, n, None)
        rna = getattr(cls, "bl_rna", None)
        if rna is None:
            continue
        base = rna.base
        bprops = set(base.properties.keys()) if base is not None else set()
        for p in rna.properties:
            if getattr(p, "is_deprecated", False) and p.identifier not in bprops:
                res.append({"where": f"{n}.{p.identifier}", "note": p.deprecated_note,
                            "since": jsonable(p.deprecated_version), "removal": jsonable(p.deprecated_removal_version)})
        for f in rna.functions:
            for p in f.parameters:
                if getattr(p, "is_deprecated", False):
                    res.append({"where": f"{n}.{f.identifier}({p.identifier}=)", "note": p.deprecated_note,
                                "since": jsonable(p.deprecated_version),
                                "removal": jsonable(p.deprecated_removal_version)})
    for c in op_categories():
        grp = getattr(bpy.ops, c)
        for n in dir(grp):
            if n.startswith("_"):
                continue
            try:
                rna = getattr(grp, n).get_rna_type()
            except Exception:
                continue
            for p in rna.properties:
                if getattr(p, "is_deprecated", False):
                    res.append({"where": f"bpy.ops.{c}.{n}({p.identifier}=)", "note": p.deprecated_note,
                                "since": jsonable(p.deprecated_version),
                                "removal": jsonable(p.deprecated_removal_version)})
    if flt:
        res = [r for r in res if flt.lower() in r["where"].lower() or flt.lower() in (r["note"] or "").lower()]
    return {"kind": "deprecated", "blender": bpy.app.version_string, "count": len(res), "items": res,
            "note": "Доступ к таким свойствам из Python печатает DeprecationWarning; removal — версия удаления"}


# ---------------- env

def cmd_env(**kw):
    scene = bpy.context.scene
    vs = scene.view_settings
    d = {"kind": "env", "blender": bpy.app.version_string, "version": list(bpy.app.version),
         "build_date": bpy.app.build_date.decode() if isinstance(bpy.app.build_date, bytes) else str(bpy.app.build_date),
         "build_hash": bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash, bytes) else str(bpy.app.build_hash),
         "binary": bpy.app.binary_path, "python": sys.version.split()[0], "background": bpy.app.background,
         "factory_startup": getattr(bpy.app, "factory_startup", None)}
    try:
        import numpy
        d["numpy"] = numpy.__version__
    except Exception:
        d["numpy"] = None
    d["render_engine_default"] = scene.render.engine
    d["render_engines"] = enum_runtime(scene.render, "engine")
    d["view_transform_default"] = vs.view_transform
    d["view_transforms"] = enum_runtime(vs, "view_transform")
    d["look_default"] = vs.look
    d["looks"] = enum_runtime(vs, "look")
    d["display_device"] = scene.display_settings.display_device
    d["display_devices"] = enum_runtime(scene.display_settings, "display_device")
    d["image_file_formats"] = [i.identifier for i in bpy.types.ImageFormatSettings.bl_rna.properties["file_format"].enum_items]
    try:
        import addon_utils
        mods = {m.__name__: m for m in addon_utils.modules()}
        g = mods.get("io_scene_gltf2")
        d["gltf_addon_version"] = list(g.bl_info.get("version", ())) if g else None
    except Exception as e:
        d["gltf_addon_version"] = f"error: {e}"
    d["addons_enabled"] = sorted(a.module for a in bpy.context.preferences.addons)
    try:
        import gpu
        d["gpu_backend"] = gpu.platform.backend_type_get()
        d["gpu_renderer"] = gpu.platform.renderer_get()
    except Exception as e:
        d["gpu_backend"] = f"недоступно: {e}"
    d["script_paths"] = bpy.utils.script_paths()
    d["extension_repos"] = [r.module for r in getattr(bpy.context.preferences, "extensions").repos] \
        if hasattr(bpy.context.preferences, "extensions") else None
    return d


# ------------------------------------------------------------------ разбор аргументов и вывод

COMMANDS = {"op": cmd_op, "ops": cmd_ops, "type": cmd_type, "node": cmd_node, "nodes": cmd_nodes,
            "enum": cmd_enum, "modifier": cmd_modifier, "sockets": cmd_sockets, "search": cmd_search,
            "deprecated": cmd_deprecated, "env": cmd_env}


def safe_for_blender_run(s):
    # blender_run.py отфильтровывает строки с «Compositing», «| Rendering», «Remaining:» как шум рендера;
    # unicode-экранирование сохраняет валидность JSON и спасает строку от фильтра.
    return (s.replace("Compositing", "\\u0043ompositing").replace("| ", "|\\u0020")
             .replace("Remaining:", "\\u0052emaining:"))


def inner_main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out_path, kw, pos = None, {}, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--out":
            out_path = argv[i + 1]; i += 2; continue
        if a == "--tree":
            kw["tree"] = argv[i + 1]; i += 2; continue
        if a == "--limit":
            kw["limit"] = argv[i + 1]; i += 2; continue
        if a == "--own":
            kw["own"] = True; i += 1; continue
        if a == "--full":
            kw["full"] = True; i += 1; continue
        pos.append(a); i += 1
    if not pos or pos[0] not in COMMANDS:
        res = {"error": f"команда: {', '.join(COMMANDS)}", "usage": __doc__.split("Примеры:")[0].strip()}
    else:
        cmd, args = pos[0], pos[1:]
        fn = COMMANDS[cmd]
        try:
            if cmd == "nodes":
                res = fn(args[0] if args else "ShaderNodeTree", args[1] if len(args) > 1 else None, **kw)
            elif cmd == "sockets":
                res = fn(args[0] if args else "GeometryNodeTree", **kw)
            elif cmd in ("modifier", "deprecated"):
                res = fn(args[0] if args else None, **kw)
            elif cmd == "env":
                res = fn(**kw)
            elif cmd == "node":
                res = fn(args[0], *args[1:], **kw) if args else {"error": "node <bl_idname> [prop=value ...]"}
            elif cmd == "search":
                res = fn(args[0], **kw) if args else {"error": "search <текст>"}
            else:
                res = fn(args[0], **kw) if args else {"error": f"{cmd} <аргумент>"}
        except Exception as e:
            import traceback
            res = {"error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()}
    res_meta = {"blender": bpy.app.version_string}
    if isinstance(res, dict):
        res = {**res, **{k: v for k, v in res_meta.items() if k not in res}}
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
    text = dumps_compact(res)
    print(MARK_BEGIN)
    print(safe_for_blender_run(text))
    print(MARK_END)
    if out_path:
        print(f"[bpy_probe] полный JSON: {out_path}")


inner_main()
