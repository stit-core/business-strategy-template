#!/usr/bin/env python3
"""plan_to_assets.py — план ассетов страницы: каркас из медиа- и 3D-слотов плана страницы и проверка плана.

Формат плана ассетов — канон ai-media 01/01 §8 (`kb/ai-media/01-web-assets-landscape/01-asset-slots-by-page-type.md`),
схема — `kb/ai-media/05-prompting/asset-plan.schema.json`; файл проекта —
`docs/projects/<slug>/design/<surface>/assets/plans/<page-id>.yaml` (пути — `lib/docpaths.py`). Id — словарь site
(`kb/site/02-site-types/vocabulary.yaml`): page.page_type — тип страницы, slots[].slot — вид слота, slots[].section — id
секции плана страницы; класс ai-media page.media_class — проекция по строкам §8 `kb/site/02-site-types/crosswalk.tsv`:
строка типа сайта брифа («§8 (page.media_class)», site_type файла site-brief.yaml), у типа сайта без строки — строка
page_type («§8 (page.page_type)»). Бриф — site-brief.yaml поверхности, у файла плана страницы — ссылка refs.brief.
Канон слоя — `docs/projects/_template/design/README.md § Ассеты`; манифест готовых ассетов — схема
`kb/ai-media/05-prompting/asset-manifest.schema.json`.

Каркас: строка на медиа- и 3D-слот секций и на медиа-слот уровня страницы; id строки — <секция>-<id> слота плана
страницы (у слота уровня страницы — его id), он же asset_ref строк copy deck. Из плана страницы: section, slot, role
(media_role), goal, source (customer-tbd → real и заметка; edit-real при подлинности real-only → real, заглушка
local_edit и заметка: кадр доводится без генерации; постер 3D-слота без source — render; слот уровня страницы без
source — template, фавикон — code), task_codes (task:), recipe, соотношения и зона текста → variants, lcp_candidate и loading → delivery, load
3D-слота (без load — умолчание схемы плана страницы), alt и caption → alt_ref и caption_ref (сам текст — строки copy
deck, copydeck.py export-assets), authenticity → ai_fit и policy.no_ai_subjects, poster и poster_for, cta_before_3d →
three_d. Каркас проходит свою проверку: строки, которую она бракует, он не пишет. key — визуал и фон
первого экрана не кодом и постер 3D-слота: ключевые ассеты делаются до ДС (`references/phases.md § Порядок ассетов и
ДС`); агент уточняет. Бюджеты — профиль плана страницы (`kb/site/07-seo-geo-performance-analytics/budgets.yaml`).
Размер, форматы, вес, предмет и дорога 3D — заглушки TODO и пустые поля: их дописывает агент. Статус каркаса — draft;
план, предложенный заказчику, — proposed; утверждает заказчик до генерации (status: approved и approval).
Источник слота действует у каждого варианта; вариант из другого источника называет его сам (variants[].source:
телефон — настоящий кадр, десктоп — генерация) — подлинность и маршрут генерации сверяются по каждому варианту.

Проверка — находки контракта `scripts/project/findings.py` (rule, severity, surface, kind, ref, path, message, fix),
правила `.claude/skills/design-audit/references/rules.md`:
  R-STRUCT-005  форма по схеме; page_type и slot — id словаря site (out-of-scope и measurement-only — ошибка,
                deprecated — предупреждение); media_class — проекция crosswalk.tsv (проходит проекция типа сайта и
                проекция page_type); повтор id строки; generate или edit-real у слота или варианта при ai_fit:
                forbidden; poster_for на строку, которой нет; warning — форма демо-картинки макета x-demo {file |
                files, what} (есть ли файл, не сверяется: путь вне git), local_edit у строки без настоящего кадра
                (источник не real и не edit-real), instance без записи в instances; в проекте — форма манифеста ассетов поверхности
                (design/<surface>/assets/manifest.yaml) по схеме asset-manifest.schema.json (warning); у строки файла
                шрифта (woff2, woff, ttf, otf) манифестов поверхности и продукта — поле font {family, weight, style}
                (warning); у принятой строки (status: accepted) манифестов поверхности и продукта
                (design/_assets/manifest.yaml) sha256 есть и равен файлу — error: по нему код-репо сверяет снимок
                (docs/projects/_template/design/README.md § Пакет для кода)
  R-MAT-002     поля утверждённого плана: approval, дорога 3D у 3D-слота, нет заглушек TODO, у generate и
                edit-real слота или варианта — коды задач routing.yaml
  R-COV-004     3D-слот без постера; с планом страницы — строка на каждый медиа- и 3D-слот (нет строки: error у
                утверждённого плана, иначе warning), строка без слота плана страницы, real-only не на generate ни у
                слота, ни у варианта (error) и с ai_fit: forbidden, постер 3D-слота как в плане страницы; в проекте — план страницы ведёт в план
                ассетов (refs.asset_plan), план ассетов есть у страницы с медиа- и 3D-слотами (error — у страницы
                партии входа холста: поле units манифеста INPUT.md; у остальных страниц и до входа — hint)
  R-REF-001     refs.* плана ассетов и refs.asset_plan плана страницы ведут в пустоту или в другой файл; файл принятой строки
                манифеста ассетов (путь от папки манифеста) не найден
  R-MAT-001     в проекте — план ассетов approved при плане страницы или арт-дирекции не approved (warning)
  R-STRUCT-001  в проекте — план ассетов страницы, которой нет среди планов поверхности (warning)

Вызов:
  plan_to_assets.py PAGE_PLAN [--out FILE]              каркас из файла плана страницы (печать или файл)
  plan_to_assets.py --check ASSET_PLAN … [--plan PAGE_PLAN] [--json]
                                                        проверка файлов плана ассетов; план страницы — --plan,
                                                        refs.page_plan или место файла в проекте
  plan_to_assets.py --spec-role ASSET_PLAN SLOT         блок role спецификации ассета (asset-spec.schema.json) для
                                                        строки SLOT: page_type словаря и проекция page_class
  plan_to_assets.py --types [new|all] [--plan PAGE_PLAN] [--json]
                                                        каркас на каждый тип страницы словаря (new — типы v1 со
                                                        строками проекции; all — все типы в рамках) из плана-образца
                                                        (по умолчанию главная примера saas-okoshko) и его проверка
  plan_to_assets.py build <slug> [<surface>] [--page ID …] [--repo DIR] [--out DIR] [--write] [--json]
                                                        каркасы страниц поверхности: в --out DIR/<surface>/ (по
                                                        умолчанию $DDD_HOME/out/site/plan_to_assets/<slug>/); --write —
                                                        в проект, только для страниц без плана ассетов (план ассетов
                                                        правит агент, существующий файл не перезаписывается)
  plan_to_assets.py check <slug> [<surface>] [--page ID …] [--repo DIR] [--json]
                                                        планы ассетов поверхностей со слоем страницы, покрытие,
                                                        форма манифеста ассетов и отпечатки его принятых строк, без
                                                        --page — и манифеста продукта; --page — только эти страницы
                                                        (находки и код выхода — по ним; из манифеста — их строки)
  plan_to_assets.py --selftest                          примеры баз, 10 типов v1, фикстура asset-plan, без сети
Без <surface> — все поверхности проекта со слоем страницы (web рода landing и site). Корень данных — --repo,
переменная DDD_REPO или репозиторий скилла. --json — строки JSON находок (check) или один документ JSON (build,
--types). Код выхода: 0 — нет error, 1 — есть error, 2 — ошибка вызова или окружения.
"""
from __future__ import annotations

import argparse
import copy
import csv
import difflib
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "lib"))
import kbpaths  # noqa: E402
import docpaths  # noqa: E402
kbpaths.use("project")
import findings as F  # noqa: E402
import vocab_lint  # noqa: E402

SITE = kbpaths.kb("site")
VOCAB = SITE / "02-site-types" / "vocabulary.yaml"
CROSSWALK = SITE / "02-site-types" / "crosswalk.tsv"
BUDGETS = SITE / "07-seo-geo-performance-analytics" / "budgets.yaml"
LEVELS = kbpaths.kb("creative", "01-creative-direction", "ambition-levels.yaml")   # умолчания уровня по типу страницы
PAGE_PLAN_SCHEMA = SITE / "10-playbooks-contracts" / "schemas" / "page-plan.schema.json"
EXAMPLES = SITE / "10-playbooks-contracts" / "examples"
BASE_PLAN = EXAMPLES / "saas-okoshko" / "plans" / "home.yaml"
SCHEMA = kbpaths.kb("ai-media", "05-prompting", "asset-plan.schema.json")
SPEC_SCHEMA = kbpaths.kb("ai-media", "05-prompting", "asset-spec.schema.json")
MANIFEST_SCHEMA = kbpaths.kb("ai-media", "05-prompting", "asset-manifest.schema.json")
PLAN_FILE = "01-asset-slots-by-page-type.md"
KIND = "asset-plan"
MANIFEST_KIND = "asset-manifest"
FONT_FORMATS = ("woff2", "woff", "ttf", "otf")             # файл шрифта: строка манифеста несёт font
FIXTURE = "asset-plan"
CHROME_ROLES = {"header", "footer", "utility", "legal"}          # не первый экран (как site_validate.py)
SVG_SLOTS = {"diagram", "qr-code", "logo", "brand-logo", "favicon", "icon"}
AI_FIT = {"real-only": "forbidden", "real-or-generated": "conditional", "generated-ok": "allowed", "code": "allowed"}
NEVER_AI = {"logo", "brand-logo"}                                # знаки — файлы владельцев, не генерируются
NO_AI = {"avatar": "testimonials", "logo": "logos", "brand-logo": "logos", "screenshot": "ui_screens",
         "product-photo": "product_as_is", "document-image": "documents"}   # прочее real-only — real_people_or_work
KEY_SLOTS = {"hero-visual", "background"}                        # визуал и атмосфера первого экрана
KEY_SOURCES = {"generate", "edit-real", "render", "real"}        # герой кодом строится после ДС по её токенам
AI_SOURCES = ("generate", "edit-real")                           # источники, где кадр делает или правит модель
DEMO = "x-demo"                                                  # демо-картинка макета: имя ключа читает вход холста
TODO = "TODO"
# типы страниц, добавленные в словарь v1: у каждого — строка проекции §8 в crosswalk.tsv
NEW_TYPES = ("specialist-page", "location-page", "program-catalog-page", "search-results-page", "documents-page",
             "event-program-page", "speakers-page", "integrations-page", "security-page", "html-sitemap-page")
OUT_OF_SCOPE = ("out-of-scope", "measurement-only")


def load_yaml(p):
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_plan(ap, head):
    return head + yaml.safe_dump(ap, allow_unicode=True, sort_keys=False, width=120)


# ------------------------------------------------------------------ база: словарь, проекции, схемы

