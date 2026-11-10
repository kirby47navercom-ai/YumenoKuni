"""Source/branch checks for chapter five; static model, no game execution.

Task success, when requested, is a structural assumption used to inspect the
authored continuation. It neither solves a real input nor binds missing art.
"""
import itertools
import json
from build_v4_story import ROOT, Source
from v4_story_case5 import compile_chapter_five, route_source_hashes


def fixture():
    sources={p.name:Source(p) for p in (ROOT/'docs/design/rewrite_v4').glob('*.md')}
    tasks=json.loads((ROOT/'data/v4_story/tasks.json').read_text(encoding='utf-8-sig'))
    return sources,tasks,compile_chapter_five(sources,{},tasks)


def walk(g,choices=None,flags=None,start=None,tasks=None,assume_success=False):
    choices=choices or {};flags=dict(flags or {});flags.setdefault('4-C10','C')
    trace=[];owned=set();stack=[];nid=start or g['entry'];inputs=[]
    for _ in range(20000):
        n=g['nodes'][nid];trace.append(n);flags.update(n.get('set',{}));kind=n['type']
        if kind in ('gate','end'):return n,trace,flags,owned,inputs
        if kind=='menu':
            key=next(iter(n['options'][0].get('set',{})),None)
            wanted=choices.get(key,n['options'][0]['id'])
            o=next(x for x in n['options'] if x['id']==wanted)
            assert all(flags.get(k,False)==v for k,v in o.get('requires',{}).items())
            flags.update(o.get('set',{}));nid=o['to']
        elif kind=='branch':
            nid=next((c['to'] for c in n['cases'] if flags.get(c['flag'],False)==c['equals']),n['default'])
        elif kind=='investigate':
            pending=[s for s in n['spots'] if not flags.get(s['completionFlag'],False)]
            if pending:
                s=pending[0];stack.append((s['returnTo'],s['onReturnSet']));nid=s['entry']
            else:
                assert set(n.get('requiredCards',[]))<=owned;nid=n['next']
        elif kind=='call':
            stack.append((n['returnTo'],n.get('onReturnSet',{})));nid=n['target']
        elif kind=='return':
            nid,changes=stack.pop();flags.update(changes)
        elif kind=='evidence':
            if n.get('revision'):assert n['evidenceId'] in owned,n
            owned.add(n['evidenceId']);nid=n['next']
        elif kind=='task':
            inputs.append(n['taskId'])
            assert tasks and set(tasks['tasks'][n['taskId']].get('requiresEvidence',[]))<=owned
            if not assume_success:return n,trace,flags,owned,inputs
            outcome=n.get('outcomes',{}).get(choices.get('lie','A'))
            if outcome:flags.update(outcome.get('sets',{}));nid=outcome['to']
            else:nid=n['success']
        else:nid=n['next']
    raise AssertionError('Unexpected control loop')


def source_lines(trace,prefix):
    return {n.get('source',{}).get('line') for n in trace if n.get('source',{}).get('file','').startswith(prefix+'_')}


