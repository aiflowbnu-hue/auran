#!/usr/bin/env python3
"""Modern location samples in the same flat, outlined, slightly hand-drawn look as the ancient scenes, with the
modern character from gen.py: a bedroom at midnight (phone glow), a Silicon Valley tech office, a Las Vegas casino.

    python3 modern_scenes.py   -> scene_bedroom.png, scene_office.png, scene_casino.png
"""
import math, os, random
from gen import figure, render, P, chair
from ancient import stroke, smooth, uid

HERE = os.path.dirname(os.path.abspath(__file__))
INK = "#1b1b1d"
W, H = 1920, 1080


def wobble(svg, seed=1, scale=2.2):
    fid = uid("mw")
    return (f'<filter id="{fid}" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="{seed}"/>'
            f'<feDisplacementMap in="SourceGraphic" scale="{scale}"/></filter><g filter="url(#{fid})">{svg}</g>')


def guy(x, y, s, view, mood, pose, seed=1, flip=False):
    sx = -s if flip else s
    return f'<g transform="translate({x},{y}) scale({sx},{s})">{wobble(figure("modern", view, pose, mood), seed)}</g>'


def rect(x, y, w, h, fill, rx=0, sw=3, stroke_=INK, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke_}" stroke-width="{sw}" {extra}/>'


def phone_in_hand(x, y, ang=-15, glow=True):
    g = ""
    if glow:
        g = (f'<radialGradient id="pg"><stop offset="0" stop-color="#bfe0ff" stop-opacity="0.9"/><stop offset="1" stop-color="#bfe0ff" stop-opacity="0"/></radialGradient>'
             f'<ellipse cx="{x - 40}" cy="{y - 60}" rx="170" ry="140" fill="url(#pg)"/>')
    return g + (f'<g transform="translate({x},{y}) rotate({ang})">{rect(-17, -30, 34, 60, "#2b2f38", 7, 3.5)}'
                f'{rect(-13, -24, 26, 46, "#cfe8ff", 3, 0)}</g>')


