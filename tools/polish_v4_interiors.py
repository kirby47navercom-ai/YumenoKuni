"""Non-blocking wall/ceiling art detail for original interiors; preserve case geometry."""
import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SPACE=ROOT/'art/space_v4/full_v2';OUT=SPACE/'interior_art_r3';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SPACE/'space_kit_source.blend'));scene=bpy.context.scene
manifest=json.loads((SPACE/'manifest.json').read_text(encoding='utf8'));M={k:bpy.data.materials['yk_'+k] for k in ['ink','wood','gold','paper','rose','ivory']}
def box(name,loc,size,mat,parent):
    x,y,z=[v/2 for v in size];mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update()
    layer=mesh.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        axes=[i for i in range(3) if i!=max(range(3),key=lambda k:abs(p.normal[k]))]
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;layer.data[li].uv=(v[axes[0]]/2,v[axes[1]]/2)
    o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o);o.parent=parent;o.location=loc;o.data.materials.append(M[mat]);o.hide_render=True;return o
outdoor={'plaza','park_garden','pool_edge','ferris_platform','ferris_cabin','coaster_platform','park_main_gate','loading_gate','outside_threshold','lower_stairway','courtroom','inspection_hall_normal','inspection_hall_changed','mirror_maze'}
records=[]
for s in manifest['spaces']:
    if s['id'] in outdoor:continue
    root=bpy.data.objects[s['id']];w,d,h=s['size_m'];count=0
    for side,length in [('north',w),('south',w),('east',d),('west',d)]:
        # Height-only cornices never occupy doors/windows or the movement footprint.
        for z,thick,mat in [(h-.16,.12,'wood'),(h-.26,.035,'gold'),(h-.34,.025,'ink')]:
            size=(length-.12,.075,thick) if side in ('north','south') else (.075,length-.12,thick)
            loc=(0,(-1 if side=='south' else 1)*(d/2-.13),z) if side in ('north','south') else ((-1 if side=='west' else 1)*(w/2-.13),0,z)
            box('art_cornice_'+side,loc,size,mat,root);count+=1
        # Flush dark trim on existing side-wall panels, avoiding all known portals.
        portals=s.get('portals',[])
        coords=[p['position_blender'][0 if side in ('north','south') else 1] for p in portals if p.get('side')==side]
        for i in range(1,max(2,int(length/1.6))):
            off=-length/2+i*length/max(2,int(length/1.6))
            if any(abs(off-q)<.8 for q in coords) or (side in ('north','south') and abs(off)<1.3):continue
            if side in ('north','south'):loc=(off,(-1 if side=='south' else 1)*(d/2-.12),.55);size=(.035,.025,1.0)
            else:loc=((-1 if side=='west' else 1)*(w/2-.12),off,.55);size=(.025,.035,1.0)
            box('art_panel_stile_'+side,loc,size,'gold',root);count+=1
    # Ceiling coffer trims, narrow and high: preserve all authored wall/door topology.
    for x in [-w*.25,w*.25]:box('art_ceiling_long',(x,0,h-.06),(.07,d-.25,.06),'wood',root);count+=1
    for y in [-d*.25,d*.25]:box('art_ceiling_cross',(0,y,h-.06),(w-.25,.07,.06),'wood',root);count+=1
    bpy.ops.object.select_all(action='DESELECT')
    for o in [root]+list(root.children_recursive):o.select_set(True)
    bpy.context.view_layer.objects.active=root;file=OUT/(s['id']+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
    records.append({'id':s['id'],'file':file.relative_to(ROOT).as_posix(),'topology_owner':s['file'],'camera':s['camera'],'added_visual_parts':count,'collision_policy':'flush high/wall decoration; retain canonical topology collision candidates, validate in engine separately','runtime_integrated':False})
bpy.ops.wm.save_as_mainfile(filepath=str(SPACE/'space_art_source.blend'))
(OUT/'manifest.json').write_text(json.dumps({'status':'authored visual variants, not additional logical rooms','base_manifest':'art/space_v4/full_v2/manifest.json','spaces':records,'not_changed':['case floors/tanks/hatches/doors/furniture placements','all canonical room sizes and camera/portal coordinates'],'runtime_integrated':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('INTERIOR_ART_COMPLETE',len(records),'visual room variants',flush=True)
