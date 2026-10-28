#!/usr/bin/env python3
"""asset_audit.py — автоматическая приёмка ИИ-ассетов сайта и пакет судьи по рубрике.

Объединяет проверки соседних утилит вызовом и импортом, не переписывая их: image_metrics.py (цвет, «HDR»),
composition_metrics.py («средний вид»), text_zone.py (зона текста, скрим, WCAG F83), series_metrics.py и split_grid.py
(серия), stand_run.py (сверка строк, Уилсон), edit_check.py и alpha_check.py (правка, альфа), tile_check.py (текстура),
video_loop_check.py (петли), check_icons.py (иконки), mp_client.py (сведения SVG), vlm_to_dna.py (паспорт визуала:
палитра, приёмка, запреты), паспорта генераций polza.py и mp_client.py, провенанс (provenance_check.py, exiftool,
c2patool), OCR кириллицы (RapidOCR + PP-OCRv5 eslav). Пороги — kb/ai-media/11-evaluation-qa/thresholds.yaml (у каждого —
источник). Вход — файл, список или папка с паспортами. Выход — JSON-вердикт с кодами дефектов (asset-audit/1),
Markdown-сводка и контактный лист для человека. Нет пакета, модели или программы окружения — проверка не запускается: в
`errors` ассета и в строках «Окружение» сводки — одна строка с командой установки (`scripts/install.sh --groups ocr
--models`, `--groups svg`, `--bin`, `--ffmpeg`).

Режимы (--mode; auto — по паспорту, коду задачи, альфе и расширению):
  image       фото, иллюстрация, фон, 3D-объект: размеры, цвет-слоп, композиция, зона текста, палитра, текст (OCR: число
              вхождений строки — «строка{×N}», расхождение в мелких буквах — предупреждение), провенанс; с --master —
              сжатие к мастеру без усечения глубины (AVIF → PNG 16 бит) и резкость источника отдельной метрикой
  cutout      вырез/нативная альфа: альфа есть и настоящая, ореол, поле, полупрозрачность, эталон (--ref-alpha)
  edit        правка на месте (--orig [--mask] [--protect]) или аутпейнт (другая пропорция) — edit_check.py; без маски —
              маска из разницы (ΔE00 > 5 после подгонки цвета + морфология) и композит с растушёвкой
  series      папка или список кадров: оттенок, ΔE палитр, светлота, pHash-дубли (+ --ref, --grid RxC)
  texture     бесшовность (tile_check)
  video-loop  шов по файлу как есть (порог — по стадии: мезонин и выход модели или файл после кодирования), живость
              (+ --control), склейки и монтаж (--montage), угасание (--fade-event — объявленное затемнение), повторы
              кадров, вспышки WCAG 2.3.1, пинг-понг, камера, звук, мерцание яркости, синемаграф (--mask → drift)
  video-once  разовый ролик (вступление): без шва, угасания, длины петли и «ползущей камеры»; склейки, повторы кадров,
              вспышки, звук и вес — как у петли
  video-alpha хромакей-исходник (chroma) или файл с альфой (pix_fmt)
  svg-icon    линейная иконка (check_icons, пороги Lucide; эталон шапки и штрих — --icon-stroke, --icon-viewbox или
              --conventions SYSTEM.yaml; шапка не по эталону — брак только у набора Lucide, у другого набора —
              предупреждение: --icon-set) или цветной SVG (фон, корень, <image>, <text>, подпись Recraft)
  og          OG-картинка 1200×630: размер, вес, текст (OCR), поля, + всё из image

Команды:
  audit PATH… [--mode M] [--out DIR] [--dna DNA.json] [--spec SPEC.json] [--expect "строка"]… [--orig O] [--mask M]
        [--control C] [--ref-alpha GT] [--text-zone x0,y0,x1,y1] [--slot hero|section|product|icon|og] [--stage web]
        [--plan PLAN.yaml --slot ID [--variant V]] [--montage] [--fade-event] [--css-width W]
        [--mobile] [--icon-set НАБОР] [--icon-stroke ШТРИХ] [--icon-viewbox VIEWBOX] [--conventions SYSTEM.yaml] [--strict]
  ocr IMG… [--lang ru|en] [--expect …]      OCR под блокировкой heavy + сверка со строками
  thresholds [--check]                       пороги с источниками; --check — у каждого есть source
  judge-jobs (--items F | --from-stand-page DIR | --calibration [--pairs ID,…]) [--rubric R] [--mode M] [--runs 3]
             [--same-encoding] [--out DIR] [--name N]
                                             пакет заданий судьи для отдельных сессий Opus (агент design-judge): кадры
                                             вслепую, вопросы рубрики, формат ответа по judge-response.schema.json; оба
                                             порядка пары и повторы — отдельные задания; ключ слепоты — рядом, вне пакета
  judge-parse PACKAGE [--key K] [--answers DIR] [--out F]
                                             ответы сессий → строки ответов и сводка: пара — оба порядка и большинство
                                             прогонов, находка — не меньше чем в двух прогонах (kb/common/judge.md §5)
  agree --answers ROWS.jsonl [--votes V.json…] [--key PAGE.key.json] [--labels L.jsonl]
                                             согласие судьи с человеком: Уилсон, F1, повторы, позиция A, «не уверен»,
                                             сессии подряд → уровень доверия (пороги — группа judge thresholds.yaml)
  calibrate --audit A.json --labels L.jsonl --metric PATH   порог метрики по меткам человека (Юден, AUC)
  selftest                                   офлайн-проверки на синтетике (tests/test_asset_audit.py без OCR)
Моделей утилита не вызывает: оценку делает сессия Opus по пакету, код готовит пакет и разбирает ответы.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

VERSION = "0.2"
SCHEMA = "asset-audit/1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))  # scripts/lib: kbpaths
import kbpaths  # noqa: E402
ROOT = kbpaths.kb("ai-media")
TOOLS = kbpaths.scripts("ai-media")
THRESHOLDS = ROOT / "11-evaluation-qa" / "thresholds.yaml"
RUBRICS = ROOT / "11-evaluation-qa" / "rubrics"
OCR_MODELS = kbpaths.models("ocr")
LUCIDE_REF = kbpaths.data("ai-media", "lucide-ref")
ICON_SET = "lucide"             # набор иконок по умолчанию (--icon-set; у продукта — conventions.icons.set карты решений)
INSTALL = "scripts/install.sh"  # установка окружения скилла (путь от корня скилла)
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".bmp", ".tif", ".tiff")
VID_EXT = (".mp4", ".webm", ".mov", ".m4v", ".mkv")
SVG_EXT = (".svg",)

sys.path.insert(0, str(TOOLS))

# ================================================================ общие помощники


def _load(name: str, path: Path):
    """Импорт модуля по пути (утилиты-соседи из scripts/ai-media импортируются без побочных эффектов)."""
    key = f"_aa_{name}"
    if key in sys.modules:
        return sys.modules[key]
    for extra in (str(path.parent),):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    spec = importlib.util.spec_from_file_location(key, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def mod(name: str):
    """Модули соседей: импорт по требованию (numpy/scipy нужны только им)."""
    paths = {"edit_check": TOOLS / "edit_check.py", "alpha_check": TOOLS / "alpha_check.py",
             "tile_check": TOOLS / "tile_check.py", "video_loop_check": TOOLS / "video_loop_check.py",
             "stand_run": TOOLS / "stand_run.py", "vlm_to_dna": TOOLS / "vlm_to_dna.py", "mp_client": TOOLS / "mp_client.py",
             "image_metrics": TOOLS / "image_metrics.py",
             "composition_metrics": TOOLS / "composition_metrics.py", "text_zone": TOOLS / "text_zone.py",
             "series_metrics": TOOLS / "series_metrics.py", "split_grid": TOOLS / "split_grid.py"}
    return _load(name, paths[name])


def rel(p) -> str:
    p = Path(p)
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def jdump(o, indent=1) -> str:
    return json.dumps(o, ensure_ascii=False, indent=indent, default=_json_default)


def _json_default(o):
    try:
        import numpy as np
        if isinstance(o, np.generic):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
    except ImportError:
        pass
    if isinstance(o, Path):
        return str(o)
    return str(o)


def rnd(x, k=4):
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return x
    return round(v, k) if math.isfinite(v) else None


def free_gb() -> float | None:
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 1024 / 1024
    except OSError:
        return None
    return None


def env_hint(what: str, flags: str) -> str:
    """Одна строка о недостающем окружении: чего нет и какой командой поставить (вместо трассировки)."""
    return f"{what} — поставьте `{INSTALL} {flags}`"


def last_line(text: str, n: int = 300) -> str:
    """Последняя непустая строка вывода (у трассировки — строка исключения)."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return (lines[-1] if lines else "")[:n]


def run_locked(cmd: list[str], lock: str = "heavy", wait: int = 1800, **kw) -> subprocess.CompletedProcess:
    """Команда под замком `$DDD_HOME/locks/ai-media/<lock>.lock` (heavy — модели, browser — Chromium, blender — Blender).

    Замок берёт `kbpaths.lock`: он реентерабелен по дереву процессов — замок, который уже держит этот процесс или его
    предок (переменная DDD_LOCKS_HELD), повторно не берётся и не ждёт, а дочерняя команда наследует переменную. Замок
    занят дольше wait секунд — TimeoutError.
    """
    with kbpaths.lock(lock, "ai-media", timeout=wait):
        return subprocess.run(cmd, **kw)


# ================================================================ пороги


_TH_CACHE: dict = {}


def load_thresholds(path: Path | None = None) -> dict:
    """Пороги из YAML; у каждого узла {value, source, …}. Возвращает dict и плоский индекс 'a.b.c' → value."""
    p = Path(path or THRESHOLDS)
    if str(p) in _TH_CACHE:
        return _TH_CACHE[str(p)]
    import yaml
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    flat: dict = {}

    def walk(node, prefix):
        if isinstance(node, dict) and "value" in node and ("source" in node or "sources" in node):
            flat[prefix] = node["value"]
            return
        if isinstance(node, dict):
            for k, v in node.items():
                if k.startswith("_"):
                    continue
                walk(v, f"{prefix}.{k}" if prefix else k)
    walk(doc.get("thresholds", {}), "")
    doc["_flat"] = flat
    doc["_path"] = rel(p)
    doc["_sha"] = sha256_file(p)[:12] if p.exists() else None
    _TH_CACHE[str(p)] = doc
    return doc


class Th:
    """Доступ к порогам: th('image.colorfulness_max') → значение; переопределения из паспорта визуала (--dna)."""

    def __init__(self, doc: dict, overrides: dict | None = None):
        self.doc = doc
        self.flat = dict(doc.get("_flat", {}))
        self.over = overrides or {}

    def __call__(self, key: str, default=None):
        if key in self.over:
            return self.over[key]
        return self.flat.get(key, default)

    def src(self, key: str) -> str | None:
        node = self.doc.get("thresholds", {})
        for part in key.split("."):
            if not isinstance(node, dict):
                return None
            node = node.get(part)
        if isinstance(node, dict):
            s = node.get("source") or node.get("sources")
            if key in self.over:
                return f"паспорт визуала (переопределено); база: {s}"
            return s if isinstance(s, str) else "; ".join(s) if isinstance(s, list) else None
        return None


# ================================================================ дефекты и вердикт


class Report:
    """Отчёт по одному ассету: checks (числа), defects (коды), human (что смотреть человеку)."""

    LEVELS = {"info": 0, "warn": 1, "needs_human": 2, "fail": 3}

    def __init__(self, path: Path, mode: str, th: Th):
        self.path = Path(path)
        self.mode = mode
        self.th = th
        self.checks: dict = {}
        self.defects: list[dict] = []
        self.human: list[dict] = []
        self.errors: list[str] = []
        self.env: set[str] = set()      # чего нет в окружении: одна строка с командой установки на недостающее
        self.meta: dict = {}
        self.markers: set[str] = set()

    def defect(self, code: str, level: str, msg: str, metric: str | None = None, value=None, th_key: str | None = None,
               threshold=None, marker: str | None = None, evidence=None):
        d = {"code": code, "level": level, "msg": msg}
        if metric:
            d["metric"] = metric
        if value is not None:
            d["value"] = rnd(value) if isinstance(value, (int, float)) else value
        if th_key:
            d["threshold_key"] = th_key
            d["threshold"] = threshold if threshold is not None else self.th(th_key)
            s = self.th.src(th_key)
            if s:
                d["source"] = s
        elif threshold is not None:
            d["threshold"] = threshold
        if marker:
            d["marker"] = marker
            if level in ("warn", "fail", "needs_human"):
                self.markers.add(marker)
        if evidence is not None:
            d["evidence"] = evidence
        self.defects.append(d)
        return d

    def ask_human(self, item: str, why: str, codes: list[str] | None = None):
        self.human.append({"item": item, "why": why, **({"codes": codes} if codes else {})})

    def no_env(self, hint: str, check: str | None = None):
        """Нет окружения: hint — одна строка «чего нет — поставьте `scripts/install.sh …`». С именем проверки строка идёт и в
        errors: проверка не запущена, вердикт — не ниже needs_human; без имени — только в env (сведения неполны)."""
        self.env.add(hint)
        if check:
            self.errors.append(f"{check} не запущен: {hint}")

    def verdict(self) -> str:
        lv = max([self.LEVELS[d["level"]] for d in self.defects] + [0])
        if self.errors and lv < 2:
            lv = 2
        return {0: "pass", 1: "warn", 2: "needs_human", 3: "fail"}[lv]

    def to_dict(self) -> dict:
        v = self.verdict()
        return {"schema": SCHEMA, "tool": f"asset_audit.py {VERSION}", "checked_at": now_iso(), "file": rel(self.path),
                "mode": self.mode, **self.meta, "verdict": v,
                "summary": {k: sum(1 for d in self.defects if d["level"] == k) for k in ("fail", "needs_human", "warn", "info")},
                "markers": sorted(self.markers), "defects": self.defects, "human": self.human, "checks": self.checks,
                "errors": self.errors, **({"env": sorted(self.env)} if self.env else {}),
                "thresholds": {"file": self.th.doc.get("_path"), "sha": self.th.doc.get("_sha")}}


# ================================================================ OCR (RapidOCR + PP-OCRv5, Python окружения скилла)

OCR_SETS = {
    # det — детектор строк, rec — распознаватель; модели: $DDD_HOME/models/ocr (sha256 — thresholds.yaml → ocr_models);
    # «@» — модель из колеса rapidocr 3.9.2. Кириллица — только eslav/cyrillic PP-OCRv5 (у PP-OCRv6 её нет).
    # опыт OCR на 714 синтетических баннерах: ru = det PP-OCRv6 small + rec eslav — меньше всего ложного брака (3/72 чистых).
    "ru": ("@PP-OCRv6_det_small.onnx", "eslav_PP-OCRv5_rec_mobile.onnx"),
    "ru-v5det": ("ch_PP-OCRv5_det_mobile.onnx", "eslav_PP-OCRv5_rec_mobile.onnx"),
    "ru-cyrillic": ("@PP-OCRv6_det_small.onnx", "cyrillic_PP-OCRv5_rec_mobile.onnx"),
    "en": ("@PP-OCRv6_det_small.onnx", "en_PP-OCRv5_rec_mobile.onnx"),
    "multi-v6": ("@PP-OCRv6_det_small.onnx", "@PP-OCRv6_rec_small.onnx"),
}
OCR_SNIFF_REC = "en_PP-OCRv5_rec_mobile.onnx"   # второй распознаватель по тем же рамкам строк — «латинский нюх»
OCR_DET_LIMIT = (1600, "max")
OCR_INSTALL = "--groups ocr --models"


def _ocr_model_path(name: str) -> str:
    if name.startswith("@"):      # модель из колеса rapidocr
        import rapidocr
        return str(Path(rapidocr.__file__).parent / "models" / name[1:])
    return str(OCR_MODELS / name)


def ocr_missing(lang: str = "ru") -> str | None:
    """Модели набора lang, которых нет в $DDD_HOME/models/ocr, — строка с командой установки, иначе None. Модели из колеса
    rapidocr («@») проверяет обработчик: они приходят с пакетом."""
    det, rec = OCR_SETS[lang]
    names = [det, rec] + ([OCR_SNIFF_REC] if lang.startswith("ru") else [])
    miss = [n for n in dict.fromkeys(names) if not n.startswith("@") and not (OCR_MODELS / n).is_file()]
    return env_hint(f"нет моделей OCR ({', '.join(miss)})", OCR_INSTALL) if miss else None


def ocr_lines(boxes, txts, scores, y_overlap=0.5):
    """Слова/фрагменты RapidOCR → строки в порядке чтения: группировка по перекрытию по вертикали, внутри — по x."""
    items = []
    for b, t, s in zip(boxes, txts, scores):
        xs, ys = [p[0] for p in b], [p[1] for p in b]
        items.append({"text": t, "score": round(float(s), 4), "x0": min(xs), "x1": max(xs), "y0": min(ys), "y1": max(ys),
                      "h": max(ys) - min(ys)})
    items.sort(key=lambda it: (it["y0"] + it["y1"]) / 2)
    lines: list[list[dict]] = []
    for it in items:
        placed = False
        for ln in lines:
            ly0, ly1 = min(x["y0"] for x in ln), max(x["y1"] for x in ln)
            ov = min(ly1, it["y1"]) - max(ly0, it["y0"])
            if ov >= y_overlap * min(it["h"], ly1 - ly0):
                ln.append(it)
                placed = True
                break
        if not placed:
            lines.append([it])
    out = []
    for ln in lines:
        ln.sort(key=lambda x: x["x0"])
        out.append({"text": " ".join(x["text"] for x in ln), "score_min": min(x["score"] for x in ln),
                    "score_mean": round(sum(x["score"] for x in ln) / len(ln), 4),
                    "h_px": round(sorted(x["h"] for x in ln)[len(ln) // 2], 1),
                    "box": [round(min(x["x0"] for x in ln)), round(min(x["y0"] for x in ln)),
                            round(max(x["x1"] for x in ln)), round(max(x["y1"] for x in ln))],
                    "words": [{"text": x["text"], "score": x["score"], "box": [round(x["x0"]), round(x["y0"]),
                                                                              round(x["x1"]), round(x["y1"])]} for x in ln]})
    out.sort(key=lambda L: (L["box"][1], L["box"][0]))
    return out


def _load_rgb_pil(p):
    from PIL import Image
    im = Image.open(p)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (128, 128, 128, 255))   # прозрачное — на средне-сером: виден и светлый, и тёмный текст
        bg.alpha_composite(im)
        im = bg
    return im.convert("RGB")


def ocr_worker(paths: list[str], lang: str = "ru", text_score: float = 0.3, relines: bool = True,
               det_limit: tuple = OCR_DET_LIMIT, sniff: bool = True) -> list[dict]:
    """Выполняется в Python окружения скилла (rapidocr 3.9.2 + onnxruntime). Возвращает на каждую картинку строки, слова,
    время. relines: слова одной строки склеиваются по рамке и строка распознаётся заново целиком (детектор PP-OCRv5 режет
    строку на перекрывающиеся слова, и буква на стыке читается дважды — «Весенняяр распродажа»)."""
    import time
    from rapidocr import RapidOCR
    det, rec = OCR_SETS[lang]
    eng = RapidOCR(params={"Global.log_level": "error", "Global.use_cls": False, "Global.text_score": text_score,
                           "Det.model_path": _ocr_model_path(det), "Rec.model_path": _ocr_model_path(rec),
                           "Det.limit_side_len": int(det_limit[0]), "Det.limit_type": str(det_limit[1]),
                           "EngineConfig.onnxruntime.intra_op_num_threads": 4})
    sn = None
    if sniff and lang.startswith("ru"):
        # опыт OCR на 714 синтетических баннерах: русская модель «исправляет» латиницу в кириллицу (DОСТАВКА → ДОСТАВКА: 5 из 5); английская по той же
        # рамке читает «D» (5 из 5, ложных 1 из 144) — сверка в text_verdict (класс latin_suspect)
        sn = RapidOCR(params={"Global.log_level": "error", "Global.use_cls": False, "Global.text_score": 0.0,
                              "Det.model_path": _ocr_model_path(det), "Rec.model_path": _ocr_model_path(OCR_SNIFF_REC),
                              "EngineConfig.onnxruntime.intra_op_num_threads": 4})
    res = []
    for p in paths:
        t0 = time.time()
        try:
            img = _load_rgb_pil(p)
            r = eng(img, use_det=True, use_cls=False, use_rec=True)   # параметры RapidOCR «залипают» между вызовами
            boxes = [] if r.boxes is None else [[[float(x), float(y)] for x, y in b] for b in r.boxes]
            txts = list(r.txts or [])
            scores = list(r.scores or [])
            lines = ocr_lines(boxes, txts, scores)
            W, H = img.size
            for L in lines:
                L["text_words"] = L["text"]
                x0, y0, x1, y1 = L["box"]
                pad = max(2, int(0.25 * (y1 - y0)))
                crop = img.crop((max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)))
                if relines and len(L["words"]) >= 2:
                    rr = eng(crop, use_det=False, use_cls=False, use_rec=True)
                    if rr.txts:
                        t, sc = str(rr.txts[0]), float(rr.scores[0])
                        L["text_line"], L["score_line"] = t, round(sc, 4)
                        if sc >= L["score_min"] - 0.05:
                            L["text"] = t
                if sn is not None:
                    rs = sn(crop, use_det=False, use_cls=False, use_rec=True)
                    L["text_en"] = str(rs.txts[0]) if rs.txts else ""
            res.append({"file": str(p), "lang": lang, "det": det, "rec": rec, "relines": relines, "sniff": sn is not None,
                        "det_limit": list(det_limit),
                        "size": list(img.size),
                        "lines": lines, "elapsed_s": round(time.time() - t0, 3)})
        except Exception as e:  # noqa: BLE001
            res.append({"file": str(p), "lang": lang, "error": f"{type(e).__name__}: {e}"[:300]})
    return res


def run_ocr(paths: list, lang: str = "ru", text_score: float = 0.3, timeout: int = 900) -> list[dict]:
    """OCR отдельным процессом Python окружения скилла под heavy.lock (одна загрузка моделей на пачку картинок)."""
    miss = ocr_missing(lang)
    if miss:   # до запуска: нет моделей — одна строка с командой установки, обработчик не стартует
        return [{"file": str(p), "error": miss, "env": True} for p in paths]
    fg = free_gb()
    if fg is not None and fg < 1.0:
        return [{"file": str(p), "error": f"мало памяти ({fg:.1f} ГБ available) — OCR не запущен"} for p in paths]
    cmd = ([kbpaths.python(), str(Path(__file__).resolve()), "_ocr-worker", "--lang", lang, "--text-score", str(text_score)]
           + [str(Path(p).resolve()) for p in paths])
    try:
        r = run_locked(cmd, "heavy", capture_output=True, text=True, timeout=timeout)
    except TimeoutError as e:
        return [{"file": str(p), "error": f"OCR не запущен: {e}"} for p in paths]
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return [{"file": str(p), "error": f"OCR упал: {last_line(r.stderr or r.stdout) or f'код {r.returncode}'}"} for p in paths]


# ================================================================ сверка текста (кириллица): классы ошибок, GNED

LAT = re.compile(r"[A-Za-z]")
CYR = re.compile(r"[А-Яа-яЁё]")
HOMO_LAT = set("ABEKMHOPCTXYaeopcxy")                      # латинские двойники кириллических букв
DIGIT_PAIRS = {("о", "0"), ("о", "o"), ("з", "3"), ("б", "6"), ("ч", "4"), ("в", "8"), ("l", "1"), ("i", "1"), ("s", "5")}
SIMILAR_CYR = {frozenset(p) for p in (("и", "й"), ("ш", "щ"), ("б", "в"), ("п", "н"), ("ц", "щ"), ("ь", "ъ"), ("е", "ё"),
                                        ("ы", "ь"), ("л", "п"), ("к", "н"), ("г", "т"), ("з", "э"))}


def norm_text(s: str, homoglyphs: bool = True, all_homoglyphs: bool = False) -> str:
    """Нормализация как stand_run.norm_line: NFC, тире и кавычки, пробелы; латинские двойники в русских словах → кириллица.
    all_homoglyphs — двойники → кириллица и в словах без кириллицы (однобуквенное «K» вместо «к»): только если в ожидаемой
    строке нет латиницы («Щедрые подарки K Новому году» — ложный брак без этого правила)."""
    sr = mod("stand_run")
    s = sr.norm_line(s, homoglyphs)
    if homoglyphs and all_homoglyphs:
        s = s.translate(sr.HOMO_TO_CYR)
    return s


