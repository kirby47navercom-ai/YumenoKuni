"""Blender high-to-low geometry bake, from the corrected material source bank.

Keep node transforms and transparent surfaces. Simplify only dense opaque meshes;
transfer their actual high mesh normals, colour and PBR response to an atlas.
An incremental output is not publishable until every catalog entry is verified.
"""
import bpy, bmesh, json, math, sys, hashlib, time, os
from pathlib import Path
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v4_lowpoly_glb import read as read_glb, write as write_glb, Copier, triangles as glb_triangles, node_keys
OUT = ROOT / 'art/space_v4/lowpoly_v1'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'models').mkdir(exist_ok=True)
CATALOG = json.loads((ROOT / 'art/space_v4/materials_v2/manifest.json').read_text())['assets']
ONLY = set(sys.argv[sys.argv.index('--') + 1:]) if '--' in sys.argv else set()
VERSION = 6
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
CACHE_FILE=OUT/'bake-cache.json'
CACHE=json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
if CACHE.get('version')!=VERSION:CACHE={'version':VERSION,'meshes':{}}


def tris(obj):
    return sum(len(p.vertices)-2 for p in obj.data.polygons)

def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def optical(mat):
    if mat is None:
        return False
    n = mat.name.lower()
    return any(x in n for x in ('glass', 'mirror', 'light', 'scrum_dots', 'scrum_stripes')) or mat.surface_render_method == 'BLENDED'

def filtered(data, keep):
    result = data.copy()
    bm = bmesh.new(); bm.from_mesh(result)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in keep], context='FACES')
    bm.to_mesh(result); bm.free(); result.update()
    return result

def face_subset(data, keep):
    result=data.copy();bm=bmesh.new();bm.from_mesh(result);bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index not in keep],context='FACES')
    bm.to_mesh(result);bm.free();result.update();return result

def simple_components(data):
    # A compiled outdoor chunk also contains large six-face floors/roofs. Keep
    # their original tiled UVs instead of spending the normal atlas on flat land.
    if sum(len(p.vertices)-2 for p in data.polygons)<=10000:return set()
    bm=bmesh.new();bm.from_mesh(data);bm.faces.ensure_lookup_table();tag=bm.faces.layers.int.new('source_face')
    for f in bm.faces:f[tag]=f.index
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
    pending=set(bm.faces);keep=set()
    while pending:
        todo=[pending.pop()];component=[]
        while todo:
            f=todo.pop();component.append(f)
            for edge in f.edges:
                for neighbor in edge.link_faces:
                    if neighbor in pending:pending.remove(neighbor);todo.append(neighbor)
        if sum(len(f.verts)-2 for f in component)<96:keep.update(f[tag] for f in component)
    bm.free();return keep

def simple_beveled_box(obj):
    # These 108-triangle solids are our bevelled panels/trim/cabinet bodies.
    # Keep their full volume as six faces; bake the bevel instead of modelling it.
    if tris(obj)!=108:return False
    bm=bmesh.new();bm.from_mesh(obj.data)
    coords=[v.co for v in bm.verts];lo=[min(v[k] for v in coords) for k in range(3)];hi=[max(v[k] for v in coords) for k in range(3)]
    volume=math.prod(hi[k]-lo[k] for k in range(3));filled=abs(bm.calc_volume());bm.free()
    if volume<1e-10 or filled/volume<.90:return False
    verts=[(x,y,z) for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]]
    mesh=bpy.data.meshes.new('Simple solid with baked bevel');mesh.from_pydata(verts,[],[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]);mesh.update()
    for mat in obj.data.materials:mesh.materials.append(mat)
    obj.data=mesh;return True

def target_material(name, images):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    for key, image in images.items():
        n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.name = key; n.image = image
    return mat

