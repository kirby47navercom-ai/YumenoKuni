"""Join the actual handrails to the upper balustrade; preserve all other art."""
import bpy,sys,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
import build_v4_rebuilt_environment as A
from v4_park_access_geometry import observatory
O=R/'art/space_v4/park_levels_v1';bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'));root=bpy.data.objects['park_level_mirrors']
K.M['gold']=next(m for m in bpy.data.materials if m.name.startswith('park_gold'))
for angle,y in [(2*math.tau/48,4.55),(47*math.tau/48,2.45)]:
    x0,y0=14+6.45*math.cos(angle),3.5+6.45*math.sin(angle)
    K.tube('connected_landing_handrail',[(x0,y0,6.9),(20.4,y,6.85)],[.05,.05],'gold',root,8)
    K.tube('landing_handrail_support',[(20.4,y,5.85),(20.4,y,6.85)],[.04,.04],'gold',root,8)
m=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'));a=next(a for a in m['levels']if a['id']=='mirrors');assert len(a['collision'])==115;a['collision']=a['collision'][:6];observatory(a['collision'],a['walkSurfaces']);A.O=O;a['raw']=A.export([root,*root.children_recursive],'mirrors.glb','Assets/Art/park_levels/mirrors.glb',{'parkDistrict':'mirrors','continuousLandingAndRailing':True});bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True);(O/'raw-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('OBSERVATORY_LANDING_CONNECTED',flush=True)
