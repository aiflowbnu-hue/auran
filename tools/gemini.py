#!/usr/bin/env python3
"""Google Gemini API client: the same models Google Flow uses, called directly.

  - image(): Gemini 3 Pro Image ("Nano Banana Pro") - text-to-image and image editing with reference images.
  - video(): Veo - text/image-to-video (long-running operation, polled until done).

Needs a Gemini API key (Google AI Studio -> Get API key) in the GEMINI_API_KEY environment variable.
Never commit the key.

    python3 tools/gemini.py image prompt.txt out.png [--ref a.png --ref b.png] [--aspect 16:9] [--size 2K]
    python3 tools/gemini.py video prompt.txt out.mp4 [--image first_frame.png] [--aspect 16:9]
"""
import argparse, base64, json, mimetypes, os, sys, time, urllib.error, urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta"
IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview")
VIDEO_MODEL = os.environ.get("GEMINI_VIDEO_MODEL", "veo-3.1-generate-preview")


def _key():
    return os.environ.get("GEMINI_API_KEY") or sys.exit("GEMINI_API_KEY is not set")


def _call(method, url, body=None, retries=5):
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"x-goog-api-key": _key(), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:600]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
                continue
            raise SystemExit(f"Gemini API {e.code}: {msg}")


def _inline(path):
    mt = mimetypes.guess_type(path)[0] or "image/png"
    return {"inline_data": {"mime_type": mt, "data": base64.b64encode(open(path, "rb").read()).decode()}}


def image(prompt, out, refs=(), aspect="16:9", size="2K"):
    """One image. refs: reference image paths (characters, style, previous frame) sent before the prompt."""
    parts = [_inline(p) for p in refs] + [{"text": prompt}]
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"],
                                 "imageConfig": {"aspectRatio": aspect, "imageSize": size}}}
    r = _call("POST", f"{BASE}/models/{IMAGE_MODEL}:generateContent", body)
    for cand in r.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            blob = part.get("inlineData") or part.get("inline_data")
            if blob:
                os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
                open(out, "wb").write(base64.b64decode(blob["data"]))
                print(out, flush=True)
                return out
    raise SystemExit(f"no image returned: {json.dumps(r)[:600]}")


def video(prompt, out, first_frame=None, aspect="16:9", timeout=1200):
    """Veo clip. Starts a long-running operation, polls it, downloads the result."""
    inst = {"prompt": prompt}
    if first_frame:
        mt = mimetypes.guess_type(first_frame)[0] or "image/png"
        inst["image"] = {"bytesBase64Encoded": base64.b64encode(open(first_frame, "rb").read()).decode(), "mimeType": mt}
    op = _call("POST", f"{BASE}/models/{VIDEO_MODEL}:predictLongRunning",
               {"instances": [inst], "parameters": {"aspectRatio": aspect}})
    name, t0 = op["name"], time.time()
    while not op.get("done"):
        if time.time() - t0 > timeout:
            raise SystemExit(f"video timed out: {name}")
        time.sleep(10)
        op = _call("GET", f"{BASE}/{name}")
    if "error" in op:
        raise SystemExit(f"video failed: {op['error']}")
    resp = op["response"]
    samples = (resp.get("generateVideoResponse") or resp).get("generatedSamples") or resp.get("generatedVideos") or []
    uri = samples[0]["video"]["uri"]
    req = urllib.request.Request(uri, headers={"x-goog-api-key": _key()})
    with urllib.request.urlopen(req, timeout=600) as r:
        open(out, "wb").write(r.read())
    print(out, flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("image")
    i.add_argument("prompt_file"); i.add_argument("out")
    i.add_argument("--ref", action="append", default=[])
    i.add_argument("--aspect", default="16:9"); i.add_argument("--size", default="2K")
    v = sub.add_parser("video")
    v.add_argument("prompt_file"); v.add_argument("out")
    v.add_argument("--image"); v.add_argument("--aspect", default="16:9")
    a = ap.parse_args()
    text = open(a.prompt_file).read()
    if a.cmd == "image":
        image(text, a.out, a.ref, a.aspect, a.size)
    else:
        video(text, a.out, a.image, a.aspect)
