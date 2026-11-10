"""Replace only reviewed owned facility children, preserving site/nav/story owners."""
import bpy,sys,json,hashlib,shutil
from pathlib import Path
import numpy as np
R=Path.cwd();sys.path.insert(0,str(R/'tools'));O=R/'art/space_v4/park_levels_v1';W=R/'Game/Saved/park-architecture-v6';D=O/'architecture_v6'
# The master is a single mutable authoring file. Keep a process-held lock;
# independent renders may overlap, but integrations must never overlap.
import msvcrt
integrationLock=open(W/'.integration.lock','a+b')
if integrationLock.tell()==0:integrationLock.write(b'0');integrationLock.flush()
integrationLock.seek(0);msvcrt.locking(integrationLock.fileno(),msvcrt.LK_NBLCK,1)
from park_architecture_v6 import architecture_owner,architecture_model,STRUCTURE_SLOTS,structure_slot
ident=next((a.split('=',1)[1]for a in sys.argv if a.startswith('--asset=')),'clinic')
model=architecture_model(ident)
source=D/model/'source.blend'
geometry=json.loads((source.parent/'geometry.json').read_text(encoding='utf8'))
review=json.loads((source.parent/'visual-review.json').read_text(encoding='utf8'))
sourceSHA=hashlib.sha256(source.read_bytes()).hexdigest()
assert geometry['ok']and geometry['sourceSHA256']==review['sourceSHA256']==sourceSHA and not review['visualReviewPending']
backup=R/'삭제 대기/공원건축6_이전_160_20261104';backup.mkdir(exist_ok=True)
for name in ['parks-authoring.blend','raw-manifest.json','manifest.json']:
    if not(backup/name).exists():shutil.copy2(O/name,backup/name)
bpy.ops.wm.open_mainfile(filepath=str(O/'parks-authoring.blend'))
def enable(c):
    c.exclude=False
    for q in c.children:enable(q)
enable(bpy.context.view_layer.layer_collection);bpy.context.view_layer.update()
owner,retired=structure_slot(ident) if ident in STRUCTURE_SLOTS else (architecture_owner(ident),[])
assert owner is not None and owner.type=='EMPTY',('Missing architecture owner',ident)
root=owner
while root and not root.name.startswith('park_level_'):root=root.parent
assert root is not None,'Missing owning park';district=root.name.removeprefix('park_level_')
def outside_digest():
    skip={o.name for o in owner.children_recursive};h=hashlib.sha256();count=0
    skip.update(retiredNames)
    for o in sorted(bpy.context.scene.objects,key=lambda o:o.name):
        if o.name in skip or o.type!='MESH':continue
        h.update(o.name.encode());h.update(np.asarray(o.matrix_world,dtype='<f8').tobytes());count+=1
        for collection,key,dtype,n in [(o.data.vertices,'co','<f4',3),(o.data.loops,'vertex_index','<i4',1),(o.data.polygons,'material_index','<i4',1)]:
            values=np.empty(len(collection)*n,dtype=dtype);collection.foreach_get(key,values);h.update(values.tobytes())
        for uv in o.data.uv_layers:
            values=np.empty(len(uv.data)*2,dtype='<f4');uv.data.foreach_get('uv',values);h.update(values.tobytes())
        h.update(json.dumps([m.name if m else None for m in o.data.materials]).encode())
    return {'sha256':h.hexdigest(),'meshObjects':count}
retiredNames=[o.name for o in retired]
before=outside_digest();old=owner.children_recursive[:]+retired
removed=sum(len(p.vertices)-2 for o in old if o.type=='MESH'for p in o.data.polygons);bpy.data.batch_remove(ids=old)
with bpy.data.libraries.load(str(source),link=False)as(a,b):b.objects=list(a.objects)
collection=owner.users_collection[0]
for o in b.objects:
    if o:collection.objects.link(o);o['_parkSourceCollection']=district
asset=next(o for o in b.objects if o.parent is None);asset.parent=owner;asset.location=(0,0,0)
import build_v4_rebuilt_environment as E
E.freeze([asset,*asset.children_recursive]);bpy.context.view_layer.update();after=outside_digest();assert before==after,('Outside facility geometry or material changed',before,after)
owner['architectureRevision']=6;owner['architectureSource']=source.relative_to(R).as_posix();owner['architectureSourceSHA256']=sourceSHA
raw=json.loads((O/'raw-manifest.json').read_text(encoding='utf8'));row=next(r for r in raw['levels']if r['id']==district);prior=row['raw']['triangles'];flags={k:v for k,v in row['raw'].items()if k in ['textFreePublicArchitecture','themeParkRevision','surfaceDetailRevision','hotelArchitectureRevision','surfaceMaterialRevision','facilityArchitectureRevision','physicalAccessAndContinuingRoad']};flags['facilityArchitectureRevision']=6
E.O=O;E.freeze=lambda objects:None;row['raw']=E.export([root,*root.children_recursive],district+'.glb','Assets/Art/park_levels/'+district+'.glb',flags);assert row['raw']['triangles']==prior-removed+geometry['triangles'],('Unexpected triangle delta',prior,removed,geometry['triangles'],row['raw']['triangles'])
(O/'raw-manifest.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf8');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'parks-authoring.blend'),compress=True)
proof={'ok':True,'id':ident,'district':district,'sourceSHA256':sourceSHA,'outsideExact':before,'removedTriangles':removed,'newTriangles':geometry['triangles'],'navigationAndCaseMetadataChanged':False,'published':False,'scope':'One reviewed asset replaces only owned children. Other source mesh coordinates, UVs and materials are exact.'}
if retiredNames:
    proof.update(retiredStructures=retiredNames,scope='Only the specified old structure meshes and owned children were replaced. Other mesh coordinates, UVs and materials are exact.')
placement=D/ident
placement.mkdir(exist_ok=True)
(placement/'integration.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
manifestFile=D/'manifest.json';manifest=json.loads(manifestFile.read_text(encoding='utf8'))if manifestFile.exists()else{'assets':{}}
manifest['assets'][ident]={'owner':owner.name,'district':district,'source':source.relative_to(R).as_posix(),'sourceSHA256':sourceSHA,'sourceReviewed':True,'runtimeVerified':False}
if asset.get('presentationLights'):
    from mathutils import Vector
    rig=json.loads(asset['presentationLights'])
    for light in rig:
        for key in ['position','target']:
            p=asset.matrix_world@Vector(light[key]);light[key]=[p.x,p.z,-p.y]
    manifest['assets'][ident]['presentationLights']=rig
manifestFile.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('FACILITY_ARCHITECTURE_INTEGRATED',ident,geometry['triangles'],flush=True)
