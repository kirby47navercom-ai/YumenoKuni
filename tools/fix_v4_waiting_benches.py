"""Apply manuscript two-bench contract to source and visual variant, without regenerating unrelated rooms."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];SPACE=ROOT/'art/space_v4/full_v2'
for style in [False,True]:
    source=SPACE/('space_art_source.blend' if style else 'space_kit_source.blend')
    bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;root=bpy.data.objects['mirror_waiting'];removed=set()
    for child in list(root.children):
        if 'meeting_table' in child.name or child.name.startswith('mirror_waiting_chair'):
            for o in [child]+list(child.children_recursive):removed.add(o.name)
    for name in removed:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
    benches=[o for o in root.children if 'park_bench' in o.name];assert len(benches) in (1,2)
    first=benches[0];mapping={}
    if len(benches)==1:
        for old in [first]+list(first.children_recursive):
            new=old.copy();new.name=old.name+'_second';scene.collection.objects.link(new);mapping[old]=new
        for old,new in mapping.items():new.parent=mapping.get(old.parent,root)
        second=mapping[first];second.location=(2.8,1.5,0)
    for bench in [o for o in root.children if 'park_bench' in o.name]:
        bench.rotation_euler.z=math.pi/2 if bench.location.x<0 else -math.pi/2
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in [root]+list(root.children_recursive):o.select_set(True)
    bpy.context.view_layer.objects.active=root
    dest=SPACE/('interior_art_r3/mirror_waiting.glb' if style else 'mirror_waiting.glb')
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    if not style:
        mp=SPACE/'manifest.json';manifest=json.loads(mp.read_text(encoding='utf8'));rec=next(s for s in manifest['spaces'] if s['id']=='mirror_waiting')
        rec['collision_candidates']=[]
        for o in root.children_recursive:
            if o.type!='MESH':continue
            pts=[o.matrix_world@Vector(c) for c in o.bound_box]
            rec['collision_candidates'].append({'node':o.name,'min_blender':[min(p[i] for p in pts) for i in range(3)],'max_blender':[max(p[i] for p in pts) for i in range(3)],'candidate_only':True,'requires_interaction_filter':False})
        rec['furniture_contract']='two benches along opposite side walls, clear central passage; left bench head deeper/foot nearer entrance (13a11;13b2 I3-20)'
        mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('WAITING_TWO_BENCH_CONTRACT_FIXED',flush=True)
