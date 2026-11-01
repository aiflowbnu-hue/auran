"""Render a 5 s bench-dips clip (12 fps, toon look) as PNG frames into <out_dir>/dips_frames/."""
import math, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from pose_dips import build, set_pelvis
from blaze_look import scene_setup

OUT = os.path.join(sys.argv[-1], "dips_frames"); os.makedirs(OUT, exist_ok=True)
FPS, DUR, PERIOD = 12, 5.0, 2.4
body, rig = build()
cam, sun = scene_setup(res=(1280, 720), ortho_scale=2.8)
cam.location = (6, -0.3, 0.72); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
sun.rotation_euler = (math.radians(55), 0, math.radians(110))
t0 = time.time()
n = int(FPS * DUR)
for i in range(n):
    t = i / FPS
    # hold briefly at the top, smooth descent and press
    ph = (t % PERIOD) / PERIOD
    u = 0.5 - 0.5 * math.cos(2 * math.pi * min(1.0, ph / 0.85)) if ph < 0.85 else 0.0
    set_pelvis(rig, u)
    bpy.context.scene.render.filepath = os.path.join(OUT, f"f{i:03d}.png")
    bpy.ops.render.render(write_still=True)
    if i % 10 == 0:
        print(f"frame {i}/{n} {time.time() - t0:.0f}s", flush=True)
print("done", flush=True)
