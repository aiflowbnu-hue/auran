#!/usr/bin/env python3
"""Realistic test: voiceover (ElevenLabs via ai33) + images (Gemini 3 Pro Image via ai33).
Character reference portraits are made first, then every scene uses them as reference images for consistency.
Needs AI33_KEY in the environment. Skips files that already exist, so it can be re-run after a failure."""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import ai33

S = json.load(open(os.path.join(HERE, "script.json")))
A = os.path.join(HERE, "assets"); os.makedirs(os.path.join(A, "frames"), exist_ok=True)


def job(fn, *a, **k):
    out = a[1]
    if os.path.exists(out):
        return out
    try:
        fn(*a, **k)
    except SystemExit as e:
        print("FAILED", out, e, flush=True)
    except Exception as e:
        print("FAILED", out, repr(e), flush=True)
    return out


with ThreadPoolExecutor(3) as ex:
    vo = ex.submit(job, ai33.tts, S["voiceover"], os.path.join(A, "voiceover.mp3"), S["voice"])
    refs = {}
    for name, desc in S["characters"].items():
        p = (f"Character reference photo: {desc} Full body, standing, neutral pose, facing the camera at three-quarter angle, "
             f"plain light-grey studio background. {S['style']}")
        refs[name] = ex.submit(job, ai33.image, p, os.path.join(A, f"ref_{name}.png"), aspect="3:4", res="2K")
    refs = {k: v.result() for k, v in refs.items()}
    futs = []
    for sc in S["scenes"]:
        assets, tags = [], []
        for i, c in enumerate(sc["chars"]):
            if os.path.exists(refs[c]):
                assets.append(refs[c]); tags.append(f"the {c} is the same person as in @img{len(assets)} ({S['characters'][c]})")
        p = sc["prompt"] + (" " + "; ".join(tags) + "." if tags else "") + " " + S["style"]
        futs.append(ex.submit(job, ai33.image, p, os.path.join(A, "frames", f"scene_{sc['id']:02d}.png"),
                              aspect="16:9", res="2K", assets=assets))
    for f in futs:
        print("done", f.result(), flush=True)
    print("voiceover", vo.result(), flush=True)
