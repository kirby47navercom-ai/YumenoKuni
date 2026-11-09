"""Retain the latest shipped cooked story; adapt only declared geography text."""
import json,sys
from pathlib import Path
from v4_park_story import adapt
R=Path(__file__).resolve().parents[1];W=R/'Game/Saved/park-levels-20261104';B=json.loads((W/'baseline-build.json').read_text(encoding='utf8'));F=Path(B['flat']);rows=[]
for k in range(128):
    rel=f'Assets/Data/v4_story/nodes/{k}.json';p=W/'baseline-content'/rel
    if not p.exists():p=F/'Content'/rel
    data=json.loads(p.read_text(encoding='utf8'));before=json.dumps(data,ensure_ascii=False);changed=[]
    for n in data['nodes'].values():
        old=json.dumps(n,ensure_ascii=False);adapt(n)
        if old!=json.dumps(n,ensure_ascii=False):changed.append(n['id'])
    if not changed:continue
    dest=W/'story-candidate'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8');rows.append({'runtime':rel,'file':str(dest),'nodes':changed})
(W/'story-candidate.json').write_text(json.dumps({'rows':rows,'stableNodeIDs':True,'latestShippedStoryPreserved':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('GEOGRAPHY_SHARDS',len(rows),'NODES',sum(len(r['nodes'])for r in rows),flush=True)
