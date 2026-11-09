"""Blender background compiler: reuse the authored finished park around local playable rooms."""
import bpy,json,hashlib,os,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];refine_architecture=os.environ.get('V4_EXTERIOR_ARCHITECTURE')=='1';O=R/('art/space_v4/architecture_finish_v2' if refine_architecture else 'art/space_v4/outdoor_finish_v1');O.mkdir(exist_ok=True)
S=R/'art/space_v4/full_v2';source=S/'park_exterior_r2_source.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));world=bpy.data.objects['park_exterior_level']
architecture=None
if refine_architecture:
 sys.path.insert(0,str(R/'tools'))
 from refine_v4_exterior_architecture import refine
 layout=json.loads((S/'world_layout.json').read_text(encoding='utf8'))
 specs={row['id']:row for row in json.loads((S/'manifest.json').read_text(encoding='utf8'))['spaces']}
 architecture=refine(world,layout,specs)
names=['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']
groups={n:bpy.data.objects['exterior_'+n] for n in names}
landmarks={n:set([g]+list(g.children_recursive)) for n,g in groups.items()}
all_landmarks=set().union(*landmarks.values())
common=[o for o in world.children_recursive if o.type=='MESH' and o not in all_landmarks]
result={'source':source.relative_to(R).as_posix(),'policy':'Reuse original own finished park with source world transforms. Shared context and six replaceable landmarks; current local interactive set remains the evidence/collision owner. No V3 extraction or engine edits.','context':{},'landmarks':{},'local':{}}
if architecture:result['architecture']=architecture
def export(objects,name):
 objects=[o for o in objects if o.type=='MESH'];assert objects,name
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.hide_set(False);o.hide_render=False;o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();joined=bpy.context.object
 # Bake world transforms so every exported context chunk shares the source world origin.
 matrix=joined.matrix_world.copy();joined.parent=None;joined.matrix_world=matrix
 if joined.data.users>1:joined.data=joined.data.copy()
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 joined.name='Runtime_'+name;path=O/(name+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_extras=False)
 vertices=len(joined.data.vertices);materials=len(joined.data.materials)
 bpy.data.objects.remove(joined,do_unlink=True)
 return {'file':path.relative_to(R).as_posix(),'runtime':'Assets/Art/explore3d/finish_'+name+'.glb','vertices':vertices,'material_slots':materials,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
result['context']=export(common,'context')
if refine_architecture:
 # The facade additions all belong to the shared context. Reuse unchanged
 # landmarks/local interactive sets rather than export duplicate large files.
 previous=json.loads((R/'art/space_v4/outdoor_finish_v1/manifest.json').read_text(encoding='utf8'))
 result['landmarks']=previous['landmarks'];result['local']=previous['local']
else:
 for name,objects in landmarks.items():result['landmarks'][name]=export(list(objects),name)
# Keep local target geometry and coordinates, replacing only the broad untextured base ground.
manifest=json.loads((S/'manifest.json').read_text(encoding='utf-8'))
reactive=R/'art/space_v4/reactions_v1/manifest.json'
replaced=set(json.loads(reactive.read_text(encoding='utf-8'))['spaces']) if reactive.exists() else set()
outdoor={'plaza','park_garden','park_main_gate','ticket_booth','pool_edge','ferris_platform','ferris_cabin','coaster_platform','loading_gate','outside_threshold'}
paving=bpy.data.materials.get('yk_paving') or bpy.data.materials.get('paving')
sage=bpy.data.materials.get('yk_sage') or bpy.data.materials.get('sage');assert paving and sage
for spec in ([] if refine_architecture else manifest['spaces']):
 sid=spec['id']
 if sid not in outdoor or sid in replaced:continue
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(R/spec['file']));objects=list(set(bpy.data.objects)-before)
 changed=[];w,d,_=spec['size_m']
 for obj in objects:
  if obj.type!='MESH':continue
  if obj.dimensions.x>w*.8 and obj.dimensions.y>d*.8 and obj.dimensions.z<.5:
   for i,mat in enumerate(obj.data.materials):
    if mat and mat.name.split('.')[0]=='yk_ink':obj.data.materials[i]=sage if sid=='park_garden' else paving;changed.append(obj.name)
 result['local'][sid]=export(objects,'local_'+sid);result['local'][sid]['changed_ground_nodes']=changed
 for obj in objects:
  try:name=obj.name
  except ReferenceError:continue
  if name in bpy.data.objects:bpy.data.objects.remove(obj,do_unlink=True)
(O/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('EXTERIOR_CONTEXT_READY '+json.dumps({'landmarks':len(result['landmarks']),'local_sets':len(result['local']),'bytes':sum(x['bytes'] for x in [result['context'],*result['landmarks'].values(),*result['local'].values()])}),flush=True)
