"""Read only the Nonstop cartridge UI explicitly requested by the user; never run V3."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'re'))
import cpk,spc,srd,sfl
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('C:/Program Files (x86)/Steam/steamapps/common/Danganronpa V3 Killing Harmony/data/win')
CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_nonstop_ammo_20261107')
OUT=ROOT/'ui/v3_authorized/nonstop_ammo'
SELECT={'partition_data_win.cpk':['flash/trial/t_gun_cylinder.spc']+['flash/trial/program/t_bullet/t_bullet'+suffix+'.spc' for suffix in ['_000','_001','_002','_base_000','_base_001','_base_002','_glow_000','_glow_001','_glow_002']], 'partition_data_win_us.cpk':['flash/trial/t_gun_US.spc']}

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
    try:payload=srd.external_bytes(srd.texture_resource(block['decoded'],info),companions);im=srd.texture_image(block['decoded'],payload)
    except ValueError as error:errors.append({'container':source.stem,'resource':resource,'error':str(error)});continue
    dest=folder/(resource+'.png');im.save(dest);records.append({'container':source.stem,'imageIndex':index,'resource':resource,'file':dest.relative_to(ROOT).as_posix(),'size':list(im.size),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'containerSHA256':hashlib.sha256(raw).hexdigest()})
 manifest={'authorization':'User20261107 explicitly requests original-equivalent Nonstop cartridge UI instead of the handmade substitute. Only gun-cylinder nine bullet UI carriers and the original gun-frame UI; read-only conversion, no game execution or original installation changes.','textures':records,'timelines':timelines,'errors':errors,'executedGame':False,'modifiedInstallation':False,'selection':SELECT,'koreanReference':{'file':'ui/v3_authorized/nonstop_ammo/korean-reference.png','origin':'User supplied original Korean V3 screenshot eb612dab; Kotodama lettering only'}}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');(OUT/'runtime-layout.json').write_text('{}',encoding='utf-8')
 print(json.dumps({'containers':len(containers),'textures':len(records),'errors':errors,'source':str(OUT)}))
if __name__=='__main__':main()
