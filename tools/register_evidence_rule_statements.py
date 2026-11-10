"""Individually read rule explanations, tied to their actual speaker.

This is not an automatic portrait fallback for unillustrated documents/rules.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROWS=[
 ('v4:3:knowledge:culprit-rule','13b1_3장_아직_살아있는_사람_초고.md',155,'[래피] 살해를 수행한 조종자예요.'),
 ('v4:3:knowledge:possession-rules','13b1_3장_아직_살아있는_사람_초고.md',185,'[래피] 보통 상태라면 유지하지 못하고 끝나요.'),
 ('v4:3:knowledge:memory-rule','13b3_3장_건네지_않은_말_초고.md',137,'[래피] 아니요. 흐리게 하는 것과 새로운 기억을 넣는 건 달라요.'),
 ('v4:3:knowledge:riku-function','13b3_3장_건네지_않은_말_초고.md',215,'[래피] 확장은 지속이30분으로 늘어요.'),
 ('v4:4:knowledge:shadow-light','14b2_4장_입구와_햇빛_초고.md',105,'[래피] 네. 본체가 빛 아래로 나가면 유지할 수 없어요.'),
 ('v4:11a2:1-16:contact-rule','11a2_1장_둘째날_초고.md',855,'[래피] 대표를 정해 접수한 뒤에는 그분에게만 신청이 남아요.'),
 ('v4:4:knowledge:sense-range','14b4_4장_조사에서_남긴_말_초고.md',69,'[래피] 두 감각을 함께 강화할 수 있어요. 몸을 늘이거나 물건을 조작하는 기능은 없어요.'),
 ('v4:E5-18','15b3_5장_사라진_쪽의_행위_초고.md',119,'[래피] 네.아카리 씨의 기억과 이미 쓴 횟수는 남아요.'),
]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 evidence={}
 for p in (ROOT/'data/v4_story/chapters').glob('*.json'):evidence.update(json.loads(p.read_text(encoding='utf-8-sig')).get('evidenceCatalog',{}))
 view=next(v for v in json.loads((ROOT/'tools/v4_evidence_illustration_views.json').read_text(encoding='utf8'))['views'] if v['id']=='testimony_portrait_lappy')
 p=ROOT/'tools/v4_evidence_art_semantic.json';registry=json.loads(p.read_text(encoding='utf8'))
 for ident,file,line,quote in ROWS:
  text=(ROOT/'docs/design/rewrite_v4'/file).read_text(encoding='utf-8-sig');assert quote in text.splitlines()[line-1]
  ev=evidence[ident];digest=sha((ev['name']+'\n'+ev['text']).encode());entries=[{'id':view['id'],'sha256':sha((ROOT/view['file']).read_bytes())}]
  ref={'file':file,'line':line,'quote':quote,'sha256':sha(text.encode())}
  old=next((b for b in registry['bindings'] if b['evidenceId']==ident),None)
  if old:assert old['evidenceTextSha256']==digest and old['views']==entries and old['sourceStatements']==[ref];continue
  registry['bindings'].append({'evidenceId':ident,'evidenceTextSha256':digest,'views':entries,'sourceStatements':[ref],'reviewBasis':'The rule was individually read in the current manuscript and is explicitly explained by Lappy. Portrait denotes the actual explanation source, not a photograph or independent experiment proving the rule. Exact limits stay in the existing evidence text.','pixelReview':'Existing directly reviewed approved portrait/native SVG layout; no new raster.','grantPolicy':'No new acquisition, action, capability, witness or story fact.'})
 p.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'individuallySourcePinnedRuleStatements':len(ROWS),'newImages':0,'storyFactsChanged':False}))
if __name__=='__main__':main()
