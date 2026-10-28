#!/usr/bin/env python3
"""lint_agent_code.py — самопроверка текста скрипта агента регулярными выражениями до отправки в Blender: CLI из кода
lint_agent_code() в kb/3d/02-blender-workflow/03-patterns-antipatterns.md §6, код ниже — как напечатан там, без
изменений.

  python3 lint_agent_code.py script.py [script2.py …]     # свои файлы
  python3 lint_agent_code.py -                             # или без аргументов вовсе — то же: текст со stdin

Печатает в stdout JSON {путь: [[код, уровень, совет], …]} (путь "-" — для stdin). Код выхода: 0 — замечаний нет ни в
одном файле, 1 — есть хотя бы одно (ERROR или WARN). Это дешёвый фильтр текста скрипта до его исполнения в Blender
(регулярки ловят текст, не смысл) — не заменяет проверку результата после запуска (blender `03-bpy-api/04-llm-failure-modes… §3`).
Уровни: ERROR — не отправлять в сцену человека; WARN — допустимо в своём фоновом файле агента (`orphans_purge`,
настройки рендера своей сцены превью — см. `SCENE_SETTINGS`).

Проверено на 24 скриптах «первой попытки» трёх моделей: срабатывания на файл совпадают с прогоном того же блока кода,
извлечённого из статьи регулярным выражением.

`.fcurves` — ошибка, только если получатель не channelbag и не NLA-полоса (OLD_FCURVES): правильный `channelbag.fcurves`
Blender 5.x (дрейф № 68) не ловится; тот же код — в `02/03 §6`.
"""
import json
import re
import sys

# `.fcurves` в Blender 5.2 есть только у ActionChannelbag и NlaStrip (проверено по RNA Blender 5.2); у Action удалён в 5.0.
# Ловим `.fcurves` после любого получателя, кроме: имени с «bag»/«cb…»/«nla» (channelbag, cb, bag, channel_bag, nla_strip),
# вызова `…channelbag…(…)` (`strip.channelbag(slot)`, `anim_utils.action_get_channelbag_for_slot(act, slot)`) и функции
# помощника `x.fcurves(…)` (`animx.fcurves(ob)`). Ловится: action.fcurves, act.fcurves.new(…), ob.animation_data.action.fcurves,
# bpy.data.actions["A"].fcurves, bpy.types.Action.fcurves. Регулярка ловит текст: другое имя переменной channelbag — сработает.
OLD_FCURVES = r"\b(?![Cc]b|\w*[Bb]ag|\w*[Nn]la)\w+(?:\((?:[^()]|\([^()]*\))*\)|\[[^\]]*\])*\.fcurves\b(?!\s*\()"

RULES = [  # (код, уровень, шаблон, что делать)
    ("WIPE_SCENE", "ERROR", r"select_all\(\s*action\s*=\s*['\"]SELECT['\"]\s*\)[\s\S]{0,200}?object\.delete", "своя коллекция и тег (01 §1–2)"),
    ("WIPE_FILE", "ERROR", r"for\s+\w+\s+in\s+(?:list\()?bpy\.data\.objects\)?\s*:\s*[\s\S]{0,80}?objects\.remove", "удалять только своё по тегу"),
    ("PURGE_ALL", "WARN", r"orphans_purge\(", "в сцене человека — уборка своего по тегу"),
    ("RESET_FILE", "ERROR", r"read_factory_settings|read_homefile", "только в своём фоновом процессе"),
    ("EXIT", "ERROR", r"\bsys\.exit\(|(?<![\w.])(?:exit|quit)\(\s*\)", "raise вместо выхода (M7.1)"),
    ("BARE_EXCEPT", "WARN", r"except\s*:|except\s+Exception\s*:\s*pass", "ловить конкретное и пробрасывать причину"),
    ("GLOBAL_LOGGING", "WARN", r"logging\.basicConfig\(", "не трогать глобальное состояние Blender"),
    ("SHIFT_DELETE", "ERROR", r"location(?:\.x|\[0\])\s*\+=\s*\d{3,}", "удалить объект, а не сдвигать"),
    ("NODE_BY_NAME", "ERROR", r"nodes(?:\[|\.get\()\s*['\"]Principled BSDF['\"]", "по type: BSDF_PRINCIPLED (B4.5)"),
    ("USE_NODES", "WARN", r"\.use_nodes\s*=\s*True", "устарело в 5.x, удаление в 6.0"),
    ("APPLY_MOVES_ORIGIN", "ERROR", r"transform_apply\((?![^)]*location\s*=\s*False)[^)]*\)", "location=False (умолчание True) — 01 §7.1"),
    ("SCENE_SETTINGS", "WARN", r"\bengine\s*=\s*['\"]", "в сцене человека — своя сцена превью (01 §3)"),
    ("CYCLES_NO_SAMPLES", "WARN", r"engine\s*=\s*['\"]CYCLES['\"](?![\s\S]*cycles\.samples\b[^\n]*=)", "явные сэмплы (умолчание 4096)"),
    ("OLD_API", "ERROR", r"BLENDER_EEVEE_NEXT|use_auto_smooth|scene\.node_tree|" + OLD_FCURVES, "таблица дрейфа B 03 §4"),
]


def lint_agent_code(src):
    """Список (код, уровень, совет) для текста скрипта; пустой — нарушений из списка нет."""
    return [(code, level, hint) for code, level, pat, hint in RULES if re.search(pat, src)]


def main():
    paths = sys.argv[1:] or ["-"]
    out = {}
    for p in paths:
        src = sys.stdin.read() if p == "-" else open(p, encoding="utf-8").read()
        out[p] = [list(x) for x in lint_agent_code(src)]
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(1 if any(out.values()) else 0)


if __name__ == "__main__":
    main()
