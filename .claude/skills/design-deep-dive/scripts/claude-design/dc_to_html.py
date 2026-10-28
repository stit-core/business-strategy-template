#!/usr/bin/env python3
"""dc_to_html — статичные HTML-копии артбордов холста Claude Design: перевод исходника `.dc.html` в обычный HTML.

Артборд холста (тип Design) — самодостаточная страница фиксированной ширины: разметка внутри `<x-dc>`, база и шрифты — в
`<helmet>`, логика и твики — в блоке `<script type="text/x-dc" data-dc-script data-props='…'>`, среда исполнения — строка
`support.js`. Локально такую страницу открывает только редактор типа, поэтому автопроверки макета (кадры, метки,
скрипты, сверка текстов и фактов) идут по статичной копии. Оригинал макета — холст в claude.ai: копии нужны скриптам
проверок, а не для просмотра, и собираются, когда заказчик попросил проверки макета (строка «Проверки макета:
разрешены» в ARTIFACTS.md). Правило перевода (claude-design/05-design-artifacts/02-staying-current.md §5; протокол
холста `references/claude-design.md § HTML-копии и kit`):
  - инлайн-стили и остальная разметка сохраняются байт в байт;
  - `<x-dc>`, `<helmet>`, блок логики и строка `support.js` снимаются, шрифты и базовые стили `<helmet>` уходят в `<head>`;
  - значения твиков подставляются: умолчания `data-props` (или `--tweak имя=значение`) проходят через `renderVals()`
    артборда в Node (изолированный контекст `vm`, без модулей и сети), дырки `{{путь}}` получают значения;
  - `<sc-if>` раскрывается по начальному состоянию, `<sc-for>` повторяет содержимое по списку, `<dc-import>` вставляет
    артборд-источник; обработчики событий (`onClick="{{…}}"` и другие) снимаются;
  - ссылки прототипа `X.dc.html` ведут на копию `X.html`; ширина окна копии — ширина рамки.
Копия — производная: руками не правится. В голове копии — строка о происхождении с отпечатком исходника и твиками: по
ней `check` узнаёт копию и находит устаревшие; в папке копий других HTML нет.

Команды (файлы проекта — через lib/docpaths.py: ключ --repo, переменная DDD_REPO или репозиторий скилла):
  dc_to_html.py build <slug> <surface> [--repo DIR] [--json]
      design/<surface>/canvas/project/<Имя>.dc.html → design/<surface>/canvas/html/<Имя>.html для артбордов canvas.json
      (без canvas.json — всех .dc.html); пишет только изменившиеся копии, снимает копии артбордов, которых больше нет.
  dc_to_html.py check <slug> <surface> [--repo DIR] [--json]
      правило R-FRESH-005 `design-audit`: у каждого артборда есть копия, копия равна переводу исходника, копий снятых
      артбордов нет (error); HTML без строки происхождения — не копия, в папке копий ему не место (warning). Ничего
      не пишет. Находки — строки JSON {rule, severity, surface, kind, ref, path, message, fix}.
  dc_to_html.py fingerprint <slug> <surface> [--artboards A.dc.html,B.dc.html] [--repo DIR] [--json]
      отпечаток артбордов (sha256 по именам и содержимому): он входит в отпечаток одобрения единицы в REVIEW.md
      (`ready show`), поэтому правка артборда снимает одобрение его единицы.
  dc_to_html.py convert <файл.dc.html | папка project> … [--out DIR] [--tweak имя=значение …] [--motion] [--json]
      перевод вне проекта (пример базы, снимок живой версии из scratchpad); по умолчанию —
      $DDD_HOME/out/claude-design/dc_to_html/. `--motion` — копия с движением для проверок этапа motion: файлы
      поддержки `lib/` артборда ложатся рядом с копией (набора движения нет в артборде — берётся из базы,
      kb/creative/11-motion-code/examples/motion-kit.js), после load копия зовёт `MotionKit.mount` на корне документа —
      то, что делает логика артборда; CSS набора приходит из `<helmet>`. Такая копия — цель `motion_check.py --spec` и
      `motion_probe.py probe`; в папку копий проекта она не идёт.
  dc_to_html.py --selftest      самопроверка на примере базы claude-design и фикстуре canvas, без сети

Коды выхода: 0 — готово, ошибок нет; 1 — есть находки error (check); 2 — ошибка вызова или окружения (нет проекта,
поверхности, исходников, Node для renderVals).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
import kbpaths  # noqa: E402
import docpaths  # noqa: E402

kbpaths.use("project")
import findings as FND  # noqa: E402

RULE = "R-FRESH-005"
MARK = "dc_to_html:"                                   # строка происхождения статичной копии (комментарий в <head>)
EXAMPLE = kbpaths.kb("claude-design", "05-design-artifacts", "example")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
HOLE = re.compile(r"\{\{\s*([^{}]*?)\s*\}\}")
ATTR = re.compile(r"""(\s+)([^\s=/>"']+)(?:(\s*=\s*)("[^"]*"|'[^']*'|[^\s>"']+))?""")
DC_HREF = re.compile(r"^([^#?]*?)\.dc\.html((?:[?#].*)?)$")
EVENT_ATTR = re.compile(r"^on[a-z]+$", re.I)
TIMEOUT_NODE = 60

# Этап страницы холста по её id и имени (протокол § Артефакты проекта: «Направления»; у сайта — «Креатив» и «Подача»
# этапа art-direction; «Макет и прототип», у кабинета — «Состояния»); неизвестное имя — макет.
STAGE_RX = (("directions", re.compile(r"направл|direction|moodboard|мудборд|style[- ]?tile|карточк", re.I)),
            ("treatment", re.compile(r"креатив|creative|подач|treatment", re.I)))

NODE_HARNESS = r"""
const vm = require('vm');
let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => { buf += d; });
process.stdin.on('end', () => {
  const inp = JSON.parse(buf);
  const out = inp.jobs.map(job => {
    try {
      const code = 'class DCLogic { constructor(props) { this.props = props || {}; this.state = {}; } ' +
        'setState(s) { this.state = Object.assign({}, this.state, typeof s === "function" ? s(this.state, this.props) : s); } }\n' +
        job.code + '\n;globalThis.__dcComponent = (typeof Component !== "undefined") ? Component : null;';
      const ctx = vm.createContext({console: {log() {}, info() {}, warn() {}, error() {}}});
      vm.runInContext(code, ctx, {timeout: 2000});
      const C = ctx.__dcComponent;
      if (!C) return {ok: false, error: 'в блоке логики нет class Component'};
      const c = new C(job.props);
      if (job.state) c.state = Object.assign({}, c.state || {}, job.state);
      const vals = typeof c.renderVals === 'function' ? c.renderVals() : {};
      return {ok: true, vals: JSON.parse(JSON.stringify(vals === undefined ? {} : vals,
        (k, v) => typeof v === 'function' ? {__dcFunction: true} : (v === undefined ? null : v)))};
    } catch (e) { return {ok: false, error: String((e && e.message) || e)}; }
  });
  process.stdout.write(JSON.stringify(out));
});
"""


class ToolError(RuntimeError):
    """Ошибка окружения или входа — код выхода 2."""


# ------------------------------------------------------------------ разбор: токены с исходным текстом и дерево

@dataclass
class El:
    tag: str
    attrs: dict
    raw: str                                           # начальный тег как в исходнике
    children: list = field(default_factory=list)
    end: str = ""                                      # закрывающий тег как в исходнике ("" — void или не закрыт)
    closed: bool = True


@dataclass
class Tx:
    raw: str
    kind: str = "text"                                 # text · comment · decl · stray


class _Tokens(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.starts = [0] + [m.end() for m in re.finditer("\n", text)]
        self.events = []

    def _pos(self):
        line, col = self.getpos()
        return self.starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        self.events.append(("start", self._pos(), tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.events.append(("startend", self._pos(), tag, attrs))

    def handle_endtag(self, tag):
        self.events.append(("end", self._pos(), tag, None))

    def handle_data(self, data):
        self.events.append(("text", self._pos(), None, None))

    handle_entityref = handle_charref = lambda self, name: self.events.append(("text", self._pos(), None, None))

    def handle_comment(self, data):
        self.events.append(("comment", self._pos(), None, None))

    def handle_decl(self, decl):
        self.events.append(("decl", self._pos(), None, None))

    unknown_decl = handle_decl

    def handle_pi(self, data):
        self.events.append(("decl", self._pos(), None, None))


def parse(text):
    """Исходник → (корень El '#root', заметки). Сумма исходных текстов узлов равна исходнику."""
    tk = _Tokens(text)
    tk.feed(text)
    tk.close()
    ev = tk.events
    root = El("#root", {}, "")
    stack, notes = [root], []
    for i, (kind, pos, tag, attrs) in enumerate(ev):
        raw = text[pos:ev[i + 1][1] if i + 1 < len(ev) else len(text)]
        if kind in ("start", "startend"):
            el = El(tag, {k.lower(): (v if v is not None else "") for k, v in attrs}, raw)
            stack[-1].children.append(el)
            if kind == "start" and tag not in VOID:
                stack.append(el)
        elif kind == "end":
            at = next((j for j in range(len(stack) - 1, 0, -1) if stack[j].tag == tag), None)
            if at is None:
                if tag not in VOID:
                    notes.append(f"лишний закрывающий тег </{tag}>")
                stack[-1].children.append(Tx(raw, "stray"))
                continue
            for el in stack[at + 1:]:
                el.closed = False
                notes.append(f"не закрыт тег <{el.tag}>")
            stack[at].end = raw
            del stack[at:]
        else:
            stack[-1].children.append(Tx(raw, kind))
    for el in stack[1:]:
        el.closed = False
        notes.append(f"не закрыт тег <{el.tag}> до конца файла")
    return root, notes


def walk(node):
    """Все узлы дерева в порядке документа."""
    yield node
    for ch in getattr(node, "children", ()):
        yield from walk(ch)


def find(node, pred):
    return next((n for n in walk(node) if isinstance(n, El) and pred(n)), None)


# ------------------------------------------------------------------ артборд: части, твики, значения

@dataclass
class Artboard:
    path: Path
    text: str
    root: El
    notes: list
    xdc: El | None
    helmet: El | None
    frame: El | None                                   # корень разметки — рамка артборда
    logic: El | None
    props_spec: dict
    preview: dict

    @property
    def name(self):
        return self.path.name

    @property
    def stem(self):
        return self.path.name[:-len(".dc.html")] if self.path.name.endswith(".dc.html") else self.path.stem


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_logic(el):
    return isinstance(el, El) and el.tag == "script" and ("data-dc-script" in el.attrs or el.attrs.get("type") == "text/x-dc")


def is_support(el):
    return isinstance(el, El) and el.tag == "script" and el.attrs.get("src", "").rstrip("/").endswith("support.js")


def load(path):
    """Прочитать и разобрать артборд `.dc.html`."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    root, notes = parse(text)
    xdc = find(root, lambda e: e.tag == "x-dc")
    helmet = find(xdc, lambda e: e.tag == "helmet") if xdc else None
    frame = next((c for c in (xdc.children if xdc else []) if isinstance(c, El) and c.tag != "helmet"), None)
    logic = find(root, is_logic)
    spec, preview = {}, {}
    if logic is not None and logic.attrs.get("data-props"):
        try:
            spec = json.loads(logic.attrs["data-props"])
        except json.JSONDecodeError as e:
            notes.append(f"data-props — не JSON: {e}")
    if isinstance(spec, dict):
        preview = spec.get("$preview") or {}
    else:
        spec = {}
    if xdc is None:
        notes.append("нет <x-dc>: не артборд типа Design")
    if not find(root, is_support):
        notes.append("нет строки <script src=\"./support.js\"></script>: артборд без среды исполнения типа")
    return Artboard(path, text, root, notes, xdc, helmet, frame, logic, spec, preview)


