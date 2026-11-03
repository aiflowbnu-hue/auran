#!/usr/bin/env python3
"""Compose the final frames: clean visual + my own text layer (spoken words as a bold caption, key word marked
with a yellow highlighter stroke). Static frames only - no zoom, no animation, no transitions.

Caption text comes from the word-level transcript (what is actually said), not from the guide, so it always
matches the voice. A visual's words are split into short chunks; each chunk is its own hard cut that appears
LEAD seconds before its first word.

    python3 compose.py [START END]   -> build/composed/*.png + edit.json (optionally only the START..END seconds)
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "build", "composed")
os.makedirs(OUT, exist_ok=True)
W, H, LEAD, MIN_HOLD = 1920, 1080, 0.30, 0.6
SCALE, TOP = 1.25, -40            # base 1376x768 -> 1720x960, content (y 79..650) lands at 59..773
CAP_Y, CAP_SIZE, CAP_W = 930, 72, 1640
INK, MARK = (29, 29, 31), (255, 214, 10)
MAX_WORDS, MAX_SECS = 7, 3.0
STOP = set("a an the in of is to and it on at your you for by are was that this what so but with had has be they "
           "their them he his its if or as do did just then when there were we i not no one from into than more "
           "every all can could would will about out up down over".split())

tl = json.load(open(os.path.join(HERE, "timeline.json")))
tr = json.load(open(os.path.join(A, "transcript.json")))
tr = tr[0] if isinstance(tr, list) else tr
words = [w for w in tr["words"] if w["type"] == "word"]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
END = words[-1]["end"] + 0.5


def font(size):
    f = ImageFont.truetype(os.path.join(A, "fonts", "Fredoka.ttf"), size)
    f.set_variation_by_axes([700, 100])
    return f


FONT = font(CAP_SIZE)


def chunks(ws):
    """Split a visual's words into caption chunks: at most MAX_WORDS words / MAX_SECS, preferring punctuation."""
    out, cur = [], []
    P = lambda w: re.search(r"[.,;:!?—]$", w["text"])
    for i, w in enumerate(ws):
        cur.append(w)
        long_ = len(cur) >= MAX_WORDS or cur[-1]["end"] - cur[0]["start"] >= MAX_SECS
        soon = any(P(x) for x in ws[i + 1:i + 3]) and len(cur) < MAX_WORDS + 2   # sentence ends in 1-2 words
        if (long_ and not soon and not (i + 1 < len(ws) and ws[i + 1]["text"][0].isupper() is False and len(cur) < MAX_WORDS)) or (P(w) and len(cur) >= 3):
            out.append(cur); cur = []
    if cur:
        if out and len(cur) <= 2 and len(out[-1]) + len(cur) <= MAX_WORDS + 2:
            out[-1] += cur
        else:
            out.append(cur)
    return out


def keyword(ws, action):
    """Index of the word to mark: a word named in the visual's action (SpinningWheel -> spinning), else the
    longest content word."""
    names = [norm(x) for x in re.findall(r"[A-Z][a-z]+|\d+", action)]
    names = [x for x in names if len(x) > 3 and x not in STOP and not x.startswith("solo") and x not in ("obj", "clause", "check", "loop")]
    hits = [(len(norm(w["text"])), i) for i, w in enumerate(ws)
            if any(norm(w["text"]) == x or (len(norm(w["text"])) > 3 and norm(w["text"])[:4] == x[:4]) for x in names)
            and norm(w["text"]) not in STOP]
    if hits:
        return max(hits)[1]
    cand = [(len(norm(w["text"])), i) for i, w in enumerate(ws) if norm(w["text"]) not in STOP]
    return max(cand)[1] if cand and max(cand)[0] >= 4 else None


