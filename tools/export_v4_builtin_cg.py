"""Preserve built-in CG originals, perform local 4x upscale and exact 16:9 export.
No image generation or remote API calls. Never overwrite a different source.
"""
from pathlib import Path
import argparse,json,hashlib,shutil
from PIL import Image
from upscale_v4_assets import run
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('job');ap.add_argument('generated');a=ap.parse_args()
    job=json.loads(Path(a.job).read_text(encoding='utf8'));ident=job['id']
    folder=ROOT/'art/cg_v4/builtin';folder.mkdir(parents=True,exist_ok=True)
    src=Path(a.generated);dst=folder/(ident+'.png')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if dst.exists():assert digest(src)==digest(dst),'Revision ID required'
    else:shutil.copy2(src,dst)
    with Image.open(dst) as im:
        size=im.size;assert abs(size[0]/size[1]-16/9)<.005,('Wrong canvas',size)
        im.save(dst.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
    hd=f'art/hd_v4/cg/builtin/{ident}.png'
    run({'id':'cg_builtin_'+ident,'family':'story_cg','source':dst.relative_to(ROOT).as_posix(),'output':hd})
    # Imagegen may round canvas edges to odd pixels. Normalize the delivery raster,
    # with no composition crop, after local super-resolution; preserve raw 4x too.
    final=ROOT/'art/cg_v4/delivery'/f'{ident}.png';final.parent.mkdir(parents=True,exist_ok=True)
    with Image.open(ROOT/hd) as im:
        k=min(im.width//16,im.height//9);target=(16*k,9*k)
        normalized=im.resize(target,Image.Resampling.LANCZOS)
        normalized.save(final);normalized.save(final.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
    record={**job,'manuscript_sha256':job.get('source_sha256'),'tool':'built-in image_gen','original_generated_file':str(src),'source_file':dst.relative_to(ROOT).as_posix(),'source_sha256':digest(dst),'source_size':list(size),'hd_file':hd,'delivery_file':final.relative_to(ROOT).as_posix(),'delivery_size':list(target),'delivery_sha256':digest(final),'aspect_normalization':'full frame resampling only, no crop; original and raw 4x preserved','runtime_integrated':False}
    record['visual_status']='generated; individual scene and HD acceptance pending'
    dst.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(ident,'preserved + 4x + exact 16:9 delivery',target,flush=True)

if __name__=='__main__':main()