def logic_code(ab):
    return "".join(c.raw for c in ab.logic.children if isinstance(c, Tx)) if ab.logic is not None else ""


def defaults(ab):
    """Значения твиков по умолчанию из `data-props` (ключи `$…` — служебные)."""
    return {k: (v.get("default") if isinstance(v, dict) else None) for k, v in ab.props_spec.items() if not k.startswith("$")}


def parse_tweaks(items):
    """['имя=значение', …] → {имя: значение}; значение — JSON, если читается, иначе строка."""
    out = {}
    for it in items or []:
        k, sep, v = str(it).partition("=")
        if not sep or not k.strip():
            raise ToolError(f"--tweak: ожидается имя=значение, получено {it!r}")
        try:
            out[k.strip()] = json.loads(v)
        except json.JSONDecodeError:
            out[k.strip()] = v
    return out


def node_bin():
    return kbpaths.find("node")


def render_values(boards, tweaks=None):
    """Значения дырок каждого артборда: renderVals() в Node на умолчаниях твиков (с --tweak поверх). → [(vals, props)]."""
    jobs, out = [], []
    for ab in boards:
        props = dict(defaults(ab))
        props.update({k: v for k, v in (tweaks or {}).items() if k in props or not ab.props_spec})
        code = logic_code(ab)
        jobs.append({"code": code, "props": props} if code.strip() else None)
        out.append([None, props])
    todo = [j for j in jobs if j]
    if todo:
        node = node_bin()
        if not node:
            raise ToolError("нужен Node для renderVals() артбордов (системный Node; путь — kbpaths.py --bins)")
        try:
            r = subprocess.run([node, "-e", NODE_HARNESS], input=json.dumps({"jobs": todo}), capture_output=True,
                               text=True, timeout=TIMEOUT_NODE, env=kbpaths.node_env())
        except (OSError, subprocess.TimeoutExpired) as e:
            raise ToolError(f"Node не посчитал renderVals(): {e}") from e
        if r.returncode != 0:
            raise ToolError(f"Node не посчитал renderVals(): {r.stderr.strip()[:300]}")
        res = iter(json.loads(r.stdout))
    for i, j in enumerate(jobs):
        if j is None:
            out[i][0] = {}
            continue
        got = next(res)
        if got.get("ok"):
            out[i][0] = got.get("vals") or {}
        else:
            boards[i].notes.append(f"renderVals(): {got.get('error')} — дырки получат значения твиков как есть")
            out[i][0] = {}
    return [(v, p) for v, p in out]


