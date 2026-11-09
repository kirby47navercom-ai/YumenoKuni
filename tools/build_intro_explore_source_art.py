"""Source-only Intro, ADV reticle and PadHome button material correction."""
import runpy,json,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];core=runpy.run_path(str(ROOT/'tools/build_trial_input_source_art.py'));g=core['comp'].__globals__
BANK=ROOT/'ui/v3_authorized/intro_explore_source';OUT=ROOT/'ui/v4/intro_explore_source';OUT.mkdir(parents=True,exist_ok=True)
g.update(L=json.loads((BANK/'layout.json').read_text(encoding='utf-8')),M=json.loads((BANK/'manifest.json').read_text(encoding='utf-8')),OUT=OUT,records={})
original_texture=core['texture']
def texture(file,resource):return original_texture(file,'additive_DXT1.png' if 'DXT1' in resource else resource)
g['texture']=texture
def sprite(name,im):
 p=OUT/(name+'.png');im.save(p);g['records'][name]={'file':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(im.size)}
def direct(name,resource):
 row=core['res']('t_nonstop_start_US',resource);im=texture(row['file'],resource).copy();box=im.getbbox()
 if not box:raise ValueError('Empty Korean source glyph '+resource)
 sprite(name,im.crop(box))
def main():
 # The supplied Korean patch intentionally erases three of the eight JP
 # character slots. Keep only the five actual Korean letters, in own existing
 # five animation carriers; animation/camera/timing code is not rewritten.
 for i,(body,glow) in enumerate([('t_nonstop_tx_000_JP.png','t_nonstop_tx_a_000_DXT1_JP.png'),('t_nonstop_tx_s_002_JP.png','t_nonstop_tx_a_s_002_DXT1_JP.png'),('t_nonstop_tx_s_003_JP.png','t_nonstop_tx_a_003_DXT1_JP.png'),('t_nonstop_tx_s_006_JP.png','t_nonstop_tx_a_006_DXT1_JP.png'),('t_nonstop_tx_007_JP.png','t_nonstop_tx_a_007_DXT1_JP.png')]):
  bodyrow=core['res']('t_nonstop_start_US',body);glowrow=core['res']('t_nonstop_start_US',glow)
  ink=texture(bodyrow['file'],body).copy();halo=texture(glowrow['file'],glow).resize(ink.size,Image.Resampling.LANCZOS)
  # Both source display-list quads have the same local extent, although the
  # blur bitmap has half-resolution storage. Share one union crop so the
  # original blue halo registers with the black brush strokes.
  a,b=ink.getbbox(),halo.getbbox();box=(min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3]))
  sprite('nonstop_glyph'+str(i),ink.crop(box));sprite('nonstop_glow'+str(i),halo.crop(box))
 direct('nonstop_start','t_nonstop_tx_l_a_000_DXT1_JP.png');direct('nonstop_start_echo','t_nonstop_tx_l_a_000_DXT1_JP.png');direct('nonstop_hoop','t_nonstop_hoop_000_DXT1.png')
 frame=g['L']['t_nonstop_start_US']['frames'][30]
 core['save']('nonstop_streaks',core['comp']([r for r in frame if 't_nonstop_line_' in r['resource']]))
 core['save']('nonstop_title',core['comp']([r for r in frame if 't_nonstop_tx_' in r['resource']]))
 # A 200px viewport preserves the exact133px idle ring and200px focus halo.
 # Original center is(0,0); compose centrally then crop only this local plane.
 for name,state in [('ex_cross','fl_wait'),('ex_cross_on','fl_focus')]:
  family=g['L']['adv_search_target'];frame=family['frames'][family['labels']['fl_focus']-family['labels']['fl_in']+10] if state=='fl_focus' else family['states'][state]
  data=[r for r in frame if not r['path'].startswith('p_tex_mark_')]
  im=core['comp'](data,(640,360)).crop((1080,520,1480,920));sprite(name,im)
 # techou_top carries the original common buttons. Never substitute themed
 # type027 icons or fabricate circular frames around them.
 for key,family in [('map','map'),('bullet','kotodama'),('gift','present'),('card','tsusinbo'),('rules','rules'),('option','system')]:
  data=[r for r in g['L']['techou_top']['states']['fl_wait'] if r['path'].startswith(('i_icon_waku_'+('presents' if family=='present' else family)+'/','p_category_'+family+'_base/'))]
  if not data:raise ValueError('Missing original PadHome button '+key)
  core['save']('pad_icon_'+key,core['comp'](data))
 (OUT/'manifest.json').write_text(json.dumps({'sourceManifest':'ui/v3_authorized/intro_explore_source/manifest.json','records':g['records'],'scope':'Provided Korean NonstopStart five visible glyph carriers + same-family line/ring; original ADV idle/focus reticle in200px viewport; original techou_top common buttons. Existing camera/timing/mechanics are preserved. AreaBand/Icon deliberately excluded because no matching native field role was established; do not reuse target-name/map-N as a place header.'},ensure_ascii=False,indent=2),encoding='utf-8');print('INTRO_EXPLORE_SOURCE_ART',len(g['records']))
if __name__=='__main__':main()
