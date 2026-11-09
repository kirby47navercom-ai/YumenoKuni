"""Whole environment source assembly. Original placements and game data are read-only.

New roof/tree/casework/furniture sources are assembled into all existing runtime
chunks. No content, collision, route, save, UI or engine changes are made here.
"""
import bpy,bmesh,sys,json,math,re,hashlib,subprocess,os
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import v4_rebuilt_environment_kit as K
O=R/'art/space_v4/rebuild_v1';(O/'raw').mkdir(exist_ok=True);(O/'sources').mkdir(exist_ok=True)
P=R/'Game/Saved/sculpted-environment-20261103'
SOURCE=json.loads((R/'art/space_v4/materials_v2/manifest.json').read_text(encoding='utf8'))['assets']
SPECS={s['id']:s for s in json.loads((R/'art/space_v4/full_v2/manifest.json').read_text(encoding='utf8'))['spaces']}

def descendants(o):return [o,*o.children_recursive]
def erase(objects):
    live=[]
    for o in list(objects):
        try:o.name;live.append(o)
        except ReferenceError:pass
    if live:bpy.data.batch_remove(ids=live)
def clean():bpy.ops.wm.read_factory_settings(use_empty=True);K.setup_materials()
def base(o):return re.sub(r'\.\d+$','',o.name)
def freeze(objects):
    graph=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        if o.type!='MESH':continue
        if o.modifiers:o.data=bpy.data.meshes.new_from_object(o.evaluated_get(graph));o.modifiers.clear()
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        zero=[f for f in bm.faces if f.calc_area()<1e-14]
        if zero:bmesh.ops.delete(bm,geom=zero,context='FACES_ONLY')
        bm.to_mesh(o.data);bm.free();o.data.update()
        # BMesh's area accumulator can retain roundoff on exactly collinear
        # float32 coordinates. Use the serialized mesh's own area for this gate.
        zero_indices={p.index for p in o.data.polygons if p.area<1e-14}
        if zero_indices:
            bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i]for i in zero_indices],context='FACES_ONLY');bm.to_mesh(o.data);bm.free();o.data.update()
        if not o.data.uv_layers:
            uv=o.data.uv_layers.new(name='UVMap')
            for face in o.data.polygons:
                axis=max(range(3),key=lambda i:abs(face.normal[i]));axes=[i for i in range(3)if i!=axis]
                for li in face.loop_indices:
                    co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]],co[axes[1]])

def panel_front(o):
    if 'wood_panel'not in K.M:return
    mi=len(o.data.materials);o.data.materials.append(K.M['wood_panel']);bounds=[v.co for v in o.data.vertices];lo=[min(v[i]for v in bounds)for i in range(3)];hi=[max(v[i]for v in bounds)for i in range(3)]
    for face in o.data.polygons:
        if face.normal.y>-.98:continue
        face.material_index=mi
        for li in face.loop_indices:
            c=o.data.vertices[o.data.loops[li].vertex_index].co;o.data.uv_layers[0].data[li].uv=((c.x-lo[0])/max(1e-6,hi[0]-lo[0]),(c.z-lo[2])/max(1e-6,hi[2]-lo[2]))

def replace_props(objects):
    changed=[]
    for old in list(objects):
        try:n=base(old)
        except ReferenceError:continue
        if old.type!='EMPTY':continue
        key=next((k for k in K.BUILDERS if n==k or n.endswith('_'+k)),None)
        if n.startswith('sculpt_street_lamp'):key='street_lamp'
        if not key:continue
        if old.parent and (base(old.parent)==key or base(old.parent).endswith('_'+key)):continue
        original_matrix=[list(v)for v in old.matrix_world];states=[]
        for child in old.children_recursive:
            if child.type=='EMPTY' and any(k in child.name for k in ['hinge','drawer_slide','receiver']):states.append((child.name,child.rotation_euler.copy(),dict(child.items())))
        erase(old.children_recursive);new=K.BUILDERS[key]();new.parent=old
        for name,rotation,extras in states:
            token='hinge'if'hinge'in name else('drawer_slide'if'drawer_slide'in name else'receiver')
            candidates=[o for o in new.children_recursive if o.type=='EMPTY'and token in o.name]
            if candidates:
                candidate=candidates[0];candidate.name=name;candidate.rotation_euler=rotation
                for k,v in extras.items():candidate[k]=v
        for child in new.children_recursive:
            if child.type=='MESH'and any(v in base(child)for v in ['door_leaf','panel_door','drawer_front','cabinet_door']):panel_front(child)
        bpy.context.view_layer.update();assert max(abs(old.matrix_world[i][j]-original_matrix[i][j])for i in range(4)for j in range(4))<1e-6
        changed.append({'root':old.name,'kind':key,'rootTransformUnchanged':True,'statePivotsPreserved':len(states)})
    return changed