# ------------------------------------------------------------------ перевод

def lookup(path, scope):
    """Значение дырки `{{a.b}}`: литерал (true, false, null, число, строка в кавычках) или поиск по точкам в значениях
    renderVals, затем в твиках. Нет — (False, None)."""
    if re.fullmatch(r"true|false|null|-?\d+(?:\.\d+)?|\"[^\"]*\"", path.strip()):
        return True, json.loads(path.strip())
    for base in scope:
        cur, ok = base, True
        for part in [p for p in path.split(".") if p != ""]:
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
                cur = cur[int(part)]
            else:
                ok = False
                break
        if ok and path.strip():
            return True, cur
    return False, None


def is_fn(v):
    return isinstance(v, dict) and v.get("__dcFunction") is True


def as_text(v):
    """Значение дырки строкой — как её показала бы страница."""
    if v is None or is_fn(v):
        return ""
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def truthy(v):
    """Истинность значения, как у условия страницы: false, 0, пустая строка и null — ложь."""
    if is_fn(v):
        return True
    return not (v is None or v is False or v == 0 or v == "")


class Translator:
    def __init__(self, ab, vals, props, folder=None, depth=0):
        self.ab, self.vals, self.props = ab, vals or {}, props or {}
        self.folder = Path(folder or ab.path.parent)
        self.depth = depth
        self.missing = []

    def value(self, expr, scope):
        ok, v = lookup(expr, scope)
        if not ok and expr not in self.missing:
            self.missing.append(expr)
        return v

    def sub_text(self, s, scope):
        return HOLE.sub(lambda m: html.escape(as_text(self.value(m.group(1), scope)), quote=False), s)

    def start_tag(self, el, scope):
        raw = el.raw
        if "{{" not in raw and ".dc.html" not in raw:
            return raw

        def one(m):
            lead, name, eq, val = m.group(1), m.group(2), m.group(3), m.group(4)
            if val is None:
                return m.group(0)
            q = val[0] if val[:1] in "\"'" else ""
            inner = val[1:-1] if q else val
            if "{{" in inner and EVENT_ATTR.match(name):
                return ""                              # обработчик события: в статичной копии не нужен
            if "{{" in inner:
                inner = HOLE.sub(lambda mm: as_text(self.value(mm.group(1), scope)), inner)
                inner = inner.replace("&", "&amp;").replace("<", "&lt;")
                if q:
                    inner = inner.replace(q, "&quot;" if q == '"' else "&#39;")
                elif not inner or re.search(r"[\s\"'=<>`]", inner):
                    q = '"'
                    inner = inner.replace('"', "&quot;")
            if name.lower() == "href":
                mm = DC_HREF.match(inner)
                if mm:
                    inner = f"{mm.group(1)}.html{mm.group(2)}"
            return f"{lead}{name}{eq or '='}{q}{inner}{q}"

        head = re.match(r"<[^\s/>]+", raw).group(0)
        close = re.search(r"\s*/?>\s*$", raw)
        body = raw[len(head):close.start()] if close else raw[len(head):]
        return head + ATTR.sub(one, body) + (close.group(0) if close else "")

    def children(self, nodes, scope, out, strip=False):
        """Дети узла; пустой отрезок пробелов перед снятым элементом снимается вместе с ним."""
        items = list(nodes)
        if strip:
            while items and isinstance(items[0], Tx) and items[0].kind == "text" and not items[0].raw.strip():
                items.pop(0)
            while items and isinstance(items[-1], Tx) and items[-1].kind == "text" and not items[-1].raw.strip():
                items.pop()
        pending = None
        for ch in items:
            if isinstance(ch, Tx) and ch.kind == "text" and not ch.raw.strip():
                if pending is not None:
                    out.append(pending)
                pending = ch.raw
                continue
            part = []
            self.node(ch, scope, part)
            if part:
                if pending is not None:
                    out.append(pending)
                out.extend(part)
            pending = None
        if pending is not None:
            out.append(pending)

    def node(self, n, scope, out):
        if isinstance(n, Tx):
            out.append(n.raw if n.kind in ("comment", "decl") else self.sub_text(n.raw, scope))
            return
        if n.tag == "helmet" or is_logic(n) or is_support(n):
            return
        if n.tag == "x-dc":
            self.children(n.children, scope, out, strip=True)
            return
        if n.tag == "sc-if":
            cond = n.attrs.get("value", "")
            m = HOLE.fullmatch(cond.strip())
            v = self.value(m.group(1), scope) if m else {"true": True, "false": False}.get(cond.strip().lower(), cond)
            if truthy(v):
                self.children(n.children, scope, out, strip=True)
            return
        if n.tag == "sc-for":
            m = HOLE.fullmatch(n.attrs.get("list", "").strip())
            items = self.value(m.group(1), scope) if m else None
            name = (n.attrs.get("as") or "item").strip()
            for i, it in enumerate(items if isinstance(items, list) else []):
                self.children(n.children, [{name: it, "index": i}] + scope, out, strip=True)
            return
        if n.tag == "dc-import":
            out.append(self.dc_import(n, scope))
            return
        out.append(self.start_tag(n, scope))
        self.children(n.children, scope, out)
        out.append(n.end)

    def dc_import(self, n, scope):
        name = (n.attrs.get("name") or n.attrs.get("src") or "").strip()
        src = self.folder / (name if name.endswith(".dc.html") else f"{name}.dc.html")
        if self.depth >= 3 or not name or not src.is_file():
            self.ab.notes.append(f"<dc-import name={name!r}>: артборд-источник не найден или вложенность глубже трёх")
            return f"<!-- dc-import {html.escape(name)}: источник не найден -->"
        child = load(src)
        over = {k: self.sub_text(v, scope) for k, v in n.attrs.items() if k not in ("name", "src")}
        (vals, props), = render_values([child], over)
        t = Translator(child, vals, props, self.folder, self.depth + 1)
        part = []
        if child.frame is not None:
            t.node(child.frame, [vals, props], part)
        self.ab.notes += [f"{child.name}: {x}" for x in child.notes]
        return "".join(part)

    def body(self):
        scope = [self.vals, self.props]
        out = []
        top = self.ab.xdc if self.ab.xdc is not None else self.ab.frame
        if top is not None:
            self.node(top, scope, out)
        return "".join(out)


