#!/usr/bin/env python3
"""Draw the two characters myself (no AI image service): a modern human and an ancient human (Ice Age caveman),
in the same look as the Dopamine video images - big round white head with a soft grey shade, thin black stick
limbs, clean black outlines, flat colours.

Every pose is built from joint angles (0 deg = limb straight down, positive = toward the way the character faces),
so new poses are one dict away.

    python3 gen.py   -> modern_sheet.png, ancient_sheet.png (+ .svg) and poses/<char>_<pose>.png (transparent)
"""
import math, os, random, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
INK, SHADE, WHITE = "#1b1b1d", "#d6d6d8", "#ffffff"
HAIR, HAIR_D, FUR, FUR_D = "#8a5a2e", "#4a2e14", "#8b5a2b", "#5a3716"
LW = 5            # line width of limbs and outlines
HEAD_R = 84


def P(x, y):
    return f"{x:.1f},{y:.1f}"


def seg(x, y, ang, length):
    a = math.radians(ang)
    return x + math.sin(a) * length, y + math.cos(a) * length


def chain(x, y, a1, l1, a2, l2):
    """Two-segment limb from (x, y): first segment at angle a1, second bent a2 relative to it."""
    x1, y1 = seg(x, y, a1, l1)
    x2, y2 = seg(x1, y1, a1 + a2, l2)
    return (x, y), (x1, y1), (x2, y2), a1 + a2


def line(pts, w=LW, color=INK):
    return f'<polyline points="{" ".join(P(*p) for p in pts)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'


