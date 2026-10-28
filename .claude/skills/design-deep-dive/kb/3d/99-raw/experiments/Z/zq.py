#!/usr/bin/env python3
"""zq — обёртка над общим slot_run.py (оркестратор сессии 2, 26.09.2026). Прежняя версия (блокирующий flock в обход
очереди) — zq_v1.py. Её порядок «память до замков, без гонки опросом» перенесён в slot_run v2 — честную очередь по номерку
(FIFO) для всех дорожек; zq теперь просто ставит задачу в неё (--heavy всегда, как было).

    python3 zq.py [--kind blender|browser] [--min-mem 6000] [--wait 5400] [--label Z2-…] -- КОМАНДА …
    --kind browser — «тишина» для замеров: тяжёлый замок + замок браузера (= slot_run --kind browser --heavy)
"""
import os
import sys

SLOT_RUN = "/home/mm/Документы/app-design/blender-research/99-raw/tools/slot_run.py"


def main():
    a = sys.argv[1:]
    i = a.index("--")
    opts, cmd = a[:i], a[i + 1:]

    def opt(n, d):
        return opts[opts.index(n) + 1] if n in opts else d
    args = [sys.executable, SLOT_RUN, "--heavy", "--kind", opt("--kind", "blender"), "--min-mem", opt("--min-mem", "6000"),
            "--wait", opt("--wait", "5400"), "--label", opt("--label", "Z2"), "--"] + cmd
    os.execv(sys.executable, args)


if __name__ == "__main__":
    main()