# ------------------------------------------------------------------ bedroom at midnight
def bedroom():
    rnd = random.Random(3)
    o = ['<linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#28305a"/><stop offset="1" stop-color="#1c2240"/></linearGradient>',
         '<linearGradient id="nightsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f1430"/><stop offset="1" stop-color="#2d2c58"/></linearGradient>',
         f'<rect width="{W}" height="{H}" fill="url(#wall)"/>',
         f'<rect y="820" width="{W}" height="260" fill="#3a2f3a"/>', stroke([(0, 820), (W, 820)], 4, INK)]
    # window with the city at night
    o.append(rect(1180, 150, 520, 420, "url(#nightsky)", 8, 6))
    o.append(f'<circle cx="1590" cy="230" r="34" fill="#f6efc8" stroke="{INK}" stroke-width="2.5"/>')
    o += [f'<circle cx="{rnd.uniform(1200, 1680):.0f}" cy="{rnd.uniform(170, 330):.0f}" r="{rnd.uniform(1, 2.6):.1f}" fill="#f8f2d4"/>' for _ in range(22)]
    bx = 1190
    for i, (w, h) in enumerate(((60, 140), (80, 210), (50, 170), (90, 250), (60, 150), (70, 200), (60, 120))):
        o.append(rect(bx, 570 - h, w, h, "#161a33", 0, 2))
        for _ in range(int(h / 30)):
            o.append(rect(bx + rnd.randint(8, w - 18), 570 - h + rnd.randint(10, h - 20), 8, 10, rnd.choice(("#f7d774", "#f7d774", "#3a3f66")), 0, 0))
        bx += w + 4
    o.append(stroke([(1440, 150), (1440, 570)], 6) + stroke([(1180, 360), (1700, 360)], 6))
    o.append(rect(1150, 130, 40, 470, "#5b4a7a", 4, 3) + rect(1690, 130, 40, 470, "#5b4a7a", 4, 3))     # curtains
    # wall clock 12:00
    o.append(f'<circle cx="420" cy="230" r="70" fill="#f3f0e6" stroke="{INK}" stroke-width="5"/>'
             + stroke([(420, 230), (420, 180)], 6) + stroke([(420, 230), (424, 190)], 4)
             + "".join(stroke([(420 + math.sin(math.radians(a)) * 58, 230 - math.cos(math.radians(a)) * 58),
                               (420 + math.sin(math.radians(a)) * 66, 230 - math.cos(math.radians(a)) * 66)], 3) for a in range(0, 360, 30)))
    # bed: headboard, mattress, blanket
    o.append(rect(240, 520, 70, 330, "#6b4a3a", 10, 4))
    o.append(rect(300, 690, 900, 90, "#ece7f4", 14, 4))
    o.append(rect(300, 770, 900, 70, "#5a4a6a", 8, 4))
    o.append(f'<path d="M330,690 C330,660 430,650 470,665 C500,676 500,690 480,700 L340,705 Z" fill="#ffffff" stroke="{INK}" stroke-width="4"/>')
    # the guy sitting up in bed, scrolling, phone light on his face
    pose = dict(dy=134, lh=92, lk=-4, rh=90, rk=-2, ra=40, rb=-120, la=34, lb=-114, lean=-4, hand_r="phone")
    o.append('<radialGradient id="pg"><stop offset="0" stop-color="#bfe0ff" stop-opacity="0.8"/><stop offset="1" stop-color="#bfe0ff" stop-opacity="0"/></radialGradient>'
             '<ellipse cx="600" cy="520" rx="200" ry="170" fill="url(#pg)"/>')
    o.append(guy(500, 830, 1.15, "side", "bored", pose, 2))
    o.append(f'<path d="M560,700 C700,690 900,686 1180,694 L1190,770 L540,770 Z" fill="#7b6aa8" stroke="{INK}" stroke-width="4"/>')
    o.append(f'<path d="M640,705 C760,720 880,712 980,716" stroke="#5f528a" stroke-width="3" fill="none"/>')
    # rug
    o.append(f'<ellipse cx="760" cy="950" rx="420" ry="70" fill="#4a3d63" stroke="{INK}" stroke-width="4"/><ellipse cx="760" cy="950" rx="360" ry="52" fill="none" stroke="#6b5a8a" stroke-width="4" stroke-dasharray="14 10"/>')
    # nightstand + lamp off + charger cable
    o.append(rect(1240, 690, 150, 140, "#6b4a3a", 6, 4) + stroke([(1240, 740), (1390, 740)], 3))
    o.append(f'<path d="M1285,690 L1295,620 L1335,620 L1345,690 Z" fill="#c9b98f" stroke="{INK}" stroke-width="3"/>')
    o.append('<rect width="1920" height="1080" fill="#0b1030" opacity="0.18"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(o)}</svg>'


# ------------------------------------------------------------------ Silicon Valley tech office
def monitor(x, y, s=1.0, screen="#d6e9ff", content=""):
    def k(v):
        return v * s
    return (rect(x - k(80), y - k(110), k(160), k(100), "#2b2f38", k(8), 3.5)
            + rect(x - k(72), y - k(102), k(144), k(84), screen, k(3), 0) + content
            + rect(x - k(8), y - k(10), k(16), k(14), "#7d828c", 0, 3) + rect(x - k(40), y + k(2), k(80), k(8), "#7d828c", k(4), 3))


def plant(x, y, s=1.0):
    def k(v):
        return v * s
    leaves = "".join(f'<path d="M{x},{y - k(40)} q{k(dx * 0.5)},{k(-60)} {k(dx)},{k(-90 + abs(dx) * 0.4)} q{k(-dx * 0.2)},{k(40)} {k(-dx)},{k(90 - abs(dx) * 0.4)} Z" fill="#4f8a4a" stroke="{INK}" stroke-width="2.5"/>'
                     for dx in (-60, -30, 0, 30, 60))
    return leaves + f'<path d="M{x - k(36)},{y - k(46)} L{x + k(36)},{y - k(46)} L{x + k(28)},{y} L{x - k(28)},{y} Z" fill="#e8e2d4" stroke="{INK}" stroke-width="3"/>'


def office():
    rnd = random.Random(5)
    o = ['<linearGradient id="dsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fc6ec"/><stop offset="1" stop-color="#e3f2fb"/></linearGradient>',
         f'<rect width="{W}" height="{H}" fill="#eef0f3"/>']
    # big glass wall with the city
    o.append(rect(80, 80, 1760, 560, "url(#dsky)", 6, 5))
    x = 100
    while x < 1820:
        w, h = rnd.randint(70, 150), rnd.randint(140, 380)
        col = rnd.choice(("#a9b6c8", "#9aa8bd", "#b8c3d3"))
        o.append(rect(x, 640 - h, w, h, col, 0, 2.5, "#6b7890"))
        for wy in range(640 - h + 14, 630, 26):
            o.append(stroke([(x + 10, wy), (x + w - 10, wy)], 3, "#d9e3ee"))
        x += w + rnd.randint(4, 20)
    o.append(f'<path d="M1500,640 C1520,560 1560,520 1600,520 C1650,520 1680,580 1690,640 Z" fill="#7aa86a" stroke="{INK}" stroke-width="3"/>')
    for gx in range(80, 1841, 440):
        o.append(stroke([(gx, 80), (gx, 640)], 8, "#c7ccd4"))
    o.append(stroke([(80, 80), (1840, 80)], 6) + stroke([(80, 640), (1840, 640)], 6))
    # floor
    o.append(f'<rect y="640" width="{W}" height="440" fill="#d9d4c9"/>' + stroke([(0, 640), (W, 640)], 4))
    for i in range(9):
        o.append(stroke([(i * 260 - 300, 1080), (960 + (i - 4) * 80, 640)], 2, "#c4beb1"))
    # company sign on the wall
    o.append(rect(760, 26, 400, 46, "#ffffff", 10, 3) + f'<text x="960" y="60" text-anchor="middle" font-family="Patrick Hand" font-size="34" fill="{INK}">TECH CO. ✦ CAMPUS</text>')
    # desks with monitors + people
    def desk(x, y):
        return rect(x - 200, y - 20, 400, 24, "#f4f4f4", 6, 4) + stroke([(x - 180, y + 4), (x - 180, y + 160)], 6) + stroke([(x + 180, y + 4), (x + 180, y + 160)], 6)
    chart = lambda x, y: stroke([(x - 60, y - 30), (x - 30, y - 55), (x, y - 40), (x + 30, y - 80), (x + 60, y - 70)], 4, "#2e9d5b")
    feed = lambda x, y: "".join(rect(x - 60, y - 98 + i * 26, 120, 18, ("#ffd1dc", "#cde6ff", "#e8f5d0")[i], 3, 0) for i in range(3))
    o.append(desk(480, 860) + monitor(440, 840, 1.0, "#e9f2ff", chart(440, 790)) + monitor(600, 840, 0.8, "#fff4f4", feed(600, 890)))
    o.append(guy(330, 1020, 0.9, "side", "focused", dict(dy=60, lh=90, lk=-90, rh=86, rk=-86, ra=70, rb=-30, la=64, lb=-26, behind=chair(-10, -76)), 3))
    o.append(desk(1360, 860) + monitor(1360, 840, 1.1, "#e9f2ff", feed(1360, 880)))
    o.append(guy(1180, 1020, 0.9, "side", "happy", dict(dy=60, lh=90, lk=-90, rh=86, rk=-86, ra=70, rb=-30, la=64, lb=-26, behind=chair(-10, -76)), 4))
    # standing designer with a whiteboard: "variable rewards"
    o.append(stroke([(930, 560), (910, 700)], 6) + stroke([(1170, 560), (1190, 700)], 6))
    o.append(rect(900, 360, 300, 200, "#ffffff", 6, 5) + stroke([(940, 520), (980, 470), (1020, 500), (1060, 420), (1100, 440), (1160, 390)], 5, "#d64545"))
    o.append(f'<text x="1050" y="400" text-anchor="middle" font-family="Patrick Hand" font-size="30" fill="{INK}">ENGAGEMENT ↑</text>')
    o.append(guy(860, 1000, 0.85, "three", "happy", dict(ra=150, rb=-10, la=-10), 5))
    o.append(plant(1760, 1000, 1.4) + plant(90, 1000, 1.2))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(o)}</svg>'


