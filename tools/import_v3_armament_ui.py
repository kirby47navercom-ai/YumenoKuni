"""Read only the specifically authorized V3 armament UI carriers; never run V3."""
from pathlib import Path
import hashlib,json,sys,shutil
sys.path.insert(0,str(Path(__file__).resolve().parent/'re'))
import cpk,spc,srd,sfl
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('C:/Program Files (x86)/Steam/steamapps/common/Danganronpa V3 Killing Harmony/data/win')
CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_armament_20261105')
OUT=ROOT/'ui/v3_authorized/armament'
SELECT={
 'partition_data_win.cpk':['flash/trial/'+n+'.spc' for n in ['t_riron_enemy_gauge_bug','t_riron_gauge_fever','t_riron_hakai','t_riron_rythm_frame','t_riron_rythm_frame_onpu','t_riron_stage_fever','t_riron_stage_shadow','t_riron_time','t_time','t_riron_todome_circle','t_riron_todome_cross','t_riron_todome_square','t_riron_todome_triangle']],
 'partition_data_win_us.cpk':['flash/trial/'+n+'_US.spc' for n in ['t_riron_combo','t_riron_enemy_gauge','t_riron_frame','t_riron_gauge','t_riron_hit','t_riron_rythm']]
}
def main(include_supplied=True):
 OUT.mkdir(parents=True,exist_ok=True);records=[];containers=[];timelines={};errors=[]
 for archive,names in SELECT.items():
  root=CACHE/Path(archive).stem;missing=[n for n in names if not (root/n).exists()]
  if missing:cpk.CPK(SOURCE/archive).extract(root,exact=missing)
  containers.extend(root/n for n in names)
 supplied=Path('C:/Users/kirby/Downloads/v3_re/ui_import_20261029/ui-containers/data/win/flash')
 if include_supplied:
  containers.extend([supplied/'event/t_phase_start_riron_JP.spc',supplied/'trial/t_riron_todome_cutin_JP.spc'])
  containers.extend((CACHE/'korean-finish/data/win/flash/event').glob('*.spc'))
 for source in containers:
  raw=source.read_bytes();members={e['name']:spc.payload(raw,e) for e in spc.entries(raw)};folder=OUT/source.stem;folder.mkdir(exist_ok=True)
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
