"""Exact admitted Imagination tiles/HUD; preserve existing native state IDs."""
import runpy,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops,ImageOps
ROOT=Path(__file__).resolve().parents[1];core=runpy.run_path(str(ROOT/'tools/build_trial_input_source_art.py'));g=core['comp'].__globals__
M=json.loads((ROOT/'ui/v3_authorized/all_general/manifest.json').read_text(encoding='utf-8'));OUT=ROOT/'ui/v4/mine_source';OUT.mkdir(parents=True,exist_ok=True);records={}
def src(resource,additive=False):
 r=next(r for r in M['textures'] if r['container']=='imagination_US' and r['resource']==resource)
 return core['texture'](r['file'],resource.removesuffix('.png')+'_DXT1.png' if additive else resource).copy()
def save(name,im,resources):
 p=OUT/(name+'.png');im.save(p);records[name]={'file':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'resources':resources,'size':list(im.size)}
def main():
 for key,n in [('w',1),('p',2),('y',3),('b',4)]:
  resource=f'piece_{n:03d}.png';tile=src(resource);save('tile_'+key,tile,[resource])
  cracked=tile.copy();cracked.alpha_composite(src('piece_crack_2.png'));save('tile_'+key+'_break',cracked,[resource,'piece_crack_2.png'])
  for mask in range(1,16):
   # Native selection glows only on exposed group edges. Clip the actual
   # conc-effect bitmap; do not replace its bevel with an invented stroke.
   glow=src('piece_conc_ef.png');allowed=Image.new('L',(80,80))
   for bit,box in [(1,(0,0,80,18)),(2,(62,0,80,80)),(4,(0,62,80,80)),(8,(0,0,18,80))]:
    if mask&bit:allowed.paste(255,box)
   glow.putalpha(ImageChops.multiply(glow.getchannel('A'),allowed));selected=tile.copy();selected.alpha_composite(glow);save('tile_'+key+'_edge'+str(mask),selected,[resource,'piece_conc_ef.png'])
  save('chip_'+str(n-1),tile.crop((0,0,24,24)),[resource])
 for n in [1,2]:save('hit_'+str(n),src(f'piece_crack_{n}.png'),[f'piece_crack_{n}.png'])
 for i in range(5):
  resource='t_hkt_cursor_ring1_DXT1.png' if i in [2,4] else 't_hkt_cursor_ring2_DXT1.png';im=src(resource);dot=src('t_hkt_cursor_dot_000.png');im.alpha_composite(dot,((im.width-dot.width)//2,(im.height-dot.height)//2))
  save('cursor_'+str(i),im,[resource,'t_hkt_cursor_dot_000.png'])
 for name,resource in [('meter','t_hkt_gauge_heart10_DXT1.png'),('focus','t_hkt_gauge_star10_DXT1.png')]:
  im=src(resource);box=im.getbbox();im=im.crop(box);save(name,im.crop((im.width*4//10,0,im.width*5//10,im.height)),[resource])
 base=src('t_hkt_gauge_base10.png');back=Image.new('RGBA',(base.width,base.height*2+4));back.alpha_composite(base,(0,0));back.alpha_composite(base,(0,base.height+4));save('meter_back',back,['t_hkt_gauge_base10.png'])
 for palette in ['g','r']:
  for i in range(11):
   resource=f't_time_num_{i:03d}.png';im=src(resource)
   if palette=='r':
    alpha=im.getchannel('A');im=ImageOps.colorize(im.convert('L'),(60,0,30),(255,105,170)).convert('RGBA');im.putalpha(alpha)
   save('digit_'+palette+('colon' if i==10 else str(i)),im,[resource])
 save('question',src('t_hkt_mondai_pl_000.png'),['t_hkt_mondai_pl_000.png'])
 save('stage',src('t_hkt_bg_ef_bl_DXT1.png'),['t_hkt_bg_ef_bl_DXT1.png'])
 line=src('t_hkt_grid_DXT1.png');board=Image.new('RGBA',(1080,600));strip=line.resize((1080,8),Image.Resampling.LANCZOS);board.alpha_composite(strip,(0,0));board.alpha_composite(strip,(0,592));save('board_frame',board,['t_hkt_grid_DXT1.png'])
 save('bottom_frame',line.resize((1280,50),Image.Resampling.LANCZOS),['t_hkt_grid_DXT1.png'])
 (OUT/'manifest.json').write_text(json.dumps({'sourceManifest':'ui/v3_authorized/all_general/manifest.json','records':records,'scope':'Exact decoded Imagination assets; normal/break/edge masks preserve current C++ contracts. Edge selection clips existing piece_conc glow. Stage remains translucent original blue effect so court can show through. No mechanics/story/image/solution changes. Missing piece_change_ef_mask is not guessed or decoded.'},ensure_ascii=False,indent=2),encoding='utf-8');print('MINE_SOURCE_ART',len(records))
if __name__=='__main__':main()
