import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from blaze_look import setup, place_eyes, scene_setup
body, rig = setup()
place_eyes(body, rig)
cam, sun = scene_setup(res=(900, 1100), ortho_scale=2.0)
OUT = sys.argv[-1]
for name, loc, rot in [("front", (0, -6, 0.88), (math.radians(90), 0, 0)), ("side", (6, 0, 0.88), (math.radians(90), 0, math.radians(90))), ("q34", (4.2, -4.2, 1.1), (math.radians(86), 0, math.radians(45)))]:
    cam.location = loc; cam.rotation_euler = rot
    bpy.context.scene.render.filepath = f"{OUT}/look_{name}.png"
    bpy.ops.render.render(write_still=True)
print("done")
