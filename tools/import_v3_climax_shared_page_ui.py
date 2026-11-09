"""Import generic page arrows and a non-narrative question crop only."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image,ImageDraw,ImageChops
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools/re'))
import cpk,spc,srd
CACHE=Path('C:/Users/kirby/Downloads/v3_re/native/climax-ui-20261106/question-reference')
OUT=ROOT/'ui/v4/climax_original_20261106/shared_page';OUT.mkdir(parents=True,exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def build():
 names=['flash/climax/climax_page_01.spc','flash/climax/climax_01_00.spc']
 archive=Path('C:/Program Files (x86)/Steam/steamapps/common/Danganronpa V3 Killing Harmony/data/win/partition_data_win.cpk')
 missing=[n for n in names if not(CACHE/n).exists()]
 if missing:cpk.CPK(archive).extract(CACHE,exact=missing)
 records={}
 for name in names:
  raw=(CACHE/name).read_bytes();members={e['name']:spc.payload(raw,e)for e in spc.entries(raw)}
  for member,data in members.items():
   if not member.endswith('.srd'):continue
   stem=member[:-4];companions={ext:members[stem+'.'+ext]for ext in ['srdi','srdv']if stem+'.'+ext in members}
   for b in srd.walk(srd.parse_srd(data,companions)['blocks']):
    if b['type']!='$TXR'or'decoded'not in b:continue
    info=next((c.get('decoded')for c in b['children']if c['type']=='$RSI'),None)
    if not info:continue
    resource=info['strings'][0]
    # All answer snippets, candidate illustrations, and whole manga pages stay out.
    allowed=['act_DXT1.png','mask_00.png','yazirusi_00.png','006_sys_l1.png','009_sys_r1.png']if 'climax_page_01'in name else['page_01_01_ef_DXT1.png','page_DXT1.png']
    if resource not in allowed:continue
    im=srd.texture_image(b['decoded'],srd.external_bytes(srd.texture_resource(b['decoded'],info),companions)).convert('RGBA')
    extra={}
    if resource=='page_DXT1.png':
     # Positively inspected non-story pink question quadrilateral within sourcepage.
     # Crop/mask only its interior; no original characters/panels enter the bank.
     polygon=[[546,225],[982,307],[982,555],[490,555]]
     mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon([tuple(p)for p in polygon],fill=255)
     im.putalpha(mask);clean=Image.new('RGBA',im.size);clean.alpha_composite(im);im=clean.crop((488,222,984,557));key='questionPink'
     extra=dict(sourceCrop=[488,222,496,335],sourcePolygon=polygon,derivative='Only generic pink question quadrilateral, masked from sourcepage; all narrative panels removed.')
    else:key={'act_DXT1.png':'pageActiveGlow','mask_00.png':'pageMask','yazirusi_00.png':'pageArrow','006_sys_l1.png':'buttonL1','009_sys_r1.png':'buttonR1','page_01_01_ef_DXT1.png':'questionGlow'}[resource]
    dest=OUT/(key+'.png');im.save(dest,optimize=True)
    records[key]=dict(texture=dest.relative_to(ROOT).as_posix(),size=list(im.size),sha256=sha(dest.read_bytes()),sourceContainer=name,sourceSHA256=sha(raw),sourceResource=resource,format=b['decoded']['format'],**extra)
    if b['decoded']['format']=='DXT1'and resource!='page_DXT1.png':
     glow=im.copy();r,g,blue,a=glow.split();glow.putalpha(ImageChops.multiply(a,ImageChops.lighter(ImageChops.lighter(r,g),blue)))
     pdest=OUT/(key+'Alpha.png');glow.save(pdest,optimize=True)
     records[key]['presentationTexture']=pdest.relative_to(ROOT).as_posix();records[key]['presentationDerivative']='Additive-black RGB converted to luminance alpha; raw texture unchanged.'
 (OUT/'manifest.json').write_text(json.dumps(dict(schema='v3-climax-shared-page-ui-v1',originalNarrativeArtInBank=False,records=records),ensure_ascii=False,separators=(',',':')),encoding='utf8')
 corefile=ROOT/'ui/v4/climax_original_20261106/core.json';core=json.loads(corefile.read_text(encoding='utf8'));core['sharedPageUI']=records;corefile.write_text(json.dumps(core,ensure_ascii=False,separators=(',',':')),encoding='utf8')
 print(json.dumps({k:v['texture']for k,v in records.items()}))
if __name__=='__main__':build()
