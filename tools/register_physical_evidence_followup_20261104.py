"""Reviewed physical successors to the remaining flat evidence-card plates.

The old diagrams remain available to their separately verified region tasks.
Only acquired evidence-card art changes here; no answer/hit region is modified.
"""
import hashlib,json,shutil
from pathlib import Path
from prepare_comic_revision_runtime import chunks
ROOT=Path(__file__).resolve().parents[1]
GEN=Path('C:/Users/kirby/.codex/generated_images/01a19fd4-cd3f-7123-91ea-3a9194054780')
OUT=ROOT/'art/inspection_v4/physical_clues_20261104'
REVIEWED_SOURCE_HASHES={
 '11b':'380913610b608fa861e229632bf4cba3f42d4d26cd74b79f9295c854c163d546',
 '16b1':'d9521701cdc7909363e256b02f7193b8f497871fa2e8febfca84b8342516b953',
 '16b2':'00c3335ddc974117d52a88648fe31005b9404dd0392d06afe7da49a65a6fccf0',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def proof(prefix,line):
 p=next((ROOT/'docs/design/rewrite_v4').glob(prefix+'_*.md'));t=p.read_text(encoding='utf-8-sig')
 assert sha(t.encode())==REVIEWED_SOURCE_HASHES[prefix], 'Re-read changed physical clue source: '+p.name
 return dict(file=p.name,line=line,quote=t.splitlines()[line-1],sha256=sha(t.encode()))
def main():
 vp=ROOT/'tools/v4_evidence_illustration_views.json';sp=ROOT/'tools/v4_evidence_art_semantic.json'
 views=json.loads(vp.read_text(encoding='utf-8'));semantic=json.loads(sp.read_text(encoding='utf-8'))
 evidence={}
 for p in (ROOT/'data/v4_story/chapters').glob('*.json'):evidence.update(json.loads(p.read_text(encoding='utf-8')).get('evidenceCatalog',{}))
 rows=[
 ('printer_order','efb04bd6-6136-473f-9cd5-a7ce6d56b35b',['v4:E1-04'],[proof('11b',793),proof('11b',797),proof('11b',799)],['printer_output','report_16_excerpt','report_17_excerpt','printer_order_excerpt']),
 ('report_original','76bda53a-51e0-4508-be2d-12b9765b31fa',['v4:E1-05'],[proof('11b',575),proof('11b',581)],['report_torn_edge','report_17_excerpt']),
 ('paper_join','e4c0d996-caee-42b4-8a97-449799cf737c',['v4:E1-06'],[proof('11b',557),proof('11b',575),proof('11b',579),proof('11b',581)],['report_torn_edge','report_17_excerpt']),
 ('observation_notebook','7ac899b6-5e5f-4989-917a-23d83b2c4618',['v4:E1-12'],[proof('11b',513),proof('11b',515)],['observation_summary_excerpt']),
 ('statement_pair','a544a4f8-24ae-46ee-85ee-40ddc5618669',['v4:E6-09'],[proof('16b2',83),proof('16b2',85),proof('16b2',87),proof('16b2',89),proof('16b2',101)],[]),
 ('old_door_photo','0e10f19a-729e-4c33-9815-eb0d555de742',['v4:E6-02'],[proof('16b1',49),proof('16b1',51),proof('16b1',53),proof('16b1',77),proof('16b1',113)],[]),
 ]
 receipts=[]
 for name,generated,ids,refs,retired in rows:
  data=(GEN/('exec-'+generated+'.png')).read_bytes();original=OUT/(name+'_original.png');shutil.copyfile(GEN/('exec-'+generated+'.png'),original)
  pixel=b'\x89PNG\r\n\x1a\n'+b''.join(raw for kind,raw in chunks(data) if kind!=b'caBX')
  assert [raw for kind,raw in chunks(data) if kind in (b'IHDR',b'IDAT')]==[raw for kind,raw in chunks(pixel) if kind in (b'IHDR',b'IDAT')]
  target=OUT/(name+'.png');target.write_bytes(pixel);vid='physical_clue_'+name
  view=dict(id=vid,file=target.relative_to(ROOT).as_posix(),reviewed=True,scope='Physical illustration of already acquired material. Not an exact newly discovered photograph, measured architecture, newly disclosed statement, clock, signature, fingerprint or forensic conclusion.')
  old=next((r for r in views['views'] if r['id']==vid),None)
  if old:old.clear();old.update(view)
  else:views['views'].append(view)
  for ident in ids:
   ev=evidence[ident];binding=dict(evidenceId=ident,evidenceTextSha256=sha((ev['name']+'\n'+ev['text']).encode()),views=[dict(id=vid,sha256=sha(pixel))],sourceStatements=refs,reviewBasis='Latest user correction: material evidence illustration, not flat prose on a plate. Preserve acquired text, story and gameplay.',pixelReview='Original directly inspected 2026-11-04. Paper join revised once to align the printed rule above both text fragments. Printer has only sequential16/17 and no clock; notebook has only existing headings; statement preserves four source lines and does not invent unknown summary prose; old photograph is a tightly cropped illustrative doorway gap, not a room topology.',grantPolicy='No new evidence, route, witness identity, exact coordinate, private text or trace.')
   if retired:binding['replaceCatalogueViews']=retired
   old=next((r for r in semantic['bindings'] if r['evidenceId']==ident),None)
   if old:old.clear();old.update(binding)
   else:semantic['bindings'].append(binding)
  receipts.append(dict(evidenceIds=ids,original=original.relative_to(ROOT).as_posix(),runtime=target.relative_to(ROOT).as_posix(),originalSha256=sha(data),runtimeSha256=sha(pixel),source=refs,directViewed=True,compressedPixelsPreserved=True,nativeAccepted=False))
 vp.write_text(json.dumps(views,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');sp.write_text(json.dumps(semantic,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (OUT/'followup_manifest.json').write_text(json.dumps(dict(rows=receipts,tool='builtin image_gen',runtimeAdapter='caBX-only removal; compressed pixels preserved',scope='Evidence cards only. Existing region-task pictures/hit geometry unchanged and still need their own material-art pass.'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(physicalImages=len(rows),evidenceIDs=sum(len(r[2]) for r in rows),storyChanged=False)))
if __name__=='__main__':main()
