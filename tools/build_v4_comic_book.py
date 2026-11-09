"""Bake own comic art through one perspective sheet; original art is excluded."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageOps,ImageEnhance
from v4_comic_presentation import build_comic
from v4_comic_geometry import SIZE,MAIN,PREVIOUS,REPLAY,homography,panels,thumb

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ui/v4/climax_book_20261107'

def picture(path,size):
    im=Image.open(ROOT/path).convert('RGB')
    if not path.startswith('ui/'):
        # Approved art carries an outer cream print border. The comic sheet
        # supplies its own gutters, so remove that border, not scene content.
        w,h=im.size;im=im.crop((round(w*.035),round(h*.055),round(w*.965),round(h*.945)))
    # Preserve the entire authored evidence, never crop an essential prop.
    return ImageOps.pad(im,size,method=Image.Resampling.LANCZOS,color=(5,4,8))

def warp(im,quad):
    inv=np.linalg.inv(homography(quad));inv/=inv[2,2]
    return im.transform((1280,720),Image.Transform.PERSPECTIVE,tuple(inv.ravel()[:8]),Image.Resampling.BICUBIC)

def save(name,im):
    box=im.getbbox();assert box
    file=OUT/(name+'.webp');im.crop(box).save(file,lossless=True,method=5)
    return dict(texture=file.relative_to(ROOT).as_posix(),rect=[box[0],box[1],box[2]-box[0],box[3]-box[1]],rotation=0)

def build():
    OUT.mkdir(exist_ok=True,parents=True)
    meta=build_comic();shared=json.loads((ROOT/'ui/v4/climax_original_20261106/runtime.json').read_text())
    question=shared['sharedPageUI']['questionPink']['texture'];books={}
    for ident,task in meta['tasks'].items():
        pages=[];slot_records={};replay=[]
        for p,page in enumerate(task['pages']):
            shapes=panels(len(page['slots'])+len(page['contexts']))
            base=Image.new('RGBA',SIZE,(3,2,5,255));answers={}
            for j,index in enumerate(page['slots']):
                x,y,w,h=shapes[j];base.paste(picture(question,(w,h)),(x,y))
                s=task['slots'][index];answer=next(a for a in s['options'] if a['id']==s['answer'])
                answers[index]=(picture(answer['image'],(w,h)),(x,y,w,h))
            for j,path in enumerate(page['contexts'],len(page['slots'])):
                x,y,w,h=shapes[j];base.paste(picture(path,(w,h)),(x,y))
            record={'base':save(f'{ident}-p{p}-base',warp(base,MAIN)),
                    'previous':save(f'{ident}-p{p}-previous',ImageEnhance.Brightness(warp(base,PREVIOUS)).enhance(.32)),
                    'thumb':save(f'{ident}-p{p}-thumb',warp(base,thumb(p))),
                    'thumbQuad':thumb(p),'slots':page['slots']}
            if p==0:
                cover=base.copy();draw=ImageDraw.Draw(cover)
                for j in range(len(page['slots'])):
                    x,y,w,h=shapes[j];draw.rectangle((x,y,x+w,y+h),fill=(3,2,5,255))
                record['cover']=save(f'{ident}-cover',ImageEnhance.Brightness(warp(cover,PREVIOUS)).enhance(.32))
            filled=base.copy()
            # Replay is a real page reveal, with every existing response once.
            for index in page['slots']:
                art,(x,y,w,h)=answers[index]
                layer=Image.new('RGBA',SIZE);layer.paste(art,(x,y))
                slot_records[str(index)]={'filled':save(f'{ident}-s{index}-filled',warp(layer,MAIN)),
                    'previous':save(f'{ident}-s{index}-previous',ImageEnhance.Brightness(warp(layer,PREVIOUS)).enhance(.32)),
                    'thumb':save(f'{ident}-s{index}-thumb',warp(layer,thumb(p)))}
            # Hide not-yet-told panels, rather than spoiling the final answer.
            revealed=Image.new('RGBA',SIZE,(0,0,0,255))
            for j,path in enumerate(page['contexts'],len(page['slots'])):
                x,y,w,h=shapes[j];revealed.paste(picture(path,(w,h)),(x,y))
            for index in page['slots']:
                art,(x,y,w,h)=answers[index];revealed.paste(art,(x,y));filled.paste(art,(x,y))
                replay.append({'slot':index,'page':p,'image':save(f'{ident}-s{index}-replay',warp(revealed,REPLAY))})
            record['complete']=save(f'{ident}-p{p}-complete',warp(filled,REPLAY));pages.append(record)
        book={'pages':pages,'slots':slot_records,'replay':replay,
              'geometry':'Video-calibrated homography; original camera/FOV not claimed.'}
        (OUT/(ident+'.json')).write_text(json.dumps(book,separators=(',',':')),encoding='utf8');books[ident]='ui/v4/climax_book_20261107/'+ident+'.json'
    manifest={'schema':1,'sourceVideo':'https://www.youtube.com/watch?v=hCqejpi6Hps&t=5550s','sourceFrameSeconds':5550.847924,'screenQuad':MAIN,'ownArtOnly':True,'books':books}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps({'books':len(books),'pages':18,'files':len(list(OUT.glob('*.webp')))}))
def update_thumbs():
    meta=build_comic();shared=json.loads((ROOT/'ui/v4/climax_original_20261106/runtime.json').read_text())
    question=shared['sharedPageUI']['questionPink']['texture']
    for ident,task in meta['tasks'].items():
        file=OUT/(ident+'.json');book=json.loads(file.read_text())
        for p,page in enumerate(task['pages']):
            shapes=panels(len(page['slots'])+len(page['contexts']));base=Image.new('RGBA',SIZE,(3,2,5,255))
            for j,index in enumerate(page['slots']):
                x,y,w,h=shapes[j];base.paste(picture(question,(w,h)),(x,y))
                slot=task['slots'][index];answer=next(a for a in slot['options']if a['id']==slot['answer'])
                layer=Image.new('RGBA',SIZE);layer.paste(picture(answer['image'],(w,h)),(x,y))
                book['slots'][str(index)]['thumb']=save(f'{ident}-s{index}-thumb',warp(layer,thumb(p)))
            for j,path in enumerate(page['contexts'],len(page['slots'])):
                x,y,w,h=shapes[j];base.paste(picture(path,(w,h)),(x,y))
            book['pages'][p]['thumb']=save(f'{ident}-p{p}-thumb',warp(base,thumb(p)));book['pages'][p]['thumbQuad']=thumb(p)
        file.write_text(json.dumps(book,separators=(',',':')),encoding='utf8')
    print('Updated 18 book-strip thumbnails and 38 reveal layers only')
if __name__=='__main__':
    import sys
    update_thumbs() if '--thumbs-only'in sys.argv else build()
