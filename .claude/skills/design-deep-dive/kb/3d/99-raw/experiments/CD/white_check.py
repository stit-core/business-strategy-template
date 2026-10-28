#!/usr/bin/env python3
"""J/04 · яркость и теплота «белого пластика» на кадрах сцены (продолжатель J2 · 2026-09-25). Без браузера.

  python3 white_check.py DIR [DIR …] [--states hero,first-move] [--box 560,60,900,560]
Маска «белого»: яркость L (Rec.709) > 110 и насыщенность (max−min)/max < 0,18 в рамке, где стоит рука (кадр 960×600 из lp.py frames).
Печатает: число пикселей, медиану L (L50 — насколько светел белый в среднем, с тенями), L95 (белая точка), средний RGB верхних 10 %
по яркости и R−B (тёплый сдвиг белой точки; нейтральный белый — |R−B| ≤ 5).
"""
import argparse
import json

import numpy as np
from PIL import Image


def stats(path, box):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)[box[1]:box[3], box[0]:box[2]]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b
    m = (L > 110) & (sat < 0.18)
    if m.sum() < 50:
        return None
    Lm = L[m]
    top = m & (L >= np.percentile(Lm, 90))
    rgb = a[top].mean(axis=0)
    return {'n': int(m.sum()), 'L50': round(float(np.percentile(Lm, 50)), 1), 'L95': round(float(np.percentile(Lm, 95)), 1),
            'top_rgb': [int(round(x)) for x in rgb], 'R_minus_B': round(float(rgb[0] - rgb[2]), 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dirs', nargs='+')
    ap.add_argument('--states', default='hero,first-move')
    ap.add_argument('--box', default='560,60,900,560')
    a = ap.parse_args()
    box = [int(x) for x in a.box.split(',')]
    for d in a.dirs:
        for s in a.states.split(','):
            print(json.dumps({'dir': d, 'state': s, **(stats(f'{d}/{s}.png', box) or {})}, ensure_ascii=False))


if __name__ == '__main__':
    main()
