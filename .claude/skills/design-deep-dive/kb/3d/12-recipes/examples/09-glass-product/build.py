# Сгенерировано run_recipes.py из 12-recipes/09-glass-product.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 41
# Blender 5.2.2 — [проверено] рецепт 09: стеклянный флакон (transmission + volume) + сцена за ним
import sys, math, json, struct, bpy
from mathutils import Matrix
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
D, bpyx = rk.D, rk.bpyx
SLUG = "09-glass-product"
P = dict(W=0.060, D=0.032, H=0.084, corner=0.009, edge=0.004, cap_r=0.013, cap_h=0.022, neck_r=0.006, neck_h=0.006,
         glass_tint=("#E8B27A", 3.0), thickness=0.03, cap="gold", plinth="#CFC7BC", pebbles=("#C8674A", "#7C8B5A"),
         bg="#EFE9E1", cam=dict(az=22, el=9, lens=90, margin=1.18, res=(768, 1024)))


def build(P):
    C = D.fresh_collection("ASSET_glass")
    glass = rk.web_material("Glass_Amber", "glass", "#FFFFFF", thickness=P["thickness"], absorption=P["glass_tint"],
                            ior=1.52)                                        # 1,5 = умолчание glTF → KHR_materials_ior не пишется
    gold = rk.web_material("Cap_Gold", "metal_polished", P["cap"], roughness=0.22)
    stone = rk.web_material("Plinth_Stone", "plastic_matte", P["plinth"], roughness=0.75)
    plinth = D.rounded_slab("Plinth", 0.20, 0.12, 0.014, 0.012, (0.002, 0.004), C, corner_seg=8, edge_seg=3)
    bpyx.assign_material(plinth, stone)
    body = D.rounded_slab("Bottle_Glass", P["W"], P["D"], P["H"], P["corner"], (P["edge"], P["edge"]), C,
                          corner_seg=10, edge_seg=6, power=2.4)
    body.location.z = 0.014 - 0.0005                                          # стоит на подставке, врастает на 0,5 мм
    bpyx.assign_material(body, glass)
    top = 0.014 - 0.0005 + P["H"]
    neck = D.lathe("Bottle_Neck", [(0.0, 0.0), (P["neck_r"], 0.0), (P["neck_r"], P["neck_h"]), (0.0, P["neck_h"])], C,
                   segments=48)
    neck.location.z = top - 0.001
    bpyx.assign_material(neck, gold)
    cap_prof = D.fillet_polyline([(0.0, 0.0), (P["cap_r"], 0.0), (P["cap_r"], P["cap_h"]), (0.0, P["cap_h"])],
                                 [0, 0.0015, 0.004, 0], 4)
    cap = D.lathe("Bottle_Cap", cap_prof, C, segments=64, smooth_angle=40)
    cap.location.z = top + P["neck_h"] - 0.002
    bpyx.assign_material(cap, gold)
    pebbles = []
    for i, (hexc, x, y, r) in enumerate(((P["pebbles"][0], -0.035, 0.035, 0.022), (P["pebbles"][1], 0.03, 0.028, 0.028))):
        m = rk.web_material(f"Pebble_{i}", "plastic_matte", hexc, roughness=0.6)
        pb = bpyx.primitive("uvsphere", f"Pebble_{i}", radius=r, segments=48, rings=24, collection=C)
        pb.data.transform(Matrix.Scale(0.62, 4, (0, 0, 1)))                 # сплюснутая галька
        pb.location = (x, y, 0.014 + r * 0.62 - 0.001)
        bpyx.assign_material(pb, m); pebbles.append(pb)
    return C, [plinth, body, neck, cap] + pebbles


rk.reset()
C, parts = build(P)
rk.asserts("ASSET_glass", (0.20, 0.12, 0.014 + P["H"] + P["neck_h"] + P["cap_h"] - 0.0035), tol=0.06,
           touch=[("Bottle_Glass", "Plinth"), ("Bottle_Neck", "Bottle_Glass"), ("Bottle_Cap", "Bottle_Neck"),
                  ("Pebble_0", "Plinth"), ("Pebble_1", "Plinth")], max_tris=30000)
rk.studio(parts, bg=P["bg"], E_key=2.5, az=P["cam"]["az"])
rk.camera(parts[1:4], **P["cam"])                                      # кадр — по флакону, подставка и галька — окружение
sc = rk.neutral(samples=64)
sc.eevee.use_raytracing = True                                          # преломление в EEVEE (иначе — эталон неверный)
rk.audit()
rk.render(SLUG, "poster_eevee_rt", res=P["cam"]["res"], samples=64)
res = rk.ship(SLUG, "ASSET_glass", "glass", preset="static_hero", optimize="meshopt")
raw = open(f"{rk.out_dir(SLUG)}/glass_raw.glb", "rb").read()
j = json.loads(raw[20:20 + struct.unpack_from("<I", raw, 12)[0]])
g = next(m for m in j["materials"] if m["name"] == "Glass_Amber")
assert {"KHR_materials_transmission", "KHR_materials_volume", "KHR_materials_ior"} <= set(g.get("extensions", {})), g
rk.save(SLUG, glass_material=g, passport=P)
