#!/usr/bin/env python3
"""Turn generated sheets into transparent, aligned animation sprites.

- Two-panel sheets (21:9) are split at the empty gap; the right frame is shifted so its
  ground-contact area (bench, feet, hands) lines up with the left frame.
- The flat background is removed by flood-filling from the image border; stray blobs that are
  not touching the character are dropped.
Output: sprites/<id>_a.png and <id>_b.png for sheets, sprites/<id>.png for single images.
"""
import json, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS, OUT = os.path.join(HERE, "sheets"), os.path.join(HERE, "sprites")
os.makedirs(OUT, exist_ok=True)


def fg_mask(rgb):
    a = rgb.astype(np.int16)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bgc = np.median(border, axis=0)
    near = (np.abs(a - bgc).max(axis=2) < 16) | (a.min(axis=2) > 246)
    lab, _ = ndi.label(near)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bg = np.isin(lab, edge[edge > 0])
    # background pockets enclosed by the body (e.g. between arm and torso): bg-coloured and large
    close = np.abs(a - bgc).max(axis=2) < 12
    plab, pn = ndi.label(close & ~bg)
    if pn:
        psize = ndi.sum(np.ones_like(plab), plab, range(1, pn + 1))
        bg |= np.isin(plab, np.where(psize > 3000)[0] + 1)
    fg = ~bg
    fg = ndi.binary_fill_holes(fg) & fg | ndi.binary_opening(fg, iterations=1)
    lab, n = ndi.label(fg)
    if n == 0:
        return fg
    sizes = ndi.sum(fg, lab, range(1, n + 1))
    main = lab == (np.argmax(sizes) + 1)
    near_main = ndi.binary_dilation(main, iterations=45)
    keep = np.isin(lab, np.unique(lab[near_main & fg]))
    return keep


def rgba(rgb, mask):
    alpha = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    im = Image.fromarray(rgb).convert("RGBA")
    im.putalpha(alpha)
    return im


def split(rgb):
    """Cut at the emptiest column near the centre (the gap between the two panels), ignoring drop shadows."""
    w = rgb.shape[1]
    a = rgb.astype(np.float32)
    mx, mn = a.max(axis=2), a.min(axis=2)
    shadow = ((mx - mn) / np.maximum(mx, 1) < 0.12) & (mx > 140)
    counts = (fg_mask(rgb) & ~shadow).sum(axis=0).astype(np.float32)
    xs = np.arange(int(w * 0.35), int(w * 0.65))
    score = counts[xs] + np.abs(xs - w / 2) * 0.01  # prefer the centre on ties
    bx = int(xs[np.argmin(score)])
    return rgb[:, :bx], rgb[:, bx:]


ANCHOR = {"dips": "minx", "push": "maxx", "knee": "maxx", "ohe": "meanx", "hook": "meanx", "shirt": "meanx"}


def contact(rgb, mask, mode):
    """Floor y and anchor x of the ground-contact area, ignoring the grey drop shadow."""
    a = rgb.astype(np.float32)
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    shadow = (sat < 0.12) & (mx > 140) & (mx < 232)
    solid = mask & ~shadow
    ys = np.where(solid.any(axis=1))[0]
    floor = ys[-1]
    band = solid[max(0, floor - 70):floor + 1]
    xs = np.where(band.any(axis=0))[0]
    x = {"minx": xs.min(), "maxx": xs.max(), "meanx": int(np.where(band)[1].mean())}[mode]
    return int(x), int(floor)


def shift(im, dx, dy, size):
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(im, (dx, dy), im)
    return canvas


cfg = json.load(open(os.path.join(HERE, "poses.json")))
report = {}
for it in cfg["items"]:
    rgb = np.array(Image.open(os.path.join(SHEETS, f"{it['id']}.png")).convert("RGB"))
    if it["aspect"] == "21:9":
        L, R = split(rgb)
        h = L.shape[0]
        wmax = max(L.shape[1], R.shape[1])
        ma, mb = fg_mask(L), fg_mask(R)
        pad = lambda m: np.pad(m, ((0, 0), (0, wmax - m.shape[1])))
        xa, fa = contact(L, ma, ANCHOR[it["id"]])
        xb, fb = contact(R, mb, ANCHOR[it["id"]])
        dx, dy = xa - xb, fa - fb
        a, b = rgba(L, ma), rgba(R, mb)
        size = (wmax + abs(dx), h + abs(dy))  # grow the canvas so neither frame gets clipped
        ox, oy = max(0, -dx), max(0, -dy)
        shift(a, ox, oy, size).save(os.path.join(OUT, f"{it['id']}_a.png"))
        shift(b, ox + dx, oy + dy, size).save(os.path.join(OUT, f"{it['id']}_b.png"))
        report[it["id"]] = {"size": size, "shift_b": (dx, dy)}
    else:
        rgba(rgb, fg_mask(rgb)).save(os.path.join(OUT, f"{it['id']}.png"))
        report[it["id"]] = {"size": rgb.shape[1::-1]}
    print(it["id"], report[it["id"]])
json.dump(report, open(os.path.join(OUT, "sprites.json"), "w"), indent=1)
