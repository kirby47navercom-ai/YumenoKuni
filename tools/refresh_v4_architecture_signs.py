"""Refresh printed pixels only; leave all completed building geometry alone."""
import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));import build_v4_rebuilt_environment as A
O=R/'art/space_v4/facility_architecture_v2';bpy.ops.wm.open_mainfile(filepath=str(A.O/'sources/park-rebuilt.blend'));image=bpy.data.images.load(str(R/'art/space_v4/facility_identity_v1/facility-signs.png'),check_existing=False);image.pack()
for m in bpy.data.materials:
    if m.name.startswith('identity_facility_sign')and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE':n.image=image
world=bpy.data.objects['park_exterior_level'];A.freeze(list(world.children_recursive))
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(A.O/'sources/park-rebuilt.blend'),compress=True);groups=[bpy.data.objects['exterior_'+n]for n in ['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']];landmarks=set(o for p in groups for o in A.descendants(p));common=[o for o in world.children_recursive if o not in landmarks];row=A.export(common,'finish_context.glb','Assets/Art/explore3d/finish_context.glb',{'facadesRebuilt':31,'treesRebuilt':22,'purposeArchitecture':30});file=O/'manifest.json';m=json.loads(file.read_text());m['rawAsset']=row;file.write_text(json.dumps(m,indent=2)+'\n');print('PRINTED_PIXELS_REFRESHED_GEOMETRY_UNCHANGED',flush=True)
