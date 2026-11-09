"""Fit own portraits into the original sixteen perspective card silhouettes."""
from pathlib import Path
import json,re
import numpy as np
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'ui/v4/trial_vote_cards';OUT.mkdir(parents=True,exist_ok=True)
M=json.loads((ROOT/'ui/v3_authorized/trial_inputs/manifest.json').read_text(encoding='utf-8'))
faces={}
for p in sorted((ROOT/'art/trial3d/id_portraits_color_v1/runtime').glob('*_thumb.webp')):
 face=Image.open(p).convert('RGBA')
 assert face.size==(256,256),p
 faces[p.stem.removesuffix('_thumb')]=face
assert len(faces)==16
cards={who:[]for who in faces};cursors=[];polygons=[]
def save(im,name):im.save(OUT/(name+'.png'));return 'Assets/Art/ui/v3/trial_vote_cards/'+name+'.png'
for i in range(16):
 r=next(r for r in M['textures']if r['resource']==f't_tohyo_chara_frame_{i:03d}_blank.png');base=Image.open(ROOT/r['file']).convert('RGBA');a=np.array(base);red=(a[:,:,0]>a[:,:,1]*1.5)&(a[:,:,0]>a[:,:,2]*1.5)&(a[:,:,0]>20)&(a[:,:,3]>200)
 y,x=np.where(red);assert len(x)>1000
 # The corners come from the red inset, leaving the original gray edge intact.
 xy=np.column_stack([x,y]);corners=[xy[np.argmin(x+y)],xy[np.argmax(x-y)],xy[np.argmax(x+y)],xy[np.argmin(x-y)]]
 polygons.append([[float(p[0])/256,float(p[1])/256]for p in corners])
 A=[];b=[]
 for (px,py),(u,v)in zip(corners,[(0,0),(255,0),(255,255),(0,255)]):A.extend([[px,py,1,0,0,0,-u*px,-u*py],[0,0,0,px,py,1,-v*px,-v*py]]);b.extend([u,v])
 matrix=np.linalg.solve(np.array(A),np.array(b));mask=Image.fromarray((red*255).astype('uint8'))
 for who,face in faces.items():
  warped=face.resize((256,256)).transform(base.size,Image.Transform.PERSPECTIVE,matrix,Image.Resampling.BICUBIC);warped.putalpha(ImageChops.multiply(warped.getchannel('A'),mask));out=base.copy();out.alpha_composite(warped);cards[who].append(save(out,f'{who}_{i}'))
 edge=base.copy();z=np.array(edge);z[red,3]=0;z[:,:,:3]=[255,24,66];edge=Image.fromarray(z);cursors.append(save(edge,f'cursor_{i}'))
result={'cards':cards,'cursors':cursors,'polygons':polygons,'scope':'Existing own color ID profile thumbnails inside the original card silhouette and border; perspective fitted from the original blank.'}
(OUT/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8');print({'cards':sum(map(len,cards.values())),'cursors':len(cursors)})
