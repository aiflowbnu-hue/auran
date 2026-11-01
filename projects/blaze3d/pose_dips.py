"""Bench-dips pose with IK: hands fixed on a bench behind, heels on the floor, pelvis moves with u (0 top .. 1 bottom)."""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix
from blaze_look import setup, place_eyes, scene_setup, toon_material

def empty(name, loc):
    e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e); e.location = loc; return e

def add_ik(rig, bone, target, chain, pole=None, pole_angle=0):
    c = rig.pose.bones[bone].constraints.new("IK"); c.target = target; c.chain_count = chain
    if pole: c.pole_target = pole; c.pole_angle = math.radians(pole_angle)
    return c

def build():
    body, rig = setup()
    place_eyes(body, rig)
    # bench: a toon-shaded box behind him
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.42, 0.22))
    bench = bpy.context.active_object; bench.scale = (0.9, 0.36, 0.44)
    bench.data.materials.append(toon_material("Wood", [(0.22, 0.10, 0.04), (0.38, 0.19, 0.08), (0.55, 0.30, 0.14)]))
    sol = bench.modifiers.new("Outline", "SOLIDIFY"); sol.thickness = 0.012; sol.offset = 1; sol.use_flip_normals = True
    from blaze_look import flat_material
    bench.data.materials.append(flat_material("BenchLine", (0.005, 0.005, 0.008), backface_cull=True)); sol.material_offset = 1
    T = {}
    for s, x in (("L", 0.19), ("R", -0.19)):
        T["hand" + s] = empty("Hand" + s, (x, 0.27, 0.46))
        T["foot" + s] = empty("Foot" + s, (x * 0.6, -0.95, 0.07))
        T["elbowpole" + s] = empty("ElbowPole" + s, (x * 1.6, 1.2, 0.9))
        T["kneepole" + s] = empty("KneePole" + s, (x * 0.7, -0.6, 1.2))
        add_ik(rig, "lowerarm02." + s, T["hand" + s], 4, T["elbowpole" + s], -90)
        add_ik(rig, "lowerleg02." + s, T["foot" + s], 4, T["kneepole" + s], -90)
    return body, rig

def set_pelvis(rig, u):
    pb = rig.pose.bones["root"]
    rest = rig.matrix_world @ pb.bone.head_local
    top, bottom = Vector((0, 0.02, 0.60)), Vector((0, 0.06, 0.33))
    tgt = top.lerp(bottom, u)
    pb.matrix = Matrix.Translation(rig.matrix_world.inverted() @ tgt - pb.bone.head_local) @ pb.bone.matrix_local
    bpy.context.view_layer.update()

if __name__ == "__main__":
    OUT = sys.argv[-1]
    body, rig = build()
    cam, sun = scene_setup(res=(1280, 720), ortho_scale=2.4)
    cam.location = (6, -0.2, 0.75); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
    for u in (0.0, 1.0):
        set_pelvis(rig, u)
        bpy.context.scene.render.filepath = f"{OUT}/dips3d_{int(u)}.png"
        bpy.ops.render.render(write_still=True)
    print("done")
