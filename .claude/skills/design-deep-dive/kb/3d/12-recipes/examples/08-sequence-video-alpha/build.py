# Сгенерировано run_recipes.py из 12-recipes/08-sequence-video-alpha.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 37
# Blender 5.2.2 — [проверено] рецепт 08: вращение 360° импортированного GLB → PNG RGBA
import sys, math, os, bpy
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "08-sequence-video-alpha"
P = dict(glb=f"{rk.ROOT}/12-recipes/examples/04-abstract-sculpture/sculpture_ink_34_raw.glb", frames=24, res=(512, 512),
         samples=16, cam=dict(az=30, el=12, lens=85, margin=1.12))

rk.reset()
C = D.fresh_collection("ASSET_turntable")
before = set(bpy.data.objects)
assert bpy.ops.import_scene.gltf(filepath=P["glb"]) == {"FINISHED"}
imported = [o for o in bpy.data.objects if o not in before]
for o in imported:                                                    # в свою коллекцию (импорт кладёт в активную)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    C.objects.link(o)
meshes = [o for o in imported if o.type == "MESH"]
root = bpy.data.objects.new("Turntable", None); C.objects.link(root)
for o in imported:
    if o.parent is None:
        o.parent = root
rk.studio(meshes, E_key=2.5, az=P["cam"]["az"], backdrop=False, world=0.3)   # без циклорамы: фон — альфа
rk.camera(meshes, res=P["res"], **P["cam"])
rk.neutral(samples=P["samples"], transparent=True)
out = f"{rk.out_dir(SLUG)}/seq"; os.makedirs(out, exist_ok=True)
secs = []
for i in range(P["frames"]):
    root.rotation_euler.z = 2 * math.pi * i / P["frames"]              # поворот корня перед кадром — без ключей
    r = bpyx.render_still(f"{out}/f_{i + 1:04d}.png", resolution=P["res"], samples=P["samples"], transparent=True)
    secs.append(r["sec"])
assert len(os.listdir(out)) >= P["frames"]
rk.save(SLUG, frames=P["frames"], sec_per_frame=round(sum(secs) / len(secs), 2), sec_frames=round(sum(secs), 1), passport=P)
