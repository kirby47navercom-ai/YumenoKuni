"""Publish the checked architecture candidate into the existing 61-model bank."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'art/space_v4/facility_architecture_v2';B=R/'art/space_v4/rebuild_v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((O/'manifest.json').read_text());proof=json.loads((O/'roof-closure-proof.json').read_text());assert m['allFacadesRebuilt']and len(m['rows'])==30 and proof['ok']and len(proof['buildings'])==30
assert proof['sourceBlendSHA256']==sha(B/'sources/park-rebuilt.blend');a=m['asset'];assert a['sha256']==sha(R/a['file'])and a['sourceSHA256']==sha(R/a['source'])
assert len({r['id']for r in m['rows']})==30 and all(len(r['features'])>=1 for r in m['rows'])
old=json.loads((B/'manifest.json').read_text());(O/'previous-bank-manifest.json').write_text(json.dumps(old,indent=2)+'\n')
old['assets']=[a if r['runtime']==a['runtime']else r for r in old['assets']];old['facilityArchitectureVersion']=2;old['facilityArchitectureSource']='art/space_v4/facility_architecture_v2/manifest.json';old['runtimeVerified']=False
(B/'manifest.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
file=B/'exterior-assembly.json';ex=json.loads(file.read_text());ex['assets']=[m['rawAsset']if r['runtime']==a['runtime']else r for r in ex['assets']];ex['facilityArchitectureVersion']=2;file.write_text(json.dumps(ex,indent=2)+'\n')
print('PURPOSE_ARCHITECTURE_PUBLISHED',30,a['triangles'],a['materialPrimitives'])
