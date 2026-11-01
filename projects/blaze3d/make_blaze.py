"""Build the 3D Blaze base model with MPFB (MakeHuman for Blender) and save blaze_base.blend.

Run: EGL_PLATFORM=surfaceless python3.11 make_blaze.py <path-to-mpfb-extension.zip>
"""
import os, sys, importlib
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
zip_path = sys.argv[-1]

bpy.ops.wm.read_factory_settings(use_empty=True)
import addon_utils  # noqa: E402
if not addon_utils.check("bl_ext.user_default.mpfb")[0]:
    try:
        bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
    except Exception:
        bpy.ops.extensions.package_install_files(filepath=zip_path, repo="user_default", enable_on_install=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402

macro = {
    "gender": 1.0, "age": 0.5, "muscle": 1.0, "weight": 0.45, "proportions": 1.0,
    "height": 0.62, "cupsize": 0.5, "firmness": 1.0,
    "race": {"asian": 0.2, "caucasian": 0.3, "african": 0.5},
}
body = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                 feet_on_ground=False, scale=0.1, macro_detail_dict=macro)
body.name = "Blaze"

# extra muscle definition on top of the macro sliders, then bake into the mesh
from bl_ext.user_default.mpfb.services.targetservice import TargetService  # noqa: E402
TDIR = os.path.join(os.path.dirname(importlib.import_module("bl_ext.user_default.mpfb").__file__), "data", "targets")
EXTRA = {
    "arms/{s}-upperarm-muscle-incr": 1.0, "arms/{s}-upperarm-shoulder-muscle-incr": 1.0,
    "arms/{s}-lowerarm-muscle-incr": 0.8, "arms/{s}-upperarm-scale-horiz-incr": 0.35,
    "legs/{s}-upperleg-muscle-incr": 0.8, "legs/{s}-lowerleg-muscle-incr": 0.7,
    "torso/torso-muscle-pectoral-incr": 1.0, "torso/torso-muscle-dorsi-incr": 1.0,
    "torso/torso-vshape-incr": 0.8, "torso/measure-waist-circ-decr": 0.4,
}
done = set()
for pat, w in EXTRA.items():
    for side in ("l", "r"):
        rel = pat.format(s=side)
        if rel in done:
            continue
        done.add(rel)
        path = os.path.join(TDIR, rel + ".target.gz")
        if os.path.exists(path):
            TargetService.load_target(body, path, weight=w)
        else:
            print("missing target", rel)
TargetService.bake_targets(body)
rig = HumanService.add_builtin_rig(body, "default")
rig.name = "BlazeRig"
# lift the whole rig (body is parented to it) so the feet stand on z=0
bpy.context.view_layer.update()
mw = body.matrix_world
gi = body.vertex_groups["body"].index
minz = min((mw @ v.co).z for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups))
rig.location.z -= minz
bpy.context.view_layer.update()
for bn in ("root", "head", "eye.L", "upperarm01.L", "foot.L"):
    print("bone", bn, tuple(round(x, 3) for x in rig.matrix_world @ rig.data.bones[bn].head_local))
print("body verts", len(body.data.vertices), "bones", len(rig.data.bones))
print("vertex groups sample", [g.name for g in body.vertex_groups][:60])
print("bones", [b.name for b in rig.data.bones])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "blaze_base.blend"))
