"""Compile authored v4 space geometry/contracts into local exploration data.
No source assets are modified; engine builds/runtime are deliberately not launched.
"""
from __future__ import annotations
import argparse, collections, hashlib, html, json, math, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'art/space_v4/full_v2'
OUT=ROOT/'art/space_v4/runtime_v1'
# Explicit authored exterior sets, including the glazed cabin's outside view.
OUTDOOR={'plaza','park_garden','park_main_gate','ticket_booth','pool_edge','ferris_platform','ferris_cabin','coaster_platform','loading_gate','outside_threshold'}
LABELS={
 'plaza':'중앙 광장','hotel_lobby':'호텔 로비','hotel_corridor':'호텔 복도',
 'management_office':'관리 사무실','service_lounge':'직원 휴게실','electrical_room':'전기실',
 'dining_room':'호텔 식당','kitchen':'주방','laundry_room':'세탁실','clinic':'의무실',
 'supply_store':'비품 창고','hotel_multiuse':'호텔 다목적실','park_garden':'정원',
 'park_main_gate':'정문','ticket_booth':'매표소','performance_stage':'공연장',
 'theatre_preparation':'공연 준비실','staff_passage':'직원 통로','cold_store':'냉장 창고',
 'refreshment_store':'매점 창고','pool_edge':'수영장 가장자리','dream_lobby':'드림관 로비',
 'screening_room':'상영실','reading_room':'열람실','archive_room':'자료실',
 'ferris_platform':'관람차 승강장','ferris_cabin':'관람차 객실','mirror_maze':'거울 미로',
 'mirror_workbay':'거울 작업실','mirror_waiting':'거울 대기실','central_control':'중앙 제어실',
 'coaster_platform':'롤러코스터 승강장','maintenance_workshop':'정비 작업실',
 'exhibition_room':'전시실','record_room':'기록실','inspection_hall_normal':'점검동',
 'inspection_hall_changed':'점검동','loading_gate':'반출구','outside_threshold':'외부 문턱',
 'lower_stairway':'지하 계단','lower_corridor':'지하 복도','shelter_reception':'대피소 접수실',
 'shelter_inner':'대피소 안쪽','operating_archive':'운영 기록실','trial_elevator':'재판 엘리베이터',
 'courtroom':'학급재판장'}
# Labels/old background names are compatibility locators, never new story unlocks.
ALIASES=[
 ('직원 휴게','service_lounge'),('직원휴게','service_lounge'),('휴게실','service_lounge'),
 ('관리실','management_office'),('관리 사무','management_office'),('냉장','cold_store'),
 ('공연 준비','theatre_preparation'),('대기실','mirror_waiting'),('거울 작업','mirror_workbay'),
 ('거울','mirror_maze'),('점검','inspection_hall_normal'),('작업대','inspection_hall_normal'),
 ('운영 기록','operating_archive'),('운영기록','operating_archive'),('지하 복도','lower_corridor'),
 ('접수실','shelter_reception'),('대피소 안','shelter_inner'),('반출','loading_gate'),
 ('공연장','performance_stage'),('무대','performance_stage'),('직원 통로','staff_passage'),
 ('서비스 복도','staff_passage'),('자료실','archive_room'),('서고','archive_room'),
 ('열람','reading_room'),('관람차','ferris_platform'),('기록실','record_room'),
 ('의무실','clinic'),('주방','kitchen'),('창고','supply_store'),('식당','dining_room'),
 ('라운지','service_lounge'),('로비','hotel_lobby'),('호텔','hotel_lobby'),
 ('광장','plaza'),('산책','park_garden'),('정원','park_garden'),('매표','ticket_booth'),
 ('기념품','supply_store'),('푸드코트','dining_room'),('정비','maintenance_workshop'),
 ('승강장','coaster_platform')]
BG_ALIASES={'hotel_lounge_day':'service_lounge','hotel_lounge_night':'service_lounge',
 'infirmary':'clinic','foodcourt':'dining_room','hotel_lobby':'hotel_lobby',
 'souvenir_shop':'supply_store','castle_library':'archive_room','castle_vault':'record_room',
 'core_shelter':'shelter_reception','core_control':'central_control','core_hall':'inspection_hall_normal',
 'food_service_corridor_day':'staff_passage','ferris_boarding':'ferris_platform',
 'rollercoaster_maintenance':'maintenance_workshop','plaza_day':'plaza','plaza_night':'plaza',
 'plaza_dawn':'plaza','waterpark_day':'pool_edge','theater_lobby':'dream_lobby'}
