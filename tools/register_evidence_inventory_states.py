"""Keep initially sealed six and currently missing D as different evidence views."""
import hashlib,json,shutil
from pathlib import Path
from prepare_comic_revision_runtime import chunks
ROOT=Path(__file__).resolve().parents[1]
GEN=Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')
SPECS=[
 ('inventory_six_sealed','8fe2df22-b7bf-4d7a-84e4-a7c5399f9bb3','v4:E5-08','15a9_5장_쓰지_않은_한번_초고.md',21,'안에는 식별 표지가 A~F로 나뉜 개별 용기 여섯 개가 있다.모두 봉함 상태다.'),
 ('inventory_five_missing_d','4845b221-6248-49e5-8e21-3a7be06dab53','v4:E5-09','15b2_5장_돌아오지_않은_하나_초고.md',17,'용기 다섯 개가 남아 있다.D칸이 비어 있다.'),
]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 out=ROOT/'art/inspection_v4/inventory_states_20261104';out.mkdir(exist_ok=True)
 vp=ROOT/'tools/v4_evidence_illustration_views.json';v=json.loads(vp.read_text(encoding='utf8'));viewmap={r['id']:r for r in v['views']}
 sp=ROOT/'tools/v4_evidence_art_semantic.json';semantic=json.loads(sp.read_text(encoding='utf8'));evidence={};receipts=[]
 for p in (ROOT/'data/v4_story/chapters').glob('*.json'):evidence.update(json.loads(p.read_text(encoding='utf-8-sig')).get('evidenceCatalog',{}))
 for name,generated,evidenceId,file,line,quote in SPECS:
  source=(ROOT/'docs/design/rewrite_v4'/file).read_text(encoding='utf-8-sig');assert quote in source.splitlines()[line-1]
  original=GEN/f'exec-{generated}.png';data=original.read_bytes();copy=out/(name+'_original.png');shutil.copyfile(original,copy)
  runtime=b'\x89PNG\r\n\x1a\n'+b''.join(raw for kind,raw in chunks(data) if kind!=b'caBX')
  assert [raw for kind,raw in chunks(runtime) if kind in [b'IHDR',b'IDAT']]==[raw for kind,raw in chunks(data) if kind in [b'IHDR',b'IDAT']]
  path=out/(name+'.png');path.write_bytes(runtime);image=path.relative_to(ROOT).as_posix();ident='reviewed_'+name
  viewmap[ident]={'id':ident,'file':image,'reviewed':True,'scope':'Previously acquired source-described inventory state only. Illustrative box spacing, no measured layout, substance, time or removing actor. Exact source statement stays in evidence text.'}
  ev=evidence[evidenceId];digest=sha((ev['name']+'\n'+ev['text']).encode());entries=[{'id':ident,'sha256':sha(runtime)}]
  old=next((b for b in semantic['bindings'] if b['evidenceId']==evidenceId),None)
  if old:assert old['evidenceTextSha256']==digest and old['views']==entries
  else:semantic['bindings'].append({'evidenceId':evidenceId,'evidenceTextSha256':digest,'views':entries,'reviewBasis':'Six initially sealed A-F; later five A/B/C/E/F with empty D and already torn wrapper. Do not put the missing state in the initial confirmation. All depicted remaining bands intact; first broken-band draft rejected.','pixelReview':'2026-11-04 directly viewed generated originals; native acceptance pending','grantPolicy':'Existing owned evidence only, no grants/answers/queues changed.'})
  receipts.append({'id':evidenceId,'original':copy.relative_to(ROOT).as_posix(),'originalSha256':sha(data),'runtime':image,'runtimeSha256':sha(runtime),'onlyCaBXRemoved':True,'compressedPixelsPreserved':True,'directViewed':True,'source':{'file':file,'line':line,'quote':quote,'sha256':sha(source.encode())}})
 v['views']=list(viewmap.values());vp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8');sp.write_text(json.dumps(semantic,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(out/'manifest.json').write_text(json.dumps({'rows':receipts,'newStoryFacts':False,'nativeAccepted':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'inventoryStates':2,'sourceFactsChanged':False,'runtimePixelsPreserved':True}))
if __name__=='__main__':main()
