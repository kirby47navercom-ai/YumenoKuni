"""Replace only exterior architecture, retaining checked rooms/cast/trees/rides."""
import bpy,sys,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
import v4_rebuilt_environment_kit as K
import v4_facility_identity as I
import v4_facility_architecture as F
O=R/'art/space_v4/facility_architecture_v2';O.mkdir(exist_ok=True)
if(R/'art/space_v4/facility_forms_v3/manifest.json').exists():raise RuntimeError('The user rejected this v2 architecture. Use rebuild_v4_facility_forms.py with the selected IDs; do not restore the shared house shell.')
bpy.ops.wm.open_mainfile(filepath=str(A.O/'sources/park-rebuilt.blend'));K.setup_materials();I.setup();world=bpy.data.objects['park_exterior_level'];only=next((set(s.split('=',1)[1].split(','))for s in sys.argv if s.startswith('--only=')),None);rows=[]
for inst in json.loads((R/'art/space_v4/full_v2/world_layout.json').read_text(encoding='utf8'))['instances']:
    ident=inst['id'];old=bpy.data.objects.get('facade_'+ident)
    if not old or ident=='hotel_corridor' or (only and ident not in only):continue
    A.erase(old.children_recursive);w,d,h=A.SPECS[inst['asset_id']]['size_m'];new=F.build(ident,w,d,h,I);new.parent=old
    rows.append({'id':ident,'role':new['architectureFamily'],'features':list(new.get('purposeFeatures',[])),'size':[w,d,h],'roof':new['roofStyle']});print('ARCHITECTURE_REBUILT',ident,flush=True)
if not only:
    wing=bpy.data.objects.get('rebuilt_hotel_upper_wing')
    if wing:
        A.erase([o for o in wing.children if o.name.startswith(('coherent_mansard_roof','continuous_mansard_roof','sealed_mansard_end_wall'))]);F.roof(wing,18.2,56,6.4,'mansard')
A.freeze(list(world.children_recursive));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(A.O/'sources/park-rebuilt.blend'),compress=True)
groups=[bpy.data.objects['exterior_'+n]for n in ['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']];landmarks=set(o for p in groups for o in A.descendants(p));common=[o for o in world.children_recursive if o not in landmarks]
row=A.export(common,'finish_context.glb','Assets/Art/explore3d/finish_context.glb',{'facadesRebuilt':31,'treesRebuilt':22,'purposeArchitecture':30})
updated=[r['id']for r in rows];rows=[{'id':o['facilityIdentity'],'role':o['architectureFamily'],'features':list(o['purposeFeatures']),'size':list(o['nominalSize']),'roof':o['roofStyle']}for o in world.children_recursive if o.get('architectureVersion')==2]
manifest={'architectureVersion':2,'allFacadesRebuilt':len(rows)==30,'updated':updated,'rows':rows,'rawAsset':row,'runtimeAccepted':False,'scope':'Exterior-only candidate. Existing other60 GLBs, stories, collision, engine and cast markers unchanged.'};(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('ARCHITECTURE_CANDIDATE_READY',len(rows),flush=True)
