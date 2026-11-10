"""Rebuild every authored park exterior and its continuous landscape in Blender."""
import bpy,json,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
import v4_rebuilt_environment_kit as K
import v4_facility_identity as I
import v4_facility_forms as F
import v4_park_continuity as C
O=R/'art/space_v4/facility_forms_v3';O.mkdir(exist_ok=True);(O/'raw').mkdir(exist_ok=True);(O/'review').mkdir(exist_ok=True)
checkpoint=O/'assembly-checkpoint.blend';cursor=O/'assembly-checkpoint.json'
only=next((set(a.split('=',1)[1].split(','))for a in sys.argv if a.startswith('--only=')),None)
resume=checkpoint.exists()and'--fresh'not in sys.argv
source=O/'park-form-source.blend'if only and(O/'park-form-source.blend').exists()else checkpoint if resume else A.O/'sources/park-rebuilt.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));K.setup_materials();I.setup();F.palette();world=bpy.data.objects['park_exterior_level']
def row_for(new,parent):return {'id':str(new['facilityIdentity']),'role':str(new['architectureFamily']),'profile':[[float(v)for v in pair]for pair in new.get('roofProfileXZ',[])],'features':list(new['purposeFeatures']),'sourceObject':parent.name,'sourceParentTransformUnchanged':True,'size':list(new['nominalSize'])}
rows=[row_for(o,o.parent)for o in world.children_recursive if o.get('architectureVersion')==3]if resume or only else[];done={r['id']for r in rows}-(only or set());changed=0
layout=json.loads((R/'art/space_v4/full_v2/world_layout.json').read_text(encoding='utf8'))
for inst in layout['instances']:
    ident=inst['id'];old=bpy.data.objects.get('facade_'+ident)
    if not old or ident=='hotel_corridor'or ident in done or only and ident not in only:continue
    A.erase(old.children_recursive);w,d,h=A.SPECS[inst['asset_id']]['size_m'];new=F.build(ident,w,d,h,I);new.parent=old
    rows=[r for r in rows if r['id']!=ident];rows.append(row_for(new,old));changed+=1;print('PURPOSE_FORM_REBUILT',ident,flush=True)
    if changed%5==0:
        bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(checkpoint),compress=True);cursor.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
continuity=json.loads((O/'manifest.json').read_text(encoding='utf8'))['continuity']if'--keep-landscape'in sys.argv else C.build(world,A);A.freeze(list(world.children_recursive));bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(O/'park-form-source.blend'),compress=True)
groups=[bpy.data.objects['exterior_'+n]for n in ['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']];landmarks=set(o for p in groups for o in A.descendants(p));common=[o for o in world.children_recursive if o not in landmarks]
oldout=A.O;A.O=O
try:raw=A.export(common,'finish_context.glb','Assets/Art/explore3d/finish_context.glb',{'facadesRebuilt':31,'treesRebuilt':22,'purposeArchitecture':30,'purposeFormsVersion':3})
finally:A.O=oldout
assert len(rows)==30
(O/'manifest.json').write_text(json.dumps({'version':3,'allFacadesRebuilt':True,'source':'art/space_v4/facility_forms_v3/park-form-source.blend','rows':rows,'rawAsset':raw,'continuity':continuity,'runtimeAccepted':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('ALL_EXTERIOR_FORMS_AND_CONTINUITY_BUILT',len(rows),flush=True)
