"""Pack reviewed agreement art with measured head/eye anchors; never invent poses."""
from pathlib import Path
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'art/agreement_v5_20261106';OUT=ROOT/'ui/v4/debate_feedback/agreement';OUT.mkdir(exist_ok=True)
# Own generated art, visually measured against agreement-head-landmark-review.png.
# Crown excludes tall ahoge, cat mask, miniature hat and ponytail, not anatomy.
ANCHORS={
 'mio':(620,100,505,380),'akari':(650,110,540,410),
 'rin':(665,40,490,350),'sho':(640,85,455,320),
 'satsuki':(660,10,440,290),'rei':(625,10,410,270),
 'sora':(650,125,500,365),'ken':(685,10,365,240),
 'nana':(650,10,465,320),'riku':(640,100,480,340),
 'yuu':(650,80,430,290),'koto':(640,10,385,260),
 'taiga':(625,10,395,230),'ai':(650,50,420,290),
 'haruka':(650,10,490,330),'kaede':(650,10,430,300)}
HERO={'head':300.,'eye':370.}
# Preserve source quads. Compensate only inner portrait scale/pivot, not the
# original motion: foreground partner 695.979h/-107.956y, hero 682.667h/-93.333y.
PARTNER={'head':300.*682.6666666667/695.9791666667,
 'eye':(-93.3333333333+370*682.6666666667/1024+107.95625)*1024/695.9791666667}
rows=[]
for slug,(cx,crown,chin,eye) in ANCHORS.items():
 source=SOURCE/(slug+'.png');im=Image.open(source).convert('RGBA');assert im.getchannel('A').getextrema()==(0,255),slug
 for role,target in [('partner',PARTNER),('shadow',HERO)]+([('hero',HERO)]if slug=='mio'else[]):
  scale=target['head']/(chin-crown);dx=512-cx*scale;dy=target['eye']-eye*scale
  layer=im.transform((1024,1024),Image.Transform.AFFINE,(1/scale,0,-dx/scale,0,1/scale,-dy/scale),Image.Resampling.BICUBIC)
  if role=='shadow':
   alpha=layer.getchannel('A');layer=Image.new('RGBA',layer.size,(254,51,203,0));layer.putalpha(alpha)
  file=slug+('_shadow'if role=='shadow'else'_hero'if role=='hero'else'')+'.png';layer.save(OUT/file)
  rows.append({'slug':slug,'role':role,'file':file,'source':source.relative_to(ROOT).as_posix(),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'sha256':hashlib.sha256((OUT/file).read_bytes()).hexdigest(),'headHeight':target['head'],'eyeY':target['eye'],'headCenterX':512,'measuredSource':{'centerX':cx,'crownY':crown,'chinY':chin,'eyeY':eye},'scale':scale,'translation':[dx,dy]})
manifest={'scope':'Dedicated agreement cutins only, all16 distinct reviewed generated poses; common screen head size and eye line without stretching anatomy. Original source quads/timing retained. Generic T03 and other modes not replaced.','canvas':[1024,1024],'hero':HERO,'partner':PARTNER,'rows':rows}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('16 agreement characters / 33 role-calibrated textures; transparent alpha preserved')