def replace_finish(objects):
    replaced=0
    for old in list(objects):
        try:n=base(old)
        except ReferenceError:continue
        if old.type=='EMPTY'and n=='finish_panel':
            inset=next((o for o in old.children_recursive if o.name.startswith('finish_walnut_inset')),None)
            width=inset.dimensions.x if inset else 1.1
            has_lamp=any('finish_sconce' in o.name for o in old.children_recursive)
            erase(old.children_recursive)
            p=K.rounded_solid('single_baked_wall_panel',width,.035,.92,'wood',old,.008,(0,-.025,.57));panel_front(p)
            if has_lamp:s=K.sconce();s.parent=old;s.location=(0,-.035,2.28)
            replaced+=1
        elif old.type=='MESH'and n.startswith(('art_panel_stile_','back_panel_strip','left_panel_strip','right_panel_strip','front_panel_strip','back_inset_edge','left_inset_edge','right_inset_edge','front_inset_edge')):erase([old])
    return replaced

def export(objects,name,runtime,extra=None):
    objects=[o for o in objects if o.name in bpy.data.objects];freeze(objects);meshes=[o for o in objects if o.type=='MESH'];assert meshes,name
    bad=[];triangles=0
    for o in meshes:
        assert o.data.uv_layers,(name,o.name)
        for p in o.data.polygons:
            if len(p.vertices)!=3 or p.area<1e-14:bad.append((o.name,p.index))
            triangles+=len(p.vertices)-2
    assert not bad,(name,bad[:8])
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.hide_render=False;o.hide_set(False);o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0];file=O/'raw'/name
    bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',use_selection=True,export_apply=True,export_tangents=True,export_extras=True)
    result={'file':file.relative_to(R).as_posix(),'runtime':runtime,'triangles':triangles,'meshParts':len(meshes),'rawBytes':file.stat().st_size,**(extra or {})}
    print('REBUILT_CHUNK',name,triangles,len(meshes),flush=True);return result

def roof_kind(ident):
    if any(k in ident for k in ['hotel','guest','reading','archive','record']):return'mansard'
    if any(k in ident for k in ['theatre','dream','performance','exhibition']):return'barrel'
    if any(k in ident for k in ['control','electrical','staff','management','cold','laundry','supply','maintenance']):return'hip'
    return'gable'

def hotel_upper_walls(wing):
    erase([o for o in wing.children if o.name.startswith('continuous_mitred_wall_shell')])
    # Same footprint; actual eight window holes along each long side.
    for side in [-1,1]:
        c=bpy.data.curves.new('upper_wing_pierced_side','CURVE');c.dimensions='2D';c.fill_mode='BOTH';c.extrude=.10;c.resolution_u=1
        def loop(points):
            s=c.splines.new('POLY');s.points.add(len(points)-1)
            for p,(x,z)in zip(s.points,points):p.co=(x,z,0,1)
            s.use_cyclic_u=True
        loop([(-28,0),(28,0),(28,6.4),(-28,6.4)])
        for i in range(8):
            x=-24.5+i*7;loop([(x-.915,4.11),(x-.915,5.49),(x+.915,5.49),(x+.915,4.11)])
        o=bpy.data.objects.new('upper_side_with_window_apertures',c);bpy.context.scene.collection.objects.link(o);o.parent=wing;o.location=(side*9.0,0,0);o.rotation_euler=(math.pi/2,0,side*math.pi/2)
        bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.data.materials.append(K.M['plaster'])
    K.rounded_solid('upper_wing_rear_wall',18.2,.20,6.4,'plaster',wing,.005,(0,27.9,3.2))

