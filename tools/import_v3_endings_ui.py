"""Authorized read-only V3 ending UI conversion; no game execution or installation writes."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'re'))
import cpk,spc,srd,sfl
ROOT=Path(__file__).resolve().parents[1]
CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_endings_20261106')
OUT=ROOT/'ui/v3_authorized/endings'
def main():
 OUT.mkdir(parents=True,exist_ok=True);records=[];containers=[];timelines={};errors=[]
 prior=json.loads((OUT/'manifest.json').read_text(encoding='utf-8')) if (OUT/'manifest.json').exists() else {}
 containers.extend(sorted(CACHE.rglob('*.spc')))
 for source in containers:
  raw=source.read_bytes();digest=hashlib.sha256(raw).hexdigest();old=[r for r in prior.get('textures',[]) if r['container']==source.stem]
  timeline=prior.get('timelines',{}).get(source.stem)
  if old and all(r['containerSHA256']==digest and (ROOT/r['file']).exists() for r in old) and timeline and (ROOT/timeline).exists():
   records.extend(old);timelines[source.stem]=timeline;continue
  members={e['name']:spc.payload(raw,e) for e in spc.entries(raw)};folder=OUT/source.stem;folder.mkdir(exist_ok=True)
  for name,data in members.items():
   if name.endswith('.sfl'):
    parsed=sfl.parse_sfl(data);dest=folder/'animation.json';dest.write_text(json.dumps(parsed,ensure_ascii=False),encoding='utf-8');timelines[source.stem]=dest.relative_to(ROOT).as_posix()
   if not name.endswith('.srd'):continue
   stem=name[:-4];companions={ext:members[stem+'.'+ext] for ext in ['srdi','srdv'] if stem+'.'+ext in members};parsed=srd.parse_srd(data,companions)
   image_index=-1
   for block in srd.walk(parsed['blocks']):
    if block['type']!='$TXR' or 'decoded' not in block:continue
    image_index+=1
    info=next((c.get('decoded') for c in block['children'] if c['type']=='$RSI'),None)
    if not info:continue
    resource=info['strings'][0]
    try:
     payload=srd.external_bytes(srd.texture_resource(block['decoded'],info),companions);im=srd.texture_image(block['decoded'],payload)
    except ValueError as error:
     errors.append({'container':source.stem,'resource':resource,'error':str(error),'metadata':block['decoded']});continue
    dest=folder/(resource+'.png');im.save(dest)
    records.append({'container':source.stem,'imageIndex':image_index,'containerSHA256':hashlib.sha256(raw).hexdigest(),'resource':resource,'file':dest.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'size':list(im.size),'unchangedDecodedPixels':True})
 manifest={'authorization':'User 2026-11-05 explicitly overrides HANDOFF §0 asset-extraction ban for this armament UI work. Read-only original UI conversion authorized; no game launch or save mutation.','textures':records,'errors':errors,'timelines':timelines,'executedGame':False,'modifiedInstallation':False}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'containers':len(containers),'textures':len(records),'errors':len(errors),'source':str(OUT)}))
if __name__=='__main__':main()
