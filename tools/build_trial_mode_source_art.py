"""Compose admitted Anagram/Panic/Showdown UI; no game/engine execution."""
import runpy,json,copy,hashlib
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
core=runpy.run_path(str(ROOT/'tools/build_trial_input_source_art.py'))
g=core['comp'].__globals__
BANK=ROOT/'ui/v3_authorized/all_general'
OUT=ROOT/'ui/v4/trial_modes_source';OUT.mkdir(parents=True,exist_ok=True)
g.update(L=json.loads((BANK/'layout.json').read_text(encoding='utf-8')),M=json.loads((BANK/'manifest.json').read_text(encoding='utf-8')),OUT=OUT,records={})

def direct(name,family,resource,additive=False):
 row=core['res'](family,resource)
 im=core['texture'](row['file'],resource if not additive else resource.removesuffix('.png')+'_DXT1.png').copy()
 file=OUT/(name+'.png');im.save(file)
 g['records'][name]={'file':file.relative_to(ROOT).as_posix(),'rect':[0,0,im.width,im.height],'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'family':family,'resource':resource}

def rows(family,state):return copy.deepcopy(g['L'][family]['states'][state])
def scaled(data,factor):
 for r in data:
  r['sourceAffine']=[n*factor for n in r['sourceAffine']];r['rect']=[n*factor for n in r['rect']]
 return data

def main():
 data=rows('ana_bg','fl_in_2')
 core['save']('anagram_background',core['comp'](scaled([r for r in data if r['resource']!='bustup_00_00.png'],4)),True)
 core['save']('anagram_silhouette',core['comp'](scaled([r for r in data if r['resource']=='bustup_00_00.png'],4)),True)
 for name,resource,additive in [('orb','item_004.png',False),('orb_dark','item_000.png',False),('orb_0','item_001.png',False),('orb_1','item_007.png',False),('orb_2','item_002.png',False),('orb_3','item_005.png',False),('aim','cursor_00_00_DXT1.png',False),('spot','spot.png',True),('light','wave.png',True),('slot','box_non.png',True),('rays','t_start_line_DXT1.png',False),('status','base_base.png',False),('subtitle_plate','t_start_pl_000.png',False),('correct_ef','ef_DXT1.png',False),('wrong_ef','sym_DXT1.png',False)]:
  direct('anagram_'+name,'anagram_US',resource,additive)
 core['save']('showdown_frame',core['comp'](rows('t_hr_frame','fl_wait')),True)
 # Separate original left/right argument plane and center transition separator.
 line=rows('t_hr_line_US','fl_left_in_1')
 core['save']('showdown_divider',core['comp']([r for r in line if 'bg_' not in r['resource']]),True)
 direct('showdown_blade','t_hr_zan_pointer_ico','t_hr_zan_pointer_ico_katana.png')
 direct('showdown_pointer_bg','t_hr_zan_pointer_ico','t_hr_zan_pointer_bg_stripe_DXT1.png')
 direct('showdown_pointer_mask','t_hr_zan_pointer_ico','t_hr_zan_pointer_bg_mask.png')
 direct('panic_line','t_panic_line','t_panic_line_000_DXT1.png')
 for i in range(3):direct('panic_intro_'+str(i),'t_panic_in_window',f'base_{i:02d}.png')
 core['save']('panic_word_lock',core['comp'](rows('t_panic_word_off','fl_wait_01')),True)
 (OUT/'manifest.json').write_text(json.dumps({'sourceManifest':'ui/v3_authorized/all_general/manifest.json','records':g['records'],'scope':'Exact original mode bitmaps/SFL planes; Anagram minigame plane320x180 maps4x to1280x720. DXT1 additive black converted to alpha. Anonymous original silhouette only; no original character face/name/story. No runtime execution.'},ensure_ascii=False,indent=2),encoding='utf-8')
 print('TRIAL_MODE_SOURCE_ART',len(g['records']))

if __name__=='__main__':main()
