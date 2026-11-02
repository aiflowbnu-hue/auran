#!/usr/bin/env python3
"""Build edit.json for the 116 hard-cut frames.

Each row of the guide gives a cut, an approximate time and a voiceover cue (e.g. "...are locked,").
The cut is snapped to the spoken start of the cue's first words (word timings in assets/transcript.json).
Cues without spoken words (e.g. "(locked checkmark)") keep the guide's time, shifted by the local drift
of the neighbouring matched cuts. Per the owner's standing rule: no zoom, no transitions, no SFX.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")

tr = json.load(open(os.path.join(A, "transcript.json")))
tr = tr[0] if isinstance(tr, list) else tr
words = [w for w in tr["words"] if w["type"] == "word"]


def norm(s):
    s = s.lower().replace("2:00", "two").replace("40,000", "fortythousand").replace("forty thousand", "fortythousand")
    return re.sub(r"[^a-z0-9]", "", s)


wn = [norm(w["text"]) for w in words]

rows = []
for ln in open(os.path.join(A, "00_HARD_CUTS_EXPLANATION_GUIDE.md"), encoding="utf-8"):
    m = re.match(r"\|\s*\*\*(\d+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*`(\d+):(\d+(?:\.\d+)?)\s*-[^`]*`\s*\|\s*\*?(.*?)\*?\s*\|", ln)
    if m:
        rows.append({"n": int(m.group(1)), "img": m.group(2), "approx": int(m.group(3)) * 60 + float(m.group(4)),
                     "cue": m.group(5).strip().strip('"')})
assert len(rows) == 116, len(rows)
files = set(os.listdir(os.path.join(A, "frames")))
for r in rows:  # two filenames in the zip contain a stray space the guide does not have
    if r["img"] not in files:
        alt = [f for f in files if f.replace(" ", "") == r["img"].replace(" ", "")]
        assert alt, r["img"]
        r["img"] = alt[0]


def cue_variants(cue):
    """Token lists to try: the cue as written, and with whole-word "you are" <-> "you're" swapped."""
    if cue.startswith("("):
        return []
    base = cue.replace("...", " ")
    alts = {base, re.sub(r"\b([Yy]ou) are\b", r"\1're", base), re.sub(r"\b([Yy]ou)'re\b", r"\1 are", base)}
    return [[norm(t) for t in v.split() if norm(t)][:3] for v in alts]


def match(toks, approx, lo, hi_time):
    best = None
    for i in range(lo, len(words)):
        if words[i]["start"] > hi_time:
            break
        score = sum(1 for k, t in enumerate(toks) if i + k < len(wn) and (wn[i + k] == t or (len(t) > 3 and wn[i + k].startswith(t[:4]))))
        if score >= min(2, len(toks)) or (len(toks) == 1 and score == 1):
            key = (score, -abs(words[i]["start"] - approx))
            if best is None or key > best[0]:
                best = (key, i)
    return best[1] if best else None


idx, drift = 0, 0.0
for r in rows:
    i = None
    for toks in cue_variants(r["cue"]):
        j = match(toks, r["approx"] + drift, idx, r["approx"] + drift + 4.0)
        if j is not None and (i is None or j < i):
            i = j
    if i is not None:
        r["t"], r["matched"] = words[i]["start"] - 0.05, True
        drift = r["t"] - r["approx"]
        idx = i + 1
    else:
        r["t"], r["matched"] = r["approx"] + drift, False

# the closing header has no spoken cue: show it on the last words ("...on guard.")
last = rows[-1]
if not last["matched"]:
    on = [w for w in words if norm(w["text"]) == "on" and w["start"] > rows[-2]["t"]]
    last["t"] = (on[-1]["start"] - 0.05) if on else words[-1]["start"]

# visuals lead the voice: show each cut a little before its word starts (owner: text felt late)
LEAD = 0.35
for r in rows[1:]:
    r["t"] -= LEAD

# keep strictly increasing, at least 0.15 s per frame
prev = -1.0
for r in rows:
    r["t"] = max(r["t"], prev + 0.15)
    prev = r["t"]
rows[0]["t"] = 0.0

cuts = [{"img": r["img"], "start": round(r["t"], 3), "fx": [], "sfx": []} for r in rows]
edit = {"fps": 30, "size": [1920, 1080], "voiceover": "assets/voiceover.mp3",
        "music": "assets/music.mp3", "music_volume": 0.16, "tail": 1.5, "cuts": cuts}
json.dump(edit, open(os.path.join(HERE, "edit.json"), "w"), indent=1)
miss = [r for r in rows if not r["matched"]]
print(f"{len(rows)} cuts, {len(rows) - len(miss)} matched to words, {len(miss)} placed from guide time")
for r in rows:
    print(f"{r['n']:3d} {r['t']:7.2f} (guide {r['approx']:6.1f}) {'ok ' if r['matched'] else '-- '} {r['cue'][:40]}")
