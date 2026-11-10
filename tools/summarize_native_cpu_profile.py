import json,collections,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text(encoding='utf8'));nodes={n['id']:n for n in r['nodes']};weights=collections.Counter()
parents={child:n['id'] for n in r['nodes'] for child in n.get('children',[])}
for key,delta in zip(r['samples'],r['timeDeltas']):
    stack=[];at=key
    while at in nodes:
        n=nodes[at];frame=n['callFrame'];stack.append((frame['functionName'],frame.get('url',''),frame.get('lineNumber',-1)+1));at=parents.get(at)
    if not any('native-widget-layer' in f[1] or 'run-project.mjs' in f[1] for f in stack):continue
    if stack:weights[stack[0]]+=delta
print(json.dumps([{'function':k[0],'file':k[1].split('/')[-1],'line':k[2],'ms':round(v/1000,2)} for k,v in weights.most_common(25)],ensure_ascii=False))