def layout(tokens):
    """Wrap upper-case tokens into lines that fit CAP_W."""
    lines, cur = [], []
    for t in tokens:
        test = " ".join(cur + [t])
        if cur and FONT.getlength(test) > CAP_W:
            lines.append(cur); cur = [t]
        else:
            cur.append(t)
    lines.append(cur)
    if len(lines) == 2:                            # balance two lines (no lonely last word)
        allt = lines[0] + lines[1]
        lines = min(([allt[:k], allt[k:]] for k in range(1, len(allt))
                     if FONT.getlength(" ".join(allt[:k])) <= CAP_W),
                    key=lambda L: max(FONT.getlength(" ".join(x)) for x in L))
    return lines


def caption(img, ws, key):
    d = ImageDraw.Draw(img)
    tokens = [w["text"].upper() for w in ws]
    lines = layout(tokens)
    lh = int(CAP_SIZE * 1.22)
    y0 = CAP_Y - (len(lines) * lh) // 2
    k = 0
    for li, line in enumerate(lines):
        text = " ".join(line)
        x = (W - FONT.getlength(text)) / 2
        y = y0 + li * lh
        for t in line:
            if k == key:                          # highlighter stroke behind the key word, slightly tilted
                core = re.sub(r"[^\w']+$", "", t)
                wl = FONT.getlength(core)
                top, bot = y + CAP_SIZE * 0.24, y + CAP_SIZE * 1.04
                d.polygon([(x - 12, top + 4), (x + wl + 12, top - 1), (x + wl + 9, bot - 3), (x - 14, bot + 1)], fill=MARK)
            k += 1
            x += FONT.getlength(t + " ")
        d.text(((W - FONT.getlength(text)) / 2, y), text, font=FONT, fill=INK)


lo_t, hi_t = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (0, END)
bases = {}
cuts = []
times = [v["t"] for v in tl] + [END]
for i, v in enumerate(tl):
    t0, t1 = times[i], times[i + 1]
    if t1 <= lo_t or t0 >= hi_t:
        continue
    ws = [w for w in words if t0 - 0.02 <= w["start"] < t1 - 0.02]
    if v["img"] not in bases:
        src = Image.open(os.path.join(A, "frames", v["img"])).convert("RGB")
        src = src.resize((round(src.width * SCALE), round(src.height * SCALE)), Image.LANCZOS)
        base = Image.new("RGB", (W, H), "white")
        base.paste(src, ((W - src.width) // 2, TOP))
        bases[v["img"]] = base
    parts = chunks(ws) if ws else [[]]
    merged = [parts[0]]
    for part in parts[1:]:                         # a chunk too soon after the previous one joins it
        if part[0]["start"] - (merged[-1][0]["start"] if merged[-1] else t0) < MIN_HOLD or len(merged) == 1 and part[0]["start"] - t0 < MIN_HOLD:
            merged[-1] = merged[-1] + part
        else:
            merged.append(part)
    if len(merged) > 1 and t1 - merged[-1][0]["start"] < MIN_HOLD:
        merged[-2:] = [merged[-2] + merged[-1]]
    for j, part in enumerate(merged):
        start = t0 if j == 0 else part[0]["start"]
        img = bases[v["img"]].copy()
        if part:
            caption(img, part, keyword(part, v["action"]))
        name = f"{v['n']:03d}_{j}.png"
        img.save(os.path.join(OUT, name))
        cuts.append({"img": os.path.join("build", "composed", name), "start": round(max(start - LEAD, 0), 3),
                     "n": v["n"], "text": " ".join(w["text"] for w in part), "fx": [], "sfx": []})
if lo_t == 0:
    cuts[0]["start"] = 0.0
json.dump({"fps": 30, "size": [W, H], "voiceover": "assets/voiceover.mp3", "music": "assets/music.mp3",
           "music_volume": 0.16, "tail": 1.5, "range": [lo_t, hi_t], "cuts": cuts},
          open(os.path.join(HERE, "edit.json"), "w"), indent=1)
print(f"{len(cuts)} cuts from {len(tl)} visuals")