# ------------------------------------------------------------------ Las Vegas casino
def slot_machine(x, y, s=1.0, seed=0, pulled_to=None):
    rnd = random.Random(seed)
    def k(v):
        return v * s
    body = (f'<path d="M{x - k(90)},{y} L{x - k(90)},{y - k(300)} C{x - k(90)},{y - k(360)} {x + k(90)},{y - k(360)} {x + k(90)},{y - k(300)} L{x + k(90)},{y} Z" fill="#c8323a" stroke="{INK}" stroke-width="4"/>'
            + rect(x - k(70), y - k(260), k(140), k(90), "#fff8e6", k(6), 3.5)
            + "".join(f'<text x="{x + k(dx)}" y="{y - k(200)}" text-anchor="middle" font-family="Patrick Hand" font-size="{k(46):.0f}" fill="{c}">{t}</text>'
                      for dx, t, c in zip((-45, 0, 45), rnd.sample(["7", "7", "7", "$", "?"], 3), ("#c8323a", "#2e6bd6", "#c8323a")))
            + rect(x - k(80), y - k(150), k(160), k(26), "#f3c242", k(4), 3)
            + rect(x - k(60), y - k(80), k(120), k(40), "#2b2b33", k(4), 3)
            + rect(x - k(70), y - k(330), k(140), k(34), "#f3c242", k(10), 3)
            + f'<text x="{x}" y="{y - k(304)}" text-anchor="middle" font-family="Patrick Hand" font-size="{k(26):.0f}" fill="{INK}">JACKPOT</text>')
    if pulled_to:      # lever pulled down by a hand
        hx, hy = pulled_to
        lever = stroke([(x + k(90), y - k(180)), (hx, hy)], k(8)) + f'<circle cx="{hx}" cy="{hy}" r="{k(15)}" fill="#e23b3b" stroke="{INK}" stroke-width="3"/>'
    else:
        lever = stroke([(x + k(90), y - k(180)), (x + k(130), y - k(200)), (x + k(130), y - k(300))], k(8)) + \
            f'<circle cx="{x + k(130)}" cy="{y - k(306)}" r="{k(15)}" fill="#e23b3b" stroke="{INK}" stroke-width="3"/>'
    lights = "".join(f'<circle cx="{x + k(dx)}" cy="{y - k(345)}" r="{k(6)}" fill="#ffe27a" stroke="{INK}" stroke-width="1.5"/>' for dx in range(-60, 61, 30))
    return body + lever + lights


