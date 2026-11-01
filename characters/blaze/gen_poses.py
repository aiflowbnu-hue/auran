#!/usr/bin/env python3
"""Generate Blaze pose images/keyframe sheets from poses.json (needs AI33_KEY). Existing files are skipped.

Sheets (21:9) hold two keyframes side by side at the same scale; split_sheets.py cuts and aligns them.
Usage: python3 gen_poses.py [id ...]
"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import ai33  # noqa: E402

cfg = json.load(open(os.path.join(HERE, "poses.json")))
REF = os.path.join(HERE, "..", "concept_blaze.png")
OUT = os.path.join(HERE, "sheets")
os.makedirs(OUT, exist_ok=True)
only = set(sys.argv[1:])


def gen(it):
    out = os.path.join(OUT, f"{it['id']}.png")
    if os.path.exists(out) or (only and it["id"] not in only):
        return
    prompt = f"{cfg['style']}\n\n{it['prompt']}"
    ai33.image(prompt, out, aspect=it["aspect"], res="2K", assets=[REF])


with ThreadPoolExecutor(2) as ex:
    list(ex.map(gen, cfg["items"]))
print("done")
