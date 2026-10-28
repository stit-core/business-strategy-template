# Сгенерировано run_recipes.py из 12-recipes/12-model-viewer-ar.md — блоки python в напечатанном виде, по порядку.

# ---- блок со строки 38
# Blender 5.2.2 — [проверено] рецепт 12: AR-GLB (лимиты Scene Viewer) + USDZ (Quick Look)
import sys, os, json, shutil, struct, bpy
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts", "3d"))  # перенос: rk.py — scripts/3d
import rk
SLUG = "12-model-viewer-ar"
SRC = f"{rk.ROOT}/12-recipes/examples/01-hero-product"
OUT = rk.out_dir(SLUG)
AR_EXT_OK = {"KHR_materials_unlit", "KHR_texture_transform"}             # что знает Scene Viewer (F1 09/06 §2.2)


def ar_lint(path, max_tris=100_000, max_mats=10, max_tex=2048, max_mb=10):
    """Лимиты Scene Viewer по JSON GLB: расширения, треугольники, материалы, морфы, цвета вершин, анимации, размер."""
    data = open(path, "rb").read(); j = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
    acc, fails = j.get("accessors", []), []
    tris = sum(acc[p["indices"]]["count"] // 3 for m in j.get("meshes", []) for p in m["primitives"] if "indices" in p)
    req = set(j.get("extensionsRequired", [])) - AR_EXT_OK                  # обязательное неизвестное → файл не откроется
    if req: fails.append(f"обязательные расширения вне Scene Viewer: {sorted(req)}")
    warn = sorted(set(j.get("extensionsUsed", [])) - AR_EXT_OK - req)       # необязательное → в AR молча без эффекта
    if tris > max_tris: fails.append(f"треугольников {tris} > {max_tris}")
    if len(j.get("materials", [])) > max_mats: fails.append("материалов > 10")
    if any("targets" in p for m in j.get("meshes", []) for p in m["primitives"]): fails.append("морфы запрещены")
    if any("COLOR_0" in p["attributes"] for m in j.get("meshes", []) for p in m["primitives"]): fails.append("цвета вершин запрещены")
    if len(j.get("animations", [])) > 1: fails.append("анимаций > 1")
    if len(data) > max_mb * 2**20: fails.append(f"размер {len(data) / 2**20:.1f} МБ > {max_mb}")
    return {"ok": not fails, "fails": fails, "ignored_in_ar": warn, "tris": tris, "materials": len(j.get("materials", [])),
            "extensionsUsed": j.get("extensionsUsed", []), "kb": round(len(data) / 1024, 1)}


def export_usdz(path, **overrides):                                       # F1 09/06 §2.4 [проверено]
    kw = dict(selected_objects_only=False, export_animation=False, export_materials=True, generate_preview_surface=True,
              export_textures_mode="NEW", usdz_downscale_size="2048", export_subdivision="TESSELLATE", evaluation_mode="RENDER",
              convert_orientation=True, export_global_forward_selection="NEGATIVE_Z", export_global_up_selection="Y",
              convert_scene_units="METERS", export_lights=False, export_cameras=False)
    kw.update(overrides)
    valid = {p.identifier for p in bpy.ops.wm.usd_export.get_rna_type().properties}
    bad = [k for k in kw if k not in valid]
    if bad:
        raise KeyError(f"нет параметров {bad} в wm.usd_export этой версии")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return bpy.ops.wm.usd_export(filepath=os.path.abspath(path), **kw)


shutil.copy(f"{SRC}/case_raw.glb", f"{OUT}/case_ar.glb")                  # AR-файл = экспорт static_hero БЕЗ сжатия
shutil.copy(f"{SRC}/poster.webp", f"{OUT}/poster.webp")
lint = ar_lint(f"{OUT}/case_ar.glb"); print("AR_LINT", lint); assert lint["ok"], lint
lint_web = ar_lint(f"{SRC}/case.glb")                                     # сжатый веб-GLB Scene Viewer не годится
assert not lint_web["ok"] and "EXT_meshopt_compression" in str(lint_web["fails"]), lint_web
rk.reset()
assert bpy.ops.import_scene.gltf(filepath=f"{OUT}/case_ar.glb") == {"FINISHED"}
assert export_usdz(f"{OUT}/case.usdz") == {"FINISHED"}
from pxr import Usd, UsdGeom                                                 # проверка пакета тем же Blender
st = Usd.Stage.Open(f"{OUT}/case.usdz")
bb = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"]).ComputeWorldBound(st.GetPseudoRoot()).ComputeAlignedRange()
size = [round(v, 4) for v in (bb.GetMax() - bb.GetMin())]
usd = {"upAxis": UsdGeom.GetStageUpAxis(st), "metersPerUnit": UsdGeom.GetStageMetersPerUnit(st), "size_m": size,
       "kb": round(os.path.getsize(f"{OUT}/case.usdz") / 1024, 1),
       "shaders": sorted({p.GetAttribute("info:id").Get() for p in st.Traverse() if p.GetTypeName() == "Shader"} - {None})}
print("USDZ", usd)
assert usd["upAxis"] == "Y" and abs(usd["metersPerUnit"] - 1) < 1e-6 and abs(size[1] - 0.0452) < 0.002, usd   # высота кейса — ось Y
rk.save(SLUG, ar_lint=lint, web_glb_lint=lint_web, usdz=usd)
