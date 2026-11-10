"""Finish missing UI art states using the existing editable vector art system."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
import make_v4_ui_batch as ui
R=Path(__file__).resolve().parents[1];ui.OUT=R/'ui/v4/completion_hd';ui.OUT.mkdir(parents=True,exist_ok=True);ui.SCALE=4;ui.records.clear()
P=ui.Plate;I,E,A,V,G=ui.INK,ui.PAPER,ui.RED,ui.VIOLET,ui.GREY
def shell(ident,w,h,state='idle',text=None):
 p=P(ident,w,h,text);c={'focus':V,'active':V,'selected':V,'hit':E,'miss':A,'locked':G,'disabled':G,'error':A,'new':A,'owned':E,'equipped':V}.get(state,E)
 p.poly([(15,5),(w-7,0),(w-1,h-18),(w-19,h-3),(2,h-1)],I)
 p.line([(23,15),(w-19,9),(w-14,h-27)],c,2)
 p.line([(18,h-14),(w-35,h-22)],c,4)
 p.poly([(9,20),(17,19),(11,h-27),(3,h-25)],c)
 return p,c
def save(p,role,state='base',event='actual state change'):
 p.save(role,'enter120ms out90ms; event='+event+'; reduced motion=crossfade70ms',state)
 ui.records[-1].update(event=event,meaning_not_color_only=True,mask_owner='engine widget',runtime_integrated=False)
def symbol(p,k,x,y,s,col):
 q=lambda pts:p.line([(x+a*s,y+b*s) for a,b in pts],col,max(2,s*3))
 if k=='next':p.poly([(x+8*s,y+8*s),(x+29*s,y+22*s),(x+8*s,y+36*s)],col)
 elif k=='previous':p.poly([(x+29*s,y+8*s),(x+8*s,y+22*s),(x+29*s,y+36*s)],col)
 elif k=='auto':q([(10,9),(30,22),(10,35),(10,9)]);q([(4,39),(35,39)])
 elif k=='skip':
  p.poly([(x+3*s,y+9*s),(x+18*s,y+22*s),(x+3*s,y+35*s)],col);p.poly([(x+19*s,y+9*s),(x+34*s,y+22*s),(x+19*s,y+35*s)],col)
 elif k=='log':
  for n in range(3):q([(5,10+n*12),(34,10+n*12)])
 elif k=='help':q([(9,12),(12,5),(28,5),(33,12),(29,19),(20,24),(20,29)]);p.box(x+18*s,y+34*s,4*s,4*s,col)
 elif k=='cancel':q([(8,8),(32,36)]);q([(32,8),(8,36)])
 elif k=='confirm':q([(5,23),(16,34),(35,8)])
 elif k=='lock':q([(10,20),(10,10),(15,5),(26,5),(31,10),(31,20)]);q([(6,20),(35,20),(35,39),(6,39),(6,20)])
 elif k=='new':p.poly([(x+20*s,y+3*s),(x+26*s,y+15*s),(x+38*s,y+21*s),(x+26*s,y+26*s),(x+20*s,y+40*s),(x+14*s,y+26*s),(x+2*s,y+21*s),(x+14*s,y+15*s)],col)
 elif k=='hold':q([(5,22),(35,22)]);p.box(x+4*s,y+12*s,5*s,20*s,col);p.box(x+31*s,y+12*s,5*s,20*s,col)
 elif k=='release':q([(5,30),(20,10),(35,30)]);q([(20,10),(20,38)])
 elif k=='repeat':q([(7,17),(10,8),(30,8),(34,15),(34,30),(10,30)]);q([(10,30),(16,23)]);q([(10,30),(16,37)])
 elif k=='key':q([(3,11),(37,11),(37,34),(3,34),(3,11)]);q([(10,29),(30,29)])
 elif k=='gamepad':q([(6,12),(34,12),(39,33),(31,37),(26,29),(14,29),(9,37),(1,33),(6,12)]);q([(9,17),(9,26)]);q([(5,21),(14,21)]);p.box(x+28*s,y+18*s,4*s,4*s,col)
 elif k=='unbound':q([(7,22),(33,22)])

def make():
 for kind in ['auto','skip','log','help','confirm','cancel','next','previous']:
  for state in ['idle','focus','active','disabled']:
   p,c=shell('control_'+kind+'_'+state,176,68,state,[61,17,93,36]);symbol(p,kind,21,13,.85,c)
   if state=='active':p.line([(71,49),(147,45)],V,3)
   save(p,'진행 제어 '+kind+'; 허용/선택/작동/불가를 분리',state,kind+' permission/activation')
 for chapter,col in enumerate([A,'#5fabb0',V,'#c8a46b','#7d9eb1',E],1):
  p,c=shell(f'chapter_header_{chapter}',1120,120,text=[95,24,910,68]);p.poly([(27,34),(66,13),(82,83),(41,105)],col);p.line([(96,101),(1082,91)],col,4);save(p,'장 제목 헤더; 제목/번호는 별도 텍스트',str(chapter),'chapter start')
 for family,states in [('gift_slot',['owned','unowned','selected','disabled']),('profile_slot',['alive','unmet','memorial','focus']),('chapter_select',['locked','available','cleared','focus']),('gallery_slot',['locked','available','new','focus']),('comic_candidate',['available','selected','used','locked']),('ammo_slot',['normal','note','magic','rule'])]:
  for state in states:
   p,c=shell(family+'_'+state,300,218,state,[31,158,237,37]);p.line([(25,147),(273,139)],G,1)
   p.line([(34,29),(256,21),(249,132),(28,139),(34,29)],c,2)
   if state in ['locked','unmet','unowned','disabled']:symbol(p,'lock',115,55,1.5,G)
   if state in ['new','cleared','selected','used','memorial']:
    symbol(p,'cancel' if state=='memorial' else 'confirm' if state in ['cleared','used'] else 'new',229,24,.65,c)
   if family=='ammo_slot':
    p.poly([(47,67),(65,44),(136,44),(156,65),(136,89),(65,89)],c)
    if state=='note':p.line([(74,56),(126,56)],I,3)
    elif state=='magic':p.poly([(101,47),(112,66),(101,86),(91,66)],I)
    elif state=='rule':p.line([(84,49),(84,83)],I,4);p.line([(117,49),(117,83)],I,4)
   save(p,family+' 상태; 실제 그림·이름은 마스크/텍스트 별도',state,family+' actual state')
 for family,states in [('setting_row',['idle','focus','disabled','conflict']),('save_status',['busy','error','overwrite']),('skill_capacity',['available','full','focus']),('backlog_voice',['playing','paused','unavailable'])]:
  for state in states:
   p,c=shell(family+'_'+state,950,114,state,[92,25,810,59]);symbol(p,'cancel' if state in ['error','conflict','full'] else 'hold' if state=='paused' else 'confirm' if state=='available' else 'next',29,29,1,c);save(p,family+' 보조 상태판',state,family+' actual state')
 for part in ['track','fill','thumb_idle','thumb_focus']:
  w,h=(640,52) if part in ['track','fill'] else (46,66);p=P('slider_'+part,w,h)
  if part=='track':p.poly([(10,23),(w-2,11),(w-9,34),(1,47)],I);p.line([(17,29),(w-15,20)],G,4)
  elif part=='fill':p.poly([(10,23),(w-2,11),(w-9,24),(1,37)],V)
  else:p.poly([(22,2),(44,24),(28,64),(2,44)],E if part.endswith('idle') else V);p.line([(13,32),(29,28)],I,3)
  save(p,'음량/속도/감도 공용 슬라이더; fill은 왼쪽 기준 clip',part,'actual option value')
 for family in ['toggle','radio']:
  for state in ['off','on','disabled']:
   p,c=shell(family+'_'+state,126,62,'disabled' if state=='disabled' else 'focus' if state=='on' else 'idle');symbol(p,'confirm' if state=='on' else 'unbound',44,10,.9,c);save(p,'옵션 '+family,state,'actual option bool')
 for k in ['key','gamepad','unbound','hold','release','repeat']:
  p,c=shell('input_badge_'+k,112,82);symbol(p,k,29,17,1.1,c);save(p,'논리 입력 안내; 실제 키명은 엔진에서 별도',k,'input binding')
 for side,angle in [('up',-math.pi/2),('down',math.pi/2),('left',math.pi),('right',0),('center',None)]:
  p,c=shell('scrum_direction_'+side,124,124,'focus')
  if angle is None:p.poly([(62,30),(92,62),(62,94),(32,62)],E)
  else:
   pts=[(-31,-12),(5,-12),(5,-25),(35,0),(5,25),(5,12),(-31,12)];p.poly([(62+x*math.cos(angle)-y*math.sin(angle),62+x*math.sin(angle)+y*math.cos(angle)) for x,y in pts],E)
  save(p,'대립 후반 방향 입력5종; 판정과 분리',side,'scrum direction cue')
 for typ in ['standard','hold_head','hold_body','hold_tail','release','repeat']:
  for state in ['waiting','active','hit','miss']:
   p,c=shell('armor_note_'+typ+'_'+state,132,140,'idle' if state=='waiting' else state);col=G if state=='waiting' else c
   if typ=='standard':p.poly([(66,29),(107,70),(66,111),(25,70)],col)
   elif typ=='hold_body':p.poly([(48,8),(92,8),(81,129),(37,129)],col);p.line([(60,20),(55,114)],I,4)
   elif typ=='hold_tail':p.poly([(36,28),(96,28),(84,99),(64,120),(44,99)],col)
   else:symbol(p,'hold' if typ=='hold_head' else typ,35,42,1.55,col)
   if state=='hit':symbol(p,'confirm',86,97,.65,V)
   if state=='miss':symbol(p,'cancel',86,97,.65,A)
   save(p,'무장 노트 '+typ+'; 입력 종류와 판정 시각을 분리',state,typ+' note state')
 for family in ['showdown_power','lie_cost','armor_tension','armor_fever','opponent_health']:
  for part in ['track','fill']:
   p=P(family+'_'+part,540,54)
   p.poly([(15,8),(538,0),(525,41),(1,53)],I)
   if part=='fill':p.poly([(26,17),(522,9),(515,29),(16,41)],V if family!='lie_cost' else A)
   else:
    p.line([(26,17),(522,9),(515,29),(16,41),(26,17)],E,2)
    for x in range(85,510,85):p.line([(x,9),(x-4,45)],G,1)
   save(p,family+' 실제값 게이지; fill을 clip',part,family+' actual value')
 for state in ['normal','special','selected','broken']:
  p=P('anagram_orb_'+state,164,164,[41,39,82,85]);col={'normal':E,'special':V,'selected':A,'broken':G}[state]
  pts=[(82+70*math.cos(i*math.tau/48),82+70*math.sin(i*math.tau/48)) for i in range(49)];p.poly(pts,I);p.line(pts,col,4);p.line([(40,32),(58,22),(74,19)],col,5)
  if state=='special':symbol(p,'new',51,49,1.5,col)
  if state=='broken':p.line([(65,16),(72,63),(50,88),(95,146)],G,4)
  save(p,'글자 구슬; 실제 글자/특수 종류는 데이터',state,'anagram ball state')
 for state in ['hidden','exposed','selected','wrong']:
  p,c=shell('mindmine_cell_'+state,190,190,'miss' if state=='wrong' else 'focus' if state=='selected' else 'idle')
  if state=='hidden':
   p.poly([(34,56),(95,23),(156,49),(95,84)],V);p.poly([(34,56),(95,84),(95,153),(34,121)],G);p.poly([(95,84),(156,49),(156,119),(95,153)],E)
  elif state=='wrong':symbol(p,'cancel',58,61,1.8,A)
  else:p.line([(32,33),(158,25),(151,153),(25,160),(32,33)],c,3)
  save(p,'발굴 블록/노출/제출 상태; 노출은 정답과 별개',state,'mindmine state')
 for state in ['waiting','picked','seated','missed']:
  p,c=shell('drive_passenger_'+state,300,112,state,[108,26,164,55]);p.line([(51,23),(70,23),(79,42),(70,57),(49,57),(40,42),(51,23)],c,3);p.line([(33,89),(37,71),(84,71),(90,88)],c,4);save(p,'주행 질문 승객 상태; 실제 질문은 별도',state,'passenger state')
 for part in ['speed_dial','speed_needle','question_face','answer_marker']:
  p,c=shell('drive_'+part,280,170,text=[59,43,161,79] if part in ['question_face','speed_dial'] else None)
  if part=='speed_dial':
   for i in range(11):
    a=math.pi+i*math.pi/10;p.line([(140+69*math.cos(a),132+69*math.sin(a)),(140+85*math.cos(a),132+85*math.sin(a))],E,3)
  elif part=='speed_needle':p.poly([(131,134),(151,134),(136,30)],A)
  elif part=='answer_marker':p.poly([(43,35),(85,85),(43,133),(103,127),(145,83),(101,37)],V)
  save(p,'주행 '+part+'; 수치/질문/선택은 엔진 표시',part,'drive state')
 for state in ['idle','focus','selected','deceased','hidden']:
  p,c=shell('vote_portrait_'+state,250,300,state,[25,245,199,34]);p.line([(25,26),(222,18),(216,229),(17,237),(25,26)],c,3)
  if state=='deceased':p.line([(44,49),(198,207)],G,5);p.line([(198,42),(39,215)],G,5)
  if state=='hidden':symbol(p,'lock',89,92,1.65,G)
  save(p,'투표 초상 슬롯; 실제 인물/생존/지목 대상은 별도',state,'vote candidate state')
 for rank,col in [('s',V),('a',E),('b','#c8a46b'),('c',G)]:
  p=P('result_medal_'+rank,220,236,[66,73,89,82]);p.poly([(61,145),(48,226),(108,200),(160,224),(157,143)],A);p.poly([(110,5),(195,52),(193,146),(110,190),(24,144),(23,52)],I);p.line([(110,22),(178,61),(178,135),(110,171),(41,134),(40,61),(110,22)],col,6);save(p,'정산 등급 메달; 등급 문자는 별도',rank,'result rank')
 for kind in ['loading_spinner','page_dots','new_badge','investigation_done','evidence_updated','free_time_end','chapter_end','trial_open','trial_close','discovery_banner']:
  w,h=(160,160) if kind=='loading_spinner' else (700,124);p,c=shell(kind,w,h,text=None if kind=='loading_spinner' else [83,27,553,65])
  if kind=='loading_spinner':
   for i in range(8):
    a=i*math.tau/8;p.line([(80+44*math.cos(a),80+44*math.sin(a)),(80+63*math.cos(a),80+63*math.sin(a))],E if i<3 else G,7)
  else:symbol(p,'new' if 'new' in kind or 'updated' in kind else 'confirm',24,34,1.1,V)
  save(p,'전환/완료 '+kind+'; 문구·진입 시점은 실제 이벤트에 연결',kind,kind+' resolved event')
 manifest={'scale':4,'text_baked':False,'status':'original editable UI states, runtime integration separate','assets':ui.records,'runtime_tested':False}
 (ui.OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 review=R/'Game/Saved/v4-completion-ui';review.mkdir(parents=True,exist_ok=True)
 for start in range(0,len(ui.records),30):
  page=Image.new('RGB',(1500,1080),'#61596b');d=ImageDraw.Draw(page)
  for i,a in enumerate(ui.records[start:start+30]):
   with Image.open(R/a['file']) as im:
    im.thumbnail((285,139));x=i%5*300+6;y=i//5*180+5;page.paste(im,(x,y),im);d.text((x,y+146),a['id'],fill='white')
  page.save(review/f'states_{start//30+1:02d}.jpg',quality=96)
 print('Exported',len(ui.records),'additional editable native4x UI states',flush=True)
if __name__=='__main__':make()
