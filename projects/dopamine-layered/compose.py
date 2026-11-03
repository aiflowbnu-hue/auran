#!/usr/bin/env python3
"""Compose the final frames: clean visual + my own small hand-lettered labels next to the object (1-3 key words,
not a full caption; hand-picked in labels.txt), with a short curved callout line - same look as the labels in the earlier image sets
("CHEMICAL ITCH!" beside the ancestor). Font: Patrick Hand, upper case, slightly tilted.

Static frames only - no zoom, no animation, no transitions. The label is its own hard cut that appears
TEXT_LEAD before its spoken word; the plain visual comes SCENE_LEAD before its clause.

    python3 compose.py [START END]   -> build/composed/*.png + edit.json (optionally only START..END seconds)
"""
import json, math, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "build", "composed")
os.makedirs(OUT, exist_ok=True)
W, H = 1920, 1080
TEXT_LEAD, SCENE_LEAD, MIN_HOLD = 0.30, 0.08, 0.5
INK = (26, 26, 28)
SIZES = (66, 56)                      # try the big size first, smaller if it does not fit beside the object
TILT = -4                             # degrees, like hand lettering
STOP = set("a an the in of is to and it on at your you for by are was that this what so but with had has be they "
           "their them he his its if or as do did just then when there were we i not no one from into than more "
           "every all can could would will about out up down over these those how why who which been being our "
           "us me my she her him very much many most some any only also even still again yet here".split())

tl = json.load(open(os.path.join(HERE, "timeline.json")))
tr = json.load(open(os.path.join(A, "transcript.json")))
tr = tr[0] if isinstance(tr, list) else tr
words = [w for w in tr["words"] if w["type"] == "word"]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
END = words[-1]["end"] + 0.5
FONT = {s: ImageFont.truetype(os.path.join(A, "fonts", "PatrickHand-Regular.ttf"), s) for s in SIZES}
num = lambda w: bool(re.search(r"\d", w["text"]))


LABELS = {}
for ln in open(os.path.join(HERE, "labels.txt"), encoding="utf-8"):
    if ln.strip() and not ln.startswith("#"):
        n, rest = ln.rstrip("\n").split(" ", 1)
        text, _, anchor = rest.partition("@")
        LABELS[int(n)] = (text.strip(), norm(anchor or text.split()[0]))


def label_for(n, ws):
    """(label text, index of the spoken word it appears on) from labels.txt, or None."""
    if n not in LABELS:
        return None
    text, anc = LABELS[n]
    for i, w in enumerate(ws):
        x = norm(w["text"])
        if x == anc or (len(anc) > 3 and x[:len(anc)] == anc) or (len(x) > 3 and anc.startswith(x)):
            return text, i
    return "missing"


def base_image(img):
    src = Image.open(os.path.join(A, "frames", img)).convert("RGB")
    s = H / src.height
    src = src.resize((round(src.width * s), H), Image.LANCZOS)
    x = (src.width - W) // 2
    return src.crop((x, 0, x + W, H))


