"""Shared setup: open blaze_base.blend and give it the Blaze toon look (colors, shorts, band, tape, eyes, outline).

Import from other scripts (run with python3.11, EGL_PLATFORM=surfaceless):
    from blaze_look import setup; body, rig = setup()
"""
import math, os
import bpy
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))

SKIN = [(0.30, 0.025, 0.05), (0.52, 0.06, 0.10), (0.78, 0.20, 0.26)]   # shadow, base, light (linear-ish)
SHORTS = [(0.012, 0.012, 0.015), (0.035, 0.035, 0.04), (0.09, 0.09, 0.1)]
ORANGE = [(0.75, 0.18, 0.0), (1.0, 0.33, 0.0), (1.0, 0.55, 0.12)]
WHITE = [(0.62, 0.64, 0.7), (0.9, 0.9, 0.92), (1.0, 1.0, 1.0)]


def toon_material(name, tones, spec=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*tones[0], 1)
    els[1].position, els[1].color = 0.22, (*tones[1], 1)
    e = els.new(0.62); e.color = (*tones[2], 1)
    emit = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(diff.outputs[0], s2r.inputs[0]); nt.links.new(s2r.outputs[0], ramp.inputs[0])
    col = ramp.outputs[0]
    if spec:
        glossy = nt.nodes.new("ShaderNodeBsdfGlossy"); glossy.inputs["Roughness"].default_value = 0.25
        s2r2 = nt.nodes.new("ShaderNodeShaderToRGB"); rg = nt.nodes.new("ShaderNodeValToRGB")
        rg.color_ramp.interpolation = "CONSTANT"; rg.color_ramp.elements[1].position = 0.55
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "ADD"
        nt.links.new(glossy.outputs[0], s2r2.inputs[0]); nt.links.new(s2r2.outputs[0], rg.inputs[0])
        nt.links.new(rg.outputs[0], mix.inputs["Factor"]); mix.inputs["A"].default_value = (0, 0, 0, 1)
        nt.links.new(col, mix.inputs["A"]); mix.inputs["B"].default_value = (spec, spec * 0.8, spec * 0.8, 1)
        col = mix.outputs["Result"]
    nt.links.new(col, emit.inputs[0]); nt.links.new(emit.outputs[0], out.inputs[0])
    return m


def flat_material(name, rgb, backface_cull=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*rgb, 1); nt.links.new(em.outputs[0], out.inputs[0])
    m.use_backface_culling = backface_cull
    return m


def group_weight(body, v, names):
    w = 0.0
    for g in v.groups:
        if body.vertex_groups[g.group].name in names:
            w += g.weight
    return w


