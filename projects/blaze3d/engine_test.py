import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=False)
for eng in ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH", "CYCLES"]:
    try:
        bpy.context.scene.render.engine = eng
    except Exception as e:
        print(eng, "not available", e); continue
    sc = bpy.context.scene; sc.render.resolution_x = 160; sc.render.resolution_y = 90
    sc.render.filepath = f"/tmp/claude-0/-home-user/195b105c-e58f-5fbf-b96e-aaf0f183e3e6/scratchpad/eng_{eng}.png"
    if eng == "CYCLES": sc.cycles.samples = 4; sc.cycles.device = "CPU"
    try:
        bpy.ops.render.render(write_still=True); print(eng, "OK")
    except Exception as e:
        print(eng, "FAILED", e)
