"""Build the 3D Blaze base model with MPFB (MakeHuman for Blender) and save blaze_base.blend.

Run: EGL_PLATFORM=surfaceless python3.11 make_blaze.py <path-to-mpfb-extension.zip>
"""
import os, sys, importlib
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
zip_path = sys.argv[-1]

bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    importlib.import_module("bl_ext.user_default.mpfb")
except ImportError:
    bpy.ops.extensions.package_install_files(filepath=zip_path, repo="user_default", enable_on_install=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402

macro = {
    "gender": 1.0, "age": 0.5, "muscle": 1.0, "weight": 0.45, "proportions": 1.0,
    "height": 0.62, "cupsize": 0.5, "firmness": 1.0,
    "race": {"asian": 0.2, "caucasian": 0.3, "african": 0.5},
}
body = HumanService.create_human(mask_helpers=True, detailed_helpers=False, extra_vertex_groups=True,
                                 feet_on_ground=True, scale=0.1, macro_detail_dict=macro)
body.name = "Blaze"
rig = HumanService.add_builtin_rig(body, "default")
rig.name = "BlazeRig"
print("body verts", len(body.data.vertices), "bones", len(rig.data.bones))
print("vertex groups sample", [g.name for g in body.vertex_groups][:60])
print("bones", [b.name for b in rig.data.bones])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "blaze_base.blend"))