def source_emission(materials, mode):
    for mat in materials:
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree; bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        output = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
        if bs is None or output is None:
            continue
        emit = nt.nodes.get('LP_transfer_emit') or nt.nodes.new('ShaderNodeEmission'); emit.name = 'LP_transfer_emit'
        for link in list(emit.inputs['Color'].links): nt.links.remove(link)
        def socket_to(src, dest):
            if src.is_linked: nt.links.new(src.links[0].from_socket, dest)
            else: dest.default_value = src.default_value
        if mode == 'color':
            socket_to(bs.inputs['Base Color'], emit.inputs['Color'])
        elif mode == 'orm':
            comb = nt.nodes.get('LP_transfer_orm') or nt.nodes.new('ShaderNodeCombineColor'); comb.name = 'LP_transfer_orm'; comb.mode = 'RGB'
            comb.inputs['Red'].default_value = 1
            socket_to(bs.inputs['Roughness'], comb.inputs['Green'])
            socket_to(bs.inputs['Metallic'], comb.inputs['Blue'])
            nt.links.new(comb.outputs[0], emit.inputs['Color'])
        else:
            socket_to(bs.inputs['Emission Color'], emit.inputs['Color'])
            emit.inputs['Strength'].default_value = bs.inputs['Emission Strength'].default_value
        if mode != 'emission': emit.inputs['Strength'].default_value = 1
        nt.links.new(emit.outputs[0], output.inputs['Surface'])

def restore_surface(materials):
    for mat in materials:
        if mat and mat.use_nodes:
            nt=mat.node_tree; bs=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
            output=next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None)
            if bs and output: nt.links.new(bs.outputs['BSDF'],output.inputs['Surface'])

