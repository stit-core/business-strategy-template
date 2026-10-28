#!/usr/bin/env python3
"""Все проверки примеров copy deck базы (kb/text/10-templates-recipes/examples/*.yaml) по порядку аудита текстов:
claims_check.py --legal-category → copy_lint.py → copydeck.py check → copydeck.py validate (+ validate на Python
окружения скилла с jsonschema) → copydeck.py export (вход холста этапа directions: pages/<page-id>/copy.md и facts.md).
JSON и выгрузки — в $DDD_HOME/out/text/run_checks/, сводка — таблицей Markdown (для 02-examples-ru.md и
03-examples-en.md) и summary.json. Код выхода: 0 — ни одной ошибки; 1 — есть ошибки (error в выводе проверок); 2 —
ошибка вызова (нет файла примера, он не copy deck, ключ --md без файла) или проверка не отработала (утилита завершилась
кодом 2 и выше: её вывод неполон — строка «не отработали» в stderr).
Запуск: python3 scripts/text/run_checks.py [пример.yaml …] [--md table.md]"""
import json, os, subprocess, sys, time, yaml
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import kbpaths  # noqa: E402
ROOT = str(kbpaths.kb('text'))
EX = os.path.join(ROOT, '10-templates-recipes', 'examples')
OUT = str(kbpaths.out('text', 'run_checks'))
T = str(kbpaths.scripts('text'))
TODAY = '2026-09-24'   # дата сверки примеров: сроки и «по состоянию на» демо-фактов считаются от неё
STAGE = 'directions'   # этап выгрузки во вход холста: тексты первого экрана assumed · checked · approved — примеры
                       # базы черновики агента (assumed), макет берёт только approved
VENV = kbpaths.python()


def run(cmd):
    t = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, round(time.time() - t, 1), p


def counts(js, key='summary'):
    s = (js or {}).get(key) or {}
    return s.get('error', 0), s.get('warning', 0), s.get('info', 0)


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    md_out = None
    if '--md' in argv:
        i = argv.index('--md')
        if i + 1 >= len(argv):
            print('run_checks: --md без файла таблицы', file=sys.stderr)
            return 2
        md_out = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    files = argv or sorted(os.path.join(EX, f) for f in os.listdir(EX) if f.endswith('.yaml'))
    decks = {}
    for path in files:
        try:
            with open(path, encoding='utf-8') as fi:
                decks[path] = yaml.safe_load(fi)['copy_deck']
        except (OSError, yaml.YAMLError, KeyError, TypeError) as e:
            print(f'run_checks: {path}: не copy deck ({type(e).__name__}: {e})', file=sys.stderr)
            return 2
    os.makedirs(OUT, exist_ok=True)
    rows, summ = [], {}
    for path in files:
        name = os.path.splitext(os.path.basename(path))[0]
        deck = decks[path]
        facts = os.path.normpath(os.path.join(os.path.dirname(path), deck['facts_ref']))
        cats = deck.get('legal_category') or ['general']
        cats = ','.join(cats if isinstance(cats, list) else [cats])
        r = {}
        j = os.path.join(OUT, f'{name}.claims.json')
        code, sec, _p = run([sys.executable, os.path.join(T, 'claims_check.py'), 'check', path, '--facts', facts, '--legal-category', cats,
                             '--today', TODAY, '--json', j, '--quiet'])
        r['claims'] = (code, sec, counts(json.load(open(j))) if os.path.exists(j) else None)
        j = os.path.join(OUT, f'{name}.lint.json')
        code, sec, p = run([sys.executable, os.path.join(T, 'copy_lint.py'), path, '--json'])
        try:
            lj = json.loads(p.stdout)
            open(j, 'w', encoding='utf-8').write(json.dumps(lj, ensure_ascii=False, indent=1))
            res = lj.get('results') or [{}]
            s = lj.get('summary') or (res[0] if isinstance(res, list) else res).get('summary') or {}
            r['lint'] = (code, sec, (s.get('error', 0), s.get('warning', 0), s.get('info', 0)))
        except Exception:  # noqa: BLE001
            r['lint'] = (code, sec, None)
        for cmd, key in (('check', 'check'), ('validate', 'validate')):
            j = os.path.join(OUT, f'{name}.{key}.json')
            code, sec, _p = run([sys.executable, os.path.join(T, 'copydeck.py'), cmd, path, '--today', TODAY, '--json', j, '--quiet'])
            r[key] = (code, sec, counts(json.load(open(j))) if os.path.exists(j) else None)
        if os.path.exists(VENV):
            j = os.path.join(OUT, f'{name}.validate-jsonschema.json')
            code, sec, _p = run([VENV, os.path.join(T, 'copydeck.py'), 'validate', path, '--today', TODAY, '--json', j, '--quiet'])
            r['jsonschema'] = (code, sec, counts(json.load(open(j))) if os.path.exists(j) else None)
        j = os.path.join(OUT, f'{name}.export.json')
        code, sec, _p = run([sys.executable, os.path.join(T, 'copydeck.py'), 'export', path, '--stage', STAGE,
                             '--out', os.path.join(OUT, name, 'input'), '--today', TODAY, '--json', j, '--quiet'])
        r['export'] = (code, sec, counts(json.load(open(j))) if os.path.exists(j) else None)
        summ[name] = {k: {'exit': v[0], 'sec': v[1], 'error': (v[2] or (None,))[0], 'warning': (v[2] or (None, None))[1],
                          'info': (v[2] or (None, None, None))[2]} for k, v in r.items()}
        cell = lambda v: '—' if v[2] is None else f'{v[2][0]} / {v[2][1]} / {v[2][2]}'
        rows.append(f"| `{name}` | {cell(r['claims'])} | {cell(r['lint'])} | {cell(r['check'])} | {cell(r['validate'])} | "
                    f"{cell(r['jsonschema']) if 'jsonschema' in r else '—'} | {cell(r['export'])} |")
        print(name, {k: (v[0], v[2]) for k, v in r.items()}, flush=True)
    head = ['| Пример | claims_check (error / warning / info) | copy_lint | copydeck check | copydeck validate | validate + jsonschema | '
            'copydeck export (directions) |',
            '|---|---|---|---|---|---|---|']
    table = '\n'.join(head + rows) + '\n'
    print(table)
    json.dump(summ, open(os.path.join(OUT, 'summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if md_out:
        open(md_out, 'w', encoding='utf-8').write(table)
    failed = [f"{n}: {k} (код {v['exit']})" for n, s in summ.items() for k, v in s.items() if v['exit'] not in (0, 1)]
    if failed:
        print('run_checks: не отработали — ' + '; '.join(failed), file=sys.stderr)
        return 2
    return 0 if all(v['error'] in (0, None) for s in summ.values() for v in s.values()) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
