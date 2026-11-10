"""Exact-count documentary reconstruction art. Never invent extra witnesses or resurrect document owners."""
from pathlib import Path
import json,math,html
from PIL import Image,ImageFont
import make_v4_ui_batch as u
R=Path(__file__).resolve().parents[1];O=R/'ui/v4/reconstruction_diagrams_hd';O.mkdir(parents=True,exist_ok=True);u.OUT=O;u.SCALE=4;u.records.clear();font=R/'fonts/pretendard/Pretendard-Regular.otf'
contracts=json.loads((R/'art/v4_production/completion/comic_contracts.json').read_text(encoding='utf8'))['slots'];records=[]
def label(p,t,x,y,size=26):
 p.draw.text((x*4,y*4),t,font=ImageFont.truetype(str(font),size*4),fill='#29232e');p.svg.append(f'<text x="{x}" y="{y+size*.87}" font-family="Pretendard" font-size="{size}" fill="#29232e">{html.escape(t)}</text>')
def arrow(p,a,b):
 p.line([a,b],'#9770cf',6);x,y=b;p.poly([(x,y),(x-15,y-10),(x-15,y+10)],'#9770cf')
def doc(p,x,y,w=150,h=180,state=None):
 p.poly([(x,y),(x+w-20,y),(x+w,y+20),(x+w,y+h),(x,y+h)],'#ded1bc');p.line([(x+15,y+35),(x+w-20,y+35)],'#29232e',3)
 for yy in range(y+62,y+h-20,23):p.line([(x+17,yy),(x+w-25,yy)],'#b1a08d',2)
 if state=='check':p.line([(x+45,y+h-45),(x+61,y+h-30),(x+100,y+h-80)],'#9770cf',7)
 if state=='question':label(p,'?',x+w//2-10,y+h//2-5,55)
def person(p,x,y,col='#29232e',hollow=False):
 pts=[(x+12*math.cos(i*math.tau/24),y+12+12*math.sin(i*math.tau/24)) for i in range(24)]
 if hollow:p.line(pts+[pts[0]],col,2);p.line([(x-17,y+62),(x-13,y+30),(x+13,y+30),(x+17,y+62)],col,3)
 else:p.poly(pts,col);p.poly([(x-13,y+30),(x+13,y+30),(x+18,y+63),(x-18,y+63)],col)
def row(p,count,x,y,step=47,accent_first=False,hollow_last=False):
 for i in range(count):person(p,x+i*step,y,'#9770cf' if accent_first and i==0 else '#29232e',hollow=hollow_last and i==count-1)
def shell(ident):
 p=u.Plate(ident,960,540);p.box(2,2,956,536,'#f3ead9');p.line([(12,12),(948,12),(948,528),(12,528),(12,12)],'#29232e',5);return p
for slot in [1,4,6,7,8]:
 source=next(x for x in contracts if x['chapter']==6 and x['slot']==slot)
 for opt in source['options']:
  key=opt['key']
  if slot==8 and key!='A':continue
  ident=f'comic_c6_slot{slot:02d}_{key}_diagram';p=shell(ident);semantics={}
  if slot==1:
   if key=='A':doc(p,105,155,state=None);label(p,'시험 진술',110,350);arrow(p,(285,250),(555,250));doc(p,615,155,state='check');label(p,'최종 승인',620,350)
   elif key=='B':
    for i in range(3):doc(p,90+i*280,155,state='check')
    arrow(p,(260,250),(360,250));arrow(p,(540,250),(640,250));label(p,'검토 해결',95,355);label(p,'승인',385,355);label(p,'정상 인수',655,355)
   else:
    for i,st in enumerate(['question','check','check','question']):doc(p,45+i*230,160,150,170,st)
    for i in range(3):arrow(p,(205+i*230,245),(260+i*230,245))
    for i,t in enumerate(['유보','완료 수정','최종 정상','인수 미해결']):label(p,t,48+i*230,360,25)
  elif slot==4:
   if key=='A':p.line([(100,180),(395,180),(395,370),(100,370),(100,180)],'#29232e',7);label(p,'진술 없음',165,265,32);arrow(p,(445,270),(585,270));doc(p,650,170,state='question')
   elif key=='B':
    for i in range(13):p.poly([(130+i*15,165),(140+i*15,165),(185+i*15,370),(175+i*15,370)],'#b1a08d')
    arrow(p,(430,270),(580,270));p.line([(620,180),(850,180),(850,370),(620,370),(620,180)],'#29232e',7);label(p,'원본 없음',660,270,29)
   else:doc(p,130,140,230,220,'check');doc(p,610,140,230,220,'question');label(p,'접수된 진술',155,385,29);label(p,'다른 요약',650,385,29);p.line([(480,170),(480,395)],'#9770cf',4)
  elif slot==6:
   if key=='A':label(p,'코토',85,170,32);arrow(p,(180,205),(285,205));row(p,14,290,180,37);arrow(p,(740,315),(845,315));label(p,'나나',790,355,31);semantics={'counterfactual_order':'Koto gathers first -> Nana directed later'}
   elif key=='B':
    label(p,'선행 접수 14',60,90,29);row(p,14,75,145,60,True);label(p,'나나 포함',60,225,27);row(p,13,110,300,55);label(p,'자신을 제외한 13',60,390,28);label(p,'그 뒤 코토 · 별도 맹세',600,455,24);semantics={'initial_count':14,'initial_includes_nana':True,'memory_targets':13,'nana_targets_self':False,'koto_arrival':'later'}
   else:doc(p,80,160,state=None);label(p,'지워진 기억',85,370,27);arrow(p,(270,250),(410,250));p.line([(445,180),(500,230),(445,280),(500,330)],'#9770cf',6);arrow(p,(550,250),(650,250));doc(p,725,160,state='check');label(p,'원래대로 복원',705,370,25)
  elif slot==7:
   if key=='A':row(p,16,70,200,54,True);label(p,'처음부터 실제 16',300,340,32);semantics={'counterfactual_actual_arrival':16}
   elif key=='B':label(p,'나나',75,235,32);arrow(p,(195,265),(395,265));person(p,510,220,'#9770cf');label(p,'새 하루카',445,330,30);p.line([(660,155),(840,155),(880,200),(880,370),(660,370),(660,155)],'#29232e',5);label(p,'방 구조',690,390,27)
   else:
    for count,y,t in [(16,95,'요청 16'),(15,245,'실제 도착 15'),(16,395,'레이 생성 뒤 16')]:
     label(p,t,35,y+14,26);row(p,count,280,y,39,False,hollow_last=y==95)
    semantics={'requested':16,'arrived':15,'generated_Haruka':1,'after_generation':16,'original_arrival_contains_Haruka':False}
  else:
   label(p,'래피의 현재 운영',60,90,32)
   for i,t in enumerate(['감금','조건부 공개','처형']):doc(p,65+i*300,175,200,170);label(p,t,85+i*300,370,30)
   label(p,'각 살인의 행위와 구분',60,450,27);label(p,'마지막 지목: 과거 행위자',510,450,26);semantics={'operator_not_victim':True,'current_murders_separate':True,'final_nomination':'past direct actor, not arbitrary substitute'}
  p.save('source-bound documentary reconstruction candidate '+key,'static; caption must remain visible')
  a=u.records[-1];a.update(chapter=6,slot=slot,key=key,source_document=source['source'],source_sha256=source['source_sha256'],caption=opt['description'],caption_required=True,correct_key=source['correct_key'],semantic_values=semantics,text_baked=True,art_type='original editable reconstruction diagram, NOT an in-world historical document/photograph',replaces='generated crowd counts/owners and agency where illustration was ambiguous or wrong',runtime_integrated=False);records.append(a)
  path=O/(ident+'.svg');svg=path.read_text(encoding='utf8');svg=svg.replace('>', '><style>@font-face{font-family:Pretendard;src:url(../../../fonts/pretendard/Pretendard-Regular.otf)}</style>',1);path.write_text(svg,encoding='utf8')
source=next(x for x in contracts if x['chapter']==5 and x['slot']==6);opt=next(x for x in source['options'] if x['key']=='A');p=shell('comic_c5_slot06_A_diagram')
for char,x in [('akari',45),('satsuki',735)]:
 path=R/'art/character_delivery_v4/portraits'/(char+'.png');im=Image.open(path).convert('RGBA').resize((180*4,180*4),Image.Resampling.LANCZOS);p.im.alpha_composite(im,(x*4,55*4));p.svg.append(f'<image href="../../../art/character_delivery_v4/portraits/{char}.png" x="{x}" y="55" width="180" height="180"/>')
for i in range(3):doc(p,285+i*135,100,110,145);label(p,str(i+1),320+i*135,265,25)
arrow(p,(220,180),(275,180));arrow(p,(690,180),(735,180));label(p,'전체 세 쪽 제시',340,325,30);p.line([(275,370),(460,370)],'#29232e',6);p.line([(505,370),(690,370)],'#29232e',6);label(p,'새 선 종료',375,392,29)
arrow(p,(700,430),(790,430));p.box(820,385,28,100,'#ded1bc');p.box(815,375,38,18,'#29232e');label(p,'그 뒤 D 이동',680,485,26)
p.save('exact3-page disclosure -> new oath ends -> later D custody; source caption required','static')
a=u.records[-1];a.update(chapter=5,slot=6,key='A',source_document=source['source'],source_sha256=source['source_sha256'],caption=opt['description'],caption_required=True,correct_key='A',semantic_values={'full_statement_pages':3,'new_oath_end':'after full disclosure, not automatic death','D_transfer':'later'},text_baked=True,art_type='original editable documentary reconstruction diagram; portraits are identity legend, not a new physical scene',runtime_integrated=False);records.append(a)
(O/'manifest.json').write_text(json.dumps({'scale':4,'assets':records,'tool':'original editable vector/PIL native4x, not a raster edit','caption_required':True,'runtime_integrated':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Created',len(records),'exact-semantic reconstruction diagrams')
