"""Explicit original-story NAI V5 CG jobs with per-character captions and synchronous HD.
Never executes old rejected requests, changes the model, or retries an uncertain paid call.
"""
from pathlib import Path
import argparse,io,json,os,zipfile,hashlib,re
import requests
from PIL import Image
from generate_tpose_nai import build_payload
from generate_v4_nai_cg import token_from_current_user
from upscale_v4_assets import run as upscale
ROOT=Path(__file__).resolve().parents[1]
STYLE='best quality, highres, danganronpa (style), original anime mystery visual novel event CG, expressive angular faces, fine variable-width dark ink linework, detailed hair strands, firm clean cel shadows, subdued rich colors, deliberate cinematic composition, psychological tension'
NEG='lowres, blurry, text, letters, watermark, logo, signature, extra person, duplicated character, identical faces, extra limbs, malformed hands, deformed anatomy, nudity, sexualized, pinup, gore, exposed organs, dismemberment, red blood, glamour, photorealism, 3d render, smiling at viewer, looking at viewer, collage, split screen'

def run(job,token):
    raise SystemExit('NAI generation disabled by current user instruction; no request sent.')
    dest=ROOT/job['output'];dest.parent.mkdir(parents=True,exist_ok=True);mp=dest.with_suffix('.json')
    if dest.exists():
        if not mp.exists():raise RuntimeError('Existing art without metadata; inspect instead of overwrite '+job['id'])
        meta=json.loads(mp.read_text(encoding='utf8'))
        assert meta['spec_sha256']==hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'Job changed; create revision ID'
    else:
        positive=STYLE+', '+job['scene'];negative=NEG+', '+job.get('negative','')
        payload=build_payload(positive,negative,job['seed']);payload['parameters'].update(width=1536,height=1024)
        characters=[{'char_caption':c['description'],'centers':[{'x':c['x'],'y':c.get('y',.5)}]} for c in job.get('characters',[])]
        payload['parameters']['v4_prompt']={'caption':{'base_caption':positive,'char_captions':characters},'use_coords':True,'use_order':True}
        payload['parameters']['v4_negative_prompt']={'caption':{'base_caption':negative,'char_captions':[{'char_caption':'extra limbs, malformed hands, text','centers':c['centers']} for c in characters]}}
        try:r=requests.post('https://image.novelai.net/ai/generate-image',json=payload,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},timeout=180)
        except requests.RequestException:print(job['id'],'network outcome uncertain; stop without paid retry',flush=True);return False
        if r.status_code!=200:
            try:message=json.dumps(json.JSONDecoder().raw_decode(r.text)[0],ensure_ascii=False)
            except (ValueError,TypeError):message='non-JSON body omitted'
            print(job['id'],'HTTP',r.status_code,re.sub(r'pst-[A-Za-z0-9_-]+','[REDACTED]',message).replace(token,'[REDACTED]')[:400],flush=True);return False
        with zipfile.ZipFile(io.BytesIO(r.content)) as archive:
            names=[n for n in archive.namelist() if n.endswith('.png')];assert len(names)==1
            dest.write_bytes(archive.read(names[0]))
        with Image.open(dest) as im:im.save(dest.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
        meta={**job,'model':payload['model'],'tool':'NovelAI V5','positive_prompt':positive,'negative_prompt':negative,'character_captions':characters,'spec_sha256':hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'runtime_integrated':False,'visual_status':'not yet accepted','hd_file':f"art/hd_v4/cg/full/{job['id']}.png"}
        mp.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    upscale({'id':'cg_full_'+job['id'],'source':dest.relative_to(ROOT).as_posix(),'output':meta['hd_file'],'family':'story_cg'})
    meta['upscale']='complete';mp.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(job['id'],'generated and HD; visual acceptance pending',flush=True);return True

def main():
    raise SystemExit('NAI generation disabled by latest user instruction; no request sent')
    ap=argparse.ArgumentParser();ap.add_argument('jobs');ap.add_argument('--ids',nargs='+');ap.add_argument('--use-current-user-key',action='store_true');args=ap.parse_args()
    token=os.environ.get('NAI_TOKEN')
    if not token and args.use_current_user_key:token=token_from_current_user()
    if not token:raise SystemExit('NAI_TOKEN unavailable; no requests sent')
    jobs=json.loads((ROOT/args.jobs).read_text(encoding='utf8'))['jobs']
    if args.ids:jobs=[j for j in jobs if j['id'] in args.ids]
    for job in jobs:
        if not run(job,token):raise SystemExit(1)

if __name__=='__main__':main()
