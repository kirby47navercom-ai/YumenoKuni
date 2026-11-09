"""Own authored charts over REA-derived judgment rules; never an original score.

The script determines claims, speaker identity, responses and their order. The
new chart determines physical tap/hold/mash inputs and their timing windows.
"""
from copy import deepcopy


def bind_rhythm_tasks(tasks):
    tasks=deepcopy(tasks)
    for ident in ('T3-AA-01','T4-AA-01','T5-AA-01'):
        if ident not in tasks:
            continue
        task=tasks[ident]
        unresolved=[b for b in task.get('bindings',[]) if b.get('kind')!='rhythmWaveTiming']
        if unresolved:
            continue
        original=deepcopy(task['waves'])
        assert len(original)==3 and len(task['answerParts'])==4
        opponent=next(e['actor'] for e in original[0]['script'] if e.get('type')=='say')
        claims=[];waves=[];line_waves=[]
        for index,wave in enumerate(original):
            pairs=[];pending=[]
            for event in wave['script']:
                if event.get('type')=='say' and event.get('actor')==opponent:
                    if pending:
                        assert pairs, (ident,'directions before first claim need explicit intro')
                        pairs[-1]['response'].extend(pending);pending=[]
                    pairs.append({'claim':deepcopy(event),'response':[]})
                else:
                    pending.append(deepcopy(event))
            assert pairs, (ident,index)
            pairs[-1]['response'].extend(pending)
            for pair in pairs:
                claims.append(pair['claim']);line_waves.append(index)
            waves.append({**wave,'pairs':pairs})
        # Explicitly different physical patterns per source wave. Durations are
        # authored here, not inferred as exact original music keyframes.
        patterns=[
            [{'button':0,'type':'tap','targetSeconds':.9},{'button':2,'type':'tap','targetSeconds':.9},{'button':1,'type':'hold','targetSeconds':.9,'holdFrames':60}],
            [{'button':3,'type':'hold','targetSeconds':1.05,'holdFrames':48},{'button':1,'type':'tap','targetSeconds':.75},{'button':0,'type':'mash','targetSeconds':.9}],
            [{'button':2,'type':'tap','targetSeconds':.65},{'button':0,'type':'mash','targetSeconds':.9},{'button':3,'type':'hold','targetSeconds':.8,'holdFrames':72}],
        ]
        task.update(opponent=opponent,opponentDisplay=claims[0]["speaker"],waves=waves,sourceWaves=original,lines=claims,
                    waveIndexByLine=line_waves,rhythm_waves=[{'notes':p} for p in patterns],
                    final=deepcopy(task['answerParts']),finalDistractors=deepcopy(task['distractors']),
                    finalSubject=task.get('fixedSubject',''),bindings=[],runtimeReady=True,
                    rhythmBinding={'kind':'own-authored-chart','source':'tools/v4_rhythm_bindings.py',
                     'normalCriticalFrames':[19,21],'normalHitFrames':[12,28],
                     'normalInputFrames':[1,45],'holdCriticalDeltaFrames':1,'holdHitDeltaFrames':8,
                     'sameWaveResponseOnlyAfterPhysicalSuccess':True,
                     'originalSongScoreRecovered':False})
        assert len(task['lines'])==len(task['waveIndexByLine'])
    return tasks


if __name__=='__main__':
    import json
    from pathlib import Path
    tasks=json.loads(Path('data/v4_story/tasks.json').read_text(encoding='utf8'))['tasks']
    bound=bind_rhythm_tasks(tasks)
    for ident in ('T3-AA-01','T4-AA-01','T5-AA-01'):
        t=bound[ident]
        assert t['runtimeReady'] and not t['bindings'] and len(t['waves'])==3
        assert {n['type'] for w in t['rhythm_waves'] for n in w['notes']}=={'tap','hold','mash'}
        original=[e for w in tasks[ident]['waves'] for e in w['script']]
        rebuilt=[]
        for wave in t['waves']:
            for pair in wave['pairs']:
                rebuilt += [pair['claim'],*pair['response']]
        assert rebuilt==original, ident
    print('PASS: three actual source waves, every claim/response in order, explicit tap/hold/mash windows; own chart, no original score claim')
