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


# ---------------------------------------------------------------- one figure
def figure(kind, view, pose, mood):
    """kind 'modern' | 'ancient'. pose keys (degrees): la/lb = left arm (back arm) shoulder/elbow, ra/rb = right arm
    (front arm), lh/lk, rh/rk = legs, dy = body drop (sitting), lean, hand_l/hand_r = prop names, extra = svg."""
    p = dict(la=-8, lb=0, ra=8, rb=0, lh=-4, lk=0, rh=4, rk=0, dy=0, lean=0)
    p.update(pose)
    hip_y = -138 + p["dy"]
    th = 122 if kind == "modern" else 130
    lean = p["lean"]
    t = math.radians(lean)
    neck = (math.sin(t) * th, hip_y - math.cos(t) * th)
    head_c = (neck[0] + math.sin(t) * 76, neck[1] - math.cos(t) * 76)
    spread = {"front": 20, "back": 20, "three": 14, "side": 4}[view]
    sh = {"front": 47, "back": 47, "three": 38, "side": 8}[view]
    out_back, out_front = [], []

    # legs
    legs = []
    for side, h, k in ((-1, p["lh"], p["lk"]), (1, p["rh"], p["rk"])):
        a, b, c, end = chain(side * spread, hip_y, h, 72, k, 70)
        foot_dir = 1 if view in ("side", "three") else side
        foot = (c[0] + foot_dir * 20, c[1] + 1)
        legs.append(line([a, b, c, foot]))
    # arms (left = far/back arm, right = near/front arm)
    sx, sy = neck[0], neck[1] + 24
    arms, hands = [], []
    for side, a1, a2, prop in ((-1, p["la"], p["lb"], p.get("hand_l")), (1, p["ra"], p["rb"], p.get("hand_r"))):
        a, b, c, end = chain(sx + side * sh, sy, a1, 62, a2, 60)
        arms.append((line([a, b, c]), c, end, prop))

    body, waist = (shirt if kind == "modern" else tunic)(neck[0], neck[1], view, lean)
    out = []
    out.append(p.get("behind", ""))
    if kind == "ancient":
        out.append(hair_back(*head_c, view=view))
    # far arm behind body
    far, near = arms
    out.append(far[0])
    out += legs
    out.append(body)
    if view == "back" or abs(p["ra"]) < 25 and abs(p["rb"]) < 30:
        out.insert(out.index(body), near[0]); near = (None,) + near[1:]
    out.append(head(*head_c, view, mood))
    if kind == "ancient":
        out.append(hair_front(*head_c, view=view))
    for arm_svg, c, end, prop in (far, near):
        if prop == "phone":
            out.append(phone(c[0] + 4, c[1] - 14, ang=-15, glow=False))
        elif prop == "spear":
            out.append(spear(c[0], c[1]))
        elif prop == "bone":
            out.append(bone(c[0] + 8, c[1] - 6, 30, 0.8))
    if view != "back" and near[0]:
        out.append(near[0])
    for arm_svg, c, end, prop in (far, near):
        if kind == "modern":
            out.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="10" fill="{WHITE}" stroke="{INK}" stroke-width="3.5"/>')
        else:
            out.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="6" fill="{INK}"/>')
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
    ("walking_spear", "three", "neutral", dict(la=-25, lb=-10, ra=35, rb=-50, lh=-24, lk=10, rh=24, rk=-4, hand_r="spear")),
    ("by_campfire", "side", "focused", dict(dy=126, lh=130, lk=-112, rh=125, rk=-108, la=60, lb=-25, ra=70, rb=-20,
                                            extra=campfire(190, 0))),
    ("throwing_bone", "side", "happy", dict(la=-50, lb=-10, ra=115, rb=-25, lh=-22, lk=8, rh=24, rk=-6, lean=8,
                                             extra=bone(150, -12, 15) + bone(205, -8, -25))),
    ("excited", "front", "happy", dict(la=-140, lb=-15, ra=140, rb=15, lh=-10, rh=10)),
    ("crouch_bush", "side", "focused", dict(dy=82, lh=100, lk=-115, rh=92, rk=-112, la=80, lb=-5, ra=90, rb=-10, lean=14,
                                             extra=bush(250, 0))),
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
    for kind, title, poses in (("modern", "MODERN HUMAN", MODERN_POSES), ("ancient", "ANCIENT HUMAN", ANCIENT_POSES)):
        svg = sheet(kind, title, poses)
        open(os.path.join(HERE, f"{kind}_sheet.svg"), "w").write(svg)
        jobs.append((svg, os.path.join(HERE, f"{kind}_sheet.png"), False))
        for view, pose in TURN:
            jobs.append((single(kind, view, "neutral", pose), os.path.join(HERE, "poses", f"{kind}_{view}.png"), True))
        for name, view, mood, pose in poses:
            jobs.append((single(kind, view, mood, pose), os.path.join(HERE, "poses", f"{kind}_{name}.png"), True))
    render(jobs)
    print("wrote", len(jobs), "images")