def rematerial(objects):
    for o in objects:
        if o.type!='MESH':continue
        for i,m in enumerate(o.data.materials):
            if not m:continue
            if m.name.startswith('identity_'):continue
            if m.name.startswith('rebuilt_'):
                key=re.sub(r'\.\d+$','',m.name)[8:];key='wood_panel'if key=='baked_wood_panel'else key
                if key in K.M:o.data.materials[i]=K.M[key]
                continue
            n=m.name.lower();name=o.name.lower()
            key='wood'if'wood'in n else'cloth'if any(k in n for k in ['rose','cloth']) else'glass'if any(k in n for k in ['mirror','glass']) else'light'if'light'in n else'plaster'if any(k in n for k in ['paper','ivory','white']) else'brass'if any(k in n for k in ['gold','brass']) else'lacquer'if'purple'in n else'iron'
            if 'floor'in name or 'path'in name:key='paving'
            if 'paving'in n or 'walkway'in name:key='paving'
            if 'sage'in n or name=='terrain':key='grass'
            if 'leaf'in n:key='leaf'
            if 'stone'in n:key='stone'
            o.data.materials[i]=K.M[key]

def terrain_aperture(world):
    terrain=next((o for o in world.children_recursive if base(o)=='terrain'),None)
    assert terrain is not None
    inst=next(a for a in json.loads((R/'art/space_v4/full_v2/world_layout.json').read_text(encoding='utf8'))['instances']if a['id']=='pool_edge')
    x,y,_=inst['position_blender'];inverse=terrain.matrix_world.inverted();corners=[inverse@Vector((xx,yy,-.04))for xx,yy in [(x-6.01,y-3.01),(x+6.01,y-3.01),(x+6.01,y+3.01),(x-6.01,y+3.01)]]
    # The global grass ground must have the same real opening as the pool deck.
    # Otherwise it occludes water at -0.45m despite a valid local basin model.
    outer=[(-140,-95),(140,-95),(140,95),(-140,95)];inner=[(v.x,v.y)for v in corners];verts=[(xx,yy,z)for z in [-.2,.2]for ring in [outer,inner]for xx,yy in ring];faces=[]
    for i in range(4):
        k=(i+1)%4;faces.extend([(i+8,k+8,k+12,i+12),(i,i+4,k+4,k),(i,k,k+8,i+8),(i+4,i+12,k+12,k+4)])
    obj=K.mesh('terrain_opening_source',verts,faces,'grass');terrain.data=obj.data;bpy.data.objects.remove(obj,do_unlink=True);terrain['poolOpeningWorldBlender']=[x,y,12.02,6.02];return {'poolOpeningWorldBlender':[x,y,12.02,6.02]}

