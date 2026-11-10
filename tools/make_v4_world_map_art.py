"""Editable map art from actual authored room positions/links; no invented chapter unlocks."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw,ImageFont
import make_v4_ui_batch as ui
R=Path(__file__).resolve().parents[1];O=R/'ui/v4/world_maps';O.mkdir(parents=True,exist_ok=True);ui.OUT=O;ui.SCALE=4
layout_path=R/'art/space_v4/full_v2/world_layout.json';layout=json.loads(layout_path.read_text(encoding='utf8'))
spec={s['id']:s for s in json.loads((R/'art/space_v4/full_v2/manifest.json').read_text(encoding='utf8'))['spaces']}
names=dict(zip(['plaza','hotel_lobby','hotel_corridor','management_office','service_lounge','electrical_room','dining_room','kitchen','laundry_room','clinic','supply_store','hotel_multiuse','park_garden','park_main_gate','ticket_booth','performance_stage','theatre_preparation','staff_passage','cold_store','refreshment_store','pool_edge','dream_lobby','screening_room','reading_room','archive_room','ferris_platform','ferris_cabin','mirror_maze','mirror_workbay','mirror_waiting','central_control','coaster_platform','maintenance_workshop','exhibition_room','record_room','inspection_hall_normal','loading_gate','outside_threshold','lower_stairway','lower_corridor','shelter_reception','shelter_inner','operating_archive','trial_elevator','courtroom'],['분수 광장','호텔 로비','객실 복도','관리실','서비스 휴게실','전기 점검실','식당','주방','세탁실','진료실','물품 보관실','다목적실','공원 정원','정문','매표소','공연 무대','준비실','직원 통로','냉장 보관실','매점','수영장','꿈의 로비','상영실','열람실','자료실','관람차 승강장','관람차 객실','거울 미로','거울 작업실','대기실','중앙 제어실','코스터 승강장','정비실','전시실','기록실','점검 홀','반출문','문밖 통로','하부 계단','하부 복도','대피소 접수','대피소 안쪽','운용 기록실','재판 승강기','재판장']))
groups={k:[] for k in ['surface','hotel_upper','lower','court','cabin']}
for a in layout['instances']:
 if a['id']=='inspection_hall_changed':continue
 key='hotel_upper' if a['tier']=='hotel_upper' or a['id']=='hotel_corridor' else 'cabin' if a['id']=='ferris_cabin' else 'court' if a['id'] in ('trial_elevator','courtroom') else 'lower' if a['tier']=='subterranean' else 'surface'
 groups[key].append(a)
records=[];seen=set();review=R/'Game/Saved/v4-world-map-review';review.mkdir(parents=True,exist_ok=True)
for key,items in groups.items():
 W,H=1440,960;p=ui.Plate('map_'+key,W,H)
 p.poly([(24,20),(W-14,6),(W-4,H-24),(14,H-6),(4,43)],ui.INK)
 p.poly([(34,32),(W-29,22),(W-21,H-40),(30,H-23),(21,49)],'#24212c')
 p.line([(44,63),(W-47,47)],ui.PAPER,2);p.line([(44,H-52),(W-47,H-68)],ui.RED,3)
 for x in range(70,W-40,44):p.line([(x,80),(x,H-78)],'#302c38',.6)
 for y in range(90,H-70,44):p.line([(50,y),(W-44,y)],'#302c38',.6)
 coords={a['id']:a['position_blender'][:2] for a in items}
 bounds=[]
 for a in items:
  x,y=coords[a['id']];w,d=spec[a['asset_id']]['size_m'][:2];bounds += [(x-w/2,y-d/2),(x+w/2,y+d/2)]
 x0,y0=min(v[0] for v in bounds),min(v[1] for v in bounds);x1,y1=max(v[0] for v in bounds),max(v[1] for v in bounds)
 scale=min((W-160)/(x1-x0),(H-210)/(y1-y0));cx,cy=(x0+x1)/2,(y0+y1)/2
 project=lambda x,y:(W/2+(x-cx)*scale,H/2-(y-cy)*scale)
 for edge in layout['connections']:
  if edge['a'] in coords and edge['b'] in coords:
   a=project(*coords[edge['a']]);b=project(*coords[edge['b']]);p.line([a,b],ui.INK,8);p.line([a,b],ui.VIOLET,3)
 anchors=[]
 for a in items:
  seen.add(a['id']);x,y=project(*coords[a['id']]);w,d=spec[a['asset_id']]['size_m'][:2];w=max(14,w*scale-3);d=max(14,d*scale-3)
  p.box(x-w/2,y-d/2,w,d,ui.INK);p.line([(x-w/2,y-d/2),(x+w/2,y-d/2),(x+w/2,y+d/2),(x-w/2,y+d/2),(x-w/2,y-d/2)],ui.PAPER,1.6)
  p.line([(x-w/2+3,y+d/2-3),(x+w/2-3,y+d/2-3)],ui.VIOLET,2)
  aliases=['inspection_hall_changed'] if a['id']=='inspection_hall_normal' else []
  seen.update(aliases)
  anchors.append({'instance':a['id'],'aliases':aliases,'label':names.get(a['id'],f"객실 {a['id'].split('_')[-1]}"),'anchor_uv':[x/W,y/H],'hit_rect_uv':[(x-w/2)/W,(y-d/2)/H,(x+w/2)/W,(y+d/2)/H],'mode':a['mode'],'locked_by_default':True,'runtime_visibility':'explicit story reveal/discovery/access flags; never reveal all rooms from this atlas'})
 p.save('실제 자체3D 배치에 대응하는 시설 연결 지도; 이름/얼굴/현재위치/잠김은 별도 층','지도 전환150ms; 미발견 시설과 미허용 연결은 숨김',key)
 with Image.open(O/(p.name+'.png')) as im:
  assert im.size==(W*4,H*4)
  with Image.open(O/(p.name+'.webp')) as wp:assert im.tobytes()==wp.tobytes()
  preview=im.resize((W,H),Image.Resampling.LANCZOS);draw=ImageDraw.Draw(preview);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',14)
  for a in anchors:
   x,y=a['anchor_uv'];draw.text((x*W,y*H),a['label'],font=font,anchor='mm',fill='#f3ead9',stroke_width=2,stroke_fill='#14131b')
  preview.convert('RGB').save(review/(key+'.jpg'),quality=95)
 records.append({**ui.records[-1],'anchors':anchors,'geometry_policy':'room footprints and center positions derive from the authored layout; thin connecting lines are schematic scene links, not collision corridors','map_label_layer':'engine text; labels only appear in QA preview','runtime_integrated':False})
assert seen=={a['id'] for a in layout['instances']},seen.symmetric_difference({a['id'] for a in layout['instances']})
(O/'manifest.json').write_text(json.dumps({'source_layout':layout_path.relative_to(R).as_posix(),'source_layout_sha256':hashlib.sha256(layout_path.read_bytes()).hexdigest(),'assets':records,'covered_instances':len(seen),'status':'PASS native4x PNG/WebP pixels and 62 instance anchors/alias coverage; not runtime access validation'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS',len(records),'editable map atlases,',len(seen),'instance anchors/aliases, native4x PNG/WebP')
