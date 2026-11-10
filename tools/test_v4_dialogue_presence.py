"""Only reviewed live FTE listeners change; all source graph semantics remain exact."""
import copy,json
from v4_dialogue_presence import ROOT,apply

graphs={p.relative_to(ROOT).as_posix():json.loads(p.read_text(encoding='utf-8'))
        for folder in ('chapters','freetime')for p in (ROOT/'data/v4_story'/folder).glob('*.json')}
before=copy.deepcopy(graphs);count=apply(graphs);changed=[]
for file,graph in graphs.items():
    for id,node in graph.get('nodes',{}).items():
        prior=before[file]['nodes'][id];normalized=dict(node);actor=normalized.pop('dialoguePortrait',None)
        assert normalized==prior,(file,id)
        if actor:
            assert node['source']['file'].split('_')[0]in('44','45')
            assert node['type']=='menu'or(node['type']=='say'and node['actor']=='mio'and not node.get('mono'))
            changed.append((file,id))
assert count==len(changed)>0
for prefix,actor in [('44','yuu'),('45','rei')]:
    g=graphs['data/v4_story/freetime/'+prefix+'.json']
    first_reply=min((n for n in g['nodes'].values()if n['type']=='say'and n.get('actor')=='mio'and not n.get('mono')),key=lambda n:n['source']['line'])
    assert first_reply['dialoguePortrait']==actor
    assert all(n['dialoguePortrait']==actor for n in g['nodes'].values()if n['type']=='menu')
    assert all('dialoguePortrait'not in n for n in g['nodes'].values()if n.get('pov')or n.get('mono'))
report={'ok':True,'boundNodeCopies':count,'onlyProtagonistSpokenRepliesAndMenus':True,'sameAllOtherFields':True,'scope':'Two source-hash-locked live conversations; no inference from old sprite, no speaker/body/route/word change. Native rendering is separate.'}
(ROOT/'Game/Saved/dialogue-presence-source-proof-2026110116.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
