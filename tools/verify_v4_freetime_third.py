"""Actual later-FTE branch/return tests, independent of generated JSON."""
import itertools
import json
from build_v4_story import Source,ROOT
from v4_story_freetime_third import compile_third,THIRD_PREFIXES
from verify_v4_story import walk,references


def main():
    sources={p.name:Source(p) for p in (ROOT/'docs/design/rewrite_v4').glob('*.md')};count=0
    for prefix in THIRD_PREFIXES:
        graph=compile_third(prefix,sources);nodes=graph['nodes'];menus=[n for n in nodes.values() if n['type']=='menu']
        assert all(ref in nodes for ref in references(graph))
        h=graph.get('requiresPriorFlags',{})
        for values in itertools.product(*h.values()):
            history=dict(zip(h,values));histories=[history]
            for flag,rule in graph.get('conditionalPriorFlags',{}).items():
                if all(history.get(k) in v if isinstance(v,list) else history.get(k)==v for k,v in rule['when'].items()):histories=[{**row,flag:value} for row in histories for value in rule['values']]
            for history in histories:
                seen_routes=set()
                for opts in itertools.product(*(n['options'] for n in menus)):
                    trace,flags=walk(graph,{n['id']:o['id'] for n,o in zip(menus,opts)},history)
                    route=tuple(n['id'] for n in trace)
                    if route in seen_routes:continue
                    seen_routes.add(route)
                    assert trace[-1]['type']=='return',(prefix,history,trace[-1])
                    assert graph['completionFlag'] not in flags
                    actual={n.get('source',{}).get('line') for n in trace if n.get('source',{}).get('file')==graph['sourceFile']}
                    if prefix=='55':
                        a,b=flags['KOTO-03A'],flags['KOTO-03B']
                        assert (28 in actual)==(history['KOTO-02B']=='A') and (40 in actual)==(history['KOTO-02B']=='B') and (50 in actual)==(history['KOTO-02B']=='C')
                        assert (66 in actual)==(history['KOTO-02A']=='A') and (74 in actual)==(history['KOTO-02A']=='B') and (84 in actual)==(history['KOTO-02A']=='C')
                        assert 130 in actual,'First actual win exists in every path'
                        assert (320 in actual)==(b=='B1') and (358 in actual)==(b=='B2') and (510 in actual)==(b=='B3')
                        assert (464 in actual)==(b=='B3' and a=='A1') and (468 in actual)==(b=='B3' and a=='A2') and (472 in actual)==(b=='B3' and a=='A3')
                    elif prefix=='58':
                        old_a,old_b=history['F-RE02-A'],history['F-RE02-B'];b=flags['F-RE03-B']
                        assert (26 in actual)==(old_a=='A1') and (36 in actual)==(old_a=='A2') and (46 in actual)==(old_a=='A3')
                        assert (58 in actual)==(old_b=='B1') and (70 in actual)==(old_b=='B2') and (80 in actual)==(old_b=='B3')
                        assert (104 in actual)==(old_b=='B1') and (108 in actual)==(old_b!='B1')
                        assert (444 in actual)==(b=='B2' and old_a=='A1')
                        assert (208 in actual)==(b=='B1') and (456 in actual)==(b=='B2') and (568 in actual)==(b=='B3')
                        assert (554 in actual)==(b!='B3')
                    elif prefix=='60':
                        old_a,old_b=history['F-KE02-A'],history['F-KE02-B'];b=flags['F-KE03-B']
                        assert (28 in actual)==(old_a=='A1') and (36 in actual)==(old_a=='A2') and (42 in actual)==(old_a=='A3')
                        assert (50 in actual)==(old_b=='B1') and (60 in actual)==(old_b=='B2') and (70 in actual)==(old_b=='B3')
                        assert (136 in actual)==(b=='B1') and (202 in actual)==(b=='B2') and (334 in actual)==(b=='B3')
                        assert (318 in actual)==(b!='B3')
                    elif prefix=='61':
                        old=history['F-RI02-B'];a,b=flags['F-RI03-A'],flags['F-RI03-B']
                        assert (23 in actual)==(old=='B1') and (37 in actual)==(old=='B2') and (49 in actual)==(old=='B3')
                        assert (127 in actual)==(a=='A2' and old=='B1') and (131 in actual)==(a=='A2' and old!='B1')
                        assert (161 in actual)==(a=='A1' and b=='B1') and (313 in actual)==(a=='A1' and b=='B2') and (353 in actual)==(a=='A1' and b=='B3')
                        assert (275 in actual)==(b=='B1') and (331 in actual)==(b=='B2') and (369 in actual)==(b=='B3')
                    elif prefix=='56':
                        old=history['SHO-02B'];b=flags['SHO-03B']
                        assert (22 in actual)==(old=='A') and (36 in actual)==(old=='B') and (48 in actual)==(old=='C')
                        assert (56 in actual)==(old=='C' and history['SHO-02A']=='A')
                        assert (62 in actual)==(old=='C' and history['SHO-02A']=='B')
                        assert (68 in actual)==(old=='C' and history['SHO-02A']=='C')
                        assert (380 in actual)==(b=='B1') and (438 in actual)==(b=='B2') and (402 in actual)==(b=='B3')
                        assert (422 in actual)==(b!='B2')
                    elif prefix=='59':
                        a=flags['SORA-03A'];old=history['SORA-02B']
                        assert (20 in actual)==(old=='A') and (28 in actual)==(old=='B') and (38 in actual)==(old=='C')
                        assert 162 in actual and 104 in actual,'Every actual first game ends5:4'
                        assert (398 in actual)==(a=='A3')
                        assert ('SORA-03B-A' in flags)==(a=='A1') and ('SORA-03B-B' in flags)==(a=='A2')
                        assert (308 in actual)==(a=='A1' and flags['SORA-03B-A']=='B1')
                        assert (256 in actual)==(a=='A2')
                        assert (376 in actual)==(a=='A2' and flags['SORA-03B-B']=='B2')
                    elif prefix=='57':
                        a,b=flags['F-NA03-A'],flags['F-NA03-B'];old=history['F-NA02-B']
                        assert (22 in actual)==(history['4-C10']=='A') and (32 in actual)==(history['4-C10']=='B')
                        assert (42 in actual)==(history['F-NA02-A']=='A1') and (50 in actual)==(history['F-NA02-A']=='A2') and (60 in actual)==(history['F-NA02-A']=='A3')
                        assert (72 in actual)==(old=='B1') and (78 in actual)==(old=='B2') and (84 in actual)==(old=='B3')
                        assert (192 in actual)==(a=='A1') and (220 in actual)==(a=='A2') and (206 in actual)==(a=='A3')
                        assert (326 in actual)==(b=='B1') and (346 in actual)==(b=='B2') and (418 in actual)==(b=='B3')
                        assert (386 in actual)==(b!='B3')
                    elif prefix=='62':
                        a,b=flags['F-AK03-A'],flags['F-AK03-B'];old=history['F-AK02-A']
                        assert (21 in actual)==(old=='A1') and (31 in actual)==(old=='A2') and (43 in actual)==(old=='A3')
                        assert (57 in actual)==(history['F-AK02-B']!='B3') and (67 in actual)==(history['F-AK02-B']=='B3')
                        assert 171 in actual,'Satsuki actually leaves with her unfixed garment'
                        assert (205 in actual)==(b=='B1' and old=='A1') and (213 in actual)==(b=='B1' and old=='A2') and (221 in actual)==(b=='B1' and old=='A3')
                        assert (367 in actual)==(b=='B2' and a=='A1') and (371 in actual)==(b=='B2' and a=='A2') and (375 in actual)==(b=='B2' and a=='A3')
                        assert (349 in actual)==(b=='B1') and (377 in actual)==(b=='B2') and (393 in actual)==(b=='B3')
                    elif prefix=='64':
                        a,b=flags['F-HA03-A'],flags['F-HA03-B'];old=history['F-HA02-A']
                        assert (41 in actual)==(old=='A1') and (53 in actual)==(old=='A2') and (65 in actual)==(old=='A3')
                        assert (105 in actual)==(history['F-HA02-B']=='B1') and (113 in actual)==(history['F-HA02-B']=='B2') and (121 in actual)==(history['F-HA02-B']=='B3')
                        assert 73 in actual and 247 in actual and 253 in actual
                        assert (135 in actual)==(a=='A1') and (163 in actual)==(a=='A2') and (181 in actual)==(a=='A3')
                        assert (337 in actual)==(b=='B1' and a=='A1') and (341 in actual)==(b=='B1' and a!='A1')
                        assert (345 in actual)==(b=='B1') and (365 in actual)==(b=='B2') and (385 in actual)==(b=='B3')
                    elif prefix=='37':
                        a,b=flags['F-HA02-A'],flags['F-HA02-B']
                        assert (105 in actual)==(a=='A1') and (155 in actual)==(a=='A2') and (201 in actual)==(a=='A3')
                        assert (305 in actual)==(b=='B1') and 357 in actual
                    elif prefix=='38':
                        old_a,old_b=history['F-NA01-A'],history['F-NA01-B'];a=flags['F-NA02-A']
                        assert (33 in actual)==(old_a=='A1') and (47 in actual)==(old_a=='A2') and (59 in actual)==(old_a=='A3')
                        assert (373 in actual)==(old_b=='B1') and (383 in actual)==(old_b=='B2') and (395 in actual)==(old_b=='B3')
                        assert (197 in actual)==(a=='A1') and (283 in actual)==(a=='A2') and (345 in actual)==(a=='A3')
                    count+=1
        if h:
            trace,flags=walk(graph,{n['id']:n['options'][0]['id'] for n in menus})
            assert trace[-1]['type']=='gate' and graph['completionFlag'] not in flags
    print(json.dumps({'passed':True,'paths':count,'meetings':list(THIRD_PREFIXES),'runtimeExecuted':False}))


if __name__=='__main__':main()
