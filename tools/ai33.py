#!/usr/bin/env python3
"""Small ai33.pro client: submit a task, poll until done, download the audio.

API key is read from the AI33_KEY environment variable (never commit it).

Usage:
  python3 tools/ai33.py sfx "cartoon whoosh" out.mp3 --duration 1.0 [--influence 0.5] [--loop]
  python3 tools/ai33.py tts script.txt out.mp3 --voice elevenlabs_TX3LPaxmHKxFdv7VOQHJ [--speed 1.0]
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

API = "https://api.ai33.pro/v1"
UA = {"User-Agent": "curl/8.5.0"}  # the CDN rejects Python's default user-agent


def _req(method, path, body=None):
    key = os.environ.get("AI33_KEY")
    if not key:
        sys.exit("AI33_KEY is not set")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}/{path}", data=data, method=method,
                                 headers={"xi-api-key": key, "Content-Type": "application/json", **UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))


def wait(task_id, timeout=300):
    end = time.time() + timeout
    while time.time() < end:
        t = _req("GET", f"task/{task_id}")
        if t["status"] != "doing":
            if t["status"] != "done":
                sys.exit(f"task {task_id} ended with status {t['status']}: {t}")
            return t
        time.sleep(3)
    sys.exit(f"task {task_id} timed out")


def download(url, out):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(out, "wb") as f:
        f.write(r.read())


def sfx(text, out, duration=None, influence=0.5, loop=False):
    body = {"text": text, "prompt_influence": influence, "loop": loop,
            "model_id": "eleven_text_to_sound_v3"}
    if duration:
        body["duration_seconds"] = duration
    r = _req("POST", "task/sound-effect", body)
    t = wait(r["task_id"])
    m = t["metadata"]
    download(m.get("audio_url") or m.get("output_uri"), out)
    print(f"{out}  (credits used {t.get('credit_cost')}, remaining {r.get('ec_remain_credits')})")


def tts(text, out, voice, speed=1.0):
    """ElevenLabs (or any provider-prefixed voice) via the unified v3 endpoint. ~1 credit per character."""
    key = os.environ.get("AI33_KEY") or sys.exit("AI33_KEY is not set")
    boundary = "----ai33boundary"
    parts = [("text", text), ("voice_id", voice), ("speed", str(speed))]
    body = "".join(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'
                   for k, v in parts) + f"--{boundary}--\r\n"
    req = urllib.request.Request("https://api.ai33.pro/v3/text-to-speech", data=body.encode(), method="POST",
                                 headers={"xi-api-key": key, **UA,
                                          "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        task_id = json.load(r)["task_id"]
    t = wait(task_id)
    download(t["metadata"]["audio_url"], out)
    print(f"{out}  (credits used {t.get('credit_cost')})")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sfx")
    s.add_argument("text"); s.add_argument("out")
    s.add_argument("--duration", type=float)
    s.add_argument("--influence", type=float, default=0.5)
    s.add_argument("--loop", action="store_true")
    t = sub.add_parser("tts")
    t.add_argument("text_file"); t.add_argument("out")
    t.add_argument("--voice", required=True)
    t.add_argument("--speed", type=float, default=1.0)
    a = p.parse_args()
    if a.cmd == "sfx":
        sfx(a.text, a.out, a.duration, a.influence, a.loop)
    elif a.cmd == "tts":
        tts(open(a.text_file).read(), a.out, a.voice, a.speed)
