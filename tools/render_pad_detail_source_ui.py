"""Compose five Pad UI families from their own decoded source affine/RGBA.
Original character/evidence/gift content is deliberately excluded from chrome.
"""
from pathlib import Path
import copy,json,math
from PIL import Image
from render_adv_source_ui import composite,ROOT,SCALE
BANK=ROOT/'ui/v3_authorized/pad_detail_source';OUT=ROOT/'ui/v4/pad_detail_source'
SOURCE=json.loads((BANK/'layout.json').read_text(encoding='utf-8'))
BASE=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'))
M={'bindings':{},'states':{},'source':'Exact family bitmap/RGBA/affine; own content remains dynamic. Settled states, not original script execution or full timeline equality.'}

def rows(name,label='fl_wait'):return SOURCE[name]['states'][label]
def node(screen,id):return next(n for n in BASE[screen]['nodes'] if n['id']==id)['slot']['offset']
def shift(rr,origin):
 rr=copy.deepcopy(rr)
 for r in rr:
  r['sourceAffine'][4]+=origin[0]*1.5;r['sourceAffine'][5]+=origin[1]*1.5
 return rr
def save(name,rr,rect=None):
 im=composite(rr)
 if rect is None:
  box=im.getbbox();assert box,name;rect=[box[0]/SCALE,box[1]/SCALE,(box[2]-box[0])/SCALE,(box[3]-box[1])/SCALE]
 else:box=[round(rect[0]*SCALE),round(rect[1]*SCALE),round((rect[0]+rect[2])*SCALE),round((rect[1]+rect[3])*SCALE)]
 file=name+'.png';im.crop(box).save(OUT/file)
 return {'file':file,'rect':rect,'sourceLeaves':[r['path'] for r in rr]}
def bind(screen,id,rr,rect=None):M['bindings'].setdefault(screen,{})[id]=save(screen+'_'+id,rr,rect or node(screen,id))
def take(rr,*prefixes):return [r for r in rr if any(r['path'].startswith(p) for p in prefixes)]

