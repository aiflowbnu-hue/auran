#!/usr/bin/env python3
"""Build edit.json for the 201 solo, text-free visuals (Dopamine & Slot Machine History, 14:08).

The guide gives every visual a scene, an object name and the scene's voiceover sentence(s), with evenly split guide
times. Timing here:
  1. Scene start = where the scene's sentence is actually spoken (fuzzy: the guide text is sometimes condensed).
  2. Visuals whose object name is a spoken word (LootBox -> "loot", SpinningWheel -> "spinning") go on that word,
     TEXT_LEAD early.
  3. Generic visuals (SoloObj1, SoloObj2 ...) split the time left between those anchors evenly, each snapped to the
     nearest natural break (a word that follows a pause), else the nearest word start; SCENE_LEAD early.
Owner's standing rules: no zoom, no transitions, no SFX.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
TEXT_LEAD, SCENE_LEAD = 0.30, 0.08

tr = json.load(open(os.path.join(A, "transcript.json")))
tr = tr[0] if isinstance(tr, list) else tr
words = [w for w in tr["words"] if w["type"] == "word"]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
wn = [norm(w["text"]) for w in words]
pause_before = [words[i]["start"] - words[i - 1]["end"] if i else 9.9 for i in range(len(words))]


def ts(s):
    m, sec = s.split(":")
    return int(m) * 60 + float(sec)


rows = []
for ln in open(os.path.join(A, "00_SOLO_VISUALS_TIMELINE_GUIDE.md"), encoding="utf-8"):
    m = re.match(r"\|\s*\*\*(\d+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*`([\d:.]+)\s*-\s*([\d:.]+)`\s*\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|\s*$", ln)
    if m:
        rows.append({"n": int(m.group(1)), "img": m.group(2), "approx": ts(m.group(3)), "obj": m.group(5),
                     "ctx": m.group(6), "scene": int(re.search(r"Scene(\d+)", m.group(2)).group(1))})
assert len(rows) == 201, len(rows)
assert all(os.path.exists(os.path.join(A, "frames", r["img"])) for r in rows)

STOP = {"a", "an", "the", "in", "of", "is", "to", "and", "it", "on", "at", "your", "you", "for", "by", "are", "was",
        "that", "this", "what", "so", "but", "with", "had", "has", "be", "they", "their", "them", "he", "his", "its",
        "if", "or", "as", "do", "did", "just", "then", "when", "there", "were", "we", "i", "not", "no", "one"}
NUM = {"2006": "two thousand and six", "2008": "two thousand and eight", "10": "ten", "30": "thirty", "50": "fifty",
       "100": "hundred", "1990s": "nineties", "40,000": "forty thousand", "2": "two"}


def content(text):
    for k, v in NUM.items():
        text = re.sub(rf"(?<![\d,]){re.escape(k)}(?![\d,])", v, text)
    return list(dict.fromkeys(t for t in (norm(x) for x in text.split()) if t and t not in STOP and len(t) > 2))


def hit(tok, w):
    return w == tok or (len(tok) > 4 and w.startswith(tok[:5]))


def find_scene_start(ctx, approx, lo):
    toks = content(ctx)[:10]
    best = None
    for i in range(lo, len(words)):
        if words[i]["start"] < approx - 25:
            continue
        if words[i]["start"] > approx + 25:
            break
        if not any(hit(t, wn[i]) for t in toks[:4]) and pause_before[i] < 0.25:
            continue                    # a scene starts on one of its first words or after a pause
        win = wn[i:i + 14]
        n = len({t for t in toks if any(hit(t, w) for w in win)})
        key = (n, -abs(words[i]["start"] - approx))
        if best is None or key > best[0]:
            best = (key, i)
    return best[1] if best and best[0][0] >= 2 else None


# 1. scene starts
scenes = []
for r in rows:
    if not scenes or scenes[-1]["id"] != r["scene"]:
        scenes.append({"id": r["scene"], "rows": [], "ctx": r["ctx"], "approx": r["approx"]})
    scenes[-1]["rows"].append(r)
lo, drift = 0, 0.0
for sc in scenes:
    i = find_scene_start(sc["ctx"], sc["approx"] + drift, lo)
    if i is not None:
        sc["i"], sc["t"], sc["matched"] = i, words[i]["start"], True
        drift, lo = sc["t"] - sc["approx"], i + 1
    else:
        sc["t"], sc["matched"] = sc["approx"] + drift, False
        sc["i"] = min(range(len(words)), key=lambda k: abs(words[k]["start"] - sc["t"]))
scenes[0]["t"], scenes[0]["i"] = 0.0, 0
for a, b in zip(scenes, scenes[1:]):
    assert b["t"] > a["t"], (a["id"], b["id"], a["t"], b["t"])
end_t = words[-1]["end"]


def snap(t, lo_t, hi_t):
    """Nearest word start to t inside (lo_t, hi_t), preferring one that follows a pause."""
    cands = [k for k, w in enumerate(words) if lo_t < w["start"] < hi_t]
    if not cands:
        return t
    near = [k for k in cands if abs(words[k]["start"] - t) < 0.9 and pause_before[k] >= 0.18]
    k = min(near or cands, key=lambda k: abs(words[k]["start"] - t))
    return words[k]["start"]


# 2 + 3. visuals inside each scene
for si, sc in enumerate(scenes):
    t0 = sc["t"]
    t1 = scenes[si + 1]["t"] if si + 1 < len(scenes) else end_t
    rs = sc["rows"]
    rs[0]["t"], rs[0]["how"] = t0, "scene start"
    # named objects on their word
    cur = t0
    for r in rs[1:]:
        name = r["obj"].split("_")[-1]          # "LockedPhone_2_SpinningWheel" -> "SpinningWheel"
        toks = [norm(x) for x in re.findall(r"[A-Z][a-z]+|\d+", name)]
        toks = [t for t in toks if t and t not in STOP and not t.startswith("solo") and t != "obj" and len(t) > 2]
        r["t"] = None
        # the spot in this scene where most of the name is said together ("chemical of MAYBE", not the
        # earlier "chemical of pleasure"); ties go to the earliest
        best = None
        for k, w in enumerate(words):
            if not (cur + 0.12 < w["start"] < t1 - 0.2) or not any(hit(t, wn[k]) for t in toks):
                continue
            score = len({t for t in toks if any(hit(t, x) for x in wn[k:k + 4])})
            if best is None or score > best[0]:
                best = (score, k)
        if best:
            w = words[best[1]]
            r["t"], r["how"], cur = w["start"], f"on '{w['text']}'", w["start"]
    # generic ones: evenly between anchors, snapped to natural breaks
    k = 0
    while k < len(rs):
        if rs[k]["t"] is not None:
            k += 1
            continue
        j = k
        while j < len(rs) and rs[j]["t"] is None:
            j += 1
        a = rs[k - 1]["t"]
        b = rs[j]["t"] if j < len(rs) else t1
        n = j - k + 1
        for m in range(k, j):
            ideal = a + (b - a) * (m - k + 1) / n
            rs[m]["t"] = snap(ideal, rs[m - 1]["t"] + 0.6, b - 0.6) if b - a > 1.5 else ideal
            rs[m]["how"] = "split"
        k = j

# leads, order, minimum hold
flat = [r for sc in scenes for r in sc["rows"]]
for r in flat[1:]:
    r["t"] -= TEXT_LEAD if r["how"].startswith("on ") else SCENE_LEAD
prev = -1.0
for r in flat:
    r["t"] = max(r["t"], prev + 0.4)
    prev = r["t"]
flat[0]["t"] = 0.0

cuts = [{"img": r["img"], "start": round(r["t"], 3), "fx": [], "sfx": []} for r in flat]
json.dump({"fps": 30, "size": [1920, 1080], "voiceover": "assets/voiceover.mp3", "music": "assets/music.mp3",
           "music_volume": 0.16, "tail": 1.5, "cuts": cuts}, open(os.path.join(HERE, "edit.json"), "w"), indent=1)
ms = sum(sc["matched"] for sc in scenes)
print(f"{len(flat)} visuals, {len(scenes)} scenes ({ms} scene starts found in the speech, {len(scenes) - ms} from guide time)")
for sc in scenes:
    print(f"scene {sc['id']:02d} @ {sc['t']:7.2f} {'ok' if sc['matched'] else '--'}  {sc['ctx'][:60]}")
    for r in sc["rows"]:
        print(f"    #{r['n']:03d} {r['t']:7.2f} {r['how']:22} {r['obj']}")
