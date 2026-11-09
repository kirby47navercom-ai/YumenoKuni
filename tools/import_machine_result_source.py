"""Read only system UI carriers requested by the user. Never execute V3."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools/re'))
import cpk,spc,srd,sfl
CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_machine_result_20261107');BANK=ROOT/'ui/v3_authorized/machine_result_source'
GAME=Path('C:/Program Files (x86)/Steam/steamapps/common/Danganronpa V3 Killing Harmony/data/win')
NAMES=['flash/event/m_get_US.spc']

def main():
 BANK.mkdir(parents=True,exist_ok=True);CACHE.mkdir(exist_ok=True)
 missing=[n for n in NAMES if not (CACHE/n).exists()]
 if missing:cpk.CPK(GAME/'partition_data_win_us.cpk').extract(CACHE,exact=missing)
 carriers=[CACHE/n for n in NAMES]
 records=[];timelines={};errors=[]
 for source in carriers:
  raw=source.read_bytes();members={r['name']:spc.payload(raw,r) for r in spc.entries(raw)};out=BANK/source.stem;out.mkdir(exist_ok=True)
  for name,data in members.items():
   if name.endswith('.sfl'):
    p=out/'animation.json';p.write_text(json.dumps(sfl.parse_sfl(data),ensure_ascii=False),encoding='utf-8');timelines[source.stem]=p.relative_to(ROOT).as_posix()
   if not name.endswith('.srd'):continue
   stem=name[:-4];companions={e:members[stem+'.'+e] for e in ['srdi','srdv'] if stem+'.'+e in members};parsed=srd.parse_srd(data,companions);index=-1
   for block in srd.walk(parsed['blocks']):
    if block['type']!='$TXR' or 'decoded' not in block:continue
    index+=1;info=next((r.get('decoded') for r in block['children'] if r['type']=='$RSI'),None)
    if not info:continue
    resource=info['strings'][0]
    if resource.startswith(('chara_name_','chara_icon_')):continue
    try:im=srd.texture_image(block['decoded'],srd.external_bytes(srd.texture_resource(block['decoded'],info),companions))
    except ValueError as error:errors.append({'container':source.stem,'resource':resource,'error':str(error)});continue
    p=out/(resource+'.png');im.save(p);records.append({'container':source.stem,'imageIndex':index,'resource':resource,'file':p.relative_to(ROOT).as_posix(),'size':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 manifest={'authorization':'User20261107 requests every game UI match original V3. Narrow flash/event/m_get_US.spc machine result UI read-only conversion; no original execution or installation/save modification. Cached resident UI reused.','archive':'partition_data_win_us.cpk','selection':NAMES,'sourceInstallationPath':str(GAME),'carrierSHA256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in carriers},'textures':records,'timelines':timelines,'errors':errors,'carriers':[str(p) for p in carriers],'originalGameExecuted':False,'modifiedInstallation':False}
 (BANK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');(BANK/'runtime-layout.json').write_text('{}',encoding='utf-8')
 print('MACHINE_RESULT_SOURCE',len(carriers),len(records),len(errors))
if __name__=='__main__':main()