def casino():
    rnd = random.Random(8)
    o = ['<linearGradient id="cw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a1240"/><stop offset="1" stop-color="#5a1e48"/></linearGradient>',
         '<radialGradient id="spot"><stop offset="0" stop-color="#ffd76a" stop-opacity="0.45"/><stop offset="1" stop-color="#ffd76a" stop-opacity="0"/></radialGradient>',
         f'<rect width="{W}" height="{H}" fill="url(#cw)"/>']
    # neon sign
    o.append(rect(560, 60, 800, 150, "#22082a", 20, 5))
    o.append('<text x="960" y="170" text-anchor="middle" font-family="Patrick Hand" font-size="110" fill="#ff5fa8" stroke="#ffd1e8" stroke-width="2">CASINO</text>')
    o += [f'<circle cx="{x}" cy="{y}" r="7" fill="#ffe27a" stroke="{INK}" stroke-width="1.5"/>' for x in range(580, 1350, 40) for y in (78, 192)]
    # chandeliers
    for cx in (260, 1660):
        o.append(stroke([(cx, 0), (cx, 90)], 3) + f'<path d="M{cx - 80},90 L{cx + 80},90 L{cx + 40},150 L{cx - 40},150 Z" fill="#f3c242" stroke="{INK}" stroke-width="3"/>')
        o.append(f'<ellipse cx="{cx}" cy="200" rx="200" ry="120" fill="url(#spot)"/>')
    # carpet floor with pattern
    o.append(f'<rect y="700" width="{W}" height="380" fill="#7a1a2a"/>' + stroke([(0, 700), (W, 700)], 4))
    for i in range(30):
        x, y = rnd.uniform(0, W), rnd.uniform(720, 1060)
        o.append(f'<path d="M{x:.0f},{y:.0f} l12,-12 l12,12 l-12,12 Z" fill="#c8a03a" opacity="0.6"/>')
    # row of slot machines
    for i, x in enumerate((180, 420, 1500, 1740)):
        o.append(slot_machine(x, 760, 1.05, i))
    # the guy pulling the lever, tired at 3 AM
    o.append(guy(1440, 1000, 0.95, "side", "bored", dict(ra=100, rb=0, la=10, lb=-10), 6, flip=True))
    o.append(slot_machine(1180, 820, 1.35, 9, pulled_to=(1322, 790)))
    o.append(rect(1290, 300, 150, 60, "#111", 8, 3) + '<text x="1365" y="345" text-anchor="middle" font-family="Patrick Hand" font-size="40" fill="#ff4a4a">3:00 AM</text>')
    # roulette table at the back left
    o.append(f'<ellipse cx="640" cy="760" rx="260" ry="70" fill="#1f7a45" stroke="{INK}" stroke-width="4"/>'
             f'<circle cx="640" cy="745" r="44" fill="#2b2b33" stroke="#f3c242" stroke-width="6"/>'
             + "".join(f'<path d="M640,745 L{640 + math.cos(math.radians(a)) * 40:.1f},{745 + math.sin(math.radians(a)) * 40:.1f}" stroke="{c}" stroke-width="6"/>'
                       for a, c in zip(range(0, 360, 30), ("#c8323a", "#111") * 6)))
    o.append(stroke([(420, 800), (420, 1000)], 8) + stroke([(860, 800), (860, 1000)], 8))
    o.append(guy(820, 1000, 0.85, "three", "happy", dict(la=-140, lb=-15, ra=140, rb=15), 7))
    for i in range(6):        # chips
        o.append(f'<ellipse cx="{560 + i * 18}" cy="{740 - i * 5}" rx="16" ry="6" fill="{("#e23b3b", "#2e6bd6", "#f3c242")[i % 3]}" stroke="{INK}" stroke-width="2"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(o)}</svg>'


if __name__ == "__main__":
    render([(bedroom(), os.path.join(HERE, "scene_bedroom.png"), False),
            (office(), os.path.join(HERE, "scene_office.png"), False),
            (casino(), os.path.join(HERE, "scene_casino.png"), False)])
    print("wrote 3 modern scenes")
