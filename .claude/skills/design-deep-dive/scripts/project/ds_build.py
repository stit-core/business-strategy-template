#!/usr/bin/env python3
"""ds_build — производные дизайн-системы продукта из токенов DTCG и проверка их свежести и формата токенов.

Источник правды значений ДС — токены `docs/projects/<slug>/design/system.tokens.json` (DTCG 2025.10); проза —
`design/DESIGN.md`. Из них в одну сторону собираются производные (канон — `docs/projects/_template/design/README.md`,
разделы «ДС» и «Производные»); руками их не правят:

  design/system.tokens.css                   CSS-переменные для kit и кода: имя переменной — путь токена через дефис
                                             (`color.bg.canvas` → `--color-bg-canvas`); алиасы разрешены до значения;
                                             составной типографический токен — пять переменных `-family`, `-size`,
                                             `-leading`, `-weight`, `-tracking`; гарнитура, которой нужен файл, —
                                             ссылкой на переменную семейства со стеком в запасе; режимы — блоки темы
                                             (`[data-theme]` и `prefers-color-scheme`), сокращённого движения
                                             (`[data-motion]` и `prefers-reduced-motion`), плотности (`[data-density]`),
                                             в блок режима идут все токены, чьё значение в режиме другое (ui 09/04 §5);
                                             пружина — `<время успокоения>ms linear(…)`, её параметры — комментарием
  design/DESIGN.md — передняя часть          YAML между метками `---` в начале файла (формат DESIGN.md, ui 12/04 §2.3):
                                             colors, typography, rounded, spacing, прочие токены `x-tokens`, параметры
                                             пружин для кода `x-springs`, режимы `x-modes`, узкая ширина `x-narrow`;
                                             проза после меток не трогается
  design/_design-system/project/tokens.json  токены артефакта Design System списками по семействам (cd 05/01 §3.2):
                                             color с темами, type (families → `--font-<ключ>`, groups со стилями),
                                             spacing, radius, shadow и свои семейства по первому сегменту пути
  design/_design-system/project/README.md    бренд-бук артефакта — проза DESIGN.md без передней части

Узкая ширина: ниже первой границы `breakpoint.*` основной текст `type.body` — не меньше 16 px в любом пресете
(ux/09-mobile/03-mobile-content-tables-forms-dashboards.md §7.1, строка NU-15 `kb/common/canon.tsv`): сборка кладёт это
значение в блок `@media (width < <граница>)` CSS и в `x-narrow` передней части; мобильное приложение берёт основной
кегль оттуда же.

Тема значений `$value` — `light`, пока корень токенов не объявил другую: `$extensions["org.design-deep-dive.modes"].base` —
`light` или `dark`. От неё — `color-scheme` в `:root` (у продукта с одной тёмной темой — `dark`) и первая тема
артефакта; режим токена с именем парной темы даёт вторую тему — её блок включается и по настройке системы
(`prefers-color-scheme`), и атрибутом `[data-theme]`. Каждый блок темы объявляет её `color-scheme`: у продукта с двумя
темами `:root` несёт обе (решает система), блок парной темы — её схему и по системе, и под атрибутом, а тема значений
под атрибутом — блок `:root[data-theme="<тема значений>"]` с одной её схемой: без него выбор темы значений при другой
теме системы оставил бы системные элементы страницы (чекбокс, полосы прокрутки) в теме системы. Режим с другим
именем — правка поверх действующей темы: своей схемы у его блока нет, и второй темой он продукт не делает.

Сокращённое движение — режим `reduced` токенов (или расширение `reduce`): выбор посетителя сильнее системы в обе
стороны, как у тем (норма переключателя — creative 05/01 §4.4).
Блок по системе — `@media (prefers-reduced-motion: reduce)` на `:root:not([data-motion="full"])`: выбор «полное
движение» оставляет значения `$value` и при системном «уменьшить движение»; блок `:root[data-motion="reduced"]` —
сокращённое движение при любой системе; без атрибута решает система. У ДС без режима `reduced` блока нет.

Пружина — расширение `$extensions["org.design-deep-dive.spring"]` токена transition: `dampingRatio` (ζ) и `stiffness`
(k при массе 1, ω = √k) — форма Compose и Material 3 (ui 08/04 §1). В CSS токен даёт `<время успокоения>ms linear(…)` и
задержку `$value`: время успокоения — последний выход кривой из полосы 1 % пути вокруг цели, вверх до 10 ms; точки
`linear()` ставятся там, где кривая гнётся, пока ломаная отходит от неё больше чем на 0,25 % пути вместе с округлением
записи; остаток до цели (не больше 1 % пути) кривая выбирает плавно на последней четверти времени. Параметры пружины —
комментарием над переменной; алиас на пружину целиком даёт ту же кривую. `$value` — переход-запас для инструментов без
расширения: его длительность равна времени успокоения, кривую сборка не читает. Значение режима `reduced` — переход без
пружины: кривая без перелёта и своё время. Для кода параметры идут в `x-springs` передней части (`dampingRatio`,
`stiffness`, `response` и `bounce` SwiftUI, перелёт, время успокоения) и в `show --json`; в артефакт движение не идёт.

Темы, которых ждут брифы — бриф сайта каждой поверхности слоя страницы и бриф на вид кабинета, блок `themes` (две темы
— `dark.needed` или `default: system`, иначе одна — `default`), — есть у токенов темой значений или режимом; иначе
R-COV-010 (`theme_gaps()`): сайт в тёмной теме на токенах без `modes.base: dark` получил бы `color-scheme: light`, и
системные элементы страницы были бы светлыми. Ту же нехватку манифест готовности несёт строкой open «тема: …» единиц
поверхности (ready.py) — публикацию она держит.

Шрифты: семейство, которому нужен файл, — первое имя стека токена fontFamily или fontFamily типографического токена,
если оно не родовое (`GENERIC_FONTS`) и не системное (`SYSTEM_FONTS`); прочие имена стека — запасные, файлов им не
нужно. Начертания семейства — насыщенности `fontWeight` его типографических токенов во всех режимах, начертание —
normal: `font_needs()` (`web_families()` — только имена). Файлы — строки манифеста ассетов продукта с полем `font` (их
сверяет ready.py: начертание без принятого файла с лицензией — строка open «шрифт: …»).

Гарнитура в CSS: стек такого семейства — у токена fontFamily и у части `-family` типографического токена — идёт
ссылкой на переменную семейства со стеком в запасе, `var(--font-<ключ>, <стек>)`. Ключ — имя семейства строчными,
каждый отрезок знаков вне латинских букв и цифр — один дефис, дефисы по краям срезаются (`family_key()`): `Golos
Text` → `--font-golos-text`, значение —
`var(--font-golos-text, "Golos Text", Arial, sans-serif)`. Сам файл переменную семейства не объявляет: без загрузчика
шрифтов действует стек, а загрузчик кода, который подключает файл под своим именем `@font-face`, объявляет её на
`:root` — и токены гарнитуры и роли текста берут его семейство. Стек системного или родового семейства идёт литералом.
Литералом остаётся и стек семейства без ключа (в имени нет латинских букв и цифр) и семейства, чьё имя переменной
занято переменной токена (`font.inter` → `--font-inter` при гарнитуре Inter): ссылка на себя оставила бы её без
значения. Оба случая и два семейства с одним ключом (`PT Sans` и `PT-Sans` ссылаются на одну `--font-pt-sans`) —
предупреждения R-STRUCT-006: загрузчик такую гарнитуру не подменит или подменит не той. Токен гарнитуры называют
ролью, имя семейства пишут латиницей и одним написанием; переименование токена, который читает код, — решение
владельца продукта. В передней части DESIGN.md, в tokens.json артефакта и в `show` стек — литералом.

Типографика в CSS считается от того, что покажет браузер. Интерлиньяж: число DTCG — отношение, округлённое до шести
знаков; когда оно недотягивает до целого px (14 px × 1.428571 = 19,999994), браузер усекает высоту строки до шага
раскладки 1/64 px и строка выходит 19,98 px — в CSS идёт наименьшее шестизначное отношение, которое даёт целый px
(1.428572); в передней части и артефакте остаётся число DTCG. У стиля с готовым интерлиньяжем — `line_height_css`
расширения `org.design-deep-dive.fluid`, выражение от кегля вроде `calc(0.925em + 0.5625rem)` — в CSS идёт это
выражение: число значения верно только на кегле значения, с ним выражение не сверяется. Трекинг: у стиля с резиновым
кеглем (расширение `org.design-deep-dive.fluid` или готовый CSS кегля) px значения верен только на наибольшем кегле,
поэтому в CSS и в передней части он идёт в em — `letter_spacing_em` расширения, иначе px значения / кегль значения.

Что не идёт в артефакт: примитивы (`primitive.*` — холст и компоненты берут значения ролей) и движение (группы
`motion*`, типы duration, cubicBezier, transition — у формата токенов артефакта нет семейства движения, длительности и
кривые задаёт `components/bundle.css`). Поля артефакта, которых нет в DTCG, — расширение
`$extensions["org.design-deep-dive.artifact"]`: у токена `family` (семейство артефакта), у типографического токена
`group` и `sample`; в корне `name` (имя системы) и `families.<семейство>.note`. `usage` токена артефакта —
`$description`
токена DTCG. `example: true` в корне токенов — пометка иллюстрации (фикстуры), она переходит в производный tokens.json.

Расширения токенов — ключи `$extensions` пространства `org.design-deep-dive.`: `modes`, `reduce`, `fluid`, `css`,
`spring` и `artifact` читает сборка; `llm` (правила применения), `meta` и `limits` — пометки, в производные они не
идут. Ключ вне этого списка сборка не читает и называет предупреждением: опечатка в имени и расширение под именем
другого инструмента иначе теряют значение молча. Режим токена с именем темы значений — тоже предупреждение: тема
значений живёт в `$value`.

    ds_build build <slug> [--repo DIR] [--out DIR] [--json]    собрать производные; --out DIR → DIR/docs/projects/…
    ds_build check <slug> [--repo DIR] [--json]                формат DTCG и свежесть производных; ничего не пишет
    ds_build show  <slug> [--repo DIR] [--json]                токены: путь, имя переменной, тип, значения по режимам
    ds_build artifact <slug> --bind-assets FILE --out DIR [--repo DIR] [--json]
                                                               копия исходников артефакта с id загрузок; проект не
                                                               меняется
    ds_build --selftest                                        без сети: разбор, сборка, фикстура cabinet-ds

Загрузки артефакта. Картинки артефакта Design System — загрузки: страница адресует их `/_blob/<id>`, индекс
`design-system.json` — полем `blob` записи `assetGroups.<группа>.files.<имя>`. id у каждого артефакта свой, поэтому
исходники `design/_design-system/project/` называют файл ассета репозитория путём от своего файла
(`../../../../_assets/icons/play.svg` в превью компонента), а id подставляет команда `artifact` по ответу загрузки
`--bind-assets FILE`. Ответ — JSON: список записей с именем файла (`file`, `path` или `name`) и id (`id` или адрес `url`
вида `/_blob/<id>`) либо словарь `{файл: id}`; запись находит файл по имени и концу пути. В копии `--out DIR/docs/
projects/<slug>/design/_design-system/project/`: ссылка `src`, `href`, `poster` или `url(…)` на файл `design/` вне папки
артефакта → `/_blob/<id>`; `/_blob/<id>` с id из индекса исходников → id того же имени файла; `blob` записи индекса —
по имени файла. Публикуется копия. Ссылка или запись без id в ответе остаётся как в исходнике — R-REF-008 `warning`.

Правила (`.claude/skills/design-audit/references/rules.md`):
  R-STRUCT-006  формат DTCG схемой (группы, `$type`, форма `$value` по типу, алиасы `{…}` ведут в токен того же типа,
                без циклов; значения режимов; тема значений `base`; одна шкала space.*; пружина — у токена
                transition, `dampingRatio` и `stiffness` больше нуля и других ключей нет)                   error;
                warning — вторая шкала, лимит семейств, px типографики из CSS расходится с px значения DTCG,
                ключ `$extensions` вне известных сборке, режим токена с именем темы значений, гарнитура, которую
                загрузчик шрифтов не подменит: имя переменной семейства `--font-<ключ>` занято переменной токена, у
                имени семейства нет ключа, у двух семейств один ключ; пружина: перелёт больше 10 %, успокоение
                дольше 600 ms, точек `linear()` больше 64, длительность `$value` не равна времени успокоения, нет
                значения сокращённого движения или в нём перелёт, расширение `css` рядом с пружиной
  R-COV-010     тема брифа сайта или кабинета есть у токенов (тема значений `modes.base` или режим)           warning
  R-FRESH-001   system.tokens.css, передняя часть DESIGN.md, tokens.json и README артефакта равны сборке байт в байт
                (README сверяется по началу файла: хвост, который дописывает страница артефакта, — не расхождение)
                error; нет прозы — warning. Пересборка, которая меняет system.tokens.css, снимает одобрения принятых
                макетов: файл — источник отпечатка одобрения единицы (ready.py); подсказка находки это называет
  R-REF-008     команда artifact: у файла ассета, на который ссылается исходник артефакта, или у записи индекса нет
                id в ответе загрузки                                                                          warning
Код выхода: 0 — нет error, 1 — есть error, 2 — ошибка вызова или окружения.
"""
from __future__ import annotations

import functools
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "lib"))
import kbpaths  # noqa: E402
import docpaths  # noqa: E402
import findings as F  # noqa: E402

EXT_MODES = "org.design-deep-dive.modes"
EXT_LLM = "org.design-deep-dive.llm"
EXT_REDUCE = "org.design-deep-dive.reduce"                 # сокращённое движение расширения страниц сайта
EXT_FLUID = "org.design-deep-dive.fluid"                   # fluid-значение clamp() расширения страниц
EXT_CSS = "org.design-deep-dive.css"                       # готовое CSS-значение расширения страниц
EXT_SPRING = "org.design-deep-dive.spring"                 # пружина токена transition: dampingRatio и stiffness
EXT_ART = "org.design-deep-dive.artifact"                   # поля артефакта Design System, которых нет в DTCG
EXT_SPACE = "org.design-deep-dive."                         # пространство ключей `$extensions`, которые знает сборка
EXT_NOTES = (EXT_SPACE + "meta", EXT_SPACE + "limits")      # пометки токенов страниц: в производные не идут
EXT_KNOWN = (EXT_MODES, EXT_LLM, EXT_REDUCE, EXT_FLUID, EXT_CSS, EXT_SPRING, EXT_ART) + EXT_NOTES

NARROW_BODY_MIN_PX = 16     # ux/09-mobile/03-mobile-content-tables-forms-dashboards.md §7.1 (canon.tsv, NU-15)
REM_PX = 16
LAYOUT_STEP = 64            # браузер считает высоту строки шагами 1/64 px и усекает её до шага
RATIO_DIGITS = 6            # знаков после запятой у отношения интерлиньяжа и у трекинга в em (ui 09/04 §2.5)
TRACKING_TOL_PX = 0.005     # трекинг em × кегль против px значения: расхождение больше половины сотой px

# Пружина в CSS (ui 08/04 §1.2): кривая единичного скачка при массе 1, время — до успокоения, точки — по допуску.
SPRING_KEYS = ("dampingRatio", "stiffness")   # масса 1: при заданном ζ движение задаёт только stiffness / mass
SPRING_SETTLE = 0.01        # успокоение: после него кривая навсегда в полосе 1 % пути вокруг цели
SPRING_FIT = 0.0025         # допуск linear(): ломаная точек отходит от кривой не больше чем на 0,25 % пути
SPRING_THIN = 0.002         # допуск прореживания точек; остаток допуска — на округление записи
SPRING_STEP_MS = 10         # время успокоения в CSS — вверх до 10 ms
SPRING_TAIL = 0.25          # остаток до цели выбирается плавно на последней четверти времени: конец без скачка
SPRING_SAMPLES = 2000       # выборка кривой перед прореживанием (шаг 0,05 % времени)
SPRING_POINTS_MAX = 64      # больше точек — пружина слишком колебательная для linear()
SPRING_OVERSHOOT_MAX = 0.10  # перелёт выше 10 % — вне нормы интерфейса (ui 08/01 §4.6)
SPRING_SETTLE_MAX_MS = 600  # успокоение дольше — выше потолка движения интерфейса (ui 08/01 §1.3)

TYPES = ("color", "dimension", "fontFamily", "fontWeight", "duration", "cubicBezier", "number", "strokeStyle", "border",
         "transition", "shadow", "gradient", "typography")
MOTION_TYPES = ("duration", "cubicBezier", "transition")
THEMES = {"light": "Светлая", "dark": "Тёмная"}
THEME_PAIR = {"light": "dark", "dark": "light"}              # тема, парная теме значений `$value`
DENSITY = ("compact", "comfortable")
REDUCED = "reduced"
BASE_FAMILIES = ("color", "type", "spacing", "radius", "shadow")
FAMILY_OF_GROUP = {"color": "color", "space": "spacing", "radius": "radius", "shadow": "shadow", "elevation": "shadow"}
OWN_FAMILIES_MAX = 12                                        # своих семейств у артефакта (cd 05/01 §3.2)
GENERIC_FONTS = ("serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "emoji", "math", "fangsong",
                 "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded")
SYSTEM_FONTS = ("-apple-system", "blinkmacsystemfont", "segoe ui", "helvetica neue", "helvetica", "arial", "georgia",
                "times new roman", "times", "courier new", "courier", "verdana", "tahoma", "trebuchet ms", "menlo",
                "monaco", "consolas")                  # гарнитуры, которые стоят в системах: файла шрифта не требуют
FONT_WEIGHTS = {"thin": 100, "hairline": 100, "extra-light": 200, "ultra-light": 200, "light": 300, "normal": 400,
                "regular": 400, "book": 400, "medium": 500, "semi-bold": 600, "demi-bold": 600, "bold": 700,
                "extra-bold": 800, "ultra-bold": 800, "black": 900, "heavy": 900, "extra-black": 950,
                "ultra-black": 950}
ALIAS = re.compile(r"^\{([^{}]+)\}$")
NAME = re.compile(r"^[^$.{}][^.{}]*$")
FM = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
KIND = "design-system"


# ------------------------------------------------------------------ схема формата DTCG 2025.10

def _alias():
    return {"type": "string", "pattern": r"^\{[^{}]+\}$"}


def _v(t):
    return {"$ref": f"#/$defs/v-{t}"}


def _or_alias(schema):
    return {"anyOf": [{"$ref": "#/$defs/alias"}, schema]}


_LAYER = {"type": "object", "required": ["color", "offsetX", "offsetY", "blur", "spread"],
          "additionalProperties": False,
          "properties": {"color": _v("color"), "offsetX": _v("dimension"), "offsetY": _v("dimension"),
                         "blur": _v("dimension"), "spread": _v("dimension"), "inset": {"type": "boolean"}}}
