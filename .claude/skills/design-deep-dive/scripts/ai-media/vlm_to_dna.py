#!/usr/bin/env python3
"""vlm_to_dna.py — паспорт визуала бренда (visual DNA): разбор сетки бренд-картинок сессией Opus → черновик паспорта,
проверка по схеме и смыслу, сверка прогонов, грейд .cube, вывод из токенов UI, спецификация ассета.

Разбор сетки делает отдельная сессия Opus — агент design-judge по пакету той же формы, что пакет судьи
(asset_audit.py judge-jobs): код собирает пакет и разбирает ответ, моделей сам не вызывает. Схема паспорта —
kb/ai-media/06-art-direction-consistency/visual-dna.schema.json; поля и правила вывода — 06-art-direction-consistency/
01-visual-dna-from-ui.md; паспорт утверждает человек. Схему проверяет jsonschema, без него — встроенный валидатор
подмножества JSON Schema 2020-12.

Команды:
  grid IMG... --out GRID.jpg [--cell 640 --cols 3]      сетка бренд-картинок (белые желоба 10 px)
  build GRID [--out DIR] [--name N] [--runs 2]          пакет для сессии Opus: сетка → JSON-бриф (характер, палитра, грейд,
                                                        свет, камера, композиция, реквизит, блок стиля, запреты,
                                                        канарейки); прогоны — отдельные задания
  parse PACKAGE|ANSWER --out DNA.json [--grid GRID] [--id ID] [--brand B] [--art-direction AD.json]
                                                        ответ сессии (answers/<id>.md пакета, текст с ```json или голый
                                                        JSON) → черновик паспорта; по сетке — палитра, баланс белого и
                                                        хрома, снятые локально, критерий «≥ 3 из 5 hex в ΔE ≤ 0,05» и
                                                        «придуманные» цвета; два ответа и больше — сверка прогонов
  validate DNA.json... [--art-direction AD.json]        схема + смысловой линт (запрещённые оттенки, слова, роли, паспорт
                                                        3D-серии, метафоры иллюстраций); с --art-direction — сверка
                                                        скрима: числа прозрачности рядом со словом «скрим» в текстах
                                                        арт-дирекции против post.scrim.max_alpha паспорта, расхождение —
                                                        предупреждение
  compare A.json B.json                                 два прогона разбора: совпадение grade и light, ΔE палитр
  lut DNA.json --out FILE.cube [--size 33]              параметрический грейд паспорта → 3D LUT (.cube)
  from-tokens TOKENS.json --out DNA.json [--adjectives a,b,c] [--id ID]
                                                        скелет паспорта из токенов DTCG (ui 09/04)
  to-spec DNA.json --kind photo|illustration|icon3d --task CODE --subject TEXT [--section hero] [--slot hero-visual]
          [--ratio 16:9] [--no-text-zone] [--ref-class CLASS] [--edit SOURCE --operation OP] [--out SPEC.json]
                                                        спецификация ассета (05-prompting) из паспорта: --section — id
                                                        секции плана страницы, --slot — id строки плана ассетов (без
                                                        --section секцией служит значение --slot); --edit — профиль
                                                        правки настоящего кадра: в спецификацию не идут исключения
                                                        паспорта и композиция генерации с нуля, референсы паспорта —
                                                        только с --ref-class; `edit.changes` и `edit.keep` дописывает
                                                        автор
  selftest                                              самопроверка на синтетике и заглушках ответа

Код выхода: 0 — ошибок нет; 1 — ошибки схемы или линта (validate, parse, to-spec) или провал самопроверки; 2 — ошибка
вызова или входа (нет ответов пакета, файл арт-дирекции не читается, --edit без --operation).
"""
import argparse, copy, datetime as dt, hashlib, io, json, math, os, re, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))  # scripts/lib: kbpaths, color
import kbpaths  # noqa: E402
ROOT = kbpaths.kb("ai-media")
TOOLS = kbpaths.scripts("ai-media")
SCHEMA_PATH = ROOT / "06-art-direction-consistency" / "visual-dna.schema.json"
SPEC_SCHEMA_PATH = ROOT / "05-prompting" / "asset-spec.schema.json"
EXAMPLES = ROOT / "06-art-direction-consistency" / "examples"
JUDGE_AGENT = kbpaths.repo(".claude", "agents", "design-judge.md")
JUDGE_PROTOCOL = ".claude/skills/design-deep-dive/kb/common/judge.md"
SERIES_PASSPORT = "3d/06-materials-lighting-render/02-lighting-camera-composition.md §6"
sys.path.insert(0, str(TOOLS))

# ---------------------------------------------------------------- рубрика разбора сетки (задание сессии, текст запроса)
GRID_SYSTEM = ("You are an expert brand visual analyst and image generation brief writer. You receive one image containing "
               "a grid of brand photographs. Describe only what is visible; use numbers where asked; do not flatter; do not "
               "invent brand names.")
GRID_REQUEST = ("Return one JSON object with these keys: character: {adjectives: [3 words]}; palette: [5 items {hex, "
                "name, role: background|dominant|secondary|accent|shadow, share: 0-1 of image area}] (shares sum <= 1); grade: "
                "{white_balance: warm|neutral|cool, contrast: low|medium|high, saturation: muted|natural|vivid, black_point: "
                "crushed|neutral|lifted, grain: none|fine|visible}; light: {direction, quality: soft|hard|mixed, time_of_day, "
                "color_temp_K: integer}; camera: {lens_mm: integer, height: ground|eye-level|high, depth_of_field: "
                "shallow|medium|deep}; composition: {subject_region, horizon_position: top-third|middle|bottom-third, "
                "negative_space: low|medium|high, crop_style}; subject_matter: {domain_props: [up to 8 concrete objects], motifs: "
                "[up to 4], people_policy: none|background|primary}; style_block_photo: one paragraph of at most 60 words in English "
                "that would make a text-to-image model reproduce this photographic style for NEW subjects (visible features only, "
                "no adjectives like stunning/cinematic/vibrant); exclusions: [up to 6 visible features that would break this "
                "style]; canaries: [5 short test subjects of different classes (object, interior, nature, abstract, product) to "
                "check the style on a new model].")
GRID_RULES = ["- Только видимое на сетке: hex — цвета, которые занимают площадь картинок, доли — от площади; числа цвета код "
              "сверит с пикселями сетки, придуманный цвет будет помечен.",
              "- В блоке стиля нет оценочных слов (stunning, cinematic, vibrant …) и «no X»: признаки — позитивом.",
              "- Решение — не твоё: паспорт утверждает человек."]

# ---------------------------------------------------------------- категории брифа → числа паспорта [позиция; утверждает человек глазом]
WB = {"warm": (0.002, 0.010), "neutral": (0.0, 0.0), "cool": (-0.001, -0.006)}
WB_TARGET_B = {"warm": (0.010, 0.006), "neutral": (0.0, 0.004), "cool": (-0.004, 0.004)}
SAT = {"muted": 0.80, "natural": 0.92, "vivid": 1.0}
CON = {"low": 0.05, "medium": 0.12, "high": 0.20}
BLACK = {"crushed": 0.0, "neutral": 0.03, "lifted": 0.05}
GRAIN = {"none": 0.0, "fine": 1.5, "visible": 3.0}
NEG = {"low": 0.15, "medium": 0.30, "high": 0.45}
DEFAULT_BANNED = ["stunning", "vibrant", "luminous", "radiant", "breathtaking", "gorgeous", "mesmerizing", "cinematic", "epic",
                  "dramatic", "masterpiece", "8k", "hyper-detailed", "hyperrealistic", "award-winning", "golden hour", "hdr"]
DEFAULT_MARKERS = ["IMG-M02", "IMG-M03", "IMG-M05", "IMG-M07", "IMG-M09", "IMG-M10", "IMG-M13", "IMG-M14", "IMG-M21", "IMG-M22"]
ACCEPTANCE_DEFAULT = {  # пороги фото одной съёмки (ai-media 06/02–06/04)
    "palette_dE_max": 0.02, "series_hue_spread_max_deg": 10, "series_pal_dE_mean_max": 0.045, "series_pal_dE_break": 0.06,
    "series_sd_L_max": 0.04, "phash_min": 10, "text_contrast_min": 4.5, "text_zone_percentile": 99.9, "zone_edge_max": 0.06,
    "centroid_x_min": 0.62, "colorfulness_max_rel": 1.2, "hdr_index_max_delta": 0.1, "markers_max": 1}


