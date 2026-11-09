"""Original park arrangement and directed room transitions from the authored 3D catalogue.
Scene portals may load another space; only explicitly paired boundaries claim alignment.
"""
from pathlib import Path
from collections import deque
import json,hashlib,math,os
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/os.environ.get('V4_SPACE_OUT','art/space_v4/full_v1')
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf8'));spaces={s['id']:s for s in manifest['spaces']}
centers={
 'plaza':(0,0,0),'hotel_lobby':(0,24,0),'hotel_corridor':(-4,58,3.2),
 'management_office':(20,24,0),'service_lounge':(22.6,32,0),'electrical_room':(34,24,0),
 'dining_room':(-38,24,0),'kitchen':(-24,24,0),'laundry_room':(-24,36,0),'clinic':(-38,36,0),
 'supply_store':(-24,48,0),'hotel_multiuse':(-38,48,0),'park_garden':(-24,-8,0),
 'park_main_gate':(0,-42,0),'ticket_booth':(-10,-34,0),
 'performance_stage':(70,0,0),'theatre_preparation':(70,13,0),'staff_passage':(70,26,0),
 'cold_store':(70,39,0),'refreshment_store':(58,39,0),'pool_edge':(84,26,0),
 'dream_lobby':(70,64,0),'screening_room':(70,78,0),'reading_room':(83,64,0),
 'archive_room':(98,64,0),'ferris_platform':(112,78,0),'ferris_cabin':(112,78,10),
 'mirror_maze':(98,14,0),'mirror_workbay':(103,27.5,0),'mirror_waiting':(118,27.5,0),'central_control':(118,42,0),
 'coaster_platform':(-70,0,0),'maintenance_workshop':(-70,16,0),'exhibition_room':(-88,16,0),
 'record_room':(-88,32,0),'inspection_hall_normal':(-70,34,0),'inspection_hall_changed':(-70,34,0),
 'loading_gate':(-70,90,0),'outside_threshold':(-70,112,0),
 'lower_stairway':(0,-4,0),'lower_corridor':(0,20,-5.76),'shelter_reception':(0,40,-5.76),
 'shelter_inner':(0,54,-5.76),'operating_archive':(18,40,-5.76),
 'trial_elevator':(0,-18,-6),'courtroom':(0,0,-16)
}
missing=set(spaces)-set(centers)-{'guest_room'};assert not missing,missing
instances=[]
for ident,pos in centers.items():
    s=spaces[ident]
    tier='subterranean' if pos[2]<0 or ident=='lower_stairway' else ('attraction_interior' if ident=='ferris_cabin' else 'surface')
    instances.append({'id':ident,'asset_id':ident,'asset':s['file'],'position_blender':list(pos),'rotation_z_degrees':0,'mode':s['mode'],'tier':tier,'mutually_exclusive_group':'inspection_hall_state' if ident.startswith('inspection_hall_') else None})
# Reuse the physically verified 16-room hotel frontage, now with the fixed-pan asset.
for i,y in enumerate([-24.5,-17.5,-10.5,-3.5,3.5,10.5,17.5,24.5]):
    for side in [-1,1]:
        ident=f'guest_{i*2+(1 if side<0 else 2):02d}'
        instances.append({'id':ident,'asset_id':'guest_room','asset':spaces['guest_room']['file'],'position_blender':[-4+side*5.6,58+y,3.2],'rotation_z_degrees':90 if side<0 else -90,'mode':'fixed_pan','tier':'hotel_upper','occupant':'story assignment pending'})
lookup={i['id']:i for i in instances};edges=[]
def connect(a,b,kind='scene_portal',**extra):
    assert a in lookup and b in lookup,(a,b)
    edges.append({'id':a+'__'+b,'a':a,'b':b,'bidirectional':True,'kind':kind,'access':'source/story flags must be wired; not unlocked by this file','runtime_implemented':False,**extra})
