"""Editable full-screen asset layouts plus populated Korean legibility proofs, not game screens."""
from pathlib import Path
import json,html,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'ui/v4/layouts_hd';O.mkdir(parents=True,exist_ok=True);Q=R/'Game/Saved/v4-ui-layouts';Q.mkdir(parents=True,exist_ok=True)
assets={}
for f in ['hd','systems_hd','trial_hd','completion_hd','brand_hd']:
 for a in json.loads((R/'ui/v4'/f/'manifest.json').read_text(encoding='utf8'))['assets']:assets[a['id']]=a
font=R/'fonts/pretendard/Pretendard-Regular.otf';bold=R/'fonts/blackhansans/BlackHanSans-Regular.ttf';screens=[]
class Screen:
 def __init__(self,ident,title,bg='hotel_lobby_day'):
  self.id=ident;self.layers=[];self.fields=[];self.svg=[];self.im=Image.open(R/'art/bg_v4/plates_r4'/(bg+'.png')).convert('RGBA').resize((1920,1080));self.im.alpha_composite(Image.new('RGBA',self.im.size,(15,11,23,145 if ident!='dialogue' else 10)))
  self.svg.append('<rect width="1920" height="1080" fill="#14131b"/>');self.text(title,105,60,52,True,'screen_title')
 def text(self,t,x,y,size=31,heading=False,key=None,width=1600,color='#f3ead9'):
  f=ImageFont.truetype(str(bold if heading else font),size);d=ImageDraw.Draw(self.im);lines=[];line=''
  for c in t:
   if c=='\n' or d.textlength(line+c,font=f)>width:lines.append(line);line='' if c=='\n' else c
   else:line+=c
  if line:lines.append(line)
  for i,line in enumerate(lines):d.text((x,y+i*(size+9)),line,font=f,fill=color)
  self.fields.append({'id':key or 'label_'+str(len(self.fields)),'rect':[x,y,width,len(lines)*(size+9)],'font':str((bold if heading else font).relative_to(R)).replace('\\','/'),'font_size':size,'color':color,'fixture_only':t,'dynamic_text':True});assert x>=0 and y>=0 and x+width<=1920 and y+len(lines)*(size+9)<=1080,(self.id,t)
 def layer(self,ident,x,y,w=None,caption=None):
  a=assets[ident];lw,lh=a['logical_size'];w=w or lw;h=round(lh*w/lw);x=round(x);y=round(y);w=round(w);assert x>=0 and y>=0 and x+w<=1920 and y+h<=1080,(self.id,ident,x,y,w,h)
  im=Image.open(R/a['file']).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS);self.im.alpha_composite(im,(x,y));self.layers.append({'asset':ident,'file':a['file'],'rect':[x,y,w,h],'z':len(self.layers)+1,'aspect':'uniform scale','runtime_state':'provided by engine, not inferred by image'})
  href='../../../'+a['file'];self.svg.append(f'<image href="{html.escape(href)}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')
  if caption and a.get('text_rect'):
   tx,ty,tw,th=a['text_rect'];scale=w/lw;size=max(22,min(34,round(th*scale*.58)));self.text(caption,round(x+tx*scale),round(y+ty*scale),size,width=round(tw*scale),key=ident+'_text_'+str(len(self.fields)),color='#14131b' if ident=='comic_caption' or ident.startswith('dialogue_') else '#f3ead9')
 def save(self):
  self.im.convert('RGB').save(Q/(self.id+'.jpg'),quality=96);p=O/(self.id+'.svg');p.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="7680" height="4320" viewBox="0 0 1920 1080">'+''.join(self.svg)+'</svg>\n',encoding='utf8');screens.append({'id':self.id,'source':p.relative_to(R).as_posix(),'logical_size':[1920,1080],'native_vector_size':[7680,4320],'layers':self.layers,'text_fields':self.fields,'fixture_image':(Q/(self.id+'.jpg')).relative_to(R).as_posix(),'font_policy':'project OFL fonts, text separate from plates','runtime_integrated':False})
s=Screen('title','', 'park_night');s.layer('yumeno_wordmark',90,145,1200)
for i,t in enumerate(['처음부터','이어하기','기록 보기','설정']):s.layer('choice_focus' if i==1 else 'choice_idle',130,510+i*122,760,t)
s.save()
s=Screen('dialogue','', 'hotel_lobby_day');s.layer('dialogue_daily',100,825);s.layer('nameplate_daily',120,760,390,'미오');s.text('같이 가겠다고 대답한 적은 없어.\n지금 내가 어디까지 들었는지부터 말할게.',200,865,34,width=1480,color='#14131b')
for i,k in enumerate(['auto','skip','log','help']):s.layer('control_'+k+'_idle',1050+i*190,740,176)
s.save()
s=Screen('settings','설정')
for i,t in enumerate(['전체 음량','배경음악','효과음','글자 표시 속도','화면 흔들림 줄이기','입력 설정']):
 s.layer('setting_row_focus' if i==2 else 'setting_row_idle',130,190+i*144,1170,t)
 if i<4:s.layer('slider_track',900,230+i*144,300);s.layer('slider_fill',900,230+i*144,190)
 elif i==4:s.layer('toggle_off',1030,225+i*144,160)
 else:s.layer('input_badge_key',1080,225+i*144,100)
