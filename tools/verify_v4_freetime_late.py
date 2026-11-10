"""Late routes consume exact calendar and previous choices, without game run."""
import itertools
import json
from build_v4_story import Source,ROOT,Graph,compile_choice_scene
from v4_story_freetime import compile_nested_first_meeting
from v4_story_freetime_followups import compile_followup
from v4_story_freetime_late import compile_late,LATE_KEYS
from v4_story_freetime_third import compile_third
from verify_v4_story import walk,references


def all_histories(g):
    h=g.get('requiresPriorFlags',{})
    for values in itertools.product(*h.values()):
        base=dict(zip(h,values));out=[base]
        for flag,rule in g.get('conditionalPriorFlags',{}).items():
            if all(base.get(k) in v if isinstance(v,list) else base.get(k)==v for k,v in rule['when'].items()):out=[{**row,flag:v} for row in out for v in rule['values']]
        yield from out


def source_lines(trace,p):return {n.get('source',{}).get('line') for n in trace if n.get('source',{}).get('file','').startswith(p+'_')}


def main():
    sources={p.name:Source(p) for p in (ROOT/'docs/design/rewrite_v4').glob('*.md')};docs={s.prefix:s for s in sources.values()}
    f={p:(compile_followup(p,sources) if p in ('21','23','35','39','41','43','44','45','48','49','52','53','54','63') else compile_nested_first_meeting(docs[p]) if p in ('26','27','28','31','34') else compile_choice_scene(docs[p])) for p in ('20','21','23','24','25','26','27','28','30','31','32','34','35','39','41','43','44','45','48','49','52','53','54','63')}
    f['29']=compile_choice_scene(docs['29']);f['38']=compile_third('38',sources)
    before=json.dumps(f,sort_keys=True,ensure_ascii=False);count=0
    for key in LATE_KEYS:
        g=compile_late(key,sources,f);assert all(ref in g['nodes'] for ref in references(g))
        menus=[n for n in g['nodes'].values() if n['type']=='menu']
        for history in all_histories(g):
            for selected in itertools.product(*(n['options'] for n in menus)):
                trace,flags=walk(g,{n['id']:o['id'] for n,o in zip(menus,selected)},history)
                assert trace[-1]['type']=='return',(key,history,trace[-1])
                assert g['completionFlag'] not in flags
                if key=='143':assert 160 not in source_lines(trace,'20') and 63 in source_lines(trace,'143')
                elif key=='144':
                    actual=source_lines(trace,'144');old=source_lines(trace,'21')
                    assert 84 not in old and 352 not in old and 199 in actual
                    assert (95 in actual)==(flags['KOTO-01A']=='A') and (123 in actual)==(flags['KOTO-01A']=='B')
                elif key=='145':
                    assert not source_lines(trace,'25')&set(range(1,37))
                    assert (57 in source_lines(trace,'145'))==(flags['F-AI01-B']=='B2')
                elif key=='146':
                    current=source_lines(trace,'146');old=source_lines(trace,'26')
                    assert not old&set(range(1,40)) and not old&{529,531}
                    assert all(i in current for i in (119,125,137,143))
                    assert (55 in current)==(history['2-C01']=='A') and (67 in current)==(history['2-C01']=='B') and (83 in current)==(history['2-C01']=='C')
                elif key=='147':assert not source_lines(trace,'27')&set(range(1,53))
                elif key=='RIN02Late6AM':assert 91 in source_lines(trace,'143') and 8 not in source_lines(trace,'35')
                elif key=='RIN03Late7':
                    old=source_lines(trace,'54');assert 12 not in old and 504 not in old and 508 in old and 113 in source_lines(trace,'143')
                elif key=='AI02Late6AM':
                    new=source_lines(trace,'145');old=source_lines(trace,'43')
                    assert 93 in new and 339 not in old
                    assert (123 in new)==(history['F-AI01-A']=='A1')
                    assert (63 in old)==(history['F-AI01-A']=='A3' and history['AI01Dinner5A3']=='EAT')
                    assert (69 in old)==(history['F-AI01-A']=='A3' and history['AI01Dinner5A3']=='LEAVE')
                elif key=='AI03Late6PM':
                    new=source_lines(trace,'145');old=source_lines(trace,'52')
                    assert not old&set(range(7,18)) and 151 in new
                    assert (165 in new)==(history['F-AI02-B']=='B1')
                elif key=='RE02Late6PM':assert 9 not in source_lines(trace,'45') and 113 in source_lines(trace,'147')
                elif key=='148':assert 296 not in source_lines(trace,'23') and 77 in source_lines(trace,'148')
                elif key=='149':assert not source_lines(trace,'32')&{7,9} and 31 in source_lines(trace,'149') and 11 in source_lines(trace,'32')
                elif key=='150':assert not source_lines(trace,'28')&set(range(1,47)) and 103 in source_lines(trace,'150')
                elif key=='151':assert not source_lines(trace,'31')&set(range(1,18)) and 39 in source_lines(trace,'151')
                elif key=='87':
                    actual=source_lines(trace,'87');assert not source_lines(trace,'34')&set(range(496,514))
                    assert (81 in actual)==(flags['F-HA01-B']=='B1') and (89 in actual)==(flags['F-HA01-B']=='B2') and (99 in actual)==(flags['F-HA01-B']=='B3')
                    assert 117 in actual
                elif key=='88':
                    new=source_lines(trace,'88');old=source_lines(trace,'29')
                    assert not old&set(range(9,38)) and 97 in old
                    assert all(i in new for i in (9,67,73,85,91,105))
                    assert 271 not in old and not old&set(range(365,374))
                    assert (123 in new)==(flags['F-NA01-B']=='B2') and (377 in old)==(flags['F-NA01-B']=='B2')
                    assert sum(n.get('text')=='규칙을 바꾸면 한 판은 더 해 보고 싶어' for n in trace)==int(flags['F-NA01-A']=='A3' and flags['F-NA01-B']=='B1')
                elif key=='38-late':
                    new=source_lines(trace,'88');old=source_lines(trace,'38')
                    assert 147 in new and 161 in new and 21 in old and not old&set(range(9,20))
                    assert not old&set(range(383,392))
                    assert (169 in new)==(history['F-NA01-B']=='B2')
                elif key=='89':assert all(i in source_lines(trace,'89') for i in (7,45,83,107,115))
                elif key=='90':assert all(i in source_lines(trace,'90') for i in (9,51,75,81,93))
                elif key=='SHO02Late7':assert 101 in source_lines(trace,'148') and 7 not in source_lines(trace,'41')
                elif key=='SA03Late6PM':assert 49 in source_lines(trace,'149') and not source_lines(trace,'63')&set(range(9,40))
                elif key=='AK02Late6AM':
                    assert (47 in source_lines(trace,'151'))==(history['F-AK01-B']=='B2')
                    assert not source_lines(trace,'39')&set(range(9,24))
                elif key=='RI02Late6AM':assert 103 in source_lines(trace,'90') and 9 in source_lines(trace,'48')
                count+=1
    assert json.dumps(f,sort_keys=True,ensure_ascii=False)==before,'Normal graphs must not acquire late route mutations'
    # Actual current fifth-day dinner follows145; it cannot award old lunch.
    from v4_story_case2 import Router,_day_five
    fg=compile_late('145',sources,f);g=Graph('2');end=g.add('test-end',{'type':'end'});r=Router(g,sources,{'145':fg});entry=_day_five(r,end);graph=g.export(entry)
    menus=[n for n in g.nodes.values() if n['type']=='menu']
    base={n['id']:n['options'][0]['id'] for n in menus};base['v4:2:window:F2-A']='145'
    first=next(n for n in menus if any('F-AI01-A' in o.get('set',{}) for o in n['options']))
    for a,meal in itertools.product(('A1','A2','A3'),('EAT','LEAVE')):
        selected={**base,first['id']:a,'v4:2:menu:AI01Dinner5A3':meal}
        trace,flags=walk(graph,selected);assert trace[-1]['type']=='end'
        actual=source_lines(trace,'145')
        assert (67 in actual)==(a=='A1') and (71 in actual)==(a=='A2')
        assert (77 in actual)==(a=='A3' and meal=='EAT') and (81 in actual)==(a=='A3' and meal=='LEAVE')
        assert flags['AI01Late5'] and flags['fte:25:complete']
        assert 'F-AI01-A3-LUNCH' not in flags
        count+=1
    # The late63 callback happens at seventh-day dinner, never retroactively
    # inside the already-passed sixth-day lunch.
    from v4_story_case2 import _waiting_evening
    g=Graph('2');end=g.add('test-end',{'type':'end'});r=Router(g,sources,{});entry=_waiting_evening(r,end);graph=g.export(entry)
    selected={n['id']:n['options'][0]['id'] for n in g.nodes.values() if n['type']=='menu'}
    for late,a,b in itertools.product((False,True),('A1','A2','A3'),('B1','B2','B3')):
        trace,flags=walk(graph,selected,{'2-C06':'A','SA03Late6PM':late,'F-SA03-A':a,'F-SA03-B':b})
        assert trace[-1]['type']=='end';actual=source_lines(trace,'149')
        assert (75 in actual)==late and (147 in actual)==late
        assert (79 in actual)==(late and b=='B1') and (89 in actual)==(late and b=='B2') and (101 in actual)==(late and b=='B3')
        assert (125 in actual)==(late and a=='A1') and (131 in actual)==(late and a=='A2') and (139 in actual)==(late and a=='A3')
        count+=1
    print(json.dumps({'passed':True,'paths':count,'lateMeetings':len(LATE_KEYS),'baseGraphMutation':False,'currentDinnerSeparateFromOldLunch':True}))


if __name__=='__main__':main()
