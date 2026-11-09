"""Decode the retained loading UI carrier only; no original runtime."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent/'re'))
import spc,srd,sfl
import build_v3_armament_layout as resolver
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('C:/Users/kirby/Downloads/v3_re/resources/game_resident_US/loading_s.spc')
BANK=ROOT/'ui/v3_authorized/loading_source';BANK.mkdir(parents=True,exist_ok=True)
raw=SOURCE.read_bytes();members={e['name']:spc.payload(raw,e) for e in spc.entries(raw)}
(BANK/'animation.json').write_text(json.dumps(sfl.parse_sfl(members['flash.sfl']),ensure_ascii=False),encoding='utf-8')
companions={e:members['texture.'+e] for e in ['srdi','srdv'] if 'texture.'+e in members};parsed=srd.parse_srd(members['texture.srd'],companions);records=[];index=-1
for b in srd.walk(parsed['blocks']):
 if b['type']!='$TXR' or 'decoded' not in b:continue
 index+=1;info=next(c['decoded'] for c in b['children'] if c['type']=='$RSI');resource=info['strings'][0]
 payload=srd.external_bytes(srd.texture_resource(b['decoded'],info),companions);im=srd.texture_image(b['decoded'],payload);dest=BANK/(resource+'.png');im.save(dest)
 records.append({'container':'loading_s','imageIndex':index,'resource':resource,'file':dest.relative_to(ROOT).as_posix(),'size':list(im.size),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(BANK/'manifest.json').write_text(json.dumps({'source':str(SOURCE),'sha256':hashlib.sha256(raw).hexdigest(),'textures':records,'timelines':{'loading_s':(BANK/'animation.json').relative_to(ROOT).as_posix()}},ensure_ascii=False,indent=2),encoding='utf-8')
(BANK/'runtime-layout.json').write_text('{}',encoding='utf-8');resolver.BANK=BANK;resolver.SOLID_NAMES={'loading_s'};resolver.ANIMATED_NAMES={'loading_s'};resolver.build()
print(json.dumps({'textures':len(records),'executedGame':False}))