s.save()
s=Screen('save_load','저장 · 불러오기')
for i,t in enumerate(['선택한 기록을 불러와요','비어 있는 저장 위치','현재 버전과 맞지 않는 기록']):s.layer(['save_slot_selected','save_slot_empty','save_slot_incompatible'][i],150,200+i*240,1510,t)
s.save()
s=Screen('pad_home','래피패드');s.layer('pad_shell',170,140,1580)
for i,k in enumerate(['map','profile','evidence','gift','skills','save','settings','backlog']):
 x=220+i%4*400;y=260+i//4*330;s.layer('icon_'+k,x,y,150);s.text({'map':'지도','profile':'인물','evidence':'조사 기록','gift':'선물','skills':'스킬','save':'저장','settings':'설정','backlog':'대화 기록'}[k],x,y+170,32,width=280)
s.save()
for ident,title,plate in [('profile','인물 기록','profile_detail'),('evidence','조사 기록','evidence_detail')]:
 s=Screen(ident,title);s.layer(plate,180,180,900);s.text('아직 확인하지 않은 항목',1140,285,36,width=650);s.text('공개된 정보와 직접 확인한 내용을 구분해 표시해요.',1140,395,31,width=650);s.save()
for ident,title,family in [('gifts','선물','gift_slot'),('skills','장착할 스킬','skill_card'),('gallery','장면 기록','gallery_slot'),('chapter_select','장 선택','chapter_select')]:
 s=Screen(ident,title)
 for i in range(8):
  if family=='skill_card':state=['idle','equipped','unavailable'][i%3]
  elif family=='gift_slot':state=['owned','selected','unowned'][i%3]
  elif family=='chapter_select':state=['available','focus','locked'][i%3]
  else:state=['available','focus','locked'][i%3]
  if family=='skill_card':s.layer(family+'_'+state,170+i%2*840,200+i//2*205,750)
  else:s.layer(family+'_'+state,170+i%4*430,220+i//4*375,365)
 s.save()
s=Screen('backlog','대화 기록')
for i,t in enumerate(['같이 봤다는 것과 전부 확인했다는 건 달라.','그 말은 내가 직접 들은 건 아니에요.','지금 고치면 이전에 쓴 말도 함께 남길게.']):s.layer('backlog_row_focus' if i==1 else 'backlog_row_idle',140,190+i*270,1580,t)
s.save()
# The following are separate authored overlay layouts; current game renderer is not exercised.
for mode,title in [('nonstop','논의'),('panic','동시 논의'),('showdown','반론'),('scrum','대립'),('armor','리듬 논박'),('anagram','문자 조합'),('drive','질문과 경로'),('mindmine','그림 발굴'),('comic','사건 재구성'),('result','재판 기록')]:
 s=Screen(mode,title,'operating_archive');s.layer('trial_health_track',100,155,400);s.layer('trial_health_fill',100,155,300);s.layer('trial_timer',1510,130,280)
 if mode in ['nonstop','panic','showdown']:
  for i in range(3):s.layer('statement_band_weak' if i==1 else 'statement_band_normal',280+i*70,290+i*170,1200,['아직 확인하지 않은 전제','그때 보았다는 말의 범위','다른 가능성과 비교'][i])
  s.layer('ammo_card',110,840,760,'확인한 조사 기록')
 elif mode=='scrum':
  for i in range(3):
   y=285+i*220;s.layer('scrum_endpoint_candidate',100,y,110);s.layer('statement_band_normal',230,y+15,570);s.layer('statement_band_normal',1120,y+15,570);s.layer('scrum_endpoint_target',1720,y,110)
  s.layer('scrum_direction_up',860,420,150)
 elif mode=='armor':
  for i in range(6):s.layer('armor_note_standard_active' if i%2 else 'armor_note_hold_head_waiting',210+i*260,300+(i%3)*130,115)
  s.layer('armor_tension_track',200,820,1150);s.layer('armor_tension_fill',200,820,680)
 elif mode=='anagram':
  for i in range(6):s.layer('anagram_orb_selected' if i==2 else 'anagram_orb_normal',180+i*270,410,160);s.text('가나다라마바사'[i],230+i*270,455,50,width=70)
 elif mode=='drive':
  s.layer('drive_question_face',660,245,600,'지금 확인해야 할 것은?');s.layer('route_prompt_left',150,690,600);s.layer('route_prompt_right',1170,690,600);s.layer('drive_speed_dial',810,820,300)
 elif mode=='mindmine':
  for i in range(24):s.layer('mindmine_cell_selected' if i==7 else 'mindmine_cell_hidden',370+i%6*195,255+i//6*177,160)
 elif mode=='comic':
  for i in range(6):s.layer('comic_slot_focus' if i==2 else 'comic_slot_empty',140+i%3*570,245+i//3*280,510)
  s.layer('comic_caption',540,835,840,'선택한 조각의 설명을 확인해 주세요')
 else:s.layer('trial_result',250,210,1250);s.layer('result_medal_a',1510,480,270)
 s.save()
(O/'manifest.json').write_text(json.dumps({'scope':'editable full-screen asset layouts and Korean text fixtures, NOT game screenshots or working menus','screens':screens,'runtime_integrated':False,'claims_excluded':['HB widget creation','live input/masking','save interaction','actual trial decisions'],'coordinate_system':'1920x1080 logical top-left pixels, SVG native4x; preserve actual engine layers'},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Created',len(screens),'editable UI layouts + populated review images')
