"""Replace the remaining outside facade proxy and expose no road endpoint."""
import bpy,json,math,sys,random
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
import build_v4_rebuilt_environment as A
from v4_park_continuity import distant_tree
O=R/'art/space_v4/park_levels_v1';W=R/'Game/Saved/park-levels-20261104/public-space-finish'
bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'));K.setup_materials()
for key in ['cream','blue','gold','teal']:
    candidates=[m for m in bpy.data.materials if m.name.startswith('park_'+key)]
    if candidates:K.M[key]=candidates[0]
root=bpy.data.objects['park_level_perimeter'];removed=[]
for o in list(root.children):
    if o.name.startswith(('parkcopy_facade_outside_threshold','preserved_outdoor_outside_threshold','continuing_service_road','perimeter_actual_access')):
        removed.append(o.name)
        for child in [*reversed(o.children_recursive),o]:bpy.data.objects.remove(child,do_unlink=True)
finish=K.root('perimeter_actual_access',root)
# A through route, shaped protective gateway and an off-axis service lodge.
# There is no new destination, event, evidence text or changed scene exit.
for x in [-3.9,3.9]:
    K.section('service_gateway_tapered_pier',[(-.42,0),(.42,0),(.36,3.6),(.25,4.4),(-.25,4.4),(-.36,3.6)],.65,'stone',finish).location=(x,7,0)
roof=K.section('fitted_service_gateway_roof',[(-1.6,4.25),(1.6,4.25),(1.72,4.42),(0,5.25),(-1.72,4.42)],9.2,'teal',finish);roof.location=(0,7,0)
for x in [-3.9,3.9]:K.tube('gate_roof_connection',[(x,7,3.5),(x,7,4.6)],[.14,.11],'iron',finish,8)
lodge=K.root('actual_service_lodge',finish);lodge.location=(-7,7,0)
# Single wall shell with real door/window apertures, curved fascia and deep roof.
K.rounded_solid('service_lodge_floor',4.8,4.0,.18,'stone',lodge,.08,(0,0,.09))
for y in [-1.9,1.9]:
    K.rounded_solid('service_lodge_end_wall',4.6,.16,2.9,'cream',lodge,.035,(0,y,1.55))
K.rounded_solid('service_lodge_back_wall',.16,3.8,2.9,'cream',lodge,.035,(-2.2,0,1.55))
# Road-facing wall: low sill and lintel frame a real recessed service window.
for z,h in [(.53,.9),(2.7,.6)]:K.rounded_solid('service_window_sill_and_lintel',.16,3.65,h,'cream',lodge,.025,(2.2,0,z))
for y in [-1.75,1.75]:K.rounded_solid('service_window_jamb',.22,.22,1.45,'stone',lodge,.025,(2.2,y,1.65))
K.rounded_solid('recessed_service_window',.07,3.25,1.3,'glass',lodge,.02,(2.12,0,1.65))
K.tube('service_window_mullion',[(2.24,0,1.0),(2.24,0,2.30)],[.035,.035],'iron',lodge,6)
K.section('lodge_fitted_pitched_roof',[(-2.28,2.95),(2.28,2.95),(2.45,3.12),(0,3.95),(-2.45,3.12)],5.35,'teal',lodge)
K.rounded_solid('service_lodge_recessed_door',1.05,.07,2.25,'blue',lodge,.025,(0,-2.01,1.25))
K.tube('service_lodge_door_handle',[(.32,-2.07,1.04),(.32,-2.07,1.46)],[.025,.025],'gold',lodge,6)
# Smooth road bend continues behind the first terrain/tree belt. Project its
# entire ribbon onto the same authored radial terrain, not through the hill.
control=[(0,-40),(0,-10),(0,18),(5,35),(16,50),(28,60),(32,82),(26,108),(10,132),(-15,155),(-32,189),(-28,245),(0,300),(50,380),(90,470)]
points=[]
for i in range(len(control)-1):
    a,b,c,d=[Vector(control[max(0,min(len(control)-1,j))])for j in [i-1,i,i+1,i+2]]
    for k in range(max(3,math.ceil((c-b).length/1.8))):
        t=k/max(3,math.ceil((c-b).length/1.8));points.append((b*2+(c-a)*t+(a*2-b*5+c*4-d)*t*t+(-a+b*3-c*3+d)*t*t*t)*.5)
points.append(Vector(control[-1]))
rings=[(110,-.05),(150,.1),(225,7),(340,18),(500,28),(800,20),(1300,35),(1900,22)]
def height(p):
    r=p.length;a=math.atan2(p.y,p.x)
    if r<110:return -.04
    for k in range(len(rings)-1):
        lo,h0=rings[k];hi,h1=rings[k+1]
        if lo<=r<=hi:
            t=(r-lo)/(hi-lo);return (1-t)*h0*(.7+.2*math.sin(a*3+k*.12))+t*h1*(.7+.2*math.sin(a*3+(k+1)*.12))
    return 20
edges=[]
for i,p in enumerate(points):
    tangent=points[min(i+1,len(points)-1)]-points[max(0,i-1)];normal=Vector((-tangent.y,tangent.x));normal.normalize();edges.append([p-normal*3,p+normal*3])
vertices=[(p.x,p.y,height(p)+.075)for pair in edges for p in pair]
K.mesh('curved_continuing_service_road',vertices,[(2*i,2*i+1,2*i+3,2*i+2)for i in range(len(edges)-1)],'paving',finish,uv_scale=.3)
for side in [0,1]:
    line=[(pair[side].x,pair[side].y,height(pair[side])+.12)for pair in edges];K.tube('service_road_fitted_coping',line,[.055]*len(line),'stone',finish,6)
rng=random.Random(261104)
for k in range(100):
    angle=rng.uniform(0,math.tau);radius=rng.uniform(70,145);p=Vector((radius*math.cos(angle),radius*math.sin(angle)))
    if min((p-q).length for q in points)<8:continue
    tree=distant_tree(finish,p.x,p.y,990000+k);tree.location.z=height(p);tree.scale=(1.1,1.1,1.35)
manifest=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'));row=next(a for a in manifest['levels']if a['id']=='perimeter')
row.setdefault('publicSpaceBaseCollision',row['collision']);row['collision']=[*row['publicSpaceBaseCollision'],[-9.5,-9.1,-4.5,-4.9,0,4.0],[-4.25,-7.5,-3.55,-6.5,0,4.5],[3.55,-7.5,4.25,-6.5,0,4.5]]
__import__('park_architecture_v6').restore_reviewed(root,'perimeter')
A.O=O;bpy.context.view_layer.update();flags={'parkDistrict':'perimeter','physicalAccessAndContinuingRoad':True}
if lodge.get('architectureRevision')==6:flags['facilityArchitectureRevision']=6
row['raw']=A.export([root,*root.children_recursive],'perimeter.glb','Assets/Art/park_levels/perimeter.glb',flags)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True)
(O/'raw-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(W/'perimeter.json').write_text(json.dumps({'removed':removed,'roadSamples':len(points),'sourceObject':finish.name,'noNewStoryOrExit':True,'runtimeVerified':False},ensure_ascii=False,indent=2),encoding='utf8');print('PERIMETER_PROXY_REPLACED',removed,flush=True)
