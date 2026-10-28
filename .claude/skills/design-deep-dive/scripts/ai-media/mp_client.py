#!/usr/bin/env python3
"""mp_client.py — клиент каналов генерации вне Media API polza: RouterAI, Gen-API, polza-chat, polza-images.

Python 3.13, только стандартная библиотека (+ polza_catalog.py рядом: снимок каталога polza и калькулятор ступеней).
Образец и совместимость — polza.py: сухой прогон по умолчанию, трата только с --live, оценка цены до отправки, лимиты,
опрос, немедленное скачивание, паспорт рядом с файлом, общий журнал затрат (поле channel; события polza-chat и
polza-images считаются в бюджет polza вместе с polza.py). Каналы — для генерации картинок, видео и SVG по утверждённому
плану ассетов. Оценка по рубрике и разбор картинок — не задание канала: их делает отдельная сессия Opus (агент
design-judge) по пакету asset_audit.py judge-jobs или vlm_to_dna.py build. 3D-генераторы Gen-API не вызываются: 3D —
Blender и код (kb/3d/10-ai-3d-generation-assets/01-generators-landscape.md §1).

Каналы (документация и правила — kb/ai-media/02-providers-platforms/07-multichannel-client.md):
  routerai      POST /api/v1/images — синхронно: data[].b64_json (+ media_type; SVG у векторных Recraft), usage.cost в ₽
                POST /api/v1/videos — 202 {id, polling_url} → GET /api/v1/videos/{id} → unsigned_urls (скачивание с ключом)
                POST /api/v1/chat/completions — диалоговые модели (картинки в message.images)
  genapi        POST /api/v1/networks/{slug} → {request_id} → GET /api/v1/request/get/{id}: processing → success | error;
                is_sync; ссылки на файлы живут 24 ч — скачивать сразу; translate_input клиент ставит явно
  polza-chat    POST /api/v1/chat/completions — OpenAI-совместимый; картинки на вход — image_url; цена по токенам
  polza-images  POST /api/v2/images/generations — синхронно до 120 с, иначе {id, status: pending} → GET /api/v1/media/{id}

Подкоманды:
  estimate JOBS...                  проверка по каталогам и документации, цена, лимиты — без сети и без ключей
  run JOB [--pick TAG|N|/re/]       одно задание (сухой прогон; --live — отправить)
  batch JOBS... [--parallel 2]      серии и несколько файлов (не больше 3 параллельно)
  status ID --channel C             статус задачи (routerai — видео; genapi; polza-images — /v1/media; polza-chat — history)
  download ID --channel C           дожать готовый результат: скачать файлы, паспорт, закрыть запись журнала
  ledger [--sum] [--channel C] [--agent A] [--tail N] [--json]   общий журнал затрат (и события polza.py)
  show MODEL --channel C            что клиент знает о модели или сети: параметры, значения, цены, passthrough
  snapshot [--channel routerai|genapi|all]   свежий публичный каталог (бесплатный GET без ключа) в $DDD_HOME/cache/ai-media/<канал>/:
                                    файл качается во временную папку и встаёт на место переименованием; оборванный
                                    запрос повторяется; не удалось — папки снимка нет, последним остаётся снимок
                                    до запуска, код 1
  balance --channel C [--path P]    баланс и лимит ключа канала: чтение, не трата — идёт без --live; polza-chat и
                                    polza-images — GET /v2/balance и /v1/key; адрес чтения у routerai и genapi называет
                                    --path (GET); ответ канала и его числа — в stdout; адрес не назван — код 2
  selftest                          самопроверка без сети: оценки сверяются с ценами, посчитанными из полей последних
                                    снимков каталогов; снимка канала нет — его случаи пропускаются

Задание: {"channel": "routerai", "method": "POST", "path": "/api/v1/images", "body": {...}, "tag": "...", "agent": "...",
  "variant": 1, "max_rub": 10, "price_rub": 8.74, "notes": "гипотеза", "meta": {...}}.
Файлы: .json (объект или массив заданий), .jsonl (строка — генерация); channel можно не писать, если он в имени файла
(*.routerai.json, *.genapi.jsonl …). Локальные пути в полях картинок (относительно файла задания) уходят data:URI base64.
Шаблоны: {{ИМЯ}} где угодно в теле и «<…>» в полях файлов — estimate предупреждает и берёт цену из price_rub, --live
отказывает, пока не подставлено: --set ИМЯ=значение, --set-file ИМЯ=путь.

Окружение: ключи ROUTERAI_API_KEY | GENAPI_API_KEY | POLZA_API_KEY или файлы ~/.config/{routerai,genapi,polza}/api_key
(права 600; другой путь — ROUTERAI_KEY_FILE | GENAPI_KEY_FILE | POLZA_KEY_FILE) — читаются только при --live и при
чтении баланса (balance) и только для нужного канала; базы ROUTERAI_BASE_URL (https://routerai.ru/api),
GENAPI_BASE_URL (https://api.gen-api.ru/api),
POLZA_BASE_URL (https://polza.ai/api, общий с polza.py); бюджеты ROUTERAI_BUDGET_TOTAL, GENAPI_BUDGET_TOTAL (по умолчанию
0 — без явного лимита --live не тратит), POLZA_BUDGET_TOTAL (2000, общий с polza.py); MP_BUDGET_AGENT; MP_MAX_JOB (60 ₽
на задание); журнал MP_LEDGER или POLZA_LEDGER ($DDD_HOME/out/ai-media/_ledger.jsonl); MP_OUT_ROOT
($DDD_HOME/out/ai-media/_mp/<агент>/<дата>/). Ключ никогда не печатается и не пишется; Authorization уходит только на
хост своего канала и не переносится при редиректе.

Коды выхода (как у polza.py): 0 — успех; 1 — ошибка задания или проверки (в том числе незаполненный шаблон, задание
оценки, 3D-сеть); 2 — ошибка вызова или окружения (нет снимка каталога, файла, модели; не назван адрес баланса; файл
задания не разбирается). Особые исходы: 3 — отказ по бюджету или цене; 4 — таймаут опроса (дожать: download ID
--channel C --live); 5 — генерация failed / error / expired / cancelled или ответ без результата: тело и заголовки
ответа канала — в паспорте задания (<тег>__<модель>__<id>.passport.json, поле response); 6 — отказ канала (HTTP-ошибка);
7 — файл не скачан. У batch — наибольший код серии.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures as cf
import contextlib
import datetime as dt
import fcntl
import hashlib
import io
import json
import math
import mimetypes
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(TOOLS.parent / "lib"))  # scripts/lib: kbpaths
import kbpaths  # noqa: E402
import polza_catalog as pc  # noqa: E402

VERSION = "mp_client.py 1.1"
ROOT = pc.ROOT
CACHE = kbpaths.cache("ai-media")
DEFAULT_LEDGER = kbpaths.out("ai-media") / "_ledger.jsonl"  # журнал затрат — общий с polza.py
DEFAULT_OUT_ROOT = kbpaths.out("ai-media", "_mp")
P04 = kbpaths.data("ai-media")  # прайс Gen-API — scripts/ai-media/data/; каталог RouterAI — снимок snapshot
MAX_PARALLEL = 3
EXIT_OK, EXIT_JOB, EXIT_USAGE = 0, 1, 2                  # 2 — ошибка вызова или окружения
EXIT_BUDGET, EXIT_TIMEOUT, EXIT_FAILED, EXIT_HTTP, EXIT_DOWNLOAD = 3, 4, 5, 6, 7   # особые исходы
RESPONSE_TEXT_MAX = 20000            # тело ответа не JSON в паспорте отказа: первые символы, остальное — длиной и sha256
INLINE_WARN = 4 * 1024 * 1024        # больше — предупреждение (тело запроса тяжёлое)
INLINE_MAX = 20 * 1024 * 1024        # больше — ошибка (дайте публичный URL)
FX_ROUTERAI_DEFAULT = 109.285        # ₽/$ RouterAI к ценам OpenRouter (3,82498935 ₽ / $0,035 у Recraft V4.1)
MP_PX = 1024 * 1024                  # 1 Мп у BFL = 1 048 576 px
RECRAFT_STYLES_REF_USD = 0.005       # OpenRouter endpoints recraft-v4-styles-vector: input_reference $0,005 за запрос

CHANNELS = {
    "routerai": dict(base_env="ROUTERAI_BASE_URL", base="https://routerai.ru/api", key_env="ROUTERAI_API_KEY",
                     key_file_env="ROUTERAI_KEY_FILE", key_file="~/.config/routerai/api_key",
                     budget_env="ROUTERAI_BUDGET_TOTAL", budget_default=0.0, scope="routerai",
                     default_path="/api/v1/images"),
    "genapi": dict(base_env="GENAPI_BASE_URL", base="https://api.gen-api.ru/api", key_env="GENAPI_API_KEY",
                   key_file_env="GENAPI_KEY_FILE", key_file="~/.config/genapi/api_key",
                   budget_env="GENAPI_BUDGET_TOTAL", budget_default=0.0, scope="genapi", default_path=None),
    "polza-chat": dict(base_env="POLZA_BASE_URL", base="https://polza.ai/api", key_env="POLZA_API_KEY",
                       key_file_env="POLZA_KEY_FILE", key_file="~/.config/polza/api_key",
                       budget_env="POLZA_BUDGET_TOTAL", budget_default=2000.0, scope="polza",
                       default_path="/api/v1/chat/completions"),
    "polza-images": dict(base_env="POLZA_BASE_URL", base="https://polza.ai/api", key_env="POLZA_API_KEY",
                         key_file_env="POLZA_KEY_FILE", key_file="~/.config/polza/api_key",
                         budget_env="POLZA_BUDGET_TOTAL", budget_default=2000.0, scope="polza",
                         default_path="/api/v2/images/generations"),
}
SCOPE_CHANNEL = {"routerai": "routerai", "genapi": "genapi", "polza": "polza-chat"}
CHANNEL_FROM_NAME = re.compile(r"\.(routerai|genapi|polza-chat|polza-images)\.jsonl?$")
SYNC_TIMEOUT = {"ra-image": 300.0, "ra-chat": 300.0, "chat": 300.0, "pz-image": 150.0, "ga-sync": 330.0}
TERMINAL = {
    "ra-video": ("completed", "failed", "cancelled", "expired"),
    "ga": ("success", "error", "failed", "cancelled"),
    "pz-media": ("completed", "failed", "cancelled"),
}

_print_lock = threading.Lock()
_SECRETS: set[str] = set()
SECRET_FIELDS = {"authorization", "x-api-key", "api_key", "apikey"}


# ---------------------------------------------------------------------------------------------------------------
# Секреты и вывод
# ---------------------------------------------------------------------------------------------------------------

def add_secret(k: str | None):
    if k and len(k) >= 6:
        _SECRETS.add(k)


def redact(s):
    if isinstance(s, str) and _SECRETS:
        for k in _SECRETS:
            if k in s:
                s = s.replace(k, "***")
    return s


def redact_obj(o):
    if isinstance(o, dict):
        return {k: ("***" if str(k).lower() in SECRET_FIELDS and isinstance(v, str) else redact_obj(v))
                for k, v in o.items()}
    if isinstance(o, list):
        return [redact_obj(x) for x in o]
    return redact(o)


def say(*parts, err=False):
    msg = " ".join(str(p) for p in parts)
    with _print_lock:
        print(redact(msg), file=sys.stderr if err else sys.stdout, flush=True)


def now_iso() -> str:
    return dt.datetime.now(pc.MSK).isoformat(timespec="seconds")


def jdump(o, indent=1) -> str:
    return json.dumps(o, ensure_ascii=False, indent=indent)


def fmt(x) -> str:
    return pc.fmt_rub(x)


def num(v):
    return pc.to_num(v)


def slug(s) -> str:
    return re.sub(r"[^\w.-]+", "-", str(s)).strip("-")[:60] or "x"


def rel(p) -> str:
    p = Path(p)
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def absp(p) -> Path:
    p = Path(p)
    return p if p.is_absolute() else ROOT / p


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def as_bool(v):
    if isinstance(v, bool):
        return v
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off", ""):
        return False
    return None


B64_CHARS = re.compile(r"^[A-Za-z0-9+/=_-]+$")


def shorten(o, key=None):
    """Копия для печати, журнала и паспорта: data:URI и длинный base64 заменены описанием (длина, sha256)."""
    if isinstance(o, dict):
        return {k: shorten(v, k) for k, v in o.items()}
    if isinstance(o, list):
        return [shorten(x, key) for x in o]
    if isinstance(o, str):
        if o.startswith("data:") and ";base64," in o[:200]:
            head, _, raw = o.partition(",")
            return f"<{head[5:]}: {len(raw)} симв., sha256 {sha256_hex(raw.encode())[:16]}…>"
        if len(o) > 256 and (key in ("b64_json", "base64", "data", "image_base64") or len(o) > 4096) \
                and B64_CHARS.match(o[:2048].replace("\n", "")):
            return f"<base64: {len(o)} симв., sha256 {sha256_hex(o.encode())[:16]}…>"
    return o


def sniff(b: bytes) -> tuple[str, str]:
    """Тип файла по сигнатуре: (mime, расширение). SVG — по корню <svg в начале текста."""
    if b.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg", ".jpg"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp", ".webp"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif", ".gif"
    if b[4:12] in (b"ftypavif", b"ftypavis"):
        return "image/avif", ".avif"
    if b[4:10] == b"ftypqt":
        return "video/quicktime", ".mov"
    if b[4:8] == b"ftyp":
        return "video/mp4", ".mp4"
    if b[:4] == b"\x1a\x45\xdf\xa3":
        return "video/webm", ".webm"
    if b[:4] == b"PK\x03\x04":
        return "application/zip", ".zip"
    if b[:4] == b"glTF":                                  # GLB (glTF 2.0, двоичный)
        return "model/gltf-binary", ".glb"
    head = b[:4096].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if head.startswith(b"<svg") or (head.startswith((b"<?xml", b"<!doctype svg", b"<!--")) and b"<svg" in head):
        return "image/svg+xml", ".svg"
    if head[:1] in (b"{", b"["):
        return "application/json", ".json"
    return "application/octet-stream", ".bin"


EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif", "image/avif": ".avif",
       "image/svg+xml": ".svg", "video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov",
       "application/zip": ".zip", "application/json": ".json", "model/gltf-binary": ".glb"}


def image_dims(data: bytes):
    try:
        from PIL import Image  # системный Pillow 11.3 (необязателен)
        with Image.open(io.BytesIO(data)) as im:
            return im.width, im.height
    except Exception:  # noqa: BLE001
        pass
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    return None, None


def ffprobe(path: Path) -> dict | None:
    prog = kbpaths.find("ffprobe", **kbpaths.BIN_LOOKUP["ffprobe"])
    if not prog:
        return None
    try:
        r = subprocess.run([prog, "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
                            str(path)], capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout or "{}")
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return None
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a_ = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    fps = None
    if v.get("avg_frame_rate") and v["avg_frame_rate"] != "0/0":
        n, _, dd = v["avg_frame_rate"].partition("/")
        fps = round(float(n) / float(dd or 1), 3)
    dur = d.get("format", {}).get("duration")
    return {"duration_s": round(float(dur), 3) if dur else None, "width": v.get("width"), "height": v.get("height"),
            "codec": v.get("codec_name"), "fps": fps, "has_audio": a_ is not None}


def image_info(path: Path) -> dict | None:
    try:
        from PIL import Image
        with Image.open(path) as im:
            info = {"width": im.width, "height": im.height, "mode": im.mode, "format": im.format,
                    "has_alpha": im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info}
            if im.mode in ("RGBA", "LA"):
                lo, hi = im.getchannel("A").getextrema()
                info["alpha_min"], info["alpha_used"] = lo, lo < 250
            return info
    except Exception:  # noqa: BLE001
        return None


def svg_info(data: bytes) -> dict:
    t = data.decode("utf-8", "replace")
    root = re.search(r"<svg\b[^>]*>", t)
    tag = root.group(0) if root else ""
    fills = set(re.findall(r"(?:fill|stroke)\s*[:=]\s*\"?(#[0-9a-fA-F]{3,8}|rgb\([^)]*\))", t))
    return {"root_svg": bool(root), "viewBox": (re.search(r'viewBox="([^"]+)"', tag) or [None, None])[1],
            "width": (re.search(r'\bwidth="([^"]+)"', tag) or [None, None])[1],
            "height": (re.search(r'\bheight="([^"]+)"', tag) or [None, None])[1],
            "paths": t.count("<path"), "colors": len(fills), "colors_list": sorted(fills)[:16],
            "has_text": "<text" in t, "has_image": "<image" in t, "recraft_signature": "recraft" in t.lower()}


def glb_info(data: bytes) -> dict:
    """Паспорт GLB: версия, генератор, расширения, меши, треугольники (по accessors), материалы, картинки."""
    import struct
    try:
        ver, _total = struct.unpack("<II", data[4:12])
        jlen = struct.unpack("<I", data[12:16])[0]
        js = json.loads(data[20:20 + jlen].decode("utf-8"))
    except (struct.error, UnicodeDecodeError, json.JSONDecodeError) as e:
        return {"glb_valid": False, "error": str(e)}
    acc = js.get("accessors", [])
    tris = 0
    for m in js.get("meshes", []):
        for pr in m.get("primitives", []):
            if pr.get("mode", 4) != 4:
                continue
            idx = pr.get("indices")
            n = acc[idx]["count"] if idx is not None else acc[pr.get("attributes", {}).get("POSITION", 0)]["count"]
            tris += n // 3
    mats = [{"metallic": (m.get("pbrMetallicRoughness") or {}).get("metallicFactor", 1.0),
             "roughness": (m.get("pbrMetallicRoughness") or {}).get("roughnessFactor", 1.0),
             "maps": sorted(k for k in list((m.get("pbrMetallicRoughness") or {}).keys()) + list(m.keys()) if k.endswith("Texture"))}
            for m in js.get("materials", [])]
    return {"glb_valid": True, "glb_version": ver, "generator": (js.get("asset") or {}).get("generator"),
            "extensions": js.get("extensionsUsed", []), "meshes": len(js.get("meshes", [])), "triangles": tris,
            "materials": mats, "images": [i.get("mimeType") for i in js.get("images", [])]}


def file_media(path: Path, mime: str) -> dict | None:
    if mime == "model/gltf-binary":
        return glb_info(path.read_bytes())
    if mime == "image/svg+xml":
        return svg_info(path.read_bytes())
    if mime.startswith("image/"):
        return image_info(path)
    if mime.startswith("video/"):
        return ffprobe(path)
    if mime == "application/json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
            return {"json_valid": True}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"json_valid": False}
    return None


# ---------------------------------------------------------------------------------------------------------------
# Токены: текст, картинки на вход, GPT Image на выход (порт калькулятора OpenAI)
# ---------------------------------------------------------------------------------------------------------------

def text_tokens(s: str) -> int:
    """Грубо: 4 символа ASCII или 2 символа кириллицы на токен [практика]."""
    if not s:
        return 0
    a = sum(1 for ch in s if ord(ch) < 128)
    return math.ceil(a / 4 + (len(s) - a) / 2)


def vision_tokens(model_id: str, w, h) -> tuple[int, int]:
    """Токены картинки на входе чат-модели: (ожидание, верх). Формулы вендоров; [не проверено] на polza."""
    mid = (model_id or "").lower()
    if not w or not h:
        return 1000, 1600
    if "gemini" in mid or mid.startswith("google/"):
        t = 258 if (w <= 384 and h <= 384) else math.ceil(w / 768) * math.ceil(h / 768) * 258
        return t, max(t, 1120)          # Gemini 3: media_resolution high ≈ 1120 на картинку
    if "claude" in mid or mid.startswith("anthropic/"):
        s = min(1.0, 1568 / max(w, h))
        t = math.ceil(w * s * h * s / 750)
        return t, t
    t = openai_image_tokens(w, h)
    return t, t


def openai_image_tokens(w, h) -> int:
    if not w or not h:
        return 765
    s = min(1.0, 2048 / max(w, h))
    w2, h2 = w * s, h * s
    s2 = min(1.0, 768 / min(w2, h2))
    w2, h2 = w2 * s2, h2 * s2
    return 85 + 170 * math.ceil(w2 / 512) * math.ceil(h2 / 512)


GPT_GRID = {"gpt-image-2": {"low": 16, "medium": 48, "high": 96},
            "gpt-image-2.5": {"low": 16, "medium": 24, "high": 48, "xhigh": 64, "max": 96}}
GPT1_TOKENS = {"low": 272, "medium": 1056, "high": 4160}      # gpt-image-1 / -mini, 1024², гайд OpenAI
GPT25_SIZES = {"1:1": (1024, 1024), "3:2": (1536, 1024), "2:3": (1024, 1536), "4:3": (1536, 1152),
               "3:4": (1152, 1536), "16:9": (1536, 864), "9:16": (864, 1536), "21:9": (1568, 672)}
GPT2_SIZES = {"1:1": (1024, 1024), "3:2": (1536, 1024), "2:3": (1024, 1536)}


def gpt_family(mid: str) -> str | None:
    if "gpt-image-2.5" in mid:
        return "gpt-image-2.5"
    if "gpt-image-2" in mid:
        return "gpt-image-2"
    if "gpt-image-1" in mid:
        return "gpt-image-1"
    return None


def _js_round(m: float) -> int:
    h = math.floor(m)
    if m - h == 0.5:
        return h + h % 2
    return math.floor(m + 0.5)


def gpt_image_tokens(family: str, w: int, h: int, q: str) -> int:
    """Выходные токены GPT Image 2 / 2.5 (формула калькулятора OpenAI)."""
    if family == "gpt-image-1":
        return math.ceil(GPT1_TOKENS[q] * (w * h) / (1024 * 1024))
    u, n = max(w, h), min(w, h)
    grid = GPT_GRID[family][q]
    d = _js_round(grid / (u / n))
    g = grid if w >= h else d
    o = d if w >= h else grid
    return math.ceil(g * o * (2e6 + w * h) / 4e6)


# ---------------------------------------------------------------------------------------------------------------
# Каталоги: RouterAI (+ эндпоинты OpenRouter), Gen-API (+ прайс), polza (polza_catalog.Snapshot)
# ---------------------------------------------------------------------------------------------------------------

def latest_file(sub: str, fname: str, ref: str | None = None) -> Path | None:
    if ref:
        p = Path(ref)
        if p.is_file():
            return p
        if p.is_dir() and (p / fname).exists():
            return p / fname
        q = CACHE / sub / ref / fname
        if q.exists():
            return q
        raise SystemExit(f"снимок не найден: {ref}")
    d = CACHE / sub
    if d.is_dir():      # временная папка снимка, который ещё качается (имя с точки), снимком не считается
        dirs = sorted(x for x in d.iterdir() if x.is_dir() and not x.name.startswith(".") and (x / fname).exists())
        if dirs:
            return dirs[-1] / fname
    return None


def snap_time(path: Path) -> str:
    meta = path.parent / "snapshot.meta.json"
    if meta.exists():
        try:
            t = json.loads(meta.read_text(encoding="utf-8")).get("fetched_at_msk")
            if t:
                return t
        except (OSError, json.JSONDecodeError):
            pass
    return dt.datetime.fromtimestamp(path.stat().st_mtime, pc.MSK).isoformat(timespec="seconds")


class RouterCatalog:
    def __init__(self, ref: str | None = None):
        path = latest_file("routerai", "api-v1-models.json", ref) or (P04 / "routerai_models.json")
        if not path.exists():
            raise SystemExit("нет снимка каталога RouterAI: python3 scripts/ai-media/mp_client.py snapshot --channel routerai")
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.models = {m["id"]: m for m in (raw["data"] if isinstance(raw, dict) else raw)}
        self.path, self.fetched = path, snap_time(path)
        self.endpoints = {}
        for f in sorted(CACHE.glob("openrouter-*/img_endpoints/*.json")):
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            j = j.get("data", j) if isinstance(j, dict) else {}
            if j.get("id"):
                self.endpoints[j["id"]] = {"endpoints": j.get("endpoints") or [], "source": rel(f)}

    @property
    def label(self) -> str:
        return f"каталог RouterAI {rel(self.path)} ({self.fetched})"

    def near(self, mid: str) -> list[str]:
        key = mid.split("/")[-1][:6]
        return [x for x in self.models if key and key in x][:8]

    def ep(self, mid: str) -> list[dict]:
        return (self.endpoints.get(mid) or {}).get("endpoints") or []

    def fx(self, mid: str) -> float:
        m = self.models.get(mid) or {}
        try:
            ra = float(((m.get("image_pricing") or [{}])[0]).get("price"))
            usd = next(float(p["cost_usd"]) for e in self.ep(mid) for p in e.get("pricing") or []
                       if p.get("billable") == "output_image")
            if usd > 0:
                return ra / usd
        except (StopIteration, TypeError, ValueError, KeyError):
            pass
        return FX_ROUTERAI_DEFAULT


def genapi_table(item: dict | None) -> list[dict]:
    """Таблица прайса Gen-API (data/genapi_prices_*.json): подписи в labels, значения по столбцам в rows → список
    вариантов."""
    if not item:
        return []
    labels, rows = item.get("labels") or [], item.get("rows") or []
    if not labels or len(labels) != len(rows):
        return []
    return [dict(zip(labels, vals)) for vals in zip(*rows)]


def rub_of(s) -> float | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*₽", str(s))
    return float(m.group(1).replace(",", ".")) if m else None


class GenapiCatalog:
    def __init__(self, ref: str | None = None):
        path = latest_file("genapi", "networks-include-parameters.json", ref)
        if path is None:
            raise SystemExit("нет снимка каталога Gen-API: python3 scripts/ai-media/mp_client.py snapshot --channel genapi")
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.nets = {n["slug"]: n for n in raw.get("data", [])}
        self.params = {s: {p["title"]: p for p in (n.get("parameters") or []) if p.get("title")}
                       for s, n in self.nets.items()}
        self.path, self.fetched = path, snap_time(path)
        self.prices, self.prices_src = {}, None
        pf = max(P04.glob("genapi_prices_*.json"), default=None)      # последний по дате в имени
        if pf is not None:
            for it in json.loads(pf.read_text(encoding="utf-8")):
                if isinstance(it, dict) and it.get("id"):
                    self.prices[it["id"]] = it
            self.prices_src = rel(pf)

    @property
    def label(self) -> str:
        return f"каталог Gen-API {rel(self.path)} ({self.fetched})"


# ---------------------------------------------------------------------------------------------------------------
# Журнал затрат — тот же файл и те же события, что у polza.py (append-only JSONL, события по uid)
# ---------------------------------------------------------------------------------------------------------------

class Ledger:
    KEEP = ("agent", "tag", "model", "base_url", "request_hash", "estimate_rub", "id", "files", "passport",
            "cost_rub", "operation", "parent_id", "channel", "path", "client")

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def append(self, ev: dict):
        ev = {"ts": now_iso(), "client": "mp_client", **ev}
        line = json.dumps(redact_obj(ev), ensure_ascii=False) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock, open(self.path, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(line)
            f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)

    def events(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for ln in self.path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
        return out

    def jobs(self) -> dict:
        """uid → сводка; правила траты — как у polza.py (completed — факт или оценка; неясное — резерв оценки)."""
        js = {}
        for e in self.events():
            uid = e.get("uid")
            if not uid:
                continue
            j = js.setdefault(uid, {"uid": uid, "events": 0})
            j["events"] += 1
            for k in self.KEEP:
                if e.get(k) is not None:
                    j[k] = e[k]
            j["state"] = e.get("event")
            j["ts"] = e.get("ts")
            if e.get("status") is not None:
                j["status"] = e["status"]
        for j in js.values():
            st = j.get("state")
            if st == "completed":
                j["spent"] = float(j.get("cost_rub") if j.get("cost_rub") is not None else j.get("estimate_rub") or 0)
            elif st in ("failed", "cancelled"):
                j["spent"] = float(j.get("cost_rub") or 0)
            elif st in ("http_error", "cache_hit", "upload", "rejected"):
                j["spent"] = 0.0
            else:       # submit / created / timeout / unknown — резерв по оценке
                j["spent"] = float(j.get("estimate_rub") or 0)
        return js

    def spent(self, base_url: str, agent: str | None = None) -> float:
        return round(sum(j["spent"] for j in self.jobs().values()
                         if j.get("base_url") == base_url and (agent is None or j.get("agent") == agent)), 6)

    def find_cached(self, request_hash: str, base_url: str):
        for j in reversed(list(self.jobs().values())):
            if j.get("request_hash") == request_hash and j.get("base_url") == base_url and j.get("state") == "completed":
                files = j.get("files") or []
                if files and all(absp(f).exists() for f in files):
                    return j
        return None

    def find_by_id(self, gen_id: str, base_url: str | None = None):
        for j in reversed(list(self.jobs().values())):
            if str(j.get("id")) == str(gen_id) and (base_url is None or j.get("base_url") == base_url):
                return j
        return None


# ---------------------------------------------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------------------------------------------

class ApiError(Exception):
    def __init__(self, status, code, message, body=None, headers=None, ambiguous=False):
        super().__init__(f"HTTP {status} {code}: {message}")
        self.status, self.code, self.message, self.body, self.headers = status, code, message, body, headers or {}
        self.ambiguous = ambiguous      # запрос мог быть принят (сеть оборвалась после отправки)


class Resp:
    def __init__(self, status, headers, body: bytes):
        self.status, self.headers, self.body = status, {k.lower(): v for k, v in headers.items()}, body
        try:
            self.json = json.loads(body.decode("utf-8")) if body else None
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.json = None


def err_info(status: int, resp: Resp) -> tuple[str, str]:
    """Код и текст ошибки в формах трёх каналов: polza/OpenRouter {error:{code,message}}, Gen-API {error: str} и
    {error: true, errors_validation: {...}}, {message}."""
    j = resp.json
    code, msg = f"HTTP_{status}", resp.body[:300].decode("utf-8", "replace")
    if isinstance(j, dict):
        e = j.get("error")
        if isinstance(e, dict):
            code = str(e.get("code") or e.get("type") or code)
            msg = str(e.get("message") or jdump(e, None)[:300])
        elif isinstance(e, str):
            msg = e
        elif e is True and j.get("errors_validation") is not None:
            code, msg = "VALIDATION", jdump(j.get("errors_validation"), None)[:600]
        elif j.get("message"):
            msg = str(j["message"])
    return code, msg


def origin(url: str) -> str:
    u = urllib.parse.urlsplit(url)
    return f"{u.scheme}://{u.netloc}".lower()


class Http:
    def __init__(self, channel: str, base: str, key_getter, live: bool, timeout: float = 60.0, curl: bool = False):
        self.channel, self.base = channel, base.rstrip("/")
        self.key_getter, self.live, self.timeout, self.curl = key_getter, live, timeout, curl
        self.env = CHANNELS[channel]["key_env"]

    def url(self, api_path: str) -> str:
        return self.base + api_path

    def same_origin(self, url: str) -> bool:
        return origin(url) == origin(self.base)

    def show(self, method: str, url: str, body=None, note: str | None = None, auth: bool = True):
        say(f"{method} {url}")
        if auth:
            say(f"Authorization: Bearer ${self.env}   # ключ не читается и не печатается")
        if body is not None:
            say("Content-Type: application/json")
            say("")
            say(jdump(shorten(body)))
        if note:
            say(note)
        if self.curl and body is not None:
            say("\n# то же через curl (ключ из переменной окружения; base64 в печати сокращён):")
            say(f"curl -sS -X {method} '{url}' -H \"Authorization: Bearer ${self.env}\" "
                f"-H 'Content-Type: application/json' --data @- <<'JSON'\n{jdump(shorten(body), None)}\nJSON")

    def request(self, method: str, url: str, *, body=None, timeout=None, retries=None, auth=True,
                retry_429_base: float = 2.0) -> Resp:
        if not self.live:
            raise RuntimeError("сеть без --live запрещена")
        key = None
        if auth and self.same_origin(url):
            key = self.key_getter()
            if not key:
                raise ApiError(0, "NO_KEY", f"ключ канала {self.channel} не найден: {self.env} или "
                                            f"{CHANNELS[self.channel]['key_file']}")
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        is_get = method == "GET"
        n_try = retries if retries is not None else (5 if is_get else 4)
        delay = retry_429_base if not is_get else 2.0
        for attempt in range(1, n_try + 1):
            req = urllib.request.Request(url, data=data, method=method,
                                         headers={"Accept": "application/json", "User-Agent": VERSION})
            if data is not None:
                req.add_header("Content-Type", "application/json")
            if key:
                req.add_unredirected_header("Authorization", f"Bearer {key}")   # не переносится при редиректе
            try:
                with urllib.request.urlopen(req, timeout=timeout or self.timeout) as r:
                    return Resp(r.status, dict(r.headers.items()), r.read())
            except urllib.error.HTTPError as e:
                resp = Resp(e.code, dict(e.headers.items()) if e.headers else {}, e.read() or b"")
                code, msg = err_info(e.code, resp)
                retryable = e.code == 429 or (is_get and e.code in (500, 502, 503, 504))
                if retryable and attempt < n_try:
                    wait = self._retry_after(resp.headers, delay)
                    say(f"  … {self.channel}: {e.code} {code}: повтор через {wait:.1f} с (попытка {attempt + 1}/{n_try})",
                        err=True)
                    time.sleep(wait)
                    delay = min(delay * 2, 60)
                    continue
                raise ApiError(e.code, code, msg, resp.json if resp.json is not None else resp.body[:2000].decode(
                    "utf-8", "replace"), resp.headers)
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                if is_get and attempt < n_try:
                    say(f"  … {self.channel}: сеть: {e}; повтор через {delay:.0f} с", err=True)
                    time.sleep(delay)
                    delay = min(delay * 2, 30)
                    continue
                # POST: запрос мог дойти до сервера — повторять нельзя (двойное списание)
                raise ApiError(0, "NETWORK", str(e), ambiguous=not is_get)
        raise ApiError(0, "RETRIES", "исчерпаны попытки")

    @staticmethod
    def _retry_after(h: dict, fallback: float) -> float:
        for k in ("retry-after", "x-ratelimit-reset"):
            v = h.get(k)
            if v:
                try:
                    return max(0.5, min(float(v), 60.0))
                except ValueError:
                    pass
        return fallback

    def download(self, url: str, dest_base: Path, *, auth: bool = False, timeout: float = 300, tries: int = 3) -> dict:
        """Скачать в <dest_base><расширение по сигнатуре>. Ключ — только своему хосту и только если auth.
        Атомарная запись через .part; 403/404/410 не повторяются (истёк срок хранения)."""
        last = None
        key = self.key_getter() if (auth and self.same_origin(url)) else None
        for attempt in range(1, tries + 1):
            tmp = dest_base.with_name(dest_base.name + ".part")
            h = hashlib.sha256()
            try:
                req = urllib.request.Request(url, headers={"User-Agent": VERSION})
                if key:
                    req.add_unredirected_header("Authorization", f"Bearer {key}")
                n, first = 0, b""
                with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
                    ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip()
                    while True:
                        chunk = r.read(1 << 16)
                        if not chunk:
                            break
                        if len(first) < 4096:
                            first += chunk[:4096 - len(first)]
                        f.write(chunk)
                        h.update(chunk)
                        n += len(chunk)
                mime, ext = sniff(first)
                if mime == "application/octet-stream" and ctype in EXT:
                    mime, ext = ctype, EXT[ctype]
                dest = dest_base.with_name(dest_base.name + ext)
                tmp.replace(dest)
                return {"path": rel(dest), "url": url, "bytes": n, "sha256": h.hexdigest(), "content_type": mime,
                        "http_content_type": ctype, "media": file_media(dest, mime)}
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}"
                if e.code in (401, 403, 404, 410):
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last = str(e)
            finally:
                if tmp.exists():
                    tmp.unlink(missing_ok=True)
            time.sleep(2 * attempt)
        raise ApiError(0, "DOWNLOAD", f"не удалось скачать {url}: {last}")


def save_bytes(dest_base: Path, data: bytes, source: str, hint_mime: str | None = None) -> dict:
    mime, ext = sniff(data)
    if mime in ("application/octet-stream", "application/json") and hint_mime in EXT:
        mime, ext = hint_mime, EXT[hint_mime]
    dest = dest_base.with_name(dest_base.name + ext)
    tmp = dest.with_name(dest.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return {"path": rel(dest), "source": source, "bytes": len(data), "sha256": sha256_hex(data), "content_type": mime,
            "media_type_declared": hint_mime, "media": file_media(dest, mime)}


# ---------------------------------------------------------------------------------------------------------------
# Контекст
# ---------------------------------------------------------------------------------------------------------------

def norm_base(b: str) -> str:
    b = b.rstrip("/")
    return b if b.endswith("/api") else b + "/api"


def api_path(path) -> str:
    p = "/" + str(path or "").lstrip("/")
    return p[4:] if p.startswith("/api/") else p


class Ctx:
    def __init__(self, a):
        self.a = a
        self.live = bool(getattr(a, "live", False))
        self._bases = {"routerai": getattr(a, "routerai_base", None), "genapi": getattr(a, "genapi_base", None),
                       "polza-chat": getattr(a, "polza_base", None), "polza-images": getattr(a, "polza_base", None)}
        self.ledger = Ledger(Path(a.ledger or os.environ.get("MP_LEDGER") or os.environ.get("POLZA_LEDGER")
                                  or DEFAULT_LEDGER))
        self.out_root = Path(a.out or os.environ.get("MP_OUT_ROOT") or DEFAULT_OUT_ROOT)
        self.max_job = float(a.max_job if a.max_job is not None else os.environ.get("MP_MAX_JOB", 60))
        ba = a.budget_agent if a.budget_agent is not None else os.environ.get("MP_BUDGET_AGENT")
        self.budget_agent = float(ba) if ba not in (None, "") else None
        self.default_agent = a.agent or os.environ.get("MP_AGENT") or "unknown"
        self.set_values = {}
        for kv in a.set or []:
            k, _, v = kv.partition("=")
            self.set_values[k.strip()] = v
        for kv in a.set_file or []:
            k, _, v = kv.partition("=")
            self.set_values[k.strip()] = Path(v).expanduser().read_text(encoding="utf-8")
        self._ra = self._ga = self._pz = None
        self._keys: dict[str, str | None] = {}
        self._key_lock = threading.Lock()
        self._budget_lock = threading.Lock()
        self._preflight_done: set[str] = set()
        self.stop = {"routerai": threading.Event(), "genapi": threading.Event(), "polza": threading.Event()}

    # каталоги лениво: estimate одного канала не требует снимков остальных
    @property
    def ra(self) -> RouterCatalog:
        if self._ra is None:
            self._ra = RouterCatalog(getattr(self.a, "routerai_catalog", None))
        return self._ra

    @property
    def ga(self) -> GenapiCatalog:
        if self._ga is None:
            self._ga = GenapiCatalog(getattr(self.a, "genapi_catalog", None))
        return self._ga

    @property
    def pz(self):
        if self._pz is None:
            self._pz = pc.Snapshot(getattr(self.a, "polza_catalog", None) or os.environ.get("POLZA_CATALOG"))
        return self._pz

    def base(self, ch: str) -> str:
        c = CHANNELS[ch]
        return norm_base(self._bases.get(ch) or os.environ.get(c["base_env"]) or c["base"])

    def budget_total(self, ch: str) -> float:
        if self.a.budget_total is not None:
            return float(self.a.budget_total)
        c = CHANNELS[ch]
        v = os.environ.get(c["budget_env"])
        return float(v) if v not in (None, "") else float(c["budget_default"])

    def key_status(self, ch: str) -> str:
        c = CHANNELS[ch]
        if os.environ.get(c["key_env"]):
            return f"в окружении {c['key_env']}"
        kf = Path(os.environ.get(c["key_file_env"]) or c["key_file"]).expanduser()
        if kf.exists():
            mode = kf.stat().st_mode & 0o777
            return f"файл {kf} (права {oct(mode)}{', НЕ 600' if mode & 0o077 else ''})"
        return "не найден"

    def key(self, ch: str, read: bool = False) -> str | None:
        """Ключ канала — только при --live или для чтения без траты (read: баланс) и только по запросу к своему хосту.
        Значение нигде не печатается."""
        if not self.live and not read:
            return None
        c = CHANNELS[ch]
        scope = c["scope"]
        with self._key_lock:
            if scope in self._keys:
                return self._keys[scope]
            k = os.environ.get(c["key_env"])
            if not k:
                kf = Path(os.environ.get(c["key_file_env"]) or c["key_file"]).expanduser()
                if kf.exists():
                    mode = kf.stat().st_mode & 0o777
                    if mode & 0o077:
                        say(f"! файл ключа {kf} доступен не только владельцу (права {oct(mode)}): chmod 600", err=True)
                    k = kf.read_text().strip()
            add_secret(k)
            self._keys[scope] = k or None
            return self._keys[scope]

    def http(self, ch: str, read: bool = False) -> Http:
        """Канал запросов; read — канал чтения без траты (баланс): запрос с ключом идёт и без --live."""
        return Http(ch, self.base(ch), lambda: self.key(ch, read), self.live or read, timeout=self.a.http_timeout,
                    curl=getattr(self.a, "curl", False))


# ---------------------------------------------------------------------------------------------------------------
# Задания: загрузка, шаблоны, файлы
# ---------------------------------------------------------------------------------------------------------------

def load_jobs(path: str) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        raise SystemExit(f"нет файла задания {path}")
    text = p.read_text(encoding="utf-8")
    if p.suffix == ".jsonl":
        jobs = []
        for i, ln in enumerate(text.splitlines(), 1):
            s = ln.strip()
            if not s or s.startswith("#") or s.startswith("//"):
                continue
            try:
                jobs.append(json.loads(s))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{i}: не JSON: {e}")
    else:
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as e:
            raise SystemExit(f"{path}: не JSON: {e}")
        jobs = obj if isinstance(obj, list) else [obj]
    m = CHANNEL_FROM_NAME.search(p.name)
    out = []
    for i, j in enumerate(jobs, 1):
        if not isinstance(j, dict):
            raise SystemExit(f"{path}: элемент {i} — не объект")
        j = dict(j)
        j["_file"], j["_index"], j["_dir"] = rel(p), i, str(p.resolve().parent)
        if m:
            if not j.get("channel"):
                j["channel"] = m.group(1)
                j["_channel_from_name"] = True
            elif j["channel"] != m.group(1):
                j["_channel_mismatch"] = m.group(1)
        out.append(j)
    return out


def pick_jobs(jobs: list[dict], pick: str | None) -> list[dict]:
    if not pick:
        return jobs
    if pick.startswith("/") and pick.endswith("/") and len(pick) > 2:
        rx = re.compile(pick[1:-1])
        return [j for j in jobs if rx.search(str(j.get("tag") or ""))]
    if pick.isdigit():
        return [j for j in jobs if j["_index"] == int(pick)]
    return [j for j in jobs if str(j.get("tag")) == pick]


TPL_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")
ANGLE_RE = re.compile(r"^\s*<[^<>]{1,200}>\s*$")


def fill_templates(obj, values: dict):
    used, missing = set(), set()

    def rep(mm):
        name = mm.group(1)
        if name in values:
            used.add(name)
            return values[name]
        missing.add(name)
        return mm.group(0)

    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(x) for x in o]
        if isinstance(o, str) and "{{" in o:
            return TPL_RE.sub(rep, o)
        return o

    return walk(obj), used, missing


def canon(o):
    """Для хэша запроса: data:URI заменён sha256 содержимого — локальный путь и тот же файл в base64 равны."""
    if isinstance(o, dict):
        return {k: canon(v) for k, v in o.items()}
    if isinstance(o, list):
        return [canon(x) for x in o]
    if isinstance(o, str) and o.startswith("data:") and "," in o[:200]:
        return "sha256:" + sha256_hex(o.partition(",")[2].encode())
    return o


class Prepared:
    def __init__(self, job: dict, ctx: Ctx):
        self.job = job
        self.channel = str(job.get("channel") or "")
        self.scope = CHANNELS.get(self.channel, {}).get("scope")
        self.kind = None
        self.method = str(job.get("method") or "POST").upper()
        self.api_path = None
        self.body: dict = {}
        self.model = None           # id модели или slug сети Gen-API
        self.minfo = None           # запись каталога
        self.issues: list[dict] = []
        self.filled: list[str] = []
        self.files: list[dict] = []
        self.templates: list[str] = []
        self.estimate = {"rub": None, "rub_low": None, "rub_high": None, "formula": "", "warnings": [], "source": ""}
        self.request_hash = ""
        self.uid = uuid.uuid4().hex[:12]
        self.agent = str(job.get("agent") or ctx.default_agent)
        self.tag = slug(job.get("tag") or f"{Path(str(job.get('_file') or 'job')).stem}-{job.get('_index', 1)}")

    def add(self, level: str, param: str, msg: str):
        self.issues.append({"level": level, "param": param, "msg": msg})

    @property
    def errors(self):
        return [i for i in self.issues if i["level"] == "error"]

    @property
    def label(self) -> str:
        return f"{self.tag}·{self.channel}"


def resolve_media(prep: Prepared, value, where: str, exts: tuple[str, ...] | None = None):
    """URL и data:URI — как есть; «<…>» — шаблон; локальный путь (от файла задания) → data:URI base64."""
    if not isinstance(value, str):
        prep.add("error", where, f"ожидалась строка (URL, data:URI или путь), получено {type(value).__name__}")
        return value
    s = value.strip()
    if s.startswith(("http://", "https://")):
        prep.files.append({"where": where, "url": s})
        return s
    if s.startswith("data:"):
        raw = s.partition(",")[2]
        prep.files.append({"where": where, "data_uri": True, "chars": len(raw), "sha256": sha256_hex(raw.encode())})
        return s
    if ANGLE_RE.match(s) or TPL_RE.search(s):
        prep.templates.append(f"{where} = {s}")
        return s
    p = Path(s).expanduser()
    if not p.is_absolute():
        p = Path(prep.job.get("_dir", ".")) / p
    if not p.exists():
        prep.add("error", where, f"файл не найден: {s}")
        return s
    data = p.read_bytes()
    mime, ext = sniff(data)
    if mime == "application/octet-stream":
        mime = mimetypes.guess_type(p.name)[0] or mime
    if exts and ext.lstrip(".") not in exts and p.suffix.lower().lstrip(".") not in exts:
        prep.add("error", where, f"тип {mime} ({p.name}) не из допустимых: {', '.join(exts)}")
    if len(data) > INLINE_MAX:
        prep.add("error", where, f"файл {len(data)} байт > {INLINE_MAX} — дайте публичный URL")
    elif len(data) > INLINE_WARN:
        prep.add("warn", where, f"файл {len(data) // 1024} КБ уходит base64 в теле (+33 %) — тяжёлый запрос")
    w, h = image_dims(data) if mime.startswith("image/") else (None, None)
    prep.files.append({"where": where, "src": rel(p), "bytes": len(data), "sha256": sha256_hex(data), "mime": mime,
                       "w": w, "h": h})
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def notes_mention(job: dict, words) -> bool:
    t = (str(job.get("notes") or "") + " " + json.dumps(job.get("meta") or {}, ensure_ascii=False)).lower()
    return any(w.lower() in t for w in words)


# ---------------------------------------------------------------------------------------------------------------
# RouterAI: картинки, видео, чат
# ---------------------------------------------------------------------------------------------------------------

RA_IMAGE_DOC = {"model", "prompt", "n", "aspect_ratio", "resolution", "size", "quality", "background", "output_format",
                "output_compression", "seed", "input_references", "mask", "input_fidelity", "stream", "user", "provider"}
RA_VIDEO_DOC = {"model", "prompt", "duration", "resolution", "aspect_ratio", "size", "frame_images", "input_references",
                "seed", "generate_audio", "negative_prompt", "callback_url", "provider"}
RA_TIERS_MP = {"512": 0.25, "1K": 1.0, "2K": 4.0, "4K": 16.0}
PROVIDER_KEYS = {"only", "order", "ignore", "sort", "allow_fallbacks", "options", "max_price", "require_parameters",
                 "data_collection"}
PASSTHROUGH_WORDS = ("passthrough", "не документ", "гипотез", "доходит", "пропускает")


def check_provider(ctx: Ctx, prep: Prepared, prov):
    if not isinstance(prov, dict):
        prep.add("error", "provider", "должен быть объектом")
        return
    for k in prov:
        if k not in PROVIDER_KEYS:
            prep.add("warn", f"provider.{k}", "поле не из документации OpenRouter (only/order/ignore/sort/"
                                              "allow_fallbacks/options)")
    opts = prov.get("options")
    if opts is None:
        return
    if not isinstance(opts, dict):
        prep.add("error", "provider.options", "должен быть объектом {slug провайдера: {параметры}}")
        return
    eps = ctx.ra.ep(prep.model) if prep.channel == "routerai" else []
    slugs = {e.get("provider_slug"): e for e in eps}
    for sl, params in opts.items():
        where = f"provider.options.{sl}"
        if not isinstance(params, dict):
            prep.add("error", where, "должен быть объектом параметров")
            continue
        e = slugs.get(sl)
        if eps and e is None:
            prep.add("warn", where, f"slug не из эндпоинтов OpenRouter для {prep.model}: {sorted(slugs)}")
        allowed = set((e or {}).get("allowed_passthrough_parameters") or [])
        for k in params:
            if e is not None and k not in allowed:
                prep.add("warn", f"{where}.{k}", f"нет в allowed_passthrough_parameters OpenRouter ({sorted(allowed)})")
        prep.add("info", where, f"passthrough {sorted(params)}: у RouterAI для /api/v1/images не документирован "
                                f"(документирован у OpenRouter) — гипотеза теста")
        if not notes_mention(prep.job, PASSTHROUGH_WORDS + tuple(params)):
            prep.add("warn", where, "в notes нет гипотезы про passthrough — допишите, что это проверка неизвестного")


def prep_ra_image(ctx: Ctx, prep: Prepared, body: dict):
    prep.kind = "ra-image"
    mid = body.get("model")
    prep.model = mid
    m = ctx.ra.models.get(mid) if isinstance(mid, str) else None
    prep.estimate["source"] = ctx.ra.label
    if m is None:
        if prep.templates or (isinstance(mid, str) and TPL_RE.search(mid)):
            return
        prep.add("error", "model", f"нет в {ctx.ra.label}; похожие: {ctx.ra.near(str(mid))}")
        return
    prep.minfo = m
    arch = m.get("architecture") or {}
    outs = arch.get("output_modalities") or []
    if "image" not in outs:
        prep.add("error", "model", f"у модели нет выхода image ({outs}) — не для /api/v1/images")
    elif "text" in outs:
        prep.add("error", "model", "диалоговая модель (выход text+image): RouterAI документирует её через "
                                   "/api/v1/chat/completions с modalities и image_config")
    sup = set(m.get("supported_parameters") or [])
    fam = gpt_family(mid)
    for k, v in body.items():
        if k in ("model", "prompt", "provider"):
            continue
        if k not in RA_IMAGE_DOC:
            prep.add("warn", k, "не документирован в /api/v1/images RouterAI — провайдерный параметр в корне тела "
                                "(гипотеза passthrough)")
            if not notes_mention(prep.job, PASSTHROUGH_WORDS + (k,)):
                prep.add("warn", k, "в notes нет гипотезы про этот параметр — допишите")
        elif k not in sup and k not in ("user", "stream", "resolution", "size", "mask", "input_fidelity"):
            prep.add("warn", k, f"нет в supported_parameters модели ({sorted(sup)}) — по документации RouterAI "
                                f"неподдерживаемое игнорируется или нормализуется")
    refs = body.get("input_references")
    if not body.get("prompt") and not refs:
        prep.add("error", "prompt", "обязателен без input_references")
    n = body.get("n", 1)
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        prep.add("error", "n", f"целое ≥ 1, получено {n!r}")
    elif m.get("max_image_count") and n > int(m["max_image_count"]):
        prep.add("error", "n", f"{n} > max_image_count {m['max_image_count']} (одиночные провайдеры отклоняют n > 1)")
    ar = body.get("aspect_ratio")
    if ar is not None and m.get("supported_aspect_ratios") and ar not in m["supported_aspect_ratios"]:
        prep.add("warn", "aspect_ratio", f"{ar!r} нет в {m['supported_aspect_ratios']} — провайдер приведёт к ближайшему")
    res = body.get("resolution")
    if res is not None and str(res) not in RA_TIERS_MP:
        prep.add("error", "resolution", f"{res!r} не из 512/1K/2K/4K")
    size = body.get("size")
    if size is not None:
        if not (isinstance(size, str) and re.fullmatch(r"\d+x\d+", size)):
            prep.add("error", "size", f"формат ШИРИНАxВЫСОТА, получено {size!r}")
        elif fam == "gpt-image-2.5":
            w, h = map(int, size.split("x"))
            if w % 16 or h % 16 or max(w, h) > 3840 or max(w, h) / min(w, h) > 3:
                prep.add("error", "size", "GPT Image 2.5: стороны кратны 16, ≤ 3840, соотношение от 1:3 до 3:1")
    q = body.get("quality")
    if q is not None and m.get("supported_qualities") and q not in m["supported_qualities"]:
        prep.add("warn", "quality", f"{q!r} нет в {m['supported_qualities']}")
    bg = body.get("background")
    if bg is not None:
        if bg not in ("auto", "transparent", "opaque"):
            prep.add("error", "background", f"{bg!r} не из auto/transparent/opaque")
        elif m.get("supported_backgrounds") and bg not in m["supported_backgrounds"]:
            prep.add("warn", "background", f"{bg!r} нет в {m['supported_backgrounds']} — будет проигнорирован")
        if bg == "transparent" and body.get("output_format") == "jpeg":
            prep.add("error", "background", "transparent требует png или webp (документация)")
    of = body.get("output_format")
    if of is not None:
        if of not in ("png", "jpeg", "webp", "svg"):
            prep.add("error", "output_format", f"{of!r} не из png/jpeg/webp/svg")
        elif m.get("supported_output_formats") and of not in m["supported_output_formats"]:
            prep.add("warn", "output_format", f"{of!r} нет в {m['supported_output_formats']}")
    oc = body.get("output_compression")
    if oc is not None and not (isinstance(oc, int) and 0 <= oc <= 100):
        prep.add("error", "output_compression", "целое 0–100")
    if body.get("seed") is not None and m.get("image_seed") is False:
        prep.add("warn", "seed", "у модели image_seed=false (каталог) — seed не повторит результат")
    if refs is not None:
        if not isinstance(refs, list):
            prep.add("error", "input_references", "должен быть массивом")
        else:
            mx = m.get("max_image_references")
            if mx is not None and len(refs) > int(mx):
                prep.add("error", "input_references", f"{len(refs)} > max_image_references {mx}")
            for i, it in enumerate(refs):
                where = f"input_references[{i}]"
                if not (isinstance(it, dict) and it.get("type") == "image_url" and isinstance(it.get("image_url"), dict)):
                    prep.add("error", where, "формат по документации RouterAI: {\"type\": \"image_url\", \"image_url\": "
                                             "{\"url\": \"…\"}} (URL или data URI)")
                    continue
                it["image_url"]["url"] = resolve_media(prep, it["image_url"].get("url"), where + ".image_url.url")
    mask = body.get("mask")
    if mask is not None:
        if isinstance(mask, dict) and isinstance(mask.get("image_url"), dict):
            mask["image_url"]["url"] = resolve_media(prep, mask["image_url"].get("url"), "mask.image_url.url")
        elif isinstance(mask, str):
            body["mask"] = resolve_media(prep, mask, "mask")
        else:
            prep.add("error", "mask", "строка URL или объект {\"image_url\": {\"url\": …}}")
        if not refs:
            prep.add("error", "mask", "работает только вместе с input_references (без исходника игнорируется)")
        if not mid.startswith("openai/gpt-image"):
            prep.add("warn", "mask", "маску принимают только openai/gpt-image-* — будет проигнорирована")
    if body.get("input_fidelity") is not None:
        if "gpt-image-2" in mid:
            prep.add("error", "input_fidelity", "gpt-image-2 отвечает ошибкой invalid_input_fidelity_model (документация)")
        elif fam != "gpt-image-1":
            prep.add("warn", "input_fidelity", "только gpt-image-1 / -mini")
    if body.get("stream"):
        prep.add("error", "stream", "потоковый режим (SSE) клиент не поддерживает — уберите stream")
    if body.get("provider") is not None:
        check_provider(ctx, prep, body["provider"])
    ra_image_price(ctx, prep, m, body)


def ra_megapixels(body: dict) -> tuple[float, float, str]:
    size = body.get("size")
    if isinstance(size, str) and re.fullmatch(r"\d+x\d+", size):
        w, h = map(int, size.split("x"))
        mp = w * h / MP_PX
        return mp, mp, f"{size}"
    tier = str(body.get("resolution") or "1K")
    base = RA_TIERS_MP.get(tier, 1.0)
    return base, base * 1.1, f"тир {tier}; кадр выбирает провайдер — верх +10 %"


def ra_input_prices(ctx: Ctx, m: dict) -> tuple[float, float, str]:
    """₽ за входной токен текста и картинки: из каталога RouterAI, иначе из эндпоинтов OpenRouter × курс."""
    pr = m.get("pricing") or {}
    p_text, p_img = num(pr.get("prompt")), num(pr.get("image"))
    if p_text:
        return float(p_text), float(p_img or p_text), "каталог RouterAI (prompt)"
    fx = ctx.ra.fx(m["id"])
    lines = {p.get("billable"): p for e in ctx.ra.ep(m["id"]) for p in e.get("pricing") or [] if p.get("unit") == "token"}
    t = num((lines.get("input_text") or {}).get("cost_usd"))
    i = num((lines.get("input_image") or {}).get("cost_usd"))
    if t or i:
        return float(t or 0) * fx, float(i or t or 0) * fx, f"OpenRouter endpoints × {fx:.3f} ₽/$"
    return 0.0, 0.0, "цены входа нет — не учтён"


def ra_image_price(ctx: Ctx, prep: Prepared, m: dict, body: dict):
    e, W = prep.estimate, prep.estimate["warnings"]
    ip = (m.get("image_pricing") or [{}])[0]
    unit, price = ip.get("unit"), num(ip.get("price"))
    if price is None:
        pr = m.get("pricing") or {}
        price = num(pr.get("image_output"))
        unit = unit or (m.get("pricing_units") or {}).get("image_output")
    n = body.get("n", 1) if isinstance(body.get("n", 1), int) else 1
    mid = m["id"]
    refs = body.get("input_references") or []
    extra, extra_f = 0.0, ""
    if refs:
        lines = [p for x in ctx.ra.ep(mid) for p in x.get("pricing") or []
                 if p.get("billable") == "input_reference" and p.get("unit") == "request"]
        fx = ctx.ra.fx(mid)
        if lines:
            usd = float(lines[0]["cost_usd"])
            extra, extra_f = usd * fx, f" + {fmt(usd * fx)} ₽ за референс-стиль (OpenRouter ${usd} × {fx:.3f})"
        elif "styles" in mid:
            extra = RECRAFT_STYLES_REF_USD * fx
            extra_f = f" + {fmt(extra)} ₽ за референс-стиль (по аналогии с recraft-v4-styles-vector [не проверено])"
    if unit == "image" and price is not None:
        rub = float(price) * n + extra
        e.update(rub=rub, rub_low=rub, rub_high=rub, formula=f"{fmt(price)} ₽ за картинку × {n}{extra_f}")
    elif unit == "megapixel" and price is not None:
        mp, mp_hi, note = ra_megapixels(body)
        rub, hi = float(price) * mp * n, float(price) * mp_hi * n
        e.update(rub=rub, rub_low=rub, rub_high=hi, formula=f"{fmt(price)} ₽/Мп × {mp:.2f} Мп ({note}) × {n}")
        if refs:
            W.append("входные картинки у BFL тарифицируются отдельно (FLUX.2 [pro]: правка «from $0,045»), в каталоге "
                     "RouterAI строки нет — [не проверено]")
    elif unit == "token" and price is not None:
        gpt_image_price(ctx, prep, m, body, float(price), n)
    else:
        W.append(f"единица цены {unit!r} не поддерживается оценкой")


def gpt_image_price(ctx: Ctx, prep: Prepared, m: dict, body: dict, out_price: float, n: int):
    e, W = prep.estimate, prep.estimate["warnings"]
    mid = m["id"]
    fam = gpt_family(mid)
    if fam is None:
        W.append(f"{mid}: цена за токен, но число выходных токенов неизвестно — оценки нет")
        return
    q = str(body.get("quality") or "auto")
    grid = GPT1_TOKENS if fam == "gpt-image-1" else GPT_GRID[fam]
    if q in grid:
        q_exp = q_hi = q
    else:
        q_exp, q_hi = "medium", "high"
        W.append(f"quality {q!r}: модель выбирает сама — оценка по medium, лимит по high; задайте quality явно")
    size, ar = body.get("size"), str(body.get("aspect_ratio") or "auto")
    if isinstance(size, str) and re.fullmatch(r"\d+x\d+", size):
        w, h = map(int, size.split("x"))
        size_note = size
    else:
        table = GPT25_SIZES if fam == "gpt-image-2.5" else GPT2_SIZES
        if ar in table:
            w, h = table[ar]
            size_note = f"{ar} → {w}×{h}"
        else:
            ref = next((f for f in prep.files if f.get("w")), None)
            w, h = (ref["w"], ref["h"]) if ref else (1024, 1024)
            if (w, h) not in table.values():
                w, h = 1024, 1024
            size_note = f"aspect {ar} → оценка по {w}×{h}"
    t_exp = gpt_image_tokens(fam, w, h, q_exp) * n
    t_hi = gpt_image_tokens(fam, w, h, q_hi) * n
    p_text, p_img, src = ra_input_prices(ctx, m)
    t_text = text_tokens(str(body.get("prompt") or ""))
    t_refs = sum(openai_image_tokens(f.get("w"), f.get("h")) for f in prep.files
                 if str(f.get("where", "")).startswith("input_references"))
    t_mask = sum(openai_image_tokens(f.get("w"), f.get("h")) for f in prep.files if str(f.get("where", "")).startswith("mask"))
    inp_lo = t_text * p_text + t_refs * p_img
    inp_hi = t_text * p_text + (2 * t_refs + t_mask) * p_img
    rub, hi = t_exp * out_price + inp_lo, t_hi * out_price + inp_hi
    e.update(rub=rub, rub_low=rub, rub_high=hi,
             formula=(f"{t_exp} вых. ток. ({fam} {q_exp}, {size_note}) × {out_price:.7f} ₽ + вход ≈ {fmt(inp_lo)} ₽ "
                      f"({t_text} ток. текста, {t_refs} ток. референсов; {src})"))
    if t_refs or t_mask:
        W.append("токены входных картинок — по формуле vision OpenAI; у gpt-image-2 вход всегда «high fidelity» — "
                 "верх ×2 и маска [не проверено]")


def prep_ra_video(ctx: Ctx, prep: Prepared, body: dict):
    prep.kind = "ra-video"
    mid = body.get("model")
    prep.model = mid
    m = ctx.ra.models.get(mid) if isinstance(mid, str) else None
    prep.estimate["source"] = ctx.ra.label
    if m is None:
        if not prep.templates:
            prep.add("error", "model", f"нет в {ctx.ra.label}; похожие: {ctx.ra.near(str(mid))}")
        return
    prep.minfo = m
    if "video" not in ((m.get("architecture") or {}).get("output_modalities") or []):
        prep.add("error", "model", "у модели нет выхода video")
    if not body.get("prompt"):
        prep.add("error", "prompt", "обязателен (документация /api/v1/videos)")
    for k in body:
        if k not in RA_VIDEO_DOC:
            prep.add("info", k, "провайдер-специфичный параметр в корне тела — RouterAI передаёт как есть (документация)")
    dur = body.get("duration")
    durs = m.get("supported_durations") or []
    if dur is None:
        prep.add("error", "duration", f"ценовой параметр — задайте явно (допустимо: {durs})")
    elif durs and int(num(dur) or 0) not in durs:
        prep.add("error", "duration", f"{dur!r} нет в {durs}")
    for k, key in (("resolution", "supported_resolutions"), ("aspect_ratio", "supported_aspect_ratios"),
                   ("size", "supported_sizes")):
        if body.get(k) is not None and m.get(key) and body[k] not in m[key]:
            prep.add("error", k, f"{body[k]!r} нет в {m[key]}")
    fr = body.get("frame_images")
    if fr is not None:
        allowed = m.get("supported_frame_images") or []
        for i, it in enumerate(fr if isinstance(fr, list) else []):
            where = f"frame_images[{i}]"
            if not (isinstance(it, dict) and isinstance(it.get("image_url"), dict)):
                prep.add("error", where, "формат: {\"type\": \"image_url\", \"image_url\": {\"url\": …}, "
                                         "\"frame_type\": \"first_frame\"|\"last_frame\"}")
                continue
            if it.get("frame_type") not in ("first_frame", "last_frame"):
                prep.add("error", where + ".frame_type", "first_frame или last_frame")
            elif allowed and it["frame_type"] not in allowed:
                prep.add("error", where + ".frame_type", f"модель принимает только {allowed}")
            it["image_url"]["url"] = resolve_media(prep, it["image_url"].get("url"), where + ".image_url.url")
    refs = body.get("input_references")
    for i, it in enumerate(refs if isinstance(refs, list) else []):
        t = it.get("type") if isinstance(it, dict) else None
        if t not in ("image_url", "video_url", "audio_url") or not isinstance(it.get(t), dict):
            prep.add("error", f"input_references[{i}]", "элемент {type: image_url|video_url|audio_url, <type>: {url}}")
            continue
        it[t]["url"] = resolve_media(prep, it[t].get("url"), f"input_references[{i}].{t}.url")
    if fr and refs and "seedance" in mid:
        prep.add("error", "frame_images", "у Seedance frame_images и input_references взаимоисключающие (документация)")
    if m.get("generate_audio") and "generate_audio" not in body:
        prep.add("warn", "generate_audio", "у модели есть звук (у Wan по умолчанию true) — задайте явно; цена за "
                                           "секунду в каталоге одна, без разбивки")
    if body.get("callback_url"):
        prep.add("warn", "callback_url", "клиент опрашивает сам; вебхук RouterAI идёт только на публичный HTTPS")
    if body.get("provider") is not None:
        check_provider(ctx, prep, body["provider"])
    rate = num((m.get("pricing") or {}).get("seconds"))
    if rate is not None and dur is not None:
        rub = float(rate) * float(num(dur) or 0)
        prep.estimate.update(rub=rub, rub_low=rub, rub_high=rub, formula=f"{fmt(rate)} ₽/с × {dur} с")
    elif rate is not None and durs:
        hi = float(rate) * max(durs)
        prep.estimate.update(rub=None, rub_high=hi, formula=f"{fmt(rate)} ₽/с × ? (худший случай {max(durs)} с)")


# ---------------------------------------------------------------------------------------------------------------
# Чат: polza-chat и routerai /v1/chat/completions
# ---------------------------------------------------------------------------------------------------------------

CHAT_DOC = {"model", "messages", "prompt", "max_tokens", "max_completion_tokens", "temperature", "top_p", "top_k",
            "frequency_penalty", "presence_penalty", "repetition_penalty", "min_p", "logit_bias", "stop", "seed",
            "stream", "reasoning", "reasoning_effort", "verbosity", "tools", "tool_choice", "response_format",
            "structured_outputs", "web_search_options", "provider", "plugins", "modalities", "audio", "user",
            "image_config", "include_reasoning"}
CHAT_ALWAYS = {"model", "messages", "prompt", "stream", "provider", "user", "plugins", "modalities", "audio",
               "image_config", "max_completion_tokens"}


def chat_prices(ctx: Ctx, prep: Prepared, m: dict) -> dict:
    if prep.channel == "routerai":
        pr = m.get("pricing") or {}
        p_in = float(num(pr.get("prompt")) or 0)
        return {"prompt": p_in, "image": float(num(pr.get("image")) or p_in),
                "completion": float(num(pr.get("completion")) or 0),
                "reasoning": float(num(pr.get("internal_reasoning")) or num(pr.get("completion")) or 0),
                "max_completion": num(m.get("top_provider", {}).get("max_completion_tokens")) if m.get("top_provider")
                else None, "unit": "₽/токен (каталог RouterAI)"}
    tp = m.get("top_provider") or {}
    pr = tp.get("pricing") or {}
    per = lambda k: float(num(pr.get(k)) or 0) / 1e6  # noqa: E731
    p_in = per("prompt_per_million")
    return {"prompt": p_in, "image": per("image_input_per_million") or p_in, "completion": per("completion_per_million"),
            "reasoning": per("internal_reasoning_per_million") or per("completion_per_million"),
            "max_completion": num(tp.get("max_completion_tokens")), "unit": "₽/1M токенов (каталог polza)"}


def prep_chat(ctx: Ctx, prep: Prepared, body: dict):
    prep.kind = "chat" if prep.channel == "polza-chat" else "ra-chat"
    mid = body.get("model")
    prep.model = mid
    is_tpl = isinstance(mid, str) and bool(TPL_RE.search(mid))
    if prep.channel == "routerai":
        m = ctx.ra.models.get(mid) if isinstance(mid, str) else None
        prep.estimate["source"] = ctx.ra.label
        sup = set((m or {}).get("supported_parameters") or [])
        ins = ((m or {}).get("architecture") or {}).get("input_modalities") or []
        label = ctx.ra.label
    else:
        m = ctx.pz.by_id.get(mid) if isinstance(mid, str) else None
        prep.estimate["source"] = f"каталог polza {ctx.pz.dir.name} ({ctx.pz.fetched_at()})"
        sup = set(((m or {}).get("top_provider") or {}).get("supported_parameters") or [])
        ins = ((m or {}).get("architecture") or {}).get("input_modalities") or []
        label = f"каталоге polza {ctx.pz.dir.name}"
        if m is not None and m.get("type") != "chat":
            prep.add("error", "model", f"тип {m.get('type')!r}, нужен chat")
        if m is not None and "/api/v1/chat/completions" not in (m.get("endpoints") or []):
            prep.add("warn", "model", f"эндпоинты модели: {m.get('endpoints')}")
    if m is None:
        if is_tpl:
            prep.add("warn", "model", f"шаблон {mid!r} — модель подставляется перед запуском (--set)")
        else:
            prep.add("error", "model", f"нет в {label}")
    prep.minfo = m
    msgs = body.get("messages")
    if not isinstance(msgs, list) or not msgs:
        if not body.get("prompt"):
            prep.add("error", "messages", "нужен непустой массив messages (или prompt)")
        msgs = []
    t_text, img_lo, img_hi, n_img = 0, 0, 0, 0
    for i, msg in enumerate(msgs):
        where = f"messages[{i}]"
        if not isinstance(msg, dict) or msg.get("role") not in ("system", "user", "assistant", "developer", "tool"):
            prep.add("error", where, "объект {role: system|user|assistant|developer|tool, content}")
            continue
        c = msg.get("content")
        t_text += 4
        if isinstance(c, str):
            t_text += text_tokens(c)
            continue
        if not isinstance(c, list):
            if c is not None or msg.get("role") != "assistant":
                prep.add("error", where + ".content", "строка или массив частей")
            continue
        for j, part in enumerate(c):
            pw = f"{where}.content[{j}]"
            t = part.get("type") if isinstance(part, dict) else None
            if t == "text":
                t_text += text_tokens(str(part.get("text") or ""))
            elif t == "image_url" and isinstance(part.get("image_url"), dict):
                n_img += 1
                if "image" not in ins and m is not None:
                    prep.add("error", pw, f"модель не принимает картинки (input_modalities {ins})")
                before = len(prep.files)
                part["image_url"]["url"] = resolve_media(prep, part["image_url"].get("url"), pw + ".image_url.url")
                f = prep.files[before] if len(prep.files) > before else {}
                lo, hi = vision_tokens(str(mid), f.get("w"), f.get("h"))
                img_lo, img_hi = img_lo + lo, img_hi + hi
            elif t == "video_url" and isinstance(part.get("video_url"), dict):
                part["video_url"]["url"] = resolve_media(prep, part["video_url"].get("url"), pw + ".video_url.url")
                img_lo, img_hi = img_lo + 2000, img_hi + 20000
                prep.add("warn", pw, "видео на входе: токены оценены грубо (2–20 тыс.)")
            elif t == "file" and isinstance(part.get("file"), dict):
                fd = part["file"].get("file_data")
                if isinstance(fd, str) and not fd.startswith("data:"):
                    part["file"]["file_data"] = resolve_media(prep, fd, pw + ".file.file_data")
                img_lo, img_hi = img_lo + 1000, img_hi + 10000
            elif t == "input_audio":
                img_lo, img_hi = img_lo + 500, img_hi + 5000
            else:
                prep.add("error", pw, "часть {type: text|image_url|video_url|file|input_audio, …}")
    if prep.channel == "polza-chat" and body.get("prompt"):
        t_text += text_tokens(str(body["prompt"]))
    for k in body:
        if k not in CHAT_DOC:
            prep.add("warn", k, "параметра нет в документации chat/completions")
        elif m is not None and k not in CHAT_ALWAYS and sup and k not in sup:
            prep.add("warn", k, f"нет в supported_parameters модели — провайдер может отбросить или отклонить")
    if body.get("stream"):
        prep.add("error", "stream", "потоковый режим клиент не поддерживает — уберите stream")
    if m is None:
        return
    pr = chat_prices(ctx, prep, m)
    cap = num(body.get("max_tokens") or body.get("max_completion_tokens"))
    p_out = max(pr["completion"], pr["reasoning"])
    inp_lo = t_text * pr["prompt"] + img_lo * pr["image"]
    inp_hi = t_text * pr["prompt"] + img_hi * pr["image"]
    W = prep.estimate["warnings"]
    if cap is None:
        mc = pr.get("max_completion")
        limit = min(ctx.max_job, float(prep.job["max_rub"])) if prep.job.get("max_rub") is not None else ctx.max_job
        if ctx.a.no_auto_cap or p_out <= 0:
            cap = mc or 32768
            W.append(f"max_tokens не задан — худший случай по потолку модели {cap} ток.")
        else:
            cap = int((limit - inp_hi) / p_out)
            if mc:
                cap = min(cap, int(mc))
            if cap < 256:
                prep.add("error", "max_tokens", f"max_rub {fmt(limit)} ₽ не покрывает и 256 токенов ответа")
            else:
                body["max_tokens"] = cap
                prep.filled.append("max_tokens")
                prep.add("warn", "max_tokens", f"не задан — клиент ставит потолок {cap} ток. по max_rub "
                                               f"{fmt(limit)} ₽ (отключить: --no-auto-cap)")
    cap = int(cap)
    hi = inp_hi + cap * p_out
    declared = num(prep.job.get("price_rub"))
    exp = float(declared) if declared is not None else inp_lo + min(cap, 2000) * pr["completion"]
    if exp > hi and not prep.templates:
        W.append(f"price_rub задания {fmt(exp)} ₽ выше потолка по max_tokens {fmt(hi)} ₽ — ожидание взято по потолку")
        exp = hi
    prep.estimate.update(rub=exp, rub_low=inp_lo, rub_high=hi,
                         formula=(f"вход ≈ {t_text} ток. текста + {img_lo}–{img_hi} ток. картинок ({n_img}) = "
                                  f"{fmt(inp_lo)}–{fmt(inp_hi)} ₽; выход ≤ {cap} ток. × {pr['completion'] * 1e6:.2f} ₽/1M"
                                  f" (рассуждения {pr['reasoning'] * 1e6:.2f}) → верх {fmt(hi)} ₽; ожидание "
                                  f"{'по price_rub задания' if declared is not None else 'по 2000 ток.'} {fmt(exp)} ₽"))
    reas = body.get("reasoning")
    if isinstance(reas, dict) and (reas.get("effort") not in (None, "none") or reas.get("type") or reas.get("enabled")):
        rmax = num(reas.get("max_tokens"))
        guess = rmax or {"minimal": 512, "low": 2048, "medium": 8192, "high": 24576, "xhigh": 32768}.get(
            str(reas.get("effort") or reas.get("effort_level") or "medium"), 8192)
        W.append(f"рассуждения биллятся как выход; входят ли они в max_tokens у провайдера — [не проверено]: если нет, "
                 f"до +{fmt(guess * pr['reasoning'])} ₽ сверх верха (оценка {guess} ток.)")


# ---------------------------------------------------------------------------------------------------------------
# Gen-API
# ---------------------------------------------------------------------------------------------------------------

GENAPI_EXPLICIT = {"recraft-v4": ("model", "pro")}
# Gen-API отвечает на data:URI в url_or_file HTTP 422 «Неверный тип. Параметр … должен быть file либо url» (без списания);
# рабочий путь — публичный URL
GA_DATA_URI_WARN = ("локальный файл уйдёт data:URI — Gen-API отвечает 422 «должен быть file либо url»: "
                    "выложите файл `polza.py upload ФАЙЛ --live` (TEMP 24 ч) и подставьте URL")
# 3D-генераторы (сетка, облако точек, анимация скелета) в работе скилла не вызываются: 3D — Blender и код
# (kb/3d/10-ai-3d-generation-assets/01-generators-landscape.md §1); сеть узнаётся по имени и по форматам выхода каталога
GA_3D_SLUG = re.compile(r"(^|-)3d(-|$)|^(trellis|tripo|rodin|meshy|hi3d|hunyuan-motion)")
GA_3D_FORMATS = {"glb", "gltf", "obj", "stl", "fbx", "usdz", "ply"}


def ga_is_3d(sl: str, params: dict) -> bool:
    """Сеть Gen-API — 3D-генератор: по имени или по формату выхода (export_format, output_format) из каталога."""
    if GA_3D_SLUG.search(sl or ""):
        return True
    for k in ("export_format", "output_format", "format"):
        items = {str(x).lower() for x in ((params.get(k) or {}).get("items") or [])}
        if items & GA_3D_FORMATS:
            return True
    return False


def ga_type_check(prep: Prepared, name: str, spec: dict, v, body: dict):
    t = str(spec.get("type") or "")
    where = name
    if t == "boolean":
        if not isinstance(v, bool):
            if as_bool(v) is None:
                prep.add("error", where, f"boolean, получено {v!r}")
            else:
                prep.add("warn", where, f"boolean ожидается JSON true/false, получено {v!r}")
    elif t == "integer":
        if not (isinstance(v, int) and not isinstance(v, bool)):
            prep.add("error" if num(v) is None else "warn", where, f"integer, получено {v!r}")
    elif t == "numeric":
        if num(v) is None:
            prep.add("error", where, f"число, получено {v!r}")
    elif t == "string":
        if not isinstance(v, str):
            prep.add("warn", where, f"строка, получено {type(v).__name__}")
    elif t == "url":
        if not (isinstance(v, str) and v.startswith(("http://", "https://"))):
            prep.add("error", where, "нужен URL http(s)")
    elif t.startswith("url_or_file"):
        exts = tuple(t.split(":", 1)[1].split(",")) if ":" in t else None
        body[name] = resolve_media(prep, v, where, exts)
        if isinstance(body[name], str) and body[name].startswith("data:"):
            prep.add("warn", where, GA_DATA_URI_WARN)
    elif t.startswith("files_array"):
        exts = tuple(t.split(":", 1)[1].split(",")) if ":" in t else None
        if not isinstance(v, list):
            prep.add("error", where, "нужен массив файлов (URL, data:URI или пути)")
        else:
            body[name] = [resolve_media(prep, x, f"{where}[{i}]", exts) for i, x in enumerate(v)]
            if any(isinstance(x, str) and x.startswith("data:") for x in body[name]):
                prep.add("warn", where, GA_DATA_URI_WARN)
    elif t in ("RGB", "RGB_background"):
        items = v if t == "RGB" else [v]
        if t == "RGB" and not isinstance(v, list):
            prep.add("error", where, "массив цветов [{\"r\":…,\"g\":…,\"b\":…}]")
            return
        for i, c in enumerate(items):
            ok = isinstance(c, dict) and all(isinstance(c.get(ch), int) and 0 <= c[ch] <= 255 for ch in "rgb")
            if not ok:
                prep.add("error", f"{where}[{i}]" if t == "RGB" else where, "цвет {\"r\": 0–255, \"g\": 0–255, \"b\": 0–255}")
            elif set(c) - set("rgb"):
                prep.add("warn", f"{where}[{i}]" if t == "RGB" else where, f"лишние поля {sorted(set(c) - set('rgb'))} "
                                                                           f"(у Gen-API веса цвета не документированы)")


def prep_genapi(ctx: Ctx, prep: Prepared, body: dict):
    mm = re.fullmatch(r"/v1/networks/([\w.-]+)", prep.api_path or "")
    prep.estimate["source"] = ctx.ga.label
    if not mm:
        prep.add("error", "path", "ожидается /api/v1/networks/{slug} (документация Gen-API)")
        return
    sl = mm.group(1)
    prep.model = sl
    prep.kind = "ga-sync" if as_bool(body.get("is_sync")) else "ga-task"
    net = ctx.ga.nets.get(sl)
    if net is None:
        near = [s for s in ctx.ga.nets if sl[:5] in s][:8]
        prep.add("error", "path", f"сети {sl!r} нет в {ctx.ga.label}; похожие: {near}")
        return
    prep.minfo = net
    params = ctx.ga.params.get(sl) or {}
    if ga_is_3d(sl, params):
        prep.add("error", "path", f"{sl}: 3D-генератор — в работе скилла не вызывается; 3D — Blender и код "
                                  f"(3d 10/01 §1), поворот и конфигуратор — модель из Blender")
        return
    for k, v in list(body.items()):
        spec = params.get(k)
        if spec is None:
            prep.add("warn", k, f"параметра нет у сети в каталоге ({sorted(params)}) — Gen-API может отклонить "
                                f"(400 errors_validation) или проигнорировать")
            continue
        items = spec.get("items")
        if items and pc.as_str(v) not in [str(x) for x in items]:
            prep.add("error", k, f"{v!r} не из {items}")
        ga_type_check(prep, k, spec, v, body)
    for k, spec in params.items():
        if spec.get("required") and k not in body:
            prep.add("error", k, "обязательный параметр сети (каталог Gen-API)")
    if "translate_input" in params:
        d = as_bool(params["translate_input"].get("default"))
        if "translate_input" not in body:
            body["translate_input"] = False
            prep.filled.append("translate_input")
            prep.add("warn" if d else "info", "translate_input",
                     f"не задан — клиент ставит false явно (умолчание Gen-API: {'true — платный перевод GPT-4.1, '
                     f'переводит и надписи' if d else 'false'})")
        elif as_bool(body["translate_input"]):
            prep.add("warn", "translate_input", "true — платный перевод промта моделью GPT-4.1 (копейки, отдельной "
                                                "транзакцией) и перевод надписей в кавычках")
    for k in GENAPI_EXPLICIT.get(sl, ()):
        if k not in body and k in params:
            prep.add("error", k, f"ценовой параметр с умолчанием {params[k].get('default')!r} — задайте явно")
    for k, spec in params.items():
        if k == "pro" and k not in body and as_bool(spec.get("default")):
            prep.add("error", k, "pro по умолчанию включён (дороже в 3–4 раза) — задайте явно")
    if body.get("callback_url"):
        prep.add("warn", "callback_url", "клиент опрашивает сам; вебхук Gen-API шлёт на публичный URL")
    if net.get("is_payment_upfront"):
        prep.add("info", "оплата", "is_payment_upfront: списание при создании задачи; возврат при error — [не проверено]")
    genapi_price(ctx, prep, sl, body, params, net)


def genapi_price(ctx: Ctx, prep: Prepared, sl: str, body: dict, params: dict, net: dict):
    e, W = prep.estimate, prep.estimate["warnings"]
    rows = genapi_table(ctx.ga.prices.get(sl))

    def val(k):
        return body[k] if k in body else (params.get(k) or {}).get("default")

    n = int(num(val("num_images")) or 1) if "num_images" in params else 1
    src = f"прайс Gen-API ({ctx.ga.prices_src})"
    if sl == "recraft-v4":
        model, pro = str(val("model") or "image"), bool(as_bool(val("pro")))
        for r in rows:
            if r.get("Модель") == model and r.get("Pro") == ("Включен" if pro else "Выключен"):
                p = rub_of(r.get("Цена за изображение"))
                if p is not None:
                    e.update(rub=p, rub_low=p, rub_high=p, formula=f"Recraft V4 {model}, Pro {'вкл' if pro else 'выкл'}"
                                                                   f" = {fmt(p)} ₽ ({src})")
    elif sl.startswith("flux-2") and rows:
        w, h = num(val("width")), num(val("height"))
        mp = (float(w) * float(h) / 1e6) if w and h else 1.0
        has_img = bool(body.get("image_urls") or body.get("image_url"))
        first = extra = None
        for r in rows:
            label = " ".join(str(r.get(k) or "") for k in ("Модель", "Тип генерации"))
            if sl == "flux-2" and str(r.get("Модель")) != str(val("model") or "standard"):
                continue
            if ("изображени" in label) != has_img:
                continue
            p = rub_of(r.get("Цена") or r.get("Цена за 1 мегапиксель"))
            if "дополнительн" in label:
                extra = p
            elif first is None:
                first = p
        if first is not None:
            k_mp = max(1, math.ceil(mp - 1e-9))
            if extra is not None:
                rub = first + extra * max(0.0, mp - 1)
                hi = first + extra * (k_mp - 1)
            else:
                rub, hi = first * max(1.0, mp), first * k_mp
            e.update(rub=rub * n, rub_low=rub * n, rub_high=hi * n,
                     formula=f"{fmt(first)} ₽/Мп × {mp:.2f} Мп ({int(w or 0)}×{int(h or 0)}) × {n} ({src}; "
                             f"верх — по целым Мп)")
    if e["rub"] is None:
        c = net.get("cost")
        if isinstance(c, (int, float)) and c > 0:
            e.update(rub=float(c) * n, rub_low=float(c) * n, rub_high=float(c) * n,
                     formula=f"{fmt(c)} ₽ за запрос (каталог Gen-API)" + (f" × {n}" if n > 1 else ""))
    if as_bool(body.get("translate_input")) and e["rub_high"] is not None:
        e["rub_high"] += 0.1
        W.append("translate_input=true: + перевод GPT-4.1 (≈ копейки) в верхней оценке")


# ---------------------------------------------------------------------------------------------------------------
# polza-images: /v2/images/generations
# ---------------------------------------------------------------------------------------------------------------

PZ_IMG_SCHEMA = {"model": None, "prompt": None, "n": None,
                 "size": ("auto", "256x256", "512x512", "1024x1024", "1536x1024", "1024x1536", "1792x1024", "1024x1792"),
                 "quality": ("auto", "low", "medium", "high", "standard", "hd"), "response_format": ("url", "b64_json"),
                 "style": ("vivid", "natural"), "output_format": ("png", "jpeg", "webp"),
                 "background": ("transparent", "opaque", "auto"), "output_compression": None, "user": None}
PZ_SIZE_AR = {"1024x1024": "1:1", "512x512": "1:1", "256x256": "1:1", "1536x1024": "3:2", "1024x1536": "2:3",
              "1792x1024": "16:9", "1024x1792": "9:16", "auto": "auto"}


def prep_pz_image(ctx: Ctx, prep: Prepared, body: dict):
    prep.kind = "pz-image"
    mid = body.get("model")
    prep.model = mid
    prep.estimate["source"] = f"каталог polza {ctx.pz.dir.name} ({ctx.pz.fetched_at()})"
    m = ctx.pz.by_id.get(mid) if isinstance(mid, str) else None
    if m is None:
        prep.add("error", "model", f"нет в каталоге polza {ctx.pz.dir.name}")
        return
    prep.minfo = m
    eps = m.get("endpoints") or []
    if not any("images/generations" in x for x in eps):
        prep.add("error", "model", f"модель не отдаётся через images/generations (эндпоинты {eps})")
    if not body.get("prompt"):
        prep.add("error", "prompt", "обязателен (OpenAPI)")
    for k, v in body.items():
        if k not in PZ_IMG_SCHEMA:
            prep.add("warn", k, "поля нет в схеме OpenAPI /v2/images/generations")
            continue
        allowed = PZ_IMG_SCHEMA[k]
        if allowed and pc.as_str(v) not in allowed:
            prep.add("error", k, f"{v!r} не из {list(allowed)} (OpenAPI polza)")
    n = body.get("n", 1)
    if not (isinstance(n, int) and 1 <= n <= 10):
        prep.add("error", "n", "целое 1–10")
        n = 1
    oc = body.get("output_compression")
    if oc is not None and not (isinstance(oc, (int, float)) and 0 <= oc <= 100):
        prep.add("error", "output_compression", "0–100")
    for k in ("background", "output_format", "output_compression"):
        if k in body:
            prep.add("info", k, "в OpenAPI polza описан «для gpt-image-1» (в mdx /v2 его нет) — дойдёт ли до "
                                f"{mid} у провайдера {((m.get('top_provider') or {}).get('name'))} — гипотеза теста")
    size = str(body.get("size") or "auto")
    ar = PZ_SIZE_AR.get(size, "auto")
    est = pc.estimate(m, {"image_resolution": "1K", "aspect_ratio": ar})
    rub, fb = est.get("rub"), est.get("fallback_rub")
    if rub is not None:
        hi = max(rub, fb or rub)
        prep.estimate.update(rub=rub * n, rub_low=rub * n, rub_high=hi * n,
                             formula=(f"ступень 1K каталога Media API = {fmt(rub)} ₽ × {n} (size {size} → 1K, aspect "
                                      f"{ar} — отображение /v2 на ступени [не проверено]); верх — запасная ступень "
                                      f"[] = {fmt(fb)} ₽"))
        if fb and fb > rub:
            prep.estimate["warnings"].append(f"как /v2 выбирает ступень цены, не документировано: худший случай — "
                                             f"запасная ступень {fmt(fb)} ₽ (лимиты считаются по нему; "
                                             f"--limit-by expected — по 1K)")


# ---------------------------------------------------------------------------------------------------------------
# Подготовка задания
# ---------------------------------------------------------------------------------------------------------------

def evaluation_job(job: dict) -> str | None:
    """Задание оценки по рубрике (судья) — не задание канала: оценку делает отдельная сессия Opus по пакету. → причина."""
    meta = job.get("meta") if isinstance(job.get("meta"), dict) else {}
    if str(meta.get("judge") or "").lower() == "vlm" or meta.get("rubric"):
        return ("оценка по рубрике — не задание канала: её делает отдельная сессия Opus (агент design-judge) по пакету "
                "asset_audit.py judge-jobs, разбор — judge-parse")
    return None


def prepare(ctx: Ctx, job: dict) -> Prepared:
    prep = Prepared(job, ctx)
    why = evaluation_job(job)
    if why:
        prep.add("error", "задание", why)
        return prep
    if prep.channel not in CHANNELS:
        prep.add("error", "channel", f"{job.get('channel')!r}: нужен routerai | genapi | polza-chat | polza-images "
                                     f"(задания Media API polza — через polza.py)")
        return prep
    if job.get("_channel_mismatch"):
        prep.add("warn", "channel", f"в задании {prep.channel!r}, в имени файла {job['_channel_mismatch']!r}")
    if prep.method != "POST":
        prep.add("error", "method", "генерация — только POST")
    body = job.get("body")
    if not isinstance(body, dict):
        prep.add("error", "body", "нужен объект тела запроса")
        return prep
    body = json.loads(json.dumps(body))
    body, used, missing = fill_templates(body, ctx.set_values)
    if used:
        prep.filled.append(f"шаблон: {', '.join(sorted(used))}")
    prep.templates += [f"{{{{{n}}}}}" for n in sorted(missing)]
    prep.api_path = api_path(job.get("path") or CHANNELS[prep.channel]["default_path"])
    ap = prep.api_path
    try:
        if prep.channel == "routerai":
            if ap == "/v1/images":
                prep_ra_image(ctx, prep, body)
            elif ap == "/v1/videos":
                prep_ra_video(ctx, prep, body)
            elif ap == "/v1/chat/completions":
                prep_chat(ctx, prep, body)
            else:
                prep.add("error", "path", "RouterAI: /api/v1/images | /api/v1/videos | /api/v1/chat/completions")
        elif prep.channel == "genapi":
            prep_genapi(ctx, prep, body)
        elif prep.channel == "polza-chat":
            if ap == "/v1/chat/completions":
                prep_chat(ctx, prep, body)
            else:
                prep.add("error", "path", "polza-chat: /api/v1/chat/completions")
        elif prep.channel == "polza-images":
            if ap == "/v2/images/generations":
                prep_pz_image(ctx, prep, body)
            else:
                prep.add("error", "path", "polza-images: /api/v2/images/generations")
    except SystemExit as e:        # нет снимка каталога — ошибка задания, а не падение
        prep.add("error", "каталог", str(e))
    prep.body = body
    e = prep.estimate
    declared = num(job.get("price_rub"))
    if prep.templates:
        prep.add("warn", "шаблон", "ШАБЛОН: " + "; ".join(prep.templates[:6]) + " — оценка по price_rub задания; "
                                   "--live после --set/--set-file")
    if declared is not None and (prep.templates or (e["rub"] is None and e["rub_high"] is None)):
        # шаблон (например, судья на N картинок) или цена не вычислена: ожидание — price_rub задания
        lo = e["rub_low"] if e["rub_low"] is not None else float(declared)
        e.update(rub=float(declared), rub_low=min(lo, float(declared)),
                 rub_high=max(float(declared), float(e["rub_high"] or 0)))
        e["formula"] = (e["formula"] + "; " if e["formula"] else "") + f"ожидание по price_rub задания {fmt(declared)} ₽"
        e["source"] = (e["source"] + " + " if e["source"] else "") + "price_rub задания"
    if e["rub"] is not None and declared is not None and not prep.templates and prep.kind not in ("chat", "ra-chat"):
        d = e["rub"] - float(declared)
        if abs(d) > max(0.05, 0.25 * float(declared)):
            e["warnings"].append(f"оценка клиента {fmt(e['rub'])} ₽ расходится с price_rub задания {fmt(declared)} ₽ "
                                 f"({d / max(float(declared), 1e-9) * 100:+.0f} %)")
    if job.get("max_rub") is None:
        prep.add("warn", "max_rub", "нет лимита на задание — действует только --max-job / MP_MAX_JOB")
    if not job.get("tag"):
        prep.add("warn", "tag", "нет tag — имя файла результата по имени задания")
    canon_obj = {"channel": prep.channel, "path": prep.api_path, "body": canon(body), "variant": job.get("variant")}
    prep.request_hash = sha256_hex(json.dumps(canon_obj, sort_keys=True, ensure_ascii=False).encode())
    return prep


# ---------------------------------------------------------------------------------------------------------------
# Бюджет
# ---------------------------------------------------------------------------------------------------------------

def price_for_limits(ctx: Ctx, prep: Prepared):
    e = prep.estimate
    if getattr(ctx.a, "limit_by", "high") == "expected" and e.get("rub") is not None:
        return e["rub"]
    return e["rub_high"] if e.get("rub_high") is not None else e.get("rub")


def budget_check(ctx: Ctx, prep: Prepared, extra_reserved: float = 0.0) -> tuple[bool, str]:
    rub = price_for_limits(ctx, prep)
    if prep.channel not in CHANNELS:
        return False, "канал неизвестен"
    if rub is None:
        if ctx.a.allow_unknown_price:
            return True, "цена неизвестна (разрешено --allow-unknown-price)"
        return False, "цена неизвестна — уточните параметры или --allow-unknown-price"
    cap = min(ctx.max_job, float(prep.job["max_rub"])) if prep.job.get("max_rub") is not None else ctx.max_job
    if rub > cap + 1e-9:
        return False, (f"оценка {fmt(rub)} ₽ > лимита на задание {fmt(cap)} ₽ (max_rub / --max-job)"
                       + ("; ожидаемая " + fmt(prep.estimate['rub']) + " ₽ — --limit-by expected"
                          if prep.estimate.get("rub") is not None and prep.estimate["rub"] <= cap < rub else ""))
    total = ctx.budget_total(prep.channel)
    env = CHANNELS[prep.channel]["budget_env"]
    base = ctx.base(prep.channel)
    if total <= 0:
        return False, f"бюджет канала {prep.channel} = 0 ₽ — задайте {env} (или --budget-total)"
    spent = ctx.ledger.spent(base) + extra_reserved
    if spent + rub > total + 1e-9:
        return False, f"бюджет {env}: потрачено/в резерве {fmt(spent)} ₽ + {fmt(rub)} ₽ > {fmt(total)} ₽"
    if ctx.budget_agent is not None:
        sa = ctx.ledger.spent(base, prep.agent)
        if sa + rub > ctx.budget_agent + 1e-9:
            return False, f"бюджет агента {prep.agent}: {fmt(sa)} ₽ + {fmt(rub)} ₽ > {fmt(ctx.budget_agent)} ₽"
    return True, f"{env}: потрачено/в резерве {fmt(spent)} из {fmt(total)} ₽; после задания останется " \
                 f"{fmt(total - spent - rub)} ₽"


def preflight_polza(ctx: Ctx, need_rub):
    """GET /v2/balance и /v1/key polza (как polza.py) — один раз на процесс."""
    if "polza" in ctx._preflight_done or ctx.a.no_preflight:
        return
    ctx._preflight_done.add("polza")
    http = ctx.http("polza-chat")
    try:
        b = http.request("GET", http.url("/v2/balance")).json or {}
        avail = num(b.get("available"))
        say(f"  polza баланс: available {b.get('available')} ₽, резерв {b.get('reservedAmount')}")
        if need_rub is not None and avail is not None and avail < need_rub:
            say(f"  ОТКАЗ: недостаточно средств polza — available {avail} ₽ < {fmt(need_rub)} ₽", err=True)
            raise SystemExit(EXIT_BUDGET)
    except ApiError as e:
        say(f"  ! /v2/balance: {e}", err=True)
        if e.status in (401, 403):
            raise SystemExit(EXIT_HTTP)
    try:
        k = http.request("GET", http.url("/v1/key")).json or {}
        rem = num(k.get("limit_remaining"))
        say(f"  ключ polza: лимит {k.get('limit')}, остаток {k.get('limit_remaining')}")
        if need_rub is not None and rem is not None and rem < need_rub:
            say(f"  ОТКАЗ: остаток лимита ключа polza {rem} ₽ < {fmt(need_rub)} ₽", err=True)
            raise SystemExit(EXIT_BUDGET)
    except ApiError as e:
        say(f"  ! /v1/key: {e}", err=True)


# ---------------------------------------------------------------------------------------------------------------
# Результат: имена, файлы, паспорт
# ---------------------------------------------------------------------------------------------------------------

def out_dir_for(ctx: Ctx, job: dict, agent: str) -> Path:
    d = Path(job["out_dir"]) if job.get("out_dir") else ctx.out_root / str(agent) / dt.date.today().isoformat()
    if not d.is_absolute():
        d = ROOT / d
    d.mkdir(parents=True, exist_ok=True)
    return d


def base_name(tag: str, model, gen_id) -> str:
    return f"{slug(tag)}__{slug(model or 'model')}__{slug(gen_id or 'x')}"


def prompt_of(body: dict):
    if body.get("prompt"):
        return str(body["prompt"])[:4000]
    for msg in reversed(body.get("messages") or []):
        if isinstance(msg, dict) and msg.get("role") == "user":
            c = msg.get("content")
            if isinstance(c, str):
                return c[:4000]
            if isinstance(c, list):
                return " ".join(str(p.get("text")) for p in c if isinstance(p, dict) and p.get("type") == "text")[:4000]
    return None


def write_passport(files: list[dict], passport: dict, fallback: Path) -> str:
    if files:
        first = absp(files[0]["path"])
        stem = re.sub(r"_\d+$", "", first.stem) if len(files) > 1 else first.stem
        path = first.with_name(stem + ".passport.json")
    else:
        path = fallback.with_name(fallback.name + ".passport.json")
    path.write_text(jdump(redact_obj(passport)), encoding="utf-8")
    return rel(path)


def cost_of(obj: dict, *keys):
    """Цена из usage: RouterAI — usage.cost (₽), polza — usage.cost_rub (= cost)."""
    u = (obj or {}).get("usage") or {}
    for k in keys:
        v = num(u.get(k))
        if v is not None:
            return float(v)
    return None


class Run:
    """Живой прогон одного подготовленного задания: кэш → бюджет → submit → запрос → файлы → паспорт → журнал."""

    def __init__(self, ctx: Ctx, prep: Prepared, force: bool):
        self.ctx, self.prep, self.force = ctx, prep, force
        self.http = ctx.http(prep.channel)
        self.base = ctx.base(prep.channel)
        self.label = prep.label
        self.t0 = time.time()
        self.submitted_at = now_iso()
        self.last: Resp | None = None       # последний ответ канала: при отказе его тело и заголовки идут в паспорт

    def request(self, method: str, url: str, **kw) -> Resp:
        self.last = self.http.request(method, url, **kw)
        return self.last

    def ev(self, event: str, **kw):
        self.ctx.ledger.append({"event": event, "uid": self.prep.uid, "base_url": self.base,
                                "channel": self.prep.channel, **kw})

    def begin(self) -> int | None:
        p = self.prep
        if not self.force:
            hit = self.ctx.ledger.find_cached(p.request_hash, self.base)
            if hit:
                self.ev("cache_hit", agent=p.agent, tag=p.tag, model=p.model, request_hash=p.request_hash,
                        source_uid=hit["uid"], id=hit.get("id"), files=hit.get("files"))
                say(f"  [{self.label}] кэш: тот же запрос уже выполнен ({hit.get('id')}), файлы {hit.get('files')} — "
                    f"0 ₽ (повтор — --force или другой variant)")
                return EXIT_OK
        with self.ctx._budget_lock:
            ok, msg = budget_check(self.ctx, p)
            if not ok:
                say(f"  [{self.label}] ОТКАЗ: {msg}", err=True)
                return EXIT_BUDGET
            self.ev("submit", agent=p.agent, tag=p.tag, model=p.model, path=p.api_path, request_hash=p.request_hash,
                    estimate_rub=price_for_limits(self.ctx, p), estimate_expected_rub=p.estimate.get("rub"),
                    notes=p.job.get("notes"))
        self.t0 = time.time()
        self.submitted_at = now_iso()
        return None

    def post_error(self, e: ApiError) -> int:
        ev = "unknown" if e.ambiguous else "http_error"
        self.ev(ev, http_status=e.status, code=e.code, message=e.message,
                body=e.body if isinstance(e.body, dict) else None)
        say(f"  [{self.label}] ОШИБКА создания: {e}" + ("  — запрос мог быть принят: резерв оставлен в журнале, "
                                                        "проверьте историю канала" if e.ambiguous else ""), err=True)
        if isinstance(e.body, dict):
            say(jdump(redact_obj(shorten(e.body))), err=True)
        if e.status in (401, 402, 403):
            self.ctx.stop[self.prep.scope].set()
        return EXIT_HTTP

    def out_base(self, gen_id) -> Path:
        d = out_dir_for(self.ctx, self.prep.job, self.prep.agent)
        return d / base_name(self.prep.tag, self.prep.model, gen_id)

    def passport_head(self, gen_id) -> dict:
        p = self.prep
        return {
            "schema": "mp-passport/1", "client": VERSION, "channel": p.channel, "kind": p.kind, "uid": p.uid,
            "request_hash": p.request_hash, "id": gen_id,
            "job": {**{k: p.job.get(k) for k in ("tag", "agent", "notes", "variant", "channel", "path", "price_rub",
                                                  "max_rub", "price_source", "docs", "meta")},
                    "file": p.job.get("_file"), "index": p.job.get("_index")},
            "model": p.model, "prompt": prompt_of(p.body),
            "request": {"method": "POST", "url": self.http.url(p.api_path or ""), "body": shorten(p.body)},
            "catalog": {"source": p.estimate.get("source"), "estimate": p.estimate, "issues": p.issues,
                        "filled": p.filled, "inputs": p.files}}

    def response_record(self) -> dict | None:
        """Последний ответ канала для паспорта отказа: статус, заголовки (без cookie), тело — JSON с сокращённым
        base64, иначе начало текста; длина и sha256 — всего тела."""
        r = self.last
        if r is None:
            return None
        text = r.body.decode("utf-8", "replace")
        return {"http_status": r.status, "headers": {k: v for k, v in r.headers.items() if k != "set-cookie"},
                "bytes": len(r.body), "sha256": sha256_hex(r.body),
                "body": shorten(r.json) if r.json is not None else text[:RESPONSE_TEXT_MAX]}

    def finish(self, gen_id, files: list[dict], cost, resp_create, resp_final, polls=0, extra=None) -> int:
        p = self.prep
        passport = {
            **self.passport_head(gen_id),
            "response_create": shorten(resp_create), "response_final": shorten(resp_final),
            "timing": {"submitted_at": self.submitted_at, "completed_at": now_iso(),
                       "wall_s": round(time.time() - self.t0, 2), "polls": polls},
            "cost": {"usage_cost_rub": cost, "estimate_rub": p.estimate.get("rub"),
                     "limit_rub": price_for_limits(self.ctx, p),
                     "delta_rub": (round(cost - p.estimate["rub"], 4) if cost is not None and p.estimate.get("rub")
                                   is not None else None)},
            "files": files, "base_url": self.base, **(extra or {}),
        }
        if getattr(self, "download_note", None):
            passport["note"] = self.download_note
            passport["downloaded_at"] = now_iso()
        pp = write_passport(files, passport, self.out_base(gen_id))
        self.ev("completed", id=gen_id, cost_rub=cost, estimate_rub=price_for_limits(self.ctx, p),
                files=[f["path"] for f in files], passport=pp, wall_s=passport["timing"]["wall_s"])
        say(f"  [{self.label}] ГОТОВО за {passport['timing']['wall_s']} с; цена {cost} ₽ (оценка "
            f"{fmt(p.estimate.get('rub'))}); файлов {len(files)}; паспорт {pp}")
        return EXIT_OK

    def fail(self, gen_id, status, cost, error, final=None) -> int:
        """Отказ или ответ без результата: паспорт без файлов с телом и заголовками последнего ответа канала — по
        одной строке журнала причину отказа не разобрать."""
        passport = {**self.passport_head(gen_id), "status": status, "error": shorten(error),
                    "response": self.response_record(),
                    "timing": {"submitted_at": self.submitted_at, "completed_at": now_iso(),
                               "wall_s": round(time.time() - self.t0, 2)},
                    "cost": {"usage_cost_rub": cost or 0.0, "estimate_rub": self.prep.estimate.get("rub")},
                    "files": [], "base_url": self.base}
        pp = write_passport([], passport, self.out_base(gen_id))
        self.ev("cancelled" if status == "cancelled" else "failed", id=gen_id, status=status, cost_rub=cost or 0.0,
                error=shorten(error), passport=pp)
        say(f"  [{self.label}] {str(status).upper()}: {jdump(shorten(error), None)[:600]}; списано {cost or 0} ₽; "
            f"ответ канала — в паспорте {pp}", err=True)
        return EXIT_FAILED

    def download_error(self, gen_id, cost, e, hint) -> int:
        self.ev("completed", id=gen_id, cost_rub=cost, files=[], download_error=str(e))
        say(f"  [{self.label}] ОШИБКА скачивания: {e}. {hint}", err=True)
        return EXIT_DOWNLOAD

    def poll(self, url: str, terminal: tuple, kind: str):
        interval = self.ctx.a.poll_interval or (8.0 if kind == "video" else 4.0)
        max_wait = self.ctx.a.max_wait or (1800.0 if kind == "video" else 900.0)
        t0, n, last, st = time.time(), 0, None, {}
        while True:
            st = self.request("GET", url).json or {}
            n += 1
            s = st.get("status")
            if s != last:
                say(f"  [{self.label}] {time.time() - t0:6.1f} с  {s}")
                last = s
            if s in terminal or time.time() - t0 > max_wait:
                return st, n
            time.sleep(interval * random.uniform(0.85, 1.15))


def save_b64_items(run: Run, items: list, gen_id) -> list[dict]:
    files = []
    base = run.out_base(gen_id)
    for i, it in enumerate(items):
        b = base.with_name(base.name + (f"_{i + 1}" if len(items) > 1 else ""))
        if isinstance(it, dict) and it.get("b64_json"):
            data = base64.b64decode(it["b64_json"])
            info = save_bytes(b, data, "b64_json", it.get("media_type"))
        elif isinstance(it, dict) and isinstance(it.get("url"), str) and it["url"].startswith("data:"):
            data = base64.b64decode(it["url"].partition(",")[2])
            info = save_bytes(b, data, "data_url", it.get("media_type"))
        elif isinstance(it, dict) and isinstance(it.get("url"), str):
            info = run.http.download(it["url"], b, auth=True)
        else:
            continue
        if it.get("revised_prompt"):
            info["revised_prompt"] = it["revised_prompt"]
        files.append(info)
        say(f"  ↓ {info['path']}  ({info['bytes']} байт, {info['content_type']}, sha256 {info['sha256'][:16]}…)")
    return files


def sync_timeout(ctx: Ctx, kind: str) -> float:
    """Таймаут синхронного POST (генерация в ответе): --sync-timeout или по виду (картинки RouterAI до 300 с)."""
    st = getattr(ctx.a, "sync_timeout", None)
    return float(st) if st else max(ctx.a.http_timeout, SYNC_TIMEOUT[kind])


def run_ra_image(run: Run) -> int:
    p = run.prep
    try:
        r = run.request("POST", run.http.url("/v1/images"), body=p.body, timeout=sync_timeout(run.ctx, "ra-image"))
    except ApiError as e:
        return run.post_error(e)
    j = r.json or {}
    gen_id = r.headers.get("x-generation-id") or j.get("id") or f"ra_{p.uid}"
    cost = cost_of(j, "cost", "cost_rub")
    data = j.get("data") or []
    if not data:
        return run.fail(gen_id, "empty", cost, {"message": "в ответе нет data[] — картинок нет", "usage": j.get("usage")})
    try:
        files = save_b64_items(run, data, gen_id)
    except (ApiError, ValueError, OSError) as e:
        return run.download_error(gen_id, cost, e, "Картинки RouterAI приходят в ответе — повтор только новым запросом")
    if not files:
        return run.fail(gen_id, "empty", cost, {"message": "в data[] нет b64_json/url"})
    return run.finish(gen_id, files, cost, None, j)


def run_ra_video(run: Run) -> int:
    p = run.prep
    try:
        r = run.request("POST", run.http.url("/v1/videos"), body=p.body, retry_429_base=10.0, retries=7)
    except ApiError as e:
        return run.post_error(e)
    j = r.json or {}
    gen_id = j.get("id")
    run.ev("created", id=gen_id, status=j.get("status"), polling_url=j.get("polling_url"))
    say(f"  [{run.label}] создано {gen_id} (HTTP {r.status}, {j.get('status')}), оценка {fmt(p.estimate.get('rub'))} ₽")
    st, n = run.poll(run.http.url(f"/v1/videos/{gen_id}"), TERMINAL["ra-video"], "video")
    return ra_video_result(run, gen_id, st, j, n)


def ra_video_result(run: Run, gen_id, st: dict, create, polls) -> int:
    s = st.get("status")
    cost = cost_of(st, "cost", "cost_rub")
    if s not in TERMINAL["ra-video"]:
        run.ev("timeout", id=gen_id, status=s)
        say(f"  [{run.label}] ТАЙМАУТ опроса (статус {s}). Дожать: mp_client.py download {gen_id} --channel routerai "
            f"--live", err=True)
        return EXIT_TIMEOUT
    if s != "completed":
        return run.fail(gen_id, s, cost, st.get("error"))
    urls = st.get("unsigned_urls") or []
    if not urls:
        return run.download_error(gen_id, cost, "нет unsigned_urls", "проверьте status")
    files = []
    try:
        base = run.out_base(gen_id)
        for i, u in enumerate(urls):
            b = base.with_name(base.name + (f"_{i + 1}" if len(urls) > 1 else ""))
            info = run.http.download(u, b, auth=True)          # content-эндпоинт RouterAI — с ключом, только свой хост
            files.append(info)
            say(f"  ↓ {info['path']}  ({info['bytes']} байт, {info['content_type']})")
    except ApiError as e:
        return run.download_error(gen_id, cost, e, f"дожать: mp_client.py download {gen_id} --channel routerai --live "
                                                   f"(до статуса expired)")
    return run.finish(gen_id, files, cost, create, st, polls)


def run_genapi(run: Run) -> int:
    p = run.prep
    sync = p.kind == "ga-sync"
    try:
        r = run.request("POST", run.http.url(p.api_path), body=p.body,
                             timeout=sync_timeout(run.ctx, "ga-sync") if sync else None)
    except ApiError as e:
        return run.post_error(e)
    j = r.json or {}
    rid = j.get("request_id") or j.get("id")
    st, n = j, 0
    if j.get("status") not in TERMINAL["ga"]:
        run.ev("created", id=rid, status=j.get("status"))
        say(f"  [{run.label}] задача {rid} ({j.get('status')}), оценка {fmt(p.estimate.get('rub'))} ₽")
        st, n = run.poll(run.http.url(f"/v1/request/get/{rid}"), TERMINAL["ga"], "image")
    return genapi_result(run, rid, st, j, n)


def genapi_urls(st: dict) -> list[str]:
    urls = []

    def add(x):
        if isinstance(x, str) and x.startswith(("http://", "https://", "data:")):
            urls.append(x)
        elif isinstance(x, dict):
            for k in ("url", "image", "video", "file", "svg"):
                if isinstance(x.get(k), str):
                    add(x[k])
            # у части сетей Gen-API `result` — объект с номерами файлов, например Bria FIBO
            # `{"0": url, "structured_prompt": {…}}` — раньше ссылка не находилась и успех падал в «нет ссылок result/output»
            for k, v in x.items():
                if str(k).isdigit() or (isinstance(v, str) and v.startswith(("http://", "https://"))):
                    add(v)
        elif isinstance(x, list):
            for y in x:
                add(y)

    for key in ("result", "output", "full_response"):
        add(st.get(key))
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def genapi_result(run: Run, rid, st: dict, create, polls) -> int:
    s = st.get("status")
    cost = num(st.get("cost"))
    cost = float(cost) if cost is not None else None
    if s not in TERMINAL["ga"]:
        run.ev("timeout", id=rid, status=s)
        say(f"  [{run.label}] ТАЙМАУТ опроса (статус {s}). Дожать: mp_client.py download {rid} --channel genapi --live "
            f"(ссылки на файлы живут 24 ч, результат — 14 дней)", err=True)
        return EXIT_TIMEOUT
    if s != "success":
        return run.fail(rid, s, cost, st.get("error") or st.get("errors_validation") or st.get("result"))
    urls = genapi_urls(st)
    # структурные данные ответа (Bria FIBO `structured_prompt`; у `bria-fibo-prompt` — только они,
    # без файла) сохраняются JSON-файлом рядом, а не теряются и не валят успешную задачу
    res = st.get("result")
    extra_json = None
    if isinstance(res, dict):
        extra_json = {k: v for k, v in res.items() if not (str(k).isdigit() or (isinstance(v, str) and v.startswith(("http://", "https://"))))}
    elif isinstance(res, list) and not urls and res:
        extra_json = {"result": res}
    if not urls and not extra_json:
        return run.download_error(rid, cost, "в ответе success нет ссылок result/output", "проверьте status")
    files = []
    try:
        base = run.out_base(rid)
        for i, u in enumerate(urls):
            b = base.with_name(base.name + (f"_{i + 1}" if len(urls) > 1 else ""))
            if u.startswith("data:"):
                info = save_bytes(b, base64.b64decode(u.partition(",")[2]), "data_url")
            else:
                info = run.http.download(u, b, auth=False)       # хранилище Gen-API — без ключа
            files.append(info)
            say(f"  ↓ {info['path']}  ({info['bytes']} байт, {info['content_type']})")
        if extra_json:                                   # после файлов: паспорт называется по первому (картинке)
            info = save_bytes(base.with_name(base.name + ".result"), jdump(extra_json).encode("utf-8"), "result.json",
                              "application/json")
            files.append(info)
            say(f"  ↓ {info['path']}  ({info['bytes']} байт, структурный ответ)")
    except ApiError as e:
        return run.download_error(rid, cost, e, f"ссылки живут 24 ч; перезапросить: mp_client.py download {rid} "
                                                f"--channel genapi --live")
    return run.finish(rid, files, cost, create, st, polls, extra={"genapi": {k: st.get(k) for k in (
        "response_type", "runtime", "progress", "parameters")}})


def strip_fence(t: str) -> str:
    m = re.fullmatch(r"\s*```[\w-]*\s*\n(.*?)\n?```\s*", t, re.S)
    return m.group(1) if m else t


def run_chat(run: Run) -> int:
    p = run.prep
    try:
        r = run.request("POST", run.http.url("/v1/chat/completions"), body=p.body,
                             timeout=sync_timeout(run.ctx, "chat"))
    except ApiError as e:
        return run.post_error(e)
    j = r.json or {}
    gen_id = j.get("id") or f"chat_{p.uid}"
    cost = cost_of(j, "cost_rub", "cost")
    ch = (j.get("choices") or [{}])[0]
    msg = ch.get("message") or {}
    c = msg.get("content")
    text = c if isinstance(c, str) else "".join(str(x.get("text") or "") for x in (c or []) if isinstance(x, dict))
    files = []
    base = run.out_base(gen_id)
    if text:
        body_t = strip_fence(text)
        try:
            parsed = json.loads(body_t)
            info = save_bytes(base, jdump(parsed).encode("utf-8"), "message.content", "application/json")
        except json.JSONDecodeError:
            parsed = None
        if parsed is not None:
            pass
        elif sniff(body_t.encode("utf-8"))[0] == "image/svg+xml":
            info = save_bytes(base, body_t.encode("utf-8"), "message.content", "image/svg+xml")
        else:
            dest = base.with_name(base.name + ".md")
            dest.write_text(text, encoding="utf-8")
            info = {"path": rel(dest), "source": "message.content", "bytes": len(text.encode()),
                    "sha256": sha256_hex(text.encode()), "content_type": "text/markdown", "media": None}
        files.append(info)
        say(f"  ↓ {info['path']}  ({info['bytes']} байт, {info['content_type']})")
    imgs = msg.get("images") or []
    if imgs:
        files += save_b64_items(run, [{"url": (x.get("image_url") or {}).get("url")} for x in imgs
                                      if isinstance(x, dict)], gen_id + "_img")
    if not files:
        return run.fail(gen_id, ch.get("finish_reason") or "empty", cost, {"message": "пустой ответ", "choice": ch})
    u = j.get("usage") or {}
    extra = {"usage": u, "finish_reason": ch.get("finish_reason"), "provider": j.get("provider")}
    if ch.get("finish_reason") == "length":
        say(f"  [{run.label}] ! finish_reason=length — ответ обрезан потолком max_tokens", err=True)
    return run.finish(gen_id, files, cost, None, j, extra=extra)


def run_pz_image(run: Run) -> int:
    p = run.prep
    try:
        r = run.request("POST", run.http.url("/v2/images/generations"), body=p.body,
                             timeout=sync_timeout(run.ctx, "pz-image"))
    except ApiError as e:
        return run.post_error(e)
    j = r.json or {}
    if j.get("status") in ("pending", "processing") and j.get("id"):
        gid = j["id"]
        run.ev("created", id=gid, status=j.get("status"))
        say(f"  [{run.label}] > 120 с — асинхронно: {gid}; опрос /v1/media/{gid}")
        st, n = run.poll(run.http.url(f"/v1/media/{gid}"), TERMINAL["pz-media"], "image")
        return pz_media_result(run, gid, st, j, n)
    gen_id = j.get("id") or f"img_{p.uid}"
    cost = cost_of(j, "cost_rub", "cost")
    data = j.get("data") or []
    if not data:
        return run.fail(gen_id, "empty", cost, {"message": "в ответе нет data[]", "response": j})
    try:
        files = save_b64_items(run, data, gen_id)
    except ApiError as e:
        return run.download_error(gen_id, cost, e, "URL CDN polza живут 7 дней: скачайте вручную по ссылке из журнала")
    return run.finish(gen_id, files, cost, None, j)


def pz_media_urls(st: dict) -> list[str]:
    urls = []

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in ("url", "image_url", "video_url", "file_url") and isinstance(v, str) and v.startswith("http"):
                    urls.append(v)
                elif k == "urls" and isinstance(v, list):
                    urls.extend(u for u in v if isinstance(u, str))
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    for k in ("data", "output", "result"):
        walk((st or {}).get(k))
    return list(dict.fromkeys(urls))


def pz_media_result(run: Run, gid, st: dict, create, polls) -> int:
    s = st.get("status")
    cost = cost_of(st, "cost_rub", "cost")
    if s not in TERMINAL["pz-media"]:
        run.ev("timeout", id=gid, status=s)
        say(f"  [{run.label}] ТАЙМАУТ опроса. Дожать: mp_client.py download {gid} --channel polza-images --live", err=True)
        return EXIT_TIMEOUT
    if s != "completed":
        return run.fail(gid, s, cost, st.get("error"))
    files = []
    try:
        base = run.out_base(gid)
        urls = pz_media_urls(st)
        for i, u in enumerate(urls):
            b = base.with_name(base.name + (f"_{i + 1}" if len(urls) > 1 else ""))
            files.append(run.http.download(u, b, auth=False))
            say(f"  ↓ {files[-1]['path']}  ({files[-1]['bytes']} байт)")
    except ApiError as e:
        return run.download_error(gid, cost, e, f"дожать: mp_client.py download {gid} --channel polza-images --live")
    if not files:
        return run.download_error(gid, cost, "нет URL в data", "проверьте status")
    return run.finish(gid, files, cost, create, st, polls)


RUNNERS = {"ra-image": run_ra_image, "ra-video": run_ra_video, "ra-chat": run_chat, "chat": run_chat,
           "ga-task": run_genapi, "ga-sync": run_genapi, "pz-image": run_pz_image}


def run_prepared(ctx: Ctx, prep: Prepared, *, force=False) -> int:
    run = Run(ctx, prep, force)
    code = run.begin()
    if code is not None:
        return code
    try:
        return RUNNERS[prep.kind](run)
    except ApiError as e:            # сбой опроса (GET) после создания: резерв остаётся
        run.ev("unknown", code=e.code, message=e.message, http_status=e.status)
        say(f"  [{run.label}] ОШИБКА после создания: {e}; резерв оставлен — проверьте status", err=True)
        return EXIT_HTTP


# ---------------------------------------------------------------------------------------------------------------
# Печать сухого прогона и оценки
# ---------------------------------------------------------------------------------------------------------------

def print_issues(prep: Prepared, quiet_info=False):
    for i in prep.issues:
        if quiet_info and i["level"] == "info":
            continue
        mark = {"error": "✗", "warn": "!", "info": "·"}[i["level"]]
        say(f"#   {mark} [{i['level']}] {i['param']}: {i['msg']}")


def print_plan(ctx: Ctx, prep: Prepared, show_request=True, quiet_info=False):
    e = prep.estimate
    j = prep.job
    say(f"# ── {prep.tag} · {prep.channel} · {prep.model or '—'} · агент {prep.agent}"
        + (f" · вариант {j.get('variant')}" if j.get("variant") is not None else "")
        + f"  [{j.get('_file')}#{j.get('_index')}]")
    if show_request and prep.channel in CHANNELS:
        ctx.http(prep.channel).show("POST", ctx.http(prep.channel).url(prep.api_path or ""), prep.body)
    rng = ""
    if e.get("rub_low") is not None and e.get("rub_high") is not None and abs(e["rub_high"] - (e["rub_low"] or 0)) > 1e-6:
        rng = f" (диапазон {fmt(e['rub_low'])}–{fmt(e['rub_high'])} ₽)"
    say(f"# Оценка: {fmt(e.get('rub'))} ₽{rng} — {e.get('formula') or '—'}")
    if j.get("price_rub") is not None:
        say(f"#   заявлено в задании: price_rub {fmt(j.get('price_rub'))} ₽, max_rub {fmt(j.get('max_rub'))} ₽")
    for w in e.get("warnings") or []:
        say(f"#   ! цена: {w}")
    print_issues(prep, quiet_info)
    if prep.channel in CHANNELS:
        ok, msg = budget_check(ctx, prep)
        say(f"# {'Лимиты OK' if ok else 'ОТКАЗ при --live'}: {msg}")
        hit = ctx.ledger.find_cached(prep.request_hash, ctx.base(prep.channel))
        say(f"# Кэш: {'есть — ' + str(hit.get('files')) if hit else 'нет'} (хэш {prep.request_hash[:16]}…); "
            f"ключ {prep.channel}: {ctx.key_status(prep.channel)}")


# ---------------------------------------------------------------------------------------------------------------
# Команды
# ---------------------------------------------------------------------------------------------------------------

def collect(ctx: Ctx, files: list[str], pick=None) -> list[Prepared]:
    preps = []
    for f in files:
        for j in pick_jobs(load_jobs(f), pick):
            preps.append(prepare(ctx, j))
    return preps


def catalog_notes(ctx: Ctx) -> list[tuple[str, bool]]:
    """Снимки каталогов, по которым считалась оценка: (строка с папкой и возрастом, отметка «свериться»). Берутся
    только каталоги, которые оценка прочитала."""
    out = []
    for cat, name, refresh in ((ctx._ra, "RouterAI", "mp_client.py snapshot --channel routerai"),
                               (ctx._ga, "Gen-API", "mp_client.py snapshot --channel genapi")):
        if cat is not None:
            out.append(pc.age_note(f"{name} {cat.path.parent.name}", cat.fetched,
                                   (cat.path.parent / "snapshot.meta.json").exists(), refresh))
    if ctx._pz is not None:
        out.append(pc.snapshot_note(ctx._pz))
    return out


def say_catalogs(ctx: Ctx):
    for note, check in catalog_notes(ctx):
        say(("# ! " if check else "# ") + note)


def cmd_estimate(ctx: Ctx, a):
    preps = collect(ctx, a.jobs, a.pick)
    total, by_scope, bad, tpl, refused, rows = 0.0, {}, 0, 0, 0, []
    for p in preps:
        if not a.json:
            if a.summary:
                e = p.estimate
                ok, msg = budget_check(ctx, p)
                say(f"{'✗' if p.errors else ('T' if p.templates else '·')} {p.tag[:44]:44} {p.channel:12} "
                    f"{str(p.model)[:36]:36} {fmt(e.get('rub')):>8} ₽ ≤ {fmt(e.get('rub_high')):>8} ₽  "
                    f"max {fmt(p.job.get('max_rub')):>6}  {'OK' if ok else 'ОТКАЗ: ' + msg[:70]}")
            else:
                print_plan(ctx, p, show_request=a.verbose, quiet_info=not a.verbose)
                say("")
        bad += bool(p.errors)
        tpl += bool(p.templates)
        rub = p.estimate.get("rub") or 0.0
        total += rub
        by_scope[p.channel] = by_scope.get(p.channel, 0.0) + rub
        ok, msg = budget_check(ctx, p) if p.channel in CHANNELS else (False, "канал")
        refused += not ok
        rows.append({"file": p.job.get("_file"), "index": p.job.get("_index"), "tag": p.tag, "channel": p.channel,
                     "kind": p.kind, "model": p.model, "rub": p.estimate.get("rub"),
                     "rub_low": p.estimate.get("rub_low"), "rub_high": p.estimate.get("rub_high"),
                     "price_rub": p.job.get("price_rub"), "max_rub": p.job.get("max_rub"),
                     "errors": [f"{i['param']}: {i['msg']}" for i in p.errors],
                     "warnings": [f"{i['param']}: {i['msg']}" for i in p.issues if i["level"] == "warn"]
                     + p.estimate.get("warnings", []),
                     "template": bool(p.templates), "filled": p.filled, "limits_ok": ok, "limits_msg": msg,
                     "formula": p.estimate.get("formula"), "request_hash": p.request_hash})
    if a.json:
        say(jdump({"client": VERSION, "at": now_iso(), "jobs": rows, "total_rub": round(total, 4),
                   "by_channel": {k: round(v, 4) for k, v in by_scope.items()}, "with_errors": bad,
                   "templates": tpl, "limits_refused": refused,
                   "catalogs": [{"note": n, "check": c} for n, c in catalog_notes(ctx)]}))
    else:
        parts = " · ".join(f"{k} {fmt(v)}" for k, v in sorted(by_scope.items()))
        say(f"# ИТОГО: файлов {len(a.jobs)}, заданий {len(preps)}, с ошибками {bad}, шаблонов {tpl}; оценка "
            f"{fmt(total)} ₽ ({parts}); отказов лимитов при --live: {refused}")
        say_catalogs(ctx)
    return EXIT_JOB if bad else EXIT_OK


def cmd_run(ctx: Ctx, a):
    jobs = pick_jobs(load_jobs(a.job), a.pick)
    if len(jobs) != 1:
        raise SystemExit(f"run принимает одно задание (в файле {len(jobs)}; выберите --pick TAG|N|/re/ или batch)")
    prep = prepare(ctx, jobs[0])
    say_catalogs(ctx)
    if not ctx.live:
        say("# СУХОЙ ПРОГОН — ничего не отправлено (для реального вызова добавьте --live)")
        print_plan(ctx, prep)
        if prep.errors:
            return EXIT_JOB
        return EXIT_OK if budget_check(ctx, prep)[0] else EXIT_BUDGET
    if prep.errors and not a.no_validate:
        print_plan(ctx, prep, show_request=False)
        say("# ОТКАЗ: ошибки проверки (обойти: --no-validate)", err=True)
        return EXIT_JOB
    if prep.templates:
        print_plan(ctx, prep, show_request=False)
        say("# ОТКАЗ: задание — шаблон; подставьте значения (--set ИМЯ=значение, --set-file ИМЯ=путь)", err=True)
        return EXIT_JOB
    if prep.kind not in RUNNERS:
        say(f"# ОТКАЗ: вид задания {prep.kind!r} не исполняется", err=True)
        return EXIT_JOB
    say(f"# ЖИВОЙ ВЫЗОВ → {prep.channel} {ctx.base(prep.channel)}")
    print_plan(ctx, prep, show_request=False, quiet_info=True)
    if prep.scope == "polza":
        preflight_polza(ctx, price_for_limits(ctx, prep))
    return run_prepared(ctx, prep, force=a.force)


def cmd_batch(ctx: Ctx, a):
    preps = collect(ctx, a.jobs, a.pick)
    bad = [p for p in preps if (p.errors and not a.no_validate) or p.templates or p.kind not in RUNNERS]
    for p in preps:
        print_plan(ctx, p, show_request=not ctx.live and a.verbose, quiet_info=True)
        say("")
    par = max(1, min(a.parallel, MAX_PARALLEL))
    need = {}
    for p in preps:
        if p.channel in CHANNELS and p not in bad:
            need[p.channel] = need.get(p.channel, 0.0) + (price_for_limits(ctx, p) or 0.0)
    say(f"# СЕРИЯ: {len(preps)} заданий, к исполнению {len(preps) - len(bad)}, с ошибками или шаблонов {len(bad)}; "
        f"параллельно {par}; лимит по каналам: " + ", ".join(f"{k} {fmt(v)} ₽" for k, v in need.items()))
    say_catalogs(ctx)
    if bad and not a.skip_bad:
        say("# ОТКАЗ: исправьте ошибки и шаблоны (или --skip-bad — пропустить их)", err=True)
        return EXIT_JOB
    todo = [p for p in preps if p not in bad]
    for ch in need:
        total = ctx.budget_total(ch)
        spent = ctx.ledger.spent(ctx.base(ch))
        grp = sum(need[c] for c in need if ctx.base(c) == ctx.base(ch))
        if spent + grp > total + 1e-9:
            say(f"# ОТКАЗ: серия {fmt(grp)} ₽ не помещается в бюджет {CHANNELS[ch]['budget_env']} "
                f"(потрачено {fmt(spent)} из {fmt(total)} ₽)", err=True)
            return EXIT_BUDGET
    if not ctx.live:
        say("# СУХОЙ ПРОГОН серии — ничего не отправлено (--live для реального вызова)")
        return EXIT_OK
    if any(p.scope == "polza" for p in todo):
        preflight_polza(ctx, sum(v for c, v in need.items() if CHANNELS[c]["scope"] == "polza"))

    def worker(p):
        if ctx.stop[p.scope].is_set():
            say(f"  [{p.label}] пропущено: канал остановлен после 401/402/403", err=True)
            return EXIT_HTTP
        try:
            return run_prepared(ctx, p, force=a.force)
        except Exception as e:  # noqa: BLE001
            say(f"  [{p.label}] исключение: {e}", err=True)
            return EXIT_HTTP

    with cf.ThreadPoolExecutor(max_workers=par) as ex:
        codes = list(ex.map(worker, todo))
    say(f"# СЕРИЯ ГОТОВА: коды {codes}")
    return max(codes) if codes else EXIT_OK


def status_url(ctx: Ctx, ch: str, gid: str) -> tuple[str, tuple]:
    if ch == "routerai":
        return ctx.http(ch).url(f"/v1/videos/{gid}"), TERMINAL["ra-video"]
    if ch == "genapi":
        return ctx.http(ch).url(f"/v1/request/get/{gid}"), TERMINAL["ga"]
    if ch == "polza-images":
        return ctx.http(ch).url(f"/v1/media/{gid}"), TERMINAL["pz-media"]
    return ctx.http(ch).url(f"/v1/history/generations/{gid}"), ()


def cmd_status(ctx: Ctx, a):
    url, term = status_url(ctx, a.channel, a.id)
    if not ctx.live:
        say("# СУХОЙ ПРОГОН (GET бесплатен, но с ключом — только с --live)")
        ctx.http(a.channel).show("GET", url)
        return EXIT_OK
    st = ctx.http(a.channel).request("GET", url).json or {}
    say(jdump(redact_obj(shorten(st))))
    j = ctx.ledger.find_by_id(a.id, ctx.base(a.channel))
    s = st.get("status")
    if j and term and s in term and s not in ("completed", "success") and j.get("state") not in ("failed", "cancelled"):
        ctx.ledger.append({"event": "cancelled" if s == "cancelled" else "failed", "uid": j["uid"], "id": a.id,
                           "status": s, "cost_rub": num(st.get("cost")) or cost_of(st, "cost", "cost_rub") or 0.0,
                           "error": shorten(st.get("error")), "base_url": ctx.base(a.channel), "channel": a.channel})
    return EXIT_OK


def cmd_download(ctx: Ctx, a):
    ch = a.channel
    if ch == "polza-chat":
        say("polza-chat синхронный: ответ сохраняется при run; повторно скачать нечего")
        return EXIT_JOB
    url, term = status_url(ctx, ch, a.id)
    if not ctx.live:
        say("# СУХОЙ ПРОГОН")
        ctx.http(ch).show("GET", url, note="# затем скачивание результата и паспорт")
        return EXIT_OK
    j = ctx.ledger.find_by_id(a.id, ctx.base(ch)) or {}
    job = {"tag": a.tag or j.get("tag") or "download", "agent": j.get("agent") or ctx.default_agent, "channel": ch,
           "_file": "download", "_index": 1}
    prep = Prepared(job, ctx)
    prep.uid = j.get("uid") or ("dl_" + uuid.uuid4().hex[:10])
    prep.model = a.model or j.get("model") or "model"
    prep.request_hash = j.get("request_hash") or ""
    prep.kind = {"routerai": "ra-video", "genapi": "ga-task", "polza-images": "pz-image"}[ch]
    prep.api_path = j.get("path") or {"routerai": "/v1/videos", "genapi": "/v1/networks/?",
                                      "polza-images": "/v2/images/generations"}[ch]
    if j.get("estimate_rub") is not None:
        prep.estimate.update(rub=j["estimate_rub"], rub_high=j["estimate_rub"])
    run = Run(ctx, prep, force=True)
    run.download_note = f"скачано командой download {a.id} (запрос — в журнале по uid {prep.uid})"
    st = run.request("GET", url).json or {}
    if ch == "routerai":
        return ra_video_result(run, a.id, st, None, 0)
    if ch == "genapi":
        return genapi_result(run, a.id, st, None, 0)
    return pz_media_result(run, a.id, st, None, 0)


def ledger_channel(ctx: Ctx, j: dict) -> str:
    if j.get("channel"):
        return j["channel"]
    return "polza-media" if j.get("base_url") == ctx.base("polza-chat") else "?"


def cmd_ledger(ctx: Ctx, a):
    js = list(ctx.ledger.jobs().values())
    if a.agent:
        js = [j for j in js if j.get("agent") == a.agent]
    if a.channel:
        js = [j for j in js if ledger_channel(ctx, j) == a.channel]
    if a.sum:
        by = {}
        for j in js:
            key = (ledger_channel(ctx, j), j.get("base_url"), j.get("agent"))
            b = by.setdefault(key, {"jobs": 0, "spent": 0.0, "completed": 0, "failed": 0, "reserved": 0.0})
            b["jobs"] += 1
            b["spent"] += j["spent"]
            b["completed"] += j.get("state") == "completed"
            b["failed"] += j.get("state") in ("failed", "cancelled", "http_error")
            if j.get("state") in ("submit", "created", "timeout", "unknown"):
                b["reserved"] += j["spent"]
        say(f"{'канал':13} {'base_url':32} {'агент':8} {'заданий':>7} {'готово':>6} {'ошибок':>6} {'₽ всего':>10} "
            f"{'₽ резерв':>9}")
        for (ch, bu, ag), b in sorted(by.items(), key=lambda x: tuple(str(v) for v in x[0])):
            say(f"{ch:13} {str(bu):32} {str(ag):8} {b['jobs']:>7} {b['completed']:>6} {b['failed']:>6} "
                f"{fmt(b['spent']):>10} {fmt(b['reserved']):>9}")
        for scope, ch in SCOPE_CHANNEL.items():
            say(f"# {CHANNELS[ch]['budget_env']}: {fmt(ctx.budget_total(ch))} ₽; потрачено/в резерве "
                f"{fmt(ctx.ledger.spent(ctx.base(ch)))} ₽ ({ctx.base(ch)})")
        say(f"# журнал {ctx.ledger.path}")
        return EXIT_OK
    uids = {j["uid"] for j in js}
    by_uid = {j["uid"]: j for j in js}
    evs = [e for e in ctx.ledger.events() if e.get("uid") in uids]
    for e in evs[-a.tail:]:
        j = by_uid.get(e.get("uid"), {})
        e = {**{k: j.get(k) for k in ("agent", "tag", "model", "channel") if j.get(k)}, **e}
        say(json.dumps(e, ensure_ascii=False) if a.json else
            f"{e.get('ts')} {e.get('event'):10} {str(e.get('channel') or ledger_channel(ctx, j)):12} "
            f"{str(e.get('agent') or ''):6} {str(e.get('tag') or '')[:28]:28} {str(e.get('model') or '')[:30]:30} "
            f"{str(e.get('id') or '')[:22]:22} "
            f"{('оценка ' + fmt(e['estimate_rub'])) if e.get('estimate_rub') is not None else ''} "
            f"{('цена ' + fmt(e['cost_rub'])) if e.get('cost_rub') is not None else ''}")
    return EXIT_OK


def cmd_show(ctx: Ctx, a):
    ch = a.channel
    if ch == "routerai":
        m = ctx.ra.models.get(a.model)
        if not m:
            raise SystemExit(f"нет в {ctx.ra.label}; похожие: {ctx.ra.near(a.model)}")
        say(f"{m['id']} — {m.get('name')} · {(m.get('architecture') or {}).get('modality')} · {ctx.ra.label}")
        for k in ("supported_parameters", "supported_aspect_ratios", "supported_resolutions", "supported_sizes",
                  "supported_qualities", "supported_backgrounds", "supported_output_formats", "max_image_count",
                  "max_image_references", "image_seed", "supports_negative_prompt", "supported_durations",
                  "supported_frame_images", "generate_audio", "seed", "pricing", "pricing_units", "image_pricing"):
            if m.get(k) is not None:
                say(f"  {k:26} {json.dumps(m[k], ensure_ascii=False)}")
        for e in ctx.ra.ep(a.model):
            say(f"  OpenRouter {e.get('provider_slug')}: passthrough {e.get('allowed_passthrough_parameters')}; "
                f"цены {json.dumps(e.get('pricing'), ensure_ascii=False)}")
        say(f"  курс к OpenRouter: {ctx.ra.fx(a.model):.3f} ₽/$")
    elif ch == "genapi":
        n = ctx.ga.nets.get(a.model)
        if not n:
            raise SystemExit(f"сети {a.model!r} нет в {ctx.ga.label}")
        say(f"{a.model} — {n.get('name')} · cost {n.get('cost')} ₽ · is_payment_upfront {n.get('is_payment_upfront')} · "
            f"{ctx.ga.label}")
        for p in n.get("parameters") or []:
            say(f"  {p.get('title'):26} {str(p.get('type')):34} default {str(p.get('default')):10} "
                f"{'ОБЯЗ. ' if p.get('required') else ''}{p.get('items') or ''}")
        for r in genapi_table(ctx.ga.prices.get(a.model)):
            say(f"  прайс: {json.dumps(r, ensure_ascii=False)}")
    else:
        m = ctx.pz.by_id.get(a.model)
        if not m:
            raise SystemExit(f"нет в каталоге polza {ctx.pz.dir.name}")
        tp = m.get("top_provider") or {}
        say(f"{m['id']} — {m.get('name')} · {m.get('type')} · провайдер {tp.get('name')} · эндпоинты {m.get('endpoints')}")
        say(f"  вход {(m.get('architecture') or {}).get('input_modalities')}; контекст {tp.get('context_length')}; "
            f"max_completion {tp.get('max_completion_tokens')}")
        say(f"  цены: {json.dumps(tp.get('pricing'), ensure_ascii=False)}")
        say(f"  supported_parameters: {tp.get('supported_parameters')}")
    return EXIT_OK


SNAPSHOT_FILES = {"routerai": ("/v1/models", "api-v1-models.json"),
                  "genapi": ("/v1/networks?include=parameters", "networks-include-parameters.json")}


def public_get(url: str, timeout: float = 90):
    """Публичный GET без ключа → (статус, заголовки, тело)."""
    req = urllib.request.Request(url, headers={"User-Agent": VERSION, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers.items()), r.read()


def take_snapshot(root: Path, ch: str, url: str, *, get=public_get, stamp: dt.datetime | None = None,
                  tries: int = pc.SNAPSHOT_TRIES, retry_pause: float = 2.0) -> tuple[Path, int, int]:
    """Снимок публичного каталога канала в root/<канал>/<дата_ЧЧММ>/ → (папка, байт, записей). Файл и метаданные
    пишутся во временную папку рядом и встают на место одним переименованием: пустая или недописанная папка стала бы
    «последним снимком» для оценок. Оборванный запрос повторяется (tries попыток). Попытки кончились, ответ не 200
    или не каталог — pc.SnapshotError; временная папка убирается, папки снимка нет."""
    stamp = stamp or dt.datetime.now(pc.MSK)
    fname = SNAPSHOT_FILES[ch][1]
    home = root / ch
    d = home / stamp.strftime("%Y-%m-%d_%H%M")
    if d.exists():
        raise pc.SnapshotError(f"папка уже существует: {d} — повторите через минуту")
    home.mkdir(parents=True, exist_ok=True)
    tmp = home / f".snapshot-{stamp:%Y%m%d-%H%M%S}-{os.getpid()}.part"
    tmp.mkdir()
    try:
        t0 = time.time()
        status, headers, body = pc.get_retry(get, url, fname, tries, retry_pause)
        try:
            data = json.loads(body)
        except ValueError:
            data = None
        items = data.get("data", data) if isinstance(data, dict) else data
        if status != 200 or not isinstance(items, (list, dict)) or not items:
            raise pc.SnapshotError(f"{fname}: ответ {status}, {len(body)} байт — не каталог ← {url}")
        (tmp / fname).write_bytes(body)
        hdr = {k.lower(): v for k, v in headers.items() if k.lower() != "set-cookie"}
        (tmp / "snapshot.meta.json").write_text(jdump({
            "tool": VERSION, "fetched_at_msk": stamp.isoformat(timespec="seconds"),
            "files": {fname: {"url": url, "status": status, "bytes": len(body), "sha256": sha256_hex(body),
                              "seconds": round(time.time() - t0, 2), "headers": hdr}},
            "note": "публичный GET без ключа; заголовки set-cookie не сохраняются"}), encoding="utf-8")
        tmp.rename(d)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return d, len(body), len(items)


def cmd_snapshot(ctx: Ctx, a):
    """Публичные каталоги без ключа (бесплатно): RouterAI /v1/models, Gen-API /v1/networks?include=parameters."""
    todo = ["routerai", "genapi"] if a.channel == "all" else [a.channel]
    stamp = dt.datetime.now(pc.MSK)
    root = Path(a.dest) if a.dest else CACHE
    code = EXIT_OK
    for ch in todo:
        url = ctx.base(ch) + SNAPSHOT_FILES[ch][0]
        try:
            d, size, n = take_snapshot(root, ch, url, stamp=stamp)
        except pc.SnapshotError as e:
            say(f"{ch}: снимок не снят: {e}; папки снимка нет, последним остаётся снимок до запуска — повторите позже",
                err=True)
            code = EXIT_JOB
            continue
        say(f"{ch}: {url} → {rel(d / SNAPSHOT_FILES[ch][1])} ({size} байт, {n} записей)")
    return code


# адреса чтения баланса и лимита ключа (GET с ключом, не трата); у канала без строки адрес называет ключ --path
BALANCE_PATHS = {"polza-chat": ("/v2/balance", "/v1/key"), "polza-images": ("/v2/balance", "/v1/key")}


def balance_fields(resp) -> dict:
    """Числа ответа канала о балансе и лимитах: поля верхнего уровня и вложенного объекта data, значение — число или
    строка с числом. Имена полей — как в ответе канала."""
    out = {}

    def take(obj: dict, prefix: str = ""):
        for k, v in obj.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[prefix + k] = float(v)
            elif isinstance(v, str) and num(v) is not None:
                out[prefix + k] = float(num(v))

    if isinstance(resp, dict):
        take(resp)
        if isinstance(resp.get("data"), dict):
            take(resp["data"], "data.")
    return out


def read_balance(http, paths) -> list[tuple[str, object, dict]]:
    """GET по каждому адресу → (адрес, ответ, числа ответа)."""
    out = []
    for p in paths:
        j = http.request("GET", http.url(api_path(p))).json
        out.append((api_path(p), j, balance_fields(j)))
    return out


def cmd_balance(ctx: Ctx, a):
    """Баланс и лимит ключа канала — чтение, не трата: запрос с ключом идёт и без --live."""
    ch = a.channel
    paths = [a.path] if a.path else list(BALANCE_PATHS.get(ch) or ())
    if not paths:
        say(f"{ch}: адрес чтения баланса канала не задан — задайте его ключом --path (GET из документации кабинета "
            f"канала, например --path /v1/…); у polza-chat и polza-images адреса известны", err=True)
        return EXIT_USAGE
    for p, j, nums in read_balance(ctx.http(ch, read=True), paths):
        say(f"# {ch} GET {p}")
        say(jdump(redact_obj(shorten(j))))
        if nums:
            say("# числа ответа: " + ", ".join(f"{k} {v:g}" for k, v in nums.items()))
    return EXIT_OK


# ---------------------------------------------------------------------------------------------------------------
# Самопроверка без сети
# ---------------------------------------------------------------------------------------------------------------

class _Reply:
    """Канал самопроверки: один ответ на любой запрос, сети нет."""

    def __init__(self, status: int, headers: dict, body: bytes):
        self.resp = Resp(status, headers, body)

    def url(self, path: str) -> str:
        return "https://channel.test/api" + path

    def request(self, method: str, url: str, **kw) -> Resp:
        return self.resp


def cmd_selftest(ctx: Ctx, a):
    global CACHE
    res, skipped = [], []

    def ok(name, cond, got=""):
        res.append((name, bool(cond), got))

    def skip(name, why):
        skipped.append((name, why))

    def missing(prop: str) -> str | None:
        """Почему снимка каталога канала нет; None — снимок на месте."""
        try:
            getattr(ctx, prop)
        except SystemExit as e:
            return str(e)
        return None

    no_ra, no_ga, no_pz = missing("ra"), missing("ga"), missing("pz")

    # 1. формула токенов GPT Image = таблица калькулятора OpenAI
    for fam, w, h, q, exp in [("gpt-image-2.5", 1024, 1024, "medium", 439), ("gpt-image-2.5", 1024, 1024, "high", 1756),
                              ("gpt-image-2.5", 1024, 1024, "max", 7024), ("gpt-image-2.5", 3840, 2160, "high", 3336),
                              ("gpt-image-2.5", 1536, 864, "medium", 280), ("gpt-image-2", 1024, 1024, "medium", 1756),
                              ("gpt-image-2", 1536, 1024, "high", 5488), ("gpt-image-2.5", 1200, 640, "low", 100)]:
        got = gpt_image_tokens(fam, w, h, q)
        ok(f"токены {fam} {w}×{h} {q} = {exp}", got == exp, got)
    ok("vision OpenAI 1024² = 765 ток.", openai_image_tokens(1024, 1024) == 765, openai_image_tokens(1024, 1024))
    ok("vision Gemini 1940×424 = 774 ток.", vision_tokens("google/gemini-3-flash-preview", 1940, 424)[0] == 774)
    # 2. сигнатуры
    png = b"\x89PNG\r\n\x1a\n" + b"\0" * 32
    ok("sniff PNG", sniff(png)[1] == ".png")
    ok("sniff SVG с <?xml", sniff(b'<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg"/>')[1] == ".svg")
    ok("sniff SVG", sniff(b'<svg viewBox="0 0 1 1"></svg>')[1] == ".svg")
    ok("sniff MP4", sniff(b"\0\0\0\x18ftypisom" + b"\0" * 16)[1] == ".mp4")
    ok("sniff JPEG", sniff(b"\xff\xd8\xff\xe0" + b"\0" * 16)[1] == ".jpg")
    ok("sniff WebP", sniff(b"RIFF\0\0\0\0WEBPVP8 ")[1] == ".webp")
    _glb_js = json.dumps({"asset": {"version": "2.0"}, "accessors": [{"count": 6}], "meshes": [{"primitives": [
        {"attributes": {"POSITION": 0}, "indices": 0}]}], "materials": [{}]}).encode()
    _glb_js += b" " * (-len(_glb_js) % 4)
    _glb = b"glTF" + (2).to_bytes(4, "little") + (20 + len(_glb_js)).to_bytes(4, "little") + \
        len(_glb_js).to_bytes(4, "little") + b"JSON" + _glb_js
    ok("sniff GLB → .glb", sniff(_glb)[1] == ".glb")
    ok("паспорт GLB: 2 треуг., metallic 1.0 по умолчанию", glb_info(_glb).get("triangles") == 2 and
       glb_info(_glb)["materials"][0]["metallic"] == 1.0, glb_info(_glb))
    ok("3D-сети Gen-API узнаются по имени: trellis-2, tripo-3d, hunyuan-3d, meshy-v7, rodin, hi3d-v3",
       all(ga_is_3d(x, {}) for x in ("trellis-2", "tripo-3d", "hunyuan-3d", "hunyuan-3d-multi-view", "meshy-v7", "rodin", "hi3d-v3")))
    ok("3D-сеть Gen-API узнаётся по формату выхода каталога (fbx, glb)",
       ga_is_3d("new-mesh-net", {"output_format": {"items": ["fbx", "dict"]}}) and not ga_is_3d("flux-2", {"output_format": {"items": ["png"]}}))
    ok("картиночные сети Gen-API — не 3D: flux-2, recraft-v4, hunyuan-image-v3",
       not any(ga_is_3d(x, {}) for x in ("flux-2", "recraft-v4", "hunyuan-image-v3")))
    p = prepare(ctx, {"channel": "polza-chat", "path": "/api/v1/chat/completions", "_dir": ".", "_file": "st", "_index": 1,
                      "tag": "st", "max_rub": 1, "meta": {"judge": "vlm", "mode": "pairwise"},
                      "body": {"model": "x", "messages": [{"role": "user", "content": "x"}]}})
    ok("задание оценки по рубрике — ошибка задания (оценку делает сессия Opus по пакету)",
       any(i["param"] == "задание" and "design-judge" in i["msg"] for i in p.errors), p.errors[:1])
    # 3. пути и база
    ok("api_path /api/v1/images → /v1/images", api_path("/api/v1/images") == "/v1/images")
    ok("api_path /v2/images/generations", api_path("v2/images/generations") == "/v2/images/generations")
    ok("norm_base добавляет /api", norm_base("https://routerai.ru/") == "https://routerai.ru/api")
    # 4. ключи
    add_secret("sk-selftest-0123456789")
    ok("redact строки", redact("Bearer sk-selftest-0123456789 x") == "Bearer *** x")
    ok("redact заголовка", redact_obj({"Authorization": "Bearer abc"})["Authorization"] == "***")
    _SECRETS.discard("sk-selftest-0123456789")
    # 5. шаблоны
    body, used, missing = fill_templates({"model": "{{M}}", "x": ["a {{N}} b"]}, {"M": "google/x"})
    ok("шаблон: подставлен M, не подставлен N", body["model"] == "google/x" and missing == {"N"} and used == {"M"})
    ok("угловой шаблон в поле файла", bool(ANGLE_RE.match("<картинка под хэшем>")))
    ok("shorten data:URI", shorten("data:image/png;base64," + "A" * 400).startswith("<image/png;base64:"))
    ok("shorten b64_json", shorten({"b64_json": "A" * 300})["b64_json"].startswith("<base64:"))
    # 6. журнал совместим с polza.py
    with tempfile.TemporaryDirectory() as td:
        lp = Path(td) / "ledger.jsonl"
        led = Ledger(lp)
        base = "http://x/api"
        led.append({"event": "submit", "uid": "a1", "base_url": base, "estimate_rub": 5.0, "agent": "G"})
        led.append({"event": "completed", "uid": "a1", "base_url": base, "cost_rub": 4.0})
        led.append({"event": "submit", "uid": "a2", "base_url": base, "estimate_rub": 3.0, "agent": "G"})
        led.append({"event": "failed", "uid": "a3", "base_url": base, "cost_rub": 0.0})
        led.append({"event": "submit", "uid": "a4", "base_url": base, "estimate_rub": 9.0})
        led.append({"event": "http_error", "uid": "a4", "base_url": base})
        mine = led.spent(base)
        try:
            import polza as pzmod
            theirs = pzmod.Ledger(lp).spent(base)
        except Exception as e:  # noqa: BLE001
            theirs = f"import polza: {e}"
        ok("журнал: трата как у polza.py (4 + резерв 3)", mine == 7.0 and theirs == 7.0, f"{mine} / {theirs}")
    # 7. хэш: путь и тот же файл base64 — одинаково
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "a.png"
        f.write_bytes(png)
        j1 = {"channel": "routerai", "path": "/api/v1/images", "_dir": td, "_file": "t", "_index": 1, "tag": "t",
              "body": {"model": "recraft/recraft-v4-styles", "prompt": "p", "aspect_ratio": "1:1", "n": 1,
                       "input_references": [{"type": "image_url", "image_url": {"url": "a.png"}}]}}
        j2 = json.loads(json.dumps(j1))
        j2["body"]["input_references"][0]["image_url"]["url"] = "data:image/png;base64," + base64.b64encode(png).decode()
        if no_ra:
            skip("хэш: локальный путь = тот же файл в base64", no_ra)
        else:
            h1, h2 = prepare(ctx, j1).request_hash, prepare(ctx, j2).request_hash
            ok("хэш: локальный путь = тот же файл в base64", h1 == h2)
    # 8. отказ канала: тело и заголовки ответа — в паспорте задания
    with tempfile.TemporaryDirectory() as td:
        saved = (ctx.ledger, ctx.out_root, ctx.a.budget_total)
        ctx.ledger, ctx.out_root, ctx.a.budget_total = Ledger(Path(td) / "ledger.jsonl"), Path(td) / "out", 100.0
        try:
            def refused(tag, headers, body):
                p = Prepared({"channel": "routerai", "tag": tag, "_file": "st", "_index": 1, "max_rub": 10}, ctx)
                p.kind, p.model, p.api_path, p.request_hash = "ra-image", "demo/vector", "/v1/images", tag
                p.body = {"model": "demo/vector", "prompt": "x", "n": 1, "output_format": "svg"}
                p.estimate.update(rub=1.0, rub_low=1.0, rub_high=1.0)
                run = Run(ctx, p, force=True)
                run.http = _Reply(200, headers, body)
                with contextlib.redirect_stderr(io.StringIO()):       # строка отказа — не итог самопроверки
                    code = run.begin() or run_ra_image(run)
                job = ctx.ledger.jobs().get(p.uid) or {}
                pas = json.loads(absp(job["passport"]).read_text(encoding="utf-8")) if job.get("passport") else {}
                return code, job, pas.get("response") or {}

            code, job, resp = refused("st-empty", {"Content-Type": "application/json", "X-Generation-Id": "gen-demo",
                                                   "Set-Cookie": "sid=1"},
                                      json.dumps({"data": [], "usage": {"cost": 0}, "detail": "format is not accepted"}).encode())
            ok("ответ без картинок: код 5, запись failed с паспортом", code == EXIT_FAILED and job.get("state") == "failed"
               and job.get("spent") == 0.0 and bool(resp), (code, job))
            ok("паспорт отказа: тело и заголовки ответа канала, cookie не сохранён",
               resp.get("http_status") == 200 and (resp.get("body") or {}).get("detail") == "format is not accepted"
               and (resp.get("headers") or {}).get("x-generation-id") == "gen-demo"
               and "set-cookie" not in (resp.get("headers") or {}), resp)
            code, job, resp = refused("st-html", {"Content-Type": "text/html"}, b"<html>upstream error</html>")
            ok("ответ не JSON: в паспорте текст тела, длина и sha256",
               code == EXIT_FAILED and resp.get("body") == "<html>upstream error</html>" and resp.get("bytes") == 27
               and len(resp.get("sha256") or "") == 64, resp)
        finally:
            ctx.ledger, ctx.out_root, ctx.a.budget_total = saved
    # 9. оценки против цен, посчитанных из полей тех же снимков каталогов: случай не зависит от даты снимка; снимка
    #    канала нет или каталог сменил устройство цены — случай пропускается
    def ra_field(mid):
        m = ctx.ra.models.get(mid)
        if m is None:
            raise LookupError("модели нет в каталоге RouterAI")
        ip = (m.get("image_pricing") or [{}])[0]
        return m, ip.get("unit"), num(ip.get("price"))

    def want_ra_image(mid):
        _, unit, price = ra_field(mid)
        if unit != "image" or price is None:
            raise LookupError(f"цена каталога RouterAI — не за картинку ({unit})")
        return float(price), None

    def want_ra_tokens(mid, ar, quality, prompt):
        m, unit, price = ra_field(mid)
        fam = gpt_family(mid)
        if unit != "token" or price is None or fam != "gpt-image-2.5":
            raise LookupError(f"цена каталога RouterAI — не за токен GPT Image 2.5 ({unit})")
        w, h = GPT25_SIZES[ar]
        return gpt_image_tokens(fam, w, h, quality) * float(price) + text_tokens(prompt) * ra_input_prices(ctx, m)[0], None

    def want_ga(net, column, **row):
        for r in genapi_table(ctx.ga.prices.get(net)):
            if all(r.get(k) == v for k, v in row.items()) and rub_of(r.get(column)) is not None:
                return rub_of(r.get(column)), None
        raise LookupError(f"строки {row} нет в прайсе Gen-API")

    def want_pz(mid, **eff):
        m = ctx.pz.by_id.get(mid)
        if m is None:
            raise LookupError("модели нет в снимке polza")
        rub, why = pc.price_by_fields(m, eff, None)
        if why or rub is None:
            raise LookupError(why or "цены нет")
        fb = [float(t["cost_rub"]) for t in ((m.get("top_provider") or {}).get("pricing") or {}).get("tiers") or []
              if not t.get("conditions")]
        return rub, max([rub] + fb[:1])

    cases = [
        (no_ra, {"channel": "routerai", "path": "/api/v1/images", "body": {"model": "recraft/recraft-v4.1-vector",
         "prompt": "x", "aspect_ratio": "1:1", "n": 1, "output_format": "svg"}},
         lambda: want_ra_image("recraft/recraft-v4.1-vector")),
        (no_ra, {"channel": "routerai", "path": "/api/v1/images", "body": {"model": "openai/gpt-image-2.5-sunburst",
         "prompt": "x", "aspect_ratio": "1:1", "quality": "medium", "n": 1}},
         lambda: want_ra_tokens("openai/gpt-image-2.5-sunburst", "1:1", "medium", "x")),
        (no_ga, {"channel": "genapi", "path": "/api/v1/networks/recraft-v4", "body": {"model": "vector", "pro": False,
         "prompt": "x", "translate_input": False}},
         lambda: want_ga("recraft-v4", "Цена за изображение", **{"Модель": "vector", "Pro": "Выключен"})),
        (no_ga, {"channel": "genapi", "path": "/api/v1/networks/flux-2", "body": {"prompt": "x", "width": 1328,
         "height": 736, "model": "standard", "num_images": 1, "translate_input": False}},      # кадр меньше 1 Мп — цена 1 Мп
         lambda: want_ga("flux-2", "Цена", **{"Модель": "standard", "Тип генерации": "По тексту"})),
        (no_pz, {"channel": "polza-images", "path": "/api/v2/images/generations", "body": {
         "model": "openai/gpt-image-2.5-sunburst", "prompt": "x", "size": "1024x1024", "n": 1}},
         lambda: want_pz("openai/gpt-image-2.5-sunburst", image_resolution="1K", aspect_ratio="1:1")),
    ]
    for why_not, job, want in cases:
        name = f"оценка {job['channel']} {job['body'].get('model') or job['path']}"
        if why_not:
            skip(name, why_not)
            continue
        try:
            exp, exp_hi = want()
        except LookupError as e:
            skip(name, str(e))
            continue
        job.update(_dir=".", _file="selftest", _index=1, tag="st", max_rub=50)
        p = prepare(ctx, job)
        got = p.estimate.get("rub")
        cond = got is not None and abs(got - exp) < 0.01 and not p.errors and \
            (exp_hi is None or abs((p.estimate.get("rub_high") or 0) - exp_hi) < 0.01)
        ok(f"{name} = {fmt(exp)} ₽ — из полей снимка", cond,
           f"{got} / {p.estimate.get('rub_high')} / ошибок {len(p.errors)}")
    # 10. ловушки
    if no_ga:
        skip("Gen-API recraft-v4: ценовые параметры и translate_input", no_ga)
    else:
        p = prepare(ctx, {"channel": "genapi", "path": "/api/v1/networks/recraft-v4", "_dir": ".", "_file": "st",
                          "_index": 1, "tag": "st", "max_rub": 100, "body": {"prompt": "x"}})
        ok("Gen-API recraft-v4 без model/pro — ошибка ценовых параметров", {"model", "pro"} <= {i["param"] for i in p.errors})
        ok("Gen-API translate_input подставлен false", p.body.get("translate_input") is False)
    if no_ra:
        skip("RouterAI input_references строкой — ошибка формата", no_ra)
    else:
        p = prepare(ctx, {"channel": "routerai", "path": "/api/v1/images", "_dir": ".", "_file": "st", "_index": 1,
                          "tag": "st", "max_rub": 10, "body": {"model": "openai/gpt-image-2", "prompt": "x",
                                                               "input_references": ["a.png"]}})
        ok("RouterAI input_references строкой — ошибка формата", any(i["param"] == "input_references[0]" for i in p.errors))
    p = prepare(ctx, {"channel": "routerai", "path": "/api/v1/images", "_dir": ".", "_file": "st", "_index": 1, "tag": "st",
                      "max_rub": 10, "body": {"model": "recraft/recraft-v4.1", "prompt": "x", "n": 1}})
    saved = ctx.a.budget_total
    ctx.a.budget_total = None
    b_ok, b_msg = budget_check(ctx, p) if not os.environ.get("ROUTERAI_BUDGET_TOTAL") else (False, "задан в окружении")
    ctx.a.budget_total = saved
    ok("бюджет RouterAI по умолчанию 0 — отказ", not b_ok, b_msg)
    # 11. снимок каталога: обрыв и ответ не каталогом — папки снимка нет; оборванный запрос повторяется
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        stamp = dt.datetime(2030, 1, 31, 10, 0, tzinfo=pc.MSK)
        catalog = json.dumps({"data": [{"id": "demo/image", "name": "Demo Image"}]}).encode()

        def channel_get(fail=(), body=catalog):
            calls = []

            def get(url):
                calls.append(url)
                if len(calls) in fail:
                    raise ConnectionResetError("selftest")
                return 200, {"Content-Type": "application/json", "Set-Cookie": "sid=1"}, body
            get.calls = calls
            return get

        def snap(get):
            with contextlib.redirect_stdout(io.StringIO()):          # строки повтора — не итог самопроверки
                return take_snapshot(root, "routerai", "https://channel.test/api/v1/models", get=get, stamp=stamp,
                                     retry_pause=0)

        def names():
            return sorted(x.name for x in (root / "routerai").iterdir()) if (root / "routerai").is_dir() else []

        for label, get in (("обрыв сети во всех попытках", channel_get(fail=(1, 2, 3))),
                           ("ответ не каталогом", channel_get(body=b"<html>maintenance</html>"))):
            try:
                snap(get)
                err = None
            except pc.SnapshotError as e:
                err = str(e)
            ok(f"снимок каталога, {label}: отказ, папки снимка и временной папки нет", err is not None and names() == [],
               (err, names()))
        once = channel_get(fail=(1,))
        d, size, n = snap(once)
        meta = json.loads((d / "snapshot.meta.json").read_text(encoding="utf-8"))
        ok("снимок каталога, обрыв один раз: запрос повторён, папка снимка с файлом и метаданными",
           names() == ["2030-01-31_1000"] and len(once.calls) == 2 and (size, n) == (len(catalog), 1)
           and (d / "api-v1-models.json").read_bytes() == catalog
           and "set-cookie" not in meta["files"]["api-v1-models.json"]["headers"], (names(), once.calls))
        part = root / "routerai" / ".snapshot-20300131-110000-1.part"
        part.mkdir()
        (part / "api-v1-models.json").write_bytes(catalog)
        cache, CACHE = CACHE, root
        try:
            last = latest_file("routerai", "api-v1-models.json")
        finally:
            CACHE = cache
        ok("временная папка идущего снимка — не «последний снимок»", last == d / "api-v1-models.json", last)
    # 12. баланс: разбор ответа на записанных образцах; ключ для чтения баланса читается без --live
    sample = {"amount": "500.00000000", "available": "480.00000000", "reservedAmount": "20.00000000",
              "spentAmount": "145.00000000", "updatedAt": "2030-01-31T10:00:00.000Z"}
    ok("баланс: числа ответа — строки с числом, дата не берётся",
       balance_fields(sample) == {"amount": 500.0, "available": 480.0, "reservedAmount": 20.0, "spentAmount": 145.0},
       balance_fields(sample))
    nested = {"data": {"label": "demo", "usage": 12.5, "limit": None, "active": True}, "balance": 80}
    ok("баланс: числа вложенного data, флаги и пустые поля не берутся",
       balance_fields(nested) == {"balance": 80.0, "data.usage": 12.5}, balance_fields(nested))
    got = read_balance(_Reply(200, {"Content-Type": "application/json"}, json.dumps(sample).encode()), ["/api/v2/balance"])
    ok("баланс: чтение адреса канала — адрес, ответ, числа",
       [(p, j, n.get("available")) for p, j, n in got] == [("/v2/balance", sample, 480.0)], got)
    with contextlib.redirect_stderr(io.StringIO()) as said:
        code = cmd_balance(ctx, argparse.Namespace(channel="routerai", path=None))
    ok("баланс канала без известного адреса и без --path: код 2, запроса нет", code == 2 and "--path" in said.getvalue(),
       (code, said.getvalue()))
    with tempfile.TemporaryDirectory() as td:
        kf = Path(td) / "api_key"
        kf.write_text("sk-selftest-read-0123456789\n")
        kf.chmod(0o600)
        env = {k: os.environ.pop(k, None) for k in ("ROUTERAI_API_KEY", "ROUTERAI_KEY_FILE")}
        os.environ["ROUTERAI_KEY_FILE"] = str(kf)
        try:
            fresh = Ctx(ctx.a)
            for_jobs, for_read = fresh.key("routerai"), fresh.key("routerai", read=True)
            ok("ключ без --live: заданиям не читается, чтению баланса — читается; канал чтения отправляет запрос",
               (fresh.live or for_jobs is None) and for_read == "sk-selftest-read-0123456789"
               and fresh.http("routerai", read=True).live and fresh.http("routerai").live == fresh.live)
        finally:
            os.environ.pop("ROUTERAI_KEY_FILE", None)
            os.environ.update({k: v for k, v in env.items() if v is not None})
            _SECRETS.discard("sk-selftest-read-0123456789")
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "broken.routerai.json").write_text("{не json", encoding="utf-8")
        codes = []
        for job_file in (Path(td) / "absent.routerai.json", Path(td) / "broken.routerai.json"):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as said:
                try:
                    main(["estimate", str(job_file), "--ledger", str(Path(td) / "ledger.jsonl"), "--out", td])
                except SystemExit as e:
                    codes.append((e.code, bool(said.getvalue().strip())))
                except Exception as e:  # noqa: BLE001
                    codes.append((type(e).__name__, False))
        ok("нет файла задания или не JSON: код 2 (ошибка вызова), строка в stderr", codes == [(EXIT_USAGE, True)] * 2,
           codes)
    npass = sum(1 for _, c, _ in res if c)
    for name, c, got in res:
        say(f"{'PASS' if c else 'FAIL'}  {name}" + ("" if c else f"   ← {got}"))
    for name, why in skipped:
        say(f"SKIP  {name}   ← {why}")
    say(f"# selftest: {npass}/{len(res)} PASS" + (f", пропущено {len(skipped)} — нет снимка каталога или каталог сменил "
                                                   f"устройство цены" if skipped else ""))
    return EXIT_OK if npass == len(res) else EXIT_JOB


# ---------------------------------------------------------------------------------------------------------------

def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    g = common.add_argument_group("общие")
    g.add_argument("--live", action="store_true", help="реально отправлять запросы (иначе сухой прогон)")
    g.add_argument("--ledger", help="журнал затрат (по умолчанию MP_LEDGER | POLZA_LEDGER | $DDD_HOME/out/ai-media/_ledger.jsonl)")
    g.add_argument("--out", help="корень результатов (по умолчанию MP_OUT_ROOT | $DDD_HOME/out/ai-media/_mp)")
    g.add_argument("--agent", help="агент по умолчанию для заданий без поля agent")
    g.add_argument("--budget-total", type=float, help="общий лимит ₽ каждого затронутого канала (иначе *_BUDGET_TOTAL)")
    g.add_argument("--budget-agent", type=float, help="лимит ₽ на агента в пределах канала (MP_BUDGET_AGENT)")
    g.add_argument("--max-job", type=float, help="лимит ₽ на одно задание (MP_MAX_JOB, по умолчанию 60)")
    g.add_argument("--limit-by", choices=("high", "expected"), default="high",
                   help="лимиты по верхней оценке (по умолчанию) или по ожидаемой")
    g.add_argument("--force", action="store_true", help="не брать результат из кэша журнала")
    g.add_argument("--curl", action="store_true", help="в сухом прогоне напечатать и curl-команду")
    g.add_argument("--verbose", "-v", action="store_true")
    g.add_argument("--poll-interval", type=float, help="пауза опроса, с (по умолчанию 4 — картинки, 8 — видео)")
    g.add_argument("--max-wait", type=float, help="таймаут опроса, с (по умолчанию 900 — картинки, 1800 — видео)")
    g.add_argument("--http-timeout", type=float, default=60.0)
    g.add_argument("--sync-timeout", type=float, help="таймаут синхронного POST, с (по умолчанию: картинки RouterAI и "
                                                         "чат 300, polza /v2 150, Gen-API is_sync 330)")
    g.add_argument("--no-preflight", action="store_true", help="не проверять баланс polza перед тратой")
    g.add_argument("--no-validate", action="store_true", help="отправлять даже при ошибках проверки")
    g.add_argument("--allow-unknown-price", action="store_true", help="разрешить задания с неизвестной ценой")
    g.add_argument("--no-auto-cap", action="store_true", help="чат без max_tokens: не ставить потолок по max_rub")
    g.add_argument("--set", action="append", metavar="ИМЯ=значение", help="подставить {{ИМЯ}} в шаблон")
    g.add_argument("--set-file", action="append", metavar="ИМЯ=путь", help="подставить {{ИМЯ}} содержимым файла")
    g.add_argument("--routerai-base", help="база RouterAI (ROUTERAI_BASE_URL | https://routerai.ru/api)")
    g.add_argument("--genapi-base", help="база Gen-API (GENAPI_BASE_URL | https://api.gen-api.ru/api)")
    g.add_argument("--polza-base", help="база polza (POLZA_BASE_URL | https://polza.ai/api)")
    g.add_argument("--routerai-catalog", help="снимок каталога RouterAI (папка/файл; по умолчанию последний)")
    g.add_argument("--genapi-catalog", help="снимок каталога Gen-API (папка/файл; по умолчанию последний)")
    g.add_argument("--polza-catalog", help="снимок каталога polza (имя папки в $DDD_HOME/cache/ai-media/polza; по умолчанию последний)")
    ap = argparse.ArgumentParser(prog="mp_client.py", description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("estimate", parents=[common])
    s.add_argument("jobs", nargs="+")
    s.add_argument("--pick")
    s.add_argument("--json", action="store_true", help="машиночитаемый итог")
    s.add_argument("--summary", action="store_true", help="одна строка на задание")
    s.set_defaults(fn=cmd_estimate)
    s = sp.add_parser("run", parents=[common])
    s.add_argument("job")
    s.add_argument("--pick")
    s.set_defaults(fn=cmd_run)
    s = sp.add_parser("batch", parents=[common])
    s.add_argument("jobs", nargs="+")
    s.add_argument("--parallel", type=int, default=2)
    s.add_argument("--pick")
    s.add_argument("--skip-bad", action="store_true", help="пропустить задания с ошибками и шаблоны")
    s.set_defaults(fn=cmd_batch)
    for name, fn in (("status", cmd_status), ("download", cmd_download)):
        s = sp.add_parser(name, parents=[common])
        s.add_argument("id")
        s.add_argument("--channel", required=True, choices=list(CHANNELS))
        s.add_argument("--model", help="модель (для имени файла, если её нет в журнале)")
        s.add_argument("--tag", help="тег (для имени файла, если его нет в журнале)")
        s.set_defaults(fn=fn)
    s = sp.add_parser("ledger", parents=[common])
    s.add_argument("--sum", action="store_true")
    s.add_argument("--channel", choices=list(CHANNELS) + ["polza-media"])
    s.add_argument("--tail", type=int, default=30)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_ledger)
    s = sp.add_parser("show", parents=[common])
    s.add_argument("model")
    s.add_argument("--channel", required=True, choices=list(CHANNELS))
    s.set_defaults(fn=cmd_show)
    s = sp.add_parser("snapshot", parents=[common])
    s.add_argument("--channel", choices=("routerai", "genapi", "all"), default="all")
    s.add_argument("--dest", help="корень для снимков (по умолчанию $DDD_HOME/cache/ai-media)")
    s.set_defaults(fn=cmd_snapshot)
    s = sp.add_parser("balance", parents=[common])
    s.add_argument("--channel", required=True, choices=list(CHANNELS))
    s.add_argument("--path", help="адрес чтения баланса у канала (GET), например /v1/…; у polza-chat и polza-images "
                                  "по умолчанию /v2/balance и /v1/key")
    s.set_defaults(fn=cmd_balance)
    s = sp.add_parser("selftest", parents=[common])
    s.set_defaults(fn=cmd_selftest)
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        ctx = Ctx(a)
        code = a.fn(ctx, a)
    except SystemExit as e:         # текст вместо кода — ошибка вызова или окружения (нет снимка, файла, модели)
        if not isinstance(e.code, str):
            raise
        say(e.code, err=True)
        code = EXIT_USAGE
    except ApiError as e:
        say(f"ОШИБКА API: {e}", err=True)
        if isinstance(e.body, dict):
            say(jdump(redact_obj(shorten(e.body))), err=True)
        code = EXIT_HTTP
    except KeyboardInterrupt:
        say("прервано; незавершённые задачи — mp_client.py ledger", err=True)
        code = 130
    sys.exit(code or 0)


if __name__ == "__main__":
    main()
