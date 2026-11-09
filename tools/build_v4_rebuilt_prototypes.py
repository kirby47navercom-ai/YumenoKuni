"""Export and independently check the new whole-environment prefab recipes."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
O=R/'art/space_v4/rebuild_v1';(O/'prototypes').mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);K.setup_materials();records=[]
for ident,builder in K.BUILDERS.items():
    obj=builder();parts=[obj,*obj.children_recursive];bpy.context.view_layer.update();verts=[];triangles=0
    for part in parts:
        if part.type!='MESH':continue
        assert part.data.uv_layers,part.name
        assert len(part.data.polygons)>0,part.name
        for vertex in part.data.vertices:
            assert all(math.isfinite(v) for v in vertex.co),part.name;verts.append(part.matrix_world@vertex.co)
        for polygon in part.data.polygons:
            assert polygon.area>1e-12,(ident,part.name,polygon.index,polygon.area)
            assert len(polygon.vertices)==3,(ident,part.name,'freeze triangulation')
            triangles+=1
    bounds=[[min(v[k]for v in verts)for k in range(3)],[max(v[k]for v in verts)for k in range(3)]]
    bpy.ops.object.select_all(action='DESELECT')
    for part in parts:part.select_set(True)
    bpy.context.view_layer.objects.active=obj;file=O/'prototypes'/(ident+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',use_selection=True,export_tangents=True,export_extras=True)
    records.append({'id':ident,'file':file.relative_to(R).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'bytes':file.stat().st_size,'triangles':triangles,'meshParts':sum(o.type=='MESH'for o in parts),'boundsBlender':bounds,'authoredVolumeAndCavities':True,'runtimeIntegrated':False})
    print('REBUILT_PREFAB',ident,triangles,file.stat().st_size,flush=True)
    for part in reversed(parts):bpy.data.objects.remove(part,do_unlink=True)
(O/'prefab-manifest.json').write_text(json.dumps({'completeEnvironment':False,'scope':'Individually authored and geometry-checked replacement prefab sources. Full environment assembly/runtime acceptance remains separate.','assets':records},indent=2)+'\n')
print('REBUILT_PREFABS_READY',len(records),flush=True)