def build(row):
    source=Path(os.environ.get('V4_LOWPOLY_SOURCE',str(ROOT/row['file']))); dest=OUT/'models'/Path(row['file']).name
    receipt=OUT/(Path(row['file']).stem+'.json'); digest=sha(source)
    if receipt.exists() and dest.exists():
        prev=json.loads(receipt.read_text())
        if prev.get('version')==VERSION and prev.get('sourceSHA256')==digest and prev.get('sha256')==sha(dest):
            print('LP_REUSE', dest.name, flush=True); return prev
    start=time.monotonic(); bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.device='CPU'
    scene.cycles.samples=1; scene.render.threads_mode='FIXED'; scene.render.threads=6
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        available=[d for d in prefs.devices if d.type=='OPTIX']
        if available:
            for d in prefs.devices:d.use=d.type=='OPTIX'
            scene.cycles.device='GPU'
        print('LP_DEVICE',scene.cycles.device,[d.name for d in available],flush=True)
    except Exception as error:print('LP_DEVICE_CPU',str(error),flush=True)
    scene.render.bake.use_selected_to_active=True; scene.render.bake.use_clear=True
    scene.render.bake.margin=8; scene.render.bake.cage_extrusion=.035
    scene.render.bake.max_ray_distance=.07
    hj,hb=read_glb(source);nodekey=node_keys(hj,hb);first={};masked=json.loads(json.dumps(hj));candidates={}
    for old,n in zip(hj['nodes'],masked['nodes']):
        if 'mesh'not in old:continue
        key=nodekey[old['name']]
        if glb_triangles(hj,old['mesh'])<96 or key in CACHE['meshes'] or key in first:n.pop('mesh')
        else:first[key]=old['name'];candidates[old['name']]=key
    scratch=OUT/'source-for-bake.glb';write_glb(scratch,masked,hb)
    bpy.ops.import_scene.gltf(filepath=str(scratch))
    original=list(scene.objects); original_mesh=[o for o in original if o.type=='MESH']
    before=sum(tris(o) for o in original_mesh)
    roots={o.name:list(sum((list(v) for v in o.matrix_local),[])) for o in original}
    originals_materials=set(m for o in original_mesh for m in o.data.materials if m)
    pairs=[]; highs=[]; lows=[]; changed=[]
    for obj in original_mesh:
        if tris(obj)<96: continue
        opaque={i for i,m in enumerate(obj.data.materials) if not optical(m)}
        if not opaque: continue
        high_data=filtered(obj.data,opaque)
        if len(high_data.polygons)<32:
            bpy.data.meshes.remove(high_data); continue
        passthrough=simple_components(high_data)
        if passthrough:
            retained=bpy.data.objects.new(obj.name+'_preserved',face_subset(high_data,passthrough));scene.collection.objects.link(retained);retained.parent=obj;retained.matrix_parent_inverse=Matrix.Identity(4);retained.matrix_basis=Matrix.Identity(4)
            high_data=face_subset(high_data,set(range(len(high_data.polygons)))-passthrough)
            if len(high_data.polygons)<32:
                bpy.data.objects.remove(retained,do_unlink=True);continue
        high=bpy.data.objects.new('HP_'+obj.name,high_data); scene.collection.objects.link(high); high.matrix_world=obj.matrix_world.copy()
        low=bpy.data.objects.new('LP_'+obj.name,high_data.copy()); scene.collection.objects.link(low); low.matrix_world=obj.matrix_world.copy()
        activate(low)
        # Weld importer seam duplicates before reduction; the atlas replaces UVs.
        bm=bmesh.new();bm.from_mesh(low.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
        bm.to_mesh(low.data);bm.free()
        count=tris(low)
        boxed=simple_beveled_box(low)
        if not boxed:
            planar=low.modifiers.new('Remove coplanar subdivisions','DECIMATE');planar.decimate_type='DISSOLVE';planar.angle_limit=math.radians(.3);planar.delimit={'MATERIAL','NORMAL'}
            bpy.ops.object.modifier_apply(modifier=planar.name)
        if not boxed and tris(low)>96:
            dec=low.modifiers.new('Simple silhouette','DECIMATE');dec.ratio=.34 if count>1000 else .50
            dec.use_collapse_triangulate=True;dec.delimit={'MATERIAL'}
            bpy.ops.object.modifier_apply(modifier=dec.name)
        triangulate=low.modifiers.new('Frozen bake triangulation','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=triangulate.name)
        if tris(low)>=count*.92:
            bpy.data.objects.remove(low,do_unlink=True);bpy.data.objects.remove(high,do_unlink=True)
            if passthrough:bpy.data.objects.remove(retained,do_unlink=True)
            continue
        # Original transparent polygons remain separate children in the same pose.
        optical_indices=set(range(len(obj.data.materials)))-opaque
        if optical_indices:
            glass=bpy.data.objects.new(obj.name+'_optical',filtered(obj.data,optical_indices));scene.collection.objects.link(glass);glass.parent=obj;glass.matrix_parent_inverse=Matrix.Identity(4);glass.matrix_basis=Matrix.Identity(4)
        obj.hide_render=True
        pairs.append((obj,low));highs.append(high);lows.append(low)
        changed.append({'node':obj.name,'beforeOpaqueTriangles':count,'afterOpaqueTriangles':tris(low),'method':'six-face solid with baked bevel' if boxed else 'silhouette reduction with high-mesh normal bake'})
    if lows:
        # Atlas is sized by actual replaced mesh surface area, not the room label.
        size=int(os.environ.get('V4_BAKE_SIZE',0)) or (4096 if sum(tris(h) for h in highs)>150000 else 2048)
        images={key:bpy.data.images.new('baked_'+key,width=size,height=size,alpha=False) for key in ['normal','color','orm','emission']}
        for key,im in images.items(): im.colorspace_settings.name='sRGB' if key in ['color','emission'] else 'Non-Color'
        tags={}; mats=[];bake_mat=target_material('LP_single_bake_target',images)
        for i,(obj,low) in enumerate(pairs):
            mat=bpy.data.materials.new('LP_target_'+str(i));tags[mat.name]=obj;mats.append(mat)
            low.data.materials.clear();low.data.materials.append(bake_mat)
            for poly in low.data.polygons: poly.material_index=0
            owner=low.data.attributes.new('lp_owner','INT','FACE')
            for face in owner.data:face.value=i
        bpy.ops.object.select_all(action='DESELECT')
        for low in lows: low.select_set(True)
        bpy.context.view_layer.objects.active=lows[0];bpy.ops.object.join();joined=bpy.context.object
        while len(joined.data.uv_layers)>1: joined.data.uv_layers.remove(joined.data.uv_layers[-1])
        activate(joined);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,area_weight=.2,correct_aspect=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        # Retire old UVs so glTF TEXCOORD_0 is precisely the baked tangent basis.
        joined.data.uv_layers[0].active_render=True
        for h in highs: h.select_set(True)
        joined.select_set(True);bpy.context.view_layer.objects.active=joined
        for mode,kind in [('normal','NORMAL'),('color','EMIT'),('orm','EMIT'),('emission','EMIT')]:
            if mode=='normal': restore_surface(originals_materials)
            else: source_emission(originals_materials,mode)
            bake_mat.node_tree.nodes.active=bake_mat.node_tree.nodes[mode]
            print('LP_BAKE',dest.name,mode,size,flush=True)
            bpy.ops.object.bake(type=kind)
        restore_surface(originals_materials)
        # Split by temporary object tags; maintain every original node and pivot.
        joined.data.materials.clear()
        for mat in mats:joined.data.materials.append(mat)
        for poly,owner in zip(joined.data.polygons,joined.data.attributes['lp_owner'].data):poly.material_index=owner.value
        activate(joined);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.separate(type='MATERIAL');bpy.ops.object.mode_set(mode='OBJECT')
        separated=list(bpy.context.selected_objects)
        material=bpy.data.materials.new('HighMesh_baked_to_simple_mesh');material.use_nodes=True
        nt=material.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
        nodes={}
        for key,im in images.items():
            tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nodes[key]=tex;im.pack()
        nt.links.new(nodes['color'].outputs['Color'],bs.inputs['Base Color'])
        normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nodes['normal'].outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs[0],bs.inputs['Normal'])
        separate=nt.nodes.new('ShaderNodeSeparateColor');separate.mode='RGB';nt.links.new(nodes['orm'].outputs['Color'],separate.inputs[0]);nt.links.new(separate.outputs['Green'],bs.inputs['Roughness']);nt.links.new(separate.outputs['Blue'],bs.inputs['Metallic'])
        nt.links.new(nodes['emission'].outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1
        for low in separated:
            obj=tags[low.data.materials[low.data.polygons[0].material_index].name]
            data=low.data.copy();data.transform(obj.matrix_world.inverted()@low.matrix_world)
            data.materials.clear();data.materials.append(material)
            for poly in data.polygons: poly.material_index=0
            obj.data=data;obj.hide_render=False
            bpy.data.objects.remove(low,do_unlink=True)
        for h in highs:bpy.data.objects.remove(h,do_unlink=True)
        assert len(separated)==len(pairs),(len(separated),len(pairs))
    after=sum(tris(o) for o in scene.objects if o.type=='MESH')
    assert after<=before,(before,after)
    for obj in original:
        assert roots[obj.name]==list(sum((list(v) for v in obj.matrix_local),[])),obj.name
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_tangents=True,export_image_format='AUTO',export_cameras=False,export_lights=False)
    # Graft only changed opaque meshes and their optical children. Everything
    # else retains its exact source accessors, material slots and node graph.
    lj,lb=read_glb(dest);copier=Copier(hj)
    lookup={n.get('name'):n for n in lj['nodes']};changed_names={r['node'] for r in changed}
    local={candidates[name]:name for name in changed_names};libraries={};all_changes=[]
    for node in list(copier.j['nodes']):
        if 'mesh' not in node:continue
        key=nodekey[node['name']];binding=CACHE['meshes'].get(key);use_name=local.get(key)
        if use_name or binding and not binding.get('unchanged'):
            if use_name:sj,sb,sn,token=lj,lb,lookup[use_name],'low'
            else:
                lib=ROOT/binding['file']
                if str(lib)not in libraries:
                    assert sha(lib)==binding['sha256'],lib
                    sj,sb=read_glb(lib);libraries[str(lib)]=(sj,sb,{n.get('name'):n for n in sj['nodes']})
                sj,sb,libnames=libraries[str(lib)];sn=libnames[binding['node']];token=str(lib)
            node['mesh']=copier.copy(sj,sb,'meshes',sn['mesh'],token)
            children=[sj['nodes'][c] for c in sn.get('children',[]) if any(sj['nodes'][c].get('name','').startswith(sn['name']+suffix) for suffix in ['_optical','_preserved'])]
            for child in children:
                import copy
                child=copy.deepcopy(child);child['name']=node['name']+child['name'][len(sn['name']):];child['mesh']=copier.copy(sj,sb,'meshes',child['mesh'],token);node.setdefault('children',[]).append(len(copier.j['nodes']));copier.j['nodes'].append(child)
            previous=next((r for r in changed if r['node']==use_name),None) if use_name else binding['change']
            all_changes.append({**previous,'node':node['name'],'sharedBakePrototype':use_name or binding['node']})
        else:node['mesh']=copier.copy(hj,hb,'meshes',node['mesh'],'high')
    # All texture compression is lossless, including tangent-space normals.
    write_glb(dest,copier.j,bytes(copier.b),limit=False)
    import subprocess
    subprocess.run([os.environ.get('V4_PACK_PYTHON','C:/python/python.exe'),str(ROOT/'tools/compress_v4_bake.py'),str(dest)],check=True)
    assert dest.stat().st_size<64*1024*1024,(dest,dest.stat().st_size)
    fj,fb=read_glb(dest);before=sum(glb_triangles(hj,n['mesh']) for n in hj['nodes'] if 'mesh'in n);after=sum(glb_triangles(fj,n['mesh']) for n in fj['nodes'] if 'mesh'in n)
    result={'version':VERSION,'file':dest.relative_to(ROOT).as_posix(),'runtime':row['runtime'],'source':row['file'],'sourceSHA256':digest,'sha256':sha(dest),'bytes':dest.stat().st_size,'beforeTriangles':before,'afterTriangles':after,'changedMeshes':all_changes,'bakeType':'Cycles selected-to-active tangent NORMAL and source colour/roughness/metallic/emission, from actual high mesh; identical mesh/material/scale metrics reuse a prototype','atlasSize':size if lows else 0,'seconds':time.monotonic()-start,'originalNodesPreserved':len(hj['nodes']),'originalNodeTransformsUnchanged':True}
    for key,name in first.items():
        change=next((c for c in all_changes if c['node']==name),None)
        CACHE['meshes'][key]={'file':result['file'],'sha256':result['sha256'],'node':name,'change':change} if change else {'unchanged':True}
    CACHE_FILE.write_text(json.dumps(CACHE,indent=2)+'\n')
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    print('LP_DONE',json.dumps({k:result[k] for k in ['runtime','beforeTriangles','afterTriangles','bytes','seconds']}),flush=True)
    return result

results=[]
for row in CATALOG:
    if ONLY and Path(row['runtime']).stem not in ONLY:continue
    results.append(build(row))
if not ONLY:
    assert len(results)==len(CATALOG)
    manifest={'version':VERSION,'complete':True,'sourceManifestSHA256':sha(ROOT/'art/space_v4/materials_v2/manifest.json'),'assets':results,'beforeTriangles':sum(r['beforeTriangles'] for r in results),'afterTriangles':sum(r['afterTriangles'] for r in results)}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('LP_FINISHED',len(results),flush=True)
