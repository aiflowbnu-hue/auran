#!/usr/bin/env python3
"""Lossless render for hard-cut projects (no zoom/effects): the source PNGs go straight into ffmpeg - no browser,
no JPEG step. Each image is scaled once with Lanczos to cover 1920x1080 and the video is encoded with lossless
H.264 (qp 0, 4:4:4). Audio: voiceover + ducked music, loudness -14 LUFS, AAC 320 kb/s (the source voiceover is an
MP3, so the audio cannot be more lossless than that).

    python3 render_lossless.py            -> build/<name>_lossless.mp4
"""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
os.makedirs(BUILD, exist_ok=True)
E = json.load(open(os.path.join(HERE, "edit.json")))
W, H = E["size"]
FPS = E["fps"]
dur = lambda f: float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                               "-of", "csv=p=0", f]))
vo = os.path.join(HERE, E["voiceover"])
FULL = dur(vo) + E["tail"]
R0, R1 = E.get("range", [0, FULL])
R1 = min(R1, FULL)
TOTAL = R1 - R0                     # a sample renders only the edit's range (compose.py START END)

# concat list: each image held until the next cut (times snapped to the frame grid so cuts land on exact frames)
cuts = E["cuts"]
starts = [round(max(c["start"] - R0, 0) * FPS) / FPS for c in cuts] + [round(TOTAL * FPS) / FPS]
lst = os.path.join(BUILD, "frames.txt")
with open(lst, "w") as f:
    for c, a, b in zip(cuts, starts, starts[1:]):
        f.write(f"file '{os.path.join(HERE, c['img'])}'\nduration {b - a:.6f}\n")
    f.write(f"file '{os.path.join(HERE, cuts[-1]['img'])}'\n")

silent = os.path.join(BUILD, "video_lossless.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos+accurate_rnd+full_chroma_int,"
                       f"crop={W}:{H},fps={FPS},format=yuv444p",
                "-c:v", "libx264", "-qp", "0", "-preset", "slow", "-t", f"{TOTAL:.3f}", silent], check=True)

audio = os.path.join(BUILD, "audio.m4a")
mus = os.path.join(HERE, E["music"])
fl = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{TOTAL},asplit=2[vo][key];"
      f"[1:a]aresample=48000,aformat=channel_layouts=stereo,aloop=loop=-1:size=2e9,atrim=0:{TOTAL},"
      f"volume={E['music_volume']},afade=t=in:d=0.5,afade=t=out:st={TOTAL - 1.5}:d=1.5[mraw];"
      f"[mraw][key]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=300[music];"
      f"[vo][music]amix=inputs=2:normalize=0,atrim=0:{TOTAL},loudnorm=I=-14:TP=-1.5:LRA=11[out]")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(R0), "-i", vo, "-ss", str(R0), "-i", mus, "-filter_complex", fl, "-map", "[out]",
                "-ar", "48000", "-c:a", "aac", "-b:a", "320k", audio], check=True)

name = os.path.basename(HERE).replace("-", "_")
name += "_sample" if R0 > 0 or R1 < FULL else ""
out = os.path.join(BUILD, f"{name}_lossless.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", silent, "-i", audio, "-c", "copy", "-shortest",
                "-movflags", "+faststart", out], check=True)
play = out.replace("_lossless.mp4", "_play.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", out, "-c:v", "libx264", "-crf", "8", "-preset", "slow",
                "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", play], check=True)
print("wrote", out, f"{TOTAL:.2f}s", f"{os.path.getsize(out) / 1e6:.0f} MB")