_ROOT_NAME = r"^(?!example$)[^$.{}][^.{}]*$"                # в корне `example` — пометка иллюстрации, не токен
_NODE_NAME = r"^[^$.{}][^.{}]*$"
_META = {"$type": {"enum": list(TYPES)}, "$description": {"type": "string"}, "$extensions": {"type": "object"},
         "$deprecated": {"type": ["boolean", "string"]}}

DTCG_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "urn:app-design:design-deep-dive:dtcg-format:2025.10",
    "title": "Формат токенов DTCG 2025.10: группы, токены, форма $value по типу",
    "$ref": "#/$defs/root",
    "$defs": {
        "root": {"type": "object", "additionalProperties": False,
                 "properties": {"$schema": {"type": "string"}, "$description": {"type": "string"},
                                "$extensions": {"type": "object"}, "example": {"type": "boolean"}},
                 "patternProperties": {_ROOT_NAME: {"$ref": "#/$defs/node"}}},
        "node": {"if": {"type": "object", "required": ["$value"]}, "then": {"$ref": "#/$defs/token"},
                 "else": {"$ref": "#/$defs/group"}},
        "token": {"type": "object", "required": ["$value"], "additionalProperties": False,
                  "properties": dict(_META, **{"$value": {}})},
        "group": {"type": "object", "additionalProperties": False,
                  "properties": dict(_META, **{"$extends": {"$ref": "#/$defs/alias"}}),
                  "patternProperties": {_NODE_NAME: {"$ref": "#/$defs/node"}}},
        "alias": _alias(),
        "v-color": _or_alias({
            "type": "object", "required": ["colorSpace", "components"], "additionalProperties": False,
            "properties": {
                "colorSpace": {"enum": ["srgb", "srgb-linear", "hsl", "hwb", "lab", "lch", "oklab", "oklch",
                                        "display-p3", "a98-rgb", "prophoto-rgb", "rec2020", "xyz-d65", "xyz-d50"]},
                "components": {"type": "array", "minItems": 3, "maxItems": 3,
                               "items": {"anyOf": [{"type": "number"}, {"const": "none"}]}},
                "alpha": {"type": "number", "minimum": 0, "maximum": 1},
                "hex": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"}}}),
        "v-dimension": _or_alias({"type": "object", "required": ["value", "unit"], "additionalProperties": False,
                                  "properties": {"value": {"type": "number"}, "unit": {"enum": ["px", "rem"]}}}),
        "v-duration": _or_alias({"type": "object", "required": ["value", "unit"], "additionalProperties": False,
                                 "properties": {"value": {"type": "number"}, "unit": {"enum": ["ms", "s"]}}}),
        "v-fontFamily": _or_alias({"anyOf": [{"type": "string", "minLength": 1},
                                             {"type": "array", "minItems": 1,
                                              "items": {"type": "string", "minLength": 1}}]}),
        "v-fontWeight": _or_alias({"anyOf": [{"type": "number", "minimum": 1, "maximum": 1000},
                                             {"enum": sorted(FONT_WEIGHTS)}]}),
        "v-cubicBezier": _or_alias({"type": "array", "minItems": 4, "maxItems": 4,
                                    "prefixItems": [{"type": "number", "minimum": 0, "maximum": 1}, {"type": "number"},
                                                    {"type": "number", "minimum": 0, "maximum": 1},
                                                    {"type": "number"}]}),
        "v-number": _or_alias({"type": "number"}),
        "v-strokeStyle": _or_alias({"anyOf": [
            {"enum": ["solid", "dashed", "dotted", "double", "groove", "ridge", "outset", "inset"]},
            {"type": "object", "required": ["dashArray", "lineCap"], "additionalProperties": False,
             "properties": {"dashArray": {"type": "array", "items": _v("dimension")},
                            "lineCap": {"enum": ["round", "butt", "square"]}}}]}),
        "v-border": _or_alias({"type": "object", "required": ["color", "width", "style"], "additionalProperties": False,
                               "properties": {"color": _v("color"), "width": _v("dimension"),
                                              "style": _v("strokeStyle")}}),
        "v-transition": _or_alias({"type": "object", "required": ["duration", "delay", "timingFunction"],
                                   "additionalProperties": False,
                                   "properties": {"duration": _v("duration"), "delay": _v("duration"),
                                                  "timingFunction": _v("cubicBezier")}}),
        "v-shadow": _or_alias({"anyOf": [_LAYER, {"type": "array", "items": {"anyOf": [{"$ref": "#/$defs/alias"},
                                                                                        _LAYER]}}]}),
        "v-gradient": _or_alias({"type": "array", "items": {"anyOf": [{"$ref": "#/$defs/alias"}, {
            "type": "object", "required": ["color", "position"], "additionalProperties": False,
            "properties": {"color": _v("color"), "position": _or_alias({"type": "number", "minimum": 0,
                                                                        "maximum": 1})}}]}}),
        "v-typography": _or_alias({"type": "object", "additionalProperties": False,
                                   "required": ["fontFamily", "fontSize", "fontWeight", "letterSpacing", "lineHeight"],
                                   "properties": {"fontFamily": _v("fontFamily"), "fontSize": _v("dimension"),
                                                  "fontWeight": _v("fontWeight"), "letterSpacing": _v("dimension"),
                                                  "lineHeight": _v("number")}}),
    },
}
# тип подзначения составного токена — для сверки алиасов внутри значения
SUBTYPES = {"typography": {"fontFamily": "fontFamily", "fontSize": "dimension", "fontWeight": "fontWeight",
                           "letterSpacing": "dimension", "lineHeight": "number"},
            "border": {"color": "color", "width": "dimension", "style": "strokeStyle"},
            "transition": {"duration": "duration", "delay": "duration", "timingFunction": "cubicBezier"},
            "shadow": {"color": "color", "offsetX": "dimension", "offsetY": "dimension", "blur": "dimension",
                       "spread": "dimension"},
            "gradient": {"color": "color", "position": "number"}}


def _jsonschema():
    try:
        import jsonschema  # noqa: F401
        return jsonschema
    except ImportError as e:
        raise F.ToolError("нужен jsonschema: $DDD_HOME/venv/bin/python (scripts/install.sh)") from e


def _reexec_venv(script=None):
    """Без jsonschema в текущем Python — перезапуск утилиты script в Python окружения скилла (один раз)."""
    import importlib.util
    if importlib.util.find_spec("jsonschema") is not None:
        return
    py = kbpaths.python()
    in_venv = Path(sys.prefix).resolve() == kbpaths.venv().resolve()   # у venv python — ссылка на системный
    if os.environ.get("DDD_DS_VENV") or not Path(py).exists() or in_venv:
        return
    os.environ["DDD_DS_VENV"] = "1"
    os.execv(py, [py, str(Path(script or __file__).resolve())] + sys.argv[1:])


# ------------------------------------------------------------------ модель токенов

def esc(key):
    return str(key).replace("~", "~0").replace("/", "~1")


def pointer(path, *more):
    return "/" + "/".join(esc(p) for p in tuple(path) + more)


@dataclass
class Issue:
    pointer: str
    message: str
    severity: str = "error"
    fix: str = ""                                            # что сделать; пусто — правка токена по сообщению


@dataclass
class Token:
    path: tuple
    raw: dict
    type: str | None = None
    ancestors: list = field(default_factory=list)          # группы от корня к токену (словари)

    @property
    def name(self):
        """Имя CSS-переменной без «--» — путь через дефис."""
        return "-".join(self.path)

    @property
    def pointer(self):
        return pointer(self.path)

    @property
    def value(self):
        return self.raw.get("$value")

    @property
    def description(self):
        d = self.raw.get("$description")
        return d if isinstance(d, str) else ""

    def ext(self, key):
        e = self.raw.get("$extensions")
        return e.get(key) if isinstance(e, dict) else None

    def mode_entries(self):
        """[(режим, значение, место)]: `org.design-deep-dive.modes` и сокращённое движение расширения страниц."""
        out = []
        m = self.ext(EXT_MODES)
        if isinstance(m, dict):
            out += [(k, v, f"$extensions/{EXT_MODES}/{esc(k)}") for k, v in m.items()]
        r = self.ext(EXT_REDUCE)
        if r is not None and not any(k == REDUCED for k, _, _ in out):
            out.append((REDUCED, r, f"$extensions/{EXT_REDUCE}"))
        return out

    def modes(self):
        """{режим: значение} (`reduced` — и из расширения страниц)."""
        return {k: v for k, v, _ in self.mode_entries()}

    def art(self, key):
        """Поле артефакта: у токена, иначе у ближайшей группы (`$extensions.org.design-deep-dive.artifact`)."""
        for node in [self.raw] + list(reversed(self.ancestors)):
            e = node.get("$extensions") if isinstance(node, dict) else None
            a = e.get(EXT_ART) if isinstance(e, dict) else None
            if isinstance(a, dict) and key in a:
                return a[key]
        return None


class Tokens:
    """Разобранный файл токенов DTCG: токены по порядку документа, разрешение алиасов и режимов."""

    def __init__(self, data):
        self.data = data if isinstance(data, dict) else {}
        self.list = []
        self.by_path = {}
        self.groups = {}                                     # путь группы → словарь
        self.structure = []                                  # замечания обхода (не токен и не группа)
        self._walk(self.data, (), [], None)
        for t in self.list:
            if t.type is None:
                t.type = self._alias_type(t, set())

    def _walk(self, node, path, ancestors, inherited):
        for key, val in node.items():
            if key.startswith("$") or (not path and key == "example"):
                continue
            p = path + (key,)
            if not isinstance(val, dict):
                self.structure.append(Issue(pointer(p), f"`{'.'.join(p)}` — не токен и не группа: ожидается объект"))
                continue
            if "$value" in val:
                ty = val.get("$type") if val.get("$type") in TYPES else inherited
                t = Token(p, val, ty, list(ancestors))
                self.list.append(t)
                self.by_path[p] = t
            else:
                self.groups[p] = val
                ty = val.get("$type") if val.get("$type") in TYPES else inherited
                self._walk(val, p, ancestors + [val], ty)

    def get(self, ref):
        """Токен по пути `a.b.c` (или None)."""
        return self.by_path.get(tuple(str(ref).split(".")))

    def _alias_type(self, t, seen):
        m = ALIAS.match(t.value) if isinstance(t.value, str) else None
        if not m or t.path in seen:
            return None
        seen.add(t.path)
        target = self.get(m.group(1))
        if target is None:
            return None
        return target.type or self._alias_type(target, seen)

    # -- разрешение значений

    def in_mode(self, t, mode):
        if mode:
            modes = t.modes()
            if mode in modes:
                return modes[mode]
        return t.value

    def resolve(self, value, mode=None, stack=()):
        """Значение без алиасов: алиас → значение цели в том же режиме (транзитивно); составные — по частям.
        Алиас в пустоту или цикл — ValueError."""
        if isinstance(value, str):
            m = ALIAS.match(value)
            if m:
                ref = m.group(1)
                if ref in stack:
                    raise ValueError("цикл алиасов: " + " → ".join(stack + (ref,)))
                target = self.get(ref)
                if target is None:
                    raise ValueError(f"алиас {{{ref}}} ведёт в пустоту")
                return self.resolve(self.in_mode(target, mode), mode, stack + (ref,))
            return value
        if isinstance(value, dict):
            if "colorSpace" in value:                        # цвет — лист
                return value
            if set(value) == {"value", "unit"}:
                return value
            return {k: self.resolve(v, mode, stack) for k, v in value.items()}
        if isinstance(value, list):
            return [self.resolve(v, mode, stack) for v in value]
        return value

    def value(self, t, mode=None):
        return self.resolve(self.in_mode(t, mode), mode, (".".join(t.path),))

    def mode_names(self):
        out = []
        for t in self.list:
            for m in t.modes():
                if m not in out:
                    out.append(m)
        return out


def _root_modes(data):
    ext = data.get("$extensions") if isinstance(data, dict) else None
    return ext.get(EXT_MODES) if isinstance(ext, dict) else None


def token_themes(toks):
    """Темы токенов: тема значений `$value` (`modes.base`) и парная, если у токенов есть режим с её именем."""
    first = base_theme(toks.data)
    return {first} | ({THEME_PAIR[first]} if THEME_PAIR[first] in toks.mode_names() else set())


def _web_fonts(toks):
    """(семейство, токен, насыщенность) значений токенов fontFamily и типографических токенов во всех режимах, у
    которых первому имени стека нужен файл шрифта (`web_family`), — по порядку документа. Насыщенность — fontWeight
    типографического значения, у токена fontFamily — None. Значение, которое не разрешается, пропускается: его
    называет R-STRUCT-006."""
    for t in toks.list:
        if t.type not in ("fontFamily", "typography"):
            continue
        for mode in [None] + toks.mode_names():
            try:
                v = toks.value(t, mode)
            except ValueError:
                continue
            typo = t.type == "typography" and isinstance(v, dict)
            name = web_family(v.get("fontFamily") if typo else v)
            if name:
                yield name, t, weight_num(v.get("fontWeight")) if typo else None


def font_needs(data):
    """Начертания, которым нужен файл шрифта: {семейство: [насыщенности по возрастанию]} по порядку документа.
    Семейство — первое имя стека каждого токена fontFamily и fontFamily типографических токенов, если оно не родовое и
    не системное (GENERIC_FONTS, SYSTEM_FONTS); насыщенности — fontWeight типографических токенов этого семейства во
    всех режимах, числом; у семейства без типографического токена список пуст — ему нужен хотя бы один файл. Токен,
    значение которого не разрешается, пропускается: его называет R-STRUCT-006."""
    out = {}
    for name, _t, w in _web_fonts(Tokens(data)):
        weights = out.setdefault(name, [])
        if isinstance(w, (int, float)) and not isinstance(w, bool) and w not in weights:
            weights.append(w)
    return {name: sorted(ws) for name, ws in out.items()}


def web_families(data):
    """Семейства токенов, которым нужен файл шрифта (`font_needs`), — по порядку документа, без повторов."""
    return list(font_needs(data))


def web_family(stack):
    """Семейство стека, которому нужен файл шрифта: первое имя, если оно не родовое и не системное (GENERIC_FONTS,
    SYSTEM_FONTS); иначе None."""
    first = stack[0] if isinstance(stack, list) and stack else stack
    name = str(first or "").split(",")[0].strip().strip("'\"")
    return name if name and name.lower() not in GENERIC_FONTS + SYSTEM_FONTS else None


def family_key(name):
    """Ключ семейства по имени: строчными, каждый отрезок знаков вне латинских букв и цифр — один дефис, дефисы по
    краям срезаются (`Golos Text` → `golos-text`, `M+ 1p` → `m-1p`); переменная семейства — `--font-<ключ>`. Имя без
    латинских букв и цифр — пустой ключ: ключа у семейства нет."""
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")


def theme_gaps(prj, toks):
    """Темы брифов, которых нет у токенов (R-COV-010): [(поверхность или None, путь брифа, {темы брифа}, {темы
    токенов})] — бриф сайта каждой поверхности слоя страницы и бриф на вид кабинета (`brief_themes`) против темы
    значений и парной по режиму (`token_themes`)."""
    have = token_themes(toks)
    return [(surf, path, need, have) for surf, path, need in brief_themes(prj) if not need <= have]


def base_theme(data):
    """Тема значений `$value`: `base` корневого расширения режимов (`light` · `dark`); не объявлена — `light`."""
    m = _root_modes(data)
    b = m.get("base") if isinstance(m, dict) else None
    return b if isinstance(b, str) and b in THEMES else "light"


# ------------------------------------------------------------------ проверка формата (R-STRUCT-006)

def validate(data):
    """Замечания формата DTCG: структура схемой, тип каждого токена, форма значений по типу, алиасы, режимы."""
    js = _jsonschema()
    issues = []
    if not isinstance(data, dict):
        return [Issue("", "корень файла токенов — не объект JSON")]
    validator = js.Draft202012Validator(DTCG_SCHEMA)
    for e in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        issues.append(Issue(pointer(tuple(str(p) for p in e.absolute_path)), "форма DTCG: " + _schema_message(e)))
    m = _root_modes(data)
    if m is not None and not (isinstance(m, dict) and base_theme(data) == m.get("base", "light")):
        issues.append(Issue(pointer(("$extensions", EXT_MODES, "base")),
                            f"тема значений `$value` — `base` расширения режимов в корне: {' или '.join(THEMES)}"))
    toks = Tokens(data)
    issues += toks.structure
    value_validators = {t: js.Draft202012Validator({"$ref": f"#/$defs/v-{t}", "$defs": DTCG_SCHEMA["$defs"]})
                        for t in TYPES}
    for t in toks.list:
        if t.type is None:
            m = ALIAS.match(t.value) if isinstance(t.value, str) else None
            why = f"алиас {t.value} не даёт типа" if m else "нет $type у токена и у его групп"
            issues.append(Issue(t.pointer, f"`{'.'.join(t.path)}` — тип не определён: {why} (DTCG: тип не угадывают "
                                           "по значению)"))
            continue
        values = [(None, t.value, "$value")] + t.mode_entries()
        for mode, v, where in values:
            errs = list(value_validators[t.type].iter_errors(v))
            if errs:
                best = min(errs, key=lambda e: len(list(e.absolute_path)))
                issues.append(Issue(t.pointer + "/" + where,
                                    f"`{'.'.join(t.path)}` ({t.type}) — {where}: не по форме типа "
                                    f"({_schema_message(best)})"))
                continue
            issues += _alias_issues(toks, t, v, t.type, t.pointer + "/" + where, mode)
    tops = [k for k in data if not k.startswith("$") and k != "example"]
    for second in ("spacing", "spacer", "spaces"):
        if second in tops and "space" in tops:
            issues.append(Issue(pointer((second,)), f"вторая шкала отступов `{second}.*` рядом с `space.*`: шкала одна",
                                "warning"))
    issues += _extension_issues(data) + _base_mode_issues(toks) + _family_var_issues(toks) + _spring_issues(toks)
    return issues


def _extension_keys(node, path=()):
    """[(ключ `$extensions`, указатель)] корня, групп и токенов — по порядку документа."""
    ext = node.get("$extensions")
    out = [(k, pointer(path, "$extensions", k)) for k in ext] if isinstance(ext, dict) else []
    if "$value" not in node:
        for key, val in node.items():
            if isinstance(val, dict) and not key.startswith("$"):
                out += _extension_keys(val, path + (key,))
    return out


def _extension_issues(data):
    """Ключ `$extensions` вне известных сборке — предупреждение на ключ: его значения в производные не идут, и
    опечатка в имени или расширение под именем другого инструмента иначе проходит молча."""
    places = {}
    for key, ptr in _extension_keys(data):
        if key not in EXT_KNOWN:
            places.setdefault(key, []).append(ptr)
    known = " · ".join(k[len(EXT_SPACE):] for k in EXT_KNOWN)
    return [Issue(ptrs[0], f"расширение `{key}` — вне известных сборке (`{EXT_SPACE}` + {known}): его значения в "
                           f"производные не идут; мест — {len(ptrs)}", "warning",
                  f"расширение сборки — ключом `{EXT_SPACE}<имя>`; данные другого инструмента сборке не мешают")
            for key, ptrs in places.items()]


def _base_mode_issues(toks):
    """Режим токена с именем темы значений: CSS кладёт его в блок этой темы, артефакт берёт `$value` — одно
    предупреждение на файл."""
    first = base_theme(toks.data)
    same = [t for t in toks.list if first in t.modes()]
    if not same:
        return []
    names = ", ".join(".".join(t.path) for t in same[:3]) + (" …" if len(same) > 3 else "")
    return [Issue(same[0].pointer + f"/$extensions/{EXT_MODES}/{first}",
                  f"режим `{first}` совпадает с темой значений `$value`: токенов — {len(same)} ({names}); CSS кладёт "
                  f"значение режима в блок `[data-theme=\"{first}\"]`, артефакт берёт `$value`", "warning",
                  f"значение темы `{first}` — в `$value`, режим `{first}` снять; значения другой темы — режимом "
                  f"`{THEME_PAIR[first]}` или сменой `base` в корне")]


def _family_var_issues(toks):
    """Гарнитура, которую загрузчик шрифтов кода не подменит или подменит не той, — по предупреждению на случай:
    у имени семейства нет ключа или имя переменной семейства `--font-<ключ>` занято переменной токена (стек в
    производном CSS остаётся литералом — `family_css`); у двух семейств один ключ (их стеки ссылаются на одну
    переменную). Форму файла предупреждение не меняет."""
    taken = {n: t for t in toks.list for n in var_names(t)}
    first = {}
    for name, t, _w in _web_fonts(toks):
        first.setdefault(name, t)
    out, same = [], {}
    for name, t in first.items():
        key = family_key(name)
        if not key:
            out.append(Issue(t.pointer, f"у гарнитуры «{name}» нет ключа семейства — в имени нет латинских букв и "
                                        "цифр: в производном CSS её стек остаётся литералом, загрузчик шрифтов кода "
                                        "её не подменит", "warning",
                             "имя семейства в стеке — латиницей, как в файле шрифта и в `font.family` строки "
                             "манифеста"))
            continue
        same.setdefault(key, []).append(name)
        held = taken.get(f"font-{key}")
        if held is not None:
            out.append(Issue(held.pointer, f"переменная семейства `--font-{key}` гарнитуры «{name}» занята токеном "
                                           f"`{'.'.join(held.path)}`: в производном CSS стек гарнитуры остаётся "
                                           "литералом, загрузчик шрифтов кода её не подменит", "warning",
                             "токен гарнитуры называют ролью (`font.text`, `font.display`), а не семейством; "
                             "переименование токена меняет имя переменной в коде — решает владелец продукта"))
    for key, names in same.items():
        if len(names) > 1:
            out.append(Issue(first[names[1]].pointer,
                             f"у гарнитур {', '.join(f'«{n}»' for n in names)} один ключ семейства: их стеки "
                             f"ссылаются на одну переменную `--font-{key}`, загрузчик шрифтов кода объявит её одной "
                             "гарнитурой", "warning", "одно семейство — одно написание имени во всех токенах"))
    return out


def _ms(v):
    """Длительность DTCG → ms, до шести знаков: 0.34 s — ровно 340 (или None)."""
    if isinstance(v, dict) and isinstance(v.get("value"), (int, float)) and v.get("unit") in ("ms", "s"):
        return round(v["value"] * (1000 if v["unit"] == "s" else 1), 6)
    return None


def _spring_issues(toks):
    """Пружины (`org.design-deep-dive.spring`, ui 08/04 §1): форма — ошибка; нормы движения — предупреждения."""
    out = []
    for t in toks.list:
        sp = t.ext(EXT_SPRING)
        if sp is None:
            continue
        name, where = ".".join(t.path), t.pointer + f"/$extensions/{EXT_SPRING}"
        if t.type != "transition":
            out.append(Issue(where, f"`{name}` ({t.type}) — пружина читается только у токена transition: её кривая и "
                                    "время успокоения — одно значение",
                             fix="пружина — токеном transition: `$value` — переход-запас, параметры — в расширении"))
            continue
        if not isinstance(sp, dict):
            out.append(Issue(where, f"`{name}` — пружина: объект {{dampingRatio, stiffness}}"))
            continue
        bad = [k for k in SPRING_KEYS if not (isinstance(sp.get(k), (int, float)) and not isinstance(sp.get(k), bool)
                                              and math.isfinite(sp[k]) and sp[k] > 0)]
        extra = [k for k in sp if k not in SPRING_KEYS]
        if bad or extra:
            why = [f"{', '.join(bad)} — число больше нуля"] if bad else []
            why += [f"{', '.join(extra)} — вне формы пружины"] if extra else []
            out.append(Issue(where, f"`{name}` — пружина: {'; '.join(why)}",
                             fix="пружина — dampingRatio (ζ) и stiffness при массе 1; масса не пишется: при заданном ζ "
                                 "движение задаёт stiffness / mass (ui 08/04 §1.1, §2.1)"))
            continue
        c = spring_curve(*spring_of(t))
        warn = []
        if c.overshoot > SPRING_OVERSHOOT_MAX:
            warn.append((f"перелёт {num(round(c.overshoot * 100, 1))} % — больше {num(SPRING_OVERSHOOT_MAX * 100)} %: "
                         "так прыгает только приём подачи", "dampingRatio не меньше 0.6 (ui 08/01 §4.6)"))
        if c.settle_ms > SPRING_SETTLE_MAX_MS:
            warn.append((f"успокоение {c.settle_ms} ms — дольше {SPRING_SETTLE_MAX_MS} ms, потолка движения "
                         "интерфейса", "stiffness выше или dampingRatio ближе к 1 (ui 08/01 §1.3)"))
        if len(c.points) > SPRING_POINTS_MAX:
            warn.append((f"точек linear() {len(c.points)} — больше {SPRING_POINTS_MAX}: пружина слишком колебательная "
                         "для CSS", "dampingRatio ближе к 1"))
        try:
            have = _ms(toks.value(t).get("duration"))
            reduced = toks.value(t, REDUCED) if REDUCED in t.modes() else None
        except (ValueError, AttributeError):
            have, reduced = c.settle_ms, None                # значение не разрешается — замечание формата уже есть
        if have != c.settle_ms:
            warn.append((f"длительность `$value` {num(have)} ms, время успокоения пружины {c.settle_ms} ms: "
                         "инструменты без расширения покажут другое время",
                         f"`$value.duration` — {{\"value\": {c.settle_ms}, \"unit\": \"ms\"}}"))
        if REDUCED not in t.modes():
            warn.append(("нет значения сокращённого движения: при «уменьшить движение» пружина перелетит и закачается",
                         "режим reduced — переход без пружины: кривая входа, 150 ms (ui 08/03 §3.2)"))
        elif isinstance(reduced, dict) and isinstance(reduced.get("timingFunction"), list) and \
                any(not 0 <= y <= 1 for y in reduced["timingFunction"][1::2]):
            warn.append(("в значении сокращённого движения кривая с перелётом",
                         "кривая без перелёта: y обеих точек от 0 до 1 (ui 08/03 §3.2)"))
        if t.ext(EXT_CSS) is not None:
            warn.append((f"расширение `{EXT_CSS}` рядом с пружиной не читается: CSS токена даёт пружина",
                         f"снять `{EXT_CSS}`"))
        out += [Issue(where, f"`{name}` — пружина: {msg}", "warning", fix) for msg, fix in warn]
    return out


def _schema_message(e):
    msg = e.message
    if len(msg) > 160:
        msg = msg[:157] + "…"
    return msg


def _alias_issues(toks, t, value, ty, where, mode=None):
    """Алиасы значения: ведут в токен (не в группу и не в пустоту), тип цели = ожидаемый, без циклов в своём режиме."""
    out = []
    if isinstance(value, str):
        m = ALIAS.match(value)
        if not m:
            return out
        ref = m.group(1)
        target = toks.get(ref)
        if target is None:
            kind = "в группу" if tuple(ref.split(".")) in toks.groups else "в пустоту"
            out.append(Issue(where, f"`{'.'.join(t.path)}` — алиас {{{ref}}} ведёт {kind}"))
            return out
        if target.type and ty and target.type != ty:
            out.append(Issue(where, f"`{'.'.join(t.path)}` — алиас {{{ref}}}: тип цели {target.type}, нужен {ty}"))
        try:
            toks.resolve(value, mode, (".".join(t.path),))
        except ValueError as e:
            out.append(Issue(where, f"`{'.'.join(t.path)}` — {e}" + (f" (режим {mode})" if mode else "")))
        return out
    sub = SUBTYPES.get(ty)
    if sub and isinstance(value, dict):
        for k, v in value.items():
            if k in sub:
                out += _alias_issues(toks, t, v, sub[k], f"{where}/{k}", mode)
    elif sub and isinstance(value, list):
        for i, item in enumerate(value):
            if isinstance(item, dict):
                for k, v in item.items():
                    if k in sub:
                        out += _alias_issues(toks, t, v, sub[k], f"{where}/{i}/{k}", mode)
            else:
                out += _alias_issues(toks, t, item, ty, f"{where}/{i}", mode)
    return out


# ------------------------------------------------------------------ значения CSS

def num(x):
    """Число для CSS и JSON артефакта: целое без «.0», дробное — кратчайшей записью."""
    if isinstance(x, bool):
        return "1" if x else "0"
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        return str(int(x)) if x.is_integer() else repr(x)
    return str(x)


def dim(v):
    return f"{num(v['value'])}{v['unit']}"


def px_of(v):
    """dimension → px (rem по 16 px) или None."""
    if isinstance(v, dict) and isinstance(v.get("value"), (int, float)):
        return v["value"] * (REM_PX if v.get("unit") == "rem" else 1)
    return None


def color_css(v):
    if not isinstance(v, dict):
        return str(v)
    alpha = v.get("alpha")
    hexv = v.get("hex") or _hex_from(v)
    if alpha is not None and alpha < 1:
        if hexv:
            r, g, b = (int(hexv[i:i + 2], 16) for i in (1, 3, 5))
            return f"rgb({r} {g} {b} / {num(alpha)})"
        return _color_fn(v, alpha)
    return hexv or _color_fn(v, None)


def _hex_from(v):
    comps = v.get("components") or []
    if any(c == "none" for c in comps) or len(comps) != 3:
        return None
    space = v.get("colorSpace")
    if space == "srgb":
        return "#" + "".join(f"{max(0, min(255, round(c * 255))):02x}" for c in comps)
    if space == "oklch":
        sys.path.insert(0, str(HERE.parent / "lib"))
        from color import oklch2hex
        return oklch2hex(*comps)
    return None


def _color_fn(v, alpha):
    comps = " ".join(num(c) for c in v.get("components") or [])
    a = f" / {num(alpha)}" if alpha is not None and alpha < 1 else ""
    space = v.get("colorSpace")
    if space in ("oklch", "oklab", "lab", "lch", "hsl", "hwb"):
        return f"{space}({comps}{a})"
    return f"color({space} {comps}{a})"


def font_css(v):
    if isinstance(v, str):
        return v if "," in v or " " not in v else json.dumps(v)
    out = []
    for name in v:
        out.append(name if name in GENERIC_FONTS or " " not in name else json.dumps(name, ensure_ascii=False))
    return ", ".join(out)


def family_css(v, taken=None):
    """Стек гарнитуры в CSS. С `taken` — именами переменных, которые объявляет производный CSS, — стек семейства,
    которому нужен файл шрифта (`web_family`), идёт ссылкой на переменную семейства со стеком в запасе:
    `var(--font-<ключ>, <стек>)`. Переменную файл не объявляет: без загрузчика шрифтов действует стек, загрузчик кода
    объявляет её на `:root`. Ключа нет или имя занято переменной токена — стек литералом: ссылка на себя оставила бы
    переменную токена без значения."""
    stack = font_css(v)
    key = family_key(web_family(v) or "") if taken is not None else ""
    return f"var(--font-{key}, {stack})" if key and f"font-{key}" not in taken else stack


def weight_num(v):
    return FONT_WEIGHTS.get(v, v) if isinstance(v, str) else v


def bezier(v):
    return "cubic-bezier(" + ", ".join(num(x) for x in v) + ")"


def shadow_css(v):
    layers = v if isinstance(v, list) else [v]
    if not layers:
        return "none"
    out = []
    for layer in layers:
        s = f"{dim(layer['offsetX'])} {dim(layer['offsetY'])} {dim(layer['blur'])} {dim(layer['spread'])} " \
            f"{color_css(layer['color'])}"
        out.append(("inset " if layer.get("inset") else "") + s)
    return ", ".join(out)


def css_value(ty, v):
    """Разрешённое значение токена → строка CSS (ui 09/04 §5.1)."""
    if ty == "color":
        return color_css(v)
    if ty in ("dimension", "duration"):
        return dim(v)
    if ty == "fontFamily":
        return font_css(v)
    if ty == "fontWeight":
        return num(weight_num(v))
    if ty == "number":
        return num(v)
    if ty == "cubicBezier":
        return bezier(v)
    if ty == "strokeStyle":
        return v if isinstance(v, str) else "dashed"
    if ty == "border":
        return f"{dim(v['width'])} {css_value('strokeStyle', v['style'])} {color_css(v['color'])}"
    if ty == "transition":
        delay = "" if not v["delay"]["value"] else " " + dim(v["delay"])
        return f"{dim(v['duration'])} {bezier(v['timingFunction'])}{delay}"
    if ty == "shadow":
        return shadow_css(v)
    if ty == "gradient":
        stops = ", ".join(f"{color_css(s['color'])} {num(round(s['position'] * 100, 4))}%" for s in v)
        return f"linear-gradient({stops})"
    return json.dumps(v, ensure_ascii=False)


def _ext_css(t):
    """Готовое CSS-значение расширения страниц: fluid.css или css-строка / одно свойство."""
    fl = t.ext(EXT_FLUID)
    if isinstance(fl, dict) and isinstance(fl.get("css"), str):
        return fl["css"]
    c = t.ext(EXT_CSS)
    if isinstance(c, str):
        return c
    if isinstance(c, dict) and len(c) == 1 and isinstance(next(iter(c.values())), str):
        return next(iter(c.values()))
    return None


# ------------------------------------------------------------------ пружина (ui 08/04 §1)

@dataclass(frozen=True)
class SpringCurve:
    """Пружина в CSS: параметры, время успокоения и точки `linear()` — (доля времени 0…1, прогресс)."""
    ratio: float                                             # ζ, dampingRatio
    stiffness: float                                         # k при массе 1
    settle_ms: int                                           # время успокоения, вверх до SPRING_STEP_MS
    points: tuple

    @property
    def omega(self):
        """Собственная частота ω = √k, рад/с."""
        return math.sqrt(self.stiffness)

    @property
    def response(self):
        """Период колебания без трения 2π/ω, с: `response` и `duration` пружины SwiftUI."""
        return 2 * math.pi / self.omega

    @property
    def bounce(self):
        """`bounce` пружины SwiftUI: 1 − ζ у пружины с отскоком и без, 1/ζ − 1 у передемпфированной (меньше нуля)."""
        return 1 - self.ratio if self.ratio <= 1 else 1 / self.ratio - 1

    @property
    def overshoot(self):
        """Перелёт кривой физики: exp(−πζ/√(1−ζ²)) доли пути; при ζ ≥ 1 перелёта нет."""
        z = self.ratio
        return math.exp(-math.pi * z / math.sqrt(1 - z * z)) if z < 1 else 0.0

    @property
    def css(self):
        """`linear(0, p₁ t₁%, …, 1)`: у промежуточных точек — доля времени в процентах."""
        last = len(self.points) - 1
        return "linear(" + ", ".join("0" if i == 0 else "1" if i == last else f"{num(v)} {num(round(u * 100, 2))}%"
                                     for i, (u, v) in enumerate(self.points)) + ")"


def spring_step(ratio, omega):
    """Кривая пружины x(t), с: старт в покое в 0, цель 1, масса 1 — решение x″ + 2ζωx′ + ω²(x − 1) = 0."""
    z, w = ratio, omega
    if abs(z - 1) < 1e-6:
        return lambda t: 1 - (1 + w * t) * math.exp(-w * t)
    if z < 1:
        wd = w * math.sqrt(1 - z * z)
        return lambda t: 1 - math.exp(-z * w * t) * (math.cos(wd * t) + z * w / wd * math.sin(wd * t))
    s = math.sqrt(z * z - 1)
    r1, r2 = -w * (z - s), -w * (z + s)
    return lambda t: 1 + (r1 * math.exp(r2 * t) - r2 * math.exp(r1 * t)) / (r2 - r1)


def spring_settle(ratio, omega, band=SPRING_SETTLE):
    """Время успокоения, с: последний выход кривой из полосы ±band вокруг цели — дальше она в полосе навсегда."""
    x = spring_step(ratio, omega)
    if ratio < 1:                                            # огибающая отклонения колебательной пружины
        bound = lambda t: math.exp(-ratio * omega * t) / math.sqrt(1 - ratio * ratio)  # noqa: E731
    else:                                                    # без колебаний отклонение убывает само
        bound = lambda t: abs(1 - x(t))  # noqa: E731
    hi = 1 / omega
    while bound(hi) > band:
        hi *= 1.5
    n = 4000
    out = next((i for i in range(n, -1, -1) if abs(x(hi * i / n) - 1) > band), None)
    if out is None:
        return 0.0
    lo, up = hi * out / n, hi * (out + 1) / n
    for _ in range(50):
        mid = (lo + up) / 2
        lo, up = (mid, up) if abs(x(mid) - 1) > band else (lo, mid)
    return up


def spring_target(ratio, omega, duration):
    """Кривая для `linear()` на [0, duration]: пружина, у которой остаток до цели в конце (не больше SPRING_SETTLE)
    выбран плавно на последней четверти времени — конец без скачка и с нулевым остатком."""
    x = spring_step(ratio, omega)
    rest, start = 1 - x(duration), duration * (1 - SPRING_TAIL)

    def f(t):
        v = x(t)
        if t > start:
            s = (t - start) / (duration - start)
            v += rest * s * s * (3 - 2 * s)
        return v
    return f


def _thin(us, xs, eps):
    """Индексы точек ломаной, которая отходит от выборки не больше eps по вертикали (Рамер — Дуглас — Пекер)."""
    keep, stack = {0, len(us) - 1}, [(0, len(us) - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        k = (xs[b] - xs[a]) / (us[b] - us[a])
        worst, at = max((abs(xs[i] - xs[a] - k * (us[i] - us[a])), i) for i in range(a + 1, b))
        if worst > eps:
            keep.add(at)
            stack += [(a, at), (at, b)]
    return sorted(keep)


@functools.lru_cache(maxsize=None)
def spring_curve(ratio, stiffness):
    """Пружина в CSS: время успокоения до SPRING_SETTLE (вверх до SPRING_STEP_MS) и точки `linear()`, прореженные до
    SPRING_THIN; запись — прогресс тремя знаками, доля времени четырьмя (проценты двумя)."""
    omega = math.sqrt(stiffness)
    settle = spring_settle(ratio, omega)
    ms = max(SPRING_STEP_MS, math.ceil(round(settle * 1000, 6) / SPRING_STEP_MS) * SPRING_STEP_MS)
    f = spring_target(ratio, omega, ms / 1000)
    us = [i / SPRING_SAMPLES for i in range(SPRING_SAMPLES + 1)]
    xs = [f(u * ms / 1000) for u in us]
    xs[0], xs[-1] = 0.0, 1.0
    pts = [(round(us[i], 4), round(xs[i], 3)) for i in _thin(us, xs, SPRING_THIN)]
    pts[0], pts[-1] = (0.0, 0.0), (1.0, 1.0)
    return SpringCurve(float(ratio), float(stiffness), ms, tuple(pts))


def spring_of(t):
    """(ζ, k) пружины токена transition — `$extensions["org.design-deep-dive.spring"]` с `dampingRatio` и
    `stiffness` больше нуля; иначе None (форму расширения называет validate)."""
    sp = t.ext(EXT_SPRING)
    if t.type != "transition" or not isinstance(sp, dict):
        return None
    vals = [sp.get(k) for k in SPRING_KEYS]
    if all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and v > 0 for v in vals):
        return float(vals[0]), float(vals[1])
    return None


def spring_source(toks, t, mode=None):
    """Токен, чья пружина задаёт значение t в режиме mode: сам t или цель его алиаса целиком; значение режима по пути
    — переход без пружины (None)."""
    seen = set()
    while t is not None and t.path not in seen:
        seen.add(t.path)
        if mode and mode in t.modes():
            return None
        if t.ext(EXT_SPRING) is not None:
            return t if spring_of(t) else None
        m = ALIAS.match(t.value) if isinstance(t.value, str) else None
        t = toks.get(m.group(1)) if m else None
    return None


def spring_css(toks, src):
    """CSS пружины токена src: `<время успокоения>ms linear(…)` и задержка `$value`."""
    curve = spring_curve(*spring_of(src))
    delay = toks.value(src)["delay"]
    return f"{curve.settle_ms}ms {curve.css}" + ("" if not delay["value"] else " " + dim(delay))


def spring_fields(curve):
    """Параметры пружины для кода (`x-springs` передней части, `show`): форма токена, SwiftUI, перелёт, время CSS."""
    return {"dampingRatio": curve.ratio, "stiffness": curve.stiffness, "response": round(curve.response, 4),
            "bounce": round(curve.bounce, 4), "overshoot": round(curve.overshoot, 4), "settle": f"{curve.settle_ms}ms"}


def spring_note(toks, t, src):
    """Комментарий CSS над переменной пружины: параметры, по которым её пересобирают."""
    c = spring_curve(*spring_of(src))
    whose = "" if src is t else f" токена {'.'.join(src.path)}"
    return (f"пружина{whose}: dampingRatio {num(c.ratio)}, stiffness {num(c.stiffness)} (масса 1, ω "
            f"{c.omega:.2f} рад/с), перелёт {num(round(c.overshoot * 100, 1))} %, успокоение до 1 % пути — "
            f"{c.settle_ms} ms")


def _dec(x):
    return Decimal(str(x))


def whole_leading(ratio, size):
    """Целый px интерлиньяжа, если отношение × кегль отличается от него меньше шага раскладки; иначе None."""
    p = _dec(ratio) * _dec(size)
    whole = p.to_integral_value(rounding=ROUND_HALF_EVEN)
    return int(whole) if abs(p - whole) * LAYOUT_STEP < 1 else None


def leading_px(ratio, size):
    """Высота строки в браузере: отношение × кегль, усечённое до шага раскладки."""
    return (_dec(ratio) * _dec(size) * LAYOUT_STEP).to_integral_value(rounding=ROUND_FLOOR) / LAYOUT_STEP


def ready_leading(t):
    """Готовый интерлиньяж CSS токена — `line_height_css` расширения резинового кегля (выражение от кегля) или None."""
    fl = t.ext(EXT_FLUID)
    css = fl.get("line_height_css") if isinstance(fl, dict) else None
    return css.strip() if isinstance(css, str) and css.strip() else None


def leading_css(v, t=None):
    """Интерлиньяж CSS: у токена t с готовым выражением `line_height_css` — оно; иначе число DTCG, а если оно
    недотягивает до целого px, который записывает (отношение округлено вниз), — наименьшее отношение той же точности,
    которое этот px даёт. Округление вверх, а не точная дробь: браузер хранит множитель с одинарной точностью, и после
    усечения до шага точная дробь тоже теряет px (20 / 15)."""
    ready = ready_leading(t) if t is not None else None
    if ready:
        return ready
    ratio, size = v["lineHeight"], px_of(v["fontSize"])
    if not size or isinstance(ratio, bool) or not isinstance(ratio, (int, float)):
        return num(ratio)
    whole = whole_leading(ratio, size)
    if whole is None or leading_px(ratio, size) == whole:
        return num(ratio)
    up = (Decimal(whole) / _dec(size)).quantize(Decimal(1).scaleb(-RATIO_DIGITS), rounding=ROUND_CEILING)
    return format(up.normalize(), "f")


def tracking_em(t, v):
    """Трекинг в em у стиля с резиновым кеглем: `letter_spacing_em` расширения fluid, иначе px значения / кегль
    значения — у кегля из готового CSS. None — кегль постоянный или трекинга нет: остаётся px значения."""
    fl = t.ext(EXT_FLUID)
    em = fl.get("letter_spacing_em") if isinstance(fl, dict) else None
    if isinstance(em, bool) or not isinstance(em, (int, float)):
        size, px = px_of(v["fontSize"]), px_of(v["letterSpacing"])
        if _ext_css(t) is None or not size or px is None:
            return None
        em = round(px / size, RATIO_DIGITS)
    return em or None


def tracking_css(t, v):
    em = tracking_em(t, v)
    return css_value("dimension", v["letterSpacing"]) if em is None else f"{num(em)}em"


TYPO_PARTS = (("family", "fontFamily"), ("size", "fontSize"), ("leading", "lineHeight"), ("weight", "fontWeight"),
              ("tracking", "letterSpacing"))


def var_names(t):
    """Имена переменных токена без «--»: у типографического — пять, по частям."""
    return [f"{t.name}-{suffix}" for suffix, _ in TYPO_PARTS] if t.type == "typography" else [t.name]


def token_vars(toks, t, mode=None, taken=None):
    """[(имя переменной, значение CSS)] токена в режиме; типографический токен — пять переменных. С `taken` (имена
    переменных производного CSS) гарнитура идёт в его форме — `family_css`."""
    v = toks.value(t, mode)
    if t.type == "typography":
        sub = SUBTYPES["typography"]
        out = []
        own = mode is None or mode not in t.modes()          # своё значение режима расширениями кегля не правится
        fluid = _ext_css(t) if own else None
        for suffix, key in TYPO_PARTS:
            if key == "fontSize" and fluid:
                val = fluid
            elif key == "lineHeight":
                val = leading_css(v, t if own else None)
            elif key == "letterSpacing" and own:
                val = tracking_css(t, v)
            elif key == "fontFamily":
                val = family_css(v[key], taken)
            else:
                val = css_value(sub[key], v[key])
            out.append((f"{t.name}-{suffix}", val))
        return out
    src = spring_source(toks, t, mode) if t.type == "transition" else None
    if src is not None:
        return [(t.name, spring_css(toks, src))]
    if mode is None or mode not in t.modes():
        ext = _ext_css(t)
        if ext is not None and (mode is None or toks.in_mode(t, mode) == t.value):
            return [(t.name, ext)]
    return [(t.name, family_css(v, taken) if t.type == "fontFamily" else css_value(t.type, v))]


def typography_issues(toks):
    """Типографика CSS против значения DTCG при кегле значения: высота строки в браузере — целый px интерлиньяжа,
    трекинг в em × кегль — px трекинга. Расхождение — замечание: в CSS уходит не то, что записано в `$value`.
    Готовый интерлиньяж `line_height_css` — выражение от кегля, с числом значения он не сверяется."""
    out = []
    for t in toks.list:
        if t.type != "typography":
            continue
        try:
            v = toks.value(t)
            size, track, em = px_of(v["fontSize"]), px_of(v["letterSpacing"]), tracking_em(t, v)
            lead = dict(token_vars(toks, t))[f"{t.name}-leading"]
            whole = whole_leading(v["lineHeight"], size) if size and ready_leading(t) is None else None
            shown = leading_px(lead, size) if whole is not None else None
        except (ValueError, KeyError, TypeError, ArithmeticError):
            continue                                         # значение не по форме — замечание формата уже есть
        name = ".".join(t.path)
        if whole is not None and shown != whole:
            out.append(Issue(t.pointer + "/$value/lineHeight",
                             f"`{name}` — интерлиньяж: в CSS {lead} × {num(size)} px даёт в браузере "
                             f"{num(float(shown))} px, в значении — {whole} px", "warning"))
        if em is not None and size and track is not None and abs(em * size - track) > TRACKING_TOL_PX:
            out.append(Issue(t.pointer + "/$value/letterSpacing",
                             f"`{name}` — трекинг: в CSS {num(em)}em × {num(size)} px = {num(round(em * size, 4))} px, "
                             f"в значении — {num(track)} px", "warning"))
    return out


# ------------------------------------------------------------------ узкая ширина (NU-15)

def narrow(toks):
    """{"below": граница, "breakpoint": путь, "size": значение, "base": значение} — если основной текст type.body
    ниже первой границы надо поднять до минимума; иначе None. Нет границ или type.body — None."""
    body = toks.get("type.body")
    bps = [t for t in toks.list if t.path[0] == "breakpoint" and t.type == "dimension"]
    if body is None or body.type != "typography" or not bps:
        return None
    try:
        size = toks.value(body)["fontSize"]
        first = min(bps, key=lambda t: px_of(toks.value(t)) or 0)
        first_v = toks.value(first)
    except (ValueError, KeyError, TypeError):
        return None
    base_px = px_of(size)
    if base_px is None or base_px >= NARROW_BODY_MIN_PX:
        return None
    unit = size.get("unit", "px")
    target = {"value": NARROW_BODY_MIN_PX / REM_PX if unit == "rem" else NARROW_BODY_MIN_PX, "unit": unit}
    return {"below": dim(first_v), "breakpoint": ".".join(first.path), "size": dim(target), "base": dim(size)}


# ------------------------------------------------------------------ system.tokens.css

CSS_HEAD = ("/* Производный файл: собирает scripts/project/ds_build.py из system.tokens.json — руками не правится.\n"
            "   Имя переменной — путь токена DTCG через дефис; алиасы разрешены до значения. */\n")


def build_css(toks):
    taken = {n for t in toks.list for n in var_names(t)}
    base, notes = [], {}
    for t in toks.list:
        base += token_vars(toks, t, taken=taken)
        src = spring_source(toks, t) if t.type == "transition" else None
        if src is not None:
            notes[t.name] = spring_note(toks, t, src)
    base_map = dict(base)
    modes = toks.mode_names()
    themes = [m for m in modes if m not in DENSITY and m != REDUCED]
    first = base_theme(toks.data)
    pair = THEME_PAIR[first]
    two = pair in themes
    lines = [CSS_HEAD, ":root {", f"  color-scheme: {f'{first} {pair}' if two else first};"]
    for n, v in base:
        lines += ([f"  /* {notes[n]} */"] if n in notes else []) + [f"  {_var(n)}: {v};"]
    lines.append("}")

    def block(mode):
        out = []
        for t in toks.list:
            for n, v in token_vars(toks, t, mode, taken):
                if base_map.get(n) != v:
                    out.append((n, v))
        return out

    nar = narrow(toks)
    if nar:
        lines += ["", f"/* Узкая ширина: ниже {nar['breakpoint']} основной текст не меньше {NARROW_BODY_MIN_PX} px "
                      "(ux 09/03 §7.1). */",
                  f"@media (width < {nar['below']}) {{", "  :root {", f"    --type-body-size: {nar['size']};", "  }",
                  "}"]
    if two and not (first in themes and block(first)):
        lines += ["", f"/* Тема «{THEMES[first]}» ({first}) — тема значений: под атрибутом — её color-scheme, иначе "
                      "системные элементы остаются в теме системы. */",
                  f':root[data-theme="{first}"] {{', f"  color-scheme: {first};", "}"]
    for mode in themes:
        rows = block(mode)
        if not rows:
            continue
        label = THEMES.get(mode, mode)
        lines += ["", f"/* Тема «{label}» ({mode}): на :root, где объявлены переменные, иначе алиасы "
                      "не пересчитаются. */"]
        if mode == pair:
            lines += [f"@media (prefers-color-scheme: {mode}) {{", f'  :root:not([data-theme="{first}"]) {{',
                      f"    color-scheme: {mode};"] + [f"    {_var(n)}: {v};" for n, v in rows] + ["  }", "}", ""]
        lines += [f':root[data-theme="{mode}"] {{'] + ([f"  color-scheme: {mode};"] if mode in THEMES else []) + \
                 [f"  {_var(n)}: {v};" for n, v in rows] + ["}"]
    if REDUCED in modes:
        rows = block(REDUCED)
        if rows:
            lines += ["", "/* Сокращённое движение: только токены движения; выбор посетителя data-motion сильнее "
                          "системы в обе стороны. */",
                      "@media (prefers-reduced-motion: reduce) {",
                      '  :root:not([data-motion="full"]) {'] + [f"    {_var(n)}: {v};" for n, v in rows] + \
                     ["  }", "}", "", ':root[data-motion="reduced"] {'] + \
                     [f"  {_var(n)}: {v};" for n, v in rows] + ["}"]
    for mode in DENSITY:
        if mode in modes:
            rows = block(mode)
            if rows:
                lines += ["", f"/* Плотность {mode}: переопределяются роли, режим включается и на поддереве. */",
                          f'[data-density="{mode}"] {{'] + [f"  {_var(n)}: {v};" for n, v in rows] + ["}"]
    return "\n".join(lines) + "\n"


def _var(name):
    return "--" + name


# ------------------------------------------------------------------ передняя часть DESIGN.md

def _y(v):
    """Скаляр YAML: числа как есть, строки — в двойных кавычках (JSON-запись — допустимая строка YAML)."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return num(v)
    return json.dumps(str(v), ensure_ascii=False)


def _typo(toks, t, mode=None):
    v = toks.value(t, mode)
    return {"fontFamily": css_value("fontFamily", v["fontFamily"]), "fontSize": _ext_css(t) or dim(v["fontSize"]),
            "fontWeight": weight_num(v["fontWeight"]), "lineHeight": v["lineHeight"],
            "letterSpacing": tracking_css(t, v)}


def in_artifact(t):
    return t.path[0] != "primitive"


def front_matter(toks, name, description):
    colors, typo, rounded, spacing, other, springs = {}, {}, {}, {}, {}, {}
    for t in toks.list:
        if not in_artifact(t):
            continue
        src = spring_source(toks, t) if t.type == "transition" else None
        if src is not None:
            springs[t.name] = spring_fields(spring_curve(*spring_of(src)))
        if t.type == "color":
            colors[t.name] = token_vars(toks, t)[0][1]
        elif t.type == "typography":
            typo[t.name] = _typo(toks, t)
        elif t.path[0] == "radius" and t.type == "dimension":
            rounded[t.name] = token_vars(toks, t)[0][1]
        elif t.path[0] == "space" and t.type == "dimension":
            spacing[t.name] = token_vars(toks, t)[0][1]
        else:
            for n, v in token_vars(toks, t):
                other[n] = v
    modes = {}
    for mode in toks.mode_names():
        rows = {}
        for t in toks.list:
            if not in_artifact(t):
                continue
            for (n, v), (_, b) in zip(token_vars(toks, t, mode), token_vars(toks, t)):
                if v != b:
                    rows[n] = v
        if rows:
            modes[mode] = rows
    lines = ["---", "version: alpha", f"name: {_y(name)}", f"description: {_y(description)}"]

    def section(title, d, nested=False):
        if not d:
            return
        lines.append(f"{title}:")
        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"  {k}:")
                for k2, v2 in v.items():
                    if isinstance(v2, dict):
                        lines.append(f"    {k2}:")
                        lines.extend(f"      {k4}: {_y(v4)}" for k4, v4 in v2.items())
                    else:
                        lines.append(f"    {k2}: {_y(v2)}")
            else:
                lines.append(f"  {k}: {_y(v)}")

    section("colors", colors)
    section("typography", typo)
    section("rounded", rounded)
    section("spacing", spacing)
    section("x-tokens", other)
    section("x-springs", springs)
    section("x-modes", modes)
    nar = narrow(toks)
    if nar:
        section("x-narrow", {"below": nar["below"], "type-body": {"fontSize": nar["size"]}})
    lines.append("---")
    return "\n".join(lines) + "\n"


def with_front_matter(text, fm):
    m = FM.match(text)
    if m:
        return fm + text[m.end():]
    return fm + ("" if text.startswith("\n") else "\n") + text


def prose(text):
    """Проза DESIGN.md без передней части и начальных пустых строк."""
    m = FM.match(text)
    body = text[m.end():] if m else text
    return body.lstrip("\n")


def title_of(text):
    for line in prose(text).splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1)
    return None


# ------------------------------------------------------------------ артефакт Design System

def family_of(t):
    """Семейство токена в tokens.json артефакта или None (не идёт в артефакт)."""
    if not in_artifact(t) or t.type in MOTION_TYPES or t.path[0].startswith("motion"):
        return None
    explicit = t.art("family")
    if isinstance(explicit, str) and explicit:
        return explicit
    if t.type == "color":
        return "color"
    if t.type == "typography":
        return "type"
    if t.type == "fontFamily" and t.path[0] == "font":
        return "font"
    if t.type == "shadow":
        return "shadow"
    return FAMILY_OF_GROUP.get(t.path[0], t.path[0])


def font_key(t):
    """Ключ `type.families` для токена гарнитуры: переменная артефакта — `--font-<ключ>`."""
    p = list(t.path)
    if p[0] == "font":
        return "-".join(p[1:]) or p[0]
    if "family" in p and p.index("family") < len(p) - 1:
        return "-".join(p[p.index("family") + 1:])
    return p[-1]


def artifact_tokens(toks, name, example=False):
    """tokens.json артефакта: имя, версия, источник, семейства по порядку первого появления."""
    art_root = (toks.data.get("$extensions") or {}).get(EXT_ART) if isinstance(toks.data.get("$extensions"),
                                                                                dict) else None
    art_root = art_root if isinstance(art_root, dict) else {}
    notes = {k: (v or {}).get("note") for k, v in (art_root.get("families") or {}).items() if isinstance(v, dict)}
    doc = {"name": name}
    if example:
        doc["example"] = True
    doc.update({"version": 1, "meta": {"source": "system.tokens.json (DTCG) — сборка ds_build"}})
    order, fam_tokens = [], {}
    for t in toks.list:
        f = family_of(t)
        if f is None:
            continue
        f = "type" if f == "font" else f
        if f not in fam_tokens:
            order.append(f)
            fam_tokens[f] = []
        fam_tokens[f].append(t)
    first = base_theme(toks.data)
    themes = [first] + [m for m in toks.mode_names() if m not in DENSITY and m != REDUCED and m != first]
    for f in order:
        ts = fam_tokens[f]
        if f == "color":
            doc["color"] = {"themes": [{"id": m, "name": THEMES.get(m, m)} for m in themes],
                            "tokens": [{"name": t.name,
                                        "value": {m: token_vars(toks, t, None if m == first else m)[0][1]
                                                  for m in themes},
                                        "usage": t.description} for t in ts]}
        elif f == "type":
            doc["type"] = _type_family(toks, ts)
        else:
            body = {}
            note = notes.get(f) or _group_note(toks, f)
            if note:
                body["note"] = note
            body["tokens"] = [{"name": n, "value": v, "usage": t.description}
                              for t in ts for n, v in token_vars(toks, t)]
            doc[f] = body
    return doc


def _group_note(toks, family):
    for g, f in FAMILY_OF_GROUP.items():
        if f == family and (g,) in toks.groups:
            d = toks.groups[(g,)].get("$description")
            if isinstance(d, str) and d:
                return d
    if (family,) in toks.groups:
        d = toks.groups[(family,)].get("$description")
        if isinstance(d, str) and d:
            return d
    return None


def _type_family(toks, ts):
    families, groups, keyed = {}, [], {}
    fonts = [t for t in ts if t.type == "fontFamily"]
    for t in fonts:
        families[font_key(t)] = css_value("fontFamily", toks.value(t))
    for t in ts:
        if t.type != "typography":
            continue
        v = toks.value(t)
        fam_ref = t.value.get("fontFamily") if isinstance(t.value, dict) else None
        m = ALIAS.match(fam_ref) if isinstance(fam_ref, str) else None
        key = None
        if m and toks.get(m.group(1)) is not None:
            key = font_key(toks.get(m.group(1)))
            families.setdefault(key, css_value("fontFamily", v["fontFamily"]))
        else:
            stack = css_value("fontFamily", v["fontFamily"])
            key = next((k for k, s in families.items() if s == stack), None)
            if key is None:
                key = family_key(v["fontFamily"][0] if isinstance(v["fontFamily"], list) else stack.split(",")[0])
                families[key] = stack
        gname = t.art("group") if isinstance(t.art("group"), str) else None
        if not gname:
            gname = families[key].split(",")[0].strip().strip('"')
        if (gname, key) not in keyed:
            keyed[(gname, key)] = {"name": gname, "family": key, "styles": []}
            groups.append(keyed[(gname, key)])
        style = {"name": "-".join(t.path[1:]) if t.path[0] == "type" and len(t.path) > 1 else t.name,
                 "fontSize": _ext_css(t) or dim(v["fontSize"]), "lineHeight": v["lineHeight"],
                 "fontWeight": weight_num(v["fontWeight"])}
        sample = t.art("sample")
        if isinstance(sample, str) and sample:
            style["sample"] = sample
        style["usage"] = t.description
        keyed[(gname, key)]["styles"].append(style)
    out = {"families": families}
    if groups:
        out["groups"] = groups
    return out


INLINE_LISTS = ("tokens", "themes", "styles")


def _inline(v):
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{json.dumps(k, ensure_ascii=False)}: {_inline(x)}" for k, x in v.items()) + " }" \
            if v else "{}"
    if isinstance(v, list):
        return "[" + ", ".join(_inline(x) for x in v) + "]"
    return json.dumps(v, ensure_ascii=False)


def dump_artifact(obj):
    """JSON артефакта: записи списков tokens, themes, styles — строкой на запись, остальное — с отступом 2."""

    def pretty(v, ind, key=None):
        pad = "  " * ind
        if isinstance(v, dict):
            if not v:
                return "{}"
            items = [f"{pad}  {json.dumps(k, ensure_ascii=False)}: {pretty(x, ind + 1, k)}" for k, x in v.items()]
            return "{\n" + ",\n".join(items) + f"\n{pad}}}"
        if isinstance(v, list):
            if not v:
                return "[]"
            items = [f"{pad}  {_inline(x) if key in INLINE_LISTS else pretty(x, ind + 1)}" for x in v]
            return "[\n" + ",\n".join(items) + f"\n{pad}]"
        return json.dumps(v, ensure_ascii=False)

    return pretty(obj, 0) + "\n"


def readme(design_md_text, slug):
    return (f"<!-- Производный файл: собирает ds_build из docs/projects/{slug}/design/DESIGN.md — правка в прозе ДС, "
            "не здесь. -->\n\n" + prose(design_md_text).rstrip("\n") + "\n")


def readme_fresh(disk, built):
    """README на диске равен сборке или продолжает её с новой строки: собранная часть сверяется по началу файла, а
    хвост, который дописывает страница артефакта, не сверяется — его текст меняется вместе с типом артефакта."""
    if disk == built:
        return True
    head = built.rstrip("\n")
    return disk.startswith(head) and disk[len(head):].startswith("\n")


# ------------------------------------------------------------------ сборка проекта

@dataclass
class Project:
    slug: str
    repo: Path
    tokens_path: Path
    css_path: Path
    design_md_path: Path
    art_dir: Path
    brand_path: Path

    @classmethod
    def of(cls, slug, repo):
        d = lambda key: docpaths.design(slug, key, repo=repo)  # noqa: E731
        return cls(slug, repo, d("tokens"), d("tokens-css"), d("design-md"), d("ds-project"), d("brand"))

    @property
    def art_tokens(self):
        return self.art_dir / "tokens.json"

    @property
    def art_readme(self):
        return self.art_dir / "README.md"

    def rel(self, p):
        return docpaths.rel(p, self.repo)


def load_tokens(path):
    """(данные, ошибка): JSON файла токенов."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), None
    except (OSError, UnicodeDecodeError) as e:
        return None, f"файл не читается: {e}"
    except ValueError as e:
        return None, f"не JSON: {e}"


def ds_name(toks, prj):
    art = (toks.data.get("$extensions") or {}).get(EXT_ART) if isinstance(toks.data.get("$extensions"), dict) else None
    if isinstance(art, dict) and isinstance(art.get("name"), str) and art["name"]:
        return art["name"]
    if prj.design_md_path.is_file():
        t = title_of(prj.design_md_path.read_text(encoding="utf-8"))
        if t:
            return t
    if prj.brand_path.is_file():
        try:
            import yaml
            b = yaml.safe_load(prj.brand_path.read_text(encoding="utf-8")) or {}
            if isinstance(b, dict) and isinstance(b.get("name"), str) and not b["name"].startswith("<"):
                return b["name"]
        except Exception:                                     # noqa: BLE001 — битый бренд проверяет его аудит
            pass
    return prj.slug


def derive(prj, data):
    """{путь: текст} производных из разобранных токенов; DESIGN.md — только если проза есть."""
    toks = Tokens(data)
    name = ds_name(toks, prj)
    desc = data.get("$description") if isinstance(data.get("$description"), str) else ""
    out = {prj.css_path: build_css(toks),
           prj.art_tokens: dump_artifact(artifact_tokens(toks, name, example=data.get("example") is True))}
    if prj.design_md_path.is_file():
        text = prj.design_md_path.read_text(encoding="utf-8")
        out[prj.design_md_path] = with_front_matter(text, front_matter(toks, name, desc))
        out[prj.art_readme] = readme(text, prj.slug)
    return out, toks


def brief_themes(prj):
    """Темы, которых ждут брифы продукта: [(поверхность или None, путь, {темы})] — бриф сайта каждой поверхности слоя
    страницы и бриф на вид кабинета, блок `themes`: две темы — `dark.needed` или `default: system`, иначе одна —
    `default` (светлая по умолчанию). Бриф, который не читается, называет его валидатор."""
    import yaml
    try:
        rows = docpaths.surfaces(prj.slug, repo=prj.repo)
    except docpaths.DocPathError:
        rows = []
    paths = [(s.slug, docpaths.site(prj.slug, s.slug, "brief", repo=prj.repo)) for s in rows if s.page]
    paths.append((None, docpaths.design(prj.slug, "app-brief", repo=prj.repo)))
    out = []
    for surf, p in paths:
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8")) if p.is_file() else None
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(doc, dict):
            continue
        th = doc.get("themes") if isinstance(doc.get("themes"), dict) else {}
        dark = th.get("dark") if isinstance(th.get("dark"), dict) else {}
        default = th.get("default") or "light"
        need = set(THEMES) if dark.get("needed") is True or default == "system" else {default}
        if need <= set(THEMES):
            out.append((surf, p, need))
    return out


def check(prj):
    """Находки R-STRUCT-006, R-COV-010 и R-FRESH-001 по ДС продукта."""
    rep = F.Report()
    derived = [prj.css_path, prj.design_md_path, prj.art_tokens, prj.art_readme]
    if not prj.tokens_path.is_file():
        present = [p for p in derived if p.is_file()]
        if present:
            rep.add("R-STRUCT-006", "error", surface=None, kind=KIND, ref="tokens", path=prj.rel(prj.tokens_path),
                    message="нет токенов DTCG, а производные ДС есть: " + ", ".join(p.name for p in present),
                    fix=f"токены — этап design-system: /design-deep-dive {prj.slug}")
        return rep.items
    data, err = load_tokens(prj.tokens_path)
    rel_tokens = prj.rel(prj.tokens_path)
    if err:
        rep.add("R-STRUCT-006", "error", surface=None, kind=KIND, ref="tokens", path=rel_tokens,
                message=f"system.tokens.json — {err}")
        return rep.items
    issues = validate(data)
    for i in issues:
        rep.add("R-STRUCT-006", i.severity, surface=None, kind=KIND, ref="tokens#" + i.pointer, path=rel_tokens,
                message=i.message, fix=i.fix or ("" if i.severity != "error" else "правка токена в system.tokens.json, "
                                                 f"затем ds_build build {prj.slug}"))
    if any(i.severity == "error" for i in issues):
        rep.add("R-FRESH-001", "hint", surface=None, kind=KIND, ref="tokens", path=rel_tokens,
                message="свежесть производных не сверялась: токены не собираются, пока есть ошибки формата")
        return rep.items
    toks = Tokens(data)
    own = [f for f in dict.fromkeys(family_of(t) for t in toks.list) if f and f not in BASE_FAMILIES + ("font",)]
    if len(own) > OWN_FAMILIES_MAX:
        rep.add("R-STRUCT-006", "warning", surface=None, kind=KIND, ref="tokens", path=rel_tokens,
                message=f"в артефакт уходит {len(own)} своих семейств ({', '.join(own)}), формат типа принимает до "
                        f"{OWN_FAMILIES_MAX}: лишние сведите поле `family` расширения {EXT_ART}")
    if narrow(toks) is None and toks.get("type.body") is not None and \
            not [t for t in toks.list if t.path[0] == "breakpoint"]:
        rep.add("R-STRUCT-006", "warning", surface=None, kind=KIND, ref="tokens#/breakpoint", path=rel_tokens,
                message="нет breakpoint.*: граница узкой ширины для основного текста (ux 09/03 §7.1) не задана")
    for i in typography_issues(toks):
        rep.add("R-STRUCT-006", i.severity, surface=None, kind=KIND, ref="tokens#" + i.pointer, path=rel_tokens,
                message=i.message, fix="одно значение в `$value` и в расширении кегля токена, затем "
                                       f"ds_build build {prj.slug}")
    first = base_theme(toks.data)
    declared = isinstance(_root_modes(data), dict) and "base" in _root_modes(data)
    for surf, path, need, have in theme_gaps(prj, toks):
        rep.add("R-COV-010", "warning", surface=surf, kind=KIND, ref="tokens#" + pointer(("$extensions", EXT_MODES)),
                path=rel_tokens,
                message=f"бриф {prj.rel(path)} ждёт тем {', '.join(sorted(need))}, у токенов — "
                        f"{', '.join(sorted(have))}: тема значений `$value` — {first}"
                        + ("" if declared else " (`modes.base` не объявлена)")
                        + f", color-scheme производного CSS — {' '.join([first] + sorted(have - {first}))}",
                fix="тёмные значения `$value` — `modes.base: dark` в корне токенов, вторая тема — режим токенов с её "
                    f"именем, затем ds_build build {prj.slug}; правка токенов снимает одобрение макета — решает "
                    "владелец продукта, как и правка темы брифа")
    built, _ = derive(prj, data)
    fix = f"ds_build build {prj.slug} — производные руками не правят"
    for path in (prj.css_path, prj.design_md_path, prj.art_tokens, prj.art_readme):
        ref = {prj.css_path: "tokens-css", prj.design_md_path: "design-md#front-matter", prj.art_tokens:
               "artifact#tokens.json", prj.art_readme: "artifact#README.md"}[path]
        if path not in built:
            rep.add("R-FRESH-001", "warning", surface=None, kind=KIND, ref="design-md",
                    path=prj.rel(prj.design_md_path),
                    message="нет прозы DESIGN.md: передняя часть и README артефакта не собираются",
                    fix=f"проза ДС — этап design-system: /design-deep-dive {prj.slug}")
            continue
        if not path.is_file():
            rep.add("R-FRESH-001", "error", surface=None, kind=KIND, ref=ref, path=prj.rel(path),
                    message=f"{path.name}: производного нет — сборка из токенов не запускалась", fix=fix)
            continue
        disk = path.read_text(encoding="utf-8")
        fresh = readme_fresh(disk, built[path]) if path == prj.art_readme else disk == built[path]
        if not fresh:
            rep.add("R-FRESH-001", "error", surface=None, kind=KIND, ref=ref, path=prj.rel(path),
                    message=f"{_what(path, prj)} от сборки: {_first_diff(disk, built[path])}",
                    fix=fix + (CSS_APPROVALS if path == prj.css_path else ""))
    return rep.items


CSS_APPROVALS = ("; пересборка изменит system.tokens.css — источник отпечатка одобрения: одобрения принятых макетов "
                 "сняты до новой приёмки, решает владелец продукта")


def _what(path, prj):
    return {prj.css_path: "system.tokens.css отстал", prj.design_md_path: "передняя часть DESIGN.md отстала",
            prj.art_tokens: "tokens.json артефакта отстал", prj.art_readme: "README артефакта отстал"}.get(
        path, path.name + " отстал")


def _first_diff(a, b):
    la, lb = a.splitlines(), b.splitlines()
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else "∅"
        y = lb[i] if i < len(lb) else "∅"
        if x != y:
            return f"строка {i + 1}: в файле «{x[:70]}», в сборке «{y[:70]}»"
    return "различаются концы строк"


def build(prj, out=None):
    """Записать производные (по месту или в out/docs/projects/<slug>/…) → [(путь, записан ли)]."""
    data, err = load_tokens(prj.tokens_path)
    if err:
        raise F.ToolError(f"{prj.rel(prj.tokens_path)} — {err}")
    errors = [i for i in validate(data) if i.severity == "error"]
    if errors:
        raise F.ToolError(f"токены с ошибками формата ({len(errors)}), первая: {errors[0].pointer} — "
                          f"{errors[0].message}"
                          f"; ds_build check {prj.slug}")
    built, _ = derive(prj, data)
    done = []
    for path, text in built.items():
        target = path if out is None else Path(out) / Path(prj.rel(path))
        same = target.is_file() and target.read_text(encoding="utf-8") == text
        if not same:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        done.append((target, not same))
    return done


# ------------------------------------------------------------------ загрузки артефакта Design System

ASSET_ID = r"[0-9a-f]{32}"                                  # id загрузки артефакта
BLOB_URL = re.compile(rf"/_blob/({ASSET_ID})")
ASSET_REF = re.compile(r"""\b(src|href|poster)(\s*=\s*)(["'])([^"'<>]+)\3|url\(\s*(["']?)([^"'()]+)\5\s*\)""")
BIND_TEXT = (".html", ".css", ".js", ".json", ".md", ".svg", ".ts")
INDEX = "design-system.json"                                 # индекс артефакта: загрузки — assetGroups.<группа>.files


def upload_answer(path):
    """Ответ загрузки → [(файл как в ответе, id)]. JSON: список записей с именем файла (`file`, `path` или `name`) и
    id (`id` или адрес `url` вида `/_blob/<id>`) либо словарь `{файл: id или адрес}`."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        raise F.ToolError(f"ответ загрузки {path} не читается как JSON: {e}") from e
    if isinstance(data, dict):
        pairs = list(data.items())
    elif isinstance(data, list) and all(isinstance(r, dict) for r in data):
        pairs = [(next((r[k] for k in ("file", "path", "name") if isinstance(r.get(k), str)), None),
                  r.get("id") or r.get("url")) for r in data]
    else:
        raise F.ToolError(f"ответ загрузки {path}: нужен список записей {{file, id}} или словарь {{файл: id}}")
    rows = []
    for name, value in pairs:
        m = re.search(rf"(?:^|/)({ASSET_ID})(?:$|[/?#])", value) if isinstance(value, str) else None
        if not isinstance(name, str) or not name or m is None:
            raise F.ToolError(f"ответ загрузки {path}: запись без имени файла или id загрузки ({name!r})")
        rows.append((re.sub(r"^(?:\./|/)+", "", name.replace("\\", "/")), m.group(1)))
    return rows


def answer_id(rows, rel):
    """id загрузки файла репозитория (путь от `design/` или имя файла): запись ответа с тем же именем и тем же
    концом пути. Записей с разными id несколько или ни одной — None."""
    name = rel.rsplit("/", 1)[-1]
    ids = {i for n, i in rows if n.rsplit("/", 1)[-1] == name
           and (n == rel or n.endswith("/" + rel) or rel.endswith("/" + n))}
    return next(iter(ids)) if len(ids) == 1 else None


def bind_assets(prj, answer, out):
    """Копия исходников артефакта ДС с id загрузок из ответа загрузки → ([(путь, записан ли)], находки); исходники
    не меняются. Ссылка `src`, `href`, `poster` или `url(…)` на файл `design/` вне папки артефакта → `/_blob/<id>`;
    `/_blob/<id>` с id из индекса исходников → id того же имени файла; `blob` записи индекса — по имени файла."""
    rows = upload_answer(answer)
    src, design = prj.art_dir.resolve(), prj.tokens_path.parent.resolve()
    if not src.is_dir():
        raise F.ToolError(f"нет исходников артефакта ДС: {prj.rel(prj.art_dir)}")
    copy = (Path(out) / Path(prj.rel(prj.art_dir))).resolve()
    if copy == src or src in copy.parents:
        raise F.ToolError("artifact: --out ведёт в исходники артефакта — копия с id загрузок пишется вне проекта")
    rep = F.Report()
    index = None
    if (src / INDEX).is_file():
        try:
            index = json.loads((src / INDEX).read_text(encoding="utf-8"))
        except ValueError as e:
            raise F.ToolError(f"{prj.rel(prj.art_dir / INDEX)} — не JSON: {e}") from e
    groups = index.get("assetGroups") if isinstance(index, dict) else None
    records = [(name, rec) for g in (groups.values() if isinstance(groups, dict) else ())
               for name, rec in (g["files"].items() if isinstance(g, dict) and isinstance(g.get("files"), dict)
                                 else ()) if isinstance(rec, dict)]
    was = {rec["blob"]: name for name, rec in records
           if isinstance(rec.get("blob"), str) and re.fullmatch(ASSET_ID, rec["blob"])}
    now = {i for _, i in rows}
    path = src

    def miss(what, ref):
        rep.add("R-REF-008", "warning", surface=None, kind=KIND, ref="artifact#" + ref,
                path=prj.rel(prj.art_dir / path.relative_to(src)),
                message=f"{what}: id загрузки в ответе загрузки нет — ссылка осталась как в исходнике",
                fix="загрузить файл в артефакт и повторить привязку с новым ответом загрузки")

    def blob(m):
        old = m.group(1)
        new = answer_id(rows, was[old]) if old in was else None
        if new is None and old not in now:
            miss(f"`/_blob/{old}`" + (f" (файл {was[old]})" if old in was else " — id нет в индексе исходников"), old)
        return f"/_blob/{new}" if new else m.group(0)

    def ref(m):
        attr = m.group(1) is not None
        target = (m.group(4) if attr else m.group(6)).split("#", 1)[0].split("?", 1)[0].strip()
        if not target or re.match(r"(?:[a-z][a-z0-9+.-]*:|/)", target, re.I):
            return m.group(0)
        file = (path.parent / target).resolve()
        if not file.is_file() or design not in file.parents or src in file.parents:
            return m.group(0)
        rel = file.relative_to(design).as_posix()
        new = answer_id(rows, rel)
        if new is None:
            miss(f"файл ассета `{rel}`", rel)
            return m.group(0)
        q = m.group(3) if attr else m.group(5)
        return f"{m.group(1)}{m.group(2)}{q}/_blob/{new}{q}" if attr else f"url({q}/_blob/{new}{q})"

    done = []
    for path in sorted(p for p in src.rglob("*") if p.is_file()):
        raw = path.read_bytes()
        if path.suffix.lower() in BIND_TEXT:
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if text is not None and path == src / INDEX:
                for name, rec in records:
                    new = answer_id(rows, name)
                    if new:
                        rec["blob"] = new
                    elif rec.get("blob") not in now:
                        miss(f"запись индекса `{name}`", "assetGroups/" + name)
                raw = (json.dumps(index, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            elif text is not None:
                raw = ASSET_REF.sub(ref, BLOB_URL.sub(blob, text)).encode("utf-8")
        target = copy / path.relative_to(src)
        same = target.is_file() and target.read_bytes() == raw
        if not same:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        done.append((target, not same))
    return done, rep.items


def show(prj, as_json=False, out=None):
    out = out or sys.stdout
    data, err = load_tokens(prj.tokens_path)
    if err:
        raise F.ToolError(f"{prj.rel(prj.tokens_path)} — {err}")
    toks = Tokens(data)
    rows = []
    for t in toks.list:
        try:
            base = token_vars(toks, t)
            modes = {m: token_vars(toks, t, m) for m in t.modes()}
        except (ValueError, KeyError, TypeError) as e:
            base, modes = [(t.name, f"не разрешается: {e}")], {}
        row = {"path": ".".join(t.path), "var": "--" + t.name, "type": t.type, "family": family_of(t),
               "value": dict(base), "modes": {m: dict(v) for m, v in modes.items()}}
        src = spring_source(toks, t) if t.type == "transition" else None
        if src is not None:
            row["spring"] = dict(spring_fields(spring_curve(*spring_of(src))), source=".".join(src.path))
        rows.append(row)
    if as_json:
        print(json.dumps({"project": prj.slug, "tokens": rows, "narrow": narrow(toks)}, ensure_ascii=False, indent=1),
              file=out)
        return
    for r in rows:
        vals = "; ".join(f"{k}: {v}" for k, v in r["value"].items())
        print(f"{r['path']:<34} {r['type'] or '?':<11} {(r['family'] or '—'):<10} {vals}", file=out)
        for m, v in r["modes"].items():
            print(f"{'':<34} {'':<11} {'':<10} [{m}] " + "; ".join(f"{k}: {x}" for k, x in v.items()), file=out)
        if "spring" in r:
            print(f"{'':<34} {'':<11} {'':<10} [пружина] " + "; ".join(
                f"{k}: {num(x) if isinstance(x, float) else x}" for k, x in r["spring"].items()), file=out)


# ------------------------------------------------------------------ самопроверка

def reference_tokens():
    """Эталонный листинг DTCG ui 09/04 §4 (для самопроверки формата)."""
    text = kbpaths.kb("ui", "09-design-tokens", "04-reference-token-schema.md").read_text(encoding="utf-8")
    m = re.search(r"^## 4\..*?^```json\s*\n(.*?)^```", text, re.S | re.M)
    return json.loads(m.group(1)) if m else None


def _selftest_themes(check_):
    """R-COV-010: темы брифов сайта и кабинета против тем токенов — на вымышленном проекте во временной папке."""
    import tempfile
    import yaml
    with tempfile.TemporaryDirectory(prefix="ddd-ds-themes-") as td:
        pj = Path(td) / "docs" / "projects" / "demo"
        (pj / "site" / "promo").mkdir(parents=True)
        (pj / "design").mkdir()
        (pj / "surface.md").write_text("| slug | name | type | web-kind | status |\n|---|---|---|---|---|\n"
                                       "| promo | Лендинг | `web` | `landing` | draft |\n", encoding="utf-8")
        prj = Project.of("demo", Path(td))
        color = {"color": {"$type": "color", "bg": {"$value": {"colorSpace": "srgb", "components": [0.1, 0.1, 0.1],
                                                               "hex": "#1A1A1A"}}}}

        def cov(tokens, themes, app=None):
            prj.tokens_path.write_text(json.dumps(tokens, ensure_ascii=False), encoding="utf-8")
            (pj / "site" / "promo" / "site-brief.yaml").write_text(yaml.safe_dump({"themes": themes}), encoding="utf-8")
            ab = pj / "design" / "app-brief.yaml"
            if app:
                ab.write_text(yaml.safe_dump({"themes": app}), encoding="utf-8")
            elif ab.exists():
                ab.unlink()
            return [(f.surface, f.severity, f.message) for f in check(prj) if f.rule == "R-COV-010"]

        dark_one = {"default": "dark", "dark": {"needed": False, "why": "вымышлено"}}
        got = cov(color, dark_one)
        check_("сайт в одной тёмной теме на токенах без modes.base: dark → R-COV-010 warning поверхности, в "
               "сообщении — тема значений и color-scheme", len(got) == 1 and got[0][:2] == ("promo", "warning")
               and "не объявлена" in got[0][2] and "color-scheme производного CSS — light" in got[0][2])
        based = dict(color, **{"$extensions": {EXT_MODES: {"base": "dark"}}})
        check_("modes.base: dark — тема брифа есть у токенов, находки нет", cov(based, dark_one) == [])
        two = {"default": "system", "dark": {"needed": True, "why": "вымышлено"}, "switcher": True}
        got = cov(based, two, app={"default": "light"})
        check_("две темы брифа сайта на токенах одной тёмной темы и светлый бриф на вид кабинета → по находке, у "
               "кабинета без поверхности", sorted((g[0] or "", g[1]) for g in got) == [("", "warning"),
                                                                                    ("promo", "warning")])


def _spring_errors(c, grid=8000):
    """(отклонение ломаной точек от кривой spring_target, от физики spring_step) на мелкой сетке времени."""
    dur = c.settle_ms / 1000
    f, x, pts = spring_target(c.ratio, c.omega, dur), spring_step(c.ratio, c.omega), c.points
    fit = phys = 0.0
    j = 0
    for i in range(grid + 1):
        u = i / grid
        while j < len(pts) - 2 and pts[j + 1][0] < u:
            j += 1
        (u0, v0), (u1, v1) = pts[j], pts[j + 1]
        line = v0 + (v1 - v0) * (u - u0) / (u1 - u0)
        fit, phys = max(fit, abs(line - f(u * dur))), max(phys, abs(line - x(u * dur)))
    return fit, phys


def _selftest_springs(check_, doc):
    """Пружина: кривая, время успокоения, точки linear(), формы вывода и замечания (ui 08/04 §1)."""
    import copy
    import io
    import tempfile
    crit, snap = spring_curve(1.0, 700), spring_curve(0.7, 380)
    vals = [v for _, v in crit.points]
    check_("пружина ζ = 1: linear() монотонная без перелёта, конец — цель 1; время — успокоение до 1 % пути, вверх до "
           "10 ms",
           all(b >= a for a, b in zip(vals, vals[1:])) and max(vals) == 1 and crit.overshoot == 0
           and crit.css.startswith("linear(0, ") and crit.css.endswith(", 1)") and crit.settle_ms % SPRING_STEP_MS == 0
           and crit.settle_ms - SPRING_STEP_MS < spring_settle(1.0, crit.omega) * 1000 <= crit.settle_ms
           and abs(spring_step(1.0, crit.omega)(spring_settle(1.0, crit.omega)) - (1 - SPRING_SETTLE)) < 1e-9)
    ts, x = spring_settle(0.7, snap.omega), spring_step(0.7, snap.omega)
    check_("пружина ζ = 0.7, stiffness 380: перелёт точек — перелёт физики 4,6 % в пределах допуска; после времени "
           "успокоения кривая не выходит из полосы 1 %, перед ним — выходит; CSS — 340 ms",
           abs(max(v for _, v in snap.points) - 1 - snap.overshoot) <= SPRING_FIT and round(snap.overshoot, 3) == 0.046
           and snap.settle_ms == 340 and all(abs(x(ts + i / 1000) - 1) <= SPRING_SETTLE + 1e-12 for i in range(2000))
           and abs(x(ts - 1e-6) - 1) > SPRING_SETTLE - 1e-6)
    springs = [(0.9, 700), (0.9, 1400), (0.9, 300), (1.0, 1600), (1.0, 3800), (1.0, 800), (0.8, 380), (0.6, 800),
               (0.8, 200), (0.7, 380), (1.0, 157.9137), (0.85, 157.9137), (1.3, 700), (0.5, 400)]
    worst = []
    for z, k in springs:
        c = spring_curve(z, k)
        fit, phys = _spring_errors(c)
        us = [u for u, _ in c.points]
        worst.append((fit, phys, len(c.points), all(b > a for a, b in zip(us, us[1:])) and c.points[-1] == (1.0, 1.0)))
    check_(f"точки linear() у {len(springs)} пружин (M3, SwiftUI, передемпфированная, с отскоком): ломаная отходит "
           f"от кривой не больше {num(SPRING_FIT * 100)} % пути с округлением записи, от физики — не больше "
           f"{num((SPRING_SETTLE + SPRING_FIT) * 100)} % (плавный остаток в конце); точек не больше "
           f"{SPRING_POINTS_MAX}, время растёт строго (наибольшее: {num(round(max(w[0] for w in worst) * 100, 3))} %, "
           f"{max(w[2] for w in worst)} точек)",
           all(f <= SPRING_FIT and p <= SPRING_SETTLE + SPRING_FIT and n <= SPRING_POINTS_MAX and inc
               for f, p, n, inc in worst))
    check_("перевод параметров: ω = √k, response SwiftUI = 2π/ω, bounce = 1 − ζ (с отскоком), 1/ζ − 1 "
           "(передемпфированная)",
           abs(snap.omega - 19.4936) < 1e-4 and abs(snap.response - 0.3223) < 1e-4 and abs(snap.bounce - 0.3) < 1e-9
           and abs(spring_curve(1.3, 700).bounce - (1 / 1.3 - 1)) < 1e-9 and crit.bounce == 0)

    zero = {"value": 0, "unit": "ms"}

    def tr(ms, curve="{motion.easing.entrance}", delay=zero):
        return {"duration": {"value": ms, "unit": "ms"}, "delay": delay, "timingFunction": curve}

    sd = copy.deepcopy(doc)
    sd["motion"].update({
        "easing": {"$type": "cubicBezier", "entrance": {"$value": [0, 0, 0.2, 1]}},
        "spring": {"$type": "transition",
                   "snap": {"$value": tr(340), "$extensions": {
                       EXT_SPRING: {"dampingRatio": 0.7, "stiffness": 380}, EXT_MODES: {"reduced": tr(150)}}},
                   "late": {"$value": tr(260, delay={"value": 50, "unit": "ms"}), "$extensions": {
                       EXT_SPRING: {"dampingRatio": 1, "stiffness": 700}, EXT_MODES: {"reduced": tr(150)}}}},
        "switch": {"$type": "transition", "thumb": {"$value": "{motion.spring.snap}"}}})
    st = Tokens(sd)
    scss, sfm = build_css(st), front_matter(st, "Проба", "описание")
    root = scss.split("\n}\n")[0]
    check_("CSS пружины: `<успокоение>ms linear(…)` и задержка значения, над переменной — комментарий с параметрами; "
           "алиас на пружину — та же кривая; в блоке сокращённого движения — переход без пружины",
           f"  --motion-spring-snap: 340ms {snap.css};" in root
           and f"  --motion-spring-late: 260ms {crit.css} 50ms;" in root
           and f"  --motion-switch-thumb: 340ms {snap.css};" in root
           and "  /* пружина: dampingRatio 0.7, stiffness 380 (масса 1, ω 19.49 рад/с), перелёт 4.6 %, успокоение до "
               "1 % пути — 340 ms */\n  --motion-spring-snap:" in root
           and "/* пружина токена motion.spring.snap: " in root
           and '  :root:not([data-motion="full"]) {\n    --motion-fast: 0ms;\n    --motion-spring-snap: 150ms '
               'cubic-bezier(0, 0, 0.2, 1);\n    --motion-spring-late: 150ms cubic-bezier(0, 0, 0.2, 1);\n'
               '    --motion-switch-thumb: 150ms cubic-bezier(0, 0, 0.2, 1);\n' in scss
           and validate(sd) == [])
    check_("передняя часть: x-springs — параметры для кода (форма токена, response и bounce SwiftUI, перелёт, время "
           "CSS), у алиаса — параметры цели; в x-modes.reduced — переход без пружины; в артефакт движение не идёт",
           "x-springs:\n  motion-spring-snap:\n    dampingRatio: 0.7\n    stiffness: 380\n    response: 0.3223\n"
           "    bounce: 0.3\n    overshoot: 0.046\n    settle: \"340ms\"\n" in sfm
           and "  motion-switch-thumb:\n    dampingRatio: 0.7\n" in sfm.split("x-springs:")[1].split("x-modes:")[0]
           and '    motion-spring-snap: "150ms cubic-bezier(0, 0, 0.2, 1)"' in sfm.split("x-modes:")[1]
           and "motion" not in artifact_tokens(st, "Проба"))
    with tempfile.TemporaryDirectory(prefix="ddd-ds-spring-") as td:
        path = Path(td) / "system.tokens.json"
        path.write_text(json.dumps(sd, ensure_ascii=False), encoding="utf-8")
        buf = io.StringIO()
        show(Project("demo", Path(td), path, Path(td) / "x.css", Path(td) / "DESIGN.md", Path(td) / "art",
                     Path(td) / "brand.yaml"), as_json=True, out=buf)
        rows = {r["path"]: r for r in json.loads(buf.getvalue())["tokens"]}
    check_("show --json: у пружины и у алиаса на неё — параметры и токен-источник",
           rows["motion.spring.snap"]["spring"] == dict(spring_fields(snap), source="motion.spring.snap")
           and rows["motion.switch.thumb"]["spring"]["source"] == "motion.spring.snap"
           and "spring" not in rows["motion.fast"])

    def issues(mutate):
        d = copy.deepcopy(sd)
        mutate(d["motion"]["spring"])
        return [(i.severity, i.message, i.fix) for i in validate(d) if "/spring/" in i.pointer]

    def put(key, **kw):
        return lambda s: s["snap"]["$extensions"][EXT_SPRING].update(kw) if key is None else \
            s["snap"]["$extensions"][EXT_SPRING].pop(key)

    def on_duration(s):
        s["wrong"] = {"$type": "duration", "$value": zero, "$extensions": {EXT_SPRING: {"dampingRatio": 1,
                                                                                       "stiffness": 700}}}

    errs = [issues(on_duration), issues(put("stiffness")), issues(put(None, dampingRatio=0)),
            issues(put(None, mass=1.75)), issues(put(None, stiffness=True))]
    check_("форма пружины — ошибка: у токена не transition, без stiffness, ζ = 0, лишний ключ (mass) с подсказкой "
           "«масса не пишется», логическое вместо числа",
           all(len(e) == 1 and e[0][0] == "error" for e in errs) and "только у токена transition" in errs[0][0][1]
           and "stiffness — число больше нуля" in errs[1][0][1] and "mass — вне формы пружины" in errs[3][0][1]
           and "масса не пишется" in errs[3][0][2])

    def soft(s):
        s["snap"]["$extensions"][EXT_SPRING]["dampingRatio"] = 0.5

    def slow(s):
        s["snap"]["$extensions"][EXT_SPRING].update(dampingRatio=1, stiffness=50)

    def stale(s):
        s["snap"]["$value"]["duration"]["value"] = 300

    def bare(s):
        del s["snap"]["$extensions"][EXT_MODES]

    def bouncy_reduced(s):
        s["snap"]["$extensions"][EXT_MODES]["reduced"]["timingFunction"] = [0.12, 0.4, 0.29, 1.46]

    def css_too(s):
        s["snap"]["$extensions"][EXT_CSS] = "200ms ease"

    def seconds(s):
        s["snap"]["$value"]["duration"] = {"value": 0.34, "unit": "s"}

    warns = {n: issues(m) for n, m in (("soft", soft), ("slow", slow), ("stale", stale), ("bare", bare),
                                       ("bouncy", bouncy_reduced), ("css", css_too), ("seconds", seconds))}

    def has(n, text, fix=""):
        return any(s == "warning" and text in m and fix in f for s, m, f in warns[n])

    check_("нормы пружины — предупреждения: перелёт больше 10 % (ζ 0.5 — 16.3 %), успокоение дольше 600 ms, "
           "длительность $value не равна времени успокоения (подсказка — число; 0.34 s — то же, что 340 ms), нет "
           "значения сокращённого движения, в нём перелёт, расширение css рядом с пружиной; ошибок нет",
           has("soft", "перелёт 16.3 %") and has("slow", "дольше 600 ms")
           and has("stale", "длительность `$value` 300 ms, время успокоения пружины 340 ms", '"value": 340')
           and warns["seconds"] == []
           and has("bare", "нет значения сокращённого движения") and has("bouncy", "кривая с перелётом")
           and has("css", "не читается") and not any(s == "error" for w in warns.values() for s, _, _ in w))


def _selftest():
    import copy
    import subprocess
    import tempfile
    ok = True

    def check_(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("OK   " if cond else "FAIL ") + msg)

    _jsonschema()
    # 1. значения CSS и разрешение алиасов
    doc = {"primitive": {"color": {"$type": "color", "ink": {"$value": {"colorSpace": "srgb", "components": [0, 0, 0],
                                                                       "hex": "#000000"}},
                                   "paper": {"$value": {"colorSpace": "srgb", "components": [1, 1, 1],
                                                        "hex": "#FFFFFF"}}},
                         "size": {"$type": "dimension", "14": {"$value": {"value": 14, "unit": "px"}}}},
           "color": {"$type": "color",
                     "bg": {"$value": "{primitive.color.paper}",
                            "$extensions": {EXT_MODES: {"dark": "{primitive.color.ink}"}}},
                     "text": {"$value": "{primitive.color.ink}",
                              "$extensions": {EXT_MODES: {"dark": "{primitive.color.paper}"}}},
                     "on-bg": {"$value": "{color.text}"},
                     "scrim": {"$value": {"colorSpace": "srgb", "components": [0, 0, 0], "alpha": 0.5,
                                          "hex": "#000000"}}},
           "font": {"sans": {"$type": "fontFamily", "$value": ["Golos Text", "Arial", "sans-serif"]}},
           "breakpoint": {"$type": "dimension", "desktop": {"$value": {"value": 1024, "unit": "px"}},
                          "tablet": {"$value": {"value": 640, "unit": "px"}}},
           "motion": {"fast": {"$type": "duration", "$value": {"value": 100, "unit": "ms"},
                               "$extensions": {EXT_MODES: {"reduced": {"value": 0, "unit": "ms"}}}}},
           "type": {"$type": "typography",
                    "body": {"$value": {"fontFamily": "{font.sans}", "fontSize": "{primitive.size.14}",
                                        "fontWeight": 400,
                                        "letterSpacing": {"value": 0, "unit": "px"}, "lineHeight": 1.428571}}}}
    check_("формат DTCG: чистый документ — 0 замечаний", validate(doc) == [])
    toks = Tokens(doc)
    check_("алиас разрешается в режиме транзитивно: color.on-bg в dark = paper",
           color_css(toks.value(toks.get("color.on-bg"), "dark")) == "#FFFFFF")
    check_("цвет с альфой → rgb(R G B / A)", color_css(toks.value(toks.get("color.scrim"))) == "rgb(0 0 0 / 0.5)")
    check_("гарнитура: многословные — в кавычках", font_css(["Golos Text", "Arial", "sans-serif"]) ==
           '"Golos Text", Arial, sans-serif')
    css = build_css(toks)
    check_("CSS: имена = пути через дефис, типографика — пять переменных",
           "--color-bg: #FFFFFF;" in css and "--type-body-size: 14px;" in css
           and "--type-body-leading: 1.428572;" in css
           and '--font-sans: var(--font-golos-text, "Golos Text", Arial, sans-serif);' in css)
    check_("CSS: блок тёмной темы — транзитивное замыкание (color.on-bg без своего режима)",
           re.search(r':root\[data-theme="dark"\] \{[^}]*--color-on-bg: #FFFFFF;', css) is not None)
    check_("CSS: сокращённое движение и узкая ширина (type.body 14 → 16 ниже первой границы 640px)",
           "--motion-fast: 0ms;" in css and "@media (width < 640px)" in css and "--type-body-size: 16px;" in css)
    check_("CSS: сокращённое движение — по системе, кроме выбора data-motion=\"full\", и под атрибутом reduced при "
           "любой системе; значение $value — в :root",
           '@media (prefers-reduced-motion: reduce) {\n  :root:not([data-motion="full"]) {\n    --motion-fast: 0ms;\n'
           '  }\n}\n\n:root[data-motion="reduced"] {\n  --motion-fast: 0ms;\n}\n' in css
           and ":root {\n" in css and "  --motion-fast: 100ms;\n" in css.split("\n}\n")[0]
           and css.count("[data-motion=") == 2)
    still = copy.deepcopy(doc)
    del still["motion"]
    still_css = build_css(Tokens(still))
    check_("CSS: ДС без токенов движения — без блока сокращённого движения",
           "prefers-reduced-motion" not in still_css and "data-motion" not in still_css
           and still_css == css.split("\n\n/* Сокращённое движение")[0].replace("  --motion-fast: 100ms;\n", "")
           + "\n")
    fam = copy.deepcopy(doc)
    fam["font"].update({"ui": {"$type": "fontFamily", "$value": ["system-ui", "-apple-system", "sans-serif"]},
                        "serif": {"$type": "fontFamily", "$value": "Georgia"}})
    fam["type"]["title"] = {"$value": dict(doc["type"]["body"]["$value"], fontFamily=["Demo Display", "serif"])}
    fam["type"]["broken"] = {"$value": dict(doc["type"]["body"]["$value"], fontFamily="{font.nope}")}
    check_("web_families: первое имя стека fontFamily и типографики — не родовое и не системное, без повторов; "
           "алиас в пустоту пропускается", web_families(fam) == ["Golos Text", "Demo Display"])
    fam["font"]["solo"] = {"$type": "fontFamily", "$value": ["Solo Sans", "sans-serif"]}
    fam["type"]["strong"] = {"$value": dict(doc["type"]["body"]["$value"], fontWeight="semi-bold"),
                             "$extensions": {EXT_MODES: {"compact": dict(doc["type"]["body"]["$value"], fontWeight=500)}}}
    check_("font_needs: насыщенности типографики семейства числом по возрастанию — значение (словом тоже) и режимы; "
           "семейство без типографического токена — без насыщенностей",
           font_needs(fam) == {"Golos Text": [400, 500, 600], "Demo Display": [400], "Solo Sans": []})
    wf = copy.deepcopy(fam)
    del wf["type"]["broken"]
    wcss = build_css(Tokens(wf))
    check_("гарнитура в CSS: стек семейства, которому нужен файл, — ссылкой на переменную семейства со стеком в запасе "
           "(токен, роль по алиасу, роль с литералом); системный и родовой стек — литералом; в передней части и "
           "tokens.json артефакта — литералом; ключ — имя семейства строчными через дефис, без латиницы ключа нет",
           '--font-sans: var(--font-golos-text, "Golos Text", Arial, sans-serif);' in wcss
           and '--type-body-family: var(--font-golos-text, "Golos Text", Arial, sans-serif);' in wcss
           and '--type-title-family: var(--font-demo-display, "Demo Display", serif);' in wcss
           and "--font-ui: system-ui, -apple-system, sans-serif;" in wcss and "--font-serif: Georgia;" in wcss
           and "var(--font-" not in front_matter(Tokens(wf), "Проба", "описание")
           and "var(--font-" not in dump_artifact(artifact_tokens(Tokens(wf), "Проба")) and validate(wf) == []
           and [family_key(n) for n in ("IBM Plex Sans", "M+ 1p", " Font (Beta) ", "Élan", "Шрифт")]
           == ["ibm-plex-sans", "m-1p", "font-beta", "lan", ""]
           and family_css(["Шрифт Проекта", "serif"], set()) == '"Шрифт Проекта", serif')
    held = copy.deepcopy(wf)
    held["font"]["demo-display"] = {"$type": "fontFamily", "$value": ["Demo Display", "serif"]}
    hcss, got = build_css(Tokens(held)), validate(held)
    check_("имя переменной семейства занято переменной токена (font.demo-display при гарнитуре Demo Display): её стек "
           "— литералом у токена и у роли, одно предупреждение с подсказкой; прочие гарнитуры — ссылкой",
           '--font-demo-display: "Demo Display", serif;' in hcss
           and '--type-title-family: "Demo Display", serif;' in hcss and "--font-sans: var(--font-golos-text, " in hcss
           and [(i.severity, i.pointer) for i in got] == [("warning", "/font/demo-display")]
           and "`--font-demo-display`" in got[0].message and "`font.demo-display`" in got[0].message
           and "владелец продукта" in got[0].fix)
    mute = copy.deepcopy(wf)
    mute["font"]["alt"] = {"$type": "fontFamily", "$value": ["Golos-Text", "sans-serif"]}
    mute["type"]["local"] = {"$value": dict(doc["type"]["body"]["$value"], fontFamily=["Шрифт Проекта", "serif"])}
    mcss, got = build_css(Tokens(mute)), validate(mute)
    check_("гарнитура без ключа (в имени нет латинских букв и цифр) и два семейства с одним ключом — по "
           "предупреждению с подсказкой; форма CSS та же: стек без ключа — литералом, оба семейства — ссылкой на одну "
           "переменную",
           '--type-local-family: "Шрифт Проекта", serif;' in mcss
           and "--font-alt: var(--font-golos-text, Golos-Text, sans-serif);" in mcss
           and '--font-sans: var(--font-golos-text, "Golos Text", Arial, sans-serif);' in mcss
           and [(i.severity, i.pointer) for i in got] == [("warning", "/type/local"), ("warning", "/font/alt")]
           and "«Шрифт Проекта»" in got[0].message and "нет ключа" in got[0].message and got[0].fix
           and "«Golos Text», «Golos-Text»" in got[1].message and "`--font-golos-text`" in got[1].message
           and got[1].fix)
    check_("темы токенов: тема значений и парная по режиму (light + dark); без режимов темы — одна",
           token_themes(toks) == {"light", "dark"} and token_themes(Tokens({"font": doc["font"]})) == {"light"})
    _selftest_themes(check_)
    fm = front_matter(toks, "Проба", "описание")
    check_("передняя часть: colors, typography, x-modes, x-narrow",
           'color-bg: "#FFFFFF"' in fm and "type-body:" in fm and "x-modes:" in fm and "x-narrow:" in fm)
    art = artifact_tokens(toks, "Проба")
    check_("артефакт: без примитивов и движения; цвет по темам; type.families → font-sans",
           [t["name"] for t in art["color"]["tokens"]] == ["color-bg", "color-text", "color-on-bg", "color-scrim"]
           and art["color"]["tokens"][0]["value"] == {"light": "#FFFFFF", "dark": "#000000"}
           and art["type"]["families"] == {"sans": '"Golos Text", Arial, sans-serif'}
           and "motion" not in art and "breakpoint" in art)
    back = json.loads(dump_artifact(art))
    check_("tokens.json артефакта — валидный JSON той же структуры", back == art)
    # 1а. тема значений
    lite = copy.deepcopy(doc)
    for role in ("bg", "text"):
        del lite["color"][role]["$extensions"]
    check_("тема значений не объявлена: с тёмным режимом — color-scheme: light dark, без режимов темы — light",
           "  color-scheme: light dark;\n" in css and "  color-scheme: light;\n" in build_css(Tokens(lite))
           and [x["id"] for x in artifact_tokens(Tokens(lite), "Проба")["color"]["themes"]] == ["light"])
    check_("две темы: каждый блок темы объявляет её color-scheme — тема значений под атрибутом одну свою, парная — по "
           "системе и под атрибутом; у одной темы блоков темы нет",
           ':root[data-theme="light"] {\n  color-scheme: light;\n}\n' in css
           and ':root:not([data-theme="light"]) {\n    color-scheme: dark;\n' in css
           and ':root[data-theme="dark"] {\n  color-scheme: dark;\n' in css and css.count(" color-scheme: ") == 4
           and "data-theme" not in build_css(Tokens(lite)))
    own = copy.deepcopy(lite)
    own["color"]["bg"]["$extensions"] = {EXT_MODES: {"contrast": "{primitive.color.ink}"}}
    ocss = build_css(Tokens(own))
    mix = copy.deepcopy(doc)
    mix["color"]["scrim"]["$extensions"] = {EXT_MODES: {"contrast": "{primitive.color.ink}"}}
    check_("режим с другим именем — правка поверх действующей темы: своей схемы у блока нет, второй темой продукт он "
           "не делает (color-scheme: light, блока темы значений нет); при двух темах — блок без схемы",
           "  color-scheme: light;\n" in ocss and ocss.count(" color-scheme: ") == 1
           and ':root[data-theme="contrast"] {\n  --color-bg: #000000;' in ocss and 'data-theme="light"' not in ocss
           and ':root[data-theme="contrast"] {\n  --color-scrim: #000000;' in build_css(Tokens(mix)))
    dark = copy.deepcopy(lite)
    dark["$extensions"] = {EXT_MODES: {"base": "dark"}}
    dark["color"]["bg"]["$value"], dark["color"]["text"]["$value"] = "{primitive.color.ink}", "{primitive.color.paper}"
    dcss, dart = build_css(Tokens(dark)), artifact_tokens(Tokens(dark), "Проба")
    check_("одна тёмная тема (base: dark, режимов темы нет): color-scheme: dark, блоков темы нет, в артефакте — dark",
           validate(dark) == [] and "  color-scheme: dark;\n" in dcss and "data-theme" not in dcss
           and "prefers-color-scheme" not in dcss and dart["color"]["themes"] == [{"id": "dark", "name": "Тёмная"}]
           and dart["color"]["tokens"][0]["value"] == {"dark": "#000000"})
    both = copy.deepcopy(dark)
    both["color"]["bg"]["$extensions"] = {EXT_MODES: {"light": "{primitive.color.paper}"}}
    both["color"]["text"]["$extensions"] = {EXT_MODES: {"light": "{primitive.color.ink}"}}
    bcss, bart = build_css(Tokens(both)), artifact_tokens(Tokens(both), "Проба")
    check_("тёмная тема значений со светлым режимом: color-scheme: dark light, блок светлой — по системе и атрибутом, "
           "тёмная под атрибутом — блок с её схемой",
           "  color-scheme: dark light;\n" in bcss and ':root[data-theme="dark"] {\n  color-scheme: dark;\n}\n' in bcss
           and '@media (prefers-color-scheme: light) {\n  :root:not([data-theme="dark"]) {\n    color-scheme: light;\n'
           in bcss
           and re.search(r':root\[data-theme="light"\] \{\n  color-scheme: light;\n  --color-bg: #FFFFFF;', bcss)
           is not None and [x["id"] for x in bart["color"]["themes"]] == ["dark", "light"]
           and bart["color"]["tokens"][0]["value"] == {"dark": "#000000", "light": "#FFFFFF"})
    # 1б. типографика: интерлиньяж и трекинг

    def style(size, leading, tracking, fluid=None):
        tok = {"$value": {"fontFamily": "{font.sans}", "fontSize": {"value": size, "unit": "px"}, "fontWeight": 600,
                          "letterSpacing": {"value": tracking, "unit": "px"}, "lineHeight": leading}}
        if fluid is not None:
            tok["$extensions"] = {EXT_FLUID: fluid}
        return tok

    clamp = "clamp(2.25rem, 1.7857rem + 1.9048vw, 3.5rem)"
    typ = copy.deepcopy(doc)
    typ["type"].update({"label": style(15, 1.333333, 0.12), "media": style(28, 1.214286, 0.42,
                                                                          {"letter_spacing_em": 0.015}),
                        "lead": style(16, 1.5, 0), "display": style(56, 1.04, 0.84, {"css": clamp,
                                                                                    "letter_spacing_em": 0.015}),
                        "title": style(56, 1.1, -0.28, {"css": clamp}),
                        "quote": style(44, 1.2, 0, {"css": clamp, "letter_spacing_em": 0})})
    tt = Tokens(typ)
    tcss = build_css(tt)
    check_("интерлиньяж: отношение, округлённое вниз, поднимается до целого px (14 × 1.428572, 15 × 1.333334); "
           "точное, округлённое вверх и дробное — как в значении",
           leading_px(1.428571, 14) < 20 == leading_px("1.428572", 14) and "--type-label-leading: 1.333334;" in tcss
           and "--type-lead-leading: 1.5;" in tcss and "--type-media-leading: 1.214286;" in tcss
           and "--type-display-leading: 1.04;" in tcss)
    check_("трекинг: резиновый кегль — em (объявленный и px / кегль), постоянный кегль и нулевой трекинг — px",
           "--type-display-tracking: 0.015em;" in tcss and "--type-title-tracking: -0.005em;" in tcss
           and "--type-media-tracking: 0.015em;" in tcss and "--type-label-tracking: 0.12px;" in tcss
           and "--type-quote-tracking: 0px;" in tcss and "--type-display-size: " + clamp + ";" in tcss)
    tfm = front_matter(tt, "Проба", "описание")
    check_("передняя часть: трекинг резинового стиля — em, интерлиньяж — число значения",
           'letterSpacing: "0.015em"' in tfm and 'letterSpacing: "0.12px"' in tfm and "lineHeight: 1.428571" in tfm)
    clean = typography_issues(tt)
    typ["type"]["display"]["$value"]["letterSpacing"]["value"] = 0.9
    got = typography_issues(Tokens(typ))
    check_("сверка px: согласованная типографика — 0 замечаний; трекинг em × кегль ≠ px значения — предупреждение",
           clean == [] and len(got) == 1 and got[0].severity == "warning"
           and "трекинг" in got[0].message and "0.84" in got[0].message and "0.9" in got[0].message)
    grow = "calc(0.925em + 0.5625rem)"
    lead = copy.deepcopy(doc)
    lead["type"].update({"poster": style(56, 1.04, 0.84, {"css": clamp, "letter_spacing_em": 0.015,
                                                          "line_height_css": grow}),
                         "note": style(15, 1.333333, 0.12, {"line_height_css": " "})})
    lt = Tokens(lead)
    lcss, lfm, lart = build_css(lt), front_matter(lt, "Проба", "описание"), artifact_tokens(lt, "Проба")
    clean = typography_issues(lt)
    lead["type"]["poster"]["$value"]["letterSpacing"]["value"] = 0.9
    got = typography_issues(Tokens(lead))
    check_("готовый интерлиньяж: line_height_css расширения резинового кегля идёт в CSS как есть, пустое поле — число "
           "значения; в передней части и артефакте — число значения; с числом значения выражение не сверяется, "
           "трекинг того же стиля сверяется",
           f"--type-poster-leading: {grow};" in lcss and "--type-note-leading: 1.333334;" in lcss
           and "lineHeight: 1.04" in lfm and grow not in lfm
           and [s["lineHeight"] for g in lart["type"]["groups"] for s in g["styles"] if s["name"] == "poster"] == [1.04]
           and clean == [] and len(got) == 1 and "трекинг" in got[0].message and "poster" in got[0].message)
    _selftest_springs(check_, doc)
    # 2. дефекты формата
    bad = copy.deepcopy(doc)
    bad["color"]["bg"]["$value"] = "#fff"
    check_("битый $value цвета (строка вместо объекта) — ошибка",
           any("не по форме типа" in i.message for i in validate(bad)))
    bad = copy.deepcopy(doc)
    bad["color"]["text"]["$value"] = "{primitive.color.nope}"
    check_("алиас в пустоту — ошибка", any("в пустоту" in i.message for i in validate(bad)))
    bad = copy.deepcopy(doc)
    bad["color"]["bg"]["$value"] = "{color.on-bg}"
    bad["color"]["text"]["$value"] = "{color.bg}"
    check_("цикл алиасов — ошибка", any("цикл" in i.message for i in validate(bad)))
    bad = copy.deepcopy(doc)
    bad["color"]["bg"]["$extensions"][EXT_MODES]["dark"] = "{color.on-bg}"
    bad["color"]["text"]["$extensions"][EXT_MODES]["dark"] = "{color.bg}"
    check_("цикл алиасов только в режиме dark — ошибка", any("цикл" in i.message and "dark" in i.message
                                                             for i in validate(bad)))
    bad = copy.deepcopy(doc)
    bad["$extensions"] = {EXT_MODES: {"base": "system"}}
    check_("тема значений вне light и dark — ошибка", any("`base`" in i.message and i.severity == "error"
                                                         for i in validate(bad)))
    bad = copy.deepcopy(doc)
    bad["loose"] = {"x": {"$value": 3}}
    check_("токен без типа — ошибка (тип не угадывают)", any("тип не определён" in i.message for i in validate(bad)))
    bad = copy.deepcopy(doc)
    bad["type"]["body"]["$value"]["fontSize"] = "{color.bg}"
    check_("алиас подзначения другого типа — ошибка", any("тип цели color, нужен dimension" in i.message
                                                          for i in validate(bad)))
    bad = copy.deepcopy(doc)
    bad["spacing"] = {"$type": "dimension", "a": {"$value": {"value": 4, "unit": "px"}}}
    bad["space"] = {"$type": "dimension", "b": {"$value": {"value": 4, "unit": "px"}}}
    check_("вторая шкала отступов — предупреждение", any(i.severity == "warning" for i in validate(bad)))
    # 2а. расширения вне известных сборке и режим с именем темы значений
    bad = copy.deepcopy(doc)
    bad["$extensions"] = {"org.sample-tool.meta": {"v": 1}}
    bad["motion"]["fast"]["$extensions"]["org.sample-tool.fluid"] = {"css": "0ms"}
    bad["type"]["body"]["$extensions"] = {"org.sample-tool.fluid": {"css": clamp}, EXT_FLUID + "e": {"css": clamp}}
    got = validate(bad)
    check_("ключ $extensions вне известных сборке (другое пространство, опечатка в имени) — предупреждение на ключ с "
           "числом мест и первым местом, ошибок нет",
           [(i.severity, i.pointer) for i in got] == [
               ("warning", "/$extensions/org.sample-tool.meta"),
               ("warning", "/motion/fast/$extensions/org.sample-tool.fluid"),
               ("warning", f"/type/body/$extensions/{EXT_FLUID}e")]
           and "`org.sample-tool.fluid`" in got[1].message and "мест — 2" in got[1].message and got[1].fix)
    known = copy.deepcopy(doc)
    known["$extensions"] = {EXT_NOTES[0]: {"version": "1"}}
    known["color"]["text"]["$extensions"][EXT_LLM] = {"usage": ["body"]}
    known["motion"]["fast"]["$extensions"][EXT_NOTES[1]] = "motion.yaml#fast"
    known["type"]["body"]["$extensions"] = {EXT_FLUID: {"css": clamp}, EXT_ART: {"sample": "Аа"}}
    known["motion"]["press"] = {"$type": "transition", "$value": {
        "duration": {"value": 140, "unit": "ms"}, "delay": {"value": 0, "unit": "ms"},
        "timingFunction": [0, 0, 0.2, 1]},
        "$extensions": {EXT_SPRING: {"dampingRatio": 0.9, "stiffness": 1400}, EXT_REDUCE: {
            "duration": {"value": 100, "unit": "ms"}, "delay": {"value": 0, "unit": "ms"},
            "timingFunction": [0, 0, 0.2, 1]}}}
    check_("известные ключи расширений (modes, llm, reduce, fluid, css, spring, artifact, meta, limits) — 0 замечаний",
           validate(known) == [] and set(EXT_KNOWN) >= {EXT_MODES, EXT_REDUCE, EXT_CSS, EXT_SPRING})
    bad = copy.deepcopy(doc)
    bad["color"]["bg"]["$extensions"][EXT_MODES]["light"] = "{primitive.color.ink}"
    bad["color"]["text"]["$extensions"][EXT_MODES]["light"] = "{primitive.color.paper}"
    got = validate(bad)
    scss = build_css(Tokens(bad))
    check_("режим токена с именем темы значений — одно предупреждение с числом токенов; у темы значений dark режим "
           "light — чисто; в CSS блок этой темы под атрибутом один — со схемой и значениями режима",
           len(got) == 1 and got[0].severity == "warning" and "токенов — 2" in got[0].message
           and got[0].pointer == f"/color/bg/$extensions/{EXT_MODES}/light" and "`dark`" in got[0].fix
           and validate(both) == [] and scss.count(':root[data-theme="light"] {') == 1
           and ':root[data-theme="light"] {\n  color-scheme: light;\n  --color-bg: #000000;' in scss)
    # 3. эталоны баз проходят формат
    ref = reference_tokens()
    check_("эталон ui 09/04 §4 проходит формат DTCG (0 ошибок)",
           ref is not None and not [i for i in validate(ref) if i.severity == "error"])
    mk = json.loads(kbpaths.kb("creative", "04-visual-language", "marketing-tokens.json").read_text(encoding="utf-8"))
    errs = [i for i in validate(mk) if i.severity == "error"]
    check_("токены страниц creative (marketing-tokens.json) проходят формат DTCG"
           + (f" (есть: {errs[0].pointer} {errs[0].message})" if errs else ""), not errs)
    rt = Tokens(ref)
    rcss = build_css(rt)
    check_("эталон ui: сборка CSS — плотность, тёмная тема и сокращённое движение",
           '[data-density="compact"]' in rcss and ':root[data-theme="dark"]' in rcss
           and "prefers-reduced-motion" in rcss
           and "--space-md: 16px;" in rcss and "@media (width < 640px)" in rcss)
    check_("README: собранная часть сверяется по началу файла — хвост с новой строки, какой бы ни был, не расхождение; "
           "правка прозы и продолжение последней строки — расхождение",
           readme_fresh("# A\n\nтекст\n\n## Consuming this system\n…\n", "# A\n\nтекст\n")
           and readme_fresh("# A\n\nтекст\n\n## Как подключить систему\n…\n", "# A\n\nтекст\n")
           and readme_fresh("# A\n\nтекст\n", "# A\n\nтекст\n")
           and not readme_fresh("# A\n\nдругой\n", "# A\n\nтекст\n")
           and not readme_fresh("# A\n\nтекст и ещё слово\n", "# A\n\nтекст\n"))
    # 4. фикстура cabinet-ds
    kbpaths.use("tests")
    import fixture_project
    with fixture_project.built("cabinet-ds") as fx:
        prj = Project.of(fx.slug, fx.root)
        items = check(prj)
        loud = [f for f in items if f.severity in ("error", "warning")]
        check_("фикстура cabinet-ds: check — 0 error, 0 warning (производные свежие)"
               + (f" (есть: {'; '.join(f.rule + ' ' + f.ref + ' ' + f.message[:80] for f in loud[:3])})"
                  if loud else ""),
               not loud)
        done = build(prj)
        check_("build на свежей фикстуре ничего не меняет", done and not any(changed for _, changed in done))
        with tempfile.TemporaryDirectory(prefix="ddd-ds-cwd-") as cwd:
            r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "check", fx.slug, "--repo", str(fx.root),
                                "--json"], cwd=cwd, capture_output=True, text=True)
        try:
            lines = F.parse_lines(r.stdout)
        except ValueError:
            lines = None
        check_("check --json из чужой рабочей папки с --repo — код 0, строки находок",
               r.returncode == 0 and lines is not None and not [f for f in lines if f.severity == "error"])
        # правка значения без сборки
        raw = prj.tokens_path.read_text(encoding="utf-8")
        prj.tokens_path.write_text(raw.replace('"hex": "#1d4ed8"', '"hex": "#1e40af"', 1), encoding="utf-8")
        stale = [f for f in check(prj) if f.severity == "error"]
        got = {(f.rule, f.ref) for f in stale}
        check_("правка значения токена без build → R-FRESH-001 (CSS, передняя часть, tokens.json); у CSS подсказка "
               "называет цену пересборки — одобрения принятых макетов",
               {("R-FRESH-001", "tokens-css"), ("R-FRESH-001", "design-md#front-matter"),
                ("R-FRESH-001", "artifact#tokens.json")} <= got
               and [f.ref for f in stale if "одобрения" in f.fix] == ["tokens-css"])
        with tempfile.TemporaryDirectory(prefix="ddd-ds-out-") as od:
            build(prj, out=od)
            outp = Path(od) / prj.rel(prj.css_path)
            check_("build --out пишет в DIR/docs/projects/<slug>/…, проект не трогает",
                   outp.is_file() and "#1e40af" in outp.read_text(encoding="utf-8")
                   and "#1e40af" not in prj.css_path.read_text(encoding="utf-8"))
        build(prj)
        check_("после build — снова 0 error", not [f for f in check(prj) if f.severity == "error"])
        loose = json.loads(raw)
        loose["type"]["title"].setdefault("$extensions", {})[EXT_FLUID] = {"letter_spacing_em": 0.05}
        prj.tokens_path.write_text(json.dumps(loose, ensure_ascii=False, indent=2), encoding="utf-8")
        got = [f for f in check(prj) if f.rule == "R-STRUCT-006" and f.severity == "warning"]
        check_("трекинг в em расходится с px значения в токенах фикстуры → R-STRUCT-006 warning",
               got and "трекинг" in got[0].message)
        alien = json.loads(raw)
        alien["type"]["title"].setdefault("$extensions", {})["org.sample-tool.fluid"] = {"css": clamp}
        prj.tokens_path.write_text(json.dumps(alien, ensure_ascii=False, indent=2), encoding="utf-8")
        got = [f for f in check(prj) if f.rule == "R-STRUCT-006"]
        check_("ключ расширения вне известных в токенах фикстуры → одна находка R-STRUCT-006 warning с именем ключа и "
               "подсказкой",
               len(got) == 1 and got[0].severity == "warning" and "org.sample-tool.fluid" in got[0].message
               and got[0].fix and got[0].ref.endswith("/type/title/$extensions/org.sample-tool.fluid"))
        prj.tokens_path.write_text(raw.replace('"$value": "{primitive.color.accent.700}"',
                                               '"$value": "{primitive.color.nope}"', 1), encoding="utf-8")
        got = [f for f in check(prj) if f.rule == "R-STRUCT-006" and f.severity == "error"]
        check_("алиас в пустоту в токенах фикстуры → R-STRUCT-006", got and "в пустоту" in got[0].message)
        prj.tokens_path.write_text(raw.replace('{"value": 16, "unit": "px"}', '"16px"', 1), encoding="utf-8")
        got = [f for f in check(prj) if f.rule == "R-STRUCT-006" and f.severity == "error"]
        check_("битый $value (строка «16px» вместо dimension) → R-STRUCT-006", got and "не по форме" in got[0].message)
        (prj.css_path).unlink()
        prj.tokens_path.write_text(raw, encoding="utf-8")
        got = [f for f in check(prj) if f.rule == "R-FRESH-001" and f.ref == "tokens-css"]
        check_("нет производного CSS → R-FRESH-001", got and "производного нет" in got[0].message)
        # 5. загрузки артефакта: привязка по ответу загрузки
        icons = prj.tokens_path.parent / "_assets" / "icons"
        icons.mkdir(parents=True, exist_ok=True)
        for name in ("play.svg", "stop.svg"):
            (icons / name).write_text("<svg/>", encoding="utf-8")
        card = prj.art_dir / "components" / "MediaCard"
        card.mkdir(parents=True, exist_ok=True)
        was_id, play_id, cover_id = "a" * 32, "b" * 32, "c" * 32
        source = ('<img src="../../../../_assets/icons/play.svg" alt="">\n'
                  f'<img src="/_blob/{was_id}" alt="">\n'
                  '<img src="../../../../_assets/icons/stop.svg" alt="">\n'
                  '<i style="background: url(../../../../_assets/icons/play.svg)"></i>\n'
                  '<a href="https://example.org/">ссылка</a> <a href="../Button/preview.html">сосед</a>\n')
        (card / "preview.html").write_text(source, encoding="utf-8")
        files = {"cover.webp": {"name": "cover.webp", "blob": was_id, "size": 1, "type": "image/webp"},
                 "play.svg": {"name": "play.svg", "size": 6, "type": "image/svg+xml"}}
        (prj.art_dir / INDEX).write_text(json.dumps({"v": 3, "assetGroups": {"Media": {"name": "Media",
                                                                                      "files": files}}}),
                                         encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="ddd-ds-bind-") as od:
            answer = Path(od) / "answer.json"
            answer.write_text(json.dumps([{"file": "design/_assets/icons/play.svg", "id": play_id},
                                          {"name": "cover.webp", "url": f"/_blob/{cover_id}"}]), encoding="utf-8")
            done, items = bind_assets(prj, answer, Path(od) / "copy")
            copy_dir = Path(od) / "copy" / prj.rel(prj.art_dir)
            html = (copy_dir / "components" / "MediaCard" / "preview.html").read_text(encoding="utf-8")
            idx = json.loads((copy_dir / INDEX).read_text(encoding="utf-8"))["assetGroups"]["Media"]["files"]
            check_("привязка загрузок: ссылка на файл репозитория и url(…) → /_blob/<id>, id из индекса исходников → "
                   "id того же файла, blob записей индекса — по имени; чужие ссылки не тронуты",
                   html.count(f'/_blob/{play_id}') == 2 and f'src="/_blob/{cover_id}"' in html and was_id not in html
                   and 'href="https://example.org/"' in html and 'href="../Button/preview.html"' in html
                   and idx["cover.webp"]["blob"] == cover_id and idx["play.svg"]["blob"] == play_id)
            check_("файл без id в ответе загрузки: ссылка остаётся, находка R-REF-008 warning с путём файла; "
                   "исходники не меняются, копия полная",
                   'src="../../../../_assets/icons/stop.svg"' in html and len(items) == 1
                   and (items[0].rule, items[0].severity) == ("R-REF-008", "warning")
                   and "_assets/icons/stop.svg" in items[0].message
                   and (card / "preview.html").read_text(encoding="utf-8") == source
                   and (copy_dir / "tokens.json").is_file() and all(w for _, w in done))
            r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "artifact", fx.slug, "--repo",
                                str(fx.root), "--bind-assets", str(answer), "--out", str(Path(od) / "copy"), "--json"],
                               capture_output=True, text=True)
            r2 = subprocess.run([sys.executable, str(Path(__file__).resolve()), "artifact", fx.slug, "--repo",
                                 str(fx.root)], capture_output=True, text=True)
            check_("artifact --bind-assets --out --json — код 0 и строка находки; без ответа загрузки — код 2",
                   r.returncode == 0 and len(F.parse_lines(r.stdout)) == 1 and r2.returncode == F.EXIT_USAGE)
            bad, flat = Path(od) / "bad.json", Path(od) / "flat.json"
            bad.write_text(json.dumps([{"file": "play.svg"}]), encoding="utf-8")
            flat.write_text(json.dumps({"./icons/play.svg": play_id}), encoding="utf-8")
            refused = []
            for call_ in (lambda: upload_answer(bad), lambda: bind_assets(prj, answer, fx.root)):
                try:
                    call_()
                    refused.append(False)
                except F.ToolError:
                    refused.append(True)
            check_("ответ загрузки: словарь {файл: id} читается; запись без id — отказ; два разных id одного имени и "
                   "другой путь — файл не привязан; --out в исходники артефакта — отказ",
                   refused == [True, True] and upload_answer(flat) == [("icons/play.svg", play_id)]
                   and answer_id([("play.svg", play_id), ("x/play.svg", cover_id)], "play.svg") is None
                   and answer_id([("icons/play.svg", play_id)], "_assets/icons/play.svg") == play_id
                   and answer_id([("web/assets/play.svg", play_id)], "_assets/icons/play.svg") is None
                   and (card / "preview.html").read_text(encoding="utf-8") == source)
    print("ds_build selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


# ------------------------------------------------------------------ вызов

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    _reexec_venv()
    if "--selftest" in argv:
        try:
            return _selftest()
        except F.ToolError as e:
            print(f"ds_build: {e}", file=sys.stderr)
            return F.EXIT_USAGE
    ap = docpaths.parser("ds_build", __doc__, commands=("build", "check", "show", "artifact"), surface="none")
    ap.add_argument("--bind-assets", metavar="FILE",
                    help="команда artifact: ответ загрузки — JSON, список записей {file, id} или словарь {файл: id}")
    call = docpaths.parse(ap, argv)
    prj = Project.of(call.slug, call.repo)
    try:
        if call.command == "artifact":
            if not call.args.bind_assets or call.out is None:
                raise F.ToolError("artifact: нужны --bind-assets FILE (ответ загрузки) и --out DIR (куда писать копию)")
            done, items = bind_assets(prj, call.args.bind_assets, call.out)
            if not call.json:
                for p, w in done:
                    print(f"{'записан' if w else 'без изменений':<15} {p}")
            F.print_findings(items, as_json=call.json)
            return F.exit_code(items)
        if call.command == "check":
            items = check(prj)
            F.print_findings(items, as_json=call.json)
            return F.exit_code(items)
        if call.command == "show":
            show(prj, as_json=call.json)
            return F.EXIT_OK
        if not prj.tokens_path.is_file():
            raise F.ToolError(f"нет токенов DTCG: {prj.rel(prj.tokens_path)}")
        done = build(prj, call.out)
        if call.json:
            print(json.dumps([{"path": docpaths.rel(p, call.repo) if call.out is None else str(p), "written": w}
                              for p, w in done], ensure_ascii=False))
        else:
            for p, w in done:
                shown = docpaths.rel(p, call.repo) if call.out is None else p
                print(f"{'записан' if w else 'без изменений':<15} {shown}")
        return F.EXIT_OK
    except (F.ToolError, docpaths.DocPathError, OSError) as e:
        print(f"ds_build: {e}", file=sys.stderr)
        return F.EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
