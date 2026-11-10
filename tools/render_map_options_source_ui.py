"""Exact Map/options family chrome; own atlas and PC-only setting values stay separate."""
from pathlib import Path
import json
from PIL import Image
from render_adv_source_ui import ROOT,SCALE,composite
BANK=ROOT/'ui/v3_authorized/map_options_source';OUT=ROOT/'ui/v4/map_options_source'
X=json.loads((BANK/'layout.json').read_text(encoding='utf-8'));B=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'));M={'bindings':{'map':{},'options':{}},'extra':{},'source':'Map/options own-family bitmap+SFL affine, original RGBA. Own connected-world atlas and platform display values retained; original native animation not claimed.'}
def rows(n,l='fl_wait'):return X[n]['states'][l]
def take(rr,*prefixes):return[r for r in rr if any(r['path'].startswith(p)for p in prefixes)]
def node(screen,id):return next(n for n in B['Assets/UI/'+('PadMapV4'if screen=='map'else'OptionsV4')+'.hbwidget.json']['nodes']if n['id']==id)['slot']['offset']
def save(name,rr,rect):
 im=composite(rr);box=[round(rect[0]*SCALE),round(rect[1]*SCALE),round((rect[0]+rect[2])*SCALE),round((rect[1]+rect[3])*SCALE)];im.crop(box).save(OUT/(name+'.png'));return{'file':name+'.png','rect':rect,'sourceLeaves':[r['path']for r in rr]}
def bind(screen,id,rr,rect=None):M['bindings'][screen][id]=save(screen+'_'+id,rr,rect or node(screen,id))
def main():
 rr=rows('techou_map_list_US','fl_list_wait_000')
 bind('map','MpListShade',take(rr,'i_dammy/','i_base/','p_title_base_color_'),[0,132.66667,333.33333,325])
 bind('map','MpListActive',take(rr,'p_base_act/'))
 for id,p in [('MpScrollBase','i_scroll_base/'),('MpScrollTrack','i_scroll_base_grey/'),('MpScroll','p_scroll_color/')]:bind('map',id,take(rr,p))
 chara=rows('techou_map_list_US','fl_chara_wait');contract=json.loads((ROOT/'docs/analysis/v3_rebuild/pad_map_ui_contract.json').read_text(encoding='utf-8'))
 for cell in contract['character_search']['cells']:
  for id,key in [('MpCharBase','base'),('MpCharDim','disabled_overlay'),('MpCharUnavailable','unavailable_overlay'),('MpCharSelected','selected')]:
   prefix=cell['parts'][key]['path'].replace('/depth1','/1');selected=[r for r in chara if r['path']==prefix]
   assert selected,(id,cell['index'],prefix)
   bind('map',id+str(cell['index']),selected)
 M['extra']['map_region']=save('map_region',take(rows('techou_map'),'i_plate/','p_plate_color/'),[0,60,780,93])
 # The PC labels Q/E and Korean place/student values remain native text.
 o=rows('techou_system_option_US')
 for id,p in [('OptionsListShade','i_icon_base_beta/'),('OptionsNoticeShade','i_setumei_base_beta/'),('OptionsScrollBase','i_scroll_base/'),('OptionsScrollTrack','i_scroll_yohaku_base/'),('OptionsScroll','p_scroll/')]:bind('options',id,take(o,p))
 for i in range(4):bind('options','OptionsFrame'+str(i),take(o,f'p_line_waku_{i:03d}/'),[0,0,1280,720])
 M['extra']['options_notice']=save('options_notice',take(o,'p_setumei_base_color/','29'),[0,491.33333,1280,170.66667])
 # Use the existing common-confirm family for the PC-only keep/revert popup.
 p=ROOT/'ui/v4/pad_system_source/confirm_background.png';im=Image.open(p);box=im.getbbox();assert box;im.crop(box).save(OUT/'display_confirm.png');M['extra']['display_confirm']={'file':'display_confirm.png','rect':[0,0,600,220]}
 (OUT/'layout.json').write_text(json.dumps(M,ensure_ascii=False,indent=2),encoding='utf-8');print('MAP_OPTIONS_SOURCE',len(M['bindings']['map']),len(M['bindings']['options']))
if __name__=='__main__':main()