def board_size(ab, board=None):
    """Ширина и высота рамки: canvas.json (boards), иначе $preview артборда, иначе стиль корня."""
    w = h = None
    if board:
        w, h = board.get("w"), board.get("h")
    if not w and ab.preview:
        w, h = ab.preview.get("width"), ab.preview.get("height")
    if not w and ab.frame is not None:
        st = ab.frame.attrs.get("style", "")
        mw, mh = re.search(r"(?<![-\w])width:\s*(\d+)px", st), re.search(r"(?<![-\w])height:\s*(\d+)px", st)
        w, h = (int(mw.group(1)) if mw else None), (int(mh.group(1)) if mh else None)
    return w, h


def frame_notes(ab, w, h):
    """Корень артборда фиксированного размера, равного рамке (cd 05/01 §3.1)."""
    notes = []
    if ab.frame is None:
        return ["нет корня разметки внутри <x-dc>"]
    st = ab.frame.attrs.get("style", "")
    mw, mh = re.search(r"(?<![-\w])width:\s*(\d+)px", st), re.search(r"(?<![-\w])height:\s*(\d+)px", st)
    if w and (not mw or int(mw.group(1)) != int(w)):
        notes.append(f"ширина корня {mw.group(1) + 'px' if mw else '—'} ≠ рамке {w}px")
    if h and (not mh or int(mh.group(1)) != int(h)):
        notes.append(f"высота корня {mh.group(1) + 'px' if mh else '—'} ≠ рамке {h}px")
    pw, ph = ab.preview.get("width"), ab.preview.get("height")
    if w and pw and int(pw) != int(w) or h and ph and int(ph) != int(h):
        notes.append(f"$preview {pw}×{ph} ≠ рамке {w}×{h}")
    return notes


