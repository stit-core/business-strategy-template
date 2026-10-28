#!/usr/bin/env python3
"""VD3/tools — запуск команды с замером реального пика памяти самого большого потомка (Blender):
ru_maxrss из getrusage(RUSAGE_CHILDREN) после ожидания = RSS наибольшего дождавшегося потомка (Linux, КБ).

    python3 peak.py КОМАНДА …      → код выхода команды; в конце строка «VD_PEAK_RSS_MB N» (stdout)
Нужен, чтобы ставить порог `slot_run --min-mem` по реальному пику процесса (оркестратор, 26.09.2026)."""
import resource
import subprocess
import sys


def main():
    cmd = sys.argv[1:]
    if not cmd:
        print(__doc__)
        return 2
    code = subprocess.call(cmd)
    peak_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0
    print(f"VD_PEAK_RSS_MB {peak_mb:.0f}", flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
