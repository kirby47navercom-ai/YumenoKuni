"""Build explicit test-only art camera fixtures; production navigation stays intact."""
from pathlib import Path
import json,sys,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
import compile_v4_rebuilt_environment as C
from v4_lowpoly_glb import read,digest
O=R/'art/space_v4/facility_forms_v3';W=R/'Game/Saved/facility-form-20261104';m=json.loads((O/'manifest.json').read_text(encoding='utf8'))
j,b=read(R/m['rawAsset']['file']);omit=set()
def visit(i):
    omit.add(i)
    for child in j['nodes'][i].get('children',[]):visit(child)
for i,n in enumerate(j['nodes']):
    if 'facilityLabel'in n.get('extras',{}):visit(i)
previous=C.O;C.O=O/'unlabelled';(C.O/'models').mkdir(parents=True,exist_ok=True)
try:unlabelled=C.compile(m['rawAsset'],omit_mesh_nodes=omit)
finally:C.O=previous
world=json.loads((R/'Game/Assets/Data/explore_world.json').read_text(encoding='utf8'));bucket=world['spaces']['plaza']['bucket'];page=json.loads((R/'Game'/bucket).read_text(encoding='utf8'));page['spaces']['plaza'].update(bounds=[-1800,-1800,1800,1800],collision=[],pitch_limits=[-70,70]);camera=W/'test-only-camera-bucket.json';camera.write_text(json.dumps(page,separators=(',',':'))+'\n')
overrides={'Content/Assets/Art/explore3d/finish_context.glb':str(R/unlabelled['file']),'Content/'+bucket:str(camera)}
(W/'unlabelled-camera-overrides.json').write_text(json.dumps(overrides,indent=2)+'\n')
layout={s['id']:s for s in json.loads((R/'art/space_v4/full_v2/world_layout.json').read_text(encoding='utf8'))['instances']};views=[]
for row in m['rows']:
    ident=row['id'];x,y,z=layout[ident]['position_blender'];w,d,h=row['size'];cx=x+w*.86;cy=y-d*.95-7.5;eye=1.6
    if ident=='theatre_preparation':cx=x+w*.9+8;cy=y
    if ident in ['staff_passage','mirror_workbay']:cx=x-w*.9-8;cy=y
    # Dense service rows: the common southeast orbit enters the neighbouring
    # facility. Review from the real promenade instead of counting its wall.
    if ident in ['clinic','hotel_multiuse','record_room']:cx=x-w*.5-8;cy=y-d*.25
    if ident in ['laundry_room','supply_store']:cx=x-w*.5-3;cy=y-d*.5-2
    if ident=='theatre_preparation':cx=x+w*.5+8;cy=y+1
    dx=x-cx;dz=-(y-cy);yaw=math.degrees(math.atan2(-dx,-dz));pitch=math.degrees(math.atan2(h*.44-eye,math.hypot(dx,dz)))
    views.append({'label':'unlabelled-'+ident,'room':'plaza','pose':[cx,eye,-cy,yaw,pitch]})
for i,(x,y,eye,yaw)in enumerate([(-70,112,1.6,0),(0,-65,1.6,180),(125,90,1.6,-90),(-115,35,1.6,90)]):views.append({'label':'continuity-'+str(i),'room':'plaza','pose':[x,eye,-y,yaw,-3]})
(W/'unlabelled-native-views.json').write_text(json.dumps(views,indent=2)+'\n');(W/'unlabelled-resource-proof.json').write_text(json.dumps({'fullCandidate':m['asset'],'unlabelledCandidate':unlabelled,'removedNamedLabelNodes':len(omit),'testOnlyWorldMetadata':str(camera.relative_to(R)),'productionNavigationChanged':False,'purpose':'Art-camera fixtures without physical nameplate meshes; not normal progression, movement, collision or final shipping navigation evidence.'},indent=2)+'\n');print('UNLABELLED_NATIVE_FIXTURES_READY',len(views),len(omit))