def verify_daily(g,c,tasks):
    n,trace,flags,owned,inputs=walk(g,c,tasks=tasks)
    # At the current boundary, either the unbound first actual input or the
    # visible trial integration gate ends normal progress; never auto-succeed.
    assert n['type'] in ('gate','task'),n
    assert len(owned)==20 and not flags.get('v4:death:akari:public',False)
    assert flags['v4:death:koto:public'] is True
    assert all(not x.get('geometryReady') for node in trace if node['type']=='investigate' for x in node['spots'])
    conflict=source_lines(trace,'15a8');b3=source_lines(trace,'15b3')
    choice=c.get('5-C04','A');invest=c.get('I5-C01','A')
    assert bool(conflict&set(range(173,190)))==(choice!='A')
    assert bool(conflict&set(range(93,100)))==(choice=='A')
    assert bool(conflict&set(range(103,138)))==(choice=='B')
    assert bool(conflict&set(range(141,172)))==(choice=='C')
    for key,lo,hi in [('A',295,301),('B',305,315),('C',319,325)]:
        assert bool(conflict&set(range(lo,hi+1)))==(choice==key)
    for key,lo,hi in [('A',347,356),('B',359,372),('C',375,390)]:
        assert bool(b3&set(range(lo,hi+1)))==(invest=='C' and choice==key)
    for key,lo,hi in [('A',425,428),('B',431,436),('C',439,442)]:
        assert bool(b3&set(range(lo,hi+1)))==(invest!='C' and choice==key)
    assert bool(b3&set(range(445,453)))==(invest=='C')
    assert bool(b3&set(range(402,409)))==(invest=='A')
    assert bool(b3&set(range(410,417)))==(invest=='B')
    assert not source_lines(trace,'15a7')&set(range(203,246))
    # Only actual death confirmation changes the public state.
    before=next(i for i,x in enumerate(trace) if x.get('set',{}).get('v4:death:koto:public'))
    assert trace[before]['source']['line']==185
    return len(trace)


def main():
    sources,tasks,g=fixture();nodes=g['nodes'];route_source_hashes(sources)
    for n in nodes.values():
        for field in ('next','success','default','target','returnTo'):
            if field in n:assert n[field] in nodes,(n['id'],field)
        for child in n.get('cases',[])+n.get('options',[]):assert child['to'] in nodes
        for s in n.get('spots',[]):assert s['entry'] in nodes and not s['geometryReady']
    keys=['5-C01','5-C02','5-C03','5-C04','5-C05','5-C06','5-C07','I5-C01']
    cases=[{}]
    for a,b in itertools.combinations(keys,2):
        cases.extend({a:x,b:y} for x,y in itertools.product('ABC',repeat=2))
    for c in cases:verify_daily(g,c,tasks)
    for prior in 'ABC':
        n,t,f,cards,inputs=walk(g,flags={'4-C10':prior},tasks=tasks)
        old=source_lines(t,'127')
        assert bool(old&set(range(149,164)))==(prior=='A')
        assert bool(old&set(range(167,180)))==(prior=='B')
        assert bool(old&{185})==(prior=='C')
    for memory in ('A1','A2','A3'):
        n,t,f,cards,inputs=walk(g,flags={'fte:54:complete':True,'RIN-03A':memory},tasks=tasks)
        r=source_lines(t,'15a7')
        assert bool(r&set(range(375,400)))==(memory=='A1')
        assert f.get('v4:5:rin03:correction-needed',False)==(memory=='A1')
    for first,second,lie in itertools.product('ABC','ABC',(False,True)):
        # Start only after a structurally successful trial for result callbacks;
        # do not pretend the input has actually been completed.
        entry=next(n['pendingResultEntry'] for n in nodes.values() if 'pendingResultEntry' in n)
        n,t,f,owned,inputs=walk(g,flags={'T5-C03':first,'T5-C02':second,'T5-LIE-B':lie},start=entry)
        assert n['type']=='end' and n['nextChapter']=='6'
        assert f['v4:death:akari:public'] is True
        assert bool(source_lines(t,'169')&set(range(312,329)))==lie
        for key,lo,hi in [('A',287,297),('B',301,309),('C',313,319)]:
            assert bool(source_lines(t,'100')&set(range(lo,hi+1)))==(first==key)
        for key,lo,hi in [('A',349,354),('B',357,362),('C',365,370)]:
            assert bool(source_lines(t,'15d')&set(range(lo,hi+1)))==(second==key)
        docs=[x for x in t if x['id']=='v4:5:document:unfinished-akari-note']
        assert len(docs)==1 and docs[0]['rows'][-1]=='그걸 말하면 네가'
    print(json.dumps({'chapter':5,'livingInvestigationPairwisePaths':len(cases),'historicalVariants':6,'resultCallbacks':18,'nodes':len(nodes),'evidence':20,'model':'static authored branches only; no native input or playtime claim'},ensure_ascii=False))


if __name__=='__main__':main()
