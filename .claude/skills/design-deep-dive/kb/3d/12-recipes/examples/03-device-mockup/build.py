# Сгенерировано run_recipes.py из 12-recipes/03-device-mockup.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 34
# Blender 5.2.2 — [проверено] рецепт 03: телефон (3d 05/04 §2) + скриншот из файла → постер + GLB
import sys, math, bpy, bmesh
import numpy as np
from mathutils import Matrix
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "03-device-mockup"
P = dict(W=0.0715, D=0.147, H=0.0078, corner=0.0115, edge=0.0011, bezel=0.0018, screen_corner=0.0098,
         island=0.034, island_corner=0.0085, island_h=0.0011, island_margin=0.0045, lens_r=0.0056, lens_h=0.0016,
         btn_t=0.0006, frame="#8E9196", back="#C9C4BC", glass="#0B0C0E", lens="#1A1C20", ring="#B7BABF", bg="#ECEEF2",
         screenshot=f"{rk.ROOT}/99-raw/experiments/K/02-hero-page/mobile/shot_mobile_thr_quick_0.png", tex_w=540,
         cam=dict(az=-18, el=8, lens=85, margin=1.2, res=(768, 1024)), max_tris=10000)


def fit_screenshot(src, dst, aspect, width):
    """Обрезать скриншот под аспект экрана (ширина/высота), верх страницы сохранить; ужать до width; JPEG sRGB."""
    im = bpy.data.images.load(src, check_existing=False)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(h, w, 4)   # строки снизу вверх
    if w / h > aspect:
        nw = round(h * aspect); x0 = (w - nw) // 2; px = px[:, x0:x0 + nw]
    else:
        nh = round(w / aspect); px = px[h - nh:, :]                                           # верх = последние строки
    out = bpy.data.images.new("screen_ui", px.shape[1], px.shape[0], alpha=False)
    out.pixels.foreach_set(np.ascontiguousarray(px).ravel())
    out.scale(width, round(width / aspect))
    out.filepath_raw = dst; out.file_format = "JPEG"; out.save(quality=88)
    bpy.data.images.remove(im)
    img = bpy.data.images.load(dst, check_existing=False); img.colorspace_settings.name = "sRGB"
    return img


