#!/usr/bin/env python3
"""Build edit.json for the 95 word-by-word visuals.

Every image illustrates one spoken phrase (guide column "Voiceover Word / Phrase"). Each image is put on the
spoken start of its phrase (word timings in assets/transcript.json) and shown TEXT_LEAD seconds early so the
visual never trails the voice. Phrases in brackets are not spoken: those images go in the gap between their
neighbours. Images are ordered by when their phrase is spoken (the guide lists #95 after #94, but its phrase
is said first). Owner's standing rule: no zoom, no transitions, no SFX.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
TEXT_LEAD = 0.30

tr = json.load(open(os.path.join(A, "transcript.json")))
tr = tr[0] if isinstance(tr, list) else tr
words = [w for w in tr["words"] if w["type"] == "word"]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
wn = [norm(w["text"]) for w in words]


def ts(s):
    m, sec = s.split(":")
    return int(m) * 60 + float(sec)


rows = []
for ln in open(os.path.join(A, "00_WORD_BY_WORD_TIMELINE_GUIDE.md"), encoding="utf-8"):
    m = re.match(r"\|\s*(\d+)\s*\|\s*`([\d:.]+)`\s*\|\s*`([\d:.]+)`\s*\|\s*`([^`]+)`\s*\|\s*\"?(.*?)\"?\s*\|", ln)
    if m:
        rows.append({"n": int(m.group(1)), "approx": ts(m.group(2)), "img": m.group(4), "cue": m.group(5)})
assert len(rows) == 95, len(rows)
assert all(os.path.exists(os.path.join(A, "frames", r["img"])) for r in rows)


def variants(cue):
    base = cue.replace("...", " ").replace("40,000", "forty thousand").replace("2:00", "two")
    alts = {base, re.sub(r"\b([Yy]ou) are\b", r"\1're", base), re.sub(r"\b([Yy]ou)'re\b", r"\1 are", base)}
    return [[norm(t) for t in v.split() if norm(t)][:4] for v in alts]


def find(cue, approx):
    """Word index where the phrase starts. The guide wording can differ a little from the speech (e.g. "and you
    are completely safe" vs spoken "you're completely safe"), so count cue words found in order within the next
    few spoken words; the image goes on the first matched word. Ties: closest to the guide time."""
    best = None
    for toks in variants(cue):
        toks = toks[:5]
        need = 1 if len(toks) == 1 else 2
        for i, w in enumerate(words):
            if abs(w["start"] - approx) > 7:
                continue
            j, score, first = i, 0, None
            for t in toks:
                for jj in range(j, min(j + 3, len(wn))):
                    if wn[jj] == t or (len(t) > 4 and wn[jj].startswith(t[:5])):
                        score += 1; first = jj if first is None else first; j = jj + 1
                        break
            if score >= need and first == i:
                key = (score, -abs(w["start"] - approx))
                if best is None or key > best[0]:
                    best = (key, i)
    return best[1] if best else None


drift = 0.0
for r in rows:
    if r["cue"].startswith("("):
        r["t"], r["word"] = None, None
        continue
    i = find(r["cue"], r["approx"] + drift)
    if i is None:
        raise SystemExit(f"phrase not found: #{r['n']} {r['cue']}")
    r["word_t"], r["word"] = words[i]["start"], words[i]["text"]
    r["t"] = r["word_t"] - TEXT_LEAD
    drift = r["word_t"] - r["approx"]

# unspoken (bracketed) visuals: right after the previous phrase finishes, in the pause before the next one
for k, r in enumerate(rows):
    if r["t"] is None:
        prev = rows[k - 1]
        nxt = next(x for x in rows[k + 1:] if x["t"] is not None)
        pend = max(w["end"] for w in words if prev["word_t"] <= w["start"] < nxt["word_t"] - 0.05) if prev.get("word_t") else prev["t"]
        r["t"] = min(max(pend - 0.1, prev["t"] + 0.4), nxt["t"] - 0.35)

rows.sort(key=lambda r: r["t"])
rows[0]["t"] = 0.0
for a, b in zip(rows, rows[1:]):
    assert b["t"] - a["t"] >= 0.15, (a["n"], b["n"], a["t"], b["t"])

cuts = [{"img": r["img"], "start": round(r["t"], 3), "fx": [], "sfx": []} for r in rows]
json.dump({"fps": 30, "size": [1920, 1080], "voiceover": "assets/voiceover.mp3", "music": "assets/music.mp3",
           "music_volume": 0.16, "tail": 1.5, "cuts": cuts}, open(os.path.join(HERE, "edit.json"), "w"), indent=1)
print(f"{len(rows)} cuts")
for r in rows:
    on = f"on '{r['word']}' @ {r['word_t']:.2f}" if r.get("word") else "(not spoken: placed in the pause)"
    print(f"#{r['n']:02d} {r['t']:7.2f}  {on:32}  {r['cue'][:46]}")