def today():
    return dt.date.today().isoformat()


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump_json(obj, p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ---------------------------------------------------------------- цвет (без numpy: color.py)
def hex_rgb(h):
    h = h.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def hex_oklab(h):
    from color import rgb2oklab
    return rgb2oklab(*hex_rgb(h))


def hex_oklch(h):
    L, a, b = hex_oklab(h)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def dE(a, b):
    return math.dist(hex_oklab(a) if isinstance(a, str) else a, hex_oklab(b) if isinstance(b, str) else b)


def hue_in(h, lo, hi):
    return lo <= h <= hi if lo <= hi else (h >= lo or h <= hi)


# ---------------------------------------------------------------- валидатор (jsonschema или встроенный)
def _type_ok(v, t):
    return {"object": isinstance(v, dict), "array": isinstance(v, list), "string": isinstance(v, str),
            "integer": isinstance(v, int) and not isinstance(v, bool),
            "number": isinstance(v, (int, float)) and not isinstance(v, bool),
            "boolean": isinstance(v, bool), "null": v is None}.get(t, True)


def mini_validate(inst, sch, root, path="", errs=None):
    """Подмножество JSON Schema 2020-12, которого хватает схемам паспорта и спецификации ассета."""
    errs = [] if errs is None else errs
    where = path or "(root)"
    if sch is True or not isinstance(sch, dict):
        return errs
    if "$ref" in sch:
        node = root
        for part in sch["$ref"].lstrip("#/").split("/"):
            node = node[part]
        mini_validate(inst, node, root, path, errs)
    t = sch.get("type")
    if t is not None:
        ts = t if isinstance(t, list) else [t]
        if not any(_type_ok(inst, x) for x in ts):
            errs.append(f"{where}: тип {type(inst).__name__}, ожидался {t}")
            return errs
    if "const" in sch and inst != sch["const"]:
        errs.append(f"{where}: должно быть {sch['const']!r}")
    if "enum" in sch and inst not in sch["enum"]:
        errs.append(f"{where}: {inst!r} не из {sch['enum']}")
    if isinstance(inst, str):
        if "pattern" in sch and not re.search(sch["pattern"], inst):
            errs.append(f"{where}: {inst!r} не соответствует {sch['pattern']}")
        if "minLength" in sch and len(inst) < sch["minLength"]:
            errs.append(f"{where}: короче {sch['minLength']}")
        if "maxLength" in sch and len(inst) > sch["maxLength"]:
            errs.append(f"{where}: длиннее {sch['maxLength']}")
    if _type_ok(inst, "number"):
        if "minimum" in sch and inst < sch["minimum"]:
            errs.append(f"{where}: {inst} < {sch['minimum']}")
        if "maximum" in sch and inst > sch["maximum"]:
            errs.append(f"{where}: {inst} > {sch['maximum']}")
        if "exclusiveMinimum" in sch and inst <= sch["exclusiveMinimum"]:
            errs.append(f"{where}: {inst} ≤ {sch['exclusiveMinimum']}")
        if "exclusiveMaximum" in sch and inst >= sch["exclusiveMaximum"]:
            errs.append(f"{where}: {inst} ≥ {sch['exclusiveMaximum']}")
    if isinstance(inst, list):
        if "minItems" in sch and len(inst) < sch["minItems"]:
            errs.append(f"{where}: элементов {len(inst)} < {sch['minItems']}")
        if "maxItems" in sch and len(inst) > sch["maxItems"]:
            errs.append(f"{where}: элементов {len(inst)} > {sch['maxItems']}")
        pre = sch.get("prefixItems", [])
        for i, (x, s) in enumerate(zip(inst, pre)):
            mini_validate(x, s, root, f"{path}/{i}", errs)
        if "items" in sch:
            for i, x in enumerate(inst[len(pre):], start=len(pre)):
                mini_validate(x, sch["items"], root, f"{path}/{i}", errs)
    if isinstance(inst, dict):
        for k in sch.get("required", []):
            if k not in inst:
                errs.append(f"{where}: нет обязательного поля {k!r}")
        props = sch.get("properties", {})
        for k, v in inst.items():
            if k in props:
                mini_validate(v, props[k], root, f"{path}/{k}", errs)
            elif sch.get("additionalProperties") is False:
                errs.append(f"{where}: лишнее поле {k!r}")
            elif isinstance(sch.get("additionalProperties"), dict):
                mini_validate(v, sch["additionalProperties"], root, f"{path}/{k}", errs)
        if "minProperties" in sch and len(inst) < sch["minProperties"]:
            errs.append(f"{where}: полей {len(inst)} < {sch['minProperties']}")
    for key in ("oneOf", "anyOf"):
        if key in sch:
            ok = sum(1 for s in sch[key] if not mini_validate(inst, s, root, path, []))
            if (key == "oneOf" and ok != 1) or (key == "anyOf" and ok < 1):
                errs.append(f"{where}: {key} — подходит {ok} вариантов")
    for s in sch.get("allOf", []):
        mini_validate(inst, s, root, path, errs)
    return errs


def schema_errors(inst, schema_path=SCHEMA_PATH, force_builtin=False):
    schema = load_json(schema_path)
    if not force_builtin:
        try:
            import jsonschema
            v = jsonschema.Draft202012Validator(schema)
            return ["/" + "/".join(map(str, e.absolute_path)) + ": " + e.message
                    for e in sorted(v.iter_errors(inst), key=lambda e: list(map(str, e.absolute_path)))], "jsonschema"
        except ImportError:
            pass
    return mini_validate(inst, schema, schema), "builtin"


# ---------------------------------------------------------------- смысловой линт паспорта
def words(s):
    return len(re.findall(r"[A-Za-zА-Яа-яЁё0-9#'-]+", s))


def lint(dna, dna_path=None):
    errs, warns = [], []
    if dna.get("status") == "approved" and not dna.get("approved_by"):
        errs.append("status approved без approved_by: паспорт утверждает человек")
    pal = dna.get("palette", {})
    bands = pal.get("forbidden_hues", [])
    for key in ("image_palette", "illustration_palette"):
        for e in pal.get(key, []):
            L, C, H = hex_oklch(e["hex"])
            brand_token = e.get("strict") and e.get("source") == "token"
            for b in bands:
                if key == "illustration_palette" and brand_token:
                    continue  # бренд-акцент из токенов в иллюстрации разрешён; потолок доли полосы — для фото
                if C > 0.04 and hue_in(H, b["from"], b["to"]) and e.get("share_max", 1) > b.get("except_share_max", 0):
                    errs.append(f"{key} {e['hex']} ({e['name']}): оттенок {H:.0f}° в запрещённой полосе {b['from']}–{b['to']}°, "
                                f"доля {e.get('share_max')} > {b.get('except_share_max', 0)}")
            caps = pal.get("chroma_caps")
            if key == "illustration_palette" and caps:
                s = e.get("share_max", 0)
                cap = caps.get("large_area_C_max") if s > 0.3 else caps.get("mid_area_C_max") if s > 0.05 else caps.get("small_area_C_max")
                if cap is not None and C > cap + 0.005 and e.get("role") != "accent":
                    warns.append(f"illustration_palette {e['hex']}: хрома {C:.3f} выше потолка {cap} для доли {s}")
        roles = [e["role"] for e in pal.get(key, [])]
        if key == "image_palette" and not ({"dominant", "background"} & set(roles)):
            errs.append("image_palette: нет роли dominant или background")
        if roles.count("accent") > 3:
            warns.append(f"{key}: акцентов {roles.count('accent')} > 3 (ui 07/02 §2.1: 2–3)")
    banned = [w.lower() for w in dna.get("exclusions", {}).get("banned_words", [])] or DEFAULT_BANNED
    for k, block in dna.get("style_blocks", {}).items():
        n = words(block)
        if n > 80:
            warns.append(f"style_blocks.{k}: {n} слов > 80 (FLUX: 30–80 оптимально; блок идёт первым в каждом промте)")
        negs = re.findall(r"\bno [a-z-]+", block.lower())
        if negs:
            warns.append(f"style_blocks.{k}: «{', '.join(negs[:3])}» — у FLUX, Gemini и Recraft V4 негативов нет, «no X» может "
                         "вызвать X; писать позитивом (словарь замен 01-visual-dna-from-ui.md §4)")
        if re.search(r"\btransparent background\b|\bon transparent\b|\bno background\b", block, re.I):
            warns.append(f"style_blocks.{k}: «transparent background» в промте — модели без альфы рисуют шахматку (H `08/01` §3, "
                         "`alpha_check.py fake`); в блоке — ровный фон цвета секции, альфа — вырезом или векторизацией (поле "
                         "`illustration.background` паспорта — про поставку, не про промт)")
        if re.match(r"^\s*series style", block, re.I):
            warns.append(f"style_blocks.{k}: начинается с ярлыка «Series style» — компилятор добавит свой, будет дубль")
        low = block.lower()
        hits = [w for w in banned if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low)]
        if hits:
            errs.append(f"style_blocks.{k}: запрещённые слова {hits}")
    for e in dna.get("exclusions", {}).get("replace_with", []):
        if e.get("kind") == "object" and e.get("replace_with") and words(e["replace_with"]) > 6:
            warns.append(f"exclusions: замена «{e['replace_with']}» длинная — не вписывает ли она новые предметы в каждый кадр серии?")
    refs = dna.get("references", [])
    style_refs = [r for r in refs if r.get("role") == "style"]
    if len({r.get("class") for r in style_refs}) > 1:
        warns.append("references: стилевые референсы разных классов сюжетов — делите по классам (референс работает на классе, "
                     "на котором собран) и подавайте 1–3 одного класса на вызов")
    if dna.get("icon3d") and not pal.get("env_color"):
        warns.append("icon3d без palette.env_color: фон и рефлексы 3D не привязаны к цвету секции страницы (ореол при вырезе)")
    if dna.get("icon3d") and not dna["icon3d"].get("series_passport"):
        warns.append(f"icon3d без series_passport: камера, свет, поля кадра и контактная тень серии — паспорт 3D-серии "
                     f"({SERIES_PASSPORT}); паспорт визуала держит материал и долю акцента")
    ill = dna.get("illustration") or {}
    ids = [m.get("id") for m in ill.get("metaphors") or []]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        errs.append(f"illustration.metaphors: id повторяются {dup} — экран называет метафору по id")
    if any(x.get("place") == "empty-state" for x in ill.get("places") or []) and not ids:
        warns.append("illustration: пустые состояния без списка метафор — экраны кабинета называют метафору "
                     "(`illustration=` у ui:EmptyState) из этого списка")
    if dna_path:
        for r in refs:
            if not re.match(r"^[a-z]+://", r["src"]) and not (Path(dna_path).parent / r["src"]).exists():
                warns.append(f"references: файл не найден {r['src']}")
        lut = dna.get("grade", {}).get("lut", {}).get("file")
        if lut and not (Path(dna_path).parent / lut).exists():
            warns.append(f"grade.lut.file не найден: {lut}")
    can = dna.get("canaries", [])
    classes = {c.split(":")[0].strip() for c in can if ":" in c}
    if can and len(classes) < 3:
        warns.append("canaries: меньше 3 разных классов («object: …», «interior: …», «nature: …»)")
    comp = dna.get("composition", {})
    tz = comp.get("text_zone_default")
    if tz and tz.get("side") in ("left", "right") and comp.get("subject_region") in ("left-third", "right-third"):
        if (tz["side"] == "left") == (comp["subject_region"] == "left-third"):
            errs.append(f"composition: объект ({comp['subject_region']}) и зона текста ({tz['side']}) на одной стороне")
    if tz and tz.get("side") == "center" and comp.get("subject_region") == "center":
        warns.append("composition: объект и зона текста оба в центре кадра — спецификацию с такой парой компилятор промтов "
                     "отклоняет; объект — в стороне от центральной полосы текста")
    acc = dna.get("acceptance", {})
    if acc.get("text_zone_percentile", 99.9) < 99:
        warns.append("acceptance.text_zone_percentile < 99: скрим по p95 оставил нечитаемыми 14 из 64 комбинаций (ai-media 06/03)")
    nw = pal.get("neutral_wb")
    if nw and nw["target_b"] > 0.008 and "IMG-M04" in dna.get("exclusions", {}).get("forbidden_markers", []):
        warns.append("IMG-M04 (тёплый сдвиг) в запретах, а баланс белого бренда тёплый: сдвиг — стиль, проверять к neutral_wb")
    return errs, warns