def translate(ab, vals, props, board=None):
    """Артборд → текст статичной копии (детерминированно: одни исходник и твики — одни байты)."""
    w, h = board_size(ab, board)
    t = Translator(ab, vals, props)
    body = t.body()
    head_el = find(ab.root, lambda e: e.tag == "head")
    html_el = find(ab.root, lambda e: e.tag == "html")
    body_el = find(ab.root, lambda e: e.tag == "body")
    tweaks = ", ".join(f"{k}={as_text(v)}" for k, v in sorted(props.items())) or "—"
    mark = (f"<!-- {MARK} статичная копия артборда {ab.name}; перевод исходника, руками не правится · исходник sha256 "
            f"{sha256_text(ab.text)} · рамка {w or '?'}×{h or '?'} · твики: {tweaks} -->")
    head = []
    if head_el is not None:
        head.append(head_el.raw)
        tr = Translator(ab, vals, props)
        tr.children([c for c in head_el.children], [vals, props], head)
    else:
        head.append("<head>\n")
    text = "".join(head).rstrip()
    viewport = f'<meta name="viewport" content="width={w}">' if w else ""
    has_vp = head_el is not None and find(head_el, lambda e: e.tag == "meta" and e.attrs.get("name") == "viewport")
    helmet = []
    if ab.helmet is not None:
        Translator(ab, vals, props).children(ab.helmet.children, [vals, props], helmet, strip=True)
    lines = [text] + ([viewport] if viewport and not has_vp else []) + [mark] + (["".join(helmet)] if helmet else [])
    head_txt = "\n".join(lines) + "\n" + (head_el.end if head_el is not None and head_el.end else "</head>")
    doctype = next((c.raw.strip() for c in ab.root.children if isinstance(c, Tx) and c.kind == "decl"), "<!doctype html>")
    html_open = html_el.raw.strip() if html_el is not None else '<html lang="ru">'
    body_open = body_el.raw.strip() if body_el is not None else "<body>"
    missing = [m for m in t.missing if not m.startswith("__")]
    if missing:
        ab.notes.append("дырки без значения: " + ", ".join("{{" + m + "}}" for m in missing))
    return f"{doctype}\n{html_open}\n{head_txt}\n{body_open}\n{body.strip()}\n</body>\n</html>\n"


# ------------------------------------------------------------------ холст: canvas.json, этапы, отпечаток

def load_canvas(folder):
    """canvas.json папки исходников холста → {'boards': {файл: запись}, 'order': [файлы], 'pages': {id: имя}} или None."""
    p = Path(folder) / "canvas.json"
    if not p.is_file():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ToolError(f"{p}: canvas.json — не JSON ({e})") from e
    boards = d.get("boards") or {}
    order = [f for f in (d.get("order") or []) if f in boards] + sorted(f for f in boards if f not in (d.get("order") or []))
    pages = {str(x.get("id")): str(x.get("name") or "") for x in d.get("pages") or [] if isinstance(x, dict)}
    return {"boards": boards, "order": order, "pages": pages, "title": d.get("title") or ""}


def artboard_files(folder, canvas=None):
    """Артборды папки исходников: по canvas.json (порядок `order`), без него — все .dc.html по имени."""
    folder = Path(folder)
    canvas = canvas if canvas is not None else load_canvas(folder)
    if canvas:
        return [folder / f for f in canvas["order"] if (folder / f).is_file() and f.endswith(".dc.html")]
    return sorted(folder.glob("*.dc.html"))


def stage_of(board, canvas):
    """Этап страницы холста, на которой лежит артборд: directions · treatment · mockup."""
    if not board or not canvas:
        return "mockup"
    pid = str(board.get("page") or "")
    label = f"{pid} {canvas['pages'].get(pid, '')}"
    for stage, rx in STAGE_RX:
        if rx.search(label):
            return stage
    return "mockup"


def fingerprint(paths):
    """Отпечаток артбордов: sha256 по строкам «имя:sha256 содержимого», отсортированным по имени."""
    rows = sorted(f"{Path(p).name}:{hashlib.sha256(Path(p).read_bytes()).hexdigest()}" for p in paths)
    return "sha256:" + hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def copy_name(ab_path):
    name = Path(ab_path).name
    return (name[:-len(".dc.html")] if name.endswith(".dc.html") else Path(name).stem) + ".html"


def copy_source(text):
    """Имя артборда из строки происхождения статичной копии; не копия — None."""
    m = re.search(r"<!--\s*" + re.escape(MARK) + r"\s*статичная копия артборда (\S+?);", text or "")
    return m.group(1) if m else None


def build_copies(src_dir, tweaks=None):
    """Переводы артбордов папки: [(артборд, имя копии, текст, запись canvas.json, заметки)]."""
    src_dir = Path(src_dir)
    canvas = load_canvas(src_dir)
    files = artboard_files(src_dir, canvas)
    boards = [load(p) for p in files]
    out = []
    for ab, (vals, props) in zip(boards, render_values(boards, tweaks)):
        board = (canvas or {}).get("boards", {}).get(ab.name) if canvas else None
        text = translate(ab, vals, props, board)
        w, h = board_size(ab, board)
        ab.notes += frame_notes(ab, w, h)
        out.append((ab, copy_name(ab.path), text, board, ab.notes))
    return out


# ------------------------------------------------------------------ команды

def surface_dirs(call):
    src = docpaths.design(call.slug, "canvas-project", surface=call.surface, repo=call.repo)
    dst = docpaths.design(call.slug, "canvas-html", surface=call.surface, repo=call.repo)
    return src, dst


