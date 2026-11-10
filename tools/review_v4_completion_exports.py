"""Verify newly authored vector/motion/audio files without claiming runtime acceptance."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,wave
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];results=[]
for folder in ['ui/v4/completion_hd','ui/v4/documents_hd','ui/v4/comic_diagrams_hd','ui/v4/motion_hd','ui/v4/reconstruction_diagrams_hd','ui/v4/brand_hd']:
 out=R/folder;m=json.loads((out/'manifest.json').read_text(encoding='utf8'))
 for a in m['assets']:
  frames=a.get('frames')
  if frames is None:frames=[{'svg':a['source'],'png':str(Path(a['file']).with_suffix('.png')),'webp':a['file'],'size':a['texture_size']}]
  areas=[]
  for f in frames:
   svg=R/f['svg'];xml=ET.fromstring(svg.read_text(encoding='utf8'));sz=(int(xml.attrib['width']),int(xml.attrib['height']));assert sz==tuple(f['size'])
   with Image.open(R/f['png']) as p,Image.open(R/f['webp']) as q:
    assert p.size==q.size==sz;px=np.asarray(p.convert('RGBA'));assert px.tobytes()==q.convert('RGBA').tobytes();areas.append(float((px[:,:,3]>8).mean()))
    if 'center_clear_rect_normalized' in a:
     l,t,r,b=a['center_clear_rect_normalized'];region=px[round(t*sz[1]):round(b*sz[1]),round(l*sz[0]):round(r*sz[0]),3];assert region.max()==0,a['id']
   if a.get('text_rect'):
    x,y,w,h=a['text_rect'];lw,lh=a['logical_size'];assert min(x,y,w,h)>=0 and x+w<=lw and y+h<=lh
  if a.get('monotonic_coverage'):
   diff=np.diff(areas);assert (diff>=-1e-7).all() if 'uncover' not in a['id'] else (diff<=1e-7).all();assert min(areas)==0 and max(areas)==1
  if a.get('loop'):
   assert (R/frames[0]['png']).read_bytes()==(R/frames[-1]['png']).read_bytes(),a['id']
  results.append({'id':a['id'],'folder':folder,'frames':len(frames),'RGBA_equality':'PASS','vector_size':'PASS','motion_alpha_coverage':areas if len(areas)>1 else None,'runtime_integrated':False})
extra=R/'ui/v4/documents_hd/report17_matching_fragment.json';a=json.loads(extra.read_text(encoding='utf8'))
with Image.open(R/a['file']) as q,Image.open((R/a['file']).with_suffix('.png')) as p:assert p.convert('RGBA').tobytes()==q.convert('RGBA').tobytes();assert list(p.size)==a['texture_size']
audio=json.loads((R/'audio/v4_original/manifest.json').read_text(encoding='utf8'))
for a in audio['assets']:
 p=R/a['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'];assert (R/a['ogg']).stat().st_size>0
 with wave.open(str(p),'rb') as w:
  assert w.getframerate()==48000 and w.getnchannels()==2;raw=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
  assert np.max(abs(raw))<.71 and len(raw)==a['samples']*2
report={'status':'PASS','vector_or_motion_assets':len(results)+1,'individual_vector_frames':sum(x['frames'] for x in results)+1,'audio_cues':len(audio['assets']),'checks':results,'paper_matching_detail':'shared complementary mask/identical glyph coordinates, no generated pseudo-text evidence','runtime_or_listening_claim':'NOT RUN; numeric audio check is not a listening test'}
(R/'art/v4_production/completion/technical_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('PASS',len(results)+1,'vector/motion assets;',sum(x['frames'] for x in results)+1,'actual frames;',len(audio['assets']),'audio cues')