def build(P, coll):
    parts = {}
    body = D.rounded_slab("Phone_Body", P["W"], P["D"], P["H"], P["corner"], (P["edge"], P["edge"]), coll,
                          corner_seg=10, edge_seg=4, smooth_angle=35)
    m_frame, _ = bpyx.principled("Phone_Frame", base_color=P["frame"], metallic=1.0, roughness=0.32)
    m_back, _ = bpyx.principled("Phone_BackGlass", base_color=P["back"], roughness=0.45, coat_weight=0.6)
    m_glass, _ = bpyx.principled("Phone_FrontGlass", base_color=P["glass"], roughness=0.05, coat_weight=1.0)
    for m in (m_frame, m_back, m_glass):
        body.data.materials.append(m)
    body.data.polygons.foreach_set("material_index", [1 if p.normal.z < -0.99 else 2 if p.normal.z > 0.99 else 0
                                                      for p in body.data.polygons])
    parts["body"] = body
    sw, sd = P["W"] - 2 * P["bezel"], P["D"] - 2 * P["bezel"]          # экран: UV 0–1, на 0,1 мм над стеклом
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    f = bm.faces.new([bm.verts.new((x, y, P["H"] + 0.0001)) for x, y in D.rrect_pts(sw, sd, P["screen_corner"], 10)])
    for loop in f.loops:
        loop[uvl].uv = (loop.vert.co.x / sw + 0.5, loop.vert.co.y / sd + 0.5)
    bmesh.ops.triangulate(bm, faces=[f], quad_method="BEAUTY", ngon_method="BEAUTY")
    screen = D.obj_from_bm(bm, "Phone_Screen", coll, smooth_angle=None)
    img = fit_screenshot(P["screenshot"], f"{rk.out_dir(SLUG)}/screen_ui.jpg", sw / sd, P["tex_w"])
    m_scr, p = bpyx.principled("Screen", roughness=0.08, emission_strength=1.0)
    tex = m_scr.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = img
    bpyx.link_sockets(m_scr.node_tree, (tex, "Color"), (p, "Base Color"))
    bpyx.link_sockets(m_scr.node_tree, (tex, "Color"), (p, "Emission Color"))
    bpyx.assign_material(screen, m_scr)
    parts["screen"] = screen
    isl = D.rounded_slab("Phone_CameraIsland", P["island"], P["island"], P["island_h"], P["island_corner"],
                         (0.0, P["island_h"] * 0.6), coll, corner_seg=8, edge_seg=3)
    ix = P["W"] / 2 - P["island_margin"] - P["island"] / 2
    iy = P["D"] / 2 - P["island_margin"] - P["island"] / 2
    isl.data.transform(Matrix.Rotation(math.pi, 4, "X")); isl.location = (ix, iy, 0.0)
    bpyx.assign_material(isl, m_back); parts["island"] = isl
    m_lens, _ = bpyx.principled("Phone_Lens", base_color=P["lens"], roughness=0.08, coat_weight=1.0)
    m_ring, _ = bpyx.principled("Phone_LensRing", base_color=P["ring"], metallic=1.0, roughness=0.25)
    r, h = P["lens_r"], P["lens_h"]
    prof = D.fillet_polyline([(0.0, -0.7 * h), (0.78 * r, -0.7 * h), (0.78 * r, -h), (r, -h), (r, 0.0), (0.0, 0.0)],
                             [0, 0.00015, 0.00015, 0.0004, 0, 0], 3)
    off = P["island"] * 0.24
    for k, (dx, dy) in enumerate(((-off, off), (-off, -off), (off, 0.0))):
        lens = D.lathe(f"Phone_Lens{k}", prof, coll, segments=40, smooth_angle=40)
        lens.location = (ix + dx, iy + dy, -P["island_h"])
        lens.data.materials.append(m_ring); lens.data.materials.append(m_lens)
        lens.data.polygons.foreach_set("material_index", [1 if (abs(q.center.z + 0.7 * h) < 1e-5 and
                                       math.hypot(q.center.x, q.center.y) < 0.78 * r) else 0 for q in lens.data.polygons])
        parts[f"lens{k}"] = lens

    def button(name, side, y0, length):
        b = D.rounded_slab(name, P["btn_t"] * 2, length, P["H"] * 0.42, P["btn_t"], 0.0, coll, corner_seg=6)
        b.data.transform(Matrix.Translation((0, 0, -P["H"] * 0.21)))
        b.location = (side * P["W"] / 2, y0, P["H"] / 2)
        bpyx.assign_material(b, m_frame)
        return b
    parts["action"] = button("Phone_BtnAction", -1, P["D"] * 0.30, 0.008)
    parts["volup"] = button("Phone_BtnVolUp", -1, P["D"] * 0.20, 0.012)
    parts["power"] = button("Phone_BtnPower", 1, P["D"] * 0.16, 0.018)
    Rm = Matrix.Translation((0, 0, P["D"] / 2)) @ Matrix.Rotation(math.radians(90), 4, "X")   # экраном к −Y, низом на пол
    bpy.context.view_layer.update()
    for o in parts.values():
        o.matrix_world = Rm @ o.matrix_world
        bpyx.apply_transforms(o, rotation=True, scale=True)
    root = bpy.data.objects.new("Phone", None); coll.objects.link(root)
    root.location = (0, -P["H"] / 2, P["D"] / 2); bpy.context.view_layer.update()
    for o in parts.values():
        o.parent = root; o.matrix_parent_inverse = root.matrix_world.inverted()
    return root, list(parts.values())


rk.reset()
C = D.fresh_collection("ASSET_phone")
root, parts = build(P, C)
rk.asserts("ASSET_phone", (P["W"] + 2 * P["btn_t"], P["H"] + P["island_h"] + P["lens_h"], P["D"]), tol=0.06,
           touch=[("Phone_CameraIsland", "Phone_Body"), ("Phone_Lens0", "Phone_CameraIsland"),
                  ("Phone_Screen", "Phone_Body"), ("Phone_BtnPower", "Phone_Body")], max_tris=P["max_tris"])
rk.studio(parts, bg=P["bg"], E_key=2.5, az=-18)
rk.camera(parts, **P["cam"])
rk.neutral(samples=48)
rk.audit()
rk.render(SLUG, "poster_blender", res=P["cam"]["res"], samples=48)
rk.ship(SLUG, "ASSET_phone", "phone", preset="static_hero", optimize="meshopt", phone=True)
rk.save(SLUG, passport={k: v for k, v in P.items() if k != "screenshot"})