def lev(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def fit_align(a: str, t: str):
    """Нечёткий поиск строки a внутри транскрипта t (начало и конец в t бесплатны). Возвращает (дистанция, j0, j1, ops),
    ops — ('eq'|'sub'|'del'|'ins', символ a, символ t, позиция в a)."""
    n, m = len(a), len(t)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = i
    for i in range(1, n + 1):
        ai = a[i - 1]
        Di, Dp = D[i], D[i - 1]
        for j in range(1, m + 1):
            Di[j] = min(Dp[j] + 1, Di[j - 1] + 1, Dp[j - 1] + (ai != t[j - 1]))
    j1 = min(range(m + 1), key=lambda j: (D[n][j], -j)) if m else 0
    dist = D[n][j1]
    ops, i, j = [], n, j1
    while i > 0:
        if j > 0 and D[i][j] == D[i - 1][j - 1] + (a[i - 1] != t[j - 1]):
            ops.append(("eq" if a[i - 1] == t[j - 1] else "sub", a[i - 1], t[j - 1], i - 1))
            i, j = i - 1, j - 1
        elif D[i][j] == D[i - 1][j] + 1:
            ops.append(("del", a[i - 1], "", i - 1))
            i -= 1
        elif j > 0 and D[i][j] == D[i][j - 1] + 1:
            ops.append(("ins", "", t[j - 1], i))
            j -= 1
        else:          # j == 0 — остаток a не найден
            ops.append(("del", a[i - 1], "", i - 1))
            i -= 1
    ops.reverse()
    return dist, j, j1, ops


def classify_ops(ops: list, exp: str) -> list[dict]:
    """Операции выравнивания → классы ошибок кириллицы (C1, W6, E): пропуск, удвоение, латинский недвойник, ё → е,
    похожая буква, цифра вместо буквы, регистр, пробел/пунктуация, прочая замена или вставка."""
    out = []
    for k, (op, ca, ct, pos) in enumerate(ops):
        if op == "eq":
            continue
        if op == "del":
            if ca == " ":
                cls = "spacing"
            elif not ca.isalnum():
                cls = "punct"
            else:
                cls = "omission"
        elif op == "ins":
            prev_t = next((o[2] for o in reversed(ops[:k]) if o[0] in ("eq", "sub", "ins") and o[2]), "")
            next_t = next((o[2] for o in ops[k + 1:] if o[0] in ("eq", "sub", "ins") and o[2]), "")
            if ct == " ":
                cls = "spacing"
            elif not ct.isalnum():
                cls = "punct"
            elif ct.lower() in (prev_t.lower(), next_t.lower()):
                cls = "doubling"
            else:
                cls = "insertion"
        else:  # sub
            la, lt = ca.lower(), ct.lower()
            if la == "ё" and lt == "е":
                cls = "yo_lost"
            elif la == lt:
                cls = "case"
            elif (la, lt) in DIGIT_PAIRS or (lt, la) in DIGIT_PAIRS or (ca.isalpha() and ct.isdigit()) or (ca.isdigit() and ct.isalpha()):
                cls = "digit_confusion"
            elif CYR.match(ca) and LAT.match(ct) and ct not in HOMO_LAT:
                cls = "latin_substitute"
            elif frozenset((la, lt)) in SIMILAR_CYR:
                cls = "similar_cyr"
            elif not ca.isalnum() or not ct.isalnum():
                cls = "punct"
            else:
                cls = "substitution"
        out.append({"class": cls, "op": op, "expected": ca, "got": ct, "pos": pos,
                    "context": exp[max(0, pos - 6):pos + 7]})
    return out


FAIL_CLASSES = {"omission", "doubling", "insertion", "substitution", "latin_substitute", "similar_cyr", "digit_confusion"}
# Классы, которые OCR ловит почти без ложных тревог (опыт OCR на 714 синтетических баннерах): при уверенном OCR и строке ≥ min_line_h — сразу брак;
# остальные расхождения — «покажи человеку» (кроп строки и дифф).
ROBUST_CLASSES = {"omission", "doubling", "extra_text", "missing_line", "latin_substitute"}
# «Латинский нюх»: пары, где английская модель надёжно видит латиницу, которую русская исправила (опыт OCR на 714 синтетических баннерах: D 5/5 при 1/144
# ложных, R 5/7 при 0/144, g 9/16 при 2/144); n, u, r — шумно (34, 8, 6 ложных из 144) — не используются.
SNIFF_PAIRS = {"Д": "D", "д": "g", "Я": "R", "я": "R"}


def latin_sniff(expected: list[str], lines_meta: list[dict] | None) -> list[dict]:
    en = " ".join(L.get("text_en", "") for L in (lines_meta or []) if L.get("text_en"))
    if not en or not expected:
        return []
    exp_all = " ".join(expected)
    xw, ew = exp_all.split(), en.split()
    hits = []
    for i, w in enumerate(xw):
        cand = ew[i] if len(ew) == len(xw) else en
        for c, L in SNIFF_PAIRS.items():
            if c in w and L in cand and L not in exp_all:
                hits.append({"word": w, "cyr": c, "latin": L, "en_reading": cand if len(ew) == len(xw) else en[:80]})
    return hits


def gned(expected_words: list[str], got_words: list[str]) -> float | None:
    """GNED (TIIF-Bench): венгерское сопоставление слов по нормированной дистанции + штраф |m − n|; 0 — идеально."""
    m, n = len(expected_words), len(got_words)
    if m == 0 and n == 0:
        return 0.0
    if m == 0 or n == 0:
        return 1.0
    try:
        import numpy as np
        from scipy.optimize import linear_sum_assignment
    except ImportError:
        return None
    C = np.ones((max(m, n), max(m, n)))
    for i, a in enumerate(expected_words):
        for j, b in enumerate(got_words):
            C[i, j] = lev(a, b) / max(len(a), len(b), 1)
    r, c = linear_sum_assignment(C)
    matched = sum(C[i, j] for i, j in zip(r, c) if i < m and j < n)
    return round(float((matched + abs(m - n)) / max(m, n)), 4)


EXPECT_COUNT = re.compile(r"\s*\{[×xх](\d+)\}\s*$")     # «строка{×2}» — строка стоит на картинке дважды


def expect_counts(expected: list[str]) -> list[tuple[str, int]]:
    """Ожидаемые строки с числом вхождений: суффикс «{×N}» или повтор одинаковой строки в списке."""
    out: dict[str, int] = {}
    for e in expected:
        m = EXPECT_COUNT.search(e)
        s, n = (e[:m.start()], int(m.group(1))) if m else (e, 1)
        out[s] = out.get(s, 0) + max(1, n)
    return list(out.items())


def ocr_scale(o: dict) -> float:
    """Во сколько раз OCR уменьшил кадр перед поиском строк (предел длинной стороны детектора): высота букв для порога
    считается в масштабе распознавания, а не в пикселях файла."""
    size, lim_ = o.get("size") or [], o.get("det_limit") or []
    if size and len(lim_) == 2 and lim_[1] == "max" and max(size) > lim_[0]:
        return lim_[0] / max(size)
    return 1.0


def text_verdict(expected: list[str], transcript: str, case_sensitive: bool = False, yo_required: bool = True,
                 extra_allowed: bool = False, lines_meta: list[dict] | None = None, th: Th | None = None,
                 allowed: list[str] | None = None, h_scale: float = 1.0) -> dict:
    """Сверка ожидаемых строк брифа с транскриптом картинки (OCR, VLM или человек).
    Основа — stand_run.text_check (двойники, латинские недвойники, лишние слова, ё); сверху — классы ошибок
    по выравниванию (пропуск, удвоение, похожая буква, цифра), точность и полнота слов, GNED. Строка ищется столько раз,
    сколько вхождений заказано (expect_counts): второе вхождение — не «лишний текст». Высота букв — в масштабе
    распознавания (h_scale): расхождение в строке ниже text.fail_min_line_h_px — предупреждение (warn), искажение строки
    в полном размере — брак или «покажи человеку»."""
    sr = mod("stand_run")
    pairs = expect_counts(expected)
    expected = [e for e, _ in pairs]
    base = sr.text_check(expected, transcript) if expected else {"lines": [], "fake_latin": [], "extra_words": []}
    pure_cyr = bool(expected) and not any(LAT.search(e) for e in expected)
    T = norm_text(transcript, all_homoglyphs=pure_cyr)
    Tc = T if case_sensitive else T.lower()
    th = th or Th({"_flat": {}})
    h_fail = th("text.fail_min_line_h_px", 16)
    s_fail = th("text.fail_min_ocr_score", 0.9)
    # строки OCR в транскрипте: участок строки → высота букв в масштабе распознавания
    spans, cur = [], 0
    for L in lines_meta or []:
        nl = norm_text(L.get("text") or "", all_homoglyphs=pure_cyr)
        nl = nl if case_sensitive else nl.lower()
        pos = Tc.find(nl, cur) if nl else -1
        if pos < 0 or not L.get("h_px"):
            spans = None
            break
        spans.append((pos, pos + len(nl), L["h_px"] * h_scale))
        cur = pos + len(nl)

    def height_at(j0, j1):
        mid = (j0 + j1) // 2
        return next((h for a, b, h in spans or [] if a <= mid < b), None)
    lines, covered, Tw = [], [False] * len(Tc), Tc
    for e, cnt in pairs:
        E = norm_text(e, all_homoglyphs=pure_cyr)
        Ec = E if case_sensitive else E.lower()
        for k in range(cnt):
            dist, j0, j1, ops = fit_align(Ec, Tw)
            cls = classify_ops(ops, Ec)
            found = dist <= max(1, len(Ec)) * 0.5
            h = height_at(j0, j1) if found else None
            if found or k == 0:
                for j in range(j0, j1):
                    covered[j] = True
            if found:
                Tw = Tw[:j0] + "\x00" * (j1 - j0) + Tw[j1:]      # найденное вхождение второй раз не засчитывается
            lines.append({"expected": e, "found": found, "distance": dist, "cer": round(dist / max(1, len(Ec)), 4),
                          "match": Tc[j0:j1], "errors": cls if found else [],
                          "classes": sorted({c["class"] for c in cls}) if found else ["missing_line"],
                          **({"occurrence": k + 1} if cnt > 1 else {}),
                          **({"h_px": round(h, 1), "small": True} if h is not None and h < h_fail else {})})
    # лишний текст: слова транскрипта вне найденных окон (WeGenBench: точность — «нет лишнего»); считаются только буквы
    # и цифры вне окон — висящая точка или кавычка от JPEG-шума не «лишнее слово» («булок.» — ложный брак)
    extra, cur, start = [], "", 0
    for j, ch in enumerate(Tc + " "):
        if ch == " ":
            if cur and any(ch2.isalnum() and not covered[start + k] for k, ch2 in enumerate(cur)):
                extra.append(T[start:j])
            cur, start = "", j + 1
        else:
            cur += ch
    if allowed:   # разрешённый текст (этикетка товара и т. п.) — не «лишний»
        allow_words = {w.strip('.,:;!?"«»()') for x in allowed for w in norm_text(x, all_homoglyphs=pure_cyr).lower().split()}
        extra = [w for w in extra if w.lower().strip('.,:;!?"«»()') not in allow_words]
    exp_words = [w for e, cnt in pairs for w in norm_text(e, all_homoglyphs=pure_cyr).lower().split() * cnt]
    got_words = Tc.split()
    counts: dict[str, int] = {}
    full: dict[str, int] = {}
    small: dict[str, int] = {}
    for L in lines:
        for c in L["classes"]:
            counts[c] = counts.get(c, 0) + 1
            tgt = small if L.get("small") else full
            tgt[c] = tgt.get(c, 0) + 1
    line_fails = {c for c in full if c in FAIL_CLASSES}
    fails = sorted(line_fails | ({"missing_line"} if full.get("missing_line") else set()))
    small_fails = sorted({c for c in small if c in FAIL_CLASSES} | ({"yo_lost"} if yo_required and small.get("yo_lost") else set()))
    if base.get("fake_latin") and not all(LAT.search(e) for e in expected):
        fails = sorted(set(fails) | {"latin_substitute"})
    if yo_required and full.get("yo_lost"):
        fails = sorted(set(fails) | {"yo_lost"})
    if extra and not extra_allowed:
        fails = sorted(set(fails) | {"extra_text"})
    min_h = None
    if lines_meta:
        hs = [L.get("h_px") * h_scale for L in lines_meta if L.get("h_px")]
        min_h = round(min(hs), 1) if hs else None
    sniff = latin_sniff(expected, lines_meta)
    scores = [L.get("score_line", L.get("score_min")) for L in (lines_meta or []) if L.get("score_min") is not None]
    score_min = min(scores) if scores else None
    # высота для брака без человека: у расхождений строки она известна по строке (мелкие уже отделены); лишний текст,
    # ненайденная строка и сверка без привязки к строкам OCR — по самой мелкой строке кадра
    by_line = spans is not None and set(fails) <= line_fails
    height_ok = by_line or min_h is None or min_h >= h_fail
    if not fails and not sniff:
        verdict = "warn" if small_fails else "pass"
    elif fails and set(fails) <= ROBUST_CLASSES and (score_min is None or score_min >= s_fail) and height_ok:
        verdict = "fail"
    else:
        verdict = "needs_human"
    res = {"expected": expected, "transcript": transcript, "normalized": T, "lines": lines, "classes": counts,
           "fake_latin": base.get("fake_latin", []), "latin_suspect": sniff, "extra_text": extra, "ocr_score_min": score_min,
           "verdict": verdict, "small_text": small_fails,
           "precision_words": round(1 - len(extra) / max(1, len(got_words)), 4) if got_words else (1.0 if not expected else 0.0),
           "recall_lines": round(sum(L["found"] and not (set(L["classes"]) & FAIL_CLASSES) for L in lines) / max(1, len(lines)), 4),
           "gned": gned(exp_words, got_words), "fail_classes": fails, "pass": verdict == "pass", "min_line_h_px": min_h}
    return res




# ================================================================ вызов утилит соседей: JSON из stdout


def call_json(fn, **kw):
    """Вызвать cmd_* соседа (печатает JSON в stdout) с Namespace и вернуть (код, JSON)."""
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(argparse.Namespace(**kw))
    txt = buf.getvalue().strip()
    try:
        return rc, json.loads(txt)
    except json.JSONDecodeError:
        # некоторые cmd_* печатают несколько строк: берём последний JSON-объект
        for chunk in reversed(re.split(r"\n(?=\{)", txt)):
            try:
                return rc, json.loads(chunk)
            except json.JSONDecodeError:
                continue
        return rc, {"_raw": txt[-500:]}


# ================================================================ паспорта polza.py / mp_client.py


def find_passport(path: Path) -> tuple[dict | None, Path | None]:
    """Паспорт рядом с файлом: <стем>.passport.json (для нескольких файлов генерации — без суффикса _N)."""
    stems = [path.stem, re.sub(r"_\d+$", "", path.stem)]
    for st in dict.fromkeys(stems):
        pp = path.with_name(st + ".passport.json")
        if pp.exists():
            try:
                return json.loads(pp.read_text(encoding="utf-8")), pp
            except json.JSONDecodeError:
                return None, pp
    return None, None


def passport_facts(pp: dict, pp_path: Path, path: Path) -> dict:
    job = pp.get("job") or {}
    meta = job.get("meta") or {}
    fentry = {}
    for f in pp.get("files") or []:
        fp = f.get("path") if isinstance(f, dict) else f
        if fp and Path(fp).name == path.name:
            fentry = f if isinstance(f, dict) else {"path": f}
            break
    cost = pp.get("cost") or {}
    body = ((pp.get("request") or {}).get("body") or {})
    inp = body.get("input") if isinstance(body.get("input"), dict) else body
    out = {"passport": rel(pp_path), "passport_schema": pp.get("schema"), "channel": pp.get("channel") or "polza-media",
           "model": pp.get("model") or job.get("model"), "provider_actual": pp.get("provider_actual"), "tag": job.get("tag"),
           "agent": job.get("agent"), "variant": job.get("variant"), "test": meta.get("test"),
           "task_code": meta.get("code") or meta.get("task_code") or meta.get("task"),
           "cost_rub": cost.get("usage_cost_rub"), "estimate_rub": cost.get("estimate_rub"),
           "requested": {k: inp.get(k) for k in ("aspect_ratio", "image_resolution", "resolution", "duration", "background",
                                               "output_format", "size", "generate_audio") if isinstance(inp, dict) and k in inp},
           "media": fentry.get("media"), "sha256_passport": fentry.get("sha256"),
           "prompt": (pp.get("prompt") or "")[:300] if isinstance(pp.get("prompt"), str) else None}
    for k in ("expect", "slot", "series", "brief", "spec", "text_zone", "palette", "control", "source", "target", "mask",
              "orig", "judge", "success"):
        if k in meta:
            out.setdefault("meta", {})[k] = meta[k]
    return out


SLOT_KINDS = ("hero", "section", "product", "icon", "og", "texture")
# вид слота словаря site в строке плана ассетов → род слота порогов приёмки; прочие виды — общие пороги
PLAN_SLOT_KIND = {"hero-visual": "hero", "og-image": "og", "favicon": "icon", "icon": "icon", "texture": "texture"}


class AuditError(Exception):
    """Ошибка входа приёмки (план ассетов, слот) — код выхода 2."""


def plan_slot(plan_path: Path, slot_id: str | None, variant: str | None = None, mobile: bool = False) -> dict:
    """Строка слота плана ассетов (asset-plan v1): бюджет веса `max_kb` варианта и род слота для порогов. Вариант —
    --variant; без него — mobile при --mobile, иначе desktop, иначе первый вариант с числом `max_kb`. Заглушка или
    пустой `max_kb` — бюджет по умолчанию."""
    import yaml
    if not slot_id:
        raise AuditError("с --plan нужен --slot <id слота плана ассетов>")
    if not plan_path.is_file():
        raise AuditError(f"нет плана ассетов {plan_path}")
    try:
        doc = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise AuditError(f"план ассетов {plan_path} не разобран: {last_line(str(e))}")
    rows = [s for s in (doc.get("slots") if isinstance(doc, dict) else None) or [] if isinstance(s, dict)]
    row = next((s for s in rows if s.get("id") == slot_id), None)
    if row is None:
        raise AuditError(f"в плане {plan_path.name} нет слота {slot_id}; есть: "
                         + (", ".join(str(s.get("id")) for s in rows[:12]) or "ни одного"))
    vs = [v for v in row.get("variants") or [] if isinstance(v, dict)]

    def num(v):
        x = v.get("max_kb")
        return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None
    pick = next((v for v in vs if v.get("id") == (variant or ("mobile" if mobile else "desktop"))), None)
    if pick is None and variant:
        raise AuditError(f"у слота {slot_id} нет варианта {variant}; есть: "
                         + (", ".join(str(v.get("id")) for v in vs) or "ни одного"))
    if pick is None:
        pick = next((v for v in vs if num(v) is not None), vs[0] if vs else {})
    return {"id": slot_id, "kind": PLAN_SLOT_KIND.get(str(row.get("slot") or "")), "variant": pick.get("id"),
            "max_kb": num(pick), "plan": rel(plan_path)}


def ratio_of(s) -> float | None:
    if not s or not isinstance(s, str) or ":" not in s:
        return None
    try:
        a, b = s.split(":")
        return float(a) / float(b)
    except (ValueError, ZeroDivisionError):
        return None


# ================================================================ режим по файлу

TASK_MODE = {"IMG-CUTOUT": "cutout", "IMG-EDIT": "edit", "IMG-OUTPAINT": "edit", "IMG-TEXTURE": "texture",
             "VID-ALPHA": "video-alpha", "VEC-ICON-LINE": "svg-icon", "VEC-ICON-FILLED": "svg-icon", "VEC-ILLUSTR": "svg-icon",
             "VEC-PATTERN": "svg-icon", "VEC-TRACE": "svg-icon"}
SLOT_OF_TASK = {"IMG-HERO-PHOTO": "hero", "IMG-BG-ABSTRACT": "hero", "IMG-PRODUCT": "product", "IMG-ICON3D": "section",
                "IMG-ILLUSTR": "section", "IMG-SERIES": "section", "IMG-TEXT-LATIN": "og", "IMG-TEXT-CYR": "og",
                "IMG-MOCKUP": "section", "IMG-TEXTURE": "texture", "VID-HERO-LOOP": "hero", "VID-CINEMAGRAPH": "hero"}


def image_alpha_info(path: Path) -> dict:
    from PIL import Image
    with Image.open(path) as im:
        has = im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info)
        if not has:
            return {"has_alpha": False}
        a = im.convert("RGBA").getchannel("A")
        hist = a.histogram()
        n = sum(hist)
        return {"has_alpha": True, "alpha_min": min(i for i, v in enumerate(hist) if v),
                "transparent_frac": round(sum(hist[:5]) / n, 4), "partial_frac": round(sum(hist[5:250]) / n, 4)}


def infer_mode(path: Path, facts: dict | None, a) -> str:
    ext = path.suffix.lower()
    if ext in SVG_EXT:
        return "svg-icon"
    code = (facts or {}).get("task_code") or getattr(a, "task", None)
    if ext in VID_EXT:
        if code == "VID-ALPHA" or getattr(a, "key", None):
            return "video-alpha"
        return "video-loop"
    if code in TASK_MODE:
        m = TASK_MODE[code]
        if m == "edit" and not getattr(a, "orig", None) and not ((facts or {}).get("meta") or {}).get("source"):
            return "image"
        return m
    if getattr(a, "orig", None):
        return "edit"
    if getattr(a, "slot", None) == "og":
        return "og"
    ai = image_alpha_info(path)
    if ai.get("has_alpha") and ai.get("transparent_frac", 0) > 0.01:
        return "cutout"
    return "image"


# ================================================================ картинка: загрузка и общие проверки


def load_rgb_np(path: Path, maxside: int | None = None, bg=(255, 255, 255)):
    import numpy as np
    from PIL import Image
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P", "PA"):
        im = im.convert("RGBA")
        base = Image.new("RGBA", im.size, bg + (255,))
        base.alpha_composite(im)
        im = base
    im = im.convert("RGB")
    if maxside and max(im.size) > maxside:
        s = maxside / max(im.size)
        im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    return np.asarray(im).astype(np.float32)


def check_file_basics(R: Report, path: Path, facts: dict | None, a):
    from PIL import Image
    th = R.th
    st = path.stat()
    info = {"bytes": st.st_size, "sha256": sha256_file(path)}
    if facts and facts.get("sha256_passport") and facts["sha256_passport"] != info["sha256"]:
        R.defect("QA-FILE-CHANGED", "info", "файл отличается от скачанного (паспорт): производная — провенанс вендора мог "
                 "потеряться (C2PA не переживает перекодирование, H/04b)", value=facts["sha256_passport"][:12])
    if path.suffix.lower() in IMG_EXT:
        with Image.open(path) as im:
            info.update({"w": im.width, "h": im.height, "ratio": round(im.width / im.height, 4), "format": im.format,
                         "mode": im.mode, "icc": bool(im.info.get("icc_profile")), "exif": bool(im.info.get("exif"))})
        want = ratio_of((facts or {}).get("requested", {}).get("aspect_ratio")) or ratio_of(getattr(a, "ratio", None))
        if want:
            dev = abs(info["ratio"] / want - 1)
            info["ratio_requested"] = round(want, 4)
            if dev > th("image.ratio_tolerance", 0.02):
                R.defect("QA-DIMS-RATIO", "fail", f"пропорция {info['ratio']:.3f} вместо заказанной {want:.3f}",
                         metric="dims.ratio", value=info["ratio"], th_key="image.ratio_tolerance")
    R.checks["file"] = info
    return info


def check_budget(R: Report, info: dict, slot: str | None, a, kind="image", plan: dict | None = None):
    """Бюджет веса — только для файлов на страницу (--stage web). Со строкой плана ассетов (--plan, --slot) — её `max_kb`;
    без плана — умолчание рода слота: ai-media 01/01 §7. Телефонный кадр (--mobile) — свой ключ слота `<slot>_mobile_kb`,
    если он есть (hero ≤ 80 КБ), иначе ключ слота."""
    if getattr(a, "stage", "master") != "web":
        return
    if plan and plan.get("max_kb") is not None:
        kb, lim = info["bytes"] / 1024, plan["max_kb"]
        R.checks.setdefault("budget", {})[plan["id"]] = {"kb": round(kb, 1), "limit_kb": lim,
                                                        "key": f"plan:{plan['id']}/{plan['variant']}"}
        if kb > lim:
            R.defect("QA-BUDGET", "warn", f"{kb:.0f} КБ > бюджета {lim} КБ слота {plan['id']} плана ассетов "
                     f"(вариант {plan['variant']})", metric="file.bytes", value=round(kb, 1), threshold=lim)
        return
    if not slot:
        return
    key = f"budget.{kind}.{slot}_kb"
    if getattr(a, "mobile", False) and R.th(f"budget.{kind}.{slot}_mobile_kb") is not None:
        key = f"budget.{kind}.{slot}_mobile_kb"
    lim = R.th(key)
    if lim is None:
        return
    kb = info["bytes"] / 1024
    R.checks.setdefault("budget", {})[slot] = {"kb": round(kb, 1), "limit_kb": lim, "key": key}
    if kb > lim:
        R.defect("QA-BUDGET", "warn", f"{kb:.0f} КБ > бюджета слота {slot} {lim} КБ", metric="file.bytes", value=round(kb, 1),
                 th_key=key)


def slop_color_metrics(path: Path) -> dict:
    im = mod("image_metrics")
    return im.metrics(im.load(str(path)))


def dna_reference_metrics(dna: dict | None, dna_path: Path | None) -> dict | None:
    """Средние цветовые метрики эталонов паспорта визуала (references) — основа порогов «к эталону бренда» (ai-media 06/04)."""
    if not dna or not dna_path:
        return None
    refs = [r.get("src") for r in dna.get("references", []) if r.get("src")]
    vals = []
    for s in refs:
        p = (dna_path.parent / s)
        if p.exists():
            try:
                vals.append(slop_color_metrics(p))
            except Exception:  # noqa: BLE001
                pass
    if not vals:
        return None
    keys = ("colorfulness", "hdr_index", "sat_share", "warm_b")
    return {k: round(sum(v[k] for v in vals if v.get(k) is not None) / max(1, sum(1 for v in vals if v.get(k) is not None)), 4)
            for k in keys} | {"n": len(vals)}


def check_slop_color(R: Report, path: Path, ref: dict | None, dna: dict | None):
    th = R.th
    m = slop_color_metrics(path)
    R.checks["slop_color"] = m
    renderish = (m.get("chroma_med") or 0) < 0.005 and (m.get("clip_hi") or 0) > 0.1   # рендер на белом: пороги фото не применимы
    if ref:
        R.checks["slop_color"]["ref"] = ref
        rel_c = m["colorfulness"] / max(ref["colorfulness"], 1e-6)
        dh = m["hdr_index"] - ref["hdr_index"]
        if rel_c > th("image.colorfulness_max_rel", 1.2):
            R.defect("QA-COLOR-OVERSAT", "warn", f"colorfulness ×{rel_c:.2f} к эталонам бренда", metric="slop_color.colorfulness",
                     value=rel_c, th_key="image.colorfulness_max_rel", marker="IMG-M03")
        if dh > th("image.hdr_index_max_delta", 0.1):
            R.defect("QA-COLOR-HDR", "warn", f"hdr_index +{dh:.2f} к эталонам", metric="slop_color.hdr_index", value=dh,
                     th_key="image.hdr_index_max_delta", marker="IMG-M03")
        if rel_c > th("image.filter_colorfulness_rel", 1.5) and dh > th("image.hdr_index_max_delta", 0.1):
            R.defect("QA-FILTER-INSTAGRAM", "warn", "«Instagram-фильтр»: насыщенность +50 % и локальный контраст +0,1 к эталону",
                     metric="slop_color", value=round(rel_c, 2), th_key="image.filter_colorfulness_rel", marker="IMG-M03")
    elif not renderish:
        for k, key, code in (("colorfulness", "image.colorfulness_q3", "QA-COLOR-OVERSAT"), ("sat_share", "image.sat_share_q3", "QA-COLOR-OVERSAT"),
                             ("hdr_index", "image.hdr_index_q3", "QA-COLOR-HDR"), ("clip_hi", "image.clip_hi_q3", "QA-COLOR-CLIP")):
            v, lim = m.get(k), th(key)
            if v is not None and lim is not None and v > lim:
                R.defect(code, "warn", f"{k} {v} выше Q3 фото лидеров ({lim}) — посмотреть глазом, не брак сам по себе",
                         metric=f"slop_color.{k}", value=v, th_key=key, marker="IMG-M03")
    wb_neutral = bool(dna and ((dna.get("palette") or {}).get("neutral_wb") or {}).get("target_b", 1) <= 0.004)
    if m.get("warm_b") is not None and m["warm_b"] > th("image.warm_b_max", 4.0):
        R.defect("QA-COLOR-WARM", "warn" if wb_neutral else "info",   # предупреждение — только при нейтральном белом в паспорте
                 f"b* нейтралей +{m['warm_b']} — жёлтый сдвиг белого (у 9 из 51 фото лидеров это стиль)",
                 metric="slop_color.warm_b", value=m["warm_b"], th_key="image.warm_b_max", marker="IMG-M04")
    purple_ok = False
    if dna:
        for e in (dna.get("palette") or {}).get("image_palette", []) + (dna.get("palette") or {}).get("illustration_palette", []):
            try:
                _, C, H = mod("vlm_to_dna").hex_oklch(e["hex"])
                purple_ok |= C > 0.04 and 270 <= H <= 320
            except Exception:  # noqa: BLE001
                pass
    if (m.get("purple_share") or 0) > th("image.purple_share_max", 0.5) and not purple_ok:
        R.defect("QA-COLOR-PURPLE", "warn", f"пурпур 270–320° — {m['purple_share']:.2f} хроматических пикселей без пурпура в бренде",
                 metric="slop_color.purple_share", value=m["purple_share"], th_key="image.purple_share_max", marker="IMG-M05")
    return m


