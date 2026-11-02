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
    s = s.lower().replace("2:00", "two")
    return re.sub(r"[^a-z0-9]", "", s)


wn = [norm(w["text"]) for w in words]

rows = []
for ln in open(os.path.join(A, "00_HARD_CUTS_EXPLANATION_GUIDE.md"), encoding="utf-8"):
    m = re.match(r"\|\s*\*\*(\d+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*`(\d+):(\d+(?:\.\d+)?)\s*-[^`]*`\s*\|\s*\*?(.*?)\*?\s*\|\s*([^|]*)\|", ln)
    if m:
        rows.append({"n": int(m.group(1)), "img": m.group(2), "approx": int(m.group(3)) * 60 + float(m.group(4)),
                     "cue": m.group(5).strip().strip('"'),
                     "overlay": " ".join(re.findall(r"'([^']+)'", m.group(6)))})
assert len(rows) == 185, len(rows)
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
    base = cue.replace("...", " ").replace("40,000", "forty thousand")  # spoken as two words
    alts = {base, re.sub(r"\b([Yy]ou) are\b", r"\1're", base), re.sub(r"\b([Yy]ou)'re\b", r"\1 are", base)}
    return [[norm(t) for t in v.split() if norm(t)][:4] for v in alts]


def match(toks, approx, lo, hi_time):
    best = None
    for i in range(lo, len(words)):
        if words[i]["start"] > hi_time:
            break
        score = sum(1 for k, t in enumerate(toks) if i + k < len(wn) and (wn[i + k] == t or (len(t) > 3 and wn[i + k].startswith(t[:4]))))
        if score >= min(3, len(toks)) or (len(toks) == 1 and score == 1):
            key = (score, -abs(words[i]["start"] - approx))
            if best is None or key > best[0]:
                best = (key, i)
    return best[1] if best else None


FUZZY_STOP = {"a", "an", "the", "in", "of", "is", "to", "and", "it", "on", "at", "your", "you", "for", "by", "are",
              "was", "that", "this", "what", "so", "but", "with", "had", "has", "be", "they", "their", "them", "he",
              "his", "its", "if", "or", "as", "do", "did", "just", "then", "when", "there", "were", "we", "i"}
NUMWORDS = {"2006": "two thousand and six", "2": "two", "30": "thirty", "50": "fifty", "100": "hundred",
            "1990s": "nineties", "2,000,000": "two million"}


def fuzzy(cue, approx, lo):
    """Paraphrased cue (the guide text was not updated with the final script): find where most of the cue's
    distinctive words are spoken close together, near the guide time; return the first matching word there."""
    text = cue.replace("...", " ")
    for k, v in NUMWORDS.items():
        text = re.sub(rf"\b{re.escape(k)}\b", v, text)
    toks = [norm(t) for t in text.split()]
    toks = list(dict.fromkeys(t for t in toks if t and t not in FUZZY_STOP and len(t) > 2))
    if len(toks) < 2:
        return None
    span = max(8, len(text.split()) + 6)
    best = None
    for i in range(lo, len(words)):
        if words[i]["start"] < approx - 15:
            continue
        if words[i]["start"] > approx + 15:
            break
        win = wn[i:i + span]
        hits = {t for t in toks if any(w == t or (len(t) > 4 and w.startswith(t[:5])) for w in win)}
        if not hits or not any(wn[i] == t or (len(t) > 4 and wn[i].startswith(t[:5])) for t in toks):
            continue                                   # the cut starts on a cue word
        key = (len(hits), -abs(words[i]["start"] - approx))
        if best is None or key > best[0]:
            best = (key, i)
    if best and best[0][0] >= max(2, int(0.4 * len(toks) + 0.5)):
        return best[1]
    return None


idx, drift = 0, 0.0
for r in rows:
    i = None
    for toks in cue_variants(r["cue"]):
        j = match(toks, r["approx"] + drift, idx, r["approx"] + drift + 15.0)  # guide times can be far off
        if j is not None and (i is None or j < i):
            i = j
    if i is None and not r["cue"].startswith("("):
        i = fuzzy(r["cue"], r["approx"] + drift, idx)
        if i is not None:
            r["fuzzy"] = True
    if i is not None:
        r["t"], r["matched"] = words[i]["start"] - 0.05, True
        drift = r["t"] - r["approx"]
        idx = i + 1
    else:
        r["t"], r["matched"] = r["approx"] + drift, False