# ---------------------------------------------------------------- сетка и замеры с картинки
def make_grid(paths, out, cell=640, cols=3, gutter=10):
    from PIL import Image
    ims = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        h = round(im.height * cell / im.width)
        ims.append(im.resize((cell, h), Image.LANCZOS))
    rows = math.ceil(len(ims) / cols)
    ch = min(i.height for i in ims)
    W = cols * cell + (cols - 1) * gutter
    H = rows * ch + (rows - 1) * gutter
    g = Image.new("RGB", (W, H), "white")
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        g.paste(im.crop((0, (im.height - ch) // 2, cell, (im.height - ch) // 2 + ch)), (c * (cell + gutter), r * (ch + gutter)))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    g.save(out, quality=90)
    return g.size


def strip_gutters(img, thr=0.94, frac=0.95):
    """Убрать белые желоба сетки (строки и столбцы, где ≥ 95 % пикселей почти белые)."""
    import numpy as np
    white = (img > thr).all(axis=2)
    keep_r = white.mean(axis=1) < frac
    keep_c = white.mean(axis=0) < frac
    return img[keep_r][:, keep_c]


def measure_image(path, k=6):
    import numpy as np
    from palette import load, palette, to_oklab, hexs
    img = strip_gutters(load(path, 1200))
    pal = palette(img, k)
    X = to_oklab(img.reshape(-1, 3))
    C = np.hypot(X[:, 1], X[:, 2])
    n = C < 0.03
    return {"palette": [[h.upper(), round(s, 3)] for h, s, _ in pal],
            "neutral_ab": [round(float(X[n, 1].mean()), 4), round(float(X[n, 2].mean()), 4)] if n.any() else None,
            "neutral_share": round(float(n.mean()), 3),
            "median_chroma": round(float(np.median(C)), 4),
            "L_percentiles_1_25_50_75_99": [round(float(v), 3) for v in np.percentile(X[:, 0], [1, 25, 50, 75, 99])],
            "_lab": [c for _, _, c in pal],
            "_pix": X[np.random.default_rng(0).choice(len(X), min(40000, len(X)), replace=False)]}


# ---------------------------------------------------------------- разбор ответа сессии
def extract_json(obj):
    """Ответ сессии (текст с ```json), голый JSON или сохранённый chat completion → dict брифа."""
    if isinstance(obj, dict) and "choices" in obj:
        content = obj["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
        return extract_json(content)
    if isinstance(obj, dict):
        return obj
    s = str(obj).strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", s, re.S)
    if m:
        s = m.group(1).strip()
    start = s.find("{")
    if start < 0:
        raise ValueError("в ответе нет JSON-объекта")
    depth, instr, esc = 0, False, False
    for i, ch in enumerate(s[start:], start):
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(s[start:i + 1])
    raise ValueError("JSON-объект в ответе не закрыт")


BRIEF_KEYS = ["character", "palette", "grade", "light", "camera", "composition", "subject_matter", "style_block_photo",
              "exclusions", "canaries"]


def vlm_problems(v):
    p = [f"нет ключа {k}" for k in BRIEF_KEYS if k not in v]
    pal = v.get("palette", [])
    if not isinstance(pal, list) or not pal:
        p.append("palette пуст")
    else:
        for i, e in enumerate(pal):
            if not re.match(r"^#[0-9A-Fa-f]{6}$", str(e.get("hex", ""))):
                p.append(f"palette[{i}].hex {e.get('hex')!r}")
        s = sum(float(e.get("share", 0) or 0) for e in pal)
        if s > 1.05:
            p.append(f"palette: сумма долей {s:.2f} > 1")
    for k, allowed in (("white_balance", WB), ("contrast", CON), ("saturation", SAT), ("black_point", BLACK), ("grain", GRAIN)):
        val = v.get("grade", {}).get(k)
        if val not in allowed:
            p.append(f"grade.{k} = {val!r} не из {list(allowed)}")
    return p


def map_direction(txt):
    t = (txt or "").lower()
    for key, words_ in (("back", ("back", "behind", "contre", "rim")), ("top", ("overhead", "top", "above", "zenith")),
                        ("left", ("left",)), ("right", ("right",)), ("front", ("front",)), ("side", ("side",))):
        if any(w in t for w in words_):
            return key
    return "ambient"


def map_region(txt):
    t = (txt or "").lower()
    if "left" in t:
        return "left-third"
    if "right" in t:
        return "right-third"
    if "cent" in t or "middle" in t:
        return "center"
    if "top" in t or "upper" in t:
        return "top"
    if "bottom" in t or "lower" in t or "foreground" in t:
        return "bottom"
    return "full-frame"


def vlm_to_dna(v, dna_id, brand=None, measured=None, model=None, runs=1, art_direction=None):
    g, li, cam, comp, sm = v["grade"], v.get("light", {}), v.get("camera", {}), v.get("composition", {}), v.get("subject_matter", {})
    sat, con = g.get("saturation"), g.get("contrast")
    boldness = "bold" if sat == "vivid" or con == "high" else "restrained" if sat == "muted" or con == "low" else "balanced"
    image_palette = []
    for e in v["palette"][:6]:
        role = e.get("role") if e.get("role") in ("background", "dominant", "secondary", "accent", "shadow") else "secondary"
        share = float(e.get("share", 0) or 0)
        image_palette.append({"role": role, "hex": e["hex"].upper(), "name": str(e.get("name", "colour"))[:40],
                              "share_max": round(min(1.0, share * 1.3 + 0.02), 2), "applies_to": "", "source": "vlm"})
    for e in image_palette:
        if not e["applies_to"]:
            e.pop("applies_to")
    height = cam.get("height") if cam.get("height") in ("ground", "eye-level", "high") else "eye-level"
    tb, tol = WB_TARGET_B[g["white_balance"]]
    if measured and measured.get("neutral_ab") and measured.get("neutral_share", 0) > 0.01:
        tb, tol = measured["neutral_ab"][1], 0.006
    region = map_region(comp.get("subject_region"))
    dna = {
        "dna_version": "0.1", "id": dna_id, "brand": brand or "черновик разбора сетки", "checked_at": today(), "status": "draft",
        "approved_by": None,
        "character": {"adjectives": (list(v.get("character", {}).get("adjectives", [])) + ["?", "?", "?"])[:3], "boldness": boldness},
        "palette": {"image_palette": image_palette,
                    "forbidden_hues": [{"from": 270, "to": 320, "reason": "пурпур и неон (IMG-M05), если их нет в бренде"}],
                    "neutral_wb": {"target_b": round(tb, 4), "tol": tol}},
        "grade": {"wb_ab": list(WB[g["white_balance"]]), "chroma": SAT[sat], "black": BLACK[g["black_point"]], "white": 0.975,
                  "contrast": CON[con], "grain_pct": GRAIN[g["grain"]], "lut": {"size": 33, "file": None},
                  "applies_to": ["photo", "video"], "note": "числа — из категорий брифа по таблице vlm_to_dna.py; утвердить глазом"},
        "light": {"direction": map_direction(li.get("direction")), "detail": str(li.get("direction", "")),
                  "quality": li.get("quality") if li.get("quality") in ("soft", "hard", "mixed") else "soft",
                  "time_of_day": str(li.get("time_of_day", ""))},
        "camera": {"lens_mm": int(cam.get("lens_mm") or 35), "height": height,
                   "angle": {"ground": "low-angle", "eye-level": "eye-level", "high": "high-angle"}[height],
                   "depth_of_field": cam.get("depth_of_field") if cam.get("depth_of_field") in ("shallow", "medium", "deep") else "medium"},
        "composition": {"subject_region": region, "negative_space_min": NEG.get(comp.get("negative_space"), 0.3),
                        "max_elements": 3, "asymmetry": region != "center",
                        "horizon": comp.get("horizon_position") if comp.get("horizon_position") in ("top-third", "middle", "bottom-third") else "none",
                        "note": str(comp.get("crop_style", ""))},
        "subject_matter": {"domain_props": (list(sm.get("domain_props", [])) + ["?", "?", "?"])[:max(3, len(sm.get("domain_props", [])))][:16],
                           "motifs": list(sm.get("motifs", []))[:6],
                           "people_policy": "none" if sm.get("people_policy") == "none" else "real-only",
                           "product_policy": "reference-locked"},
        "canaries": [str(c) for c in v.get("canaries", [])][:8] or ["object: ?", "interior: ?", "nature: ?"],
        "style_blocks": {"photo": str(v.get("style_block_photo", "")).strip()},
        "exclusions": {"forbidden_markers": list(DEFAULT_MARKERS), "banned_words": list(DEFAULT_BANNED),
                       "replace_with": [{"what": str(x), "kind": "style"} for x in v.get("exclusions", [])][:6]},
        "post": {"grain_pct": GRAIN[g["grain"]], "scrim": {"max_alpha": 0.55, "shape": "gradient", "percentile": 99.9},
                 "focal_required": True},
        "acceptance": dict(ACCEPTANCE_DEFAULT),
        "provenance": {"created_by": "vlm", "vlm_model": model, "runs": runs, "vlm_raw": v,
                       **({"art_direction": art_direction} if art_direction else {})},
    }
    ct = li.get("color_temp_K")
    if isinstance(ct, (int, float)) and 2000 <= ct <= 12000:
        dna["light"]["cct_K"] = int(ct)
    if len(dna["canaries"]) < 3:
        dna["canaries"] += ["object: ?", "interior: ?", "nature: ?"][:3 - len(dna["canaries"])]
    if dna["composition"]["subject_region"] in ("left-third", "right-third"):
        dna["composition"]["text_zone_default"] = {"side": "right" if region == "left-third" else "left", "share": 0.4}
    if measured:
        dna["palette"]["median_chroma_max"] = round(measured["median_chroma"] * 1.2, 3)
        dna["provenance"]["measured"] = {k: v_ for k, v_ in measured.items() if not k.startswith("_")}
    return dna


def palette_check(dna_or_vlm_palette, measured, thr=0.05):
    """Сколько hex брифа лежат в ΔE OKLab ≤ thr от ближайшего цвета палитры, снятой с пикселей локально, и покрытие цвета."""
    import numpy as np
    labs = [tuple(float(x) for x in c) for c in measured["_lab"]]
    pix = measured.get("_pix")
    rows = []
    for e in dna_or_vlm_palette:
        lab = hex_oklab(e["hex"])
        d = min(math.dist(lab, c) for c in labs)
        row = {"hex": e["hex"], "name": e.get("name"), "dE_to_local": round(d, 4), "ok": d <= thr}
        if pix is not None:
            cov = float((np.sqrt(((pix - np.array(lab)) ** 2).sum(1)) <= thr).mean())
            share = float(e.get("share", e.get("share_max", 0)) or 0)
            row.update({"coverage": round(cov, 3), "declared_share": share,
                        "invented": cov < 0.005 or (share >= 0.1 and cov < share / 3)})
        rows.append(row)
    return rows


# ---------------------------------------------------------------- сравнение прогонов
def compare(a, b):
    out = {}
    ra, rb = a.get("provenance", {}).get("vlm_raw"), b.get("provenance", {}).get("vlm_raw")
    if ra and rb:
        out["grade_categories_equal"] = {k: ra["grade"].get(k) == rb["grade"].get(k) for k in ("white_balance", "contrast", "saturation", "black_point", "grain")}
        out["light_equal"] = {"direction": a["light"]["direction"] == b["light"]["direction"], "quality": a["light"]["quality"] == b["light"]["quality"]}
    else:
        out["grade_numbers_equal"] = {k: a["grade"].get(k) == b["grade"].get(k) for k in ("wb_ab", "chroma", "black", "contrast", "grain_pct")}
        out["light_equal"] = {"direction": a["light"]["direction"] == b["light"]["direction"], "quality": a["light"]["quality"] == b["light"]["quality"]}
    pa, pb = a["palette"]["image_palette"], b["palette"]["image_palette"]
    d1 = [min(dE(x["hex"], y["hex"]) for y in pb) for x in pa]
    d2 = [min(dE(y["hex"], x["hex"]) for x in pa) for y in pb]
    out["palette_dE_sym_mean"] = round((sum(d1) / len(d1) + sum(d2) / len(d2)) / 2, 4)
    gk = out.get("grade_categories_equal") or out.get("grade_numbers_equal")
    out["same_grade_and_light"] = all(gk.values()) and all(out["light_equal"].values())
    return out


# ---------------------------------------------------------------- LUT
def write_lut(dna, out, size=33):
    from palette import parametric_grade, write_cube
    g = dna["grade"]
    f = lambda x: parametric_grade(x, wb_ab=tuple(g["wb_ab"]), chroma=g["chroma"], black=g["black"], white=g["white"],
                                   contrast=g["contrast"])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    write_cube(str(out), f, n=size, title=f"{dna['id']} grade (vlm_to_dna.py lut)")
    return out


def cube_numbers(p):
    rows = []
    for line in open(p):
        parts = line.split()
        if len(parts) == 3:
            try:
                rows.append(tuple(float(x) for x in parts))
            except ValueError:
                pass
    return rows


# ---------------------------------------------------------------- вывод из токенов DTCG
def tok(tokens, path):
    node = tokens
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    val = node.get("$value") if isinstance(node, dict) and "$value" in node else node
    if isinstance(val, str) and val.startswith("{") and val.endswith("}"):
        return tok(tokens, val[1:-1])
    return val


def tok_hex(tokens, path):
    v = tok(tokens, path)
    if isinstance(v, dict):
        v = v.get("hex")
    return v.upper() if isinstance(v, str) and re.match(r"^#[0-9A-Fa-f]{6}$", v) else None


def tok_px(tokens, path):
    v = tok(tokens, path)
    if isinstance(v, dict) and "value" in v:
        return float(v["value"])
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str) and v.endswith("px"):
        return float(v[:-2])
    return None


def name_for(hexv):
    """Английское название цвета для промта по OKLCH (hex без названия не отправлять — BFL)."""
    L, C, H = hex_oklch(hexv)
    warm, cool = 20 <= H <= 110, 180 <= H <= 290
    light = "light " if L > 0.8 else "dark " if L < 0.45 else ""
    if C < 0.02:
        tone = "white" if L > 0.96 else "light grey" if L > 0.8 else "mid grey" if L > 0.55 else "dark grey" if L > 0.3 else "near black"
        tint = "" if C < 0.006 or tone == "white" else ("warm " if warm else "cool " if cool else "")
        return (tint + tone).strip()
    if C < 0.06:
        if L < 0.32:
            return "deep navy" if cool else "dark brown" if warm else "near black"
        return light + ("blue-grey" if cool else "warm grey" if warm else "grey")
    hues = [(40, "red"), (70, "orange"), (95, "amber"), (115, "yellow"), (135, "yellow-green"), (165, "green"), (200, "teal"),
            (240, "sky blue"), (270, "blue"), (295, "indigo"), (330, "violet"), (360, "magenta")]
    hn = next(n for lim, n in hues if H <= lim)
    return ("deep " if L < 0.45 else "light " if L > 0.8 else "") + hn


def from_tokens(tokens, dna_id="from-tokens", adjectives=None, tokens_path=None):
    """Правила R1–R8 файла 01-visual-dna-from-ui.md §3: токены UI → скелет паспорта (без брендовых фото)."""
    canvas = tok_hex(tokens, "color.bg.canvas") or "#FFFFFF"
    surface = tok_hex(tokens, "color.bg.surface") or "#FFFFFF"
    text = tok_hex(tokens, "color.text.primary") or "#111111"
    text2 = tok_hex(tokens, "color.text.secondary") or text
    border = tok_hex(tokens, "color.border.subtle") or tok_hex(tokens, "color.border.default") or "#E5E7EB"
    accent = tok_hex(tokens, "color.accent.solid") or "#2563EB"
    neutral_mid = tok_hex(tokens, "primitive.color.neutral.500") or text2
    n200 = tok_hex(tokens, "primitive.color.neutral.200") or border
    n400 = tok_hex(tokens, "primitive.color.neutral.400") or text2
    a200 = tok_hex(tokens, "primitive.color.accent.200")
    radius = tok_px(tokens, "radius.md") or 6.0
    fam = tok(tokens, "primitive.font.family.serif") and "serif" or ""
    sans = tok(tokens, "primitive.font.family.sans")
    fam_name = (sans[0] if isinstance(sans, list) and sans else str(sans or "")).lower()
    AL, AC, AH = hex_oklch(accent)
    NL, NC, NH = hex_oklch(neutral_mid)
    temp = "neutral" if NC < 0.006 else ("warm" if 20 <= NH <= 110 else "cool" if 180 <= NH <= 290 else "neutral")
    has_raised = tok(tokens, "elevation.raised") is not None
    dark = False
    try:
        dark = "dark" in json.dumps(tokens.get("color", {}).get("bg", {}).get("canvas", {}).get("$extensions", {}))
    except AttributeError:
        pass
    font_voice = ("serif-display" if fam or any(w in fam_name for w in ("serif", "literata", "georgia", "garamond"))
                  else "mono" if "mono" in fam_name else "technical-sans" if "geist" in fam_name or "plex" in fam_name
                  else "neutral-sans")
    rules = []
    # R1 палитра: нейтрали UI + акцент ≤ 3 % площади
    image_palette = [
        {"role": "background", "hex": canvas, "name": name_for(canvas), "share_max": 0.6, "applies_to": "walls, paper, empty surfaces", "source": "token", "token": "color.bg.canvas"},
        {"role": "dominant", "hex": n200, "name": name_for(n200), "share_max": 0.4, "applies_to": "large surfaces", "source": "token", "token": "primitive.color.neutral.200"},
        {"role": "secondary", "hex": n400, "name": name_for(n400), "share_max": 0.2, "applies_to": "secondary objects", "source": "token", "token": "primitive.color.neutral.400"},
        {"role": "shadow", "hex": text, "name": name_for(text), "share_max": 0.12, "applies_to": "shadows and dark details", "source": "token", "token": "color.text.primary"},
        {"role": "accent", "hex": accent, "name": name_for(accent), "share_max": 0.03, "applies_to": "one small object", "strict": True, "source": "token", "token": "color.accent.solid"}]
    illustration_palette = [
        {"role": "background", "hex": surface, "name": name_for(surface), "share_max": 0.6, "applies_to": "background", "source": "token", "token": "color.bg.surface"},
        {"role": "dominant", "hex": n200, "name": name_for(n200), "share_max": 0.4, "applies_to": "large shapes", "source": "token", "token": "primitive.color.neutral.200"},
        {"role": "text", "hex": text, "name": name_for(text), "share_max": 0.08, "applies_to": "lines and small details", "source": "token", "token": "color.text.primary"},
        {"role": "accent", "hex": accent, "name": name_for(accent), "share_max": 0.1, "applies_to": "one key element", "strict": True, "source": "token", "token": "color.accent.solid"}]
    if a200:
        illustration_palette.insert(2, {"role": "secondary", "hex": a200, "name": name_for(a200), "share_max": 0.2, "applies_to": "secondary shapes", "source": "token", "token": "primitive.color.accent.200"})
    rules.append("R1 палитра — нейтрали UI (canvas, neutral 200/400, text.primary) + акцент ≤ 3 % площади фото, ≤ 10 % иллюстрации")
    # R2 потолок хромы — на ступень ниже UI (ui 11/02 §4.4)
    caps = {"large_area_C_max": round(min(0.02, NC + 0.005), 3), "mid_area_C_max": 0.06, "small_area_C_max": round(min(AC, 0.2), 3)}
    rules.append("R2 хрома картинок по площади на ступень ниже UI: > 30 % кадра ≤ min(0,02; C нейтрали + 0,005)")
    # R3 запрещённые оттенки: 270–320° вне бренда
    if hue_in(AH, 270, 320):
        lo, hi = max(270, AH - 12), min(320, AH + 12)
        bands = [{"from": 270, "to": round(lo, 1), "reason": "пурпур (IMG-M05) вне бренд-акцента"} if lo > 270 else None,
                 {"from": round(lo, 1), "to": round(hi, 1), "reason": "полоса бренд-акцента: только акцент", "except_share_max": 0.03},
                 {"from": round(hi, 1), "to": 330, "reason": "пурпур и маджента (IMG-M05)"} if hi < 330 else None]
        bands = [b for b in bands if b]
        rules.append(f"R3 акцент {AH:.0f}° внутри 270–320°: полоса акцента ±12° только для акцента ≤ 3 %")
    else:
        bands = [{"from": 270, "to": 320, "reason": "пурпур и неон (IMG-M05); в бренде нет"}]
        rules.append("R3 полоса 270–320° запрещена: в бренде нет")
    # R4 баланс белого по температуре нейтрали
    tb, tol = WB_TARGET_B[temp]
    rules.append(f"R4 нейтраль {temp} (C {NC:.3f}, H {NH:.0f}°) → b нейтралей кадра {tb:+.3f} ± {tol}")
    # R5 грейд из характера: хрома по акценту, чёрная точка по теме
    chroma = 0.85 if AC < 0.12 else 0.92 if AC < 0.2 else 1.0
    grade = {"wb_ab": list(WB[temp]), "chroma": chroma, "black": 0.02 if dark else 0.03, "white": 0.98, "contrast": 0.1,
             "grain_pct": 1.0, "lut": {"size": 33, "file": None}, "applies_to": ["photo", "icon3d", "render3d", "video"],
             "note": "выведено из токенов (R5); утвердить глазом на canaries"}
    rules.append(f"R5 грейд: хрома ×{chroma} (акцент C {AC:.2f}), баланс белого по нейтрали, зерно 1 %")
    rules.append("R6 свет сверху-слева = направление теней UI (ui 07/02 §2.2)")
    depth = "soft-shadow" if has_raised else "border"
    ill = {"medium": "flat-illustration", "line_px": 1.5, "display_px": 160, "radius_px": radius,
           "perspective": "three-quarter" if has_raised else "flat-front", "fills": "flat",
           "shadows": "soft" if has_raised else "none", "background": "transparent", "accents_per_image": 2, "detail_min_px": 4,
           "saturation_offset": "на 1–2 шага ниже UI", "dark_theme": "two-files", "format": "svg",
           "recolor": {"neutrals": "css-variables", "accents": "fixed"}}
    rules.append(f"R7 иллюстрации: радиус {radius:g} px = radius.md, линия 1,5 = штрих иконок, детали ≥ 4 px")
    rules.append("R8 абстрактный фон — кодом (CSS/SVG/WebGL), не генерацией")
    acc_name = name_for(accent)
    dna = {
        "dna_version": "0.1", "id": dna_id, "brand": "скелет из токенов UI", "checked_at": today(), "status": "draft", "approved_by": None,
        "derived_from_ui": {"tokens": tokens_path or "", "knobs": {
            "accent_hex": accent, "accent_oklch": [round(AL, 3), round(AC, 3), round(AH, 1)], "neutral_temp": temp,
            "neutral_C": round(NC, 3), "base_L": round(hex_oklch(canvas)[0], 3), "radius_px": radius, "font_voice": font_voice,
            "depth_model": depth, "theme": "both" if dark else "light"}, "rules_applied": rules},
        "character": {"adjectives": (adjectives or ["?", "?", "?"])[:3], "boldness": "restrained" if AC < 0.14 else "balanced"},
        "palette": {"image_palette": image_palette, "illustration_palette": illustration_palette, "chroma_caps": caps,
                    "median_chroma_max": 0.04, "forbidden_hues": bands, "neutral_wb": {"target_b": tb, "tol": tol},
                    "env_color": {"hex": canvas, "token": "color.bg.canvas", "note": "фон 3D и выреза = цвет секции страницы"}},
        "grade": grade,
        "light": {"direction": "left", "detail": "soft daylight from the upper left", "quality": "soft", "source": "window"},
        "camera": {"lens_mm": 50, "height": "eye-level", "angle": "eye-level", "depth_of_field": "medium",
                   "capture": "documentary, no styling"},
        "composition": {"subject_region": "right-third", "text_zone_default": {"side": "left", "share": 0.4},
                        "negative_space_min": 0.35, "max_elements": 3, "asymmetry": True, "edge_cut_allowed": True,
                        "master_ratio": "16:9", "phone_frame": "separate-master"},
        "subject_matter": {"domain_props": ["?", "?", "?"], "people_policy": "real-only", "product_policy": "real-photo-only"},
        "illustration": ill,
        "icon3d": {"material": f"matte ceramic in {name_for(n200)} with one {acc_name} part", "camera": "3/4 view from 25 degrees above, 85mm",
                   "accent_share_max": 0.15, "series_passport": SERIES_PASSPORT},
        "abstract": {"policy": "code-first"},
        "canaries": ["object: ?", "interior: ?", "nature: ?", "product-like: ?", "abstract: ?"],
        "style_blocks": {
            "illustration": (f"Flat vector illustration: simple geometric shapes with {radius:g} px rounded corners, flat fills in "
                             f"{name_for(n200)} {n200} and {name_for(surface)} with {acc_name} {accent} as the only accent, "
                             f"1.5 px lines in {name_for(text)} {text}, smooth flat colour only, one light from the upper left, "
                             f"plain flat {name_for(surface)} {surface} background, generous empty space."),
            "icon3d": (f"Single object as a matte ceramic figure in {name_for(n200)} with one {acc_name} part; 3/4 view from 25 "
                       f"degrees above, 85mm; soft key light from the upper left, gentle fill and rim; soft contact shadow; plain "
                       f"light background; clean text-free surfaces.")},
        "exclusions": {"forbidden_markers": list(DEFAULT_MARKERS), "banned_words": list(DEFAULT_BANNED), "replace_with": [
            {"what": "people", "kind": "object", "replace_with": "no one in the frame"},
            {"what": "readable text", "kind": "artifact", "replace_with": "clean unmarked surfaces"}]},
        "post": {"grain_pct": 1.0, "scrim": {"color": text, "max_alpha": 0.55, "shape": "gradient", "percentile": 99.9},
                 "focal_required": True},
        "acceptance": dict(ACCEPTANCE_DEFAULT),
        "provenance": {"created_by": "script", "runs": 0, "notes": "vlm_to_dna.py from-tokens; фото-стиль (style_blocks.photo), "
                       "сюжеты и canaries заполняет человек или разбор сетки брендовых фото (vlm_to_dna.py build); места "
                       "иллюстраций и список метафор — владелец продукта"},
    }
    return dna


# ---------------------------------------------------------------- паспорт → спецификация ассета (05-prompting v0.2)
MEDIUM_3D = (("glass", "glass-3d"), ("clay", "clay-3d"), ("ceramic", "clay-3d"), ("matte", "clay-3d"))


def edit_operations():
    """Операции правки — перечень edit.operation схемы спецификации ассета."""
    return load_json(SPEC_SCHEMA_PATH)["properties"]["edit"]["properties"]["operation"]["enum"]


def pick_palette(entries, limit=5):
    order = {"dominant": 0, "background": 1, "secondary": 2, "accent": 3, "text": 4, "shadow": 5, "highlight": 6}
    sel = sorted(entries, key=lambda e: order.get(e["role"], 9))[:limit]
    acc = sum(e["share_max"] for e in sel if e["role"] == "accent")
    rest = sum(e["share_max"] for e in sel if e["role"] != "accent")
    k = min(1.0, (0.98 - acc) / rest) if rest > 0 else 1.0
    out = []
    for e in sel:
        p = {"role": e["role"], "hex": e["hex"].upper(), "name": e["name"],
             "share": round(e["share_max"] * (1 if e["role"] == "accent" else k), 3)}
        if e.get("applies_to"):
            p["applies_to"] = e["applies_to"]
        if e.get("strict"):
            p["strict"] = True
        out.append(p)
    return out


def to_spec(dna, kind, task, subject, slot="hero", ratio=None, text_zone=True, ref_class=None, dna_path=None, out_path=None,
            shot=None, section=None, purpose=None, edit=None):
    """Паспорт → спецификация ассета. section — id секции плана страницы, slot — id строки плана ассетов (без section
    секцией служит slot). edit = {"operation", "source"} — профиль правки настоящего кадра: исключения паспорта и
    композиция генерации с нуля (область объекта, ракурс, зона текста, правило «против среднего») в спецификацию не
    идут — кадр уже снят; референсы паспорта идут только при названном ref_class; что менять (`edit.changes`) и что
    сохранить (`edit.keep`) дописывает автор."""
    comp, cam, light, pal = dna["composition"], dna["camera"], dna["light"], dna["palette"]
    if kind not in dna["style_blocks"]:
        raise SystemExit(f"в паспорте нет style_blocks.{kind}")
    entries = pal["image_palette"] if kind == "photo" else pal.get("illustration_palette") or pal["image_palette"]
    spec = {"spec_version": "0.2", "id": f"{dna['id']}-{slot}-{kind}", "checked_at": today(), "brief_language": "en",
            "task": task, "role": {"section": section or slot, "slot": slot, "purpose": purpose or f"{kind} of the {dna['id']} series",
                                   "series_id": dna["id"]},
            "subject": {"summary": subject},
            "composition": {"shot": shot or {"photo": "medium", "illustration": "medium", "icon3d": "close-up"}[kind]},
            "palette": pick_palette(entries, 4 if kind == "photo" and dna.get("references") else 5), "text": {"mode": "none"},
            "output": {"primary_ratio": ratio or (comp.get("master_ratio", "16:9") if kind == "photo" else "1:1"), "resolution": "1K"}}
    c = spec["composition"]
    if kind == "photo":
        if not edit:
            c["subject_region"] = comp["subject_region"]
            if cam.get("angle"):
                c["angle"] = cam["angle"]
        spec["camera"] = {k: cam[k] for k in ("lens_mm", "depth_of_field", "capture") if k in cam}
        spec["light"] = {k: light[k] for k in ("direction", "quality", "time_of_day", "source") if light.get(k)}
        if dna.get("materials"):
            spec["materials"] = dna["materials"][:3]
        spec["style"] = {"medium": "photograph"}
        gp = dna["grade"].get("grain_pct", 0)
        if gp:
            spec["style"]["grain"] = "fine natural film grain" if gp < 2.5 else "visible natural film grain"
        tz = comp.get("text_zone_default")
        if text_zone and tz and not edit:
            s = tz["share"]
            rect = {"left": [0, 0, s, 1], "right": [round(1 - s, 3), 0, 1, 1], "top": [0, 0, 1, s], "bottom": [0, round(1 - s, 3), 1, 1],
                    "center": [round((1 - s) / 2, 3), 0, round((1 + s) / 2, 3), 1]}[tz["side"]]   # center — полоса шириной share
            bg = next((e for e in pal["image_palette"] if e["role"] == "background"), None)
            surface = tz.get("surface") or (bg["applies_to"] if bg and bg.get("applies_to") else "plain, evenly lit area")
            c["text_zone"] = {"side": tz["side"], "rect": rect, "tone": "even, low contrast", "surface": surface,
                              "purpose": "caption" if tz["side"] == "bottom" and s <= 0.3 else "headline"}
            spec["text"] = {"mode": "html_overlay"}
    elif kind == "icon3d":
        if not edit:
            c["subject_region"] = "center"
            c["angle"] = "high-angle"
        ic = dna.get("icon3d", {})
        spec["light"] = {"direction": "left", "quality": "soft", "source": "soft key light from the upper left, gentle fill and rim"}
        mat = ic.get("material", "")
        spec["style"] = {"medium": next((m for w, m in MEDIUM_3D if w in mat.lower()), "3d-render")}
        ents = pal.get("illustration_palette") or pal["image_palette"]
        bgc = next((e for e in ents if e["role"] == "background"), None)
        env = pal.get("env_color")
        if env:  # фон 3D-иконки = цвет секции страницы (W5 §8): рефлексы и контактная тень под него
            bgc = {"role": "background", "hex": env["hex"], "name": name_for(env["hex"]), "share_max": 0.55}
        body = next((e for e in ents if e["role"] in ("dominant", "secondary")), None)
        acc = next((e for e in ents if e["role"] == "accent"), None)
        spec["palette"] = pick_palette([dict(e, applies_to=t, share_max=sh) for e, t, sh in
                                        ((bgc, "plain background", 0.55), (body, "object body", 0.3), (acc, "single accent part of the object", 0.1)) if e])
        if mat:
            spec["materials"] = [mat]
    else:
        il = dna.get("illustration", {})
        medium = il.get("medium", "flat-illustration")
        spec["style"] = {"medium": medium if medium in ("flat-illustration", "vector", "line-art", "watercolor", "gouache", "collage") else "other"}
        if il.get("line_px"):
            spec["style"]["line"] = f"uniform {il['line_px']:g} px lines at {il.get('display_px', 160)} px width"
        if not edit:
            c["subject_region"] = "center"
    spec["series"] = {"id": dna["id"], "block": dna["style_blocks"][kind],
                      "avoid_average": bool(comp.get("asymmetry")) and kind == "photo" and not edit}
    refs = [r for r in dna.get("references", []) if r["role"] in ("style", "palette", "material")
            and (ref_class is None or r.get("class") == ref_class)][:3]
    if edit and ref_class is None:  # вход правки — сам кадр; референсы паспорта («сюжет и сцена — из промта») — по явному классу
        refs = []
    if refs:
        base_in = Path(dna_path).parent if dna_path else Path.cwd()
        base_out = Path(out_path).parent if out_path else Path.cwd()
        spec["references"] = []
        for i, r in enumerate(refs, 1):
            src = r["src"] if re.match(r"^[a-z]+://", r["src"]) else os.path.relpath((base_in / r["src"]).resolve(), base_out.resolve())
            e = {"id": f"ref{i}", "src": src, "role": r["role"]}
            if r.get("note"):
                e["note"] = r["note"]
            spec["references"].append(e)
        spec["series"]["reference_ids"] = [e["id"] for e in spec["references"]]
    ex = dna["exclusions"].get("replace_with", [])
    if kind != "photo":  # фото-замены («soft late-morning daylight», «desk») не вносить в иллюстрации и 3D
        ex = [e for e in ex if e.get("kind") in ("artifact", "service")]
    if ex and not edit:  # в правке настоящего кадра запреты генерации с нуля («без людей») стёрли бы то, что снято
        spec["exclusions"] = [{k: e[k] for k in ("what", "kind", "replace_with") if e.get(k)} for e in ex]
    if edit:
        src = edit["source"]
        if not re.match(r"^[a-z]+://", src):
            src = os.path.relpath(Path(src).resolve(), (Path(out_path).parent if out_path else Path.cwd()).resolve())
        spec["edit"] = {"operation": edit["operation"], "source": src}
    return spec


# ---------------------------------------------------------------- скрим: арт-дирекция против паспорта
SCRIM_WORD = re.compile(r"скрим|scrim", re.I)
OTHER_LAYER = re.compile(r"вуал|veil|оверле|overlay|затемнени", re.I)   # число после этих слов — не о скриме
SCRIM_ALPHA = re.compile(r"(?<![\w.,])(?:(0[.,]\d{1,3}|1[.,]0{1,3})(?!\d|[.,]\d|\s?%)|(\d{1,3}(?:[.,]\d+)?)\s?%)")
SIZE_AFTER = re.compile(r"\s*(?:высот|ширин|кадр|экран|окна|of the |height|width)", re.I)   # доля размера, а не прозрачность


def scrim_mentions(obj, path=""):
    """Числа прозрачности, названные рядом со словом «скрим» в текстовых полях арт-дирекции → [(путь поля, значение
    0–1, фраза)]. Берётся число в той же фразе после слова «скрим»: доля 0,xx или проценты; число размера («30 %
    высоты») и число после слова о другом слое («вместо вуали 25 %») не берутся."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += scrim_mentions(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += scrim_mentions(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        for clause in re.split(r"[;\n]|\.\s", obj):
            m = SCRIM_WORD.search(clause)
            if not m:
                continue
            tail = clause[m.end():]
            other = OTHER_LAYER.search(tail)
            tail = tail[:other.start()] if other else tail
            for n in SCRIM_ALPHA.finditer(tail):
                if SIZE_AFTER.match(tail[n.end():]):
                    continue
                val = float(n.group(1).replace(",", ".")) if n.group(1) else float(n.group(2).replace(",", ".")) / 100
                if 0 <= val <= 1:
                    out.append((path, val, " ".join(clause.split())[:160]))
    return out


def scrim_check(dna, art_direction):
    """Скрим арт-дирекции против паспорта визуала: числа прозрачности скрима из текстов арт-дирекции сверяются с
    `post.scrim.max_alpha` паспорта (равенство до сотых). Фраза сходится, если одно из её чисел равно значению паспорта
    (диапазон «от 0,3 до 0,55»); расхождение или число без значения в паспорте — предупреждение."""
    alpha = ((dna.get("post") or {}).get("scrim") or {}).get("max_alpha")
    phrases = {}
    for path, val, quote in scrim_mentions(art_direction):
        phrases.setdefault((path, quote), []).append(val)
    warns = []
    for (path, quote), vals in phrases.items():
        named = ", ".join(f"{v:g}" for v in vals)
        if alpha is None:
            warns.append(f"скрим: арт-дирекция ({path}) называет {named} — «{quote}», а в паспорте post.scrim.max_alpha не задан")
        elif all(round(v, 2) != round(alpha, 2) for v in vals):
            warns.append(f"скрим: арт-дирекция ({path}) называет {named} — «{quote}», в паспорте post.scrim.max_alpha {alpha:g}: "
                         "значения расходятся — привести к одному")
    return warns


# ---------------------------------------------------------------- команды
def cmd_grid(a):
    size = make_grid(a.images, a.out, a.cell, a.cols)
    print(json.dumps({"grid": a.out, "size": size}, ensure_ascii=False))


def judge_model():
    """Модель сессии — из описания агента design-judge (frontmatter `model:`): запись в паспорт, а не выбор кода."""
    try:
        txt = JUDGE_AGENT.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.match(r"---\n(.*?)\n---", txt, re.S)
    mm = re.search(r"^model:\s*(\S+)", m.group(1), re.M) if m else None
    return mm.group(1).strip("'\"") if mm else None


def grid_prompt(pkg, frame):
    """Задание одной сессии: сетка бренда → JSON-бриф по рубрике GRID_REQUEST."""
    L = ["# Задание · рубрика · сетка бренда → бриф паспорта визуала", "",
         f"Ты — агент `design-judge`; протокол — `{JUDGE_PROTOCOL}` (путь от корня репозитория), §1–§3. Открывай только "
         "файлы, названные в этом задании.", "", "## Задача", "",
         "Описать видимые приметы изображений бренда на сетке — основа паспорта визуала (ai-media 06/01): цвет, грейд, свет, "
         "камера, композиция, реквизит, блок стиля, запреты и канарейки.", "", "## Кадры", "",
         f"- Сетка: `{Path(pkg) / frame['frame']}` — {frame['w']}×{frame['h']}, {frame['format']}; белые желоба между картинками",
         "", "## Рубрика", "", GRID_SYSTEM, "", GRID_REQUEST, "", "## Ответ", "",
         "Первая строка — «рубрика · сетка бренда · входы, чего не хватило». Затем один блок ```json — объект с ключами "
         "рубрики выше.", "", *GRID_RULES]
    return "\n".join(L) + "\n"


def build_package(grid, out_root=None, name=None, runs=2, force=False):
    """Пакет той же формы, что пакет судьи (judge-package/1): сетка — PNG под нейтральным именем, задание на прогон,
    README; ключ с исходником сетки — рядом с папкой пакета. Прогоны — разные сессии: сверка — compare."""
    from PIL import Image
    grid = Path(grid).resolve()
    if runs < 1:
        raise ValueError("--runs — не меньше 1")
    name = name or f"brand-grid-{hashlib.sha256(grid.read_bytes()).hexdigest()[:8]}"
    out_root = Path(out_root).resolve() if out_root else kbpaths.out("ai-media", "dna")
    pkg = out_root / name
    if pkg.exists():
        if any((pkg / "answers").glob("*")) and not force:
            raise ValueError(f"в пакете {pkg} уже есть ответы — другое имя (--name) или --force")
        shutil.rmtree(pkg)
    for d in ("frames", "jobs", "answers"):
        (pkg / d).mkdir(parents=True)
    im = Image.open(grid).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    png = buf.getvalue()
    frame = {"frame": f"frames/{hashlib.sha256(png).hexdigest()[:16]}.png", "w": im.width, "h": im.height, "format": "PNG"}
    (pkg / frame["frame"]).write_bytes(png)
    jobs, key_jobs = [], {}
    for run in range(1, runs + 1):
        jid = f"j{run:03d}"
        (pkg / "jobs" / f"{jid}.md").write_text(grid_prompt(pkg, frame), encoding="utf-8")
        jobs.append({"id": jid, "kind": "рубрика", "prompt": f"jobs/{jid}.md", "frames": [frame["frame"]], "answer": f"answers/{jid}.md"})
        key_jobs[jid] = {"mode": "brand-grid", "run": run}
    session = {"agent": "design-judge", "model": judge_model()}
    created = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    manifest = {"schema": "judge-package/1", "package": name, "created": created, "tool": "vlm_to_dna.py build",
                "mode": "brand-grid", "kind": "рубрика", "runs": runs, "orders": 1,
                "rubric": {"id": "brand-grid", "sha256": hashlib.sha256((GRID_SYSTEM + GRID_REQUEST).encode()).hexdigest()[:16]},
                "response_schema": None, "session": session, "jobs": jobs, "warnings": []}
    dump_json(manifest, pkg / "manifest.json")
    (pkg / "README.md").write_text(
        f"# Пакет разбора сетки бренда · {name}\n\nЗадания для отдельных сессий Opus — агента `design-judge`: сетка бренд-картинок "
        f"→ JSON-бриф паспорта визуала. Состав: кадр — 1, прогонов — {runs}; заданий — {runs}.\n\n"
        "1. Каждое задание `jobs/<id>.md` — отдельный вызов инструмента `Agent` с `subagent_type: design-judge`; текст задания —\n"
        "   промт вызова целиком. Модель в вызове не передают — её задаёт описание агента.\n"
        "2. Ответ агента целиком — в `answers/<id>.md` (тот же id); прогоны не видят друг друга.\n"
        "3. Ответы собраны — `vlm_to_dna.py parse <папка пакета> --out dna.json`: черновик паспорта, сверка палитры с пикселями\n"
        "   сетки и прогонов между собой; паспорт утверждает человек.\n", encoding="utf-8")
    key_path = out_root / f"{name}.key.json"
    dump_json({"schema": "judge-key/1", "package": name, "package_dir": str(pkg), "created": created, "mode": "brand-grid",
               "runs": runs, "grid": str(grid), "session": session, "jobs": key_jobs}, key_path)
    return {"package": str(pkg), "key": str(key_path), "jobs": runs, "frame": frame["frame"]}


def cmd_build(a):
    try:
        r = build_package(a.grid, a.out, a.name, a.runs, a.force)
    except ValueError as e:
        print(f"vlm_to_dna.py build: {e}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(r, ensure_ascii=False, indent=1))


def read_answers(src):
    """Папка пакета (answers/*) или файл ответа → ([(имя, ответ)], ключ пакета | None). Ответ — текст сессии с блоком
    ```json, голый JSON или сохранённый chat completion."""
    P = Path(src)
    if P.is_dir():
        kp = P.with_name(P.name + ".key.json")
        K = load_json(kp) if kp.exists() else None
        out = []
        for f in sorted((P / "answers").glob("*")):
            if f.suffix in (".md", ".txt", ".json"):
                txt = f.read_text(encoding="utf-8")
                try:
                    out.append((f.name, json.loads(txt) if f.suffix == ".json" else txt))
                except json.JSONDecodeError:
                    out.append((f.name, txt))
        return out, K
    txt = P.read_text(encoding="utf-8")
    try:
        return [(P.name, json.loads(txt))], None
    except json.JSONDecodeError:
        return [(P.name, txt)], None


def parse_response(resp_obj, dna_id, brand=None, grid=None, model=None, runs=1, art_direction=None, measured=None):
    v = extract_json(resp_obj)
    probs = vlm_problems(v)
    if any(p.startswith("нет ключа") or p.startswith("grade.") or p == "palette пуст" for p in probs):
        return None, {"brief_problems": probs}
    measured = measured or (measure_image(grid) if grid else None)
    dna = vlm_to_dna(v, dna_id, brand, measured, model, runs, art_direction)
    report = {"brief_problems": probs}
    if measured:
        rows = palette_check(v["palette"], measured)
        report["palette_check"] = rows
        report["palette_criterion"] = f"{sum(r['ok'] for r in rows)} из {len(rows)} hex в ΔE ≤ 0,05 (успех — ≥ 3 из 5)"
        report["palette_pass"] = sum(r["ok"] for r in rows) >= 3
        report["invented_colours"] = [r["hex"] for r in rows if r.get("invented")]
    errs, eng = schema_errors(dna)
    lerrs, lwarns = lint(dna)
    report.update({"schema_errors": errs, "validator": eng, "lint_errors": lerrs, "lint_warnings": lwarns})
    return dna, report


def parse_answers(src, dna_id=None, brand=None, grid=None, art_direction=None):
    """Ответы пакета или файла → черновик паспорта из первого годного ответа; сетка — из ключа пакета, если не задана;
    два ответа и больше — сверка прогонов (compare) с первым. → (паспорт | None, отчёт)."""
    answers, K = read_answers(src)
    if not answers:
        return None, {"error": f"нет ответов в {src}"}
    grid = grid or (K or {}).get("grid")
    model = ((K or {}).get("session") or {}).get("model")
    dna_id = dna_id or re.sub(r"[^a-z0-9-]+", "-", Path(src).stem.lower()).strip("-")[:60] or "brand-grid-draft"
    measured = measure_image(grid) if grid and Path(grid).exists() else None
    drafts, reports = [], {}
    for name, obj in answers:
        try:
            d, r = parse_response(obj, dna_id, brand, None, model, 1, art_direction, measured)
        except ValueError as e:
            d, r = None, {"error": str(e)}
        reports[name] = r
        if d is not None:
            drafts.append((name, d))
    if not drafts:
        return None, {"answers": reports}
    name0, dna = drafts[0]
    dna["provenance"]["runs"] = len(drafts)
    rep = dict(reports[name0])
    rep["answers"] = len(answers)
    rep["valid_answers"] = len(drafts)
    if len(drafts) > 1:
        rep["runs_compare"] = {n: compare(dna, d) for n, d in drafts[1:]}
    rep["schema_errors"], rep["validator"] = schema_errors(dna)
    return dna, rep


def cmd_parse(a):
    dna, rep = parse_answers(a.response, a.id, a.brand, a.grid, a.art_direction)
    if dna is None:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        sys.exit(2)
    dump_json(dna, a.out)
    print(json.dumps({"dna": a.out, **rep}, ensure_ascii=False, indent=1))
    sys.exit(0 if not rep["schema_errors"] and not rep["lint_errors"] else 1)


def cmd_validate(a):
    ad = None
    if a.art_direction:
        try:
            ad = load_json(a.art_direction)
        except (OSError, json.JSONDecodeError) as e:
            print(f"vlm_to_dna.py validate: арт-дирекция не читается — {e}", file=sys.stderr)
            sys.exit(2)
    bad = 0
    for p in a.files:
        dna = load_json(p)
        errs, eng = schema_errors(dna, force_builtin=a.builtin)
        lerrs, lwarns = lint(dna, p)
        if ad is not None:
            lwarns += scrim_check(dna, ad)
        ok = not errs and not lerrs
        bad += not ok
        print(json.dumps({"file": p, "ok": ok, "validator": eng, "schema_errors": errs[:20], "lint_errors": lerrs,
                          "lint_warnings": lwarns}, ensure_ascii=False, indent=1))
    sys.exit(1 if bad else 0)


def cmd_compare(a):
    print(json.dumps(compare(load_json(a.a), load_json(a.b)), ensure_ascii=False, indent=1))


def cmd_lut(a):
    dna = load_json(a.dna)
    write_lut(dna, a.out, a.size)
    print(json.dumps({"lut": a.out, "size": a.size, "grade": dna["grade"]}, ensure_ascii=False))


def cmd_from_tokens(a):
    tokens = load_json(a.tokens)
    adj = [x.strip() for x in a.adjectives.split(",")] if a.adjectives else None
    dna = from_tokens(tokens, a.id, adj, a.tokens)
    dump_json(dna, a.out)
    errs, eng = schema_errors(dna)
    lerrs, lwarns = lint(dna)
    print(json.dumps({"dna": a.out, "knobs": dna["derived_from_ui"]["knobs"], "schema_errors": errs, "validator": eng,
                      "lint_errors": lerrs, "lint_warnings": lwarns}, ensure_ascii=False, indent=1))


def cmd_to_spec(a):
    if bool(a.edit) != bool(a.operation):
        print("vlm_to_dna.py to-spec: профиль правки — оба ключа: --edit SOURCE и --operation OP", file=sys.stderr)
        sys.exit(2)
    dna = load_json(a.dna)
    spec = to_spec(dna, a.kind, a.task, a.subject, a.slot, a.ratio, not a.no_text_zone, a.ref_class, a.dna, a.out, a.shot,
                   section=a.section, edit={"operation": a.operation, "source": a.edit} if a.edit else None)
    errs, eng = schema_errors(spec, SPEC_SCHEMA_PATH)
    if a.out:
        dump_json(spec, a.out)
    print(json.dumps({"spec": a.out or "(stdout)", "asset_spec_errors": errs, "validator": eng,
                      **({} if a.out else {"body": spec})}, ensure_ascii=False, indent=1))
    sys.exit(1 if errs else 0)


# ---------------------------------------------------------------- самопроверка
STUB_BRIEF = {  # заглушка ответа сессии: поля брифа без палитры; палитру самопроверка берёт с пикселей сетки
    "character": {"adjectives": ["calm", "natural", "seasonal"]},
    "grade": {"white_balance": "warm", "contrast": "medium", "saturation": "natural", "black_point": "neutral", "grain": "fine"},
    "light": {"direction": "late-morning sun from the upper left", "quality": "soft", "time_of_day": "late morning", "color_temp_K": 5200},
    "camera": {"lens_mm": 35, "height": "eye-level", "depth_of_field": "deep"},
    "composition": {"subject_region": "tree line across the upper third", "horizon_position": "top-third", "negative_space": "high",
                    "crop_style": "wide, lawn fills the lower half"},
    "subject_matter": {"domain_props": ["lawn", "fallen leaves", "birch trees", "pine trees", "maple with red leaves"],
                       "motifs": ["autumn foliage", "open lawn"], "people_policy": "none"},
    "style_block_photo": ("Documentary outdoor photograph of a city park in early autumn, soft late-morning sun, yellow and rust "
                          "foliage over a muted green lawn with scattered fallen leaves, pale clear sky, 35mm at eye level, deep "
                          "depth of field, fine natural grain, no retouching."),
    "exclusions": ["golden-hour glow", "shallow depth of field", "saturated orange cast", "people posing", "fog or mist", "lens flare"],
    "canaries": ["a ceramic mug on a garden table", "a small cafe interior at noon", "a riverside path with one oak",
                 "soft abstract shapes of leaves", "a folded paper map on a bench"]}
STUB_BAD_PALETTE = [{"hex": "#E8A33D", "name": "golden yellow", "role": "dominant", "share": 0.3},  # «идеализированные» цвета
                    {"hex": "#C4452B", "name": "rust red", "role": "accent", "share": 0.1},
                    {"hex": "#4F7A2E", "name": "grass green", "role": "secondary", "share": 0.3},
                    {"hex": "#87CEEB", "name": "sky blue", "role": "background", "share": 0.2},
                    {"hex": "#3B2A1A", "name": "bark brown", "role": "shadow", "share": 0.1}]


def synthetic_grid(tmp):
    """Сетка из трёх синтетических «снимков» одной съёмки (тёплый свет, небо, трава, пятно кроны) — вход самопроверки."""
    import numpy as np
    from PIL import Image
    paths = []
    for i, warm in enumerate((0, 8, 16)):
        rng = np.random.default_rng(10 + i)
        H, W = 480, 720
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        sky = np.stack([160 + 25 * yy / H + warm, 190 + 15 * yy / H, 215 - warm / 2 + 0 * xx], -1)
        lawn = np.stack([110 + 25 * xx / W + warm, 118 + 10 * xx / W, 62 + 0 * yy], -1)
        img = np.where((yy > H * (0.45 + 0.05 * i))[..., None], lawn, sky)
        crown = ((yy - H * 0.4) ** 2 / 80 ** 2 + (xx - W * (0.3 + 0.2 * i)) ** 2 / 110 ** 2) < 1
        img[crown] = np.array([176 + warm, 118, 44])
        img = img + rng.normal(0, 4, img.shape)
        p = Path(tmp) / f"shot{i}.png"
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(p)
        paths.append(str(p))
    grid = Path(tmp) / "grid.jpg"
    make_grid(paths, grid, cell=480, cols=3)
    return grid


def selftest():
    import tempfile
    res, fails = [], []

    def check(name, cond, info=""):
        res.append(("PASS" if cond else "FAIL", name, info))
        if not cond:
            fails.append(name)

    tmp = Path(tempfile.mkdtemp(prefix="vlm_to_dna_"))
    # 1. build — пакет той же формы, что пакет судьи: кадр сетки, задание на прогон, ключ вне пакета
    grid = synthetic_grid(tmp)
    r = build_package(grid, tmp / "out", "grid", runs=2)
    pkg = Path(r["package"])
    man = load_json(pkg / "manifest.json")
    jobs = sorted((pkg / "jobs").glob("*.md"))
    prompt = jobs[0].read_text(encoding="utf-8") if jobs else ""
    check("build: пакет judge-package/1 — 2 задания, кадр PNG под нейтральным именем, сессия design-judge",
          man["schema"] == "judge-package/1" and len(jobs) == 2 and re.fullmatch(r"frames/[0-9a-f]{16}\.png", r["frame"])
          and man["session"]["agent"] == "design-judge", (len(jobs), r["frame"], man["session"]))
    check("build: задание — кадр пакета, рубрика брифа, формат ответа", str(pkg / r["frame"]) in prompt and GRID_REQUEST in prompt
          and "```json" in prompt)
    key = load_json(Path(r["key"]))
    check("build: ключ с исходником сетки — рядом с пакетом, в пакете имени сетки нет",
          Path(r["key"]).parent == pkg.parent and key["grid"] == str(grid.resolve())
          and "grid.jpg" not in "".join(f.read_text(encoding="utf-8") for f in pkg.rglob("*") if f.suffix in (".md", ".json")))
    # 2. разбор ответов пакета: правдоподобный бриф (цвета — с пикселей сетки) и сверка двух прогонов
    measured = measure_image(str(grid))
    roles = ["dominant", "secondary", "background", "secondary", "shadow"]
    good = dict(STUB_BRIEF, palette=[{"hex": h, "name": f"colour {i}", "role": roles[i], "share": round(min(sh, 0.4), 2)}
                                     for i, (h, sh) in enumerate(measured["palette"][:5])])
    for jid in ("j001", "j002"):
        (pkg / "answers" / f"{jid}.md").write_text("рубрика · сетка бренда · входов хватило\n\n```json\n" + json.dumps(good) + "\n```\n",
                                                   encoding="utf-8")
    dna, rep = parse_answers(pkg, "grid-good", "заглушка")
    check("parse: ответы пакета → паспорт проходит схему и линт", dna is not None and not rep["schema_errors"] and not rep["lint_errors"],
          (rep.get("schema_errors"), rep.get("lint_errors")))
    check("parse: палитра брифа совпала с пикселями сетки (≥ 3 из 5)", rep.get("palette_pass") is True, rep.get("palette_criterion"))
    check("parse: два прогона — сверка совпала, runs = 2, модель — из описания агента",
          dna["provenance"]["runs"] == 2 and all(c["same_grade_and_light"] for c in rep.get("runs_compare", {}).values())
          and dna["provenance"]["vlm_model"] == man["session"]["model"], (dna["provenance"]["runs"], rep.get("runs_compare")))
    check("parse: баланс белого — замер нейтралей сетки, а не таблица категорий брифа",
          measured.get("neutral_ab") and dna["palette"]["neutral_wb"] == {"target_b": round(measured["neutral_ab"][1], 4), "tol": 0.006},
          (dna["palette"]["neutral_wb"], measured.get("neutral_ab")))
    dump_json(dna, tmp / "good.json")
    bad = dict(STUB_BRIEF, palette=STUB_BAD_PALETTE, grade=dict(STUB_BRIEF["grade"], saturation="vivid"),
               style_block_photo="A stunning cinematic autumn park, vibrant golden foliage, dramatic light.")
    (tmp / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
    dna_b, rep_b = parse_answers(tmp / "bad.json", "grid-bad", "заглушка", str(grid), "design/promo/art-direction.json")
    check("parse: «идеализированная» палитра — критерий не выполнен, придуманные цвета помечены",
          rep_b.get("palette_pass") is False and "#E8A33D" in rep_b.get("invented_colours", []), rep_b.get("palette_criterion"))
    check("parse: слова stunning/cinematic/vibrant/dramatic ловит линт", any("запрещённые слова" in e for e in rep_b["lint_errors"]),
          rep_b["lint_errors"])
    check("parse: ссылка на арт-дирекцию — в происхождении паспорта", dna_b["provenance"].get("art_direction") == "design/promo/art-direction.json"
          and not schema_errors(dna_b)[0], dna_b["provenance"].get("art_direction"))
    broken = copy.deepcopy(good)
    del broken["grade"]
    d0, r0 = parse_response(broken, "x", None, None)
    check("parse: нет grade → отказ с причиной", d0 is None and any("grade" in p for p in r0["brief_problems"]), r0["brief_problems"][:3])
    c = compare(dna, dna_b)
    check("compare: разная насыщенность → «grade и light не совпали»", c["same_grade_and_light"] is False, c)
    # 3. примеры паспортов базы: схема (jsonschema и встроенный валидатор) и линт
    samples = sorted(EXAMPLES.glob("dna-*.json")) + sorted(ROOT.glob("14-recipes/examples/*/brand/dna-*.json"))
    for p in samples:
        d = load_json(p)
        e1, eng = schema_errors(d)
        e2, _ = schema_errors(d, force_builtin=True)
        le, lw = lint(d, p)
        check(f"пример {p.name}: схема ({eng}) и встроенный валидатор — 0 ошибок, линт — 0 ошибок", not e1 and not e2 and not le, (e1 or e2 or le)[:3])
    d = load_json(EXAMPLES / "dna-warm-consumer.json")
    d["palette"]["image_palette"][0]["hex"] = "#7B6A3"
    d["composition"]["subject_region"] = "left"
    d["grade"]["chroma"] = 2
    d["extra"] = 1
    e1, eng = schema_errors(d)
    e2, _ = schema_errors(d, force_builtin=True)
    check("сломанный паспорт: ≥ 4 ошибки у обоих валидаторов", len(e1) >= 4 and len(e2) >= 4, (len(e1), len(e2), eng))
    d = load_json(EXAMPLES / "dna-strict-saas.json")
    d["palette"]["image_palette"].append({"role": "secondary", "hex": "#8B5CF6", "name": "violet", "share_max": 0.2})
    le, _ = lint(d)
    check("линт: фиолетовый #8B5CF6 (293°) с долей 0,2 в запрещённой полосе", any("запрещённой полосе" in e for e in le), le)
    d = load_json(EXAMPLES / "dna-strict-saas.json")
    d["icon3d"].pop("series_passport", None)
    d["icon3d"]["key_light"] = "soft key"
    e1, _ = schema_errors(d)
    _, lw = lint(d)
    check("icon3d: свет в паспорте визуала — ошибка схемы; без series_passport — предупреждение линта",
          any("key_light" in e for e in e1) and any("series_passport" in w for w in lw), (e1[:2], lw))
    d = load_json(EXAMPLES / "dna-strict-saas.json")
    ms = d["illustration"].get("metaphors") or []
    check("пример strict-saas: места, формат, перекраска и метафоры иллюстраций — поля системы", ms and d["illustration"].get("places")
          and d["illustration"].get("recolor"), d["illustration"])
    d["illustration"]["metaphors"] = ms + [dict(ms[0], meaning="тот же id — другой смысл")] if ms else ms
    le, _ = lint(d)
    check("illustration: повтор id метафоры — ошибка линта", any("metaphors" in e for e in le), le)
    d["illustration"].pop("metaphors", None)
    _, lw = lint(d)
    check("illustration: пустые состояния без списка метафор — предупреждение линта", any("метафор" in w for w in lw), lw)
    d["video"] = {"tempo": "fast"}
    check("video.tempo: fast — проходит схему", not schema_errors(d)[0], schema_errors(d)[0][:2])
    # 4. LUT: нейтральный грейд — тождество; грейд паспорта — файл 33³
    ident = load_json(EXAMPLES / "dna-warm-consumer.json")
    ident["grade"].update({"wb_ab": [0.0, 0.0], "chroma": 1.0, "black": 0.0, "white": 1.0, "contrast": 0.0})
    rows = cube_numbers(write_lut(ident, tmp / "ident.cube", size=9))
    import numpy as np
    g = np.linspace(0, 1, 9)
    b_, gg, r_ = np.meshgrid(g, g, g, indexing="ij")
    lattice = np.stack([r_, gg, b_], -1).reshape(-1, 3)
    diff = float(np.abs(np.array(rows) - lattice).max()) if len(rows) == len(lattice) else None
    check("lut: нейтральный грейд → тождественный .cube", diff is not None and diff < 1e-3, f"max|Δ| = {diff}")
    rows = cube_numbers(write_lut(load_json(EXAMPLES / "dna-warm-consumer.json"), tmp / "warm.cube"))
    mid = rows[len(rows) // 2] if rows else None
    check("lut: паспорт warm-consumer → 33³ строк, средний серый теплеет (R > B)", len(rows) == 33 ** 3 and mid and mid[0] > mid[2], mid)
    # 5. from-tokens на мини-наборе DTCG (алиасы, oklch+hex, px)
    toks = {"primitive": {"color": {"neutral": {"200": {"$value": {"colorSpace": "oklch", "components": [0.929, 0.013, 255.5], "hex": "#e2e8f0"}},
                                                "400": {"$value": {"hex": "#90a1b9"}}, "500": {"$value": {"hex": "#62748e"}},
                                                "50": {"$value": {"hex": "#f8fafc"}}},
                                    "accent": {"600": {"$value": {"hex": "#155dfc"}}, "200": {"$value": {"hex": "#bedbff"}}}},
                          "font": {"family": {"sans": {"$value": ["Inter", "sans-serif"]}}}, "size": {"6": {"$value": {"value": 6, "unit": "px"}}}},
            "color": {"bg": {"canvas": {"$value": "{primitive.color.neutral.50}"}, "surface": {"$value": "#ffffff"}},
                      "text": {"primary": {"$value": "#0f172b"}}, "accent": {"solid": {"$value": "{primitive.color.accent.600}"}},
                      "border": {"subtle": {"$value": "{primitive.color.neutral.200}"}}},
            "radius": {"md": {"$value": "{primitive.size.6}"}}}
    dt_ = from_tokens(toks, "tokens-demo", ["строгий", "плотный", "технический"])
    e1, _ = schema_errors(dt_)
    le, lw = lint(dt_)
    k = dt_["derived_from_ui"]["knobs"]
    check("from-tokens: скелет проходит схему и линт", not e1 and not le, (e1 or le)[:3])
    check("from-tokens: алиасы разрешены (canvas #F8FAFC, акцент #155DFC, радиус 6)", dt_["palette"]["image_palette"][0]["hex"] == "#F8FAFC"
          and k["accent_hex"] == "#155DFC" and k["radius_px"] == 6, k)
    check("from-tokens: холодная slate-нейтраль → cool, b −0,004", k["neutral_temp"] == "cool" and dt_["palette"]["neutral_wb"]["target_b"] == -0.004, k)
    check("from-tokens: icon3d — материал и акцент, свет и камера — ссылкой на паспорт 3D-серии",
          dt_["icon3d"].get("series_passport") == SERIES_PASSPORT and "key_light" not in dt_["icon3d"], dt_["icon3d"])
    # 6. паспорт → спецификация ассета; компилятор промтов вставляет блок стиля дословно (нужен снимок каталога polza)
    wc = EXAMPLES / "dna-warm-consumer.json"
    spec = to_spec(load_json(wc), "photo", "IMG-HERO-PHOTO", "a weathered wooden park bench under a birch tree", "hero", None, True,
                   "exterior-park-autumn", wc, tmp / "spec.json")
    e1, eng = schema_errors(spec, SPEC_SCHEMA_PATH)
    check(f"to-spec: спецификация проходит asset-spec.schema.json ({eng})", not e1, e1[:3])
    check("to-spec: сумма долей палитры ≤ 1, ≤ 5 цветов", sum(p["share"] for p in spec["palette"]) <= 1.0 and len(spec["palette"]) <= 5,
          [p["share"] for p in spec["palette"]])
    s3 = to_spec(load_json(EXAMPLES / "dna-strict-saas.json"), "icon3d", "IMG-ICON3D", "a small parcel box", "section")
    check("to-spec icon3d: свет — схема паспорта 3D-серии, спецификация проходит схему",
          "fill and rim" in s3["light"]["source"] and not schema_errors(s3, SPEC_SCHEMA_PATH)[0], s3["light"])
    sp2 = to_spec(load_json(wc), "photo", "IMG-HERO-PHOTO", "a wooden park bench", "hero-visual", section="hero")
    check("to-spec: секция и слот — раздельные значения; без секции секцией служит слот",
          (sp2["role"]["section"], sp2["role"]["slot"]) == ("hero", "hero-visual") and spec["role"]["section"] == spec["role"]["slot"] == "hero",
          (sp2["role"], spec["role"]))
    se = to_spec(load_json(wc), "photo", "IMG-EDIT", "a wooden park bench under a birch tree", "hero-visual", section="hero",
                 out_path=tmp / "edit.spec.json", edit={"operation": "relight", "source": str(tmp / "shot0.png")})
    check("to-spec, профиль правки: edit с исходником от папки спецификации; без исключений и референсов паспорта, "
          "области объекта, ракурса и зоны текста; схема проходит",
          se.get("edit") == {"operation": "relight", "source": "shot0.png"} and "exclusions" not in se and "references" not in se
          and list(se["composition"]) == ["shot"] and se["text"] == {"mode": "none"} and se["series"]["avoid_average"] is False
          and not schema_errors(se, SPEC_SCHEMA_PATH)[0], (se.get("edit"), se["composition"], schema_errors(se, SPEC_SCHEMA_PATH)[0][:2]))
    se = to_spec(load_json(wc), "photo", "IMG-EDIT", "a wooden park bench", "hero-visual", ref_class="exterior-park-autumn", dna_path=wc,
                 out_path=tmp / "edit.spec.json", edit={"operation": "restyle", "source": str(tmp / "shot0.png")})
    check("to-spec, профиль правки с --ref-class: референсы названного класса идут", len(se.get("references") or []) >= 1, se.get("references"))
    check("to-spec без профиля правки: исключения и композиция паспорта — в спецификации",
          spec.get("exclusions") and {"subject_region", "text_zone"} <= set(spec["composition"]) and "edit" not in spec, spec["composition"])
    d = load_json(wc)
    d["composition"].update({"text_zone_default": {"side": "center", "share": 0.4}, "subject_region": "bottom"})
    e1, _ = schema_errors(d)
    e2, _ = schema_errors(d, force_builtin=True)
    sc = to_spec(d, "photo", "IMG-HERO-PHOTO", "a wooden park bench", "hero")
    check("зона текста по центру: паспорт проходит схему, в спецификации — центральная полоса шириной share",
          not e1 and not e2 and sc["composition"]["text_zone"]["side"] == "center" and sc["composition"]["text_zone"]["rect"] == [0.3, 0, 0.7, 1]
          and not schema_errors(sc, SPEC_SCHEMA_PATH)[0], (e1 or e2, sc["composition"].get("text_zone")))
    d["composition"]["subject_region"] = "center"
    le, lw = lint(d)
    check("зона текста и объект оба в центре — предупреждение линта, не ошибка", any("в центре кадра" in w for w in lw) and not le, (le, lw))
    d = load_json(wc)
    d["lifecycle"] = {"version": "1.1", "history": [
        {"version": "1.0", "date": "2030-01-15", "by": "владелец продукта", "change": "первая утверждённая версия"},
        {"version": "1.1", "date": "2030-02-01", "by": "владелец продукта", "change": "post.scrim.max_alpha: 0,55 → 0,6"}]}
    e1, _ = schema_errors(d)
    e2, _ = schema_errors(d, force_builtin=True)
    check("версия паспорта и история подтверждений (lifecycle) — необязательные поля, схема проходит", not e1 and not e2, (e1 or e2)[:2])
    d["lifecycle"]["history"][1].pop("by")
    e1, _ = schema_errors(d)
    e2, _ = schema_errors(d, force_builtin=True)
    check("история подтверждений: запись без «кто» — ошибка схемы у обоих валидаторов", any("by" in e for e in e1) and any("by" in e for e in e2),
          (e1[:2], e2[:2]))
    # 7. скрим: числа прозрачности из текстов арт-дирекции против post.scrim.max_alpha паспорта
    ad = {"visual_language": {"composition": [
        "скрим под заголовком — не слабее 0,7 тёмного слоя; контраст строк ≥ 4,5:1",
        "подпись карточки лежит на скриме 30 % высоты карточки", "скрим у меню вместо вуали 25 % на всё фото"]}}
    d = load_json(wc)
    d["post"]["scrim"]["max_alpha"] = 0.55
    w = scrim_check(d, ad)
    check("скрим: арт-дирекция 0,7 против 0,55 паспорта — одно предупреждение; число размера и число вуали не берутся",
          len(w) == 1 and "0.7" in w[0] and "0.55" in w[0] and "visual_language.composition[0]" in w[0], w)
    d["post"]["scrim"]["max_alpha"] = 0.7
    check("скрим: значения равны — чисто", not scrim_check(d, ad), scrim_check(d, ad))
    rng = {"notes": "скрим — градиент от 0,3 до 0,7 под колонкой текста"}
    check("скрим: диапазон с числом паспорта — чисто; диапазон без него — одно предупреждение на фразу",
          not scrim_check(d, rng) and len(scrim_check(dict(d, post={"scrim": {"max_alpha": 0.5}}), rng)) == 1, scrim_check(d, rng))
    d["post"].pop("scrim")
    check("скрим: в паспорте значения нет, арт-дирекция его называет — предупреждение", len(scrim_check(d, ad)) == 1, scrim_check(d, ad))
    d = load_json(wc)
    d["references"] = []
    dump_json(d, tmp / "dna-scrim.json")
    dump_json(ad, tmp / "art-direction.json")
    venv = Path(kbpaths.python())
    py = str(venv) if venv.exists() else sys.executable
    me = str(Path(__file__).resolve())
    r = subprocess.run([py, me, "validate", str(tmp / "dna-scrim.json"), "--art-direction", str(tmp / "art-direction.json")],
                       capture_output=True, text=True, timeout=120)
    check("validate --art-direction: расхождение скрима — предупреждение в lint_warnings, код 0",
          r.returncode == 0 and "скрим: арт-дирекция" in r.stdout, (r.returncode, (r.stderr or r.stdout)[-300:]))
    r = subprocess.run([py, me, "validate", str(tmp / "dna-scrim.json"), "--art-direction", str(tmp / "none.json")],
                       capture_output=True, text=True, timeout=120)
    check("validate --art-direction: файл не читается — строка в stderr и код 2", r.returncode == 2 and "арт-дирекция не читается" in r.stderr,
          (r.returncode, r.stderr[-200:]))
    r = subprocess.run([py, me, "to-spec", str(wc), "--kind", "photo", "--task", "IMG-EDIT", "--subject", "a wooden park bench",
                        "--edit", str(tmp / "shot0.png")], capture_output=True, text=True, timeout=120)
    check("to-spec --edit без --operation — код 2", r.returncode == 2 and "--operation" in r.stderr, (r.returncode, r.stderr[-200:]))
    dump_json(spec, tmp / "spec.json")
    r = subprocess.run([py, str(TOOLS / "prompt_compile.py"), "compile", str(tmp / "spec.json"), "--model", "openai/gpt-image-2.5-sunburst"],
                       capture_output=True, text=True, timeout=120)
    block = load_json(wc)["style_blocks"]["photo"]
    if "нет снимков" in (r.stdout + r.stderr):
        check("prompt_compile: нет снимка каталога polza (install.sh --catalogs) — пропуск", True)
    else:
        check("prompt_compile: блок стиля паспорта дословно в промте GPT Image 2.5", r.returncode == 0 and block in r.stdout,
              (r.stderr or r.stdout)[-300:] if r.returncode else "")
    for s_ in res:
        print(f"{s_[0]}  {s_[1]}" + (f"  → {s_[2]}" if s_[0] == "FAIL" else ""))
    print(f"итого: {len(res) - len(fails)}/{len(res)} PASS")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("grid"); s.add_argument("images", nargs="+"); s.add_argument("--out", required=True)
    s.add_argument("--cell", type=int, default=640); s.add_argument("--cols", type=int, default=3); s.set_defaults(f=cmd_grid)
    s = sub.add_parser("build", help="пакет для сессии Opus (агент design-judge): сетка → JSON-бриф паспорта")
    s.add_argument("grid"); s.add_argument("--out", help="папка пакетов (по умолчанию $DDD_HOME/out/ai-media/dna)")
    s.add_argument("--name", help="имя пакета (по умолчанию — хэш сетки)")
    s.add_argument("--runs", type=int, default=2, help="прогонов — отдельных сессий (сверка — compare)")
    s.add_argument("--force", action="store_true", help="пересобрать пакет, в котором уже есть ответы"); s.set_defaults(f=cmd_build)
    s = sub.add_parser("parse", help="ответы пакета или файл ответа → черновик паспорта")
    s.add_argument("response", help="папка пакета build или файл ответа"); s.add_argument("--out", required=True)
    s.add_argument("--grid", help="сетка для сверки палитры (по умолчанию — из ключа пакета)")
    s.add_argument("--id"); s.add_argument("--brand")
    s.add_argument("--art-direction", help="путь к art-direction.json, из которого выведен паспорт (происхождение)")
    s.set_defaults(f=cmd_parse)
    s = sub.add_parser("validate"); s.add_argument("files", nargs="+"); s.add_argument("--builtin", action="store_true")
    s.add_argument("--art-direction", help="art-direction.json: сверить скрим арт-дирекции с post.scrim паспорта (предупреждение)")
    s.set_defaults(f=cmd_validate)
    s = sub.add_parser("compare"); s.add_argument("a"); s.add_argument("b"); s.set_defaults(f=cmd_compare)
    s = sub.add_parser("lut"); s.add_argument("dna"); s.add_argument("--out", required=True); s.add_argument("--size", type=int, default=33)
    s.set_defaults(f=cmd_lut)
    s = sub.add_parser("from-tokens"); s.add_argument("tokens"); s.add_argument("--out", required=True); s.add_argument("--id", default="from-tokens")
    s.add_argument("--adjectives"); s.set_defaults(f=cmd_from_tokens)
    s = sub.add_parser("to-spec"); s.add_argument("dna"); s.add_argument("--kind", required=True, choices=["photo", "illustration", "icon3d"])
    s.add_argument("--task", required=True); s.add_argument("--subject", required=True)
    s.add_argument("--slot", default="hero", help="id строки плана ассетов (role.slot)")
    s.add_argument("--section", help="id секции плана страницы (role.section); без ключа — значение --slot")
    s.add_argument("--ratio"); s.add_argument("--shot"); s.add_argument("--no-text-zone", action="store_true"); s.add_argument("--ref-class")
    s.add_argument("--edit", metavar="SOURCE", help="профиль правки: файл настоящего кадра — без исключений паспорта и "
                                                    "композиции генерации с нуля; нужен --operation")
    s.add_argument("--operation", choices=edit_operations(), help="операция правки (edit.operation) для --edit")
    s.add_argument("--out"); s.set_defaults(f=cmd_to_spec)
    s = sub.add_parser("selftest"); s.set_defaults(f=lambda a: sys.exit(selftest()))
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
