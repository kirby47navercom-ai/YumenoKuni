"""Editable source-grounded document details and nonviolent reconstruction diagrams."""
from pathlib import Path
import json,hashlib,html
from PIL import Image,ImageFont,ImageChops,ImageDraw
import make_v4_ui_batch as u
R=Path(__file__).resolve().parents[1];O=R/'ui/v4/documents_hd';O.mkdir(parents=True,exist_ok=True);u.OUT=O;u.SCALE=4;u.records.clear();S=4
FONT=R/'fonts/pretendard/Pretendard-Regular.otf'
def txt(p,text,x,y,size=32,col='#29232e'):
 p.draw.text((x*S,y*S),text,font=ImageFont.truetype(str(FONT),size*S),fill=col)
 p.svg.append(f'<text x="{x}" y="{y+size*.87}" font-family="Pretendard" font-size="{size}" fill="{col}">{html.escape(text)}</text>')
def paper(ident,title):
 p=u.Plate(ident,800,1040,[70,150,650,800]);p.poly([(30,18),(770,18),(768,1018),(30,1024)],'#f3ead9');p.line([(52,37),(747,37),(746,995)],'#c4b7a5',2);txt(p,title,68,65,35);p.line([(66,125),(730,125)],'#4c4053',2)
 return p
rows=[
 ('report_16_excerpt','16','11b_1장_수사_초고.md',['16'], 'E1-04; print identity only, no invented full report'),
 ('report_17_excerpt','17','11b_1장_수사_초고.md',['17','작동 확인 불가'], 'E1-04/05/06; confirmed printed fragment, NOT full fabricated report'),
 ('printer_order_excerpt','출력 목록','11b_1장_수사_초고.md',['16','17'], 'E1-04; completion order only, no author/time field invented'),
 ('observation_summary_excerpt','레이·린과 확인','11b_1장_수사_초고.md',['관찰','작동','일부 문'], 'E1-12; actual quoted heading, annotations remain separate'),
 ('document_original','원문','11_6장_과거와현재_원장_스포주의.md',[], 'inspection viewer heading, not physical historical document title'),
 ('document_summary','요약','11_6장_과거와현재_원장_스포주의.md',[], 'inspection viewer heading, different from original'),
 ('entry_ledger','접수 목록','11_6장_과거와현재_원장_스포주의.md',[], 'distinct ledger form; record rows supplied by verified story data'),
 ('allocation_grid','배정표','11_6장_과거와현재_원장_스포주의.md',[], 'distinct allocation form, NEVER interpreted as arrival list'),
 ('statement_sheet','진술','11_6장_과거와현재_원장_스포주의.md',[], 'statement body stays engine text; no invented confession'),
 ('contract_three_pages','전체 문서','10_5장_정보와행위_원장_스포주의.md',[], 'three page tabs1..3, no unsupported legal terms/signatures'),
 ('control_separation','현재 상태','11_6장_과거와현재_원장_스포주의.md',['출입·연락 통제','의식 지원'], 'player inspection overlay, separate fields and values'),
 ('evidence_custody','보관','11b_1장_수사_초고.md',['원본','조각'], 'viewer annotation fields: two different custodians, never merged record')]
sources={}
for ident,title,name,content,role in rows:
 source=R/'docs/design/rewrite_v4'/name;text=source.read_text(encoding='utf8');p=paper(ident,title)
 for i,v in enumerate(content):txt(p,v,85,205+i*90,42 if ident=='report_17_excerpt' else 34)
 if ident=='allocation_grid':
  for x in [75,220,365,510,720]:p.line([(x,190),(x,900)],'#b3a18f',1)
  for y in range(190,901,100):p.line([(75,y),(720,y)],'#b3a18f',1)
 elif ident in ['entry_ledger','statement_sheet','evidence_custody']:
  for y in range(350,901,85):p.line([(78,y),(719,y)],'#b3a18f',1)
 if ident=='contract_three_pages':
  for i in range(3):p.box(90+i*210,200,180,62,'#d6c5af');txt(p,str(i+1),160+i*210,211,30)
 p.save(role,'document viewer fade100ms; text and pan stay stable')
 rec=u.records[-1];rec.update(text_baked=True,source_document=source.relative_to(R).as_posix(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),diegetic_status='quoted excerpt only' if ident.startswith(('report_','printer_','observation_')) else 'player inspection overlay, NOT historical physical wording',body_policy='Only explicitly supplied/quoted fields are filled; full prose is not invented. Engine binds verified manuscript text into text_rect.',printed_fields=content)
 # Current SVG retains editable glyphs and an explicit project font link.
 path=O/(ident+'.svg');svg=path.read_text(encoding='utf8');svg=svg.replace('>', '><style>@font-face{font-family:Pretendard;src:url(../../../fonts/pretendard/Pretendard-Regular.otf)}</style>',1);path.write_text(svg,encoding='utf8')
manifest={'scale':4,'assets':list(u.records),'runtime_integrated':False,'claims_excluded':['invented full legal/forensic document text','runtime dynamic text proof']}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

# A safe, source-faithful alternative to depicting the bodily incident: causal/evidence diagrams.
u.OUT=R/'ui/v4/comic_diagrams_hd';u.OUT.mkdir(parents=True,exist_ok=True);u.records.clear()
j=json.loads((R/'art/v4_production/completion/jobs/comic_c6_slot03_candidates_r1.json').read_text(encoding='utf8'))
for opt in j['options']:
 key=opt['key'];p=u.Plate('comic_c6_slot03_'+key,960,540,[35,425,885,94]);p.box(2,2,956,536,'#f3ead9');p.line([(10,10),(950,10),(950,530),(10,530),(10,10)],'#29232e',5)
 # A railing shown as an inert object, never a person or action at height.
 for x in [125,245,365]:p.poly([(x,180),(x+10,180),(x+10,330),(x,330)],'#29232e')
 p.poly([(90,165),(425,165),(425,185),(90,185)],'#4c4053');p.line([(80,335),(435,335)],'#29232e',5)
 if key=='A':
  p.poly([(570,180),(850,180),(850,325),(570,325)],'#ded1bc');p.line([(600,220),(815,220)],'#9770cf',6);p.line([(600,260),(750,260)],'#29232e',5)
 elif key=='B':
  for x,y in [(495,110),(715,110),(495,270),(715,270)]:
   p.poly([(x,y),(x+180,y),(x+180,y+115),(x,y+115)],'#29232e');p.line([(x+18,y+25),(x+158,y+25)],'#f3ead9',4);p.line([(x+18,y+65),(x+135,y+65)],'#9770cf',4)
  p.line([(425,250),(480,250)],'#9770cf',5)
 else:
  p.poly([(490,260),(865,100),(865,380)],'#ded1bc');p.line([(490,260),(865,100)],'#9770cf',4);p.line([(490,260),(865,380)],'#9770cf',4)
 p.save('source option '+key+'; nonviolent evidence diagram, source caption required','static; no camera shake')
 u.records[-1].update(source_document=j['source'],source_sha256=j['source_sha256'],option=opt,correct_key=j['correct_key'],caption_required=True,caption=opt['description'],art_alternative='original native vector evidence layout; no bodily action illustrated',runtime_integrated=False)
(u.OUT/'manifest.json').write_text(json.dumps({'scale':4,'chapter':6,'slot':3,'assets':u.records,'tool':'original editable vector/PIL exact native4x output, no image editing','source':j['source'],'correct_key':'B','reason':'safer nonviolent evidence diagram alternative; same image request not retried','runtime_integrated':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Created12editable document/detail plates +3native4x nonviolent comic candidates')
