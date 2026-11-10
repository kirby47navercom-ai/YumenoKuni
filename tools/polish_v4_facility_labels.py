"""Move only the four theatre signs onto the marquee's outward face."""
import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
O=A.O;bpy.ops.wm.open_mainfile(filepath=str(O/'sources/park-rebuilt.blend'));world=bpy.data.objects['park_exterior_level'];changed=[]
atlas=bpy.data.images.load(str(R/'art/space_v4/facility_identity_v1/facility-signs.png'),check_existing=False);atlas.pack()
for material in bpy.data.materials:
    if material.name.startswith('identity_facility_sign')and material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type=='TEX_IMAGE':node.image=atlas
for o in world.children_recursive:
    if o.get('architectureFamily')!='theatre':continue
    ident=o['facilityIdentity'];w,d,h=A.SPECS[ident]['size_m'];tag=next(c for c in o.children if c.get('facilityLabel'))
    tag.location.y=-d/2-1.125;changed.append(ident)
assert len(changed)==4,changed
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(O/'sources/park-rebuilt.blend'),compress=True)
groups=[bpy.data.objects['exterior_'+n]for n in ['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']];landmarks=set(o for p in groups for o in A.descendants(p));common=[o for o in world.children_recursive if o not in landmarks]
row=A.export(common,'finish_context.glb','Assets/Art/explore3d/finish_context.glb',{'facadesRebuilt':31,'treesRebuilt':22,'purposeArchitecture':30});file=O/'exterior-assembly.json';m=json.loads(file.read_text());m['assets']=[row if a['runtime']==row['runtime']else a for a in m['assets']];file.write_text(json.dumps(m,indent=2)+'\n');print('MARQUEE_LABELS_CORRECTED',changed,flush=True)
