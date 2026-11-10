"""Check actual callbacks/physical states, not dialogue volume or play time."""
import itertools
import json
from build_v4_story import Source,ROOT
from v4_story_freetime_followups import compile_followup
from verify_v4_story import walk


def lines(events,prefix):return {n.get('source',{}).get('line') for n in events if n.get('source',{}).get('file','').startswith(prefix+'_')}


def main():
    sources={p.name:Source(p) for p in (ROOT/'docs/design/rewrite_v4').glob('*.md')}
    count=0
    for prefix in ('21','152'):
        g=compile_followup(prefix,sources);menus=[n for n in g['nodes'].values() if n['type']=='menu']
        for opts in itertools.product(*(n['options'] for n in menus)):
            selected={n['id']:o['id'] for n,o in zip(menus,opts)}
            trace,flags=walk(g,selected);assert trace[-1]['type']=='return'
            if prefix=='21':
                for key,lo,hi in [('A',268,294),('B',298,318),('C',322,342)]:
                    assert bool(lines(trace,'21')&set(range(lo,hi+1)))==(flags['KOTO-01A']==key)
            else:
                assert not lines(trace,'33')&set(range(1,30))
                assert lines(trace,'152')&set(range(5,34))
                assert g['completionSet']=={'fte:33:complete':True,'TA01Late2B':True}
                assert 'fte:33:complete' not in flags and 'TA01Late2B' not in flags,'Completion is caller-return only'
            count+=1
    g=compile_followup('46',sources);menus=[n for n in g['nodes'].values() if n['type']=='menu']
    for a,b,late in itertools.product(('A1','A2','A3'),('B1','B2','B3'),(False,True)):
        for opts in itertools.product(*(n['options'] for n in menus)):
            selected={n['id']:o['id'] for n,o in zip(menus,opts)}
            trace,flags=walk(g,selected,{'F-TA01-A':a,'F-TA01-B':b,'TA01Late2B':late})
            assert trace[-1]['type']=='return'
            actual=lines(trace,'46')
            for key,lo,hi in [('A1',34,42),('A2',45,54),('A3',58,68)]:assert bool(actual&set(range(lo,hi+1)))==(a==key)
            assert bool(actual&{381,383})==(flags['F-TA02-B']=='B1' and flags['F-TA02-A']=='A2')
            assert bool(actual&{387,389})==(flags['F-TA02-B']=='B1' and flags['F-TA02-A']!='A2')
            assert bool(lines(trace,'152')&set(range(41,62)))==late
            replaced=[n for n in trace if n.get('authoredTimeReplacement')]
            assert len(replaced)==(int(a!='A2')+int(b=='B1') if late else 0)
            assert all(n['text'].startswith('어제') for n in replaced)
            assert 'fte:46:complete' not in flags
            count+=1
    trace,flags=walk(g,{n['id']:n['options'][0]['id'] for n in menus})
    assert trace[-1]['type']=='gate' and 'F-TA02-A' not in flags
    campaign=json.loads((ROOT/'data/v4_story/chapters/1.json').read_text(encoding='utf8'))
    call=campaign['nodes']['v4:1:F1-B:call:152'];assert call['onReturnSet']['TA01Late2B'] and call['onReturnSet']['fte:33:complete']
    late_call=campaign['nodes']['v4:1:F1-early:call:46'];assert late_call['onReturnSet']['TA02Late3AM']
    normal_call=campaign['nodes']['v4:1:F1-B:call:46'];assert 'TA02Late3AM' not in normal_call['onReturnSet']
    for prefix in ('51','43','49'):
        g=compile_followup(prefix,sources);menus=[n for n in g['nodes'].values() if n['type']=='menu']
        histories=g['requiresPriorFlags']
        for values in itertools.product(*histories.values()):
            history=dict(zip(histories,values))
            for lunch in ('EAT','LEAVE') if prefix=='43' and history.get('F-AI01-A')=='A3' else ('EAT',):
                history['F-AI01-A3-LUNCH']=lunch
                for opts in itertools.product(*(n['options'] for n in menus)):
                    selected={n['id']:o['id'] for n,o in zip(menus,opts)}
                    trace,flags=walk(g,selected,history);assert trace[-1]['type']=='return'
                    actual=lines(trace,prefix)
                    if prefix=='51':
                        for key,line in [('A1',285),('A2',289),('A3',293)]:assert (line in actual)==(flags['F-TA03-A']==key)
                        for key,lo,hi in [('A1',359,360),('A2',363,366),('A3',369,372)]:assert bool(actual&set(range(lo,hi+1)))==(flags['F-TA03-A']==key)
                    elif prefix=='43':
                        for key,lo,hi in [('B1',411,422),('B2',425,438),('B3',441,454)]:assert bool(actual&set(range(lo,hi+1)))==(history['F-AI01-B']==key)
                        assert bool(actual&set(range(351,367)))==(flags['F-AI02-B']=='B2' and flags['F-AI02-A']!='A2')
                        assert bool(actual&set(range(369,381)))==(flags['F-AI02-B']=='B2' and flags['F-AI02-A']=='A2')
                        assert (63 in actual)==(history['F-AI01-A']=='A3' and lunch=='EAT')
                        assert (69 in actual)==(history['F-AI01-A']=='A3' and lunch=='LEAVE')
                    else:
                        for key,lo,hi in [('B1',445,454),('B2',457,466),('B3',469,470)]:assert bool(actual&set(range(lo,hi+1)))==(flags['F-SA02-B']==key)
                    count+=1
    for prefix in ('23','40','50','153'):
        g=compile_followup(prefix,sources);menus=[n for n in g['nodes'].values() if n['type']=='menu']
        histories=g.get('requiresPriorFlags',{})
        for values in itertools.product(*histories.values()):
            history=dict(zip(histories,values))
            for opts in itertools.product(*(n['options'] for n in menus)):
                selected={n['id']:o['id'] for n,o in zip(menus,opts)}
                trace,flags=walk(g,selected,history);assert trace[-1]['type']=='return'
                actual=lines(trace,prefix)
                if prefix=='23':
                    a,b=flags['SHO-01A'],flags['SHO-01B']
                    assert (140 in actual)==(b=='A' and a=='A')
                    assert (144 in actual)==(b=='A' and a!='A')
                    assert (170 in actual)==(b=='B' and a=='A')
                    assert (174 in actual)==(b=='B' and a!='A')
                    assert (194 in actual)==(b=='C' and a=='A')
                    assert (200 in actual)==(b=='C' and a!='A')
                    assert (222 in actual)==(a=='A') and (226 in actual)==(a!='A')
                elif prefix=='40':
                    a,b=flags['KAEDE-02A'],flags['KAEDE-02B']
                    assert bool(actual&set(range(75,103)))==(a in ('A','B'))
                    if a in ('A','B'):
                        menu_index=next(i for i,n in enumerate(trace) if n['id']=='v4:40:KAEDE-02A:menu')
                        practice_index=next(i for i,n in enumerate(trace) if n.get('source',{}).get('line')==85)
                        assert menu_index < practice_index
                    assert (657 in actual)==(a=='A') and (661 in actual)==(a=='B')
                    assert (665 in actual)==(a=='C' and b=='A')
                    assert (669 in actual)==(a=='C' and b=='B')
                    assert (673 in actual)==(a=='C' and b=='C')
                elif prefix=='50':
                    assert (565 in actual)==(flags['KAEDE-03B']=='A')
                    assert bool(actual&set(range(207,227)))==(history['KAEDE-02A']=='B')
                    assert bool(actual&set(range(33,51)))==(history['KAEDE-02B']=='A')
                    assert bool(actual&set(range(81,95)))==(history['KAEDE-02B']=='C')
                    assert bool(actual&set(range(253,259)))==(flags['KAEDE-03B']=='A' and flags['KAEDE-03A']=='C')
                    assert bool(actual&set(range(247,251)))==(flags['KAEDE-03B']=='A' and flags['KAEDE-03A']!='C')
                else:
                    assert not lines(trace,'22')&set(range(1,40))
                    assert g['completionSet']=={'fte:22:complete':True,'KAEDE01Late3D':True}
                    assert 'fte:22:complete' not in flags
                count+=1
    assert campaign['nodes']['v4:1:F1-E:call:40']['onReturnSet']['KAEDE02Late3E']
    assert not any(n['type']=='gate' and 'unrouted' in n['id'] for n in campaign['nodes'].values())
    for prefix in ('35','41','44','45','48'):
        g=compile_followup(prefix,sources);menus=[n for n in g['nodes'].values() if n['type']=='menu']
        histories=g['requiresPriorFlags']
        for values in itertools.product(*histories.values()):
            history=dict(zip(histories,values))
            for consent in ('N1','N2') if prefix=='44' and history['F-YU01-B']=='B2' else (None,):
                if consent:history['F-YU01-B2-N']=consent
                for opts in itertools.product(*(n['options'] for n in menus)):
                    selected={n['id']:o['id'] for n,o in zip(menus,opts)}
                    trace,flags=walk(g,selected,history);assert trace[-1]['type']=='return'
                    actual=lines(trace,prefix)
                    if prefix=='35':
                        early=flags['RIN-02A']=='A'
                        assert bool(actual&set(range(170,230)))==early
                        assert bool(actual&set(range(234,421)))==(not early)
                        assert (328 in actual)==(not early and flags['RIN-02B-BC']=='B2')
                        assert ('RIN-02B-A' in flags)==early and ('RIN-02B-BC' in flags)==(not early)
                    elif prefix=='41':
                        a,b=history['SHO-01A'],history['SHO-01B']
                        assert (43 in actual)==(a=='A' and b=='A')
                        assert (55 in actual)==(b=='B')
                        assert (63 in actual)==(b=='B' and a=='A')
                        assert (69 in actual)==(b=='B' and a!='A')
                        assert (79 in actual)==(b!='B' and not(a=='A' and b=='A'))
                        assert sum(bool(n.get('authoredInlineQuotation')) for n in trace)==1
                    elif prefix=='44':
                        old=history['F-YU01-B'];current=flags['F-YU02-B']
                        assert (141 in actual)==(old=='B2' and consent=='N1')
                        assert (147 in actual)==(old=='B2' and consent=='N2')
                        assert (323 in actual)==(current=='B1' and old in ('B1','B3'))
                        assert (359 in actual)==(current=='B1' and old=='B2')
                        assert (401 in actual)==(current=='B1' and old in ('B1','B3'))
                        assert (405 in actual)==(current=='B1' and old=='B2')
                        assert (487 in actual)==(current=='B3')
                        assert (473 in actual)==(current!='B3')
                        assert (63 in actual)==(flags['F-YU02-A']=='A2')
                    elif prefix=='45':
                        a,b=flags['F-RE02-A'],flags['F-RE02-B']
                        assert (177 in actual)==(a=='A1')
                        assert (309 in actual)==(b=='B1')
                        assert (355 in actual)==(b!='B3') and (369 in actual)==(b=='B3')
                        if b=='B3':
                            closing=next(n for n in trace if n.get('source',{}).get('file')==g['sourceFile'] and n.get('source',{}).get('line')==369)
                            assert closing['pov']=='rei' and closing['knowledgeOwner']=='rei'
                    else:
                        a,b=flags['F-RI02-A'],flags['F-RI02-B']
                        assert (43 in actual)==(a=='A1') and (75 in actual)==(a=='A2') and (179 in actual)==(a=='A3')
                        assert (319 in actual)==(b=='B1') and (345 in actual)==(b=='B2') and (363 in actual)==(b=='B3')
                        assert (441 in actual)==(b=='B1') and (445 in actual)==(b=='B2') and (449 in actual)==(b=='B3')
                    assert g['completionFlag'] not in flags
                    count+=1
        trace,flags=walk(g,{n['id']:n['options'][0]['id'] for n in menus})
        assert trace[-1]['type']=='gate' and g['completionFlag'] not in flags
    for prefix in ('39','42','47'):
        g=compile_followup(prefix,sources);menus=[n for n in g['nodes'].values() if n['type']=='menu'];histories=g['requiresPriorFlags']
        for values in itertools.product(*histories.values()):
            history=dict(zip(histories,values))
            for late in (False,True) if prefix=='39' else (False,):
                if prefix=='39':history['AK01Late5']=late
                for opts in itertools.product(*(n['options'] for n in menus)):
                    trace,flags=walk(g,{n['id']:o['id'] for n,o in zip(menus,opts)},history)
                    assert trace[-1]['type']=='return' and g['completionFlag'] not in flags
                    actual=lines(trace,prefix)
                    if prefix=='39':
                        a,b=flags['F-AK02-A'],flags['F-AK02-B']
                        assert (13 in actual)==(history['F-AK01-B']=='B2' and not late)
                        assert (323 in actual)==(a=='A1') and (333 in actual)==(a=='A2') and (345 in actual)==(a=='A3')
                        assert (391 in actual)==(b=='B1' and a=='A1') and (395 in actual)==(b=='B1' and a=='A2')
                        assert (399 in actual)==(b=='B1' and a=='A3')
                        assert (415 in actual)==(b=='B2') and (433 in actual)==(b=='B3')
                    elif prefix=='42':
                        a=flags['SORA-02A']
                        assert (93 in actual)==(a=='A') and (115 in actual)==(a=='B') and (205 in actual)==(a=='C')
                        assert (445 in actual)==(a!='B') and (451 in actual)==(a=='B')
                        assert (239 in actual),'Yuu new single-ball game must be shared, not prior-game score'
                    else:
                        old_a,old_b=history['F-KE01-A'],history['F-KE01-B']
                        assert (37 in actual)==(old_a=='A3') and (47 in actual)==(old_a!='A3')
                        assert (175 in actual)==(old_b=='B1') and (183 in actual)==(old_b=='B2') and (191 in actual)==(old_b=='B3')
                        assert (205 in actual)==(flags['F-KE02-B']=='B1') and (263 in actual)==(flags['F-KE02-B']=='B2') and (321 in actual)==(flags['F-KE02-B']=='B3')
                    count+=1
    for prefix in ('52','54','63'):
        g=compile_followup(prefix,sources);menus=[n for n in g['nodes'].values() if n['type']=='menu'];histories=g['requiresPriorFlags']
        for values in itertools.product(*histories.values()):
            history=dict(zip(histories,values));extras=[{}]
            for flag,rule in g.get('conditionalPriorFlags',{}).items():
                if all(history.get(k) in v if isinstance(v,list) else history.get(k)==v for k,v in rule['when'].items()):
                    extras=[{**h,flag:value} for h in extras for value in rule['values']]
            for extra in extras:
                for opts in itertools.product(*(n['options'] for n in menus)):
                    trace,flags=walk(g,{n['id']:o['id'] for n,o in zip(menus,opts)},{**history,**extra})
                    assert trace[-1]['type']=='return' and g['completionFlag'] not in flags
                    actual=lines(trace,prefix)
                    if prefix=='52':
                        a=flags['F-AI03-A'];b=history['F-AI02-B']
                        assert (29 in actual)==(b=='B1') and (39 in actual)==(b=='B2') and (51 in actual)==(b=='B3')
                        assert (329 in actual)==(a=='A1') and (333 in actual)==(a=='A2') and (337 in actual)==(a=='A3')
                        assert (217 in actual)==(a=='A1') and (235 in actual)==(a=='A2') and (253 in actual)==(a=='A3')
                    elif prefix=='54':
                        a,b=flags['RIN-03A'],flags['RIN-03B'];old=history['RIN-02A']
                        assert (52 in actual)==(old!='A')
                        assert (12 in actual)==(old=='A' and extra['RIN-02B-A']=='A1')
                        assert (26 in actual)==(old=='A' and extra['RIN-02B-A']=='A2')
                        assert (38 in actual)==(old=='A' and extra['RIN-02B-A']=='A3')
                        assert (64 in actual)==(old!='A' and extra['RIN-02B-BC']=='B2')
                        assert (436 in actual)==(a=='A1') and (460 in actual)==(a=='A2') and (482 in actual)==(a=='A3')
                        assert (372 in actual)==(b=='B1') and (396 in actual)==(b=='B2') and (424 in actual)==(b=='B3')
                        assert 504 in actual and 508 not in actual
                    else:
                        a,b=flags['F-SA03-A'],flags['F-SA03-B'];old_a,old_b=history['F-SA02-A'],history['F-SA02-B']
                        assert (193 in actual)==(old_a=='A3' and old_b=='B3')
                        assert (257 in actual)==(b=='B1') and (353 in actual)==(b=='B2') and (459 in actual)==(b=='B3')
                        assert (233 in actual)==(b=='B1' and a=='A1') and (241 in actual)==(b=='B1' and a=='A2') and (249 in actual)==(b=='B1' and a=='A3')
                        assert 39 in actual,'Exactly one actual current promise and late arrival must exist'
                    count+=1
    for prefix in ('36','53'):
        g=compile_followup(prefix,sources);menus=[n for n in g['nodes'].values() if n['type']=='menu'];histories=g['requiresPriorFlags']
        for values in itertools.product(*histories.values()):
            history=dict(zip(histories,values))
            for opts in itertools.product(*(n['options'] for n in menus)):
                trace,flags=walk(g,{n['id']:o['id'] for n,o in zip(menus,opts)},history)
                assert trace[-1]['type']=='return' and g['completionFlag'] not in flags
                actual=lines(trace,prefix)
                if prefix=='36':
                    a,b=flags['KOTO-02A'],flags['KOTO-02B'];old=history['KOTO-01B']
                    assert (34 in actual)==(old=='A') and (40 in actual)==(old=='B') and (46 in actual)==(old=='C')
                    assert (162 in actual)==(a=='A') and (166 in actual)==(a=='B') and (170 in actual)==(a=='C')
                    assert (218 in actual)==(b=='A')
                    assert (258 in actual)==(a=='A') and (264 in actual)==(a!='A')
                else:
                    b=flags['F-YU03-B'];old=history['F-YU01-B']
                    assert (9 in actual)==(history['F-YU02-B']!='B3') and (23 in actual)==(history['F-YU02-B']=='B3')
                    assert (293 in actual)==(history['2-C05']=='A') and (305 in actual)==(history['2-C05']=='B')
                    assert (349 in actual)==(b=='B2' and old=='B2') and (353 in actual)==(b=='B2' and old!='B2')
                    assert (337 in actual)==(b=='B1') and (361 in actual)==(b=='B2') and (377 in actual)==(b=='B3')
                count+=1
    print(json.dumps({'passed':True,'paths':count,'meetings':['21','46','152','51','43','49','23','40','50','153','35','41','44','45','48','39','42','47','52','54','63','36','53'],'missingPriorFailsClosed':True,'completionOnlyAfterReturn':True}))


if __name__=='__main__':main()
