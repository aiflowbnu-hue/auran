#!/usr/bin/env python3
"""Ancient humans drawn to match the owner's reference image (savanna tribe): slightly tall oval white heads, big
round outlined eyes, thick shaggy dark-brown hair with a fringe, one-shoulder fur tunics with shaggy edges and
fur texture, rope belt, thin black stick limbs, white mitten hands and white feet, and a gentle hand-drawn wobble
on every line. Variants: man (short shaggy hair), woman (long hair), elder (bald, grey hair and beard), child.

    python3 ancient.py   -> ancient_sheet.png, scene_savanna.png, scene_cave.png, poses/ancient_*.png
"""
import math, os, random
from gen import render, P

HERE = os.path.dirname(os.path.abspath(__file__))
INK = "#1d1a17"
SKIN = "#ffffff"
HAIR = {"base": "#4a2f1b", "light": "#7b5535", "dark": "#26180c"}
GREY = {"base": "#9a9a9a", "light": "#d0d0d0", "dark": "#5c5c5c"}
FUR = {"base": "#7a5535", "light": "#a3805c", "dark": "#43291a", "edge": "#3a2414"}
_id = [0]


def uid(p):
    _id[0] += 1
    return f"{p}{_id[0]}"


def path(pts, close=True):
    return "M" + " L".join(P(*q) for q in pts) + (" Z" if close else "")


