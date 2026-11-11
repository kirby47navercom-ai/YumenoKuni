"""Live portrait continuity is a display decision, never a story/identity decision."""
import copy,json
from v4_dialogue_presence import ROOT,continue_live_replies,apply
from v4_acting_bindings import build_acting,bind_node

def node(id,actor,following=None,**extra):
    n={'id':id,'type':'say','actor':actor,'speaker':actor,'text':id,'mono':False,'source':{'file':'demo.md','location':'room','line':1},**extra}
    if following:n['next']=following
    return n
def graph(rows):return {'g':{'nodes':{n['id']:n for n in rows}}}
bindings={'sections':{'demo.md:room':{'space':'hotel_lobby'}}}
g=graph([node('a','ken','b',pose='ken_C05'),node('b','mio','c'),node('c','mio','d'),{'id':'d','type':'menu','source':{'file':'demo.md','location':'room','line':1},'options':[]}])
before=copy.deepcopy(g);result=continue_live_replies(g,bindings,{'ken','ken_C05','rin'})
assert result=={'b':'ken_C05','c':'ken_C05','d':'ken_C05'}
assert g['g']['nodes']['b']['actor']=='mio'
for mode in ('stage','choice','conflict','newscene','cg','mono','recording','private','trial','v5-trial','v5-verdict','pool'):
    g=graph([node('a','ken','b'),node('b','mio')])
    if mode=='stage':g['g']['nodes']['a'].update(type='stage')
    if mode=='choice':g['g']['nodes']['a'].pop('next');g['g']['nodes']['a'].update(type='menu',options=[{'to':'b'}])
    if mode=='conflict':g['g']['nodes']['x']=node('x','rin','b')
    if mode=='newscene':g['g']['nodes']['b']['source']['location']='other'
    if mode=='cg':g['g']['nodes']['b']['shot']={'image':'actual-cg.webp'}
    if mode=='mono':g['g']['nodes']['b']['mono']=True
    if mode=='recording':g['g']['nodes']['a']['delivery']='켄·복원'
    if mode=='private':g['g']['nodes']['b']['pov']='rei'
    if mode=='trial':
        for n in g['g']['nodes'].values():n['source']['location']='T-01'
    if mode in ('v5-trial','v5-verdict'):
        for n in g['g']['nodes'].values():n['source']['location']='03-T01'if mode=='v5-trial'else'03-R00'
    if mode=='pool':g['g']['nodes']['b'].update(type='menu',selectionRole='freetime')
    assert not continue_live_replies(g,bindings,{'ken','rin'}),mode
g=graph([node('a','ken','b'),node('b','mio')]);g['other']=copy.deepcopy(g['g'])
assert continue_live_replies(g,bindings,{'ken'})=={'b':'ken'}
assert all(n['nodes']['b']['dialoguePortrait']=='ken'for n in g.values())
g=graph([node('a','sora','b',appearanceActor='ken',pose='ken_C05'),node('b','mio')])
assert continue_live_replies(g,bindings,{'ken_C05'})=={'b':'ken_C05'}
assert g['g']['nodes']['a']['actor']=='sora'and g['g']['nodes']['b']['actor']=='mio'
for mode in ('range','conditional','private-scene','return-call'):
    g=graph([node('a','ken','b'),node('b','mio')]);g['g']['nodes']['b']['source']['line']=3
    b=copy.deepcopy(bindings)
    if mode=='range':b['sceneRanges']=[{'source':{'file':'demo.md'},'startLine':3,'endLineExclusive':4,'space':'other'}]
    if mode=='conditional':b['conditionalSceneRanges']=[{'source':{'file':'demo.md'},'startLine':3,'endLineExclusive':4,'space':'other','when':[{'flag':'actual','equals':True}]}]
    if mode=='private-scene':b['sections']['demo.md:room']['perspective']='objective-unseen-by-mio'
    if mode=='return-call':g['g']['nodes']['x']={'id':'x','type':'call','target':'a','returnTo':'b'}
    assert not continue_live_replies(g,b,{'ken'}),mode
for direction,kept in [('유우가 앉는다.',True),('유우가 작게 웃는다.',True),('유우가 앉는다. 잠깐 뒤 나간다.',False),('나나가 앉는다.',False),('사진 속 유우가 앉는다.',False),('유우가 앉는다. 나나가 웃는다.',False),('유우가 앉지 않는다.',False)]:
    g=graph([node('a','yuu','s'),node('s','', 'b',type='stage',direction=direction),node('b','mio')])
    result=continue_live_replies(g,bindings,{'yuu','nana'})
    assert bool(result)==kept,(direction,result)
    assert 'dialoguePortrait'not in g['g']['nodes']['s']

graphs={p.relative_to(ROOT).as_posix():json.loads(p.read_text(encoding='utf-8'))for directory in ('chapters','freetime')for p in(ROOT/'data/v4_story'/directory).glob('*.json')}
acting=build_acting();graphs=bind_node(graphs,acting);apply(graphs);before=copy.deepcopy(graphs)
scenes=json.loads((ROOT/'data/presentation/v4_scenes.json').read_text(encoding='utf-8'))
assigned=continue_live_replies(graphs,scenes,acting['assets']);changed=[];examples=[]
for file,g in graphs.items():
    for id,n in g.get('nodes',{}).items():
        if n==before[file]['nodes'][id]:continue
        stripped=dict(n);value=stripped.pop('dialoguePortrait')
        assert value==assigned[id]and stripped==before[file]['nodes'][id],(file,id)
        changed.append((file,id))
        if file.startswith('data/v4_story/chapters/')and n['type']=='say'and n.get('source',{}).get('file','').startswith(('11a_','12a_','13a_'))and len(examples)<15:
            examples.append({'graph':file,'node':id,'portrait':value,'source':n['source'],'speaker':n['speaker'],'text':n['text']})
assert len(assigned)>100 and changed
report={'ok':True,'uniqueLiveContinuityNodes':len(assigned),'nodeCopies':len(changed),'allOtherFieldsExact':True,'allIncomingEdgesMustAgree':True,'unprovenStageChoiceSceneCgHistoryPrivateTrialPoolBreaksChecked':True,'onlySameKnownPersonLiteralPresentGestureMayBridgeStage':True,'samePhysicalBodyPoseAsProvenLiveSpeaker':True,'saveSchemaChanged':False,'nativePlayed':False,'examples':examples,'assignments':assigned}
(ROOT/'Game/Saved/dialogue-continuity-source-proof-2026110117.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items()if k not in('examples','assignments')},ensure_ascii=False))
