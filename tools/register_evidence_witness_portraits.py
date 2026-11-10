"""Explicit testimony associations; native SVG layout of unchanged own portraits.

No image processing or new bitmap. The SVG is a UI carrier using existing
approved portrait bytes; it does not depict the witnessed historical event.
"""
import base64,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROWS={
 'v4:E1-10':['nana'],
 'v4:E2-05':['sora','nana'],
 'v4:E2-07':['rei','riku'],
 'v4:E2-09':['mio','yuu'],
 'v4:3:knowledge:first-attack':['mio','rin'],
 'v4:3:knowledge:restraint-awake':['rin','rei'],
 'v4:3:knowledge:nana-contact':['nana'],
 'v4:3:knowledge:continuous-awake':['mio','rin','rei'],
 'v4:3:knowledge:current-nonattempt':['mio','rin'],
 'v4:4:knowledge:injury-order':['sho'],
 'v4:4:knowledge:last-alive':['mio','nana','akari'],
 'v4:4:knowledge:late-company':['rin'],
 'v4:4:knowledge:entry-observers':['mio','nana','akari','satsuki'],
 'v4:4:knowledge:rei-close':['rei'],
 'v4:4:knowledge:rear-answer':['rei'],
 'v4:4:knowledge:waiting-request':['haruka'],
 'v4:E5-20':['mio'],
 'v4:E5-13':['rin','sho','nana'],
 'v4:E5-19':['mio','satsuki'],
 'v4:E5-06':['akari'],
 'v4:E5-15':['sho'],
 'v4:E5-07':['rin','sho','nana'],
 'v4:E5-12':['lappy'],
}
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 out=ROOT/'ui/v4/evidence_witnesses_20261104';out.mkdir(exist_ok=True)
 catalogue=json.loads((ROOT/'art/character_delivery_v4/manifest.json').read_text(encoding='utf8'))
 profiles={r['id'].removesuffix('_profile'):r for r in catalogue['assets'] if r.get('kind')=='profile'}
 vp=ROOT/'tools/v4_evidence_illustration_views.json';views=json.loads(vp.read_text(encoding='utf8'))
 viewmap={r['id']:r for r in views['views']};receipts=[]
 for who in sorted({n for names in ROWS.values() for n in names}):
  row=profiles[who];source=ROOT/row['file'];data=source.read_bytes();x0,y0,x1,y1=row['alpha_bbox']
  # Presentation crop only, with the original raster embedded unchanged.
  height=(y1-y0)*(.95 if who=='lappy' else .72);scale=320/height
  px=320-(x0+x1)*.5*scale;py=20-y0*scale
  image='ui/v4/evidence_witnesses_20261104/'+who+'.svg'
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="640" height="360" viewBox="0 0 640 360"><defs><radialGradient id="bg"><stop stop-color="#fff"/><stop offset=".7" stop-color="#f5f5f5"/><stop offset="1" stop-color="#b6b6b6"/></radialGradient></defs><rect width="640" height="360" fill="url(#bg)"/><image x="{px:.5f}" y="{py:.5f}" width="{1600*scale:.5f}" height="{1600*scale:.5f}" xlink:href="data:image/webp;base64,{base64.b64encode(data).decode()}"/></svg>'
  (ROOT/image).write_text(svg,encoding='utf8');ident='testimony_portrait_'+who
  viewmap[ident]={'id':ident,'file':image,'reviewed':True,'scope':'Testimony subject identity only, not a scene photograph, proof of every event or new identification. Existing approved portrait, unchanged raster bytes in native SVG UI layout.'}
  receipts.append({'person':who,'portrait':row['file'],'portraitSha256':sha(data),'image':image,'uiSha256':sha(svg.encode()),'rasterBytesChanged':False})
 evidence={}
 for p in (ROOT/'data/v4_story/chapters').glob('*.json'):evidence.update(json.loads(p.read_text(encoding='utf-8-sig')).get('evidenceCatalog',{}))
 sp=ROOT/'tools/v4_evidence_art_semantic.json';semantic=json.loads(sp.read_text(encoding='utf8'))
 for evidenceId,names in ROWS.items():
  ev=evidence[evidenceId];digest=sha((ev['name']+'\n'+ev['text']).encode())
  entries=[{'id':'testimony_portrait_'+n,'sha256':sha((ROOT/viewmap['testimony_portrait_'+n]['file']).read_bytes())} for n in names]
  old=next((b for b in semantic['bindings'] if b['evidenceId']==evidenceId),None)
  if old:
   assert old['evidenceTextSha256']==digest and old['views']==entries;continue
  semantic['bindings'].append({'evidenceId':evidenceId,'evidenceTextSha256':digest,'views':entries,'reviewBasis':'Exact evidence text reviewed for these individual testimony sources. Portrait indicates the person whose statement/observation is being considered; separate pages retain separate observers and scope. No omniscient scene reconstruction.','pixelReview':'2026-11-04 approved own portrait contact review; native UI crop pending runtime review.','grantPolicy':'Existing owned evidence only. No grant, answer, timeline or dialogue changes.'})
 views['views']=list(viewmap.values());vp.write_text(json.dumps(views,ensure_ascii=False,indent=2)+'\n',encoding='utf8');sp.write_text(json.dumps(semantic,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (out/'manifest.json').write_text(json.dumps({'reference':'https://danganronpa.fandom.com/wiki/Truth_Bullets/Danganronpa_V3?file=DR_V3_Chapter_1_-_Truth_Bullet_%2810%29.png','referenceDirectViewed':True,'originalGameExecuted':False,'policy':'Original witness portrait convention used only for explicit testimony subject bindings. Physical objects, documents and abstract rules are not auto-filled with portraits.','rows':receipts,'bindings':ROWS},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'explicitTestimonyBindings':len(ROWS),'portraits':len(receipts),'rasterPixelsChanged':False,'storyFactsChanged':False}))
if __name__=='__main__':main()