def cmd_build(call):
    src, dst = surface_dirs(call)
    if not src.is_dir():
        raise ToolError(f"нет исходников холста: {docpaths.rel(src, call.repo)}")
    copies = build_copies(src)
    dst.mkdir(parents=True, exist_ok=True)
    written, same, removed, notes = [], [], [], []
    keep = set()
    for ab, name, text, _board, nts in copies:
        p = dst / name
        keep.add(name)
        if p.is_file() and p.read_text(encoding="utf-8") == text:
            same.append(name)
        else:
            p.write_text(text, encoding="utf-8")
            written.append(name)
        notes += [f"{ab.name}: {n}" for n in nts]
    for p in sorted(dst.glob("*.html")):
        if p.name not in keep and copy_source(p.read_text(encoding="utf-8", errors="replace")):
            p.unlink()
            removed.append(p.name)
    res = {"dir": docpaths.rel(dst, call.repo), "written": written, "unchanged": same, "removed": removed, "notes": notes}
    if call.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(f"{res['dir']}: записано {len(written)}, без изменений {len(same)}, снято {len(removed)}")
        for n in written:
            print(f"  + {n}")
        for n in removed:
            print(f"  − {n}")
        for n in notes:
            print(f"  заметка: {n}", file=sys.stderr)
    return 0


def check_copies(call):
    """Находки R-FRESH-005 по статичным копиям поверхности."""
    src, dst = surface_dirs(call)
    rep = FND.Report()
    if not src.is_dir():
        return rep
    fix = f"dc_to_html build {call.slug} {call.surface} — копии пересобираются из исходников, руками не правятся"
    names = set()
    for ab, name, text, _board, _notes in build_copies(src):
        names.add(name)
        p = dst / name
        rel = docpaths.rel(p, call.repo)
        if not p.is_file():
            rep.add(RULE, "error", surface=call.surface, kind="copy", ref=name, path=rel,
                    message=f"нет статичной копии артборда {ab.name}", fix=fix)
        elif p.read_text(encoding="utf-8") != text:
            rep.add(RULE, "error", surface=call.surface, kind="copy", ref=name, path=rel,
                    message=f"копия не равна переводу исходника {ab.name}: правлена руками или исходник изменился после "
                            "сборки", fix=fix)
    if dst.is_dir():
        for p in sorted(dst.glob("*.html")):
            ab = copy_source(p.read_text(encoding="utf-8", errors="replace"))
            if ab and p.name not in names:
                rep.add(RULE, "error", surface=call.surface, kind="copy", ref=p.name, path=docpaths.rel(p, call.repo),
                        message=f"копия артборда {ab}, которого нет в исходниках холста", fix=fix)
            elif not ab:
                rep.add(RULE, "warning", surface=call.surface, kind="copy", ref=p.name, path=docpaths.rel(p, call.repo),
                        message="HTML без строки происхождения dc_to_html — не копия артборда: в папке копий только "
                                "производные копии, все ширины макета — артборды холста",
                        fix="убрать файл из canvas/html/; нужная ширина или состояние — артбордом на холсте")
    return rep


def cmd_check(call):
    rep = check_copies(call)
    FND.print_findings(rep.items, as_json=call.json,
                       title=None if call.json else f"dc_to_html check {call.slug} {call.surface}")
    return rep.exit_code()


def cmd_fingerprint(call):
    src, _dst = surface_dirs(call)
    want = [x.strip() for x in (call.args.artboards or "").split(",") if x.strip()]
    files = [src / w for w in want] if want else artboard_files(src)
    miss = [docpaths.rel(p, call.repo) for p in files if not p.is_file()]
    if miss or not files:
        raise ToolError("нет артбордов: " + (", ".join(miss) or docpaths.rel(src, call.repo)))
    fp = fingerprint(files)
    if call.json:
        print(json.dumps({"artboards": [p.name for p in files], "fingerprint": fp}, ensure_ascii=False))
    else:
        print(fp)
    return 0


MOTION_KIT = kbpaths.kb("creative") / "11-motion-code" / "examples" / "motion-kit.js"
MOTION_RUN = ("<script>addEventListener('load', function () { var root = document.documentElement; "
              "if (window.MotionKit) { window.__motionKit = MotionKit.mount(root); root.setAttribute('data-motion-copy', 'mounted'); } "
              "else { root.setAttribute('data-motion-copy', 'no-kit'); } });</script>")


def motion_copy(text, src_dir, out_dir):
    """Копия с движением: lib/ артборда рядом, набор из базы, если артборд его не подключил, запуск MotionKit.mount после
    load. Возвращает (текст, заметки)."""
    notes = []
    lib = Path(src_dir) / "lib"
    if lib.is_dir():
        shutil.copytree(lib, Path(out_dir) / "lib", dirs_exist_ok=True)
    linked = "motion-kit.js" in text
    if not linked:
        text = text.replace("</head>", '<script src="./lib/motion-kit.js"></script>\n</head>', 1)
        notes.append("артборд не подключил набор движения: в копию добавлен набор базы")
    kit = Path(out_dir) / "lib" / "motion-kit.js"
    if not kit.is_file():
        if not MOTION_KIT.is_file():
            raise ToolError(f"нет набора движения базы: {MOTION_KIT}")
        kit.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MOTION_KIT, kit)
        if linked:
            notes.append("файла набора нет рядом с артбордом (lib/): в копию положен набор базы")
    if "data-mk=" in text and "[data-mk" not in text:
        notes.append("разметка набора есть, а CSS набора в <helmet> — нет: движение копии без стилей набора")
    return text.replace("</body>", MOTION_RUN + "\n</body>", 1), notes


