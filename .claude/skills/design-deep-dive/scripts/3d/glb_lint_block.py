# Python 3.10+ (без bpy) — [проверено] проверка готового GLB:
# расширения и декодеры, вызовы, треугольники, текстуры и память GPU, прозрачность, UV, свет, анимация
import json, struct

DECODERS = {"KHR_draco_mesh_compression": "DRACOLoader", "EXT_meshopt_compression": "MeshoptDecoder",
            "KHR_meshopt_compression": "MeshoptDecoder", "KHR_texture_basisu": "KTX2Loader"}


def _image_size(data):
    """(ширина, высота) из заголовка PNG, JPEG, WebP или KTX2."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:12] == b"\xabKTX 20\xbb\r\n\x1a\n":
        return struct.unpack("<II", data[20:28])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X":
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        if data[12:16] == b"VP8L":
            b = int.from_bytes(data[21:25], "little")
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
        return struct.unpack("<HH", data[26:30])[0] & 0x3FFF, struct.unpack("<HH", data[26:30])[1] & 0x3FFF
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1; continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9]); return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def glb_lint(path):
    raw = open(path, "rb").read()
    jlen = struct.unpack_from("<I", raw, 12)[0]
    j = json.loads(raw[20:20 + jlen])
    binc = raw[20 + jlen + 8:] if len(raw) > 20 + jlen else b""
    rep = {"file_kb": round(len(raw) / 1024, 1), "extensionsRequired": j.get("extensionsRequired", []), "warnings": []}
    warn = rep["warnings"].append
    rep["decoders"] = sorted({DECODERS[e] for e in rep["extensionsRequired"] if e in DECODERS})
    acc = j.get("accessors", [])
    # вызовы и треугольники: примитивы × экземпляры узлов (инстансинг — 1 вызов на примитив)
    calls = tris = 0
    for n in j.get("nodes", []):
        if "mesh" not in n:
            continue
        inst = n.get("extensions", {}).get("EXT_mesh_gpu_instancing")
        count = acc[inst["attributes"]["TRANSLATION"]]["count"] if inst and "TRANSLATION" in inst["attributes"] else 1
        for prim in j["meshes"][n["mesh"]]["primitives"]:
            calls += 1
            if prim.get("mode", 4) == 4:
                k = acc[prim["indices"]]["count"] if "indices" in prim else acc[prim["attributes"]["POSITION"]]["count"]
                tris += k // 3 * count
            uv = [a for a in prim["attributes"] if a.startswith("TEXCOORD_")]
            if len(uv) > 4:
                warn(f"mesh {j['meshes'][n['mesh']].get('name')}: {len(uv)} наборов UV (three читает 4)")
    rep["draw_calls_estimate"], rep["triangles"] = calls, tris
    # материалы
    mats = j.get("materials", [])
    rep["materials"] = len(mats)
    rep["blend_materials"] = [m.get("name") for m in mats if m.get("alphaMode") == "BLEND"]
    rep["unlit_materials"] = [m.get("name") for m in mats if "KHR_materials_unlit" in m.get("extensions", {})]
    if any("KHR_materials_transmission" in m.get("extensions", {}) for m in mats):
        warn("transmission: three r186 рисует все непрозрачные объекты ещё раз в текстуру — вызовы и треугольники ×2")
    # текстуры и память GPU (RGBA8 + мипмапы; KTX2 ≈ 1 байт/пиксель + мипмапы)
    gpu = 0.0; imgs = []
    for im in j.get("images", []):
        size = None
        if "bufferView" in im:
            bv = j["bufferViews"][im["bufferView"]]; data = binc[bv.get("byteOffset", 0): bv.get("byteOffset", 0) + bv["byteLength"]]
            size = _image_size(data)
        mime = im.get("mimeType", "uri")
        if size:
            bpp = 1 if mime == "image/ktx2" else 4
            gpu += size[0] * size[1] * bpp * 4 / 3
            if max(size) > 2048:
                warn(f"текстура {im.get('name')} {size[0]}×{size[1]} > 2048")
            if mime == "image/ktx2" and (size[0] % 4 or size[1] % 4):
                warn(f"KTX2 {im.get('name')}: размер не кратен 4")
        imgs.append((im.get("name"), mime, size))
    rep["images"], rep["gpu_textures_mb"] = imgs, round(gpu / 2 ** 20, 1)
    # свет и анимация
    lights = j.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])
    if any(l.get("intensity", 1) > 500 for l in lights):
        warn("интенсивность света > 500 — похоже на режим SPEC (×683): экспортировать с COMPAT")
    anims = j.get("animations", [])
    rep["animations"] = [a.get("name") for a in anims]
    if any("node" not in c.get("target", {}) for a in anims for c in a["channels"]):
        warn("есть каналы KHR_animation_pointer — three r186 без плагина их не проигрывает")
    if not any(n.get("extras") for n in j.get("nodes", [])):
        rep["note_extras"] = "extras у узлов нет (export_extras=False или постобработка без -ke)"
    return rep
