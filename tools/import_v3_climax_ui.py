"""Authorized read-only Climax UI import. Never imports original manga/story art."""
from pathlib import Path
import sys,json,hashlib,math,re
sys.path.insert(0,str(Path(__file__).resolve().parent/'re'))
import cpk,spc,srd,sfl
from build_v3_armament_layout import matrix,mul,state,I
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('C:/Program Files (x86)/Steam/steamapps/common/Danganronpa V3 Killing Harmony/data/win')
CACHE=Path('C:/Users/kirby/Downloads/v3_re/native/climax-ui-20261106')
OUT=ROOT/'ui/v4/climax_original_20261106'
SELECT={
 'partition_data_win.cpk':['flash/climax/'+name+'.spc'for name in ['climax_anime_page','climax_bg_01','climax_bg_02','climax_bg_03','climax_bg_04','climax_bg_05','climax_bg_06','climax_cursor','climax_cutin_ng','climax_cutin_ok','climax_hint','climax_hukidasi','climax_koma_base','climax_status_ht10','climax_status_ht5','climax_status_ht7','climax_tama']],
 'partition_data_win_us.cpk':['flash/climax/'+name+'_US.spc'for name in ['climax_koma_act','climax_koma_choise','climax_page_base','climax_page','climax_time','climax_title']],
}
def sha(data):return hashlib.sha256(data).hexdigest()
def write_json(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf8')
def original_story_resource(container,resource):
 return container.startswith('climax_bg_')or(container=='climax_koma_base'and resource=='yogosi_00.png')or(container in['climax_koma_act_US','climax_koma_choise_US']and re.fullmatch(r'koma_\d+_\d+\.png',resource))
def import_bank():
 OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
 textures=[];containers=[];timelines={};errors=[];placeholders=[]
 for archive,names in SELECT.items():
  cache=CACHE/Path(archive).stem
  missing=[n for n in names if not(cache/n).exists()]
  if missing:cpk.CPK(SOURCE/archive).extract(cache,exact=missing)
  for name in names:
   path=cache/name;raw=path.read_bytes();members={e['name']:spc.payload(raw,e)for e in spc.entries(raw)}
   folder=OUT/path.stem;folder.mkdir(exist_ok=True)
   containers.append(dict(name=path.stem,archive=archive,member=name,sha256=sha(raw),bytes=len(raw),cache=str(path),sourceStat=dict(size=(SOURCE/archive).stat().st_size,mtimeNs=(SOURCE/archive).stat().st_mtime_ns)))
   for member,data in members.items():
    if member.endswith('.sfl'):
     parsed=sfl.parse_sfl(data);dest=folder/'animation.json';write_json(dest,parsed);timelines[path.stem]=dest.relative_to(ROOT).as_posix()
    elif member.endswith('.srd'):
     stem=member[:-4];companions={ext:members[stem+'.'+ext]for ext in ['srdi','srdv']if stem+'.'+ext in members}
     parsed=srd.parse_srd(data,companions);write_json(CACHE/(path.stem+'-'+stem+'-texture-metadata.json'),parsed)
     image_index=-1
     for block in srd.walk(parsed['blocks']):
      if block['type']!='$TXR'or'decoded'not in block:continue
      image_index+=1;info=next((c.get('decoded')for c in block['children']if c['type']=='$RSI'),None)
      if not info:continue
      resource=info['strings'][0]
      try:
       payload=srd.external_bytes(srd.texture_resource(block['decoded'],info),companions);im=srd.texture_image(block['decoded'],payload)
      except ValueError as error:errors.append(dict(container=path.stem,resource=resource,error=str(error),metadata=block['decoded'],optionalTitleOnly=path.stem=='climax_title_US'));continue
      filename=f'{image_index:03d}_'+re.sub(r'[^A-Za-z0-9_.-]','_',resource)+'.png'
      if original_story_resource(path.stem,resource):
       dest=CACHE/'reference-only'/path.stem/filename;dest.parent.mkdir(parents=True,exist_ok=True)
       previous=folder/filename
       if previous.exists():
        assert not dest.exists();previous.rename(dest)
       else:im.save(dest)
       placeholders.append(dict(container=path.stem,imageIndex=image_index,resource=resource,file='',size=list(im.size),ownMangaRequired=True,externalReferenceOnly=str(dest)))
       continue
      dest=folder/filename;im.save(dest)
      textures.append(dict(container=path.stem,imageIndex=image_index,containerSHA256=sha(raw),member=member,resource=resource,file=dest.relative_to(ROOT).as_posix(),sha256=sha(dest.read_bytes()),pixelSHA256=sha(im.convert('RGBA').tobytes()),size=list(im.size),format=block['decoded'].get('format'),unchangedDecodedPixels=True))
 manifest=dict(schema='v3-climax-original-ui-bank-v1',authorization='User explicitly overrides new original asset extraction ban for Climax reconstruction on 2026-11-06. Installation reads only, no game launch/process probe/save or settings changes.',containers=containers,textures=textures,ownArtPlaceholders=placeholders,timelines=timelines,errors=errors,originalMangaInProject=False,originalStoryImagesInProject=False,executedOriginalGame=False,modifiedInstallation=False)
 write_json(OUT/'manifest.json',manifest)
 assert all(e['container']=='climax_title_US'and e['resource']=='climax_US.png'and e['error']=='unverified texture layout flag'for e in errors),errors
 return manifest
def layout(inv):
 result={}
 for name,file in inv['timelines'].items():
  parsed=json.loads((ROOT/file).read_text(encoding='utf8'));tables={t['id']:{e['id']:e for e in t['entries']}for t in parsed['tables']};images={r['imageIndex']:r for r in inv['textures']+inv.get('ownArtPlaceholders',[])if r['container']==name}
  if 6 not in tables or 0 not in tables[6]:continue
  seq=tables[6][0].get('sequences',[]);labels={q['name']:i for i,q in enumerate(seq)if q.get('name')}
  def leaves(ref,age,affine=I,alpha=1,path='',depth=0,rgbmul=(1,1,1),rgbadd=(0,0,0)):
   if depth>20:raise ValueError('SFL reference cycle '+name)
   table,idx=ref['table'],ref['entry'];entry=tables[table][idx]
   if table==3:
    out=[]
    for r in entry.get('rect_records',[]):
     image=r['image_id'];solid=image==4294967295
     if solid:
      if r.get('unknown_hex')not in ['80000000','80ffffff']:continue
      texture=dict(file='',resource='__solid_black'if r['unknown_hex']=='80000000'else'__solid_white',size=[8,8])
     else:
      if image not in images:continue
      texture=images[image]
     p=r['four_ints'];a=mul(affine,[1,0,0,1,p[0],p[2]]);w=p[1]-p[0];h=p[3]-p[2]
     sx=math.hypot(a[0],a[1]);sy=math.hypot(a[2],a[3]);rotation=math.degrees(math.atan2(a[1],a[0]));cx=a[4]+a[0]*w/2+a[2]*h/2;cy=a[5]+a[1]*w/2+a[3]*h/2
     quad=[[a[4],a[5]],[a[4]+a[0]*w,a[5]+a[1]*w],[a[4]+a[0]*w+a[2]*h,a[5]+a[1]*w+a[3]*h],[a[4]+a[2]*h,a[5]+a[3]*h]]
     out.append(dict(path=path,texture=texture['file'],resource=texture['resource'],imageIndex=image,rect=[(cx-w*sx/2)*2/3,(cy-h*sy/2)*2/3,w*sx*2/3,h*sy*2/3],rotation=rotation,opacity=alpha,sourceAffine=a,sourceQuad=quad,sourceRect=p,sourceRectRecord=r,colorMultiply=list(rgbmul),colorAdd=list(rgbadd)))
    return out
   if table not in[5,6]:return[]
   sequences=entry.get('sequences',[])
   if not sequences:return[]
   stops=[i for i,q in enumerate(sequences)if any(a.get('name')=='Stop'for op in q['operations']for a in op.get('decoded',{}).get('actions',[]))]
   frame=min(age,stops[0])if stops else age%len(sequences);return layer_state(state(sequences,min(frame,len(sequences)-1)),frame,affine,alpha,path,depth,rgbmul,rgbadd)
  def layer_state(display,frame,affine,alpha,path,depth,rgbmul,rgbadd):
   out=[];masks=[]
   for at,o in sorted(display.items()):
    masks=[m for m in masks if at<=m[0]]
    if'character_reference'not in o:continue
    a=mul(affine,matrix(o.get('matrix',{})));ct=o.get('color_transform',{});cm=ct.get('multiply_rgba',[1]*4);ca=ct.get('add_rgba',[0]*4)
    rm=[rgbmul[i]*cm[i]for i in range(3)];ra=[rgbadd[i]+rgbmul[i]*ca[i]for i in range(3)]
    child=leaves(o['character_reference'],max(0,frame-o['born']),a,alpha*cm[3],path+'/'+o.get('instance_name',str(at)),depth+1,rm,ra)
    if o.get('clip_depth'):masks.append((o['clip_depth'],child));continue
    for row in child:
     if masks:row['clips']=row.get('clips',[])+[m[1]for m in masks]
    out+=child
   return out
  frames=[layer_state(state(seq,at),at,I,1,'',0,(1,1,1),(0,0,0))for at in range(len(seq))]
  symbols={}
  for idx,entry in tables.get(5,{}).items():
   sequences=entry.get('sequences',[])
   if not sequences:continue
   labels5={q['name']:i for i,q in enumerate(sequences)if q.get('name')}
   # Independent symbols preserve numbered digits, stock marks and used/locked variants.
   symbols[str(idx)]=dict(labels=labels5,frames=[layer_state(state(sequences,at),at,I,1,'',0,(1,1,1),(0,0,0))for at in range(len(sequences))])
  result[name]=dict(sourceSHA256=parsed['sha256'],labels=labels,frames=frames,states={k:frames[v]for k,v in labels.items()},symbols=symbols,coordinateContract='sourceAffine/sourceQuad use original 1920x1080 SFL coordinate space. rect is a 2/3 flat projection convenience; separate data_3d transform/projection is not applied. Preserve source affine for exact fitting; do not claim final 3D projection from rect alone.')
 write_json(OUT/'layout.json',result)
 return result
if __name__=='__main__':
 inv=import_bank();resolved=layout(inv)
 print(json.dumps(dict(containers=len(inv['containers']),textures=len(inv['textures']),timelines=len(resolved),errors=len(inv['errors']),bank=str(OUT)),ensure_ascii=False))
