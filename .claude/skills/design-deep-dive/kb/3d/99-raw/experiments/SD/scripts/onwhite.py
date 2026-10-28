"""onwhite.py — RGBA-кадр → на белом #fff (как на странице); шум по ровным участкам (без контуров среза)."""
import json, sys
import numpy as np
from PIL import Image

def onwhite(src, dst, bg=(255, 255, 255)):
    im = Image.open(src).convert("RGBA")
    b = Image.new("RGBA", im.size, bg + (255,)); b.alpha_composite(im); b.convert("RGB").save(dst)
    return dst

def gauss(img, s):
    r = max(1, int(3 * s)); x = np.arange(-r, r + 1); k = np.exp(-x * x / (2 * s * s)); k /= k.sum()
    pad = np.pad(img, ((r, r), (r, r)), mode="reflect")
    t = np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 1, pad)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), 0, t)

def noise_flat(src, mask=None):
    """СКО (L/100 − гаусс σ2) ×10⁻³ только там, где сглаженный кадр ровный (|∇| мал) и есть объект: шум рендера, а не линии."""
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float64) / 255
    lin = np.where(im <= 0.04045, im / 12.92, ((im + 0.055) / 1.055) ** 2.4)
    Y = lin @ np.array([0.2126, 0.7152, 0.0722])
    L = np.where(Y > 216 / 24389, 116 * np.cbrt(Y) - 16, Y * 24389 / 27) / 100
    g = gauss(L, 2.0); hp = L - g
    gy, gx = np.gradient(gauss(L, 3.0))
    flat = np.hypot(gx, gy) < 0.002
    if mask:
        m = np.asarray(Image.open(mask).convert("RGBA").split()[-1]) > 127
        flat &= m
    return {"noise_flat_e3": float(hp[flat].std() * 1000), "flat_share": float(flat.mean())}

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "onwhite":
        print(onwhite(a[1], a[2]))
    else:
        print(json.dumps(noise_flat(a[1], a[2] if len(a) > 2 else None)))