class Kb:
    """Словарь site, проекции crosswalk.tsv, схемы плана ассетов и спецификации ассета — читаются один раз."""

    def __init__(self):
        try:
            import jsonschema
        except ImportError as e:
            raise F.ToolError("нет jsonschema — окружение скилла: scripts/install.sh") from e
        for p in (VOCAB, CROSSWALK, SCHEMA, MANIFEST_SCHEMA, PAGE_PLAN_SCHEMA):
            if not p.is_file():
                raise F.ToolError(f"нет файла базы: {p}")
        self.vocab = vocab_lint.Vocab.load(VOCAB)
        ns = self.vocab.data["namespaces"]
        self.page_types = {str(v["id"]): v for v in ns["page_type"]["values"]}
        self.slot_kind = {str(v["id"]): v.get("kind") for v in ns["slot"]["values"]}
        self.plan_proj, self.spec_proj, self.site_proj = {}, {}, {}
        with open(CROSSWALK, encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                if r["source_base"] != "ai-media" or not r["our_id"]:
                    continue
                if r["namespace"] == "site_type":
                    if r["source_file"].endswith(PLAN_FILE) and r["source_section"].startswith("§8 (page.media_class)"):
                        self.site_proj.setdefault(r["our_id"], (r["source_term"], r["relation"]))
                    continue
                if r["namespace"] != "page_type":
                    continue
                if r["source_file"].endswith(PLAN_FILE) and r["source_section"].startswith("§8 (page.page_type)"):
                    self.plan_proj.setdefault(r["our_id"], (r["source_term"], r["relation"]))
                elif r["source_file"].endswith("asset-spec.schema.json") and r["source_section"].startswith("role.page_type"):
                    self.spec_proj.setdefault(r["our_id"], (r["source_term"], r["relation"]))
        self.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.validator = jsonschema.Draft202012Validator(self.schema)
        self.manifest_validator = jsonschema.Draft202012Validator(json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8")))
        spec = json.loads(SPEC_SCHEMA.read_text(encoding="utf-8"))
        self.role_validator = jsonschema.Draft202012Validator(spec["properties"]["role"])
        pp = json.loads(PAGE_PLAN_SCHEMA.read_text(encoding="utf-8"))["$defs"]["slot-3d"]["properties"]
        self.load_3d = pp["load"].get("default", "on-interaction")
        self.cta_before_3d = pp["cta_before_3d"].get("default", True)
        self.budgets = load_yaml(BUDGETS) if BUDGETS.is_file() else {}
        self.levels = load_yaml(LEVELS) if LEVELS.is_file() else {}

    def media_class(self, page_type, site_type=None):
        """Класс ai-media по строкам §8 crosswalk.tsv → (класс, отношение) или (None, None): строка типа сайта брифа
        («§8 (page.media_class)», пространство site_type), у типа сайта без строки — строка page_type."""
        return self.site_proj.get(site_type) or self.plan_proj.get(page_type, (None, None))

    def page_class(self, page_type):
        """Класс спецификации ассета по строкам «role.page_type» crosswalk.tsv → (класс, отношение) или (None, None)."""
        return self.spec_proj.get(page_type, (None, None))

    def type_status(self, page_type):
        v = self.page_types.get(page_type)
        return None if v is None else v.get("status", "active")

    def level_of(self, page_type):
        """Уровень по умолчанию типа страницы — таблица creative ambition-levels.yaml#defaults_by_page_type (разделы
        L0–L2; типы раздела proposed умолчания не имеют)."""
        dpt = (self.levels or {}).get("defaults_by_page_type") or {}
        return next((lv for lv in ("L0", "L1", "L2") if page_type in (dpt.get(lv) or [])), None)


_KB = None


def kb():
    global _KB
    if _KB is None:
        _KB = Kb()
    return _KB


# ------------------------------------------------------------------ каркас из плана страницы

def first_screen(plan):
    """Первый экран: первая секция потока (не шапка, подвал, служебные) и секции first_screen.must_show."""
    pg = plan.get("page") or {}
    ids = {str(r).partition(".")[0] for r in (pg.get("first_screen") or {}).get("must_show") or []}
    ids |= set([s.get("id") for s in plan.get("sections") or [] if s.get("role") not in CHROME_ROLES][:1])
    return ids


def budgets(K, profile, level):
    """Бюджеты веса по профилю плана страницы: уровень → levels.<L>.weight, исключение профиля → overrides."""
    b = K.budgets or {}
    w = ((b.get("levels") or {}).get(level) or {}).get("weight") or {}
    out = {}
    if profile:
        out["profile"] = profile
    for k in ("first_screen_kb", "session_kb"):
        v = w.get(k)
        if v is None:
            continue
        out[k] = dict(v) if isinstance(v, dict) else {"mobile": v, "desktop": None}
    ov = (((b.get("overrides") or {}).get(profile) or {}).get("weight") or {}).get("first_screen_kb")
    if isinstance(ov, dict):
        out["first_screen_kb"] = dict(ov)
    return out


def ladder(sl, kind):
    if kind == "3d":
        return "3d"
    if sl.get("motion") == "shader":
        return "shader"
    if sl.get("slot") == "video" or sl.get("motion") in ("loop", "video-controls"):
        return "video"
    if sl.get("slot") in SVG_SLOTS or sl.get("authenticity") == "code":
        return "svg"
    return "image"


def variants(sl, kind):
    out = []
    ratio = sl.get("ratio") or {}
    for dev in ("desktop", "mobile"):
        if ratio.get(dev):
            v = {"id": dev, "ratio": str(ratio[dev]), "size": TODO, "formats": TODO, "max_kb": TODO}
            if sl.get("text_zone") and dev == "desktop":
                v["text_zone"] = dict(sl["text_zone"])
            out.append(v)
    if not out:
        out.append({"id": "default", "ratio": TODO, "size": TODO, "formats": TODO, "max_kb": TODO})
    return out


def source_of(sl, default):
    """Источник строки плана ассетов и заметки к нему по слоту плана страницы. customer-tbd — real: ждём материалы
    заказчика. edit-real при подлинности real-only — тоже real: правка моделью изменила бы то, что обязано остаться
    настоящим, а доводка без генерации источник не меняет — её операции называет поле local_edit (каркас ставит
    заглушку); строку edit-real при ai_fit: forbidden проверка плана бракует, поэтому каркас её не пишет.
    → (источник, заметки, заглушка local_edit или None)."""
    src, note, local = sl.get("source"), [], None
    if src == "customer-tbd":
        src = "real"
        note.append("ждём материалы заказчика (source: customer-tbd в плане страницы)")
    elif src == "edit-real" and sl.get("authenticity") == "real-only":
        src = "real"
        local = [f"{TODO}: что делается с кадром без генерации (кадрирование, цвет, апскейл)"]
        note.append("edit-real при подлинности real-only в плане страницы: настоящий кадр доводится без генерации — "
                    "операции в local_edit; правка моделью — только при real-or-generated")
    return src or default, note, local


def text_ref(sec_id, value):
    if not value:
        return None
    return "decorative" if value == "decorative" else f"{sec_id}.{value}"


def slot_entry(K, sec, sl, kind, posters, fs):
    """Строка плана ассетов для медиа- или 3D-слота секции sec; posters — (секция, id) → 3d | video и постеры видео."""
    sid = f"{sec['id']}-{sl['id']}"
    target_kind = posters["kind"].get((sec["id"], sl.get("poster_for")))
    src, note, local = source_of(sl, "code" if kind == "3d" else ("render" if target_kind == "3d" else "real"))
    auth = sl.get("authenticity") or ("code" if kind == "3d" else None)
    e = {"id": sid, "section": sec["id"], "slot": sl["slot"], "role": sl.get("media_role", "informational")}
    e["goal"] = sl.get("goal") or "TODO: что ассет показывает за 3 секунды"
    if (sec["id"] in fs and sl["slot"] in KEY_SLOTS and src in KEY_SOURCES) or (sl.get("poster_for") and target_kind == "3d"):
        e["key"] = True
    e["ladder"] = ladder(sl, kind)
    e["source"] = src
    if local:
        e["local_edit"] = local
    e["task_codes"] = [t.replace("task:", "", 1) for t in sl.get("task") or []]
    if sl.get("recipe"):
        e["recipe"] = sl["recipe"]
    if kind == "3d":
        e["three_d"] = {"cta_before_3d": sl.get("cta_before_3d", K.cta_before_3d)}
        e["poster"] = f"{sec['id']}-{sl['poster']}"
    elif (sec["id"], sl.get("id")) in posters["video"]:
        e["poster"] = posters["video"][(sec["id"], sl["id"])]
    if sl.get("poster_for"):
        e["poster_for"] = f"{sec['id']}-{sl['poster_for']}"
    if src in ("generate", "edit-real", "render"):
        e["subject"] = "TODO: предмет словами паспорта визуала"
    e["variants"] = variants(sl, kind)
    e["motion"] = {"type": sl.get("motion") or "none"}
    d = {"lcp_candidate": bool(sl.get("lcp_candidate"))}
    d["loading"] = sl.get("loading") or ("eager" if sl.get("lcp_candidate") else "lazy")
    if d["lcp_candidate"]:
        d["fetchpriority"] = "high"
    if kind == "3d":
        d["load"] = sl.get("load") or K.load_3d
    elif sl.get("load"):
        d["load"] = sl["load"]
    e["delivery"] = d
    a, c = text_ref(sec["id"], sl.get("alt")), text_ref(sec["id"], sl.get("caption"))
    if a:
        e["alt_ref"] = a
    if c:
        e["caption_ref"] = c
    e["ai_fit"] = AI_FIT.get(auth, "forbidden" if sl["slot"] in NEVER_AI else "conditional")
    if auth == "real-only":
        note.append("подлинность real-only: люди-доказательства, товар «как есть», чужие знаки — только настоящие "
                    "(ai-media 12/04 §2, site 08/02 §2.1)")
    if note:
        e["note"] = "; ".join(note)
    return e


def page_slot_entry(sl):
    """Строка плана ассетов для медиа-слота уровня страницы (OG, фавикон): источник и подлинность — из слота плана
    страницы, как у слота секции; без них — шаблон с уместным ИИ у картинки и код без ИИ у фавикона."""
    kind = sl.get("slot")
    fav = kind == "favicon"
    src, note, local = source_of(sl, "code" if fav else "template")
    e = {"id": sl["id"], "section": "meta", "slot": kind, "role": sl.get("media_role", "informational"),
         "goal": sl.get("goal") or kind, "ladder": "svg" if fav else "image", "source": src}
    if local:
        e["local_edit"] = local
    e["task_codes"] = [t.replace("task:", "", 1) for t in sl.get("task") or []]
    if src in ("generate", "edit-real", "render"):
        e["subject"] = "TODO: предмет словами паспорта визуала"
    e.update({"variants": [{"id": kind, "ratio": "1.91:1" if kind == "og-image" else "1:1"}],
              "motion": {"type": "none"}, "delivery": {"lcp_candidate": False, "loading": "lazy"}})
    a = text_ref("meta", sl.get("alt"))
    if a:
        e["alt_ref"] = a
    e["ai_fit"] = AI_FIT.get(sl.get("authenticity"), "forbidden" if fav else "allowed")
    if note:
        e["note"] = "; ".join(note)
    return e


def site_type_of(brief):
    """Тип сайта брифа (site_type файла site-brief.yaml) или None: брифа нет или он не читается."""
    try:
        d = load_yaml(brief) if brief and Path(brief).is_file() else None
    except (OSError, yaml.YAMLError):
        return None
    st = d.get("site_type") if isinstance(d, dict) else None
    return st if isinstance(st, str) else None


def plan_site_type(plan, plan_path):
    """Тип сайта для плана страницы из файла plan_path — бриф по ссылке refs.brief плана; ссылки нет — None."""
    refs = plan.get("refs") if isinstance(plan, dict) and isinstance(plan.get("refs"), dict) else {}
    ref = refs.get("brief")
    return site_type_of(Path(plan_path).parent / ref) if isinstance(ref, str) and ref else None


def build(plan, page_plan_ref=None, K=None, site_type=None):
    """План страницы (dict) → каркас плана ассетов (dict); site_type — тип сайта брифа для класса media_class."""
    K = K or kb()
    pg = plan.get("page") or {}
    pt = pg.get("page_type")
    mc, _ = K.media_class(pt, site_type)
    fs = first_screen(plan)
    # кто чей постер: id слотов — в пределах секции, ключ — (секция, id)
    posters = {"kind": {}, "video": {}}
    for sec in plan.get("sections") or []:
        sl_all = (sec.get("slots") or {})
        for s3 in sl_all.get("3d") or []:
            posters["kind"][(sec["id"], s3["id"])] = "3d"
        for m in sl_all.get("media") or []:
            if m.get("slot") == "video" or m.get("motion") in ("loop", "video-controls"):
                posters["kind"].setdefault((sec["id"], m["id"]), "video")
        for m in sl_all.get("media") or []:
            pf = m.get("poster_for")
            if pf and posters["kind"].get((sec["id"], pf)) == "video":
                posters["video"][(sec["id"], pf)] = f"{sec['id']}-{m['id']}"
    slots, no_ai = [], []
    for sec in plan.get("sections") or []:
        for kind in ("media", "3d"):
            for sl in (sec.get("slots") or {}).get(kind) or []:
                e = slot_entry(K, sec, sl, kind, posters, fs)
                slots.append(e)
                if e["ai_fit"] == "forbidden":
                    subj = NO_AI.get(sl.get("slot"), "real_people_or_work")
                    if subj not in no_ai:
                        no_ai.append(subj)
    for sl in (plan.get("page_slots") or {}).get("media") or []:
        slots.append(page_slot_entry(sl))
        if sl.get("authenticity") == "real-only":
            subj = NO_AI.get(sl.get("slot"), "real_people_or_work")
            if subj not in no_ai:
                no_ai.append(subj)
    ap = {"plan_version": 1}
    if plan.get("checked"):
        ap["checked"] = str(plan["checked"])
    ap["status"] = "draft"
    if plan.get("example"):
        ap["example"] = True
    if page_plan_ref:
        ap["refs"] = {"page_plan": page_plan_ref}
    page = {"id": pg.get("id"), "page_type": pt}
    if mc:
        page["media_class"] = mc
    if pg.get("template"):
        page["template"] = True
    page["locale"] = pg.get("locale") or "ru-RU"
    if pg.get("goal"):
        page["goal"] = pg["goal"]
    ap["page"] = page
    level = pg.get("ambition_level") or str(pg.get("budget_profile") or "@L1").rpartition("@")[2] or "L1"
    b = budgets(K, pg.get("budget_profile"), level)
    if b:
        ap["budgets"] = b
    ap["policy"] = {"no_ai_subjects": sorted(no_ai), "disclosure": "per-slot"}
    ap["slots"] = slots
    return ap


def head_for(name, page_id):
    return (f"# План ассетов страницы {page_id} — каркас из {name} (plan_to_assets.py). Формат — ai-media 01/01 §8, схема —\n"
            "# kb/ai-media/05-prompting/asset-plan.schema.json. Заглушки TODO, предмет, варианты, вес, фокус и дорогу 3D\n"
            "# дописывает агент; тексты ассетов — copydeck.py export-assets; генерация — после status: approved и approval.\n")


def relpath(target, start_dir):
    return os.path.relpath(Path(target).resolve(), Path(start_dir).resolve()).replace(os.sep, "/")


def expected_rows(plan):
    """Строки, которых ждёт план страницы: id → {section, slot, kind, auth, poster, local}."""
    out = {}
    for sec in plan.get("sections") or []:
        for kind in ("media", "3d"):
            for sl in (sec.get("slots") or {}).get(kind) or []:
                out[f"{sec['id']}-{sl['id']}"] = {"section": sec["id"], "slot": sl.get("slot"), "kind": kind,
                                                   "auth": sl.get("authenticity"), "local": f"{sec['id']}.{sl['id']}",
                                                   "poster": f"{sec['id']}-{sl['poster']}" if kind == "3d" and sl.get("poster") else None}
    for sl in (plan.get("page_slots") or {}).get("media") or []:
        out[sl["id"]] = {"section": "meta", "slot": sl.get("slot"), "kind": "media", "auth": sl.get("authenticity"),
                         "local": f"page_slots.{sl['id']}", "poster": None}
    return out


# ------------------------------------------------------------------ проверка плана ассетов

@dataclass
class Ctx:
    rep: F.Report
    path: str                        # файл для находки (docpaths.rel)
    ref: str                         # id страницы
    surface: str | None = None
    fix: str = ""
    approved: bool = False
    todo: int = 0
    kind: str = KIND

    def add(self, rule, severity, where, message, fix=None):
        ref = self.ref + (f"#{where}" if where else "")
        self.rep.add(rule, severity, surface=self.surface, kind=self.kind, ref=ref, path=self.path, message=message,
                     fix=self.fix if fix is None else fix)


def todos(x, ptr=""):
    """Заглушки TODO: [(указатель, значение)]."""
    if isinstance(x, str):
        return [(ptr, x)] if x.startswith(TODO) else []
    if isinstance(x, dict):
        return [t for k, v in x.items() for t in todos(v, f"{ptr}/{k}")]
    if isinstance(x, list):
        return [t for i, v in enumerate(x) for t in todos(v, f"{ptr}/{i}")]
    return []


def row_sources(s):
    """Источники строки плана по вариантам: [(указатель от строки, подпись, источник)] — первым источник слота, дальше
    варианты со своим source; у варианта без поля действует источник слота."""
    out = [("", "", s.get("source"))]
    for j, v in enumerate(s.get("variants") or []):
        if isinstance(v, dict) and v.get("source"):
            out.append((f"/variants/{j}/source", f"вариант {v.get('id')} — ", v["source"]))
    return out


def demo_problems(s):
    """Форма демо-картинки слота — расширение x-demo {file | files, what}: [(указатель от x-demo, сообщение)].
    Есть ли файл на диске, не сверяется: путь машинный, вне git."""
    d = s[DEMO]
    if not isinstance(d, dict):
        return [("", "x-demo — объект {file | files, what}")]
    out = []
    f, fs = d.get("file"), d.get("files")
    if f is None and fs is None:
        out.append(("", "в x-demo нет пути: file — путь файла или files — {<id варианта>: путь}"))
    if f is not None and not (isinstance(f, str) and f.strip()):
        out.append(("/file", "x-demo.file — непустая строка пути"))
    if fs is not None:
        if not (isinstance(fs, dict) and fs and all(isinstance(v, str) and v.strip() for v in fs.values())):
            out.append(("/files", "x-demo.files — непустой объект {<id варианта>: путь}"))
        else:
            ids = {str(v.get("id")) for v in s.get("variants") or [] if isinstance(v, dict)}
            extra = [str(k) for k in fs if str(k) not in ids]
            if extra:
                out.append(("/files", f"x-demo.files: вариантов {', '.join(extra)} нет среди variants строки"))
    if not (isinstance(d.get("what"), str) and d["what"].strip()):
        out.append(("/what", "в x-demo нет what — что это за картинка"))
    return out


def schema_findings(K, ap, c):
    for e in sorted(K.validator.iter_errors(ap), key=lambda e: [str(x) for x in e.absolute_path]):
        if DEMO in e.absolute_path:                      # форму x-demo называет demo_problems — предупреждением
            continue
        ptr = "/" + "/".join(str(x) for x in e.absolute_path) if e.absolute_path else ""
        m = re.search(r"'([^']+)' is a required property", e.message) if e.validator == "required" else None
        miss = m.group(1) if m else None
        if miss == "approval":
            c.add("R-MAT-002", "error", ptr, "план утверждён (status: approved) без approval — кто и когда утвердил")
        elif miss == "poster":
            c.add("R-COV-004", "error", ptr, "3D-слот без постера: poster — id строки с постером того же ракурса")
        elif miss in ("three_d", "road"):
            c.add("R-MAT-002", "error", ptr, "у 3D-слота утверждённого плана нет дороги 3D (three_d.road: code · "
                                             "blender-frame · blender-sequence · hybrid — blender/15-showcase/VERDICT.md §3)")
        else:
            c.add("R-STRUCT-005", "error", ptr, f"форма плана ассетов: {e.message[:300]}")


def check_plan(K, ap, c, page_plan=None, file_dir=None, site_type=None):
    """Находки одного плана ассетов (dict) в Ctx c; page_plan — план страницы (dict) для покрытия; site_type — тип
    сайта брифа: media_class сверяется с проекцией типа сайта и с проекцией page_type, проходит любая из двух."""
    if not isinstance(ap, dict):
        c.add("R-STRUCT-005", "error", "", "план ассетов — не объект YAML")
        return
    c.approved = ap.get("status") == "approved"
    schema_findings(K, ap, c)
    page = ap.get("page") if isinstance(ap.get("page"), dict) else {}
    pt = page.get("page_type")
    if isinstance(pt, str):
        st = K.type_status(pt)
        if st is None:
            near = difflib.get_close_matches(pt, list(K.page_types), n=1)
            c.add("R-STRUCT-005", "error", "/page/page_type", f"page_type {pt!r} вне словаря site"
                  + (f" (ближе всего — {near[0]})" if near else ""))
        elif st in OUT_OF_SCOPE:
            c.add("R-STRUCT-005", "error", "/page/page_type", f"page_type {pt!r} — статус словаря {st}: вне рамок сайта")
        elif st == "deprecated":
            rb = K.page_types[pt].get("replaced_by")
            c.add("R-STRUCT-005", "warning", "/page/page_type", f"page_type {pt!r} устарел" + (f": замена — {rb}" if rb else ""))
        if st is not None:
            proj, _ = K.media_class(pt)
            by_site = K.site_proj.get(site_type, (None, None))[0]
            site_note = f"типа сайта {site_type}: {by_site!r}" if by_site else ""
            mc = page.get("media_class")
            if proj is None:
                c.add("R-STRUCT-005", "error", "/page/page_type", f"у page_type {pt!r} нет строки проекции §8 в crosswalk.tsv: "
                      "новый id — сначала словарь, затем строка таблицы", fix="строка kb/site/02-site-types/crosswalk.tsv")
            elif mc is None:
                c.add("R-STRUCT-005", "error" if c.approved else "warning", "/page",
                      "нет media_class — проекция crosswalk.tsv для " + (site_note or f"{pt}: {proj}"))
            elif mc not in (proj, by_site):
                c.add("R-STRUCT-005", "error", "/page/media_class", f"media_class {mc!r} ≠ проекции crosswalk.tsv для {pt}: {proj!r}"
                      + (f" и для {site_note}" if by_site else ""))
    refs = ap.get("refs") if isinstance(ap.get("refs"), dict) else {}
    if file_dir is not None:
        for k, v in refs.items():
            if isinstance(v, str) and v and not (Path(file_dir) / v).exists():
                c.add("R-REF-001", "error", f"/refs/{k}", f"refs.{k} ведёт в пустоту: {v}")
    slots = ap.get("slots") if isinstance(ap.get("slots"), list) else []
    ids = [s.get("id") for s in slots if isinstance(s, dict)]
    inst = {x.get("id") for x in ap.get("instances") or [] if isinstance(x, dict)} if isinstance(ap.get("instances"), list) else set()
    seen = set()
    for i, s in enumerate(slots):
        if not isinstance(s, dict):
            continue
        w = f"/slots/{i}"
        sid = s.get("id")
        if sid in seen:
            c.add("R-STRUCT-005", "error", w, f"id строки {sid!r} повторяется")
        seen.add(sid)
        sk = s.get("slot")
        if isinstance(sk, str):
            kind = K.slot_kind.get(sk)
            if sk not in K.slot_kind:
                near = difflib.get_close_matches(sk, [k for k, v in K.slot_kind.items() if v in ("media", "3d")], n=1)
                c.add("R-STRUCT-005", "error", w + "/slot", f"вид слота {sk!r} вне словаря site"
                      + (f" (ближе всего — {near[0]})" if near else ""))
            elif kind not in ("media", "3d"):
                c.add("R-STRUCT-005", "error", w + "/slot", f"вид слота {sk!r} — {kind}, в плане ассетов только медиа и 3D")
        if s.get("poster") and s["poster"] not in ids:
            c.add("R-COV-004", "error", w + "/poster", f"постер {s['poster']!r} — строки с таким id в плане нет")
        if s.get("poster_for") and s["poster_for"] not in ids:
            c.add("R-STRUCT-005", "warning", w + "/poster_for", f"poster_for {s['poster_for']!r} — строки с таким id в плане нет")
        srcs = row_sources(s)
        for ptr, who, src in srcs:
            if src in AI_SOURCES and s.get("ai_fit") == "forbidden":
                c.add("R-STRUCT-005", "error", w + ptr, f"{sid}: {who}source {src} при ai_fit: forbidden — слот только для настоящего")
        if s.get("local_edit") and not {"real", "edit-real"} & {src for _, _, src in srcs}:
            c.add("R-STRUCT-005", "warning", w + "/local_edit", f"{sid}: local_edit — доводка настоящего кадра без генерации, "
                  f"а настоящего кадра у строки нет (source: {s.get('source')})")
        if isinstance(s.get("instance"), str) and s["instance"] not in inst:
            c.add("R-STRUCT-005", "warning", w + "/instance", f"{sid}: instance {s['instance']!r} — экземпляра с таким id в "
                  "instances плана нет")
        if DEMO in s:
            for ptr, msg in demo_problems(s):
                c.add("R-STRUCT-005", "warning", f"{w}/{DEMO}{ptr}", f"{sid}: {msg}")
        if c.approved and not s.get("task_codes"):
            gen = next(((who, src) for _, who, src in srcs if src in AI_SOURCES), None)
            if gen:
                c.add("R-MAT-002", "error", w + "/task_codes", f"{sid}: {gen[0]}у {gen[1]} нет кодов задач routing.yaml — маршрут генерации")
    c.todo = len(todos(ap))
    if c.approved:
        for i, s in enumerate(slots):
            t = todos(s)
            if t:
                c.add("R-MAT-002", "error", f"/slots/{i}", f"{s.get('id')}: в утверждённом плане заглушки TODO — "
                      + ", ".join(p.lstrip('/') for p, _ in t[:6]) + (" …" if len(t) > 6 else ""))
        top = [p for p, _ in todos({k: v for k, v in ap.items() if k != "slots"})]
        if top:
            c.add("R-MAT-002", "error", "", "в утверждённом плане заглушки TODO — " + ", ".join(p.lstrip('/') for p in top[:6]))
    if isinstance(page_plan, dict):
        coverage(ap, page_plan, c)


def coverage(ap, plan, c):
    """R-COV-004: строки плана ассетов против медиа- и 3D-слотов плана страницы."""
    exp = expected_rows(plan)
    rows = {s.get("id"): (i, s) for i, s in enumerate(ap.get("slots") or []) if isinstance(s, dict)}
    for rid, x in exp.items():
        if rid not in rows:
            c.add("R-COV-004", "error" if c.approved else "warning", "",
                  f"{x['kind']}-слот {x['local']} плана страницы без строки плана ассетов ({rid})")
            continue
        i, s = rows[rid]
        w = f"/slots/{i}"
        if s.get("section") != x["section"]:
            c.add("R-COV-004", "warning", w + "/section", f"{rid}: section {s.get('section')!r}, в плане страницы — {x['section']!r}")
        if x["slot"] and s.get("slot") != x["slot"]:
            c.add("R-COV-004", "warning", w + "/slot", f"{rid}: вид слота {s.get('slot')!r}, в плане страницы — {x['slot']!r}")
        if x["auth"] == "real-only":
            gen = [(ptr, who) for ptr, who, src in row_sources(s) if src == "generate"]
            for ptr, who in gen:
                c.add("R-COV-004", "error", w + (ptr or "/source"), f"{rid}: {who}подлинность real-only — люди-доказательства, "
                      "товар «как есть», чужие знаки только настоящие, не generate")
            if not gen and s.get("ai_fit") != "forbidden":
                c.add("R-COV-004", "warning", w + "/ai_fit", f"{rid}: подлинность real-only — ai_fit: forbidden")
        if x["kind"] == "3d" and x["poster"] and s.get("poster") and s["poster"] != x["poster"]:
            c.add("R-COV-004", "warning", w + "/poster", f"{rid}: постер {s['poster']!r}, в плане страницы — {x['poster']!r}")
    for rid, (i, s) in rows.items():
        if rid not in exp:
            c.add("R-COV-004", "warning", f"/slots/{i}", f"строка {rid!r} без медиа- или 3D-слота плана страницы: слот снят "
                  "или переименован")


def check_manifest(K, path, c, pages=None):
    """Форма манифеста ассетов по схеме asset-manifest.schema.json — находки в Ctx c. pages — только строки этих
    страниц (поле page строки); находки вне строк тогда не называются."""
    try:
        data = load_yaml(path)
    except (OSError, yaml.YAMLError) as e:
        c.add("R-STRUCT-005", "warning", "", f"манифест ассетов не читается как YAML: {str(e)[:200]}")
        return
    if not isinstance(data, (dict, list)):
        c.add("R-STRUCT-005", "warning", "", "манифест ассетов — объект с ключом assets или список строк")
        return
    rows = data if isinstance(data, list) else data.get("assets")
    branch = 0 if isinstance(data, list) else 1          # ветка anyOf схемы: список строк или объект с assets
    errs = []
    for e in K.manifest_validator.iter_errors(data):
        sub = [x for x in e.context or [] if x.relative_schema_path and x.relative_schema_path[0] == branch]
        errs += sub or [e]
    for e in sorted(errs, key=lambda e: [str(x) for x in e.absolute_path]):
        ap_ = list(e.absolute_path)
        i = next((x for x in ap_ if isinstance(x, int)), None)
        row = rows[i] if isinstance(rows, list) and i is not None and i < len(rows) else None
        if pages is not None and not (isinstance(row, dict) and str(row.get("page") or "") in pages):
            continue
        who = f"{row.get('slot')}: " if isinstance(row, dict) and row.get("slot") else ""
        c.add("R-STRUCT-005", "warning", "/" + "/".join(str(x) for x in ap_) if ap_ else "",
              f"форма манифеста ассетов: {who}{e.message[:300]}")
    # файл шрифта код подключает по полям font строки (Fonts API с локальным провайдером): без них файла для кода нет
    for i, row in enumerate(rows if isinstance(rows, list) else []):
        if isinstance(row, dict) and isinstance(row.get("file"), str) and "font" not in row and \
                (pages is None or str(row.get("page") or "") in pages) and \
                str(row.get("format") or Path(row["file"]).suffix.lstrip(".")).lower() in FONT_FORMATS:
            c.add("R-STRUCT-005", "warning", (f"/assets/{i}" if branch else f"/{i}") + "/font",
                  f"{row.get('slot')}: строка файла шрифта {row['file']} без font {{family, weight, style}}: код "
                  "подключает шрифт по этим полям")
    # принятая строка — файл снимка код-репо: лок берёт её sha256 как отпечаток файла, поэтому отпечаток, не равный файлу,
    # — дефект строки, как ссылка в пустоту (docs/projects/_template/design/README.md § Пакет для кода)
    for i, row in enumerate(rows if isinstance(rows, list) else []):
        if not (isinstance(row, dict) and row.get("status") == "accepted" and isinstance(row.get("file"), str)):
            continue
        if pages is not None and str(row.get("page") or "") not in pages:
            continue
        ptr = f"/assets/{i}" if branch else f"/{i}"
        f = path.parent / row["file"]
        if not f.is_file():
            c.add("R-REF-001", "error", ptr + "/file", f"{row.get('slot')}: файл принятой строки ведёт в пустоту: "
                  f"{row['file']} (путь — от папки манифеста)")
            continue
        sha = str(row.get("sha256") or "").removeprefix("sha256:")
        real = hashlib.sha256(f.read_bytes()).hexdigest()
        if sha != real:
            what = f"sha256 не равен файлу (файл — {real})" if sha else f"нет sha256 (файл — {real})"
            c.add("R-STRUCT-005", "error", ptr + "/sha256", f"{row.get('slot')}: у принятой строки {row['file']} "
                  f"{what}: по нему код-репо сверяет снимок")


def has_media(plan):
    return bool(expected_rows(plan)) if isinstance(plan, dict) else False


def read_plan_file(p, c):
    """YAML плана ассетов; ошибка разбора — находка, None."""
    try:
        return load_yaml(p)
    except (OSError, yaml.YAMLError) as e:
        c.add("R-STRUCT-005", "error", "", f"файл не читается как YAML: {str(e)[:200]}")
        return None


def locate(path, repo=None):
    """Место файла в проекте: (slug, surface, page_id) или None."""
    try:
        rel = Path(path).resolve().relative_to(docpaths.projects_dir(repo))
    except (ValueError, docpaths.DocPathError):
        return None
    parts = rel.parts
    if len(parts) == 6 and parts[1] == "design" and parts[3:5] == ("assets", "plans") and parts[5].endswith(".yaml"):
        return parts[0], parts[2], parts[5][:-5]
    return None


# ------------------------------------------------------------------ режим файлов

def cmd_skeleton(a):
    K = kb()
    src = Path(a.plan)
    plan = load_yaml(src)
    if not isinstance(plan, dict) or not isinstance(plan.get("page"), dict):
        print(f"plan_to_assets: {src} — не план страницы (нет page)", file=sys.stderr)
        return 2
    dest_dir = Path(a.out).resolve().parent if a.out else Path.cwd()
    st = plan_site_type(plan, src)
    ap = build(plan, relpath(src, dest_dir), K, st)
    text = dump_plan(ap, head_for(src.name, ap["page"]["id"]))
    rep = F.Report()
    c = Ctx(rep, str(a.out or "-"), str(ap["page"]["id"]))
    check_plan(K, ap, c, plan, dest_dir if a.out else None, st)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    mc = ap["page"].get("media_class")
    print(f"слотов {len(ap['slots'])}; page_type {ap['page']['page_type']} → media_class {mc or '—'}; "
          f"заглушек TODO {c.todo}; {F.summary(rep.items)}", file=sys.stderr)
    for f in rep.items:
        print(f"  {f.severity} {f.rule} {f.ref}: {f.message}", file=sys.stderr)
    return rep.exit_code()


def check_file(K, path, plan_path=None, repo=None, rep=None):
    rep = rep if rep is not None else F.Report()
    p = Path(path)
    where = locate(p, repo)
    c = Ctx(rep, docpaths.rel(p, repo), p.stem)
    if where:
        c.surface = where[1]
        c.fix = f"/design-deep-dive {where[0]} {where[1]} asset-plan:{where[2]}"
    ap = read_plan_file(p, c)
    if ap is None:
        return rep, c
    if isinstance(ap, dict) and isinstance(ap.get("page"), dict) and ap["page"].get("id"):
        c.ref = str(ap["page"]["id"])
    pp = None
    if plan_path:
        pp_path = Path(plan_path)
    elif where and docpaths.site(where[0], where[1], "plans", f"{where[2]}.yaml", repo=repo).is_file():
        pp_path = docpaths.site(where[0], where[1], "plans", f"{where[2]}.yaml", repo=repo)
    elif isinstance(ap, dict) and isinstance(ap.get("refs"), dict) and isinstance(ap["refs"].get("page_plan"), str):
        pp_path = p.parent / ap["refs"]["page_plan"]
    else:
        pp_path = None
    if pp_path is not None and pp_path.is_file():
        try:
            pp = load_yaml(pp_path)
        except yaml.YAMLError as e:
            c.add("R-STRUCT-005", "warning", "", f"план страницы {pp_path.name} не читается: {str(e)[:120]}")
    st = site_type_of(docpaths.site(where[0], where[1], "brief", repo=repo)) if where else plan_site_type(pp, pp_path)
    check_plan(K, ap, c, pp, p.parent, st)
    return rep, c


def cmd_check_files(a):
    K = kb()
    rep = F.Report()
    todo = 0
    for f in a.check:
        if not Path(f).is_file():
            print(f"plan_to_assets: нет файла {f}", file=sys.stderr)
            return 2
        _, c = check_file(K, f, a.plan, None, rep)
        todo += c.todo
    F.print_findings(rep.items, as_json=a.json)
    if not a.json:
        print(f"файлов {len(a.check)}; заглушек TODO {todo} (дописывает агент; в утверждённом плане — ошибка)")
    return rep.exit_code()


def spec_role(K, ap, slot_id):
    """Блок role спецификации ассета для строки плана: page_type словаря, page_class проекции, section, slot, purpose."""
    row = next((s for s in ap.get("slots") or [] if isinstance(s, dict) and s.get("id") == slot_id), None)
    if row is None:
        raise KeyError(slot_id)
    pt = (ap.get("page") or {}).get("page_type")
    role = {"page_type": pt}
    pc, _ = K.page_class(pt)
    if pc:
        role["page_class"] = pc
    role["section"] = row.get("section")
    role["slot"] = row.get("id")
    goal = row.get("goal")
    role["purpose"] = goal if isinstance(goal, str) and not goal.startswith(TODO) else f"{row.get('slot')} в секции {row.get('section')}"
    d = row.get("delivery") or {}
    if d.get("lcp_candidate"):
        role["priority"] = "lcp"
    elif row.get("role") == "decorative":
        role["priority"] = "decorative"
    return role


def cmd_spec_role(a):
    K = kb()
    path, sid = a.spec_role
    ap = load_yaml(path)
    try:
        role = spec_role(K, ap, sid)
    except KeyError:
        ids = ", ".join(str(s.get("id")) for s in (ap or {}).get("slots") or [] if isinstance(s, dict))
        print(f"plan_to_assets: нет строки {sid!r}; есть: {ids or '—'}", file=sys.stderr)
        return 2
    errs = [e.message for e in K.role_validator.iter_errors(role)]
    print(json.dumps({"role": role}, ensure_ascii=False, indent=1))
    for e in errs:
        print(f"  role не по схеме asset-spec: {e}", file=sys.stderr)
    return 1 if errs else 0


def types_run(K, which="new", base=None):
    """Каркас на каждый тип страницы из плана-образца: [{page_type, status, media_class, relation, slots, error, …}]."""
    base = Path(base or BASE_PLAN)
    plan0 = load_yaml(base)
    if which == "new":
        types = list(NEW_TYPES)
    else:
        types = [t for t, v in K.page_types.items() if v.get("status", "active") not in OUT_OF_SCOPE + ("deprecated",)]
    rows = []
    for pt in types:
        plan = copy.deepcopy(plan0)
        lv = K.level_of(pt) or (plan.get("page") or {}).get("ambition_level") or "L1"
        plan["page"]["page_type"] = pt
        plan["page"]["ambition_level"] = lv
        plan["page"]["budget_profile"] = f"{pt}@{lv}"
        ap = build(plan, None, K)
        rep = F.Report()
        c = Ctx(rep, base.name, pt)
        check_plan(K, ap, c, plan, None)
        mc, rel = K.media_class(pt)
        cnt = F.count(rep.items)
        rows.append({"page_type": pt, "status": K.type_status(pt), "media_class": ap["page"].get("media_class"),
                     "relation": rel, "projection": "crosswalk §8" if mc else "нет строки", "slots": len(ap["slots"]),
                     "error": cnt["error"], "warning": cnt["warning"], "hint": cnt["hint"],
                     "findings": [f.as_dict() for f in rep.items]})
    return rows


def cmd_types(a):
    K = kb()
    rows = types_run(K, a.types, a.plan)
    if a.json:
        print(json.dumps({"base": str(a.plan or BASE_PLAN), "types": rows}, ensure_ascii=False, indent=1))
    else:
        print(f"образец: {docpaths.rel(Path(a.plan or BASE_PLAN))}")
        for r in rows:
            print(f"{r['page_type']:<24} {r['status'] or '—':<9} → {r['media_class'] or '—':<16} "
                  f"({r['projection']}{', ' + r['relation'] if r['relation'] else ''}); строк {r['slots']}; "
                  f"error {r['error']} · warning {r['warning']} · hint {r['hint']}")
            for f in r["findings"]:
                print(f"    {f['severity']} {f['rule']} {f['ref']}: {f['message']}")
        bad = sum(1 for r in rows if r["error"])
        print(f"типов {len(rows)}; с ошибками {bad}")
    return 1 if any(r["error"] for r in rows) else 0


# ------------------------------------------------------------------ режим проекта

def page_surfaces(call, need_page=False):
    ss = [call.surf] if call.surf else [s for s in call.surfaces if s.page]
    return [s for s in ss if s.page or not need_page]


def plans_of(call, s):
    d = docpaths.site(call.slug, s.slug, "plans", repo=call.repo)
    return sorted(d.glob("*.yaml")) if d.is_dir() else []


def asset_plans_of(call, s):
    d = docpaths.design(call.slug, "asset-plans", surface=s.slug, repo=call.repo)
    return sorted(d.glob("*.yaml")) if d.is_dir() else []


def cmd_build(call):
    K = kb()
    a = call.args
    wanted = set(a.page or [])
    out_root = call.out or kbpaths.out("site", "plan_to_assets", call.slug)
    project = call.project.resolve()
    res = []
    rc = 0
    for s in page_surfaces(call, need_page=True):
        home = docpaths.design(call.slug, "asset-plans", surface=s.slug, repo=call.repo)   # место файла в проекте
        dst_dir = home if a.write else Path(out_root) / s.slug
        st = site_type_of(docpaths.site(call.slug, s.slug, "brief", repo=call.repo))
        for pp in plans_of(call, s):
            try:
                plan = load_yaml(pp)
            except yaml.YAMLError as e:
                res.append({"surface": s.slug, "page": pp.stem, "result": f"план страницы не читается: {str(e)[:120]}"})
                rc = 1
                continue
            if not isinstance(plan, dict) or not isinstance(plan.get("page"), dict):
                continue
            pid = str(plan["page"].get("id") or pp.stem)
            if wanted and pid not in wanted:
                continue
            if not has_media(plan):
                res.append({"surface": s.slug, "page": pid, "result": "медиа- и 3D-слотов нет — план ассетов не нужен"})
                continue
            dest = Path(dst_dir) / f"{pid}.yaml"
            in_project = str(dest.resolve()).startswith(str(project) + os.sep)
            if in_project and dest.exists():
                res.append({"surface": s.slug, "page": pid, "path": docpaths.rel(dest, call.repo),
                            "result": "план ассетов есть — не перезаписан (правит агент; сверка — check)"})
                continue
            ap = build(plan, relpath(pp, home), K, st)      # ссылки — от места файла в проекте
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(dump_plan(ap, head_for(pp.name, pid)), encoding="utf-8")
            res.append({"surface": s.slug, "page": pid, "path": docpaths.rel(dest, call.repo), "slots": len(ap["slots"]),
                        "media_class": ap["page"].get("media_class"), "result": "каркас записан"})
        for w in sorted(wanted - {r["page"] for r in res if r["surface"] == s.slug}):
            res.append({"surface": s.slug, "page": w, "result": "нет плана страницы"})
            rc = 2
    if call.json:
        print(json.dumps({"project": call.slug, "results": res}, ensure_ascii=False, indent=1))
    else:
        for r in res:
            print(f"{r['surface']}/{r['page']}: {r['result']}" + (f" → {r['path']}" if r.get("path") else ""))
        if not res:
            print("страниц с медиа- и 3D-слотами нет")
    return rc


def input_batch(inp):
    """Партия входа холста: (вход есть, страницы партии). Страницы — поле units передней части INPUT.md, без него —
    папки pages/ входа; None — вход есть, а партию из него не узнать (манифест без передней части и без pages/): тогда
    в партии считается каждая страница."""
    manifest = Path(inp) / "INPUT.md"
    if not manifest.is_file():
        return False, None
    text = manifest.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(\r?\n|$)", text, re.S)
    try:
        fm = yaml.safe_load(m.group(1)) if m else None
    except yaml.YAMLError:
        fm = None
    if isinstance(fm, dict) and isinstance(fm.get("units"), list):
        return True, {str(u) for u in fm["units"]}
    pages = Path(inp) / "pages"
    return True, ({d.name for d in pages.iterdir() if d.is_dir()} if pages.is_dir() else None)


def cmd_check(call):
    K = kb()
    rep = F.Report()
    todo = 0
    wanted = set(call.args.page or [])
    found = []
    for s in page_surfaces(call):
        plans = {}
        for pp in plans_of(call, s) if s.page else []:
            try:
                plan = load_yaml(pp)
            except yaml.YAMLError:
                continue
            if isinstance(plan, dict) and isinstance(plan.get("page"), dict):
                plans[str(plan["page"].get("id") or pp.stem)] = (pp, plan)
        found.append((s, plans, {p.stem: p for p in asset_plans_of(call, s)}))
    unknown = sorted(wanted - {pid for _, plans, aps in found for pid in (*plans, *aps)})
    if unknown:
        raise F.ToolError(f"--page: нет страниц {', '.join(unknown)} среди планов страниц и планов ассетов")
    man = docpaths.design(call.slug, "assets", "manifest.yaml", repo=call.repo)
    if man.is_file() and not wanted:
        # манифест продукта: строки без страницы, общие для поверхностей, — проверяется один раз, без --page
        check_manifest(K, man, Ctx(rep, docpaths.rel(man, call.repo), "_assets/manifest", None,
                                   f"/design-deep-dive {call.slug} assets", kind=MANIFEST_KIND))
    for s, plans, aps in found:
        ad_status = docpaths.status(docpaths.design(call.slug, "art-direction", surface=s.slug, repo=call.repo))
        has_input, batch = input_batch(docpaths.design(call.slug, "input", surface=s.slug, repo=call.repo))
        fix = f"/design-deep-dive {call.slug} {s.slug} asset-plan:"
        st = site_type_of(docpaths.site(call.slug, s.slug, "brief", repo=call.repo)) if s.page else None
        man = docpaths.design(call.slug, "assets", surface=s.slug, repo=call.repo) / "manifest.yaml"
        if man.is_file():
            check_manifest(K, man, Ctx(rep, docpaths.rel(man, call.repo), "manifest", s.slug,
                                       f"/design-deep-dive {call.slug} {s.slug} assets", kind=MANIFEST_KIND), wanted or None)
        if wanted:
            plans = {pid: v for pid, v in plans.items() if pid in wanted}
            aps = {pid: v for pid, v in aps.items() if pid in wanted}
        for pid, (pp, plan) in plans.items():
            if not has_media(plan):
                continue
            dest = docpaths.design(call.slug, "asset-plans", pid + ".yaml", surface=s.slug, repo=call.repo)
            c0 = Ctx(rep, docpaths.rel(pp, call.repo), pid, s.slug, fix + pid)
            if pid not in aps:
                # план ассетов обязателен странице, которая уходит на холст: остальные страницы поверхности могут ждать
                # своей партии — у шаблона, до которого очередь не дошла, плана ещё нет законно
                in_batch = has_input and (batch is None or pid in batch)
                why = "" if in_batch else (" — страница вне партии входа холста: план нужен к её входу" if has_input
                                           else " — до входа холста это норма")
                c0.add("R-COV-004", "error" if in_batch else "hint", "", f"у страницы {pid} медиа- и 3D-слоты, а плана "
                       f"ассетов нет ({docpaths.rel(dest, call.repo)})" + why,
                       fix=f"plan_to_assets.py build {call.slug} {s.slug} --page {pid} --write")
                continue
            ref = (plan.get("refs") or {}).get("asset_plan") if isinstance(plan.get("refs"), dict) else None
            if not ref:
                c0.add("R-COV-004", "warning", "/refs", f"план страницы {pid} не ведёт в план ассетов: refs.asset_plan — "
                       f"{relpath(dest, pp.parent)}", fix=f"/design-deep-dive {call.slug} {s.slug} page-plan:{pid}")
            else:
                tgt = (pp.parent / ref)
                if not tgt.exists():
                    c0.add("R-REF-001", "error", "/refs/asset_plan", f"refs.asset_plan ведёт в пустоту: {ref}")
                elif tgt.resolve() != dest.resolve():
                    c0.add("R-REF-001", "error", "/refs/asset_plan", f"refs.asset_plan ведёт в {ref}, план ассетов страницы — "
                           f"{relpath(dest, pp.parent)}")
        for pid, p in aps.items():
            c = Ctx(rep, docpaths.rel(p, call.repo), pid, s.slug, fix + pid)
            ap = read_plan_file(p, c)
            if ap is None:
                continue
            pp, plan = plans.get(pid, (None, None))
            if s.page and plan is None:
                c.add("R-STRUCT-001", "warning", "", f"план ассетов страницы {pid}, которой нет среди планов site/{s.slug}/plans/")
            check_plan(K, ap, c, plan, p.parent, st)
            todo += c.todo
            refs = ap.get("refs") if isinstance(ap, dict) and isinstance(ap.get("refs"), dict) else {}
            if pp is not None and isinstance(refs.get("page_plan"), str) and (p.parent / refs["page_plan"]).exists() \
                    and (p.parent / refs["page_plan"]).resolve() != pp.resolve():
                c.add("R-REF-001", "error", "/refs/page_plan", f"refs.page_plan ведёт не в план страницы {pid}: {refs['page_plan']}")
            if c.approved:
                ps = docpaths.status(pp) if pp is not None else None
                if ps != "approved" or ad_status != "approved":
                    c.add("R-MAT-001", "warning", "/status", "план ассетов утверждён при плане страницы "
                          f"{ps or '—'} и арт-дирекции {ad_status or '—'}: утверждённое опирается на неутверждённое")
    F.print_findings(rep.items, as_json=call.json)
    if not call.json:
        print(f"заглушек TODO {todo} (дописывает агент; в утверждённом плане — ошибка)")
    return rep.exit_code()


# ------------------------------------------------------------------ самопроверка

def _selftest():
    import subprocess
    K = kb()
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)

    def rules(ap, plan=None, file_dir=None):
        rep = F.Report()
        c = Ctx(rep, "selftest", "home")
        check_plan(K, ap, c, plan, file_dir)
        return rep.items

    def codes(items, sev=None):
        return {f.rule for f in items if sev is None or f.severity == sev}

    exp_class = {"corporate-b2b-stalkon": "corporate", "lead-services-otves": "corporate", "saas-okoshko": "saas-landing"}
    for ex, mc in exp_class.items():
        pp = EXAMPLES / ex / "plans" / "home.yaml"
        plan = load_yaml(pp)
        ap = build(plan, "plans/home.yaml", K)
        items = rules(ap, plan, pp.parent.parent)
        check(f"{ex}: каркас по схеме и словарю, покрытие полное — 0 находок", not items)
        check(f"{ex}: media_class {mc} — проекция crosswalk §8", ap["page"].get("media_class") == mc)
        fx = EXAMPLES / ex / "asset-plan.home.yaml"
        text = dump_plan(ap, head_for(pp.name, ap["page"]["id"]))
        check(f"{ex}: пример asset-plan.home.yaml пересобирается байт в байт", fx.read_text(encoding="utf-8") == text)
        rep, _ = check_file(K, fx)
        check(f"{ex}: --check примера — 0 error", not any(f.severity == "error" for f in rep.items))
    otv = load_yaml(EXAMPLES / "lead-services-otves" / "plans" / "home.yaml")
    base = build(otv, "plans/home.yaml", K)
    hero = next(s for s in base["slots"] if s["id"] == "hero-visual")
    check("real-only → ai_fit forbidden и policy.no_ai_subjects", hero["ai_fit"] == "forbidden"
          and base["policy"]["no_ai_subjects"] == ["logos", "real_people_or_work"])
    check("логотип бренда без подлинности — ai_fit forbidden", next(s for s in base["slots"] if s["slot"] == "brand-logo")["ai_fit"] == "forbidden")
    check("визуал первого экрана из настоящего фото — key", hero.get("key") is True and hero["source"] == "real")
    check("alt → alt_ref <секция>.<слот>", hero.get("alt_ref") == "hero.alt")
    # отрицательные случаи на копии плана
    ap = copy.deepcopy(base)
    ap["status"] = "approved"
    it = rules(ap)
    check("status approved без approval → R-MAT-002", any(f.rule == "R-MAT-002" and "approval" in f.message for f in it))
    check("заглушки TODO в утверждённом плане → R-MAT-002", any(f.rule == "R-MAT-002" and "TODO" in f.message for f in it))
    ap = copy.deepcopy(base)
    ap["page"]["page_type"] = "landing-lead-servises"
    it = rules(ap)
    check("page_type вне словаря → R-STRUCT-005 с подсказкой", any(f.rule == "R-STRUCT-005" and "вне словаря" in f.message
                                                                   and "landing-lead-services" in f.message for f in it))
    ap = copy.deepcopy(base)
    ap["slots"][1]["slot"] = "hero-image"
    check("вид слота вне словаря → R-STRUCT-005", any(f.rule == "R-STRUCT-005" and "вне словаря" in f.message for f in rules(ap)))
    ap = copy.deepcopy(base)
    ap["slots"][0]["slot"] = "headline"
    check("вид слота не медиа → R-STRUCT-005", any("в плане ассетов только медиа и 3D" in f.message for f in rules(ap)))
    ap = copy.deepcopy(base)
    ap["page"]["media_class"] = "saas-landing"
    check("media_class не по проекции → R-STRUCT-005", any("≠ проекции crosswalk" in f.message for f in rules(ap)))
    ap = copy.deepcopy(base)
    ap["page"]["page_type"] = "ecommerce-product-page"
    ap["page"]["media_class"] = "ecom-pdp"
    check("page_type вне рамок сайта → R-STRUCT-005", any("вне рамок" in f.message for f in rules(ap)))
    ap = copy.deepcopy(base)
    ap["slots"].append(copy.deepcopy(ap["slots"][0]))
    check("повтор id строки → R-STRUCT-005", any("повторяется" in f.message for f in rules(ap)))
    ap = copy.deepcopy(base)
    ap["slots"][1]["source"] = "generate"
    it = rules(ap, otv)
    check("real-only на generate → R-COV-004 error и противоречие ai_fit → R-STRUCT-005",
          any(f.rule == "R-COV-004" and f.severity == "error" and "real-only" in f.message for f in it)
          and any(f.rule == "R-STRUCT-005" and "ai_fit: forbidden" in f.message for f in it))
    ap = copy.deepcopy(base)
    del ap["slots"][2]
    it = rules(ap, otv)
    check("медиа-слот плана страницы без строки → R-COV-004 warning (черновик)",
          any(f.rule == "R-COV-004" and f.severity == "warning" and "без строки" in f.message for f in it))
    ap["status"], ap["approval"] = "approved", {"by": "владелец продукта", "date": "2026-09-29"}
    check("… у утверждённого плана — error", any(f.rule == "R-COV-004" and f.severity == "error" and "без строки" in f.message
                                                 for f in rules(ap, otv)))
    ap = copy.deepcopy(base)
    ap["slots"][0]["id"] = "header-logotype"
    check("строка без слота плана страницы → R-COV-004 warning", any("без медиа- или 3D-слота" in f.message for f in rules(ap, otv)))
    ap = copy.deepcopy(base)
    ap["refs"] = {"page_plan": "plans/nope.yaml"}
    check("refs.page_plan в пустоту → R-REF-001", any(f.rule == "R-REF-001" for f in rules(ap, None, EXAMPLES / "lead-services-otves")))
    ap = copy.deepcopy(base)
    ap["status"], ap["approval"] = "approved", {"by": "владелец продукта", "date": "2026-09-29"}
    for s in ap["slots"]:
        for k in ("goal", "subject"):
            if str(s.get(k, "")).startswith(TODO):
                s[k] = "кадр по паспорту"
        for v in s["variants"]:
            v.update({"ratio": v["ratio"] if not str(v["ratio"]).startswith(TODO) else "1:1", "size": [1200, 1200],
                      "formats": ["avif", "webp"], "max_kb": 120})
    check("заполненный утверждённый план с approval — 0 error", not [f for f in rules(ap, otv) if f.severity == "error"])
    # каркас против своей проверки: правка настоящего кадра при real-only и слоты уровня страницы с подлинностью
    pe = copy.deepcopy(otv)
    next(s for s in pe["sections"] if s["id"] == "hero")["slots"]["media"][0]["source"] = "edit-real"
    pe["page_slots"]["media"][0].update({"source": "edit-real", "authenticity": "real-only"})
    ae = build(pe, "plans/home.yaml", K)
    he, og = (next(s for s in ae["slots"] if s["id"] == i) for i in ("hero-visual", "og-image"))
    check("edit-real при real-only → строка real, ai_fit forbidden, заметка о доводке без генерации",
          (he["source"], he["ai_fit"]) == ("real", "forbidden") and "без генерации" in he.get("note", ""))
    check("слот уровня страницы: источник и подлинность плана страницы — real, forbidden, заметка",
          (og["source"], og["ai_fit"]) == ("real", "forbidden") and "без генерации" in og.get("note", ""))
    check("… доводку без генерации называет поле local_edit — заглушка у обеих строк",
          all(str((x.get("local_edit") or [""])[0]).startswith(TODO) for x in (he, og)))
    po = copy.deepcopy(pe)
    for sec in po["sections"]:
        for sl in (sec.get("slots") or {}).get("media") or []:
            sl.pop("authenticity", None)
    check("слот уровня страницы с real-only называет предмет в policy.no_ai_subjects и без таких слотов в секциях",
          "real_people_or_work" in build(po, None, K)["policy"]["no_ai_subjects"]
          and "real_people_or_work" not in build({**po, "page_slots": {}}, None, K)["policy"]["no_ai_subjects"])
    check("каркас с edit-real при real-only проходит свою проверку — 0 находок", not rules(ae, pe, EXAMPLES / "lead-services-otves"))
    pe["page_slots"]["media"][0].update({"source": "generate", "authenticity": "generated-ok", "task": ["task:IMG-ILLUSTR"]})
    next(s for s in pe["sections"] if s["id"] == "hero")["slots"]["media"][0]["authenticity"] = "real-or-generated"
    ae = build(pe, "plans/home.yaml", K)
    he, og = (next(s for s in ae["slots"] if s["id"] == i) for i in ("hero-visual", "og-image"))
    check("edit-real при real-or-generated остаётся правкой: conditional и предмет-заглушка",
          (he["source"], he["ai_fit"]) == ("edit-real", "conditional") and str(he.get("subject", "")).startswith(TODO))
    check("слот уровня страницы на generate: allowed, коды задач и предмет-заглушка",
          (og["source"], og["ai_fit"], og["task_codes"]) == ("generate", "allowed", ["IMG-ILLUSTR"])
          and str(og.get("subject", "")).startswith(TODO))
    check("… и такой каркас проходит свою проверку — 0 находок", not rules(ae, pe, EXAMPLES / "lead-services-otves"))
    # 3D: постер, рендер, загрузка по умолчанию схемы плана страницы
    p3 = copy.deepcopy(otv)
    hero_sec = next(s for s in p3["sections"] if s["id"] == "hero")
    hero_sec["slots"]["media"].append({"id": "poster", "slot": "hero-visual", "media_role": "informational",
                                       "poster_for": "model", "ratio": {"desktop": "16:9", "mobile": "4:5"}})
    hero_sec["slots"]["3d"] = [{"id": "model", "slot": "model-3d", "poster": "poster", "recipe": "recipe:01-hero-product"}]
    a3 = build(p3, None, K)
    m3 = next(s for s in a3["slots"] if s["id"] == "hero-model")
    po = next(s for s in a3["slots"] if s["id"] == "hero-poster")
    check("3D без load — умолчание схемы плана страницы", m3["delivery"]["load"] == K.load_3d == "on-interaction")
    check("3D-строка: постер, рецепт, cta_before_3d", m3["poster"] == "hero-poster" and m3["recipe"] == "recipe:01-hero-product"
          and m3["three_d"]["cta_before_3d"] is True and m3["ladder"] == "3d")
    check("постер 3D-слота без source — render, ключевой, poster_for", po["source"] == "render" and po.get("key") is True
          and po["poster_for"] == "hero-model")
    check("каркас с 3D — 0 error (черновик)", not [f for f in rules(a3, p3) if f.severity == "error"])
    ap = copy.deepcopy(a3)
    del next(s for s in ap["slots"] if s["id"] == "hero-model")["poster"]
    check("3D-слот без постера → R-COV-004 error", any(f.rule == "R-COV-004" and "без постера" in f.message for f in rules(ap)))
    ap = copy.deepcopy(a3)
    ap["status"], ap["approval"] = "approved", {"by": "владелец продукта", "date": "2026-09-29"}
    check("утверждённый план: 3D без дороги → R-MAT-002", any(f.rule == "R-MAT-002" and "дороги 3D" in f.message for f in rules(ap)))
    ap = copy.deepcopy(a3)
    next(s for s in ap["slots"] if s["id"] == "hero-model")["three_d"]["road"] = "hybrid"
    next(s for s in ap["slots"] if s["id"] == "hero-poster")["source"] = "render"
    check("дорога 3D hybrid и source render проходят схему", not [f for f in rules(ap) if f.rule == "R-STRUCT-005"])
    # 10 типов v1: проекция из crosswalk §8, без ошибок
    rows = types_run(K, "new")
    check("10 типов v1: у каждого строка проекции §8", len(rows) == 10 and all(r["projection"] == "crosswalk §8" for r in rows))
    check("10 типов v1: каркас без ошибок", all(r["error"] == 0 for r in rows))
    rows = types_run(K, "all")
    check(f"все типы в рамках ({len(rows)}): проекция и каркас без ошибок", rows and all(r["error"] == 0 and r["media_class"] for r in rows))
    ptl = K.budgets.get("page_type_levels") or {}
    check("уровень по умолчанию — таблица creative (faq L0, landing-product L1, landing-campaign L2, proposed — нет); "
          "в budgets.yaml — ссылка без копии",
          (K.level_of("faq-page"), K.level_of("landing-product"), K.level_of("landing-campaign"), K.level_of("event-program-page"))
          == ("L0", "L1", "L2", None) and "default" not in ptl and str(ptl.get("ref", "")).endswith("ambition-levels.yaml#defaults_by_page_type"))
    # спецификация ассета: page_type словаря и проекция page_class
    role = spec_role(K, base, "hero-visual")
    check("--spec-role: page_type словаря, page_class проекции, role по схеме asset-spec",
          role["page_type"] == "landing-lead-services" and role["page_class"] == "landing" and role["priority"] == "lcp"
          and not list(K.role_validator.iter_errors(role)))
    # источник по варианту: перечень тот же, что у слота; подлинность и маршрут сверяются по каждому варианту
    sp = K.schema["$defs"]
    check("variants[].source — перечень тот же, что у source слота",
          sp["variant"]["properties"]["source"]["enum"] == sp["slot"]["properties"]["source"]["enum"])
    ap = copy.deepcopy(base)
    hv = next(s for s in ap["slots"] if s["id"] == "hero-visual")
    hv["ai_fit"] = "conditional"
    hv["variants"][0]["source"] = "generate"
    check("телефон — настоящий кадр, десктоп — генерация: источник варианта проходит схему и сверку",
          hv["variants"][0]["id"] == "desktop" and not [f for f in rules(ap) if f.severity == "error"])
    hv["ai_fit"] = "forbidden"
    it = rules(ap, otv)
    check("generate у варианта при ai_fit: forbidden → R-STRUCT-005, при real-only → R-COV-004: находки называют вариант",
          any(f.rule == "R-STRUCT-005" and f.severity == "error" and "вариант desktop" in f.message for f in it)
          and any(f.rule == "R-COV-004" and f.severity == "error" and "вариант desktop" in f.message
                  and f.ref.endswith("/variants/0/source") for f in it))
    hv["ai_fit"], hv["task_codes"] = "conditional", []
    ap["status"], ap["approval"] = "approved", {"by": "владелец продукта", "date": "2026-09-29"}
    check("утверждённый план: генерация у варианта без кодов задач → R-MAT-002",
          any(f.rule == "R-MAT-002" and "вариант desktop" in f.message and "кодов задач" in f.message for f in rules(ap)))
    hv["variants"][0]["source"] = "photo"
    check("источник варианта вне перечня → R-STRUCT-005", any(f.rule == "R-STRUCT-005" and f.ref.endswith("/variants/0/source")
                                                               for f in rules(ap)))
    # класс по типу сайта брифа: строка «§8 (page.media_class)» таблицы, у типа сайта без строки — проекция page_type
    stk = load_yaml(EXAMPLES / "corporate-b2b-stalkon" / "plans" / "home.yaml")
    folio = build(stk, None, K, "portfolio-site")
    check("главная сайта-портфолио: media_class studio — проекция типа сайта; тип сайта без строки — проекция page_type",
          folio["page"]["media_class"] == "studio" and build(stk, None, K, "corporate-site")["page"]["media_class"] == "corporate")

    def class_findings(ap_, st_):
        rep_ = F.Report()
        check_plan(K, ap_, Ctx(rep_, "selftest", "home"), None, None, st_)
        return [f for f in rep_.items if "media_class" in f.message]

    ap = copy.deepcopy(folio)
    by_site = class_findings(ap, "portfolio-site")
    ap["page"]["media_class"] = "corporate"
    by_type = class_findings(ap, "portfolio-site")
    ap["page"]["media_class"] = "blog"
    check("сверка media_class при типе сайта: проходят проекция типа сайта и проекция page_type, прочее → R-STRUCT-005",
          not by_site and not by_type and any(f.severity == "error" and "portfolio-site" in f.message
                                              for f in class_findings(ap, "portfolio-site")))
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "plans").mkdir()
        (Path(td) / "site-brief.yaml").write_text("site_type: portfolio-site\n", encoding="utf-8")
        check("тип сайта для файла плана страницы — бриф по refs.brief; ссылки нет — None",
              plan_site_type({"refs": {"brief": "../site-brief.yaml"}}, Path(td) / "plans" / "home.yaml") == "portfolio-site"
              and plan_site_type({}, Path(td) / "plans" / "home.yaml") is None)

    # демо-картинка макета: форма x-demo {file | files, what}; путь машинный — файл на диске не сверяется
    def demo(value):
        ap_ = copy.deepcopy(base)
        next(s for s in ap_["slots"] if s["id"] == "hero-visual")[DEMO] = value
        return [(f.rule, f.severity) for f in rules(ap_) if DEMO in f.ref]

    check("x-demo: file и what, files по вариантам и ключи-заметки проекта — 0 находок",
          not demo({"file": "/nowhere/demo.png", "what": "кадр-заглушка до съёмки"})
          and not demo({"files": {"desktop": "/nowhere/d.png", "mobile": "/nowhere/m.png"}, "what": "кадр-заглушка",
                        "route": "заметка проекта"}))
    bad = [demo("demo.png"), demo({"what": "кадр-заглушка"}), demo({"file": "", "what": "кадр-заглушка"}),
           demo({"files": {"tablet": "/nowhere/t.png"}, "what": "кадр-заглушка"}), demo({"file": "/nowhere/demo.png"})]
    check("x-demo неверной формы (не объект, нет пути, пустой file, вариант вне variants, нет what) → R-STRUCT-005 warning",
          all(b and set(b) == {("R-STRUCT-005", "warning")} for b in bad))
    # статус proposed, доводка без генерации, экземпляры шаблона коллекции, источник настоящего кадра
    ap = copy.deepcopy(base)
    ap["status"] = "proposed"
    ap["instances"] = [{"id": "sample-one", "title": "первая запись коллекции"}]
    hv = next(s for s in ap["slots"] if s["id"] == "hero-visual")
    hv.update({"local_edit": ["кадрирование", "цвет"], "instance": "sample-one",
               "real_source": {"origin": "архив заказчика", "file": "frame-01.tif"}})
    check("status proposed, local_edit, instances и instance, real_source — по схеме, 0 находок", not rules(ap))
    hv["source"], hv["ai_fit"] = "edit-real", "conditional"
    check("local_edit при источнике edit-real — настоящий кадр есть, находки нет",
          not [f for f in rules(ap) if f.ref.endswith("/local_edit")])
    hv["source"], hv["ai_fit"] = "real", "forbidden"
    hv["instance"] = "sample-two"
    next(s for s in ap["slots"] if s["id"] == "og-image")["local_edit"] = ["кадрирование"]
    it = rules(ap)
    check("instance без записи в instances и local_edit у строки без настоящего кадра → R-STRUCT-005 warning",
          {f.ref.rpartition("/")[2] for f in it if f.rule == "R-STRUCT-005" and f.severity == "warning"} == {"instance", "local_edit"}
          and not [f for f in it if f.severity == "error"])

    def meta_ok(schema):
        try:
            type(K.validator).check_schema(schema)
        except Exception:                                # noqa: BLE001 — любой отказ метасхемы — провал случая
            return False
        return True

    check("схемы плана ассетов и манифеста ассетов проходят метасхему Draft 2020-12",
          meta_ok(K.schema) and meta_ok(K.manifest_validator.schema))
    # проект: фикстура asset-plan (лендинг promo с планом ассетов главной)
    kbpaths.use("tests")
    import fixture_project
    tool = [sys.executable, str(Path(__file__).resolve())]
    with fixture_project.built(FIXTURE) as fx:
        r = subprocess.run(tool + ["check", fx.slug, "promo", "--repo", str(fx.root), "--json"], capture_output=True, text=True)
        items = F.parse_lines(r.stdout)
        check(f"фикстура: check — 0 находок, код 0 ({len(items)} находок, код {r.returncode})", r.returncode == 0 and not items)
        # манифест ассетов поверхности: форма по схеме — предупреждением, код выхода не меняется
        man = fx.project / "design" / "promo" / "assets" / "manifest.yaml"
        man_src = fixture_project.FIXTURES / "package-landing-defects" / "files" / "design" / "promo" / "assets" / "manifest.yaml"

        def man_check(text, *more):
            man.write_text(text, encoding="utf-8")
            r_ = subprocess.run(tool + ["check", fx.slug, "promo", *more, "--repo", str(fx.root), "--json"],
                                capture_output=True, text=True)
            return r_.returncode, [(f.rule, f.severity, f.kind) for f in F.parse_lines(r_.stdout)]

        check("фикстура: манифест ассетов фикстуры package-landing-defects проходит схему — check 0 находок",
              man_src.is_file() and man_check(man_src.read_text(encoding="utf-8")) == (0, []))
        hero = man.parent / "hero-visual-desktop.webp"
        hero.write_bytes(b"webp\n")
        real = hashlib.sha256(b"webp\n").hexdigest()
        row = ("slot: hero-visual\n  page: home\n  file: hero-visual-desktop.webp\n  variant: desktop\n  format: webp\n"
               "  status: accepted\n  license: права у заказчика (демо)\n  origin: съёмка заказчика (демо)\n  ai: false\n"
               "  sha256: " + real + "\n")
        check("фикстура: манифест списком строк, у принятой строки отпечаток файла — 0 находок",
              man_check("- " + row) == (0, []))
        # отпечаток принятой строки — отпечаток файла в локе снимка код-репо: расхождение — error
        check("фикстура: у принятой строки sha256 не равен файлу → R-STRUCT-005 error, код 1",
              man_check("- " + row.replace(real, "a1" * 32)) == (1, [("R-STRUCT-005", "error", MANIFEST_KIND)]))
        check("фикстура: у принятой строки нет sha256 → R-STRUCT-005 error",
              man_check("- " + row.replace("  sha256: " + real + "\n", "")) == (1, [("R-STRUCT-005", "error", MANIFEST_KIND)]))
        check("фикстура: файла принятой строки нет → R-REF-001 error",
              man_check("- " + row.replace("hero-visual-desktop.webp", "nope.webp")) == (1, [("R-REF-001", "error", MANIFEST_KIND)]))
        check("фикстура: черновая строка с чужим sha256 не сверяется — 0 находок",
              man_check("- " + row.replace(real, "a1" * 32).replace("status: accepted", "status: draft")) == (0, []))
        check("фикстура: check --page — общая строка без page с чужим sha256 не сверяется",
              man_check("- " + row.replace(real, "a1" * 32).replace("  page: home\n", ""), "--page", "home") == (0, []))
        man.write_text("- " + row, encoding="utf-8")
        prod = fx.project / "design" / "_assets" / "manifest.yaml"
        prod.parent.mkdir(parents=True, exist_ok=True)
        (prod.parent / "logo.svg").write_text("<svg/>\n", encoding="utf-8")
        prod.write_text("assets:\n- slot: header-logo\n  file: logo.svg\n  status: accepted\n  sha256: " + "b2" * 32 + "\n",
                        encoding="utf-8")
        r = subprocess.run(tool + ["check", fx.slug, "--repo", str(fx.root), "--json"], capture_output=True, text=True)
        got = [(f.rule, f.severity, f.surface, f.path.endswith("design/_assets/manifest.yaml")) for f in F.parse_lines(r.stdout)]
        check("фикстура: манифест продукта — у принятой строки sha256 не равен файлу → R-STRUCT-005 error без поверхности",
              r.returncode == 1 and got == [("R-STRUCT-005", "error", None, True)])
        check("фикстура: check --page — манифест продукта не сверяется",
              man_check("- " + row, "--page", "home") == (0, []))
        (prod.parent / "fonts").mkdir()
        (prod.parent / "fonts" / "demo-400.woff2").write_bytes(b"wOF2\n")
        frow = ("- slot: font-demo\n  file: fonts/demo-400.woff2\n  status: accepted\n  license: OFL (демо)\n  sha256: "
                + hashlib.sha256(b"wOF2\n").hexdigest() + "\n")
        fonts = {}
        for name, extra in (("без font", ""), ("с font", "  font: {family: Demo Sans, weight: 400, style: normal}\n"),
                            ("font не по форме", "  font: {family: Demo Sans, weight: bold}\n")):
            prod.write_text("assets:\n" + frow + extra, encoding="utf-8")
            r = subprocess.run(tool + ["check", fx.slug, "--repo", str(fx.root), "--json"], capture_output=True,
                               text=True)
            fonts[name] = [(f.rule, f.severity, f.ref.endswith("/font") or "font" in f.message)
                           for f in F.parse_lines(r.stdout)]
        check("фикстура: строка файла шрифта манифеста продукта без font {family, weight, style} и font не по форме "
              "(насыщенность словом, нет начертания) — R-STRUCT-005 warning; с font — 0 находок",
              fonts["без font"] == [("R-STRUCT-005", "warning", True)] and fonts["с font"] == []
              and fonts["font не по форме"] and set(fonts["font не по форме"]) == {("R-STRUCT-005", "warning", True)})
        prod.unlink()
        (prod.parent / "logo.svg").unlink()
        (prod.parent / "fonts" / "demo-400.woff2").unlink()
        (prod.parent / "fonts").rmdir()
        broken = ("manifest_version: 1\nassets:\n- " + row.replace("status: accepted", "status: done")
                  + "- slot: header-logo\n  role: informational\n")
        check("фикстура: статус строки вне перечня и строка без file → R-STRUCT-005 warning вида asset-manifest, код 0",
              man_check(broken) == (0, [("R-STRUCT-005", "warning", MANIFEST_KIND)] * 2))
        check("фикстура: check --page — из манифеста только строки этой страницы",
              man_check(broken, "--page", "home") == (0, [("R-STRUCT-005", "warning", MANIFEST_KIND)]))
        man.unlink()
        # тип сайта брифа: каркас берёт класс по строке типа сайта, план с классом по page_type проверку проходит
        brief = fx.project / "site" / "promo" / "site-brief.yaml"
        brief_text = brief.read_text(encoding="utf-8")
        brief.write_text(re.sub(r"(?m)^site_type: .*$", "site_type: portfolio-site", brief_text), encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(tool + ["build", fx.slug, "promo", "--repo", str(fx.root), "--out", td], capture_output=True, text=True)
            built_class = (load_yaml(Path(td) / "promo" / "home.yaml").get("page") or {}).get("media_class")
        r = subprocess.run(tool + ["check", fx.slug, "promo", "--repo", str(fx.root), "--json"], capture_output=True, text=True)
        check("фикстура: бриф сайта-портфолио — build даёт media_class studio, план с классом по page_type проходит check",
              built_class == "studio" and r.returncode == 0 and not F.parse_lines(r.stdout))
        brief.write_text(brief_text, encoding="utf-8")
        r = subprocess.run(tool + ["check", fx.slug, "cabinet", "--repo", str(fx.root)], capture_output=True, text=True)
        check("фикстура: поверхность кабинета без планов ассетов — код 0", r.returncode == 0)
        r = subprocess.run(tool + ["check", fx.slug, "nope", "--repo", str(fx.root)], capture_output=True, text=True)
        check("фикстура: неизвестная поверхность — код 2", r.returncode == 2)
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run(tool + ["build", fx.slug, "promo", "--repo", str(fx.root), "--out", td, "--json"],
                               capture_output=True, text=True)
            out = Path(td) / "promo" / "home.yaml"
            proj_ap = fx.project / "design" / "promo" / "assets" / "plans" / "home.yaml"
            check("фикстура: build --out — каркас главной рядом с проектом", r.returncode == 0 and out.is_file())
            check("фикстура: каркас build байт в байт = план ассетов фикстуры (refs.page_plan — от места в проекте)",
                  out.read_text(encoding="utf-8") == proj_ap.read_text(encoding="utf-8"))
        before = proj_ap.read_text(encoding="utf-8")
        r = subprocess.run(tool + ["build", fx.slug, "promo", "--repo", str(fx.root), "--write"], capture_output=True, text=True)
        check("фикстура: build --write не перезаписывает план ассетов", r.returncode == 0 and proj_ap.read_text(encoding="utf-8") == before
              and "не перезаписан" in r.stdout)
        pp = fx.project / "site" / "promo" / "plans" / "home.yaml"
        pp.write_text(pp.read_text(encoding="utf-8").replace("  asset_plan: ../../../design/promo/assets/plans/home.yaml\n", ""),
                      encoding="utf-8")
        proj_ap.write_text(before.replace("status: draft", "status: approved"), encoding="utf-8")
        r = subprocess.run(tool + ["check", fx.slug, "--repo", str(fx.root), "--json"], capture_output=True, text=True)
        got = {(f.rule, f.severity) for f in F.parse_lines(r.stdout)}
        check("фикстура: план страницы без refs.asset_plan → R-COV-004 warning", ("R-COV-004", "warning") in got)
        check("фикстура: утверждённый каркас → R-MAT-002 и R-MAT-001, код 1",
              {("R-MAT-002", "error"), ("R-MAT-001", "warning")} <= got and r.returncode == 1)
        proj_ap.unlink()
        r = subprocess.run(tool + ["check", fx.slug, "promo", "--repo", str(fx.root), "--json"], capture_output=True, text=True)
        got = F.parse_lines(r.stdout)
        check("фикстура: плана ассетов нет до арт-дирекции → R-COV-004 hint", [(f.rule, f.severity) for f in got] == [("R-COV-004", "hint")])
        inp = fx.project / "design" / "promo" / "input"
        inp.mkdir(parents=True)
        (inp / "INPUT.md").write_text("stage: mockup\n", encoding="utf-8")
        r = subprocess.run(tool + ["check", fx.slug, "promo", "--repo", str(fx.root), "--json"], capture_output=True, text=True)
        check("фикстура: плана ассетов нет при входе холста → R-COV-004 error", r.returncode == 1
              and [(f.rule, f.severity) for f in F.parse_lines(r.stdout)] == [("R-COV-004", "error")])

        def cov(manifest):
            (inp / "INPUT.md").write_text(manifest, encoding="utf-8")
            r_ = subprocess.run(tool + ["check", fx.slug, "promo", "--repo", str(fx.root), "--json"], capture_output=True, text=True)
            return r_.returncode, [(f.rule, f.severity) for f in F.parse_lines(r_.stdout)]

        check("фикстура: страница вне партии входа (units) → R-COV-004 hint, код 0",
              cov("---\nstage: mockup\nunits:\n- spasibo\n---\n") == (0, [("R-COV-004", "hint")]))
        check("фикстура: страница в партии входа (units) → R-COV-004 error, код 1",
              cov("---\nstage: mockup\nunits:\n- home\n- spasibo\n---\n") == (1, [("R-COV-004", "error")]))
        (inp / "pages" / "spasibo").mkdir(parents=True)
        check("фикстура: вход без units — партия по папкам pages/: страницы там нет → hint",
              cov("---\nstage: mockup\n---\n") == (0, [("R-COV-004", "hint")]))
        (inp / "pages" / "home").mkdir()
        check("фикстура: … страница среди папок pages/ → error", cov("---\nstage: mockup\n---\n")[0] == 1)
        r = subprocess.run(tool + ["build", fx.slug, "promo", "--repo", str(fx.root), "--write"], capture_output=True, text=True)
        check("фикстура: build --write пишет каркас на пустое место", r.returncode == 0 and proj_ap.is_file()
              and "каркас записан" in r.stdout)
        # сужение проверки до страниц: второй план ассетов с ошибкой не портит код выхода первой страницы
        extra = proj_ap.with_name("spasibo.yaml")
        extra.write_text(proj_ap.read_text(encoding="utf-8").replace("status: draft", "status: approved"), encoding="utf-8")
        r = subprocess.run(tool + ["check", fx.slug, "promo", "--repo", str(fx.root), "--json"], capture_output=True, text=True)
        refs = {f.ref.split("#")[0] for f in F.parse_lines(r.stdout) if f.severity == "error"}
        check("фикстура: check поверхности — ошибки второго плана, код 1", r.returncode == 1 and bool(refs))
        r = subprocess.run(tool + ["check", fx.slug, "promo", "--page", "home", "--repo", str(fx.root), "--json"],
                           capture_output=True, text=True)
        check("фикстура: check --page home — только находки страницы, код 0",
              r.returncode == 0 and not [f for f in F.parse_lines(r.stdout) if "spasibo" in f.path])
        r = subprocess.run(tool + ["check", fx.slug, "promo", "--page", "spasibo", "--repo", str(fx.root), "--json"],
                           capture_output=True, text=True)
        check("фикстура: check --page второго плана — его ошибки, код 1",
              r.returncode == 1 and all("spasibo" in f.path for f in F.parse_lines(r.stdout)))
        r = subprocess.run(tool + ["check", fx.slug, "promo", "--page", "nope", "--repo", str(fx.root)], capture_output=True, text=True)
        check("фикстура: check --page неизвестной страницы — код 2 и имя в сообщении", r.returncode == 2 and "nope" in r.stderr)
    print("plan_to_assets selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


# ------------------------------------------------------------------ вызов

def file_parser():
    ap = argparse.ArgumentParser(prog="plan_to_assets.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan_file", nargs="?", metavar="PAGE_PLAN", help="план страницы (YAML) — каркас плана ассетов")
    ap.add_argument("--out", metavar="FILE", help="куда записать каркас (по умолчанию — печать)")
    ap.add_argument("--check", nargs="+", metavar="ASSET_PLAN", help="проверить файлы плана ассетов")
    ap.add_argument("--plan", metavar="PAGE_PLAN", help="план страницы для покрытия (--check) или образец (--types)")
    ap.add_argument("--spec-role", nargs=2, metavar=("ASSET_PLAN", "SLOT"), help="блок role спецификации ассета для строки")
    ap.add_argument("--types", nargs="?", const="new", choices=("new", "all"), help="каркас на каждый тип страницы словаря")
    ap.add_argument("--json", action="store_true", help="машинный вывод")
    ap.add_argument("--selftest", action="store_true", help="самопроверка на примерах баз и фикстуре, без сети")
    return ap


def project_parser():
    ap = docpaths.parser("plan_to_assets.py", "План ассетов проекта: каркасы страниц (build) и проверка (check). "
                         "Подробно — plan_to_assets.py --help.", surface="optional", accept=lambda s: s.design)
    ap.add_argument("--page", action="append", metavar="ID", help="только эти страницы (build и check); ключ — повтором")
    ap.add_argument("--write", action="store_true", help="build: в проект, только для страниц без плана ассетов")
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv and argv[0] in ("build", "check"):
            call = docpaths.parse(project_parser(), argv)
            return cmd_build(call) if call.command == "build" else cmd_check(call)
        ap = file_parser()
        a = ap.parse_args(argv)
        if a.selftest:
            return _selftest()
        if a.check:
            return cmd_check_files(a)
        if a.spec_role:
            return cmd_spec_role(a)
        if a.types:
            return cmd_types(a)
        if a.plan_file:
            a.plan = a.plan_file
            return cmd_skeleton(a)
        ap.print_help()
        return 2
    except F.ToolError as e:
        print(f"plan_to_assets: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