for a,b in [
 ('plaza','hotel_lobby'),('plaza','park_main_gate'),('park_main_gate','ticket_booth'),('plaza','park_garden'),
 ('hotel_lobby','management_office'),('management_office','electrical_room'),('management_office','service_lounge'),
 ('hotel_lobby','dining_room'),('dining_room','kitchen'),('hotel_lobby','laundry_room'),('hotel_lobby','clinic'),('hotel_lobby','supply_store'),('hotel_lobby','hotel_multiuse'),
 ('plaza','performance_stage'),('performance_stage','theatre_preparation'),('theatre_preparation','staff_passage'),('staff_passage','cold_store'),('cold_store','refreshment_store'),('plaza','pool_edge'),
 ('plaza','dream_lobby'),('dream_lobby','screening_room'),('dream_lobby','reading_room'),('reading_room','archive_room'),('plaza','ferris_platform'),('ferris_platform','ferris_cabin'),
 ('plaza','mirror_maze'),('mirror_maze','mirror_workbay'),('mirror_maze','mirror_waiting'),('dream_lobby','central_control'),
 ('plaza','coaster_platform'),('coaster_platform','maintenance_workshop'),('maintenance_workshop','exhibition_room'),('exhibition_room','record_room'),
 ('maintenance_workshop','inspection_hall_normal'),('maintenance_workshop','inspection_hall_changed'),('maintenance_workshop','loading_gate'),('loading_gate','outside_threshold'),
 ('maintenance_workshop','lower_stairway'),('lower_stairway','lower_corridor'),('lower_corridor','shelter_reception'),('shelter_reception','shelter_inner'),('shelter_reception','operating_archive'),
 ('plaza','trial_elevator'),('trial_elevator','courtroom'),('hotel_lobby','hotel_corridor')]:connect(a,b)
for ident in lookup:
    if ident.startswith('guest_'):connect('hotel_corridor',ident,kind='paired_boundary')
# Shared physical pair proofs; elsewhere this file claims explicit scene transitions only.
pairs=[('management_office','service_lounge',[2.6,4,0],[0,-4,0]),('theatre_preparation','staff_passage',[0,4,0],[0,-9,0]),('staff_passage','cold_store',[0,9,0],[0,-4,0]),('performance_stage','theatre_preparation',[0,9,0],[0,-4,0]),('dream_lobby','screening_room',[0,5,0],[0,-9,0]),('dream_lobby','reading_room',[7,0,0],[-6,0,0]),('hotel_lobby','hotel_corridor',[-4,6,3.2],[0,-28,0])]
def transform(ident,p):
    inst=lookup[ident];a=math.radians(inst['rotation_z_degrees']);x,y,z=p;cx,cy,cz=inst['position_blender'];return [cx+x*math.cos(a)-y*math.sin(a),cy+x*math.sin(a)+y*math.cos(a),cz+z]
for a,b,pa,pb in pairs:
    aa,bb=transform(a,pa),transform(b,pb);assert max(abs(x-y) for x,y in zip(aa,bb))<.001,(a,b,aa,bb)
    edge=next(e for e in edges if e['a']==a and e['b']==b);edge.update(kind='paired_boundary',a_local=pa,b_local=pb,world=aa,shared_frame_owner=b)
# Guest boundary coordinates; fix orientation/door local origins before any runtime import.
for ident in lookup:
    if not ident.startswith('guest_'):continue
    inst=lookup[ident];idx=int(ident[-2:])-1;y=[-24.5,-17.5,-10.5,-3.5,3.5,10.5,17.5,24.5][idx//2];side=-1 if idx%2==0 else 1
    pa=[side*2.1,y,0];pb=[0,-3.5,0];aa,bb=transform('hotel_corridor',pa),transform(ident,pb)
    assert max(abs(x-y) for x,y in zip(aa,bb))<.001,(ident,aa,bb)
    edge=next(e for e in edges if e['b']==ident);edge.update(a_local=pa,b_local=pb,world=aa,shared_frame_owner='hotel_corridor')
adj={i:set() for i in lookup}
for e in edges:adj[e['a']].add(e['b']);adj[e['b']].add(e['a'])
seen={'plaza'};q=deque(seen)
while q:
    for v in adj[q.popleft()]-seen:seen.add(v);q.append(v)
assert seen==set(lookup),set(lookup)-seen
assert 'central_control' not in adj['mirror_waiting']
assert 'pool_edge' not in adj['staff_passage']
report={'status':'authored complete catalogue arrangement/connection draft; not runtime accepted','source_manifest_sha256':hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest(),'axes':'Blender Z-up authored meters, not measured V3 coordinates','instances':instances,'connections':edges,'checks':{'all_instances_reachable_in_design_graph':True,'explicitly_paired_boundaries':sum(e['kind']=='paired_boundary' and 'world' in e for e in edges),'no_waiting_control_direct_door':True,'no_pool_staff_shortcut':True},'limits':['paired boundary alignment does not prove engine collision or doorway clearance','other edges are explicit loading transitions, not claims of coincident global geometry','duplicate boundary trim visibility ownership must be applied by importer','guest occupant allocation and exact chapter locks pending','normal/changed hall is mutually exclusive, never duplicate live rooms']}
(OUT/'world_layout.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('World design graph',len(instances),'instances,',len(edges),'connections; paired boundaries verified; runtime pending')
