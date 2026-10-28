#!/usr/bin/env python3
"""literal_tokens — «литерал ∈ значений токенов ДС»: облик артбордов холста против токенов продукта.

На артбордах типа Design значения облика — литералы, и каждый литерал берётся из токенов ДС (так требует тип, а свой
цвет или отступ на артборде — облик вне системы; `references/claude-design.md § Приёмка`, пункт C2; правило R-VIS-004
`design-audit`). Все ширины приёмки — артборды холста, поэтому сверка артбордов покрывает макет целиком; утилита
читает исходники холста без браузера:
  - литералы — инлайн-стили и `<style>` артборда, цветовые атрибуты SVG (`fill`, `stroke`, `stop-color`, `color`),
    умолчания цветовых твиков `data-props`; дырки `{{…}}` получают значения `renderVals()` на умолчаниях твиков (как в
    статичной копии, `dc_to_html.py`). Образцы твика (`options`) — варианты на выбор заказчика, а не облик артборда:
    не сверяются;
  - семейства: цвет; кегль, интерлиньяж, насыщенность, гарнитура, разрядка; отступы (padding, margin, gap); радиусы;
    толщина границы; тени; длительности. Размеры элементов (width, height, min-, max-) и рамка артборда — раскладка, а
    не облик: не сверяются (раскладку артборда заказчик правит как есть, `references/claude-design.md § Правки
    заказчика`); относительные единицы (%, em, ch, vw, fr) и ключевые слова (auto, none, inherit, transparent,
    currentColor) — не литералы облика;
  - значения ДС — из токенов: `system.tokens.css` (сборка `ds_build.py`), DTCG `system.tokens.json` (через сборку CSS
    `ds_build`), `tokens.json` артефакта Design System (списки по семействам, значения по темам); семейство токена —
    по имени (`space`, `radius`, `size`, `font-size`/`fs-`, `leading`/`lh-`, `weight`/`fw-`, `family`/`font-`,
    `shadow`/`elevation`, `duration`, `border-w`) и по семейству артефакта; у цвета — любой цветовой токен любой темы.
    Семейства, которого в ДС нет, утилита не сверяет и говорит об этом заметкой: требовать значение токена, которого
    нет, — пробел ДС, а не литерал;
  - что считается значением токена:
      резиновый токен `clamp(мин, …, макс)` — любое значение в его границах: артборд фиксированной ширины несёт
        значение токена на своей ширине;
      интерлиньяж — отношением: литерал в px рядом с кеглем того же блока сверяется и как отношение к кеглю, а
        безразмерный — и как px (ДС называет интерлиньяж то отношением, то px); шаг округления `round(…, 1px)` —
        арифметика, а не литерал;
      длительности — времена всех токенов движения: простых (`duration`, `delay`, `stagger`) и составных переходов
        (`200ms cubic-bezier(…) 50ms` — оба времени);
      цвета слоёв — остановки токенов-градиентов (вуали, блики) — цвета ДС, как и цвета теней; полностью прозрачный
        цвет с цветом токена — конец растворения слоя, а не свой цвет;
  - одна страница холста на нескольких ширинах (`<Имя>-<ширина>`, части `<Имя>-<ширина>-<N>`) даёт одну находку на
    литерал с перечнем ширин: места складываются, строки — первого артборда, где литерал встретился;
  - сверяются артборды страниц холста этапа макета («Макет и прототип», «Состояния»); артборды страницы «Направления»
    — до ДС, их берёт ключ --all-stages.
Находка — литерал со счётом мест, ширинами и строками исходника и ближайшее значение токена (цвет — по OKLab);
решение по литералу — уровень правки (элемент, компонент, токен) решает заказчик (`references/claude-design.md §
Правки токенов`).

Команды (файлы проекта — через lib/docpaths.py):
  literal_tokens.py check <slug> <surface> [--repo DIR] [--accepted] [--all-stages] [--json]
      исходники design/<surface>/canvas/project/ против токенов продукта (system.tokens.css, иначе system.tokens.json,
      иначе tokens.json артефакта; плюс копия ДС, установленная в холст, `canvas/project/ds/*/tokens.json`).
      Тяжесть — warning и у принятого макета: литерал вне токенов — пункт C2 приёмки (S), его исправляют или
      принимают с записью; --accepted (макет принят) ведёт совет к записи в REVIEW.md. Ничего не пишет.
  literal_tokens.py scan <файл.dc.html | папка project> … --tokens ФАЙЛ [--tokens ФАЙЛ …] [--all-stages] [--json]
      то же вне проекта (пример базы, снимок живой версии).
  literal_tokens.py tokens ФАЙЛ … [--json]      значения токенов по семействам, границы резиновых токенов, темы
                                                (первая — `color-scheme` блока `:root`) и брейкпоинты — для разбора
  literal_tokens.py --selftest                  самопроверка на примере базы claude-design и фикстурах, без сети
Находки — строки JSON {rule, severity, surface, kind, ref, path, message, fix} (контракт утилит project/). Коды выхода:
0 — ошибок нет; 1 — есть находки error; 2 — ошибка вызова или окружения.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import math
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

kbpaths.use("project")
import findings as FND  # noqa: E402

RULE = "R-VIS-004"
FAMILIES = ("color", "font-size", "line-height", "weight", "family", "letter-spacing", "spacing", "radius", "border",
            "shadow", "duration")
FAMILY_RU = {"color": "цвет", "font-size": "кегль", "line-height": "интерлиньяж", "weight": "насыщенность",
             "family": "гарнитура", "letter-spacing": "разрядка", "spacing": "отступ", "radius": "радиус",
             "border": "толщина границы", "shadow": "тень", "duration": "длительность"}
SIZE_PROPS = ("width", "height", "min-width", "min-height", "max-width", "max-height", "inline-size", "block-size")
# семейство токена по имени: первое совпадение по порядку (кегль раньше размера, толщина границы раньше цвета)
TOKEN_CATS = (
    ("breakpoint", re.compile(r"(^|-)(bp|breakpoint)(-|$)")),
    ("duration", re.compile(r"duration|(^|-)dur(-|$)|delay")),
    ("easing", re.compile(r"easing|(^|-)ease(-|$)|bezier")),
    ("shadow", re.compile(r"shadow|elevation")),
    ("radius", re.compile(r"radius|corner|rounded")),
    ("line-height", re.compile(r"line-height|leading|(^|-)lh(-|$)")),
    ("weight", re.compile(r"weight|(^|-)fw(-|$)")),
    ("letter-spacing", re.compile(r"tracking|letter")),
    ("font-size", re.compile(r"font-size|(^|-)fs(-|$)|^type-.+-size$|typescale")),
    ("family", re.compile(r"family|(^|-)font(-|$)")),
    ("border", re.compile(r"border-w|border-width|stroke-w")),
    ("spacing", re.compile(r"space|spacing|gap|gutter|inset|padding|margin")),
    ("size", re.compile(r"size|control|height|width|(^|-)(max|min)(-|$)|panel|row")),
)
KEYWORDS = {"auto", "none", "inherit", "initial", "unset", "revert", "transparent", "currentcolor", "normal", "0",
            "0px", "100%", "fit-content", "min-content", "max-content"}
NAMED = {"white": "#ffffff", "black": "#000000", "red": "#ff0000", "green": "#008000", "blue": "#0000ff",
         "gray": "#808080", "grey": "#808080", "silver": "#c0c0c0", "yellow": "#ffff00", "orange": "#ffa500"}
COLOR_RX = re.compile(r"#[0-9a-fA-F]{3,8}\b|(?:rgba?|hsla?|oklch)\([^()]*\)", re.I)
LEN_RX = re.compile(r"(?<![\w.#-])(-?\d*\.?\d+)(px|rem)\b", re.I)
NUM_RX = re.compile(r"^-?\d*\.?\d+$")
DUR_RX = re.compile(r"(?<![\w.])(\d*\.?\d+)(ms|s)\b")
CLAMP_RX = re.compile(r"clamp\(\s*([^,()]+),(.*),\s*([^,()]+)\)", re.I | re.S)
ROUND_RX = re.compile(r"(?<![\w-])round\(", re.I)
MOTION_NAME_RX = re.compile(r"motion|transition|anim|duration|delay|stagger")
LENGTH_CATS = ("font-size", "line-height", "letter-spacing", "spacing", "radius", "border", "size")
SVG_COLOR_ATTRS = ("fill", "stroke", "stop-color", "color", "flood-color", "lighting-color")
COLOR_PROPS = {"color", "background-color", "border-color", "outline-color", "fill", "stroke", "stop-color",
               "caret-color", "accent-color", "text-decoration-color", "column-rule-color", "flood-color"}


class ToolError(RuntimeError):
    """Ошибка вызова или окружения — код выхода 2."""


# ------------------------------------------------------------------ цвет

def _clamp(x):
    return max(0.0, min(1.0, x))


def _pct(s, scale=1.0):
    s = s.strip()
    return float(s[:-1]) / 100.0 * scale if s.endswith("%") else float(s)


def _oklch_to_rgb(L, C, H):
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l_, m_, s_ = L + 0.3963377774 * a + 0.2158037573 * b, L - 0.1055613458 * a - 0.0638541728 * b, \
        L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    lin = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    return tuple(_clamp(1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c) for c in lin)


def norm_color(s):
    """Цвет → '#rrggbb' или '#rrggbbaa' (строчными); не цвет — None."""
    s = (s or "").strip().lower()
    if s in NAMED:
        return NAMED[s]
    m = re.fullmatch(r"#([0-9a-f]{3,8})", s)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        return "#" + (h[:6] if h[6:] in ("", "ff") else h)
    m = re.fullmatch(r"(rgba?|hsla?|oklch)\((.*)\)", s)
    if not m:
        return None
    fn, body = m.group(1), m.group(2)
    parts = [p for p in re.split(r"[\s,/]+", body.strip()) if p]
    try:
        if fn.startswith("rgb") and len(parts) >= 3:
            rgb = [_pct(p, 255.0) / 255.0 if p.endswith("%") else float(p) / 255.0 for p in parts[:3]]
        elif fn.startswith("hsl") and len(parts) >= 3:
            h = float(parts[0].replace("deg", "")) / 360.0
            rgb = list(colorsys.hls_to_rgb(h % 1.0, _pct(parts[2]), _pct(parts[1])))
        elif fn == "oklch" and len(parts) >= 3:
            rgb = list(_oklch_to_rgb(_pct(parts[0]), float(parts[1]), float(parts[2].replace("deg", ""))))
        else:
            return None
        alpha = _pct(parts[3]) if len(parts) > 3 else 1.0
    except ValueError:
        return None
    out = "#" + "".join("%02x" % round(_clamp(c) * 255) for c in rgb)
    return out if alpha >= 0.999 else out + "%02x" % round(_clamp(alpha) * 255)


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def oklab(hexs):
    r, g, b = (_lin(int(hexs[i:i + 2], 16) / 255.0) for i in (1, 3, 5))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


# ------------------------------------------------------------------ значения

def px(value):
    """'24px' / '1.5rem' → 24.0 / 24.0; иначе None."""
    m = re.fullmatch(r"(-?\d*\.?\d+)(px|rem)", (value or "").strip().lower())
    if not m:
        return None
    return round(float(m.group(1)) * (16.0 if m.group(2) == "rem" else 1.0), 2)


def clamp_bounds(value):
    """Границы резинового значения `clamp(мин, …, макс)` в px → (мин, макс); не clamp или границы не длины — None."""
    m = CLAMP_RX.fullmatch((value or "").strip())
    if not m:
        return None
    lo, hi = px(m.group(1)), px(m.group(3))
    return None if lo is None or hi is None else (min(lo, hi), max(lo, hi))


def drop_round_step(v):
    """Значение без шага округления: `round(nearest, X, 1px)` → `round(nearest, X)`. Шаг — сетка пикселей, к которой
    приводится значение токена, а не литерал облика."""
    out, pos = [], 0
    for m in ROUND_RX.finditer(v):
        if m.start() < pos:
            continue
        depth, k, last = 1, m.end(), None
        while k < len(v) and depth:
            ch = v[k]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 1:
                last = k
            k += 1
        if depth or last is None or px(v[last + 1:k - 1]) is None:
            continue
        out += [v[pos:last], ")"]
        pos = k
    out.append(v[pos:])
    return "".join(out)


def ms(value):
    m = re.fullmatch(r"(\d*\.?\d+)(ms|s)", (value or "").strip().lower())
    return None if not m else round(float(m.group(1)) * (1000.0 if m.group(2) == "s" else 1.0), 2)


def first_family(stack):
    return (stack or "").split(",")[0].strip().strip("\"'").strip().lower()


def weight_of(v):
    v = (v or "").strip().lower()
    return {"normal": 400.0, "bold": 700.0}.get(v, float(v) if NUM_RX.match(v) else None)


def norm_shadow(v):
    s = COLOR_RX.sub(lambda m: norm_color(m.group(0)) or m.group(0), (v or "").strip().lower())
    return re.sub(r"\s+", " ", re.sub(r"\s*,\s*", ", ", s))


def fmt(x):
    return ("%g" % x) if isinstance(x, float) else str(x)


# ------------------------------------------------------------------ токены ДС

@dataclass
class TokenSet:
    colors: dict = field(default_factory=dict)         # '#rrggbb' → [имена]
    lengths: dict = field(default_factory=dict)        # семейство → {px: [имена]}
    ranges: dict = field(default_factory=dict)         # семейство → [(от px, до px, имя)] — границы токенов clamp()
    numbers: dict = field(default_factory=dict)        # line-height, weight → {число: [имена]}
    families: dict = field(default_factory=dict)       # первая гарнитура → [имена]
    shadows: dict = field(default_factory=dict)
    durations: dict = field(default_factory=dict)
    names: set = field(default_factory=set)            # имена CSS-переменных токенов
    themes: list = field(default_factory=list)
    breakpoints: list = field(default_factory=list)
    sources: list = field(default_factory=list)

    def put(self, bucket, key, name, cat=None):
        d = getattr(self, bucket)
        if cat is not None:
            d = d.setdefault(cat, {})
        d.setdefault(key, [])
        if name not in d[key]:
            d[key].append(name)

    def has(self, fam):
        if fam == "color":
            return bool(self.colors)
        if fam == "family":
            return bool(self.families)
        if fam == "shadow":
            return bool(self.shadows)
        if fam == "duration":
            return bool(self.durations)
        if fam in ("weight",):
            return bool(self.numbers.get("weight"))
        if fam == "line-height":
            return bool(self.numbers.get("line-height") or self.lengths.get("line-height")
                        or self.ranges.get("line-height"))
        return bool(self.lengths.get(fam) or self.ranges.get(fam))

    def in_range(self, fam, value):
        """Имя резинового токена семейства, в границы которого попадает значение; нет — None."""
        if not isinstance(value, (int, float)):
            return None
        return next((name for lo, hi, name in self.ranges.get(fam, ()) if lo <= value <= hi), None)


def token_cat(name):
    n = (name or "").lower().lstrip("-")
    for cat, rx in TOKEN_CATS:
        if rx.search(n):
            return cat
    return None


def add_value(ts, name, value, cat=None):
    """Значение токена по его виду: цвет, длина, число, длительность, тень, гарнитура."""
    v = (value or "").strip() if isinstance(value, str) else value
    cat = cat or token_cat(name)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if cat in ("line-height", "weight"):
            ts.put("numbers", round(float(v), 4), name, cat)
        elif cat in ("font-size", "spacing", "radius", "size", "border", "letter-spacing"):
            ts.put("lengths", round(float(v), 2), name, cat)
        return
    if not isinstance(v, str) or not v:
        return
    c = norm_color(v)
    if c:
        ts.put("colors", c, name)
        return
    if "gradient(" in v.lower():                         # остановки градиента-токена — цвета ДС
        for m in COLOR_RX.finditer(v):
            cc = norm_color(m.group(0))
            if cc:
                ts.put("colors", cc, name)
        return
    rng = clamp_bounds(v)
    if rng:
        if cat in LENGTH_CATS and rng + (name,) not in ts.ranges.setdefault(cat, []):
            ts.ranges[cat].append(rng + (name,))
        return
    if cat == "breakpoint":
        p = px(v)
        if p is not None and p not in ts.breakpoints:
            ts.breakpoints.append(p)
        return
    d = ms(v)
    if d is not None and cat in ("duration", None):
        ts.put("durations", d, name)
        return
    if cat in ("duration", None) and MOTION_NAME_RX.search(str(name).lower()):
        times = [ms(m.group(0)) for m in DUR_RX.finditer(v.lower())]     # составной переход: длительность и задержка
        if times:
            for t in times:
                ts.put("durations", t, name)
            return
    if cat == "shadow":
        ts.put("shadows", norm_shadow(v), name)
        for m in COLOR_RX.finditer(v):
            cc = norm_color(m.group(0))
            if cc:
                ts.put("colors", cc, name)
        return
    if cat == "family" or ("," in v and not re.search(r"\d", v.split(",")[0])):
        ts.put("families", first_family(v), name)
        return
    p = px(v)
    if p is not None and cat:
        ts.put("lengths", p, name, cat)
        return
    if NUM_RX.match(v) and cat in ("line-height", "weight"):
        ts.put("numbers", round(float(v), 4), name, cat)


def load_css_tokens(text, ts, source):
    """CSS-переменные всех блоков (темы, плотность, узкая ширина): значения, имена, темы, брейкпоинты. Ссылка
    `var(--x, запас)` — значение `--x` этого файла, а переменной, которую файл не объявляет (переменная семейства
    шрифта производного CSS), — значение в запасе."""
    decl = re.findall(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;{}]+);", text)
    raw = {}
    for name, val in decl:
        raw.setdefault(name, val.strip())
    for name, val in decl:
        v = val.strip()
        for _ in range(8):                               # var(--x) → значение x, иначе запасное
            m = re.search(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,([^()]*))?\)", v)
            sub = raw.get(m.group(1), m.group(2)) if m else None
            if sub is None:
                break
            v = v[:m.start()] + sub.strip() + v[m.end():]
        ts.names.add(name)
        add_value(ts, name[2:], v)
    first = css_first_theme(text)
    _theme(ts, first)
    for t in ("light", "dark"):
        if t != first and re.search(r"data-theme=[\"']?%s|prefers-color-scheme:\s*%s" % (t, t), text):
            _theme(ts, t)
    ts.sources.append(source)


def css_first_theme(text):
    """Тема блока `:root` — первое слово его `color-scheme` (`dark` у продукта с одной тёмной темой); свойства нет —
    `light`."""
    for block in re.findall(r":root\s*\{([^{}]*)\}", text):
        m = re.search(r"(?<![\w-])color-scheme\s*:\s*([^;{}]+)", block)
        if m:
            words = m.group(1).lower().split()
            return "dark" if words[:1] == ["dark"] else "light"
    return "light"


def _theme(ts, t):
    if t not in ts.themes:
        ts.themes.append(t)


def load_artifact_tokens(data, ts, source):
    """tokens.json артефакта Design System: списки {name, value} по семействам, цвет по темам, стили текста."""
    by_name = {}
    for fam, block in data.items():
        if isinstance(block, dict) and isinstance(block.get("tokens"), list):
            for t in block["tokens"]:
                if isinstance(t, dict) and t.get("name"):
                    by_name[t["name"]] = t.get("value")

    def resolve(v, theme=None, depth=0):
        if isinstance(v, dict):
            v = v.get(theme) if theme in v else next(iter(v.values()), None)
        if isinstance(v, str) and re.fullmatch(r"\{[^{}]+\}", v.strip()) and depth < 8:
            return resolve(by_name.get(v.strip()[1:-1]), theme, depth + 1)
        return v

    color = data.get("color") if isinstance(data.get("color"), dict) else {}
    themes = [str(t.get("id")) for t in color.get("themes") or [] if isinstance(t, dict) and t.get("id")]
    for t in themes or ["light"]:
        _theme(ts, t)
    fam_cat = {"spacing": "spacing", "radius": "radius", "shadow": "shadow"}     # прочие семейства — по имени токена
    for fam, block in data.items():
        if not isinstance(block, dict) or not isinstance(block.get("tokens"), list):
            continue
        for t in block["tokens"]:
            if not isinstance(t, dict) or not t.get("name"):
                continue
            name, value = t["name"], t.get("value")
            ts.names.add("--" + name)
            cat = fam_cat.get(fam) or token_cat(name)
            if isinstance(value, dict):
                for th in value:
                    add_value(ts, name, resolve(value, th), cat)
            else:
                add_value(ts, name, resolve(value), cat)
    typ = data.get("type") if isinstance(data.get("type"), dict) else {}
    for key, stack in (typ.get("families") or {}).items():
        ts.names.add(f"--font-{key}")
        ts.put("families", first_family(str(stack)), f"font-{key}")
    for grp in typ.get("groups") or []:
        for st in (grp or {}).get("styles") or []:
            nm = str(st.get("name") or "style")
            if st.get("fontSize") is not None:
                add_value(ts, nm, str(st["fontSize"]) if isinstance(st["fontSize"], str) else st["fontSize"], "font-size")
            if st.get("lineHeight") is not None:
                lh = st["lineHeight"]
                if isinstance(lh, str) and px(lh) is not None:
                    ts.put("lengths", px(lh), nm, "line-height")
                else:
                    add_value(ts, nm, float(lh) if not isinstance(lh, str) else lh, "line-height")
            if st.get("fontWeight") is not None:
                add_value(ts, nm, float(st["fontWeight"]) if not isinstance(st["fontWeight"], str) else st["fontWeight"],
                          "weight")
            if st.get("letterSpacing") is not None:
                add_value(ts, nm, st["letterSpacing"], "letter-spacing")
    ts.sources.append(source)


def is_dtcg(data):
    def walk(x, depth=0):
        if isinstance(x, dict):
            if "$value" in x:
                return True
            return depth < 6 and any(walk(v, depth + 1) for k, v in x.items() if not str(k).startswith("$"))
        return False
    return walk(data)


def load_tokens(paths):
    """Токены ДС из файлов: .css — переменные; .json — DTCG (через сборку CSS ds_build) или tokens.json артефакта."""
    ts = TokenSet()
    for p in paths:
        p = Path(p)
        if not p.is_file():
            raise ToolError(f"нет файла токенов: {p}")
        text = p.read_text(encoding="utf-8")
        if p.suffix.lower() == ".css":
            load_css_tokens(text, ts, str(p))
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ToolError(f"{p}: не JSON ({e})") from e
        if isinstance(data, dict) and is_dtcg(data):
            import ds_build
            load_css_tokens(ds_build.build_css(ds_build.Tokens(data)), ts, str(p))
        elif isinstance(data, dict):
            load_artifact_tokens(data, ts, str(p))
        else:
            raise ToolError(f"{p}: не токены ДС (ожидается DTCG, tokens.json артефакта или CSS)")
    ts.breakpoints.sort()
    return ts


# ------------------------------------------------------------------ литералы

@dataclass
class Literal:
    family: str
    raw: str
    key: object                                        # нормализованное значение
    line: int
    prop: str
    where: str = "style"                               # style · attr · tweak · css
    alt: object = None                                 # интерлиньяж другой записью: px ↔ отношение к кеглю блока


def declarations(style):
    """'a: b; c: d' → [(свойство, значение)]; точка с запятой внутри скобок и кавычек не делит."""
    out, buf, depth, q = [], "", 0, None
    for ch in (style or "") + ";":
        if q:
            buf += ch
            q = None if ch == q else q
            continue
        if ch in "\"'":
            q = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            if ":" in buf:
                k, v = buf.split(":", 1)
                if k.strip():
                    out.append((k.strip().lower(), v.strip()))
            buf = ""
            continue
        buf += ch
    return out


def css_rules(text):
    """Объявления блоков CSS (без @-правил с вложенностью глубже одного уровня): [(свойство, значение, смещение)]."""
    out = []
    for m in re.finditer(r"\{([^{}]*)\}", text or ""):
        for k, v in declarations(m.group(1)):
            out.append((k, v, m.start(1)))
    return out


def lengths_in(v):
    return [(m.group(0), round(float(m.group(1)) * (16.0 if m.group(2).lower() == "rem" else 1.0), 2))
            for m in LEN_RX.finditer(v)]


def literals_of(prop, value, line, where="style"):
    """Литералы облика в одном объявлении CSS."""
    v = drop_round_step(value.strip())
    low = v.lower()
    if not v or low in KEYWORDS or "var(" in low and not COLOR_RX.search(v) and not LEN_RX.search(v):
        return []
    out = []

    def colors(s):
        for m in COLOR_RX.finditer(s):
            c = norm_color(m.group(0))
            if c:
                out.append(Literal("color", m.group(0), c, line, prop, where))
        for w in re.findall(r"(?<![\w#-])([a-z]+)(?![\w(-])", s.lower()):
            if w in NAMED and prop in COLOR_PROPS | {"background", "border", "outline"}:
                out.append(Literal("color", w, NAMED[w], line, prop, where))

    def lens(s, fam):
        for raw, p in lengths_in(s):
            if p != 0:
                out.append(Literal(fam, raw, p, line, prop, where))

    base = prop.split("-")[0]
    if prop in COLOR_PROPS:
        colors(v)
    elif prop in ("background", "background-image"):
        colors(re.sub(r"url\([^)]*\)", "", v))
    elif prop in ("box-shadow", "text-shadow"):
        out.append(Literal("shadow", v, norm_shadow(v), line, prop, where))
        colors(v)
    elif base in ("border", "outline") and "radius" not in prop:
        colors(v)
        if not prop.endswith("-color") and not prop.endswith("-style"):
            lens(COLOR_RX.sub(" ", v), "border")
    elif "radius" in prop:
        lens(v, "radius")
    elif base in ("padding", "margin") or prop in ("gap", "row-gap", "column-gap", "grid-gap", "grid-row-gap",
                                                     "grid-column-gap"):
        lens(v, "spacing")
    elif prop in SIZE_PROPS:
        pass                                           # размер элемента — раскладка артборда, не облик: не сверяется
    elif prop == "font-size":
        lens(v, "font-size")
    elif prop == "line-height":
        if NUM_RX.match(low):
            out.append(Literal("line-height", v, round(float(low), 4), line, prop, where))
        else:
            lens(v, "line-height")
    elif prop == "font-weight":
        w = weight_of(low)
        if w is not None:
            out.append(Literal("weight", v, w, line, prop, where))
    elif prop == "font-family":
        f = first_family(v)
        if f and f not in ("inherit", "system-ui", "sans-serif", "serif", "monospace"):
            out.append(Literal("family", v.split(",")[0].strip(), f, line, prop, where))
    elif prop == "letter-spacing":
        lens(v, "letter-spacing")
    elif prop == "font":
        m = re.match(r"^\s*(?:(italic|oblique|normal)\s+)?(?:(\d{3}|bold|normal)\s+)?(\d*\.?\d+(?:px|rem))"
                     r"(?:\s*/\s*(\d*\.?\d+(?:px|rem)?))?\s+(.+)$", v, re.I)
        if m:
            if m.group(2):
                out.append(Literal("weight", m.group(2), weight_of(m.group(2)), line, prop, where))
            out.append(Literal("font-size", m.group(3), px(m.group(3)), line, prop, where))
            if m.group(4):
                lh = m.group(4)
                out.append(Literal("line-height", lh, px(lh) if px(lh) is not None else round(float(lh), 4), line,
                                   prop, where))
            f = first_family(m.group(5))
            if f:
                out.append(Literal("family", m.group(5).split(",")[0].strip(), f, line, prop, where))
    elif prop in ("transition", "transition-duration", "animation", "animation-duration", "transition-delay",
                  "animation-delay"):
        for m in DUR_RX.finditer(low):
            out.append(Literal("duration", m.group(0), ms(m.group(0)), line, prop, where))
    return out


def block_literals(decls, line, where="style"):
    """Литералы блока объявлений [(свойство, значение)]. Интерлиньяж получает вторую запись по кеглю того же блока
    (один литерал кегля на блок): у px — отношение к кеглю, у безразмерного — px."""
    out = []
    for prop, value in decls:
        out += literals_of(prop, value, line, where)
    sizes = {x.key for x in out if x.family == "font-size"}
    size = next(iter(sizes)) if len(sizes) == 1 else None
    if size:
        for x in out:
            if x.family == "line-height" and isinstance(x.key, (int, float)):
                x.alt = round(x.key * size, 2) if NUM_RX.match(x.raw.strip()) else round(x.key / size, 4)
    return out


def in_tokens(lit, ts):
    """(в токенах, семейство есть в ДС)."""
    f = lit.family
    if not ts.has(f):
        return False, False
    if f == "color":
        k = lit.key                                      # прозрачный конец растворения — цвет токена с альфой 0
        return k in ts.colors or (len(k) == 9 and k.endswith("00") and k[:7] in ts.colors), True
    if f == "family":
        return lit.key in ts.families, True
    if f == "shadow":
        return lit.key in ts.shadows, True
    if f == "duration":
        return lit.key in ts.durations, True
    if f == "weight":
        return lit.key in ts.numbers.get("weight", {}), True
    if f == "line-height":
        nums, lens = ts.numbers.get("line-height", {}), ts.lengths.get("line-height", {})
        ratio = NUM_RX.match(lit.raw.strip()) is not None
        own, other = (nums, lens) if ratio else (lens, nums)
        in_px = lit.alt if ratio else lit.key            # высота строки в px: своя запись или отношение × кегль блока
        return (lit.key in own or (lit.alt is not None and lit.alt in other)
                or ts.in_range(f, in_px) is not None), True
    return (lit.key in ts.lengths.get(f, {}) or ts.in_range(f, lit.key) is not None), True


def nearest(lit, ts):
    """Ближайшее значение токена: цвет — по OKLab, длина и число — по модулю разности."""
    try:
        if lit.family == "color":
            if not ts.colors or len(lit.key) < 7:
                return None
            a = oklab(lit.key[:7])
            best = min(ts.colors, key=lambda c: sum((x - y) ** 2 for x, y in zip(a, oklab(c[:7]))))
            return f"{', '.join(ts.colors[best][:2])} {best}"
        pool = {}
        if lit.family in ("weight",):
            pool = ts.numbers.get("weight", {})
        elif lit.family == "line-height":
            pool = dict(ts.numbers.get("line-height", {}))
            pool.update(ts.lengths.get("line-height", {}))
        elif lit.family == "duration":
            pool = ts.durations
        else:
            pool = ts.lengths.get(lit.family, {})
        nums = [k for k in pool if isinstance(k, (int, float))]
        if not nums or not isinstance(lit.key, (int, float)):
            return None
        best = min(nums, key=lambda k: abs(k - lit.key))
        unit = "px" if lit.family not in ("weight", "line-height", "duration") else ("ms" if lit.family == "duration" else "")
        if lit.family == "line-height" and best in ts.lengths.get("line-height", {}):
            unit = "px"
        return f"{', '.join(pool[best][:2])} {fmt(best)}{unit}"
    except (ValueError, TypeError):
        return None


def line_of(text, offset):
    return text.count("\n", 0, offset) + 1


def artboard_literals(ab, vals, props):
    """Литералы облика артборда: стили элементов, <style>, цветовые атрибуты SVG, твики. Рамка — не литерал."""
    text = ab.text
    lits = []
    tr = DC.Translator(ab, vals, props)
    scope = [vals, props]
    offsets = _offsets(ab.root)
    for node in DC.walk(ab.root):
        if not isinstance(node, DC.El) or node.tag == "#root" or DC.is_logic(node):
            continue
        line = line_of(text, offsets.get(id(node), 0))
        style = node.attrs.get("style")
        if style:
            style = DC.HOLE.sub(lambda m: DC.as_text(tr.value(m.group(1), scope)), style)
            lits += block_literals([(prop, value) for prop, value in declarations(style)
                                    if not (node is ab.frame and prop in ("width", "height"))], line)
        for attr in SVG_COLOR_ATTRS:
            if attr in node.attrs and node.tag not in ("html", "body", "meta"):
                v = DC.HOLE.sub(lambda m: DC.as_text(tr.value(m.group(1), scope)), node.attrs[attr])
                lits += [x for x in literals_of("fill" if attr != "color" else "color", v, line, "attr")]
        if node.tag == "style":
            css = "".join(c.raw for c in node.children if isinstance(c, DC.Tx))
            base = offsets.get(id(node), 0) + len(node.raw)
            blocks = {}
            for prop, value, off in css_rules(css):
                blocks.setdefault(off, []).append((prop, value))
            for off, decls in blocks.items():
                lits += block_literals(decls, line_of(text, base + off), "css")
    if ab.logic is not None:
        line = line_of(text, offsets.get(id(ab.logic), 0))
        for name, spec in ab.props_spec.items():
            if name.startswith("$") or not isinstance(spec, dict) or spec.get("editor") != "color":
                continue
            v = spec.get("default")                    # образцы твика (options) — выбор заказчика, не облик артборда
            c = norm_color(str(v)) if v is not None else None
            if c:
                lits.append(Literal("color", str(v), c, line, f"твик {name} (умолчание)", "tweak"))
    return lits


def _offsets(root):
    out, pos = {}, 0

    def rec(n):
        nonlocal pos
        if isinstance(n, DC.Tx):
            pos += len(n.raw)
            return
        if n.tag != "#root":
            out[id(n)] = pos
            pos += len(n.raw)
        for c in n.children:
            rec(c)
        if n.tag != "#root":
            pos += len(n.end)
    rec(root)
    return out


# ------------------------------------------------------------------ сверка

@dataclass
class Group:
    family: str
    raw: str
    key: object
    lines: list
    props: list
    where: set
    near: str | None = None
    count: int = 0
    widths: list = field(default_factory=list)         # ширины артбордов страницы, где литерал встретился
    board: object = None                               # первый такой артборд: его строки и путь несёт находка


def compare(lits, ts):
    """Литералы вне токенов, сгруппированные по (семейство, значение); семейства без токенов в ДС — заметкой."""
    groups, skipped = {}, set()
    for lit in lits:
        ok, known = in_tokens(lit, ts)
        if not known:
            skipped.add(lit.family)
            continue
        if ok:
            continue
        g = groups.get((lit.family, lit.key))
        if g is None:
            g = groups[(lit.family, lit.key)] = Group(lit.family, lit.raw, lit.key, [], [], set(), nearest(lit, ts))
        g.count += 1
        if lit.line not in g.lines:
            g.lines.append(lit.line)
        if lit.prop not in g.props:
            g.props.append(lit.prop)
        g.where.add(lit.where)
    return sorted(groups.values(), key=lambda g: (FAMILIES.index(g.family), g.lines[0])), sorted(skipped)


def message(g):
    count = g.count
    lines = ", ".join(str(x) for x in sorted(g.lines)[:8]) + (" …" if len(g.lines) > 8 else "")
    where = "; ".join(g.props[:4])
    near = f"; ближайший токен — {g.near}" if g.near else ""
    if len(g.widths) > 1:
        widths = ", ".join(str(w) for w in sorted(g.widths, reverse=True))
        return (f"{FAMILY_RU[g.family]} `{g.raw}` вне токенов ДС ({where}): ширины {widths}; мест {count}; строки "
                f"{lines} — {g.board.name}{near}")
    return (f"{FAMILY_RU[g.family]} `{g.raw}` вне токенов ДС ({where}): мест {count}, строки {lines}{near}")


def page_of(name, width):
    """Имя страницы холста по имени артборда: `<Имя>-<ширина>` и часть `<Имя>-<ширина>-<N>` → `<Имя>`, когда ширина в
    имени равна ширине рамки; иначе артборд — страница сам по себе."""
    stem = name[:-len(".dc.html")] if name.endswith(".dc.html") else Path(name).stem
    for rx in (r"(.+)-(\d+)-\d+", r"(.+)-(\d+)"):
        m = re.fullmatch(rx, stem)
        if m and width and int(m.group(2)) == int(width):
            return m.group(1)
    return stem


def merge_widths(results, canvas=None):
    """Находки артбордов одной страницы холста — одной записью на литерал с перечнем ширин.
    → [(страница, первый артборд, группы, пропущенные семейства)] в порядке артбордов."""
    pages = {}
    for ab, _stage, groups, skipped in results:
        if groups is None:
            continue
        board = (canvas or {}).get("boards", {}).get(ab.name) if canvas else None
        width = DC.board_size(ab, board)[0]
        first, merged, skip = pages.setdefault(page_of(ab.name, width), (ab, {}, []))
        for g in groups:
            m = merged.get((g.family, g.key))
            if m is None:
                m = merged[(g.family, g.key)] = Group(g.family, g.raw, g.key, list(g.lines), [], set(), g.near,
                                                      board=ab)
            m.count += g.count
            m.props += [p for p in g.props if p not in m.props]
            m.where |= g.where
            if width and int(width) not in m.widths:
                m.widths.append(int(width))
        skip += [fam for fam in skipped if fam not in skip]
    return [(name, first, sorted(merged.values(), key=lambda g: (FAMILIES.index(g.family), g.lines[0])), skip)
            for name, (first, merged, skip) in pages.items()]


FIX = ("литерал → значение токена ДС: разовая правка — ближайший токен, системная — токен или ручка DTCG; решает "
       "заказчик как владелец облика (references/claude-design.md § Правки токенов)")
FIX_ACCEPTED = ("макет принят: литерал вне токенов — пункт C2 приёмки (S): правка (разовая — ближайший токен, системная — "
                "токен или ручка DTCG) или запись исключения в REVIEW.md — кто принял и почему; решает заказчик как "
                "владелец облика")


def scan_boards(files, ts, canvas=None, all_stages=False):
    """[(артборд, этап, группы, пропущенные семейства)] для файлов .dc.html."""
    boards = [DC.load(p) for p in files]
    out = []
    for ab, (vals, props) in zip(boards, DC.render_values(boards)):
        board = (canvas or {}).get("boards", {}).get(ab.name) if canvas else None
        stage = DC.stage_of(board, canvas)
        if stage != "mockup" and not all_stages:
            out.append((ab, stage, None, []))
            continue
        lits = artboard_literals(ab, vals, props)
        groups, skipped = compare(lits, ts)
        out.append((ab, stage, groups, skipped))
    return out


def project_tokens(call):
    """Файлы токенов продукта по старшинству и копия ДС, установленная в холст."""
    css = docpaths.design(call.slug, "tokens-css", repo=call.repo)
    dtcg = docpaths.design(call.slug, "tokens", repo=call.repo)
    art = docpaths.design(call.slug, "ds-project", repo=call.repo) / "tokens.json"
    files = [css] if css.is_file() else [dtcg] if dtcg.is_file() else [art] if art.is_file() else []
    src = docpaths.design(call.slug, "canvas-project", surface=call.surface, repo=call.repo)
    files += sorted(src.glob("ds/*/tokens.json")) if src.is_dir() else []
    return files


def cmd_check(call):
    rep = FND.Report()
    sev = "warning"
    fix = FIX_ACCEPTED if call.args.accepted else FIX
    src = docpaths.design(call.slug, "canvas-project", surface=call.surface, repo=call.repo)
    tok_files = project_tokens(call)
    if not src.is_dir():
        FND.print_findings([], as_json=call.json)
        return 0
    if not tok_files:
        rep.add(RULE, "hint", surface=call.surface, kind="canvas", ref=call.surface,
                path=docpaths.rel(docpaths.design(call.slug, repo=call.repo), call.repo),
                message="нет токенов ДС продукта (system.tokens.css, system.tokens.json, tokens.json артефакта): литералы "
                        "холста сверять не с чем", fix="этап design-system — /design-deep-dive " + call.slug)
        FND.print_findings(rep.items, as_json=call.json)
        return rep.exit_code()
    ts = load_tokens(tok_files)
    canvas = DC.load_canvas(src)
    boards = scan_boards(DC.artboard_files(src, canvas), ts, canvas, call.args.all_stages)
    for page, first, groups, skipped in merge_widths(boards, canvas):
        for g in groups:
            rep.add(RULE, sev, surface=call.surface, kind="artboard", ref=f"{page}#{g.family}:{g.raw}",
                    path=docpaths.rel(g.board.path, call.repo), message=message(g), fix=fix)
        for fam in skipped:
            rep.add(RULE, "hint", surface=call.surface, kind="artboard", ref=f"{page}#{fam}",
                    path=docpaths.rel(first.path, call.repo),
                    message=f"{FAMILY_RU[fam]}: в ДС нет токенов этого семейства — литералы не сверялись",
                    fix="пробел ДС — этап design-system")
    FND.print_findings(rep.items, as_json=call.json,
                       title=None if call.json else f"literal_tokens check {call.slug} {call.surface}")
    return rep.exit_code()


def cmd_scan(a):
    ts = load_tokens(a.tokens)
    rep = FND.Report()
    for s in a.source:
        s = Path(s)
        if s.is_dir():
            canvas = DC.load_canvas(s)
            files = DC.artboard_files(s, canvas)
        elif s.is_file():
            canvas, files = DC.load_canvas(s.parent), [s]
        else:
            raise ToolError(f"нет файла или папки: {s}")
        for page, first, groups, skipped in merge_widths(scan_boards(files, ts, canvas, a.all_stages), canvas):
            for g in groups:
                rep.add(RULE, "warning", surface=None, kind="artboard", ref=f"{page}#{g.family}:{g.raw}",
                        path=str(g.board.path), message=message(g), fix=FIX)
            for fam in skipped:
                rep.add(RULE, "hint", surface=None, kind="artboard", ref=f"{page}#{fam}", path=str(first.path),
                        message=f"{FAMILY_RU[fam]}: в ДС нет токенов этого семейства — литералы не сверялись",
                        fix="пробел ДС — этап design-system")
    FND.print_findings(rep.items, as_json=a.json, title=None if a.json else "literal_tokens scan")
    return rep.exit_code()


def cmd_tokens(a):
    ts = load_tokens(a.files)
    d = {"sources": ts.sources, "themes": ts.themes, "breakpoints": ts.breakpoints,
         "colors": {k: v for k, v in sorted(ts.colors.items())},
         "lengths": {c: {fmt(k): v for k, v in sorted(d.items())} for c, d in sorted(ts.lengths.items())},
         "ranges": {c: [{"min": lo, "max": hi, "name": n} for lo, hi, n in r] for c, r in sorted(ts.ranges.items())},
         "numbers": {c: {fmt(k): v for k, v in sorted(d.items())} for c, d in sorted(ts.numbers.items())},
         "families": ts.families, "shadows": ts.shadows,
         "durations": {fmt(k): v for k, v in sorted(ts.durations.items())}}
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
    else:
        for k in ("themes", "breakpoints"):
            print(f"{k}: {d[k]}")
        print("цвета:", len(d["colors"]), "· длины:", {c: len(v) for c, v in d["lengths"].items()},
              "· резиновые:", {c: len(v) for c, v in d["ranges"].items()}, "· числа:",
              {c: len(v) for c, v in d["numbers"].items()}, "· гарнитуры:", sorted(d["families"]), "· тени:",
              len(d["shadows"]), "· длительности:", sorted(d["durations"]))
    return 0


# ------------------------------------------------------------------ самопроверка

def selftest():
    import subprocess
    import tempfile
    ok = True

    def check(name, got, want=True):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"{'OK  ' if good else 'FAIL'} {name}" + ("" if good else f": {got!r} (ожидалось {want!r})"))

    check("цвет #ABC → #aabbcc", norm_color("#ABC"), "#aabbcc")
    check("rgb(2 6 23 / 0.08) → #02061714", norm_color("rgb(2 6 23 / 0.08)"), "#02061714")
    check("rgba(255, 255, 255, 1) → #ffffff", norm_color("rgba(255, 255, 255, 1)"), "#ffffff")
    check("hsl(0, 0%, 100%) → #ffffff", norm_color("hsl(0, 0%, 100%)"), "#ffffff")
    check("oklch(1 0 0) → #ffffff", norm_color("oklch(1 0 0)"), "#ffffff")
    check("семейство токена: --type-title-size → кегль", token_cat("type-title-size"), "font-size")
    check("семейство токена: --size-control-md → размер", token_cat("size-control-md"), "size")
    check("семейство токена: border-w → толщина", token_cat("border-w"), "border")
    check("семейство токена: --motion-duration-fast → длительность", token_cat("motion-duration-fast"), "duration")
    check("font: 600 17px/1.3 'Golos Text' → 4 литерала",
          sorted((x.family, x.key) for x in literals_of("font", "600 17px/1.3 'Golos Text', system-ui", 1)),
          [("family", "golos text"), ("font-size", 17.0), ("line-height", 1.3), ("weight", 600.0)])
    check("border: 1px solid #CFD6DF → толщина и цвет",
          sorted((x.family, x.key) for x in literals_of("border", "1px solid #CFD6DF", 1)),
          [("border", 1.0), ("color", "#cfd6df")])
    check("padding: 0 120px → один отступ", [(x.family, x.key) for x in literals_of("padding", "0 120px", 1)],
          [("spacing", 120.0)])
    check("проценты и ch — не литералы", literals_of("max-width", "34ch", 1) + literals_of("width", "95%", 1), [])
    check("размеры элементов (width, min-height, max-width) — раскладка, не литералы облика",
          literals_of("width", "440px", 1) + literals_of("min-height", "72px", 1) + literals_of("max-width", "720px", 1),
          [])
    ex = DC.EXAMPLE
    art = ex / "design-system" / "project" / "tokens.json"
    ts = load_tokens([art])
    check("артефакт «Спицы»: темы light и dark", ts.themes, ["light", "dark"])
    check("артефакт: тёмный фон #0C0F14 в цветах", "#0c0f14" in ts.colors, True)
    check("артефакт: отступы 4…104 и gutter 40", sorted(ts.lengths.get("spacing", {})),
          [4.0, 8.0, 12.0, 16.0, 24.0, 32.0, 40.0, 48.0, 64.0, 104.0])
    check("артефакт: кегли стилей и typescale", sorted(ts.lengths.get("font-size", {})),
          [14.0, 17.0, 20.0, 21.0, 36.0, 60.0])
    check("артефакт: гарнитуры", sorted(ts.families), ["golos text", "unbounded"])
    check("артефакт: толщина границы border-w 1px", sorted(ts.lengths.get("border", {})), [1.0])
    src = ex / "canvas" / "project"
    res = {ab.name: (stage, groups) for ab, stage, groups, _s in scan_boards(DC.artboard_files(src), ts, DC.load_canvas(src))}
    check("сверяются артборды макета: Main, Landing-Phone, Booking",
          sorted(n for n, (st, g) in res.items() if g is not None), ["Booking.dc.html", "Landing-Phone.dc.html",
                                                                      "Main.dc.html"])
    main = {(g.family, g.raw) for g in res["Main.dc.html"][1]}
    check("Main: отступ 120px вне шкалы", ("spacing", "120px") in main, True)
    check("Main: образцы твика accent (#0B6E4F, #0E7490) не сверяются",
          {("color", "#0B6E4F"), ("color", "#0E7490")} & main, set())
    check("Main: размеры 440px и 720px не сверяются", any(f == "size" for f, _ in main), False)
    check("Main: цвета фона и текста из токенов", any(f == "color" and r in ("#EEF2F6", "#11151C") for f, r in main), False)
    check("Main: радиусы твика 6 и 12 — токены", any(f == "radius" for f, _ in main), False)
    bk = {(g.family, g.raw) for g in res["Booking.dc.html"][1]}
    check("Booking: тёмная палитра renderVals — токены", any(f == "color" and r.startswith("#0C0F14") for f, r in bk), False)
    fx_css = kbpaths.scripts("tests", "fixtures", "cabinet-ds", "files", "design", "system.tokens.css")
    tc = load_tokens([fx_css])
    check("CSS фикстуры cabinet-ds: брейкпоинты", tc.breakpoints, [640.0, 1024.0, 1440.0])
    check("CSS: темы light и dark", tc.themes, ["light", "dark"])
    check("CSS: гарнитура — семейство стека в запасе ссылки на переменную семейства", sorted(tc.families),
          ["golos text"])
    check("CSS: длительности", sorted(tc.durations), [100.0, 150.0, 200.0])
    check("CSS: тень elevation-raised", len(tc.shadows) >= 1, True)
    fx_dtcg = kbpaths.scripts("tests", "fixtures", "cabinet-ds", "files", "design", "system.tokens.json")
    td_ = load_tokens([fx_dtcg])
    check("DTCG через ds_build: те же значения, что CSS", (sorted(td_.colors), td_.breakpoints),
          (sorted(tc.colors), tc.breakpoints))
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "Page.dc.html"
        p.write_text('<!doctype html><html><head><script src="./support.js"></script></head><body><x-dc><helmet>'
                     '<style>a{color:#2146D8}</style></helmet><div style="width: 300px; height: 200px; background: '
                     '#EEF2F6; padding: 24px 30px; box-shadow: 0 1px 2px #000;"><p style="font-size: 17px; '
                     'color: #123456;">т</p></div></x-dc></body></html>', encoding="utf-8")
        (Path(td) / "canvas.json").write_text(json.dumps({"boards": {"Page.dc.html": {"w": 300, "h": 200, "page": "hifi"}},
                                                          "order": ["Page.dc.html"], "pages": [{"id": "hifi"}]}),
                                              encoding="utf-8")
        r = subprocess.run([sys.executable, __file__, "scan", td, "--tokens", str(art), "--json"], capture_output=True,
                           text=True)
        items = FND.parse_lines(r.stdout)
        got = sorted((f.severity, f.ref.split("#", 1)[1]) for f in items)
        check("scan: отступ 30px, цвета #123456 и #000 тени — находки, тень без токенов — заметка",
              got, [("hint", "shadow"), ("warning", "color:#000"), ("warning", "color:#123456"),
                    ("warning", "spacing:30px")])
        check("scan: ближайший токен названа", any("ближайший токен" in f.message for f in items), True)
    css = (':root { color-scheme: dark; --color-bg: #101214; --color-text: #EDEDEE; --space-md: 16px;\n'
           '  --type-display-size: clamp(2.25rem, 1.5rem + 2vw, 3.5rem); --type-display-leading: 1.1;\n'
           '  --type-body-size: 1rem; --type-body-leading: 1.5;\n'
           '  --type-note-size: 0.875rem; --type-note-leading: 1.428572;\n'
           '  --space-section: clamp(48px, 8vw, 96px); --motion-duration-fast: 120ms;\n'
           '  --motion-transition-fade: 200ms cubic-bezier(0.4, 0, 0.2, 1) 50ms;\n'
           '  --gradient-veil: linear-gradient(0deg, rgb(16 18 20 / 0.8) 0%, rgb(16 18 20 / 0.4) 60%,'
           ' rgb(16 18 20 / 0) 100%);\n'
           '}\n')
    tk = TokenSet()
    load_css_tokens(css, tk, "selftest.css")
    check("CSS с color-scheme: dark — темы [dark]", tk.themes, ["dark"])
    tl = TokenSet()
    load_css_tokens(css.replace("color-scheme: dark", "color-scheme: light dark")
                    + ':root[data-theme="dark"] { --color-bg: #000000; }', tl, "selftest.css")
    check("CSS с color-scheme: light dark и блоком тёмной темы — темы [light, dark]", tl.themes, ["light", "dark"])
    td2 = TokenSet()
    load_css_tokens(css + ":root[data-theme='light'] { --color-bg: #ffffff; }", td2, "selftest.css")
    check("CSS: первая тема тёмная, блок светлой — темы [dark, light]", td2.themes, ["dark", "light"])
    check("резиновый токен: границы clamp() в px", (tk.ranges.get("font-size"), tk.ranges.get("spacing")),
          ([(36.0, 56.0, "type-display-size")], [(48.0, 96.0, "space-section")]))
    tf = TokenSet()
    load_css_tokens(':root { --font-text: var(--font-golos-text, "Golos Text", Arial, sans-serif);\n'
                    '  --type-body-family: var(--font-golos-text, "Golos Text", Arial, sans-serif);\n'
                    '  --type-code-family: var(--font-mono); --font-mono: "Demo Mono", monospace;\n'
                    '  --type-note-family: var(--font-mono, "Reserve Mono", monospace);\n'
                    '  --type-lost-family: var(--font-nope); }\n', tf, "selftest.css")
    check("гарнитура ссылкой на переменную семейства: файл её не объявляет — стек в запасе; объявленная — её значение, "
          "и при запасе у ссылки", sorted(tf.families), ["demo mono", "golos text", "var(--font-nope)"])

    def outside(decls):
        return sorted((x.family, x.raw) for x in block_literals(decls, 1) if in_tokens(x, tk) == (False, True))

    check("резиновый токен: значение в границах clamp() — токен, вне границ — литерал",
          outside([("font-size", "44px"), ("padding", "72px 16px")]) + outside([("font-size", "60px")])
          + outside([("margin-top", "100px")]), [("font-size", "60px"), ("spacing", "100px")])
    check("интерлиньяж отношением: 24px при кегле 16px и 20px при кегле 14px — токены, 22px при 16px — литерал",
          outside([("font-size", "16px"), ("line-height", "24px")])
          + outside([("font-size", "14px"), ("line-height", "20px")])
          + outside([("font-size", "16px"), ("line-height", "22px")]), [("line-height", "22px")])
    check("интерлиньяж: безразмерный токен через round(…, 1px) и запись font — не литералы",
          outside([("line-height", "round(nearest, calc(var(--type-body-leading) * 1em), 1px)")])
          + outside([("font", "400 16px/24px system-ui")])
          + outside([("font-size", "44px"), ("line-height", "1.1")]), [])
    check("шаг round() снимается, границы clamp() остаются",
          (drop_round_step("round(up, calc(1em * 1.5), 1px)"), drop_round_step("clamp(1rem, 2vw, 3rem)")),
          ("round(up, calc(1em * 1.5))", "clamp(1rem, 2vw, 3rem)"))
    check("длительности по токенам движения: простой токен и оба времени составного перехода — токены, 600ms — литерал",
          (sorted(tk.durations), outside([("transition", "opacity 200ms linear 50ms, color 120ms")])
           + outside([("animation", "rise 600ms linear both")])), ([50.0, 120.0, 200.0], [("duration", "600ms")]))
    check("слои: остановки токена-градиента и прозрачный конец цвета токена — токены, свой цвет — литерал",
          outside([("background", "linear-gradient(90deg, rgb(16 18 20 / 0.4), rgb(16 18 20 / 0))")])
          + outside([("background", "linear-gradient(90deg, #EDEDEE, rgb(237 237 238 / 0))")])
          + outside([("background", "linear-gradient(90deg, rgb(16 18 20 / 0.5), rgb(1 2 3 / 0))")]),
          [("color", "rgb(1 2 3 / 0)"), ("color", "rgb(16 18 20 / 0.5)")])
    with tempfile.TemporaryDirectory() as td:
        board = ('<!doctype html><html><head><script src="./support.js"></script></head><body><x-dc>'
                 '<div style="width: %dpx; height: 300px; background: #101214; padding: 16px;"><p style="font-size: 16px; '
                 'line-height: 24px; color: #123456; margin-top: %s;">т</p></div></x-dc></body></html>')
        names = {"Page-1440.dc.html": (1440, "30px"), "Page-390-1.dc.html": (390, "30px"),
                 "Page-390-2.dc.html": (390, "16px"), "Flat-204-1440.dc.html": (1440, "16px")}
        for n, (w, gap) in names.items():
            (Path(td) / n).write_text(board % (w, gap), encoding="utf-8")
        (Path(td) / "canvas.json").write_text(json.dumps(
            {"boards": {n: {"w": w, "h": 300, "page": "hifi"} for n, (w, _g) in names.items()}, "order": list(names),
             "pages": [{"id": "hifi"}]}), encoding="utf-8")
        tok = Path(td) / "tokens.css"
        tok.write_text(css, encoding="utf-8")
        r = subprocess.run([sys.executable, __file__, "scan", td, "--tokens", str(tok), "--json"], capture_output=True,
                           text=True)
        items = FND.parse_lines(r.stdout)
        check("ширины: страница на двух ширинах и в частях — одна находка на литерал",
              sorted(f.ref for f in items), ["Flat-204#color:#123456", "Page#color:#123456", "Page#spacing:30px"])
        msg = {f.ref: f.message for f in items}
        check("ширины: перечень ширин, места сложены, строки — первого артборда",
              ("ширины 1440, 390; мест 3; строки 1 — Page-1440.dc.html" in msg.get("Page#color:#123456", ""),
               "ширины 1440, 390; мест 2;" in msg.get("Page#spacing:30px", ""),
               "ширины" in msg.get("Flat-204#color:#123456", "")), (True, True, False))
        check("ширины: путь находки — первый артборд страницы",
              {Path(f.path).name for f in items if f.ref.startswith("Page#")}, {"Page-1440.dc.html"})
    kbpaths.use("tests")
    import fixture_project
    with fixture_project.built("canvas") as fx:
        argv = [fx.slug, "promo", "--repo", str(fx.root)]
        r = subprocess.run([sys.executable, __file__, "check"] + argv + ["--json"], capture_output=True, text=True)
        items = FND.parse_lines(r.stdout)
        check("фикстура canvas: check — код 0 (warning не ошибка)", r.returncode, 0)
        check("фикстура canvas: находки только warning и hint", {f.severity for f in items} <= {"warning", "hint"}, True)
        check("фикстура canvas: все находки — R-VIS-004", {f.rule for f in items}, {RULE})
        r2 = subprocess.run([sys.executable, __file__, "check"] + argv + ["--json", "--accepted"], capture_output=True,
                            text=True)
        acc = FND.parse_lines(r2.stdout)
        check("--accepted: литералы — warning, код 0; совет — пункт C2 с записью в REVIEW.md",
              (r2.returncode, {f.severity for f in acc} <= {"warning", "hint"},
               any("C2" in f.fix and "REVIEW.md" in f.fix for f in acc)), (0, True, True))
        html_dir = docpaths.design(fx.slug, "canvas-html", surface="promo", repo=fx.root)
        html_dir.mkdir(parents=True, exist_ok=True)
        (html_dir / "home.html").write_text('<!doctype html><p style="color: #123456; padding: var(--nope)">т</p>\n',
                                            encoding="utf-8")
        r3 = subprocess.run([sys.executable, __file__, "check"] + argv + ["--json"], capture_output=True, text=True)
        check("HTML в canvas/html не сверяется: находки — только по артбордам холста",
              sorted(f.ref for f in FND.parse_lines(r3.stdout)), sorted(f.ref for f in items))
    print("selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


# ------------------------------------------------------------------ вызов

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv[:1] in (["scan"], ["tokens"]):
            ap = argparse.ArgumentParser(prog=f"literal_tokens.py {argv[0]}")
            ap.add_argument("cmd")
            if argv[0] == "scan":
                ap.add_argument("source", nargs="+", help="файл .dc.html или папка исходников холста")
                ap.add_argument("--tokens", action="append", required=True,
                                help="токены ДС: system.tokens.css, DTCG .json или tokens.json артефакта; повтором")
                ap.add_argument("--all-stages", action="store_true", help="сверять и страницу «Направления»")
            else:
                ap.add_argument("files", nargs="+")
            ap.add_argument("--json", action="store_true")
            a = ap.parse_args(argv)
            return cmd_scan(a) if argv[0] == "scan" else cmd_tokens(a)
        ap = docpaths.parser("literal_tokens.py", __doc__, commands=("check",), surface="required",
                             accept=lambda s: s.design)
        ap.add_argument("--accepted", action="store_true",
                        help="макет принят: литерал вне токенов — пункт C2 приёмки, совет — правка или запись в REVIEW.md")
        ap.add_argument("--all-stages", action="store_true", help="сверять и страницу «Направления»")
        call = docpaths.parse(ap, argv)
        if call.selftest:
            return selftest()
        return cmd_check(call)
    except (ToolError, DC.ToolError) as e:
        print(f"literal_tokens: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