def text_zone_rect(a, facts: dict | None, spec: dict | None, dna: dict | None):
    """Зона текста: --text-zone x0,y0,x1,y1 → спецификация (composition.text_zone.rect) → паспорт визуала (сторона + доля)."""
    if getattr(a, "text_zone", None):
        v = [float(x) for x in a.text_zone.split(",")]
        return v, "--text-zone"
    tz = ((spec or {}).get("composition") or {}).get("text_zone") or ((facts or {}).get("meta") or {}).get("text_zone")
    if isinstance(tz, dict) and tz.get("rect"):
        return list(map(float, tz["rect"])), "spec"
    d = ((dna or {}).get("composition") or {}).get("text_zone_default")
    if d and d.get("side") in ("left", "right", "top", "bottom"):
        s = float(d.get("share", 0.4))
        rect = {"left": [0, 0, s, 1], "right": [1 - s, 0, 1, 1], "top": [0, 0, 1, s], "bottom": [0, 1 - s, 1, 1]}[d["side"]]
        return rect, "dna"
    return None, None


def check_composition(R: Report, path: Path, rect, slot: str | None, dna: dict | None, spec: dict | None):
    th = R.th
    cm = mod("composition_metrics")
    c = cm.analyse(str(path), tuple(rect) if rect else (0, 0, .45, 1))
    R.checks["composition"] = {k: c[k] for k in ("centroid_x", "centroid_y", "center_offset", "mirror_sym", "empty_share",
                                                 "zone_edge", "blobs")}
    comp = (dna or {}).get("composition") or {}
    region = comp.get("subject_region") or ((spec or {}).get("composition") or {}).get("subject_region")
    if rect and slot in ("hero", "og", None) and c["center_offset"] < th("composition.center_offset_min", 0.08):
        R.defect("QA-COMP-CENTER", "warn", "главное — строго по центру при заказанной зоне текста («средний вид»)",
                 metric="composition.center_offset", value=c["center_offset"], th_key="composition.center_offset_min",
                 marker="IMG-M09")
    if region == "right-third" and c["centroid_x"] < th("composition.centroid_x_min", 0.62):
        R.defect("QA-COMP-SIDE", "warn", f"центр значимости x = {c['centroid_x']} — не в правой трети", metric="composition.centroid_x",
                 value=c["centroid_x"], th_key="composition.centroid_x_min")
    if region == "left-third" and c["centroid_x"] > 1 - th("composition.centroid_x_min", 0.62):
        R.defect("QA-COMP-SIDE", "warn", f"центр значимости x = {c['centroid_x']} — не в левой трети", metric="composition.centroid_x",
                 value=c["centroid_x"], th_key="composition.centroid_x_min")
    maxel = comp.get("max_elements") or ((spec or {}).get("composition") or {}).get("max_elements")
    if maxel is None and slot == "hero":
        maxel = th("composition.blobs_max", 3)
    if maxel is not None and c["blobs"] > maxel:
        R.defect("QA-COMP-CLUTTER", "warn", f"пятен значимости {c['blobs']} > {maxel} — перегруженность", metric="composition.blobs",
                 value=c["blobs"], threshold=maxel, th_key="composition.blobs_max" if not comp.get("max_elements") else None)
    neg = comp.get("negative_space_min")
    if neg is not None and c["empty_share"] < neg:
        R.defect("QA-COMP-NO-AIR", "warn", f"спокойных клеток {c['empty_share']} < {neg}", metric="composition.empty_share",
                 value=c["empty_share"], threshold=neg)
    return c


def check_text_zone(R: Report, path: Path, rect, dna: dict | None, text_color: str | None):
    """Плотность краёв зоны и скрим под текст (p99,9 → проверка F83 по худшему пикселю)."""
    th = R.th
    tz = mod("text_zone")
    img = tz.load(str(path), 1280)
    stats = tz.zone_stats(img, tuple(rect))
    out = {"rect": [round(x, 3) for x in rect], "edge_density": round(stats["edge_density"], 4), "L_std": round(stats["L_std"], 4),
           "colors": {}}
    q = th("text_zone.scrim_percentile", 99.9)
    target = th("text_zone.contrast_min", 4.5)
    colors = [text_color] if text_color else ["#ffffff", "#111111"]
    for col in colors:
        zc = tz.zone_contrast(img, tuple(rect), col)
        a_q = tz.scrim_alpha(img, tuple(rect), col, target, q)
        a_w = tz.scrim_alpha(img, tuple(rect), col, target, 100)
        out["colors"][col] = {"contrast_worst": round(zc["worst"], 2), "contrast_p95": round(zc["p95"], 2),
                              "f83_quick_no_scrim": zc["worst"] >= target, f"scrim_alpha_p{q}": a_q, "scrim_alpha_f83": a_w}
    best = min(out["colors"].items(), key=lambda kv: kv[1]["scrim_alpha_f83"])
    out["best_text_color"], out["best_scrim_alpha_f83"] = best[0], best[1]["scrim_alpha_f83"]
    R.checks["text_zone"] = out
    lim = th("text_zone.edge_density_max", 0.06)
    if stats["edge_density"] > lim:
        R.defect("QA-ZONE-BUSY", "warn", f"зона текста неспокойная: плотность краёв {stats['edge_density']:.3f} > {lim}",
                 metric="text_zone.edge_density", value=stats["edge_density"], th_key="text_zone.edge_density_max")
    if out["best_scrim_alpha_f83"] > th("text_zone.scrim_alpha_warn", 0.55):
        R.defect("QA-ZONE-SCRIM", "warn", f"для WCAG F83 нужна плашка α {out['best_scrim_alpha_f83']} даже для лучшего цвета текста "
                 f"({out['best_text_color']}) — «серая коробка»; сначала композиция", metric="text_zone.best_scrim_alpha_f83",
                 value=out["best_scrim_alpha_f83"], th_key="text_zone.scrim_alpha_warn")
    return out


def check_palette(R: Report, path: Path, dna: dict | None, spec: dict | None):
    """Палитра к паспорту визуала или спецификации: ΔE OKLab до палитры, снятой с картинки, и покрытие (F-05, vlm_to_dna)."""
    pal = []
    if dna:
        pal = [dict(e) for e in (dna.get("palette") or {}).get("image_palette", [])]
    if not pal and spec:
        pal = [dict(e) for e in spec.get("palette", [])]
    if not pal:
        return None
    vd = mod("vlm_to_dna")
    measured = vd.measure_image(str(path))
    rows = vd.palette_check([{"hex": e["hex"], "name": e.get("name") or e.get("role"),
                              "share": e.get("share", e.get("share_max", 0))} for e in pal], measured,
                            thr=R.th("palette.de_ok", 0.05))
    ok = sum(r["ok"] for r in rows)
    need = min(len(rows), R.th("palette.min_matched", 3))
    R.checks["palette"] = {"rows": rows, "matched": ok, "of": len(rows), "measured": measured["palette"]}
    if ok < need:
        R.defect("QA-PALETTE-OFF", "warn", f"цвета паспорта найдены {ok} из {len(rows)} (нужно ≥ {need} в ΔE OKLab ≤ "
                 f"{R.th('palette.de_ok', 0.05)})", metric="palette.matched", value=ok, th_key="palette.min_matched")
    return rows


# ================================================================ провенанс (информационно; решения — ворота 12-legal-provenance/04)


def provenance(path: Path, out_dir: Path | None = None) -> dict:
    """`provenance_check.py scan PATH --json F` (C2PA, IPTC/XMP, AIGC, подпись Recraft, маркеры) и `--corners`: эвристика
    видимой метки в углах и лист углов для глаза (ворота 12-legal-provenance/04 §5 п. 7)."""
    tool = TOOLS / "provenance_check.py"
    try:
        sheet = None
        with tempfile.TemporaryDirectory() as td:
            jf = Path(td) / "p.json"
            cmd = [sys.executable, str(tool), "scan", str(path), "--json", str(jf)]
            if out_dir is not None:
                cmd += ["--corners", "--out", str(Path(td) / "o")]
            subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            d = json.loads(jf.read_text(encoding="utf-8"))
            cs = Path(td) / "o" / "corners.jpg"
            if out_dir is not None and cs.exists():
                sheet = Path(out_dir) / (path.stem + "_corners.jpg")
                shutil.copyfile(cs, sheet)
        f = (d.get("files") or [{}])[0]
        s = f.get("summary") or {}
        # бинарники, которых provenance_check не нашёл: метки C2PA и XMP не прочитаны — сведения неполны
        missing = [b for b, part in (("c2patool", "c2pa"), ("exiftool", "exif"))
                   if "не найден" in str((f.get(part) or {}).get("error") or "")]
        return {"tool": f"{rel(tool)} {d.get('version', '')}".strip(), "c2pa_present": (f.get("c2pa") or {}).get("present"),
                "c2pa": f.get("c2pa"), "digital_source_type": (f.get("exif") or {}).get("digital_source_type"),
                "markers": f.get("bytes_markers"), "summary": s, "visible_suspect": s.get("visible_suspect") or [],
                "corners_sheet": rel(sheet) if sheet else None, **({"missing": missing} if missing else {})}
    except Exception as e:  # noqa: BLE001
        return {"tool": rel(tool), "error": str(e)[:200]}


# ================================================================ режимы


def audit_image(R: Report, path: Path, facts, a, ctx):
    info = check_file_basics(R, path, facts, a)
    slot = ctx["slot"]
    if slot in ("hero",) and not getattr(a, "mobile", False) and max(info["w"], info["h"]) < R.th("image.hero_master_min_px", 2560):
        R.defect("QA-DIMS-SMALL", "info" if getattr(a, "stage", "master") == "master" else "warn",
                 f"длинная сторона {max(info['w'], info['h'])} px < мастера hero {R.th('image.hero_master_min_px', 2560)} px "
                 "(ступень 2K/4K модели или апскейл Lanczos, H 08/02 §1)", metric="file.w", value=max(info["w"], info["h"]),
                 th_key="image.hero_master_min_px")
    check_budget(R, info, slot, a, plan=ctx.get("plan"))
    check_slop_color(R, path, ctx.get("ref_metrics"), ctx.get("dna"))
    rect, rect_src = text_zone_rect(a, facts, ctx.get("spec"), ctx.get("dna"))
    check_composition(R, path, rect, slot, ctx.get("dna"), ctx.get("spec"))
    if rect:
        tz = check_text_zone(R, path, rect, ctx.get("dna"), getattr(a, "text_color", None))
        tz["source"] = rect_src
    check_palette(R, path, ctx.get("dna"), ctx.get("spec"))
    master = Path(a.master) if getattr(a, "master", None) else None
    if master:
        check_ssimulacra(R, path, master, slot)
    if master is None or master.suffix.lower() in IMG_EXT and master.exists():
        check_sharpness(R, master or path)      # источник — мастер, без него — сам файл
    return R


def depth_png(src: Path, dst: Path, size: tuple | None = None, via: tuple | None = None) -> bool:
    """Картинка → PNG 16 бит на канал без усечения глубины (ffmpeg читает 16-битные PNG и TIFF). size — пересчёт Lanczos
    к размеру; via — сначала к этому размеру, затем к size (проба резкости)."""
    steps = [f"scale={wh[0]}:{wh[1]}:flags=lanczos" for wh in (via, size) if wh]
    cmd = [kbpaths.ffmpeg(), "-v", "error", "-y", "-i", str(src)] + (["-vf", ",".join(steps)] if steps else [])
    r = subprocess.run(cmd + ["-frames:v", "1", "-pix_fmt", "rgb48be", str(dst)], capture_output=True)
    return r.returncode == 0 and dst.exists()


