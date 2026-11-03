#!/usr/bin/env python3
"""Timing for the 360 clause-by-clause visuals: each visual goes on the spoken start of its clause.

Clauses are found in order in the word-level transcript (allowing small wording differences). Visuals that repeat
the same clause (e.g. three frames on "ever ends.") share that clause's time evenly. Writes timeline.json with, per
visual: image, start (seconds, before lead), clause text, scene. Text layers are added by compose.py.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")

tr = json.load(open(os.path.join(A, "transcript.json")))
tr = tr[0] if isinstance(tr, list) else tr
words = [w for w in tr["words"] if w["type"] == "word"]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
wn = [norm(w["text"]) for w in words]
NUM = {"40,000": "forty thousand", "2006": "two thousand and six", "2008": "two thousand and eight",
       "1990s": "nineties", "2:00": "two", "%": " percent"}


def ts(s):
    m, sec = s.split(":")
    return int(m) * 60 + float(sec)


rows = []
for ln in open(os.path.join(A, "00_CLAUSE_BY_CLAUSE_TIMELINE_GUIDE.md"), encoding="utf-8"):
    m = re.match(r"\|\s*\*\*(\d+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*`([\d:.]+)\s*-\s*([\d:.]+)`\s*\|\s*\*?\"?(.*?)\"?\*?\s*\|\s*`([^`]*)`", ln)
    if m:
        rows.append({"n": int(m.group(1)), "img": m.group(2), "approx": ts(m.group(3)), "clause": m.group(5).strip(),
                     "action": m.group(6), "scene": int(re.search(r"Scene(\d+)", m.group(2)).group(1))})
assert len(rows) == 360, len(rows)
assert all(os.path.exists(os.path.join(A, "frames", r["img"])) for r in rows)


def toks(text):
    text = text.replace("...", " ").replace("—", " ")
    for k, v in NUM.items():
        text = text.replace(k, v)
    out = []
    for t in text.split():
        n = norm(t)
        if n:
            out.append(n)
    return out


def hit(t, w):
    return w == t or (len(t) > 3 and (w.startswith(t[:4]) or t.startswith(w[:4]) and len(w) > 3))


def align(cl, lo, approx):
    """Best start index for clause tokens cl at/after lo: in-order matches within a short window."""
    best = None
    for i in range(lo, min(len(words), lo + 60)):
        if words[i]["start"] > approx + 30:
            break
        j, score, first = i, 0, None
        for t in cl:
            for jj in range(j, min(j + 3, len(wn))):
                if hit(t, wn[jj]):
                    score += 1; first = jj if first is None else first; j = jj + 1
                    break
        if first is None:
            continue
        need = 1 if len(cl) <= 2 else max(2, int(0.5 * len(cl) + 0.5))
        if score >= need:
            key = (score / len(cl), -(first - lo))
            if best is None or key > best[0]:
                best = (key, first, j)
    return (best[1], best[2]) if best else (None, None)


# Global alignment of all guide clause tokens against the spoken words (like a text diff): robust to clauses that
# were reworded, added or dropped after the guide was written, and it can never cross over or reorder.
from difflib import SequenceMatcher
g_tok, g_owner = [], []
for k, r in enumerate(rows):
    if k and r["clause"] == rows[k - 1]["clause"]:
        r["dup"] = True                       # same clause repeated on the next visual: shares its time later
        continue
    for t in toks(r["clause"]):
        g_tok.append(t); g_owner.append(k)
sm = SequenceMatcher(None, g_tok, wn, autojunk=False)
g2w = {}
for a, b, size in sm.get_matching_blocks():
    for d in range(size):
        g2w[a + d] = b + d
first_match = {}
for gi, k in enumerate(g_owner):
    if gi in g2w and k not in first_match:
        first_match[k] = g2w[gi]
misses = []
for k, r in enumerate(rows):
    if k in first_match:
        r["t"], r["word"] = words[first_match[k]]["start"], words[first_match[k]]["text"]
    else:
        r["t"] = None
        if not r.get("dup"):
            misses.append(r["n"])

# visuals without their own spoken anchor: spread between the neighbouring anchors, weighted by the guide's own
# durations so a long guide clause keeps a long share
known = [k for k, r in enumerate(rows) if r.get("t") is not None]
for k, r in enumerate(rows):
    if r.get("t") is not None:
        continue
    a = max([x for x in known if x < k], default=None)
    b = min([x for x in known if x > k], default=None)
    ta = rows[a]["t"] if a is not None else 0.0
    tb = rows[b]["t"] if b is not None else words[-1]["end"]
    ga = rows[a]["approx"] if a is not None else 0.0
    gb = rows[b]["approx"] if b is not None else rows[-1]["approx"] + 2.0
    frac = (r["approx"] - ga) / (gb - ga) if gb > ga else 0.5
    r["t"] = ta + (tb - ta) * min(max(frac, 0.05), 0.95)
rows[0]["t"] = 0.0

# snap every guessed time to the nearest spoken word start (captions then always break between words)
starts = [w["start"] for w in words]
for r in rows:
    if r.get("word") is None:
        k = min(range(len(words)), key=lambda i: abs(starts[i] - r["t"]))
        r["t"] = starts[k] if r["n"] > 1 else 0.0

# hand-checked fixes (timing.txt): a visual goes on the first word of its phrase, "-" drops it
orig = {r["n"]: r["t"] for r in rows}
fixes = []
for ln in open(os.path.join(HERE, "timing.txt"), encoding="utf-8"):
    if ln.strip() and not ln.startswith("#"):
        n, phrase = ln.strip().split(" ", 1)
        fixes.append((int(n), phrase))
drop = set()
for n, phrase in fixes:
    if phrase == "-":
        drop.add(n); continue
    ph = [norm(x) for x in phrase.split()]
    occ = [i for i in range(len(words)) if wn[i:i + len(ph)] == ph and abs(words[i]["start"] - orig[n]) < 20]
    hit = min(occ, key=lambda i: abs(words[i]["start"] - orig[n])) if occ else None   # nearest to its guide slot
    if hit is None:
        raise SystemExit(f"timing.txt: phrase not found for #{n}: {phrase}")
    r = next(r for r in rows if r["n"] == n)
    r["t"], r["fixed"] = words[hit]["start"], True
    if abs(r["t"] - orig[n]) > 12:
        print(f"  check #{n}: moved {orig[n]:.1f}s -> {r['t']:.1f}s ({phrase})")
rows = sorted((r for r in rows if r["n"] not in drop), key=lambda r: r["t"])
print(f"timing.txt: {len(fixes) - len(drop)} visuals moved, {len(drop)} dropped")

# minimum hold: a run of frames closer than MIN_HOLD is spread evenly over a wider window (growing it into the
# neighbouring long holds until there is room), then snapped to word starts again
MIN_HOLD = 0.6
t = [r["t"] for r in rows] + [words[-1]["end"] + 0.5]
n = len(rows)
while True:
    bad = [k for k in range(n) if t[k + 1] - t[k] < MIN_HOLD - 1e-6]
    if not bad:
        break
    a, b = bad[0], bad[0] + 1
    ok = lambda: (t[b] - t[a]) / (b - a) >= MIN_HOLD * 1.15
    while not ok() and (a > 0 or b < n):
        if b < n:
            b += 1
        if not ok() and a > 0:
            a -= 1
    for k in range(a + 1, b):
        ideal = t[a] + (t[b] - t[a]) * (k - a) / (b - a)
        near = [x for x in starts if t[k - 1] + MIN_HOLD <= x <= t[b] - MIN_HOLD * (b - k) and abs(x - ideal) < 0.5]
        t[k] = min(near, key=lambda x: abs(x - ideal)) if near else max(ideal, t[k - 1] + MIN_HOLD)
for r, x in zip(rows, t):
    r["t"] = x
ts_ = [r["t"] for r in rows]
assert all(b >= a for a, b in zip(ts_, ts_[1:])), "not increasing"
gaps = [b - a for a, b in zip(ts_, ts_[1:])]
big = max(range(len(gaps)), key=lambda k: gaps[k])
print("longest hold", rows[big]["n"], rows[big]["t"], rows[big]["clause"])
print(f"holds: min {min(gaps):.2f}s, under {MIN_HOLD}s: {sum(g < MIN_HOLD - 1e-6 for g in gaps)}, max {max(gaps):.2f}s")

json.dump([{k: r[k] for k in ("n", "img", "t", "clause", "scene", "action")} for r in rows],
          open(os.path.join(HERE, "timeline.json"), "w"), indent=1)
print(f"{len(rows)} visuals; clause not found in speech: {misses}")
for r in rows[:12]:
    print(f"#{r['n']:03d} {r['t']:7.2f} {r.get('word', '(shared)'):14} {r['clause']}")
