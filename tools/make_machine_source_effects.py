"""Adapt original additive-only effect rasters to the native alpha UI compositor."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'ui/v4/machine_source';OUT.mkdir(exist_ok=True);records={}
for bank,families in [('all_general',['m_machine_US','m_lucky_US']),('machine_result_source',['m_get_US'])]:
 data=json.loads((ROOT/'ui/v3_authorized'/bank/'layout.json').read_text(encoding='utf-8'))
 for family in families:
  for rows in data[family]['states'].values():
   for row in rows:
    source=row.get('texture');resource=row.get('resource','')
    if not source or 'DXT1' not in resource or source in records:continue
    raw=(ROOT/source).read_bytes();arr=np.array(Image.open(ROOT/source).convert('RGBA'));rgb=arr[:,:,:3].astype('float32');alpha=rgb.max(axis=2);denom=np.maximum(alpha,1);arr[:,:,:3]=np.minimum(rgb*255/denom[:,:,None],255).astype('uint8');arr[:,:,3]=alpha.astype('uint8');file=family+'_'+resource+'.png';Image.fromarray(arr).save(OUT/file)
    records[source]={'file':(OUT/file).relative_to(ROOT).as_posix(),'sourceSHA256':hashlib.sha256(raw).hexdigest(),'conversion':'RGB normalized by maxRGB, alpha=maxRGB for retained DXT1 additive effect; exact original GPU additive compositing unclaimed.'}
(OUT/'manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8');print('MACHINE_EFFECT_ADAPTERS',len(records))
