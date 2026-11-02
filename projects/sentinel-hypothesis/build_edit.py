#!/usr/bin/env python3
"""Build edit.json: snap each visual from 00_TIMELINE_INDEX.txt to the spoken start of its sentence
(word timings from assets/transcript.json), then pick effects and sound effects by keywords."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")

words = json.load(open(os.path.join(A, "transcript.json")))
words = words[0] if isinstance(words, list) else words
words = [w for w in words["words"] if w["type"] == "word"]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower().replace("2:00", "two").replace("you are", "youre"))
wn = [norm(w["text"]) for w in words]

lines = []
for ln in open(os.path.join(A, "00_TIMELINE_INDEX.txt"), encoding="utf-8", errors="replace"):
    m = re.match(r"(\S+\.jpg)\s+->\s+(\d\d):(\d\d)\s+-\s+\S+\s+\|\s+(.*)", ln.strip())
    if m:
        lines.append((m.group(1), int(m.group(2)) * 60 + int(m.group(3)), m.group(4)))


def find_start(sentence, approx, from_idx):
    """Index of the first word of `sentence`: best 3-word match near the index's approximate time."""
    toks = [norm(t) for t in sentence.replace("you are", "you're").replace("You are", "You're").split() if norm(t)][:3]
    best = None
    for i in range(from_idx, len(words)):
        if words[i]["start"] > approx + 6:
            break
        score = sum(1 for k, t in enumerate(toks) if i + k < len(wn) and (wn[i + k] == t or wn[i + k].startswith(t[:4])))
        dist = abs(words[i]["start"] - approx)
        key = (score, -dist)
        if score >= min(2, len(toks)) and (best is None or key > best[0]):
            best = (key, i)
    return best[1] if best else None


# keyword -> (extra fx, [sfx name, offset, volume])
RULES = [
    ("quiet", [], [["night_crickets", 0, 0.5]]),
    ("locked", ["pop"], [["tick", 0.3, 0.6]]),
    ("shut", ["pop"], [["tick", 0.3, 0.6]]),
    ("safe", [], [["sparkle", 0.2, 0.4]]),
    ("2am_remember", [], [["clock_tick", 0, 0.5], ["sparkle", 1.0, 0.4]]),
    ("2am", ["shake"], [["clock_tick", 0, 0.6]]),
    ("heart", ["shake"], [["heartbeat", 0, 0.8]]),
    ("email", [], [["pop", 0.2, 0.5]]),
    ("bill", [], [["buzzer", 0.4, 0.35]]),
    ("danger", [], [["pop", 0, 0.45]]),
    ("predator_outside", [], [["buzzer", 0.5, 0.35]]),
    ("spinning", ["shake"], [["whoosh", 0, 0.5], ["glitch", 0.4, 0.5]]),
    ("falling_apart", ["shake"], [["punch", 0, 0.6]]),
    ("modern_flaw", [], [["buzzer", 0.6, 0.4]]),
    ("survival", [], [["ding", 0.3, 0.5]]),
    ("40000_years_ago_ancestor", [], [["deep_boom", 0, 0.6], ["night_crickets", 0.3, 0.45]]),
    ("racing_heart", ["shake"], [["heartbeat", 0, 0.8]]),
    ("alive_today", [], [["ding", 0.4, 0.5]]),
    ("kill_one", ["shake"], [["punch", 0.4, 0.7]]),
    ("myth_modern", [], [["glitch", 0.3, 0.5]]),
    ("broken_or_weak", [], [["buzzer", 0.4, 0.4]]),
    ("chronic_stress", [], [["alarm_ring", 0.2, 0.3]]),
    ("glitch", [], [["glitch", 0, 0.5], ["ding", 1.6, 0.5]]),
    ("sentinel_hypothesis", ["punch"], [["deep_boom", 0, 0.85]]),
    ("asleep_at_once", [], [["night_crickets", 0, 0.45]]),
    ("staggered", [], [["pop", 0.5, 0.4], ["pop", 1.4, 0.4], ["pop", 2.3, 0.4]]),
    ("twig", ["shake"], [["twig_snap", 0.8, 0.9]]),
    ("two_types", [], [["whoosh", 0, 0.5]]),
    ("calm", [], [["sparkle", 0.3, 0.4]]),
    ("rolled_over", [], [["bush_rustle", 0, 0.7]]),
    ("leopard", ["shake"], [["big_cat_growl", 0, 0.9]]),
    ("anxious_paranoid", [], [["whoosh", 0, 0.45]]),
    ("adrenaline", ["shake"], [["heartbeat", 0, 0.8], ["bush_rustle", 0.2, 0.5]]),
    ("apex", ["shake"], [["big_cat_growl", 0.2, 0.7]]),
    ("wind", [], [["bush_rustle", 0.3, 0.5]]),
    ("lion_survived", ["shake"], [["lion_roar", 0, 0.8]]),
    ("descendant", [], [["ding", 0.5, 0.5]]),
    ("catastrophize", [], [["glitch", 0.3, 0.4]]),
    ("alarm_apartment", ["shake"], [["alarm_ring", 0.3, 0.6]]),
    ("alarm_still", [], [["alarm_ring", 0.4, 0.5]]),
    ("searching", [], [["whoosh", 0, 0.45]]),
    ("invent_threat", ["shake"], [["punch", 0.6, 0.6]]),
    ("mortgage", [], [["pop", 0.3, 0.45], ["pop", 1.0, 0.45], ["pop", 1.7, 0.45]]),
    ("predator", ["shake"], [["big_cat_growl", 0.2, 0.6]]),
    ("not_broken", [], [["ding", 0.4, 0.45], ["ding", 1.4, 0.45], ["ding", 2.4, 0.45]]),
    ("night_watch", [], [["deep_boom", 0, 0.5], ["night_crickets", 0.5, 0.5]]),
]

cuts, idx = [], 0
for name, approx, sentence in lines:
    i = find_start(sentence, approx, idx)
    t = words[i]["start"] if i is not None else float(approx)
    if i is not None:
        idx = i + 1
    t = max(t - 0.08, cuts[-1]["start"] + 0.3 if cuts else 0.0)  # cut a hair before the word
    key = name[10:-4]
    fx, sfx = ["kb"], []
    if cuts:
        fx.append("punch"); sfx.append(["whoosh", 0, 0.3])
    for kw, efx, esfx in RULES:
        if kw in key:
            fx += [f for f in efx if f not in fx]
            sfx += esfx
            break
    cuts.append({"img": name, "start": round(0.0 if not cuts else t, 3), "fx": fx, "sfx": sfx,
                 "matched": i is not None, "text": sentence})

# hard cuts with no transitions (as requested): no punch/pop/shake and no per-cut whoosh;
# the story sound effects stay. Only the gentle push-in remains on each image.
for c in cuts:
    c["fx"] = ["kb"]
    c["sfx"] = [s for s in c["sfx"] if s[0] != "whoosh"]

edit = {"fps": 30, "size": [1920, 1080], "voiceover": "assets/voiceover.mp3",
        "music": "assets/music.mp3", "music_volume": 0.16, "tail": 1.5, "cuts": cuts}
json.dump(edit, open(os.path.join(HERE, "edit.json"), "w"), indent=1)
for c, (_, approx, _) in zip(cuts, lines):
    print(f"{c['start']:7.2f} (index {approx:3d}) {'ok ' if c['matched'] else 'MISS'} {c['img'][:44]:44} {','.join(c['fx'])}")
