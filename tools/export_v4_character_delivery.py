"""Technical crops and anchors from existing 4x original-project character art; no repaint."""
from pathlib import Path
import json,re,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];O=R/'art/character_delivery_v4';O.mkdir(parents=True,exist_ok=True)
J=json.loads((R/'art/v4_production/upscale_jobs.json').read_text(encoding='utf8'))['jobs']
master={x['id'].replace('master_',''):x for x in J if x['id'].startswith('master_')}
for char,source in {'yuu':'art/masters_clean_v4/yuu.webp','taiga':'art/masters_clean_v4/taiga.webp','haruka':'art/masters_clean_v4/haruka_r2.webp'}.items():
 master[char]=next(x for x in J if x['source']==source)
chars=sorted({x['character'] for x in json.loads((R/'art/v4_production/derived_jobs.json').read_text(encoding='utf8'))['jobs']})
out=[];actors=[];selected=[];qa=R/'Game/Saved/v4-character-delivery';qa.mkdir(parents=True,exist_ok=True)
def deliver(im,p):
 p.parent.mkdir(parents=True,exist_ok=True);im.save(p);im.save(p.with_suffix('.webp'),'WEBP',lossless=True,exact=True,method=4)
 with Image.open(p.with_suffix('.webp')) as test:assert test.convert('RGBA').tobytes()==im.convert('RGBA').tobytes()
 return {'file':p.relative_to(R).as_posix(),'webp':p.with_suffix('.webp').relative_to(R).as_posix(),'size':list(im.size),'alpha_bbox':list(im.getbbox())}
for char in chars:
 m=master[char];path=R/m['output'];base=Image.open(path).convert('RGBA');bbox=base.getchannel('A').getbbox();x0,y0,x1,y1=bbox
 # Common feet/root convention is separate from dialogue crop; never burn in a desk.
 actors.append({'character':char,'master_source':m['source'],'master_hd':m['output'],'source_sha256':hashlib.sha256((R/m['source']).read_bytes()).hexdigest(),'alpha_bbox_pixels':list(bbox),'foot_anchor_pixels':[(x0+x1)/2,y1],'foot_anchor_uv':[(x0+x1)/2/base.width,y1/base.height],'width_per_height':(x1-x0)/(y1-y0),'billboard':'upright/fullbody with explicit separate contact shadow; engine assigns actual height; never use cutin crop as world actor','runtime_integrated':False})
 box=(max(0,x0-(x1-x0)//12),max(0,y0-50),min(base.width,x1+(x1-x0)//12),min(base.height,y0+int((y1-y0)*.34)))
 if char=='lappy':box=(box[0],box[1],box[2],min(base.height,y0+int((y1-y0)*.72))) # Ears start far above the mascot face.
 face=base.crop(box);canvas=Image.new('RGBA',(1600,1600));face.thumbnail((1490,1490));canvas.alpha_composite(face,((1600-face.width)//2,(1600-face.height)//2));rec=deliver(canvas,O/'portraits'/(char+'.png'));rec.update(id=char+'_profile',kind='profile',source=m['output'],crop=list(box),logical_size=[400,400],output_policy='technical crop/downsample from original4x, transparent pad, no identity edit');out.append(rec)
 tiles=[]
 files=list((R/'art/sprites_derived_v4'/char).glob('*.json'))
 for pose in [f'C{i:02d}' for i in range(2,15)]+['T01','T02','T03','T04']+[f'U{i}' for i in range(1,7)]:
  candidates=[]
  for p in files:
   match=re.fullmatch(re.escape(char+'_'+pose)+r'(?:_r(\d+))?',p.stem)
   if match:candidates.append((int(match[1] or 1),p))
  if not candidates:continue
  p=max(candidates,key=lambda x:x[0])[1];meta=json.loads(p.read_text(encoding='utf8'));hd=R/meta.get('hd_file',f'art/hd_v4/derived/{char}/{p.stem}.png')
  if not hd.exists():raise RuntimeError('Missing HD '+str(hd))
  src=Image.open(hd).convert('RGBA');bounds=src.getbbox();selected.append({'character':char,'pose':pose,'selected_id':p.stem,'source':str(p.relative_to(R)),'hd':hd.relative_to(R).as_posix(),'review':'latest continuity revision; contact/detail sheet must be inspected before scene-specific selection','runtime_integrated':False})
  # Review every selected source as a full silhouette and an actual1:1 HD face region.
  native=Image.open(R/'art/sprites_derived_v4'/char/(p.stem+'.png')).convert('RGBA');small=native.copy();small.thumbnail((230,360));tile=Image.new('RGB',(520,610),'#776e7c');tile.paste(small,((260-small.width)//2,25),small)
  cx=(bounds[0]+bounds[2])//2;fy=bounds[1]+int((bounds[3]-bounds[1])*.115);facecrop=src.crop((max(0,cx-120),max(0,fy-120),cx+120,fy+120));tile.paste(facecrop,(270,45),facecrop);ImageDraw.Draw(tile).text((10,405),p.stem,fill='white');tiles.append(tile)
  if pose not in ['T01','T02','T03','T04']:continue
  # A consistent upper-body strip crops, it does NOT invent a fresh pose or flip handedness.
  bx0,by0,bx1,by1=bounds;crop=(max(0,bx0-48),max(0,by0-40),min(src.width,bx1+48),min(src.height,by0+round((by1-by0)*.58)))
  upper=src.crop(crop);upper.thumbnail((2800,2160));strip=Image.new('RGBA',(5120,2240));position=(5120-upper.width-180,2240-upper.height);strip.alpha_composite(upper,position)
  rec=deliver(strip,O/'cutins'/f'{char}_{pose}.png');rec.update(id=f'{char}_{pose}_cutin',kind='cutin',source=hd.relative_to(R).as_posix(),crop=list(crop),placement=list(position),logical_size=[1280,560],text_safe_rect=[65,65,450,420],role={'T01':'accusation','T02':'counterstatement','T03':'agreement','T04':'under_pressure'}[pose],output_policy='technical crop/pad from complete locally4x source; no redrawing, mirroring or added props');out.append(rec)
 for start in range(0,len(tiles),8):
  sheet=Image.new('RGB',(2080,1220),'#776e7c')
  for i,tile in enumerate(tiles[start:start+8]):sheet.paste(tile,(i%4*520,i//4*610))
  sheet.save(qa/f'{char}_{start//8+1:02d}.jpg',quality=96)
print('Writing delivery manifest',flush=True)
(O/'manifest.json').write_text(json.dumps({'assets':out,'actors':actors,'selected_poses':selected,'counts':{'cutins':sum(x['kind']=='cutin' for x in out),'profiles':sum(x['kind']=='profile' for x in out),'world_actor_masters':len(actors),'selected_existing_poses':len(selected)},'source_policy':'existing one-master-derived built-in art, original4x; these crops are NOT new illustrated poses','source_identity_override':{'chapter3_current_Sora_body':'use Ken physical art/cutins, not Sora original body; see07ledger'},'runtime_integrated':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('CHARACTER_DELIVERY_COMPLETE',len(out),'crops;',len(actors),'actor anchors;',len(selected),'existing selected pose files')
