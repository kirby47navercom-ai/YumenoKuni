"""Reconcile shared visual landmark across editable sources and portable GLBs."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];SPACE=ROOT/'art/space_v4/full_v2';sys.path.insert(0,str(ROOT/'tools'))
from v4_fountain_art import add_tiers
for filename,kind in [('space_kit_source.blend','base'),('space_art_source.blend','interior'),('park_exterior_source.blend','exterior'),('park_exterior_r2_source.blend','exterior_r2')]:
    source=SPACE/filename;bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
    roots=[o for o in scene.objects if o.type=='EMPTY' and 'detail_fountain_dry' in o.name]
    assert roots,filename
    for root in roots:add_tiers(bpy,root)
    export_roots=[bpy.data.objects['detail_fountain_dry'],bpy.data.objects['plaza']] if kind=='base' else [bpy.data.objects['park_exterior_level']] if kind.startswith('exterior') else []
    for root in export_roots:
        bpy.ops.object.select_all(action='DESELECT')
        for o in [root]+list(root.children_recursive):o.select_set(True)
        bpy.context.view_layer.objects.active=root
        output=SPACE/(('park_exterior_r2' if kind=='exterior_r2' else 'park_exterior')+'.glb') if kind.startswith('exterior') else SPACE/(root.name+'.glb')
        bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
    if kind=='base':
        mp=SPACE/'manifest.json';manifest=json.loads(mp.read_text(encoding='utf8'));plaza=next(s for s in manifest['spaces'] if s['id']=='plaza');root=bpy.data.objects['plaza']
        plaza['collision_candidates']=[];bpy.context.view_layer.update()
        for o in root.children_recursive:
            if o.type!='MESH':continue
            pts=[o.matrix_world@Vector(c) for c in o.bound_box]
            plaza['collision_candidates'].append({'node':o.name,'min_blender':[min(p[i] for p in pts) for i in range(3)],'max_blender':[max(p[i] for p in pts) for i in range(3)],'candidate_only':True,'requires_interaction_filter':False})
        prop=next(r for r in manifest['models'] if r['id']=='detail_fountain_dry');r=bpy.data.objects['detail_fountain_dry'];prop.update(nodes=1+len(r.children_recursive),mesh_count=sum(o.type=='MESH' for o in r.children_recursive))
        mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(source))
print('FOUNTAIN_ART_RECONCILED',flush=True)