# a closing header with no spoken cue: show it while the last words are still being said
last = rows[-1]
if not last["matched"]:
    tail = [w for w in words if w["start"] > rows[-2]["t"] + 0.5]
    last["t"] = (tail[len(tail) // 2]["start"] if tail else words[-1]["start"]) - 0.05

# Text overlays: show each one on the spoken word it displays (not on the guide's cue, which often
# belongs to the following phrase). Then a tiny visual lead so the text never trails the voice.
STOP = {"a", "an", "the", "in", "of", "is", "to", "and", "it", "on", "at", "your", "you", "for", "by", "are", "why", "was"}
SPOKEN = {"100": "hundred", "mph": "miles", "200am": "two", "2": "two", "3": "three", "1": "one",
          "99": "time", "100safe": "safe"}


def overlay_tokens(text):
    out = []
    text = text.replace("40,000", "forty thousand")
    for t in re.split(r"[\s/()!?:%-]+|,(?!\d)", text):
        n = norm(t)
        if not n or n in STOP or set(t) <= set("$+.✓"):
            continue
        out.append(SPOKEN.get(n, n))
    return out


TEXT_LEAD = 0.30  # seconds a text overlay appears before its spoken word

# Image/icon pop-ins (no text): the spoken word each visual stands for. They are synced exactly like text.
VISUAL_KEYS = {}  # this project: overlays carry quoted text in the guide, no extra icon keywords needed


def sync_tokens(row):
    if row["n"] in VISUAL_KEYS and not any(w for w in overlay_tokens(row.get("overlay", "")) if w in wn):
        return VISUAL_KEYS[row["n"]]  # overlay text that is never spoken (e.g. 'INVOICE') uses the keyword
    return overlay_tokens(row.get("overlay", "")) or VISUAL_KEYS.get(row["n"], [])


def word_index_at(t):
    return min(range(len(words)), key=lambda k: abs(words[k]["start"] - t))


for k, r in enumerate(rows):
    toks = sync_tokens(r)
    if k == 0 or not toks:
        continue
    prev_t = rows[k - 1]["t"]
    lo = word_index_at(prev_t - 0.2)
    hit = None
    for i in range(lo, len(words)):
        if words[i]["start"] > r["t"] + 2.0:
            break
        # after a text frame, use a later word than the one it sits on; after a plain scene frame the
        # text may land on the same word (the scene frame is then moved earlier below)
        floor = rows[k - 1]["word_t"] + 0.12 if rows[k - 1].get("word_t") is not None else prev_t - 0.2
        if words[i]["start"] < floor:
            continue
        if any(wn[i] == t or (len(t) > 3 and wn[i].startswith(t[:5])) for t in toks):
            hit = i
            break
    if hit is None:
        continue
    # text frames lead their word clearly (owner asked for the text a bit earlier than the voice)
    r["t"], r["matched"], r["synced_to"], r["is_text"] = words[hit]["start"] - TEXT_LEAD, True, words[hit]["text"], True
    r["word_t"] = words[hit]["start"]
    # give the frame before it at least ~0.35 s on screen by moving it earlier if needed
    if k >= 2 and r["t"] - rows[k - 1]["t"] < 0.35:
        rows[k - 1]["t"] = max(rows[k - 2]["t"] + 0.2, r["t"] - 0.45)

LEAD = 0.08  # ~2 frames for scene frames (text frames already lead by TEXT_LEAD)
for r in rows[1:]:
    if not r.get("is_text"):
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
    sync = f" -> text on '{r['synced_to']}'" if r.get("synced_to") else ""
    flag = "~~ " if r.get("fuzzy") else ("ok " if r["matched"] else "-- ")
    print(f"{r['n']:3d} {r['t']:7.2f} (guide {r['approx']:6.1f}) {flag} {r['cue'][:34]:34}{sync}")
