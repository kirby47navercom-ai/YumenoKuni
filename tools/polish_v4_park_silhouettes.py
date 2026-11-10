"""Remove the redundant draft wheel now that the retained ride is assembled."""
import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
O=R/'art/space_v4/park_levels_v1';bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'));m=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'));root=bpy.data.objects['park_level_starlight'];removed=[]
for obj in list(root.children):
    if not obj.name.startswith(('wheel_real_load','wheel_connected','tensioned_wheel_spoke','wheel_upright_gondola','preserved_outdoor_ferris_cabin')):continue
    removed.append(obj.name)
    for child in reversed([obj,*obj.children_recursive]):bpy.data.objects.remove(child,do_unlink=True)
row=next(a for a in m['levels']if a['id']=='starlight');A.O=O;row['raw']=A.export([root,*root.children_recursive],'starlight.glb','Assets/Art/park_levels/starlight.glb',{'parkDistrict':'starlight','singleRetainedWheel':True});bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True);(O/'raw-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(O/'silhouette-polish.json').write_text(json.dumps({'removedDraftObjects':removed,'retainedOriginalRideAndCabinScene':True},indent=2)+'\n');print('PARK_RIDE_SILHOUETTE_CORRECTED',len(removed),flush=True)