def text_layer(text, size):
    f = FONT[size]
    tw = int(f.getlength(text)) + 20
    layer = Image.new("RGBA", (tw, int(size * 1.4)), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((10, int(size * 0.1)), text, font=f, fill=INK + (255,), stroke_width=1, stroke_fill=INK + (255,))
    return layer.rotate(-TILT, resample=Image.BICUBIC, expand=True)


def place(base, text):
    """Put the label in clear white space beside the object: right, left, above or below its bounding box.
    Returns the composed image or None if it does not fit anywhere."""
    a = np.asarray(base.convert("L"))
    ink = a < 225
    ys, xs = np.where(ink)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    pad, gap = 24, 70
    for size in SIZES:
        lay = text_layer(text, size)
        lw, lh = lay.size
        cy = y0 + (y1 - y0) * 0.25
        spots = [("r", x1 + gap, cy - lh / 2), ("l", x0 - gap - lw, cy - lh / 2),
                 ("t", (x0 + x1) / 2 - lw / 2, y0 - gap - lh), ("b", (x0 + x1) / 2 - lw / 2, y1 + gap)]
        for side, lx, ly in spots:
            lx, ly = int(lx), int(ly)
            if lx < 60 or ly < 40 or lx + lw > W - 60 or ly + lh > H - 40:
                continue
            if ink[max(ly - pad, 0):ly + lh + pad, max(lx - pad, 0):lx + lw + pad].any():
                continue
            out = base.copy()
            out.paste(lay, (lx, ly), lay)
            callout(out, ink, side, lx, ly, lw, lh)
            return out
    return None


def callout(img, ink, side, lx, ly, lw, lh):
    """Short curved hand-drawn line from the label toward the nearest part of the object."""
    if side == "r":
        sx, sy = lx - 6, ly + lh * 0.7
    elif side == "l":
        sx, sy = lx + lw + 6, ly + lh * 0.7
    elif side == "t":
        sx, sy = lx + lw * 0.5, ly + lh + 4
    else:
        sx, sy = lx + lw * 0.5, ly - 4
    ys, xs = np.where(ink)
    k = np.argmin((xs - sx) ** 2 + (ys - sy) ** 2)
    tx, ty = xs[k], ys[k]
    d = math.hypot(tx - sx, ty - sy)
    if d < 20:
        return
    L = min(d - 14, 80)
    ux, uy = (tx - sx) / d, (ty - sy) / d
    ex, ey = sx + ux * L, sy + uy * L
    bx, by = (sx + ex) / 2 - uy * L * 0.25, (sy + ey) / 2 + ux * L * 0.25     # bulge to one side
    pts = [((1 - t) ** 2 * sx + 2 * (1 - t) * t * bx + t * t * ex, (1 - t) ** 2 * sy + 2 * (1 - t) * t * by + t * t * ey)
           for t in np.linspace(0, 1, 24)]
    dr = ImageDraw.Draw(img)
    dr.line(pts, fill=INK, width=5, joint="curve")
    for p in (pts[0], pts[-1]):
        dr.ellipse((p[0] - 2.5, p[1] - 2.5, p[0] + 2.5, p[1] + 2.5), fill=INK)


lo_t, hi_t = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (0, END)
times = [v["t"] for v in tl] + [END]
cuts, skipped, missing = [], [], []
for i, v in enumerate(tl):
    t0, t1 = times[i], times[i + 1]
    ws = [w for w in words if t0 - 0.02 <= w["start"] < t1 - 0.02]
    lab = label_for(v["n"], ws)
    if lab == "missing":
        missing.append((v["n"], LABELS[v["n"]][0])); lab = None
    if t1 <= lo_t or t0 >= hi_t:
        continue
    base = base_image(v["img"])
    show = 0.0 if i == 0 else t0 - SCENE_LEAD
    if cuts:
        show = max(show, cuts[-1]["start"] + MIN_HOLD)
    labelled = place(base, lab[0]) if lab else None
    if lab and labelled is None:
        skipped.append((v["n"], lab[0]))
    plain = os.path.join("build", "composed", f"{v['n']:03d}_0.png")
    if labelled is not None:
        lt = ws[lab[1]]["start"] - TEXT_LEAD
        if lt - show < MIN_HOLD:              # label word comes right away: one frame, label from the start
            show = min(show, lt) if not cuts else max(min(show, lt), cuts[-1]["start"] + 0.3)
            labelled.save(os.path.join(HERE, plain))
            cuts.append({"img": plain, "start": round(show, 3), "n": v["n"], "label": lab[0], "word_t": ws[lab[1]]["start"]})
            continue
        base.save(os.path.join(HERE, plain))
        cuts.append({"img": plain, "start": round(show, 3), "n": v["n"], "label": None})
        name = os.path.join("build", "composed", f"{v['n']:03d}_1.png")
        labelled.save(os.path.join(HERE, name))
        cuts.append({"img": name, "start": round(lt, 3), "n": v["n"], "label": lab[0], "word_t": ws[lab[1]]["start"]})
    else:
        base.save(os.path.join(HERE, plain))
        cuts.append({"img": plain, "start": round(show, 3), "n": v["n"], "label": None})
if lo_t == 0:
    cuts[0]["start"] = 0.0
for c in cuts:
    c["fx"], c["sfx"] = [], []
json.dump({"fps": 30, "size": [W, H], "voiceover": "assets/voiceover.mp3", "music": "assets/music.mp3",
           "music_volume": 0.16, "tail": 1.5, "range": [lo_t, hi_t], "cuts": cuts},
          open(os.path.join(HERE, "edit.json"), "w"), indent=1)
late = [(c["n"], c["label"]) for c in cuts if c.get("label") and round(c["start"] * 30) / 30 > c["word_t"]]
print(f"{len(cuts)} cuts, {sum(1 for c in cuts if c.get('label'))} labels; no room for: {skipped}; late labels: {late}")
print("label word not spoken during its visual:", missing)