# ---------------------------------------------------------------- faces
def eyes(view, mood, cx, cy):
    """Eyes and mouth. view: front / three / side / back."""
    if view == "back":
        return ""
    if view == "front":
        xs, mx = [cx - 26, cx + 26], cx
    elif view == "three":
        xs, mx = [cx - 4, cx + 40], cx + 20
    else:
        xs, mx = [cx + 42], cx + 50
    ey, my = cy - 4, cy + 34
    out = []
    for x in xs:
        if mood in ("bored", "neutral_lid"):
            out.append(f'<ellipse cx="{x}" cy="{ey}" rx="17" ry="13" fill="{WHITE}" stroke="{INK}" stroke-width="3.5"/>')
            out.append(f'<circle cx="{x + 2}" cy="{ey + 4}" r="5.5" fill="{INK}"/>')
            out.append(f'<path d="M{x - 18},{ey - 1} Q{x},{ey - 7} {x + 18},{ey - 1}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
            out.append(f'<path d="M{x - 15},{ey + 17} Q{x},{ey + 24} {x + 15},{ey + 17}" fill="none" stroke="#9a9aa0" stroke-width="3" stroke-linecap="round"/>')
        elif mood == "happy":
            out.append(f'<path d="M{x - 12},{ey + 4} Q{x},{ey - 10} {x + 12},{ey + 4}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
        elif mood == "shocked":
            out.append(f'<circle cx="{x}" cy="{ey - 2}" r="15" fill="{WHITE}" stroke="{INK}" stroke-width="3.5"/>')
            out.append(f'<circle cx="{x}" cy="{ey - 2}" r="4" fill="{INK}"/>')
        elif mood == "focused":
            out.append(f'<circle cx="{x + 3}" cy="{ey}" r="6.5" fill="{INK}"/>')
            out.append(f'<path d="M{x - 13},{ey - 16} L{x + 13},{ey - 11}" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>')
        else:  # neutral dot eyes
            out.append(f'<circle cx="{x}" cy="{ey}" r="6.5" fill="{INK}"/>')
    if mood == "happy":
        out.append(f'<path d="M{mx - 22},{my - 6} Q{mx},{my + 22} {mx + 22},{my - 6} Z" fill="#c0392b" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>')
    elif mood == "shocked":
        out.append(f'<ellipse cx="{mx}" cy="{my + 4}" rx="10" ry="14" fill="{INK}"/>')
    elif mood in ("bored", "neutral_lid"):
        out.append(f'<path d="M{mx - 11},{my + 2} Q{mx},{my - 3} {mx + 11},{my + 2}" fill="none" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>')
    elif mood == "focused":
        out.append(f'<path d="M{mx - 9},{my} L{mx + 9},{my}" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>')
    else:
        out.append(f'<path d="M{mx - 12},{my - 2} Q{mx},{my + 8} {mx + 12},{my - 2}" fill="none" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>')
    return "".join(out)


_uid = [0]


def head(cx, cy, view, mood):
    _uid[0] += 1
    cid = f"h{_uid[0]}"
    dx = {"front": 14, "three": 18, "side": 22, "back": 10}[view]
    return (f'<clipPath id="{cid}"><circle cx="{cx}" cy="{cy}" r="{HEAD_R}"/></clipPath>'
            f'<circle cx="{cx}" cy="{cy}" r="{HEAD_R}" fill="{SHADE}"/>'
            f'<circle cx="{cx + dx}" cy="{cy - 6}" r="{HEAD_R - 4}" fill="{WHITE}" clip-path="url(#{cid})"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{HEAD_R}" fill="none" stroke="{INK}" stroke-width="{LW}"/>'
            + eyes(view, mood, cx, cy))


def _tufts(points_out, points_in):
    """Shaggy outline: alternating tuft tips and valleys joined by curves."""
    d = f"M{P(*points_in[0])}"
    for tip, val in zip(points_out, points_in[1:]):
        d += f" Q{P(*tip)} {P(*val)}"
    return d


def hair_back(cx, cy, seed=3, view="front"):
    """Messy shaggy brown hair behind the head, framing the face down past the jaw."""
    rnd = random.Random(seed)
    a0, a1 = {"front": (150, 390), "three": (140, 395), "side": (175, 400), "back": (0, 360)}[view]
    n = 15
    vals, tips = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        r = HEAD_R + rnd.uniform(8, 16)
        vals.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * (i + 0.5) / n + rnd.uniform(-6, 6))
        r = HEAD_R + rnd.uniform(34, 50)
        # tufts hang down a little (gravity)
        tips.append((cx + math.cos(a) * r, cy + math.sin(a) * r + 10))
    d = _tufts(tips, vals)
    if view != "back":
        d += f" L{P(cx + 30, cy + 40)} L{P(cx - 30, cy + 40)} Z"
    else:
        d += " Z"
    strands = "".join(line([(cx + math.cos(math.radians(a)) * (HEAD_R + 10), cy + math.sin(math.radians(a)) * (HEAD_R + 10)),
                            (cx + math.cos(math.radians(a)) * (HEAD_R + 30), cy + math.sin(math.radians(a)) * (HEAD_R + 30) + 6)], 2.5, HAIR_D)
                       for a in range(int(a0) + 10, int(a1) - 5, 24))
    return f'<path d="{d}" fill="{HAIR}" stroke="{HAIR_D}" stroke-width="3.5" stroke-linejoin="round"/>' + strands


def hair_front(cx, cy, seed=5, view="front"):
    """Fringe over the top of the head (and the whole head from the back)."""
    rnd = random.Random(seed)
    if view == "back":
        return hair_back(cx, cy, seed + 1, "back").replace(HAIR + '"', HAIR + '"', 1)
    off = {"front": 0, "three": 14, "side": 26}[view]
    top = []
    for i in range(13):           # top edge just outside the head, left -> right
        a = math.radians(195 + 150 * i / 12)
        top.append((cx + math.cos(a) * (HEAD_R + 8), cy + math.sin(a) * (HEAD_R + 8)))
    k = 7                          # ragged lower edge, right -> left, tufts pointing down
    lo = []
    for i in range(k + 1):
        x = cx + HEAD_R * 0.92 - (HEAD_R * 1.84 - off) * i / k + off * 0.4
        lo.append((x, cy - HEAD_R * 0.42 + rnd.uniform(-6, 6)))
    tips = [((lo[i][0] + lo[i + 1][0]) / 2 + rnd.uniform(-4, 4), cy - HEAD_R * 0.12 + rnd.uniform(-8, 10)) for i in range(k)]
    d = "M" + " L".join(P(*p) for p in top) + f" L{P(*lo[0])}"
    for tip, val in zip(tips, lo[1:]):
        d += f" Q{P(*tip)} {P(*val)}"
    d += " Z"
    return f'<path d="{d}" fill="{HAIR}" stroke="{HAIR_D}" stroke-width="3.5" stroke-linejoin="round"/>'


# ---------------------------------------------------------------- bodies
def shirt(x, y, view, lean=0):
    """Modern white shirt torso; (x, y) = neck base."""
    w = {"front": 52, "back": 52, "three": 44, "side": 34}[view]
    h = 122
    t = math.radians(lean)
    def r(px, py):          # rotate around the neck for leaning (bottom stays over the hips)
        return x + px * math.cos(t) - py * math.sin(t), y + px * math.sin(t) + py * math.cos(t)
    pts = [r(-w * 0.72, 0), r(-w, 18), r(-w, h - 6), r(-w + 6, h), r(w - 6, h), r(w, h - 6), r(w, 18), r(w * 0.72, 0)]
    d = (f"M{P(*pts[0])} Q{P(*r(-w, 2))} {P(*pts[1])} L{P(*pts[2])} Q{P(*r(-w, h))} {P(*pts[3])} "
         f"L{P(*pts[4])} Q{P(*r(w, h))} {P(*pts[5])} L{P(*pts[6])} Q{P(*r(w, 2))} {P(*pts[7])} Z")
    shade = f'<path d="M{P(*r(-w + 8, 22))} L{P(*r(-w + 8, h - 10))}" stroke="{SHADE}" stroke-width="12" stroke-linecap="round"/>'
    return f'<path d="{d}" fill="{WHITE}" stroke="{INK}" stroke-width="{LW}" stroke-linejoin="round"/>' + shade, r(0, h)


def tunic(x, y, view, lean=0, seed=7):
    """Caveman fur tunic over one shoulder with a ragged hem; (x, y) = neck base."""
    rnd = random.Random(seed)
    w = {"front": 46, "back": 46, "three": 40, "side": 30}[view]
    h = 140
    t = math.radians(lean)
    def r(px, py):
        return x + px * math.cos(t) - py * math.sin(t), y + px * math.sin(t) + py * math.cos(t)
    # white bare chest/neck strip underneath
    chest = f'<path d="M{P(*r(-w * 0.6, 4))} L{P(*r(-w * 0.75, 70))} L{P(*r(0, 70))} L{P(*r(w * 0.2, 4))} Z" fill="{WHITE}" stroke="{INK}" stroke-width="{LW}" stroke-linejoin="round"/>'
    pts = [r(w * 0.55, -2), r(w, 30)]
    for i in range(9):      # ragged hem right -> left
        px = w + 4 - (2 * w + 8) * i / 8
        pts.append(r(px, h + (14 if i % 2 else 0) + rnd.uniform(-4, 5)))
    pts += [r(-w - 2, 60), r(-w * 0.55, 32)]
    if view == "back":
        pts = [r(-w * 0.6, -2), r(w * 0.6, -2)] + pts[1:-2] + [r(-w, 30)]
    d = "M" + " L".join(P(*p) for p in pts) + " Z"
    fur = "".join(line([r(px, py), r(px + rnd.uniform(-4, 4), py + 14)], 2.5, FUR_D)
                  for px, py in [(rnd.uniform(-w + 10, w - 10), rnd.uniform(40, h - 20)) for _ in range(9)])
    return (chest if view != "back" else "") + f'<path d="{d}" fill="{FUR}" stroke="{FUR_D}" stroke-width="4" stroke-linejoin="round"/>' + fur, r(0, h - 10)


# ---------------------------------------------------------------- props
def phone(x, y, ang=-20, glow=True):
    g = (f'<path d="M{x},{y} L{x - 110},{y - 120} L{x - 40},{y - 150} Z" fill="#cfe0ff" opacity="0.45"/>' if glow else "")
    return (g + f'<g transform="translate({x},{y}) rotate({ang})">'
            f'<rect x="-15" y="-27" width="30" height="54" rx="6" fill="#cfd3da" stroke="{INK}" stroke-width="4"/>'
            f'<rect x="-10" y="-20" width="20" height="38" rx="2" fill="#eef2f8"/></g>')


def spear(x, y, ang=25, length=330):
    a = math.radians(ang)
    dx, dy = math.sin(a), -math.cos(a)
    x0, y0 = x - dx * 120, y - dy * 120
    x1, y1 = x0 + dx * length, y0 + dy * length
    tip = [(x1 + dx * 44, y1 + dy * 44), (x1 - dy * 12, y1 + dx * 12), (x1 + dy * 12, y1 - dx * 12)]
    return (line([(x0, y0), (x1, y1)], 11, INK) + line([(x0, y0), (x1, y1)], 6, "#c49a6c")
            + f'<polygon points="{" ".join(P(*p) for p in tip)}" fill="#9a9a9a" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>')


def campfire(x, y):
    logs = (f'<rect x="{x - 48}" y="{y - 14}" width="96" height="14" rx="7" fill="#7a4a22" stroke="{INK}" stroke-width="3.5" transform="rotate(-12 {x} {y})"/>'
            f'<rect x="{x - 48}" y="{y - 14}" width="96" height="14" rx="7" fill="#8b5a2b" stroke="{INK}" stroke-width="3.5" transform="rotate(12 {x} {y})"/>')
    stones = "".join(f'<ellipse cx="{x + dx}" cy="{y + 2}" rx="13" ry="9" fill="#a8a8ad" stroke="{INK}" stroke-width="3"/>' for dx in (-58, -30, 30, 58))
    flame = (f'<path d="M{x - 30},{y - 12} C{x - 40},{y - 50} {x - 10},{y - 60} {x - 4},{y - 100} C{x + 10},{y - 70} {x + 40},{y - 60} {x + 30},{y - 12} Z" fill="#f28c28" stroke="{INK}" stroke-width="3.5"/>'
             f'<path d="M{x - 14},{y - 12} C{x - 18},{y - 34} {x},{y - 40} {x + 2},{y - 62} C{x + 10},{y - 40} {x + 22},{y - 34} {x + 14},{y - 12} Z" fill="#ffd23f"/>')
    return logs + flame + stones


def bone(x, y, ang=20, s=1.0):
    return (f'<g transform="translate({x},{y}) rotate({ang}) scale({s})">'
            f'<path d="M-22,-6 C-30,-18 -42,-8 -32,0 C-42,8 -30,18 -22,6 L22,6 C30,18 42,8 32,0 C42,-8 30,-18 22,-6 Z" '
            f'fill="#f3ead6" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/></g>')


def bush(x, y):
    rnd = random.Random(11)
    blobs = "".join(f'<circle cx="{x + dx}" cy="{y + dy}" r="{r}" fill="#3f7d3a" stroke="{INK}" stroke-width="3.5"/>'
                    for dx, dy, r in [(-60, -40, 42), (60, -40, 42), (-25, -80, 46), (30, -82, 46), (0, -40, 50)])
    berries = "".join(f'<circle cx="{x + rnd.uniform(-70, 70):.0f}" cy="{y + rnd.uniform(-110, -20):.0f}" r="6" fill="#c0392b" stroke="{INK}" stroke-width="2"/>' for _ in range(9))
    return blobs + berries


def chair(x, seat):
    """Simple stool/chair seen from the side, seat top at y = seat."""
    return (f'<rect x="{x - 62}" y="{seat - 200}" width="14" height="190" rx="6" fill="#b0b4bc" stroke="{INK}" stroke-width="4"/>'
            + line([(x - 52, seat + 10), (x - 58, 0)], LW + 1) + line([(x + 52, seat + 10), (x + 58, 0)], LW + 1)
            + f'<rect x="{x - 66}" y="{seat}" width="132" height="16" rx="6" fill="#b0b4bc" stroke="{INK}" stroke-width="4"/>')


# ---------------------------------------------------------------- ancient human (from the owner's reference)
SKIN_LINE = 4
HAIR2, HAIR2_D = "#6b4423", "#2e1c0e"


def cave_face(view, mood, cx, cy, r):
    if view == "back":
        return ""
    k = r / 54
    if view == "front":
        xs, mx = [cx - 19 * k, cx + 19 * k], cx
    elif view == "three":
        xs, mx = [cx - 4 * k, cx + 28 * k], cx + 14 * k
    else:
        xs, mx = [cx + 30 * k], cx + 36 * k
    ey, my = cy - 2 * k, cy + 26 * k
    o = []
    for i, x in enumerate(xs):
        inner = (i == 1) if len(xs) == 2 else True        # brow slopes down toward the nose
        if mood == "happy":
            o.append(f'<path d="M{x - 8 * k},{ey + 3 * k} Q{x},{ey - 8 * k} {x + 8 * k},{ey + 3 * k}" fill="none" stroke="{INK}" stroke-width="{4 * k}" stroke-linecap="round"/>')
            continue
        rr = 7 * k if mood == "shocked" else 5.5 * k
        o.append(f'<ellipse cx="{x}" cy="{ey}" rx="{rr}" ry="{rr * 1.25}" fill="{INK}"/>')
        o.append(f'<circle cx="{x + 1.5 * k}" cy="{ey - 2 * k}" r="{1.6 * k}" fill="{WHITE}"/>')
        if mood in ("angry", "focused"):
            d = 1 if (x > cx + (0 if view == "front" else 12 * k)) else -1
            # angry: inner end low
            y_in, y_out = ey - 9 * k, ey - 16 * k
            x_in, x_out = (x - 9 * k, x + 10 * k) if d > 0 else (x + 9 * k, x - 10 * k)
            o.append(f'<path d="M{x_out},{y_out} L{x_in},{y_in}" stroke="{INK}" stroke-width="{5 * k}" stroke-linecap="round"/>')
        elif mood == "shocked":
            o.append(f'<path d="M{x - 8 * k},{ey - 16 * k} Q{x},{ey - 21 * k} {x + 8 * k},{ey - 16 * k}" fill="none" stroke="{INK}" stroke-width="{3.5 * k}" stroke-linecap="round"/>')
        else:
            o.append(f'<path d="M{x - 8 * k},{ey - 14 * k} L{x + 8 * k},{ey - 15 * k}" stroke="{INK}" stroke-width="{4 * k}" stroke-linecap="round"/>')
    nx = (cx + 4 * k) if view == "front" else (mx + 8 * k)
    o.append(f'<path d="M{nx},{cy + 8 * k} q{3 * k},{3 * k} 0,{5 * k}" fill="none" stroke="{INK}" stroke-width="{2.5 * k}" stroke-linecap="round"/>')
    if mood in ("angry", "shocked", "happy"):
        w, h = (9 * k, 8 * k) if mood != "happy" else (13 * k, 9 * k)
        o.append(f'<path d="M{mx - w},{my - 2 * k} Q{mx},{my - 5 * k} {mx + w},{my - 2 * k} Q{mx + w * 0.6},{my + h} {mx},{my + h} Q{mx - w * 0.6},{my + h} {mx - w},{my - 2 * k} Z" fill="#3a1d1d" stroke="{INK}" stroke-width="{2.5 * k}" stroke-linejoin="round"/>')
        o.append(f'<ellipse cx="{mx}" cy="{my + h * 0.6}" rx="{w * 0.55}" ry="{h * 0.3}" fill="#e78a8a"/>')
    elif mood == "focused":
        o.append(f'<path d="M{mx - 8 * k},{my} L{mx + 8 * k},{my - 1 * k}" stroke="{INK}" stroke-width="{3 * k}" stroke-linecap="round"/>')
    else:
        o.append(f'<path d="M{mx - 8 * k},{my - 1 * k} Q{mx},{my + 4 * k} {mx + 8 * k},{my - 1 * k}" fill="none" stroke="{INK}" stroke-width="{3 * k}" stroke-linecap="round"/>')
    return "".join(o)


def spikes(cx, cy, r, a0, a1, n, rin, rout, seed, droop=0.0):
    """Ring of sharp hair spikes between angles a0..a1 (degrees, 0 = right, 90 = down)."""
    rnd = random.Random(seed)
    pts = []
    for i in range(n * 2 + 1):
        a = math.radians(a0 + (a1 - a0) * i / (n * 2) + (rnd.uniform(-4, 4) if i % 2 else 0))
        rad = r + (rnd.uniform(rout * 0.65, rout) if i % 2 else rnd.uniform(rin * 0.4, rin))
        x, y = cx + math.cos(a) * rad, cy + math.sin(a) * rad
        if i % 2:       # tips lean back / down a bit
            x -= droop * rad * 0.15
        pts.append((x, y))
    return pts


def cave_head(cx, cy, view, mood, r, hair="short"):
    """Flat white round head (no shading) with short spiky messy dark-brown hair on top and at the back."""
    face_dir = {"front": 0, "three": 1, "side": 1, "back": 0}[view]
    if view == "back":
        back = spikes(cx, cy, r, 0, 360, 22, 8, 26, 21)
        d = "M" + " L".join(P(*q) for q in back) + " Z"
        hair = f'<path d="{d}" fill="{HAIR2}" stroke="{HAIR2_D}" stroke-width="3" stroke-linejoin="round"/>'
        strands = "".join(line([(cx + math.cos(math.radians(a)) * r * 0.2, cy + math.sin(math.radians(a)) * r * 0.2),
                                (cx + math.cos(math.radians(a)) * r * 0.85, cy + math.sin(math.radians(a)) * r * 0.85)], 2.5, HAIR2_D)
                           for a in range(0, 360, 40))
        neck_skin = f'<path d="M{cx - r * 0.35},{cy + r * 0.8} Q{cx},{cy + r * 1.05} {cx + r * 0.35},{cy + r * 0.8}" fill="none" stroke="{INK}" stroke-width="3"/>'
        return hair + strands
    # hair mass behind: from the back of the head over the top; more at the back in 3/4 and side
    a0, a1 = {"front": (165, 375), "three": (150, 345), "side": (125, 330)}[view]
    back = spikes(cx, cy, r, a0, a1, 13, 6, 28, 7, droop=face_dir)
    d = f"M{P(cx, cy)} L" + " L".join(P(*q) for q in back) + " Z"
    if hair == "long":       # long messy hair down past the shoulders
        sw = r * 1.25
        pts = [(cx - sw, cy + r * 1.7), (cx - sw * 0.7, cy + r * 1.95), (cx - sw * 0.4, cy + r * 1.6), (cx, cy + r * 0.2),
               (cx + sw * 0.4, cy + r * 1.6), (cx + sw * 0.7, cy + r * 1.95), (cx + sw, cy + r * 1.7)]
        top = spikes(cx, cy, r, -10, 190, 10, 6, 18, 8)
        d = "M" + " L".join(P(*q) for q in [pts[-1]] + top + pts[:3]) + f" L{P(*pts[3])} L{P(*pts[4])} L{P(*pts[5])} Z"
    out = [f'<path d="{d}" fill="{HAIR2}" stroke="{HAIR2_D}" stroke-width="3" stroke-linejoin="round"/>']
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{WHITE}" stroke="{INK}" stroke-width="{SKIN_LINE}"/>')
    # fringe: spikes hanging over the forehead
    f0, f1 = {"front": (198, 342), "three": (205, 350), "side": (220, 345)}[view]
    rim = [(cx + math.cos(math.radians(a)) * (r + 4), cy + math.sin(math.radians(a)) * (r + 4))
           for a in [f0 + (f1 - f0) * i / 10 for i in range(11)]]
    rnd = random.Random(9)
    lo = []
    for i in range(7, -1, -1):
        x = cx + math.cos(math.radians(f0)) * r * 0.95 + (math.cos(math.radians(f1)) - math.cos(math.radians(f0))) * r * 0.95 * i / 7
        top = cy - math.sqrt(max(r * r - (x - cx) ** 2, 0))
        depth = (r * 0.42 if i % 2 else r * 0.18) + rnd.uniform(-3, 4)
        lo.append((x + (6 if i % 2 else 0) * (1 if face_dir else rnd.choice((-1, 1))), top + depth))
    d = "M" + " L".join(P(*q) for q in rim + lo) + " Z"
    out.append(f'<path d="{d}" fill="{HAIR2}" stroke="{HAIR2_D}" stroke-width="3" stroke-linejoin="round"/>')
    # sideburn tuft at the back of the head
    if False:
        tuft = spikes(cx, cy, r * 0.96, 120, 200, 3, 2, 20, 4)
        out.append(f'<path d="M{P(cx - r * 0.3, cy + r * 0.2)} L' + " L".join(P(*q) for q in tuft) + f' Z" fill="{HAIR2}" stroke="{HAIR2_D}" stroke-width="3" stroke-linejoin="round"/>')
    out.append(cave_face(view, mood, cx, cy, r))
    return "".join(out)


def cave_tunic(neck_x, neck_y, hip_x, hip_y, view, seed=7):
    """One-shoulder fur tunic down to the knees, rope belt, bare chest on the other side."""
    rnd = random.Random(seed)
    w = {"front": 38, "back": 38, "three": 34, "side": 24}[view]
    dx = hip_x - neck_x
    def at(f, px):        # point along the spine (f = 0 at neck, 1 at hip) offset px sideways
        return neck_x + dx * f + px, neck_y + (hip_y - neck_y) * f
    hem_y = min(hip_y + 62, -6)
    out = []
    # bare torso underneath (white skin, outlined)
    if view != "back":
        sk = [at(0.02, -w * 1.05), at(0.02, w * 1.05), at(0.5, w * 1.0), at(0.5, -w * 1.0)]
        out.append(f'<path d="M{P(*sk[0])} L{P(*sk[1])} L{P(*sk[2])} L{P(*sk[3])} Z" fill="{WHITE}" stroke="{INK}" stroke-width="{SKIN_LINE}" stroke-linejoin="round"/>')
    strap_side = -1 if view != "back" else 1
    pts = [at(0.0, strap_side * w * 1.05), at(0.0, strap_side * w * 0.2)]
    pts += [at(0.38, -strap_side * w * 1.0) if view != "side" else at(0.32, w * 0.9)]
    pts += [at(0.6, -strap_side * w * 1.05) if view != "side" else at(0.6, w * 1.0)]
    # skirt flares a little, ragged hem
    hem = []
    for i in range(9):
        f = i / 8
        x = hip_x + (-strap_side) * (w * 1.25) - (-strap_side) * (w * 2.5) * f
        hem.append((x + rnd.uniform(-3, 3), hem_y + (12 if i % 2 else 0) + rnd.uniform(-4, 4)))
    pts += hem
    pts += [at(0.6, strap_side * w * 1.05), at(0.15, strap_side * w * 1.15)]
    d = "M" + " L".join(P(*q) for q in pts) + " Z"
    out.append(f'<path d="{d}" fill="{FUR}" stroke="{INK}" stroke-width="{SKIN_LINE}" stroke-linejoin="round"/>')
    for _ in range(14):       # fur texture strokes
        f = rnd.uniform(0.1, 1.25)
        x0, y0 = at(min(f, 1.0), rnd.uniform(-w * 0.8, w * 0.8))
        if f > 1:
            y0 = hip_y + (f - 1) * 180
        out.append(line([(x0, y0), (x0 + rnd.uniform(-3, 3), y0 + rnd.uniform(9, 15))], 2.2, FUR_D))
    by = hip_y - 6
    out.append(f'<path d="M{P(hip_x - w * 1.12, by)} Q{P(hip_x, by + 6)} {P(hip_x + w * 1.12, by)}" fill="none" stroke="#3b2510" stroke-width="7" stroke-linecap="round"/>')
    return "".join(out)


def tall_spear(x, y, ground=0):
    """Long wooden spear held upright, taller than the caveman, leaf-shaped stone tip with a binding."""
    top = y - 330
    bot = ground
    shaft = line([(x, bot), (x - 6, top)], 13, INK) + line([(x, bot), (x - 6, top)], 7, "#8a5a33")
    tip = (f'<path d="M{x - 6},{top + 4} C{x - 22},{top - 30} {x - 14},{top - 60} {x - 6},{top - 82} '
           f'C{x + 4},{top - 60} {x + 10},{top - 30} {x - 6},{top + 4} Z" fill="#9b7b5b" stroke="{INK}" stroke-width="3.5"/>')
    bind = "".join(line([(x - 13, top + 4 + i * 6), (x + 1, top + 1 + i * 6)], 3, "#3b2510") for i in range(3))
    return shaft + tip + bind


def point_hand(x, y, ang):
    a = math.radians(ang)
    fx, fy = x + math.sin(a) * 22, y + math.cos(a) * 22
    return line([(x, y), (fx, fy)], 9, INK) + line([(x, y), (fx, fy)], 3.5, WHITE)


# ---------------------------------------------------------------- one figure
DIMS = {
    "modern": dict(r=84, torso=122, arm=(62, 60), leg=(72, 70), neck=76, hip=138),
    "ancient": dict(r=54, torso=150, arm=(80, 76), leg=(98, 96), neck=66, hip=194),
}


def figure(kind, view, pose, mood):
    """kind 'modern' | 'ancient'. pose keys (degrees): la/lb = left arm (back arm) shoulder/elbow, ra/rb = right arm
    (front arm), lh/lk, rh/rk = legs, dy = body drop (sitting), lean, hand_l/hand_r = prop names, extra = svg."""
    D = DIMS[kind]
    p = dict(la=-8, lb=0, ra=8, rb=0, lh=-4, lk=0, rh=4, rk=0, dy=0, lean=0)
    p.update(pose)
    hip_y = -D["hip"] + p["dy"]
    th = D["torso"]
    lean = p["lean"]
    t = math.radians(lean)
    neck = (math.sin(t) * th, hip_y - math.cos(t) * th)
    head_c = (neck[0] + math.sin(t) * D["neck"], neck[1] - math.cos(t) * D["neck"])
    spread = {"front": 20, "back": 20, "three": 14, "side": 4}[view] * (0.7 if kind == "ancient" else 1)
    sh = {"front": 47, "back": 47, "three": 38, "side": 8}[view] * (0.66 if kind == "ancient" else 1)

    legs = []
    for side, h, k in ((-1, p["lh"], p["lk"]), (1, p["rh"], p["rk"])):
        a, b, c, end = chain(side * spread, hip_y, h, D["leg"][0], k, D["leg"][1])
        foot_dir = 1 if view in ("side", "three") else side
        foot = (c[0] + foot_dir * 18, c[1] + 1)
        legs.append(line([a, b, c, foot], LW if kind == "modern" else 4.5))
    sx, sy = neck[0], neck[1] + (24 if kind == "modern" else 14)
    arms = []
    for side, a1, a2, prop in ((-1, p["la"], p["lb"], p.get("hand_l")), (1, p["ra"], p["rb"], p.get("hand_r"))):
        a, b, c, end = chain(sx + side * sh, sy, a1, D["arm"][0], a2, D["arm"][1])
        arms.append((line([a, b, c], LW if kind == "modern" else 4.5), c, end, prop))

    if kind == "modern":
        body, waist = shirt(neck[0], neck[1], view, lean)
    else:
        body = cave_tunic(neck[0], neck[1], 0, hip_y, view)
        if view != "back":     # thin neck
            body = line([(head_c[0], head_c[1] + D["r"] - 4), (neck[0], neck[1] + 4)], 4.5) + body
    out = [p.get("behind", "")]
    far, near = arms
    out.append(far[0])
    out += legs
    out.append(body)
    if view == "back" or abs(p["ra"]) < 25 and abs(p["rb"]) < 30:
        out.insert(out.index(body), near[0]); near = (None,) + near[1:]
    out.append(head(*head_c, view, mood) if kind == "modern" else cave_head(*head_c, view, mood, D["r"], p.get("hair", "short")))
    for arm_svg, c, end, prop in (far, near):
        if prop == "phone":
            out.append(phone(c[0] + 4, c[1] - 14, ang=-15, glow=False))
        elif prop == "spear":
            out.append(tall_spear(c[0] + 4, c[1], 0))
        elif prop == "bone":
            out.append(bone(c[0] + 8, c[1] - 6, 30, 0.8))
    if view != "back" and near[0]:
        out.append(near[0])
    for arm_svg, c, end, prop in (far, near):
        rr = 10 if kind == "modern" else 8.5
        if prop == "point":
            out.append(point_hand(c[0], c[1], end))
        out.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{rr}" fill="{WHITE}" stroke="{INK}" stroke-width="3.5"/>')
    out.append(p.get("extra", ""))
    return "".join(out)


TURN = [("front", {}), ("three", {"la": -6, "ra": 6}), ("side", {"la": -4, "ra": 4, "lh": -2, "rh": 2}), ("back", {})]

MODERN_POSES = [
    ("scrolling", "three", "bored", dict(ra=25, rb=-125, la=30, lb=-115, hand_r="phone")),
    ("excited", "front", "happy", dict(la=-140, lb=-15, ra=140, rb=15, lh=-10, rh=10)),
    ("shocked", "front", "shocked", dict(la=-120, lb=-105, ra=120, rb=105, lh=-6, rh=6)),
    ("sitting", "side", "bored", dict(dy=60, lh=90, lk=-90, rh=86, rk=-86, ra=35, rb=-115, la=30, lb=-110,
                                      hand_r="phone", behind=chair(-10, -76))),
    ("walking", "side", "neutral", dict(la=-28, lb=-20, ra=30, rb=-10, lh=-24, lk=10, rh=24, rk=-4)),
]
ANCIENT_POSES = [
    ("pointing", "three", "angry", dict(la=-38, lb=20, ra=95, rb=-8, hand_l="spear", hand_r="point", lh=-6, rh=8)),
    ("walking_spear", "three", "neutral", dict(la=-38, lb=20, ra=30, rb=-20, lh=-22, lk=10, rh=22, rk=-4, hand_l="spear")),
    ("by_campfire", "side", "focused", dict(dy=176, lh=130, lk=-112, rh=125, rk=-108, la=60, lb=-25, ra=70, rb=-20,
                                            extra=campfire(220, 0))),
    ("throwing_bone", "side", "happy", dict(la=-50, lb=-10, ra=115, rb=-25, lh=-22, lk=8, rh=24, rk=-6, lean=8,
                                             extra=bone(170, -12, 15) + bone(225, -8, -25))),
    ("crouch_bush", "side", "shocked", dict(dy=110, lh=100, lk=-115, rh=92, rk=-112, la=80, lb=-5, ra=90, rb=-10, lean=14,
                                             extra=bush(280, 0))),
]


def sheet(kind, title, poses):
    W, H = 1920, 1080
    parts = [f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
             f'<text x="60" y="78" font-family="Patrick Hand" font-size="54" fill="{INK}">{title}</text>',
             f'<line x1="60" y1="560" x2="{W - 60}" y2="560" stroke="#e3e3e6" stroke-width="3"/>']
    s1 = 0.78
    for i, (view, pose) in enumerate(TURN):
        x = 300 + i * 440
        parts.append(f'<g transform="translate({x},505) scale({s1})">{figure(kind, view, pose, "neutral")}</g>')
        parts.append(f'<text x="{x}" y="545" text-anchor="middle" font-family="Patrick Hand" font-size="30" fill="#8a8a90">{view.replace("three", "3/4").upper()}</text>')
    s2 = 0.66
    for i, (name, view, mood, pose) in enumerate(poses):
        x = 220 + i * 370
        parts.append(f'<g transform="translate({x},1010) scale({s2})">{figure(kind, view, pose, mood)}</g>')
        parts.append(f'<text x="{x}" y="1055" text-anchor="middle" font-family="Patrick Hand" font-size="28" fill="#8a8a90">{name.replace("_", " ").upper()}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(parts)}</svg>'


def single(kind, view, mood, pose):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="900" viewBox="-450 -720 900 900">'
            f'{figure(kind, view, pose, mood)}</svg>')


def render(svgs):
    """svgs: list of (svg text, png path, transparent?) -> PNGs via the pre-installed Chromium."""
    font = os.path.abspath(os.path.join(HERE, "..", "..", "projects", "dopamine-layered", "assets", "fonts", "PatrickHand-Regular.ttf"))
    js = ["const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();"]
    import json as _j
    for svg, out, transp in svgs:
        w = int(svg.split('width="')[1].split('"')[0]); h = int(svg.split('height="')[1].split('"')[0])
        import base64
        fdata = base64.b64encode(open(font, "rb").read()).decode()
        html = (f"<html><head><style>@font-face{{font-family:'Patrick Hand';src:url(data:font/ttf;base64,{fdata})}}"
                f"html,body{{margin:0;background:transparent}}</style></head><body>{svg}</body></html>")
        js.append(f"await p.setViewportSize({{width:{w},height:{h}}});await p.setContent({_j.dumps(html)});"
                  f"await p.evaluate(()=>document.fonts.ready);"
                  f"await p.screenshot({{path:{_j.dumps(out)},omitBackground:{str(transp).lower()}}});")
    js.append("await b.close();})();")
    f = os.path.join(HERE, "_render.js")
    open(f, "w").write("".join(js))
    subprocess.run(["node", f], check=True, cwd=HERE)
    os.remove(f)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "poses"), exist_ok=True)
    jobs = []
    for kind, title, poses in (("modern", "MODERN HUMAN", MODERN_POSES),):     # ancient humans: ancient.py
        svg = sheet(kind, title, poses)
        open(os.path.join(HERE, f"{kind}_sheet.svg"), "w").write(svg)
        jobs.append((svg, os.path.join(HERE, f"{kind}_sheet.png"), False))
        for view, pose in TURN:
            jobs.append((single(kind, view, "neutral", pose), os.path.join(HERE, "poses", f"{kind}_{view}.png"), True))
        for name, view, mood, pose in poses:
            jobs.append((single(kind, view, mood, pose), os.path.join(HERE, "poses", f"{kind}_{name}.png"), True))
    render(jobs)
    print("wrote", len(jobs), "images")