def smooth(pts, close=True):
    """Catmull-Rom through the points -> smooth bezier path."""
    n = len(pts)
    if n < 3:
        return path(pts, close)
    d = f"M{P(*pts[0])}"
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (close or i > 0) else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (close or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{P(*c1)} {P(*c2)} {P(*p2)}"
    return d + (" Z" if close else "")


def stroke(pts, w=4, color=INK, smooth_=False):
    d = smooth(pts, False) if smooth_ else path(pts, False)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'


def shaggy(pts, rnd, step=7, lo=3, hi=10, skip=None):
    """Turn a coarse closed outline into a shaggy fur/hair edge: small pointed tufts sticking outwards.
    skip(i) -> True keeps edge i smooth."""
    area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    sgn = 1 if area > 0 else -1
    out = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        nx, ny = (b[1] - a[1]) / (L or 1) * -sgn, -(b[0] - a[0]) / (L or 1) * -sgn
        for k in range(n):
            t = k / n
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if skip and skip(i):
                out.append((x, y))
                continue
            out.append((x, y))
            t2 = (k + 0.5) / n
            h = rnd.uniform(lo, hi)
            out.append((a[0] + (b[0] - a[0]) * t2 + nx * h + rnd.uniform(-2, 2), a[1] + (b[1] - a[1]) * t2 + ny * h + rnd.uniform(-1, 2)))
    return out


def fur_fill(shape_d, bbox, rnd, pal, n=120, down=True):
    """Fill a shape with base colour + many short fur strokes (clipped)."""
    cid = uid("c")
    x0, y0, x1, y1 = bbox
    o = [f'<clipPath id="{cid}"><path d="{shape_d}"/></clipPath>',
         f'<path d="{shape_d}" fill="{pal["base"]}"/>', f'<g clip-path="url(#{cid})">']
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        L = rnd.uniform(7, 15)
        a = math.radians(rnd.uniform(-25, 25) if down else rnd.uniform(0, 360))
        col = rnd.choice([pal["light"], pal["dark"], pal["dark"], pal["light"]])
        o.append(f'<path d="M{x:.1f},{y:.1f} q{math.sin(a) * L * 0.5 + 2:.1f},{math.cos(a) * L * 0.5:.1f} {math.sin(a) * L:.1f},{math.cos(a) * L:.1f}" '
                 f'stroke="{col}" stroke-width="{rnd.uniform(1.3, 2.4):.1f}" fill="none" stroke-linecap="round" opacity="0.85"/>')
    o.append("</g>")
    return "".join(o)


# ------------------------------------------------------------------ head
def face(view, mood, cx, cy, rx, ry, gaze=(1, 0)):
    if view == "back":
        return ""
    k = rx / 44
    if view == "front":
        eyes = [(cx - 15 * k, 1.0), (cx + 15 * k, 1.0)]
        nose, mouth = (cx + 2 * k, cy + 10 * k), (cx, cy + 25 * k)
    elif view == "three":
        eyes = [(cx + 1 * k, 0.92), (cx + 27 * k, 1.0)]
        nose, mouth = (cx + 22 * k, cy + 10 * k), (cx + 16 * k, cy + 25 * k)
    else:
        eyes = [(cx + 27 * k, 1.0)]
        nose, mouth = (cx + 41 * k, cy + 8 * k), (cx + 30 * k, cy + 25 * k)
    ey = cy - 4 * k
    o = []
    gx, gy = gaze
    for x, s in eyes:
        er = 8.5 * k * s
        if mood == "happy":
            o.append(stroke([(x - er, ey + 2 * k), (x, ey - 6 * k), (x + er, ey + 2 * k)], 3 * k, INK, True))
            continue
        o.append(f'<ellipse cx="{x:.1f}" cy="{ey:.1f}" rx="{er:.1f}" ry="{er * 1.1:.1f}" fill="#fff" stroke="{INK}" stroke-width="{1.7 * k:.1f}"/>')
        pr = er * (0.5 if mood != "shocked" else 0.32)
        o.append(f'<circle cx="{x + gx * er * 0.35:.1f}" cy="{ey + gy * er * 0.3 + 1 * k:.1f}" r="{pr:.1f}" fill="{INK}"/>')
        # brows
        if mood == "angry":
            inner = x < (eyes[-1][0] if len(eyes) > 1 else x + 1)  # left eye: inner end on the right
            xa, xb = (x - er * 1.1, x + er * 1.0) if inner else (x - er * 1.0, x + er * 1.1)
            ya, yb = (ey - er * 2.1, ey - er * 1.35) if inner else (ey - er * 1.35, ey - er * 2.1)
            o.append(stroke([(xa, ya), (xb, yb)], 4.2 * k))
        elif mood in ("worried", "shocked"):
            o.append(stroke([(x - er * 0.8, ey - er * 1.7), (x, ey - er * 2.1), (x + er * 0.8, ey - er * 1.95)], 2.3 * k, INK, True))
        else:
            o.append(stroke([(x - er * 0.7, ey - er * 1.85), (x + er * 0.8, ey - er * 1.95)], 2.4 * k, INK, True))
    nx, ny = nose
    o.append(stroke([(nx - 2 * k, ny - 4 * k), (nx + 3 * k, ny + 1 * k), (nx - 1 * k, ny + 3 * k)], 2 * k, INK, True))
    mx, my = mouth
    if mood == "angry":
        o.append(f'<path d="M{mx - 8 * k:.1f},{my - 2 * k:.1f} Q{mx:.1f},{my - 5 * k:.1f} {mx + 8 * k:.1f},{my - 3 * k:.1f} Q{mx + 6 * k:.1f},{my + 7 * k:.1f} {mx:.1f},{my + 7 * k:.1f} Q{mx - 6 * k:.1f},{my + 6 * k:.1f} {mx - 8 * k:.1f},{my - 2 * k:.1f} Z" fill="#5b1f1f" stroke="{INK}" stroke-width="{2 * k:.1f}"/>'
                 f'<ellipse cx="{mx:.1f}" cy="{my + 4 * k:.1f}" rx="{4 * k:.1f}" ry="{2 * k:.1f}" fill="#e98585"/>'
                 f'<path d="M{mx - 6 * k:.1f},{my - 1.5 * k:.1f} L{mx + 6 * k:.1f},{my - 2.5 * k:.1f}" stroke="#fff" stroke-width="{2 * k:.1f}"/>')
    elif mood == "shocked":
        o.append(f'<ellipse cx="{mx:.1f}" cy="{my + 1 * k:.1f}" rx="{4.5 * k:.1f}" ry="{5.5 * k:.1f}" fill="#5b1f1f" stroke="{INK}" stroke-width="{2 * k:.1f}"/>')
    elif mood == "happy":
        o.append(f'<path d="M{mx - 9 * k:.1f},{my - 2 * k:.1f} Q{mx:.1f},{my + 10 * k:.1f} {mx + 9 * k:.1f},{my - 2 * k:.1f} Z" fill="#5b1f1f" stroke="{INK}" stroke-width="{2 * k:.1f}"/>')
    elif mood == "worried":
        o.append(stroke([(mx - 6 * k, my + 1 * k), (mx, my - 2 * k), (mx + 6 * k, my + 1 * k)], 2.2 * k, INK, True))
    else:
        o.append(stroke([(mx - 5 * k, my), (mx + 5 * k, my - 1 * k)], 2.2 * k, INK, True))
    return "".join(o)


def hair_shapes(style, view, cx, cy, rx, ry, rnd):
    """Returns (behind_head_svg, over_head_svg)."""
    back_x = {"front": 0, "three": -0.22, "side": -0.4, "back": 0}[view] * rx
    if style == "elder":
        # grey hair only around the back and sides, bald on top
        pts = []
        a0, a1 = (110, 250) if view == "front" else (95, 265)
        for i in range(9):
            a = math.radians(a0 + (a1 - a0) * i / 8)
            pts.append((cx + back_x * 0.5 + math.cos(a) * rx * 1.12, cy + math.sin(a) * ry * 1.02))
        for i in range(8, -1, -1):
            a = math.radians(a0 + (a1 - a0) * i / 8)
            pts.append((cx + back_x * 0.5 + math.cos(a) * rx * 0.86, cy + math.sin(a) * ry * 0.86))
        pts = shaggy(pts, rnd, 7, 2, 7)
        sides = [path(pts)]
        if view == "front":
            pts2 = [(2 * cx - x, y) for x, y in pts]
            sides.append(path(pts2))
        bb = (cx - rx * 1.4, cy - ry, cx + rx * 1.4, cy + ry)
        behind = "".join(fur_fill(d, bb, rnd, GREY, 40) + f'<path d="{d}" fill="none" stroke="{GREY["dark"]}" stroke-width="2"/>' for d in sides)
        return behind, ""
    # mass behind the head
    if style == "long":
        top = [(cx + back_x + math.cos(math.radians(a)) * rx * 1.12, cy + math.sin(math.radians(a)) * ry * 1.08) for a in range(160, 381, 20)]
        shape = top + [(cx + rx * 1.05 + back_x * 0.3, cy + ry * 1.9), (cx + back_x - 0.0, cy + ry * 1.75), (cx - rx * 1.2 + back_x, cy + ry * 2.0)]
        lo, hi = 3, 9
    else:
        a0, a1 = {"front": (150, 390), "three": (125, 360), "side": (100, 350), "back": (0, 360)}[view]
        shape = [(cx + back_x + math.cos(math.radians(a0 + (a1 - a0) * i / 14)) * rx * 1.2,
                  cy - ry * 0.08 + math.sin(math.radians(a0 + (a1 - a0) * i / 14)) * ry * 1.16) for i in range(15)]
        if view != "back":
            shape.append((cx + back_x * 0.5, cy + ry * 0.3))
        lo, hi = 6, 20
    edge = shaggy(shape, rnd, 9, lo, hi)
    d = path(edge)
    xs, ys = [p[0] for p in edge], [p[1] for p in edge]
    behind = fur_fill(d, (min(xs), min(ys), max(xs), max(ys)), rnd, HAIR, 70) + \
        f'<path d="{d}" fill="none" stroke="{HAIR["dark"]}" stroke-width="2.4" stroke-linejoin="round"/>'
    if view == "back":
        return behind, ""
    # cap over the top of the head with a ragged fringe
    face_off = {"front": 0, "three": 0.25, "side": 0.45}[view] * rx
    cap = []
    for i in range(13):
        a = math.radians(188 + 164 * i / 12)
        cap.append((cx + math.cos(a) * rx * 1.14, cy - ry * 0.06 + math.sin(a) * ry * 1.16))
    # fringe from right to left
    fr = []
    n = 9
    for i in range(n + 1):
        t = i / n
        x = cx + rx * 1.0 - 2 * rx * t
        rel = (x - (cx + face_off)) / rx
        base = cy - ry * (0.32 if style != "long" else 0.45) + ry * 0.5 * rel * rel
        base = min(base, cy + ry * 0.1)
        fr.append((x + (rnd.uniform(-5, 5)), base - (0 if i % 2 else ry * 0.24) + rnd.uniform(-3, 3)))
    shape = cap + fr
    d = smooth(shape) if style == "long" else path(shaggy(cap, rnd, 9, 6, 16)[:-1] + fr)
    xs, ys = [p[0] for p in shape], [p[1] for p in shape]
    over = fur_fill(d, (min(xs) - 5, min(ys) - 15, max(xs) + 5, max(ys) + 5), rnd, HAIR, 60) + \
        f'<path d="{d}" fill="none" stroke="{HAIR["dark"]}" stroke-width="1.6" stroke-linejoin="round"/>'
    return behind, over


def beard(view, cx, cy, rx, ry, rnd):
    off = {"front": 0, "three": 0.22, "side": 0.4}.get(view, 0) * rx
    pts = [(cx - rx * 0.75 + off, cy + ry * 0.05), (cx - rx * 0.2 + off, cy + ry * 0.45), (cx + rx * 0.35 + off, cy + ry * 0.4),
           (cx + rx * 0.85 + off, cy + ry * 0.05), (cx + rx * 0.6 + off, cy + ry * 1.3), (cx + rx * 0.1 + off, cy + ry * 2.1),
           (cx - rx * 0.4 + off, cy + ry * 1.5)]
    edge = shaggy(pts, rnd, 8, 3, 9)
    d = path(edge)
    xs, ys = [p[0] for p in edge], [p[1] for p in edge]
    mo = f'<path d="M{cx - rx * 0.25 + off:.1f},{cy + ry * 0.45:.1f} Q{cx + off:.1f},{cy + ry * 0.38:.1f} {cx + rx * 0.3 + off:.1f},{cy + ry * 0.45:.1f}" stroke="{INK}" stroke-width="2.4" fill="none"/>'
    return fur_fill(d, (min(xs), min(ys), max(xs), max(ys)), rnd, GREY, 70) + \
        f'<path d="{d}" fill="none" stroke="{GREY["dark"]}" stroke-width="2.2"/>' + mo


def head(view, mood, cx, cy, rx, ry, style, rnd, gaze=(1, 0)):
    behind, over = hair_shapes(style, view, cx, cy, rx, ry, rnd)
    o = [behind]
    if view == "back" and style not in ("elder",):
        return behind
    o.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{SKIN}" stroke="{INK}" stroke-width="3.2"/>')
    if style == "elder" and view != "back":
        off = {"front": 0, "three": 0.2, "side": 0.38}[view] * rx
        for i in range(3):     # forehead wrinkles
            y = cy - ry * (0.62 - i * 0.11)
            o.append(stroke([(cx - rx * 0.32 + off, y), (cx + off, y - 3), (cx + rx * 0.32 + off, y)], 1.8, INK, True))
    o.append(face(view, mood, cx, cy, rx, ry, gaze))
    if style == "elder" and view != "back":
        o.append(beard(view, cx, cy, rx, ry, rnd))
        mood_brow = ""
    o.append(over)
    return "".join(o)


# ------------------------------------------------------------------ body
def seg(x, y, ang, L):
    a = math.radians(ang)
    return x + math.sin(a) * L, y + math.cos(a) * L


def limb(x, y, a1, l1, a2, l2):
    x1, y1 = seg(x, y, a1, l1)
    x2, y2 = seg(x1, y1, a1 + a2, l2)
    return [(x, y), (x1, y1), (x2, y2)], a1 + a2


def hand(x, y, ang, kind="fist", s=1.0):
    a = math.radians(ang)
    if kind == "point":
        fx, fy = x + math.sin(a) * 20 * s, y + math.cos(a) * 20 * s
        return (stroke([(x, y), (fx, fy)], 7.5 * s) + stroke([(x, y), (fx, fy)], 3.6 * s, "#fff") +
                f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{8 * s:.1f}" ry="{6.5 * s:.1f}" fill="#fff" stroke="{INK}" stroke-width="2.6" transform="rotate({-ang + 90:.0f} {x:.1f} {y:.1f})"/>')
    tx, ty = x + math.sin(a + 1.2) * 7 * s, y + math.cos(a + 1.2) * 7 * s
    return (f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{7.5 * s:.1f}" ry="{8.5 * s:.1f}" fill="#fff" stroke="{INK}" stroke-width="2.6" transform="rotate({-ang:.0f} {x:.1f} {y:.1f})"/>'
            f'<ellipse cx="{tx:.1f}" cy="{ty:.1f}" rx="{3 * s:.1f}" ry="{4.5 * s:.1f}" fill="#fff" stroke="{INK}" stroke-width="2.2"/>')


def foot(x, y, d, s=1.0):
    return f'<path d="M{x - 4 * d * s:.1f},{y - 3 * s:.1f} Q{x + 4 * d * s:.1f},{y - 8 * s:.1f} {x + 14 * d * s:.1f},{y - 1 * s:.1f} L{x - 5 * d * s:.1f},{y + 1 * s:.1f} Z" fill="#fff" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>'


def tunic(view, nx, ny, hx, hy, w, rnd, short=False):
    """One-shoulder fur tunic: over the far shoulder, bare near shoulder/chest, flared shaggy hem, rope belt."""
    def at(f, px):
        return nx + (hx - nx) * f + px, ny + (hy - ny) * f
    hem = hy + (0.34 if not short else 0.3) * (hy - ny)
    hem = min(hem, -8)
    o = []
    # bare skin torso
    if view != "back":
        sk = [at(-0.02, -w * 0.3), at(-0.04, w * 0.98), at(0.42, w * 1.0)]
        o.append(f'<path d="{smooth(sk)}" fill="#fff" stroke="{INK}" stroke-width="3"/>')
    if view == "side":
        coarse = [at(0.0, -w * 0.9), at(-0.03, w * 0.55), at(0.35, w * 0.95), at(0.7, w * 1.0), (hx + w * 1.15, hem), (hx - w * 1.2, hem), at(0.7, -w * 1.05)]
    elif view == "back":
        coarse = [at(-0.02, -w * 1.0), at(-0.02, w * 1.0), at(0.7, w * 1.05), (hx + w * 1.25, hem), (hx - w * 1.25, hem), at(0.7, -w * 1.05)]
    else:
        coarse = [at(-0.04, -w * 1.02), at(-0.04, -w * 0.2), at(0.4, w * 1.0), at(0.72, w * 1.05), (hx + w * 1.28, hem), (hx - w * 1.25, hem), at(0.72, -w * 1.05)]
    edge = shaggy(coarse, rnd, 6, 1.5, 5)
    d = path(edge)
    xs, ys = [p[0] for p in edge], [p[1] for p in edge]
    o.append(fur_fill(d, (min(xs), min(ys), max(xs), max(ys)), rnd, FUR, int((max(ys) - min(ys)) * 1.3)))
    o.append(f'<path d="{d}" fill="none" stroke="{FUR["edge"]}" stroke-width="2.4" stroke-linejoin="round"/>')
    by = hy - 8
    o.append(f'<path d="M{hx - w * 1.1:.1f},{by:.1f} Q{hx:.1f},{by + 6:.1f} {hx + w * 1.12:.1f},{by - 1:.1f}" stroke="#2c1b0e" stroke-width="6" fill="none" stroke-linecap="round"/>')
    o.append(f'<path d="M{hx - w * 1.1:.1f},{by:.1f} Q{hx:.1f},{by + 6:.1f} {hx + w * 1.12:.1f},{by - 1:.1f}" stroke="#6a4a2c" stroke-width="2" fill="none" stroke-dasharray="4 4"/>')
    return "".join(o)


def spear(x, y, top=-560, ground=0):
    shaft = [(x + 3, ground), (x - 1, (ground + top) / 2), (x - 5, top)]
    tip = f'<path d="M{x - 5},{top + 6} C{x - 21},{top - 24} {x - 15},{top - 58} {x - 5},{top - 86} C{x + 6},{top - 58} {x + 10},{top - 24} {x - 5},{top + 6} Z" fill="#a17d5a" stroke="{INK}" stroke-width="3"/>' \
          f'<path d="M{x - 5},{top - 4} L{x - 5},{top - 70}" stroke="#7a5a3c" stroke-width="2"/>'
    bind = "".join(stroke([(x - 12, top + 8 + i * 6), (x + 2, top + 4 + i * 6)], 3, "#2c1b0e") for i in range(3))
    return stroke(shaft, 11, INK, True) + stroke(shaft, 6, "#8b6a45", True) + tip + bind


def staff(x, y, top=-260, ground=0):
    pts = [(x + 2, ground), (x - 4, (ground + top) * 0.4), (x + 3, (ground + top) * 0.7), (x - 2, top), (x + 10, top - 14)]
    return stroke(pts, 11, INK, True) + stroke(pts, 6, "#8b6a45", True)


DIM = dict(rx=48, ry=54, neck=10, torso=132, arm=(80, 76), leg=(112, 110), w=30)


def person(view="three", mood="neutral", pose=None, style="short", scale=1.0, seed=1, child=False, gaze=(1, 0)):
    """One ancient human at the origin (feet on y = 0). pose keys as in gen.py: la/lb, ra/rb (far / near arm),
    lh/lk, rh/rk (legs), dy (drop for sitting), lean, hand_l/hand_r ('spear', 'staff', 'point'), extra."""
    rnd = random.Random(seed)
    p = dict(la=-6, lb=4, ra=8, rb=-4, lh=-3, lk=0, rh=4, rk=0, dy=0, lean=0)
    p.update(pose or {})
    D = dict(DIM)
    if child:
        D.update(torso=88, arm=(52, 50), leg=(62, 60), w=22)
    rx, ry = D["rx"], D["ry"]
    hip_y = -(D["leg"][0] + D["leg"][1]) + p["dy"]
    t = math.radians(p["lean"])
    nx, ny = math.sin(t) * D["torso"], hip_y - math.cos(t) * D["torso"]
    hc = (nx + math.sin(t) * (D["neck"] + ry), ny - math.cos(t) * (D["neck"] + ry) + 6)
    spread = {"front": 15, "back": 15, "three": 11, "side": 3}[view]
    sh = {"front": D["w"] * 0.95, "back": D["w"] * 0.95, "three": D["w"] * 0.8, "side": 4}[view]
    o = [p.get("behind", "")]
    # legs
    legs = []
    for side, h, k in ((-1, p["lh"], p["lk"]), (1, p["rh"], p["rk"])):
        pts, end = limb(side * spread, hip_y, h, D["leg"][0], k, D["leg"][1])
        d = 1 if view in ("three", "side") else side
        legs.append(stroke(pts, 4.2) + foot(pts[-1][0], pts[-1][1] + 2, d))
    # arms
    sx, sy = nx, ny + 12
    arms = []
    for side, a1, a2, prop in ((-1, p["la"], p["lb"], p.get("hand_l")), (1, p["ra"], p["rb"], p.get("hand_r"))):
        pts, end = limb(sx + side * sh, sy, a1, D["arm"][0], a2, D["arm"][1])
        arms.append((pts, end, prop))
    far, near = arms
    def arm_svg(a):
        return stroke(a[0], 4.2)
    o.append(arm_svg(far))
    o += legs
    o.append(stroke([(hc[0], hc[1] + ry - 4), (nx, ny + 6)], 4.2))           # neck
    o.append(tunic(view, nx, ny, 0, hip_y, D["w"], rnd, short=child))
    near_hangs = abs(p["ra"]) < 25 and abs(p["rb"]) < 30
    if view == "back" or near_hangs:
        o.append(arm_svg(near))
    def prop_svg(pts, prop):
        x, y = pts[-1]
        if prop == "spear":
            return spear(x + 2, y)
        if prop == "staff":
            return staff(x + 2, y, top=y - 10)
        return ""
    if view in ("side", "three"):
        o.append(prop_svg(far[0], far[2])); far = (far[0], far[1], "done")
    o.append(head(view, mood, hc[0], hc[1], rx, ry, style, rnd, gaze))
    for pts, end, prop in (far, near):
        x, y = pts[-1]
        if prop == "spear":
            o.append(spear(x + 2, y))
        elif prop == "staff":
            o.append(staff(x + 2, y, top=y - 10))
    if not (view == "back" or near_hangs):
        o.append(arm_svg(near))
    for pts, end, prop in (far, near):
        x, y = pts[-1]
        o.append(hand(x, y, end, "point" if prop == "point" else "fist"))
    o.append(p.get("extra", ""))
    fid = uid("w")
    flt = (f'<filter id="{fid}" x="-20%" y="-20%" width="140%" height="140%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="{seed}"/>'
           f'<feDisplacementMap in="SourceGraphic" scale="2.6"/></filter>')
    return f'{flt}<g filter="url(#{fid})" transform="scale({scale})">{"".join(o)}</g>'


# ------------------------------------------------------------------ props / scenery
def campfire(x, y, s=1.0):
    def k(v):
        return v * s
    logs = "".join(f'<rect x="{x - k(52)}" y="{y - k(13)}" width="{k(104)}" height="{k(14)}" rx="{k(7)}" fill="{c}" stroke="{INK}" stroke-width="3" transform="rotate({r} {x} {y - k(6)})"/>'
                   for r, c in ((-14, "#6e4626"), (14, "#835530")))
    flame = (f'<path d="M{x - k(34)},{y - k(10)} C{x - k(48)},{y - k(52)} {x - k(14)},{y - k(62)} {x - k(6)},{y - k(108)} C{x + k(8)},{y - k(76)} {x + k(44)},{y - k(66)} {x + k(34)},{y - k(10)} Z" fill="#f28a24" stroke="{INK}" stroke-width="3"/>'
             f'<path d="M{x - k(16)},{y - k(10)} C{x - k(20)},{y - k(36)} {x - k(2)},{y - k(44)} {x + k(2)},{y - k(70)} C{x + k(12)},{y - k(44)} {x + k(24)},{y - k(36)} {x + k(16)},{y - k(10)} Z" fill="#ffd34a"/>')
    stones = "".join(f'<ellipse cx="{x + k(dx)}" cy="{y}" rx="{k(14)}" ry="{k(9)}" fill="#9d9aa0" stroke="{INK}" stroke-width="2.6"/>' for dx in (-62, -36, 36, 62))
    return logs + flame + stones


def bone(x, y, ang=20, s=1.0):
    return (f'<g transform="translate({x},{y}) rotate({ang}) scale({s})">'
            f'<path d="M-22,-6 C-30,-18 -42,-8 -32,0 C-42,8 -30,18 -22,6 L22,6 C30,18 42,8 32,0 C42,-8 30,-18 22,-6 Z" '
            f'fill="#f3ead6" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/></g>')


SIL = "#18161c"


def giraffe(x, y, s=1.0, flip=False):
    f = -1 if flip else 1
    def q(px, py):
        return f"{x + px * s * f:.1f},{y + py * s:.1f}"
    body = f'<path d="M{q(-40, -100)} C{q(-20, -110)} {q(20, -112)} {q(40, -108)} C{q(50, -98)} {q(46, -72)} {q(34, -68)} C{q(10, -64)} {q(-24, -68)} {q(-40, -74)} Z" fill="{SIL}"/>'
    legs = "".join(f'<path d="M{q(lx, -74)} L{q(lx + d, -36)} L{q(lx + d * 0.6, 0)}" stroke="{SIL}" stroke-width="{6 * s:.1f}" fill="none" stroke-linecap="round"/>'
                   for lx, d in ((-32, -2), (-22, 3), (24, 2), (34, -3)))
    neck = f'<path d="M{q(26, -100)} C{q(36, -130)} {q(48, -160)} {q(58, -186)} L{q(68, -182)} C{q(56, -150)} {q(48, -120)} {q(42, -92)} Z" fill="{SIL}"/>'
    head = f'<path d="M{q(54, -186)} C{q(58, -196)} {q(70, -196)} {q(84, -186)} L{q(82, -180)} C{q(72, -180)} {q(64, -178)} {q(60, -176)} Z" fill="{SIL}"/>'
    horns = f'<path d="M{q(60, -192)} L{q(58, -202)} M{q(66, -193)} L{q(66, -203)}" stroke="{SIL}" stroke-width="{2.5 * s:.1f}"/>'
    tail = f'<path d="M{q(-38, -94)} L{q(-46, -70)}" stroke="{SIL}" stroke-width="{2 * s:.1f}"/>'
    return body + legs + neck + head + horns + tail


def elephant(x, y, s=1.0, flip=False):
    d = ("M-60,0 L-58,-40 C-74,-48 -78,-84 -56,-100 C-30,-118 30,-118 52,-104 C70,-96 82,-84 86,-66 C92,-50 92,-24 96,-6 "
         "L90,-4 C84,-22 82,-40 76,-52 L72,-40 L70,0 L56,0 L54,-36 L20,-40 L18,0 L4,0 L2,-40 L-30,-40 L-32,0 L-46,0 L-46,-38 Z")
    ear = "M44,-92 C30,-88 28,-62 40,-52 C52,-56 58,-76 52,-92 Z"
    t = f"translate({x},{y}) scale({-s if flip else s},{s})"
    return f'<g transform="{t}"><path d="{d}" fill="{SIL}"/><path d="{ear}" fill="#2c2a31"/></g>'


def antelope(x, y, s=1.0, flip=False, graze=False):
    neck = "C24,-34 30,-44 34,-52 L40,-50 L42,-60 L44,-50 L46,-46 L38,-38 C34,-30 30,-26 26,-24" if not graze else "C26,-26 34,-16 40,-6 L44,-2 L36,-2 C30,-10 26,-16 22,-20"
    d = (f"M-26,0 L-24,-22 C-30,-26 -32,-30 -30,-34 C-20,-38 10,-38 20,-34 {neck} L22,-20 L22,0 L18,0 L16,-18 L-2,-18 L-4,0 L-8,0 L-10,-20 L-20,-20 L-22,0 Z")
    t = f"translate({x},{y}) scale({-s if flip else s},{s})"
    return f'<path d="{d}" fill="{SIL}" transform="{t}"/>'


def zebra(x, y, s=1.0):
    body = ("M-26,0 L-24,-24 C-30,-28 -30,-36 -24,-40 C-10,-44 14,-44 22,-40 C28,-48 32,-56 38,-62 L46,-60 L46,-52 L36,-40 "
            "C34,-34 30,-30 26,-26 L24,0 L20,0 L18,-22 L-2,-22 L-4,0 L-8,0 L-10,-22 L-20,-22 L-22,0 Z")
    stripes = "".join(f'<path d="M{dx},-42 L{dx + 3},-22" stroke="{SIL}" stroke-width="2.4"/>' for dx in range(-20, 24, 6))
    return (f'<g transform="translate({x},{y}) scale({s})"><path d="{body}" fill="#f2f0ea" stroke="{SIL}" stroke-width="2"/>{stripes}'
            f'<path d="M36,-58 L44,-52" stroke="{SIL}" stroke-width="2.4"/></g>')


def grass_clump(x, y, s=1.0, seed=0, color="#b88a32", dark="#7a5a1e"):
    rnd = random.Random(seed)
    o = []
    for i in range(rnd.randint(6, 11)):
        bx = x + rnd.uniform(-14, 14) * s
        h = rnd.uniform(26, 62) * s
        lean = rnd.uniform(-22, 22) * s
        o.append(f'<path d="M{bx - 2 * s:.1f},{y} Q{bx + lean * 0.4:.1f},{y - h * 0.6:.1f} {bx + lean:.1f},{y - h:.1f} Q{bx + lean * 0.4 + 3 * s:.1f},{y - h * 0.55:.1f} {bx + 3 * s:.1f},{y} Z" '
                 f'fill="{rnd.choice((color, "#c99b40", "#a57a2a"))}" stroke="{dark}" stroke-width="1.3"/>')
    return "".join(o)


def tall_grass(x, y, s=1.0, seed=0):
    rnd = random.Random(seed)
    o = []
    for i in range(7):
        bx = x + i * 10 * s
        h = rnd.uniform(140, 240) * s
        lean = rnd.uniform(10, 60) * s * rnd.choice((-1, 1))
        o.append(f'<path d="M{bx:.1f},{y} Q{bx + lean * 0.3:.1f},{y - h * 0.6:.1f} {bx + lean:.1f},{y - h:.1f} Q{bx + lean * 0.3 + 6 * s:.1f},{y - h * 0.55:.1f} {bx + 8 * s:.1f},{y} Z" '
                 f'fill="#8a7a4a" stroke="#4d4126" stroke-width="2"/>')
    for i in range(3):        # seed heads
        bx = x + rnd.uniform(0, 60) * s
        h = rnd.uniform(200, 280) * s
        o.append(f'<path d="M{bx:.1f},{y} Q{bx + 10 * s:.1f},{y - h * 0.5:.1f} {bx + 18 * s:.1f},{y - h:.1f}" stroke="#4d4126" stroke-width="3" fill="none"/>')
        for k in range(6):
            yy = y - h + k * 9 * s
            o.append(f'<ellipse cx="{bx + 18 * s + 4 * s:.1f}" cy="{yy:.1f}" rx="{3 * s:.1f}" ry="{6 * s:.1f}" fill="#9c8858" stroke="#4d4126" stroke-width="1.4" transform="rotate(25 {bx + 22 * s:.1f} {yy:.1f})"/>')
    return "".join(o)


def branch(a, b, w0, w1, bend=0.15, color="#7a5a3e"):
    """Tapered curved branch polygon from a (width w0) to b (width w1)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    m = ((a[0] + b[0]) / 2 + nx * L * bend, (a[1] + b[1]) / 2 + ny * L * bend)
    wm = (w0 + w1) / 2
    left = [(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (m[0] + nx * wm / 2, m[1] + ny * wm / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2)]
    right = [(b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (m[0] - nx * wm / 2, m[1] - ny * wm / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)]
    d = (f"M{P(*left[0])} Q{P(*left[1])} {P(*left[2])} L{P(*right[0])} Q{P(*right[1])} {P(*right[2])} Z")
    return f'<path d="{d}" fill="{color}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'


def bare_tree(x, y, s=1.0):
    """Leaning dry tree at the left edge (tapered trunk + branches), like the reference."""
    def k(v):
        return v * s
    o = [branch((x, y), (x + k(70), y - k(520)), k(70), k(36), 0.04)]
    for a, b, w0, w1, bend in (((x + k(60), y - k(470)), (x + k(260), y - k(700)), 26, 6, -0.08),
                               ((x + k(50), y - k(420)), (x - k(60), y - k(660)), 22, 5, 0.1),
                               ((x + k(70), y - k(515)), (x + k(120), y - k(760)), 18, 5, 0.06),
                               ((x + k(150), y - k(590)), (x + k(260), y - k(620)), 10, 3, 0.1)):
        o.append(branch(a, b, k(w0), k(w1), bend))
    for i in range(5):
        yy = y - k(60 + i * 80)
        o.append(stroke([(x + k(10 + i * 6), yy), (x + k(16 + i * 6), yy - k(50))], 2, "#5a3f28", True))
    return "".join(o)


def acacia(x, y, s=1.0, seed=3):
    rnd = random.Random(seed)
    def k(v):
        return v * s
    o = []
    trunk = [(x, y), (x - k(20), y - k(200)), (x - k(60), y - k(360))]
    o.append(stroke(trunk, k(26), INK, True) + stroke(trunk, k(19), "#6e5038", True))
    for b in [((x - k(30), y - k(260)), (x - k(260), y - k(420))), ((x - k(40), y - k(300)), (x + k(160), y - k(430))),
              ((x - k(60), y - k(360)), (x - k(120), y - k(450))), ((x - k(50), y - k(330)), (x + k(40), y - k(450)))]:
        o.append(stroke([b[0], b[1]], k(12), INK, True) + stroke([b[0], b[1]], k(7), "#6e5038", True))
    for i in range(60):          # flat umbrella crown made of leaf clumps
        cx = x - k(80) + rnd.uniform(-k(300), k(300))
        cy = y - k(450) + rnd.uniform(-k(30), k(20)) + abs(cx - (x - k(80))) * 0.08
        o.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{k(rnd.uniform(26, 44)):.1f}" ry="{k(rnd.uniform(12, 20)):.1f}" fill="{rnd.choice(("#58703c", "#4b6233", "#667f45"))}" stroke="#2f3d20" stroke-width="1.6"/>')
    return "".join(o)


def savanna(chars=True):
    W, H = 1920, 1080
    o = ['<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fc3ea"/><stop offset="1" stop-color="#d9eef9"/></linearGradient>',
         '<linearGradient id="gr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9b450"/><stop offset="0.5" stop-color="#e2a945"/><stop offset="1" stop-color="#d49638"/></linearGradient>',
         '<filter id="soft"><feGaussianBlur stdDeviation="14"/></filter>',
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']
    far = "M0,420 C200,380 360,330 560,350 C760,370 840,300 1060,310 C1260,320 1360,360 1520,330 C1680,300 1800,340 1920,350 L1920,480 L0,480 Z"
    near = "M0,460 C260,430 420,400 640,420 C840,440 1000,380 1220,400 C1420,418 1600,390 1920,410 L1920,500 L0,500 Z"
    o.append(f'<path d="{far}" fill="#9a99cf" stroke="#6b69a0" stroke-width="2.5"/>')
    o.append(f'<path d="{near}" fill="#7c79b9" stroke="#5a578f" stroke-width="2.5"/>')
    o.append(f'<path d="M0,470 C400,462 900,474 1920,466 L1920,1080 L0,1080 Z" fill="url(#gr)" stroke="#b07a2a" stroke-width="2.5"/>')
    for y0, col, op in ((560, "#f3c467", 0.55), (660, "#d59a3a", 0.45), (780, "#f0bd5c", 0.45), (900, "#cf8f33", 0.4)):
        o.append(f'<path d="M-50,{y0} C500,{y0 - 30} 1200,{y0 + 30} 1980,{y0 - 10} L1980,{y0 + 40} C1200,{y0 + 70} 500,{y0 + 10} -50,{y0 + 40} Z" fill="{col}" opacity="{op}" filter="url(#soft)"/>')
    rnd = random.Random(2)
    for _ in range(140):          # painterly grass strokes
        x, y = rnd.uniform(0, W), rnd.uniform(480, H)
        L = rnd.uniform(8, 22) * (0.6 + (y - 480) / 600)
        o.append(f'<path d="M{x:.0f},{y:.0f} l{rnd.uniform(-4, 4):.1f},{-L:.1f}" stroke="{rnd.choice(("#b98632", "#c99a44", "#a8772a"))}" stroke-width="2" opacity="0.8"/>')
    o.append(giraffe(260, 482, 0.85) + giraffe(330, 486, 0.95))
    o.append(zebra(540, 476, 0.75) + zebra(600, 478, 0.75) + zebra(660, 476, 0.72))
    o.append(antelope(900, 478, 0.7, graze=True) + antelope(960, 478, 0.65) + antelope(1040, 480, 0.75))
    for i, (x, s) in enumerate(((1330, 0.42), (1420, 0.48), (1530, 0.62), (1640, 0.5), (1730, 0.46))):
        o.append(elephant(x, 482, s))
    o.append(acacia(1880, 760, 1.0))
    o.append(bare_tree(-10, 760, 1.0))
    for i in range(18):
        x, y = rnd.uniform(0, W), rnd.uniform(560, 1050)
        o.append(grass_clump(x, y, 0.5 + (y - 560) / 500, seed=i))
    if chars:
        tribe = [
            (330, 1040, 0.85, dict(view="three", mood="worried", style="short", child=True, pose=dict(ra=-30, rb=-20), seed=11)),
            (520, 1030, 1.0, dict(view="three", mood="worried", style="long", pose=dict(la=30, lb=-90, ra=40, rb=-100), seed=12)),
            (710, 1040, 1.02, dict(view="three", mood="neutral", style="short", pose=dict(ra=-30, rb=10, hand_r="spear", la=-4), seed=13, gaze=(1, 0))),
            (960, 1050, 1.08, dict(view="three", mood="angry", style="short", pose=dict(la=-28, lb=-48, hand_l="spear", ra=96, rb=-8, hand_r="point"), seed=14)),
            (1230, 1040, 0.95, dict(view="three", mood="worried", style="elder", pose=dict(lean=8, ra=40, rb=-20, hand_r="staff", lh=-8, rh=10, rk=-6), seed=15)),
            (1440, 1040, 0.98, dict(view="three", mood="shocked", style="short", pose=dict(la=10, ra=-6), seed=16)),
            (1650, 1040, 1.0, dict(view="three", mood="worried", style="long", pose=dict(ra=150, rb=78, la=-6), seed=17)),
        ]
        for x, y, s, kw in tribe:
            o.append(f'<ellipse cx="{x + 10}" cy="{y + 2}" rx="{60 * s:.0f}" ry="{10 * s:.0f}" fill="#b47e2c" opacity="0.45"/>')
            o.append(f'<g transform="translate({x},{y})">{person(scale=s * 0.95, **kw)}</g>')
    o.append(tall_grass(30, 1090, 1.0, 5) + tall_grass(1780, 1090, 0.9, 6))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(o)}</svg>'


def cave_scene():
    W, H = 1920, 1080
    rnd = random.Random(4)
    o = ['<linearGradient id="nsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#151a3a"/><stop offset="1" stop-color="#3b3a64"/></linearGradient>',
         '<radialGradient id="glow"><stop offset="0" stop-color="#ffb24a" stop-opacity="0.75"/><stop offset="0.6" stop-color="#ff8a2a" stop-opacity="0.18"/><stop offset="1" stop-color="#ff8a2a" stop-opacity="0"/></radialGradient>',
         '<linearGradient id="rock" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5a4434"/><stop offset="1" stop-color="#3a2c22"/></linearGradient>',
         f'<rect width="{W}" height="{H}" fill="url(#nsky)"/>']
    o += [f'<circle cx="{rnd.uniform(380, 1540):.0f}" cy="{rnd.uniform(60, 470):.0f}" r="{rnd.uniform(1.2, 3.2):.1f}" fill="#f8f2d4"/>' for _ in range(60)]
    o.append(f'<circle cx="1220" cy="210" r="40" fill="#f6efc8" stroke="{INK}" stroke-width="2.5"/>')
    o.append('<path d="M0,560 C300,520 600,540 900,520 C1200,500 1500,540 1920,520 L1920,1080 L0,1080 Z" fill="#2c2b4a"/>')
    wall = ("M0,0 L1920,0 L1920,1080 L1660,1080 C1700,880 1690,700 1610,540 C1530,380 1400,260 1240,200 C1060,130 860,130 700,190 "
            "C520,260 400,380 330,540 C260,700 250,880 290,1080 L0,1080 Z")
    o.append(f'<path d="{wall}" fill="url(#rock)" stroke="{INK}" stroke-width="5"/>')
    for _ in range(26):
        x = rnd.choice([rnd.uniform(20, 280), rnd.uniform(1660, 1900), rnd.uniform(400, 1500)])
        y = rnd.uniform(30, 160) if 380 < x < 1520 else rnd.uniform(60, 1040)
        o.append(f'<path d="M{x:.0f},{y:.0f} q{rnd.uniform(20, 60):.0f},{rnd.uniform(-12, 12):.0f} {rnd.uniform(50, 110):.0f},{rnd.uniform(-4, 4):.0f}" stroke="#2a1f17" stroke-width="3" fill="none" stroke-linecap="round" opacity="0.8"/>')
    # cave paintings on the right wall
    o.append(f'<g opacity="0.85" stroke="#b5532a" stroke-width="5" fill="none" stroke-linecap="round">'
             f'<path d="M1720,420 C1740,400 1790,400 1810,420 L1830,410 M1730,420 L1725,450 M1800,420 L1805,450"/>'
             f'<path d="M1745,520 L1745,560 M1745,530 L1730,548 M1745,530 L1760,548 M1745,560 L1735,585 M1745,560 L1755,585"/><circle cx="1745" cy="510" r="8"/></g>')
    o.append('<path d="M280,1080 C600,940 1300,930 1680,1080 Z" fill="#7a5c42" stroke="#1d1a17" stroke-width="4"/>')
    o.append(f'<ellipse cx="960" cy="960" rx="700" ry="330" fill="url(#glow)"/>')
    o.append(campfire(960, 1010, 1.5))
    o.append(f'<g transform="translate(660,1022)">{person("side", "neutral", dict(dy=166, lh=128, lk=-118, rh=122, rk=-112, la=56, lb=-30, ra=66, rb=-24), "short", 1.0, 21)}</g>')
    o.append(f'<g transform="translate(1270,1022) scale(-1,1)">{person("side", "happy", dict(dy=166, lh=128, lk=-118, rh=122, rk=-112, la=80, lb=-30, ra=90, rb=-40), "long", 1.0, 22)}</g>')
    o.append(f'<g transform="translate(1440,1030) scale(-1,1)">{person("three", "neutral", dict(dy=166, lh=128, lk=-118, rh=122, rk=-112, la=20, lb=-60, ra=30, rb=-70), "short", 0.62, 23, child=True)}</g>')
    o.append(bone(1100, 1046, 18, 1.1) + bone(1150, 1056, -28, 1.1))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(o)}</svg>'


def sheet():
    W, H = 1920, 1080
    o = [f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         f'<text x="60" y="78" font-family="Patrick Hand" font-size="54" fill="{INK}">ANCIENT HUMANS</text>']
    turns = [("front", "neutral", {}), ("three", "neutral", {}), ("side", "neutral", {}), ("back", "neutral", {})]
    for i, (view, mood, pose) in enumerate(turns):
        x = 170 + i * 250
        o.append(f'<g transform="translate({x},560)">{person(view, mood, pose, "short", 0.78, 31 + i)}</g>')
        o.append(f'<text x="{x}" y="600" text-anchor="middle" font-family="Patrick Hand" font-size="28" fill="#8a8a90">{view.replace("three", "3/4").upper()}</text>')
    cast = [("WOMAN", dict(view="three", mood="worried", style="long", seed=41)),
            ("ELDER", dict(view="three", mood="worried", style="elder", pose=dict(lean=8, ra=40, rb=-20, hand_r="staff", rk=-6), seed=42)),
            ("CHILD", dict(view="three", mood="shocked", style="short", child=True, seed=43))]
    for i, (name, kw) in enumerate(cast):
        x = 1200 + i * 230
        o.append(f'<g transform="translate({x},560)">{person(scale=0.78, **kw)}</g>')
        o.append(f'<text x="{x}" y="600" text-anchor="middle" font-family="Patrick Hand" font-size="28" fill="#8a8a90">{name}</text>')
    o.append(f'<line x1="60" y1="625" x2="{W - 60}" y2="625" stroke="#e3e3e6" stroke-width="3"/>')
    poses = [("POINTING", "three", "angry", dict(la=-28, lb=-48, hand_l="spear", ra=96, rb=-8, hand_r="point")),
             ("WALKING", "three", "neutral", dict(la=-28, lb=-48, hand_l="spear", ra=30, rb=-10, lh=-24, lk=10, rh=24, rk=-4)),
             ("BY THE FIRE", "side", "happy", dict(dy=166, lh=128, lk=-118, rh=122, rk=-112, la=56, lb=-30, ra=66, rb=-24, extra=campfire(150, 0, 0.8))),
             ("THROWING BONE", "side", "happy", dict(la=-50, lb=-10, ra=115, rb=-25, lh=-22, lk=8, rh=24, rk=-6, lean=6, extra=bone(150, -10, 15) + bone(200, -6, -25))),
             ("SHOCKED", "front", "shocked", dict(la=-125, lb=-100, ra=125, rb=100))]
    for i, (name, view, mood, pose) in enumerate(poses):
        x = 190 + i * 370
        o.append(f'<g transform="translate({x},1010)">{person(view, mood, pose, "short", 0.66, 51 + i)}</g>')
        o.append(f'<text x="{x + 30}" y="1055" text-anchor="middle" font-family="Patrick Hand" font-size="28" fill="#8a8a90">{name}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(o)}</svg>'


if __name__ == "__main__":
    jobs = [(sheet(), os.path.join(HERE, "ancient_sheet.png"), False),
            (savanna(), os.path.join(HERE, "scene_savanna.png"), False),
            (cave_scene(), os.path.join(HERE, "scene_cave.png"), False)]
    render(jobs)
    print("wrote", len(jobs))