def main():
 # Evidence image/body chrome; story evidence image and body are separate.
 e=rows('techou_kotodama_US')
 bind('evidence','PeImagePlate',take(e,'i_black/'))
 bind('evidence','PePagePlate',take(e,'p_page/i_black/','p_page/3'))
 bind('evidence','PeBodyPlate',take(e,'i_text_base/','p_line_'),[0,0,1280,720])
 M['states']['evidenceChrome']=save('evidence_chrome',take(e,'i_black/','i_text_base/','p_line_','p_scroll_setumei_base/','p_scroll_setumei/'),[0,0,1280,720])
 for state,key in [('fl_wait_000','off'),('fl_wait_000','on')]:
  rr=rows('techou_kotodama_list_US',state);pick=take(rr,'i_list_base_000/');pick+=take(rr,'p_ef_000/') if key=='on' else []
  M['states']['evidence_row_'+key]=save('evidence_row_'+key,pick,[0,81.33333,566.66667,55.33333])
 # Gift cell source images are actual transparent256px carriers, not square cards.
 icon=rows('techou_present_icon_US','fl_wait_on');g=rows('techou_present_US')
 for name,paths in [('base',['p_item_base/']),('selected',['p_waku_ef_base_000/','p_ef_color_000/']),('unknown',['p_item_icon/'])]:
  rr=take(icon,*paths)
  if name=='unknown':
   tex=next((BANK/'present_icon_999').glob('*.png'));im=Image.open(tex);im.save(OUT/'gift_unknown.png');M['states']['gift_unknown']={'file':'gift_unknown.png','rect':[0,0,*im.size]};continue
  M['states']['gift_'+name]=save('gift_'+name,rr,[0,0,512/3,512/3])
 for i in range(27):
  for prefix,state in [('PgBase','base'),('PgFrame','selected')]:M['bindings'].setdefault('gift',{})[prefix+str(i)]={**M['states']['gift_'+state],'rect':node('gift',prefix+str(i))}
  a=node('gift','PgNew'+str(i));M['bindings']['gift']['PgNew'+str(i)]=save('gift_new',take(icon,'p_item_new/i_new/i_new/'),[52.33333,26,68.26562,22.39966]);M['bindings']['gift']['PgNew'+str(i)]['rect']=a
 bind('gift','PgGridPlate',take(g,'1'))
 bind('gift','PgBodyPlate',take(g,'i_black/'))
 bind('gift','PgTitlePlate',take(g,'p_setumei_title_base/'),[0,446,1280,214])
 M['states']['giftChrome']=save('gift_chrome',take(g,'1','i_black/','p_setumei_title_base/','p_no/i_no_bese_','i_scroll_','p_scroll/','p_complete/1'),[0,0,1280,720])
 # Report uses own standing/strip portraits and exact original name/record chrome.
 c=rows('techou_tsusinbo_chara_US');strip=rows('techou_tsusinbo_chara_kirikae','fl_wait_000')
 for id,prefix in [('PrNamePlate','i_bg/'),('PrNameTop','i_beta_000/'),('PrNameBottom','i_beta_001/')]:bind('report',id,take(c,prefix))
 bind('report','PrNamePlate',take(c,'i_bg/','i_ef_black_'),[0,162.66667,1280,86.66667])
 bind('report','PrStrip',take(strip,'i_base/','i_button_base_'))
 M['reportPortraitSelection']={'selectedMultiply':1,'unselectedMultiply':0.1640625,'source':'techou_tsusinbo_chara_kirikae fl_wait_N, no invented underline'}
 for level in range(6):
  rr=[r for r in c if r['path']=='p_kizuna/1' or r['path'].startswith('p_kizuna/p_kizuna_first/') or any(r['path'].startswith(f'p_kizuna/p_kizuna_{j:03d}/') for j in range(level))]
  M['states']['affinity_'+str(level)]=save('affinity_'+str(level),rr,node('report','PrAffinity'))
 for label,key in [('fl_wait_0','profile'),('fl_wait_1','memo')]:
  rr=rows('techou_tsusinbo_message_US',label)
  # Dynamic FTE page/rank values are excluded, preserving same family ink.
  rr=[r for r in rr if not r['resource'].startswith(('koukando_','level_'))]
  M['states']['report_'+key]=save('report_'+key,rr,[0,0,1280,720])
 # Actual skill list/equipped dark gradients, dotted rows, point wedges and frame.
 for side,name,origin in [('catalog','techou_skill_list_US',[97*2/3,127*2/3]),('equipped','techou_set_skill_US',[1157*2/3,126*2/3])]:
  rr=rows(name,'fl_wait_on_000');background=take(rr,'i_black_beta/','i_gra_line_')
  bind('skill','PsPanel'+side,shift(background,origin),[0,0,1280,720])
  for i in range(7):
   state=rows(name,f'fl_wait_on_{i:03d}');M['states']['skill_'+side+'_'+str(i)]=save('skill_'+side+'_'+str(i),shift(take(state,'i_ef/'),origin))
 s=rows('techou_skill_window_US','fl_wait_skilllist')
 bind('skill','PsDescriptionPlate',take(s,'i_window_beta_black/'))
 bind('skill','PsDescriptionFrame',take(s,'i_window_waku/','i_window_waku_gra/'))
 # Rule cover/title/body/number frame/arrows from rule-reader, never Pad-home icon.
 k=rows('techou_kousoku_text');cover=rows('techou_kousoku_00_US')
 bind('rules','KrCover',take(cover,'p_koushou/1'))
 bind('rules','KrCoverTitleBand',take(cover,'p_title_base/'))
 bind('rules','KrBodyShade',take(k,'i_base/'),[118,499.33333,1037.33333,182.66667])
 bind('rules','KrNumberBase',take(k,'18','p_page_base_color/'),[518.66667,74.66667,226.66667,87.33333])
 for kind,prefix in [('Next','p_yazirusi_000/'),('Prev','p_yazirusi_001/')]:
  for i in range(2):bind('rules','Kr'+kind+str(i),take(k,prefix+f'i_yazirusi_{i:03d}/'))
 # Original numeric sprites offered to runtime for dynamic quantities/page values.
 for family in ['techou_present_icon_US','techou_kousoku_text','techou_skill_list_US']:
  for i in range(10):
   file=BANK/family/f'number_{i:03d}.png.png'
   if file.exists():
    dest='digits_'+family+'_'+str(i)+'.png';Image.open(file).save(OUT/dest);M['states'][family+'_digit_'+str(i)]={'file':dest,'rect':[0,0,*Image.open(file).size]}
 (OUT/'layout.json').write_text(json.dumps(M,ensure_ascii=False,indent=2),encoding='utf-8');print('PAD_DETAIL_SOURCE',sum(map(len,M['bindings'].values())),len(M['states']))
if __name__=='__main__':main()
