"""Source-pinned reading aids in the existing document SVG system.
No full legal wording, timestamps, signature names or new document are invented.
"""
from pathlib import Path
import hashlib,json
from PIL import ImageFont
from make_v4_case1_documents import Drawing, W, H, S, PAPER, INK, MUTED, BORDER, FONT
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ui/v4/evidence_documents_20261104'
SPECS=[
 ('private_notebook','v4:3:knowledge:private-notebook','소라 수첩 · 공개한 기능 항목','13b4_3장_아침에_쓴_기회_초고.md',227,'정상15분과 호스트 기억 부재,100% 지속, 본체 사망 시 고정과 원래 의식 소멸',[
  '정상 상태: 15분','호스트의 기억은 공유되지 않음','100%: 지속','본체 사망 시 고정 / 원래 의식 소멸']),
 ('recent_conditions','v4:E5-03','최근 맹세 · 조건 사본 열람','15b1_5장_잔과_몸의_수사_초고.md',87,'코토의 선공개 제한/원본 훼손 금지/손목 통증/오늘21:00 또는 전체 세 번째 진술 직접 제시의 종료 조건',[
  '코토의 선공개 제한 / 원본 훼손 금지','대가: 손목 통증','종료: 오늘 21:00','또는 세 번째 진술 전체를 직접 제시','상호 비가해 조건은 없음']),
 ('third_statement','v4:E5-04','세 번째 진술서 · 전체 열람','15b1_5장_잔과_몸의_수사_초고.md',113,'세 번째 진술서를 꺼내 처음부터 끝까지 편다',[
  '앞의 진술에 정정할 사항이 없음을 확인','최근 서명까지 가리지 않고 직접 제시','사츠키가 처음부터 끝까지 읽음']),
 ('ordinary_protected','v4:E5-05','보호 페이지와 보통 메모 · 대조','15b3_5장_사라진_쪽의_행위_초고.md',35,'일반 메모의 같은 칸이 지워진 흔적 없이 비어 있다는 것과,앞의 두 관찰은 그대로',[
  '보호 페이지: 음용 / 어지럽다는 말','                         사츠키 / 빈잔','보통 메모: 음용 / 어지럽다는 말','                      회수 칸은 빈칸']),
 ('old_note','v4:E6-04','옛 행사일 기록 · 제시한 세 줄','16b1_6장_전실과_통로의_수사_초고.md',347,'코토가 아버지랑 점검 일정 때문에 말을 크게 했다.',[
  '코토가 아버지랑 점검 일정 때문에 말을 크게 했다.',
  '하루카가 서류를 들고 코토한테 간다고 했다.',
  '둘이 통로 쪽으로 갔다.']),
]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 OUT.mkdir(exist_ok=True);rows=[]
 viewsPath=ROOT/'tools/v4_evidence_illustration_views.json';views=json.loads(viewsPath.read_text(encoding='utf8'));vm={r['id']:r for r in views['views']}
 semanticPath=ROOT/'tools/v4_evidence_art_semantic.json';semantic=json.loads(semanticPath.read_text(encoding='utf8'));evidence={}
 for p in (ROOT/'data/v4_story/chapters').glob('*.json'):evidence.update(json.loads(p.read_text(encoding='utf8')).get('evidenceCatalog',{}))
 for name,ident,title,file,line,quote,content in SPECS:
  source=(ROOT/'docs/design/rewrite_v4'/file).read_text(encoding='utf-8-sig');assert quote in source.splitlines()[line-1]
  if name=='old_note':
   assert all(v in source.splitlines()[n-1] for v,n in zip(content,[347,349,351]))
  d=Drawing();d.box(40,25,1520,950);d.text(90,130,title,59);d.line([(90,175),(1510,175)],BORDER,3)
  # These are explicitly reading notes, not invented verbatim original terms.
  d.text(90,235,'확인한 내용' if name!='old_note' else '원문 발췌',30,MUTED)
  font=ImageFont.truetype(str(FONT),54);y=320;wrapped=[]
  for value in content:
   text=''
   for char in value:
    if font.getlength(text+char)>1400:
     wrapped.append(text);text=char
    else:text+=char
   if text:wrapped.append(text)
   wrapped.append('')
  while wrapped and not wrapped[-1]:wrapped.pop()
  assert y+len(wrapped)*62<=905,(ident,wrapped)
  for value in wrapped:
   if value:d.text(90,y,value,54)
   y+=62
  target=OUT/(name+'.svg');target.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*S}" height="{H*S}" viewBox="0 0 {W} {H}">'+''.join(d.parts)+'</svg>\n',encoding='utf8')
  viewId='reading_aid_'+name;image=target.relative_to(ROOT).as_posix();vm[viewId]={'id':viewId,'file':image,'reviewed':True,'scope':'Source-pinned reading aid of already acquired content, visibly distinguished from a verbatim historical document. No new legal wording, private page, timestamp, signature identity or action.'}
  ev=evidence[ident];digest=sha((ev['name']+'\n'+ev['text']).encode());entry=[{'id':viewId,'sha256':sha(target.read_bytes())}];ref={'file':file,'line':line,'quote':quote,'sha256':sha(source.encode())}
  old=next((r for r in semantic['bindings'] if r['evidenceId']==ident),None)
  binding={'evidenceId':ident,'evidenceTextSha256':digest,'views':entry,'sourceStatements':[ref],'reviewBasis':'Individually read source fields; inspection reading aid, not a newly acquired physical page. All authored evidence text, acquisition and routes unchanged. Third statement is a document number, not a three-page legal document.','pixelReview':'Glyph outlines from established native document source; native visual acceptance pending.','grantPolicy':'No additional information or document contents.'}
  if old:
   assert old['evidenceTextSha256']==digest and old['sourceStatements']==[ref] and old['views'][0]['id']==viewId
   old.update(binding)
  else:semantic['bindings'].append(binding)
  rows.append({'id':ident,'image':image,'sha256':entry[0]['sha256'],'source':[ref],'layoutText':wrapped,'nativeAccepted':False})
 views['views']=list(vm.values());viewsPath.write_text(json.dumps(views,ensure_ascii=False,indent=2)+'\n',encoding='utf8');semanticPath.write_text(json.dumps(semantic,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(OUT/'manifest.json').write_text(json.dumps({'rows':rows,'rasterEdits':False,'originalsPreserved':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'sourceReadingAids':len(rows),'bitmapAssetsCreated':0}))
if __name__=='__main__':
 # The user rejected these flat plates. Preserve the old source for provenance;
 # the command now registers only the inspected physical replacements.
 from register_physical_evidence_20261104 import main as register_physical
 register_physical()