def setup(outline=0.010):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "blaze_base.blend"))
    body = bpy.data.objects["Blaze"]; rig = bpy.data.objects["BlazeRig"]
    me = body.data
    mats = {
        "skin": toon_material("BlazeSkin", SKIN, spec=0.35),
        "shorts": toon_material("Shorts", SHORTS, spec=0.06),
        "orange": toon_material("Orange", ORANGE),
        "white": toon_material("Tape", WHITE),
        "outline": flat_material("Outline", (0.005, 0.005, 0.008), backface_cull=True),
    }
    me.materials.clear()
    for k in ["skin", "shorts", "orange", "white", "outline"]:
        me.materials.append(mats[k])
    idx = {k: i for i, k in enumerate(["skin", "shorts", "orange", "white", "outline"])}

    import bmesh
    body_gi = body.vertex_groups["body"].index
    zs = [v.co.z for v in me.vertices if any(g.group == body_gi and g.weight > 0.5 for g in v.groups)]
    top, bottom = max(zs), min(zs)
    H = top - bottom
    bm = bmesh.new(); bm.from_mesh(me)
    for frac in (0.355, 0.585, 0.952, 0.977):  # shorts hem, waistband, sweatband bottom/top
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, bottom + frac * H), plane_no=(0, 0, 1))
    # vertical cuts for the orange stripe on the outer hips/thighs
    xs = [abs(v.co.x) for v in bm.verts if bottom + 0.36 * H < v.co.z < bottom + 0.58 * H]
    xcut = max(xs) * 0.86 if xs else 0.15
    for sx in (1, -1):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(sx * xcut, 0, 0), plane_no=(1, 0, 0))
    bm.to_mesh(me); bm.free(); me.update()
    hips = {"pelvis.L", "pelvis.R", "root", "spine05", "upperleg01.L", "upperleg01.R", "upperleg02.L", "upperleg02.R"}
    wrists = {"wrist.L", "wrist.R", "lowerarm02.L", "lowerarm02.R"}
    vmat = [idx["skin"]] * len(me.vertices)
    for v in me.vertices:
        z = (v.co.z - bottom) / H
        # shorts: from just below the navel down to mid-thigh
        if 0.355 < z < 0.585 and group_weight(body, v, hips) > 0.25:
            vmat[v.index] = idx["shorts"]
            # orange side stripe on the outer thigh
            if abs(v.co.x) > 0.0 and 0.36 < z < 0.55:
                pass
        # sweatband around the forehead
        if 0.9515 < z < 0.9775 and group_weight(body, v, {"head"}) > 0.5:
            vmat[v.index] = idx["orange"]
        # wrist tape
        if group_weight(body, v, {"wrist.L", "wrist.R"}) > 0.35 or (
                group_weight(body, v, {"lowerarm02.L", "lowerarm02.R"}) > 0.6 and 0.0 < z < 1.0 and
                group_weight(body, v, {"wrist.L", "wrist.R"}) > 0.05):
            vmat[v.index] = idx["white"]
    # orange stripe: a clean vertical band on the outer side of each hip/thigh
    shorts_vs = [v for v in me.vertices if vmat[v.index] == idx["shorts"]]
    xmax = max(abs(v.co.x) for v in shorts_vs)
    for v in shorts_vs:
        if abs(v.co.x) > xmax * 0.86 - 1e-5:
            vmat[v.index] = idx["orange"]
    for p in me.polygons:
        counts = {}
        for vi in p.vertices:
            counts[vmat[vi]] = counts.get(vmat[vi], 0) + 1
        p.material_index = max(counts, key=counts.get)
    for p in me.polygons:
        p.use_smooth = True

    # eyes: two flattened white discs with black pupils, parented to the head bone
    head_bone = rig.pose.bones["head"]
    for side in (1, -1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=24, ring_count=12)
        eye = bpy.context.active_object; eye.name = f"Eye{side}"
        eye.data.materials.append(flat_material(f"EyeWhite{side}", (1, 1, 1)))
        bpy.ops.object.shade_smooth()
        eye.scale = (0.0105, 0.004, 0.0068)
        # placed later relative to the face; keep a reference
        eye["side"] = side
    # modifiers: subdivision for smooth silhouette + inverted-hull outline
    sub = body.modifiers.new("Subsurf", "SUBSURF"); sub.levels = 1; sub.render_levels = 1
    sol = body.modifiers.new("Outline", "SOLIDIFY")
    sol.thickness = outline; sol.offset = 1.0; sol.use_flip_normals = True
    sol.material_offset = idx["outline"]; sol.use_rim = False
    return body, rig


def place_eyes(body, rig):
    """Put white almond eye discs on the face, in front of the eye bones."""
    me = body.data
    for side, bname in ((1, "eye.L"), (-1, "eye.R")):
        eye = bpy.data.objects[f"Eye{side}"]
        b = rig.data.bones[bname]
        c = rig.matrix_world @ b.head_local
        mw = body.matrix_world
        near = [mw @ v.co for v in me.vertices]
        near = [p for p in near if abs(p.x - c.x) < 0.006 and abs(p.z - c.z) < 0.006]
        front_y = c.y - 0.013  # eye bone sits at the eyeball centre; put the disc just in front of it
        target = Matrix.Translation((c.x, front_y - 0.0015, c.z + 0.001)) @ \
            Euler((0, math.radians(-10 * side), math.radians(-14 * side))).to_matrix().to_4x4() @ \
            Matrix.Diagonal((0.0105, 0.004, 0.0068, 1))
        eye.parent = rig; eye.parent_type = "BONE"; eye.parent_bone = "head"
        bpy.context.view_layer.update()
        eye.matrix_world = target  # keeps this world placement while following the head bone


def scene_setup(res=(1280, 720), ortho_scale=2.2):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    sc.render.use_freestyle = True
    sc.render.line_thickness_mode = "ABSOLUTE"; sc.render.line_thickness = 1.4
    vl = bpy.context.view_layer; fs = vl.freestyle_settings
    fs.crease_angle = math.radians(152)
    ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Lines")
    ls.select_by_visibility = True; ls.select_silhouette = False; ls.select_border = False
    ls.select_crease = True; ls.select_contour = False
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("MuscleLines")
    ls.linestyle.color = (0.02, 0.0, 0.01); ls.linestyle.thickness = 1.4; ls.linestyle.alpha = 0.55
    sun = bpy.data.lights.new("Key", "SUN"); sun.energy = 3.0
    so = bpy.data.objects.new("Key", sun); sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), math.radians(-25), math.radians(-35))
    cam = bpy.data.cameras.new("Cam"); cam.type = "ORTHO"; cam.ortho_scale = ortho_scale
    co = bpy.data.objects.new("Cam", cam); sc.collection.objects.link(co); sc.camera = co
    return co, so
