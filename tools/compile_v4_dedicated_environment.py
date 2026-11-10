"""Lossless GLB compaction retaining node names used by authored prop states."""
from pathlib import Path
import json,sys,re,copy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from v4_lowpoly_glb import read,write,digest,array,Copier
from optimize_native_glb import repack
import compile_v4_rebuilt_environment as C
O=R/'art/space_v4/rebuilt_dedicated_v2';(O/'models').mkdir(exist_ok=True);assets=[]
for row in json.loads((O/'assembly.json').read_text())['assets']:
    source=R/row['file'];j,b=read(source)
    for m in j.get('materials',[]):
        tint=m.get('extras',{}).get('surfaceTint')
        if tint:m.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=tint
        name=re.sub(r'\.\d+$','',m.get('name',''))
        for key,color in [('rebuilt_iron',[.05,.06,.08,1]),('rebuilt_brass',[.55,.35,.12,1]),('rebuilt_wood',[.8,.8,.8,1])]:
            if name==key:m.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=color
    for s in j.get('samplers',[]):s.update(magFilter=9729,minFilter=9987)
    prefixes=['can_0_','can_1_','can_2_','can_metal_rim','soft_throw_ball','toy_goldfish_','toy_eye','toy_display_mount','toy_car_','plain_closed_game_box','blank_drawing_mount','folded_shared_towel','current_side_door_hinge','garden_glass_door_hinge']
    protected={i for i,n in enumerate(j['nodes'])if any(n.get('name','').startswith(p)for p in prefixes)}
    def include_children(i):
        for child in j['nodes'][i].get('children',[]):protected.add(child);include_children(child)
    for i in list(protected):include_children(i)
    # Batch static surfaces by exact optical material, but retain independently
    # visible cans, toys, cloth and hinged doors with their original transforms.
    previous=C.O;C.O=O/'static';(C.O/'models').mkdir(parents=True,exist_ok=True)
    try:static=C.compile(row,omit_mesh_nodes=protected)
    finally:C.O=previous
    sj,sb=read(R/static['file']);c=Copier(sj);c.j['nodes']=copy.deepcopy(sj['nodes']);c.j['nodes'][0]['mesh']=c.copy(sj,sb,'meshes',sj['nodes'][0]['mesh'],'static');offset=len(c.j['nodes'])
    for i,n in enumerate(j['nodes']):
        node=copy.deepcopy(n)
        if 'mesh'in node:
            if i in protected:node['mesh']=c.copy(j,b,'meshes',node['mesh'],'state')
            else:node.pop('mesh')
        if 'children'in node:node['children']=[x+offset for x in node['children']]
        c.j['nodes'].append(node)
    c.j['scenes']=[{'nodes':[0,*[i+offset for i in j['scenes'][j.get('scene',0)]['nodes']]]}];c.j['scene']=0
    file=O/'models'/source.name;data=write(file,c.j,bytes(c.b),limit=False)
    if any(im.get('mimeType')=='image/png'for im in c.j.get('images',[])):packed,proof=repack(data)
    else:packed=data;proof={'textures':[],'sceneGeometryMaterialsSamplersUnchanged':True}
    file.write_bytes(packed);jj,bb=read(file);assert [n.get('name')for n in jj['nodes'][offset:]]==[n.get('name')for n in j['nodes']]
    triangles=lambda spec,blob:sum(len(array(spec,blob,p['indices']))//3 for n in spec['nodes']if'mesh'in n for p in spec['meshes'][n['mesh']]['primitives'])
    tris=triangles(jj,bb);assert tris==triangles(j,b)
    assets.append({**row,'source':row['file'],'sourceSHA256':digest(source.read_bytes()),'file':file.relative_to(R).as_posix(),'sha256':digest(packed),'bytes':len(packed),'triangles':tris,'imageProof':proof,'staticImageProofs':static['losslessImageProofs'],'nodeGraphPreserved':True,'staticMaterialGroups':static['materialPrimitives'],'protectedMeshNodes':sum('mesh'in j['nodes'][i]for i in protected),'sourceMeshNodes':sum('mesh'in n for n in j['nodes'])})
(O/'manifest.json').write_text(json.dumps({'assets':assets,'count':6,'worldMetadataChanged':False},indent=2)+'\n');print('DEDICATED_COMPACTED',len(assets))
