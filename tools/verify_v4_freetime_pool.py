"""Cross-chapter pool/call/unique-completion checks; never executes the game."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def actual_candidate_walk(graph,window,wanted,history):
    """Run actual merged source routes with one selected FTE, other slots rest.

    This supplies a declared prior history and models task success. It proves
    source callbacks/call returns, not that the seeded history was played or
    that native answers, duration, pictures or sound passed.
    """
    flags=dict(history);nodes=graph['nodes'];ident=graph['entry'];stack=[];trace=[]
    for _ in range(len(nodes)*3):
        n=nodes[ident];trace.append(n);flags.update(n.get('set',{}));kind=n['type']
        if kind in ('gate','end'):return trace,flags
        if kind=='return':
            frame=stack.pop();flags.update(frame.get('onReturnSet',{}));ident=frame['returnTo']
        elif kind=='menu':
            eligible=[o for o in n['options'] if all(flags.get(k,False)==v for k,v in o.get('requires',{}).items())]
            requested=wanted if ident==window else next((o['id'] for o in eligible if o['id'] in ('REST','continue')),None) if n.get('selectionRole')=='freetime' else None
            chosen=next((o for o in eligible if o['id']==requested),None) if requested is not None else eligible[0]
            assert chosen is not None,(ident,wanted,'target candidate must actually be eligible')
            flags.update(chosen.get('set',{}));ident=chosen['to']
        elif kind=='branch':ident=next((c['to'] for c in n['cases'] if flags.get(c['flag'])==c['equals']),n['default'])
        elif kind=='call':stack.append(n);ident=n['target']
        elif kind=='investigate':
            pending=[s for s in n['spots'] if not flags.get(s['completionFlag'])]
            if pending:
                spot=pending[0];stack.append({'returnTo':spot.get('returnTo',ident),'onReturnSet':spot.get('onReturnSet',{})});ident=spot['entry']
            else:
                assert all(flags.get('card:'+c) for c in n.get('requiredCards',[]));ident=n['next']
        elif kind=='evidence':flags['card:'+n['evidenceId']]=True;ident=n['next']
        elif kind=='task':
            if n.get('outcomes'):
                outcome=n['outcomes']['A'];flags.update(outcome.get('sets',{}));ident=outcome['to']
            else:ident=n['success']
        else:ident=n['next']
    raise AssertionError('Actual merged candidate route exceeded bound')


def main():
    root=ROOT/'data/v4_story'
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    index=read(root/'freetime/index.json')
    meetings={key:read(root/row['path']) for key,row in index['meetings'].items()}
    assert set(map(str,range(20,65)))<=meetings.keys()
    assert len(meetings)==73 and index['canonicalCount']==45 and index['calendarVariantCount']==28
    chapters=[read(p) for p in (root/'chapters').glob('*.json')]
    entries={graph['entry']:key for key,graph in meetings.items()}
    assert len(entries)==73,'Calendar variants must keep independent entry IDs'
    calls={key:[] for key in meetings};options=0;candidate_paths=0
    prior={graph['completionFlag']:False for graph in meetings.values()}
    for graph in meetings.values():
        prior.update({k:v[0] for k,v in graph.get('requiresPriorFlags',{}).items() if not isinstance(v[0],bool)})
        for flag,rule in graph.get('conditionalPriorFlags',{}).items():prior.setdefault(flag,rule['values'][0])
    # Required previous-story choices without granting a never-met FTE.
    prior.update({'P-C01':'A','P-C02':'A','2-C05':'A','1-C03':'카에데','1-C05':'A','1-C07':'A','1-C08':'A','1-C09':'A','I-C01':'A','W1-C02':'A'})
    for chapter in chapters:
        nodes=chapter['nodes']
        for node in nodes.values():
            if node['type']!='call' or node.get('target') not in entries:continue
            key=entries[node['target']];graph=meetings[key];calls[key].append(node)
            returned=node.get('onReturnSet',{})
            assert returned.get(graph['completionFlag']) is True,(chapter['chapter'],key,'completion on actual return')
            assert graph['completionFlag'] not in node.get('set',{}),'Cannot award completion before meeting'
            assert node['returnTo'] in nodes and node['target'] in nodes
            for ident,original in graph['nodes'].items():
                # Presentation/scene binding may add metadata in chapter; it
                # cannot change actual source speech, routes or choice sets.
                current=nodes[ident]
                for field in ('type','text','speaker','next','target','returnTo'):
                    assert current.get(field)==original.get(field),(key,ident,field)
        for node in nodes.values():
            if node.get('selectionRole')!='freetime':continue
            assert any(o.get('id') in ('REST','continue') for o in node['options']),'All-ineligible histories still need their authored continuation'
            for option in node['options']:
                call=nodes[option['to']]
                if call['type']!='call' or call.get('target') not in entries:continue
                key=entries[call['target']];flag=meetings[key]['completionFlag']
                assert option.get('requires',{}).get(flag) is False,(chapter['chapter'],node['id'],key,'unique completion guard')
                history={**prior,**{k:v[0] for k,v in meetings[key].get('requiresPriorFlags',{}).items()},**option['requires']}
                trace,state=actual_candidate_walk(chapter,node['id'],option['id'],history)
                assert trace[-1]['type']=='end',(chapter['chapter'],node['id'],key,trace[-1])
                assert state.get(flag) is True,(key,'actual normal call return missing completion')
                assert sum(n['id']==call['id'] for n in trace)==1,(key,'must enter chosen call exactly once')
                candidate_paths+=1
                options+=1
    assert all(calls.values()),'No authored calendar variant may be an uncalled library placeholder'
    print(json.dumps({'passed':True,'canonicalMeetings':45,'calendarVariants':28,'graphs':73,'calls':sum(map(len,calls.values())),'candidateOptions':options,'actualMergedCandidatePaths':candidate_paths,'uncalled':0,'seededPriorHistory':True,'taskSuccessModel':True,'runtimeExecuted':False}))


if __name__=='__main__':main()