# Target terms refer only to geometry already present in the authored room.
TERMS=[('문','door'),('출입','door'),('프린터','printer'),('인쇄','printer'),('전화','phone'),
 ('수화기','phone'),('서랍','drawer'),('창문','window'),('창','window'),('벤치','bench'),
 ('탁자','table'),('테이블','table'),('책상','desk'),('마이크','microphone'),('상자','chest'),
 ('보관함','cabinet'),('선반','shelf'),('컵','cup'),('찻잔','cup'),('장부','archive'),
 ('문서','archive'),('기록','archive'),('난간','rail'),('해치','hatch'),('고정','fix'),
 ('거울','mirror'),('제어','console'),('배전','control'),('시계','clock'),('분수','basin')]
def read(name):return json.loads((SOURCE/name).read_text(encoding='utf-8'))
def put(name,value):
 p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
def xyz(v):return [round(v[0],4),round(v[2],4),round(-v[1],4)]
def blocked(p,boxes,r=.27):
 x,z=p
 return any(a-r<x<b+r and c-r<z<d+r for a,c,b,d,*rest in boxes)
def safe_point(p,boxes,bounds):
 x,z=p
 for radius in [0]+[i*.2 for i in range(1,61)]:
  for j in range(1 if radius==0 else 32):
   a=j*math.tau/32; q=[x+radius*math.cos(a),z+radius*math.sin(a)]
   if bounds[0]+.3<q[0]<bounds[2]-.3 and bounds[1]+.3<q[1]<bounds[3]-.3 and not blocked(q,boxes):return [round(v,3) for v in q]
 raise ValueError('no collision-free camera spawn')
