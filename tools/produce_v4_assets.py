"""NovelAI V5 production from explicit jobs. Safe resume, no secrets in metadata/logs."""
from pathlib import Path
import os,json,argparse,io,zipfile,time,base64,re
import requests
from PIL import Image,ImageOps
from generate_tpose_nai import build_payload
from generate_v4_nai_cg import token_from_current_user,STYLE

ROOT=Path(__file__).resolve().parents[1]
NEG='lowres, worst quality, bad quality, crude drawing, western cartoon, children illustration, text, signature, watermark, logo, shiny skin, sparkles, soft airbrush, extra fingers, missing fingers, extra arms, duplicate person, deformed anatomy, cropped head, cropped feet, desk, podium, scenery, nudity, sexualized, pinup'

def run(job,token):
    raise SystemExit('NAI generation disabled by current user instruction; no request sent.')
    out=ROOT/job['output'];out.parent.mkdir(parents=True,exist_ok=True)
    if out.with_suffix('.json').exists():print(job['id'],'resume: already generated',flush=True);return True
    payload=build_payload(job['prompt'],job.get('negative',NEG),job['seed'])
    width,height=job.get('size',[1024,1536])
    payload['parameters'].update(width=width,height=height)
    source=job.get('source_image')
    if source:
        src=Image.open(ROOT/source).convert('RGBA');base=Image.new('RGBA',src.size,'white');base.alpha_composite(src)
        fitted=ImageOps.pad(base.convert('RGB'),(width,height),color='white',method=Image.Resampling.LANCZOS)
        buf=io.BytesIO();fitted.save(buf,'PNG')
        payload['action']='img2img';payload['parameters'].update(image=base64.b64encode(buf.getvalue()).decode(),strength=job.get('strength',.58),noise=.03,extra_noise_seed=job['seed']+1)
    for attempt in range(3):
        try:resp=requests.post('https://image.novelai.net/ai/generate-image',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},json=payload,timeout=180)
        except requests.RequestException:
            print(job['id'],'network outcome uncertain; no automatic paid retry',flush=True);return False
        if resp.status_code==429:
            if attempt<2:time.sleep(8*(attempt+1));continue
        break
    if resp.status_code!=200:
        safe=re.sub(r'pst-[A-Za-z0-9_-]+','[REDACTED]',resp.text).replace(token,'[REDACTED]')[:300]
        print(job['id'],'HTTP',resp.status_code,safe,flush=True);return False
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.png')]
        if len(names)!=1:print('unexpected image count; stopped',flush=True);return False
        raw=z.read(names[0])
    rawdir=ROOT/'art/_candidates/v4_nai';rawdir.mkdir(parents=True,exist_ok=True)
    rawfile=rawdir/(job['id']+'.png');rawfile.write_bytes(raw)
    image=Image.open(io.BytesIO(raw)).convert('RGBA')
    if job.get('cutout',True):
        from generate_scene_nai import cutout
        image=cutout(str(rawfile))
    image.save(out);image.save(out.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=6)
    record={**job,'model':payload['model'],'generated_action':payload['action'],'size':list(image.size),'runtime_integrated':False,'status':'generated; individual visual acceptance pending','raw_source':rawfile.relative_to(ROOT).as_posix()}
    out.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(job['id'],'generated',flush=True);return True

def main():
    raise SystemExit('NAI generation disabled by latest user instruction; no request sent')
    ap=argparse.ArgumentParser();ap.add_argument('jobs');ap.add_argument('--ids',nargs='*');ap.add_argument('--family');ap.add_argument('--limit',type=int);ap.add_argument('--use-current-user-key',action='store_true');args=ap.parse_args()
    token=os.environ.get('NAI_TOKEN')
    if not token and args.use_current_user_key:token=token_from_current_user()
    if not token:raise SystemExit('NAI_TOKEN unavailable')
    jobs=json.loads((ROOT/args.jobs).read_text(encoding='utf8'))['jobs']
    if args.family:jobs=[j for j in jobs if j['family']==args.family]
    if args.ids:jobs=[j for j in jobs if j['id'] in args.ids]
    if args.limit:jobs=jobs[:args.limit]
    for job in jobs:
        if not run(job,token):raise SystemExit(1)
        time.sleep(2)

if __name__=='__main__':main()