def cmd_convert(a):
    tweaks = parse_tweaks(a.tweak)
    out_dir = Path(a.out) if a.out else kbpaths.out("claude-design", "dc_to_html")
    res = {"out": str(out_dir), "files": [], "notes": []}
    for s in a.source:
        s = Path(s)
        if s.is_dir():
            copies = build_copies(s, tweaks)
        elif s.is_file():
            canvas = load_canvas(s.parent)
            ab = load(s)
            (vals, props), = render_values([ab], tweaks)
            board = (canvas or {}).get("boards", {}).get(ab.name) if canvas else None
            text = translate(ab, vals, props, board)
            ab.notes += frame_notes(ab, *board_size(ab, board))
            copies = [(ab, copy_name(s), text, board, ab.notes)]
        else:
            raise ToolError(f"нет файла или папки: {s}")
        out_dir.mkdir(parents=True, exist_ok=True)
        for ab, name, text, _board, nts in copies:
            if getattr(a, "motion", False):
                text, more = motion_copy(text, Path(ab.path).parent, out_dir)
                nts = list(nts) + more
            (out_dir / name).write_text(text, encoding="utf-8")
            res["files"].append(str(out_dir / name))
            res["notes"] += [f"{ab.name}: {n}" for n in nts]
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        for f in res["files"]:
            print(f)
        for n in res["notes"]:
            print(f"заметка: {n}", file=sys.stderr)
    return 0


# ------------------------------------------------------------------ самопроверка