def main():
 finish_file=ROOT/'art/space_v4/architecture_finish_v2/manifest.json'
 if not finish_file.exists():finish_file=ROOT/'art/space_v4/outdoor_finish_v1/manifest.json'
 finish=json.loads(finish_file.read_text(encoding='utf8')) if finish_file.exists() else {}
 if '--exterior-art-only' in sys.argv:
  # Keep all already verified gameplay metadata byte-for-byte. Only publish the
  # source bindings for the seven existing exterior render chunks.
  assert finish and 'architecture' in finish
  copies=json.loads((OUT/'copy_manifest.json').read_text(encoding='utf8'))
  rows={row['to']:row for row in copies};changed=[]
  for asset in [finish['context'],*finish['landmarks'].values()]:
   assert asset['runtime'] in rows
   assert hashlib.sha256((ROOT/asset['file']).read_bytes()).hexdigest()==asset['sha256']
   rows[asset['runtime']]['from']=asset['file'];changed.append(asset['runtime'])
  put('copy_manifest.json',copies)
  print(json.dumps({'exteriorArtOnly':True,'runtimeBindings':changed,'worldMetadataUnchanged':True}))
  return
 manifest,layout=read('manifest.json'),read('world_layout.json')
 reaction_file=ROOT/'art/space_v4/reactions_v1/manifest.json';reactions=json.loads(reaction_file.read_text(encoding='utf8'))['spaces'] if reaction_file.exists() else {}
 spaces={s['id']:s for s in manifest['spaces']}
 result={'version':1,'coordinate_system':'standard glTF (x,z,-y) from authored Blender meters',
 'reference':'docs/spec/18_V3_분석/01_탐색.md; movement/fixed-eye distinction; our authored velocities',
 'spaces':{},'instances':{},'aliases':ALIASES,'backgrounds':BG_ALIASES,'terms':TERMS,'connections':[],
 'limits':['unassigned guest rooms do not receive invented occupants',
 'active flow destinations provide access; model catalogue alone never unlocks a destination',
 'unmapped clues keep their explicit inspection view; guessed geometry is not forensic evidence']}
 copies=[];qa={'spaces':{},'errors':[],'runtime_tested':False}
 for sid,s in spaces.items():
  if sid=='courtroom':continue
  sx,sy,sz=s['size_m'];bounds=[-sx/2,-sy/2,sx/2,sy/2]
  cam=s.get('camera',{});free=s['mode']=='free_walk'
  spawn=cam.get('spawn_blender',[0,0,0]) if free else cam.get('eye_blender',[0,-sy*.3,1.6])
  floor=spawn[2] if free else 0
  boxes=[];nodes=[];surfaces=[]
  for c in s.get('collision_candidates',[]):
   lo,hi=c['min_blender'],c['max_blender'];node=c['node']
   # Full decorative crown/foliage bounds are not player bodies. Floor/ceiling omitted.
   if any(w in node.lower() for w in ['floor','step','landing','platform']) and (hi[2]-lo[2]<.42 or 'step' in node.lower()) and hi[0]-lo[0]>.4 and hi[1]-lo[1]>.1:
    surfaces.append([round(lo[0],4),round(-hi[1],4),round(hi[0],4),round(-lo[1],4),round(hi[2],4)])
   if hi[2]>floor+.34 and lo[2]<floor+sz and (hi[0]-lo[0])*(hi[1]-lo[1])>.012:
    if not any(w in node.lower() for w in ['leaf_cluster','branch','panel_trim','inset_edge','tick','label','handle','lever','lamp_head','floor','step','landing']):
     b=[lo[0],-hi[1],hi[0],-lo[1],lo[2],hi[2]]
     if b[2]-b[0]<sx*.98 or b[3]-b[1]<sy*.98:boxes.append([round(v,4) for v in b])
   if hi[2]>=.12 and lo[2]<2.5:
    nodes.append({'id':node,'p':xyz([(a+b)/2 for a,b in zip(lo,hi)]),'box':[xyz(lo),xyz(hi)]})
  # Merge exact duplicate collision boxes; preserve distinct wall/prop bounds.
  boxes=list(map(list,dict.fromkeys(map(tuple,boxes))))
  converted=xyz(spawn);ground_boxes=[b for b in boxes if b[4]<floor+1.6 and b[5]>floor+.34];safe=safe_point([converted[0],converted[2]],ground_boxes,bounds)
  eye=cam.get('eye_height',1.6) if free else converted[1]
  floorplan='Assets/Art/explore3d/map_'+sid+'.svg'
  asset=reactions.get(sid,{}).get('file') or finish.get('local',{}).get(sid,{}).get('file') or s.get('file') or next(i['asset'] for i in layout['instances'] if i['asset_id']==sid)
  if not (ROOT/asset).exists():raise FileNotFoundError(asset)
  dest='Assets/Art/explore3d/'+sid+'.glb';copies.append({'from':asset,'to':dest})
  result['spaces'][sid]={'id':sid,'label':LABELS.get(sid,sid),'mesh':dest,'mode':s['mode'],'outdoor':sid in OUTDOOR,
   'bounds':bounds,'floor':floor,'eye_height':eye,'spawn':[safe[0],floor+eye,safe[1]],
   'yaw':0,'pitch_limits':[-20,20] if free else cam.get('pitch_limits_degrees',[-10,7]),
   'yaw_limits':[-180,180] if free else cam.get('yaw_limits_degrees',[-155,155]),
   'walk_surfaces':surfaces,'footstep_surface':('metal' if any(n in sid for n in ['platform','stair','control','corridor']) else 'wood' if sid in ['performance_stage','reading_room','archive_room'] else 'tile'),
   'collision':boxes,'targets':[{'id':t['id'],'p':xyz(t['position_blender'])} for t in s.get('targets',[]) if 'position_blender'in t],
   'nodes':nodes,'map':floorplan,'reactions':[{k:v for k,v in p.items() if k not in ['file','sha256','bytes']} for p in reactions.get(sid,{}).get('props',[])]}
  for prop in reactions.get(sid,{}).get('props',[]):
   assert hashlib.sha256((ROOT/prop['file']).read_bytes()).hexdigest()==prop['sha256'];copies.append({'from':prop['file'],'to':prop['runtime']})
  body=''.join(f'<rect x="{(a+sx/2)/sx*240:.2f}" y="{(c+sy/2)/sy*240:.2f}" width="{max(.4,(b-a)/sx*240):.2f}" height="{max(.4,(d-c)/sy*240):.2f}" fill="#8b9aa9"/>' for a,c,b,d,*rest in boxes)
  put('maps/map_'+sid+'.svg',f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="480" viewBox="0 0 240 240"><rect width="240" height="240" fill="#07131b" fill-opacity=".85"/><rect x="1" y="1" width="238" height="238" fill="none" stroke="#c9e1e7"/>{body}</svg>')
  copies.append({'from':str((OUT/'maps'/('map_'+sid+'.svg')).relative_to(ROOT)).replace('\\','/'),'to':floorplan})
  qa['spaces'][sid]={'collision_boxes':len(boxes),'nodes':len(nodes),'spawn_clear':not blocked(safe,ground_boxes),'source':asset}
 for inst in layout['instances']:
  if inst['asset_id'] not in result['spaces']:continue
  result['instances'][inst['id']]={'space':inst['asset_id'],'p':xyz(inst['position_blender']),
   'label':LABELS.get(inst['id'],'객실 '+inst['id'][-2:] if inst['id'].startswith('guest_') else inst['id']),
   'rotation':inst.get('rotation_z_degrees',0),'occupant':inst.get('occupant','')}
 for edge in layout['connections']:
  if edge['a'] not in result['instances'] or edge['b'] not in result['instances']:continue
  item={k:edge[k] for k in ['id','a','b','kind']}
  for k in ['a','b']:
   src=result['instances'][edge[k]];dst=result['instances'][edge['b' if k=='a' else 'a']]
   s=result['spaces'][src['space']];bounds=s['bounds']
   if k+'_local' in edge:p=xyz(edge[k+'_local']);p[1]+=1.2
   else:
    dx,dz=dst['p'][0]-src['p'][0],dst['p'][2]-src['p'][2]
    if abs(dx)>abs(dz):p=[bounds[2]-.22 if dx>0 else bounds[0]+.22,1.2,0]
    else:p=[0,1.2,bounds[3]-.22 if dz>0 else bounds[1]+.22]
   item[k+'_p']=p
  result['connections'].append(item)
 # Independent drawing uses same authored instance positions as door direction and atlas selection.
 atlas=[]
 for inst in result['instances'].values():
  if inst['space']=='guest_room':continue
  x=300+inst['p'][0]*2.25;y=360+inst['p'][2]*2.25
  atlas.append(f'<g transform="translate({x:.1f} {y:.1f})"><rect x="-5" y="-5" width="10" height="10" fill="#84cbd1"/><text x="9" y="4" font-family="sans-serif" font-size="10" fill="#e5eff1">{html.escape(inst["label"])}</text></g>')
 put('maps/atlas.svg','<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1440" viewBox="0 0 640 720"><rect width="640" height="720" fill="#08131c"/>'+''.join(atlas)+'</svg>')
 copies.append({'from':str((OUT/'maps/atlas.svg').relative_to(ROOT)).replace('\\','/'),'to':'Assets/Art/explore3d/atlas.svg'})
 if finish:
  assets=[finish['context'],*finish['landmarks'].values()]
  for asset in assets:
   file=ROOT/asset['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==asset['sha256'],asset['file'];copies.append({'from':asset['file'],'to':asset['runtime']})
  result['worldContext']={'mesh':finish['context']['runtime'],'landmarks':{k:v['runtime'] for k,v in finish['landmarks'].items()},'policy':'Source world positions; current active local set hides its context duplicate; local target/collision geometry remains authoritative.'}
 sculpted=ROOT/'art/space_v4/sculpted_v1/manifest.json'
 if sculpted.exists():
  replacements={a['runtime']:a['file'] for a in json.loads(sculpted.read_text(encoding='utf8'))['assets']}
  for row in copies:
   if row['to'] in replacements:row['from']=replacements[row['to']]
 put('world.json',result);put('copy_manifest.json',copies)
 # One render mesh, lazy replacement per room. Never preload every high-resolution GLB at startup.
 put('scene_objects.json',[{'id':'ExploreGeometry','name':'탐색 공간','kind':'cube','position':[300,0,0],'rotation':[0,0,0],'scale':[1,1,1],'visible':True,'components':[{'type':'MeshRenderer','properties':{'mesh':'','visible':False,'castShadow':True,'receiveShadow':True}}]}])
 qa.update({'space_count':len(result['spaces']),'instances':len(result['instances']),'connections':len(result['connections']),
 'source_hashes':{n:hashlib.sha256((SOURCE/n).read_bytes()).hexdigest() for n in ['manifest.json','world_layout.json','space_contracts.json']}})
 assert all(x['spawn_clear'] for x in qa['spaces'].values())
 assert all((ROOT/c['from']).is_file() for c in copies)
 put('qa.json',qa)
 print(json.dumps({k:qa[k] for k in ['space_count','instances','connections','errors','runtime_tested']}))
if __name__=='__main__':main()
