"""Audit HD exports and prepare per-image inspection pages. No automatic visual approval."""
from pathlib import Path
import json,hashlib,argparse
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Game/Saved/v4-hd-review';OUT.mkdir(parents=True,exist_ok=True)
jobs=json.loads((ROOT/'art/v4_production/upscale_jobs.json').read_text(encoding='utf8'))['jobs']
ap=argparse.ArgumentParser();ap.add_argument('--ids',nargs='+');args=ap.parse_args()
report_path=ROOT/'art/v4_production/hd_qa.json'
reports=[]
if args.ids and report_path.exists():
    current_ids={j['id'] for j in jobs}
    reports=[r for r in json.loads(report_path.read_text(encoding='utf8'))['art'] if r['id'] in current_ids and r['id'] not in args.ids]
for job in jobs:
    if args.ids and job['id'] not in args.ids:continue
    src=ROOT/job['source'];hd=ROOT/job['output'];stamp=hd.with_suffix('.json')
    if not stamp.exists():continue
    meta=json.loads(stamp.read_text(encoding='utf8'))
    assert meta['source_sha256']==hashlib.sha256(src.read_bytes()).hexdigest(),job['id']
    with Image.open(src) as f:lo=f.convert('RGBA')
    with Image.open(hd) as f:hi=f.convert('RGBA')
    assert hi.size==(lo.width*4,lo.height*4),job['id']
    with Image.open(hd.with_suffix('.webp')) as f:
        assert f.convert('RGBA').tobytes()==hi.tobytes(),job['id']
    clear=lo.getchannel('A').getextrema()[0]==0
    # A transparent effect may intentionally extend into a corner. Only corners
    # clear in the source must remain clear; do not impose sprite framing on VFX.
    for source_corner,hd_corner in zip([(0,0),(lo.width-1,0),(0,lo.height-1),(lo.width-1,lo.height-1)],
                                     [(0,0),(hi.width-1,0),(0,hi.height-1),(hi.width-1,hi.height-1)]):
        if lo.getpixel(source_corner)[3]==0:assert hi.getpixel(hd_corner)[3]<=2,job['id']
    mask=np.asarray(lo.getchannel('A'))>128;ys,xs=np.where(mask);assert len(xs)
    bbox=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
    top,height=bbox[1],bbox[3]-bbox[1]
    head=mask[top:top+max(1,int(height*.22)),:];hy,hx=np.where(head)
    cx=int(np.median(hx)) if len(hx) else lo.width//2
    # Ears/ahoge and body proportions differ: keep the patch on the face.
    slug=job['id'].removeprefix('master_').split('_')[0]
    face_fraction={'lappy':.47,'rei':.095,'ken':.09,'nana':.095,'taiga':.09}.get(slug,.145)
    if job['id']=='lappy_L11':face_fraction=.62  # intentional upper-body closeup
    cy=int(top+height*face_fraction)
    half=64;cx=max(half,min(lo.width-half,cx));cy=max(half,min(lo.height-half,cy))
    crop=(cx-half,cy-half,cx+half,cy+half)
    page=Image.new('RGB',(1024,1330),'#e8e5de');dr=ImageDraw.Draw(page)
    for i,im in enumerate([lo,hi]):
        preview=Image.new('RGBA',im.size,'#eeeeee');preview.alpha_composite(im);preview.thumbnail((500,750))
        page.paste(preview.convert('RGB'),(i*512+(512-preview.width)//2,30))
    # Same source-space crop: left = nearest enlargement; right = actual 1:1 AI upscale.
    for i,detail in enumerate([lo.crop(crop).resize((512,512),Image.Resampling.NEAREST),hi.crop(tuple(v*4 for v in crop))]):
        base=Image.new('RGBA',detail.size,'#eeeeee');base.alpha_composite(detail);page.paste(base.convert('RGB'),(i*512,800))
    dr.text((8,8),job['id']+' / SOURCE',fill='black');dr.text((520,8),'REAL-ESRGAN 4x / full image scaled for inspection',fill='black')
    dr.text((8,780),'source nearest x4 (comparison only)',fill='black');dr.text((520,780),'HD detail crop at 1:1 pixels',fill='black')
    page.save(OUT/(job['id']+'.jpg'),quality=95)
    reports.append({'id':job['id'],'source':job['source'],'output':job['output'],'size':list(hi.size),'source_hash_match':True,'lossless_webp_equal':True,'clear_background_preserved':clear,'source_visible_bbox':bbox,'edge_touch':bbox[0]==0 or bbox[1]==0 or bbox[2]==lo.width or bbox[3]==lo.height,'inspection_page':str((OUT/(job['id']+'.jpg')).relative_to(ROOT)).replace('\\','/'),'individual_visual_verdict':'pending; never infer from export checks'})
ui=[]
for folder in ('ui/v4/hd','ui/v4/systems_hd','ui/v4/trial_hd'):
    manifest=ROOT/folder/'manifest.json'
    if manifest.exists():ui.extend(json.loads(manifest.read_text(encoding='utf8'))['assets'])
for row in ui:
    assert row['texture_size']==[v*4 for v in row['logical_size']],row['id']
    with Image.open(ROOT/row['file']) as im:assert list(im.size)==row['texture_size']
checked={r['id'] for r in reports}
report={'status':'structural checks only; individual visual reviews recorded separately','art':reports,'vector_ui_4x_checked':len(ui),'requested_art':len(jobs),'upscaled_art_checked':len(reports),'pending_ids':[j['id'] for j in jobs if j['id'] not in checked],'runtime_import_display':'not tested'}
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS',len(reports),'AI 4x exports;',len(ui),'native 4x UI exports; visual acceptance separate')
