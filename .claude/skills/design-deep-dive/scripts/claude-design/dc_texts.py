#!/usr/bin/env python3
"""dc_texts — тексты исходников холста в формате `copy.md`: обратный разбор правок заказчика для приёма в copy deck.

Холст не источник текстов: заказчик правит текст на артборде, а тексты страницы живут в copy deck слоя страницы. При
слиянии правок (`references/claude-design.md § Правки заказчика`) текстовая правка поднимается в copy deck вариантом
`source: customer` — через приём `copydeck.py import-copy`. Эта утилита готовит для приёма файл `copy.md` того же
синтаксиса, что выгрузка текстов во вход холста (разбор и запись — `copydeck.py`, `parse_copy_md` и `render_copy_md`):
`## <section_id>` → `[<slot_id>]: <текст>` без статуса (у текстов холста его нет), тексты без секции или слота плана —
`## ?` и `[? <подпись>]` для разбора агентом.

Как текст находит место:
  - текстовые единицы артборда — заголовки, абзацы, пункты, подписи, кнопки и ссылки, ячейки, опции, подсказки полей
    (`placeholder`), текст прямо в контейнере; ветки `<sc-if>` читаются все (правка бывает в любом состоянии), alt и
    подписи картинок не берутся (они — ассеты, `assets.md`), текст с дыркой `{{…}}` — шаблон, он идёт строкой без слота;
  - служебная пометка артборда — элемент с атрибутом `data-wf` (подпись заглушки медиа, ярлык роли секции) — не текст
    страницы: единицей не становится и в copy deck не попадает;
  - секция — атрибут `data-section` или `id` предка, равный id секции плана (id секций холста = id плана, протокол §
    Вход холста); `header`, `footer`, `nav` без id — секция плана с тем же именем, если она есть;
  - слот — атрибут `data-slot`; иначе текст равен тексту слота copy deck (любого варианта) или строке `copy.md`
    входа; иначе — по месту: несопоставленный текст секции и несопоставленный слот той же секции в порядке документа,
    если тег подходит типу слота (заголовок — h1…h6, кнопка — a или button, абзац — p и т. п.; пара «по месту»
    помечена комментарием `# по месту: …`); слоты alt, подписи картинки и текста в картинке текстом на артборде не
    стоят и в сопоставление по тексту и по месту не входят — иначе чужой текст секции занял бы слот alt;
  - остальное — `[? <тег>]` в своей секции или в `## ?` с подписью ориентира (aria-label, id, тег);
  - несколько артбордов одной страницы (десктоп и телефон) сводятся в один файл: у слота — текст первого артборда,
    другой текст того же слота с другого артборда — строка `[? <slot_id> · <артборд>]`.
Без плана и copy deck секции и слоты берутся только из разметки (`data-section`, `data-slot`, `id`).

Команды:
  dc_texts.py show <slug> <surface> --page ID [--artboards A.dc.html,B.dc.html] [--repo DIR] [--out ФАЙЛ] [--json]
      артборды design/<surface>/canvas/project/ (по умолчанию — все артборды страниц макета) против copy deck
      site/<surface>/copy/<page-id>.yaml; файл в репозиторий не пишется: stdout или --out (например, scratchpad).
  dc_texts.py file <артборд.dc.html …> [--deck DECK --page ID | --copy COPY.md] [--out ФАЙЛ] [--json]
      то же вне проекта.
  dc_texts.py --selftest      круг «выгрузка copy deck → артборд → разбор → import-copy» на примере text, пример
                              claude-design, без сети
Дальше — приём: `copydeck.py import-copy COPY.md --deck DECK --page ID -o OUT`. Коды выхода: 0 — готово; 2 — ошибка
вызова или окружения.
"""
from __future__ import annotations

import argparse
import functools
import html
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
sys.path.insert(0, str(HERE))
import kbpaths  # noqa: E402
import docpaths  # noqa: E402
import dc_to_html as DC  # noqa: E402