def s2_score(s2: Path, ref: Path, dist: Path) -> float | None:
    r = subprocess.run([str(s2), str(ref), str(dist)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip().split()[-1])
    except (ValueError, IndexError):
        return None


def check_ssimulacra(R: Report, path: Path, master: Path, slot: str | None):
    """Производная для страницы против мастера: SSIMULACRA2 (H 08/04 §1.2: ≥ 80 hero, ≥ 70 прочее). Глубина не усекается:
    AVIF декодируется в PNG 16 бит (`avifdec -d 16`), мастер и производная приводятся к PNG 16 бит — оценка 10-битного
    файла и 16-битного мастера не занижается сравнением через 8 бит."""
    from PIL import Image
    s2 = kbpaths.bin_dir("libjxl", "tools", "ssimulacra2")
    if not master.exists():
        R.errors.append(f"SSIMULACRA2 не запущен: нет мастера {master}")
        return
    ext = path.suffix.lower()
    dec_bin = {".avif": kbpaths.bin_dir("libavif", "avifdec"), ".webp": kbpaths.bin_dir("libwebp", "dwebp"),
               ".jxl": kbpaths.bin_dir("libjxl", "tools", "djxl")}.get(ext)
    for b in (s2, dec_bin):
        if b is not None and not b.exists():
            R.no_env(env_hint(f"{b.name} не найден", "--bin"), "SSIMULACRA2")
            return
    with tempfile.TemporaryDirectory() as td:
        dec, ref = Path(td) / "dec.png", Path(td) / "ref.png"
        if ext == ".avif":
            subprocess.run([str(dec_bin), "-d", "16", str(path), str(dec)], capture_output=True)
        elif ext == ".webp":
            subprocess.run([str(dec_bin), "-quiet", str(path), "-o", str(dec)], capture_output=True)
        elif ext == ".jxl":
            subprocess.run([str(dec_bin), str(path), str(dec)], capture_output=True)
        else:
            depth_png(path, dec)
        if not dec.exists():
            R.errors.append(f"SSIMULACRA2 не запущен: {path.name} не декодирован")
            return
        with Image.open(dec) as d, Image.open(master) as m:
            dsize, msize = d.size, m.size
        if not depth_png(master, ref, dsize if msize != dsize else None):
            R.errors.append(f"SSIMULACRA2 не запущен: мастер {master.name} не приведён к PNG")
            return
        score = s2_score(s2, ref, dec)
    if score is None:
        return
    key = "encoding.ssimulacra2_hero_min" if slot in ("hero", "product") else "encoding.ssimulacra2_min"
    lim = R.th(key, 80 if slot in ("hero", "product") else 70)
    R.checks["encoding"] = {"master": rel(master), "ssimulacra2": round(score, 2), "min": lim}
    if score < lim:
        R.defect("QA-ENCODE-QUALITY", "fail", f"SSIMULACRA2 {score:.1f} < {lim}: сжато заметно (avif_pick.sh подберёт q)",
                 metric="encoding.ssimulacra2", value=score, th_key=key)


def check_sharpness(R: Report, src: Path):
    """Резкость источника — отдельно от оценки сжатия: производная сверяется со своим мастером и мягкости мастера не видит.
    Кадр сравнивается со своей копией, уменьшенной в image.soft_probe_scale раз и возвращённой к размеру (Lanczos): копия
    неотличима (SSIMULACRA2 не ниже encoding.ssimulacra2_hero_min — «не видно при сравнении рядом») — деталей на свой размер
    у кадра нет: источник увеличен или мягкий. Гладкий сюжет (фон, рендер) даёт то же число, поэтому находка — сведения."""
    from PIL import Image
    s2 = kbpaths.bin_dir("libjxl", "tools", "ssimulacra2")
    scale, lim = R.th("image.soft_probe_scale"), R.th("encoding.ssimulacra2_hero_min")
    if not scale or lim is None or src.suffix.lower() in (".avif", ".jxl", ".gif"):
        return
    if not s2.exists():
        R.no_env(env_hint(f"{s2.name} не найден (резкость источника не измерена)", "--bin"))
        return
    with Image.open(src) as im:
        w, h = im.size
    small = (max(1, round(w / scale)), max(1, round(h / scale)))
    with tempfile.TemporaryDirectory() as td:
        full, probe = Path(td) / "full.png", Path(td) / "probe.png"
        if not (depth_png(src, full) and depth_png(src, probe, (w, h), via=small)):
            return
        score = s2_score(s2, full, probe)
    if score is None:
        return
    R.checks["sharpness"] = {"source": rel(src), "probe_scale": scale, "probe_ssimulacra2": round(score, 2), "soft_from": lim}
    if score >= lim:
        R.defect("QA-SOURCE-SOFT", "info", f"источник мягкий: копия в {scale} раза меньшего размера неотличима от кадра "
                 f"(SSIMULACRA2 {score:.1f} ≥ {lim}) — деталей на свой размер нет: увеличенный источник или гладкий сюжет, "
                 "посмотреть на 100 % [не откалибровано]", metric="sharpness.probe_ssimulacra2", value=score,
                 th_key="image.soft_probe_scale")


def audit_cutout(R: Report, path: Path, facts, a, ctx):
    import numpy as np
    from PIL import Image
    info = check_file_basics(R, path, facts, a)
    check_budget(R, info, ctx["slot"], a, plan=ctx.get("plan"))
    ac = mod("alpha_check")
    _, fake = call_json(ac.cmd_fake, img=str(path))
    R.checks["alpha_fake"] = fake
    if fake.get("verdict") == "FAKE_CHECKERBOARD":
        R.defect("QA-ALPHA-FAKE", "fail", "нарисованная шахматка вместо прозрачности (OpenAI: «checkerboard is not transparency»)",
                 metric="alpha_fake.checker_score", value=fake.get("checker_score"), marker="IMG-M23")
        return R
    if fake.get("verdict") == "OPAQUE":
        R.defect("QA-ALPHA-MISSING", "fail", "альфы нет: картинка непрозрачна — вырез не сделан", metric="alpha_fake.opaque_frac",
                 value=fake.get("opaque_frac"))
        return R
    _, halo = call_json(ac.cmd_halo, rgba=str(path), bg=getattr(a, "bg", None))
    R.checks["alpha_halo"] = halo
    if halo.get("transparent_frac", 0) < R.th("cutout.transparent_frac_min", 0.2):
        R.defect("QA-ALPHA-LITTLE", "warn", f"прозрачно лишь {halo.get('transparent_frac')} кадра — объект во весь кадр или "
                 "альфа почти не используется", metric="alpha_halo.transparent_frac", value=halo.get("transparent_frac"),
                 th_key="cutout.transparent_frac_min")
    im = Image.open(path).convert("RGBA")
    al_ = np.asarray(im)[..., 3]
    translucent = float(((al_ > 25) & (al_ < 230)).sum() / max(1, (al_ > 25).sum()))
    if (halo.get("halo_px") or 0) > R.th("cutout.halo_px_max", 2.0):
        # на полупрозрачном (стекло, дым, ткань) «ядро» alpha_check мало, и кайма законно отличается от него — ореол по этой
        # эвристике ложный (эталонный рендер матового флакона → 12 px); смотреть на контрастном фоне глазами
        glassy = getattr(a, "object", None) == "glass" or translucent > 0.25
        R.defect("QA-ALPHA-HALO", "info" if glassy else "warn",
                 f"ореол {halo.get('halo_px')} px (кайма цвета фона) — " + ("полупрозрачный объект: эвристика ненадёжна, смотреть на "
                 "чёрном и белом" if glassy else "деконтаминация или сужение края"), metric="alpha_halo.halo_px",
                 value=halo.get("halo_px"), th_key="cutout.halo_px_max")
    al = np.asarray(im)[..., 3]
    ys, xs = np.nonzero(al > 127)
    if len(xs):
        H, W = al.shape
        margin = min(xs.min() / W, ys.min() / H, (W - 1 - xs.max()) / W, (H - 1 - ys.max()) / H)
        obj = al > 127
        partial_in = float(((al > 25) & (al < 230)).sum() / max(1, (al > 25).sum()))
        R.checks["alpha_geometry"] = {"margin_frac": round(float(margin), 4), "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                                      "object_frac": round(float(obj.mean()), 4), "partial_in_object": round(partial_in, 4)}
        if margin < R.th("cutout.margin_min_frac", 0.02):
            R.defect("QA-ALPHA-MARGIN", "warn", f"поле {margin:.3f} стороны < 2 % — объект упирается в край, обрезаны кайма и тень",
                     metric="alpha_geometry.margin_frac", value=margin, th_key="cutout.margin_min_frac")
        kind = getattr(a, "object", None)
        if kind == "glass" and partial_in < R.th("cutout.glass_partial_min", 0.3):
            R.defect("QA-ALPHA-GLASS", "warn", f"стекло почти непрозрачно: полупрозрачных {partial_in:.2f} тела (< 0,3)",
                     metric="alpha_geometry.partial_in_object", value=partial_in, th_key="cutout.glass_partial_min")
        if kind in ("hair", "fur") and partial_in < R.th("cutout.fiber_partial_min", 0.03):
            R.defect("QA-ALPHA-FIBERS", "warn", f"волокна «подстрижены»: полупрозрачных {partial_in:.3f} (< 0,03)",
                     metric="alpha_geometry.partial_in_object", value=partial_in, th_key="cutout.fiber_partial_min")
    if getattr(a, "ref_alpha", None):
        _, m = call_json(ac.cmd_metrics, pred=str(path), gt=a.ref_alpha, rgb=None, src=None)
        R.checks["alpha_vs_ref"] = m
        kind = getattr(a, "object", None)
        key = "cutout.iou_min_fibers" if kind in ("hair", "fur") else "cutout.iou_min_solid"
        if m.get("iou") is not None and m["iou"] < R.th(key, 0.95):
            R.defect("QA-ALPHA-IOU", "fail", f"IoU с эталонной альфой {m['iou']} < {R.th(key)}", metric="alpha_vs_ref.iou",
                     value=m["iou"], th_key=key)
        if (m.get("band_mae_x1000") or 0) > R.th("cutout.band_mae_x1000_max", 150):
            R.defect("QA-ALPHA-EDGE", "warn", f"ошибка края {m['band_mae_x1000']} ×10⁻³ > 150", metric="alpha_vs_ref.band_mae_x1000",
                     value=m["band_mae_x1000"], th_key="cutout.band_mae_x1000_max")
    return R


def diff_mask(orig: Path, edited: Path, thr: float = 5.0, min_frac: float = 0.0005):
    """Маска изменений для безмасочной правки (edit_check её не строит): подгонка цвета по «устойчивым» пикселям,
    ΔE00 > thr, открытие 3×3 и закрытие 5×5, компоненты ≥ min_frac кадра. Возвращает (маска bool, отчёт)."""
    import numpy as np
    from scipy import ndimage as ndi
    ec = mod("edit_check")
    O, E = ec.load_rgb(str(orig)), ec.load_rgb(str(edited))
    h, w = O.shape[:2]
    if E.shape[:2] != O.shape[:2]:
        E = ec.resize_to(E, w, h)
    de0 = ec.de2000(ec.srgb_to_lab(O), ec.srgb_to_lab(E))
    calm = de0 < np.percentile(de0, 60)
    gains = []
    for c in range(3):
        o, e = O[..., c][calm], E[..., c][calm]
        A = np.vstack([e, np.ones_like(e)]).T
        g, off = np.linalg.lstsq(A, o, rcond=None)[0]
        E[..., c] = np.clip(E[..., c] * g + off, 0, 1)
        gains.append([round(float(g), 4), round(float(off), 4)])
    de = ec.de2000(ec.srgb_to_lab(O), ec.srgb_to_lab(E))
    m = de > thr
    m = ndi.binary_opening(m, structure=np.ones((3, 3)))
    m = ndi.binary_closing(m, structure=np.ones((5, 5)))
    lab, n = ndi.label(m)
    comps = []
    if n:
        sizes = ndi.sum(np.ones_like(de), lab, range(1, n + 1))
        keep = [i + 1 for i, s in enumerate(sizes) if s >= min_frac * h * w]
        m = np.isin(lab, keep)
        for i in keep:
            ys, xs = np.nonzero(lab == i)
            comps.append({"area_frac": round(float(len(xs) / (h * w)), 4),
                          "bbox_frac": [round(xs.min() / w, 3), round(ys.min() / h, 3), round(xs.max() / w, 3), round(ys.max() / h, 3)]})
        comps.sort(key=lambda c: -c["area_frac"])
    return m, {"color_match_gain_offset": gains, "changed_frac": round(float(m.mean()), 4), "regions": len(comps),
               "largest": comps[:6], "de_median_after_match": round(float(np.median(de)), 3)}


def local_shift(orig: Path, edited: Path, target_mask: str | None, mask_mode: str, band: int, de_thr: float, min_frac: float):
    """Локальный сдвиг вне цели после робастной подгонки цвета (своя проверка K поверх edit_check.py): подгонка по
    пикселям «вне цели» в 2 прохода (второй — без пикселей с остатком ΔE00 > 3), затем связные области ΔE00 > de_thr
    площадью ≥ min_frac «вне цели». Зачем: глобальная --match-color убирает общий сдвиг модели, и локальная утечка слабее
    ΔE00 5 перестаёт быть видна порогом edit_check (утечка 0,131 без подгонки → 0,0001 с подгонкой, ai-media 08/02)."""
    import numpy as np
    from scipy import ndimage as ndi
    ec = mod("edit_check")
    O, E0 = ec.load_rgb(str(orig)), ec.load_rgb(str(edited))
    h, w = O.shape[:2]
    if E0.shape[:2] != O.shape[:2]:
        E0 = ec.resize_to(E0, w, h)
    tgt = ec.load_mask(target_mask, mask_mode, (h, w)) if target_mask else np.zeros((h, w), bool)
    far = ~ndi.binary_dilation(tgt, iterations=band) if tgt.any() else np.ones((h, w), bool)
    Lo = ec.srgb_to_lab(O)
    fit = far.copy()
    for it in range(2):
        E = E0.copy()
        for c in range(3):
            o, e = O[..., c][fit], E0[..., c][fit]
            g, off = np.linalg.lstsq(np.vstack([e, np.ones_like(e)]).T, o, rcond=None)[0]
            E[..., c] = np.clip(E0[..., c] * g + off, 0, 1)
        de = ec.de2000(Lo, ec.srgb_to_lab(E))
        if it == 0:
            keep = far & (de <= 3.0)
            if keep.sum() < 0.5 * far.sum():
                break
            fit = keep
    m = ndi.binary_opening((de > de_thr) & far, structure=np.ones((5, 5)))
    lab, n = ndi.label(m)
    dist = ndi.distance_transform_edt(~tgt) if tgt.any() else None
    regs = []
    if n:
        sizes = ndi.sum(np.ones_like(de), lab, range(1, n + 1))
        for i, sz in enumerate(sizes, 1):
            if sz >= min_frac * far.sum():
                reg = lab == i
                ys, xs = np.nonzero(reg)
                dmin = float(dist[reg].min()) / max(h, w) if dist is not None else None
                regs.append({"area_frac_outside": round(float(sz / far.sum()), 4), "de_median": round(float(np.median(de[reg])), 2),
                             "bbox_frac": [round(xs.min() / w, 3), round(ys.min() / h, 3), round(xs.max() / w, 3), round(ys.max() / h, 3)],
                             "dist_to_target_frac": round(dmin, 3) if dmin is not None else None,
                             "near_target": bool(dmin is not None and dmin <= 0.12)})
    regs.sort(key=lambda r: -r["area_frac_outside"])
    return {"fit_frac": round(float(fit.sum() / max(1, far.sum())), 4), "de_median_outside": round(float(np.median(de[far])), 3),
            "regions": regs[:6], "n_regions": len(regs)}


def audit_edit(R: Report, path: Path, facts, a, ctx):
    from PIL import Image
    info = check_file_basics(R, path, facts, a)
    orig = Path(a.orig) if getattr(a, "orig", None) else None
    if orig is None and facts and (facts.get("meta") or {}).get("source"):
        orig = ROOT / facts["meta"]["source"]
    if orig is None or not orig.exists():
        R.errors.append("режим edit: нужен --orig (исходник правки)")
        return R
    ec = mod("edit_check")
    outd = Path(ctx["out"]) / (path.stem + "_edit")
    outd.mkdir(parents=True, exist_ok=True)
    with Image.open(orig) as io_:
        ro = io_.width / io_.height
    re_ = info["w"] / info["h"]
    if abs(ro / re_ - 1) > 0.01:
        rc, rep = call_json(ec.cmd_outpaint, orig=str(orig), extended=str(path), out=str(outd), composite=True,
                            feather=max(4, int(0.005 * max(info["w"], info["h"]))))
        R.checks["outpaint"] = rep
        R.meta["edit_kind"] = "outpaint"
        if rep.get("verdict") == "REGENERATED":
            R.defect("QA-OUTPAINT-REGEN", "fail", "исходник в расширенном кадре перерисован (SSIM центра, ΔE00, резкость краёв) — "
                     "взять composite.png (исходник вставлен обратно)", metric="outpaint.edge_sharpness",
                     value=rep.get("edge_sharpness"), th_key="edit.outpaint_edge_sharpness_min",
                     evidence={"composite": rel(outd / "composite.png"), "sheet": rel(outd / "sheet.jpg")})
        return R
    mask = getattr(a, "mask", None)
    derived = None
    if not mask:
        m, drep = diff_mask(orig, path, R.th("edit.leak_de", 5.0))
        R.checks["diff_mask"] = drep
        if drep["changed_frac"] < R.th("edit.noedit_changed_min", 0.002):
            R.defect("QA-EDIT-NOEDIT", "fail", "правка почти ничего не изменила (< 0,2 % кадра)", metric="diff_mask.changed_frac",
                     value=drep["changed_frac"], th_key="edit.noedit_changed_min")
            return R
        if drep["changed_frac"] > R.th("edit.maskless_changed_max", 0.5):
            R.defect("QA-EDIT-REDRAW", "warn", f"изменено {drep['changed_frac']:.0%} кадра — перерисовка, а не правка",
                     metric="diff_mask.changed_frac", value=drep["changed_frac"], th_key="edit.maskless_changed_max")
        exp_n = getattr(a, "changes", None)
        if exp_n is not None and drep["regions"] > exp_n + R.th("edit.extra_regions_tolerance", 2):
            R.defect("QA-EDIT-EXTRA-REGIONS", "warn", f"изменённых областей {drep['regions']} при заказанных {exp_n} — утечка?",
                     metric="diff_mask.regions", value=drep["regions"], threshold=exp_n)
        from scipy import ndimage as ndi
        import numpy as np
        side = max(m.shape)
        mm = ndi.binary_dilation(m, iterations=max(2, int(R.th("edit.derived_mask_dilate_frac", 0.02) * side)))
        derived = outd / "diff_mask.png"
        Image.fromarray((mm * 255).astype(np.uint8)).save(derived)
        mask = str(derived)
        R.ask_human("Сравнить карту изменений с заказанными правками (безмасочная правка: цель неизвестна коду)",
                    "маска выведена из разницы — что изменено по заказу, а что утечка, решает глаз", ["QA-EDIT-DIFF"])
    feather = getattr(a, "feather", None)
    if not feather:
        feather = max(4, int(R.th("edit.feather_frac", 0.03) * max(info["w"], info["h"]))) if getattr(a, "removal", False) else 4
    rc, rep = call_json(ec.cmd_check, orig=str(orig), edited=str(path), mask=mask, mask_mode=getattr(a, "mask_mode", "white") if not derived else "white",
                        protect=getattr(a, "protect", None), band=6, thr=R.th("edit.leak_de", 5.0), out=str(outd),
                        composite=True, feather=feather, match_color=True, align="shift", leak_max=R.th("edit.leak_frac_max", 0.02))
    R.checks["edit"] = {k: rep.get(k) for k in ("verdict", "outside_leak_frac", "outside_de_median", "outside_ssim", "target_changed_frac",
                                               "global_drift", "edges_iou", "edges_iou_outside", "protect", "shift_px", "composite_outside_de_max")}
    R.checks["edit"]["mask"] = rel(mask) if derived else mask
    R.checks["edit"]["files"] = {"sheet": rel(outd / "sheet.jpg"), "composite": rel(outd / "composite.png"), "diff_heat": rel(outd / "diff_heat.png")}
    R.meta["edit_kind"] = "maskless" if derived else "mask"
    gd = (rep.get("global_drift") or {}).get("global_de00")
    if gd is not None and gd > R.th("edit.global_drift_max", 2.0):
        R.defect("QA-EDIT-DRIFT", "warn", f"общий сдвиг цвета ΔE00 {gd} > 2 — подогнан (--match-color); отдавать композит",
                 metric="edit.global_drift.global_de00", value=gd, th_key="edit.global_drift_max")
    if not derived:
        ls = local_shift(orig, path, mask, getattr(a, "mask_mode", "white"), 6, R.th("edit.local_shift_de", 3.0),
                         R.th("edit.local_shift_min_frac", 0.005))
        R.checks["edit"]["local_shift"] = ls
        if ls["n_regions"] and rep.get("verdict") != "LEAK":
            r0 = ls["regions"][0]
            R.defect("QA-EDIT-LOCAL-SHIFT", "warn", f"вне цели {ls['n_regions']} обл. сдвинуты на ΔE00 > {R.th('edit.local_shift_de', 3.0)} "
                     f"после робастной подгонки цвета (крупнейшая {r0['area_frac_outside']:.1%} «вне цели», ΔE {r0['de_median']}, "
                     f"{'рядом с целью' if r0['near_target'] else 'вдали от цели'}): утечка слабее порога edit_check или «призрак» "
                     "света и тени изменённого объекта (H 08/02 §2.4 — маска шире); смотреть лист, отдавать композит",
                     metric="edit.local_shift.n_regions",
                     value=ls["n_regions"], th_key="edit.local_shift_de", evidence=ls["regions"][:3])
        if rep.get("verdict") == "LEAK":
            R.defect("QA-EDIT-LEAK", "warn", f"утечка вне цели {rep.get('outside_leak_frac')} > 0,02 — композит исходника по маске "
                     "(composite.png), не перегенерация", metric="edit.outside_leak_frac", value=rep.get("outside_leak_frac"),
                     th_key="edit.leak_frac_max", evidence={"composite": rel(outd / "composite.png")})
        if rep.get("verdict") == "NO_EDIT":
            R.defect("QA-EDIT-NOEDIT", "fail", f"в цели изменено {rep.get('target_changed_frac')} (< 0,2) — правка не выполнена",
                     metric="edit.target_changed_frac", value=rep.get("target_changed_frac"), th_key="edit.target_changed_min")
    if getattr(a, "edit_kind", None) in ("light", "color") and rep.get("edges_iou") is not None and rep["edges_iou"] < R.th("edit.edges_iou_min", 0.9):
        R.defect("QA-EDIT-GEOMETRY", "warn", f"правка света/цвета изменила формы: edges_iou {rep['edges_iou']} < 0,9",
                 metric="edit.edges_iou", value=rep["edges_iou"], th_key="edit.edges_iou_min")
    pr = rep.get("protect")
    if pr and not pr.get("ok"):
        R.defect("QA-PROTECT-CHANGED", "fail", f"защищённый объект изменён: SSIM {pr.get('ssim')}, ΔE00 медиана {pr.get('de_median')} — "
                 "вставить оригинал товара по альфе", metric="edit.protect", value=pr.get("ssim"), th_key="edit.protect_ssim_min",
                 marker="IMG-M24")
    return R


def audit_texture(R: Report, path: Path, facts, a, ctx):
    info = check_file_basics(R, path, facts, a)
    check_budget(R, info, "texture", a, plan=ctx.get("plan"))
    tc = mod("tile_check")
    rh, rv = tc.seam_ratio(tc.load(str(path)))
    mx = max(rh, rv)
    R.checks["tile"] = {"seam_ratio": [rh, rv], "max": mx}
    if mx > R.th("texture.seam_ratio_fail", 1.5):
        R.defect("QA-TILE-SEAM", "fail", f"шов тайла {mx} > 1,5 — tile_check.py cut (органика) или заделка креста маской",
                 metric="tile.max", value=mx, th_key="texture.seam_ratio_fail")
    elif mx > R.th("texture.seam_ratio_max", 1.3):
        R.defect("QA-TILE-SEAM", "warn", f"шов тайла {mx}: пограничный (1,3–1,5) — смотреть превью 2×2", metric="tile.max", value=mx,
                 th_key="texture.seam_ratio_max")
    R.ask_human("Превью тайла 2×2 и сдвиг 50 %: узнаваемое пятно повторяется?", "периодичность повторов метрика шва не ловит (H 08/03 §2.2)")
    return R


def luma_flicker(frames) -> dict:
    """Мерцание яркости (VID-M14): отклонение средней яркости кадра от медианного сглаживания по 11 кадрам, 0–255."""
    import numpy as np
    from scipy.ndimage import median_filter
    L = frames.reshape(len(frames), -1).mean(1)
    if len(L) < 7:
        return {"n": int(len(L))}
    sm = median_filter(L, size=11, mode="nearest")   # окно 11: вспышка на 3–4 кадра не «съедается» медианой
    dev = np.abs(L - sm)
    return {"luma_mean": round(float(L.mean()), 2), "luma_range": round(float(L.max() - L.min()), 3),
            "flicker_max": round(float(dev.max()), 3), "flicker_p95": round(float(np.percentile(dev, 95)), 3)}


def audit_video(R: Report, path: Path, facts, a, ctx, alpha=False, once=False):
    """Видео: петля (шов, живость, концы), ролик с альфой (alpha) или разовый ролик (once — без шва, угасания, длины петли
    и «ползущей камеры»). Числа приёмки — только группы video и video_alpha thresholds.yaml: нет ключа — режим не считается."""
    vl = mod("video_loop_check")
    th = R.th
    lims = {k: th(k) for k in set(th.flat) | set(th.over) if k.startswith(("video.", "video_alpha."))}

    def need(key):
        return vl.lim(lims, key)
    montage, fade_event = bool(getattr(a, "montage", False)), bool(getattr(a, "fade_event", False))
    pr = vl.probe(str(path)) if path.is_file() else {}
    R.checks["probe"] = pr
    R.checks["file"] = {"bytes": path.stat().st_size if path.is_file() else None,
                        "sha256": sha256_file(path) if path.is_file() else None}
    if pr.get("audio"):
        R.defect("QA-VIDEO-AUDIO", "warn", f"звуковая дорожка {pr['audio']} — снять `-an` при кодировании (фон-видео без звука)",
                 metric="probe.audio", value=",".join(pr["audio"]))
    if alpha and pr.get("pix_fmt") and "yuva" in str(pr.get("pix_fmt")):
        R.checks["alpha_video"] = {"pix_fmt": pr["pix_fmt"], "note": "альфа в потоке (VP9-alpha читает libvpx, не встроенный декодер)"}
    if alpha and not ("yuva" in str(pr.get("pix_fmt") or "")):
        _, ch = call_json(vl.cmd_chroma, video=str(path), key=getattr(a, "key", None) or "auto", de=need("video_alpha.key_de"),
                          width=320, thresholds=getattr(a, "thresholds", None))
        R.checks["chroma"] = ch
        if ch.get("bg_ok_min", 1) < need("video_alpha.bg_ok_min"):
            R.defect("QA-CHROMA-BG", "fail", f"фон-ключ неоднороден: доля фона в ΔE00 ≤ {need('video_alpha.key_de')} — "
                     f"{ch.get('bg_ok_min')} (< {need('video_alpha.bg_ok_min')})",
                     metric="chroma.bg_ok_min", value=ch.get("bg_ok_min"), th_key="video_alpha.bg_ok_min")
        if ch.get("obj_drift_max_pct_w", 0) > need("video_alpha.obj_drift_max_pct_w"):
            R.defect("QA-CHROMA-DRIFT", "warn", f"объект уплывает на {ch.get('obj_drift_max_pct_w')} % ширины "
                     f"(> {need('video_alpha.obj_drift_max_pct_w')})",
                     metric="chroma.obj_drift_max_pct_w", value=ch.get("obj_drift_max_pct_w"),
                     th_key="video_alpha.obj_drift_max_pct_w")
    fr = vl.load(str(path), 320)
    rgb = vl.load(str(path), 96, "rgb")
    m = vl.loop_metrics(fr, None, rgb, vl.src_width(str(path)) / 320, th=lims, montage=montage)
    ctrl = getattr(a, "control", None)
    if ctrl:
        c = vl.loop_metrics(vl.load(ctrl, 320), th=lims)
        m["control_motion_med"] = c["motion_med"]
        m["motion_vs_control"] = round(m["motion_med"] / max(c["motion_med"], 1e-6), 2)
    master = getattr(a, "master", None)
    if master and Path(master).suffix.lower() in VID_EXT and Path(master).resolve() != path.resolve():
        # сжатие «замораживает» тихую петлю: motion_keep = motion_med финала / мезонина (J 10-web-integration/02 §6.1)
        mm = vl.loop_metrics(vl.load(str(master), 320), th=lims)
        m["master_motion_med"] = mm["motion_med"]
        m["motion_keep"] = round(m["motion_med"] / max(mm["motion_med"], 1e-6), 2)
    m.pop("_curve", None)
    m["timing"] = vl.frame_timing(str(path))
    m["flash"] = vl.flash_scan(str(path), lims, css_width=getattr(a, "css_width", None))
    lossless = "4:4:4" in str(pr.get("profile") or "") or str(pr.get("pix_fmt") or "").startswith(("yuv444", "rgb", "gbr"))
    lossy_final = (pr.get("codec") in ("h264", "hevc", "vp9", "av1") and not getattr(a, "mezzanine", False) and not lossless
                   and (pr.get("kbps") or 0) < need("video.mezzanine_kbps_min"))
    # стадия файла: файл для страницы или сжатый финал — порог шва после кодирования; мезонин и выход модели — свой
    encoded = (getattr(a, "stage", "master") == "web" or lossy_final) and not getattr(a, "mezzanine", False)
    m["verdict"] = vl.verdict(m, lims, encoded=encoded, montage=montage, once=once, fade_event=fade_event)
    m["flicker"] = luma_flicker(fr)
    R.checks["loop"] = m
    quiet = m["motion_med"] < need("video.quiet_motion_med")
    loop_like = not alpha and not once
    if loop_like:
        sc = vl.seam_check(m, lims, encoded=encoded, montage=montage)
        m["seam_check"] = sc
        seam, seam_key = m["seam_ratio_local"], "video.seam_encoded_max" if encoded else "video.seam_local_max"
        if not sc["ok"]:
            if lossy_final and quiet:
                R.defect("QA-LOOP-SEAM", "needs_human", f"шов {seam} на сжатом файле тихой петли: пульс ключевого кадра даёт ложный шов "
                         "— мерить мезонин или выход модели до перекодирования", metric="loop.seam_ratio_local",
                         value=seam, th_key=seam_key, marker="VID-M12")
            else:
                R.defect("QA-LOOP-SEAM", "fail", f"шов петли {seam} > {need(seam_key)} "
                         f"({'файл после кодирования' if encoded else 'мезонин или выход модели'}, по файлу как есть) — мост "
                         "loop_rife_bridge.py или кроссфейд хвоста (I 09/01 §3)",
                         metric="loop.seam_ratio_local", value=seam, th_key=seam_key, marker="VID-M12")
        if m["trim"]["start"] or m["trim"]["end"]:
            R.defect("QA-LOOP-TRIM", "info", f"срезать кадры: начало {m['trim']['start']}, конец {m['trim']['end']} "
                     f"(дубль последнего — {m['dup_last']}) → video_loop_check.py trim --auto", metric="loop.trim",
                     value=m["trim"]["end"] + m["trim"]["start"])
        if m["pingpong_suspect"] and not montage:
            R.defect("QA-LOOP-PINGPONG", "warn", "похоже на пинг-понг (кадры зеркальны во времени): движение разворачивается",
                     metric="loop.mirror_ratio", value=m["mirror_ratio"], marker="VID-M12")
    if montage:
        m["shots"] = len(m["cuts"]) + 1      # склейки объявлены ключом --montage: находки нет, кадры склеек — в cuts
    elif (m.get("cut_ratio") or 0) >= need("video.cut_ratio_max"):
        R.defect("QA-LOOP-CUT", "fail", f"склейка (локальный пик {m['cut_ratio']} ≥ {need('video.cut_ratio_max')} на кадре "
                 f"{m['cut_at']}) — мульти-шот выключить; ролик из нескольких планов принимается с ключом --montage",
                 metric="loop.cut_ratio", value=m["cut_ratio"], th_key="video.cut_ratio_max", marker="VID-M15")
    elif not once and (m.get("cut_ratio") or 0) >= need("video.event_ratio_warn"):
        R.defect("QA-LOOP-EVENT", "info", f"всплеск движения ×{m['cut_ratio']} на кадре {m['cut_at']}: событие в фоновой петле?",
                 metric="loop.cut_ratio", value=m["cut_ratio"], th_key="video.event_ratio_warn", marker="VID-M18")
    if not once:
        if m["collapse_suspect"]:
            R.defect("QA-LOOP-COLLAPSE", "warn" if fade_event else "fail",
                     f"движение угасает: мёртвых пар у концов — начало {m['dead_start']}, конец {m['dead_end']} "
                     f"(> {need('video.dead_trim_max')})"
                     + (" — объявлено событие-затемнение (--fade-event): посмотреть глазом" if fade_event else
                        " — срезать `video_loop_check.py trim --auto` и проверить заново, иначе перегенерировать; "
                        "событие-затемнение объявляет ключ --fade-event"),
                     metric="loop.dead_end", value=max(m["dead_start"], m["dead_end"]), th_key="video.dead_trim_max")
        elif min(m["head_motion"], m["tail_motion"]) < need("video.head_tail_min"):
            R.defect("QA-LOOP-FADE", "warn", f"движение слабеет к краю: голова {m['head_motion']}, хвост {m['tail_motion']} "
                     f"(< {need('video.head_tail_min')})",
                     metric="loop.tail_motion", value=min(m["head_motion"], m["tail_motion"]), th_key="video.head_tail_min")
        if (m.get("static_frac") or 0) > need("video.static_frac_max"):
            R.defect("QA-LOOP-STATIC", "warn", f"«замёрзших» пар кадров {m['static_frac']} > {need('video.static_frac_max')} "
                     "(заморозки, дубли кадров)",
                     metric="loop.static_frac", value=m["static_frac"], th_key="video.static_frac_max")
    held = (m.get("timing") or {}).get("held_frames") or 0
    if m["dup_frames"] or held:
        R.defect("QA-VIDEO-DUP-FRAMES", "warn", f"повторы кадров — рывок: пар без движения внутри ролика {m['dup_frames']}"
                 + (f" (кадры {', '.join(map(str, m['dup_at']))})" if m["dup_at"] else "")
                 + (f"; по таймкодам кадр держится дольше шага {held} раз (переменная частота)" if held else "")
                 + " — кодировать с постоянной частотой без размножения кадров",
                 metric="loop.dup_frames", value=m["dup_frames"] + held, th_key="video.dead_pair_frac")
    if "motion_vs_control" in m:
        if m["motion_vs_control"] < need("video.motion_vs_control_min"):
            R.defect("QA-LOOP-WEAK-MOTION", "fail", f"движения {m['motion_vs_control']} от i2v-контроля "
                     f"(< {need('video.motion_vs_control_min')}) — статичный коллапс",
                     metric="loop.motion_vs_control", value=m["motion_vs_control"], th_key="video.motion_vs_control_min")
    elif loop_like:
        R.defect("QA-LOOP-NO-CONTROL", "info", "нет i2v-контроля (--control): равномерно слабое движение метрикой не видно (ai-media 09/01)")
    if "motion_keep" in m and m["motion_keep"] < need("video.motion_keep_min"):
        R.defect("QA-ENCODE-MOTION", "warn", f"сжатие съело движение: motion_keep {m['motion_keep']} к мастеру "
                 f"(< {need('video.motion_keep_min')}) — CRF ниже "
                 "(AV1 CRF 36 тихих петель 0,24–0,77; AV1 24–28, H.264 18–20)", metric="loop.motion_keep", value=m["motion_keep"],
                 th_key="video.motion_keep_min")
    if loop_like and not montage and m["cam_shift_max_px"] >= need("video.cam_shift_max_px") and not getattr(a, "camera_move", False):
        R.defect("QA-VIDEO-CAM-CREEP", "warn", f"кадр ползёт на {m['cam_shift_max_px']} px — «ползущая камера» ломает шов",
                 metric="loop.cam_shift_max_px", value=m["cam_shift_max_px"], th_key="video.cam_shift_max_px", marker="VID-M07")
    if not once and not montage:
        for k in ("seam_dE00", "color_drift_dE00"):
            if m.get(k) is not None and m[k] >= need("video.color_de_max"):
                R.defect("QA-LOOP-COLOR", "warn", f"{k} {m[k]} ≥ {need('video.color_de_max')} — цвет плывёт", metric=f"loop.{k}",
                         value=m[k], th_key="video.color_de_max", marker="VID-M14")
    fl = m["flicker"]
    if fl.get("flicker_max") is not None and fl["flicker_max"] > need("video.flicker_max"):
        R.defect("QA-VIDEO-FLICKER", "info", f"яркость кадра «дышит»: отклонение до {fl['flicker_max']} из 255 [не откалибровано]",
                 metric="loop.flicker.flicker_max", value=fl["flicker_max"], th_key="video.flicker_max", marker="VID-M14")
    if m["flash"].get("fail"):
        R.defect("QA-VIDEO-FLASH", "warn", f"вспышки: больше {need('video.flash_per_s_max')} в секунду на "
                 f"{m['flash']['max_area_frac']:.0%} поля 10° (t ≈ {m['flash']['worst_t_s']} с, ширина на странице "
                 f"{m['flash']['css_width']:.0f} CSS px) — WCAG 2.3.1; на странице останавливают ворота эффектов EG-A11Y-04",
                 metric="loop.flash.max_area_frac", value=m["flash"]["max_area_frac"], th_key="video.flash_area_frac_min")
    if getattr(a, "mask", None):
        _, dr = call_json(vl.cmd_drift, video=str(path), mask=a.mask, width=320)
        R.checks["cinemagraph_drift"] = dr
        if dr.get("drift_max", 0) >= need("video.cinemagraph_drift_max") or dr.get("dE00_max", 0) >= need("video.color_de_max") \
                or dr.get("cam_shift_max_px", 0) >= need("video.cam_shift_max_px"):
            R.defect("QA-CINEMAGRAPH-DRIFT", "warn", f"неподвижные зоны плывут: drift {dr.get('drift_max')}, ΔE00 {dr.get('dE00_max')}, "
                     f"камера {dr.get('cam_shift_max_px')} px", metric="cinemagraph_drift.drift_max", value=dr.get("drift_max"),
                     th_key="video.cinemagraph_drift_max")
    dur = pr.get("duration_s") or 0
    if dur and loop_like and not (need("video.loop_len_min_s") <= dur <= need("video.loop_len_max_s")):
        R.defect("QA-LOOP-LENGTH", "info", f"длительность {dur:.1f} с вне {need('video.loop_len_min_s')}–"
                 f"{need('video.loop_len_max_s')} с для фоновой петли", metric="probe.duration_s", value=dur)
    if getattr(a, "stage", "master") == "web" and path.is_file():
        kb = path.stat().st_size / 1024
        plan = ctx.get("plan") or {}
        if plan.get("max_kb") is not None:      # бюджет строки плана ассетов
            key, lim_kb, label = None, plan["max_kb"], f"слота {plan['id']} плана ассетов (вариант {plan['variant']})"
        else:                                   # без плана — умолчание по высоте кадра
            key = "budget.video.hero_1080_kb" if (pr.get("h") or 0) >= 1000 else "budget.video.hero_720_kb"
            lim_kb, label = th(key), "по умолчанию"
        R.checks["budget"] = {"kb": round(kb, 1), "limit_kb": lim_kb, "key": key or f"plan:{plan['id']}/{plan['variant']}"}
        if lim_kb and kb > lim_kb:
            R.defect("QA-BUDGET", "warn", f"{kb:.0f} КБ > бюджета {lim_kb} КБ {label}", metric="file.bytes", value=round(kb),
                     th_key=key, threshold=lim_kb)
    sheet = Path(ctx["out"]) / (path.stem + "_sheet.jpg")
    call_json(vl.cmd_sheet, video=str(path), out=str(sheet), n=12, cols=4)
    R.checks["sheet"] = rel(sheet)
    return R


def svg_colors(txt: str) -> list[str]:
    cols = re.findall(r"(?:fill|stroke|stop-color)\s*[:=]\s*[\"']?\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|white|black)", txt)
    return sorted(set(c.lower() for c in cols))


def audit_svg(R: Report, path: Path, facts, a, ctx):
    info = check_file_basics(R, path, facts, a)
    raw = path.read_bytes()
    si = mod("mp_client").svg_info(raw)
    txt = raw.decode("utf-8", "replace")
    root = re.search(r"<svg\b[^>]*>", txt)
    tag = root.group(0) if root else ""
    si["preserveAspectRatio_none"] = 'preserveAspectRatio="none"' in tag
    si["colors_all"] = svg_colors(txt)
    line_like = bool(re.search(r'stroke-width="', txt)) and ('fill="none"' in tag or "fill=\"none\"" in txt[:400])
    si["style"] = "line" if line_like else "filled"
    R.checks["svg"] = si
    if not si["root_svg"]:
        R.defect("QA-SVG-INVALID", "fail", "нет корня <svg>")
        return R
    if si["has_image"]:
        R.defect("QA-SVG-RASTER", "fail", "внутри SVG растр <image> — это не вектор (перекраска и масштаб не работают)")
    if si["has_text"]:
        R.defect("QA-SVG-TEXT", "warn", "в SVG есть <text> — зависит от шрифтов; перевести в кривые или HTML")
    if si["preserveAspectRatio_none"]:
        R.defect("QA-SVG-ROOT", "warn", 'корень с preserveAspectRatio="none" — искажение при другой пропорции (ai-media 07/02)')
    if not si.get("viewBox"):
        R.defect("QA-SVG-ROOT", "warn", "нет viewBox — не масштабируется")
    first = re.search(r"<svg\b[^>]*>\s*(?:<[^>]+>\s*)?<(rect|path)\b([^>]*)>", txt)
    if first and first.group(1) == "rect" and re.search(r'width="100%"|width="' + re.escape(str(si.get("width") or "")) + '"', first.group(2) or ""):
        R.defect("QA-SVG-BG", "warn", "первым идёт прямоугольник во весь холст — фон: удалить до svgo (ai-media 07/02)")
    if si.get("recraft_signature"):
        R.defect("QA-SVG-SIGNATURE", "info", "подпись провенанса Recraft — не удалять при svgo (конфиг keep-signature, ai-media 07/02)")
    light = any(c in ("#fff", "#ffffff", "white", "#fefefe") for c in si["colors_all"])
    dark = any(c in ("#000", "#000000", "black") or (c.startswith("#") and len(c) in (4, 7) and int(c[1:2], 16) < 4)
               for c in si["colors_all"])
    if si["style"] == "filled" and light and dark:
        R.defect("QA-SVG-PAINTED-HOLES", "warn", "светлые фигуры поверх тёмных — «дырки» нарисованы цветом фона: в тёмной теме "
                 "и с currentColor будет пятно (3 из 5 иконок Recraft, ai-media 07/02) — проверить рендер на тёмном фоне")
    kb = info["bytes"] / 1024
    lim = R.th("svg.icon_kb_max", 10) if ctx["slot"] in ("icon", None) else R.th("svg.illustration_kb_max", 100)
    if kb > lim:
        R.defect("QA-SVG-HEAVY", "warn", f"{kb:.1f} КБ > {lim} КБ — svgo (−57…−65 % у Recraft) или растр AVIF", metric="file.bytes",
                 value=round(kb, 1), threshold=lim)
    if si["style"] == "line":
        etalon = [x for k, v in (("--stroke", getattr(a, "icon_stroke", None)), ("--viewbox", getattr(a, "icon_viewbox", None)),
                                 ("--conventions", getattr(a, "conventions", None))) if v is not None for x in (k, str(v))]
        check_icons(R, path, getattr(a, "icon_set", None), tuple(etalon))
    R.ask_human("Узнаётся ли метафора иконки за 5 секунд без подписи?", "новые метафоры узнаются 2 из 5 (ai-media 07/01); геометрию код "
                "проверяет, смысл — человек или VLM с контролем (G-06)")
    return R


def is_lucide(icon_set: str | None) -> bool:
    """Набор Lucide (lucide, Lucide, lucide-static …): шапка и штрих Lucide для него — правило набора, а не совет."""
    return str(icon_set or ICON_SET).strip().lower().startswith("lucide")


def check_icons(R: Report, path: Path, icon_set: str | None = None, etalon: tuple = ()):
    """check_icons.py (пороги по Lucide 1.47) — в Python окружения скилла; иконка копируется во временную папку. Эталон
    шапки и штрих — ключи etalon (`--stroke`, `--viewbox`, `--conventions`), без них — Lucide 24×24, stroke 2. Уровень
    флага — поле levels ответа: жёсткий цвет — брак у любого набора; шапка и штрих не по эталону — брак только у набора
    Lucide, у другого набора — предупреждение с советом; остальные флаги — предупреждения."""
    with tempfile.TemporaryDirectory() as td:
        shutil.copy(path, Path(td) / path.name)
        out = Path(td) / "r.json"
        r = subprocess.run([kbpaths.python(), str(TOOLS / "check_icons.py"), td, "--ref", str(LUCIDE_REF), "--json", str(out),
                            *(["--set", icon_set] if icon_set else []), *etalon], capture_output=True, text=True, timeout=300)
        if not out.exists():
            line = last_line(r.stderr or r.stdout) or f"код {r.returncode}"
            if r.returncode == 2 and INSTALL in line:   # нет пакетов группы svg — одна строка с командой установки
                R.no_env(line.removeprefix("check_icons.py: "), "check_icons")
            else:
                R.errors.append(f"check_icons: {line}")
            return
        res = json.loads(out.read_text(encoding="utf-8")).get(path.stem, {})
    R.checks["icon"] = res
    icon_set = res.get("set") or icon_set or ICON_SET      # набор без ключа — из карты решений (--conventions) или Lucide
    levels = res.get("levels") or {}
    for f in res.get("flags", []):
        key = f.split()[0]
        code = {"шапка": "QA-SVG-HEADER", "цвет": "QA-SVG-COLOR", "поле<1": "QA-SVG-MARGIN", "зазор": "QA-SVG-GAP",
                "узко": "QA-SVG-NARROW", "вес": "QA-SVG-WEIGHT", "центр": "QA-SVG-CENTER", "сетка": "QA-SVG-GRID"}.get(key, "QA-SVG-FLAG")
        lvl = levels.get(key) or ("fail" if key == "цвет" or (key == "шапка" and is_lucide(icon_set)) else "warn")
        msg = f"check_icons: {f} (пороги по Lucide 1.47, ai-media 07/01)"
        if key == "шапка":
            hr = res.get("header_rules") or {}
            msg = (f"check_icons: шапка не по спецификации Lucide ({', '.join(res.get('header_bad') or [])}; правило — "
                   f"viewBox {hr.get('viewBox', '0 0 24 24')}, {hr.get('width', '24')}×{hr.get('height', '24')}, fill none, "
                   f"stroke currentColor, stroke-width {hr.get('stroke-width', '2')}, round cap/join)")
            if lvl != "fail":
                msg += (f" — у набора «{icon_set}» это предупреждение: сверить шапку и штрих со спецификацией набора, "
                        "иконки под Lucide не подгонять")
        R.defect(code, lvl, msg, metric="icon.flags", value=f, th_key="svg.check_icons_flags")


def audit_og(R: Report, path: Path, facts, a, ctx):
    audit_image(R, path, facts, a, ctx)
    info = R.checks["file"]
    W, H = info["w"], info["h"]
    ok = (W, H) in ((1200, 630), (2400, 1260))
    if not ok:
        R.defect("QA-OG-SIZE", "warn" if abs(W / H - 1.905) < 0.02 else "fail", f"{W}×{H} вместо 1200×630 (1,91:1)",
                 metric="file.w", value=f"{W}x{H}", th_key="og.size")
    if info.get("format") not in ("PNG", "JPEG"):
        R.defect("QA-OG-FORMAT", "warn", f"формат {info.get('format')} — для OG PNG или JPEG (не AVIF)", th_key="og.formats")
    kb = info["bytes"] / 1024
    if kb > R.th("og.kb_max", 300):
        R.defect("QA-OG-WEIGHT", "warn", f"{kb:.0f} КБ > 300 КБ", metric="file.bytes", value=round(kb), th_key="og.kb_max")
    return R


MODES = {"image": audit_image, "cutout": audit_cutout, "edit": audit_edit, "texture": audit_texture,
         "video-loop": lambda R, p, f, a, c: audit_video(R, p, f, a, c, alpha=False),
         "video-alpha": lambda R, p, f, a, c: audit_video(R, p, f, a, c, alpha=True),
         "video-once": lambda R, p, f, a, c: audit_video(R, p, f, a, c, once=True),
         "svg-icon": audit_svg, "og": audit_og}


# ================================================================ текст (OCR) пачкой и «незаказанный текст»


def apply_text(reports: list[Report], ocr_res: dict, a):
    for R in reports:
        o = ocr_res.get(str(R.path.resolve()))
        exp = R.meta.get("_expect")
        if o is None:
            continue
        if "error" in o:
            if o.get("env"):
                R.no_env(o["error"], "OCR")
            else:
                R.errors.append(f"OCR: {o['error']}")
            continue
        lines = o.get("lines", [])
        R.checks["ocr"] = {"lines": [{k: L.get(k) for k in ("text", "score_min", "score_line", "h_px", "box", "text_en")} for L in lines],
                           "lang": o.get("lang"), "elapsed_s": o.get("elapsed_s")}
        if exp:
            tv = text_verdict(exp, "\n".join(L["text"] for L in lines), lines_meta=lines, th=R.th,
                              yo_required=not getattr(a, "yo_optional", False), allowed=getattr(a, "allow_text", None),
                              h_scale=ocr_scale(o))
            R.checks["text"] = {k: tv[k] for k in ("verdict", "fail_classes", "small_text", "classes", "extra_text", "latin_suspect",
                                                   "fake_latin", "precision_words", "recall_lines", "gned", "ocr_score_min",
                                                   "min_line_h_px")}
            R.checks["text"]["lines"] = [{k: L[k] for k in ("expected", "found", "cer", "match", "classes", "occurrence", "small")
                                          if k in L} for L in tv["lines"]]
            if tv["verdict"] == "fail":
                R.defect("QA-TEXT-MISMATCH", "fail", f"текст не совпал с брифом: {', '.join(tv['fail_classes'])}", metric="text.fail_classes",
                         value=",".join(tv["fail_classes"]), th_key="text.fail_min_ocr_score", marker="IMG-M12")
            elif tv["verdict"] == "warn":
                R.defect("QA-TEXT-SMALL", "warn", f"мелкие буквы (строка ниже {R.th('text.fail_min_line_h_px', 16)} px в масштабе "
                         f"распознавания): расхождение распознавания ({', '.join(tv['small_text'])}) — прочитать глазами на 200 %",
                         metric="text.small_text", value=",".join(tv["small_text"]), th_key="text.fail_min_line_h_px",
                         marker="IMG-M12")
            elif tv["verdict"] == "needs_human":
                why = ", ".join(tv["fail_classes"] + (["latin_suspect"] if tv["latin_suspect"] else [])) or "неуверенный OCR"
                R.defect("QA-TEXT-CHECK", "needs_human", f"текст прочитать глазами по буквам на 200 %: {why}", metric="text.fail_classes",
                         value=why, marker="IMG-M12")
        else:
            words = [L for L in lines if sum(ch.isalnum() for ch in L["text"]) >= R.th("text.unrequested_min_chars", 2)
                     and L.get("score_min", 0) >= R.th("text.unrequested_min_score", 0.6)]
            if words:
                R.defect("QA-TEXT-UNREQUESTED", "warn", f"на картинке найден незаказанный текст ({len(words)} строк: "
                         f"{'; '.join(L['text'][:30] for L in words[:3])}) — псевдотекст или вывеска", metric="ocr.lines",
                         value=len(words), th_key="text.unrequested_min_score", marker="IMG-M12")


# ================================================================ маркеры-кластер и человек


HUMAN_DEFAULT = {
    "image": ["5-секундный взгляд в слоте на странице: что заметно сразу (кинематографизация, фильтр, пурпур, клише, центр)",
              "Зум 200 % по сетке 3×3: руки, лица, надписи, мелкие предметы, фон-«каша» (IMG-M01, M11, M12, M15, M17)",
              "Перечислить предметы: каждый работает как в жизни? (функциональные ошибки — 58,7 % трудных ИИ-картинок, Kamali 2025)",
              "Эстетика и «годится как финальный ассет» — решает человек (у Google нет автооценщика эстетики)"],
    "cutout": ["Объект на чёрном, белом и фото-фоне, край на 200 %: ореол, «стриженые» волосы, дыры, мутное стекло"],
    "edit": ["Лист «оригинал | правка | карта | композит»: правка выполнена? остальное не испорчено? (раздельно, GEditBench v2)"],
    "texture": [],
    "video-loop": ["Три повтора подряд на полном размере и на телефоне: пауза, «вспышка» кадра 0, разворот, застывший фон",
                   "Покадрово 0 / 25 / 50 / 75 / 100 %: морфинг, «кипение» фактур, плывущий текст (VID-M01…M03, M11)"],
    "video-once": ["Ролик целиком на полном размере и на телефоне: первый и последний кадр, склейки, вспышки",
                   "Покадрово 0 / 25 / 50 / 75 / 100 %: морфинг, «кипение» фактур, плывущий текст (VID-M01…M03, M11)"],
    "video-alpha": ["Альфа на двух контрастных фонах, край объекта во движении: «кипение», зелёный отсвет на металле"],
    "svg-icon": ["Иконки набора рядом в 24 px и на тёмном фоне: вес линий, узнаваемость, «дырки» цветом фона"],
    "og": ["Превью карточки 600×315 и обрезка 1:1: заголовок читается, ключевое внутри 1100×530"],
}


def finish(R: Report, slot: str | None):
    th = R.th
    n = len(R.markers)
    key_slot = slot in ("hero", "product", "og")
    lim = th("slop.key_slot_markers", 2) if key_slot else th("slop.cluster_markers", 3)
    R.meta["markers_suspected"] = n
    if n >= lim:
        R.defect("QA-SLOP-CLUSTER", "needs_human", f"метрики подозревают {n} маркеров ({', '.join(sorted(R.markers))}) — порог "
                 f"кластера {lim} ({'ключевой слот' if key_slot else 'обычный'}): подтвердить глазом или VLM-рубрикой",
                 value=n, th_key="slop.key_slot_markers" if key_slot else "slop.cluster_markers")
    for item in HUMAN_DEFAULT.get(R.mode, []):
        R.ask_human(item, "ручная приёмка ≈ 2 мин (11-evaluation-qa/03)")


# ================================================================ контактный лист


def contact_panel(R: Report, out_dir: Path) -> str | None:
    """Панель для человека: картинка с зоной текста, центром значимости и рамками OCR + полоса вердикта."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    if R.mode.startswith("video"):
        return R.checks.get("sheet")
    if R.path.suffix.lower() in SVG_EXT:
        return None
    try:
        im = Image.open(R.path)
        if im.mode in ("RGBA", "LA", "P", "PA"):
            im = im.convert("RGBA")
            chk = Image.new("RGBA", im.size, (0, 0, 0, 0))
            d0 = ImageDraw.Draw(chk)
            s = 16
            for y in range(0, im.height, s):
                for x in range(0, im.width, s):
                    d0.rectangle([x, y, x + s - 1, y + s - 1], fill=(200, 200, 200, 255) if (x // s + y // s) % 2 else (240, 240, 240, 255))
            chk.alpha_composite(im)
            im = chk
        im = im.convert("RGB")
        W = 960
        sc = W / im.width
        im = im.resize((W, max(1, round(im.height * sc))), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        tz = R.checks.get("text_zone")
        if tz:
            x0, y0, x1, y1 = tz["rect"]
            d.rectangle([x0 * im.width, y0 * im.height, x1 * im.width - 1, y1 * im.height - 1], outline=(0, 200, 255), width=3)
        comp = R.checks.get("composition")
        if comp:
            cx, cy = comp["centroid_x"] * im.width, comp["centroid_y"] * im.height
            d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], outline=(255, 60, 60), width=3)
        for L in (R.checks.get("ocr") or {}).get("lines", []):
            b = L.get("box")
            if b:
                d.rectangle([b[0] * sc, b[1] * sc, b[2] * sc, b[3] * sc], outline=(255, 210, 0), width=2)
        v = R.verdict()
        col = {"pass": (40, 160, 70), "warn": (220, 160, 0), "needs_human": (40, 110, 220), "fail": (210, 40, 40)}[v]
        bar = Image.new("RGB", (W, 64), col)
        db = ImageDraw.Draw(bar)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
            font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except OSError:
            font = font2 = ImageFont.load_default()
        db.text((10, 6), f"{v.upper()} · {R.mode} · {R.path.name[:60]}", fill=(255, 255, 255), font=font)
        codes = [d_["code"] for d_ in R.defects if d_["level"] != "info"][:8]
        db.text((10, 36), ", ".join(codes) or "дефектов нет", fill=(255, 255, 255), font=font2)
        sheet = Image.new("RGB", (W, im.height + 64), (20, 20, 20))
        sheet.paste(bar, (0, 0))
        sheet.paste(im, (0, 64))
        out = out_dir / (R.path.stem + "_panel.jpg")
        sheet.save(out, quality=85)
        return rel(out)
    except Exception as e:  # noqa: BLE001
        R.errors.append(f"контактный лист: {e}"[:200])
        return None


def index_sheet(reports: list[Report], out: Path, cols: int = 4, cell: int = 320):
    from PIL import Image, ImageDraw, ImageFont
    items = [(R, R.meta.get("panel")) for R in reports if R.meta.get("panel")]
    if not items:
        return None
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 4)), (24, 24, 24))
    for i, (R, p) in enumerate(items):
        try:
            im = Image.open(ROOT / p if not Path(p).is_absolute() else p).convert("RGB")
            im.thumbnail((cell - 8, cell - 8))
            sheet.paste(im, ((i % cols) * cell + 4, (i // cols) * (cell + 4) + 4))
        except Exception:  # noqa: BLE001
            continue
    sheet.save(out, quality=85)
    return rel(out)


# ================================================================ серия


def audit_series(paths: list[Path], th: Th, a, out_dir: Path, dna: dict | None) -> dict:
    sm = mod("series_metrics")
    cells = list(paths)
    grid_note = None
    if getattr(a, "grid", None) and len(paths) == 1:
        r_, c_ = (int(x) for x in a.grid.lower().split("x"))
        sg = mod("split_grid")
        res, gx, gy = sg.split(str(paths[0]), str(out_dir / (paths[0].stem + "_cells")), r_, c_)
        cells = [Path(f) for f, _ in res]
        grid_note = {"grid": a.grid, "cells": [rel(c) for c in cells]}
    refs = [str(Path(x)) for x in (getattr(a, "ref", None) or [])]
    s = sm.series([str(p) for p in cells], refs or None)
    acc = (dna or {}).get("acceptance") or {}
    lim_h = acc.get("series_hue_spread_max_deg", th("series.hue_spread_max_deg", 10))
    lim_p = acc.get("series_pal_dE_mean_max", th("series.pal_de_mean_max", 0.045))
    brk_p = acc.get("series_pal_dE_break", th("series.pal_de_break", 0.06))
    lim_l = acc.get("series_sd_L_max", th("series.sd_L_max", 0.04))
    lim_ph = acc.get("phash_min", th("series.phash_dup_max", 10))
    defects = []

    def d(code, level, msg, metric, value, thr):
        defects.append({"code": code, "level": level, "msg": msg, "metric": metric, "value": value, "threshold": thr})
    if s["hue_spread_deg"] > th("series.hue_break_deg", 25):
        d("QA-SERIES-BREAK", "fail", f"серия распалась по оттенку: {s['hue_spread_deg']}° > 25°", "hue_spread_deg", s["hue_spread_deg"], 25)
    elif s["hue_spread_deg"] > lim_h:
        d("QA-SERIES-HUE", "warn", f"разброс оттенка {s['hue_spread_deg']}° > {lim_h}°", "hue_spread_deg", s["hue_spread_deg"], lim_h)
    if s["pal_dE_mean"] > brk_p:
        d("QA-SERIES-BREAK", "fail", f"ΔE палитр {s['pal_dE_mean']} > {brk_p}", "pal_dE_mean", s["pal_dE_mean"], brk_p)
    elif s["pal_dE_mean"] > lim_p:
        d("QA-SERIES-PALETTE", "warn", f"ΔE палитр {s['pal_dE_mean']} > {lim_p}", "pal_dE_mean", s["pal_dE_mean"], lim_p)
    if s["sd_L"] > lim_l:
        d("QA-SERIES-LIGHTNESS", "warn", f"разброс светлоты {s['sd_L']} > {lim_l}", "sd_L", s["sd_L"], lim_l)
    if s["phash_min"] < lim_ph:
        d("QA-SERIES-DUP", "warn", f"два кадра почти одинаковы (pHash {s['phash_min']} < {lim_ph}) — дубль сюжета", "phash_min",
          s["phash_min"], lim_ph)
    lvl = max([Report.LEVELS[x["level"]] for x in defects] + [0])
    return {"schema": SCHEMA, "kind": "series", "files": [rel(p) for p in cells], "grid": grid_note, "metrics": s,
            "verdict": {0: "pass", 1: "warn", 2: "needs_human", 3: "fail"}[lvl], "defects": defects,
            "human": ["Серия рядом в одном размере, размыть: одинаковы ли пятна по весу; стиль, свет и линия одни? (цвет метрики "
                      "видят, стиль — нет: CSD ρ 0,565 с людьми, F-src-series)"],
            "thresholds_note": "ai-media 06/02: одна съёмка 5,7° / 0,038; четыре локации 104° / 0,091; пороги — фото, для иллюстраций пересчитать"}


# ================================================================ главный проход


def load_json_opt(p):
    if not p:
        return None, None
    pth = Path(p)
    return json.loads(pth.read_text(encoding="utf-8")), pth


def collect_inputs(paths: list[str]) -> list[tuple[Path, dict | None, Path | None]]:
    """Файлы и папки → (файл, паспорт, путь паспорта). Папка: все *.passport.json (их files[]) + медиа без паспорта."""
    out, seen = [], set()
    for p in paths:
        P = Path(p)
        if P.is_dir():
            for pp in sorted(P.rglob("*.passport.json")):
                try:
                    j = json.loads(pp.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                for f in j.get("files") or []:
                    fp = f.get("path") if isinstance(f, dict) else f
                    if not fp:
                        continue
                    cand = [ROOT / fp, pp.parent / Path(fp).name]
                    fpath = next((c for c in cand if c.exists()), None)
                    if fpath and fpath.suffix.lower() in IMG_EXT + VID_EXT + SVG_EXT and fpath.resolve() not in seen:
                        seen.add(fpath.resolve())
                        out.append((fpath, j, pp))
            for f in sorted(P.rglob("*")):
                if f.is_file() and f.suffix.lower() in IMG_EXT + VID_EXT + SVG_EXT and f.resolve() not in seen \
                        and not re.search(r"_(panel|sheet|check)|diff_heat|composite", f.name):
                    seen.add(f.resolve())
                    pj, ppath = find_passport(f)
                    out.append((f, pj, ppath))
        elif P.exists():
            if P.resolve() in seen:
                continue
            seen.add(P.resolve())
            pj, ppath = find_passport(P)
            out.append((P, pj, ppath))
    return out


def audit_paths(a) -> dict:
    th_doc = load_thresholds(Path(a.thresholds) if getattr(a, "thresholds", None) else None)
    dna, dna_path = load_json_opt(getattr(a, "dna", None))
    spec, _ = load_json_opt(getattr(a, "spec", None))
    over = {}
    if dna:
        acc = dna.get("acceptance") or {}
        mapping = {"colorfulness_max_rel": "image.colorfulness_max_rel", "hdr_index_max_delta": "image.hdr_index_max_delta",
                   "zone_edge_max": "text_zone.edge_density_max", "text_contrast_min": "text_zone.contrast_min",
                   "text_zone_percentile": "text_zone.scrim_percentile", "centroid_x_min": "composition.centroid_x_min",
                   "markers_max": "slop.key_slot_markers"}
        for k, v in acc.items():
            if k in mapping:
                over[mapping[k]] = v + 1 if k == "markers_max" else v
    th = Th(th_doc, over)
    slot_arg = getattr(a, "slot", None)
    plan = plan_slot(Path(a.plan), slot_arg, getattr(a, "variant", None), getattr(a, "mobile", False)) \
        if getattr(a, "plan", None) else None
    if slot_arg and plan is None and slot_arg not in SLOT_KINDS:
        raise AuditError(f"--slot {slot_arg}: без --plan это род слота ({', '.join(SLOT_KINDS)}); id слота плана ассетов "
                         "задаётся вместе с --plan")
    slot_kind = plan["kind"] if plan else slot_arg
    out_dir = Path(a.out or (kbpaths.out("ai-media", "audit") / dt.date.today().isoformat()))
    out_dir.mkdir(parents=True, exist_ok=True)
    items = collect_inputs(a.paths)
    ref_metrics = dna_reference_metrics(dna, dna_path)
    reports: list[Report] = []
    need_ocr: list[Report] = []
    for path, pj, ppath in items:
        facts = passport_facts(pj, ppath, path) if pj else None
        mode = a.mode if a.mode != "auto" else infer_mode(path, facts, a)
        R = Report(path, mode, th)
        slot = slot_kind or SLOT_OF_TASK.get((facts or {}).get("task_code") or getattr(a, "task", None) or "")
        if mode == "og":
            slot = "og"
        R.meta.update({"slot": slot, "stage": getattr(a, "stage", "master")})
        if plan:
            R.meta["plan_slot"] = {k: plan[k] for k in ("plan", "id", "variant", "max_kb")}
        if facts:
            R.meta["generation"] = {k: facts.get(k) for k in ("passport", "passport_schema", "channel", "model", "provider_actual",
                                                              "tag", "test", "task_code", "cost_rub", "requested")}
        ctx = {"slot": slot, "dna": dna, "spec": spec, "out": str(out_dir), "ref_metrics": ref_metrics, "plan": plan}
        try:
            MODES[mode](R, path, facts, a, ctx)
        except Exception as e:  # noqa: BLE001
            import traceback
            prog = Path(str(getattr(e, "filename", "") or "")).name if isinstance(e, FileNotFoundError) else ""
            if prog in ("ffmpeg", "ffprobe"):   # нет программы окружения — одна строка с командой установки
                R.no_env(env_hint(f"{prog} не найден", "--ffmpeg"), f"режим {mode}")
            elif prog and str(e.filename).startswith(str(kbpaths.bin_dir())):
                R.no_env(env_hint(f"{prog} не найден", "--bin"), f"режим {mode}")
            else:
                R.errors.append(f"{type(e).__name__}: {e}"[:300])
            if getattr(a, "debug", False):
                traceback.print_exc()
        exp = list(getattr(a, "expect", None) or [])
        if not exp and facts and (facts.get("meta") or {}).get("expect"):
            exp = list(facts["meta"]["expect"])
        if not exp and spec:
            exp = [t for t in ((spec.get("text") or {}).get("lines") or [])] if isinstance(spec.get("text"), dict) else []
        R.meta["_expect"] = exp
        ocr_mode = getattr(a, "ocr", "auto")
        if path.suffix.lower() in IMG_EXT and mode in ("image", "og", "cutout", "edit") and ocr_mode != "off" and \
                (exp or ocr_mode == "on" or mode in ("image", "og")):
            need_ocr.append(R)
        reports.append(R)
    if need_ocr and getattr(a, "ocr", "auto") != "off":
        lang = getattr(a, "lang", None) or "ru"
        res = run_ocr([R.path for R in need_ocr], lang=lang)
        apply_text(need_ocr, {str(Path(o["file"]).resolve()): o for o in res}, a)
    results = []
    for R in reports:
        if getattr(a, "provenance", True) and R.path.suffix.lower() in IMG_EXT + VID_EXT:
            try:
                P = provenance(R.path, out_dir)
                R.checks["provenance"] = P
                for b in P.get("missing") or []:   # метки не прочитаны целиком — сведения, вердикт не меняют
                    what = {"c2patool": "C2PA", "exiftool": "XMP и EXIF"}.get(b, b)
                    R.no_env(env_hint(f"{b} не найден (провенанс: метки {what} не прочитаны)", "--bin"))
                if P.get("visible_suspect"):   # эвристика углов шумная (срабатывает и на фото без метки) → сведения с листом углов
                    sheet = P.get("corners_sheet") or "лист углов"
                    R.defect("QA-PROV-VISIBLE-MARK", "info",
                             f"подозрение на видимую метку в углу ({', '.join(P['visible_suspect'][:4])}) — посмотреть {sheet}; "
                             "метку вендора не вырезать кропом без решения заказчика (12-legal-provenance/04 §5 п. 7)",
                             evidence=P.get("corners_sheet"))
                    R.ask_human(f"Лист углов {sheet}: есть ли видимая метка вендора (водяной знак, логотип, надпись «AI»)?",
                                "эвристика углов даёт ложные срабатывания — решает глаз (12-legal-provenance/04 §5 п. 7)",
                                ["QA-PROV-VISIBLE-MARK"])
                marks = (P.get("summary") or {}).get("marks")
                if R.meta.get("stage") == "web" and R.meta.get("generation") and marks is not None and not marks:
                    # ворота L 04 §5 п. 8: у производной ИИ-ассета для страницы — машиночитаемая метка (C2PA теряется при любом кодировании)
                    R.defect("QA-PROV-NO-MARK", "warn", "в файле для страницы нет машиночитаемой метки ИИ (C2PA / XMP DigitalSourceType / "
                             "AIGC) — `provenance_check.py stamp IN OUT --dst trained|composite` (12-legal-provenance/02 §5, 04 §5 п. 8)"
                             + (f"; метки прочитаны не целиком: нет {', '.join(P['missing'])}" if P.get("missing") else ""))
            except Exception as e:  # noqa: BLE001
                R.checks["provenance"] = {"error": str(e)[:200]}
        finish(R, R.meta.get("slot"))
        R.meta["panel"] = contact_panel(R, out_dir)
        R.meta.pop("_expect", None)
        results.append(R.to_dict())
    series = None
    if getattr(a, "series", False) or a.mode == "series":
        imgs = [R.path for R in reports if R.path.suffix.lower() in IMG_EXT]
        if imgs:
            series = audit_series(imgs, th, a, out_dir, dna)
    env = sorted(set().union(*(R.env for R in reports)))
    summary = {"schema": SCHEMA, "tool": f"asset_audit.py {VERSION}", "checked_at": now_iso(), "out": rel(out_dir),
               "thresholds": {"file": th_doc.get("_path"), "sha": th_doc.get("_sha")}, "n": len(results),
               "verdicts": {v: sum(1 for r in results if r["verdict"] == v) for v in ("pass", "warn", "needs_human", "fail")},
               **({"env": env} if env else {}),
               "assets": results, "series": series, "index_sheet": index_sheet(reports, out_dir / "index_sheet.jpg")}
    (out_dir / "audit.json").write_text(jdump(summary), encoding="utf-8")
    (out_dir / "audit.md").write_text(audit_md(summary), encoding="utf-8")
    return summary


def audit_md(s: dict) -> str:
    L = [f"# Приёмка ассетов — {s['checked_at']}", "", f"Пороги: `{s['thresholds']['file']}` ({s['thresholds']['sha']}); итог: "
         + ", ".join(f"{k} {v}" for k, v in s["verdicts"].items()), ""]
    if s.get("env"):
        L += ["Окружение неполное — проверки без него не запущены или сведения неполны:"] + [f"- {h}" for h in s["env"]] + [""]
    L += ["| Файл | Режим | Вердикт | Дефекты (не info) | Человеку |", "|---|---|---|---|---|"]
    for r in s["assets"]:
        codes = ", ".join(sorted({d["code"] for d in r["defects"] if d["level"] != "info"})) or "—"
        L.append(f"| `{Path(r['file']).name}` | {r['mode']} | **{r['verdict']}** | {codes} | {len(r['human'])} |")
    if s.get("series"):
        ss = s["series"]
        L += ["", f"Серия ({len(ss['files'])} кадров): **{ss['verdict']}** — оттенок {ss['metrics']['hue_spread_deg']}°, ΔE палитр "
              f"{ss['metrics']['pal_dE_mean']}, pHash min {ss['metrics']['phash_min']}"]
    L += ["", "Коды и пороги — `11-evaluation-qa/01-metrics-and-asset-audit.md`; ручная приёмка — `03-checklists-by-asset.md`."]
    return "\n".join(L) + "\n"


# ================================================================ пороги: печать и проверка

TH_KEYS_USED = [
    "image.ratio_tolerance", "image.hero_master_min_px", "image.colorfulness_q3", "image.sat_share_q3", "image.hdr_index_q3",
    "image.clip_hi_q3", "image.colorfulness_max_rel", "image.hdr_index_max_delta", "image.filter_colorfulness_rel",
    "image.warm_b_max", "image.purple_share_max", "image.soft_probe_scale", "composition.center_offset_min", "composition.centroid_x_min",
    "composition.blobs_max", "text_zone.edge_density_max", "text_zone.scrim_percentile", "text_zone.contrast_min",
    "text_zone.scrim_alpha_warn", "palette.de_ok", "palette.min_matched", "cutout.transparent_frac_min", "cutout.halo_px_max",
    "cutout.margin_min_frac", "cutout.glass_partial_min", "cutout.fiber_partial_min", "cutout.iou_min_solid",
    "cutout.iou_min_fibers", "cutout.band_mae_x1000_max", "edit.leak_frac_max", "edit.leak_de", "edit.global_drift_max",
    "edit.target_changed_min", "edit.edges_iou_min", "edit.protect_ssim_min", "edit.outpaint_edge_sharpness_min",
    "edit.noedit_changed_min", "edit.maskless_changed_max", "edit.extra_regions_tolerance", "edit.derived_mask_dilate_frac",
    "edit.feather_frac", "edit.local_shift_de", "edit.local_shift_min_frac", "texture.seam_ratio_max", "texture.seam_ratio_fail", "video.seam_local_max", "video.cut_ratio_max",
    "video.seam_encoded_max", "video.dead_pair_frac", "video.dead_trim_max", "video.pingpong_mirror_max",
    "video.flash_luma_delta_min", "video.flash_dark_max", "video.flash_per_s_max", "video.flash_area_frac_min",
    "video.flash_field_css_px", "video.event_ratio_warn", "video.head_tail_min", "video.static_frac_max", "video.motion_vs_control_min",
    "video.cam_shift_max_px", "video.color_de_max", "video.flicker_max", "video.cinemagraph_drift_max", "video.quiet_motion_med",
    "video.mezzanine_kbps_min", "video.loop_len_min_s", "video.loop_len_max_s", "video.motion_keep_min", "video_alpha.bg_ok_min", "video_alpha.key_de",
    "video_alpha.obj_drift_max_pct_w", "series.hue_spread_max_deg", "series.hue_break_deg", "series.pal_de_mean_max",
    "series.pal_de_break", "series.sd_L_max", "series.phash_dup_max", "text.fail_min_ocr_score", "text.fail_min_line_h_px",
    "text.unrequested_min_chars", "text.unrequested_min_score", "slop.cluster_markers", "slop.key_slot_markers",
    "svg.icon_kb_max", "svg.illustration_kb_max", "svg.check_icons_flags", "og.size", "og.formats", "og.kb_max",
    "encoding.ssimulacra2_hero_min", "encoding.ssimulacra2_min", "budget.image.hero_kb", "budget.image.hero_mobile_kb",
    "budget.image.section_kb", "budget.image.og_kb", "budget.image.texture_kb", "budget.image.product_kb",
    "budget.video.hero_1080_kb", "budget.video.hero_720_kb",
    "judge.trust_agreement_min", "judge.prefilter_agreement_min", "judge.min_pairs", "judge.wilson_low_min", "judge.f1_min",
    "judge.swap_consistency_min", "judge.position_bias_max", "judge.unsure_share_max", "judge.disagree_sessions"]


def cmd_thresholds(a):
    doc = load_thresholds(Path(a.thresholds) if a.thresholds else None)
    th = Th(doc)
    rows, missing, nosrc = [], [], []
    for k in TH_KEYS_USED:
        if k not in th.flat:
            missing.append(k)
            continue
        s = th.src(k)
        if not s:
            nosrc.append(k)
        rows.append((k, th.flat[k], s))
    if a.check:
        ok = not missing and not nosrc
        print(jdump({"ok": ok, "keys_used": len(TH_KEYS_USED), "in_yaml": len(th.flat), "missing": missing, "no_source": nosrc,
                     "file": doc.get("_path"), "sha": doc.get("_sha")}))
        return 0 if ok else 1
    for k, v, s in rows:
        print(f"{k:42s} {str(v):>14s}  ← {s}")
    return 0


# ================================================================ судья: пакет для сессии Opus, разбор ответов, согласие с голосами

JUDGE_SCHEMA = RUBRICS / "judge-response.schema.json"
JUDGE_AGENT = kbpaths.repo(".claude", "agents", "design-judge.md")
JUDGE_PROTOCOL = ".claude/skills/design-deep-dive/kb/common/judge.md"
CALIBRATION = kbpaths.assets("calibration", "index.yaml")
PACKAGE_SCHEMA = "judge-package/1"
KEY_SCHEMA = "judge-key/1"
ANSWER_DEF = {"checklist": "checklist_answer", "defects": "defects_answer", "pairwise": "pairwise_answer"}
CALL_KIND = {"checklist": "рубрика", "defects": "рубрика", "pairwise": "попарно"}
WINNERS = ("A", "B", "tie", "both_bad")
FINDING_MIN_RUNS = 2        # judge.md §5: находку засчитывают, если она есть хотя бы в двух прогонах
SIZE_RATIO_TOL = 0.02       # кадры пары с пропорцией в пределах 2 % приводятся к меньшему размеру (judge.md §2)
CAL_TASK = {"creative": "кадр маркетинговой страницы сайта", "ui": "экран веб-приложения",
            "ai-media": "картинка для слота страницы сайта", "3d": "3D-кадр предмета для сайта"}
CAL_SYSTEM = ("Сравни два варианта по одному критерию рубрики. Суди только то, что видно на кадрах. Мера — задача и "
              "критерий, а не насыщенность: добавленное без просьбы — дефект того же веса, что пропущенное; не предпочитай "
              "вариант за то, что он богаче, темнее, цветнее, детальнее или эффектнее; где один вариант богаче, назови "
              "критерий, которому служит богатство, иначе — ничья.")
ROW_SYSTEM = ("Оцени кадр по вопросам рубрики владельца. Суди только то, что видно на кадре, и не додумывай соответствие "
              "задаче. Мера — задача и слот, а не насыщенность: добавленное без просьбы — дефект того же веса, что "
              "пропущенное; не засчитывай вариант за то, что он богаче, темнее, цветнее, детальнее или эффектнее.")
ROW_INTRO = {"checklist": ("На каждый вопрос ответь yes, no, unsure или not_applicable; у каждого no — доказательство: что "
                           "видно и где на кадре. Вопросы:"),
             "defects": ("Проверь кадр на каждый признак. present — yes, no или unsure; yes — только с местом (`where`) и "
                         "тем, что там видно (`evidence`). Признаки:")}
CAL_INTRO = ("Кадры A и B — два варианта одного места. Задача: {brief}. На каждый вопрос выбери A, B, tie (равны) или "
             "both_bad (оба не годятся) и дай короткую причину (`why`) и место на кадре (`where`). Суди только видимое; "
             "разницу веса файла и артефакты сжатия не учитывай. Вопросы:")
RULES = {
    "checklist": ["- На каждый вопрос — один ответ: `yes`, `no`, `unsure` или `not_applicable`. `no` — только с `evidence` "
                  "(что видно и где); без него ответ читается как `unsure`. Мелко или не видно — `unsure`.",
                  "- Находки вне вопросов — массив `findings`: что, где, правило (код рубрики), доказательство, наименьшая "
                  "правка; не больше двенадцати.",
                  "- Балл, серьёзность и решение — не твои: балл считает код, решает человек."],
    "defects": ["- На каждый код — один элемент `defects`: `present` — `yes`, `no` или `unsure`; `yes` — только с `where` и "
                "`evidence`, без места ответ читается как `unsure`. Серьёзность не ставишь.",
                "- Находки вне перечня — массив `findings`: что, где, правило (код рубрики), доказательство, наименьшая "
                "правка; не больше двенадцати.",
                "- Решение — не твоё: находку проверяет человек."],
    "pairwise": ["- На каждый вопрос — один ответ: `A`, `B`, `tie` или `both_bad`, с `why` (видимое различие) и `where`; "
                 "без причины выбор читается как ничья.",
                 "- Второй порядок пары и повторы — другие вызовы: ты их не видишь и не имитируешь.",
                 "- Коды рубрики, решившие выбор, — в `defect_codes` (можно пусто)."]}
PACKAGE_README = """# Пакет судьи · {name}

Задания для отдельных сессий судьи — агента `design-judge` (протокол `kb/common/judge.md`). Ключ слепоты лежит рядом с
папкой пакета, вне её: судья его не видит, задание его не называет.

{what}

1. Каждое задание `jobs/<id>.md` — отдельный вызов инструмента `Agent` с `subagent_type: design-judge`; текст задания —
   промт вызова целиком. Модель в вызове не передают — её задаёт описание агента.
2. Ответ агента целиком — в `answers/<id>.md` (тот же id).
3. Порядок пары и повторы — разные задания: их не объединяют в один вызов и не показывают агенту прошлые ответы.
4. Ответы собраны — `asset_audit.py judge-parse <папка пакета>`: пара — совпадение обоих порядков и большинство прогонов,
   находка — не меньше чем в двух прогонах (протокол §5); сводка ложится рядом с ключом.
"""


class JudgeError(Exception):
    """Ошибка входа судьи (рубрика, файл, порог, пакет) — код выхода 2."""


def load_rubric(name: str) -> dict:
    p = RUBRICS / f"{name}.rubric.json"
    if not p.exists():
        raise JudgeError(f"нет рубрики {rel(p)}")
    return json.loads(p.read_text(encoding="utf-8"))


def rubric_meta(name: str, rubric: dict) -> dict:
    p = RUBRICS / f"{name}.rubric.json"
    return {"id": rubric.get("rubric") or name, "title": rubric.get("title"), "version": rubric.get("version"),
            "sha256": sha256_file(p)[:16], "file": rel(p)}


def image_key(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16] if Path(path).exists() else hashlib.sha256(str(path).encode()).hexdigest()[:16]


def judge_model() -> str | None:
    """Модель судьи — из описания агента design-judge (frontmatter `model:`): запись прогона, а не выбор кода."""
    try:
        txt = JUDGE_AGENT.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.match(r"---\n(.*?)\n---", txt, re.S)
    mm = re.search(r"^model:\s*(\S+)", m.group(1), re.M) if m else None
    return mm.group(1).strip("'\"") if mm else None


def th_need(th: Th, key: str):
    """Порог группы judge из thresholds.yaml; числа доверия живут только там — нет ключа, нет расчёта."""
    v = th(key)
    if v is None:
        raise JudgeError(f"нет порога {key} в {th.doc.get('_path')} (группа judge)")
    return v


# ---------------------------------------------------------------- кадры пакета


def _item_path(p, base: Path | None) -> Path:
    P = Path(p).expanduser()
    if P.is_absolute():
        return P
    for b in ((base,) if base else ()) + (Path.cwd(),):
        if (b / P).exists():
            return (b / P).resolve()
    return (base or Path.cwd()) / P


def _open_frame(src: Path):
    from PIL import Image
    with Image.open(src) as im:
        im.load()
        alpha = im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info)
        return im.convert("RGBA" if alpha else "RGB")


def equalize(ima, imb) -> tuple:
    """Кадры пары — одного размера (judge.md §2): при пропорции в пределах SIZE_RATIO_TOL больший уменьшается до меньшего;
    иначе пара остаётся как есть с предупреждением. → (A, B, какой уменьшен | None, предупреждение | None)."""
    if ima.size == imb.size:
        return ima, imb, None, None
    ra, rb = ima.width / ima.height, imb.width / imb.height
    if abs(ra / rb - 1) > SIZE_RATIO_TOL:
        return ima, imb, None, f"кадры пары разной пропорции: {ima.width}×{ima.height} и {imb.width}×{imb.height}"
    from PIL import Image
    if ima.width * ima.height > imb.width * imb.height:
        return ima.resize(imb.size, Image.LANCZOS), imb, "a", None
    return ima, imb.resize(ima.size, Image.LANCZOS), "b", None


class FrameStore:
    """Кадры пакета под нейтральными именами (sha256 содержимого). По умолчанию — PNG без потерь и без метаданных
    (judge.md §2); same_encoding — кодирование страницы голосования stand_run (JPEG q90 ≤ 1600 px, PNG при альфе); файлы
    страницы голосования — байт в байт: судья видит то же, что заказчик. Исходники — только в ключ."""

    def __init__(self, pkg: Path, same_encoding: bool = False):
        self.pkg = pkg
        self.dir = pkg / "frames"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.same = same_encoding
        self.source: dict = {}

    def put_bytes(self, data: bytes, ext: str, source: str) -> dict:
        from PIL import Image
        name = f"{hashlib.sha256(data).hexdigest()[:16]}.{ext}"
        (self.dir / name).write_bytes(data)
        with Image.open(io.BytesIO(data)) as im:
            info = {"frame": f"frames/{name}", "w": im.width, "h": im.height, "format": im.format}
        self.source.setdefault(info["frame"], source)
        return info

    def put_image(self, im, source: str) -> dict:
        if self.same:
            data, ext = mod("stand_run")._encode(im.convert("RGBA"))
        else:
            buf = io.BytesIO()
            im.save(buf, "PNG", optimize=True)
            data, ext = buf.getvalue(), "png"
        return self.put_bytes(data, ext, source)

    def put_raw(self, path: Path) -> dict:
        data = Path(path).read_bytes()
        return self.put_bytes(data, Path(path).suffix.lstrip(".").lower() or "bin", str(path))


# ---------------------------------------------------------------- задания


def answer_example(mode: str, questions: list[dict]) -> dict:
    if mode == "checklist":
        return {"answers": [{"id": (questions[0].get("id") if questions else "q1"), "answer": "no", "evidence": "что видно и где"}],
                "findings": []}
    if mode == "defects":
        return {"defects": [{"code": (questions[0].get("code") if questions else "IMG-M03"), "present": "yes",
                             "where": "место в кадре", "evidence": "что там видно", "fix": "наименьшая правка"}], "findings": []}
    return {"answers": [{"id": (questions[0].get("id") if questions else "slot"), "winner": "A", "why": "видимое различие",
                         "where": "место на кадре"}], "defect_codes": []}


def job_prompt(pkg: Path, mode: str, title: str, frames: list[tuple[str, dict]], questions: list[dict], system: str,
               intro: str, brief: str | None, report: str | None = None) -> str:
    """Текст задания одной сессии судьи: задача, кадры, машинный отчёт (не в попарном), рубрика, формат ответа."""
    kind = CALL_KIND[mode]
    qkey = "code" if mode == "defects" else "id"
    L = [f"# Задание судьи · {kind} · {title}", "",
         f"Ты — агент `design-judge`; протокол — `{JUDGE_PROTOCOL}` (путь от корня репозитория), §1–§5. Открывай только "
         "файлы, названные в этом задании.", "", "## Задача", "", (brief or "").strip() or "Строки задачи нет — суди по рубрике.",
         "", "## Кадры", ""]
    for lab, fr in frames:
        L.append(f"- {lab + ': ' if lab else ''}`{pkg / fr['frame']}` — {fr['w']}×{fr['h']}, {fr['format']}")
    if report and mode != "pairwise":
        L += ["", "## Машинный отчёт — прочитай первым", "", report.strip()]
    L += ["", "## Рубрика", "", system.strip(), "", intro.replace("{brief}", (brief or "").strip() or "—").strip()]
    L += [f"{q.get(qkey)}: {q['q']}" for q in questions]
    L += ["", "## Ответ", "", f"Первая строка — «{kind} · что судил · входы, чего не хватило». Затем один блок ```json по "
          f"схеме `{pkg / 'response.schema.json'}`, раздел `$defs/{ANSWER_DEF[mode]}`:", "", "```json",
          json.dumps(answer_example(mode, questions), ensure_ascii=False), "```", "", *RULES[mode]]
    return "\n".join(L) + "\n"


def _rows_jsonl(path: Path) -> list[dict]:
    base = path.parent
    rows = []
    for x in path.read_text(encoding="utf-8").splitlines():
        if x.strip() and not x.lstrip().startswith("#"):
            r = json.loads(x)
            r["_base"] = str(base)
            rows.append(r)
    return rows


def stand_page_items(page_dir: Path) -> list[dict]:
    """Пары страницы слепого голосования stand_run.py (DIR/index.html + DIR.key.json) → пары судьи с теми же id и теми же
    файлами, что видел заказчик (DIR/img/*); исходники — orig_a/orig_b для сверки с голосами. Без контрольных, повторов и
    «одинаковых»; у серии (несколько файлов на сторону) судье идёт первый."""
    page_dir = Path(page_dir).resolve()
    html_ = (page_dir / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', html_, re.S)
    data = json.loads(m.group(1).replace("<\\/", "</")) if m else {"pairs": []}
    if data.get("kind") == "text":
        raise JudgeError("страница текстовых карточек: пакет судьи — для кадров; тексты судят по рубрике text "
                         "(copy-rubric.yaml) после голоса заказчика")
    K = json.loads(Path(str(page_dir) + ".key.json").read_text(encoding="utf-8"))
    out = []
    for p in data.get("pairs", []):
        kp = K["pairs"].get(p["id"])
        if not kp or kp.get("gold") or kp.get("identical") or kp.get("repeat_of") or not p["A"] or not p["B"]:
            continue
        out.append({"pair": p["id"], "a": str(page_dir / p["A"][0]), "b": str(page_dir / p["B"][0]),
                    "orig_a": str(kp["A"]["files"][0]), "orig_b": str(kp["B"]["files"][0]), "brief": p.get("brief") or "",
                    "raw": True, "test": kp.get("test"), "group": kp.get("group")})
    return out


# ---------------------------------------------------------------- калибровочный набор


ADDR_RX = re.compile(r"^(kb/\S+?\.(?:md|json|ya?ml))\b\s*(.*)$")
RUBRIC_LIKE = re.compile(r"rubric|/11-evaluation-qa/|/13-evaluation-checklists/|/09-ai-(?:execution|generation)-evaluation/")
LEAKY_HEADING = re.compile(r"^(эксперимент|опыт|калибровк|пример|итоги)", re.I)


def _addr_file(addr: str) -> str:
    m = ADDR_RX.match(addr.strip())
    return m.group(1) if m else addr.strip()


def rubric_address(frames: list[dict]) -> str:
    """Пункт рубрики пары из поля rubric кадров: сначала адрес рубрики (рубрика, чек-лист, оценка базы), общий для кадров
    пары, затем адрес рубрики любого кадра по порядку, затем общий адрес, затем первый."""
    lists = [list(f.get("rubric") or []) for f in frames]
    common = [x for x in lists[0] if all(_addr_file(x) in {_addr_file(y) for y in L} for L in lists[1:])]
    pools = [[x for x in common if RUBRIC_LIKE.search(_addr_file(x))]]
    pools += [[x for x in L if RUBRIC_LIKE.search(_addr_file(x))] for L in lists] + [common, lists[0]]
    return next((pool[0] for pool in pools if pool), "")


def _md_section(path: Path, sec: str) -> tuple[str | None, list[str]]:
    """Заголовок раздела md с номером sec и строки его тела до следующего заголовка того же или старшего уровня."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(\d+(?:\.\d+)*)\.?\s+(.+?)\s*$", line)
        if m and m.group(2) == sec:
            body = []
            for x in lines[i + 1:]:
                h = re.match(r"^(#{1,6})\s", x)
                if h and len(h.group(1)) <= len(m.group(1)):
                    break
                body.append(x)
            return m.group(3), body
    return None, []


def _twin_rubric(path: Path) -> dict | None:
    """JSON-рубрика владельца, чей `doc` — этот md (creative effectiveness.rubric.json ↔ 04-effectiveness-rubric.md)."""
    for p in sorted(path.parent.glob("*rubric*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and str(d.get("doc") or "").endswith(f"{path.parent.name}/{path.name}"):
            return d
    return None


def _stem_in(label: str, text: str) -> bool:
    words = [w[:5] for w in re.findall(r"[\wё-]{5,}", label.lower())]
    return bool(words) and all(w in text.lower() for w in words)


def criterion_of(addr: str) -> dict:
    """Вопросы пары калибровки из адреса рубрики — формулировки владельцев без тел разделов: в разделах баз стоят якоря и
    разборы тех же кадров, а судья идёт вслепую (judge.md §6). Рубрика ai-media — её вопросы по id (g1 …) или попарные
    вопросы и её промт; md с JSON-рубрикой-близнецом — попарный вопрос критерия по заголовку раздела; таблица вопросов
    раздела («…» во второй колонке); строка ворот YAML — её имя; иначе — заголовок раздела или пометка в скобках. Адрес —
    только в ключ."""
    m = ADDR_RX.match(addr.strip())
    path, rest = (m.group(1), m.group(2)) if m else ("", addr)
    P = kbpaths.skill(path) if path else None
    base = {"system": CAL_SYSTEM, "intro": CAL_INTRO, "rubric": None, "version": None}
    if P is not None and P.name.endswith(".rubric.json") and P.exists():
        rub = json.loads(P.read_text(encoding="utf-8"))
        v = rub.get("vlm") or {}
        ids = set(re.findall(r"\bg\d+\b", rest))
        qs = [{"id": q["id"], "q": f"Which image better satisfies: {q['q']}"} for q in v.get("checklist_generic", []) if q.get("id") in ids]
        return {"questions": qs or list(v.get("pairwise_questions") or []), "system": rub["judge"]["system"],
                "intro": rub["judge"]["pairwise_intro"], "rubric": rub.get("rubric"), "version": rub.get("version")}
    text = None
    label = re.search(r"§\s*[\d.]+\s*(?:[A-ZА-Я]\d+\s*)?\(([^)]{3,})\)", rest)
    label = label.group(1) if label and not LEAKY_HEADING.match(label.group(1)) else None
    if P is not None and P.suffix in (".yaml", ".yml") and P.exists():
        import yaml
        want = set(re.findall(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b", rest))

        def walk(node):
            if isinstance(node, dict):
                if node.get("id") in want and node.get("name"):
                    return str(node["name"])
                node = list(node.values())
            if isinstance(node, list):
                for x in node:
                    r = walk(x)
                    if r:
                        return r
            return None
        name = walk(yaml.safe_load(P.read_text(encoding="utf-8")))
        text = re.split(r"\s+—\s+|\s+\(", name, maxsplit=1)[0] if name else None
    elif P is not None and P.suffix == ".md" and P.exists():
        twin = _twin_rubric(P)
        for sec in re.findall(r"§\s*(\d+(?:\.\d+)*)", rest):
            head, body = _md_section(P, sec)
            if not head or LEAKY_HEADING.match(head):
                continue
            if twin:
                first = re.split(r"[\s—:.,]+", head.strip().lower(), maxsplit=1)[0]
                for c in twin.get("criteria") or []:
                    if first and first in (str(c.get("id")).lower(), str(c.get("name_en") or "").lower()) and c.get("pairwise_q"):
                        qs = [{"id": c["id"], "q": c["pairwise_q"]}]
                        qs += [{"id": f"{c['id']}.{k}", "q": sub["pairwise_q"]} for k, sub in (c.get("sub") or {}).items()
                               if isinstance(sub, dict) and sub.get("pairwise_q")]
                        return {**base, "questions": qs, "rubric": twin.get("rubric"), "version": twin.get("version")}
            table = [re.match(r"^\|\s*([a-z][a-z0-9_.-]*)\s*\|\s*«([^»]+)»", x) for x in body]
            qs = [{"id": t.group(1), "q": t.group(2)} for t in table if t]
            if qs:
                return {**base, "questions": qs}
            text = head if not label or _stem_in(label, head) else f"{head}: {label}"
            break
    if not text:
        par = re.search(r"\(([^)]{3,})\)", rest)
        text = label or (par.group(1) if par and not LEAKY_HEADING.match(par.group(1)) else None)
    q = f"Какой вариант лучше по критерию «{text}»?" if text else "Какой вариант лучше для своего места на сайте?"
    return {**base, "questions": [{"id": "c1", "q": q}]}


def _strength(frame: dict) -> str:
    s = str(frame.get("assessment") or "")
    m = re.match(r"\s*сила:\s*([^.]+)", s)
    return m.group(1).strip() if m else ""


def calibration_pairs(select: list[str] | None) -> list[dict]:
    """Пары калибровочного набора (assets/calibration/index.yaml, поле pair; у тройки — все пары тройки) с вопросами из
    поля rubric. Пары, где сила оценки брака — только мнение, в проверку не входят (judge.md §6) и берутся лишь по
    --pairs. Разметка кадров (что иллюстрирует, сила, на что смотреть) — только в ключ."""
    import itertools
    import yaml
    doc = yaml.safe_load(CALIBRATION.read_text(encoding="utf-8"))
    groups: dict = {}
    for f in doc.get("frames") or []:
        if f.get("pair"):
            groups.setdefault(str(f["pair"]), []).append(f)
    if select:
        bad = [g for g in select if g not in groups]
        if bad:
            raise JudgeError(f"нет пар {', '.join(bad)} в {rel(CALIBRATION)}; есть: {', '.join(sorted(groups))}")
    out = []
    for g, frames in groups.items():
        if select and g not in select:
            continue
        for x, y in itertools.combinations(frames, 2):
            pid = g if len(frames) == 2 else f"{g}:{x['id']}-{y['id']}"
            addr = rubric_address([x, y])
            kinds = {x["id"]: x.get("kind"), y["id"]: y.get("kind")}
            levels = [i for i, k in kinds.items() if k == "level"]
            strengths = {x["id"]: _strength(x), y["id"]: _strength(y)}
            basis = [strengths[i] for i, k in kinds.items() if k == "defect"] or list(strengths.values())
            opinion = all(b.startswith("мнение") for b in basis)
            if opinion and not select:
                continue
            out.append({"pid": pid, "group": g, "frames": (x, y), "addr": addr, "criterion": criterion_of(addr),
                        "brief": CAL_TASK.get(str(x.get("base")), "кадр для сайта"),
                        "expect": levels[0] if len(levels) == 1 else None, "opinion_only": opinion,
                        "kinds": kinds, "strength": strengths})
    return out


# ---------------------------------------------------------------- judge-jobs


def cmd_judge_jobs(a):
    """Пакет заданий судьи для отдельных сессий Opus (агент design-judge) и ключ слепоты вне пакета."""
    runs = int(a.runs)
    if runs < 1:
        raise JudgeError("--runs — не меньше 1 (три — находки и второе мнение, пять — сортировка, один — черновик)")
    sources = sum(bool(x) for x in (a.items, a.from_stand_page, a.calibration))
    if sources != 1:
        raise JudgeError("нужен ровно один вход: --items, --from-stand-page или --calibration")
    mode = "pairwise" if (a.from_stand_page or a.calibration) else a.mode
    rubric = load_rubric(a.rubric) if a.rubric and not a.calibration else None
    qfile = json.loads(Path(a.questions).read_text(encoding="utf-8")) if a.questions else {}
    if a.calibration:
        cal = calibration_pairs([x.strip() for x in a.pairs.split(",") if x.strip()] if a.pairs else None)
        rows = [{"pair": c["pid"], "_cal": c} for c in cal]
        label = "calibration"
    elif a.from_stand_page:
        rows = stand_page_items(Path(a.from_stand_page))
        label = f"{a.rubric}-stand"
    else:
        rows = _rows_jsonl(Path(a.items))
        label = f"{a.rubric}-{mode}"
    if not rows:
        raise JudgeError("входов нет: пустой список пар или картинок")
    if rubric is None and not a.calibration and not all(r.get("questions") for r in rows):
        raise JudgeError("нужна --rubric (рубрика ai-media 11-evaluation-qa/rubrics/<имя>.rubric.json) или вопросы "
                         "в каждой строке входа (questions: [{id, q}], у defects — [{code, q}])")
    digest = hashlib.sha256(json.dumps([{k: v for k, v in r.items() if k not in ("_cal", "_base")} for r in rows]
                                       + [mode, runs, a.rubric, bool(a.same_encoding)], sort_keys=True,
                                       ensure_ascii=False, default=str).encode()).hexdigest()
    name = a.name or f"{label}-{digest[:8]}"
    out_root = Path(a.out).resolve() if a.out else kbpaths.out("ai-media", "judge")
    pkg = out_root / name
    key_path = out_root / f"{name}.key.json"
    if pkg.exists():
        if any((pkg / "answers").glob("*")) and not a.force:
            raise JudgeError(f"в пакете {pkg} уже есть ответы — другое имя (--name) или --force")
        shutil.rmtree(pkg)
    (pkg / "jobs").mkdir(parents=True)
    (pkg / "answers").mkdir()
    store = FrameStore(pkg, same_encoding=bool(a.same_encoding))
    rmeta = rubric_meta(a.rubric, rubric) if rubric else None
    title = (f"{rubric.get('title')} ({rmeta['id']} v{rmeta['version']})" if rubric
             else "калибровочная пара" if a.calibration else "вопросы строки входа")
    specs, key_pairs, key_items, warnings = [], {}, {}, []
    if mode == "pairwise":
        for n, r in enumerate(rows, 1):
            pid = str(r.get("pair") or f"p{n:03d}")
            c = r.get("_cal")
            if c:
                fa, fb = c["frames"]
                va, vb = str(fa["id"]), str(fb["id"])
                src_a, src_b = kbpaths.assets("calibration", fa["file"]), kbpaths.assets("calibration", fb["file"])
                crit = c["criterion"]
                qs, system, intro, brief = crit["questions"], crit["system"], crit["intro"], c["brief"]
                ptitle = (f"рубрика {crit['rubric']} v{crit['version']}" if crit.get("rubric") else "пункт рубрики")
            else:
                base = Path(r["_base"]) if r.get("_base") else None
                va, vb = "a", "b"
                src_a, src_b = _item_path(r["a"], base), _item_path(r["b"], base)
                qs = r.get("questions") or rubric.get("vlm", {}).get("pairwise_questions", [])
                system = r.get("system") or (rubric["judge"]["system"] if rubric else CAL_SYSTEM)
                intro = rubric["judge"]["pairwise_intro"] if rubric else CAL_INTRO
                brief, ptitle = r.get("brief"), title
            for s in (src_a, src_b):
                if not Path(s).exists():
                    raise JudgeError(f"нет кадра {s} (пара {pid})")
            resized, warn = None, None
            if r.get("raw"):
                fr_a, fr_b = store.put_raw(src_a), store.put_raw(src_b)
                if (fr_a["w"], fr_a["h"]) != (fr_b["w"], fr_b["h"]):
                    warn = f"кадры пары разного размера: {fr_a['w']}×{fr_a['h']} и {fr_b['w']}×{fr_b['h']}"
            else:
                ima, imb, resized, warn = equalize(_open_frame(src_a), _open_frame(src_b))
                fr_a, fr_b = store.put_image(ima, str(src_a)), store.put_image(imb, str(src_b))
            if warn:
                warnings.append(warn)
            orig_a, orig_b = str(r.get("orig_a") or src_a), str(r.get("orig_b") or src_b)
            key_pairs[pid] = {"variants": {va: orig_a, vb: orig_b}, "frames": {va: fr_a["frame"], vb: fr_b["frame"]},
                              **({"resized": {"a": va, "b": vb}[resized]} if resized else {}),
                              **({"warning": warn} if warn else {}),
                              "meta": {k: v for k, v in r.items() if k not in ("a", "b", "orig_a", "orig_b", "_cal", "_base", "raw")}}
            if c:
                key_pairs[pid].update({"group": c["group"], "rubric_address": c["addr"], "expect": c["expect"],
                                       "in_check": not c["opinion_only"], "kinds": c["kinds"], "strength": c["strength"]})
            for run in range(1, runs + 1):
                for order in ("AB", "BA"):
                    A, B = (va, vb) if order == "AB" else (vb, va)
                    frA, frB = (fr_a, fr_b) if order == "AB" else (fr_b, fr_a)
                    specs.append({"prompt": job_prompt(pkg, "pairwise", ptitle, [("A", frA), ("B", frB)], qs, system, intro, brief),
                                  "frames": [frA["frame"], frB["frame"]],
                                  "key": {"mode": "pairwise", "pair": pid, "run": run, "order": order, "A": A, "B": B,
                                          "A_orig": key_pairs[pid]["variants"][A], "B_orig": key_pairs[pid]["variants"][B],
                                          "orig_a": orig_a, "orig_b": orig_b,
                                          "questions": [q.get("id") for q in qs]}})
    else:
        base_q = (rubric or {}).get("vlm", {}).get("defect_questions" if mode == "defects" else "checklist_generic", [])
        for n, r in enumerate(rows, 1):
            base = Path(r["_base"]) if r.get("_base") else None
            src = _item_path(r["image"], base)
            if not src.exists():
                raise JudgeError(f"нет кадра {src}")
            iid = str(r.get("id") or f"i{n:03d}")
            if mode == "checklist":
                qs = [q for q in (r.get("questions") or qfile.get(r.get("brief_id") or r.get("brief") or "", []) or base_q) if "q" in q]
            else:
                qs = r.get("questions") or base_q
            report = r.get("report")
            if report and len(str(report)) < 400 and _item_path(report, base).exists():
                report = _item_path(report, base).read_text(encoding="utf-8")
            fr = store.put_image(_open_frame(src), str(src))
            key_items[iid] = {"image": str(src), "key": image_key(src), "frame": fr["frame"],
                              "meta": {k: v for k, v in r.items() if k not in ("image", "report", "_base")}}
            for run in range(1, runs + 1):
                system = r.get("system") or (rubric["judge"]["system"] if rubric else ROW_SYSTEM)
                intro = rubric["judge"][f"{mode}_intro"] if rubric else ROW_INTRO[mode]
                specs.append({"prompt": job_prompt(pkg, mode, title, [("", fr)], qs, system, intro, r.get("brief"), report),
                              "frames": [fr["frame"]],
                              "key": {"mode": mode, "item": iid, "run": run, "image": str(src), "key": key_items[iid]["key"],
                                      "questions": [q.get("code" if mode == "defects" else "id") for q in qs]}})
    import random
    random.Random(int(digest[:12], 16)).shuffle(specs)
    width = max(3, len(str(len(specs))))
    jobs_manifest, key_jobs = [], {}
    for i, s in enumerate(specs, 1):
        jid = f"j{i:0{width}d}"
        (pkg / "jobs" / f"{jid}.md").write_text(s["prompt"], encoding="utf-8")
        jobs_manifest.append({"id": jid, "kind": CALL_KIND[mode], "prompt": f"jobs/{jid}.md", "frames": s["frames"],
                              "answer": f"answers/{jid}.md"})
        key_jobs[jid] = s["key"]
    shutil.copy(JUDGE_SCHEMA, pkg / "response.schema.json")
    session = {"agent": "design-judge", "model": judge_model()}
    if rmeta is None and not a.calibration:
        qs_all = json.dumps([r.get("questions") for r in rows], ensure_ascii=False, sort_keys=True)
        rmeta = {"id": "questions", "sha256": hashlib.sha256(qs_all.encode()).hexdigest()[:16]}
    manifest = {"schema": PACKAGE_SCHEMA, "package": name, "created": now_iso(), "tool": f"asset_audit.py {VERSION}",
                "mode": mode, "kind": CALL_KIND[mode], "runs": runs, "orders": 2 if mode == "pairwise" else 1,
                "rubric": rmeta or {"id": "calibration", "sha256": sha256_file(CALIBRATION)[:16]},
                "response_schema": "response.schema.json", "session": session, "jobs": jobs_manifest,
                "warnings": sorted(set(warnings))}
    (pkg / "manifest.json").write_text(jdump(manifest) + "\n", encoding="utf-8")
    what = (f"Состав: пар — {len(key_pairs)}, порядков — 2, прогонов — {runs}; заданий — {len(specs)}." if mode == "pairwise"
            else f"Состав: кадров — {len(key_items)}, прогонов — {runs}; заданий — {len(specs)}.")
    (pkg / "README.md").write_text(PACKAGE_README.format(name=name, what=what), encoding="utf-8")
    key = {"schema": KEY_SCHEMA, "package": name, "package_dir": str(pkg), "created": manifest["created"], "mode": mode,
           "runs": runs, "rubric": {**manifest["rubric"], **({"file": str(CALIBRATION)} if a.calibration else {})},
           "session": session, "calibration": bool(a.calibration),
           "pairs": key_pairs, "items": key_items, "frames": store.source, "jobs": key_jobs}
    key_path.write_text(jdump(key) + "\n", encoding="utf-8")
    print(jdump({"package": str(pkg), "key": str(key_path), "jobs": len(specs), "mode": mode, "runs": runs,
                 "pairs" if mode == "pairwise" else "images": len(key_pairs) if mode == "pairwise" else len(key_items),
                 "warnings": manifest["warnings"]}))
    return 0


# ---------------------------------------------------------------- judge-parse


def extract_json_text(t: str):
    t = t.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.S)
    if m:
        t = m.group(1)
    s, e = t.find("{"), t.rfind("}")
    if s < 0 or e < s:
        raise ValueError("нет JSON")
    return json.loads(t[s:e + 1])


def _norm_findings(items, probs: list[str]) -> list[dict]:
    out = []
    for f in items or []:
        if not isinstance(f, dict):
            continue
        rule = str(f.get("rule") or "").strip()
        where, ev = str(f.get("where") or "").strip(), str(f.get("evidence") or "").strip()
        if len(where) < 3 or len(ev) < 3:
            probs.append(f"находка «{str(f.get('what') or rule)[:40]}» без места или доказательства — не засчитана")
            continue
        out.append({"what": str(f.get("what") or "").strip(), "where": where, "rule": rule, "evidence": ev,
                    "fix": str(f.get("fix") or "").strip()})
    return out[:12]


def normalize_answer(ans: dict, mode: str) -> tuple[dict, list[str]]:
    """Ответ судьи → нормализованный вид по протоколу: «нет» без доказательства и дефект «есть» без места — «не уверен»,
    победитель пары без причины — ничья, находка без места или доказательства не засчитывается."""
    probs: list[str] = []
    if mode == "checklist":
        out, ev = {}, {}
        for q in ans.get("answers", []):
            v = str(q.get("answer", "")).strip().lower().replace("/", "").replace(" ", "_")
            v = {"na": "not_applicable", "n_a": "not_applicable"}.get(v, v)
            v = v if v in ("yes", "no", "unsure", "not_applicable") else "unsure"
            e = str(q.get("evidence") or "").strip()
            if v == "no" and len(e) < 3:
                v = "unsure"
                probs.append(f"{q.get('id')}: «нет» без доказательства → unsure")
            out[q.get("id")] = v
            if e:
                ev[q.get("id")] = e
        strengths = [{"what": str(x.get("what") or "").strip(), "where": str(x.get("where") or "").strip()}
                     for x in ans.get("strengths") or [] if isinstance(x, dict) and x.get("what")]
        return {"answers": out, "evidence": ev, "findings": _norm_findings(ans.get("findings"), probs),
                **({"strengths": strengths} if strengths else {})}, probs
    if mode == "defects":
        out = []
        for d in ans.get("defects", []):
            present = d.get("present")
            present = {True: "yes", False: "no"}.get(present, str(present).lower() if present is not None else "unsure")
            present = present if present in ("yes", "no", "unsure") else "unsure"
            where = (d.get("where") or "").strip()
            if present == "yes" and len(where) < 3:
                present = "unsure"
                probs.append(f"{d.get('code')}: «есть» без «где» → unsure")
            out.append({"code": d.get("code"), "present": present, "where": where,
                        "evidence": str(d.get("evidence") or "").strip(), "fix": str(d.get("fix") or "").strip()})
        return {"defects": out, "findings": _norm_findings(ans.get("findings"), probs)}, probs
    out, why = {}, {}
    for q in ans.get("answers", []):
        raw = str(q.get("winner", "")).strip()
        v = raw.upper() if raw.upper() in ("A", "B") else raw.lower().replace(" ", "_")
        v = v if v in WINNERS else "tie"
        reason = str(q.get("why") or "").strip()
        if v in ("A", "B") and len(reason) < 3:
            probs.append(f"{q.get('id')}: выбор {v} без причины → ничья")
            v = "tie"
        out[q.get("id")] = v
        if reason:
            why[q.get("id")] = {"why": reason, "where": str(q.get("where") or "").strip()}
    return {"answers": out, "why": why, "codes": ans.get("defect_codes", [])}, probs


def mini_validate(inst, sch, path="", root=None) -> list[str]:
    """Проверка подмножества JSON Schema (type, required, enum, properties, items, additionalProperties, maxItems, $ref
    внутри файла) — запасной путь, когда нет jsonschema."""
    root = root if root is not None else sch
    if "$ref" in sch and str(sch["$ref"]).startswith("#/"):
        node = root
        for part in sch["$ref"][2:].split("/"):
            node = node[part]
        return mini_validate(inst, node, path, root)
    errs = []
    t = sch.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool, "number": (int, float), "integer": int}
    if t:
        tl = t if isinstance(t, list) else [t]
        if not any(isinstance(inst, types[x]) and not (x in ("number", "integer") and isinstance(inst, bool)) for x in tl if x in types):
            return [f"{path or '/'}: тип {type(inst).__name__}, нужен {t}"]
    if "enum" in sch and inst not in sch["enum"]:
        errs.append(f"{path}: {inst!r} не из {sch['enum']}")
    if isinstance(inst, dict):
        for k in sch.get("required", []):
            if k not in inst:
                errs.append(f"{path}/{k}: нет обязательного поля")
        props = sch.get("properties", {})
        for k, v in inst.items():
            if k in props:
                errs += mini_validate(v, props[k], f"{path}/{k}", root)
            elif sch.get("additionalProperties") is False:
                errs.append(f"{path}/{k}: лишнее поле")
    if isinstance(inst, list):
        if "maxItems" in sch and len(inst) > sch["maxItems"]:
            errs.append(f"{path}: элементов {len(inst)} > {sch['maxItems']}")
        if "items" in sch:
            for i, v in enumerate(inst):
                errs += mini_validate(v, sch["items"], f"{path}[{i}]", root)
    return errs


def answer_errors(raw, mode: str, schema: dict) -> list[str]:
    """Ответ против раздела схемы ответа: jsonschema, если есть, иначе встроенная проверка."""
    sub = {"$ref": f"#/$defs/{ANSWER_DEF[mode]}"}
    try:
        import jsonschema
    except ImportError:
        return mini_validate(raw, sub, "", schema)
    v = jsonschema.Draft202012Validator({"$defs": schema["$defs"], **sub})
    return ["/" + "/".join(map(str, e.absolute_path)) + ": " + e.message for e in v.iter_errors(raw)]


def _answer_file(ans_dir: Path, jid: str) -> Path | None:
    for ext in (".md", ".json", ".txt"):
        p = ans_dir / f"{jid}{ext}"
        if p.exists():
            return p
    return None


def pair_verdicts(rows: list[dict]) -> dict:
    """Попарные ответы → вердикт пары по вопросу (judge.md §5). В прогоне: совпадение обоих порядков — вариант, разные ответы
    — ничья, «оба не годятся» в любом порядке — «оба не годятся». По прогонам — большинство, иначе «неразличимы»; один прогон
    — черновая подсказка. → {(pair, вопрос): {verdict, runs, complete, draft, same}}."""
    by: dict = {}
    for r in rows:
        if r.get("mode") != "pairwise" or not r.get("answers"):
            continue
        for q, w in r["answers"].items():
            v = {"A": r.get("A"), "B": r.get("B")}.get(w, w)
            by.setdefault((r["pair"], q), {}).setdefault(r.get("run", 1), {})[r.get("order", "AB")] = v
    out = {}
    for (pid, q), runs in by.items():
        per_run, same = {}, []
        for run, orders in sorted(runs.items()):
            if len(orders) < 2:
                continue
            x, y = orders.get("AB"), orders.get("BA")
            same.append(x == y)
            per_run[run] = "both_bad" if "both_bad" in (x, y) else (x if x == y else "tie")
        vals = list(per_run.values())
        top = max(set(vals), key=vals.count) if vals else None
        verdict = top if vals and vals.count(top) * 2 > len(vals) else ("indistinct" if vals else None)
        out[(pid, q)] = {"verdict": verdict, "runs": per_run, "complete": len(vals), "draft": len(vals) == 1, "same": same}
    return out


def item_verdicts(rows: list[dict]) -> dict:
    """Ответы по кадру (рубрика): вопрос — большинство прогонов, иначе «не уверен»; маркер и находка засчитываются, если
    есть не меньше чем в двух прогонах (judge.md §5). → {item: {runs, checklist, defects, findings}}."""
    by: dict = {}
    for r in rows:
        if r.get("mode") not in ("checklist", "defects"):
            continue
        it = by.setdefault(r["item"], {"image": r.get("image"), "key": r.get("key"), "runs": set(), "q": {}, "d": {}, "f": {}})
        it["runs"].add(r.get("run", 1))
        for q, v in (r.get("answers") or {}).items():
            it["q"].setdefault(q, []).append(v)
        for d in r.get("defects") or []:
            if d.get("present") == "yes":
                it["d"].setdefault(d["code"], []).append({"run": r.get("run"), "where": d.get("where"), "evidence": d.get("evidence")})
        for f in r.get("findings") or []:
            k = re.sub(r"\s+", " ", (f.get("rule") or f.get("what") or "").strip().lower())
            it["f"].setdefault(k, []).append({"run": r.get("run"), **f})
    out = {}
    for iid, it in by.items():
        n = len(it["runs"])
        need = FINDING_MIN_RUNS if n >= FINDING_MIN_RUNS else 1
        chk = {}
        for q, vals in it["q"].items():
            top = max(set(vals), key=vals.count)
            chk[q] = top if vals.count(top) * 2 > len(vals) else "unsure"
        defects = [{"code": c, "runs": len({x["run"] for x in xs}), "confirmed": len({x["run"] for x in xs}) >= need,
                    "where": [x["where"] for x in xs]} for c, xs in sorted(it["d"].items())]
        findings = [{"rule": xs[0].get("rule"), "what": xs[0].get("what"), "runs": len({x["run"] for x in xs}),
                     "confirmed": len({x["run"] for x in xs}) >= need, "where": [x.get("where") for x in xs],
                     "evidence": xs[0].get("evidence"), "fix": xs[0].get("fix")} for _k, xs in sorted(it["f"].items())]
        out[iid] = {"image": it["image"], "key": it["key"], "runs": n, "draft": n < FINDING_MIN_RUNS, "checklist": chk,
                    "defects": defects, "findings": findings}
    return out


def batch_checks(rows: list[dict], pv: dict, th: Th) -> dict:
    """Проверка партии (judge.md §5–§6): доля выбора позиции A, согласованность при перестановке, доля «не уверен»."""
    pos = [w == "A" for r in rows if r.get("mode") == "pairwise" for w in (r.get("answers") or {}).values() if w in ("A", "B")]
    same = [s for v in pv.values() for s in v["same"]]
    rub = [v for r in rows if r.get("mode") == "checklist" for v in (r.get("answers") or {}).values()]
    rub += [d["present"] for r in rows if r.get("mode") == "defects" for d in r.get("defects") or []]
    out = {"position_A_share": round(sum(pos) / len(pos), 3) if pos else None, "decisive_answers": len(pos),
           "swap_consistency": round(sum(same) / len(same), 3) if same else None, "swap_runs": len(same),
           "unsure_share": round(sum(v == "unsure" for v in rub) / len(rub), 3) if rub else None, "rubric_answers": len(rub),
           "usable": True, "reasons": [], "recalibrate": []}
    if out["position_A_share"] is not None and abs(out["position_A_share"] - 0.5) > th_need(th, "judge.position_bias_max"):
        out["usable"] = False
        out["reasons"].append(f"доля выбора A {out['position_A_share']} — судья смещён к позиции (порог ± {th('judge.position_bias_max')})")
    if out["swap_consistency"] is not None and out["swap_consistency"] < th_need(th, "judge.swap_consistency_min"):
        out["usable"] = False
        out["reasons"].append(f"согласованность при перестановке {out['swap_consistency']} < {th('judge.swap_consistency_min')}")
    if out["unsure_share"] is not None and out["unsure_share"] > th_need(th, "judge.unsure_share_max"):
        out["recalibrate"].append(f"доля «не уверен» {out['unsure_share']} > {th('judge.unsure_share_max')} — пересчитать калибровку")
    return out


def judge_summary(K: dict, rows: list[dict], th: Th) -> dict:
    pv = pair_verdicts(rows)
    pairs: dict = {}
    cal = {"hit": 0, "miss": 0, "tie": 0, "not_in_check": 0, "no_expect": 0} if K.get("calibration") else None
    for (pid, q), v in sorted(pv.items()):
        kp = (K.get("pairs") or {}).get(pid) or {}
        rec = {"verdict": v["verdict"], "runs": v["runs"], "complete_runs": v["complete"], "draft": v["draft"]}
        if cal is not None:
            exp = kp.get("expect")
            rec["expect"] = exp
            if not kp.get("in_check", True):
                rec["result"] = "not_in_check"
            elif exp is None:
                rec["result"] = "no_expect"
            elif v["verdict"] == exp:
                rec["result"] = "hit"
            elif v["verdict"] in (kp.get("variants") or {}):
                rec["result"] = "miss"
            else:
                rec["result"] = "tie"
            cal[rec["result"]] += 1
        pairs.setdefault(pid, {})[q] = rec
    out = {"package": K.get("package"), "mode": K.get("mode"), "runs": K.get("runs"), "rubric": K.get("rubric"),
           "session": K.get("session"), "answers": len(rows), "invalid": sum(1 for r in rows if not r.get("valid")),
           "pairs": pairs, "items": item_verdicts(rows), "batch": batch_checks(rows, pv, th)}
    if cal is not None:
        out["calibration"] = cal
    return out


def cmd_judge_parse(a):
    """Ответы сессий судьи (answers/<id>.md|json) + ключ вне пакета → строки ответов и сводка по правилу протокола."""
    pkg = Path(a.package).resolve()
    key_path = Path(a.key).resolve() if a.key else pkg.with_name(pkg.name + ".key.json")
    if not key_path.exists():
        raise JudgeError(f"нет ключа {key_path}")
    K = json.loads(key_path.read_text(encoding="utf-8"))
    ans_dir = Path(a.answers).resolve() if a.answers else pkg / "answers"
    schema = json.loads(JUDGE_SCHEMA.read_text(encoding="utf-8"))
    rows, missing = [], []
    for jid, j in sorted(K.get("jobs", {}).items()):
        f = _answer_file(ans_dir, jid)
        if f is None:
            missing.append(jid)
            continue
        mode = j["mode"]
        row = {"job": jid, **{k: v for k, v in j.items() if k != "questions"}, "file": str(f)}
        try:
            text = f.read_text(encoding="utf-8")
            raw = json.loads(text) if f.suffix == ".json" else extract_json_text(text)
            errs = answer_errors(raw, mode, schema)
            norm, probs = normalize_answer(raw, mode)
            asked = [q for q in j.get("questions") or [] if q]
            got = set(norm.get("answers") or {}) | {d["code"] for d in norm.get("defects") or []}
            if asked and set(asked) - got:
                probs.append("нет ответа на: " + ", ".join(sorted(set(asked) - got)))
            row.update(norm)
            row.update({"problems": probs, "schema_errors": errs[:5], "valid": not errs})
        except (ValueError, json.JSONDecodeError) as e:
            row.update({"valid": False, "error": str(e)[:200]})
        rows.append(row)
    th = Th(load_thresholds(Path(a.thresholds) if a.thresholds else None))
    summ = judge_summary(K, rows, th)
    summ["missing"] = missing
    out = Path(a.out).resolve() if a.out else key_path.with_name(K.get("package", pkg.name) + ".verdict.json")
    rows_path = out.with_name(out.name.replace(".verdict.json", "") + ".answers.jsonl") if out.name.endswith(".verdict.json") \
        else out.with_suffix(".answers.jsonl")
    rows_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    summ["rows"] = str(rows_path)
    out.write_text(jdump(summ) + "\n", encoding="utf-8")
    print(jdump({"verdict": str(out), "rows": str(rows_path), "answers": len(rows), "missing": len(missing),
                 "invalid": summ["invalid"], "batch": summ["batch"], **({"calibration": summ["calibration"]} if "calibration" in summ else {})}))
    return 0 if not missing and not summ["invalid"] else 1


# ---------------------------------------------------------------- согласие с человеком и доверие


def wilson(k, n):
    return mod("stand_run").wilson(k, n)


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    labels = sorted({x for p in pairs for x in p})
    n = len(pairs)
    po = sum(1 for x, y in pairs if x == y) / n
    pe = sum((sum(1 for x, _ in pairs if x == L) / n) * (sum(1 for _, y in pairs if y == L) / n) for L in labels)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else None


def trust_level(agree: float | None, lo: float | None, n: int, th: Th) -> str:
    """Уровень доверия судье по согласию с решающими голосами человека (judge.md §6); пороги — группа judge thresholds.yaml."""
    if agree is None or n < th_need(th, "judge.min_pairs"):
        return "мало данных"
    if agree >= th_need(th, "judge.trust_agreement_min") and (lo or 0) >= th_need(th, "judge.wilson_low_min"):
        return "сортировать"
    if agree >= th_need(th, "judge.prefilter_agreement_min"):
        return "только предфильтр"
    return "не использовать"


def f1_level(f1: float | None, n: int, th: Th) -> str:
    """Поиск дефектов меряют F1 против разметки человека (judge.md §6): выше порога судья — предфильтр, решает человек."""
    if f1 is None or n < th_need(th, "judge.min_pairs"):
        return "мало данных"
    return "только предфильтр" if f1 >= th_need(th, "judge.f1_min") else "не использовать"


def cmd_agree(a):
    """Согласие судьи с человеком. Попарно: голоса страницы stand_run.py (--votes — файл на сессию, по порядку; --key) против
    вердиктов пар (строки judge-parse). Рубрика: ответы человека на те же вопросы и разметка маркеров (--labels) против
    ответов судьи — согласие и F1. Пороги — группа judge thresholds.yaml."""
    th = Th(load_thresholds(Path(a.thresholds) if a.thresholds else None))
    rows = [json.loads(x) for x in Path(a.answers).read_text(encoding="utf-8").splitlines() if x.strip()]
    pv = pair_verdicts(rows)
    rep: dict = {"answers": rel(a.answers), "batch": batch_checks(rows, pv, th), "recalibrate": []}
    rep["recalibrate"] += rep["batch"]["recalibrate"]
    if a.votes and a.key:
        K = json.loads(Path(a.key).read_text(encoding="utf-8"))
        files = {}
        for r in rows:
            if r.get("mode") == "pairwise":
                files.setdefault(r["pair"], {r.get("A"): r.get("A_orig"), r.get("B"): r.get("B_orig")})
        by_set = {frozenset(map(str, f.values())): pid for pid, f in files.items()}
        per_q: dict = {}
        sessions = []
        for vf in a.votes:
            V = json.loads(Path(vf).read_text(encoding="utf-8"))
            hits = []
            for pid, v in (V.get("votes") or {}).items():
                kp = K["pairs"].get(pid)
                if not kp or kp.get("gold") or kp.get("identical") or kp.get("repeat_of"):
                    continue
                pa, pb = str(kp["A"]["files"][0]), str(kp["B"]["files"][0])
                jp = pid if pid in files else by_set.get(frozenset((pa, pb)))
                for q, o in v.items():
                    if o not in ("A", "B") or jp is None:
                        continue
                    human = pa if o == "A" else pb
                    jv = (pv.get((jp, q)) or {}).get("verdict")
                    if jv in files[jp]:
                        ok = str(files[jp][jv]) == human
                        per_q.setdefault(q, {"hits": [], "abstain": 0})["hits"].append(ok)
                        hits.append(ok)
                    else:
                        per_q.setdefault(q, {"hits": [], "abstain": 0})["abstain"] += 1
            sessions.append({"votes": rel(vf), "voter": V.get("voter"), "n": len(hits),
                             "agree": round(sum(hits) / len(hits), 3) if hits else None})
        rep["pairwise"] = {}
        for q, d in per_q.items():
            k, n = sum(d["hits"]), len(d["hits"])
            p, lo, hi = wilson(k, n) if n else (None, None, None)
            rep["pairwise"][q] = {"agree": round(p, 3) if p is not None else None,
                                  "wilson95": [round(lo, 3), round(hi, 3)] if n else None, "n": n, "abstain": d["abstain"],
                                  "decision": trust_level(p, lo, n, th)}
        rep["sessions"] = sessions
        need = int(th_need(th, "judge.disagree_sessions"))
        low = th_need(th, "judge.prefilter_agreement_min")
        tail = 0
        for s in reversed(sessions):
            if s["agree"] is None or s["agree"] >= low:
                break
            tail += 1
        rep["sessions_disagree_tail"] = tail
        if tail >= need:
            rep["recalibrate"].append(f"расхождение с заказчиком {tail} сессий подряд (порог {need}) — пересчитать калибровку")
    if a.labels:
        lab = [json.loads(x) for x in Path(a.labels).read_text(encoding="utf-8").splitlines() if x.strip()]
        iv = item_verdicts(rows)
        by_key = {v["key"]: v for v in iv.values()}
        pairs, by_type, yes_j, yes_h = [], {}, 0, 0
        tp = fp = fn = 0
        n_def = 0
        for L in lab:
            jv = by_key.get(L.get("key"))
            if jv is None:
                continue
            for q, hv in (L.get("answers") or {}).items():
                v = jv["checklist"].get(q)
                if v in ("yes", "no") and hv in ("yes", "no"):
                    pairs.append((v, hv))
                    by_type.setdefault((L.get("types") or {}).get(q, "?"), []).append(v == hv)
                    yes_j += v == "yes"
                    yes_h += hv == "yes"
            found = {d["code"] for d in jv["defects"] if d["confirmed"]} | {f["rule"] for f in jv["findings"] if f["confirmed"]}
            for code, hv in (L.get("defects") or {}).items():
                if hv not in ("yes", "no"):
                    continue
                n_def += 1
                got = code in found
                tp += got and hv == "yes"
                fp += got and hv == "no"
                fn += (not got) and hv == "yes"
        if pairs:
            k = sum(1 for x, y in pairs if x == y)
            p, lo, hi = wilson(k, len(pairs))
            rep["checklist"] = {"agree": round(p, 3), "wilson95": [round(lo, 3), round(hi, 3)], "n": len(pairs),
                                "kappa": cohen_kappa(pairs), "yes_rate_judge": round(yes_j / len(pairs), 3),
                                "yes_rate_human": round(yes_h / len(pairs), 3),
                                "by_type": {t: {"agree": round(sum(v) / len(v), 3), "n": len(v)} for t, v in by_type.items()},
                                "decision": trust_level(p, lo, len(pairs), th)}
        if n_def:
            prec = tp / (tp + fp) if tp + fp else None
            recall = tp / (tp + fn) if tp + fn else None
            f1 = (2 * prec * recall / (prec + recall)) if prec and recall else (0.0 if (tp + fp + fn) else None)
            rep["defects"] = {"precision": rnd(prec, 3), "recall": rnd(recall, 3), "f1": rnd(f1, 3), "tp": tp, "fp": fp,
                              "fn": fn, "n": n_def, "decision": f1_level(f1, n_def, th)}
    if a.out:
        Path(a.out).write_text(jdump(rep), encoding="utf-8")
    print(jdump(rep))
    return 0


def cmd_calibrate(a):
    """Порог метрики по меткам человека (ok/bad): лучший порог по Юдену, AUC (Манн–Уитни), n."""
    audit = json.loads(Path(a.audit).read_text(encoding="utf-8"))
    lab = {json.loads(x)["file"]: json.loads(x)["label"] for x in Path(a.labels).read_text(encoding="utf-8").splitlines() if x.strip()}
    vals = []
    for r in audit.get("assets", []):
        v = r
        for part in a.metric.split("."):
            v = v.get(part) if isinstance(v, dict) else None
        name = Path(r["file"]).name
        L = lab.get(r["file"]) or lab.get(name)
        if isinstance(v, (int, float)) and L in ("ok", "bad"):
            vals.append((float(v), L == "bad"))
    if len(vals) < 4:
        print(jdump({"n": len(vals), "error": "мало размеченных"}))
        return 1
    pos = [v for v, b in vals if b]
    neg = [v for v, b in vals if not b]
    auc = sum((x > y) + 0.5 * (x == y) for x in pos for y in neg) / max(1, len(pos) * len(neg))
    direction = "above" if auc >= 0.5 else "below"
    best = None
    for t in sorted({v for v, _ in vals}):
        pred = [(v > t) if direction == "above" else (v < t) for v, _ in vals]
        tp = sum(p and b for p, (_, b) in zip(pred, vals))
        fp = sum(p and not b for p, (_, b) in zip(pred, vals))
        tpr, fpr = tp / max(1, len(pos)), fp / max(1, len(neg))
        j = tpr - fpr
        if best is None or j > best[0]:
            best = (j, t, tpr, fpr)
    print(jdump({"metric": a.metric, "n": len(vals), "bad": len(pos), "auc": round(auc, 3), "direction": direction,
                 "threshold": best[1], "tpr": round(best[2], 3), "fpr": round(best[3], 3), "youden": round(best[0], 3),
                 "note": "n < 20 — ориентир, не порог; сверить с порогом thresholds.yaml" if len(vals) < 20 else ""}))
    return 0


# ================================================================ CLI


def cmd_ocr_worker(a):
    lim = a.det_limit.split(":")
    try:   # ошибки картинок ocr_worker ловит сам; наружу выходят только пакет и загрузка моделей — это окружение
        res = ocr_worker(a.paths, a.lang, a.text_score, not a.no_relines, (int(lim[0]), lim[1]))
    except ImportError as e:
        hint = env_hint(f"нет пакета {e.name or 'rapidocr'} (группа ocr)", OCR_INSTALL)
        res = [{"file": p, "lang": a.lang, "error": hint, "env": True} for p in a.paths]
    except Exception as e:  # noqa: BLE001
        hint = env_hint(f"модели OCR не загрузились ({type(e).__name__}: {last_line(str(e), 200)})", OCR_INSTALL)
        res = [{"file": p, "lang": a.lang, "error": hint, "env": True} for p in a.paths]
    print(json.dumps(res, ensure_ascii=False))
    return 0


def cmd_ocr(a):
    paths = []
    for p in a.paths:
        P = Path(p)
        paths += sorted(x for x in P.rglob("*") if x.suffix.lower() in IMG_EXT) if P.is_dir() else [P]
    res = run_ocr(paths, a.lang, a.text_score)
    th = Th(load_thresholds())
    for r in res:
        if a.expect and "lines" in r:
            tr = "\n".join(L["text"] for L in r["lines"])
            r["text_check"] = text_verdict(a.expect, tr, lines_meta=r["lines"], th=th, h_scale=ocr_scale(r))
    if a.transcripts_out:   # формат stand_run.py metrics --transcripts: {путь от корня: транскрипт}
        tr = {rel(r["file"]): "\n".join(L["text"] for L in r.get("lines", [])) for r in res if "lines" in r}
        Path(a.transcripts_out).write_text(jdump(tr), encoding="utf-8")
    print(jdump(res))
    return 0 if all("error" not in r for r in res) else 2


def cmd_audit(a):
    s = audit_paths(a)
    if a.json:
        print(jdump(s))
    else:
        print(Path(ROOT / s["out"] / "audit.md").read_text(encoding="utf-8") if (ROOT / s["out"] / "audit.md").exists()
              else audit_md(s))
        print(f"JSON: {s['out']}/audit.json · лист: {s.get('index_sheet')}")
    worst = "fail" if s["verdicts"]["fail"] else ("needs_human" if s["verdicts"]["needs_human"] else "ok")
    if s.get("series") and s["series"]["verdict"] == "fail":
        worst = "fail"
    return 1 if (a.strict and worst == "fail") else 0


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    w = sp.add_parser("_ocr-worker")
    w.add_argument("paths", nargs="+")
    w.add_argument("--lang", default="ru", choices=sorted(OCR_SETS))
    w.add_argument("--text-score", type=float, default=0.3)
    w.add_argument("--det-limit", default=f"{OCR_DET_LIMIT[0]}:{OCR_DET_LIMIT[1]}")
    w.add_argument("--no-relines", action="store_true")
    o = sp.add_parser("ocr", help="OCR кириллицы под блокировкой heavy + сверка со строками")
    o.add_argument("paths", nargs="+")
    o.add_argument("--lang", default="ru", choices=sorted(OCR_SETS))
    o.add_argument("--text-score", type=float, default=0.3)
    o.add_argument("--expect", action="append", default=[])
    o.add_argument("--transcripts-out", help="JSON {файл: транскрипт} для stand_run.py metrics --transcripts")
    u = sp.add_parser("audit", help="приёмка файлов или папки с паспортами")
    u.add_argument("paths", nargs="+")
    u.add_argument("--mode", default="auto", choices=["auto", "series"] + sorted(MODES))
    u.add_argument("--out")
    u.add_argument("--thresholds")
    u.add_argument("--dna", help="паспорт визуала (06-art-direction-consistency): палитра, приёмка, эталоны, зона текста")
    u.add_argument("--spec", help="спецификация ассета (05-prompting/asset-spec.schema.json): зона текста, палитра, строки")
    u.add_argument("--task", help="код задачи (IMG-HERO-PHOTO …), если нет паспорта")
    u.add_argument("--slot", metavar="СЛОТ",
                   help=f"род слота для порогов ({', '.join(SLOT_KINDS)}); с --plan — id слота плана ассетов")
    u.add_argument("--plan", help="план ассетов страницы (asset-plan v1): бюджет веса — `max_kb` варианта слота --slot, "
                                  "род слота — по его виду; без плана — бюджеты по умолчанию")
    u.add_argument("--variant", help="вариант слота плана (desktop, mobile …); без ключа — mobile при --mobile, иначе desktop")
    u.add_argument("--icon-set", metavar="НАБОР",
                   help="набор иконок продукта (conventions.icons.set карты решений), по умолчанию lucide или набор из "
                        "--conventions: шапка и штрих не по эталону — брак только у набора Lucide, у другого набора — "
                        "предупреждение")
    u.add_argument("--icon-stroke", type=float, metavar="ШТРИХ", help="штрих иконок продукта (эталон шапки; по умолчанию 2)")
    u.add_argument("--icon-viewbox", metavar="VIEWBOX", help="viewBox иконок продукта (эталон шапки; по умолчанию «0 0 24 24»)")
    u.add_argument("--conventions", metavar="SYSTEM.yaml",
                   help="карта решений дизайн-системы: набор и штрих иконок — conventions.icons (set, stroke)")
    u.add_argument("--stage", default="master", choices=["master", "web"],
                   help="web — файл на страницу: бюджеты веса, у видео — порог шва после кодирования")
    u.add_argument("--mobile", action="store_true",
                   help="телефонный кадр слота: бюджет <слот>_mobile_kb (hero ≤ 80 КБ), без проверки размера мастера hero")
    u.add_argument("--ratio", help="заказанная пропорция 16:9, если нет паспорта")
    u.add_argument("--expect", action="append",
                   help="строка, которая должна быть на картинке дословно (повторять); число вхождений — суффикс {×N} "
                        "(«Скидка{×2}») или повтор той же строки")
    u.add_argument("--allow-text", action="append", help="текст, который может быть на картинке (этикетка товара)")
    u.add_argument("--yo-optional", action="store_true", help="ё → е не считать ошибкой")
    u.add_argument("--ocr", default="auto", choices=["auto", "on", "off"])
    u.add_argument("--lang", default="ru", choices=sorted(OCR_SETS))
    u.add_argument("--text-zone", help="x0,y0,x1,y1 в долях кадра")
    u.add_argument("--text-color", help="#hex цвета текста поверх зоны")
    u.add_argument("--master", help="мастер для проверки производной: картинка — SSIMULACRA2, видео — motion_keep к мезонину")
    u.add_argument("--orig", help="исходник правки или аутпейнта")
    u.add_argument("--mask")
    u.add_argument("--mask-mode", default="white", choices=["white", "black", "alpha"])
    u.add_argument("--protect", help="маска защищённого объекта (товар, логотип)")
    u.add_argument("--changes", type=int, help="сколько изменений заказано (безмасочная правка)")
    u.add_argument("--removal", action="store_true", help="удаление объекта: растушёвка ≈ 3 %% стороны (H 08/02 §2.4)")
    u.add_argument("--edit-kind", choices=["light", "color", "object", "other"])
    u.add_argument("--feather", type=int)
    u.add_argument("--bg", help="#hex фона под вырезом (ореол)")
    u.add_argument("--object", choices=["solid", "glass", "hair", "fur"])
    u.add_argument("--ref-alpha", help="эталонная альфа (рендер Blender)")
    u.add_argument("--control", help="i2v-контроль того же кадра (живость петли)")
    u.add_argument("--key", help="#hex ключа хромакея или auto")
    u.add_argument("--mezzanine", action="store_true",
                   help="файл — мезонин или выход модели до перекодирования: порог шва мезонина")
    u.add_argument("--camera-move", action="store_true", help="движение камеры заказано (не считать «ползущей»)")
    u.add_argument("--montage", action="store_true",
                   help="видео из нескольких планов: склейки не находка, движение считается по планам, стык петли — шов "
                        "или ещё одна склейка")
    u.add_argument("--fade-event", action="store_true",
                   help="в петле объявлено событие-затемнение: угасание движения — предупреждение, не брак")
    u.add_argument("--css-width", type=float,
                   help="ширина видео на странице, CSS px, — для поля вспышек WCAG 2.3.1 (по умолчанию — ширина файла)")
    u.add_argument("--series", action="store_true", help="считать ещё и серию по всем картинкам")
    u.add_argument("--grid", help="RxC: разрезать сетку одной генерации и считать серию по ячейкам")
    u.add_argument("--ref", action="append", help="эталоны серии (ΔE палитры к эталону)")
    u.add_argument("--no-provenance", dest="provenance", action="store_false")
    u.add_argument("--strict", action="store_true", help="код выхода 1 при fail")
    u.add_argument("--json", action="store_true")
    u.add_argument("--debug", action="store_true")
    t = sp.add_parser("thresholds", help="пороги с источниками")
    t.add_argument("--check", action="store_true")
    t.add_argument("--thresholds")
    j = sp.add_parser("judge-jobs", help="пакет заданий судьи для отдельных сессий Opus (агент design-judge), ключ — вне пакета")
    src = j.add_mutually_exclusive_group(required=True)
    src.add_argument("--items", help="JSONL: {image, brief?, questions?, report?} или {a, b, pair?, brief?, questions?}; "
                                     "относительные пути — от файла")
    src.add_argument("--from-stand-page", help="папка страницы голосования stand_run.py page: те же пары и файлы, что у заказчика")
    src.add_argument("--calibration", action="store_true", help="пары калибровочного набора assets/calibration/index.yaml, "
                                                                "вопросы — из поля rubric")
    j.add_argument("--rubric", help="рубрика kb/ai-media/11-evaluation-qa/rubrics/<имя>.rubric.json; без неё — вопросы в каждой "
                                    "строке --items (макет, страница: вопросы рубрики владельца), с --calibration не нужна")
    j.add_argument("--mode", default="checklist", choices=["checklist", "defects", "pairwise"],
                   help="checklist, defects — вид «рубрика» по кадру; pairwise — «попарно» (страница и калибровка — всегда)")
    j.add_argument("--pairs", help="с --calibration: id пар поля pair через запятую; без него — все пары набора")
    j.add_argument("--questions", help="JSON {id брифа: [{id, q}]} — вопросы чек-листа по брифу (brief_id строки)")
    j.add_argument("--runs", type=int, default=3,
                   help="прогонов задания: 3 — находки и второе мнение, 5 — сортировка трёх и больше вариантов, 1 — черновик "
                        "(kb/common/judge.md §5)")
    j.add_argument("--same-encoding", action="store_true",
                   help="попарно: обе стороны — кодированием страницы голосования (JPEG q90 ≤ 1600 px, PNG при альфе); "
                        "по умолчанию — PNG без потерь")
    j.add_argument("--out", help="папка пакетов (по умолчанию $DDD_HOME/out/ai-media/judge)")
    j.add_argument("--name", help="имя пакета (по умолчанию — вход и хэш входов)")
    j.add_argument("--force", action="store_true", help="пересобрать пакет, в котором уже есть ответы")
    pj = sp.add_parser("judge-parse", help="ответы сессий судьи → строки ответов и сводка по правилу протокола")
    pj.add_argument("package", help="папка пакета judge-jobs")
    pj.add_argument("--key", help="ключ слепоты (по умолчанию <пакет>.key.json рядом с папкой)")
    pj.add_argument("--answers", help="папка ответов (по умолчанию <пакет>/answers)")
    pj.add_argument("--out", help="сводка JSON (по умолчанию <пакет>.verdict.json рядом с ключом; строки — <пакет>.answers.jsonl)")
    pj.add_argument("--thresholds")
    g = sp.add_parser("agree", help="согласие судьи с человеком и уровень доверия")
    g.add_argument("--answers", required=True, help="строки ответов judge-parse (<пакет>.answers.jsonl)")
    g.add_argument("--votes", action="append", help="голоса страницы stand_run.py — файл на сессию, по порядку сессий")
    g.add_argument("--key", help="ключ страницы голосования (DIR.key.json)")
    g.add_argument("--labels", help="JSONL разметки человека: {key, answers?: {id: yes|no}, types?, defects?: {код: yes|no}}")
    g.add_argument("--thresholds")
    g.add_argument("--out")
    c = sp.add_parser("calibrate", help="порог метрики по меткам человека")
    c.add_argument("--audit", required=True)
    c.add_argument("--labels", required=True)
    c.add_argument("--metric", required=True, help="путь в JSON ассета: checks.text_zone.edge_density")
    s = sp.add_parser("selftest")
    s.add_argument("--keep", action="store_true")
    return ap


def main(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    fn = {"_ocr-worker": cmd_ocr_worker, "ocr": cmd_ocr, "audit": cmd_audit, "thresholds": cmd_thresholds,
          "judge-jobs": cmd_judge_jobs, "judge-parse": cmd_judge_parse, "agree": cmd_agree, "calibrate": cmd_calibrate,
          "selftest": cmd_selftest}[a.cmd]
    try:
        return fn(a)
    except (JudgeError, AuditError) as e:
        print(f"asset_audit.py {a.cmd}: {e}", file=sys.stderr)
        return 2


def cmd_selftest(a):
    """Самопроверка без сети и без OCR-модели (OCR — tests/test_asset_audit.py --ocr)."""
    sys.path.insert(0, str(TOOLS / "tests"))
    import test_asset_audit as T
    return T.run(keep=getattr(a, "keep", False), ocr=False)


if __name__ == "__main__":
    sys.exit(main())
