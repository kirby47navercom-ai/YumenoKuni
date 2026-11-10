"""Reuse project GLB geometry validation and additionally verify real animation channels."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
source=(R/'tools/check_v4_spaces.py').read_text(encoding='utf8')
prefix=source[:source.index('\ncontracts=[]')]
for name in ['minigames_v4','interactions_v4','inspection_props_v4']:
 out=R/'art/space_v4'/name;m=json.loads((out/'manifest.json').read_text(encoding='utf8'))
 # Run the identical accessor/buffer/finite-position/index/tree checks on this kit.
 adapted=prefix.replace("OUT=ROOT/os.environ.get('V4_SPACE_OUT','art/space_v4')",f"OUT=ROOT/'art/space_v4/{name}'")
 adapted=adapted.replace("manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf8'))","manifest={'models':json.loads((OUT/'manifest.json').read_text(encoding='utf8'))['assets'],'spaces':[]}")
 env={'__file__':str(R/'tools/check_v4_spaces.py')};exec(compile(adapted,'kit_geometry_validator','exec'),env)
 report=env['reports'];np=env['np'];struct=env['struct'];animations=[]
 for rec in m['assets']:
  data=(R/rec['file']).read_bytes();n=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+n]);off=20+n;binary=data[off+8:]
  def values(idx):
   a=doc['accessors'][idx];v=doc['bufferViews'][a['bufferView']];dtype=np.dtype(env['types'][a['componentType']]);width=env['widths'][a['type']];stride=v.get('byteStride',dtype.itemsize*width);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
   ar=np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=offset,strides=(stride,dtype.itemsize));assert np.isfinite(ar).all();return ar
  count=0;changed=0
  for animation in doc.get('animations',[]):
   assert animation['channels']
   for c in animation['channels']:
    assert 0<=c['target']['node']<len(doc['nodes']);s=animation['samplers'][c['sampler']];times=values(s['input']).flatten();output=values(s['output']);assert (np.diff(times)>0).all();assert len(times)>=2
    if s.get('interpolation','LINEAR')!='CUBICSPLINE':assert len(times)==len(output)
    count+=1
    if float(np.max(np.ptp(output,axis=0)))>1e-5:changed+=1
  expected=name=='interactions_v4' or rec['id']=='drive_taxi'
  if expected:assert count>0 and changed>0,(rec['id'],'animation was not exported')
  animations.append({'id':rec['id'],'clips':len(doc.get('animations',[])),'channels':count,'actually_changing_channels':changed,'expected_motion':expected})
 p=out/'qa.json';p.write_text(json.dumps({'status':'PASS:GLB geometry and real animation-channel validation','assets':len(report),'geometry':report,'animations':animations,'runtime_integration':'NOT RUN','visual_review':'see completion visual review, separate from binary validation'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(name,'PASS',len(report),'GLBs;',sum(x['actually_changing_channels'] for x in animations),'changing channels')
