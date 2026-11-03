#!/usr/bin/env python3
"""Location samples in the style of the owner's reference (flat colours, thin dark outlines, hand-drawn feel):
a savanna with mountains and animal silhouettes, and a cave at night with a campfire. The characters from gen.py
are placed in them.

    python3 scenes.py   -> scene_savanna.png, scene_cave.png
"""
import math, os, random
from gen import figure, campfire, bone, render, line, P, INK

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
SIL = "#2c2b3a"


def grass_tuft(x, y, s=1.0, color="#b98a2e", seed=0):
    rnd = random.Random(seed)
    return "".join(line([(x + i * 6 * s, y), (x + i * 6 * s + rnd.uniform(-14, 14) * s, y - rnd.uniform(18, 40) * s)], 2.5, color)
                   for i in range(-3, 4))


def acacia(x, y, s=1.0):
    t = (f'<path d="M{x - 10 * s},{y} L{x - 4 * s},{y - 170 * s} L{x - 70 * s},{y - 250 * s} M{x - 4 * s},{y - 170 * s} '
         f'L{x + 60 * s},{y - 245 * s} M{x - 2 * s},{y - 200 * s} L{x + 5 * s},{y - 260 * s}" stroke="{INK}" stroke-width="{16 * s}" fill="none" stroke-linecap="round"/>'
         f'<path d="M{x - 10 * s},{y} L{x - 4 * s},{y - 170 * s} L{x - 70 * s},{y - 250 * s} M{x - 4 * s},{y - 170 * s} '
         f'L{x + 60 * s},{y - 245 * s} M{x - 2 * s},{y - 200 * s} L{x + 5 * s},{y - 260 * s}" stroke="#5b4030" stroke-width="{9 * s}" fill="none" stroke-linecap="round"/>')
    crown = (f'<path d="M{x - 190 * s},{y - 250 * s} Q{x - 120 * s},{y - 330 * s} {x},{y - 320 * s} Q{x + 130 * s},{y - 330 * s} '
             f'{x + 190 * s},{y - 255 * s} Q{x},{y - 230 * s} {x - 190 * s},{y - 250 * s} Z" fill="#4f6b3a" stroke="{INK}" stroke-width="4"/>')
    return t + crown


def giraffe(x, y, s=1.0):
    body = f'<path d="M{x - 26 * s},{y - 52 * s} Q{x},{y - 66 * s} {x + 26 * s},{y - 58 * s} L{x + 24 * s},{y - 44 * s} Q{x},{y - 40 * s} {x - 24 * s},{y - 42 * s} Z" fill="{SIL}"/>'
    legs = "".join(line([(x + dx * s, y - 46 * s), (x + dx * s, y)], 4.5 * s, SIL) for dx in (-20, -12, 14, 22))
    neck = line([(x + 20 * s, y - 56 * s), (x + 40 * s, y - 120 * s)], 9 * s, SIL)
    head = f'<ellipse cx="{x + 48 * s}" cy="{y - 122 * s}" rx="{12 * s}" ry="{6 * s}" fill="{SIL}" transform="rotate(20 {x + 48 * s} {y - 122 * s})"/>'
    return body + legs + neck + head


def elephant(x, y, s=1.0):
    return (f'<ellipse cx="{x}" cy="{y - 26 * s}" rx="{30 * s}" ry="{20 * s}" fill="{SIL}"/>'
            f'<circle cx="{x + 28 * s}" cy="{y - 34 * s}" r="{13 * s}" fill="{SIL}"/>'
            + "".join(f'<rect x="{x + dx * s}" y="{y - 14 * s}" width="{7 * s}" height="{14 * s}" fill="{SIL}"/>' for dx in (-24, -10, 6, 18))
            + line([(x + 38 * s, y - 32 * s), (x + 42 * s, y - 6 * s)], 5 * s, SIL))


def antelope(x, y, s=1.0):
    return (f'<ellipse cx="{x}" cy="{y - 18 * s}" rx="{16 * s}" ry="{7 * s}" fill="{SIL}"/>'
            + line([(x - 10 * s, y - 14 * s), (x - 12 * s, y)], 3 * s, SIL) + line([(x + 10 * s, y - 14 * s), (x + 12 * s, y)], 3 * s, SIL)
            + line([(x + 14 * s, y - 20 * s), (x + 20 * s, y - 32 * s), (x + 18 * s, y - 42 * s)], 3 * s, SIL))


