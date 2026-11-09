"""Compact original Climax UI quads, excluding original story artwork."""
from pathlib import Path
import json,sys,math,hashlib,re
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v4/climax_original_20261106';CACHE=Path('C:/Users/kirby/Downloads/v3_re/native/climax-ui-20261106')
sys.path.insert(0,str(ROOT/'tools/re'));import spc,dat
def read(p):return json.loads(p.read_text(encoding='utf8'))
def build():
 inv=read(BANK/'manifest.json');layout=read(BANK/'layout.json')
 def rows(container,label='fl_wait'):
  return layout[container]['states'][label]
 def pack(row):
  return {k:row[k]for k in ['texture','resource','path','rect','rotation','opacity','sourceAffine','sourceRect','colorMultiply','colorAdd']}
 def choose(container,label='fl_wait',test=lambda r:True):return [pack(r)for r in rows(container,label)if test(r)]
 components={
 'pageBar':choose('climax_page_base_US',test=lambda r:r['path'].startswith('/i_base/')),
 'pageWord':choose('climax_page_base_US',test=lambda r:r['path'].startswith('/p_page/')),
 'pageCounterBase':choose('climax_page_US',test=lambda r:r['path'].startswith('/i_base/')or r['path'].startswith('/p_no_text/')or r['path'].startswith('/i_slash/')),
 'stockBase':choose('climax_koma_choise_US','fl_wait_s',lambda r:r['path'].startswith('/i_base/')),
 'stockWord':choose('climax_koma_choise_US','fl_wait_s',lambda r:r['path'].startswith('/p_stock/')),
 'selectedPanelFrame':choose('climax_koma_act_US',test=lambda r:r['path'].startswith(('/i_shadow_00/','/i_waku/'))),
 'selectedPanelWordUS':choose('climax_koma_act_US',test=lambda r:r['path'].startswith('/p_koma_text/')),
 'selectedUsed':choose('climax_koma_act_US',test=lambda r:r['path'].startswith('/p_ok/')),
 'selectedLocked':choose('climax_koma_act_US',test=lambda r:r['path'].startswith('/p_rock_00/')),
 'captionPlate':choose('climax_hint'),
 'timerBase':choose('climax_time_US',test=lambda r:r['path'].startswith(('/i_base/','/p_time/','/i_time_no_koron'))),
 'cursor':choose('climax_cursor'),
 'placeOK':[pack(r)for r in layout['climax_cutin_ok']['frames'][23]if r['opacity']>.001],
 'placeNG':[pack(r)for r in layout['climax_cutin_ng']['frames'][23]if r['opacity']>.001],
 }
 for i in range(8):components['holeHint'+str(i)]=choose('climax_hukidasi','fl_wait_'+f'{i:02d}')
 hearts={}
 for n in [5,7,10]:
  container='climax_status_ht'+str(n)
  components['heartBase'+str(n)]=choose(container,test=lambda r:r['path'].startswith(('/i_base/','/i_heart_base/')))
  hearts[str(n)]=choose(container,test=lambda r:re.match(r'/p_heart_\d{2}/',r['path'])is not None)
 stock=rows('climax_koma_choise_US','fl_wait_s');slots=[]
 for n in range(14):
  prefix='/p_'+f'{n:02d}'+'/'
  def matching(token):return [pack(r)for r in stock if r['path'].startswith(prefix)and token in r['path']]
  slots.append(dict(index=n,image=matching('/p_koma_'),idle=matching('/i_def/'),used=matching('/p_ok_'),locked=matching('/p_rock_'),focus=matching('/p_act_l_')))
 expanded=rows('climax_koma_choise_US','fl_wait_l');expandedSlots=[]
 for n in range(14):
  prefix='/p_'+f'{n:02d}'+'/'
  def matching_exp(token):return [pack(r)for r in expanded if r['path'].startswith(prefix)and token in r['path']]
  expandedSlots.append(dict(index=n,image=matching_exp('/p_koma_'),idle=matching_exp('/i_def/'),used=matching_exp('/p_ok_'),locked=matching_exp('/p_rock_'),focus=matching_exp('/p_act_l_')))
 components['stockExpandedBase']=choose('climax_koma_choise_US','fl_wait_l',lambda r:r['path'].startswith('/i_base/'))
 components['stockExpandedWord']=choose('climax_koma_choise_US','fl_wait_l',lambda r:r['path'].startswith('/p_stock/'))
 selected=choose('climax_koma_act_US',test=lambda r:r['path'].startswith('/p_koma_act/'))
 timerSlots=choose('climax_time_US',test=lambda r:r['path'].startswith('/p_time_no_'))
 pageNoSlots=choose('climax_page_US',test=lambda r:r['path'].startswith(('/p_no_base_','/p_act_no_')))
 projection={}
 for c in inv['containers']:
  raw=Path(c['cache']).read_bytes();members={e['name']:spc.payload(raw,e)for e in spc.entries(raw)}
  if 'data_3d.dat'in members:
   d=dat.parse_dat(members['data_3d.dat']);projection[c['name']]=dict(sha256=d['sha256'],columns=[x['name']for x in d['columns']],rows=d['rows'])
 textures={}
 for t in inv['textures']:
  textures[t['container']+'/'+t['resource']]={k:t[k]for k in ['file','size','format','sha256']}
 core=dict(schema='v3-climax-compact-core-v1',canvas=[1280,720],sourceCanvas=[1920,1080],sflScale=2/3,components=components,stockSlots=slots,selectedOwnImage=selected,hearts=hearts,timerSlots=timerSlots,pageNumberSlots=pageNoSlots,textures=textures,data3d=projection,originalMangaInRuntime=False,labelsUS=dict(selectedPanel='PANEL',stock='STOCK',page='PAGE',time='TIME'),limitations=['Coordinates are exact original SFL flat1920->1280; original data_3d world transform/projection is supplied separately, not silently applied.','Original story thumbnails/collage backgrounds are external reference only; replace texture-empty selectedOwnImage/stockSlots.image quads with own approved comic art.','Climax US selected label bitmap says PANEL, while requested Korean/Japanese video may show KOMA. No false claim of Korean/Japanese body label pixels.','One optional climax_title_US/climax_US.png has undecoded layout flag7; main gameplay HUD sprites are decoded.','Original source symbols contain separate used/locked/focus branches simultaneously; the game must select one branch. Do not composite all branches as one stock icon.'])
 core['stockExpandedSlots']=expandedSlots
 core['clipDurations']={}
 for key,container,label in [('unlock','climax_koma_act_US','fl_rock'),('stockExpand','climax_koma_choise_US','fl_s_l'),('stockCollapse','climax_koma_choise_US','fl_l_s')]:
  parsed=read(ROOT/inv['timelines'][container]);root=next(t for t in parsed['tables']if t['id']==6)['entries'][0]['sequences'];start=layout[container]['labels'][label]
  end=next(i for i in range(start,len(root))if any(a.get('name')=='Stop'for op in root[i]['operations']for a in op.get('decoded',{}).get('actions',[])))
  core['clipDurations'][key]=dict(container=container,label=label,startFrame=start,stopFrame=end,frameCount=end-start+1,frameIntervalsToStop=end-start,secondsAt60=(end-start+1)/60,rateAssumption=60,runtimeRateVerified=False)
 shared=BANK/'shared_page/manifest.json'
 if shared.exists():core['sharedPageUI']=read(shared)['records']
 payload=json.dumps(core,ensure_ascii=False,separators=(',',':'));assert len(payload)<262144
 (BANK/'core.json').write_text(payload,encoding='utf8')
 print(json.dumps(dict(coreBytes=len(payload.encode()),components=len(components),textures=len(textures),stockSlots=len(slots),file=str(BANK/'core.json'))))
 return core
if __name__=='__main__':build()
