# Сгенерировано run_recipes.py из 12-recipes/05-scroll-showcase.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 39
# Blender 5.2.2 — [проверено] рецепт 05: кейс рецепта 01 + клип «Reveal» (слоты — 3d 07/03 §1.2)
import sys, math, bpy, bmesh
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py и animx.py — scripts/3d
import rk, animx
D, bpyx = rk.D, rk.bpyx
SLUG = "05-scroll-showcase"
P = dict(W=0.0606, D=0.0217, H=0.0452, corner=0.0105, edge=0.0085, power=2.6, seam_z=0.0335, gap=0.0003,
         body="#F4F3F0", bud_r=0.0085, stem=(0.003, 0.020), lift=0.030, open_deg=105, fps=30)


def split_by_z(ob, z, keep_above):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z),
                                 plane_no=(0, 0, 1), clear_inner=keep_above, clear_outer=not keep_above)
    bmesh.ops.edgeloop_fill(bm, edges=[e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free()
    ob.data.shade_smooth(); ob.data.set_sharp_from_angle(angle=math.radians(35))


def build(P):
    C = D.fresh_collection("ASSET_case_reveal")
    body = rk.web_material("Case_Plastic", "plastic_gloss", P["body"])
    base = D.rounded_slab("Case_Base", P["W"], P["D"], P["H"], P["corner"], (P["edge"], P["edge"]), C,
                          corner_seg=10, edge_seg=8, power=P["power"])
    lid = bpy.data.objects.new("Case_Lid", base.data.copy()); C.objects.link(lid)
    split_by_z(base, P["seam_z"] - P["gap"] / 2, keep_above=False)
    split_by_z(lid, P["seam_z"] + P["gap"] / 2, keep_above=True)
    D.set_origin(lid, (0, P["D"] / 2 - 0.0012, P["seam_z"]))                       # pivot — ось петли
    buds = []
    for i, x in enumerate((-0.014, 0.014)):
        bud = bpyx.primitive("uvsphere", f"Bud_{i}", radius=P["bud_r"], segments=32, rings=16, collection=C)
        stem = bpyx.primitive("cylinder", f"Bud_{i}_Stem", radius=P["stem"][0], depth=P["stem"][1], segments=24, collection=C)
        stem.location = (0, 0, -P["stem"][1] / 2)
        stem.parent = bud
        bud.location = (x, 0, P["seam_z"] - P["gap"] - P["bud_r"] * 0.2)                # утоплен в базу на 60 %
        buds.append(bud)
    for o in [base, lid] + buds + [b.children[0] for b in buds]:
        bpyx.assign_material(o, body)
    return C, base, lid, buds


def key_reveal(lid, buds, P):
    act = animx.new_action("Reveal", [lid, *buds])                      # ОДНО действие со слотами → один клип glTF
    lid.rotation_mode = "XYZ"
    animx.key(lid, "rotation_euler", 1, 0.0, index=0)
    animx.key(lid, "rotation_euler", 24, math.radians(-P["open_deg"]), index=0)
    for kp in animx.fcurves(lid)[0].keyframe_points[:1]:
        kp.interpolation = "BACK"; kp.easing = "EASE_OUT"; kp.back = 1.2
    for i, b in enumerate(buds):
        f0, z0 = 16 + 6 * i, b.location.z                                            # стаггер 6 кадров
        animx.key(b, "location", f0, z0, index=2)
        animx.key(b, "location", f0 + 20, z0 + P["lift"], index=2)
    bpy.context.scene.frame_start, bpy.context.scene.frame_end = 1, 42
    bpy.context.scene.render.fps = P["fps"]
    return act


rk.reset()
C, base, lid, buds = build(P)
act = key_reveal(lid, buds, P)
assert len(act.slots) == 3, [s.identifier for s in act.slots]
bpy.context.scene.frame_set(42)
mn, mx = bpyx.world_bbox([b for b in buds])
assert mn.z > P["seam_z"] - 0.012, mn.z                                   # наушники поднялись над швом
bpy.context.scene.frame_set(1)
res = rk.ship(SLUG, "ASSET_case_reveal", "case_reveal", preset="anim_trs", optimize="meshopt", keep_names=True)
j = rk.DX.glb_info(f"{rk.out_dir(SLUG)}/case_reveal.glb")
rk.save(SLUG, slots=[s.identifier for s in act.slots], passport=P)