def selftest():
    import tempfile
    ok = True

    def check(name, got, want=True):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"{'OK  ' if good else 'FAIL'} {name}" + ("" if good else f": {got!r} (ожидалось {want!r})"))

    src = EXAMPLE / "canvas" / "project"
    for p in sorted(src.glob("*.dc.html")):
        t = p.read_text(encoding="utf-8")
        root, notes = parse(t)
        check(f"разбор {p.name}: узлы складываются в исходник", "".join(_raw(root)), t)
        check(f"разбор {p.name}: теги закрыты", notes, [])
    pages = {"p1": "1 · Направления", "p2": "Креатив", "p3": "Подача", "p4": "2 · Макет и прототип", "p5": "Состояния"}
    check("этап страницы: «Направления» — directions, «Креатив» и «Подача» — treatment, остальные — mockup",
          [stage_of({"page": p}, {"pages": pages}) for p in sorted(pages)],
          ["directions", "treatment", "treatment", "mockup", "mockup"])
    if not node_bin():
        print("FAIL нет Node: renderVals() артбордов не посчитать")
        return 1
    copies = {name: text for _ab, name, text, _b, _n in build_copies(src)}
    check("шесть артбордов → шесть копий", sorted(copies), sorted(copy_name(p) for p in src.glob("*.dc.html")))
    main = copies["Main.html"]
    for bad in ("{{", "<x-dc", "<helmet", "data-dc-script", "support.js", "DCLogic"):
        check(f"Main.html: нет «{bad}»", bad in main, False)
    check("Main.html: шрифты и база в <head>", main.index("fonts.googleapis.com") < main.index("</head>")
          and main.index("a{color:#2146D8}") < main.index("</head>"), True)
    check("Main.html: твик радиуса 6 и карточки 12 (r * 2 в renderVals)",
          ("border-radius: 6px" in main, "border-radius: 12px" in main), (True, True))
    check("Main.html: ширина окна = рамке", '<meta name="viewport" content="width=1440">' in main, True)
    check("Main.html: ссылка прототипа ведёт на копию", 'href="Booking.html"' in main and ".dc.html\"" not in main, True)
    check("Main.html: строка происхождения", copy_source(main), "Main.dc.html")
    bk = copies["Booking.html"]
    check("Booking.html: sc-if showForm — форма есть", "Отправить заявку" in bk, True)
    check("Booking.html: sc-if sent — подтверждения нет", "Заявка отправлена" in bk, False)
    check("Booking.html: обработчики событий сняты", re.search(r"on(Submit|Change|Click)=", bk) is None, True)
    check("Booking.html: тёмная тема по умолчанию твика", "background: #0C0F14" in bk, True)
    lp = copies["Landing-Phone.html"]
    check("Landing-Phone.html: меню закрыто (sc-if menuOpen)", 'aria-label="Разделы"' in lp, False)
    check("Landing-Phone.html: aria-expanded из дырки", 'aria-expanded="false"' in lp, True)
    again = {name: text for _ab, name, text, _b, _n in build_copies(src)}
    check("перевод детерминирован", again == copies, True)
    light = {name: text for _ab, name, text, _b, _n in build_copies(src, {"dark": False})}
    check("--tweak dark=false: светлая тема", "background: #EEF2F6" in light["Booking.html"]
          and "твики: dark=false" in light["Booking.html"], True)
    syn = ('<!doctype html><html><head><meta charset="utf-8"><script src="./support.js"></script></head><body><x-dc>'
           '<helmet><style>body{margin:0}</style></helmet><div style="width: 200px; height: 100px;"><ul>'
           '<sc-for list="{{ items }}" as="it" hint-placeholder-count="{{ 2 }}"><li>{{ it.t }}</li></sc-for></ul>'
           '<p>{{ nope }}</p></div></x-dc><script type="text/x-dc" data-dc-script data-props=\'{"$preview":{"width":200,'
           '"height":100}}\'>class Component extends DCLogic { renderVals() { return {items: [{t: "A &amp; B"}, {t: "<b>"}]}; } }'
           '</script></body></html>')
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "Syn.dc.html"
        p.write_text(syn, encoding="utf-8")
        ab = load(p)
        (vals, props), = render_values([ab])
        out = translate(ab, vals, props)
        check("sc-for повторяет содержимое, текст экранирован", "<li>A &amp;amp; B</li><li>&lt;b&gt;</li>" in out, True)
        check("дырка без значения — заметка", any("{{nope}}" in n for n in ab.notes), True)
        broken = Path(td) / "Broken.dc.html"
        broken.write_text(syn.replace("</ul>", ""), encoding="utf-8")
        check("незакрытый тег — заметка", any("не закрыт тег <ul>" in n for n in load(broken).notes), True)
        a, b = Path(td) / "a.dc.html", Path(td) / "b.dc.html"
        a.write_text("A", encoding="utf-8")
        b.write_text("B", encoding="utf-8")
        fp0 = fingerprint([a, b])
        check("отпечаток не зависит от порядка", fingerprint([b, a]), fp0)
        b.write_text("B2", encoding="utf-8")
        check("отпечаток меняется с исходником", fingerprint([a, b]) != fp0, True)
    kbpaths.use("tests")
    import fixture_project
    with fixture_project.built("canvas") as fx:
        argv = [fx.slug, "promo", "--repo", str(fx.root)]
        rc_b = _run(["build"] + argv + ["--json"])
        check("фикстура canvas: build — код 0", rc_b[0], 0)
        check("фикстура canvas: build — шесть копий", len(json.loads(rc_b[1])["written"]), 6)
        check("фикстура canvas: check после build — 0 находок", _run(["check"] + argv + ["--json"]), (0, ""))
        html_dir = docpaths.design(fx.slug, "canvas-html", surface="promo", repo=fx.root)
        (html_dir / "Main.html").write_text((html_dir / "Main.html").read_text(encoding="utf-8").replace(
            "Обслужим велосипед", "Починим велосипед"), encoding="utf-8")
        (html_dir / "Dir-Paper.html").unlink()
        (html_dir / "home.html").write_text("<!doctype html><title>страница</title>", encoding="utf-8")
        rc, out = _run(["check"] + argv + ["--json"])
        items = FND.parse_lines(out)
        check("правка копии и пропавшая копия — две находки R-FRESH-005 error; HTML без строки происхождения — warning",
              (rc, sorted((f.rule, f.severity, f.ref) for f in items)),
              (1, [(RULE, "error", "Dir-Paper.html"), (RULE, "error", "Main.html"), (RULE, "warning", "home.html")]))
        (html_dir / "home.html").unlink()
        check("build чинит копии", _run(["build"] + argv)[0] == 0 and _run(["check"] + argv + ["--json"]) == (0, ""), True)
        fp1 = _run(["fingerprint"] + argv)[1].strip()
        check("fingerprint — sha256", fp1.startswith("sha256:") and len(fp1) == 71, True)
        check("нет поверхности — код 2", _run(["check", fx.slug, "nope", "--repo", str(fx.root)])[0], 2)
    adapter = MOTION_KIT.parent / "artboard-adapter.dc.html"
    if adapter.is_file():
        with tempfile.TemporaryDirectory() as td:
            ns = argparse.Namespace(source=[str(adapter)], out=td, tweak=None, motion=True, json=True)
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                cmd_convert(ns)
            copy = (Path(td) / "artboard-adapter.html").read_text(encoding="utf-8")
            check("--motion: копия зовёт MotionKit.mount после load и подключает набор",
                  MOTION_RUN in copy and copy.count('src="./lib/motion-kit.js"') == 1, True)
            check("--motion: набор лежит рядом с копией (lib/motion-kit.js базы)",
                  (Path(td) / "lib" / "motion-kit.js").read_bytes() == MOTION_KIT.read_bytes(), True)
            check("--motion: CSS набора пришёл из <helmet>", "[data-mk" in copy, True)
    print("selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def _raw(node):
    if isinstance(node, Tx):
        yield node.raw
        return
    if node.tag != "#root":
        yield node.raw
    for ch in node.children:
        yield from _raw(ch)
    if node.tag != "#root":
        yield node.end


def _run(args):
    r = subprocess.run([sys.executable, str(Path(__file__).resolve())] + args, capture_output=True, text=True)
    return r.returncode, r.stdout


# ------------------------------------------------------------------ вызов

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv[:1] == ["convert"]:
            ap = argparse.ArgumentParser(prog="dc_to_html.py convert", description="Перевод артбордов вне проекта.")
            ap.add_argument("cmd")
            ap.add_argument("source", nargs="+", help="файл .dc.html или папка исходников холста (с canvas.json)")
            ap.add_argument("--out", help="папка копий (по умолчанию $DDD_HOME/out/claude-design/dc_to_html/)")
            ap.add_argument("--tweak", action="append", help="значение твика: имя=значение (JSON или строка); повтором")
            ap.add_argument("--motion", action="store_true",
                            help="копия с движением: lib/ рядом, набор движения и запуск MotionKit.mount после load")
            ap.add_argument("--json", action="store_true")
            return cmd_convert(ap.parse_args(argv))
        ap = docpaths.parser("dc_to_html.py", __doc__, commands=("build", "check", "fingerprint"), surface="required",
                             accept=lambda s: s.design)
        ap.add_argument("--artboards", help="fingerprint: артборды через запятую (по умолчанию — все по canvas.json)")
        call = docpaths.parse(ap, argv)
        if call.selftest:
            return selftest()
        return {"build": cmd_build, "check": cmd_check, "fingerprint": cmd_fingerprint}[call.command](call)
    except ToolError as e:
        print(f"dc_to_html: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
