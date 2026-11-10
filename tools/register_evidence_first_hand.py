"""Reuse the individually source-reviewed inspection aid for its explicit scope."""
import hashlib,json
from pathlib import Path
from prepare_comic_revision_runtime import chunks
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 selection=ROOT/'art/inspection_v4/illustrations_20261104/selection.json';item=json.loads(selection.read_text(encoding='utf8'))['entries']['c4_hatch_hand_observation'];ident=item['inspectionScope'];assert ident=='v4:4:knowledge:first-hand'
 data=(ROOT/item['image']).read_bytes();assert sha(data)==item['sha256']
 runtime=b'\x89PNG\r\n\x1a\n'+b''.join(raw for kind,raw in chunks(data) if kind!=b'caBX')
 assert [raw for kind,raw in chunks(runtime) if kind in [b'IHDR',b'IDAT']]==[raw for kind,raw in chunks(data) if kind in [b'IHDR',b'IDAT']]
 target=ROOT/'art/inspection_v4/illustrations_20261104/runtime/c4_hatch_hand_observation.png';target.parent.mkdir(exist_ok=True);target.write_bytes(runtime)
 vp=ROOT/'tools/v4_evidence_illustration_views.json';v=json.loads(vp.read_text(encoding='utf8'));viewid='reviewed_first_hand_inspection_aid';row={'id':viewid,'file':target.relative_to(ROOT).as_posix(),'reviewed':True,'scope':'Previously inspected, unscaled ink observation aid of the closed-cover hand position. Not an initial photograph, new experiment, exact wound or measured geometry.'};v['views']=[r for r in v['views'] if r['id']!=viewid]+[row]
 evidence=json.loads((ROOT/'data/v4_story/chapters/4.json').read_text(encoding='utf8'))['evidenceCatalog'][ident];digest=sha((evidence['name']+'\n'+evidence['text']).encode())
 refs=[{'file':r['file'],'line':r['line'],'quote':r['quote'],'sha256':r['fileSha256']} for r in item['source']]
 sp=ROOT/'tools/v4_evidence_art_semantic.json';s=json.loads(sp.read_text(encoding='utf8'));entries=[{'id':viewid,'sha256':sha(runtime)}];old=next((r for r in s['bindings'] if r['evidenceId']==ident),None)
 if old:assert old['evidenceTextSha256']==digest and old['views']==entries and old['sourceStatements']==refs
 else:s['bindings'].append({'evidenceId':ident,'evidenceTextSha256':digest,'views':entries,'sourceStatements':refs,'reviewBasis':item['presentation'],'pixelReview':'Original illustration directly reviewed in existing native spot proof and original selection; evidence-panel review pending. Only caBX metadata omitted, compressed pixels byte-identical.','grantPolicy':'Existing acquired observation only. No new photograph, measurement, injury or act.'})
 vp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8');sp.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'newEvidenceBinding':ident,'newBitmap':False,'sourcePixelsChanged':False}))
if __name__=='__main__':main()
