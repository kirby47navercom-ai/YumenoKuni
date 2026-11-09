"""Read only the UI carriers needed by the user's09..13 original-video correction."""
from pathlib import Path
import sys,json,hashlib,re
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools/re'))
import cpk,spc,srd,sfl
SOURCE=Path('C:/Program Files (x86)/Steam/steamapps/common/Danganronpa V3 Killing Harmony/data/win')
CACHE=Path('C:/Users/kirby/Downloads/v3_re/ui_trial_inputs_20261107');OUT=ROOT/'ui/v3_authorized/trial_inputs'
SELECT={'partition_data_win.cpk':['flash/trial/'+n+'.spc' for n in ['t_tohyo_cursor','t_tohyo_frame','t_tohyo_time','t_sub_jinbutu_arrow','t_sub_jinbutu_focus','t_sub_jinbutu_pl','t_sub_spot_bg','t_sub_spot_cursor','t_sub_mondai','t_choice','t_choice_time']]+['flash/trial/spcpack/trial_bullet.spc'],'partition_data_win_us.cpk':['flash/trial/'+n+'_US.spc' for n in ['t_tohyo_bt','t_tohyo_name','t_tohyo_start','t_tohyo_timeup','t_tohyo_title','t_sub_jinbutu_kettei','t_sub_jinbutu_zaseki','t_sub_title','t_choice_frame','t_tohyo_chara','t_tohyo_chara_img']]+['flash/techou/techou_kotodama_US.spc','flash/techou/techou_kotodama_list_US.spc']}
for name in ['t_ktdm_scroll','t_ktdm_detail','t_ktdm_detail_g','t_ktdm_detail_scroll','t_ktdm_sele','t_ktdm_sele_scr','t_ktdm_time','t_gun_cylinder','t_mondai','t_kettei']:
 path='flash/trial/'+name+'.spc'
 if path not in SELECT['partition_data_win.cpk']:SELECT['partition_data_win.cpk'].append(path)
path='flash/trial/t_ktdm_detail_img_US.spc'
if path not in SELECT['partition_data_win_us.cpk']:SELECT['partition_data_win_us.cpk'].append(path)
for name in ['t_tosen_bg','t_tosen_name','t_tosen_memori','t_tosen_error']:
 path='flash/trial/'+name+'_US.spc'
 if path not in SELECT['partition_data_win_us.cpk']:SELECT['partition_data_win_us.cpk'].append(path)
def sha(b):return hashlib.sha256(b).hexdigest()
def run():
 OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
 provided=Path('C:/Users/kirby/Downloads/v3_re/ui_import_20261029/ui-containers');lookup={p.name:p for p in provided.rglob('*.spc')};lookup.update({name.replace('_JP.spc','_US.spc'):file for name,file in list(lookup.items()) if name.endswith('_JP.spc')});rows=[];textures=[];timelines={};errors=[]
 for archive,names in SELECT.items():
  missing=[n for n in names if Path(n).name not in lookup and not(CACHE/Path(archive).stem/n).exists()]
  if missing:cpk.CPK(SOURCE/archive).extract(CACHE/Path(archive).stem,exact=missing)
  for n in names:
   src=lookup.get(Path(n).name,CACHE/Path(archive).stem/n);raw=src.read_bytes();members={e['name']:spc.payload(raw,e)for e in spc.entries(raw)};folder=OUT/Path(n).stem;folder.mkdir(exist_ok=True)
   rows.append({'name':Path(n).stem,'member':n,'archive':archive,'sha256':sha(raw),'bytes':len(raw),'source':str(src),'providedKoreanCarrier':Path(n).name in lookup})
   for member,data in members.items():
    if member.endswith('.sfl'):
     f=folder/(Path(member).stem+'-animation.json');f.write_text(json.dumps(sfl.parse_sfl(data),ensure_ascii=False,separators=(',',':')),encoding='utf-8');timelines[Path(n).stem+('' if member=='flash.sfl' else ':'+member)]=f.relative_to(ROOT).as_posix()
    if not member.endswith('.srd'):continue
    stem=member[:-4];companions={e:members[stem+'.'+e]for e in ['srdi','srdv']if stem+'.'+e in members};parsed=srd.parse_srd(data,companions);index=-1
    for b in srd.walk(parsed['blocks']):
     if b['type']!='$TXR' or 'decoded' not in b:continue
     index+=1;rsi=next((c.get('decoded')for c in b['children']if c['type']=='$RSI'),None)
     if not rsi:continue
     name=rsi['strings'][0]
     try:im=srd.texture_image(b['decoded'],srd.external_bytes(srd.texture_resource(b['decoded'],rsi),companions))
     except ValueError as e:errors.append({'container':Path(n).stem,'resource':name,'error':str(e)});continue
     resultEffect=Path(n).stem=='t_tohyo_chara_img_US' and 'kamihubuki' in name
     externalPortrait=Path(n).stem=='t_tohyo_chara_img_US' and not resultEffect;targetFolder=CACHE/'reference-only'/Path(n).stem if externalPortrait else folder;targetFolder.mkdir(parents=True,exist_ok=True)
     f=targetFolder/(Path(member).stem+'_'+str(index).zfill(3)+'_'+re.sub(r'[^A-Za-z0-9_.-]','_',name)+'.png');im.save(f);textures.append({'container':Path(n).stem,'member':member,'imageIndex':index,'resource':name,'file':'' if externalPortrait else f.relative_to(ROOT).as_posix(),'ownPortraitRequired':externalPortrait,'sha256':sha(f.read_bytes()),'pixelSHA256':sha(im.convert('RGBA').tobytes()),'size':list(im.size),'runtimeSelected':resultEffect})
 result={'schema':'v3-trial-inputs-original-ui-v1','authorization':'User requests09..13 original Korean-video/UI-equivalent correction; existing explicit override of extraction ban. Read-only source carriers, no original game run/install/save changes. Own story/characters remain.','containers':rows,'textures':textures,'timelines':timelines,'errors':errors,'executedOriginalGame':False,'modifiedInstallation':False}
 (OUT/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'containers':len(rows),'textures':len(textures),'timelines':len(timelines),'errors':errors}))
if __name__=='__main__':run()

