"""Authored on-site interlocutors, separate from the speaker and physical actor.

Only the two reviewed, live FTE conversations below are bound. A prior sprite
is never carried into another scene, a private POV, a memory, or a trial.
"""
import hashlib
import json
import re
from collections import defaultdict,deque
from build_v4_story import SPEAKERS
from v4_acting_bindings import SUBJECT,own_clauses
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REVIEWED={
 '44':('yuu','c9708a37da6edcf826e4b6857845411cd215938f4dbe5b20168df12a891b3a56',7,486),
 '45':('rei','23f15ccccecd53867626941767668ef20326efe4081b27d91b4b58f79080f1c8',7,366),
}

def apply(graphs):
    sources={}
    for prefix,(actor,sha,first,last)in REVIEWED.items():
        path,=(ROOT/'docs/design/rewrite_v4').glob(prefix+'_*.md')
        text=path.read_text(encoding='utf-8-sig')
        if hashlib.sha256(text.encode()).hexdigest()!=sha:
            raise ValueError('Re-read live interlocutor bounds after source change: '+path.name)
        sources[path.name]=(actor,first,last)
    count=0
    for graph in graphs.values():
        for n in graph.get('nodes',{}).values():
            source=n.get('source',{});bound=sources.get(source.get('file'))
            if not bound:continue
            actor,first,last=bound
            if not first<=source.get('line',0)<=last:continue
            eligible=n.get('type')=='menu' or (n.get('type')=='say'and n.get('actor')=='mio'and not n.get('mono'))
            if not eligible:continue
            assert 'dialoguePortrait'not in n
            n['dialoguePortrait']=actor;count+=1
    return count


def continue_live_replies(graphs,bindings,assets):
    """Keep a proven live speaker through directly adjacent player replies.

    Every incoming edge must agree. An explicit, current on-site gesture may
    keep that same known person; other stages, choices, calls, scene changes,
    recordings, private POV and trials break continuity. This compiles an
    explicit display key, so cold Continue needs no invented portrait history.
    """
    copies=defaultdict(list)
    for graph in graphs.values():
        for id,node in graph.get('nodes',{}).items():copies[id].append(node)
    nodes={id:values[0]for id,values in copies.items()};incoming=defaultdict(set)
    for id,node in nodes.items():
        for key in ('next','target','returnTo','default','success','wrong'):
            if isinstance(node.get(key),str):incoming[node[key]].add((id,key))
        for key in ('options','cases'):
            for item in node.get(key,[]):incoming[item['to']].add((id,key))
        for item in node.get('outcomes',{}).values():
            if 'to'in item:incoming[item['to']].add((id,'outcome'))
    cache={}
    def context(n):
        source=n.get('source',{});file=source.get('file','');location=source.get('location','');line=source.get('line',0)
        key=(file,location,line,n.get('pov'),json.dumps([n.get('scene'),n.get('sceneVariants'),n.get('shot')],sort_keys=True))
        if key in cache:return cache[key]
        result=None
        if file and location and not location.startswith('T')and not re.match(r'^0[1-6]-[TR]',location)and not re.match(r'^1[1-6]c',file)and not n.get('pov'):
            scene=bindings.get('sections',{}).get(file+':'+location,n.get('scene',{}))
            for row in bindings.get('sceneRanges',[]):
                if row['source']['file']==file and row['startLine']<=line<row['endLineExclusive']:scene=row
            variants=list(n.get('sceneVariants',[]))+[{'space':r['space'],'when':r['when'],'perspective':r.get('perspective','current-observation')}
                      for r in bindings.get('conditionalSceneRanges',[])
                      if r['source']['file']==file and r['startLine']<=line<r['endLineExclusive']]
            cg=bool(n.get('shot',{}).get('image'))or any(r['source']['file']==file and r['startLine']<=line<r['endLineExclusive']for r in bindings.get('cgRanges',[]))
            if not cg and scene.get('perspective','current-observation')=='current-observation'and all(v['perspective']=='current-observation'for v in variants):
                result=(file,location,scene.get('space'),json.dumps(variants,sort_keys=True))
        cache[key]=result;return result
    def candidate(n):
        return (n.get('type')=='menu'and not n.get('selectionRole'))or(n.get('type')=='say'and n.get('actor')=='mio'and not n.get('mono'))
    stage_owners={}
    def stage_keeps(n,actor):
        direction=n.get('direction','')
        if re.search(r'떠나|나간|나가|돌아간|가버|사라|비운|다녀|헤어|문밖|화면밖|사진|영상|회상|녹음|목소리|기억|원고|경로|선택|경우|이면|라면',re.sub(r'\s+','',direction)):return False
        display=next((name for name,slug in SPEAKERS.items()if slug==actor.split('_')[0]),None)
        subjects={m[1]for m in SUBJECT.finditer(direction)}-{'미오'}
        if not display or subjects!={display}:return False
        clauses=list(own_clauses(direction,display))
        gestures={'앉는다','다시앉는다','고개를끄덕인다','작게웃는다','짧게웃는다','크게웃는다','웃는다','미소를짓는다','미소짓는다','고개를든다','미오를본다','잠깐웃는다','고개를숙인다'}
        return bool(clauses)and all(re.sub(r'\s+','',clause)in gestures for clause in clauses)
    def owner(n):
        if n.get('type')=='stage':return stage_owners.get(n['id'])
        if n.get('type')=='say'and n.get('actor')not in(None,'','mio')and not n.get('mono'):
            if re.search(r'복원|회상|방송|독백',n.get('delivery','')):return None
            key=n.get('pose')or n.get('appearanceActor')or n['actor']
            return key if key in assets else None
        return n.get('dialoguePortrait')if candidate(n)else None
    queue=deque(id for id,n in nodes.items()if (candidate(n)or n.get('type')=='stage')and 'dialoguePortrait'not in n)
    assigned={}
    while queue:
        id=queue.popleft();n=nodes[id]
        if 'dialoguePortrait'in n or id in stage_owners or not incoming[id]or context(n)is None:continue
        choices=[]
        for previous,edge in incoming[id]:
            p=nodes.get(previous)
            if edge!='next'or p is None or context(p)!=context(n):break
            actor=owner(p)
            if not actor:break
            choices.append(actor)
        else:
            if len(set(choices))!=1:continue
            actor=choices[0]
            if n.get('type')=='stage':
                if not stage_keeps(n,actor):continue
                stage_owners[id]=actor
            else:
                for copy in copies[id]:copy['dialoguePortrait']=actor
                assigned[id]=actor
            for key in ('next',):
                following=n.get(key)
                if following in nodes and (candidate(nodes[following])or nodes[following].get('type')=='stage'):queue.append(following)
    return assigned