def savanna():
    rnd = random.Random(1)
    o = [f'<rect width="{W}" height="{H}" fill="#a8d3ef"/>',
         f'']
    mts = [(0, 430), (140, 330), (330, 390), (520, 300), (760, 380), (980, 290), (1220, 370), (1450, 310), (1700, 380), (1920, 340), (1920, 470), (0, 470)]
    o.append(f'<path d="M{" L".join(P(*q) for q in mts)} Z" fill="#8a84b8" stroke="#4d4870" stroke-width="4" stroke-linejoin="round"/>')
    o.append(f'<path d="M0,450 Q480,430 960,445 T1920,440 L1920,1080 L0,1080 Z" fill="#e8b552" stroke="#a7792c" stroke-width="3"/>')
    o.append(f'<path d="M0,700 Q600,660 1100,690 T1920,670 L1920,1080 L0,1080 Z" fill="#dda443"/>')
    for x in (180, 230):
        o.append(giraffe(x, 470, 1.0))
    for i, x in enumerate((1380, 1450, 1525, 1600)):
        o.append(elephant(x, 468, 0.9 - i * 0.04))
    for x in (720, 760, 1010, 1060):
        o.append(antelope(x, 466, 0.9))
    o.append(acacia(110, 1000, 1.25))
    o.append(acacia(1760, 640, 0.8))
    for i in range(40):
        x, y = rnd.uniform(0, W), rnd.uniform(500, 1060)
        o.append(grass_tuft(x, y, 0.6 + (y - 500) / 700, "#b4832a", seed=i))
    tribe = [
        (520, 990, 0.95, "three", "shocked", dict(hair="long", la=40, lb=-80, ra=30, rb=-90)),
        (760, 1000, 1.0, "three", "neutral", dict(la=-38, lb=20, hand_l="spear")),
        (1050, 1010, 1.12, "three", "angry", dict(la=-38, lb=20, ra=95, rb=-8, hand_l="spear", hand_r="point")),
        (1360, 1000, 0.8, "front", "shocked", dict(la=-10, ra=12)),
        (1560, 995, 0.95, "three", "focused", dict(hair="long", la=-10, ra=40, rb=-100)),
    ]
    for x, y, s, view, mood, pose in tribe:
        o.append(f'<ellipse cx="{x + 10}" cy="{y + 4}" rx="{70 * s}" ry="{12 * s}" fill="#c48d33" opacity="0.6"/>')
        o.append(f'<g transform="translate({x},{y}) scale({s * 0.95})">{figure("ancient", view, pose, mood)}</g>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(o)}</svg>'


def cave():
    rnd = random.Random(4)
    o = [f'<rect width="{W}" height="{H}" fill="#1f2340"/>']
    # night sky with stars seen through the cave mouth
    o += [f'<circle cx="{rnd.uniform(500, 1500):.0f}" cy="{rnd.uniform(80, 420):.0f}" r="{rnd.uniform(1.5, 3.5):.1f}" fill="#f6f1d0"/>' for _ in range(40)]
    o.append(f'<circle cx="1380" cy="170" r="46" fill="#f6efc8" stroke="{INK}" stroke-width="3"/>')
    o.append(f'<path d="M0,600 Q500,560 960,590 T1920,580 L1920,1080 L0,1080 Z" fill="#3a3352"/>')
    # cave walls (frame) with rock outline
    wall = ("M0,0 L1920,0 L1920,1080 L1700,1080 Q1760,800 1680,560 Q1600,300 1400,190 Q1150,40 900,70 "
            "Q600,100 420,260 Q240,420 220,700 Q210,900 260,1080 L0,1080 Z")
    o.append(f'<path d="{wall}" fill="#6b5240" stroke="{INK}" stroke-width="6" fill-rule="evenodd"/>')
    for _ in range(18):
        x, y = rnd.choice([(rnd.uniform(20, 220), rnd.uniform(100, 1050)), (rnd.uniform(1720, 1900), rnd.uniform(100, 1050)), (rnd.uniform(300, 1600), rnd.uniform(10, 120))])
        o.append(f'<path d="M{x},{y} q{rnd.uniform(20, 50):.0f},{rnd.uniform(-10, 10):.0f} {rnd.uniform(40, 90):.0f},0" stroke="#4a3727" stroke-width="4" fill="none" stroke-linecap="round"/>')
    o.append(f'<path d="M200,1080 Q960,900 1720,1080 Z" fill="#8a6a4f" stroke="{INK}" stroke-width="4"/>')
    # warm firelight
    o.append('<radialGradient id="glow"><stop offset="0" stop-color="#ffb347" stop-opacity="0.55"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>')
    o.append(f'<ellipse cx="960" cy="930" rx="560" ry="300" fill="url(#glow)"/>')
    o.append(f'<g transform="translate(960,1000) scale(1.5)">{campfire(0, 0)}</g>')
    o.append(f'<g transform="translate(640,1010) scale(1.0)">{figure("ancient", "side", dict(dy=176, lh=130, lk=-112, rh=125, rk=-108, la=60, lb=-25, ra=70, rb=-20), "focused")}</g>')
    o.append(f'<g transform="translate(1290,1010) scale(-1,1)">{figure("ancient", "side", dict(hair="long", dy=176, lh=130, lk=-112, rh=125, rk=-108, la=100, lb=-20, ra=110, rb=-30), "happy")}</g>')
    o.append(bone(1120, 1040, 20, 1.2) + bone(1170, 1050, -30, 1.2))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(o)}</svg>'


if __name__ == "__main__":
    render([(savanna(), os.path.join(HERE, "scene_savanna.png"), False), (cave(), os.path.join(HERE, "scene_cave.png"), False)])
    print("wrote 2 scenes")
