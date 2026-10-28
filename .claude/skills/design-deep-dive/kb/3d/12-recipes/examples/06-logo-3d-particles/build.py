# Сгенерировано run_recipes.py из 12-recipes/06-logo-3d-particles.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 41
# Blender 5.2.2 — [проверено] рецепт 06: 3D-логотип (text_mesh) + точки для частиц (.bin)
import sys, json, math, bpy
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "06-logo-3d-particles"
P = dict(text="NOVA", size=0.2, extrude=0.024, bevel=0.003, res_u=4, color="#F2F0EC", bg="#E9E7E3",
         N=20000, seed=7, cloud_k=0.6, cam=dict(az=18, el=10, lens=85, margin=1.12, res=(1280, 720)))

rk.reset()
C = D.fresh_collection("ASSET_logo")
logo = D.text_mesh("Logo_NOVA", P["text"], C, size=P["size"], extrude=P["extrude"], bevel=P["bevel"], bevel_res=1,
                   resolution_u=P["res_u"])
bpyx.assign_material(logo, rk.web_material("Logo_Ceramic", "ceramic_glaze", P["color"]))
mn, mx = bpyx.world_bbox([logo]); W = mx.x - mn.x
assert 0.4 < W < 0.9 and abs(mn.z) < 1e-4, (W, mn.z)             # ширина в метрах, стоит на z = 0 (не плашмя, M2.12)
rk.studio([logo], bg=P["bg"], E_key=2.5, az=P["cam"]["az"])
rk.camera([logo], **P["cam"])
rk.neutral(samples=48)
rk.audit()
rk.render(SLUG, "logo_blender", res=P["cam"]["res"], samples=48)
rk.ship(SLUG, "ASSET_logo", "logo", preset="static_hero", optimize="meshopt")

# частицы: форма A — облако на сфере, форма B — поверхность логотипа; одинаковое N и порядок (морфинг по индексу)
pts_logo = D.surface_points(logo, P["N"], seed=P["seed"])
c = (mn + mx) / 2
sph = bpyx.primitive("uvsphere", "Cloud_Sphere", radius=W * P["cloud_k"], segments=64, rings=32, location=c)
pts_cloud = D.surface_points(sph, P["N"], seed=P["seed"] + 1)
bpy.data.objects.remove(sph, do_unlink=True)
out = rk.out_dir(SLUG)
a = D.export_points_f32(pts_cloud, f"{out}/cloud.bin")
b = D.export_points_f32(pts_logo, f"{out}/logo.bin")
meta = {"count": P["N"], "forms": ["cloud.bin", "logo.bin"], "axes": "three (x, z, -y)", "units": "m",
        "center": list(D.to_three(c)), "radius": W * P["cloud_k"]}
json.dump(meta, open(f"{out}/points.json", "w"))
assert a["bytes"] == b["bytes"] == P["N"] * 12
rk.save(SLUG, points={"cloud_kb": round(a["bytes"] / 1024, 1), "logo_kb": round(b["bytes"] / 1024, 1)}, passport=P)