kbpaths.use("text")
import copydeck as CD  # noqa: E402

BLOCKS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "button", "figcaption", "blockquote", "td", "th", "dt", "dd",
          "label", "legend", "summary", "caption", "option"}
INLINE = {"a", "span", "small", "strong", "em", "b", "i", "q", "cite", "mark", "u", "time", "abbr", "sup", "sub", "s",
          "code", "kbd", "br", "wbr"}
CONTAINERS = {"section", "header", "footer", "nav", "main", "aside", "article", "form", "div", "figure", "ul", "ol",
              "dl", "table", "tbody", "thead", "tr", "fieldset"}
SKIP = {"script", "style", "svg", "helmet", "template", "noscript", "head", "title", "select-none"}
LANDMARKS = ("header", "footer", "nav")
SLUG = re.compile(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")
# тип слота → теги, которыми его текст стоит на артборде (подбор «по месту»)
H1 = {"h1", "h2"}
HEAD = {"h2", "h3", "h4", "h5", "h6", "summary", "dt", "strong", "legend", "caption"}
PROSE = {"p", "div", "span", "li", "blockquote", "dd", "label", "small", "figcaption"}
ACTION = {"a", "button", "span"}
SHORT = {"span", "p", "small", "div", "strong", "li"}
SLOT_TAGS = {
    "headline": H1, "article-title": H1,
    "section-title": HEAD, "card-title": HEAD, "step-title": HEAD, "faq-q": HEAD, "case-title": HEAD,
    "pricing-plan-name": HEAD, "article-heading": HEAD, "form-title": HEAD, "email-heading": HEAD,
    "cta-label": ACTION, "cta-secondary-label": ACTION, "email-cta-label": ACTION, "nav-label": {"a", "li", "span"},
    "list-item": {"li", "td", "span", "p"}, "pricing-feature": {"li", "td", "span", "p"},
    "spec-row": {"li", "td", "tr", "p"}, "comparison-row": {"li", "td", "tr", "p"},
    "eyebrow": SHORT, "badge": SHORT, "announcement": SHORT, "stat-label": SHORT, "logos-caption": SHORT,
    "stat-value": {"span", "p", "strong", "div", "dd"}, "pricing-price": {"span", "p", "strong", "div", "dd"},
    "price-old": {"span", "p", "s", "div"},
    "testimonial-attribution": {"cite", "span", "p", "figcaption", "div"}, "article-author": {"cite", "span", "p"},
    "testimonial-quote": {"blockquote", "p", "q", "div"},
}


class ToolError(RuntimeError):
    """Ошибка вызова или окружения — код выхода 2."""


@dataclass
class Unit:
    text: str
    tag: str
    section: str | None                                # id секции (плана или разметки)
    slot: str | None                                   # data-slot
    landmark: str                                      # подпись ориентира для «## ?»
    template: bool = False                             # в тексте дырка {{…}}
    artboard: str = ""
    order: int = 0


@dataclass
class RefSlot:
    section: str
    slot: str
    stype: str | None
    texts: list = field(default_factory=list)


def norm(s):
    return CD.norm_ws(html.unescape(s or ""))


# ------------------------------------------------------------------ текстовые единицы артборда

def _text_of(node):
    """Текст узла: текстовые узлы, <br> — перевод строки; скрытые подпапки (svg, script) и служебные пометки артборда
    (`data-wf`) не читаются."""
    out = []
    for ch in node.children:
        if isinstance(ch, DC.Tx):
            if ch.kind == "text":
                out.append(ch.raw)
        elif ch.tag == "br":
            out.append("\n")
        elif ch.tag not in SKIP and "data-wf" not in ch.attrs:
            out.append("".join(_text_of(ch)))
    return "".join(out)


def _has_block(node):
    return any(isinstance(n, DC.El) and n is not node and (n.tag in BLOCKS or n.tag in CONTAINERS)
               for n in DC.walk(node))


def units_of(ab, plan_sections=()):
    """Текстовые единицы артборда по порядку документа."""
    plan = set(plan_sections)
    top = ab.xdc if ab.xdc is not None else ab.root
    out = []

    def sec_of(stack):
        for el in reversed(stack):
            if el.attrs.get("data-section"):
                return el.attrs["data-section"].strip()
        for el in reversed(stack):
            i = (el.attrs.get("id") or "").strip()
            if i and (i in plan or (not plan and SLUG.match(i) and el.tag in CONTAINERS)):
                return i
        for el in reversed(stack):
            if el.tag in LANDMARKS and el.tag in plan:
                return el.tag
        return None

    def landmark(stack):
        for el in reversed(stack):
            if el.tag in ("section", "header", "footer", "nav", "aside", "article", "form", "main"):
                return el.attrs.get("aria-label") or el.attrs.get("id") or el.tag
        return ""

    def slot_of(stack):
        for el in reversed(stack):
            if el.attrs.get("data-slot"):
                return el.attrs["data-slot"].strip()
            if el.attrs.get("data-section"):
                break
        return None

    def add(el, stack, text, tag=None):
        t = text.replace("\r", "")
        lines = [CD.norm_ws(x) for x in t.split("\n")]
        t = "\n".join(x for x in lines if x)
        if not t.strip():
            return
        out.append(Unit(t, tag or el.tag, sec_of(stack), slot_of(stack), landmark(stack), "{{" in t, ab.name,
                        len(out)))

    def rec(node, stack, in_block):
        for ch in node.children:
            if not isinstance(ch, DC.El) or ch.tag in SKIP or DC.is_logic(ch) or "data-wf" in ch.attrs:
                continue                               # служебная пометка артборда (data-wf) — не текст страницы
            st = stack + [ch]
            if ch.tag in ("input", "textarea") and ch.attrs.get("placeholder"):
                add(ch, st, html.unescape(ch.attrs["placeholder"]), "placeholder")
            if in_block:
                continue
            if ch.tag in BLOCKS and not _has_block(ch):
                add(ch, st, html.unescape(_text_of(ch)))
                rec(ch, st, True)
                continue
            if ch.tag in INLINE and not _has_block(ch):
                add(ch, st, html.unescape(_text_of(ch)))
                rec(ch, st, True)
                continue
            direct = "".join(c.raw for c in ch.children if isinstance(c, DC.Tx) and c.kind == "text")
            if direct.strip():
                add(ch, st, html.unescape(direct))
            rec(ch, st, False)

    rec(top, [], False)
    return out


# ------------------------------------------------------------------ план: copy deck или copy.md

def ref_from_deck(deck_data, page_id):
    deck = CD.deck_root(deck_data)
    page = next((p for p in CD.pages_of(deck) if str(p.get("page_id")) == str(page_id)), None)
    if page is None:
        have = ", ".join(str(p.get("page_id")) for p in CD.pages_of(deck)) or "—"
        raise ToolError(f"в copy deck нет страницы {page_id!r}; есть: {have}")
    out = []
    for s in CD.sections_of(page):
        for sl in CD.slots_of(s):
            texts = [norm(v.get("text")) for v in CD.variants_of(sl) if norm(v.get("text"))]
            ch = CD.chosen_variant(sl)
            if ch is not None and norm(ch.get("text")) in texts:
                texts.remove(norm(ch.get("text")))
                texts.insert(0, norm(ch.get("text")))
            out.append(RefSlot(str(s.get("section_id")), str(sl.get("slot_id")), sl.get("slot_type"), texts))
    return out


def ref_from_copy_md(text):
    sections, _notes = CD.parse_copy_md(text)
    out = []
    for sec in sections:
        for sl in sec.get("slots") or []:
            if sec.get("section_id") and sl.get("slot_id"):
                out.append(RefSlot(sec["section_id"], sl["slot_id"], None, [norm(sl.get("text"))]))
    return out


# ------------------------------------------------------------------ сопоставление

def tag_fits(stype, tag):
    allowed = SLOT_TAGS.get(stype or "")
    return True if allowed is None else tag in allowed


@functools.lru_cache(maxsize=None)
def asset_slot_types():
    """Типы слотов, чей текст на артборде текстом не стоит (alt, подпись картинки, текст в картинке): их не выгружает
    `copy.md` входа — список владельца, карта `copy_md.not_exported` схемы copy deck."""
    return frozenset(CD.copy_md_rules()["not_exported"])


def assign(units, ref):
    """Единицы → (секция, слот, способ): data-slot · текст · по месту · без слота."""
    plan_secs = []
    for r in ref:
        if r.section not in plan_secs:
            plan_secs.append(r.section)
    by_key = {(r.section, r.slot): r for r in ref}
    used, res = set(), [None] * len(units)
    for i, u in enumerate(units):                      # 1. разметка data-slot
        if u.slot and u.section and not u.template:
            res[i] = (u.section, u.slot, "разметка")
            used.add((u.section, u.slot))
    for i, u in enumerate(units):                      # 2. текст равен слоту: сначала своя секция
        if res[i] or u.template or not ref:
            continue
        t = norm(u.text)
        cands = [r for r in ref if t in r.texts and (r.section, r.slot) not in used
                 and r.stype not in asset_slot_types()]
        pick = next((r for r in cands if r.section == u.section), None) or (cands[0] if cands and not u.section else None)
        if pick is None and cands and u.section and u.section not in plan_secs:
            pick = cands[0]
        if pick:
            res[i] = (pick.section, pick.slot, "текст")
            used.add((pick.section, pick.slot))
    for i, u in enumerate(units):                      # 3. по месту в секции плана
        if res[i] or u.template or not u.section or u.section not in plan_secs:
            continue
        pick = next((r for r in ref if r.section == u.section and (r.section, r.slot) not in used
                     and r.stype not in asset_slot_types() and tag_fits(r.stype, u.tag)), None)
        if pick:
            res[i] = (pick.section, pick.slot, "по месту")
            used.add((pick.section, pick.slot))
    return [r if r else (u.section, None, "без слота") for u, r in zip(units, res)], plan_secs, by_key


def merge(per_board, ref):
    """Единицы нескольких артбордов → секции copy.md: [{section_id, label, slots: [{slot_id, label, text}]}], сводка."""
    sections, order, notes = {}, [], []
    stat = {"разметка": 0, "текст": 0, "по месту": 0, "без слота": 0, "расхождения": 0}
    plan_secs = []
    for units in per_board:
        assigned, ps, _ = assign(units, ref)
        plan_secs = ps or plan_secs
        for u, (sec, slot, how) in zip(units, assigned):
            key = sec or f"?{u.landmark}"
            if key not in sections:
                sections[key] = {"section_id": sec, "label": "" if sec else u.landmark, "slots": [], "seen": {}}
                order.append(key)
            s = sections[key]
            text = u.text
            if slot:
                if slot in s["seen"]:
                    if norm(s["seen"][slot]) != norm(text):
                        stat["расхождения"] += 1
                        s["slots"].append({"slot_id": None, "label": f"{slot} · {u.artboard}", "text": text})
                    continue
                s["seen"][slot] = text
                s["slots"].append({"slot_id": slot, "label": "", "text": text, "how": how, "tag": u.tag})
                stat[how] += 1
                if how == "по месту":
                    notes.append(f"по месту: {sec}/{slot} ← «{CD.norm_ws(text)[:50]}» ({u.tag}, {u.artboard})")
            else:
                dup = any(x.get("slot_id") is None and norm(x["text"]) == norm(text) for x in s["slots"])
                if not dup:
                    lab = ("шаблон " if u.template else "") + u.tag
                    s["slots"].append({"slot_id": None, "label": lab, "text": text})
                    stat["без слота"] += 1
    rank = {sid: i for i, sid in enumerate(plan_secs)}
    slot_rank = {(r.section, r.slot): i for i, r in enumerate(ref)}
    keys = sorted(order, key=lambda k: (k.startswith("?"), rank.get(k, len(rank)), order.index(k)))
    out = []
    for k in keys:
        s = sections[k]
        s["slots"].sort(key=lambda x: (x["slot_id"] is None, slot_rank.get((k, x["slot_id"]), 10 ** 6)))
        out.append({"section_id": s["section_id"], "label": s["label"],
                    "slots": [{kk: x[kk] for kk in ("slot_id", "label", "text")} for x in s["slots"]]})
    return out, stat, notes


def render(sections, notes, title):
    """copy.md: заголовок, комментарии о сопоставлении «по месту», секции через copydeck.render_copy_md."""
    head = [title, "Разбор исходников холста: тексты без статуса; [? …] — текст без секции или слота плана, решает агент."]
    body = CD.render_copy_md(sections, head)
    if notes:
        body = body.replace("\n\n", "\n" + "\n".join(f"# {n}" for n in notes) + "\n\n", 1)
    return body


def extract(files, ref=None, title=""):
    boards = [DC.load(p) for p in files]
    plan_secs = [r.section for r in ref or []]
    per = [units_of(ab, plan_secs) for ab in boards]
    sections, stat, notes = merge(per, ref or [])
    name = title or ", ".join(ab.name for ab in boards)
    return render(sections, notes, f"Тексты холста — {name}"), sections, stat, notes


# ------------------------------------------------------------------ команды

def output(a, text, sections, stat, notes, files):
    if getattr(a, "out", None):
        Path(a.out).write_text(text, encoding="utf-8")
    if a.json:
        print(json.dumps({"copy_md": text, "out": getattr(a, "out", None), "artboards": [Path(f).name for f in files],
                          "stat": stat, "notes": notes}, ensure_ascii=False, indent=1))
    elif not getattr(a, "out", None):
        sys.stdout.write(text)
    else:
        print(f"{a.out}: секций {len(sections)}; " + ", ".join(f"{k} {v}" for k, v in stat.items()))
    return 0


def cmd_show(call):
    a = call.args
    if not a.page:
        raise ToolError("нужна страница: --page <page-id>")
    src = docpaths.design(call.slug, "canvas-project", surface=call.surface, repo=call.repo)
    canvas = DC.load_canvas(src)
    want = [x.strip() for x in (a.artboards or "").split(",") if x.strip()]
    files = [src / w for w in want] if want else [p for p in DC.artboard_files(src, canvas)
                                                  if DC.stage_of((canvas or {}).get("boards", {}).get(p.name), canvas)
                                                  == "mockup"]
    miss = [docpaths.rel(p, call.repo) for p in files if not p.is_file()]
    if miss or not files:
        raise ToolError("нет артбордов: " + (", ".join(miss) or docpaths.rel(src, call.repo)))
    ref = []
    if call.surf and call.surf.page:
        deck = docpaths.site(call.slug, call.surface, "copy", f"{a.page}.yaml", repo=call.repo)
        if deck.is_file():
            ref = ref_from_deck(CD.open_deck(str(deck)), a.page)
    text, sections, stat, notes = extract(files, ref, f"{a.page} ({', '.join(p.name for p in files)})")
    a.json = call.json
    return output(a, text, sections, stat, notes, files)


def cmd_file(a):
    if a.deck and not a.page:
        raise ToolError("--deck требует --page <page-id>")
    ref = []
    if a.deck:
        ref = ref_from_deck(CD.open_deck(a.deck), a.page)
    elif a.copy:
        ref = ref_from_copy_md(Path(a.copy).read_text(encoding="utf-8"))
    files = [Path(f) for f in a.artboards]
    for f in files:
        if not f.is_file():
            raise ToolError(f"нет артборда: {f}")
    text, sections, stat, notes = extract(files, ref, (a.page + " — " if a.page else "") + ", ".join(f.name for f in files))
    return output(a, text, sections, stat, notes, files)


# ------------------------------------------------------------------ самопроверка

EL_OF = {"headline": "h1", "article-title": "h1", "section-title": "h2", "form-title": "h2", "card-title": "h3",
         "step-title": "h3", "faq-q": "h3", "case-title": "h3", "cta-label": "a", "cta-secondary-label": "a",
         "eyebrow": "span", "list-item": "li", "testimonial-quote": "blockquote", "testimonial-attribution": "cite"}


def artboard_from(deck_data, page_id, stage="mockup", edit=None, extra=None, marks=False):
    """Синтетический артборд из выгрузки copy deck: секция на секцию плана, элемент на слот по типу."""
    deck = CD.deck_root(deck_data)
    page = next(p for p in CD.pages_of(deck) if str(p.get("page_id")) == page_id)
    copy_md, _rows, _gaps = CD.export_copy_md(deck, page, stage)
    types = {(str(s.get("section_id")), str(sl.get("slot_id"))): sl.get("slot_type")
             for s in CD.sections_of(page) for sl in CD.slots_of(s)}
    secs, _n = CD.parse_copy_md(copy_md)
    parts = []
    for sec in secs:
        sid = sec["section_id"]
        inner = []
        for sl in sec["slots"]:
            tag = EL_OF.get(types.get((sid, sl["slot_id"])), "p")
            text = (edit or {}).get((sid, sl["slot_id"]), sl["text"])
            attr = f' data-slot="{sl["slot_id"]}"' if marks else ""
            body = html.escape(text, quote=False).replace("\n", "<br>")
            inner.append(f'<ul><li{attr}>{body}</li></ul>' if tag == "li" else f"<{tag}{attr}>{body}</{tag}>")
        if extra and sid == extra[0]:
            inner.append(f"<p>{html.escape(extra[1], quote=False)}</p>")
        parts.append(f'<section id="{sid}" style="padding: 24px;">\n    ' + "\n    ".join(inner) + "\n  </section>")
    return ('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n<script src="./support.js"></script>\n'
            '</head>\n<body>\n<x-dc>\n<helmet><style>body{margin:0}</style></helmet>\n<div style="width: 1440px; '
            'height: 4000px;">\n  ' + "\n  ".join(parts) + '\n</div>\n</x-dc>\n<script type="text/x-dc" data-dc-script '
            'data-props=\'{"$preview":{"width":1440,"height":4000}}\'>\nclass Component extends DCLogic { renderVals() '
            '{ return {}; } }\n</script>\n</body>\n</html>\n'), copy_md


def selftest():
    import tempfile
    ok = True

    def check(name, got, want=True):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"{'OK  ' if good else 'FAIL'} {name}" + ("" if good else f": {got!r} (ожидалось {want!r})"))

    deck_path = kbpaths.kb("text", "10-templates-recipes", "examples", "ru-otves-lead.yaml")
    data = CD.open_deck(str(deck_path))
    page = "otves-product-aware"
    # пример базы — черновик агента (assumed), а макет берёт утверждённые тексты: в памяти тексты страницы утверждены
    for v in (v for p in CD.pages_of(CD.deck_root(data)) for s in CD.sections_of(p) for sl in CD.slots_of(s)
              for v in CD.variants_of(sl)):
        if v.get("status") in ("assumed", "checked"):
            v["status"] = "approved"
    ref = ref_from_deck(data, page)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ab_text, export = artboard_from(data, page)
        (td / "Home.dc.html").write_text(ab_text, encoding="utf-8")
        text, sections, stat, notes = extract([td / "Home.dc.html"], ref, page)
        secs, pnotes = CD.parse_copy_md(text)
        check("разбор: copy.md читается без заметок формата", pnotes, [])
        n_export = sum(len(s["slots"]) for s in CD.parse_copy_md(export)[0])
        check("круг: все слоты выгрузки нашли место по тексту", (stat["текст"], stat["без слота"], stat["по месту"]),
              (n_export, 0, 0))
        out, rep, summ = CD.import_copy(data, text, page)
        fmt_notes = [f for f in rep.findings if f["rule"] == "COPY-D-IMPORT" and f["level"] != "info"]
        check("круг: import-copy без находок формата и без изменений", (len(fmt_notes), len(summ["changed"]),
                                                                          summ["unmapped"], summ["same"]),
              (0, 0, 0, n_export))
        edited = "Ремонт квартир под ключ — с 2014 года в Нижнем"
        ab2, _ = artboard_from(data, page, edit={("hero", "h1"): edited},
                               extra=("guarantee", "Гарантийный отдел отвечает в течение дня"))
        (td / "Home.dc.html").write_text(ab2, encoding="utf-8")
        text2, _s, stat2, notes2 = extract([td / "Home.dc.html"], ref, page)
        check("правка заголовка — по месту в слот h1", any("hero/h1" in n for n in notes2), True)
        check("новый абзац без слота — [? p] в секции guarantee",
              "## guarantee" in text2 and "[? p]: Гарантийный отдел отвечает в течение дня" in text2, True)
        out2, rep2, summ2 = CD.import_copy(data, text2, page)
        check("приём правки: один изменённый слот, один текст без слота",
              ([c["path"] for c in summ2["changed"]], summ2["unmapped"]), ([f"{page}/hero/h1"], 1))
        new = next(v for s in CD.sections_of(CD.pages_of(CD.deck_root(out2))[0]) if s.get("section_id") == "hero"
                   for sl in CD.slots_of(s) if sl.get("slot_id") == "h1" for v in CD.variants_of(sl)
                   if v.get("source") == "customer")
        check("приём: вариант source: customer в статусе draft", (new.get("text"), new.get("status")), (edited, "draft"))
        ab3, _ = artboard_from(data, page, marks=True, edit={("case", "title"): "Совсем другой заголовок кейса"})
        (td / "Home.dc.html").write_text(ab3, encoding="utf-8")
        _t3, _s3, stat3, _n3 = extract([td / "Home.dc.html"], ref, page)
        check("разметка data-slot — место без сопоставления текстом", stat3["разметка"], n_export)
        phone = ab_text.replace("Позвать замерщика", "Позвать замерщика сейчас", 1)
        (td / "Home.dc.html").write_text(ab_text, encoding="utf-8")
        (td / "Home-Phone.dc.html").write_text(phone, encoding="utf-8")
        t4, _s4, stat4, _n4 = extract([td / "Home.dc.html", td / "Home-Phone.dc.html"], ref, page)
        check("два артборда: расхождение текста слота — строка [? cta · Home-Phone.dc.html]",
              ("[? cta · Home-Phone.dc.html]: Позвать замерщика сейчас" in t4, stat4["расхождения"]), (True, 1))
        refc = ref_from_copy_md(export)
        _t5, _s5, stat5, _n5 = extract([td / "Home.dc.html"], refc, page)
        check("план из copy.md входа — те же места", stat5["текст"], n_export)
        # служебная пометка артборда — ярлык роли секции — и свободный слот alt той же секции: пометка не текст, слот
        # alt не место
        import copy as _copy
        data_alt = _copy.deepcopy(data)
        hero = next(s for s in CD.sections_of(CD.pages_of(CD.deck_root(data_alt))[0]) if s.get("section_id") == "hero")
        hero["slots"].append({"slot_id": "alt-hero", "slot_type": "image-alt", "asset_ref": "hero", "chosen": "a",
                              "variants": [{"id": "a", "text": "Прораб с рулеткой в пустой комнате", "status": "draft"}]})
        ref_alt = ref_from_deck(data_alt, page)
        check("слот alt есть в плане страницы", [r.slot for r in ref_alt if r.stype in asset_slot_types()], ["alt-hero"])
        label = '<div data-wf="role">Первый экран · hero — кадр во всю ширину</div>'
        tagged = ab_text.replace('<section id="hero" style="padding: 24px;">',
                                 '<section id="hero" style="padding: 24px;">' + label, 1)
        check("артборд несёт служебную пометку — ярлык роли секции", label in tagged)
        (td / "Home.dc.html").write_text(tagged, encoding="utf-8")
        t8, _s8, stat8, _n8 = extract([td / "Home.dc.html"], ref_alt, page)
        check("служебная пометка data-wf — не единица текста: слот alt не занят, строки пометки в copy.md нет",
              (stat8["по месту"], stat8["без слота"], stat8["текст"], "Первый экран" in t8), (0, 0, n_export, False))
        inline = ab_text.replace("</h1>", '<span data-wf="role">H1 · headline</span></h1>', 1)
        (td / "Home.dc.html").write_text(inline, encoding="utf-8")
        t8i, _s8i, stat8i, _n8i = extract([td / "Home.dc.html"], ref_alt, page)
        check("служебная пометка data-wf внутри текстового элемента в его текст не входит",
              (stat8i["текст"], stat8i["по месту"], stat8i["без слота"], "headline" in t8i), (n_export, 0, 0, False))
        ab9, _ = artboard_from(data_alt, page, extra=("hero", "Выезд замерщика в день обращения"))
        (td / "Home.dc.html").write_text(ab9, encoding="utf-8")
        t9, _s9, stat9, n9 = extract([td / "Home.dc.html"], ref_alt, page)
        check("новый абзац секции со свободным слотом alt — [? p], а не «по месту» в alt",
              (stat9["по месту"], "[? p]: Выезд замерщика в день обращения" in t9, any("alt-hero" in n for n in n9)),
              (0, True, False))
    spica = DC.EXAMPLE / "canvas" / "project"
    t6, s6, stat6, _n6 = extract([spica / "Main.dc.html"])
    ids = [s["section_id"] for s in s6]
    check("пример «Спицы» без плана: секции из id разметки", [i for i in ids if i], ["services", "how", "contacts"])
    check("пример без плана: текст героя — [? h1] в «## ? Первый экран»",
          "## ? Первый экран" in t6 and "[? h1]: Обслужим велосипед за один день" in t6, True)
    check("пример без плана: copy.md читается без заметок", CD.parse_copy_md(t6)[1], [])
    t7, _s7, _st7, _n7 = extract([spica / "Booking.dc.html"])
    check("обе ветки sc-if и подсказки полей читаются", ("[? h1]: Заявка отправлена" in t7,
                                                          "[? placeholder]: Например, шоссейный, 2019 год" in t7), (True, True))
    check("текст с дыркой — строка шаблона", "[? шаблон p]: Услуга: {{ service }}." in t7, True)
    print("selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


# ------------------------------------------------------------------ вызов

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv[:1] == ["file"]:
            ap = argparse.ArgumentParser(prog="dc_texts.py file", description="Тексты артбордов вне проекта → copy.md.")
            ap.add_argument("cmd")
            ap.add_argument("artboards", nargs="+", help="артборды .dc.html одной страницы (десктоп, телефон …)")
            ap.add_argument("--deck", help="copy deck страницы (YAML или JSON)")
            ap.add_argument("--page", help="id страницы в copy deck")
            ap.add_argument("--copy", help="copy.md входа холста вместо copy deck")
            ap.add_argument("--out", help="файл copy.md (по умолчанию — stdout)")
            ap.add_argument("--json", action="store_true")
            return cmd_file(ap.parse_args(argv))
        ap = docpaths.parser("dc_texts.py", __doc__, commands=("show",), surface="required", accept=lambda s: s.design)
        ap.add_argument("--page", help="id страницы плана (copy deck site/<surface>/copy/<page-id>.yaml)")
        ap.add_argument("--artboards", help="артборды страницы через запятую (по умолчанию — все артборды макета)")
        call = docpaths.parse(ap, argv)
        if call.selftest:
            return selftest()
        return cmd_show(call)
    except (ToolError, DC.ToolError) as e:
        print(f"dc_texts: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