def exterior():
    reuse='--reuse-rebuilt-trees'in sys.argv
    bpy.ops.wm.open_mainfile(filepath=str(O/'sources/park-rebuilt.blend'if reuse else R/'art/space_v4/sculpted_v1/park-sculpted-source.blend'));K.setup_materials();world=bpy.data.objects['park_exterior_level'];changes=[]
    for inst in json.loads((R/'art/space_v4/full_v2/world_layout.json').read_text(encoding='utf8'))['instances']:
        old=bpy.data.objects.get('facade_'+inst['id'])
        if not old or old.type!='EMPTY':continue
        erase(old.children_recursive);w,d,h=SPECS[inst['asset_id']]['size_m']
        # The corridor is inside the same hotel envelope. A second coplanar
        # mansard roof produced a black strip on the upper wing in source review.
        if inst['id']!='hotel_corridor':new=K.house(w,d,h,roof_kind(inst['id']));new.parent=old
        changes.append({'root':old.name,'kind':'hotel_upper_wing_envelope'if inst['id']=='hotel_corridor'else roof_kind(inst['id']),'sizeMetres':[w,d,h]});print('REBUILT_FACADE',old.name,flush=True)
    trees=[(-20,-24),(20,-24),(-18,8),(20,10),(28,25),(28,42),(58,38),(62,46),(82,46),(124,48),(124,64),(124,88),(88,87),(56,82),(-36,30),(-36,48),(-45,67),(-90,65),(-96,45),(-96,0),(-80,-14),(-60,-15)]
    for o in [v for v in world.children_recursive if v.type=='EMPTY'and base(v)=='rebuilt_hotel_upper_wing']:erase(descendants(o))
    for o in list(world.children_recursive):
        if base(o).startswith(('tree_trunk','tree_branch','ink_leaf_crown','tree_planter','planter_soil','planter_seat','hotel_upper_wing','hotel_upper_roof','upper_room_window')):erase([o])
    if not reuse:
        for i,(x,y)in enumerate(trees):t=K.tree(i);t.parent=world;t.location=(x,y,0)
    wing=K.house(18.2,56,6.4,'mansard');wing.name='rebuilt_hotel_upper_wing';wing.parent=world;wing.location=(-4,58,0)
    hotel_upper_walls(wing)
    # Upper-room windows are recessed framed apertures; not 16 floating colour blocks.
    for side in [-1,1]:
        for i in range(8):
            win=K.window();win.parent=wing;win.location=(side*9.11,-24.5+i*7,4.8);win.rotation_euler.z=side*math.pi/2
    changes+=replace_props(list(world.children_recursive))
    import v4_rebuilt_landmarks as L
    for ident in ['pool_edge','ferris_platform','coaster_platform','park_main_gate']:
        p=bpy.data.objects['exterior_'+ident];erase(p.children_recursive);new=L.build(ident,K);new.parent=p
    rematerial(list(world.children_recursive));terrain_aperture(world);freeze(list(world.children_recursive))
    groups={n:bpy.data.objects['exterior_'+n]for n in ['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']}
    landmarks=set(o for p in groups.values()for o in descendants(p));common=[o for o in world.children_recursive if o not in landmarks]
    bpy.ops.wm.save_as_mainfile(filepath=str(O/'sources/park-rebuilt.blend'),compress=True)
    assets=[export(common,'finish_context.glb','Assets/Art/explore3d/finish_context.glb',{'facadesRebuilt':len(changes),'treesRebuilt':len(trees)})]
    for name,p in groups.items():assets.append(export(descendants(p),'finish_'+name+'.glb','Assets/Art/explore3d/finish_'+name+'.glb'))
    (O/'exterior-assembly.json').write_text(json.dumps({'facades':[a for a in changes if a.get('sizeMetres')],'trees':trees,'replacements':changes,'assets':assets},indent=2)+'\n')

def rooms():
    rows=[];only=next((set(s[7:].split(','))for s in sys.argv if s.startswith('--only=')),None)
    for a in SOURCE:
        ident=Path(a['runtime']).stem
        if ident.startswith('finish_')or(only and ident not in only):continue
        clean();bpy.ops.import_scene.gltf(filepath=str(R/a['file']));changes=replace_props(list(bpy.data.objects));finish=replace_finish(list(bpy.data.objects));objects=list(bpy.data.objects)
        # A single already-joined source still has valid authored structure. Its
        # replacement is supplied by the dedicated whole-level recipe, not decimation.
        if len(objects)==1 and ident in ['coaster_platform','ferris_platform','ferris_cabin','pool_edge','loading_gate','outside_threshold','park_main_gate','ticket_booth','courtroom_stage','trial_podium']:
            import v4_rebuilt_landmarks as L
            erase(objects);obj=L.build(ident,K);objects=descendants(obj);changes.append({'root':ident,'kind':'whole_level_recipe'})
        freeze(objects)
        if ident in ['dining_room','management_office','guest_room','clinic','coaster_platform','courtroom_stage','trial_podium']:
            bpy.ops.wm.save_as_mainfile(filepath=str(O/'sources'/(ident+'.blend')),compress=True)
        row=export(objects,Path(a['file']).name,a['runtime'],{'source':a['file'],'prefabReplacements':changes,'bakedWallPanels':finish});rows.append(row)
    path=O/'room-assembly.json'
    if only and path.exists():rows=[a for a in json.loads(path.read_text())['assets']if Path(a['runtime']).stem not in only]+rows
    path.write_text(json.dumps({'assets':rows},indent=2)+'\n')

if __name__=='__main__':
    mode=next((s[7:]for s in sys.argv if s.startswith('--mode=')),'all')
    if mode in ['all','exterior']:exterior()
    if mode in ['all','rooms']:rooms()
    print('REBUILT_ASSEMBLY_READY',mode,flush=True)
