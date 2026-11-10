"""Publish checked Blender/PBR source ownership; shipping pointer is a later gate."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/facility_forms_v3';B=R/'art/space_v4/rebuild_v1';W=R/'Game/Saved/facility-form-20261104'
load=lambda p:json.loads(p.read_text(encoding='utf8'));save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=load(O/'manifest.json');proof=load(O/'geometry-verification.json');assert proof['ok']and proof['sourceBlendSHA256']==sha(O/'park-form-source.blend')and proof['compiledSHA256']==m['asset']['sha256'];assert m['allFacadesRebuilt']and len(m['rows'])==30
a=m['asset'];assert sha(R/a['file'])==a['sha256']and sha(R/a['source'])==a['sourceSHA256']and a['bytes']<64*1024*1024
p=B/'manifest.json';old=load(p)
if not(W/'bank-before-v3.json').exists():save(W/'bank-before-v3.json',old)
old['assets']=[a if r['runtime']==a['runtime']else r for r in old['assets']];old.update(facilityArchitectureVersion=3,facilityArchitectureSource='art/space_v4/facility_forms_v3/manifest.json',runtimeVerified=False);save(p,old)
p=B/'exterior-assembly.json';ex=load(p);ex['assets']=[m['rawAsset']if r['runtime']==a['runtime']else r for r in ex['assets']];ex.update(facilityArchitectureVersion=3,facilityArchitectureSource='art/space_v4/facility_forms_v3/manifest.json');save(p,ex)
print('PURPOSE_FORM_SOURCE_OWNER_PUBLISHED',len(m['rows']),'shipping pointer unchanged')
