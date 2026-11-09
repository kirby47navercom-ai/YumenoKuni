"""Incremental art pass over the checked bank; don't reassemble old furniture."""
import bpy,sys,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import build_v4_rebuilt_environment as A
import v4_rebuilt_environment_kit as K
import v4_facility_identity as I
O=A.O;ID=I.IDENTITY
def exterior():
    bpy.ops.wm.open_mainfile(filepath=str(O/'sources/park-rebuilt.blend'));K.setup_materials();I.setup();world=bpy.data.objects['park_exterior_level'];changes=[]
    for inst in json.loads((R/'art/space_v4/full_v2/world_layout.json').read_text(encoding='utf8'))['instances']:
        old=bpy.data.objects.get('facade_'+inst['id'])
        if not old or old.type!='EMPTY':continue
        A.erase(old.children_recursive);w,d,h=A.SPECS[inst['asset_id']]['size_m']
        if inst['id']!='hotel_corridor':new=I.building(inst['id'],w,d,h);new.parent=old
        changes.append({'root':old.name,'kind':I.family(inst['id']),'sizeMetres':[w,d,h],'purposeArchitecture':inst['id']!='hotel_corridor','sign':inst['id']!='hotel_corridor'})
    # The shared hotel upper envelope remains; independent guest facades must not overlap it.
    A.freeze(list(world.children_recursive));bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(O/'sources/park-rebuilt.blend'),compress=True)
    groups=[bpy.data.objects['exterior_'+n]for n in ['plaza','park_garden','pool_edge','ferris_platform','coaster_platform','park_main_gate']];landmarks=set(o for p in groups for o in A.descendants(p));common=[o for o in world.children_recursive if o not in landmarks]
    row=A.export(common,'finish_context.glb','Assets/Art/explore3d/finish_context.glb',{'facadesRebuilt':31,'treesRebuilt':22,'purposeArchitecture':30})
    p=O/'exterior-assembly.json';manifest=json.loads(p.read_text());manifest['facades']=changes;manifest['assets']=[row if a['runtime']==row['runtime']else a for a in manifest['assets']];manifest['facilityIdentityManifest']='art/space_v4/facility_identity_v1/manifest.json';p.write_text(json.dumps(manifest,indent=2)+'\n')
def rooms():
    path=O/'room-assembly.json';manifest=json.loads(path.read_text());rows=[];coverage=[]
    only=next((set(s.split('=',1)[1].split(','))for s in sys.argv if s.startswith('--only=')),None)
    if only and 'hotel_corridor'not in only:coverage=json.loads((I.O/'placement-proof.json').read_text())['roomBadges']
    for row in manifest['assets']:
        ident=Path(row['runtime']).stem
        if ident not in ID['facilities']or(only and ident not in only):rows.append(row);continue
        A.clean();bpy.ops.import_scene.gltf(filepath=str(R/row['file']));I.setup()
        old=[o for o in bpy.data.objects if o.type=='EMPTY'and o.name.startswith('facility_identity_signage')]
        for o in old:A.erase(A.descendants(o))
        r=K.root('facility_identity_signage');spec=A.SPECS.get(ident);w,d,h=spec['size_m']
        # Real wall-mounted panel. Outdoor boards have a structural post.
        outdoor=ident in ['plaza','park_garden','pool_edge','ferris_platform','ferris_cabin','coaster_platform','loading_gate','outside_threshold','park_main_gate','ticket_booth']
        if ident=='hotel_corridor':
            badges=I.guest_badges(r);I.plate(ident,r,(0,d/2-.17,2.72),width=2.6);coverage+=badges
        elif outdoor:
            x=-min(w*.3,4.2);y=-d/2+.65
            K.tube('wayfinding_support',[(x,y,.02),(x,y,2.12)],[.042]*2,'iron',r,6);I.plate(ident,r,(x,y,2.05),width=min(2.5,w*.55))
        else:I.plate(ident,r,(0,d/2-.16,min(h-.25,2.75)),width=min(2.6,w*.6))
        A.freeze(list(bpy.data.objects));bpy.context.preferences.filepaths.save_version=0
        if ident in ['hotel_corridor','clinic','dining_room']:bpy.ops.wm.save_as_mainfile(filepath=str(O/'sources'/(ident+'.blend')),compress=True)
        new=A.export(list(bpy.data.objects),Path(row['file']).name,row['runtime'],{k:v for k,v in row.items()if k not in ['file','runtime','triangles','meshParts','rawBytes']})
        new['facilitySign']=ident;rows.append(new);print('FACILITY_SIGN_READY',ident,flush=True)
    manifest['assets']=rows;path.write_text(json.dumps(manifest,indent=2)+'\n')
    out={'roomBadges':coverage,'facilityInteriors':[Path(a['runtime']).stem for a in rows if a.get('facilitySign')],'sourceManifest':'art/space_v4/facility_identity_v1/manifest.json','gameplayOrCollisionChanges':False}
    (I.O/'placement-proof.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':
    mode=next((s[7:]for s in sys.argv if s.startswith('--mode=')),'all')
    if mode in ['all','exterior']:exterior()
    if mode in ['all','rooms']:rooms()
    print('FACILITY_IDENTITY_ASSEMBLED',mode,flush=True)
