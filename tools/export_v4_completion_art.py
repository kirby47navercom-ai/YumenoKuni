"""Preserve built-in originals and locally4x export actual atlas cells; never repaint art."""
from pathlib import Path
import argparse,json,hashlib,shutil
from PIL import Image
from upscale_v4_assets import run
R=Path(__file__).resolve().parents[1];O=R/'art/v4_production/completion'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('job');ap.add_argument('generated');a=ap.parse_args();j=json.loads(Path(a.job).read_text(encoding='utf8'));kind=j['kind'];ident=j['id'];folder=R/'art/completion_v4'/kind;folder.mkdir(parents=True,exist_ok=True)
 src=Path(a.generated);native=folder/(ident+'.png');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 if native.exists():assert sha(native)==sha(src),'Use a revision ID'
 else:shutil.copy2(src,native)
 with Image.open(native) as im:
  size=im.size;im.save(native.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
 hd=f'art/hd_v4/completion/{kind}/{ident}.png';run({'id':ident,'family':kind,'source':native.relative_to(R).as_posix(),'output':hd})
 children=[]
 with Image.open(R/hd) as im:
  im=im.convert('RGBA');W,H=im.size
  cells=j.get('option_uv')
  if not cells and kind=='fx_flipbook':
   cols,rows=j['frame_grid'];cells={f'{i:02d}':[i%cols/cols,i//cols/rows,(i%cols+1)/cols,(i//cols+1)/rows] for i in range(j['frames'])}
  if cells:
   out=folder/'cells';out.mkdir(exist_ok=True)
   for key,uv in cells.items():
    bounds=tuple(round(v*(W if i%2==0 else H)) for i,v in enumerate(uv));tile=im.crop(bounds)
    # Puzzle panels may be portrait or landscape. Preserve their actual geometry;
    # aspect containment belongs to presentation, never stretch a face to16:9.
    p=out/(ident+'_'+key+'.png');tile.save(p);tile.save(p.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
    children.append({'key':key,'file':p.relative_to(R).as_posix(),'webp':p.with_suffix('.webp').relative_to(R).as_posix(),'size':list(tile.size),'uv':uv,'alpha_extrema':list(tile.getchannel('A').getextrema()),'aspect_mode':'contain with uniform scale, NEVER stretch/crop','source':'technical cell export from complete4x atlas; no semantic painting'})
 rec={**j,'tool':'built-in image_gen','source_file':native.relative_to(R).as_posix(),'original_generated_file':str(src),'source_size':list(size),'source_image_sha256':sha(native),'hd_file':hd,'hd_size':[W,H],'cells':children,'upscale':'complete','visual_status':'source/temporal/candidate inspection pending','runtime_integrated':False}
 native.with_suffix('.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(ident,'source+local4x+',len(children),'cells',flush=True)
if __name__=='__main__':main()
