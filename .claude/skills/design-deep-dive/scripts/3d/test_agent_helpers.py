"""Тесты agent_scene.py и hygiene.py для Blender 5.2.x.

Запуск (фон, --factory-startup):

    python3 scripts/3d/blender_run.py scripts/3d/test_agent_helpers.py [-- OUT_DIR]

Код выхода 0 — все тесты зелёные, 1 — есть провалы. OUT_DIR (необязательно) — куда писать test_results.json.
Проверяет: begin()/finish() не трогают чужие объекты/материалы/настройки сцены «человека» и не плодят дублей при
повторной сборке (идемпотентность); чужой объект, оказавшийся в своей коллекции, эвакуируется, а не удаляется;
hygiene_report() не падает и даёт нулевые находки на свежей сцене (пустой и заводской).
"""
import json
import os
import sys
import time
import traceback

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import agent_scene as A  # noqa: E402
import hygiene as H  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0]) if argv else None
TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def principled_color(mat):
    p = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    return p.inputs["Base Color"] if p else None


def make_human_scene():
    """Сцена «человека»: чужой объект со своим материалом, коллекцией и настройками рендера — без тега агента."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    mat = bpy.data.materials.new("Wood")
    principled_color(mat).default_value = (0.3, 0.15, 0.05, 1.0)
    me = bpy.data.meshes.new("Table")
    me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new("Table", me)
    ob.data.materials.append(mat)
    ob.location = (2.0, 0.0, 0.0)
    sc.collection.objects.link(ob)
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 800, 600
    return sc, ob, mat


@test
def t01_begin_finish_do_not_touch_foreign():
    """Два цикла begin()/добавить деталь/finish(): чужой стол не сдвинут, не перекрашен, не пересобран агент лишку."""
    sc, foreign_ob, foreign_mat = make_human_scene()
    before_loc = tuple(foreign_ob.location)
    before_color = tuple(principled_color(foreign_mat).default_value)
    before_colls = sorted(c.name for c in foreign_ob.users_collection)
    before_engine, before_res = sc.render.engine, (sc.render.resolution_x, sc.render.resolution_y)

    agent, asset = "U01", "widget"
    for _ in range(2):                                          # идемпотентная пересборка
        coll, overrides, rep = A.begin(sc, agent, asset)
        body = A.tag(bpy.data.objects.new("widget_body", bpy.data.meshes.new("widget_body")), agent, asset, "body")
        coll.objects.link(body)
        A.finish(coll, overrides, agent, asset)

    assert tuple(foreign_ob.location) == before_loc, "чужой location изменился"
    assert tuple(principled_color(foreign_mat).default_value) == before_color, "чужой материал изменился"
    assert sorted(c.name for c in foreign_ob.users_collection) == before_colls, "чужой объект сменил коллекцию"
    assert (sc.render.engine, (sc.render.resolution_x, sc.render.resolution_y)) == (before_engine, before_res), \
        "настройки рендера сцены человека тронуты"
    assert bpy.data.objects.get(foreign_ob.name) is foreign_ob, "чужой объект удалён или переименован"
    assert rep["moved_foreign"] == [], rep
    own_objs = [o for o in bpy.data.objects if o.get(A.AGENT) == agent]
    assert len(own_objs) == 1, f"повторная сборка расплодила объекты агента: {[o.name for o in own_objs]}"
    return {"foreign_loc": before_loc, "own_objects_after_2_runs": len(own_objs)}


@test
def t02_foreign_in_own_collection_is_evicted_not_deleted():
    """Человек кладёт свой объект в коллекцию агента руками: begin() переносит его в корень сцены, не удаляет."""
    sc, _, _ = make_human_scene()
    agent, asset = "U02", "widget"
    coll, overrides, _ = A.begin(sc, agent, asset)
    A.finish(coll, overrides, agent, asset)
    intruder = bpy.data.objects.new("Intruder", bpy.data.meshes.new("Intruder"))
    coll.objects.link(intruder)

    coll2, overrides2, rep2 = A.begin(sc, agent, asset)
    A.finish(coll2, overrides2, agent, asset)

    assert rep2["moved_foreign"] == ["Intruder"], rep2
    assert bpy.data.objects.get("Intruder") is intruder, "чужой объект из своей коллекции удалён, а не эвакуирован"
    assert intruder.name not in {o.name for o in coll2.objects}, "чужой объект остался в коллекции агента"
    assert intruder.name in {o.name for o in sc.collection.objects}, "чужой объект не попал в корень сцены"
    return {"evicted": rep2["moved_foreign"]}


@test
def t03_hygiene_report_fresh_empty_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rep = H.hygiene_report()
    assert rep["dup_names"] == [], rep["dup_names"]
    assert rep["orphans"] == [], rep["orphans"]
    assert rep["dup_materials"] == [] and rep["dup_images"] == [], rep
    assert rep["packed_bytes"] == 0
    assert rep["cameras_in_scene"] == 0
    assert rep["far_objects"] == [] and rep["hidden_in_export"] == []
    assert rep["stacked_modifiers"] == [] and rep["unused_slots"] == [] and rep["extra_uv"] == []
    return {"ids": rep["ids"]}


@test
def t04_hygiene_report_default_factory_scene():
    """Заводская сцена (Cube, Light, Camera) не пуста в bpy.data: кисть Grease Pencil «Dots Stroke» — материал без
    пользователей уже в свежем файле (не баг hygiene_report — реальное устройство стартового файла 5.2.2)."""
    bpy.ops.wm.read_factory_settings(use_empty=False)        # Cube, Light, Camera
    rep = H.hygiene_report()
    assert rep["ids"]["objects"] == 3, rep["ids"]
    assert rep["cameras_in_scene"] == 1
    assert rep["dup_names"] == [], rep["dup_names"]
    assert rep["orphans"] == ["materials:Dots Stroke"], rep["orphans"]
    assert rep["dup_materials"] == [] and rep["dup_images"] == [], rep
    return {"ids": rep["ids"], "known_startup_orphan": rep["orphans"]}


def main():
    results = []
    t_all = time.time()
    for fn in TESTS:
        t0 = time.time()
        try:
            info = fn()
            results.append({"test": fn.__name__, "ok": True, "sec": round(time.time() - t0, 3), "info": info})
            print(f"PASS {fn.__name__} ({time.time() - t0:.2f} s) {json.dumps(info, ensure_ascii=False, default=str)[:180]}")
        except Exception as e:  # noqa: BLE001
            tb = traceback.format_exc()
            results.append({"test": fn.__name__, "ok": False, "sec": round(time.time() - t0, 3),
                            "error": f"{type(e).__name__}: {e}", "traceback": tb})
            print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}\n{tb}")
    n_ok = sum(r["ok"] for r in results)
    summary = {"blender": bpy.app.version_string, "passed": n_ok, "total": len(results),
               "sec": round(time.time() - t_all, 2), "results": results}
    print(f"RESULT {n_ok}/{len(results)} passed in {summary['sec']} s (Blender {bpy.app.version_string})")
    if OUT:
        os.makedirs(OUT, exist_ok=True)
        json.dump(summary, open(os.path.join(OUT, "test_results.json"), "w"), ensure_ascii=False, indent=1, default=str)
    if n_ok != len(results):
        sys.exit(1)


main()
