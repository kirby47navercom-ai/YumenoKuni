"""Read only the trial dialogue UI explicitly requested by the user; never run V3."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'re'))
import cpk,spc,srd,sfl
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('C:/Program Files (x86)/Steam/steamapps/common/Danganronpa V3 Killing Harmony/data/win')
CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_trial_dialogue_20261106')
OUT=ROOT/'ui/v3_authorized/trial_dialogue'
SELECT={'partition_data_win.cpk':['flash/trial/t_kaiwa_pl.spc'],'partition_data_win_us.cpk':['flash/trial/'+n+'.spc' for n in ['t_kaiwa_fl_US','t_next_US','t_next_event_US']]}

def main():
 OUT.mkdir(parents=True,exist_ok=True);records=[];containers=[];timelines={};errors=[]
 for archive,names in SELECT.items():
  folder=CACHE/Path(archive).stem;missing=[name for name in names if not (folder/name).exists()]
  if missing:cpk.CPK(SOURCE/archive).extract(folder,exact=missing)
  containers.extend(folder/name for name in names)
 for source in containers:
  raw=source.read_bytes();members={e['name']:spc.payload(raw,e) for e in spc.entries(raw)};folder=OUT/source.stem;folder.mkdir(exist_ok=True)
  for name,data in members.items():
   if name.endswith('.sfl'):
    dest=folder/'animation.json';dest.write_text(json.dumps(sfl.parse_sfl(data),ensure_ascii=False),encoding='utf-8');timelines[source.stem]=dest.relative_to(ROOT).as_posix()
   if not name.endswith('.srd'):continue
   stem=name[:-4];companions={ext:members[stem+'.'+ext] for ext in ['srdi','srdv'] if stem+'.'+ext in members};parsed=srd.parse_srd(data,companions);index=-1
   for block in srd.walk(parsed['blocks']):
    if block['type']!='$TXR' or 'decoded' not in block:continue
    index+=1;info=next((c.get('decoded') for c in block['children'] if c['type']=='$RSI'),None)
    if not info:continue
    resource=info['strings'][0]
    # Original character faces/names are not runtime resources in our game.
    if ('t_kaiwa_chara_ico_' in resource and 'mask' not in resource) or 't_kaiwa_chara_name_' in resource:continue
    try:payload=srd.external_bytes(srd.texture_resource(block['decoded'],info),companions);im=srd.texture_image(block['decoded'],payload)
    except ValueError as error:errors.append({'container':source.stem,'resource':resource,'error':str(error)});continue
    dest=folder/(resource+'.png');im.save(dest);records.append({'container':source.stem,'imageIndex':index,'resource':resource,'file':dest.relative_to(ROOT).as_posix(),'size':list(im.size),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'containerSHA256':hashlib.sha256(raw).hexdigest()})
 manifest={'authorization':'User20261106 explicitly requests original trial dialogue UI instead of the hand-drawn frame; selective read-only UI conversion only. Own character faces/names replace original identities.','textures':records,'timelines':timelines,'errors':errors,'executedGame':False,'modifiedInstallation':False,'selection':SELECT}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');(OUT/'runtime-layout.json').write_text('{}',encoding='utf-8')
 print(json.dumps({'containers':len(containers),'textures':len(records),'errors':errors,'source':str(OUT)}))
if __name__=='__main__':main()
