"""Copy an image_gen result and record provenance, without repainting the generated art."""
from pathlib import Path
import argparse,json,hashlib,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('job');ap.add_argument('source');args=ap.parse_args()
jobs=json.loads((ROOT/'art/v4_production/derived_jobs.json').read_text(encoding='utf8'))['jobs']
job=next(j for j in jobs if j['id']==args.job)
source=Path(args.source).resolve();assert source.is_file()
out=ROOT/job['output'];out.parent.mkdir(parents=True,exist_ok=True)
assert not out.exists(),'existing export must not be overwritten silently'
shutil.copy2(source,out)
im=Image.open(out).convert('RGBA');assert im.getchannel('A').getextrema()[0]==0
im.save(out.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=6)
record={**job,'tool':'built-in image_gen','generated_source':str(source),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'size':list(im.size),'alpha_bbox':im.getchannel('A').getbbox(),'status':'generated; full-resolution individual review required','upscale':'pending','runtime_integrated':False}
out.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(args.job,'exported',list(im.size))
# Every new project drawing also receives the user-requested AI HD master.
# This is a synchronous export step, not a schedule or background automation.
from upscale_v4_assets import run as upscale
hd='art/hd_v4/'+('clean_masters' if job['family']=='master_cleanup' else 'derived')+'/'+job['character']+'/'+job['id']+'.png'
upscale({'id':job['id'],'source':job['output'],'output':hd,'family':job['family']})
record['upscale']='4x Real-ESRGAN complete; individual HD review pending'
record['hd_file']=hd
out.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
