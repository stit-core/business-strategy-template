#!/usr/bin/env python3
"""RC · разбор JSON-чанка GLB без three и без сети (системный Python), 26.09.2026. Только чтение файлов дорожек.

    python3 rc_glb_checks.py            # клавиатура KB (KHR_materials_variants) + «Звено» C (контракт крюка)

1) KB: сколько примитивов несут KHR_materials_variants до и после упаковки (raw → gltfpack KTX2 / WebP), каких нет и почему,
   сколько узлов с -vpf и без него.
2) Z: контракт крюка _shared/code3d — пустышки модулей с именами кода (без меша), j3_inner, cable, AO (occlusionTexture, texCoord 1),
   анизотропия (KHR_materials_anisotropy), extras.
"""
import json
import os
import struct

R = "/home/mm/Документы/app-design/blender-research"


def gj(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n])


# ---------------------------------------------------------------- 1) KB: варианты
KB = f"{R}/99-raw/experiments/KB/06-export/out"
rows = {}
for f in ("kb_web_raw.glb", "kb_desk.glb", "kb_mob.glb", "kb_desk_etc.glb", "kb_desk_uastc.glb"):
    j = gj(os.path.join(KB, f))
    mats = j["materials"]
    prims = [(p.get("material"), bool(p.get("extensions", {}).get("KHR_materials_variants")))
             for m in j["meshes"] for p in m["primitives"]]
    without = sorted({mats[m]["name"] for m, v in prims if not v and m is not None})
    rows[f] = {"kb": round(os.path.getsize(os.path.join(KB, f)) / 1024, 1), "nodes": len(j["nodes"]), "prims": len(prims),
               "with_variants": sum(v for _, v in prims), "without_materials": without,
               "variants": [v["name"] for v in j.get("extensions", {}).get("KHR_materials_variants", {}).get("variants", [])],
               "images": sorted({i.get("mimeType", "?") for i in j.get("images", [])}),
               "required": j.get("extensionsRequired", []),
               "Key_nodes": sum(1 for n in j["nodes"] if str(n.get("name", "")).startswith("Key_")),
               "extras_Key_q": next((n.get("extras") for n in j["nodes"] if n.get("name") == "Key_q"), None) is not None}
    print("KB", f, json.dumps(rows[f], ensure_ascii=False))
assert all(r["prims"] == 26 and r["with_variants"] == 19 for r in rows.values())            # ни одной привязки не потеряно
assert rows["kb_desk.glb"]["nodes"] == 151 and rows["kb_desk_etc.glb"]["nodes"] == 296      # -vpf: без узлов деквантования
assert all(r["Key_nodes"] == 68 and r["extras_Key_q"] for r in rows.values())                # -kn -ke: имена и extras целы

# ---------------------------------------------------------------- 2) Z: контракт GLB крюка «Звена»
ORDER = ["base", "j1", "j2", "l1", "j3", "l2", "wrist", "grip"]
for f in (f"{R}/15-showcase/zveno/c-hybrid/assets/zveno.glb", f"{R}/15-showcase/zveno/c-hybrid/assets/zveno-low.glb"):
    j = gj(f)
    nodes = j["nodes"]
    by = {n.get("name"): n for n in nodes}
    empties = {k: (k in by and "mesh" not in by[k]) for k in ORDER}
    mats = j["materials"]
    ao = sum(1 for m in mats if "occlusionTexture" in m)
    ao_tc = sorted({m["occlusionTexture"].get("texCoord", 0) for m in mats if "occlusionTexture" in m})
    aniso = sum(1 for m in mats if "KHR_materials_anisotropy" in m.get("extensions", {}))
    rep = {"kb": round(os.path.getsize(f) / 1024, 1), "modules_empty": sum(empties.values()), "j3_inner": "j3_inner" in by,
           "cable": "cable" in by, "materials": len(mats), "ao_materials": ao, "ao_texCoord": ao_tc, "aniso_materials": aniso,
           "extensionsUsed": j.get("extensionsUsed", []), "images": sorted({i.get("mimeType", "?") for i in j.get("images", [])})}
    print("Z", os.path.basename(f), json.dumps(rep, ensure_ascii=False))
    assert rep["modules_empty"] == 8 and rep["j3_inner"] and rep["cable"] and ao >= 1

# ---------------------------------------------------------------- 3) Z: куда уходит UV «AO» после постобработки
for f in (f"{R}/99-raw/experiments/Z/out/c_web/zveno_raw.glb", f"{R}/15-showcase/zveno/c-hybrid/assets/zveno.glb",
          f"{R}/99-raw/experiments/Z/out/c_web/zveno_ktx2.glb"):
    j = gj(f)
    tcs = sorted({m["occlusionTexture"].get("texCoord", 0) for m in j["materials"] if "occlusionTexture" in m})
    sets = {}
    for m in j["meshes"]:
        for p in m["primitives"]:
            k = "+".join(sorted(a for a in p["attributes"] if a.startswith("TEXCOORD")))
            sets[k] = sets.get(k, 0) + 1
    print("UV", os.path.basename(f), "ao texCoord", tcs, "UV-наборы примитивов", sets)
print("RC_CHECK_OK")
