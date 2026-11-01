#!/usr/bin/env python3
"""Generate one voiceover clip per scene (ElevenLabs via ai33), then write timeline.json.

Needs AI33_KEY in the environment. Clips already on disk are reused (no credits spent).
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import ai33  # noqa: E402

GAP = 0.35      # silence between scenes (s)
LEAD_IN = 0.6   # silence before the first line (s)

script = json.load(open(os.path.join(HERE, "script.json")))
vo_dir = os.path.join(HERE, "build", "vo")
os.makedirs(vo_dir, exist_ok=True)


def make(scene):
    out = os.path.join(vo_dir, f"{scene['id']}.mp3")
    if not os.path.exists(out):
        ai33.tts(scene["text"], out, script["voice"])
    return out


def duration(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]))


with ThreadPoolExecutor(2) as ex:
    paths = list(ex.map(make, script["scenes"]))

t = LEAD_IN
timeline = []
for scene, path in zip(script["scenes"], paths):
    d = duration(path)
    timeline.append({"id": scene["id"], "text": scene["text"], "start": round(t, 3),
                     "dur": round(d, 3), "file": os.path.relpath(path, HERE)})
    t += d + GAP
total = round(t + 1.5, 3)  # tail for the outro sting
json.dump({"total": total, "scenes": timeline}, open(os.path.join(HERE, "build", "timeline.json"), "w"), indent=1)
print(f"total {total:.1f}s")
for s in timeline:
    print(f"{s['start']:6.2f} +{s['dur']:5.2f}  {s['id']}")
