# Сгенерировано run_recipes.py из 12-recipes/01-hero-product.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 37
# Blender 5.2.2 — [проверено] рецепт 01: кейс наушников → постер Blender + GLB для hero
import sys, math, bpy, bmesh
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "01-hero-product"
P = dict(W=0.064, D=0.024, H=0.050, corner=0.0115, edge=0.0095, power=2.6, seam_z=0.037, gap=0.0003,
         lid_open_deg=0, body="#F4F3F0", led="#39D98A", bg="#ECEEF2",
         cam=dict(az=28, el=16, lens=90, margin=1.25, res=(1024, 1024)), max_tris=20000)


def split_by_z(ob, z, keep_above):
    """Разрез меша плоскостью z с заливкой среза — две замкнутые детали (3d 05/04 §1)."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, z),
                                 plane_no=(0, 0, 1), clear_inner=keep_above, clear_outer=not keep_above)
    bmesh.ops.edgeloop_fill(bm, edges=[e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data); bm.free()
    ob.data.shade_smooth(); ob.data.set_sharp_from_angle(angle=math.radians(35))


def build(P):
    C = D.fresh_collection("ASSET_case")                       # идемпотентно: своя коллекция пересоздаётся
    body = rk.web_material("Case_Plastic", "plastic_gloss", P["body"])
    led, _ = bpyx.principled("Case_LED", base_color=P["led"], emission_color=P["led"], emission_strength=3.0)
    base = D.rounded_slab("Case_Base", P["W"], P["D"], P["H"], P["corner"], (P["edge"], P["edge"]), C,
                          corner_seg=10, edge_seg=8, power=P["power"])
    lid = bpy.data.objects.new("Case_Lid", base.data.copy()); C.objects.link(lid)
    split_by_z(base, P["seam_z"] - P["gap"] / 2, keep_above=False)
    split_by_z(lid, P["seam_z"] + P["gap"] / 2, keep_above=True)
    for o in (base, lid):
        bpyx.assign_material(o, body)
    dot = bpyx.primitive("uvsphere", "Case_LED", radius=0.0009, segments=16, rings=8, collection=C)
    dot.location = (0, -P["D"] / 2 + 0.0003, P["seam_z"] - 0.008)   # от габарита базы: передняя стенка, 8 мм ниже шва
    bpyx.assign_material(dot, led)
    D.set_origin(lid, (0, P["D"] / 2 - 0.0012, P["seam_z"]))          # pivot крышки — ось петли (для рецепта 05)
    lid.rotation_euler.x = -math.radians(P["lid_open_deg"])
    lid["hinge_axis"] = "X"                                            # extras → userData в three
    return C, [base, lid, dot]


rk.reset()
C, parts = build(P)
rk.asserts("ASSET_case", (P["W"], P["D"], P["H"]), touch=[("Case_LED", "Case_Base")], max_tris=P["max_tris"])
rk.studio(parts, bg=P["bg"], E_key=2.5)
rk.camera(parts, **P["cam"])
rk.neutral(samples=48)
rk.audit()                                                          # после камеры и вида: кадр и тонмаппинг тоже проверяются
rk.render(SLUG, "poster_blender", res=P["cam"]["res"], samples=48)
rk.ship(SLUG, "ASSET_case", "case", preset="static_hero", optimize="meshopt")
rk.save(SLUG, passport=P)
