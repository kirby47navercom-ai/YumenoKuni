"""Explicit isolated rendering fixtures, never passed off as normal campaign saves."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'Game/Saved/trial-expansion-fixtures-20261101'
BASE = ROOT/'Game/Saved/v4-story-extension-1793461693288/UserData/savegames.json'
source = json.loads(BASE.read_text(encoding='utf-8'))
key = next(k for k in source['items'] if 'yumeno-progress-v4.project.' in k)
base = json.loads(source['items'][key])
checks = json.loads((ROOT/'Game/Saved/trial-expansion-20261101.json').read_text(encoding='utf-8'))
assert checks['ok']
OUT.mkdir(parents=True, exist_ok=True)
fixtures = []
for chapter, proof in checks['chapters'].items():
    graph = json.loads((ROOT/f'data/v4_story/chapters/{chapter}.json').read_text(encoding='utf-8'))
    prefix = proof['newSource']
    nodes = graph['nodes']
    added = {k for k,n in nodes.items() if n.get('source',{}).get('file','').startswith(prefix+'_')}
    added |= {k for k,n in nodes.items() if n['type']=='branch' and n.get('cases')
              and all(c['to'] in added for c in n['cases'])}
    entry = proof['resume']['entry']
    assert entry in added
    exits = {nodes[k]['next'] for k in added if 'next' in nodes[k] and nodes[k]['next'] not in added}
    assert len(exits) == 1
    returned = exits.pop()
    assert returned in nodes
    head = copy.deepcopy(base)
    head.update(chapter=chapter, node=entry, flags={'T2-C01':'A'} if chapter == '2' else {},
                stack=[], read=[], log=[], documents={}, world={}, worldId='plaza', trialResultOpen=False,
                evidence=graph.get('evidenceCatalog',{}), trialChoice={}, presentation={},
                progressFormat='parts-v1', snapshot='20261101-'+chapter, readParts=0, logParts=0)
    head.pop('read');head.pop('log');head.pop('taskResume',None);head.pop('machine',None)
    task = next(n for n in nodes.values() if n['type'] == 'task' and n.get('trialDead') is not None)
    head['court'] = {'active':True,'dead':task['trialDead'],'maxHearts':5,'hearts':5,'hp':10000,'focus':100,
                     'retries':0,'correct':0,'reviveUsed':False,'sdGuardUsed':False,'missGuardUsed':False}
    storage = copy.deepcopy(source)
    # Keep genuine engine options/profile entries; discard obsolete progress parts in this fixture only.
    storage['items'] = {k:v for k,v in storage['items'].items() if 'yumeno-v4-' not in k and k != key}
    storage['items'][key] = json.dumps(head, ensure_ascii=False, separators=(',',':'))
    file = OUT/f'chapter-{chapter}.json'
    file.write_text(json.dumps(storage, ensure_ascii=False), encoding='utf-8')
    fixtures.append({'chapter':chapter,'sourcePrefix':prefix,'entry':entry,'return':returned,
                     'file':file.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                     'earlierChoiceSeeded':head['flags'],'fixture':True,'normalRoute':False})
report = {'fixture':True,'normalRoute':False,'base':BASE.relative_to(ROOT).as_posix(),
          'scope':'Own isolated native rendering/reading-return tests. Entry/earlier choice/evidence catalogue and court state are seeded explicitly; no normal play, acquired-evidence, score or duration claim.',
          'fixtures':fixtures}
(OUT/'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'fixtures':len(fixtures),'normalRoute':False,'output':str(OUT)},ensure_ascii=False))
