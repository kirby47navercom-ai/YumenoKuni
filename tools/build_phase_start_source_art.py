"""Compose supplied Korean Panic start at its actual full-screen SFL matrices."""
from pathlib import Path
import runpy,json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];BANK=ROOT/'ui/v3_authorized/phase_start_source';OUT=ROOT/'ui/v4/phase_start_source';OUT.mkdir(parents=True,exist_ok=True)
core=runpy.run_path(str(ROOT/'tools/build_trial_input_source_art.py'));g=core['comp'].__globals__
layout=json.loads((BANK/'layout.json').read_text(encoding='utf-8'));manifest=json.loads((BANK/'manifest.json').read_text(encoding='utf-8'))
g.update(L=layout,M=manifest,OUT=OUT,S=1,SIZE=(1280,720),records={});original_texture=core['texture']
g['texture']=lambda file,resource:original_texture(file,'additive_DXT1.png' if 'DXT1' in resource else resource)

def main():
 source=layout['t_panic_start_US'];sequence=source['frames'];indices=list(range(len(sequence)))
 frames=[core['comp'](sequence[index])for index in indices]
 frames[0].save(OUT/'panic_start.webp',save_all=True,append_images=frames[1:],duration=[round((i+1)*1600/len(frames))-round(i*1600/len(frames))for i in range(len(frames))],loop=0,lossless=True,method=4)
 encoded=Image.open(OUT/'panic_start.webp');encoded_ms=0
 for at in range(encoded.n_frames):encoded.seek(at);encoded.load();encoded_ms+=encoded.info['duration']
 for i,name in [(0,'first'),(len(frames)//2,'middle')]:frames[i].save(OUT/('panic_'+name+'.png'))
 frames[min(90,len(frames)-1)].save(OUT/'panic_settled.png')
 m={'encodedFrames':encoded.n_frames,'durationMS':encoded_ms,'identicalSourceFramesMerged':len(frames)-encoded.n_frames,'sourceManifest':'ui/v3_authorized/phase_start_source/manifest.json','carrier':'t_panic_start_US (supplied Korean t_panic_start_JP.spc)','sourceLabels':source['labels'],'sourceFrames':indices,'representativeFrame':90,'viewport':[0,0,1280,720],'panicAsset':'Assets/Art/ui/start_panic.webp','existingVisibleSeconds':1.6,'sampleFrameMS':'12/13ms distributed over1600ms','loop':0,'scope':'Exact source bitmap/affine/alpha/RGB plus black-matte-to-alpha adapter for additive DXT1. All130 source sequence frames retained and retimed to the existing own1.6-second StartBand window; original timing is not claimed. No camera, input, judgment or CPP timing changes. Native cache animation restart semantics remain a runtime verification item.','files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}for p in OUT.glob('*')if p.suffix in ['.png','.webp']}}
 (OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');print('PHASE_START_SOURCE',m['files'])
if __name__=='__main__':main()
