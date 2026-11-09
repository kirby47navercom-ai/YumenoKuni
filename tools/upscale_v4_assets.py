"""User-requested native AI super-resolution, non-destructive and resumable by source/model hash."""
from pathlib import Path
import subprocess,argparse,json,hashlib,time
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
BIN=Path('C:/Users/kirby/.codex_tools/portrait_upscale_v30/esrgan/realesrgan-ncnn-vulkan.exe')
MODEL=BIN.parent/'models';NAME='realesrgan-x4plus-anime'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(job):
    src=ROOT/job['source'];dst=ROOT/job['output'];dst.parent.mkdir(parents=True,exist_ok=True)
    stamp=dst.with_suffix('.json');source_sha=sha(src);model_sha=sha(MODEL/(NAME+'.bin'))
    if stamp.exists():
        old=json.loads(stamp.read_text(encoding='utf8'))
        if old.get('source_sha256')==source_sha and old.get('model_sha256')==model_sha and dst.exists() and dst.with_suffix('.webp').exists():
            print(job['id'],'resume: unchanged',flush=True);return
        raise RuntimeError('Existing output changed; create a new version instead of overwriting '+str(dst))
    start=time.monotonic()
    proc=subprocess.run([str(BIN),'-i',str(src),'-o',str(dst),'-m',str(MODEL),'-n',NAME,'-s','4','-t','256','-g','0'],capture_output=True,timeout=240)
    if proc.returncode:raise RuntimeError('AI upscale failed: '+job['id']+' code '+str(proc.returncode))
    with Image.open(src) as im:
        original=im.size
        # Clear sprite backgrounds must stay clear. Near-opaque CG alpha (e.g.248..255)
        # has no transparent outside region and must not be required to acquire one.
        has_clear_background='A' in im.getbands() and im.getchannel('A').getextrema()[0]==0
    with Image.open(dst) as im:
        assert im.size==(original[0]*4,original[1]*4),(job['id'],im.size)
        if has_clear_background:assert 'A' in im.getbands() and im.getchannel('A').getextrema()[0]==0
        im.save(dst.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
        size=list(im.size);alpha=list(im.getchannel('A').getextrema()) if 'A' in im.getbands() else None
    record={**job,'method':'Real-ESRGAN NCNN Vulkan / '+NAME,'scale':4,'source_sha256':source_sha,'model_sha256':model_sha,'binary_sha256':sha(BIN),'source_size':original,'size':size,'alpha_extrema':alpha,'seconds':round(time.monotonic()-start,2),'status':'upscaled; individual sharpness and identity review pending','runtime_integrated':False}
    stamp.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(job['id'],'4x complete',size,flush=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('jobs');ap.add_argument('--ids',nargs='*');args=ap.parse_args()
    jobs=json.loads((ROOT/args.jobs).read_text(encoding='utf8'))['jobs']
    if args.ids:jobs=[j for j in jobs if j['id'] in args.ids]
    for job in jobs:run(job)
if __name__=='__main__':main()
